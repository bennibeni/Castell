'use client';

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

import React, { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

/* ─────────────────────────── utilità ─────────────────────────── */
const TAU = Math.PI * 2;
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (x) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
const ramp = (t, a, b) => smooth((t - a) / (b - a));
const lerp = (a, b, u) => a + (b - a) * u;
const angLerp = (a, b, u) => {
  const d = ((((b - a + Math.PI) % TAU) + TAU) % TAU) - Math.PI;
  return a + d * u;
};
const hash = (i) => { const s = Math.sin(i * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };

/* ─────────────────────────── corpo ─────────────────────────── */
const HIP = 0.9;
const squatAngle = (s) => s * 1.25;
const hipHeight = (s) => HIP * Math.cos(squatAngle(s));
const shoulderHeight = (s, leanK) => hipHeight(s) + 0.02 + 0.47 * Math.cos(s * leanK) + 0.03;
const headTopOf = (s, leanK, scale) => scale * (hipHeight(s) + 0.02 + 0.75 * Math.cos(s * leanK));

/* ─────────────────────────── geometria del castell ─────────────────────────── */
const VIDEO_DIR = Math.PI / 4;      // direzione (+x,+z): da lì riprende la camera
const T_HOLD = 2.5;                 // secondi di reticolo fermo
const GRID = { cols: 10, rows: 9, step: 1.0 };
const A = 0.32;                     // semilato del quadrato del tronc (4 colonne)
const COLS = [[1, 1], [-1, 1], [-1, -1], [1, -1]]; // c0 è la colonna verso la camera
const U = COLS.map(([x, z]) => [x / Math.SQRT2, z / Math.SQRT2]);
const R_COL = A * Math.SQRT2;       // distanza delle colonne dall'asse
const R_CONTRA = R_COL + 0.42;
const R_MANS = (j) => R_CONTRA + 0.45 * j;
const R_START = 3.5;                // da qui si comincia a salire (varco nel darrer cordó)
const R_QUEUE = (i) => 4.1 + 0.6 * i;
const CLIMB_SPEED = 1.0;            // m/s lungo il percorso in salita (passo costante)
const DOWN_SPEED = 1.3;             // m/s in discesa
const HOLD_TIME = 0.25;             // s in più per ogni appoggio (cambio di presa)

// accosciamento (s) e scala delle varie figure
const S_BAIX = 0.1, S_TRONC = 0.06, S_DOSOS = 0.15, S_AIX = 0.75, S_ENX = 0.7;
const SC_DOSOS = 0.86, SC_AIX = 0.82, SC_ENX = 0.78; // il pom de dalt: atlete più minute

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
const PIS_NAMES = ['Baixos', 'Segons', 'Terços', 'Quarts', 'Quints', 'Dosos', 'Aixecador', 'Enxaneta'];
const PIS_COLORS = ['#ef6f4f', '#f2a93b', '#cfd64a', '#5ccf7a', '#3fc4c9', '#5b8ff0', '#a07ff0', '#f26aa8'];
const PINYA_COLOR = '#8d939c';
const CAP_COLOR = '#d9b45c';
const NAVY = '#1f2b4f';
const FOV = 42;                      // campo visivo verticale della camera (gradi)
const FRAME_BOTTOM = -0.62;          // posizione verticale del pavimento sullo schermo (-1 = fondo, 1 = cima)
const FRAME_TOP = 0.88;              // posizione verticale della cima (+2 m) sullo schermo
const MANNEQUIN_COLOR = '#cfc6b6';   // legno chiaro dei manichini
const JOINT_COLOR = '#1b1f2a';       // articolazioni evidenziate
// masse ipotizzate (kg) per il calcolo del carico sui baixos
const MASS = { 1: 70, 2: 62, 3: 55, 4: 50, 5: 32, 6: 26, 7: 20 };

/* ─────────────────────────── piano della coreografia ─────────────────────────── */
function buildPlan() {
  const grid = [];
  for (let r = 0; r < GRID.rows; r++)
    for (let c = 0; c < GRID.cols; c++)
      grid.push({ gx: (c - (GRID.cols - 1) / 2) * GRID.step, gz: (r - (GRID.rows - 1) / 2) * GRID.step });

  // posti a terra (gruppi in ordine di distanza dal centro) + code di chi salirà
  const slots = [];
  const add = (group, role, x, z, extra = {}) => slots.push({ group, role, x, z, pis: 0, col: -1, scale: 1, ...extra });
  add(0, 'agulla', 0, 0);
  COLS.forEach(([cx, cz], c) => add(1, 'tronc', cx * A, cz * A, { pis: 1, col: c }));
  U.forEach((u, c) => [1, -1].forEach((sg) => { const p = colPt(c, R_COL + 0.2, 0, 0.3 * sg); add(2, 'cross', p.x, p.z, { col: c }); }));
  U.forEach((u, c) => { const p = colPt(c, R_CONTRA, 0); add(3, 'contra', p.x, p.z, { col: c }); });
  for (let j = 1; j <= 3; j++) U.forEach((u, c) => { const p = colPt(c, R_MANS(j), 0); add(4, 'mans', p.x, p.z, { col: c, j }); });
  [[1, 0], [0, 1], [-1, 0], [0, -1]].forEach(([dx, dz]) => [1.0, 1.45, 1.9].forEach((r) => add(5, 'vent', dx * r, dz * r)));
  U.forEach((u) => [1, -1].forEach((sg) => {
    const ang = Math.atan2(u[1], u[0]) + (sg * Math.PI) / 8;
    [1.4, 1.85].forEach((r) => add(6, 'lateral', r * Math.cos(ang), r * Math.sin(ang)));
  }));
  for (let k = 0; k < 12; k++) add(7, 'cordo', 3.0 * Math.cos((k * Math.PI) / 6), 3.0 * Math.sin((k * Math.PI) / 6));
  add(8, 'cap', 3.85, 0);
  // code: per ogni colonna segon, terç, quart, quint e un membro del pom de dalt
  const POM_BY_COL = ['enx', 'dosos', 'aix', 'dosos'];
  for (let c = 0; c < 4; c++)
    for (let i = 0; i < 5; i++) {
      const q = colPt(c, R_QUEUE(i), 0);
      const role = i < 4 ? 'tronc' : POM_BY_COL[c];
      const pis = i < 4 ? i + 2 : role === 'dosos' ? 6 : role === 'aix' ? 7 : 8;
      const scale = role === 'dosos' ? SC_DOSOS : role === 'aix' ? SC_AIX : role === 'enx' ? SC_ENX : 1;
      add(9, role, q.x, q.z, { pis, col: c, climber: true, scale });
    }

  // abbinamento reticolo → posti: le più vicine al centro fanno pinya e base, le più lontane salgono
  const order = grid
    .map((p) => ({ ...p, d: Math.round(Math.hypot(p.gx, p.gz) * 1e6) / 1e6, a: Math.round(Math.atan2(p.gz, p.gx) * 1e6) / 1e6 }))
    .sort((a, b) => a.d - b.d || a.a - b.a);
  const groups = [...new Set(slots.map((s) => s.group))].sort((a, b) => a - b);
  let ptr = 0;
  const athletes = [];
  for (const gi of groups) {
    const S = slots.filter((s) => s.group === gi).map((s) => ({ ...s, ang: Math.round(Math.atan2(s.z, s.x) * 1e6) / 1e6 })).sort((a, b) => a.ang - b.ang);
    const n = S.length;
    const P = order.slice(ptr, ptr + n).sort((a, b) => a.a - b.a);
    ptr += n;
    let best = 0, bestCost = Infinity;
    for (let sh = 0; sh < n; sh++) {
      let cost = 0;
      for (let i = 0; i < n; i++) { const p = P[(i + sh) % n]; cost += Math.hypot(p.gx - S[i].x, p.gz - S[i].z); }
      if (cost < bestCost) { bestCost = cost; best = sh; }
    }
    for (let i = 0; i < n; i++) {
      const p = P[(i + best) % n];
      const s = S[i];
      athletes.push({ ...s, gx: p.gx, gz: p.gz, tx: s.x, tz: s.z });
    }
  }
  athletes.forEach((a, i) => { a.id = i; });

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
      const dx = b.tx - a.tx, dz = b.tz - a.tz;
      const d = Math.hypot(dx, dz);
      if (d > REACH_MAX || (dx * fx + dz * fz) / d < Math.cos(0.7)) continue;
      if (best === null || d < best) best = d;
    }
    a.frontDist = best === null ? null : Math.round(best * 1000) / 1000;
  });

  // indici utili
  const find = (f) => athletes.find(f).id;
  const tronc = [0, 1, 2, 3, 4].map((k) => [0, 1, 2, 3].map((c) => find((a) => a.role === 'tronc' && a.pis === k + 1 && a.col === c)));
  const mans = [0, 1, 2, 3].map((c) => [null, 1, 2, 3].map((j) => (j ? find((a) => a.role === 'mans' && a.col === c && a.j === j) : null)));
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
  athletes.forEach((a) => { if (!a.climber) a.arrive = tPinyaReady; });

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
    a.ux = U[c][0]; a.uz = U[c][1];
    if (a.role === 'tronc') {
      const k = a.pis - 1; // indice di piano 1..4
      a.up = [start(c), ...holdsUp(c, k), { x: COLS[c][0] * A, y: Y[k], z: COLS[c][1] * A, own: [tronc[k - 1][c]] }];
    } else if (a.role === 'dosos') {
      const zs = c === 1 ? A : -A;
      const sup = c === 1 ? [tronc[4][0], tronc[4][1]] : [tronc[4][2], tronc[4][3]];
      a.up = [start(c), ...holdsUp(c, 5), quintEdge(c), { x: 0, y: Y[5], z: zs, own: sup }];
    } else if (a.role === 'aix') {
      a.up = [start(c), ...holdsUp(c, 5), quintEdge(c), { x: 0, y: Y_AIX, z: 0, own: [dosA, dosB] }];
    } else {
      a.up = [start(c), ...holdsUp(c, 5), quintEdge(c), { x: 0.12, y: Y[5] + 0.86 * SC_DOSOS, z: A + 0.22, own: [dosA] }, { x: 0, y: Y_ENX, z: 0, own: [aix] }];
    }
    a.sx = a.up[a.up.length - 1].x; a.sz = a.up[a.up.length - 1].z;
    // discesa: lo stesso percorso al contrario; l'enxaneta scende dal lato opposto (colonna c2)
    if (a.role === 'enx') {
      a.down = [a.up[a.up.length - 1], { x: -0.12, y: Y[5] + 0.86 * SC_DOSOS, z: -A - 0.22, own: [dosB] }, quintEdge(2), ...holdsUp(2, 5).reverse(), start(2)];
      a.downCol = 2;
      const ex = colPt(2, R_QUEUE(5), 0); a.ex = ex.x; a.ez = ex.z;
    } else {
      a.down = [...a.up].reverse();
      a.downCol = c;
      a.ex = a.tx; a.ez = a.tz;
    }
  });

  /* istanti di passaggio sugli appoggi: ogni tratto dura in proporzione alla sua lunghezza */
  const cumTimes = (pts, speed) => {
    const out = [0];
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i];
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
      h.own.forEach((o) => { cs = Math.max(cs, athletes[o].arrive + 0.25 - a.upT[i]); });
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
    last.forEach((i, o) => { if (!users.has(o)) users.set(o, []); users.get(o).push({ a, i }); });
  };
  registerUsers(E);
  const descOrder = [aix, dosA, dosB];
  for (let k = 4; k >= 1; k--) for (let c = 0; c < 4; c++) descOrder.push(tronc[k][c]);
  for (const id of descOrder) {
    const a = athletes[id];
    let ds = 0;
    (users.get(id) || []).forEach(({ a: u, i }) => { ds = Math.max(ds, u.descStart + u.downT[i] + 0.7 * (u.downT[i + 1] - u.downT[i]) + 0.2); });
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
  athletes.forEach((a) => { if (!a.climber) a.descStart = tRelax; });

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
  const T = { allArrived, tPinya, tPinyaReady, aletaStart, aletaEnd, descent: tBreak, tRelax, end: tRelax + 4 };

  /* Server (Node) e browser calcolano sin/cos/hypot con differenze infinitesime: arrotondando
     i tempi al millesimo di secondo il render lato server coincide con quello del client
     (niente errori di idratazione). */
  const q3 = (x) => (typeof x === 'number' ? Math.round(x * 1000) / 1000 : x);
  const TIME_KEYS = ['walkStart', 'walkDur', 'walkEnd', 'apStart', 'climbStart', 'arrive', 'descStart', 'descEnd', 'exitDur', 'exitEnd'];
  athletes.forEach((a) => TIME_KEYS.forEach((k) => { if (k in a) a[k] = q3(a[k]); }));
  Object.keys(T).forEach((k) => { T[k] = q3(T[k]); });
  pis.forEach((p) => { if (p) ['start', 'firstArr', 'arrive', 'descStart', 'descEnd'].forEach((k) => { p[k] = q3(p[k]); }); });

  return { athletes, T, pis, ids: { tronc, dosA, dosB, aix, enx } };
}

/* ─────────────────────────── pose ─────────────────────────── */
const A_DOWN = [0.05, 0.12, -0.15];
// nessuna posa porta le mani sopra le spalle
const A_LINK = [-0.45, 0.35, -1.35];   // tronc: gomiti piegati, mani raccolte davanti al petto
const A_CROSS = [-1.15, 0.35, -1.2];   // crosses: sorreggono i baixos sotto le ascelle
const A_AIX = [-0.4, 0.5, -1.0];      // aixecador: mani appoggiate sulle teste dei dosos, gomiti piegati
const A_DOSOS = [-0.95, 0.2, -1.2];   // le due dosos, una di fronte all'altra, si tengono per le spalle
const REACH_MAX = 0.8;                 // oltre questa distanza (m) nessun contatto: braccia giù

/** braccia di chi appoggia le mani su una compagna a distanza d davanti (più lontana = braccia più distese) */
function reachArms(d) {
  if (d === null || d === undefined) return A_DOWN;
  const u = clamp01((d - 0.4) / 0.4);
  return [lerp(-0.75, -1.1, u), 0.2, lerp(-1.35, -0.85, u)]; // gomiti sempre piegati
}
const A_OPEN = [-0.1, 1.45, -0.05];    // enxaneta: braccia aperte all'orizzontale

const newPose = () => ({
  x: 0, y: 0, z: 0, yaw: 0, hipY: HIP, thL: 0, thR: 0, knL: 0, knR: 0, spread: 0, lean: 0,
  aL: [0, 0, 0], aR: [0, 0, 0],
});
const setA = (arr, v) => { arr[0] = v[0]; arr[1] = v[1]; arr[2] = v[2]; };
const mixInto = (arr, v, w) => { arr[0] = lerp(arr[0], v[0], w); arr[1] = lerp(arr[1], v[1], w); arr[2] = lerp(arr[2], v[2], w); };
const bothArms = (p, v) => { setA(p.aL, v); setA(p.aR, v); };
const mixBoth = (p, v, w) => { mixInto(p.aL, v, w); mixInto(p.aR, v, w); };

/** accosciamento dell'enxaneta: accovacciata in salita e in discesa, in piedi da carregat */
function enxUp(T, t) {
  return ramp(t, T.aletaStart, T.aletaStart + 1.0) * (1 - ramp(t, T.descent + 0.05, T.descent + 0.85));
}
function enxSquat(T, t) {
  return lerp(S_ENX, 0.1, enxUp(T, t));
}

function standPose(p, s, lean, spread) {
  const th = squatAngle(s);
  p.hipY = HIP * Math.cos(th);
  p.thL = p.thR = -th;
  p.knL = p.knR = 2 * th;
  p.lean = lean;
  p.spread = spread;
}
function blendLimbs(p, q, w) {
  p.hipY = lerp(p.hipY, q.hipY, w);
  p.thL = lerp(p.thL, q.thL, w); p.thR = lerp(p.thR, q.thR, w);
  p.knL = lerp(p.knL, q.knL, w); p.knR = lerp(p.knR, q.knR, w);
  p.spread = lerp(p.spread, q.spread, w); p.lean = lerp(p.lean, q.lean, w);
  p.yaw = angLerp(p.yaw, q.yaw, w);
  mixInto(p.aL, q.aL, w); mixInto(p.aR, q.aR, w);
}

function walkPose(p, fx, fz, tx, tz, u, dist, yaw0, yaw1) {
  const e = smooth(u);
  p.x = lerp(fx, tx, e); p.z = lerp(fz, tz, e); p.y = 0;
  const mv = dist > 0.05 ? Math.atan2(tx - fx, tz - fz) : yaw1;
  p.yaw = angLerp(angLerp(yaw0, mv, ramp(u, 0, 0.18)), yaw1, ramp(u, 0.82, 1));
  const env = clamp01(Math.min(u * 5, (1 - u) * 5));
  const ph = ((e * dist) / 0.62) * Math.PI;
  standPose(p, 0.04, 0.02, 0);
  const sw = 0.5 * env * Math.sin(ph);
  p.thL -= sw; p.thR += sw;
  p.knL += env * 0.55 * Math.max(0, Math.sin(ph + 1.3));
  p.knR += env * 0.55 * Math.max(0, -Math.sin(ph + 1.3));
  p.hipY -= 0.035 * env * Math.abs(Math.sin(ph));
  p.aL[0] = 0.8 * sw; p.aL[1] = 0.12; p.aL[2] = -0.3;
  p.aR[0] = -0.8 * sw; p.aR[1] = 0.12; p.aR[2] = -0.3;
}

/**
 * posizione lungo la sequenza di appoggi: curva di Catmull-Rom che passa per tutti gli appoggi,
 * percorsa senza soste a passo costante (times = istanti di passaggio sugli appoggi), con partenza e arrivo dolci.
 * Niente archi né pause: il corpo sale in modo continuo, come in un'arrampicata vera.
 */
function pathAt(pts, times, t0, t, p) {
  const n = pts.length;
  const x = t - t0;
  if (x <= 0) { p.x = pts[0].x; p.y = pts[0].y; p.z = pts[0].z; return { i: 0, f: 0 }; }
  if (x >= times[n - 1]) { const l = pts[n - 1]; p.x = l.x; p.y = l.y; p.z = l.z; return { i: n - 2, f: 1 }; }
  let i = 0;
  while (i < n - 2 && x >= times[i + 1]) i++;
  const f = (x - times[i]) / (times[i + 1] - times[i]);
  // partenza e arrivo dolci, velocità continua in mezzo
  const g = n === 2 ? smooth(f) : i === 0 ? f * f : i === n - 2 ? 1 - (1 - f) * (1 - f) : f;
  const P0 = pts[Math.max(0, i - 1)], P1 = pts[i], P2 = pts[i + 1], P3 = pts[Math.min(n - 1, i + 2)];
  const g2 = g * g, g3 = g2 * g;
  const cr = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * g + (2 * a - 5 * b + 4 * c - d) * g2 + (-a + 3 * b - 3 * c + d) * g3);
  p.x = cr(P0.x, P1.x, P2.x, P3.x);
  p.y = cr(P0.y, P1.y, P2.y, P3.y);
  p.z = cr(P0.z, P1.z, P2.z, P3.z);
  return { i, f };
}

/**
 * arti durante l'arrampicata: a ogni appoggio una gamba sale (ginocchio alto) mentre l'altra
 * spinge e si distende; la mano dello stesso lato cerca la presa più in alto, l'altra tira.
 * Tutto è continuo (seno del tratto): nessun balzo.
 */
function climbLimbs(p, i, f) {
  const lift = Math.sin(Math.PI * f);          // 0 all'appoggio, 1 a metà tratto
  const left = i % 2 === 0;                      // gamba e braccio guida si alternano
  const lead = { th: -(0.5 + 0.95 * lift), kn: 0.7 + 1.25 * lift };
  const push = { th: -(0.5 - 0.35 * lift), kn: 0.7 - 0.45 * lift };
  const L = left ? lead : push, R = left ? push : lead;
  p.hipY = 0.84;
  p.thL = L.th; p.knL = L.kn;
  p.thR = R.th; p.knR = R.kn;
  p.lean = 0.28; p.spread = 0.1;
  const reach = [-1.4 - 0.45 * lift, 0.3, -1.3 + 0.35 * lift]; // mano che sale verso la presa (gomito piegato)
  const pull = [-1.25 + 0.2 * lift, 0.25, -1.35];              // mano che tira il corpo verso l'alto
  setA(p.aL, left ? reach : pull);
  setA(p.aR, left ? pull : reach);
}

/** posa "in posizione" di ciascun ruolo */
function rolePose(a, t, P, q) {
  const { T } = P;
  q.x = a.sx ?? a.tx; q.z = a.sz ?? a.tz;
  q.yaw = Math.hypot(q.x, q.z) < 0.01 ? Math.PI / 2 : Math.atan2(-q.x, -q.z);
  q.y = 0;
  const on = ramp(t, T.tPinya, T.tPinya + 1.2) * (1 - ramp(t, T.tRelax, T.tRelax + 1.5));
  bothArms(q, A_DOWN);
  switch (a.role) {
    case 'agulla':
      q.yaw = VIDEO_DIR;
      standPose(q, 0.55 * on, 0.15 * on, 0.15 * on); mixBoth(q, reachArms(a.frontDist), on); return;
    case 'cross':
      standPose(q, 0.45 * on, 0.35 * on, 0.1 * on); mixBoth(q, A_CROSS, on); return;
    case 'contra':
      standPose(q, 0.25 * on, 0.5 * on, 0.1 * on); mixBoth(q, reachArms(a.frontDist), on); return;
    case 'mans':
      standPose(q, 0.1 * on, 0.2 * on, 0.08 * on); mixBoth(q, reachArms(a.frontDist), on); return;
    case 'vent': case 'lateral': case 'cordo':
      // chi non ha nessuno a portata resta più dritta, con le braccia lungo i fianchi
      standPose(q, 0.12 * on, (a.frontDist === null ? 0.05 : 0.2) * on, 0.1 * on); mixBoth(q, reachArms(a.frontDist), on); return;
    case 'cap':
      standPose(q, 0, 0, 0); return;
    case 'tronc': {
      const k = a.pis - 1;
      if (k === 0) {
        standPose(q, S_BAIX * on, 0.06 * on, 0.12 * on);
        mixBoth(q, A_LINK, on);
        return;
      }
      q.y = Y[k];
      standPose(q, S_TRONC, 0.04, 0.05);
      bothArms(q, A_LINK);
      return;
    }
    case 'dosos':
      q.y = Y[5]; standPose(q, S_DOSOS, 0.06, 0.32); bothArms(q, A_DOSOS); return;
    case 'aix':
      q.y = Y_AIX; q.yaw = Math.PI / 2; standPose(q, S_AIX, 0.5, 0.45); bothArms(q, A_AIX); return;
    case 'enx': {
      // in piedi sulla schiena dell'aixecador, braccia aperte, per tutto il tempo del castell carregat
      q.y = Y_ENX; q.yaw = angLerp(Math.PI / 2, VIDEO_DIR, enxUp(T, t)); standPose(q, enxSquat(T, t), 0.45, 0.2); // in piedi si gira verso il pubblico
      bothArms(q, A_AIX);
      mixBoth(q, A_OPEN, ramp(t, T.aletaStart + 0.6, T.aletaStart + 1.4) * (1 - ramp(t, T.descent, T.descent + 0.6)));
      return;
    }
    default:
      standPose(q, 0, 0, 0);
  }
}

function computePose(a, t, P, p, q) {
  // 1 · reticolo
  if (t < a.walkStart) {
    p.x = a.gx; p.y = 0; p.z = a.gz; p.yaw = VIDEO_DIR;
    standPose(p, 0.02, 0.01, 0); bothArms(p, A_DOWN);
    return;
  }
  const towerYaw = a.climber ? Math.atan2(-a.ux, -a.uz) : Math.atan2(-a.tx, -a.tz);
  // 2 · implosione
  if (t < a.walkEnd) {
    const endYaw = a.role === 'agulla' ? VIDEO_DIR : towerYaw;
    walkPose(p, a.gx, a.gz, a.tx, a.tz, (t - a.walkStart) / a.walkDur, a.walkDist, VIDEO_DIR, endYaw);
    return;
  }
  // pinya e baixos: restano al loro posto
  if (!a.climber) { rolePose(a, t, P, p); return; }

  // 3 · in coda
  if (t < a.apStart) {
    p.x = a.tx; p.y = 0; p.z = a.tz; p.yaw = towerYaw;
    standPose(p, 0.03, 0.02, 0); bothArms(p, A_DOWN);
    return;
  }
  // 4 · dalla coda al punto di partenza, nel varco del darrer cordó
  if (t < a.climbStart) {
    const s0 = a.up[0];
    const d = Math.hypot(s0.x - a.tx, s0.z - a.tz);
    walkPose(p, a.tx, a.tz, s0.x, s0.z, (t - a.apStart) / (a.climbStart - a.apStart), d, towerYaw, towerYaw);
    return;
  }
  // 5 · salita appoggio per appoggio
  if (t < a.arrive) {
    const st = pathAt(a.up, a.upT, a.climbStart, t, p);
    p.yaw = towerYaw;
    climbLimbs(p, st.i, st.f);
    if (st.i === a.up.length - 2) { rolePose(a, t, P, q); blendLimbs(p, q, smooth(st.f)); }
    return;
  }
  // 6 · in posizione
  if (t < a.descStart) { rolePose(a, t, P, p); return; }
  // 7 · discesa
  const downYaw = Math.atan2(-U[a.downCol][0], -U[a.downCol][1]);
  if (t < a.descEnd) {
    const st = pathAt(a.down, a.downT, a.descStart, t, p);
    p.yaw = downYaw;
    climbLimbs(p, st.i, st.f);
    if (st.i === 0) { rolePose(a, a.descStart, P, q); const px = p.x, py = p.y, pz = p.z; blendLimbs(p, q, 1 - smooth(st.f / 0.5)); p.x = px; p.y = py; p.z = pz; }
    return;
  }
  // 8 · torna in coda
  const last = a.down[a.down.length - 1];
  if (t < a.exitEnd) {
    const d = Math.hypot(a.ex - last.x, a.ez - last.z);
    walkPose(p, last.x, last.z, a.ex, a.ez, (t - a.descEnd) / a.exitDur, d, downYaw, downYaw);
    return;
  }
  p.x = a.ex; p.y = 0; p.z = a.ez; p.yaw = downYaw;
  standPose(p, 0.03, 0.02, 0); bothArms(p, A_DOWN);
}

function applyPose(rig, p, scale) {
  rig.root.position.set(p.x, p.y, p.z);
  rig.root.rotation.y = p.yaw;
  rig.root.scale.setScalar(scale);
  rig.hips.position.y = p.hipY;
  rig.thighL.rotation.set(p.thL, 0, p.spread);
  rig.thighR.rotation.set(p.thR, 0, -p.spread);
  rig.kneeL.rotation.x = p.knL;
  rig.kneeR.rotation.x = p.knR;
  rig.torso.rotation.x = p.lean;
  rig.armL.rotation.set(p.aL[0], 0, p.aL[1]);
  rig.armR.rotation.set(p.aR[0], 0, -p.aR[1]);
  rig.elbowL.rotation.x = p.aL[2];
  rig.elbowR.rotation.x = p.aR[2];
}

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
  for (const a of P.athletes) if ((a.role === 'tronc' || a.climber) && present(a, t)) top = Math.max(top, headTopRole(a, t, P.T));
  return top;
}

function baixLoadAt(P, t) {
  let col = 0, pom = 0;
  for (const a of P.athletes) {
    if (!a.climber || !present(a, t)) continue;
    const m = MASS[a.pis - 1] ?? 0;
    if (a.role === 'tronc') col += m; else pom += m;
  }
  return (col + pom) / 4;
}

/* ─────────────────────────── grafica ─────────────────────────── */
function makeGeometries() {
  return {
    thigh: new THREE.CapsuleGeometry(0.068, 0.31, 4, 10),
    shin: new THREE.CapsuleGeometry(0.052, 0.32, 4, 10),
    foot: new THREE.BoxGeometry(0.085, 0.05, 0.21),
    pelvis: new THREE.SphereGeometry(0.13, 14, 10),
    waist: new THREE.CapsuleGeometry(0.1, 0.1, 4, 12),
    chest: new THREE.CapsuleGeometry(0.125, 0.13, 4, 12),
    neck: new THREE.CylinderGeometry(0.045, 0.05, 0.09, 10),
    head: new THREE.SphereGeometry(0.102, 16, 12),
    hair: new THREE.SphereGeometry(0.108, 16, 12, 0, TAU, 0, Math.PI * 0.62),
    bun: new THREE.SphereGeometry(0.052, 10, 8),
    upper: new THREE.CapsuleGeometry(0.043, 0.2, 4, 8),
    fore: new THREE.CapsuleGeometry(0.038, 0.19, 4, 8),
    hand: new THREE.SphereGeometry(0.042, 8, 6),
    joint: new THREE.SphereGeometry(0.062, 12, 10),
    nose: new THREE.SphereGeometry(0.028, 8, 6),
  };
}

function makeMaterials() {
  return {
    skin: new THREE.MeshStandardMaterial({ color: '#d6a07a', roughness: 0.55 }),
    navy: new THREE.MeshStandardMaterial({ color: NAVY, roughness: 0.42, metalness: 0.08 }),
    hair: new THREE.MeshStandardMaterial({ color: '#3a2618', roughness: 0.7 }),
    joint: new THREE.MeshStandardMaterial({ color: JOINT_COLOR, roughness: 0.35, metalness: 0.2 }),
  };
}

/**
 * mannequin = true: corpo di un solo colore neutro (o del colore del ruolo), senza body,
 * capelli né dettagli; articolazioni (anche, ginocchia, spalle, gomiti) evidenziate
 * da sfere scure e un piccolo "naso" che indica dove guarda la figura.
 */
const Figure = memo(function Figure({ index, geo, mats, register, mannequin }) {
  // un ref per ogni articolazione: vengono letti solo nell'effetto, mai durante il render
  const root = useRef(null);
  const hips = useRef(null);
  const thighL = useRef(null);
  const thighR = useRef(null);
  const kneeL = useRef(null);
  const kneeR = useRef(null);
  const torso = useRef(null);
  const armL = useRef(null);
  const armR = useRef(null);
  const elbowL = useRef(null);
  const elbowR = useRef(null);
  const leo = useMemo(() => mats.navy.clone(), [mats]);

  useLayoutEffect(() => {
    register(index, {
      root: root.current, hips: hips.current,
      thighL: thighL.current, thighR: thighR.current,
      kneeL: kneeL.current, kneeR: kneeR.current,
      torso: torso.current,
      armL: armL.current, armR: armR.current,
      elbowL: elbowL.current, elbowR: elbowR.current,
      leo,
    });
  }, [index, register, leo]);

  // nel manichino tutto il corpo usa il materiale della figura (colore neutro o del ruolo)
  const skin = mannequin ? leo : mats.skin;
  const joint = (s) => (mannequin ? <mesh geometry={geo.joint} material={mats.joint} scale={s} /> : null);

  return (
    <group ref={root}>
      <group ref={hips} position={[0, HIP, 0]}>
        <mesh geometry={geo.pelvis} material={leo} position={[0, 0.02, 0]} scale={[1.2, 0.75, 0.85]} />
        {[1, -1].map((sd) => (
          <group key={sd} ref={sd > 0 ? thighL : thighR} position={[sd * 0.09, -0.02, 0]}>
            {joint(1.15)}
            <mesh geometry={geo.thigh} material={skin} position={[0, -0.215, 0]} />
            <group ref={sd > 0 ? kneeL : kneeR} position={[0, -0.43, 0]}>
              {joint(1)}
              <mesh geometry={geo.shin} material={skin} position={[0, -0.215, 0]} />
              <mesh geometry={geo.foot} material={skin} position={[0, -0.44, 0.05]} />
            </group>
          </group>
        ))}
        <group ref={torso} position={[0, 0.02, 0]}>
          <mesh geometry={geo.waist} material={skin} position={[0, 0.16, 0]} scale={[1.05, 1, 0.78]} />
          <mesh geometry={geo.chest} material={leo} position={[0, 0.36, 0]} scale={[1.18, 1, 0.78]} />
          <mesh geometry={geo.neck} material={skin} position={[0, 0.54, 0]} />
          <mesh geometry={geo.head} material={skin} position={[0, 0.65, 0]} />
          {mannequin ? (
            <mesh geometry={geo.nose} material={mats.joint} position={[0, 0.65, 0.1]} />
          ) : (
            <>
              <mesh geometry={geo.hair} material={mats.hair} position={[0, 0.655, -0.012]} rotation={[-0.45, 0, 0]} />
              <mesh geometry={geo.bun} material={mats.hair} position={[0, 0.745, -0.075]} />
            </>
          )}
          {[1, -1].map((sd) => (
            <group key={sd} ref={sd > 0 ? armL : armR} position={[sd * 0.19, 0.47, 0]}>
              {joint(0.95)}
              <mesh geometry={geo.upper} material={leo} position={[0, -0.143, 0]} />
              <group ref={sd > 0 ? elbowL : elbowR} position={[0, -0.29, 0]}>
                {joint(0.8)}
                <mesh geometry={geo.fore} material={leo} position={[0, -0.133, 0]} />
                <mesh geometry={geo.hand} material={skin} position={[0, -0.285, 0]} />
              </group>
            </group>
          ))}
        </group>
      </group>
    </group>
  );
});

function Audience() {
  const ref = useRef();
  const data = useMemo(() => {
    const out = [];
    const palette = ['#1c1f28', '#262a35', '#14171f', '#2e2a33', '#3a2f30', '#1f2838', '#3c3f47', '#181b28', '#5a3f45'];
    let i = 0;
    for (let side = 0; side < 2; side++)
      for (let row = 0; row < 9; row++)
        for (let j = 0; j < 32; j++) {
          i++;
          if (hash(i * 3.1) < 0.12) continue;
          const along = -12.4 + j * 0.8 + (row % 2) * 0.4;
          const depth = 10.8 + row * 0.9;
          const h = (row + 1) * 0.5;
          const x = side === 0 ? -depth : along;
          const z = side === 0 ? along : -depth;
          out.push({ x, y: h + 0.45, z, s: 0.9 + hash(i) * 0.25, c: palette[Math.floor(hash(i * 7.7) * palette.length)] });
        }
    return out;
  }, []);
  const headRef = useRef();
  useLayoutEffect(() => {
    const m = new THREE.Object3D();
    const c = new THREE.Color();
    const skins = ['#7a5a48', '#8a6a55', '#5e4436', '#9a7a62'];
    data.forEach((d, i) => {
      m.position.set(d.x, d.y, d.z);
      m.scale.set(1, d.s, 1);
      m.updateMatrix();
      ref.current.setMatrixAt(i, m.matrix);
      ref.current.setColorAt(i, c.set(d.c));
      m.position.set(d.x, d.y + 0.36 * d.s + 0.2, d.z);
      m.scale.set(1, 1, 1);
      m.updateMatrix();
      headRef.current.setMatrixAt(i, m.matrix);
      headRef.current.setColorAt(i, c.set(skins[i % skins.length]));
    });
    for (const r of [ref.current, headRef.current]) {
      r.instanceMatrix.needsUpdate = true;
      if (r.instanceColor) r.instanceColor.needsUpdate = true;
    }
  }, [data]);
  return (
    <group>
      <instancedMesh ref={ref} args={[undefined, undefined, data.length]}>
        <capsuleGeometry args={[0.21, 0.32, 4, 8]} />
        <meshStandardMaterial roughness={0.95} />
      </instancedMesh>
      <instancedMesh ref={headRef} args={[undefined, undefined, data.length]}>
        <sphereGeometry args={[0.12, 10, 8]} />
        <meshStandardMaterial roughness={0.9} />
      </instancedMesh>
    </group>
  );
}

function Arena() {
  const steps = [];
  for (let side = 0; side < 2; side++)
    for (let row = 0; row < 9; row++) {
      const depth = 10.8 + row * 0.9;
      const h = (row + 1) * 0.5;
      steps.push(
        <mesh key={`${side}-${row}`} position={side === 0 ? [-depth, h / 2, 0] : [0, h / 2, -depth]}>
          <boxGeometry args={side === 0 ? [0.9, h, 26] : [26, h, 0.9]} />
          <meshStandardMaterial color="#17171c" roughness={0.95} />
        </mesh>,
      );
    }
  const lamps = [[-11, 13, -18, '#ff2b3d'], [-19, 12.5, -8, '#ff2b3d'], [-3, 15, -21, '#ff2b3d'], [6, 17, -21, '#fff6e0'], [-21, 16, 4, '#fff6e0']];
  const lines = [[0, 7.6, 16, 0.06], [0, -7.6, 16, 0.06], [7.6, 0, 0.06, 16], [-7.6, 0, 0.06, 16]];
  return (
    <group>
      <mesh rotation-x={-Math.PI / 2} position={[0, -0.002, 0]}>
        <planeGeometry args={[90, 90]} />
        <meshStandardMaterial color="#141418" roughness={0.95} />
      </mesh>
      <mesh rotation-x={-Math.PI / 2}>
        <planeGeometry args={[16, 16]} />
        <meshStandardMaterial color="#a3a3aa" roughness={0.9} />
      </mesh>
      {lines.map(([x, z, w, d], i) => (
        <mesh key={i} position={[x, 0.004, z]} rotation-x={-Math.PI / 2}>
          <planeGeometry args={[w, d]} />
          <meshBasicMaterial color="#f4f4f4" />
        </mesh>
      ))}
      {steps}
      <Audience />
      {lamps.map(([x, y, z, c], i) => (
        <mesh key={i} position={[x, y, z]}>
          <sphereGeometry args={[0.35, 12, 10]} />
          <meshBasicMaterial color={c} toneMapped={false} />
        </mesh>
      ))}
      <pointLight position={[-11, 12, -16]} color="#ff3346" intensity={0.8} distance={30} decay={0} />
    </group>
  );
}


/* linee guida: quadrati del tronc, colonne (rengles), pom de dalt, asse */
const GUIDE_PIS_COLORS = PIS_COLORS.map((c) => new THREE.Color(c));
const GUIDE_EDGE_COLOR = new THREE.Color('#e9e4d4');
const GUIDE_AXIS_COLOR = new THREE.Color('#ffffff');
const GUIDE_MAXV = 160;

function Guides({ plan, tRef }) {
  const lineRef = useRef(null);

  useLayoutEffect(() => {
    const g = lineRef.current.geometry;
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(GUIDE_MAXV * 3), 3));
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(GUIDE_MAXV * 3), 3));
    g.setDrawRange(0, 0);
  }, []);

  useFrame(() => {
    const line = lineRef.current;
    if (!line || !line.geometry.attributes.position) return;
    const g = line.geometry;
    const positions = g.attributes.position.array;
    const colors = g.attributes.color.array;
    const t = tRef.current;
    let v = 0;
    const push = (x, y, z, c) => {
      positions[v * 3] = x; positions[v * 3 + 1] = y; positions[v * 3 + 2] = z;
      colors[v * 3] = c.r; colors[v * 3 + 1] = c.g; colors[v * 3 + 2] = c.b;
      v++;
    };
    const anyPresent = (p) => plan.pis[p].members.some((a) => present(a, t));
    // quadrati del tronc alla quota dei piedi e colonne verticali
    const corners = COLS.map(([cx, cz]) => [cx * A, cz * A]);
    let topCol = -1;
    for (let p = 1; p <= 5; p++) {
      if (!anyPresent(p)) continue;
      topCol = p;
      const y = Y[p - 1] + 0.03;
      for (let i = 0; i < 4; i++) {
        const [x0, z0] = corners[i], [x1, z1] = corners[(i + 1) % 4];
        push(x0, y, z0, GUIDE_PIS_COLORS[p - 1]); push(x1, y, z1, GUIDE_PIS_COLORS[p - 1]);
      }
    }
    if (topCol > 1) corners.forEach(([x, z]) => { push(x, 0, z, GUIDE_EDGE_COLOR); push(x, Y[topCol - 1], z, GUIDE_EDGE_COLOR); });
    if (anyPresent(6)) { push(0, Y[5] + 0.03, A, GUIDE_PIS_COLORS[5]); push(0, Y[5] + 0.03, -A, GUIDE_PIS_COLORS[5]); }
    if (anyPresent(7)) { push(0, Y_AIX, A * 0.6, GUIDE_PIS_COLORS[6]); push(0, Y_AIX, -A * 0.6, GUIDE_PIS_COLORS[6]); }
    const top = topHeightAt(plan, t);
    push(0, 0, 0, GUIDE_AXIS_COLOR); push(0, top + 0.3, 0, GUIDE_AXIS_COLOR);
    g.setDrawRange(0, v);
    g.attributes.position.needsUpdate = true;
    g.attributes.color.needsUpdate = true;
  });

  return (
    <lineSegments ref={lineRef} renderOrder={10} frustumCulled={false}>
      <bufferGeometry />
      <lineBasicMaterial vertexColors transparent opacity={0.9} depthTest={false} />
    </lineSegments>
  );
}

/* preset di camera */
const CAM = {
  video: { label: 'Dall’angolo' },
  faccia: { label: 'Di faccia' },
  alto: { label: 'Dall’alto' },
  centro: { label: 'Dal centro, in su' },
  libera: { label: 'Libera' },
};
function presetGoal(preset, top, pos, target) {
  switch (preset) {
    case 'video': case 'faccia': {
      // inquadratura che si adatta all'altezza della torre: il pavimento sta appena sopra la barra
      // dei comandi (a ~19% dal basso) e la cima con 2 m di margine arriva a ~6% dal bordo alto
      const span = top + 2;
      const half = span / (FRAME_TOP - FRAME_BOTTOM);           // semialtezza visibile (m)
      const dist = Math.max(17, half / Math.tan((FOV / 2) * (Math.PI / 180)));
      const ty = -FRAME_BOTTOM * half;
      if (preset === 'video') pos.set(dist / Math.SQRT2, 2.0, dist / Math.SQRT2);
      else pos.set(0, 3.5, dist);
      target.set(0, ty, 0);
      break;
    }
    case 'alto': pos.set(0.01, Math.max(13, top + 5), 0.01); target.set(0, 0, 0); break;
    case 'centro': pos.set(0.05, 0.25, -0.05); target.set(0, 12, 0); break;
    default: return false;
  }
  return true;
}

const colorOf = (a) => {
  if (a.role === 'cap') return CAP_COLOR;
  if (a.role === 'tronc' || a.climber) return PIS_COLORS[a.pis - 1];
  return PINYA_COLOR;
};

const Scene = memo(function Scene({ plan, tRef, playingRef, speedRef, onTick, onEnd, colorByRole, mannequin, cutaway, guides, preset, onUserCamera }) {
  const rigs = useRef([]);
  const register = useCallback((i, r) => { rigs.current[i] = r; }, []);
  const geo = useMemo(() => makeGeometries(), []);
  const mats = useMemo(() => makeMaterials(), []);
  // buffer di lavoro mutabili: stanno in un ref e vengono creati al primo fotogramma
  const work = useRef(null);
  const lastTick = useRef(0);

  useEffect(() => {
    plan.athletes.forEach((a, i) => {
      const rig = rigs.current[i];
      if (!rig) return;
      rig.leo.color.set(colorByRole ? colorOf(a) : mannequin ? MANNEQUIN_COLOR : NAVY);
    });
  }, [colorByRole, mannequin, plan]);

  useFrame((state, dt) => {
    if (!work.current || work.current.plan !== plan) {
      work.current = {
        plan,
        poses: plan.athletes.map(() => newPose()),
        tmp: newPose(),
        goalPos: new THREE.Vector3(),
        goalTarget: new THREE.Vector3(),
      };
    }
    const { poses, tmp, goalPos, goalTarget } = work.current;
    const camera = state.camera;
    const controls = state.controls;
    const d = Math.min(dt, 0.05);
    if (playingRef.current) {
      const before = tRef.current;
      tRef.current += d * speedRef.current;
      // pausa automatica tra la fase di salita e quella di discesa
      if (before < plan.T.descent && tRef.current >= plan.T.descent) { tRef.current = plan.T.descent; onEnd(); }
      if (tRef.current >= plan.T.end) { tRef.current = plan.T.end; onEnd(); }
    }
    const t = tRef.current;

    const cl = Math.hypot(camera.position.x, camera.position.z) || 1;
    const cx = camera.position.x / cl, cz = camera.position.z / cl;
    for (let i = 0; i < plan.athletes.length; i++) {
      const rig = rigs.current[i];
      if (!rig) continue;
      const a = plan.athletes[i];
      const p = poses[i];
      computePose(a, t, plan, p, tmp);
      applyPose(rig, p, a.scale);
      rig.root.visible = !(cutaway && p.x * cx + p.z * cz > 0.12) && !(preset === 'centro' && a.role === 'agulla');
    }

    if (controls && presetGoal(preset, topHeightAt(plan, t), goalPos, goalTarget)) {
      const k = 1 - Math.exp(-Math.min(dt, 0.25) * 2.4);
      camera.position.lerp(goalPos, k);
      controls.target.lerp(goalTarget, k);
      controls.update();
    }

    const now = state.clock.elapsedTime;
    if (now - lastTick.current > 0.08) { lastTick.current = now; onTick(t); }
  });

  return (
    <>
      <color attach="background" args={['#07070b']} />
      <fog attach="fog" args={['#07070b', 30, 65]} />
      <hemisphereLight args={['#c9d3ff', '#5a5560', 0.65]} />
      <directionalLight position={[10, 22, 14]} intensity={1.9} />
      <directionalLight position={[-12, 10, -6]} intensity={0.45} color="#ffb3a6" />
      <directionalLight position={[0, 6, 18]} intensity={0.35} />
      <Arena />
      {plan.athletes.map((a, i) => (
        <Figure key={a.id} index={i} geo={geo} mats={mats} register={register} mannequin={mannequin} />
      ))}
      {guides && <Guides plan={plan} tRef={tRef} />}
      <OrbitControls makeDefault enableDamping dampingFactor={0.08} minDistance={0.4} maxDistance={60} onStart={onUserCamera} />
    </>
  );
});

/* ─────────────────────────── interfaccia ─────────────────────────── */
function phaseAt(P, t) {
  const { T, pis } = P;
  if (t < T_HOLD) return { title: 'Formazione', sub: 'Reticolo 10 × 9: 90 atlete. Da qui nasce un “4 de 8”: 4 per piano, 8 piani.' };
  if (t < T.tPinyaReady) return { title: 'Si fa pinya', sub: 'Al centro i 4 baixos si abbracciano; attorno crosses, contraforts, rengles de mans, vents e laterals. Chi sale si mette in fila sulle 4 rengles.' };
  const steps = [
    [2, 'Salgono i segons', 'Coscia e spalle della rengla de mans, spalle del contrafort, poi i piedi sulle spalle del baix.'],
    [3, 'Salgono i terços', 'Ogni appoggio è un corpo: faixa e spalle di chi sta già nel tronc. Nessun passo nel vuoto.'],
    [4, 'Salgono i quarts', 'Si sale solo quando chi sta sotto è in posizione: le colonne crescono quasi in parallelo.'],
    [5, 'Salgono i quints', 'Ultimo piano del tronc: 5 piani × 4 colonne = 20 atlete.'],
    [6, 'Pom de dalt: i dosos', 'Due ragazzine, ognuna con un piede sulle spalle di due quints.'],
    [7, 'L’aixecador', 'Accovacciata, un piede su ciascuno dei dosos.'],
    [8, 'Sale l’enxaneta', 'Si arrampica fino alla schiena dell’aixecador.'],
  ];
  for (const [p, title, sub] of steps) if (t < pis[p].arrive) return { title, sub };
  if (t < T.aletaEnd) return { title: 'Il castell è carregat!', sub: 'L’enxaneta si alza in piedi sulla schiena dell’aixecador e apre le braccia. Fine della salita.' };
  if (t <= T.descent + 0.01) return { title: 'Castell carregat', sub: 'Tutte e 24 in posizione, ferme. Premi “Discesa” per smontarlo dall’alto verso il basso.' };
  if (t < T.tRelax) return { title: 'Discesa · si descarrega', sub: 'L’enxaneta scende dal lato opposto, poi aixecador, dosos e il tronc piano per piano: ognuna parte solo quando chi sta sopra è passata oltre.' };
  return { title: 'Castell descarregat!', sub: 'Costruito e smontato senza cadute: è il risultato pieno di una colla castellera.' };
}

const ui = {
  // nel flusso della pagina, sotto l'intestazione del sito: l'altezza viene misurata (vedi useAvailableHeight)
  // fissa a tutta larghezza, dal fondo dell'intestazione del sito al fondo della finestra (vedi useLayout)
  // z-index sotto l'intestazione (z-40) così il menu del sito resta sopra
  root: { position: 'fixed', left: 0, right: 0, bottom: 0, zIndex: 30, background: '#07070b', color: '#ece9e1', fontFamily: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif', overflow: 'hidden' },
  glass: { background: 'rgba(14,14,20,0.82)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, backdropFilter: 'blur(10px)', boxShadow: '0 10px 30px rgba(0,0,0,0.45)' },
  kicker: { fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#d9b45c', fontWeight: 600 },
  num: { fontVariantNumeric: 'tabular-nums' },
  chip: (on) => ({
    padding: '6px 10px', borderRadius: 999, fontSize: 12, cursor: 'pointer', whiteSpace: 'nowrap',
    border: `1px solid ${on ? '#d9b45c' : 'rgba(255,255,255,0.14)'}`,
    background: on ? 'rgba(217,180,92,0.18)' : 'rgba(255,255,255,0.03)',
    color: on ? '#f3dca0' : '#cfcbc2',
  }),
};

function Stat({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 10.5, color: '#9a968d', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
      <div style={{ fontSize: 17, fontWeight: 600, ...ui.num }}>{value}</div>
    </div>
  );
}

const PIS_FEET = (p) => (p <= 6 ? Y[p - 1] : p === 7 ? Y_AIX : Y_ENX);

/**
 * Bordo superiore della simulazione = fondo dell'intestazione del sito (<header>), misurato:
 * la simulazione resta fissa a tutta larghezza ma non finisce sotto il menu, qualunque altezza
 * abbia. Si aggiorna con la finestra e con l'intestazione. Il setState avviene solo nei callback.
 * Su schermi stretti il pannello dei piani parte chiuso.
 */
function useLayout(setPanelOpen) {
  const [top, setTop] = useState(0);
  useEffect(() => {
    const header = document.querySelector('header');
    const measure = () => setTop(header ? Math.max(0, Math.round(header.getBoundingClientRect().bottom)) : 0);
    const raf = requestAnimationFrame(() => {
      measure();
      if (window.innerWidth < 900) setPanelOpen(false);
    });
    window.addEventListener('resize', measure);
    window.addEventListener('scroll', measure, { passive: true });
    const ro = header ? new ResizeObserver(() => requestAnimationFrame(measure)) : null;
    if (ro) ro.observe(header);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', measure);
      window.removeEventListener('scroll', measure);
      if (ro) ro.disconnect();
    };
  }, [setPanelOpen]);
  return top;
}

export default function AcrobatSimulation() {
  const plan = useMemo(() => buildPlan(), []);
  const END = plan.T.end;
  const tRef = useRef(0);
  const playingRef = useRef(true);
  const speedRef = useRef(1);
  const [uiT, setUiT] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [colorByRole, setColorByRole] = useState(false);
  const [mannequin, setMannequin] = useState(false);
  const [cutaway, setCutaway] = useState(false);
  const [guides, setGuides] = useState(false);
  const [preset, setPreset] = useState('video');
  const [panelOpen, setPanelOpen] = useState(true);
  const controlsRef = useRef(null);
  const [controlsHeight, setControlsHeight] = useState(180);

  // Il canvas usa solo lo spazio sopra i comandi, anche quando vanno a capo.
  useLayoutEffect(() => {
    const element = controlsRef.current;
    if (!element) return;
    const measure = () => setControlsHeight(Math.ceil(element.getBoundingClientRect().height) + 32);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const topPx = useLayout(setPanelOpen);

  const onTick = useCallback((t) => setUiT(t), []);
  const onEnd = useCallback(() => { playingRef.current = false; setPlaying(false); }, []);
  const onUserCamera = useCallback(() => setPreset('libera'), []);

  const togglePlay = useCallback(() => {
    const next = !playingRef.current;
    if (next && tRef.current >= END - 0.01) tRef.current = 0;
    playingRef.current = next;
    setPlaying(next);
  }, [END]);
  const restart = () => { tRef.current = 0; setUiT(0); playingRef.current = true; setPlaying(true); };
  const DESC = plan.T.descent;
  const goPhase = (which) => {
    const t0 = which === 'discesa' ? DESC : 0;
    tRef.current = t0; setUiT(t0); playingRef.current = true; setPlaying(true);
  };
  const inDescent = uiT > DESC + 0.01;
  const atBreak = !playing && Math.abs(uiT - DESC) < 0.02;
  const scrub = (v) => { tRef.current = v; setUiT(v); playingRef.current = false; setPlaying(false); };
  const changeSpeed = (s) => { speedRef.current = s; setSpeed(s); };

  useEffect(() => {
    const onKey = (e) => {
      if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') { e.preventDefault(); togglePlay(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [togglePlay]);

  const top = topHeightAt(plan, uiT);
  const inCastell = plan.athletes.filter((a) => a.climber && present(a, uiT)).length;
  const phase = phaseAt(plan, uiT);
  const marks = [
    { t: plan.T.tPinya, label: 'pinya' },
    { t: plan.pis[6].start, label: 'pom' },
    { t: plan.T.aletaStart, label: 'aleta' },
    { t: plan.pis[5].descStart, label: 'tronc giù' },
  ];
  const stateOf = (p) => {
    const m = plan.pis[p].members;
    if (m.some((a) => a.climber && uiT >= a.climbStart && uiT < a.arrive)) return 'sale';
    if (m.some((a) => a.climber && uiT >= a.descStart && uiT < a.descEnd)) return 'scende';
    if (m.every((a) => present(a, uiT))) return 'in posizione';
    if (m.every((a) => uiT >= a.descStart)) return 'a terra';
    return 'in attesa';
  };

  return (
    <div style={{ ...ui.root, top: topPx, height: `calc(100dvh - ${topPx}px)` }}>
      {/* la tabella non eredita gli stili globali del sito */}
      <style>{'.r57-table th,.r57-table td{border:0;background:transparent;color:inherit;box-shadow:none}.r57-table tr{border:0;background:transparent}'}</style>
      <Canvas style={{ position: 'absolute', inset: 0, width: '100%', height: `calc(100% - ${controlsHeight}px)` }} dpr={[1, 2]} camera={{ position: [13.4, 2.0, 13.4], fov: FOV, near: 0.1, far: 200 }} gl={{ antialias: true }}>
        <Scene
          plan={plan} tRef={tRef} playingRef={playingRef} speedRef={speedRef}
          onTick={onTick} onEnd={onEnd} onUserCamera={onUserCamera}
          colorByRole={colorByRole} mannequin={mannequin} cutaway={cutaway} guides={guides} preset={preset}
        />
      </Canvas>

      {/* scheda fase */}
      <div style={{ ...ui.glass, position: 'absolute', top: 16, left: 16, padding: '14px 16px', width: 'min(360px, calc(100vw - 120px))' }}>
        <div style={ui.kicker}>Castell 4 de 8</div>
        <div style={{ fontSize: 20, fontWeight: 650, marginTop: 6 }}>{phase.title}</div>
        <div style={{ fontSize: 13, lineHeight: 1.45, color: '#bdb8ad', marginTop: 4, minHeight: 38 }}>{phase.sub}</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px 16px', marginTop: 12 }}>
          <Stat label="Altezza della cima" value={`${top.toFixed(1)} m`} />
          <Stat label="Nel castell / pinya" value={`${inCastell} / 70`} />
          <Stat label="Carico su ogni baix" value={`≈ ${Math.round(baixLoadAt(plan, uiT))} kg`} />
          <Stat label="Piani completi" value={`${[1, 2, 3, 4, 5, 6, 7, 8].filter((p) => plan.pis[p].members.every((a) => present(a, uiT))).length} / 8`} />
        </div>
      </div>

      {/* tabella piani */}
      <div style={{ position: 'absolute', top: 16, right: 16, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
        <button onClick={() => setPanelOpen((o) => !o)} style={ui.chip(panelOpen)}>{panelOpen ? 'Nascondi piani' : 'Piani'}</button>
        {panelOpen && (
          <div style={{ ...ui.glass, padding: '12px 14px', width: 320 }}>
            <table className="r57-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5, background: 'transparent', ...ui.num }}>
              <thead>
                <tr style={{ color: '#9a968d', fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  <th style={{ textAlign: 'left', paddingBottom: 6 }}>Pis</th>
                  <th style={{ textAlign: 'left' }}>Ruolo</th>
                  <th style={{ textAlign: 'right' }}>N</th>
                  <th style={{ textAlign: 'right' }}>Piedi</th>
                  <th style={{ textAlign: 'right' }}>Stato</th>
                </tr>
              </thead>
              <tbody>
                {[8, 7, 6, 5, 4, 3, 2, 1].map((p) => {
                  const st = stateOf(p);
                  return (
                    <tr key={p} style={{ opacity: st === 'in attesa' || st === 'a terra' ? 0.5 : 1 }}>
                      <td style={{ padding: '3px 0' }}>
                        <span style={{ display: 'inline-block', width: 9, height: 9, borderRadius: 2, background: PIS_COLORS[p - 1], marginRight: 7 }} />
                        {p}
                      </td>
                      <td>{PIS_NAMES[p - 1]}</td>
                      <td style={{ textAlign: 'right' }}>{plan.pis[p].members.length}</td>
                      <td style={{ textAlign: 'right' }}>{PIS_FEET(p).toFixed(1)} m</td>
                      <td style={{ textAlign: 'right', color: st === 'sale' || st === 'scende' ? '#f3dca0' : undefined }}>{st}</td>
                    </tr>
                  );
                })}
                <tr style={{ color: '#9a968d' }}>
                  <td style={{ paddingTop: 6 }}>
                    <span style={{ display: 'inline-block', width: 9, height: 9, borderRadius: 2, background: PINYA_COLOR, marginRight: 7 }} />—
                  </td>
                  <td style={{ paddingTop: 6 }}>Pinya</td>
                  <td style={{ textAlign: 'right', paddingTop: 6 }}>66</td>
                  <td colSpan={2} style={{ textAlign: 'right', paddingTop: 6 }}>a terra</td>
                </tr>
              </tbody>
            </table>
            <div style={{ fontSize: 11.5, color: '#9a968d', lineHeight: 1.45, marginTop: 10 }}>
              Tronc 5 × 4 = 20 · pom de dalt 2 + 1 + 1 = 4 · pinya 66 (agulla 1, crosses 8, contraforts 4, mans 12, vents 12, laterals 16, darrer cordó 12, cap de colla 1). Carico calcolato con masse ipotizzate: segons 70 kg, terços 62, quarts 55, quints 50, dosos 32, aixecador 26, enxaneta 20.
            </div>
          </div>
        )}
      </div>

      {/* controlli */}
      <div ref={controlsRef} style={{ position: 'absolute', left: '50%', bottom: 16, transform: 'translateX(-50%)', width: 'min(760px, calc(100vw - 32px))', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
          {Object.entries(CAM).map(([k, v]) => (
            <button key={k} style={ui.chip(preset === k)} onClick={() => setPreset(k)}>{v.label}</button>
          ))}
          <span style={{ width: 8 }} />
          <button style={ui.chip(mannequin)} onClick={() => setMannequin((x) => !x)} title="Figure neutre con le articolazioni evidenziate">Manichino</button>
          <button style={ui.chip(colorByRole)} onClick={() => setColorByRole((x) => !x)}>Colori per ruolo</button>
          <button style={ui.chip(guides)} onClick={() => setGuides((x) => !x)}>Guide geometriche</button>
          <button style={ui.chip(cutaway)} onClick={() => setCutaway((x) => !x)}>Spaccato</button>
        </div>
        <div style={{ ...ui.glass, padding: '10px 14px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <div style={{ display: 'flex', borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.14)' }}>
            {[['salita', 'Salita', '#d9b45c'], ['discesa', 'Discesa', '#7fb2e6']].map(([k, label, col]) => {
              const on = k === 'discesa' ? inDescent : !inDescent;
              return (
                <button
                  key={k}
                  onClick={() => goPhase(k)}
                  title={k === 'salita' ? 'Dalla formazione al castell carregat' : 'Dal castell carregat al descarregat'}
                  style={{ padding: '7px 10px', fontSize: 12, border: 'none', cursor: 'pointer', background: on ? col : 'transparent', color: on ? '#14110a' : '#cfcbc2', fontWeight: on ? 700 : 500 }}
                >
                  {label}
                </button>
              );
            })}
          </div>
          <button
            onClick={togglePlay}
            style={{ width: 92, padding: '8px 0', borderRadius: 8, border: 'none', background: atBreak ? '#7fb2e6' : '#d9b45c', color: '#1a1408', fontWeight: 700, cursor: 'pointer' }}
          >
            {playing ? 'Pausa' : uiT >= END - 0.01 ? 'Rivedi' : atBreak ? 'Discesa ▶' : 'Avvia'}
          </button>
          <button onClick={restart} title="Ricomincia" style={{ ...ui.chip(false), padding: '7px 10px' }}>↺</button>
          <div style={{ position: 'relative', flex: '1 1 220px', minWidth: 200, paddingTop: 14 }}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 12 }}>
              {marks.map((m) => (
                <span key={m.label} style={{ position: 'absolute', left: `${((m.t / END) * 100).toFixed(3)}%`, transform: 'translateX(-50%)', fontSize: 9.5, color: uiT >= m.t ? '#d9b45c' : '#77736b', whiteSpace: 'nowrap' }}>
                  {m.label}
                </span>
              ))}
            </div>
            <input
              type="range" min={0} max={END} step={0.01} value={uiT}
              onChange={(e) => scrub(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: inDescent ? '#7fb2e6' : '#d9b45c', cursor: 'pointer' }}
            />
            {/* barra delle due fasi */}
            <div style={{ display: 'flex', height: 4, borderRadius: 2, overflow: 'hidden', marginTop: 2 }}>
              <div style={{ width: `${((DESC / END) * 100).toFixed(3)}%`, background: 'rgba(217,180,92,0.55)' }} />
              <div style={{ width: 2, background: '#07070b' }} />
              <div style={{ flex: 1, background: 'rgba(127,178,230,0.55)' }} />
            </div>
          </div>
          <span style={{ fontSize: 12, color: '#bdb8ad', minWidth: 70, textAlign: 'right', ...ui.num }}>
            {uiT.toFixed(1)} / {END.toFixed(0)} s
          </span>
          <div style={{ display: 'flex', gap: 4 }}>
            {[0.5, 1, 2].map((s) => (
              <button key={s} onClick={() => changeSpeed(s)} style={{ ...ui.chip(speed === s), padding: '5px 8px' }}>{s}×</button>
            ))}
          </div>
        </div>
        <div style={{ textAlign: 'center', fontSize: 11, color: '#6f6b63' }}>Trascina per ruotare · rotellina per lo zoom · barra spaziatrice per pausa</div>
      </div>
    </div>
  );
}
