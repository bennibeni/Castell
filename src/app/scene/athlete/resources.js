import * as THREE from 'three';
import { TAU } from '../../simulation/math.js';
import { NAVY, JOINT_COLOR } from '../../simulation/constants.js';

/* ─────────────────────────── grafica ─────────────────────────── */
function makeGeometries() {
  return {
    thigh: new THREE.CapsuleGeometry(0.068, 0.31, 4, 10),
    shin: new THREE.CapsuleGeometry(0.052, 0.32, 4, 10),
    foot: new THREE.BoxGeometry(0.085, 0.05, 0.21),
    pelvis: new THREE.SphereGeometry(0.13, 14, 10),
    waist: new THREE.CapsuleGeometry(0.1, 0.1, 4, 12),
    chest: new THREE.CapsuleGeometry(0.125, 0.13, 4, 12),
    neck: new THREE.CylinderGeometry(0.045, 0.05, 0.09, 10),
    head: new THREE.SphereGeometry(0.102, 16, 12),
    hair: new THREE.SphereGeometry(0.108, 16, 12, 0, TAU, 0, Math.PI * 0.62),
    bun: new THREE.SphereGeometry(0.052, 10, 8),
    upper: new THREE.CapsuleGeometry(0.043, 0.2, 4, 8),
    fore: new THREE.CapsuleGeometry(0.038, 0.19, 4, 8),
    hand: new THREE.SphereGeometry(0.042, 8, 6),
    joint: new THREE.SphereGeometry(0.062, 12, 10),
    nose: new THREE.SphereGeometry(0.028, 8, 6),
  };
}

function makeMaterials() {
  return {
    skin: new THREE.MeshStandardMaterial({ color: '#d6a07a', roughness: 0.55 }),
    navy: new THREE.MeshStandardMaterial({ color: NAVY, roughness: 0.42, metalness: 0.08 }),
    hair: new THREE.MeshStandardMaterial({ color: '#3a2618', roughness: 0.7 }),
    joint: new THREE.MeshStandardMaterial({ color: JOINT_COLOR, roughness: 0.35, metalness: 0.2 }),
  };
}

export { makeGeometries, makeMaterials };
