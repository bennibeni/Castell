# Testa del manichino piccola

La voce `mannequin-detailed-small`, etichettata **Realistic girl**,
ripristina il precedente modello dettagliato con viso, occhi, ciglia e capelli.
Il compositore applica la scala uniforme originale 0.9034934067618628 e una
correzione verticale di 0.1431342506173896 metri, prima dell'adattamento al corpo.
Le proporzioni e le dimensioni della precedente testa piccola sono conservate.

La variante è disponibile sul manichino con divisa. Le precedenti scelte
`hinako-small` e `mannequin-original-small` sono migrate a questa voce se
compatibili con il corpo; in caso contrario si mantiene il corpo e si usa la
testa geometrica originale. La voce standard geometrica rimane separata e leggera.

Il test `tests/athlete-head-size.test.mjs` verifica altezza e innesto del collo,
riuso di geometrie/materiali e scala uniforme.
