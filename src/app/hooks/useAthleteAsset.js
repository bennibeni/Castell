'use client';

import { useEffect, useState } from 'react';
import { COMPOSITION_EVENT } from '../scene/athlete/catalog.js';
import { getSessionComposition } from '../scene/athlete/session.js';
import { loadComposition } from '../scene/athlete/composition.js';

export function useAthleteAsset(enabled) {
  const [asset, setAsset] = useState({ scene: null, status: 'idle', message: '' });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const refresh = () => setRevision(value => value + 1);
    window.addEventListener(COMPOSITION_EVENT, refresh);
    return () => { window.removeEventListener(COMPOSITION_EVENT, refresh); };
  }, []);
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    setAsset({ scene: null, status: 'loading', message: 'Caricamento modello GLB…' });
    loadComposition(getSessionComposition())
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
  }, [enabled, revision]);
  return enabled ? asset : { scene: null, status: 'idle', message: '' };
}
