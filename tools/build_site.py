"""Compone il sito in un solo file: mette dentro la mappa di base e indica dove stanno le tessere del radar europeo.
Uso: python3 tools/build_site.py CARTELLA_USCITA"""
import base64, os, sys
out = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b64 = base64.b64encode(open(os.path.join(root, "site", "mappa.bin.gz"), "rb").read()).decode()
w64 = base64.b64encode(open(os.path.join(root, "site", "mondo.bin.gz"), "rb").read()).decode()
s = open(os.path.join(root, "site", "index.src.html"), encoding="utf-8").read()
s = s.replace("/*QRLIB*/", open(os.path.join(root, "site", "qr.js"), encoding="utf-8").read())
s = s.replace("/*MAPDATA*/", b64).replace("/*MONDODATA*/", w64).replace("/*EUSNAP*/null", "null").replace('eu: "",', 'eu: "tiles",').replace('noaa: "",', 'noaa: "noaa",')
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(s)
open(os.path.join(out, ".nojekyll"), "w").close()
print("sito:", len(s) // 1024, "KB")

# --- Informativa privacy: pagina pubblica richiesta da Google Play (testo in site/privacy.md) ---
import html, re
def _inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return re.sub(r"(https?://[^\s<)]+)", r'<a href="\1">\1</a>', t)
body, in_ul = [], False
for line in open(os.path.join(root, "site", "privacy.md"), encoding="utf-8").read().splitlines():
    if line.startswith(">"): continue
    if line.startswith("- "):
        if not in_ul: body.append("<ul>"); in_ul = True
        body.append("<li>" + _inline(line[2:]) + "</li>"); continue
    if in_ul and line.startswith("  ") and line.strip():
        body[-1] = body[-1][:-5] + " " + _inline(line.strip()) + "</li>"; continue
    if in_ul: body.append("</ul>"); in_ul = False
    m = re.match(r"(#{1,3}) (.*)", line)
    if m: body.append("<h%d>%s</h%d>" % (len(m.group(1)), _inline(m.group(2)), len(m.group(1))))
    elif line.strip() == "---": body.append("<hr>")
    elif line.strip(): body.append("<p>" + _inline(line) + "</p>")
if in_ul: body.append("</ul>")
page = ('<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>MeteoStrada - Privacy</title><style>body{font:16px/1.55 system-ui,sans-serif;max-width:46rem;margin:0 auto;padding:1rem 16px 3rem;color:#1a2233}'
        'h1{font-size:1.5rem}h2{margin-top:2rem}h3{margin-top:1.4rem;font-size:1.05rem}a{color:#1b5fb5;word-break:break-all}code{background:#eef1f6;padding:0 .25em;border-radius:3px}'
        '@media(prefers-color-scheme:dark){body{background:#0f1420;color:#e6ebf4}a{color:#8ab8ff}code{background:#1a2233}}</style></head><body>'
        + "\n".join(body) + "</body></html>")
open(os.path.join(out, "privacy.html"), "w", encoding="utf-8").write(page)
print("privacy.html:", len(page) // 1024, "KB")
