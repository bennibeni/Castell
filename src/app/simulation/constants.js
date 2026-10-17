/* ─────────────────────────── corpo ─────────────────────────── */
const HIP = 0.9;
const squatAngle = (s) => s * 1.25;
const hipHeight = (s) => HIP * Math.cos(squatAngle(s));
const shoulderHeight = (s, leanK) => hipHeight(s) + 0.02 + 0.47 * Math.cos(s * leanK) + 0.03;
const headTopOf = (s, leanK, scale) => scale * (hipHeight(s) + 0.02 + 0.75 * Math.cos(s * leanK));

/* ─────────────────────────── geometria del castell ─────────────────────────── */
const VIDEO_DIR = Math.PI / 4; // direzione (+x,+z): da lì riprende la camera
const T_HOLD = 2.5; // secondi di reticolo fermo
const GRID = { cols: 10, rows: 9, step: 1.0 };
const A = 0.32; // semilato del quadrato del tronc (4 colonne)
const COLS = [
  [1, 1],
  [-1, 1],
  [-1, -1],
  [1, -1],
]; // c0 è la colonna verso la camera
const U = COLS.map(([x, z]) => [x / Math.SQRT2, z / Math.SQRT2]);
const R_COL = A * Math.SQRT2; // distanza delle colonne dall'asse
const R_CONTRA = R_COL + 0.42;
const R_MANS = (j) => R_CONTRA + 0.45 * j;
const R_START = 3.5; // da qui si comincia a salire (varco nel darrer cordó)
const R_QUEUE = (i) => 4.1 + 0.6 * i;
const CLIMB_SPEED = 1.0; // m/s lungo il percorso in salita (passo costante)
const DOWN_SPEED = 1.3; // m/s in discesa
const HOLD_TIME = 0.25; // s in più per ogni appoggio (cambio di presa)

// accosciamento (s) e scala delle varie figure
const S_BAIX = 0.1,
  S_TRONC = 0.06,
  S_DOSOS = 0.15,
  S_AIX = 0.75,
  S_ENX = 0.7;
const SC_DOSOS = 0.86,
  SC_AIX = 0.82,
  SC_ENX = 0.78; // il pom de dalt: atlete più minute

// quote dei piedi (statiche: chi è in posizione non si muove)
const Y = [0];
Y[1] = shoulderHeight(S_BAIX, 0.6) - 0.03;
for (let k = 2; k <= 5; k++) Y[k] = Y[k - 1] + shoulderHeight(S_TRONC, 0.6) - 0.03; // Y[5] = piedi dei dosos
const Y_AIX = Y[5] + SC_DOSOS * shoulderHeight(S_DOSOS, 0.4) - 0.02;
const Y_ENX = Y_AIX + SC_AIX * (hipHeight(S_AIX) + 0.3);

const colPt = (c, r, y, side = 0) => ({
  x: U[c][0] * r - U[c][1] * side,
  y,
  z: U[c][1] * r + U[c][0] * side,
});

/* pis = piano del castell (1..8); la pinya sta a terra (pis 0) */
const PIS_NAMES = [
  'Baixos',
  'Segons',
  'Terços',
  'Quarts',
  'Quints',
  'Dosos',
  'Aixecador',
  'Enxaneta',
];
const PIS_COLORS = [
  '#ef6f4f',
  '#f2a93b',
  '#cfd64a',
  '#5ccf7a',
  '#3fc4c9',
  '#5b8ff0',
  '#a07ff0',
  '#f26aa8',
];
const PINYA_COLOR = '#8d939c';
const CAP_COLOR = '#d9b45c';
const NAVY = '#1f2b4f';
const FOV = 42; // campo visivo verticale della camera (gradi)
const FRAME_SHIFT = 0.18;
const FRAME_BOTTOM = -0.62 - FRAME_SHIFT; // pavimento al 10% dal fondo
const FRAME_TOP = 0.88 - FRAME_SHIFT; // cima (+2 m) al 15% dall'alto
const MANNEQUIN_COLOR = '#cfc6b6'; // legno chiaro dei manichini
const JOINT_COLOR = '#1b1f2a'; // articolazioni evidenziate
// masse ipotizzate (kg) per il calcolo del carico sui baixos
const MASS = { 1: 70, 2: 62, 3: 55, 4: 50, 5: 32, 6: 26, 7: 20 };

export {
  HIP,
  squatAngle,
  headTopOf,
  VIDEO_DIR,
  T_HOLD,
  GRID,
  A,
  COLS,
  U,
  R_COL,
  R_CONTRA,
  R_MANS,
  R_START,
  R_QUEUE,
  CLIMB_SPEED,
  DOWN_SPEED,
  HOLD_TIME,
  S_BAIX,
  S_TRONC,
  S_DOSOS,
  S_AIX,
  S_ENX,
  SC_DOSOS,
  SC_AIX,
  SC_ENX,
  Y,
  Y_AIX,
  Y_ENX,
  colPt,
  PIS_NAMES,
  PIS_COLORS,
  PINYA_COLOR,
  CAP_COLOR,
  NAVY,
  FOV,
  FRAME_SHIFT,
  FRAME_BOTTOM,
  FRAME_TOP,
  MANNEQUIN_COLOR,
  JOINT_COLOR,
  MASS,
};

const REACH_MAX = 0.8; // oltre questa distanza (m) nessun contatto: braccia giù

export { REACH_MAX };
