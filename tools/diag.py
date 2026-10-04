"""Diagnostica: per ogni foto OPERA, quanta parte di alcune tessere (z7) e' coperta dai radar."""
import os, sys, math, glob
import numpy as np
from PIL import Image
d = sys.argv[1]
def tile(lat, lon, z=7):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
pts = {"Barcellona": (41.4, 2.2), "Madrid": (40.4, -3.7), "Valencia": (39.5, -0.4), "Londra": (51.5, -0.1), "Parigi": (48.9, 2.3), "Milano": (45.5, 9.2)}
out = []
for fr in sorted(x for x in os.listdir(d) if x[:1].isdigit()):
    row = []
    for name, (la, lo) in pts.items():
        x, y = tile(la, lo)
        p = os.path.join(d, fr, "7", f"b{x // 4}_{y // 4}.png")
        if not os.path.exists(p):
            row.append(f"{name[:3]}:--"); continue
        im = np.asarray(Image.open(p))
        t = im[(y % 4) * 256:(y % 4 + 1) * 256, (x % 4) * 256:(x % 4 + 1) * 256]
        row.append(f"{name[:3]}:{(t[..., 3] > 127).mean() * 100:.0f}%")
    out.append(fr[9:] + " " + " ".join(row))
print(" | ".join(out))
