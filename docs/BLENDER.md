# Migliorare le atlete con Blender

## Corpo continuo senza vestiti

La prima versione con corpo di libreria, pesi di deformazione e capelli
dell'originale è in `blender/Castell-atleta.blend`.
Il flusso di esportazione specifico è descritto in
[`blender/LEGGIMI.md`](../blender/LEGGIMI.md): richiede la finalizzazione del GLB
per collegare lo skinning ai controlli di Castell. Questo modello dichiara
esplicitamente `castellNoUniform`; i colori per ruolo lasciano la pelle invariata.
Le istruzioni successive descrivono anche il riferimento procedurale originale.

I componenti attivi sono in `public/models/catalog/`; la composizione viene
scelta nella pagina Settings. I precedenti GLB sono stati archiviati localmente
in `artifacts/public-archive/models/`, escluso dalla pubblicazione.
`npm run model:reference` crea un riferimento locale in `blender/athlete-reference.glb`.

## Primo lavoro in Blender

1. Esegui `npm run model:reference`, poi importa `blender/athlete-reference.glb` in Blender.
2. Salva il tuo progetto `.blend` in una cartella di lavoro: è il sorgente modificabile.
3. Nell'Outliner trovi il contenitore `Castell_Athlete`, i nodi di articolazione
   `Castell_*` e, sotto di essi, le mesh di corpo, viso, capelli e vestiti.
4. Modifica le mesh e i materiali. Puoi aggiungere occhi, dettagli del viso,
   acconciature, tessuti o accessori, mantenendo ciascuna parte figlia del suo nodo.
5. Esporta **glTF Binary (.glb)** in un file di prova. Includi tutta la gerarchia,
   anche gli oggetti vuoti; conserva i materiali. Esporta nella posa di riposo,
   senza applicare trasformazioni ai nodi `Castell_*`.
6. Dalla cartella Castell esegui `npm run model:validate -- "C:\percorso\modello.glb"`.
   Se passa, esporta il componente in `public/models/catalog/` e registra il
   relativo percorso in `src/app/scene/athlete/catalog.js`. Vedi anche
   [composizione delle atlete](ATHLETE-SETTINGS.md).
7. Controlla salita, torre completa e discesa. Il pulsante **Modello GLB** permette
   di confrontare il risultato con le figure standard.

Il GLB fornito usa **mesh rigide collegate a punti di rotazione**, non una pelle
deformabile con pesi. È una base semplice da modificare. Non devi costruire
uno scheletro da zero per migliorare volto, capelli, vestiti o forme delle mesh.

## Il collegamento con la simulazione

L'adattatore `src/app/scene/athlete/rig.js` contiene il contratto `JOINTS`.
I nodi possono essere anche ossa di uno scheletro con mesh skinned, se rispettano
lo stesso contratto. Uno scheletro generico importato da altri programmi richiede
un adattamento; il solo cambio dei nomi delle ossa non basta.

Nel GLB le unità sono metri, l'alto è +Y e il viso guarda +Z. Le braccia sono
lungo i fianchi nella posa di riposo. Blender mostra una diversa convenzione degli
assi: lascia gestire la conversione all'importatore/esportatore glTF.

| Nodo | Genitore articolato | Posizione locale nel GLB, in metri |
|---|---|---|
| Castell_Hips | radice | 0, 0.9, 0 |
| Castell_Thigh_L | Castell_Hips | 0.09, -0.02, 0 |
| Castell_Thigh_R | Castell_Hips | -0.09, -0.02, 0 |
| Castell_Knee_L | Castell_Thigh_L | 0, -0.43, 0 |
| Castell_Knee_R | Castell_Thigh_R | 0, -0.43, 0 |
| Castell_Torso | Castell_Hips | 0, 0.02, 0 |
| Castell_Arm_L | Castell_Torso | 0.19, 0.47, 0 |
| Castell_Arm_R | Castell_Torso | -0.19, 0.47, 0 |
| Castell_Elbow_L | Castell_Arm_L | 0, -0.29, 0 |
| Castell_Elbow_R | Castell_Arm_R | 0, -0.29, 0 |

I nodi articolati devono mantenere rotazione locale nulla e scala 1 nella posa
di riposo del GLB. I contenitori sopra `Castell_Hips` devono avere trasformazione
identità. Non cambiare nomi, genitori, punti di rotazione o assi locali.
Puoi cambiare le forme delle mesh senza spostare questi punti.

Le superfici della divisa devono usare il materiale **Castell_Uniform**:
il comando *Colori per ruolo* ne cambia il colore. Disattivandolo torna il colore
che hai scelto in Blender. Gli altri materiali restano quelli del modello.
La modalità *Manichino* usa le figure geometriche standard.

Mantieni le dimensioni dei piedi, le altezze delle spalle, il bacino e gli appoggi
vicini al riferimento: le traiettorie dipendono da quelle misure. Il validatore
controlla i punti di articolazione, non garantisce che una mesh modificata abbia
contatti corretti. Verifica visivamente gli appoggi dopo ogni esportazione.

## Cosa viene riutilizzato

- Il modello viene caricato una sola volta e replicato per le 90 atlete.
- Articolazioni e materiali sono indipendenti; geometrie e texture sono condivise.
- Un GLB assente o incompatibile lascia funzionare le figure standard e mostra il motivo.
- La riproduzione, lo slider, i colori per ruolo e lo spaccato continuano a funzionare.
- Le animazioni eventualmente esportate da Blender non vengono riprodotte: in questa
  prima integrazione i movimenti sono ancora calcolati da `simulation/poses.js`.
- Le inquadrature restano in `scene/camera.js`. Le camere contenute nel GLB non
  sostituiscono quelle dell'applicazione.

Non sono necessarie modifiche al codice per sostituire un modello compatibile.
Per cambiare proporzioni, animazioni o camere in Blender servirà un ulteriore
adattamento delle traiettorie o dei controlli della camera.

## Comandi

```powershell
npm run model:validate
npm run model:validate -- "C:\percorso\modello.glb"
npm test
npm run build
```

`npm run model:reference` rigenera soltanto `blender/athlete-reference.glb`, senza
sovrascrivere il modello attivo. Il generatore è `scripts/create-athlete-reference.mjs`;
la forma iniziale è definita in `scene/athlete/referenceModel.js`.

Il controllo da terminale ignora la decodifica delle texture: verifica anche le
texture nel browser. Per 90 figure conviene usare pochi materiali, geometrie
leggere e texture condivise.

Riferimenti: [glTF in Blender](https://docs.blender.org/manual/en/5.1/addons/import_export/scene_gltf2.html),
[GLTFLoader](https://threejs.org/docs/pages/GLTFLoader),
[clonazione degli scheletri](https://threejs.org/docs/pages/module-SkeletonUtils.html).
