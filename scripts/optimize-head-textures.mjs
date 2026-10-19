// Preserve all mesh/accessor bytes; optimize embedded texture images only.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import sharp from 'sharp';
import assert from 'node:assert/strict';
const directory=new URL('../artifacts/head-texture-optimization/',import.meta.url);
await mkdir(directory,{recursive:true});
let bytes;
try {bytes=await readFile(new URL('../public/models/catalog/head-detailed-small.glb',import.meta.url));}
catch(error){if(error.code!=='ENOENT')throw error;bytes=await readFile(new URL('original.glb',directory));}
const jsonSize=bytes.readUInt32LE(12);
const json=JSON.parse(bytes.subarray(20,20+jsonSize)),original=structuredClone(json);
const bin=bytes.subarray(28+jsonSize);
await writeFile(new URL('original.glb',directory),bytes);
const replacements=new Map(),report=[];
async function normalImage(data,size){
  const {data:raw,info}=await sharp(data).removeAlpha().resize(size,size,{fit:'inside',withoutEnlargement:true}).raw().toBuffer({resolveWithObject:true});
  for(let i=0;i<raw.length;i+=3){
    let x=raw[i]/127.5-1,y=raw[i+1]/127.5-1,z=raw[i+2]/127.5-1;
    const length=Math.hypot(x,y,z)||1;x/=length;y/=length;z/=length;
    raw[i]=Math.round((x+1)*127.5);raw[i+1]=Math.round((y+1)*127.5);raw[i+2]=Math.round((z+1)*127.5);
  }
  return sharp(raw,{raw:{width:info.width,height:info.height,channels:3}}).png({compressionLevel:9,adaptiveFiltering:true}).toBuffer();
}
for(const image of json.images){
  const view=json.bufferViews[image.bufferView];
  const input=bin.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
  const name=image.name||'',before=await sharp(input).metadata();
  let output=input;
  if(/body_basecolor|Eye_BaseColor/i.test(name)){
    // Keep every texel of the face and iris; high quality 4:4:4 avoids color bleed.
    output=await sharp(input).removeAlpha().jpeg({quality:95,chromaSubsampling:'4:4:4',mozjpeg:true}).toBuffer();
    image.mimeType='image/jpeg';
  }else if(/body_normal/i.test(name)){
    output=await normalImage(input,1536);
  }else if(/body_roughness/i.test(name)){
    // Only green is used by this material's roughness; metallicFactor is zero.
    assert.equal(json.materials.find(m=>m.name==='Castell_Hinako_Skin').pbrMetallicRoughness.metallicFactor,0);
    output=await sharp(input).extractChannel(1).resize(1024,1024).jpeg({quality:98,mozjpeg:true}).toBuffer();
    image.mimeType='image/jpeg';
  }else if(/eyelashes_normal/i.test(name)){
    output=await normalImage(input,512);
  }
  // Hair and lash color/opacity stay byte-identical, preserving alpha silhouettes.
  replacements.set(image.bufferView,output);
  const after=await sharp(output).metadata();
  report.push({name,originalBytes:input.length,optimizedBytes:output.length,originalSize:[before.width,before.height],optimizedSize:[after.width,after.height],unchanged:input.equals(output)});
}
let offset=0;const chunks=[];
for(const [i,view] of json.bufferViews.entries()){
  assert.equal(view.buffer||0,0);
  const originalBytes=bin.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
  const data=replacements.get(i)||originalBytes;
  const padding=(4-offset%4)%4;if(padding){chunks.push(Buffer.alloc(padding));offset+=padding;}
  view.byteOffset=offset;view.byteLength=data.length;chunks.push(data);offset+=data.length;
  if(!replacements.has(i))assert.ok(data.equals(originalBytes));
}
const binaryPadding=(4-offset%4)%4;if(binaryPadding){chunks.push(Buffer.alloc(binaryPadding));offset+=binaryPadding;}
const binary=Buffer.concat(chunks);json.buffers[0].byteLength=offset;
assert.deepEqual(json.meshes,original.meshes);assert.deepEqual(json.nodes,original.nodes);assert.deepEqual(json.accessors,original.accessors);assert.deepEqual(json.materials,original.materials);
let text=Buffer.from(JSON.stringify(json));text=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]);
const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(28+text.length+binary.length,8);header.writeUInt32LE(text.length,12);header.writeUInt32LE(0x4e4f534a,16);
const binHeader=Buffer.alloc(8);binHeader.writeUInt32LE(binary.length,0);binHeader.writeUInt32LE(0x004e4942,4);
const result=Buffer.concat([header,text,binHeader,binary]);
await writeFile(new URL('optimized.glb',directory),result);
await writeFile(new URL('report.json',directory),JSON.stringify({originalBytes:bytes.length,optimizedBytes:result.length,textures:report},null,2)+'\n');
console.log(JSON.stringify({originalMiB:bytes.length/1048576,optimizedMiB:result.length/1048576,savedPercent:100*(1-result.length/bytes.length),textures:report},null,2));
