"""Compone il sito in un solo file: mette dentro la mappa di base e indica dove stanno le tessere del radar europeo.
Uso: python3 tools/build_site.py CARTELLA_USCITA"""
import base64, os, sys
out = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b64 = base64.b64encode(open(os.path.join(root, "site", "mappa.bin.gz"), "rb").read()).decode()
w64 = base64.b64encode(open(os.path.join(root, "site", "mondo.bin.gz"), "rb").read()).decode()
s = open(os.path.join(root, "site", "index.src.html"), encoding="utf-8").read()
s = s.replace("/*MAPDATA*/", b64).replace("/*MONDODATA*/", w64).replace("/*EUSNAP*/null", "null").replace('eu: "",', 'eu: "tiles",')
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(s)
open(os.path.join(out, ".nojekyll"), "w").close()
print("sito:", len(s) // 1024, "KB")
