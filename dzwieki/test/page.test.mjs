// Test logiki ekranu (index.ux) z atrapami modułów zegarka.
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..')
const ux = fs.readFileSync(path.join(root, 'src/pages/index/index.ux'), 'utf8')
let script = ux.match(/<script>([\s\S]*)<\/script>/)[1]
script = script
  .replace("import vibrator from '@system.vibrator'", 'const vibrator = globalThis.__mocks.vibrator')
  .replace("import audio from '@system.audio'", 'const audio = globalThis.__mocks.audio')
  .replace("import storage from '@system.storage'", 'const storage = globalThis.__mocks.storage')
  .split('../../common/').join(path.join(root, 'src/common/') )
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dzwieki-'))
const file = path.join(tmp, 'page.mjs')
fs.writeFileSync(file, script)

// --- atrapy -----------------------------------------------------------
let clock = 0
let timers = []
globalThis.setTimeout = (fn, ms) => { const t = { fn, at: clock + ms, on: true }; timers.push(t); return t }
globalThis.clearTimeout = (t) => { if (t) t.on = false }
Date.now = () => clock
function advance(ms) {
  const end = clock + ms
  for (;;) {
    const due = timers.filter((t) => t.on && t.at <= end).sort((a, b) => a.at - b.at)[0]
    if (!due) break
    clock = due.at
    due.on = false
    due.fn()
  }
  clock = end
}

const store = {}
const vibes = []
const played = []
const audio = {
  volume: 0.6, src: '', failMp3: false,
  play() {
    played.push({ src: this.src, volume: this.volume, at: clock })
    if (this.failMp3 && this.src.endsWith('.mp3') && this.onerror) this.onerror()
  },
  stop() { this.stopped = (this.stopped || 0) + 1 }
}
globalThis.__mocks = {
  vibrator: { vibrate(o) { vibes.push({ mode: o.mode, at: clock }) } },
  audio,
  storage: {
    get(o) { o.success(store[o.key] === undefined ? '' : store[o.key]) },
    set(o) { store[o.key] = o.value }
  }
}

const page = (await import(file)).default
function mount() {
  const vm = Object.assign({}, page, JSON.parse(JSON.stringify(page.private)))
  vm.onInit()
  return vm
}
function tap(vm, id) {
  vm.hit(id) // touchstart
  vm.hit(id) // click z tego samego dotknięcia
  advance(500)
}

let n = 0
function t(name, fn) { fn(); n++ }

t('start: menu, nic nie gra', () => {
  const vm = mount()
  assert.equal(vm.mode, 'menu')
  assert.equal(vibes.length, 0)
  assert.equal(played.length, 0)
})

t('nowy dźwięk startuje na poziomie 1 i gra super cicho', () => {
  const vm = mount()
  tap(vm, 'kind:s')
  assert.equal(vm.mode, 'list')
  assert.equal(vm.rows.length, 5)
  assert.deepEqual(vm.rows[0].lv, ['/common/img/k_1.png'])
  tap(vm, 'row:0')
  assert.equal(vm.mode, 'level')
  assert.deepEqual(vm.bigDigits, ['/common/img/d_1.png'])
  tap(vm, 'play')
  const last = played[played.length - 1]
  assert.equal(last.src, '/common/snd/ping_2.mp3')
  assert.equal(last.volume, 0.1)
})

t('zmieniony poziom zostaje zapisany i wraca po ponownym otwarciu', () => {
  const vm = mount()
  tap(vm, 'kind:s')
  tap(vm, 'row:2')
  tap(vm, 'd:100')
  tap(vm, 'd:10')
  tap(vm, 'd:1')
  assert.equal(vm._level, 112)
  assert.deepEqual(JSON.parse(store.lv), { 's:dzwonek': 112 })
  const vm2 = mount()
  tap(vm2, 'kind:s')
  assert.deepEqual(vm2.rows[2].lv, ['/common/img/k_1.png', '/common/img/k_1.png', '/common/img/k_2.png'])
  assert.deepEqual(vm2.rows[0].lv, ['/common/img/k_1.png'])
  tap(vm2, 'row:2')
  assert.equal(vm2._level, 112)
  tap(vm2, 'min')
  assert.equal(vm2._level, 1)
  assert.equal(JSON.parse(store.lv)['s:dzwonek'], 1)
  for (let i = 0; i < 15; i++) { vm2.hit('d:100'); advance(350) }
  assert.equal(vm2._level, 1000)
  for (let i = 0; i < 15; i++) { vm2.hit('d:-100'); advance(350) }
  assert.equal(vm2._level, 1)
})

t('touchstart + click liczą się raz', () => {
  const vm = mount()
  tap(vm, 'kind:v')
  tap(vm, 'row:0')
  vm.hit('d:1'); advance(80); vm.hit('d:1')
  assert.equal(vm._level, 2)
  advance(500)
})

t('po zmianie ekranu spóźniony click nie trafia w nowy ekran', () => {
  const vm = mount()
  vm.hit('kind:s')
  advance(120)
  vm.hit('row:1') // ten sam palec, nowy ekran pod spodem
  assert.equal(vm.mode, 'list')
  advance(500)
  vm.hit('row:1')
  assert.equal(vm.mode, 'level')
  advance(500)
})

t('wibracja na poziomie 1 to jeden krótki impuls', () => {
  const vm = mount()
  tap(vm, 'kind:v')
  tap(vm, 'row:0')
  vm._levels = {}
  vm._level = 1
  const before = vibes.length
  vm.hit('play')
  advance(3000)
  assert.equal(vibes.length - before, 1)
  assert.equal(vibes[vibes.length - 1].mode, 'short')
  assert.equal(vm.playImg, '/common/img/b_play.png')
})

t('mocniejsza wibracja i zatrzymanie w trakcie', () => {
  const vm = mount()
  tap(vm, 'kind:v')
  tap(vm, 'row:4') // SOS
  vm._level = 1000
  const before = vibes.length
  vm.hit('play')
  assert.equal(vm.playImg, '/common/img/b_stop.png')
  advance(600)
  vm.hit('play') // stop
  const mid = vibes.length
  assert.ok(mid - before > 1)
  advance(10000)
  assert.equal(vibes.length, mid)
  assert.equal(vm.playImg, '/common/img/b_play.png')
})

t('własny dźwięk: edytor, zapis kroków, melodia', () => {
  const vm = mount()
  tap(vm, 'kind:s')
  tap(vm, 'next')
  assert.equal(vm.rows.length, 4)
  tap(vm, 'row:8')
  assert.equal(vm.custom, true)
  tap(vm, 'edit')
  assert.equal(vm.mode, 'edit')
  assert.equal(vm.cellsA[0].img, '/common/img/e_1.png')
  tap(vm, 'c:4') // pauza -> c
  assert.equal(vm.cellsB[0].img, '/common/img/e_1.png')
  assert.deepEqual(JSON.parse(store.cs), [1, 3, 5, 8, 1, 0, 0, 0])
  const before = played.length
  tap(vm, 'play')
  advance(3000)
  const notes = played.slice(before).map((p) => p.src)
  assert.deepEqual(notes, ['n1', 'n3', 'n5', 'n8', 'n1'].map((x) => '/common/snd/' + x + '_2.mp3'))
  tap(vm, 'back')
  assert.equal(vm.mode, 'level')
  tap(vm, 'back')
  assert.equal(vm.mode, 'list')
  assert.equal(vm._page, 1)
})

t('własna wibracja: kroki zapisane', () => {
  const vm = mount()
  tap(vm, 'kind:v')
  tap(vm, 'next')
  tap(vm, 'row:7')
  tap(vm, 'edit')
  tap(vm, 'c:1') // pauza -> tik
  assert.deepEqual(JSON.parse(store.cv), [1, 1, 1, 0, 2, 0, 0, 0])
  assert.equal(vm.cellsA[1].img, '/common/img/w_1.png')
})

t('mp3 nie działa: przejście na wav i zapamiętanie', () => {
  audio.failMp3 = true
  const vm = mount()
  tap(vm, 'kind:s')
  tap(vm, 'row:1')
  const before = played.length
  tap(vm, 'play')
  const srcs = played.slice(before).map((p) => p.src)
  assert.deepEqual(srcs, ['/common/snd/kropla_2.mp3', '/common/snd/kropla_2.wav'])
  assert.equal(store.fmt, 'wav')
  assert.equal(vm.err, false)
  const vm2 = mount()
  tap(vm2, 'kind:s')
  tap(vm2, 'row:1')
  const b2 = played.length
  tap(vm2, 'play')
  assert.equal(played[b2].src, '/common/snd/kropla_2.wav')
  audio.failMp3 = false
  delete store.fmt
})

t('brak modułu audio: napis o błędzie od razu', () => {
  const saved = audio.play
  audio.play = () => { throw new Error('nie wspierane') }
  const vm = mount()
  tap(vm, 'kind:s')
  tap(vm, 'row:0')
  tap(vm, 'play')
  assert.equal(vm.err, true)
  assert.equal(vm.playImg, '/common/img/b_play.png')
  audio.play = saved
  delete store.fmt
})

t('przycisk wstecz zegarka', () => {
  const vm = mount()
  tap(vm, 'kind:s')
  tap(vm, 'row:0')
  assert.equal(vm.onBackPress(), true)
  assert.equal(vm.mode, 'list')
  assert.equal(vm.onBackPress(), true)
  assert.equal(vm.mode, 'menu')
  assert.equal(vm.onBackPress(), false)
})

t('wyjście przywraca głośność odtwarzacza', () => {
  audio.volume = 0.6
  const vm = mount()
  tap(vm, 'kind:s')
  tap(vm, 'row:0')
  tap(vm, 'play')
  assert.equal(audio.volume, 0.1)
  vm.onDestroy()
  assert.equal(audio.volume, 0.6)
})

fs.rmSync(tmp, { recursive: true, force: true })
console.log('OK:', n, 'testów ekranu')
