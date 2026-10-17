import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Bone, BoxGeometry, MeshStandardMaterial, Skeleton, SkinnedMesh, Float32BufferAttribute, Uint16BufferAttribute } from 'three';
import {
  createAthleteInstance,
  inspectAthleteModel,
  applyPose,
  JOINTS,
} from '../src/app/scene/athlete/rig.js';
import { createReferenceAthlete } from '../src/app/scene/athlete/referenceModel.js';
import { buildPlan } from '../src/app/simulation/plan.js';
import { computePose, newPose } from '../src/app/simulation/poses.js';

async function loadActiveModel() {
  const bytes = await readFile(new URL('../public/models/athlete.glb', import.meta.url));
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return (await new GLTFLoader().parseAsync(buffer, '')).scene;
}

test('il GLB distribuito viene caricato e le 90 atlete possono avere pose e materiali indipendenti', async () => {
  const source = await loadActiveModel();
  assert.deepEqual(inspectAthleteModel(source).errors, []);
  const first = createAthleteInstance(source);
  const second = createAthleteInstance(source);
  const material = (rig) => {
    let found;
    rig.root.traverse((node) => {
      if (node.material?.name === 'Castell_Uniform') found = node.material;
    });
    return found;
  };
  const originalColor = material(first).color.clone();
  first.setColor('#ff0000');
  assert.notEqual(material(first), material(second));
  assert.equal(material(first).color.getHexString(), 'ff0000');
  assert.ok(material(second).color.equals(originalColor));
  first.setColor(null);
  assert.ok(material(first).color.equals(originalColor));
  const plan = buildPlan();
  const athlete = plan.athletes.find((a) => a.pis === 5);
  for (let i = 0; i <= 40; i++) {
    const pose = newPose();
    computePose(athlete, (plan.T.end * i) / 40, plan, pose, newPose());
    applyPose(first, pose, athlete.scale);
    first.root.updateMatrixWorld(true);
    assert.ok(first.root.matrixWorld.elements.every(Number.isFinite));
    assert.equal(first.hips.position.y, pose.hipY);
    assert.equal(first.armL.rotation.x, pose.aL[0]);
    assert.equal(first.elbowR.rotation.x, pose.aR[2]);
  }
  assert.deepEqual(second.hips.position.toArray(), JOINTS.hips.position);
  assert.ok(Math.abs(second.armL.rotation.x) < 1e-12);
  assert.notEqual(first.hips, second.hips);
  first.dispose();
  second.dispose();
});

test('un modello con articolazioni rinominate, spostate o ruotate viene rifiutato con una diagnosi', () => {
  const source = createReferenceAthlete();
  source.getObjectByName(JOINTS.hips.name).position.y += 0.1;
  source.getObjectByName(JOINTS.armL.name).name = 'nome_non_valido';
  source.getObjectByName(JOINTS.kneeR.name).rotation.x = 0.4;
  const result = inspectAthleteModel(source);
  assert.equal(result.valid, false);
  assert.ok(result.errors.some((e) => e.includes('Castell_Hips')));
  assert.ok(result.errors.some((e) => e.includes('Castell_Arm_L')));
  assert.ok(result.errors.some((e) => e.includes('Castell_Knee_R')));
  assert.throws(() => createAthleteInstance(source), /Castell_Hips/);
});

test('anche i modelli con skinning ricevono uno scheletro indipendente per ogni atleta', () => {
  const source = createReferenceAthlete();
  for (const spec of Object.values(JOINTS)) {
    const node = source.getObjectByName(spec.name);
    const bone = new Bone();
    bone.name = node.name;
    bone.position.copy(node.position);
    const parent = node.parent;
    for (const child of [...node.children]) bone.add(child);
    parent.remove(node);
    parent.add(bone);
  }
  const geometry = new BoxGeometry(0.2, 0.3, 0.1);
  const count = geometry.attributes.position.count;
  const weights = new Float32Array(count * 4);
  for (let i = 0; i < count; i++) weights[i * 4] = 1;
  geometry.setAttribute('skinIndex', new Uint16BufferAttribute(new Uint16Array(count * 4), 4));
  geometry.setAttribute('skinWeight', new Float32BufferAttribute(weights, 4));
  const mesh = new SkinnedMesh(geometry, new MeshStandardMaterial());
  mesh.name = 'TestSkin';
  source.add(mesh);
  source.updateMatrixWorld(true);
  mesh.bind(new Skeleton(Object.values(JOINTS).map(spec => source.getObjectByName(spec.name))));
  const first = createAthleteInstance(source);
  const second = createAthleteInstance(source);
  const skin1 = first.root.getObjectByName('TestSkin');
  const skin2 = second.root.getObjectByName('TestSkin');
  assert.notEqual(skin1.skeleton, skin2.skeleton);
  assert.equal(skin1.skeleton.bones[0], first.hips);
  assert.equal(skin2.skeleton.bones[0], second.hips);
  first.hips.rotation.y = 0.5;
  assert.equal(skin1.skeleton.bones[0].rotation.y, 0.5);
  assert.ok(Math.abs(skin2.skeleton.bones[0].rotation.y) < 1e-12);
  first.dispose();
  second.dispose();
});
