// Run after Blender export. Bind the skin directly to Castell's named controls.
import { readFile, writeFile } from 'node:fs/promises';
import { Matrix4, Quaternion, Vector3 } from 'three';
const input = process.argv[2] || 'blender/athlete-raw.glb';
const output = process.argv[3] || 'blender/athlete-castell.glb';
const bytes = await readFile(input);
if (bytes.readUInt32LE(0) !== 0x46546c67) throw new Error('Expected GLB');
const jsonLength = bytes.readUInt32LE(12);
const gltf = JSON.parse(bytes.subarray(20,20+jsonLength));
const bin = Buffer.from(bytes.subarray(28+jsonLength));
const parent = new Map();
gltf.nodes.forEach((n,i) => n.children?.forEach(c => parent.set(c,i)));
function world(i) {
  const n = gltf.nodes[i];
  const m = n.matrix ? new Matrix4().fromArray(n.matrix) : new Matrix4().compose(
    new Vector3().fromArray(n.translation || [0,0,0]),
    new Quaternion().fromArray(n.rotation || [0,0,0,1]),
    new Vector3().fromArray(n.scale || [1,1,1]));
  return parent.has(i) ? world(parent.get(i)).multiply(m) : m;
}
for (const skin of gltf.skins || []) {
  skin.joints = skin.joints.map(i => {
    const name = gltf.nodes[i].name.replace(/^Skin_/, 'Castell_');
    const target = gltf.nodes.findIndex(n=>n.name===name);
    if(target<0) throw new Error('Missing control '+name);
    return target;
  });
  skin.skeleton = gltf.nodes.findIndex(n=>n.name==='Castell_Hips');
  const a = gltf.accessors[skin.inverseBindMatrices];
  const view = gltf.bufferViews[a.bufferView];
  const offset = (view.byteOffset||0)+(a.byteOffset||0);
  skin.joints.forEach((joint,i) => {
    world(joint).invert().elements.forEach((value,k)=>bin.writeFloatLE(value,offset+i*64+k*4));
  });
}
// The Blender-only helper bones are unnecessary in the browser.
const helper = gltf.nodes.findIndex(n=>n.name==='Castell_Skin_Rig');
for(const n of gltf.nodes) if(n.children) n.children=n.children.filter(i=>i!==helper);
for(const s of gltf.scenes) s.nodes=s.nodes.filter(i=>i!==helper);
for(const n of gltf.nodes) {
  if(n.name==='Castell_Body') n.extras={
    source:'Female body reference',author:'Rex Mun',
    assetBaseId:'b8fd598d-118c-4d37-be23-989a2f77cab2',
    identity:n.extras?.identity,
    faceRevision:n.extras?.face_revision,
    surfaceDetail:n.extras?.surface_detail,
  };
}
// Hair cards use a depth-writing cutout to avoid blend-order artifacts among athletes.
for (const material of gltf.materials || []) {
  if (material.name === 'Castell_Hair_HalfBun') {
    material.alphaMode = 'MASK';
    material.alphaCutoff = 0.35;
  }
  if (material.name === 'Castell_Hinako_Hair' || material.name === 'Castell_Hinako_Lashes') {
    material.alphaMode = 'MASK';
    material.alphaCutoff = 0.25;
  }
}
let json = Buffer.from(JSON.stringify(gltf));
json = Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,0x20)]);
const header=Buffer.alloc(20);
header.writeUInt32LE(0x46546c67,0); header.writeUInt32LE(2,4);
header.writeUInt32LE(28+json.length+bin.length,8);
header.writeUInt32LE(json.length,12); header.writeUInt32LE(0x4e4f534a,16);
const binHeader=Buffer.alloc(8);
binHeader.writeUInt32LE(bin.length,0); binHeader.writeUInt32LE(0x004e4942,4);
await writeFile(output,Buffer.concat([header,json,binHeader,bin]));
console.log('Castell skin exported: '+output);
