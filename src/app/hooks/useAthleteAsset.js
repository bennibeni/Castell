'use client';

import { useEffect, useState } from 'react';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { ATHLETE_MODEL_URL, inspectAthleteModel } from '../scene/athlete/rig.js';

// Una sola copia sorgente per la sessione: alternare GLB e figure standard non ricarica le texture.
let modelPromise;
function loadModel() {
  if (!modelPromise) {
    modelPromise = new GLTFLoader()
      .loadAsync(ATHLETE_MODEL_URL)
      .then((gltf) => {
        const result = inspectAthleteModel(gltf.scene);
        if (!result.valid) throw new Error(result.errors.join('; '));
        return gltf.scene;
      })
      .catch((error) => {
        modelPromise = null;
        throw error;
      });
  }
  return modelPromise;
}

export function useAthleteAsset(enabled) {
  const [asset, setAsset] = useState({ scene: null, status: 'idle', message: '' });
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    setAsset({ scene: null, status: 'loading', message: 'Caricamento modello GLB…' });
    loadModel()
      .then((scene) => {
        if (!active) return;
        setAsset({ scene, status: 'ready', message: 'Modello GLB attivo' });
      })
      .catch((error) => {
        if (active)
          setAsset({
            scene: null,
            status: 'error',
            message: `Uso le figure standard: ${error.message}`,
          });
      });
    return () => {
      active = false;
    };
  }, [enabled]);
  return enabled ? asset : { scene: null, status: 'idle', message: '' };
}
