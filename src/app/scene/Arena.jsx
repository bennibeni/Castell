'use client';

import { useRef, useMemo, useLayoutEffect } from 'react';
import { hash } from '../simulation/math.js';
import * as THREE from 'three';

function Audience() {
  const ref = useRef();
  const data = useMemo(() => {
    const out = [];
    const palette = [
      '#1c1f28',
      '#262a35',
      '#14171f',
      '#2e2a33',
      '#3a2f30',
      '#1f2838',
      '#3c3f47',
      '#181b28',
      '#5a3f45',
    ];
    let i = 0;
    for (let side = 0; side < 2; side++)
      for (let row = 0; row < 9; row++)
        for (let j = 0; j < 32; j++) {
          i++;
          if (hash(i * 3.1) < 0.12) continue;
          const along = -12.4 + j * 0.8 + (row % 2) * 0.4;
          const depth = 10.8 + row * 0.9;
          const h = (row + 1) * 0.5;
          const x = side === 0 ? -depth : along;
          const z = side === 0 ? along : -depth;
          out.push({
            x,
            y: h + 0.45,
            z,
            s: 0.9 + hash(i) * 0.25,
            c: palette[Math.floor(hash(i * 7.7) * palette.length)],
          });
        }
    return out;
  }, []);
  const headRef = useRef();
  useLayoutEffect(() => {
    const m = new THREE.Object3D();
    const c = new THREE.Color();
    const skins = ['#7a5a48', '#8a6a55', '#5e4436', '#9a7a62'];
    data.forEach((d, i) => {
      m.position.set(d.x, d.y, d.z);
      m.scale.set(1, d.s, 1);
      m.updateMatrix();
      ref.current.setMatrixAt(i, m.matrix);
      ref.current.setColorAt(i, c.set(d.c));
      m.position.set(d.x, d.y + 0.36 * d.s + 0.2, d.z);
      m.scale.set(1, 1, 1);
      m.updateMatrix();
      headRef.current.setMatrixAt(i, m.matrix);
      headRef.current.setColorAt(i, c.set(skins[i % skins.length]));
    });
    for (const r of [ref.current, headRef.current]) {
      r.instanceMatrix.needsUpdate = true;
      if (r.instanceColor) r.instanceColor.needsUpdate = true;
    }
  }, [data]);
  return (
    <group>
      <instancedMesh ref={ref} args={[undefined, undefined, data.length]}>
        <capsuleGeometry args={[0.21, 0.32, 4, 8]} />
        <meshStandardMaterial roughness={0.95} />
      </instancedMesh>
      <instancedMesh ref={headRef} args={[undefined, undefined, data.length]}>
        <sphereGeometry args={[0.12, 10, 8]} />
        <meshStandardMaterial roughness={0.9} />
      </instancedMesh>
    </group>
  );
}

function Arena() {
  const steps = [];
  for (let side = 0; side < 2; side++)
    for (let row = 0; row < 9; row++) {
      const depth = 10.8 + row * 0.9;
      const h = (row + 1) * 0.5;
      steps.push(
        <mesh
          key={`${side}-${row}`}
          position={side === 0 ? [-depth, h / 2, 0] : [0, h / 2, -depth]}
        >
          <boxGeometry args={side === 0 ? [0.9, h, 26] : [26, h, 0.9]} />
          <meshStandardMaterial color="#17171c" roughness={0.95} />
        </mesh>,
      );
    }
  const lamps = [
    [-11, 13, -18, '#ff2b3d'],
    [-19, 12.5, -8, '#ff2b3d'],
    [-3, 15, -21, '#ff2b3d'],
    [6, 17, -21, '#fff6e0'],
    [-21, 16, 4, '#fff6e0'],
  ];
  const lines = [
    [0, 7.6, 16, 0.06],
    [0, -7.6, 16, 0.06],
    [7.6, 0, 0.06, 16],
    [-7.6, 0, 0.06, 16],
  ];
  return (
    <group>
      <mesh rotation-x={-Math.PI / 2} position={[0, -0.002, 0]}>
        <planeGeometry args={[90, 90]} />
        <meshStandardMaterial color="#141418" roughness={0.95} />
      </mesh>
      <mesh rotation-x={-Math.PI / 2}>
        <planeGeometry args={[16, 16]} />
        <meshStandardMaterial color="#a3a3aa" roughness={0.9} />
      </mesh>
      {lines.map(([x, z, w, d], i) => (
        <mesh key={i} position={[x, 0.004, z]} rotation-x={-Math.PI / 2}>
          <planeGeometry args={[w, d]} />
          <meshBasicMaterial color="#f4f4f4" />
        </mesh>
      ))}
      {steps}
      <Audience />
      {lamps.map(([x, y, z, c], i) => (
        <mesh key={i} position={[x, y, z]}>
          <sphereGeometry args={[0.35, 12, 10]} />
          <meshBasicMaterial color={c} toneMapped={false} />
        </mesh>
      ))}
      <pointLight
        position={[-11, 12, -16]}
        color="#ff3346"
        intensity={0.8}
        distance={30}
        decay={0}
      />
    </group>
  );
}

export { Arena };
