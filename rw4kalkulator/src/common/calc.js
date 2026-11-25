// Logika kalkulatora (czysty JS, bez API systemowych).
// Stan: bieżący wpis (cur), akumulator (acc), oczekujący operator (op).

const MAX_LEN = 12

const SYM = { '+': '+', '-': '-', '*': '×', '/': '÷' }

export function fit(n) {
  if (!isFinite(n)) return null
  if (n === 0) return '0'
  for (let p = 12; p >= 1; p--) {
    let s = String(parseFloat(n.toPrecision(p)))
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

function apply(a, op, b) {
  switch (op) {
    case '+': return a + b
    case '-': return a - b
    case '*': return a * b
    case '/': return b === 0 ? NaN : a / b
  }
  return b
}

export function createCalc() {
  const s = {
    cur: '0',
    acc: null,
    op: null,
    fresh: true,
    err: false,
    expr: '',
    lastOp: null,
    lastB: null
  }

  function reset() {
    s.cur = '0'; s.acc = null; s.op = null; s.fresh = true
    s.err = false; s.expr = ''; s.lastOp = null; s.lastB = null
  }

  function setResult(n) {
    const t = fit(n)
    if (t === null) {
      reset()
      s.err = true
      s.cur = 'Error'
      return false
    }
    s.cur = t
    return true
  }

  function digit(d) {
    if (s.fresh) {
      s.cur = d
      s.fresh = false
      if (s.op === null) s.expr = ''
      return
    }
    if (s.cur === '0') { s.cur = d; return }
    if (s.cur === '-0') { s.cur = '-' + d; return }
    if (s.cur.length < MAX_LEN) s.cur += d
  }

  function dot() {
    if (s.fresh) {
      s.cur = '0.'
      s.fresh = false
      if (s.op === null) s.expr = ''
      return
    }
    if (s.cur.indexOf('.') < 0 && s.cur.length < MAX_LEN) s.cur += '.'
  }

  function operator(o) {
    if (s.op !== null && !s.fresh) {
      const a = s.acc
      if (!setResult(apply(a, s.op, parseFloat(s.cur)))) return
    }
    if (s.op === null || !s.fresh) s.acc = parseFloat(s.cur)
    s.op = o
    s.fresh = true
    s.lastOp = null
    s.expr = s.cur + ' ' + SYM[o]
  }

  function equals() {
    if (s.op !== null) {
      const a = s.acc
      const b = s.fresh ? a : parseFloat(s.cur)
      const op = s.op
      const exprA = fit(a)
      const exprB = fit(b)
      s.op = null
      s.acc = null
      s.fresh = true
      if (!setResult(apply(a, op, b))) return
      s.lastOp = op
      s.lastB = b
      s.expr = exprA + ' ' + SYM[op] + ' ' + exprB + ' ='
    } else if (s.lastOp !== null) {
      const a = parseFloat(s.cur)
      const op = s.lastOp
      const b = s.lastB
      const exprA = s.cur
      if (!setResult(apply(a, op, b))) return
      s.lastOp = op
      s.lastB = b
      s.fresh = true
      s.expr = exprA + ' ' + SYM[op] + ' ' + fit(b) + ' ='
    } else {
      s.fresh = true
    }
  }

  function negate() {
    if (s.fresh && s.op !== null) {
      s.cur = '-0'
      s.fresh = false
      return
    }
    if (s.cur.charAt(0) === '-') s.cur = s.cur.slice(1)
    else if (s.cur.length < MAX_LEN) s.cur = '-' + s.cur
  }

  function percent() {
    const v = parseFloat(s.cur)
    let r
    if (s.op !== null && s.acc !== null && (s.op === '+' || s.op === '-')) {
      r = s.acc * v / 100
    } else {
      r = v / 100
    }
    if (setResult(r)) s.fresh = s.op === null ? true : false
  }

  function backspace() {
    if (s.fresh) return
    let c = s.cur.slice(0, -1)
    if (c === '' || c === '-') c = '0'
    s.cur = c
  }

  function press(k) {
    if (s.err) {
      reset()
      if (k === 'C' || k === 'back') return
    }
    if (k >= '0' && k <= '9' && k.length === 1) digit(k)
    else if (k === '.') dot()
    else if (k === '+' || k === '-' || k === '*' || k === '/') operator(k)
    else if (k === '=') equals()
    else if (k === 'C') reset()
    else if (k === 'neg') negate()
    else if (k === '%') percent()
    else if (k === 'back') backspace()
  }

  return {
    press,
    get display() { return s.cur },
    get expr() { return s.expr }
  }
}
