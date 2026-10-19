import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Vector3 } from 'three';
import { createAthleteInstance, applyPose } from '../src/app/scene/athlete/rig.js';
import { buildPlan } from '../src/app/simulation/plan.js';
import { newPose, computePose } from '../src/app/simulation/poses.js';
const outputDirectory=process.argv[3] || 'artifacts/athlete';
await mkdir(outputDirectory,{recursive:true});
const bytes=await readFile(process.argv[2] || 'blender/athlete-castell.glb');
const loader=new GLTFLoader();
// Geometry checks do not require browser-only image decoding.
loader.register(()=>({name:'CastellSkinCheck',loadTexture(){return Promise.resolve(null);}}));
const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
const rig=createAthleteInstance(gltf.scene);
rig.root.updateMatrixWorld(true);
const skins=[];
rig.root.traverse(o=>{if(o.isSkinnedMesh) skins.push(o);});
assert.ok(skins.length>0);
let restVertices=0;
rig.root.traverse(mesh=>{
 if(!mesh.isMesh)return;
 const pos=mesh.geometry.attributes.position;
 for(let i=0;i<pos.count;i++){
  const v=new Vector3().fromBufferAttribute(pos,i);
  if(mesh.isSkinnedMesh)mesh.applyBoneTransform(i,v);
  mesh.localToWorld(v);
  rig.root.worldToLocal(v);
  assert.ok(Math.abs(v.x)<.8 && v.y>-.1 && v.y<2.0 && Math.abs(v.z)<.6,
    `Rest geometry out of athlete bounds: ${mesh.name}, vertex ${i}, ${v.toArray()}`);
  restVertices++;
 }
});
let vertices=0;
for(const mesh of skins){
 const pos=mesh.geometry.attributes.position, w=mesh.geometry.attributes.skinWeight;
 for(let i=0;i<pos.count;i++){
  const total=w.getX(i)+w.getY(i)+w.getZ(i)+w.getW(i);
  assert.ok(Math.abs(total-1)<1e-5,`Weight sum ${total}`);
  const v=new Vector3().fromBufferAttribute(pos,i);
  assert.ok(mesh.applyBoneTransform(i,v.clone()).distanceTo(v)<1e-5,'Rest pose changed');
  vertices++;
 }
}
const plan=buildPlan();
let checked=0;
for(const athlete of plan.athletes){
 for(let k=0;k<84;k++){
  const pose=newPose();
  computePose(athlete,plan.T.end*k/83,plan,pose,newPose());
  applyPose(rig,pose,athlete.scale);
  rig.root.updateMatrixWorld(true);
  for(const mesh of skins){
   const pos=mesh.geometry.attributes.position;
   for(let i=0;i<pos.count;i+=43){
    const v=mesh.applyBoneTransform(i,new Vector3().fromBufferAttribute(pos,i));
    assert.ok(v.toArray().every(Number.isFinite),'Invalid deformed vertex');
    assert.ok(v.length()<3.2,'Exploding skin');
    checked++;
   }
  }
 }
}
const poses={
 rest:{},
 support:{aL:[-.95,.2,-1.2],aR:[-.95,.2,-1.2]},
 squat:{hipY:.52,thL:-1.05,thR:-1.05,knL:1.7,knR:1.7,lean:.3,aL:[-.75,.2,-1.35],aR:[-.75,.2,-1.35]},
 salute:{aL:[-.1,1.45,-.05],aR:[-.1,1.45,-.05]},
};
for(const [name,values] of Object.entries(poses)){
 const pose=Object.assign(newPose(),values);
 applyPose(rig,pose,1);
 rig.root.updateMatrixWorld(true);
 const meshes=[];
 rig.root.traverse(mesh=>{
  if(!mesh.isMesh)return;
  const pos=mesh.geometry.attributes.position;
  const points=[];
  for(let i=0;i<pos.count;i++){
   const v=new Vector3().fromBufferAttribute(pos,i);
   if(mesh.isSkinnedMesh) mesh.applyBoneTransform(i,v);
   mesh.localToWorld(v);
   points.push([v.x,-v.z,v.y]);
  }
  const ix=mesh.geometry.index;
  const indices=ix?Array.from(ix.array):Array.from({length:pos.count},(_,i)=>i);
  const faces=[];
  for(let i=0;i<indices.length;i+=3)faces.push(indices.slice(i,i+3));
  meshes.push({name:mesh.name,points,faces,color:mesh.material.color.toArray()});
 });
 await writeFile(`${outputDirectory}/pose-${name}.json`,JSON.stringify(meshes));
}
console.log(JSON.stringify({skins:skins.length,vertices,restVertices,athletes:plan.athletes.length,instants:84,checkedVertices:checked,restPose:'unchanged',weights:'normalized'}));
