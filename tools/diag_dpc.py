"""Diagnosi: per le tessere tra Torino e Milano, confronta le foto del radar italiano di orari vicini."""
import datetime, io, urllib.request
from PIL import Image
import numpy as np
B = "https://s3-prod-dpc-radar-webp-cache.s3.eu-south-1.amazonaws.com"
now = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
now -= datetime.timedelta(minutes=now.minute % 5 + 10)
def get(t, x, y):
    u = f"{B}/SRI/{t:%Y/%m/%d}/{t:%H%M}/7/{x}/{y}/sri.webp"
    try:
        a = np.array(Image.open(io.BytesIO(urllib.request.urlopen(u, timeout=15).read())).convert("RGBA"))
        v = np.where(a[..., 3] >= 128, a[..., 0] * (100 / 255), -1.0)
        return v
    except Exception as e:
        return None
lines = []
for (x, y) in [(66, 45), (67, 45), (66, 46)]:
    fr = {k: get(now - datetime.timedelta(minutes=5 * k), x, y) for k in range(11, -1, -1)}
    prev = None
    for k in range(11, -1, -1):
        v = fr[k]; t = now - datetime.timedelta(minutes=5 * k)
        if v is None: lines.append(f"{x}/{y} {t:%H:%M} manca"); prev = None; continue
        inval = int((v < 0).sum()); rain = int((v >= 0.3).sum())
        extra = ""
        if prev is not None:
            lost = int(((prev >= 0.3) & (v < 0)).sum())      # pioggia di prima ora senza dato
            zero = int(((prev >= 0.3) & (v >= 0) & (v < 0.3)).sum())   # pioggia di prima ora ora a zero
            extra = f" rispetto a prima: pioggia->senza dato {lost}, pioggia->zero {zero}"
        lines.append(f"{x}/{y} {t:%H:%M} senza dato {inval} pioggia {rain}{extra}")
        prev = v
for i in range(0, len(lines), 12):
    print("::notice title=cmp" + str(i // 12) + "::" + "%0A".join(lines[i:i + 12]))
print("\n".join(lines))
