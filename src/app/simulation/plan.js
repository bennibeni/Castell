import {
  GRID,
  COLS,
  A,
  U,
  colPt,
  R_COL,
  R_CONTRA,
  R_MANS,
  R_QUEUE,
  SC_DOSOS,
  SC_AIX,
  SC_ENX,
  T_HOLD,
  Y,
  R_START,
  Y_AIX,
  Y_ENX,
  HOLD_TIME,
  CLIMB_SPEED,
  DOWN_SPEED,
} from './constants.js';
import { REACH_MAX } from './constants.js';
import { hash } from './math.js';

/**
 * Castell 4 de 8
 *
 * Ricostruzione di una torre umana catalana (castell) con 90 atlete:
 *  - tronc: 4 colonne × 5 piani (baixos, segons, terços, quarts, quints) = 20
 *  - pom de dalt: 2 dosos, 1 aixecador, 1 enxaneta = 4  → 8 piani in tutto
 *  - pinya: 66 atlete a terra (agulla, crosses, contraforts, rengles de mans,
 *    vents, laterals, darrer cordó, cap de colla)
 *
 * Regola fondamentale: chi sale appoggia i piedi SOLO su un corpo
 * (coscia o spalle della pinya, faixa e spalle di chi sta nel tronc).
 * Un appoggio può essere usato solo dopo che la sua "proprietaria" è in posizione,
 * e chi sta sotto scende solo dopo che tutte quelle sopra sono passate oltre.
 *
 * Fonti: Viquipèdia/Wikipedia "Castell"; Gran Enciclopèdia Catalana "castell";
 * 3Cat, "Guia castellera".
 * Tutto è funzione pura del tempo t: lo slider va avanti e indietro.
 * Coordinate: metri, y verso l'alto, camera "del video" sulla diagonale (+x, +z).
 */

/* ─────────────────────────── piano della coreografia ─────────────────────────── */
function buildPlan() {
  const grid = [];
  for (let r = 0; r < GRID.rows; r++)
    for (let c = 0; c < GRID.cols; c++)
      grid.push({
        gx: (c - (GRID.cols - 1) / 2) * GRID.step,
        gz: (r - (GRID.rows - 1) / 2) * GRID.step,
      });

  // posti a terra (gruppi in ordine di distanza dal centro) + code di chi salirà
  const slots = [];
  const add = (group, role, x, z, extra = {}) =>
    slots.push({ group, role, x, z, pis: 0, col: -1, scale: 1, ...extra });
  add(0, 'agulla', 0, 0);
  COLS.forEach(([cx, cz], c) => add(1, 'tronc', cx * A, cz * A, { pis: 1, col: c }));
  U.forEach((u, c) =>
    [1, -1].forEach((sg) => {
      const p = colPt(c, R_COL + 0.2, 0, 0.3 * sg);
      add(2, 'cross', p.x, p.z, { col: c });
    }),
  );
  U.forEach((u, c) => {
    const p = colPt(c, R_CONTRA, 0);
    add(3, 'contra', p.x, p.z, { col: c });
  });
  for (let j = 1; j <= 3; j++)
    U.forEach((u, c) => {
      const p = colPt(c, R_MANS(j), 0);
      add(4, 'mans', p.x, p.z, { col: c, j });
    });
  [
    [1, 0],
    [0, 1],
    [-1, 0],
    [0, -1],
  ].forEach(([dx, dz]) => [1.0, 1.45, 1.9].forEach((r) => add(5, 'vent', dx * r, dz * r)));
  U.forEach((u) =>
    [1, -1].forEach((sg) => {
      const ang = Math.atan2(u[1], u[0]) + (sg * Math.PI) / 8;
      [1.4, 1.85].forEach((r) => add(6, 'lateral', r * Math.cos(ang), r * Math.sin(ang)));
    }),
  );
  for (let k = 0; k < 12; k++)
    add(7, 'cordo', 3.0 * Math.cos((k * Math.PI) / 6), 3.0 * Math.sin((k * Math.PI) / 6));
  add(8, 'cap', 3.85, 0);
  // code: per ogni colonna segon, terç, quart, quint e un membro del pom de dalt
  const POM_BY_COL = ['enx', 'dosos', 'aix', 'dosos'];
  for (let c = 0; c < 4; c++)
    for (let i = 0; i < 5; i++) {
      const q = colPt(c, R_QUEUE(i), 0);
      const role = i < 4 ? 'tronc' : POM_BY_COL[c];
      const pis = i < 4 ? i + 2 : role === 'dosos' ? 6 : role === 'aix' ? 7 : 8;
      const scale =
        role === 'dosos' ? SC_DOSOS : role === 'aix' ? SC_AIX : role === 'enx' ? SC_ENX : 1;
      add(9, role, q.x, q.z, { pis, col: c, climber: true, scale });
    }

  // abbinamento reticolo → posti: le più vicine al centro fanno pinya e base, le più lontane salgono
  const order = grid
    .map((p) => ({
      ...p,
      d: Math.round(Math.hypot(p.gx, p.gz) * 1e6) / 1e6,
      a: Math.round(Math.atan2(p.gz, p.gx) * 1e6) / 1e6,
    }))
    .sort((a, b) => a.d - b.d || a.a - b.a);
  const groups = [...new Set(slots.map((s) => s.group))].sort((a, b) => a - b);
  let ptr = 0;
  const athletes = [];
  for (const gi of groups) {
    const S = slots
      .filter((s) => s.group === gi)
      .map((s) => ({ ...s, ang: Math.round(Math.atan2(s.z, s.x) * 1e6) / 1e6 }))
      .sort((a, b) => a.ang - b.ang);
    const n = S.length;
    const P = order.slice(ptr, ptr + n).sort((a, b) => a.a - b.a);
    ptr += n;
    let best = 0,
      bestCost = Infinity;
    for (let sh = 0; sh < n; sh++) {
      let cost = 0;
      for (let i = 0; i < n; i++) {
        const p = P[(i + sh) % n];
        cost += Math.hypot(p.gx - S[i].x, p.gz - S[i].z);
      }
      if (cost < bestCost) {
        bestCost = cost;
        best = sh;
      }
    }
    for (let i = 0; i < n; i++) {
      const p = P[(i + best) % n];
      const s = S[i];
      athletes.push({ ...s, gx: p.gx, gz: p.gz, tx: s.x, tz: s.z });
    }
  }
  athletes.forEach((a, i) => {
    a.id = i;
  });

  /* pinya: chi ha davanti (entro un cono di ±40°) una compagna a portata di braccio
     le appoggia le mani sulla schiena; chi non ha nessuno davanti tiene le braccia lungo i fianchi */
  const ground = athletes.filter((a) => !a.climber);
  ground.forEach((a) => {
    if (a.role === 'tronc' || a.role === 'cap' || a.role === 'cross') return;
    const r = Math.hypot(a.tx, a.tz);
    const fx = a.role === 'agulla' ? Math.SQRT1_2 : -a.tx / r;
    const fz = a.role === 'agulla' ? Math.SQRT1_2 : -a.tz / r;
    let best = null;
    for (const b of ground) {
      if (b === a) continue;
      const dx = b.tx - a.tx,
        dz = b.tz - a.tz;
      const d = Math.hypot(dx, dz);
      if (d > REACH_MAX || (dx * fx + dz * fz) / d < Math.cos(0.7)) continue;
      if (best === null || d < best) best = d;
    }
    a.frontDist = best === null ? null : Math.round(best * 1000) / 1000;
  });

  // indici utili
  const find = (f) => athletes.find(f).id;
  const tronc = [0, 1, 2, 3, 4].map((k) =>
    [0, 1, 2, 3].map((c) => find((a) => a.role === 'tronc' && a.pis === k + 1 && a.col === c)),
  );
  const mans = [0, 1, 2, 3].map((c) =>
    [null, 1, 2, 3].map((j) =>
      j ? find((a) => a.role === 'mans' && a.col === c && a.j === j) : null,
    ),
  );
  const contra = [0, 1, 2, 3].map((c) => find((a) => a.role === 'contra' && a.col === c));
  const dosA = find((a) => a.role === 'dosos' && a.col === 1);
  const dosB = find((a) => a.role === 'dosos' && a.col === 3);
  const aix = find((a) => a.role === 'aix');
  const enx = find((a) => a.role === 'enx');

  // camminata dal reticolo al proprio posto o alla coda
  athletes.forEach((a, i) => {
    a.walkStart = T_HOLD + a.group * 0.12 + hash(i) * 0.6;
    a.walkDist = Math.hypot(a.tx - a.gx, a.tz - a.gz);
    a.walkDur = 0.7 + a.walkDist / 1.5;
    a.walkEnd = a.walkStart + a.walkDur;
  });
  const allArrived = Math.max(...athletes.map((a) => a.walkEnd));
  const tPinya = allArrived + 0.5;
  const tPinyaReady = tPinya + 1.3;
  athletes.forEach((a) => {
    if (!a.climber) a.arrive = tPinyaReady;
  });

  /* appoggi lungo una colonna: coscia e spalle della rengla de mans, spalle del contrafort,
     poi faixa e spalle (dietro) di ogni piano del tronc fino al piano upTo-1 */
  const holdsUp = (c, upTo) => {
    const h = [];
    h.push({ ...colPt(c, R_MANS(3) + 0.3, 0.62, 0.12), own: [mans[c][3]] });
    h.push({ ...colPt(c, R_MANS(3), 1.42, 0.17), own: [mans[c][3]] });
    h.push({ ...colPt(c, R_MANS(2), 1.42, -0.17), own: [mans[c][2]] });
    h.push({ ...colPt(c, R_MANS(1), 1.42, 0.17), own: [mans[c][1]] });
    h.push({ ...colPt(c, R_CONTRA, 1.4, -0.15), own: [contra[c]] });
    for (let j = 1; j < upTo; j++) {
      h.push({ ...colPt(c, R_COL + 0.3, Y[j] + 0.92), own: [tronc[j][c]] });
      h.push({ ...colPt(c, R_COL + 0.3, Y[j] + 1.3), own: [tronc[j][c]] });
    }
    return h;
  };
  const start = (c) => ({ ...colPt(c, R_START, 0), own: [] });
  const quintEdge = (c) => ({ ...colPt(c, R_COL + 0.14, Y[5]), own: [tronc[4][c]] });

  athletes.forEach((a) => {
    if (!a.climber) return;
    const c = a.col;
    a.ux = U[c][0];
    a.uz = U[c][1];
    if (a.role === 'tronc') {
      const k = a.pis - 1; // indice di piano 1..4
      a.up = [
        start(c),
        ...holdsUp(c, k),
        { x: COLS[c][0] * A, y: Y[k], z: COLS[c][1] * A, own: [tronc[k - 1][c]] },
      ];
    } else if (a.role === 'dosos') {
      const zs = c === 1 ? A : -A;
      const sup = c === 1 ? [tronc[4][0], tronc[4][1]] : [tronc[4][2], tronc[4][3]];
      a.up = [start(c), ...holdsUp(c, 5), quintEdge(c), { x: 0, y: Y[5], z: zs, own: sup }];
    } else if (a.role === 'aix') {
      a.up = [
        start(c),
        ...holdsUp(c, 5),
        quintEdge(c),
        { x: 0, y: Y_AIX, z: 0, own: [dosA, dosB] },
      ];
    } else {
      a.up = [
        start(c),
        ...holdsUp(c, 5),
        quintEdge(c),
        { x: 0.12, y: Y[5] + 0.86 * SC_DOSOS, z: A + 0.22, own: [dosA] },
        { x: 0, y: Y_ENX, z: 0, own: [aix] },
      ];
    }
    a.sx = a.up[a.up.length - 1].x;
    a.sz = a.up[a.up.length - 1].z;
    // discesa: lo stesso percorso al contrario; l'enxaneta scende dal lato opposto (colonna c2)
    if (a.role === 'enx') {
      a.down = [
        a.up[a.up.length - 1],
        { x: -0.12, y: Y[5] + 0.86 * SC_DOSOS, z: -A - 0.22, own: [dosB] },
        quintEdge(2),
        ...holdsUp(2, 5).reverse(),
        start(2),
      ];
      a.downCol = 2;
      const ex = colPt(2, R_QUEUE(5), 0);
      a.ex = ex.x;
      a.ez = ex.z;
    } else {
      a.down = [...a.up].reverse();
      a.downCol = c;
      a.ex = a.tx;
      a.ez = a.tz;
    }
  });

  /* istanti di passaggio sugli appoggi: ogni tratto dura in proporzione alla sua lunghezza */
  const cumTimes = (pts, speed) => {
    const out = [0];
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1],
        b = pts[i];
      out.push(out[i - 1] + HOLD_TIME + Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z) / speed);
    }
    return out;
  };
  athletes.forEach((a) => {
    if (!a.climber) return;
    a.upT = cumTimes(a.up, CLIMB_SPEED);
    a.downT = cumTimes(a.down, DOWN_SPEED);
  });

  /* salita: ogni appoggio si usa solo quando la proprietaria è in posizione */
  const climbOrder = [];
  for (let k = 1; k <= 4; k++) for (let c = 0; c < 4; c++) climbOrder.push(tronc[k][c]);
  climbOrder.push(dosA, dosB, aix, enx);
  const lastInCol = [null, null, null, null];
  for (const id of climbOrder) {
    const a = athletes[id];
    const apDur = 0.5 + Math.hypot(a.tx - a.up[0].x, a.tz - a.up[0].z) / 1.4;
    let cs = Math.max(tPinyaReady, a.walkEnd + apDur);
    const prev = lastInCol[a.col];
    if (prev !== null) cs = Math.max(cs, athletes[prev].climbStart + athletes[prev].upT[2] + 0.4); // due appoggi dietro
    a.up.forEach((h, i) => {
      if (i === 0) return;
      h.own.forEach((o) => {
        cs = Math.max(cs, athletes[o].arrive + 0.25 - a.upT[i]);
      });
    });
    a.climbStart = cs;
    a.apStart = cs - apDur;
    a.arrive = cs + a.upT[a.up.length - 1];
    lastInCol[a.col] = id;
  }

  /* aleta e discesa: dall'alto verso il basso */
  const E = athletes[enx];
  // fine della salita: aleta, poi il castell resta carregat e fermo prima che cominci la discesa
  const aletaStart = E.arrive + 0.3;
  const aletaEnd = aletaStart + 2.2;
  const HOLD_TOP = 4.0;
  // pausa tra salita e discesa: l'enxaneta resta in piedi a braccia aperte; dopo la pausa
  // si riaccovaccia (1 s) e solo allora comincia a scendere
  const tBreak = aletaEnd + HOLD_TOP;
  E.descStart = tBreak + 1.0;
  const users = new Map(); // proprietaria → [{U, i}] ultimo indice in cui U usa un suo appoggio
  const registerUsers = (a) => {
    const last = new Map();
    a.down.forEach((h, i) => h.own.forEach((o) => last.set(o, i)));
    last.forEach((i, o) => {
      if (!users.has(o)) users.set(o, []);
      users.get(o).push({ a, i });
    });
  };
  registerUsers(E);
  const descOrder = [aix, dosA, dosB];
  for (let k = 4; k >= 1; k--) for (let c = 0; c < 4; c++) descOrder.push(tronc[k][c]);
  for (const id of descOrder) {
    const a = athletes[id];
    let ds = 0;
    (users.get(id) || []).forEach(({ a: u, i }) => {
      ds = Math.max(ds, u.descStart + u.downT[i] + 0.7 * (u.downT[i + 1] - u.downT[i]) + 0.2);
    });
    a.descStart = ds;
    registerUsers(a);
  }
  athletes.forEach((a) => {
    if (!a.climber) return;
    a.descEnd = a.descStart + a.downT[a.down.length - 1];
    const last = a.down[a.down.length - 1];
    a.exitDur = 0.5 + Math.hypot(a.ex - last.x, a.ez - last.z) / 1.4;
    a.exitEnd = a.descEnd + a.exitDur;
  });
  const tRelax = Math.max(...athletes.filter((a) => a.climber).map((a) => a.descEnd)) + 0.6;
  athletes.forEach((a) => {
    if (!a.climber) a.descStart = tRelax;
  });

  // tempi per piano (per interfaccia e fasi)
  const pis = [];
  for (let p = 1; p <= 8; p++) {
    const m = athletes.filter((a) => a.pis === p && (a.role === 'tronc' || a.climber));
    pis[p] = {
      members: m,
      start: p === 1 ? tPinya : Math.min(...m.map((a) => a.climbStart)),
      firstArr: Math.min(...m.map((a) => a.arrive)),
      arrive: Math.max(...m.map((a) => a.arrive)),
      descStart: Math.min(...m.map((a) => a.descStart)),
      descEnd: p === 1 ? tRelax : Math.max(...m.map((a) => a.descEnd)),
    };
  }
  // descent: istante in cui comincia la fase di discesa (la riproduzione si ferma qui)
  const T = {
    allArrived,
    tPinya,
    tPinyaReady,
    aletaStart,
    aletaEnd,
    descent: tBreak,
    tRelax,
    end: tRelax + 4,
  };

  /* Server (Node) e browser calcolano sin/cos/hypot con differenze infinitesime: arrotondando
     i tempi al millesimo di secondo il render lato server coincide con quello del client
     (niente errori di idratazione). */
  const q3 = (x) => (typeof x === 'number' ? Math.round(x * 1000) / 1000 : x);
  const TIME_KEYS = [
    'walkStart',
    'walkDur',
    'walkEnd',
    'apStart',
    'climbStart',
    'arrive',
    'descStart',
    'descEnd',
    'exitDur',
    'exitEnd',
  ];
  athletes.forEach((a) =>
    TIME_KEYS.forEach((k) => {
      if (k in a) a[k] = q3(a[k]);
    }),
  );
  Object.keys(T).forEach((k) => {
    T[k] = q3(T[k]);
  });
  pis.forEach((p) => {
    if (p)
      ['start', 'firstArr', 'arrive', 'descStart', 'descEnd'].forEach((k) => {
        p[k] = q3(p[k]);
      });
  });

  return { athletes, T, pis, ids: { tronc, dosA, dosB, aix, enx } };
}

export { buildPlan };
