import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { inspectAthleteModel } from '../src/app/scene/athlete/rig.js';

const file = process.argv[2]
  ? path.resolve(process.argv[2])
  : new URL('../public/models/athlete.glb', import.meta.url);
try {
  const bytes = await readFile(file);
  // I modelli con texture richiedono il browser per decodificare le immagini.
  // Per controllare nomi, articolazioni e materiali basta caricare la struttura.
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const loader = new GLTFLoader();
  loader.register((parser) => ({
    name: 'CastellValidation',
    loadTexture() {
      return Promise.resolve(null);
    },
  }));
  const gltf = await loader.parseAsync(buffer, '');
  const result = inspectAthleteModel(gltf.scene);
  if (!result.valid) throw new Error(result.errors.join('\n'));
  console.log(
    'Modello compatibile: articolazioni, gerarchia, proporzioni di riferimento e materiale della divisa validi.',
  );
  console.log('Texture e resa visiva vanno controllate anche nel browser.');
  if (gltf.animations.length)
    console.log('Le animazioni presenti sono ignorate: le pose sono guidate dalla simulazione.');
} catch (error) {
  console.error(`Modello non compatibile:\n${error.message}`);
  process.exitCode = 1;
}
