"""Diagnosi: per le tessere tra Torino e Milano, stato e pioggia di ogni foto del radar italiano (ultime 2 ore)."""
import datetime, io, urllib.request
from PIL import Image
import numpy as np
B = "https://s3-prod-dpc-radar-webp-cache.s3.eu-south-1.amazonaws.com"
now = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
now -= datetime.timedelta(minutes=now.minute % 5)
lines = []
for k in range(24, -1, -1):
    t = now - datetime.timedelta(minutes=5 * k)
    row = []
    for (x, y) in [(66, 45), (66, 46), (67, 45), (67, 46)]:
        u = f"{B}/SRI/{t:%Y/%m/%d}/{t:%H%M}/7/{x}/{y}/sri.webp"
        try:
            d = urllib.request.urlopen(u, timeout=15).read()
            a = np.array(Image.open(io.BytesIO(d)).convert("RGBA"))
            valid = a[..., 3] >= 128
            rain = valid & (a[..., 0] * (100 / 255) >= 0.3)
            if rain.any():
                ys, xs = np.nonzero(rain); c = f"{int(xs.mean())},{int(ys.mean())}"
            else:
                c = "-"
            row.append(f"{x}/{y}:v{int(valid.mean()*100)}% p{int(rain.sum())} c{c}")
        except Exception as e:
            row.append(f"{x}/{y}:{str(e)[:12]}")
    lines.append(f"{t:%H:%M} " + " | ".join(row))
for i in range(0, len(lines), 6):
    print("::notice title=dpc" + str(i // 6) + "::" + "%0A".join(lines[i:i + 6]))
print("\n".join(lines))
