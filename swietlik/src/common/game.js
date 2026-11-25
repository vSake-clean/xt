// Logika gry "Świetlik" (czysty JS, bez API systemowych).
// Jednostki: piksele i sekundy. Fizyka liczona od upływu czasu, więc
// prędkość gry nie zależy od liczby klatek na sekundę zegarka.

export const W = 390
export const H = 450
export const COL_W = 64
export const GAP = 150
export const SPACING = 230
export const BIRD_X = 80
export const BIRD_W = 40
export const BIRD_H = 32
const HIT_PAD = 6

const GRAVITY = 1300
const FLAP_V = -400
const MAX_FALL = 520
const SPEED = 115

function randomGapTop(rnd) {
  const min = 60
  const max = H - GAP - 50
  return Math.round(min + rnd() * (max - min))
}

export function createGame(rnd) {
  rnd = rnd || Math.random
  const g = {
    state: 'ready', // ready | play | over
    y: H / 2 - BIRD_H / 2,
    v: 0,
    score: 0,
    cols: [],
    t: 0
  }

  function reset() {
    g.state = 'ready'
    g.y = H / 2 - BIRD_H / 2
    g.v = 0
    g.score = 0
    g.t = 0
    g.cols = [
      { x: W + 40, gap: randomGapTop(rnd), passed: false },
      { x: W + 40 + SPACING, gap: randomGapTop(rnd), passed: false }
    ]
  }

  function hits(c) {
    const bx0 = BIRD_X + HIT_PAD
    const bx1 = BIRD_X + BIRD_W - HIT_PAD
    const by0 = g.y + HIT_PAD
    const by1 = g.y + BIRD_H - HIT_PAD
    if (bx1 <= c.x || bx0 >= c.x + COL_W) return false
    return by0 < c.gap || by1 > c.gap + GAP
  }

  // Zwraca zdarzenia: 'point', 'crash' albo null.
  function step(dt) {
    if (dt > 0.1) dt = 0.1
    if (dt <= 0) return null
    g.t += dt
    if (g.state === 'ready') {
      // Delikatne unoszenie się przed startem.
      g.y = H / 2 - BIRD_H / 2 + Math.sin(g.t * 4) * 8
      return null
    }
    if (g.state !== 'play') return null

    g.v += GRAVITY * dt
    if (g.v > MAX_FALL) g.v = MAX_FALL
    g.y += g.v * dt
    if (g.y < -BIRD_H) g.y = -BIRD_H

    let ev = null
    for (let i = 0; i < g.cols.length; i++) {
      const c = g.cols[i]
      c.x -= SPEED * dt
      if (c.x < -COL_W) {
        c.x += SPACING * g.cols.length
        c.gap = randomGapTop(rnd)
        c.passed = false
      }
      if (!c.passed && c.x + COL_W < BIRD_X) {
        c.passed = true
        g.score++
        ev = 'point'
      }
      if (hits(c)) {
        g.state = 'over'
        return 'crash'
      }
    }
    if (g.y + BIRD_H > H) {
      g.y = H - BIRD_H
      g.state = 'over'
      return 'crash'
    }
    return ev
  }

  // Dotknięcie ekranu. Zwraca true, gdy gra (re)startuje.
  function tap() {
    if (g.state === 'ready') {
      g.state = 'play'
      g.v = FLAP_V
      return true
    }
    if (g.state === 'play') {
      g.v = FLAP_V
      return false
    }
    return false
  }

  reset()
  return { g, step, tap, reset }
}
