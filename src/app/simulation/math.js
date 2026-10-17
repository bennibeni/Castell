/* ─────────────────────────── utilità ─────────────────────────── */
const TAU = Math.PI * 2;
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (x) => {
  const u = clamp01(x);
  return u * u * (3 - 2 * u);
};
const ramp = (t, a, b) => smooth((t - a) / (b - a));
const lerp = (a, b, u) => a + (b - a) * u;
const angLerp = (a, b, u) => {
  const d = ((((b - a + Math.PI) % TAU) + TAU) % TAU) - Math.PI;
  return a + d * u;
};
const hash = (i) => {
  const s = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
};

export { TAU, clamp01, smooth, ramp, lerp, angLerp, hash };
