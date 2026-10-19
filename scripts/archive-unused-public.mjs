// Preserve unused graphics locally, outside the published directory.
import { readdir, readFile, mkdir, rename, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { BODIES, HEADS } from '../src/app/scene/athlete/catalog.js';
const root=fileURLToPath(new URL('../',import.meta.url));
const publicRoot=path.join(root,'public');
const archiveRoot=path.join(root,'artifacts','public-archive');
const keep=new Set([...BODIES,...HEADS].flatMap(item=>[item.url,item.image]));
function within(base,target) {
  const relative=path.relative(base,target);
  if(!relative||relative.startsWith('..')||path.isAbsolute(relative))throw new Error(`Path outside intended directory: ${target}`);
}
// Keep external glTF images/buffers too, if a future export uses them.
for(const url of keep){
  const filename=path.resolve(publicRoot,'.'+url);within(publicRoot,filename);
  const bytes=await readFile(filename);
  if(!url.endsWith('.glb'))continue;
  const json=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
  for(const resource of [...json.images||[],...json.buffers||[]]){
    if(!resource.uri||/^(data:|https?:)/.test(resource.uri))continue;
    const dependent=path.resolve(path.dirname(filename),decodeURIComponent(resource.uri));within(publicRoot,dependent);
    keep.add('/'+path.relative(publicRoot,dependent).split(path.sep).join('/'));
  }
}
const plan=[];
for(const folder of ['models','previews']){
  async function walk(directory){
    for(const entry of await readdir(directory,{withFileTypes:true})){
      const source=path.join(directory,entry.name);
      if(entry.isDirectory()){await walk(source);continue;}
      if(!entry.isFile())continue;
      const relative=path.relative(publicRoot,source),url='/'+relative.split(path.sep).join('/');
      if(keep.has(url))continue;
      const destination=path.join(archiveRoot,relative);
      within(publicRoot,source);within(archiveRoot,destination);
      plan.push({relative,source,destination,bytes:(await stat(source)).size});
    }
  }
  await walk(path.join(publicRoot,folder));
}
console.log(JSON.stringify({files:plan.length,MiB: +(plan.reduce((n,f)=>n+f.bytes,0)/1048576).toFixed(1),paths:plan.map(f=>f.relative)},null,2));
if(!process.argv.includes('--apply')){console.log('Dry run. Pass --apply to archive.');process.exit(0);}
for(const item of plan){
  // Never overwrite an earlier archive silently.
  try {await stat(item.destination);throw new Error(`Archive already exists: ${item.destination}`);}
  catch(error){if(error.code!=='ENOENT')throw error;}
}
await mkdir(archiveRoot,{recursive:true});
await writeFile(path.join(archiveRoot,`manifest-${Date.now()}.json`),JSON.stringify(plan,null,2)+'\n');
for(const item of plan){await mkdir(path.dirname(item.destination),{recursive:true});await rename(item.source,item.destination);}
console.log('Archive complete. Source files are preserved in artifacts/public-archive/.');
