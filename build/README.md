# REMNANT Archive Clearance — data pipeline

Two pages (EN `/`, HE `/he/`) render from **one CSV**: `../data.csv`.

## The living source
`data.csv` is the bootstrap. To edit prices / fill missing data **from any machine without a rebuild**,
import it into a Google Sheet and publish that sheet as CSV, then point the pages at it:

1. Google Sheets → **File → Import → Upload** `data.csv` → *Replace spreadsheet*.
2. **File → Share → Publish to web** → choose the sheet → format **CSV** → Publish.
3. Copy the published URL and paste it into `CSV_URL` at the top of **both** `index.html` and `he/index.html`
   (replace `BASE+"data.csv"`). Commit + push. Done — from then on, editing the sheet updates the site on refresh.

## Columns (edit these in the sheet)
| column | meaning |
|---|---|
| `show` | **for sale?** `TRUE` = shown, `FALSE` = hidden (use for pieces you don't want to sell) |
| `short_title` | the display name (e.g. *Ulyana*). Blank → falls back to `name`. |
| `carats`,`shape`,`diamond_type` | the clean details line. English canonical values; the HE page auto-translates. |
| `was_usd`,`price_usd` | anchor price + clearance price (USD). Discount % is computed. Blank `price_usd` → "Price on request". |
| `site_link`,`images` | dianarafael.com link + `|`-separated image URLs. Blank images → "photo coming soon". |

Prices/₪ derive on the page: `₪ = USD × FX × VAT` (FX=3.3, VAT=1.18 — knobs at top of each page).
**Do not** put cost/margin in this sheet — it is publicly fetchable. Keep costs in the private `cost_table.html`.

## Re-seed (rarely)
`python build/seed_sheet.py` rebuilds `data.csv` from the embedded inventory + hardcoded Shopify metafields.
One-time bootstrap only; the Google Sheet is the living source after step 3 above.
