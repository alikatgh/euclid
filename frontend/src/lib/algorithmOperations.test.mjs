import assert from 'node:assert/strict';
import { test } from 'node:test';
import { computeAlgorithmSteps } from '../hooks/useAlgorithm.ts';
import { countAlgorithmOperations } from './algorithmOperations.ts';

test('rejects values outside the supported positive-integer domain before tracing', () => {
  for (const invalid of [0, -1, NaN, Infinity, -Infinity, 1.5, 10000, Number.MAX_SAFE_INTEGER, '4', null, undefined]) {
    assert.throws(() => computeAlgorithmSteps(invalid, 33, false, null), RangeError);
    assert.throws(() => computeAlgorithmSteps(84, invalid, true, null), RangeError);
  }
});

test('counts operations independently of reference animation frames', () => {
  const steps = computeAlgorithmSteps(84, 33, false, null);
  assert.equal(steps.length, 8);
  assert.deepEqual(countAlgorithmOperations(steps), {
    remainderDivisions: 4, zeroTests: 4, orderingTests: 0, exchanges: 0, pairUpdates: 3, returns: 1,
  });
  assert.deepEqual(countAlgorithmOperations(steps, 0), {
    remainderDivisions: 1, zeroTests: 0, orderingTests: 0, exchanges: 0, pairUpdates: 0, returns: 0,
  });
});

test('reversed inputs add one zero-quotient division unless E0 exchanges them', () => {
  const standard = computeAlgorithmSteps(33, 84, false, null);
  const exchanged = computeAlgorithmSteps(33, 84, true, null);
  assert.equal(standard[0].q, 0);
  assert.equal(countAlgorithmOperations(standard).remainderDivisions, 5);
  assert.equal(countAlgorithmOperations(exchanged).remainderDivisions, 4);
  assert.equal(countAlgorithmOperations(exchanged).exchanges, 1);
  assert.equal(countAlgorithmOperations(computeAlgorithmSteps(84, 33, true, null)).exchanges, 0);
});

test('all small inputs preserve the GCD and strictly reduce the positive divisor', () => {
  const gcd = (a, b) => b ? gcd(b, a % b) : a;
  for (let a = 1; a <= 80; a++) for (let b = 1; b <= 80; b++) {
    for (const withE0 of [false, true]) {
      const trace = computeAlgorithmSteps(a, b, withE0, null);
      assert.equal(trace.at(-1).verification.gcd, gcd(a, b));
      for (const frame of trace) if (frame.phase === 'E3') {
        assert.ok(frame.nextN > 0 && frame.nextN < frame.n);
        assert.equal(gcd(frame.nextM, frame.nextN), gcd(a, b));
      }
      const counts = countAlgorithmOperations(trace);
      assert.equal(counts.zeroTests, counts.remainderDivisions);
      assert.equal(counts.pairUpdates, counts.remainderDivisions - 1);
    }
  }
});
