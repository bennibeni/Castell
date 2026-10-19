# Ottimizzazione conservativa della testa dettagliata piccola

Il GLB passa da 24.183.980 a 7.311.684 byte (circa 23,1 a 7,0 MiB, -69,8%).
Nessuna modifica a geometrie, UV, gerarchie, materiali o proporzioni. Tutti i
buffer non immagine sono verificati identici byte per byte dal generatore.

- Colore del viso e iridi: risoluzione 2048px conservata, JPEG qualità 95,
  campionamento colore 4:4:4 per evitare sbavature dei contorni colorati.
- Colore/trasparenza di capelli e ciglia: PNG originali conservati byte per byte.
- Normal map della pelle: 1536px, PNG senza perdita ulteriore e vettori
  rinormalizzati dopo il ridimensionamento.
- Rugosità: 1024px, canale verde effettivamente utilizzato, JPEG qualità 98.
- Normal map delle ciglia: 512px, PNG e vettori rinormalizzati. La sagoma delle
  ciglia rimane definita dalla mappa trasparente originale a 2048px.

L'originale resta in `artifacts/head-texture-optimization/original.glb`.
`report.json` nella stessa cartella registra dimensioni e peso di ogni texture.
Le immagini original/optimized front e three-quarter mostrano un confronto
con identica camera, illuminazione e campionamento, sul manichino con divisa.

Rigenerazione locale (richiede `sharp`, disponibile con le dipendenze Next):

```powershell
node scripts/optimize-head-textures.mjs
```

Il comando legge il vecchio file pubblico se presente, altrimenti il backup
locale, ed esporta `artifacts/head-texture-optimization/optimized.glb`.
Non sostituisce direttamente il modello distribuito.
