'use client';

import { PIS_COLORS, COLS, A, Y, Y_AIX } from '../simulation/constants.js';
import * as THREE from 'three';
import { useRef, useLayoutEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { present, topHeightAt } from '../simulation/status.js';

/* linee guida: quadrati del tronc, colonne (rengles), pom de dalt, asse */
const GUIDE_PIS_COLORS = PIS_COLORS.map((c) => new THREE.Color(c));
const GUIDE_EDGE_COLOR = new THREE.Color('#e9e4d4');
const GUIDE_AXIS_COLOR = new THREE.Color('#ffffff');
const GUIDE_MAXV = 160;

function Guides({ plan, tRef }) {
  const lineRef = useRef(null);

  useLayoutEffect(() => {
    const g = lineRef.current.geometry;
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(GUIDE_MAXV * 3), 3));
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(GUIDE_MAXV * 3), 3));
    g.setDrawRange(0, 0);
  }, []);

  useFrame(() => {
    const line = lineRef.current;
    if (!line || !line.geometry.attributes.position) return;
    const g = line.geometry;
    const positions = g.attributes.position.array;
    const colors = g.attributes.color.array;
    const t = tRef.current;
    let v = 0;
    const push = (x, y, z, c) => {
      positions[v * 3] = x;
      positions[v * 3 + 1] = y;
      positions[v * 3 + 2] = z;
      colors[v * 3] = c.r;
      colors[v * 3 + 1] = c.g;
      colors[v * 3 + 2] = c.b;
      v++;
    };
    const anyPresent = (p) => plan.pis[p].members.some((a) => present(a, t));
    // quadrati del tronc alla quota dei piedi e colonne verticali
    const corners = COLS.map(([cx, cz]) => [cx * A, cz * A]);
    let topCol = -1;
    for (let p = 1; p <= 5; p++) {
      if (!anyPresent(p)) continue;
      topCol = p;
      const y = Y[p - 1] + 0.03;
      for (let i = 0; i < 4; i++) {
        const [x0, z0] = corners[i],
          [x1, z1] = corners[(i + 1) % 4];
        push(x0, y, z0, GUIDE_PIS_COLORS[p - 1]);
        push(x1, y, z1, GUIDE_PIS_COLORS[p - 1]);
      }
    }
    if (topCol > 1)
      corners.forEach(([x, z]) => {
        push(x, 0, z, GUIDE_EDGE_COLOR);
        push(x, Y[topCol - 1], z, GUIDE_EDGE_COLOR);
      });
    if (anyPresent(6)) {
      push(0, Y[5] + 0.03, A, GUIDE_PIS_COLORS[5]);
      push(0, Y[5] + 0.03, -A, GUIDE_PIS_COLORS[5]);
    }
    if (anyPresent(7)) {
      push(0, Y_AIX, A * 0.6, GUIDE_PIS_COLORS[6]);
      push(0, Y_AIX, -A * 0.6, GUIDE_PIS_COLORS[6]);
    }
    const top = topHeightAt(plan, t);
    push(0, 0, 0, GUIDE_AXIS_COLOR);
    push(0, top + 0.3, 0, GUIDE_AXIS_COLOR);
    g.setDrawRange(0, v);
    g.attributes.position.needsUpdate = true;
    g.attributes.color.needsUpdate = true;
  });

  return (
    <lineSegments ref={lineRef} renderOrder={10} frustumCulled={false}>
      <bufferGeometry />
      <lineBasicMaterial vertexColors transparent opacity={0.9} depthTest={false} />
    </lineSegments>
  );
}

export { Guides };
