import { Group } from 'three';
import { clone } from 'three/addons/utils/SkeletonUtils.js';

export const ATHLETE_MODEL_URL = '/models/athlete.glb';
export const UNIFORM_MATERIAL = 'Castell_Uniform';

// Coordinate glTF: metri, +Y verso l'alto, viso verso +Z, braccia lungo i fianchi.
// I nodi possono essere Object3D oppure Bone, purché rispettino gli stessi assi.
export const JOINTS = {
  hips: { name: 'Castell_Hips', parent: null, position: [0, 0.9, 0] },
  thighL: { name: 'Castell_Thigh_L', parent: 'hips', position: [0.09, -0.02, 0] },
  thighR: { name: 'Castell_Thigh_R', parent: 'hips', position: [-0.09, -0.02, 0] },
  kneeL: { name: 'Castell_Knee_L', parent: 'thighL', position: [0, -0.43, 0] },
  kneeR: { name: 'Castell_Knee_R', parent: 'thighR', position: [0, -0.43, 0] },
  torso: { name: 'Castell_Torso', parent: 'hips', position: [0, 0.02, 0] },
  armL: { name: 'Castell_Arm_L', parent: 'torso', position: [0.19, 0.47, 0] },
  armR: { name: 'Castell_Arm_R', parent: 'torso', position: [-0.19, 0.47, 0] },
  elbowL: { name: 'Castell_Elbow_L', parent: 'armL', position: [0, -0.29, 0] },
  elbowR: { name: 'Castell_Elbow_R', parent: 'armR', position: [0, -0.29, 0] },
};

function identityTransform(node, position = false) {
  const tolerance = 0.0001;
  return (
    Math.abs(node.quaternion.w) > 1 - tolerance &&
    [node.quaternion.x, node.quaternion.y, node.quaternion.z].every(
      (v) => Math.abs(v) < tolerance,
    ) &&
    node.scale.toArray().every((v) => Math.abs(v - 1) < tolerance) &&
    (!position || node.position.length() < tolerance)
  );
}

export function inspectAthleteModel(scene) {
  const errors = [];
  const joints = {};
  let uniformFound = false;
  for (const [key, spec] of Object.entries(JOINTS)) {
    const matches = [];
    scene.traverse((node) => {
      if (node.name === spec.name) matches.push(node);
    });
    if (matches.length !== 1) {
      errors.push(`${spec.name}: atteso un solo nodo, trovati ${matches.length}`);
      continue;
    }
    const node = matches[0];
    joints[key] = node;
    if (!identityTransform(node))
      errors.push(`${spec.name}: rotazione di riposo o scala incompatibile`);
    if (node.position.toArray().some((v, i) => Math.abs(v - spec.position[i]) > 0.0001)) {
      errors.push(`${spec.name}: punto di articolazione spostato`);
    }
  }
  for (const [key, spec] of Object.entries(JOINTS)) {
    if (
      spec.parent &&
      joints[key] &&
      joints[spec.parent] &&
      joints[key].parent !== joints[spec.parent]
    ) {
      errors.push(`${spec.name}: deve essere figlio diretto di ${JOINTS[spec.parent].name}`);
    }
  }
  // Un contenitore aggiuntivo trasformato altererebbe dimensioni e appoggi.
  for (let ancestor = joints.hips?.parent; ancestor; ancestor = ancestor.parent) {
    if (!identityTransform(ancestor, true))
      errors.push(`${ancestor.name || 'Radice'}: trasformazione incompatibile`);
  }
  scene.traverse((node) => {
    if (!node.isMesh) return;
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      if (material?.name === UNIFORM_MATERIAL && material.color) uniformFound = true;
    }
  });
  if (!uniformFound) errors.push(`Materiale ${UNIFORM_MATERIAL} mancante`);
  return { valid: errors.length === 0, errors, joints };
}

export function createAthleteInstance(source) {
  const check = inspectAthleteModel(source);
  if (!check.valid) throw new Error(check.errors.join('; '));
  const model = clone(source);
  const root = new Group();
  root.add(model);
  const materials = new Map();
  const uniforms = [];
  model.traverse((node) => {
    if (!node.isMesh) return;
    const copy = (material) => {
      if (!materials.has(material)) {
        const instance = material.clone();
        materials.set(material, instance);
        if (instance.name === UNIFORM_MATERIAL)
          uniforms.push({ material: instance, color: instance.color.clone() });
      }
      return materials.get(material);
    };
    node.material = Array.isArray(node.material) ? node.material.map(copy) : copy(node.material);
    // Le pose cambiano fuori dal renderer: i limiti di una mesh skinned possono essere obsoleti.
    if (node.isSkinnedMesh) node.frustumCulled = false;
  });
  const rig = { root };
  for (const [key, spec] of Object.entries(JOINTS)) rig[key] = model.getObjectByName(spec.name);
  rig.setColor = (color) => {
    for (const uniform of uniforms) {
      if (color == null) uniform.material.color.copy(uniform.color);
      else uniform.material.color.set(color);
    }
  };
  rig.dispose = () => {
    for (const material of materials.values()) material.dispose();
    const skeletons = new Set();
    model.traverse((node) => {
      if (node.isSkinnedMesh) skeletons.add(node.skeleton);
    });
    for (const skeleton of skeletons) skeleton.dispose();
  };
  return rig;
}

export function applyPose(rig, p, scale) {
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
