# MeteoStrada: sito e radar

Il sito di MeteoStrada: la mappa della pioggia in Italia e in Europa (radar ogni 5 minuti) e il controllo della pioggia lungo un viaggio.

- `site/` — il sito (un solo file, senza librerie esterne) e la mappa di base.
- `tools/opera_tiles.py` — converte il radar europeo OPERA in tessere web; gira ogni 10 minuti.
- `tools/build_site.py` — compone il sito.
- `.github/workflows/pubblica.yml` — il lavoro automatico che ripubblica tutto.

Il codice dell'app Android/Desktop sta in un altro repository (privato).

## Fonti dei dati

- Radar Italia: Dipartimento della Protezione Civile, licenza CC BY-SA 4.0 (letto direttamente dal loro server).
- Radar Europa: OPERA, EUMETNET, licenza CC BY 4.0.
- Mappa di base: Natural Earth (pubblico dominio) e GeoNames (CC BY 4.0).
- Previsioni lungo il viaggio: Open-Meteo. Percorsi: OSRM (OpenStreetMap).

## Accrocchi e limiti noti (da rivedere)

- **Radar europeo dal deposito di riserva** · `tools/opera_tiles.py` (`BASES`).
  Dall'11 novembre 2026 alle 20:05 UTC il deposito principale delle foto OPERA (CloudFerro, `openradar-24h`) e' vuoto per un guasto
  del fornitore. EUMETNET pubblica le stesse foto in un deposito di riserva all'ECMWF (`openradar-24h-backup`, vedi la documentazione
  Open Radar Data). Il programma prova prima il principale e poi la riserva: quando il principale torna, si riprende da solo.

- **Disturbo fisso su Dublino (radar OPERA)** · `tools/clutter.py`, usato da `tools/opera_tiles.py`.
  Dal 28 ottobre 2026 il radar europeo mostrava su Dublino (53,32 N, 6,36 O) una macchia di 20-30 km con 30-100 mm/h ferma per ore,
  con tutto intorno asciutto e Open-Meteo senza pioggia: un disturbo, non un temporale. Causa vera **non nota** (echi fissi,
  interferenze o filtraggio dei dati irlandesi).
  Rimedio provvisorio: dentro 30 km da Dublino la pioggia si toglie solo se nella corona fino a 120 km piove meno del 4 %.
  Difetti: vale solo per quel punto (altri disturbi uguali non si vedono), nasconde un vero temporale isolato e piccolo in quel cerchio,
  non si adatta da solo.
  Soluzione giusta, rimandata: filtro generale senza luoghi scritti a mano. Un punto sopra ~30 mm/h per ~30 minuti senza spostarsi,
  con i punti intorno asciutti, e' un disturbo. Si farebbe con un piccolo contatore per punto salvato nella cache di GitHub (modo 2).
  Quando c'e', tenere la regola di Dublino come rete di sicurezza finche' il filtro non toglie da solo anche Dublino.
