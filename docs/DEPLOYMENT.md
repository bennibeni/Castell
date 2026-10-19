# Pubblicazione e archivio locale

- `.gitignore` esclude `/blender/` e `/artifacts/` dai nuovi commit.
- `.vercelignore` esclude le stesse cartelle dall'upload via Vercel CLI,
  insieme a dipendenze, build locali, file Git e variabili d'ambiente.
- `public/` contiene soltanto asset attivi del catalogo: quattro GLB e quattro
  miniature. La testa dettagliata piccola è caricata soltanto quando selezionata.
- I precedenti asset pubblici e la versione non compressa della testa sono conservati in
  `artifacts/public-archive/` con la struttura delle sottocartelle e un manifest.

La dimensione di `public/` con la dettagliata piccola ottimizzata è circa 10,2 MiB. Le cartelle locali
con i sorgenti, i render e le build continuano a occupare spazio sul disco.
Questa operazione non riscrive la cronologia Git e non pulisce `.git/`.

La verifica del modello e i test caricano ora i componenti attivi del catalogo,
senza dipendere dai vecchi GLB archiviati. Il riferimento procedurale si può
rigenerare localmente con `npm run model:reference`. Gli export intermedi
`*-raw.glb` del generatore del catalogo sono salvati in `blender/catalog/`.

Per controllare eventuali altri asset inutilizzati:

```powershell
node scripts/archive-unused-public.mjs
```

Senza opzioni il comando mostra soltanto il piano. `--apply` sposta i file
in archivio dopo aver controllato percorsi, componenti attivi e dipendenze
esterne dei GLB. Non sovrascrive file già archiviati.

Prima di pubblicare:

```powershell
git status --short
npm run model:validate
npm test
npm run build
```

I file rimossi da `public/` che erano già tracciati da Git devono risultare
come eliminazioni nel prossimo commit. L'esclusione non rimuove copie già
presenti in commit precedenti; qualsiasi intervento sulla cronologia richiede
una valutazione separata. Nessun commit, push o deploy viene eseguito dalla pulizia.
