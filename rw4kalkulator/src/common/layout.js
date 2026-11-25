// Układ klawiatury zależny od ustawień (czysty JS, testowalny).
// Klawisze podstawowe (cyfry, + − × ÷, =, C, ⌫, .) są zawsze. Klawisze
// naukowe z ustawień trafiają do rzędów nad klawiaturą, a wysokość
// klawiszy dopasowuje się do liczby rzędów.

export const PAD_W = 350
export const PAD_H = 330
export const GAP = 5
const MAX_H = 58

const DIGIT = '#333333'
const FUNC = '#a5a5a5'
const OP = '#ff9500'
const SCI = '#284670'

// Opcje ustawień w kolejności wyświetlania.
export const OPTIONS = [
  { id: 'par', img: 'o_par', keys: [['(', 'lp'], [')', 'rp']] },
  { id: 'sqrt', img: 'o_sqrt', keys: [['√(', 'sqrt']] },
  { id: 'sq', img: 'o_sq', keys: [['²', 'sq']] },
  { id: 'pow', img: 'o_pow', keys: [['^', 'pow']] },
  { id: 'pct', img: 'o_pct', keys: [['%', 'pct']] },
  { id: 'fact', img: 'o_fact', keys: [['!', 'fact']] },
  { id: 'pi', img: 'o_pi', keys: [['π', 'pi']] },
  { id: 'inv', img: 'o_inv', keys: [['1÷(', 'inv']] },
  { id: 'ans', img: 'o_ans', keys: [['ans', 'ans']] },
  { id: 'prev', img: 'o_prev', keys: [] },
  { id: 'vib', img: 'o_vib', keys: [] }
]

export function defaultConfig() {
  const c = {}
  for (let i = 0; i < OPTIONS.length; i++) c[OPTIONS[i].id] = true
  return c
}

export function normalizeConfig(raw) {
  const c = defaultConfig()
  if (raw && typeof raw === 'object') {
    for (const k in c) {
      if (typeof raw[k] === 'boolean') c[k] = raw[k]
    }
  }
  return c
}

const CORE = [
  [['C', 'c', FUNC, 2], ['back', 'back', FUNC], ['÷', 'div', OP]],
  [['7', '7', DIGIT], ['8', '8', DIGIT], ['9', '9', DIGIT], ['×', 'mul', OP]],
  [['4', '4', DIGIT], ['5', '5', DIGIT], ['6', '6', DIGIT], ['−', 'sub', OP]],
  [['1', '1', DIGIT], ['2', '2', DIGIT], ['3', '3', DIGIT], ['+', 'add', OP]],
  [['0', '0', DIGIT], ['.', 'dot', DIGIT], ['=', 'eq', OP, 2]]
]

function rowOf(spec, cols, h) {
  const unit = Math.floor((PAD_W - GAP * (cols - 1)) / cols)
  const row = []
  for (let i = 0; i < spec.length; i++) {
    const s = spec[i]
    const span = s[3] || 1
    row.push({
      k: s[0],
      label: '/common/img/l_' + s[1] + '.png',
      bg: s[2],
      w: unit * span + GAP * (span - 1),
      h: h
    })
  }
  return row
}

export function buildRows(cfg) {
  const sci = []
  for (let i = 0; i < OPTIONS.length; i++) {
    const o = OPTIONS[i]
    if (!cfg[o.id]) continue
    for (let j = 0; j < o.keys.length; j++) {
      sci.push([o.keys[j][0], o.keys[j][1], SCI])
    }
  }
  const sciRows = Math.ceil(sci.length / 5)
  const total = CORE.length + sciRows
  const h = Math.min(MAX_H, Math.floor((PAD_H - GAP * (total - 1)) / total))
  const rows = []
  if (sciRows > 0) {
    const per = Math.ceil(sci.length / sciRows)
    for (let r = 0; r < sciRows; r++) {
      const part = sci.slice(r * per, (r + 1) * per)
      rows.push(rowOf(part, part.length, h))
    }
  }
  for (let r = 0; r < CORE.length; r++) rows.push(rowOf(CORE[r], 4, h))
  return rows
}
