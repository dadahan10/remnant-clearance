// Checks the pure data/price logic in index.html against the live sheet.
// Run: node build/test_render.mjs      (from repo root)
import assert from 'assert'
import fs from 'fs'

// Pull the pure helpers straight out of the page so the test can never drift from it.
const page = fs.readFileSync('index.html', 'utf8')
const slice = page.slice(page.indexOf('function parseCSV'), page.indexOf('/* ============ render'))
let cur = 'usd'
const FX = 3.3, VAT = 1.18
const { parseCSV, col, imgs, priceIn, discount } =
  new Function('FX', 'VAT', 'getCur', slice +
    '\n const cur_ = getCur; Object.defineProperty(globalThis,"cur",{get:getCur,configurable:true});' +
    '\n return {parseCSV,col,imgs,priceIn,discount};')(FX, VAT, () => cur)

const CSV = page.match(/const CSV_URL = "([^"]+)"/)[1]
const rows = parseCSV(await (await fetch(CSV, { cache: 'no-store' })).text())
const byJ = j => rows.find(r => r.j_number === j)

// 1. comma-pasted image URLs are recovered instead of silently dropped
const j286 = byJ('J286')
assert.equal(imgs(j286).length, 3, 'J286 should recover all 3 comma-pasted photos, got ' + imgs(j286).length)
assert.ok(imgs(j286).every(u => /^https?:/.test(u)), 'every recovered image must be a URL')

// 2. no row leaks an unnamed column
assert.ok(rows.every(r => !('' in r)), 'unnamed spill column must be folded away')

// 3. pipe-separated images still work
assert.ok(imgs(byJ('J1122') || rows.find(r => (r.images || '').includes('|'))).length > 1, 'pipe-separated still splits')

// 4. price: USD unchanged, ILS derived, discount % consistent across currencies
const p = rows.find(r => r.price_usd && r.was_usd && discount(r) > 0)
cur = 'usd'; assert.equal(priceIn(p, 'now'), '$' + Math.round(+p.price_usd).toLocaleString('en-US'))
cur = 'ils'; assert.equal(priceIn(p, 'now'), '₪' + Math.round(+p.price_usd * FX * VAT).toLocaleString('en-US'))

// 5. a manual ₪ overrides the computed one AND scales "was" so the % still holds
// strip whatever the sheet already holds so the injected override is the only one
const bare = Object.fromEntries(Object.entries(p).filter(([k]) => !/price\s*ils/i.test(k)))
const manual = { ...bare, 'PRice ILS': '29200' }
cur = 'ils'
assert.equal(priceIn(manual, 'now'), '₪29,200', 'manual ₪ must win')
const was = +priceIn(manual, 'was').replace(/[₪,]/g, '')
assert.equal(Math.round((was - 29200) / was * 100), discount(p), 'discount % must survive the manual override')

// 6. loose header lookup tolerates however the header gets hand-typed
for (const h of ['PRice ILS', 'price_ils', 'Price ILS', 'priceils', 'PRICE-ILS'])
  assert.equal(col({ ...bare, [h]: '29200' }, 'priceils'), '29200', 'header spelling not tolerated: ' + h)
assert.equal(col(p, 'nosuchcolumn'), '', 'missing column reads as empty, not undefined')

// 7. the three columns Daniel added in the sheet are actually reachable by the page
for (const [header, lookup] of [['Size', 'size'], ['Price ILS', 'priceils'], ['NOtes', 'notes']]) {
  assert.ok(Object.keys(rows[0]).includes(header), `sheet column "${header}" is missing`)
  assert.equal(col({ ...rows[0], [header]: 'x' }, lookup), 'x', `"${header}" not reachable as ${lookup}`)
}

console.log(`ok — ${rows.length} rows, ${rows.filter(r => (r.show || '').toUpperCase() !== 'FALSE').length} shown, J286 photos: ${imgs(j286).length}`)
