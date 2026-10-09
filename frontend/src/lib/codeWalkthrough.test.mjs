import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { computeAlgorithmSteps } from '../hooks/useAlgorithm.ts';
import { buildCodeProgram, getCodeExecution } from './codeWalkthrough.ts';

const lesson = JSON.parse(readFileSync(new URL('../../../content/lessons.json', import.meta.url), 'utf8'));
const content = lesson.algorithm.codeWalkthrough;
const languages = ['c', 'python'];
const cases = [
  ...lesson.algorithm.presets.map(({ m, n }) => [m, n]),
  [1, 1], [1, 9999], [9999, 1], [9999, 9999], [50, 10], [10, 50],
];

function expectedGcd(m, n) {
  while (n !== 0) [m, n] = [n, m % n];
  return m;
}

function variable(execution, name) {
  return execution.variables.find((entry) => entry.name === name);
}

test('source uses current original inputs and includes E0 only when enabled', () => {
  for (const language of languages) {
    for (const withE0 of [false, true]) {
      const program = buildCodeProgram(content, language, withE0, 35, 64);
      assert.match(program.source, /gcd\(35, 64\)/);
      assert.equal(program.lines.some((line) => line.phase === 'E0'), withE0);
      assert.equal(new Set(program.lines.map((line) => line.id)).size, program.lines.length);
      assert.doesNotMatch(program.source, /\{initial[MN]\}/);
    }
  }
  const cSource = buildCodeProgram(content, 'c', true, 119, 544).source;
  assert.match(cSource, /int temp = m;\s+m = n;\s+n = temp;/);
  assert.match(cSource, /int q = m \/ n;\s+int r = m - q \* n;/);
  assert.match(buildCodeProgram(content, 'python', true, 119, 544).source, /m, n = n, m/);
});

test('standard 119/544 trace keeps the initial zero quotient and final GCD', () => {
  const steps = computeAlgorithmSteps(119, 544, false, lesson);
  assert.equal(steps[0].phase, 'E1');
  assert.equal(steps[0].q, 0);
  assert.equal(steps[0].r, 119);
  assert.equal(steps[0].isDummy, true);
  for (const language of languages) {
    const first = getCodeExecution(steps[0], language, content);
    assert.deepEqual(variable(first, 'q'), { name: 'q', before: null, after: 0 });
    assert.deepEqual(variable(first, 'r'), { name: 'r', before: null, after: 119 });
    const last = getCodeExecution(steps.at(-1), language, content);
    assert.equal(last.result, 17);
    assert.deepEqual(last.activeLineIds, ['e2-condition', 'e2-return']);
    assert.match(last.explanation, /119, 544/);
  }
});

test('E0 swap shows preserved inputs; E0 no-op executes only the condition', () => {
  const swapped = computeAlgorithmSteps(119, 544, true, lesson)[0];
  const unchanged = computeAlgorithmSteps(544, 119, true, lesson)[0];
  for (const language of languages) {
    const exchange = getCodeExecution(swapped, language, content);
    assert.deepEqual(variable(exchange, 'm'), { name: 'm', before: 119, after: 544 });
    assert.deepEqual(variable(exchange, 'n'), { name: 'n', before: 544, after: 119 });
    assert.deepEqual(exchange.activeLineIds, language === 'c'
      ? ['e0-condition', 'e0-temp', 'e0-m', 'e0-n']
      : ['e0-condition', 'e0-swap']);
    assert.deepEqual(variable(exchange, 'temp'), language === 'c'
      ? { name: 'temp', before: null, after: 119 }
      : undefined);
    const keep = getCodeExecution(unchanged, language, content);
    assert.deepEqual(keep.activeLineIds, ['e0-condition']);
    assert.equal(variable(keep, 'temp'), undefined);
    assert.equal(variable(keep, 'm').before, variable(keep, 'm').after);
    assert.equal(variable(keep, 'n').before, variable(keep, 'n').after);
  }
});

test('E1 respects C block scope and Python values from the previous iteration', () => {
  const steps = computeAlgorithmSteps(119, 544, false, lesson);
  const secondDivision = steps.find((step) => step.phase === 'E1' && step.pass === 2);
  const c = getCodeExecution(secondDivision, 'c', content);
  const python = getCodeExecution(secondDivision, 'python', content);
  assert.deepEqual(c.activeLineIds, ['e1-q', 'e1-r']);
  assert.deepEqual(python.activeLineIds, ['e1-divmod']);
  assert.deepEqual(variable(c, 'q'), { name: 'q', before: null, after: 4 });
  assert.deepEqual(variable(c, 'r'), { name: 'r', before: null, after: 68 });
  assert.deepEqual(variable(python, 'q'), { name: 'q', before: 0, after: 4 });
  assert.deepEqual(variable(python, 'r'), { name: 'r', before: 119, after: 68 });
});

test('E3 includes failed E2 condition and reduction but never the return', () => {
  const steps = computeAlgorithmSteps(119, 544, false, lesson);
  for (const step of steps.filter((entry) => entry.phase === 'E3')) {
    for (const language of languages) {
      const execution = getCodeExecution(step, language, content);
      assert.deepEqual(execution.activeLineIds, language === 'c'
        ? ['e2-condition', 'e3-m', 'e3-n']
        : ['e2-condition', 'e3-pair']);
      assert.match(execution.explanation, /false/);
      assert.match(execution.explanation, /timeline/);
      assert.deepEqual(variable(execution, 'm'), { name: 'm', before: step.m, after: step.n });
      assert.deepEqual(variable(execution, 'n'), { name: 'n', before: step.n, after: step.r });
      assert.equal(execution.result, null);
    }
  }
});

test('all presets and boundaries map every step to source lines with conserved GCD', () => {
  for (const [m, n] of cases) {
    for (const withE0 of [false, true]) {
      const steps = computeAlgorithmSteps(m, n, withE0, lesson);
      for (const language of languages) {
        const { lines } = buildCodeProgram(content, language, withE0, m, n);
        const lineIds = new Set(lines.map((line) => line.id));
        for (const step of steps) {
          const execution = getCodeExecution(step, language, content);
          assert.ok(execution.activeLineIds.length > 0);
          assert.ok(execution.activeLineIds.every((id) => lineIds.has(id)));
          assert.doesNotMatch(execution.title + execution.explanation, /\{[A-Za-z]+\}/);
          assert.equal(expectedGcd(variable(execution, 'm').after, variable(execution, 'n').after), expectedGcd(m, n));
        }
        assert.equal(getCodeExecution(steps.at(-1), language, content).result, expectedGcd(m, n));
      }
    }
  }
});

test('complete Python programs print the GCD for presets and boundaries', () => {
  for (const [m, n] of cases) {
    for (const withE0 of [false, true]) {
      const program = buildCodeProgram(content, 'python', withE0, m, n);
      const result = spawnSync('python3', ['-c', program.source], { encoding: 'utf8' });
      assert.equal(result.status, 0, result.stderr);
      assert.equal(result.stdout.trim(), String(expectedGcd(m, n)));
    }
  }
});

test('complete C programs compile cleanly in standard and E0 modes', () => {
  for (const withE0 of [false, true]) {
    const program = buildCodeProgram(content, 'c', withE0, 119, 544);
    const result = spawnSync('cc', ['-x', 'c', '-fsyntax-only', '-Wall', '-Wextra', '-Werror', '-'], {
      input: program.source, encoding: 'utf8',
    });
    assert.equal(result.status, 0, result.stderr);
  }
});

test('complete C programs run for presets and boundaries', { skip: !process.env.CODE_WALKTHROUGH_SCRATCH }, () => {
  const executable = join(process.env.CODE_WALKTHROUGH_SCRATCH, 'gcd-check.o');
  for (const [m, n] of cases) {
    for (const withE0 of [false, true]) {
      const program = buildCodeProgram(content, 'c', withE0, m, n);
      const compilation = spawnSync('cc', ['-x', 'c', '-Wall', '-Wextra', '-Werror', '-', '-o', executable], {
        input: program.source, encoding: 'utf8',
      });
      assert.equal(compilation.status, 0, compilation.stderr);
      const result = spawnSync(executable, [], { encoding: 'utf8' });
      assert.equal(result.status, 0, result.stderr);
      assert.equal(result.stdout.trim(), String(expectedGcd(m, n)));
    }
  }
});
