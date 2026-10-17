import { Group, Mesh } from 'three';
import { JOINTS, UNIFORM_MATERIAL } from './rig.js';
import { makeGeometries, makeMaterials } from './resources.js';

// Modello di partenza per Blender: ogni articolazione è un nodo nominato.
// Le mesh sono rigide, figlie del proprio punto di rotazione, senza skinning.
export function createReferenceAthlete() {
  const root = new Group();
  root.name = 'Castell_Athlete';
  const joints = {};
  const geometry = makeGeometries();
  const materials = makeMaterials();
  materials.navy.name = UNIFORM_MATERIAL;
  materials.skin.name = 'Castell_Skin';
  materials.hair.name = 'Castell_Hair';
  for (const [key, spec] of Object.entries(JOINTS)) {
    const joint = new Group();
    joint.name = spec.name;
    joint.position.fromArray(spec.position);
    joints[key] = joint;
    (spec.parent ? joints[spec.parent] : root).add(joint);
  }
  function mesh(parent, shape, material, position, scale = [1, 1, 1]) {
    const object = new Mesh(geometry[shape], materials[material]);
    object.name = `${parent.name}_${shape}`;
    object.position.fromArray(position);
    object.scale.fromArray(scale);
    parent.add(object);
    return object;
  }
  mesh(joints.hips, 'pelvis', 'navy', [0, 0.02, 0], [1.2, 0.75, 0.85]);
  for (const side of ['L', 'R']) {
    mesh(joints[`thigh${side}`], 'thigh', 'skin', [0, -0.215, 0]);
    mesh(joints[`knee${side}`], 'shin', 'skin', [0, -0.215, 0]);
    mesh(joints[`knee${side}`], 'foot', 'skin', [0, -0.44, 0.05]);
    mesh(joints[`arm${side}`], 'upper', 'navy', [0, -0.143, 0]);
    mesh(joints[`elbow${side}`], 'fore', 'navy', [0, -0.133, 0]);
    mesh(joints[`elbow${side}`], 'hand', 'skin', [0, -0.285, 0]);
  }
  mesh(joints.torso, 'waist', 'skin', [0, 0.16, 0], [1.05, 1, 0.78]);
  mesh(joints.torso, 'chest', 'navy', [0, 0.36, 0], [1.18, 1, 0.78]);
  mesh(joints.torso, 'neck', 'skin', [0, 0.54, 0]);
  mesh(joints.torso, 'head', 'skin', [0, 0.65, 0]);
  mesh(joints.torso, 'hair', 'hair', [0, 0.655, -0.012]).rotation.x = -0.45;
  mesh(joints.torso, 'bun', 'hair', [0, 0.745, -0.075]);
  return root;
}
