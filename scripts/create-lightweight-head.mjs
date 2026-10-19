import { mkdir, writeFile } from 'node:fs/promises';
import { Group, Mesh } from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { createReferenceAthlete } from '../src/app/scene/athlete/referenceModel.js';
globalThis.FileReader ??= class {
  readAsArrayBuffer(blob){blob.arrayBuffer().then(result=>{this.result=result;this.onloadend?.();});}
};
const source=createReferenceAthlete();source.updateMatrixWorld(true);
const head=new Group();head.name='Castell_Original_Head';
for(const name of ['neck','head','hair','bun']){
  const original=source.getObjectByName(`Castell_Torso_${name}`);
  const geometry=original.geometry.clone();geometry.applyMatrix4(original.matrixWorld);
  const part=new Mesh(geometry,original.material);part.name=`Castell_Original_${name}`;head.add(part);
}
head.userData.description='Original procedural Castell mannequin head, neck, hair cap and bun. No image textures.';
const output=new URL('../public/models/catalog/head-mannequin-original.glb',import.meta.url);
await mkdir(new URL('.',output),{recursive:true});
const bytes=await new GLTFExporter().parseAsync(head,{binary:true});
await writeFile(output,Buffer.from(bytes));console.log(`Original head exported: ${bytes.byteLength} bytes`);
