import assert from 'node:assert/strict'
import { createGame, H, BIRD_H, GAP, BIRD_X, COL_W } from '../src/common/game.js'

function seq(vals) { let i = 0; return () => vals[i++ % vals.length] }

// 1. Bez dotknięć świetlik spada i gra się kończy.
{
  const G = createGame(seq([0.5]))
  G.tap()
  let ev = null, t = 0
  while (G.g.state === 'play' && t < 5) { ev = G.step(0.04); t += 0.04 }
  assert.equal(G.g.state, 'over')
  assert.equal(ev, 'crash')
}

// 2. Bot, który trzyma się środka szczeliny, zdobywa punkty.
{
  const G = createGame(seq([0.3, 0.7, 0.5, 0.1, 0.9]))
  G.tap()
  let t = 0, points = 0
  while (G.g.state === 'play' && t < 60) {
    const next = G.g.cols
      .filter(c => c.x + COL_W >= BIRD_X - 10)
      .sort((a, b) => a.x - b.x)[0]
    const target = next.gap + GAP / 2 + 18
    if (G.g.y + BIRD_H / 2 > target && G.g.v > 0) G.tap()
    if (G.step(0.03) === 'point') points++
    t += 0.03
  }
  assert.ok(points >= 20, 'bot zdobył tylko ' + points)
  assert.equal(points, G.g.score)
  console.log('bot: ' + points + ' pkt w ' + t.toFixed(0) + ' s, stan ' + G.g.state)
}

// 3. Duży skok czasu jest obcinany (brak przelotu przez kolumnę).
{
  const G = createGame(seq([0.5]))
  G.tap()
  const y0 = G.g.y
  G.step(5)
  assert.ok(G.g.y - y0 < 60)
}

// 4. Reset wraca do stanu startowego.
{
  const G = createGame()
  G.tap(); for (let i = 0; i < 200; i++) G.step(0.04)
  G.reset()
  assert.equal(G.g.state, 'ready'); assert.equal(G.g.score, 0)
  assert.ok(Math.abs(G.g.y - (H / 2 - BIRD_H / 2)) < 1)
}
console.log('testy OK')
