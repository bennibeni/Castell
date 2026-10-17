'use client';

import { applyPose } from './athlete/rig.js';
import { AthleteModel } from './athlete/AthleteModel.jsx';

import {
  CAP_COLOR,
  PIS_COLORS,
  PINYA_COLOR,
  MANNEQUIN_COLOR,
  NAVY,
} from '../simulation/constants.js';
import { memo, useRef, useCallback, useMemo, useEffect } from 'react';
import { makeGeometries, makeMaterials, Figure } from './Figure.jsx';
import { useFrame } from '@react-three/fiber';
import { newPose, computePose } from '../simulation/poses.js';
import * as THREE from 'three';
import { presetGoal } from './camera.js';
import { topHeightAt } from '../simulation/status.js';
import { Arena } from './Arena.jsx';
import { Guides } from './Guides.jsx';
import { OrbitControls } from '@react-three/drei';

const colorOf = (a) => {
  if (a.role === 'cap') return CAP_COLOR;
  if (a.role === 'tronc' || a.climber) return PIS_COLORS[a.pis - 1];
  return PINYA_COLOR;
};

const Scene = memo(function Scene({
  plan,
  tRef,
  playingRef,
  speedRef,
  onTick,
  onEnd,
  colorByRole,
  mannequin,
  cutaway,
  guides,
  preset,
  onUserCamera,
  athleteScene,
  viewOffsetRef,
  viewPendingRef,
}) {
  const rigs = useRef([]);
  const register = useCallback((i, r) => {
    rigs.current[i] = r;
  }, []);
  const geo = useMemo(() => makeGeometries(), []);
  const mats = useMemo(() => makeMaterials(), []);
  // buffer di lavoro mutabili: stanno in un ref e vengono creati al primo fotogramma
  const work = useRef(null);
  const lastTick = useRef(0);

  useEffect(() => {
    plan.athletes.forEach((a, i) => {
      const rig = rigs.current[i];
      if (!rig) return;
      const color = colorByRole ? colorOf(a) : mannequin ? MANNEQUIN_COLOR : null;
      if (rig.setColor) rig.setColor(color);
      else rig.leo.color.set(color ?? NAVY);
    });
  }, [colorByRole, mannequin, plan, athleteScene]);

  useFrame((state, dt) => {
    if (!work.current || work.current.plan !== plan) {
      work.current = {
        plan,
        poses: plan.athletes.map(() => newPose()),
        tmp: newPose(),
        goalPos: new THREE.Vector3(),
        goalTarget: new THREE.Vector3(),
      };
    }
    const { poses, tmp, goalPos, goalTarget } = work.current;
    const camera = state.camera;
    const controls = state.controls;
    const d = Math.min(dt, 0.05);
    if (playingRef.current) {
      const before = tRef.current;
      tRef.current += d * speedRef.current;
      // pausa automatica tra la fase di salita e quella di discesa
      if (before < plan.T.descent && tRef.current >= plan.T.descent) {
        tRef.current = plan.T.descent;
        onEnd();
      }
      if (tRef.current >= plan.T.end) {
        tRef.current = plan.T.end;
        onEnd();
      }
    }
    const t = tRef.current;

    const cl = Math.hypot(camera.position.x, camera.position.z) || 1;
    const cx = camera.position.x / cl,
      cz = camera.position.z / cl;
    for (let i = 0; i < plan.athletes.length; i++) {
      const rig = rigs.current[i];
      if (!rig) continue;
      const a = plan.athletes[i];
      const p = poses[i];
      computePose(a, t, plan, p, tmp);
      applyPose(rig, p, a.scale);
      rig.root.visible =
        !(cutaway && p.x * cx + p.z * cz > 0.12) && !(preset === 'centro' && a.role === 'agulla');
    }

    const pending = viewPendingRef.current;
    viewPendingRef.current = 0;
    if (controls && presetGoal(preset, topHeightAt(plan, t), goalPos, goalTarget)) {
      // camera e mira traslano insieme: l'inclinazione della vista non cambia
      if (preset === 'video' || preset === 'faccia') {
        goalPos.y += viewOffsetRef.current;
        goalTarget.y += viewOffsetRef.current;
      }
      const k = 1 - Math.exp(-Math.min(dt, 0.25) * 2.4);
      camera.position.lerp(goalPos, k);
      controls.target.lerp(goalTarget, k);
      controls.update();
    } else if (controls && pending) {
      camera.position.y += pending;
      controls.target.y += pending;
      controls.update();
    }

    const now = state.clock.elapsedTime;
    if (now - lastTick.current > 0.08) {
      lastTick.current = now;
      onTick(t);
    }
  });

  return (
    <>
      <color attach="background" args={['#07070b']} />
      <fog attach="fog" args={['#07070b', 30, 65]} />
      <hemisphereLight args={['#c9d3ff', '#5a5560', 0.65]} />
      <directionalLight position={[10, 22, 14]} intensity={1.9} />
      <directionalLight position={[-12, 10, -6]} intensity={0.45} color="#ffb3a6" />
      <directionalLight position={[0, 6, 18]} intensity={0.35} />
      <Arena />
      {plan.athletes.map((a, i) =>
        athleteScene && !mannequin ? (
          <AthleteModel key={a.id} scene={athleteScene} index={i} register={register} />
        ) : (
          <Figure
            key={a.id}
            index={i}
            geo={geo}
            mats={mats}
            register={register}
            mannequin={mannequin}
          />
        ),
      )}
      {guides && <Guides plan={plan} tRef={tRef} />}
      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.08}
        minDistance={0.4}
        maxDistance={60}
        onStart={onUserCamera}
      />
    </>
  );
});

export { Scene };
