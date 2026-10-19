import { writeFile, mkdir } from 'node:fs/promises';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { createReferenceAthlete } from '../src/app/scene/athlete/referenceModel.js';

// GLTFExporter usa FileReader anche per buffer binari, senza DOM o immagini.
globalThis.FileReader ??= class {
  readAsArrayBuffer(blob) {
    blob.arrayBuffer().then((result) => {
      this.result = result;
      this.onloadend?.();
    });
  }
};

const directory = new URL('../blender/', import.meta.url);
const output = new URL('athlete-reference.glb', directory);
await mkdir(directory, { recursive: true });
const scene = createReferenceAthlete();
const glb = await new GLTFExporter().parseAsync(scene, { binary: true, onlyVisible: false });
await writeFile(output, Buffer.from(glb));
console.log(`Modello di riferimento creato: ${output.pathname} (${glb.byteLength} byte)`);
console.log('Il catalogo pubblico non viene modificato. Il riferimento resta locale in blender/.');
