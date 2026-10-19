import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Box3, Vector3 } from 'three';
import { BODIES, HEADS, compatible, normalizeComposition, DEFAULT_COMPOSITION } from '../src/app/scene/athlete/catalog.js';
import { composeAthlete } from '../src/app/scene/athlete/composition.js';
import { createAthleteInstance, inspectAthleteModel } from '../src/app/scene/athlete/rig.js';
const cache=new Map();
async function source(url){
  if(!cache.has(url))cache.set(url,(async()=>{
    const bytes=await readFile(new URL(`../public${url}`,import.meta.url));
    const loader=new GLTFLoader();loader.register(()=>({name:'TestTextureStub',loadTexture:()=>Promise.resolve(null)}));
    return (await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene;
  })());
  return cache.get(url);
}
test('preferenze rimosse o corrotte diventano selezioni valide senza perdere il corpo',()=>{
  for(const value of [null,{}, 'broken', {bodyId:'unknown',headId:'adult-smile'}])assert.deepEqual(normalizeComposition(value),DEFAULT_COMPOSITION);
  for(const body of BODIES){
    for(const oldId of ['hinako','hinako-small','mannequin-original-small','adult-original','adult-smile','missing',null]){
      const migrated=normalizeComposition({bodyId:body.id,headId:oldId});
      assert.equal(migrated.bodyId,body.id);
      assert.ok(compatible(migrated.bodyId,migrated.headId));
      const small=['hinako-small','mannequin-original-small'].includes(oldId)&&body.id==='mannequin';
      assert.equal(migrated.headId,small?'mannequin-detailed-small':'mannequin-original');
    }
    for(const head of HEADS){const current={bodyId:body.id,headId:head.id};if(compatible(body.id,head.id))assert.deepEqual(normalizeComposition(current),current);else assert.deepEqual(normalizeComposition(current),{bodyId:body.id,headId:'mannequin-original'});}
  }
});
test('ogni composizione disponibile conserva articolazioni, scala e testa solidale al torso',async()=>{
  for(const body of BODIES)for(const head of HEADS){
    if(!compatible(body.id,head.id))continue;
    const scene=composeAthlete(await source(body.url),await source(head.url),body,head);
    assert.deepEqual(inspectAthleteModel(scene).errors,[],`${body.id}/${head.id}`);
    const first=createAthleteInstance(scene),second=createAthleteInstance(scene);
    first.root.updateMatrixWorld(true);second.root.updateMatrixWorld(true);
    const attached=first.root.getObjectByName('Castell_Selected_Head');
    assert.equal(attached.parent,first.torso);
    const box=new Box3().setFromObject(attached);
    // Loose hair may reach the shoulders; no head asset may contain a body.
    assert.ok(box.min.y>1.2&&box.max.y<1.9,`Testa fuori scala ${body.id}/${head.id}: ${box.min.y}, ${box.max.y}`);
    const local=attached.position.clone();
    const before=attached.getWorldPosition(new Vector3());
    first.torso.rotation.x=.4;first.root.updateMatrixWorld(true);
    assert.ok(attached.position.equals(local));
    assert.ok(attached.getWorldPosition(new Vector3()).distanceTo(before)>.01);
    assert.ok(Math.abs(second.torso.rotation.x)<1e-8);
    let skins=0;first.root.traverse(o=>{if(o.isSkinnedMesh)skins++;});
    assert.equal(skins>0,body.id==='adult');
    first.dispose();second.dispose();
  }
});
