'use client';

import { HIP } from '../simulation/constants.js';
import { makeGeometries, makeMaterials } from './athlete/resources.js';
import { memo, useRef, useMemo, useLayoutEffect } from 'react';

/**
 * mannequin = true: corpo di un solo colore neutro (o del colore del ruolo), senza body,
 * capelli né dettagli; articolazioni (anche, ginocchia, spalle, gomiti) evidenziate
 * da sfere scure e un piccolo "naso" che indica dove guarda la figura.
 */
const Figure = memo(function Figure({ index, geo, mats, register, mannequin }) {
  // un ref per ogni articolazione: vengono letti solo nell'effetto, mai durante il render
  const root = useRef(null);
  const hips = useRef(null);
  const thighL = useRef(null);
  const thighR = useRef(null);
  const kneeL = useRef(null);
  const kneeR = useRef(null);
  const torso = useRef(null);
  const armL = useRef(null);
  const armR = useRef(null);
  const elbowL = useRef(null);
  const elbowR = useRef(null);
  const leo = useMemo(() => mats.navy.clone(), [mats]);

  useLayoutEffect(() => {
    register(index, {
      root: root.current,
      hips: hips.current,
      thighL: thighL.current,
      thighR: thighR.current,
      kneeL: kneeL.current,
      kneeR: kneeR.current,
      torso: torso.current,
      armL: armL.current,
      armR: armR.current,
      elbowL: elbowL.current,
      elbowR: elbowR.current,
      leo,
    });
    return () => register(index, null);
  }, [index, register, leo]);

  // nel manichino tutto il corpo usa il materiale della figura (colore neutro o del ruolo)
  const skin = mannequin ? leo : mats.skin;
  const joint = (s) =>
    mannequin ? <mesh geometry={geo.joint} material={mats.joint} scale={s} /> : null;

  return (
    <group ref={root}>
      <group ref={hips} position={[0, HIP, 0]}>
        <mesh
          geometry={geo.pelvis}
          material={leo}
          position={[0, 0.02, 0]}
          scale={[1.2, 0.75, 0.85]}
        />
        {[1, -1].map((sd) => (
          <group key={sd} ref={sd > 0 ? thighL : thighR} position={[sd * 0.09, -0.02, 0]}>
            {joint(1.15)}
            <mesh geometry={geo.thigh} material={skin} position={[0, -0.215, 0]} />
            <group ref={sd > 0 ? kneeL : kneeR} position={[0, -0.43, 0]}>
              {joint(1)}
              <mesh geometry={geo.shin} material={skin} position={[0, -0.215, 0]} />
              <mesh geometry={geo.foot} material={skin} position={[0, -0.44, 0.05]} />
            </group>
          </group>
        ))}
        <group ref={torso} position={[0, 0.02, 0]}>
          <mesh
            geometry={geo.waist}
            material={skin}
            position={[0, 0.16, 0]}
            scale={[1.05, 1, 0.78]}
          />
          <mesh
            geometry={geo.chest}
            material={leo}
            position={[0, 0.36, 0]}
            scale={[1.18, 1, 0.78]}
          />
          <mesh geometry={geo.neck} material={skin} position={[0, 0.54, 0]} />
          <mesh geometry={geo.head} material={skin} position={[0, 0.65, 0]} />
          {mannequin ? (
            <mesh geometry={geo.nose} material={mats.joint} position={[0, 0.65, 0.1]} />
          ) : (
            <>
              <mesh
                geometry={geo.hair}
                material={mats.hair}
                position={[0, 0.655, -0.012]}
                rotation={[-0.45, 0, 0]}
              />
              <mesh geometry={geo.bun} material={mats.hair} position={[0, 0.745, -0.075]} />
            </>
          )}
          {[1, -1].map((sd) => (
            <group key={sd} ref={sd > 0 ? armL : armR} position={[sd * 0.19, 0.47, 0]}>
              {joint(0.95)}
              <mesh geometry={geo.upper} material={leo} position={[0, -0.143, 0]} />
              <group ref={sd > 0 ? elbowL : elbowR} position={[0, -0.29, 0]}>
                {joint(0.8)}
                <mesh geometry={geo.fore} material={leo} position={[0, -0.133, 0]} />
                <mesh geometry={geo.hand} material={skin} position={[0, -0.285, 0]} />
              </group>
            </group>
          ))}
        </group>
      </group>
    </group>
  );
});

export { makeGeometries, makeMaterials, Figure };
