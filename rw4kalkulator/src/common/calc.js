// Logika kalkulatora naukowego (czysty JS, bez API systemowych).
// Wpisywane jest całe wyrażenie (tokeny), liczone dopiero przy "=".
// Obsługa: + − × ÷, nawiasy, potęgi (^ i ²), pierwiastek √, procent %,
// silnia !, π, 1/x, Ans (ostatni wynik), mnożenie domyślne: 2π, 3(4), 2√(9).

const MAX_LEN = 12
const MAX_TOKENS = 64

export function fit(n) {
  if (typeof n !== 'number' || !isFinite(n)) return null
  if (n === 0) return '0'
  for (let p = 12; p >= 1; p--) {
    const s = String(parseFloat(n.toPrecision(p)))
    if (s.length <= MAX_LEN) return s
  }
  for (let p = 10; p >= 0; p--) {
    const parts = n.toExponential(p).split('e')
    let m = parts[0]
    if (m.indexOf('.') >= 0) m = m.replace(/0+$/, '').replace(/\.$/, '')
    const s = m + 'e' + parts[1].replace('+', '')
    if (s.length <= MAX_LEN) return s
  }
  return null
}

function factorial(n) {
  if (n < 0 || n > 170 || Math.floor(n) !== n) return NaN
  let r = 1
  for (let i = 2; i <= n; i++) r *= i
  return r
}

// Tokeny: '0'-'9', '.', '+', '−', '×', '÷', '^', '(', ')', '√(', '1÷(',
// '²', '!', '%', 'π', oraz '#<liczba>' (wynik / Ans).
const OPEN = { '(': 1, '√(': 1, '1÷(': 1 }
const POSTFIX = { '²': 1, '!': 1, '%': 1 }

function isDigit(t) {
  return (t >= '0' && t <= '9' && t.length === 1) || t === '.'
}

// Zamienia tokeny na listę elementów dla parsera (scala cyfry w liczby,
// zamyka brakujące nawiasy, wstawia mnożenie domyślne).
function lex(tokens) {
  const out = []
  let num = ''
  let depth = 0
  function flushNum() {
    if (num === '') return true
    if (num === '.' || num.split('.').length > 2) return false
    out.push({ k: 'n', v: parseFloat(num) })
    num = ''
    return true
  }
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i]
    if (isDigit(t)) { num += t; continue }
    if (!flushNum()) return null
    if (t.charAt(0) === '#') out.push({ k: 'n', v: parseFloat(t.slice(1)) })
    else if (t === 'π') out.push({ k: 'n', v: Math.PI })
    else if (OPEN[t]) { out.push({ k: 'open', f: t }); depth++ }
    else if (t === ')') {
      if (depth === 0) return null
      out.push({ k: 'close' }); depth--
    } else out.push({ k: 'op', v: t })
  }
  if (!flushNum()) return null
  while (depth-- > 0) out.push({ k: 'close' })
  // mnożenie domyślne
  const res = []
  for (let i = 0; i < out.length; i++) {
    const a = res[res.length - 1]
    const b = out[i]
    const aEnds = a && (a.k === 'n' || a.k === 'close' || (a.k === 'op' && POSTFIX[a.v]))
    const bStarts = b.k === 'n' || b.k === 'open'
    if (aEnds && bStarts) res.push({ k: 'op', v: '×' })
    res.push(b)
  }
  return res
}

export function evaluate(tokens) {
  const items = lex(tokens)
  if (!items || items.length === 0) return NaN
  let pos = 0
  const peek = () => items[pos]
  const isOp = (v) => peek() && peek().k === 'op' && peek().v === v

  function expr() {
    let r = term()
    let left = r.v
    while (isOp('+') || isOp('−')) {
      const op = items[pos++].v
      const rt = term()
      // a + b%  =>  a + a·b/100
      const rv = rt.pct ? left * rt.v : rt.v
      left = op === '+' ? left + rv : left - rv
    }
    return { v: left }
  }

  function term() {
    let f = unary()
    let v = f.v
    let pct = f.pct
    while (isOp('×') || isOp('÷')) {
      const op = items[pos++].v
      const g = unary()
      v = op === '×' ? v * g.v : (g.v === 0 ? NaN : v / g.v)
      pct = false
    }
    return { v: v, pct: pct }
  }

  function unary() {
    if (isOp('−')) { pos++; const u = unary(); return { v: -u.v, pct: u.pct } }
    if (isOp('+')) { pos++; return unary() }
    return power()
  }

  function power() {
    const b = postfix()
    if (isOp('^')) {
      pos++
      const e = unary()
      return { v: Math.pow(b.v, e.v), pct: false }
    }
    return b
  }

  function postfix() {
    let v = primary()
    let pct = false
    while (peek() && peek().k === 'op' && POSTFIX[peek().v]) {
      const op = items[pos++].v
      if (op === '²') v = v * v
      else if (op === '!') v = factorial(v)
      else { v = v / 100; pct = true }
    }
    return { v: v, pct: pct }
  }

  function primary() {
    const t = items[pos++]
    if (!t) throw new Error('end')
    if (t.k === 'n') return t.v
    if (t.k === 'open') {
      const v = expr().v
      if (!peek() || peek().k !== 'close') throw new Error('paren')
      pos++
      if (t.f === '√(') return v < 0 ? NaN : Math.sqrt(v)
      if (t.f === '1÷(') return v === 0 ? NaN : 1 / v
      return v
    }
    throw new Error('unexpected')
  }

  try {
    const r = expr().v
    if (pos !== items.length) return NaN
    return r
  } catch (e) {
    return NaN
  }
}

export function createCalc() {
  const s = {
    tokens: [],
    ans: 0,
    done: false, // po "=": wynik na ekranie
    err: false,
    lastExpr: ''
  }

  function text(tokens) {
    let out = ''
    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i]
      out += t.charAt(0) === '#' ? t.slice(1).replace(/-/g, '−') : t
    }
    return out
  }

  function startsValue(k) {
    return isDigit(k) || k === 'π' || OPEN[k] || k === 'ans'
  }

  function push(t) {
    if (s.tokens.length < MAX_TOKENS) s.tokens.push(t)
  }

  function ansToken(v) {
    return '#' + fit(v)
  }

  function press(k) {
    if (s.err) {
      s.err = false
      s.tokens = []
      s.done = false
      if (k === 'C' || k === 'back') return
    }
    if (s.done) {
      s.done = false
      if (k === '=') { s.done = true; return }
      if (startsValue(k)) s.tokens = []
      else if (k === 'back' || k === 'C') { s.tokens = []; return }
      // operator lub postfiks: kontynuacja z wynikiem
    }
    if (k === 'C') { s.tokens = []; return }
    if (k === 'back') { s.tokens.pop(); return }
    if (k === 'ans') { push(ansToken(s.ans)); return }
    if (k === '=') {
      if (s.tokens.length === 0) return
      const v = evaluate(s.tokens)
      const f = fit(v)
      s.lastExpr = text(s.tokens) + '='
      if (f === null) {
        s.err = true
        return
      }
      s.ans = parseFloat(f)
      s.tokens = ['#' + f]
      s.done = true
      return
    }
    if (k === '.') {
      // nie dopuszczaj dwóch kropek w jednej liczbie
      for (let i = s.tokens.length - 1; i >= 0 && isDigit(s.tokens[i]); i--) {
        if (s.tokens[i] === '.') return
      }
    }
    // dwa operatory z rzędu: zamiana (poza minusem jako znakiem)
    const binary = { '+': 1, '×': 1, '÷': 1, '^': 1 }
    const last = s.tokens[s.tokens.length - 1]
    if (binary[k] && (last === '+' || last === '−' || last === '×' || last === '÷' || last === '^')) {
      s.tokens.pop()
      if (s.tokens.length === 0) return
    }
    if (binary[k] && s.tokens.length === 0) return
    push(k)
  }

  return {
    press,
    // Duża linia: wpisywane wyrażenie albo wynik.
    get display() {
      if (s.err) return 'Error'
      if (s.tokens.length === 0) return '0'
      return text(s.tokens)
    },
    // Mała linia: po "=" całe działanie, w trakcie wpisywania podgląd wyniku.
    get expr() {
      if (s.err || s.done) return s.lastExpr
      if (s.tokens.length < 2) return ''
      const f = fit(evaluate(s.tokens))
      return f === null ? '' : '=' + f.replace(/-/g, '−')
    }
  }
}
