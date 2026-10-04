"""Raggruppa le tessere di una foto in blocchi da 4x4 tessere (un solo file PNG da 1024x1024 per blocco):
il sito fa 16 volte meno richieste (GitHub Pages limita chi ne fa troppe).
Per ogni livello: cartella/Z/bX_Y.png dove X, Y = coordinate della tessera divise per 4.
Le tessere mancanti nel blocco restano vuote (trasparenti per i radar, nere per il satellite)."""
import os, shutil
import numpy as np
from PIL import Image

B = 4

def build(frame_dir, alpha):
    made = 0
    for z in sorted(int(d) for d in os.listdir(frame_dir) if d.isdigit()):
        src = os.path.join(frame_dir, str(z))
        blocks = {}
        for x in os.listdir(src):
            xp = os.path.join(src, x)
            if not os.path.isdir(xp):
                continue
            for y in os.listdir(xp):
                blocks.setdefault((int(x) // B, int(y[:-4]) // B), []).append((int(x), int(y[:-4]), os.path.join(xp, y)))
        for (bx, by), items in blocks.items():
            canvas = np.zeros((256 * B, 256 * B, 4 if alpha else 1), np.uint8)
            for x, y, path in items:
                im = np.asarray(Image.open(path))
                if not alpha:
                    im = im[..., None] if im.ndim == 2 else im[..., :1]
                canvas[(y % B) * 256:(y % B + 1) * 256, (x % B) * 256:(x % B + 1) * 256] = im
            out = os.path.join(src, f"b{bx}_{by}.png")
            Image.fromarray(canvas if alpha else canvas[..., 0], "RGBA" if alpha else "L").save(out, optimize=True)
            made += 1
        for x in os.listdir(src):
            p = os.path.join(src, x)
            if os.path.isdir(p):
                shutil.rmtree(p)
    return made
