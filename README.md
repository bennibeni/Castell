# Castell

Simulazione 3D interattiva di una torre umana catalana **4 de 8**, con 90 atlete.
Applicazione autonoma Next.js, React e Three.js, ricavata da `Next13/src/app/rxx/R57`.

## Avvio

Richiede Node.js 20.9 o successivo e npm.

```powershell
npm install
npm run dev
```

Apri http://localhost:3000. Per una porta diversa: `npm run dev -- --port 3057`.

## Produzione

```powershell
npm run build
npm start
```

## Controlli

- Trascina la scena per ruotare; usa la rotellina per lo zoom.
- Premi la barra spaziatrice per mettere in pausa o riprendere.
- Usa la linea temporale per esplorare salita e discesa.
- I pulsanti permettono di cambiare inquadratura, velocità, colori per ruolo,
  manichini, guide geometriche e spaccato.

## Sorgenti

- `src/app/AcrobatSimulation.jsx`: simulazione originale R57.
- `src/app/page.js`: pagina principale.
- `src/app/layout.js`: layout e metadati Castell.
- `src/app/globals.css`: stili di base dell'applicazione autonoma.

Il sorgente originale nel progetto Next13 rimane invariato.
