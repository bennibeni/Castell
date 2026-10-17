'use client';

import { memo, useLayoutEffect, useMemo } from 'react';
import { createAthleteInstance } from './rig.js';

export const AthleteModel = memo(function AthleteModel({ scene, index, register }) {
  const rig = useMemo(() => createAthleteInstance(scene), [scene]);
  useLayoutEffect(() => {
    register(index, rig);
    return () => register(index, null);
  }, [index, register, rig]);
  useLayoutEffect(() => () => rig.dispose(), [rig]);
  // Geometrie e texture sono condivise tra le 90 copie; ogni copia ha articolazioni e materiali propri.
  return <primitive object={rig.root} dispose={null} />;
});
