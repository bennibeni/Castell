import {
  Y,
  headTopOf,
  S_BAIX,
  S_TRONC,
  S_DOSOS,
  SC_DOSOS,
  Y_AIX,
  S_AIX,
  SC_AIX,
  Y_ENX,
  SC_ENX,
  MASS,
  T_HOLD,
} from './constants.js';
import { enxSquat } from './poses.js';

/* ─────────────────────────── grandezze per l'interfaccia ─────────────────────────── */
const present = (a, t) => t >= a.arrive && t < a.descStart;

function headTopRole(a, t, T) {
  if (a.role === 'tronc') return Y[a.pis - 1] + headTopOf(a.pis === 1 ? S_BAIX : S_TRONC, 0.6, 1);
  if (a.role === 'dosos') return Y[5] + headTopOf(S_DOSOS, 0.4, SC_DOSOS);
  if (a.role === 'aix') return Y_AIX + headTopOf(S_AIX, 0.66, SC_AIX);
  if (a.role === 'enx') return Y_ENX + headTopOf(enxSquat(T, t), 0.45, SC_ENX);
  return 1.67;
}

function topHeightAt(P, t) {
  let top = 1.67;
  for (const a of P.athletes)
    if ((a.role === 'tronc' || a.climber) && present(a, t))
      top = Math.max(top, headTopRole(a, t, P.T));
  return top;
}

function baixLoadAt(P, t) {
  let col = 0,
    pom = 0;
  for (const a of P.athletes) {
    if (!a.climber || !present(a, t)) continue;
    const m = MASS[a.pis - 1] ?? 0;
    if (a.role === 'tronc') col += m;
    else pom += m;
  }
  return (col + pom) / 4;
}

function phaseAt(P, t) {
  const { T, pis } = P;
  if (t < T_HOLD)
    return {
      title: 'Formazione',
      sub: 'Reticolo 10 × 9: 90 atlete. Da qui nasce un “4 de 8”: 4 per piano, 8 piani.',
    };
  if (t < T.tPinyaReady)
    return {
      title: 'Si fa pinya',
      sub: 'Al centro i 4 baixos si abbracciano; attorno crosses, contraforts, rengles de mans, vents e laterals. Chi sale si mette in fila sulle 4 rengles.',
    };
  const steps = [
    [
      2,
      'Salgono i segons',
      'Coscia e spalle della rengla de mans, spalle del contrafort, poi i piedi sulle spalle del baix.',
    ],
    [
      3,
      'Salgono i terços',
      'Ogni appoggio è un corpo: faixa e spalle di chi sta già nel tronc. Nessun passo nel vuoto.',
    ],
    [
      4,
      'Salgono i quarts',
      'Si sale solo quando chi sta sotto è in posizione: le colonne crescono quasi in parallelo.',
    ],
    [5, 'Salgono i quints', 'Ultimo piano del tronc: 5 piani × 4 colonne = 20 atlete.'],
    [6, 'Pom de dalt: i dosos', 'Due ragazzine, ognuna con un piede sulle spalle di due quints.'],
    [7, 'L’aixecador', 'Accovacciata, un piede su ciascuno dei dosos.'],
    [8, 'Sale l’enxaneta', 'Si arrampica fino alla schiena dell’aixecador.'],
  ];
  for (const [p, title, sub] of steps) if (t < pis[p].arrive) return { title, sub };
  if (t < T.aletaEnd)
    return {
      title: 'Il castell è carregat!',
      sub: 'L’enxaneta si alza in piedi sulla schiena dell’aixecador e apre le braccia. Fine della salita.',
    };
  if (t <= T.descent + 0.01)
    return {
      title: 'Castell carregat',
      sub: 'Tutte e 24 in posizione, ferme. Premi “Discesa” per smontarlo dall’alto verso il basso.',
    };
  if (t < T.tRelax)
    return {
      title: 'Discesa · si descarrega',
      sub: 'L’enxaneta scende dal lato opposto, poi aixecador, dosos e il tronc piano per piano: ognuna parte solo quando chi sta sopra è passata oltre.',
    };
  return {
    title: 'Castell descarregat!',
    sub: 'Costruito e smontato senza cadute: è il risultato pieno di una colla castellera.',
  };
}

const PIS_FEET = (p) => (p <= 6 ? Y[p - 1] : p === 7 ? Y_AIX : Y_ENX);

export { present, topHeightAt, baixLoadAt, phaseAt, PIS_FEET };
