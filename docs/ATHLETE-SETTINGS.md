# Composizione delle atlete

Aprire `/settings` oppure **Settings · Atlete** nei controlli della simulazione.
Scegliere corpo e testa, controllare l'anteprima ruotabile (figura intera o viso),
quindi premere **Salva e applica alle atlete**. La preferenza si applica alle 90
atlete durante la sessione corrente; non modifica i file Blender. All'avvio o
al ricaricamento completo si parte sempre da **Manichino Castell + Testa del
manichino originale**, senza ripristinare le vecchie preferenze locali. I link
interni tra Settings e simulazione conservano la scelta della sessione.
Le modifiche non
salvate rimangono solo in anteprima. Il pulsante di ripristino prepara la
composizione iniziale e richiede un successivo salvataggio.

Il catalogo comprende due corpi, la testa geometrica originale e la precedente
testa dettagliata piccola, chiamata **Realistic girl**. La testa geometrica è disponibile su entrambi i corpi;
la dettagliata piccola è disponibile sul manichino con divisa. Le vecchie scelte
Hinako piccola e manichino piccolo vengono migrate alla dettagliata quando il
corpo lo consente; altrimenti si mantiene il corpo e si usa la testa geometrica.
Un identificatore testa sconosciuto seleziona una testa disponibile per il corpo;
preferenze prive di un corpo valido tornano alla composizione iniziale.

`src/app/scene/athlete/catalog.js` contiene schede e compatibilità.
`composition.js` carica e compone i componenti, conservando il rig del corpo e
collegando la testa al torso. Le teste hanno coordinate di riposo in metri;
ogni corpo definisce scala e quota di adattamento. Ogni atleta mantiene
materiali e articolazioni indipendenti.

Gli asset in `public/models/catalog` sono derivati dai Blender locali senza
modificare le sorgenti. Rigenerazione da PowerShell nella radice del progetto:

```powershell
& 'C:\blender-git\build_windows_x64_vc17_Release\bin\Release\blender.exe' --background --factory-startup --disable-autoexec --python scripts/export-athlete-catalog.py
node scripts/finalize-athlete.mjs blender/catalog/body-adult-raw.glb public/models/catalog/body-adult.glb
node scripts/create-lightweight-head.mjs
```

La testa geometrica è generata dal modello procedurale originale di Castell:
collo, sfera del viso, calotta dei capelli e chignon, senza texture del viso.
Il GLB geometrico pesa circa 29 KB. La dettagliata piccola usa la versione
ottimizzata del precedente modello (circa 7 MiB), caricata solo se selezionata.
Vedi [ottimizzazione delle texture](HEAD-TEXTURE-OPTIMIZATION.md).
Le teste sono statiche rispetto al torso.
Il corpo anatomico conserva lo skinning. Una cache per
sessione condivide sorgenti e texture; i cambi di composizione non scaricano
nuovamente gli stessi componenti.

Verifica: `npm test` controlla le tre combinazioni disponibili, la scala,
il collegamento al torso, l'indipendenza delle istanze e la compatibilità
delle preferenze. `npm run build` verifica anche la nuova route.
