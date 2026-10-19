import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_COMPOSITION, HEADS } from '../src/app/scene/athlete/catalog.js';
import { getSessionComposition, setSessionComposition } from '../src/app/scene/athlete/session.js';

test('avvio con manichino originale, scelta applicabile nella sessione e reset al nuovo avvio',async()=>{
  assert.deepEqual(getSessionComposition(),{bodyId:'mannequin',headId:'mannequin-original'});
  const choice={bodyId:'mannequin',headId:'mannequin-detailed-small'};
  assert.equal(HEADS.find(item=>item.id===choice.headId).label,'Realistic girl');
  setSessionComposition(choice);
  assert.deepEqual(getSessionComposition(),choice);
  const returned=getSessionComposition();returned.headId='invalid';
  assert.deepEqual(getSessionComposition(),choice);
  const fresh=await import('../src/app/scene/athlete/session.js?fresh-start');
  assert.deepEqual(fresh.getSessionComposition(),DEFAULT_COMPOSITION);
  setSessionComposition(DEFAULT_COMPOSITION);
});
