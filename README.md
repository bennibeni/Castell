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

- `src/app/AcrobatSimulation.jsx`: collega scena 3D, stato e interfaccia.
- `src/app/simulation/`: modello e costanti, piano della coreografia, calcolo delle pose,
  statistiche e fasi. Questi moduli non dipendono da React o Three.js.
- `src/app/scene/`: figure articolate, arena e pubblico, guide geometriche,
  inquadrature e aggiornamento della scena a ogni fotogramma.
- `src/app/hooks/`: riproduzione, selezioni dell'utente, scorciatoie e misure del layout.
- `src/app/ui/`: pannelli delle statistiche e dei piani, controlli e stili condivisi.
- `src/app/page.js`: pagina principale.
- `src/app/layout.js`: layout e metadati Castell.
- `src/app/globals.css`: stili di base dell'applicazione autonoma.

Il sorgente originale nel progetto Next13 rimane invariato.

## Modelli modificabili con Blender

Il pulsante **Modello GLB** usa `public/models/athlete.glb` al posto delle figure
procedurali. Il modello di partenza da importare in Blender è
`public/models/athlete-reference.glb`. Le pose restano guidate dalla simulazione.

La [guida Blender](docs/BLENDER.md) spiega come modificare le mesh, conservare le
articolazioni, verificare il GLB e riportarlo nell'app. Il comando
`npm run model:validate` controlla il modello attivo. Se il file è assente o
incompatibile, l'app mostra il motivo e usa le figure standard.

## Verifica

`npm test` confronta il piano della coreografia e le pose delle 90 atlete in 84
istanti con i risultati salvati prima del refactoring. Controlla anche altezza,
carico, fasi, numero di atlete e completamento degli otto piani.

`npm run build` verifica la compilazione di produzione.
