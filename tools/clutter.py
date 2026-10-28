"""Echi radar fissi che non sono pioggia (disturbi del radar, interferenze): si tolgono dalla mappa.

Caso noto: su Dublino il composito OPERA mostra per ore una macchia di 20-30 km con celle da 30-100 mm/h
(il "temporale sempre su Dublino"), mentre tutto intorno e' asciutto e Open-Meteo prevede cielo coperto senza pioggia.
Regola: dentro il cerchio del sito la pioggia si toglie SOLO se nella corona attorno (da RADIUS a RING km) piove
pochissimo: una perturbazione vera e' molto piu' estesa di 30 km e bagna anche la corona, un disturbo no.
"""
import numpy as np

# nome, latitudine, longitudine, raggio del cerchio in km
SITES = [("Dublino", 53.32, -6.36, 30)]
RING_KM = 120
MAX_WET_RING = 0.04     # quota di celle con pioggia >= 0.5 mm/h nella corona oltre la quale la pioggia e' vera
WET = 0.5               # mm/h


def suppress(rain, covered, centers):
    """rain: mm/h (riga, colonna) a 1 km; covered: copertura radar; centers: [(riga, colonna, raggio_km)] nella stessa griglia."""
    out = rain
    removed = 0
    H, W = rain.shape
    for (r, c, rad) in centers:
        r0, r1 = max(0, int(r - RING_KM)), min(H, int(r + RING_KM) + 1)
        c0, c1 = max(0, int(c - RING_KM)), min(W, int(c + RING_KM) + 1)
        if r1 <= r0 or c1 <= c0:
            continue
        yy, xx = np.mgrid[r0:r1, c0:c1]
        dist = np.hypot(yy - r, xx - c)
        inside = dist <= rad
        ring = (dist > rad) & (dist <= RING_KM) & covered[r0:r1, c0:c1]
        if not ring.any():
            continue
        sub = out[r0:r1, c0:c1]
        wet_ring = float((sub[ring] >= WET).mean())
        wet_in = int(((sub >= WET) & inside).sum())
        if wet_ring < MAX_WET_RING and wet_in:
            if out is rain:
                out = rain.copy()
                sub = out[r0:r1, c0:c1]
            sub[inside] = 0
            removed += wet_in
    return out, removed
