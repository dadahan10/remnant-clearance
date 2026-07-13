# -*- coding: utf-8 -*-
"""
One-time seed: merge the existing embedded DATA (Supabase inventory + Shopify images
+ computed prices, from the 12.7 build) with Shopify metafields (short_title + clean
details line) that were pulled 13.7, into data.csv — the bootstrap source for the page.

ponytail: Shopify metafields are hardcoded below (pulled once via MCP), not re-fetched.
This runs ONCE to bootstrap the sheet; after that the Google Sheet is the living source.
"""
import json, re, csv, io, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# --- Shopify metafields (custom.*) per J, pulled 13.7 via graphql. short_title cleaned. ---
# [short_title, total_carat_weight, main_shape, diamond_type_raw]
META = {
 "J1122": ["Portal",         "5.78", "Cushion",  "NATURAL DIAMOND"],
 "J1135": ["Accretion Disc", "0.6",  "Emerald",  "NATURAL DIAMOND"],
 "J1139": ["Mystery Soirée", "1.62", "Oval",     "NATURAL DIAMOND"],
 "J1144": ["Astralis",       "",     "",         ""],                # plain gold earring
 "J1148": ["Étoile",         "1",    "",         "NATURAL DIAMOND"],
 "J1334": ["Alma Negra",     "1.15", "Round",    "NATURAL DIAMOND"],
 "J1335": ["Moonlit Abyss",  "0.7",  "",         "NATURAL DIAMOND"],
 "J1411": ["Kitana",         "2.2",  "Emerald",  "NATURAL DIAMOND"],
 "J1412": ["Malagasy",       "0.33", "",         "NATURAL DIAMOND"],
 "J1417": ["Alnilam",        "1",    "",         "NATURAL DIAMOND"],
 "J1511": ["Ulyana",         "2.2",  "Oval",     "NATURAL DIAMOND"],
 "J1594": ["Whiteflash",     "1",    "",         "NATURAL DIAMOND"],
 "J789":  ["Whiteflash",     "1",    "",         "NATURAL DIAMOND"],
 "J282":  ["Boötes",         "3.1",  "Oval",     "NATURAL DIAMOND"],
 "J286":  ["Evening Light",  "2.06", "Radiant",  "NATURAL DIAMOND"],
 "J858":  ["Orion's Belt",   "4.74", "",         "LAB GROWN DIAMOND"],
 "J910":  ["Fractals",       "0.95", "Mixed",    "NATURAL DIAMOND"],
 "J972":  ["Waxing Gibbous", "2.86", "Oval",     "NATURAL DIAMOND"],
 "J984":  ["Triangulum",     "2.30", "Triangle", "NATURAL DIAMOND"],
 "J986":  ["Univers's Eye",  "2.1",  "Marquise", "NATURAL DIAMOND"],
}
# J -> Shopify product handle (for site_link). test-product match for J020 dropped (junk).
site_match = json.load(open(os.path.join(HERE, "site_match.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(HERE, "site_match.json")) else {}
HANDLE = {j: m["handle"] for j, m in site_match.items()
          if m.get("handle") and m["handle"] != "test-product"}

def norm_type(raw):
    r = (raw or "").strip().upper()
    if r == "NATURAL DIAMOND": return "Natural Diamond"
    if r == "LAB GROWN DIAMOND": return "Lab Grown Diamond"
    return ""

def parse_center(center):
    """'2.44ct Round Natural Black Diamond' -> (carats, shape). Fallback for unmatched."""
    if not center: return "", ""
    m = re.match(r"\s*([\d.]+)\s*ct\s+(\S+)", center)
    if m: return m.group(1), m.group(2)
    return "", ""

# --- pull the embedded DATA array out of index.html ---
html = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
m = re.search(r"const DATA=(\[.*?\]);", html, re.S)
if not m:
    sys.exit("could not find embedded DATA in index.html")
DATA = json.loads(m.group(1))

COLS = ["j_number","show","short_title","name","type","carats","shape",
        "diamond_type","karat","gold_color","was_usd","price_usd","site_link","images"]

rows = []
for it in DATA:
    j = it["j"]
    meta = META.get(j)
    if meta:
        st, carats, shape, dtype = meta[0], meta[1], meta[2], norm_type(meta[3])
    else:
        st = ""                                   # unmatched -> Daniel fills short_title
        carats, shape = parse_center(it.get("center"))
        dtype = "Natural Diamond" if (it.get("center") or it.get("side_count")) else ""
    karat = re.sub(r"[YWR]$", "", it.get("karat") or "")   # 14KY -> 14K
    link = "https://dianarafael.com/products/" + HANDLE[j] if j in HANDLE else ""
    rows.append({
        "j_number": j,
        "show": "TRUE",
        "short_title": st,
        "name": it.get("name",""),               # fallback title until short_title filled
        "type": it.get("type",""),
        "carats": carats,
        "shape": shape,
        "diamond_type": dtype,
        "karat": karat,
        "gold_color": it.get("gold_color",""),
        "was_usd": "" if it.get("was_usd") in (None,"") else round(it["was_usd"]),
        "price_usd": "" if it.get("usd") in (None,"") else it["usd"],
        "site_link": link,
        "images": "|".join(it.get("images") or []),
    })

out = os.path.join(REPO, "data.csv")
with io.open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)

# --- summary ---
matched = sum(1 for r in rows if r["short_title"])
withpx  = sum(1 for r in rows if r["price_usd"])
withimg = sum(1 for r in rows if r["images"])
print(f"wrote {out}: {len(rows)} rows")
print(f"  short_title filled: {matched}/{len(rows)}  (blank ones fall back to 'name')")
print(f"  price_usd filled:   {withpx}/{len(rows)}")
print(f"  images present:     {withimg}/{len(rows)}  (blank -> 'photo coming soon')")
print("  no short_title:", ", ".join(r["j_number"] for r in rows if not r["short_title"]))
print("  no price:      ", ", ".join(r["j_number"] for r in rows if not r["price_usd"]))
