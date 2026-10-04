"""Trasforma il composito radar europeo OPERA (riflettività, 1 km, LAEA) in tessere web (Web Mercator,
livello 7, 256x256), nello stesso schema delle tessere del radar italiano, per il sito.

Uso: python3 opera_tiles.py CARTELLA_USCITA [NUMERO_FOTO]
Se la cartella contiene già foto convertite (segnate con .done) non le rifà: converte solo le nuove e
toglie quelle vecchie. Se OPERA non risponde lascia tutto com'è.

Per ogni foto (una ogni 5 minuti) scrive CARTELLA/AAAAMMGGTHHMM/7/x/y.png:
  rosso=verde=blu = codifica della pioggia: v = 255 * sqrt(mm/h / 100)   (mm/h = (v/255)^2 * 100)
  alfa = 255 dove il radar vede (anche se non piove), 0 fuori dalla copertura.
E CARTELLA/latest.json con l'elenco delle foto.
Dati OPERA: EUMETNET, CC BY 4.0.
"""
import sys, os, io, json, math, time, datetime, shutil, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np, h5py
from PIL import Image
from pyproj import Transformer
from scipy.ndimage import map_coordinates

BASE = "https://s3.waw3-1.cloudferro.com/openradar-24h"
STEP = 5
Z = 7
SHIFT_DB = 6.0
NODATA_BELOW = -9_000_000
NOECHO_BELOW = -8_000_000
out_dir = sys.argv[1]
n_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 13
t_start = time.time()

def url(t):
    return f"{BASE}/{t:%Y/%m/%d}/OPERA/COMP/OPERA@{t:%Y%m%dT%H%M}@0@DBZH.h5"

def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "MeteoStrada-sito"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def find_latest():
    now = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
    t = now.replace(minute=now.minute // STEP * STEP)
    for _ in range(12):
        try:
            req = urllib.request.Request(url(t), method="HEAD", headers={"User-Agent": "MeteoStrada-sito"})
            urllib.request.urlopen(req, timeout=30).close()
            return t
        except Exception:
            t -= datetime.timedelta(minutes=STEP)
    return None

def load(t):
    b = get(url(t))
    with h5py.File(io.BytesIO(b)) as f:
        return f["dataset1"]["data1"]["data"][:].astype(np.float32)

def to_rain(dbz):
    """dBZ -> mm/h (Marshall-Palmer, meno SHIFT_DB), None-> nan fuori copertura."""
    covered = dbz > NODATA_BELOW
    rain = np.zeros(dbz.shape, np.float32)
    echo = dbz > NOECHO_BELOW
    rain[echo] = ((10 ** ((dbz[echo] - SHIFT_DB) / 10)) / 200) ** (1 / 1.6)
    rain[~covered] = 0
    return rain, covered

def despeckle(rain, covered):
    """Un punto molto forte (>=30 mm/h) circondato da pioggia debole o dal nulla e' un'antenna, non un temporale."""
    strong = rain >= 30
    if not strong.any():
        return rain
    ys, xs = np.where(strong)
    ys, xs = ys[(ys > 0) & (ys < rain.shape[0] - 1) & (xs > 0) & (xs < rain.shape[1] - 1)], xs[(ys > 0) & (ys < rain.shape[0] - 1) & (xs > 0) & (xs < rain.shape[1] - 1)]
    fixed = rain.copy(); n = 0
    for y, x in zip(ys, xs):
        nb = rain[y - 1:y + 2, x - 1:x + 2].ravel()
        cv = covered[y - 1:y + 2, x - 1:x + 2].ravel()
        nb = np.delete(nb, 4); cv = np.delete(cv, 4)
        weak = int(((nb < 2.5) | ~cv).sum())
        if weak >= 6:
            fixed[y, x] = np.median(nb); n += 1
    print("  echi isolati tolti:", n)
    return fixed

# ---- griglia di uscita: tutte le tessere del livello 7 che toccano l'Europa
def tile_range():
    n = 2 ** Z
    def tx(lon): return int(math.floor((lon + 180) / 360 * n))
    def ty(lat):
        la = math.radians(lat)
        return int(math.floor((1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n))
    return tx(-25), tx(50), ty(72), ty(30)
X0, X1, Y0, Y1 = tile_range()
to_laea = Transformer.from_crs("EPSG:4326", "+proj=laea +lat_0=55 +lon_0=10 +x_0=1950000 +y_0=-2100000 +ellps=WGS84 +units=m", always_xy=True)
NG = 256 * 2 ** Z

def tile_coords(x, y):
    px = x * 256 + (np.arange(256) + 0.5)
    py = y * 256 + (np.arange(256) + 0.5)
    lon = px / NG * 360 - 180
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * py / NG))))
    LON, LAT = np.meshgrid(lon, lat)
    gx, gy = to_laea.transform(LON.ravel(), LAT.ravel())
    return (gy * -1 / 1000 - 0.5).reshape(256, 256), (gx / 1000 - 0.5).reshape(256, 256)  # riga, colonna (in celle)

# le coordinate non cambiano da una foto all'altra: si calcolano una volta
COORDS = {}
def coords(x, y):
    if (x, y) not in COORDS:
        COORDS[(x, y)] = tile_coords(x, y)
    return COORDS[(x, y)]

def make_tiles(t, rain, covered):
    name = f"{t:%Y%m%dT%H%M}"
    count = 0; size = 0
    cov = covered.astype(np.float32)
    H, W = rain.shape
    for x in range(X0, X1 + 1):
        for y in range(Y0, Y1 + 1):
            r, c = coords(x, y)
            if r.max() < 0 or c.max() < 0 or r.min() > H - 1 or c.min() > W - 1:
                continue
            cv = map_coordinates(cov, [r, c], order=1, mode="constant", cval=0.0)
            if not (cv > 0.5).any():
                continue
            v = map_coordinates(rain, [r, c], order=1, mode="nearest")
            v = np.clip(v, 0, 100)
            code = np.rint(np.sqrt(v / 100) * 255).astype(np.uint8)
            alpha = np.where(cv > 0.5, 255, 0).astype(np.uint8)
            code = np.where(alpha > 0, code, 0).astype(np.uint8)
            img = np.dstack([code, code, code, alpha])
            d = os.path.join(out_dir, name, str(Z), str(x)); os.makedirs(d, exist_ok=True)
            p = os.path.join(d, f"{y}.png")
            Image.fromarray(img, "RGBA").save(p, optimize=True)
            count += 1; size += os.path.getsize(p)
    open(os.path.join(out_dir, name, ".done"), "w").close()
    return name, count, size

os.makedirs(out_dir, exist_ok=True)
latest = find_latest()
if latest is None:
    print("OPERA non raggiungibile: resta l'ultimo stato pubblicato")
    sys.exit(0)
times = [latest - datetime.timedelta(minutes=STEP * k) for k in range(n_frames)][::-1]
wanted = {f"{t:%Y%m%dT%H%M}" for t in times}
for d in os.listdir(out_dir):
    if d[:1].isdigit() and d not in wanted:
        shutil.rmtree(os.path.join(out_dir, d), ignore_errors=True)
todo = [t for t in times if not os.path.exists(os.path.join(out_dir, f"{t:%Y%m%dT%H%M}", ".done"))]
print("foto:", times[0], "->", times[-1], "- da convertire:", len(todo))
with ThreadPoolExecutor(3) as ex:
    futures = [(t, ex.submit(load, t)) for t in todo]
    for t, f in futures:
        try:
            dbz = f.result()
        except Exception as e:
            print(" manca", t, e); continue
        rain, covered = to_rain(dbz)
        rain = despeckle(rain, covered)
        name, cnt, size = make_tiles(t, rain, covered)
        print(f" {name}: {cnt} tessere, {size/1024:.0f} KB, pioggia>=0.3mm/h: {(rain>=0.3).sum()} celle")

frames = [t for t in times if os.path.exists(os.path.join(out_dir, f"{t:%Y%m%dT%H%M}", ".done"))]
tiles = []
if frames:
    root = os.path.join(out_dir, f"{frames[-1]:%Y%m%dT%H%M}", str(Z))
    for x in os.listdir(root):
        for y in os.listdir(os.path.join(root, x)):
            tiles.append(f"{x}/{y[:-4]}")
json.dump({"step": STEP * 60, "zoom": Z, "encoding": "sqrt", "frames": [t.strftime("%Y-%m-%dT%H:%M:00Z") for t in frames], "tiles": tiles,
           "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
          open(os.path.join(out_dir, "latest.json"), "w"))
print(f"fatto in {time.time()-t_start:.0f} s: {len(frames)} foto, {len(tiles)} tessere")
