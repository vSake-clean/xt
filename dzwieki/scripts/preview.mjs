// Podgląd ekranów w Chromium (tylko do sprawdzenia układu, nie jest częścią aplikacji).
// Prosty interpreter szablonu .ux: for / if / {{ }} i style z pliku.
//   node scripts/preview.mjs <wyjście.png>
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)
const { chromium } = require('playwright')

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..')
const ux = fs.readFileSync(path.join(root, 'src/pages/index/index.ux'), 'utf8')
const tpl = ux.match(/<template>([\s\S]*)<\/template>/)[1]
const css = ux.match(/<style>([\s\S]*)<\/style>/)[1]
const IMG = '/common/img/'
const k = (n) => String(n).split('').map((c) => IMG + 'k_' + c + '.png')
const d = (n) => String(n).split('').map((c) => IMG + 'd_' + c + '.png')
const memes = ['bomba_plant', 'bomba_tik', 'wybuch', 'kliker', 'boom']
const lv = [1, 1, 37, 1, 250]
const states = [
  { mode: 'menu' },
  { mode: 'foto', fotoCount: 3, fotoSrc: '/../sample.jpg', fotoNum: ['k_2', 'k_sl', 'k_3'].map((x) => IMG + x + '.png') },
  { mode: 'foto', fotoCount: 0, fotoSrc: '', fotoNum: [] },
  { mode: 'list', headImg: IMG + 'h_m.png', pageImg: IMG + 'p_1_4.png',
    rows: memes.map((n, i) => ({ i, name: IMG + 'n_m_' + n + '.png', lv: k(lv[i]) })) },
  { mode: 'level', nameImg: IMG + 'n_m_bomba_tik.png', bigDigits: d(1), custom: false, err: false,
    ofImg: IMG + 't_of_s.png', accent: '#ffb340', playImg: IMG + 'b_stop.png' },
  { mode: 'level', nameImg: IMG + 'n_v_serce.png', bigDigits: d(1000), custom: false, err: false, ofImg: IMG + 't_of_v.png',
    accent: '#b39dfa', playImg: IMG + 'b_stop.png' },
  { mode: 'edit', nameImg: IMG + 'n_v_wlasna.png', accent: '#b39dfa', playImg: IMG + 'b_play.png', err: false,
    cellsA: [1, 0, 1, 0].map((v, i) => ({ i, img: IMG + 'w_' + v + '.png' })),
    cellsB: [2, 0, 0, 0].map((v, i) => ({ i: i + 4, img: IMG + 'w_' + v + '.png' })) },
  { mode: 'edit', nameImg: IMG + 'n_s_wlasny.png', accent: '#4cd7c8', playImg: IMG + 'b_play.png', err: false,
    cellsA: [1, 3, 5, 8].map((v, i) => ({ i, img: IMG + 'e_' + v + '.png' })),
    cellsB: [0, 0, 0, 0].map((v, i) => ({ i: i + 4, img: IMG + 'e_' + v + '.png' })) }
]

const renderer = `
function ev(expr, ctx) { return Function(...Object.keys(ctx), 'return (' + expr + ')')(...Object.values(ctx)) }
function interp(s, ctx) { return s.replace(/\\{\\{([^}]*)\\}\\}/g, (_, e) => { const v = ev(e, ctx); return v == null ? '' : v }) }
function render(node, ctx, out) {
  if (node.nodeType === 3) { return }
  if (node.nodeType !== 1) return
  const f = node.getAttribute('for')
  if (f) {
    const m = f.match(/\\{\\{\\s*(?:\\((\\w+),\\s*(\\w+)\\)\\s+in\\s+)?(.+?)\\s*\\}\\}/)
    const list = ev(m[3], ctx) || []
    list.forEach((item, idx) => {
      const c = Object.assign({}, ctx)
      if (m[1]) { c[m[1]] = idx; c[m[2]] = item } else { c.$item = item; c.$idx = idx }
      emit(node, c, out)
    })
    return
  }
  emit(node, ctx, out)
}
function emit(node, ctx, out) {
  const cond = node.getAttribute('if')
  if (cond && !ev(cond.replace(/^\\{\\{|\\}\\}$/g, ''), ctx)) return
  const tn = node.tagName.toLowerCase(); const tag = (tn === 'image' || tn === 'img') ? 'img' : 'div'
  const el = document.createElement(tag)
  for (const a of node.attributes) {
    if (a.name === 'for' || a.name === 'if' || a.name.startsWith('@')) continue
    let v = interp(a.value, ctx)
    if (a.name === 'src') v = 'src' + v
    el.setAttribute(a.name, v)
  }
  for (const ch of node.childNodes) render(ch, ctx, el)
  out.appendChild(el)
}
`
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
body { margin: 0; background: #444; display: flex; flex-wrap: wrap; gap: 16px; padding: 16px; width: ${4 * 390 + 5 * 16}px }
.screen { width: 390px; height: 450px; overflow: hidden; border-radius: 48px; position: relative }
.screen div { display: flex; box-sizing: border-box; flex-shrink: 0 }
.screen img { display: block; flex-shrink: 0 }
${css}
</style></head><body><template id="t">${tpl}</template><script>${renderer}
const states = ${JSON.stringify(states)}
const t = document.getElementById('t').content.firstElementChild
for (const s of states) { const box = document.createElement('div'); box.className = 'screen'; render(t, s, box); document.body.appendChild(box) }
</script></body></html>`
fs.mkdirSync(path.join(root, '.preview'), { recursive: true })
fs.writeFileSync(path.join(root, '.preview/index.html'), html)
// zastępcze zdjęcie testowe (prawdziwe zdjęcia nigdy nie trafiają do podglądu)
fs.copyFileSync(path.join(root, 'podglad-zdjecie.jpg'), path.join(root, '.preview/sample.jpg'))
try { fs.symlinkSync(path.join(root, 'src'), path.join(root, '.preview/src')) } catch (e) {}
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 4 * 390 + 5 * 16, height: 2 * 450 + 3 * 16 }, deviceScaleFactor: 1 })
await page.goto('file://' + path.join(root, '.preview/index.html'))
await page.waitForTimeout(300)
// sprawdź, czy coś nie wychodzi poza ekran
const over = await page.evaluate(() => {
  const res = []
  document.querySelectorAll('.screen').forEach((s, si) => {
    const r0 = s.getBoundingClientRect()
    s.querySelectorAll('*').forEach((e) => {
      const r = e.getBoundingClientRect()
      if (r.bottom > r0.bottom + 0.5 || r.right > r0.right + 0.5) res.push(si + ':' + e.className + ' ' + Math.round(r.bottom - r0.top))
      if (e.tagName === 'IMG' && !e.complete || (e.tagName === 'IMG' && e.naturalWidth === 0)) res.push(si + ': brak obrazka ' + e.getAttribute('src'))
    })
  })
  return res
})
console.log(over.length ? over.join('\n') : 'układ OK')
await page.screenshot({ path: process.argv[2] || path.join(root, 'podglad.png') })
await browser.close()
