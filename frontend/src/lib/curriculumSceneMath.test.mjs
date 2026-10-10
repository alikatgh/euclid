import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accumulationValues, axisPosition, axisTicks, canDrawIndividualUnits, contributionTotal, divisionSegments, formatSceneNumber, visibleSceneIndices } from './curriculumSceneMath.ts';

test('division pictures conserve the exact target, including dummy and grouped passes', () => {
  for (const m of [0, 1, 17, 68, 119, 999]) for (const n of [1, 3, 17, 68, 1000]) {
    const model = divisionSegments(m, n);
    assert.equal(model.groups.reduce((sum, group) => sum + group.length, 0) + model.remainder, m);
    assert.equal(model.quotient * n + model.remainder, m);
    assert.ok(model.remainder >= 0 && model.remainder < n);
    assert.ok(model.groups.length <= 12);
    for (const group of model.groups) assert.equal(group.length, group.copies * n);
    assert.equal(model.scaleMaximum, Math.max(m, n));
  }
  assert.throws(() => divisionSegments(4, 0), RangeError);
});

test('compression marks every gap and retains focused item and domain boundaries', () => {
  for (let count = 0; count <= 100; count++) for (const focus of [-1, 0, Math.floor(count / 2), count - 1]) {
    const shown = visibleSceneIndices(count, focus);
    const numbers = shown.filter((index) => index !== null);
    assert.equal(new Set(numbers).size, numbers.length);
    assert.ok(numbers.length <= 12);
    if (count) {
      assert.equal(numbers[0], 0);
      assert.equal(numbers.at(-1), count - 1);
      if (focus >= 0 && focus < count) assert.ok(numbers.includes(focus));
    }
    for (let index = 1; index < shown.length; index++) {
      if (shown[index] !== null && shown[index - 1] !== null) assert.equal(shown[index], shown[index - 1] + 1);
    }
  }
});

test('linear axes preserve signed distances and logarithmic axes preserve ratios', () => {
  assert.equal(axisPosition(0, -10, 10), 0.5);
  assert.equal(axisPosition(5, -10, 10), 0.75);
  assert.equal(axisPosition(4, 1, 16, true), 0.5);
  assert.ok(Math.abs(axisPosition(8, 1, 32, true) - 0.6) < 1e-14);
  assert.throws(() => axisPosition(0, 0, 32, true), RangeError);
  for (const [min, max] of [[-100, 100], [0, 6], [1 / 3 - 0.0001, 1 / 3 + 0.0001], [0, 0.01]]) {
    const ticks = axisTicks(min, max);
    assert.equal(ticks[0], min); assert.equal(ticks.at(-1), max);
    assert.ok(ticks.every((tick, index) => tick >= min && tick <= max && (!index || tick > ticks[index - 1])));
  }
});

test('sum and product paths use their correct identity and signed contributions', () => {
  assert.deepEqual(accumulationValues([3, -2, 4, 0], 'sum'), [3, 1, 5, 5]);
  assert.deepEqual(accumulationValues([3, -2, 4, 0], 'product'), [3, -6, -24, 0]);
  assert.equal(contributionTotal([{ value: 119, coefficient: -1 }, { value: 68, coefficient: 2 }]), 17);
  assert.equal(contributionTotal([]), 0);
});

test('unit glyphs never round fractions into whole objects; abbreviated values disclose rounding', () => {
  assert.equal(canDrawIndividualUnits(0), true);
  assert.equal(canDrawIndividualUnits(64), true);
  for (const value of [-1, 0.5, 65, Infinity, NaN]) assert.equal(canDrawIndividualUnits(value), false);
  assert.equal(formatSceneNumber(17), '17');
  assert.equal(formatSceneNumber(-0), '0');
  assert.match(formatSceneNumber(1 / 3), /^≈/);
});

test('balance preserves authored exact fractions without hiding genuine rounding differences', async () => {
  const { compareContributions, exactContributionLabel } = await import('./curriculumSceneMath.ts');
  const thirds = compareContributions([{ exactValue: '333/1000', value: .333 }, { exactValue: '1/3000', value: 1 / 3000 }], [{ exactValue: '1/3', value: 1 / 3 }]);
  assert.deepEqual(thirds, { equal: true, leftLabel: '1/3', rightLabel: '1/3' });
  assert.equal(compareContributions([{ label: 'rounded', value: .333 }], [{ exactValue: '1/3', value: 1 / 3 }]).equal, false);
  assert.equal(compareContributions([{ value: .1 }, { value: .2 }], [{ value: .3 }]).equal, true);
  assert.throws(() => compareContributions([{ exactValue: '1/3', value: .333 }], [{ exactValue: '1/3', value: 1 / 3 }]), RangeError, 'an exact annotation cannot change the plotted quantity');
  assert.equal(compareContributions([{ label: '1/3', value: .333 }], [{ exactValue: '1/3', value: 1 / 3 }]).equal, false, 'prose labels never define arithmetic');
  assert.equal(exactContributionLabel({ exactValue: '1/3', value: 1 / 3, coefficient: -3 }), '-1');
  assert.equal(compareContributions([{ value: 26, coefficient: -4 }, { value: 15, coefficient: 7 }], [{ value: 1 }]).equal, true);
});
