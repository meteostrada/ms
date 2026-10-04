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
