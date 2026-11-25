import assert from 'node:assert/strict'
import { buildRows, defaultConfig, normalizeConfig, PAD_W, PAD_H, GAP } from '../src/common/layout.js'

function check(cfg, wantRows) {
  const rows = buildRows(cfg)
  assert.equal(rows.length, wantRows)
  let height = 0
  for (const r of rows) {
    const w = r.reduce((a, k) => a + k.w, 0) + GAP * (r.length - 1)
    assert.ok(w <= PAD_W && w >= PAD_W - 8, 'szerokość rzędu ' + w)
    assert.ok(r[0].h >= 40, 'za niskie klawisze ' + r[0].h)
    height += r[0].h + GAP
  }
  assert.ok(height - GAP <= PAD_H)
  return rows
}

// Wszystko włączone: 10 klawiszy naukowych = 2 rzędy + 5 podstawowych.
check(defaultConfig(), 7)
// Wszystko wyłączone: tylko podstawowa klawiatura, duże klawisze.
const none = normalizeConfig({ par: false, sqrt: false, sq: false, pow: false, pct: false,
  fact: false, pi: false, inv: false, ans: false })
assert.equal(check(none, 5)[0][0].h, 58)
// Tylko procent i pierwiastek: 1 rząd naukowy.
const two = normalizeConfig({ par: false, sq: false, pow: false, fact: false, pi: false, inv: false, ans: false })
const r = check(two, 6)
assert.deepEqual(r[0].map(k => k.k), ['√(', '%'])
// Śmieci w zapisanych ustawieniach są ignorowane.
assert.equal(normalizeConfig({ pct: 'x', zzz: 1 }).pct, true)
console.log('layout OK')
