import assert from 'node:assert/strict'
import {
  MIN, MAX, DEFAULT, TIERS, clamp, gain, soundPlan, pulses, longPulses, vibeTimes,
  customVibePattern, normalizeSteps, getLevel, setLevel, parseLevels, digits
} from '../src/common/levels.js'
import { SOUNDS, MEMES, VIBES, DEFAULT_NOTES, DEFAULT_VIBE, levelKey, itemsOf, pagesOf } from '../src/common/catalog.js'
import { DURATIONS } from '../src/common/durations.js'
import fs from 'node:fs'

let n = 0
function t(name, fn) {
  fn()
  n++
}

t('zakres i domyślny poziom', () => {
  assert.equal(MIN, 1)
  assert.equal(MAX, 1000)
  assert.equal(DEFAULT, 1)
  assert.equal(clamp(0), 1)
  assert.equal(clamp(-5), 1)
  assert.equal(clamp('abc'), 1)
  assert.equal(clamp(1001), 1000)
  assert.equal(clamp(55.4), 55)
})

t('poziom 1 jest super cichy, 1000 to pełna głośność', () => {
  assert.ok(Math.abs(gain(1) - 0.001) < 1e-9)
  assert.ok(Math.abs(gain(1000) - 1) < 1e-9)
  let prev = 0
  for (let l = 1; l <= 1000; l++) {
    const g = gain(l)
    assert.ok(g > prev, 'rośnie: ' + l)
    prev = g
  }
})

t('plan dźwięku: najcichszy plik + głośność odtwarzacza', () => {
  assert.deepEqual(soundPlan(1), { tier: 2, volume: 0.1, gain: 0.001 })
  assert.deepEqual(soundPlan(1000), { tier: 0, volume: 1, gain: 1 })
  for (let l = 1; l <= 1000; l++) {
    const p = soundPlan(l)
    assert.ok(p.volume > 0 && p.volume <= 1, 'volume ' + l)
    assert.ok(p.volume >= 0.0999, 'volume nie za mała ' + l)
    const total = TIERS[p.tier] * p.volume
    assert.ok(Math.abs(total - gain(l)) / gain(l) < 0.002, 'łącznie ' + l)
  }
})

t('wibracja: poziom 1 to jeden impuls, wyżej dłużej', () => {
  assert.equal(pulses(1), 1)
  assert.equal(pulses(1000), 10)
  assert.equal(longPulses(1), 3)
  let prev = 1
  for (let l = 1; l <= 1000; l++) {
    assert.ok(pulses(l) >= prev)
    prev = pulses(l)
  }
  assert.deepEqual(vibeTimes(['b'], 1), [0])
  assert.deepEqual(vibeTimes(['b', 200, 'b'], 1), [0, 240])
  assert.deepEqual(vibeTimes(['B'], 1), [0, 40, 80])
  assert.equal(vibeTimes(['b'], 1000).length, 10)
})

t('każdy wzór daje impulsy w rosnącej kolejności', () => {
  for (const v of VIBES) {
    if (v.custom) continue
    for (const l of [1, 500, 1000]) {
      const ts = vibeTimes(v.pattern, l)
      assert.ok(ts.length > 0, v.id)
      for (let i = 1; i < ts.length; i++) assert.ok(ts[i] > ts[i - 1], v.id)
      assert.ok(ts[ts.length - 1] < 10000, v.id + ' nie za długo')
    }
  }
})

t('własna wibracja', () => {
  assert.deepEqual(customVibePattern(DEFAULT_VIBE), ['b', 160, 320, 'b', 160, 320, 'B'])
  assert.deepEqual(customVibePattern([0, 0, 0, 0, 0, 0, 0, 0]), [])
  assert.equal(vibeTimes(customVibePattern([0, 0, 0, 0, 0, 0, 0, 0]), 1).length, 0)
})

t('kroki edytora są poprawiane', () => {
  assert.deepEqual(normalizeSteps(null, 8, 9, DEFAULT_NOTES), DEFAULT_NOTES)
  assert.deepEqual(normalizeSteps([1, 99, -1, 'x', 4], 8, 9, DEFAULT_NOTES), [1, 0, 0, 0, 4, 0, 0, 0])
  assert.deepEqual(normalizeSteps([2, 2, 2, 2, 2, 2, 2, 2, 2], 8, 3, DEFAULT_VIBE), [2, 2, 2, 2, 2, 2, 2, 2])
})

t('zapis poziomów: brak wpisu = 1, zmiana zostaje', () => {
  let m = parseLevels('')
  assert.equal(getLevel(m, levelKey('s', 'ping')), 1)
  m = setLevel(m, levelKey('s', 'ping'), 250)
  assert.equal(getLevel(m, 's:ping'), 250)
  assert.equal(getLevel(m, 'v:tik'), 1)
  const back = parseLevels(JSON.stringify(m))
  assert.equal(getLevel(back, 's:ping'), 250)
  assert.equal(getLevel(back, 's:gong'), 1)
  assert.equal(getLevel(parseLevels('{"s:ping": 5000}'), 's:ping'), 1000)
  assert.deepEqual(parseLevels('zepsute'), {})
})

t('cyfry poziomu', () => {
  assert.deepEqual(digits(1), ['1'])
  assert.deepEqual(digits(1000), ['1', '0', '0', '0'])
})

t('katalog: unikalne id, jeden własny w dźwiękach i wibracjach', () => {
  for (const list of [SOUNDS, MEMES, VIBES]) {
    const ids = list.map((x) => x.id)
    assert.equal(new Set(ids).size, ids.length)
  }
  assert.equal(SOUNDS.filter((x) => x.custom).length, 1)
  assert.equal(VIBES.filter((x) => x.custom).length, 1)
  assert.equal(MEMES.filter((x) => x.custom).length, 0)
  assert.equal(itemsOf('m'), MEMES)
  assert.equal(pagesOf('s'), 2)
  assert.equal(pagesOf('m'), 4)
  assert.equal(pagesOf('v'), 2)
})

t('każdy dźwięk ma pliki i długość', () => {
  const dir = new URL('../src/common/snd/', import.meta.url)
  const ids = SOUNDS.concat(MEMES).filter((x) => !x.custom).map((x) => x.id)
  for (let i = 1; i <= 8; i++) ids.push('n' + i)
  for (const id of ids) {
    assert.ok(DURATIONS[id] > 0 && DURATIONS[id] < 8000, 'długość ' + id)
    for (const f of [id + '_0.mp3', id + '_1.mp3', id + '_2.mp3', id + '.wav']) {
      assert.ok(fs.statSync(new URL(f, dir)).size > 0, f)
    }
  }
  const img = new URL('../src/common/img/', import.meta.url)
  for (const [k, list] of [['s', SOUNDS], ['m', MEMES], ['v', VIBES]]) {
    for (const x of list) assert.ok(fs.existsSync(new URL('n_' + k + '_' + x.id + '.png', img)), x.id)
    for (let p = 1; p <= pagesOf(k); p++) {
      assert.ok(fs.existsSync(new URL('p_' + p + '_' + pagesOf(k) + '.png', img)))
    }
  }
})

console.log('OK:', n, 'testów')
