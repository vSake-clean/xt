import assert from 'node:assert/strict'
import { createCalc, evaluate } from '../src/common/calc.js'

function run(keys) {
  const c = createCalc()
  for (const k of keys) c.press(k)
  return c
}
const K = (s) => s.split(' ')

const cases = [
  ['1 2 + 3 =', '15'],
  ['2 + 3 × 4 =', '14'],
  ['( 2 + 3 ) × 4 =', '20'],
  ['( 2 + 3 =', '5'],                 // auto-zamknięcie nawiasu
  ['2 ( 3 + 1 ) =', '8'],             // mnożenie domyślne
  ['0 . 1 + 0 . 2 =', '0.3'],
  ['1 0 ÷ 3 =', '3.3333333333'],
  ['7 ÷ 0 =', 'Error'],
  ['√( 1 6 ) =', '4'],
  ['√( 2 =', '1.4142135624'],
  ['2 √( 9 ) =', '6'],
  ['√( − 4 ) =', 'Error'],
  ['3 ² =', '9'],
  ['2 ^ 1 0 =', '1024'],
  ['2 ^ 3 ^ 2 =', '512'],             // potęga prawostronna
  ['− 2 ^ 2 =', '−4'],
  ['( − 2 ) ^ 2 =', '4'],
  ['5 ! =', '120'],
  ['2 0 0 + 1 0 % =', '220'],
  ['2 0 0 − 1 0 % =', '180'],
  ['5 0 % =', '0.5'],
  ['2 0 0 × 1 0 % =', '20'],
  ['2 π =', '6.2831853072'],
  ['1÷( 4 =', '0.25'],
  ['5 − − 3 =', '8'],
  ['5 + × 3 =', '15'],                // zamiana operatora
  ['1 2 3 back =', '12'],
  ['2 + 3 = × 4 =', '20'],            // kontynuacja wyniku
  ['2 + 3 = 7 =', '7'],               // nowa liczba po wyniku
  ['2 + 3 = ans × 2 =', '10'],
  ['9 = ²', '9²'],
  ['1 . 2 . 3', '1.23'],
  ['1 0 0 0 0 0 0 × 1 0 0 0 0 0 0 0 =', '1e13'],
  ['( ) =', 'Error'],
  ['7 ÷ 0 = 5', '5']
]

let fail = 0
for (const [keys, want] of cases) {
  const got = run(K(keys)).display
  if (got !== want) { fail++; console.log('FAIL', keys, '=>', got, 'expected', want) }
}
assert.equal(run(K('1 2 + 3')).expr, '=15')
assert.equal(run(K('1 2 + 3 =')).expr, '12+3=')
assert.ok(isNaN(evaluate(['+'])))
console.log(fail ? fail + ' failed' : 'all ' + cases.length + ' passed')
process.exit(fail ? 1 : 0)
