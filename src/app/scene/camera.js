import { FRAME_TOP, FRAME_BOTTOM, FRAME_SHIFT, FOV } from '../simulation/constants.js';

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
    case 'video':
    case 'faccia': {
      // inquadratura adattiva: pavimento al 10% dal fondo e cima con 2 m di margine al 15% dall'alto
      const span = top + 2;
      const half = span / (FRAME_TOP - FRAME_BOTTOM); // semialtezza visibile (m)
      const dist = Math.max(17, half / Math.tan((FOV / 2) * (Math.PI / 180)));
      const shift = FRAME_SHIFT * half;
      const ty = -FRAME_BOTTOM * half;
      if (preset === 'video') pos.set(dist / Math.SQRT2, 2.0 + shift, dist / Math.SQRT2);
      else pos.set(0, 3.5 + shift, dist);
      target.set(0, ty, 0);
      break;
    }
    case 'alto':
      pos.set(0.01, Math.max(13, top + 5), 0.01);
      target.set(0, 0, 0);
      break;
    case 'centro':
      pos.set(0.05, 0.25, -0.05);
      target.set(0, 12, 0);
      break;
    default:
      return false;
  }
  return true;
}

export { CAM, presetGoal };
