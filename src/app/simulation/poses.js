import { REACH_MAX } from './constants.js';
import { clamp01, lerp, ramp, angLerp, smooth } from './math.js';
import {
  HIP,
  S_ENX,
  squatAngle,
  VIDEO_DIR,
  S_BAIX,
  Y,
  S_TRONC,
  S_DOSOS,
  Y_AIX,
  S_AIX,
  Y_ENX,
  U,
} from './constants.js';

/* ─────────────────────────── pose ─────────────────────────── */
const A_DOWN = [0.05, 0.12, -0.15];
// nessuna posa porta le mani sopra le spalle
const A_LINK = [-0.45, 0.35, -1.35]; // tronc: gomiti piegati, mani raccolte davanti al petto
const A_CROSS = [-1.15, 0.35, -1.2]; // crosses: sorreggono i baixos sotto le ascelle
const A_AIX = [-0.4, 0.5, -1.0]; // aixecador: mani appoggiate sulle teste dei dosos, gomiti piegati
const A_DOSOS = [-0.95, 0.2, -1.2]; // le due dosos, una di fronte all'altra, si tengono per le spalle

/** braccia di chi appoggia le mani su una compagna a distanza d davanti (più lontana = braccia più distese) */
function reachArms(d) {
  if (d === null || d === undefined) return A_DOWN;
  const u = clamp01((d - 0.4) / 0.4);
  return [lerp(-0.75, -1.1, u), 0.2, lerp(-1.35, -0.85, u)]; // gomiti sempre piegati
}
const A_OPEN = [-0.1, 1.45, -0.05]; // enxaneta: braccia aperte all'orizzontale

const newPose = () => ({
  x: 0,
  y: 0,
  z: 0,
  yaw: 0,
  hipY: HIP,
  thL: 0,
  thR: 0,
  knL: 0,
  knR: 0,
  spread: 0,
  lean: 0,
  aL: [0, 0, 0],
  aR: [0, 0, 0],
});
const setA = (arr, v) => {
  arr[0] = v[0];
  arr[1] = v[1];
  arr[2] = v[2];
};
const mixInto = (arr, v, w) => {
  arr[0] = lerp(arr[0], v[0], w);
  arr[1] = lerp(arr[1], v[1], w);
  arr[2] = lerp(arr[2], v[2], w);
};
const bothArms = (p, v) => {
  setA(p.aL, v);
  setA(p.aR, v);
};
const mixBoth = (p, v, w) => {
  mixInto(p.aL, v, w);
  mixInto(p.aR, v, w);
};

/** accosciamento dell'enxaneta: accovacciata in salita e in discesa, in piedi da carregat */
function enxUp(T, t) {
  return (
    ramp(t, T.aletaStart, T.aletaStart + 1.0) * (1 - ramp(t, T.descent + 0.05, T.descent + 0.85))
  );
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
  p.thL = lerp(p.thL, q.thL, w);
  p.thR = lerp(p.thR, q.thR, w);
  p.knL = lerp(p.knL, q.knL, w);
  p.knR = lerp(p.knR, q.knR, w);
  p.spread = lerp(p.spread, q.spread, w);
  p.lean = lerp(p.lean, q.lean, w);
  p.yaw = angLerp(p.yaw, q.yaw, w);
  mixInto(p.aL, q.aL, w);
  mixInto(p.aR, q.aR, w);
}

function walkPose(p, fx, fz, tx, tz, u, dist, yaw0, yaw1) {
  const e = smooth(u);
  p.x = lerp(fx, tx, e);
  p.z = lerp(fz, tz, e);
  p.y = 0;
  const mv = dist > 0.05 ? Math.atan2(tx - fx, tz - fz) : yaw1;
  p.yaw = angLerp(angLerp(yaw0, mv, ramp(u, 0, 0.18)), yaw1, ramp(u, 0.82, 1));
  const env = clamp01(Math.min(u * 5, (1 - u) * 5));
  const ph = ((e * dist) / 0.62) * Math.PI;
  standPose(p, 0.04, 0.02, 0);
  const sw = 0.5 * env * Math.sin(ph);
  p.thL -= sw;
  p.thR += sw;
  p.knL += env * 0.55 * Math.max(0, Math.sin(ph + 1.3));
  p.knR += env * 0.55 * Math.max(0, -Math.sin(ph + 1.3));
  p.hipY -= 0.035 * env * Math.abs(Math.sin(ph));
  p.aL[0] = 0.8 * sw;
  p.aL[1] = 0.12;
  p.aL[2] = -0.3;
  p.aR[0] = -0.8 * sw;
  p.aR[1] = 0.12;
  p.aR[2] = -0.3;
}

/**
 * posizione lungo la sequenza di appoggi: curva di Catmull-Rom che passa per tutti gli appoggi,
 * percorsa senza soste a passo costante (times = istanti di passaggio sugli appoggi), con partenza e arrivo dolci.
 * Niente archi né pause: il corpo sale in modo continuo, come in un'arrampicata vera.
 */
function pathAt(pts, times, t0, t, p) {
  const n = pts.length;
  const x = t - t0;
  if (x <= 0) {
    p.x = pts[0].x;
    p.y = pts[0].y;
    p.z = pts[0].z;
    return { i: 0, f: 0 };
  }
  if (x >= times[n - 1]) {
    const l = pts[n - 1];
    p.x = l.x;
    p.y = l.y;
    p.z = l.z;
    return { i: n - 2, f: 1 };
  }
  let i = 0;
  while (i < n - 2 && x >= times[i + 1]) i++;
  const f = (x - times[i]) / (times[i + 1] - times[i]);
  // partenza e arrivo dolci, velocità continua in mezzo
  const g = n === 2 ? smooth(f) : i === 0 ? f * f : i === n - 2 ? 1 - (1 - f) * (1 - f) : f;
  const P0 = pts[Math.max(0, i - 1)],
    P1 = pts[i],
    P2 = pts[i + 1],
    P3 = pts[Math.min(n - 1, i + 2)];
  const g2 = g * g,
    g3 = g2 * g;
  const cr = (a, b, c, d) =>
    0.5 * (2 * b + (-a + c) * g + (2 * a - 5 * b + 4 * c - d) * g2 + (-a + 3 * b - 3 * c + d) * g3);
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
  const lift = Math.sin(Math.PI * f); // 0 all'appoggio, 1 a metà tratto
  const left = i % 2 === 0; // gamba e braccio guida si alternano
  const lead = { th: -(0.5 + 0.95 * lift), kn: 0.7 + 1.25 * lift };
  const push = { th: -(0.5 - 0.35 * lift), kn: 0.7 - 0.45 * lift };
  const L = left ? lead : push,
    R = left ? push : lead;
  p.hipY = 0.84;
  p.thL = L.th;
  p.knL = L.kn;
  p.thR = R.th;
  p.knR = R.kn;
  p.lean = 0.28;
  p.spread = 0.1;
  const reach = [-1.4 - 0.45 * lift, 0.3, -1.3 + 0.35 * lift]; // mano che sale verso la presa (gomito piegato)
  const pull = [-1.25 + 0.2 * lift, 0.25, -1.35]; // mano che tira il corpo verso l'alto
  setA(p.aL, left ? reach : pull);
  setA(p.aR, left ? pull : reach);
}

/** posa "in posizione" di ciascun ruolo */
function rolePose(a, t, P, q) {
  const { T } = P;
  q.x = a.sx ?? a.tx;
  q.z = a.sz ?? a.tz;
  q.yaw = Math.hypot(q.x, q.z) < 0.01 ? Math.PI / 2 : Math.atan2(-q.x, -q.z);
  q.y = 0;
  const on = ramp(t, T.tPinya, T.tPinya + 1.2) * (1 - ramp(t, T.tRelax, T.tRelax + 1.5));
  bothArms(q, A_DOWN);
  switch (a.role) {
    case 'agulla':
      q.yaw = VIDEO_DIR;
      standPose(q, 0.55 * on, 0.15 * on, 0.15 * on);
      mixBoth(q, reachArms(a.frontDist), on);
      return;
    case 'cross':
      standPose(q, 0.45 * on, 0.35 * on, 0.1 * on);
      mixBoth(q, A_CROSS, on);
      return;
    case 'contra':
      standPose(q, 0.25 * on, 0.5 * on, 0.1 * on);
      mixBoth(q, reachArms(a.frontDist), on);
      return;
    case 'mans':
      standPose(q, 0.1 * on, 0.2 * on, 0.08 * on);
      mixBoth(q, reachArms(a.frontDist), on);
      return;
    case 'vent':
    case 'lateral':
    case 'cordo':
      // chi non ha nessuno a portata resta più dritta, con le braccia lungo i fianchi
      standPose(q, 0.12 * on, (a.frontDist === null ? 0.05 : 0.2) * on, 0.1 * on);
      mixBoth(q, reachArms(a.frontDist), on);
      return;
    case 'cap':
      standPose(q, 0, 0, 0);
      return;
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
      q.y = Y[5];
      standPose(q, S_DOSOS, 0.06, 0.32);
      bothArms(q, A_DOSOS);
      return;
    case 'aix':
      q.y = Y_AIX;
      q.yaw = Math.PI / 2;
      standPose(q, S_AIX, 0.5, 0.45);
      bothArms(q, A_AIX);
      return;
    case 'enx': {
      // in piedi sulla schiena dell'aixecador, braccia aperte, per tutto il tempo del castell carregat
      q.y = Y_ENX;
      q.yaw = angLerp(Math.PI / 2, VIDEO_DIR, enxUp(T, t));
      standPose(q, enxSquat(T, t), 0.45, 0.2); // in piedi si gira verso il pubblico
      bothArms(q, A_AIX);
      mixBoth(
        q,
        A_OPEN,
        ramp(t, T.aletaStart + 0.6, T.aletaStart + 1.4) * (1 - ramp(t, T.descent, T.descent + 0.6)),
      );
      return;
    }
    default:
      standPose(q, 0, 0, 0);
  }
}

function computePose(a, t, P, p, q) {
  // 1 · reticolo
  if (t < a.walkStart) {
    p.x = a.gx;
    p.y = 0;
    p.z = a.gz;
    p.yaw = VIDEO_DIR;
    standPose(p, 0.02, 0.01, 0);
    bothArms(p, A_DOWN);
    return;
  }
  const towerYaw = a.climber ? Math.atan2(-a.ux, -a.uz) : Math.atan2(-a.tx, -a.tz);
  // 2 · implosione
  if (t < a.walkEnd) {
    const endYaw = a.role === 'agulla' ? VIDEO_DIR : towerYaw;
    walkPose(
      p,
      a.gx,
      a.gz,
      a.tx,
      a.tz,
      (t - a.walkStart) / a.walkDur,
      a.walkDist,
      VIDEO_DIR,
      endYaw,
    );
    return;
  }
  // pinya e baixos: restano al loro posto
  if (!a.climber) {
    rolePose(a, t, P, p);
    return;
  }

  // 3 · in coda
  if (t < a.apStart) {
    p.x = a.tx;
    p.y = 0;
    p.z = a.tz;
    p.yaw = towerYaw;
    standPose(p, 0.03, 0.02, 0);
    bothArms(p, A_DOWN);
    return;
  }
  // 4 · dalla coda al punto di partenza, nel varco del darrer cordó
  if (t < a.climbStart) {
    const s0 = a.up[0];
    const d = Math.hypot(s0.x - a.tx, s0.z - a.tz);
    walkPose(
      p,
      a.tx,
      a.tz,
      s0.x,
      s0.z,
      (t - a.apStart) / (a.climbStart - a.apStart),
      d,
      towerYaw,
      towerYaw,
    );
    return;
  }
  // 5 · salita appoggio per appoggio
  if (t < a.arrive) {
    const st = pathAt(a.up, a.upT, a.climbStart, t, p);
    p.yaw = towerYaw;
    climbLimbs(p, st.i, st.f);
    if (st.i === a.up.length - 2) {
      rolePose(a, t, P, q);
      blendLimbs(p, q, smooth(st.f));
    }
    return;
  }
  // 6 · in posizione
  if (t < a.descStart) {
    rolePose(a, t, P, p);
    return;
  }
  // 7 · discesa
  const downYaw = Math.atan2(-U[a.downCol][0], -U[a.downCol][1]);
  if (t < a.descEnd) {
    const st = pathAt(a.down, a.downT, a.descStart, t, p);
    p.yaw = downYaw;
    climbLimbs(p, st.i, st.f);
    if (st.i === 0) {
      rolePose(a, a.descStart, P, q);
      const px = p.x,
        py = p.y,
        pz = p.z;
      blendLimbs(p, q, 1 - smooth(st.f / 0.5));
      p.x = px;
      p.y = py;
      p.z = pz;
    }
    return;
  }
  // 8 · torna in coda
  const last = a.down[a.down.length - 1];
  if (t < a.exitEnd) {
    const d = Math.hypot(a.ex - last.x, a.ez - last.z);
    walkPose(p, last.x, last.z, a.ex, a.ez, (t - a.descEnd) / a.exitDur, d, downYaw, downYaw);
    return;
  }
  p.x = a.ex;
  p.y = 0;
  p.z = a.ez;
  p.yaw = downYaw;
  standPose(p, 0.03, 0.02, 0);
  bothArms(p, A_DOWN);
}

export { newPose, enxSquat, computePose };
