import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { schedulePlayback } from './playback.ts';

test('paused, hidden, and terminal lessons schedule no timer', () => {
  const clock = { setTimeout() { assert.fail('A timer must not run.'); }, clearTimeout() {} };
  const base = { active: true, playing: true, index: 1, frameCount: 5, delay: 3200 };
  for (const change of [{ active: false }, { playing: false }, { index: 4 }, { frameCount: 1 }]) {
    assert.equal(schedulePlayback({ ...base, ...change }, () => assert.fail(), clock), undefined);
  }
});

test('opening the course map cancels playback; closing it leaves the current index untouched', () => {
  let index = 2, playing = true, active = true;
  const pending = new Map(); let nextId = 0;
  const clock = { setTimeout(fn) { const id = ++nextId; pending.set(id, fn); return id; }, clearTimeout(id) { pending.delete(id); } };
  let cleanup = schedulePlayback({ active, playing, index, frameCount: 6, delay: 100 }, () => index++, clock);
  assert.equal(pending.size, 1);
  // React runs the old effect cleanup, then the new hidden/paused effect.
  active = false; cleanup(); playing = false;
  cleanup = schedulePlayback({ active, playing, index, frameCount: 6, delay: 100 }, () => index++, clock);
  assert.equal(pending.size, 0); assert.equal(index, 2);
  active = true;
  cleanup = schedulePlayback({ active, playing, index, frameCount: 6, delay: 100 }, () => index++, clock);
  assert.equal(cleanup, undefined); assert.equal(index, 2); assert.equal(pending.size, 0);
});

test('course map visibility retains the same keyed runtime instead of a conditional mount', () => {
  const app = readFileSync(new URL('../App.tsx', import.meta.url), 'utf8');
  assert.match(app, /className="curriculum-content" key=\{selected\} hidden=\{catalogOpen\}/);
  assert.doesNotMatch(app, /catalogOpen\s*\?\s*</);
  assert.match(app, /CurriculumPlayer lesson=\{lesson\} active=\{!catalogOpen\}/);
  assert.match(app, /ReferenceLesson active=\{!catalogOpen\}/);
});
