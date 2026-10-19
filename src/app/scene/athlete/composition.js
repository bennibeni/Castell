import { Color } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { BODIES, HEADS, normalizeComposition } from './catalog.js';
import { inspectAthleteModel } from './rig.js';

const sources = new Map();
const compositions = new Map();
function load(url) {
  if (!sources.has(url)) sources.set(url, new GLTFLoader().loadAsync(url).catch(error => { sources.delete(url); throw error; }));
  return sources.get(url);
}
export function composeAthlete(bodySource, headSource, body, headSpec = {}) {
  const scene = clone(bodySource);
  if (body.skinTint) {
    const copies = new Map();
    const tint = new Color().setRGB(...body.skinTint);
    const tinted = material => {
      if (material?.name !== 'Castell_Skin') return material;
      if (!copies.has(material)) {
        const copy = material.clone();
        copy.color.multiply(tint);
        copies.set(material, copy);
      }
      return copies.get(material);
    };
    scene.traverse(node => {
      if (node.isMesh) node.material = Array.isArray(node.material) ? node.material.map(tinted) : tinted(node.material);
    });
  }
  const torso = scene.getObjectByName('Castell_Torso');
  if (!torso) throw new Error('Corpo senza articolazione del torso.');
  const head = clone(headSource);
  head.name = 'Castell_Selected_Head';
  const variantScale = headSpec.transform?.scale ?? 1;
  head.scale.multiplyScalar(variantScale);
  head.position.multiplyScalar(variantScale);
  head.position.y += headSpec.transform?.offsetY ?? 0;
  head.scale.multiplyScalar(body.headScale);
  head.position.multiplyScalar(body.headScale);
  head.position.y += body.headY;
  scene.add(head);
  scene.updateMatrixWorld(true);
  torso.attach(head);
  scene.updateMatrixWorld(true);
  const check = inspectAthleteModel(scene);
  if (!check.valid) throw new Error(check.errors.join('; '));
  return scene;
}
export function loadComposition(value) {
  value = normalizeComposition(value);
  const key = `${value.bodyId}/${value.headId}`;
  if (!compositions.has(key)) {
    const body = BODIES.find(item => item.id === value.bodyId);
    const head = HEADS.find(item => item.id === value.headId);
    compositions.set(key, Promise.all([load(body.url), load(head.url)]).then(([b,h]) => composeAthlete(b.scene,h.scene,body,head)).catch(error => { compositions.delete(key); throw error; }));
  }
  return compositions.get(key);
}
