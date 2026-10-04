"""Livelli di zoom piu' bassi (mondo, continenti) a partire dalle tessere gia' fatte.
Ogni tessera genitore prende il valore massimo dei quattro figli (mm/h); un figlio che manca vale "asciutto"
(e "senza copertura" per le tessere con alfa).
Uso interno: build(cartella_foto, zoom_di_partenza, zoom_minimo, con_alfa)
Codifica come le tessere: v = 255 * sqrt(mm/h / 100)."""
import os
import numpy as np
from PIL import Image

def _read(path, alpha):
    if not os.path.exists(path):
        return np.zeros((256, 256), np.float32), np.zeros((256, 256), np.float32)
    im = np.asarray(Image.open(path))
    if im.ndim == 2:
        code, a = im, np.full(im.shape, 255, np.uint8)
    else:
        code, a = im[..., 0], (im[..., 3] if im.shape[2] > 3 else np.full(im.shape[:2], 255, np.uint8))
    mm = (code.astype(np.float32) / 255) ** 2 * 100
    return mm, (a.astype(np.float32) / 255 if alpha else np.ones_like(mm))

def build(frame_dir, z_from, z_min, alpha):
    made = 0
    for z in range(z_from, z_min - 1, -1):
        src = os.path.join(frame_dir, str(z))
        if not os.path.isdir(src):
            continue
        parents = set()
        for x in os.listdir(src):
            for y in os.listdir(os.path.join(src, x)):
                parents.add((int(x) // 2, int(y[:-4]) // 2))
        for px, py in parents:
            big = np.zeros((512, 512), np.float32); cov = np.zeros((512, 512), np.float32)
            for dx in (0, 1):
                for dy in (0, 1):
                    m, a = _read(os.path.join(src, str(px * 2 + dx), f"{py * 2 + dy}.png"), alpha)
                    big[dy * 256:(dy + 1) * 256, dx * 256:(dx + 1) * 256] = m
                    cov[dy * 256:(dy + 1) * 256, dx * 256:(dx + 1) * 256] = a
            mm = big.reshape(256, 2, 256, 2).max(axis=(1, 3))   # il massimo, non la media: un temporale piccolo non deve sparire da lontano
            a = cov.reshape(256, 2, 256, 2).mean(axis=(1, 3))
            code = np.rint(np.sqrt(np.clip(mm, 0, 100) / 100) * 255).astype(np.uint8)
            d = os.path.join(frame_dir, str(z - 1), str(px)); os.makedirs(d, exist_ok=True)
            p = os.path.join(d, f"{py}.png")
            if alpha:
                al = np.where(a > 0.5, 255, 0).astype(np.uint8)
                code = np.where(al > 0, code, 0).astype(np.uint8)
                Image.fromarray(np.dstack([code, code, code, al]), "RGBA").save(p, optimize=True)
            else:
                if not code.any():
                    continue
                Image.fromarray(code, "L").save(p, optimize=True)
            made += 1
    return made
