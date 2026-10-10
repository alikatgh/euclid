import test from 'node:test';
import assert from 'node:assert/strict';
import katex from 'katex';
import { coreLessons } from '../lesson-core/registry.ts';
import { algorithmE } from '../lessons/001-algorithm-e.ts';
import { validateLessonSpec, validateRegistry } from '../lesson-core/contract.ts';
import { KATEX_OPTIONS, prepareTex } from '../lesson-core/tex.ts';

test('Core lesson registry contains unique IDs and orders', () => {
  const errors = validateRegistry(coreLessons);
  assert.deepEqual(errors, [], `Registry errors: ${errors.join(', ')}`);
});

test('Every registered lesson in coreLessons satisfies the full LessonSpec contract', () => {
  for (const lesson of coreLessons) {
    const errors = validateLessonSpec(lesson, {
      renderTex: (expr) => {
        katex.renderToString(prepareTex(expr), KATEX_OPTIONS);
      },
      fuzzRuns: 40,
    });
    assert.deepEqual(errors, [], `Lesson "${lesson.id}" validation errors:\n${errors.join('\n')}`);
  }
});

test('Algorithm E parity: computes exact steps for classic TAOCP 119 & 544 without E0', () => {
  const steps = algorithmE.run({ m: 119, n: 544 }, 'standard');
  assert.equal(steps.length, 10, 'Standard 119/544 run produces 10 steps (5 divisions + reductions)');

  // Step 0: Dummy division E1
  assert.equal(steps[0].phase, 'E1');
  assert.equal(steps[0].values.m, 119);
  assert.equal(steps[0].values.n, 544);
  assert.equal(steps[0].values.q, 0);
  assert.equal(steps[0].values.r, 119);
  assert.equal(steps[0].isDummy, true);

  // Step 1: E3 swap
  assert.equal(steps[1].phase, 'E3');
  assert.equal(steps[1].next?.m, 544);
  assert.equal(steps[1].next?.n, 119);

  // Terminal step
  const last = steps[steps.length - 1];
  assert.equal(last.phase, 'E2');
  assert.equal(last.terminal, true);
  assert.equal(last.values.r, 0);
  assert.equal(last.values.n, 17); // GCD is 17!
});

test('Algorithm E parity: optimized variant with E0 avoids initial dummy division', () => {
  const steps = algorithmE.run({ m: 119, n: 544 }, 'with-e0');
  assert.equal(steps[0].phase, 'E0');
  assert.equal(steps[0].e0Type, 'E0_SWAP');
  assert.equal(steps[0].next?.m, 544);
  assert.equal(steps[0].next?.n, 119);

  // First division is now 544 / 119 = 4 remainder 68
  assert.equal(steps[1].phase, 'E1');
  assert.equal(steps[1].values.m, 544);
  assert.equal(steps[1].values.n, 119);
  assert.equal(steps[1].values.q, 4);
  assert.equal(steps[1].values.r, 68);
  assert.equal(steps[1].isDummy, false);
});
