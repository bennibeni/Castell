import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Box3, Vector3 } from 'three';
import { BODIES, HEADS, compatible } from '../src/app/scene/athlete/catalog.js';
import { composeAthlete } from '../src/app/scene/athlete/composition.js';
async function load(url) {
  const b=await readFile(new URL(`../public${url}`,import.meta.url));
  const loader=new GLTFLoader();loader.register(()=>({name:'TestTextureStub',loadTexture:()=>Promise.resolve(null)}));
  return (await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;
}
test('la testa dettagliata piccola ripristina geometria e dimensioni precedenti senza modificare quella originale',async()=>{
  const small=HEADS.find(h=>h.id==='mannequin-detailed-small');
  const original=HEADS.find(h=>h.id==='mannequin-original');
  const body=BODIES.find(b=>b.id==='mannequin');
  assert.equal(compatible('adult',small.id),false);
  assert.notEqual(small.url,original.url);
  assert.ok((await readFile(new URL(`../public${original.url}`,import.meta.url))).length<50000);
  const [bodySource,donor]=await Promise.all([load(body.url),load(small.url)]);
  const result=composeAthlete(bodySource,donor,body,small);
  const face=result.getObjectByName('Castell_Hinako_Head');
  assert.equal(face.geometry,donor.getObjectByName('Castell_Hinako_Head').geometry);
  assert.equal(face.material,donor.getObjectByName('Castell_Hinako_Head').material);
  result.updateMatrixWorld(true);
  const a=new Box3().setFromObject(face);
  assert.ok(Math.abs(a.getSize(new Vector3()).y-.24380135536193848*body.headScale)<1e-6);
  assert.ok(Math.abs(a.min.y-(1.4149999618530273*body.headScale+body.headY))<1e-6);
  const selected=result.getObjectByName('Castell_Selected_Head');
  assert.equal(selected.parent,result.getObjectByName('Castell_Torso'));
  assert.ok(Math.abs(selected.scale.x-selected.scale.y)<1e-6);
});
