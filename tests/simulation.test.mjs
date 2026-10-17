import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { buildPlan } from '../src/app/simulation/plan.js';
import { computePose, newPose } from '../src/app/simulation/poses.js';
import { topHeightAt, baixLoadAt, phaseAt, present } from '../src/app/simulation/status.js';

const baseline = JSON.parse(await readFile(new URL('./simulation-baseline.json', import.meta.url), 'utf8'));
const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

test('coreografia, pose e statistiche coincidono con la versione precedente al refactoring', () => {
  const plan = buildPlan();
  assert.equal(digest(plan), baseline.planHash, 'Piano della coreografia invariato');
  const samples = baseline.times.map(t => ({
    t,
    top: topHeightAt(plan, t),
    load: baixLoadAt(plan, t),
    phase: phaseAt(plan, t),
    poses: plan.athletes.map(a => {
      const pose = newPose();
      computePose(a, t, plan, pose, newPose());
      return pose;
    }),
  }));
  assert.equal(digest(samples), baseline.samplesHash, 'Tutte le 90 pose in 84 istanti, altezza, carico e fase invariati');
});

test('il castell completo conserva 90 atlete e tutti gli otto piani', () => {
  const plan = buildPlan();
  assert.equal(plan.athletes.length, 90);
  assert.equal(new Set(plan.athletes.map(a => a.id)).size, 90);
  for (let p = 1; p <= 8; p++) {
    assert.ok(plan.pis[p].members.every(a => present(a, plan.T.descent)), `Piano ${p} completo`);
  }
  assert.ok(topHeightAt(plan, plan.T.descent) > 10);
  assert.equal(baixLoadAt(plan, plan.T.end), 0);
});
