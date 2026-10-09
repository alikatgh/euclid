import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import katex from 'katex';
import { computeAlgorithmSteps } from '../hooks/useAlgorithm.ts';
import { getReadingIntro, getStepReading, getWorkedExample } from './mathematicalReading.ts';

const lesson = JSON.parse(readFileSync(new URL('../../../content/lessons.json', import.meta.url), 'utf8'));
const content = lesson.algorithm.mathematicalReading;
const cases = [
  ...lesson.algorithm.presets.map(({ m, n }) => [m, n]),
  [1, 1], [1, 9999], [9999, 1], [9999, 9999], [50, 10], [10, 50],
  [17, 17], [97, 37], [9999, 9973], [2, 9999],
];

function expectedGcd(m, n) {
  while (n !== 0) [m, n] = [n, m % n];
  return m;
}

function assertReadableMath(text) {
  assert.doesNotMatch(text, /\{[A-Za-z][A-Za-z0-9]*\}/, 'unresolved prose placeholder');
  assert.doesNotMatch(text, /\b(?:rod|rods|stick|sticks|ruler|rulers)\b/i);
  const expressions = [...text.matchAll(/\$([^$]+)\$/g)];
  assert.equal(expressions.length * 2, [...text.matchAll(/\$/g)].length, 'unpaired math delimiter');
  for (const [, expression] of expressions) {
    const html = katex.renderToString(expression, {
      throwOnError: true, trust: false, output: 'htmlAndMathml',
    });
    assert.match(html, /<math\b/, 'accessible MathML accompanies the expression');
  }
}

test('all presets, custom inputs and boundaries produce valid, fully substituted mathematical prose', () => {
  for (const [m, n] of cases) {
    for (const withE0 of [false, true]) {
      const steps = computeAlgorithmSteps(m, n, withE0, lesson);
      assertReadableMath(getReadingIntro(m, n, withE0, content));
      for (const step of steps) assertReadableMath(getStepReading(step, content));
      for (const paragraph of getWorkedExample(steps, content)) {
        assertReadableMath(paragraph.text);
        for (const chunk of paragraph.chunks) assertReadableMath(chunk.text);
      }
      const terminal = getStepReading(steps.at(-1), content);
      assert.ok(terminal.includes(`\\gcd(${m},${n})=${expectedGcd(m, n)}`));
    }
  }
  for (const text of Object.values(content.principles)) assertReadableMath(text);
});

test('each E1 calculation uses the actual quotient, remainder and the appropriate fraction form', () => {
  for (const [m, n] of cases) {
    for (const withE0 of [false, true]) {
      const steps = computeAlgorithmSteps(m, n, withE0, lesson);
      for (const step of steps.filter(({ phase }) => phase === 'E1')) {
        const text = getStepReading(step, content);
        assert.equal(step.m, step.q * step.n + step.r);
        assert.ok(step.r >= 0 && step.r < step.n);
        assert.ok(text.includes(`r\\leftarrow ${step.r}`));
        assert.match(text, /Next, E2 tests/);
        assert.doesNotMatch(text, /algorithm terminates|Hence.*\\gcd/);
        if (step.r === 0) {
          assert.ok(text.includes(`\\frac{${step.m}}{${step.n}}=${step.q}`));
          assert.doesNotMatch(text, /\\frac\{0\}/);
        } else if (step.q === 0) {
          assert.ok(text.includes(`\\frac{${step.m}}{${step.n}}<1`));
          assert.doesNotMatch(text, /=0\\frac/);
        } else {
          assert.ok(text.includes(`\\frac{${step.m}}{${step.n}}=${step.q}\\frac{${step.r}}{${step.n}}`));
        }
      }
    }
  }
});

test('standard 119/544 example narrates all five divisions, including the zero quotient', () => {
  const steps = computeAlgorithmSteps(119, 544, false, lesson);
  const paragraphs = getWorkedExample(steps, content);
  assert.equal(paragraphs.length, 5);
  const divisions = [[119, 544, 0, 119], [544, 119, 4, 68], [119, 68, 1, 51], [68, 51, 1, 17], [51, 17, 3, 0]];
  for (const [index, [m, n, q, r]] of divisions.entries()) {
    const step = steps[index * 2];
    assert.deepEqual([step.m, step.n, step.q, step.r], [m, n, q, r]);
    assert.ok(paragraphs[index].text.includes(`\\frac{${m}}{${n}}`));
    assert.ok(paragraphs[index].text.includes(`r\\leftarrow ${r}`));
  }
  assert.match(paragraphs[0].text, /optional E0/);
  assert.match(paragraphs[0].text, /skips precisely this initial division/);
  assert.doesNotMatch(getStepReading(steps[0], content), /optional E0/);
  assert.ok(paragraphs.at(-1).text.includes('\\gcd(119,544)=17'));
  assert.ok(paragraphs.at(-1).text.includes('119=7\\cdot 17'));
  assert.ok(paragraphs.at(-1).text.includes('544=32\\cdot 17'));
});

test('worked paragraphs cover each trace step exactly once and pair each E1 with its E3 or E2', () => {
  for (const [m, n] of cases) {
    for (const withE0 of [false, true]) {
      const steps = computeAlgorithmSteps(m, n, withE0, lesson);
      const paragraphs = getWorkedExample(steps, content);
      assert.equal(new Set(paragraphs.map(({ id }) => id)).size, paragraphs.length);
      assert.deepEqual(
        paragraphs.flatMap(({ startStep, endStep }) => Array.from({ length: endStep - startStep + 1 }, (_, offset) => startStep + offset)),
        steps.map(({ stepIndex }) => stepIndex),
      );
      assert.equal(paragraphs.length, steps.filter(({ phase }) => phase === 'E1' || phase === 'E0').length);
      for (const paragraph of paragraphs) {
        const first = steps[paragraph.startStep];
        const last = steps[paragraph.endStep];
        if (first.phase === 'E0') {
          assert.equal(first, last);
        } else {
          assert.equal(first.phase, 'E1');
          assert.equal(last.pass, first.pass);
          assert.equal(last.phase, first.r === 0 ? 'E2' : 'E3');
        }
      }
    }
  }
});

test('each executing step owns exactly one precise chunk and conceptual E0 asides own none', () => {
  for (const [m, n] of cases) {
    for (const withE0 of [false, true]) {
      const steps = computeAlgorithmSteps(m, n, withE0, lesson);
      const paragraphs = getWorkedExample(steps, content);
      const chunks = paragraphs.flatMap(({ chunks }) => chunks);
      assert.equal(new Set(chunks.map(({ id }) => id)).size, chunks.length, 'stable chunk identities are unique in the reading');
      assert.deepEqual(
        chunks.filter(({ stepIndex }) => stepIndex !== undefined).map(({ stepIndex }) => stepIndex),
        steps.map(({ stepIndex }) => stepIndex),
        'each executing step appears once in reading order',
      );
      for (const paragraph of paragraphs) {
        assert.equal(paragraph.text, paragraph.chunks.map(({ text }) => text).join(' '), 'complete prose includes every passage and aside');
      }
      for (const step of steps) {
        const active = chunks.filter(({ stepIndex }) => stepIndex === step.stepIndex);
        assert.equal(active.length, 1, `${m}/${n}, E0=${withE0}, step=${step.stepIndex} has one active passage`);
        const chunk = active[0];
        assert.equal(chunk.phase, step.phase);
        if (step.phase === 'E1') {
          assert.ok(chunk.text.includes(`r\\leftarrow ${step.r}`));
          assert.doesNotMatch(chunk.text, /E3 sets|At E2|algorithm terminates|optional E0/);
          assert.ok(!chunk.text.includes('m\\leftarrow'), 'division does not highlight the next assignment');
        } else if (step.phase === 'E3') {
          assert.ok(chunk.text.includes(`m\\leftarrow ${step.n}`));
          assert.ok(chunk.text.includes(`n\\leftarrow ${step.r}`));
          assert.ok(chunk.text.includes(`r=${step.r}\\ne 0`));
          assert.doesNotMatch(chunk.text, /The division|Dividing|optional E0/);
        } else if (step.phase === 'E2') {
          assert.match(chunk.text, /At E2 the remainder is zero/);
          assert.ok(chunk.text.includes(`\\gcd(${m},${n})=${expectedGcd(m, n)}`));
          assert.doesNotMatch(chunk.text, /The division|Dividing|E3 sets/);
        } else {
          assert.equal(chunk.text, getStepReading(step, content));
        }
      }
      const asides = chunks.filter(({ stepIndex }) => stepIndex === undefined);
      assert.equal(asides.length, !withE0 && m < n ? 1 : 0);
      for (const aside of asides) {
        assert.equal(aside.phase, undefined);
        assert.match(aside.text, /optional E0/);
      }
    }
  }
});

test('E0 swaps only ascending input pairs; ordered and equal pairs retain their values', () => {
  for (const [m, n] of [[119, 544], [544, 119], [17, 17]]) {
    const steps = computeAlgorithmSteps(m, n, true, lesson);
    const intro = getReadingIntro(m, n, true, content);
    const first = getStepReading(steps[0], content);
    if (m < n) {
      assert.match(intro, /avoiding the initial division with quotient zero/);
      assert.ok(first.includes(`m\\leftarrow ${n}`));
      assert.ok(first.includes(`n\\leftarrow ${m}`));
    } else {
      assert.match(intro, /leave the inputs unchanged/);
      assert.match(first, /condition \$m<n\$ is false/);
      assert.doesNotMatch(intro + first, /avoiding|skips|exchange the inputs/);
    }
    assert.equal(steps[1].q > 0, true);
    assert.doesNotMatch(getWorkedExample(steps, content).map(({ text }) => text).join(' '), /skips precisely this initial division/);
  }
});

test('the nonzero E2 test is explained in E3, followed by the actual assignments', () => {
  const steps = computeAlgorithmSteps(119, 544, false, lesson);
  assert.equal(steps.filter(({ phase }) => phase === 'E2').length, 1);
  for (const step of steps.filter(({ phase }) => phase === 'E3')) {
    const text = getStepReading(step, content);
    assert.match(text, /At E2 the test \$r=0\$ is false/);
    assert.ok(text.includes(`r=${step.r}\\ne 0`));
    assert.ok(text.includes(`m\\leftarrow ${step.n}`));
    assert.ok(text.includes(`n\\leftarrow ${step.r}`));
    assert.equal(expectedGcd(step.n, step.r), 17);
  }
});

test('equal inputs use exact quotient one and coprime inputs terminate with original-input GCD one', () => {
  for (const withE0 of [false, true]) {
    const equal = computeAlgorithmSteps(17, 17, withE0, lesson);
    const firstDivision = equal.find(({ phase }) => phase === 'E1');
    assert.deepEqual([firstDivision.q, firstDivision.r], [1, 0]);
    assert.ok(getStepReading(firstDivision, content).includes('\\frac{17}{17}=1'));
    assert.doesNotMatch(getStepReading(firstDivision, content), /\\frac\{0\}/);
    const coprime = computeAlgorithmSteps(35, 64, withE0, lesson);
    assert.ok(getStepReading(coprime.at(-1), content).includes('\\gcd(35,64)=1'));
    assert.ok(getWorkedExample(coprime, content).at(-1).text.includes('35=35\\cdot 1'));
  }
});

test('principles establish common divisors in both directions and strictly decreasing positive divisors', () => {
  assert.match(content.principles.invariant, /divides both \$m\$ and \$n\$/);
  assert.match(content.principles.invariant, /Conversely, if \$d\$ divides both \$n\$ and \$r\$/);
  assert.match(content.principles.invariant, /exactly the same common divisors/);
  assert.ok(content.principles.termination.includes('0\\le r<n'));
  assert.match(content.principles.termination, /positive values of \$n\$ strictly decrease/);
  assert.ok(content.principles.termination.includes('\\gcd(m,n)=\\gcd(n,0)=n'));
});
