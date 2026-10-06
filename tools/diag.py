"""Diagnostica: per ogni foto OPERA, quanta parte di alcune tessere (z7) e' coperta dai radar."""
import os, sys, math, glob
import numpy as np
from PIL import Image
d = sys.argv[1]
def tile(lat, lon, z=7):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
pts = {"Barcellona": (41.4, 2.2), "Madrid": (40.4, -3.7), "Valencia": (39.5, -0.4), "Londra": (51.5, -0.1), "Parigi": (48.9, 2.3), "Milano": (45.5, 9.2),
       "Atene": (37.98, 23.73), "Salonicco": (40.64, 22.94), "Istanbul": (41.01, 28.98), "Ankara": (39.93, 32.86), "Bucarest": (44.43, 26.10), "Budapest": (47.50, 19.04), "Belgrado": (44.79, 20.45), "Zagabria": (45.81, 15.98), "Sofia": (42.70, 23.32), "Tirana": (41.33, 19.82), "Lubiana": (46.06, 14.51), "Sarajevo": (43.86, 18.41)}
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
print(" | ".join(out[-2:]))
