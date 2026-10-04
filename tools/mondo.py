# Mappa di base del mondo per il sito (Natural Earth, pubblico dominio): terre, coste, laghi grandi,
# confini di Stato e città principali, FUORI dall'Europa (lì c'è già la mappa dettagliata dell'app).
# Stesso formato "MSM1" di mappa.bin.gz. Uso: python3 mondo.py CARTELLA_GEOJSON
import gzip, json, sys, os
from shapely.geometry import shape, box, LineString, MultiLineString, Polygon, MultiPolygon, Point
SRC = sys.argv[1]
EU = box(-25, 34, 45, 72)
WORLD = box(-180, -85, 180, 85)
REST = WORLD.difference(EU)

def load(name):
    p = os.path.join(SRC, name + ".geojson")
    if not os.path.exists(p):
        print("MANCA", name); return []
    feats = json.load(open(p, encoding="utf-8"))["features"]
    print(name, len(feats), "elementi")
    return feats
def prop(f, *names, default=None):
    pr = f["properties"]
    for n in names:
        for k in (n, n.lower(), n.upper()):
            if k in pr and pr[k] not in (None, ""): return pr[k]
    return default
def lines_of(g):
    if g.is_empty: return []
    if isinstance(g, LineString): return [g]
    if hasattr(g, "geoms"):
        out = []
        for x in g.geoms: out += lines_of(x)
        return out
    return []
def polys_of(g):
    if g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    if hasattr(g, "geoms"):
        out = []
        for x in g.geoms: out += polys_of(x)
        return out
    return []
layers = {}
def add_polys(lid, feats, tol, min_area):
    out = layers.setdefault(lid, [])
    for f in feats:
        try: g = shape(f["geometry"]).buffer(0).intersection(REST)
        except Exception: continue
        for p in polys_of(g):
            p = p.simplify(tol, preserve_topology=True)
            for pp in polys_of(p):
                if pp.is_empty or pp.area < min_area: continue
                out.append((0, None, [list(pp.exterior.coords)] + [list(r.coords) for r in pp.interiors if Polygon(r).area >= min_area]))
def add_lines(lid, feats, tol):
    out = layers.setdefault(lid, [])
    for f in feats:
        try: g = shape(f["geometry"]).intersection(REST)
        except Exception: continue
        ls = [list(l.simplify(tol).coords) for l in lines_of(g)]
        ls = [l for l in ls if len(l) >= 2]
        if ls: out.append((0, None, ls))
def add_coast(lid, feats, tol):
    out = layers.setdefault(lid, [])
    edge = REST.boundary.buffer(1e-7)
    for f in feats:
        try: g = shape(f["geometry"]).buffer(0).intersection(REST)
        except Exception: continue
        if g.is_empty: continue
        b = g.boundary.difference(edge)
        ls = [list(l.simplify(tol).coords) for l in lines_of(b)]
        ls = [l for l in ls if len(l) >= 2]
        if ls: out.append((0, None, ls))
land = load("ne_50m_land")
add_polys(1, land, 0.03, 2e-3)
add_coast(2, land, 0.03)
add_polys(3, load("ne_50m_lakes"), 0.03, 0.1)
add_lines(5, load("ne_50m_admin_0_boundary_lines_land"), 0.03)

cities = layers.setdefault(9, [])
n = 0
for f in load("ne_10m_populated_places"):
    try: g = shape(f["geometry"])
    except Exception: continue
    if EU.contains(g): continue
    pop = float(prop(f, "POP_MAX", "pop_max", default=0) or 0)
    cap = "capital" in str(prop(f, "FEATURECLA", "featurecla", default="")).lower() and "Admin-0" in str(prop(f, "FEATURECLA", "featurecla", default=""))
    if pop < 250_000 and not cap: continue
    k = 0 if cap else 1 if pop >= 3_000_000 else 2 if pop >= 1_000_000 else 3 if pop >= 500_000 else 4
    name = prop(f, "NAME_IT", "name_it") or prop(f, "NAMEASCII", "nameascii", "NAME", "name", default="?")
    cities.append((k, str(name), [[(g.x, g.y)]])); n += 1
cities.sort(key=lambda c: c[0])
print("città:", n)

def varint(n, out):
    while True:
        b = n & 0x7F; n >>= 7
        if n: out.append(b | 0x80)
        else: out.append(b); return
def zz(n): return (n << 1) ^ (n >> 63)
GEOM = {1: 3, 2: 2, 3: 3, 5: 2, 9: 1}
buf = bytearray(b"MSM1"); buf.append(len(layers)); stats = []
for lid in sorted(layers):
    feats = layers[lid]; start = len(buf)
    buf.append(lid); buf.append(GEOM[lid]); varint(len(feats), buf); npts = 0
    for cls, name, parts in feats:
        buf.append(cls)
        if GEOM[lid] == 1:
            nb = name.encode("utf-8")[:255]; buf.append(len(nb)); buf += nb
        varint(len(parts), buf); px = py = 0
        for part in parts:
            varint(len(part), buf)
            for x, y, *_ in part:
                ix, iy = int(round(x * 1e5)), int(round(y * 1e5))
                varint(zz(ix - px), buf); varint(zz(iy - py), buf); px, py = ix, iy; npts += 1
    stats.append(f"livello {lid}: {len(feats)} elementi, {npts} punti, {len(buf) - start} byte")
gz = gzip.compress(bytes(buf), 9)
open("mondo.bin.gz", "wb").write(gz)
print("\n".join(stats), f"\nTotale: {len(buf)} byte grezzi, {len(gz)} compressi")
