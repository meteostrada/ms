"""Pioggia da satellite di tutto il mondo (NOAA/NESDIS Enterprise Rain Rate, 0,02 gradi, latitudini -60..70)
trasformata in tessere web per il sito, nello stesso modo del radar OPERA ma "a macchia": se una tessera non
esiste, in quel punto non piove (dentro la fascia -60..70).

Uso: python3 noaa_tiles.py CARTELLA_USCITA [NUMERO_FOTO]
Una foto ogni 10 minuti, ritardo di circa 30 minuti. Per ogni foto scrive CARTELLA/AAAAMMGGTHHMM/Z/x/y.png
(livelli 6, 5, 4, 3; grigio = 255 * sqrt(mm/h / 100)) e CARTELLA/latest.json.
Dati NOAA, di pubblico dominio (https://registry.opendata.aws/noaa-rain-rate/)."""
import sys, os, io, re, json, math, time, datetime, shutil, urllib.request
import numpy as np, h5py
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piramide

B = "https://noaa-enterprise-rainrate-pds.s3.amazonaws.com"
Z = 6
LAT_MAX, LAT_MIN, RES = 70.0, -60.0, 0.02
out_dir = sys.argv[1]
n_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 7
t0 = time.time()

def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "MeteoStrada-sito"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()

def list_slices(t):
    """{fascia: chiave del file GLB-5 (il completo)} per l'ora di t."""
    t = t.astimezone(datetime.timezone.utc)
    xml = get(f"{B}/?list-type=2&prefix=BLEND/RainRate-Blend-INST/{t:%Y/%m/%d/%H}/").decode()
    out = {}
    for k in re.findall(r"<Key>([^<]*)</Key>", xml):
        m = re.search(r"GLB-5_v1r1_blend_s(\d{12})\d", k)
        if m:
            out[m.group(1)] = k
    return out

def load(key):
    with h5py.File(io.BytesIO(get(f"{B}/{key}"))) as f:
        a = f["RRQPE"][:]
    rain = np.where(a == -9990, 0, np.maximum(a, 0) * 0.1).astype(np.float32)
    return rain

def tiles_for(rain, name):
    """Livello Z: ogni cella di 0,02 gradi -> campionamento bilineare sulla tessera."""
    from scipy.ndimage import map_coordinates
    H, W = rain.shape
    n = 2 ** Z; NG = 256 * n
    count = 0
    ty0 = int(math.floor((1 - math.asinh(math.tan(math.radians(LAT_MAX))) / math.pi) / 2 * n))
    ty1 = int(math.floor((1 - math.asinh(math.tan(math.radians(LAT_MIN))) / math.pi) / 2 * n))
    # le tessere di sinistra e destra non cambiano: si calcolano le colonne di celle una sola volta
    for x in range(n):
        px = x * 256 + (np.arange(256) + 0.5)
        lon = px / NG * 360 - 180
        cc = (lon + 180) / RES - 0.5
        for y in range(ty0, ty1 + 1):
            py = y * 256 + (np.arange(256) + 0.5)
            lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * py / NG))))
            rr = (LAT_MAX - lat) / RES - 0.5
            if rr.max() < 0 or rr.min() > H - 1:
                continue
            r0 = max(int(rr.min()) - 1, 0); r1 = min(int(rr.max()) + 2, H); c0 = max(int(cc.min()) - 1, 0); c1 = min(int(cc.max()) + 2, W)
            sub = rain[r0:r1, c0:c1]
            if sub.max() < 0.3:
                continue
            R, C = np.meshgrid(rr - r0, cc - c0, indexing="ij")
            v = map_coordinates(sub, [R, C], order=1, mode="nearest")
            code = np.rint(np.sqrt(np.clip(v, 0, 100) / 100) * 255).astype(np.uint8)
            code[v < 0.3] = 0
            if not code.any():
                continue
            d = os.path.join(out_dir, name, str(Z), str(x)); os.makedirs(d, exist_ok=True)
            Image.fromarray(code, "L").save(os.path.join(d, f"{y}.png"), optimize=True)
            count += 1
    return count

os.makedirs(out_dir, exist_ok=True)
now = datetime.datetime.now(datetime.timezone.utc)
avail = {}
for back in range(0, 4):
    try:
        avail.update(list_slices(now - datetime.timedelta(hours=back)))
    except Exception as e:
        print("elenco non raggiungibile:", e)
slices = sorted(avail)
if not slices:
    print("NOAA non raggiungibile o vuoto: resta l'ultimo stato pubblicato"); sys.exit(0)
slices = slices[-n_frames:]
names = {s: datetime.datetime.strptime(s, "%Y%m%d%H%M").strftime("%Y%m%dT%H%M") for s in slices}
wanted = set(names.values())
for d in os.listdir(out_dir):
    if d[:1].isdigit() and d not in wanted:
        shutil.rmtree(os.path.join(out_dir, d), ignore_errors=True)
for s in slices:
    nm = names[s]
    if os.path.exists(os.path.join(out_dir, nm, ".done")):
        continue
    try:
        rain = load(avail[s])
    except Exception as e:
        print(" manca", s, e); continue
    cnt = tiles_for(rain, nm)
    extra = piramide.build(os.path.join(out_dir, nm), Z, 4, False)   # 6 -> 5 -> 4 -> 3
    open(os.path.join(out_dir, nm, ".done"), "w").close()
    print(f" {nm}: {cnt} tessere z{Z} + {extra} dei livelli bassi, celle>=0.3mm/h: {(rain >= 0.3).sum()}")
frames = [names[s] for s in slices if os.path.exists(os.path.join(out_dir, names[s], ".done"))]
json.dump({"step": 600, "zoom": Z, "min_zoom": 3, "encoding": "sqrt", "lat": [LAT_MIN, LAT_MAX],
           "frames": [datetime.datetime.strptime(f, "%Y%m%dT%H%M").strftime("%Y-%m-%dT%H:%M:00Z") for f in frames],
           "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
          open(os.path.join(out_dir, "latest.json"), "w"))
print(f"fatto in {time.time()-t0:.0f} s: {len(frames)} foto")
