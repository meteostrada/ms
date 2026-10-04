# Guarda tutti i file NOAA di una stessa fascia da 10 minuti: cosa copre ognuno e come si uniscono.
import urllib.request, re, datetime, io, collections
import numpy as np, h5py
B = "https://noaa-enterprise-rainrate-pds.s3.amazonaws.com"
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "MeteoStrada-sonda"}), timeout=120) as f:
        return f.read()
def listing(prefix):
    t = get(f"{B}/?list-type=2&prefix={prefix}").decode()
    return re.findall(r"<Key>([^<]*)</Key>", t), [int(x) for x in re.findall(r"<Size>(\d+)</Size>", t)]
now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=45)
prefix = f"BLEND/RainRate-Blend-INST/{now:%Y/%m/%d/%H}/"
keys, sizes = listing(prefix)
print("cartella", prefix, "file:", len(keys))
slices = collections.defaultdict(list)
for k, sz in zip(keys, sizes):
    m = re.search(r"GLB-?(\d*)_v1r1_blend_s(\d{13})", k)
    slices[m.group(2) if m else "?"].append((k, sz))
for s in sorted(slices):
    print(" fascia", s, [(re.search(r"GLB-?(\d*)_", k).group(0), sz // 1024) for k, sz in slices[s]])
pick = sorted(slices)[len(slices) // 2]
print("scelta", pick)
lat = lambda r: 70 - r * 0.02
lon = lambda c: -180 + c * 0.02
union = None
for k, sz in slices[pick]:
    with h5py.File(io.BytesIO(get(f"{B}/{k}"))) as f:
        a = f["RRQPE"][:]; dq = f["DQF"][:]
    valid = a != -9990
    rows = np.where(valid.any(axis=1))[0]; cols = np.where(valid.any(axis=0))[0]
    print(k.split("/")[-1][:40], "valido", f"{valid.mean():.1%}", "pioggia>0.3:", int(((a * 0.1) > 0.3).sum()), "max", a[valid].max() * 0.1 if valid.any() else None)
    if valid.any():
        print("   lat", f"{lat(rows.max()):.1f}..{lat(rows.min()):.1f}", "lon", f"{lon(cols.min()):.1f}..{lon(cols.max()):.1f}")
        for name, (la, lo) in {"Atene": (37.98, 23.73), "Istanbul": (41.0, 29.0), "Tunisi": (36.8, 10.2), "Roma": (41.9, 12.5), "Pavia": (45.2, 9.15), "Cairo": (30.0, 31.2), "Mumbai": (19.1, 72.9), "Tokyo": (35.7, 139.7), "NewYork": (40.7, -74.0), "SaoPaulo": (-23.5, -46.6), "Sydney": (-33.9, 151.2), "Johannesburg": (-26.2, 28.0)}.items():
            r, c = int(round((70 - la) / 0.02)), int(round((lo + 180) / 0.02))
            print(f"     {name}: {'sì' if valid[r, c] else 'no'}", end="")
        print()
    union = valid if union is None else (union | valid)
print("unione valida", f"{union.mean():.1%}")
