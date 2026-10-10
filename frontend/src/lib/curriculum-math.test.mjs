import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import katex from 'katex';
import { buildLessonFrames, curriculumLessons, defaultInputs } from './curriculum.ts';
import { compareContributions } from './curriculumSceneMath.ts';

// Independent numeric checks, separate from the registry and renderer tests.
function samples(lesson) {
  const defaults = defaultInputs(lesson);
  const candidates = [defaults];
  let corners = [{}];
  for (const parameter of lesson.parameters) {
    const { id, min, max, initial, step = 1 } = parameter;
    const middle = min + Math.floor((max - min) / step / 2) * step;
    for (const value of new Set([min, max, initial, middle, Math.min(max, min + step), Math.max(min, max - step)])) {
      candidates.push({ ...defaults, [id]: value });
    }
    corners = corners.flatMap((corner) => [...new Set([min, max])].map((value) => ({ ...corner, [id]: value })));
  }
  candidates.push(...corners);
  const domainSize = lesson.parameters.reduce((size, parameter) => size *
    (Math.round((parameter.max - parameter.min) / (parameter.step ?? 1)) + 1), 1);
  if (domainSize <= 256) {
    let exhaustive = [{}];
    for (const { id, min, max, step = 1 } of lesson.parameters) {
      const values = Array.from({ length: Math.round((max - min) / step) + 1 }, (_, i) => min + i * step);
      exhaustive = exhaustive.flatMap((inputs) => values.map((value) => ({ ...inputs, [id]: value })));
    }
    candidates.push(...exhaustive);
  }
  return [...new Map(candidates.map((inputs) => [JSON.stringify(inputs), inputs])).values()];
}

function close(actual, expected, context) {
  assert.ok(Number.isFinite(actual), `${context}: expected a finite quantity, got ${actual}`);
  assert.ok(Math.abs(actual - expected) <= 1e-10 * Math.max(1, Math.abs(expected)),
    `${context}: ${actual} does not equal ${expected}`);
}

function inspectScene(scene, context) {
  const finite = (value) => assert.ok(Number.isFinite(value), `${context}: nonfinite numeric value ${value}`);
  const index = (value, count) => assert.ok(Number.isInteger(value) && value >= 0 && value < count,
    `${context}: index ${value} is outside 0…${count - 1}`);
  switch (scene.kind) {
    case 'division':
      [scene.m, scene.n, scene.q, scene.r].forEach(finite);
      assert.ok(Number.isSafeInteger(scene.m) && scene.m >= 0, context);
      assert.ok(Number.isSafeInteger(scene.n) && scene.n > 0, context);
      assert.equal(scene.q, Math.floor(scene.m / scene.n), context);
      assert.equal(scene.r, scene.m % scene.n, context);
      assert.equal(scene.q * scene.n + scene.r, scene.m, context);
      break;
    case 'registers': {
      const ids = new Set(scene.registers.map((entry) => entry.symbol));
      assert.equal(ids.size, scene.registers.length, `${context}: duplicate register`);
      for (const arrow of scene.arrows) {
        assert.ok(ids.has(arrow.from), `${context}: missing source register ${arrow.from}`);
        assert.ok(ids.has(arrow.to), `${context}: missing target register ${arrow.to}`);
      }
      break;
    }
    case 'grid': {
      assert.ok(Number.isInteger(scene.rows) && scene.rows >= 0, context);
      assert.ok(Number.isInteger(scene.columns) && scene.columns >= 0, context);
      const occupied = new Set();
      for (const cell of scene.cells ?? []) {
        index(cell.row, scene.rows); index(cell.column, scene.columns);
        const location = `${cell.row},${cell.column}`;
        assert.ok(!occupied.has(location), `${context}: duplicate cell ${location}`);
        occupied.add(location);
        if (cell.value !== undefined) finite(cell.value);
      }
      if (scene.rowLabels) assert.equal(scene.rowLabels.length, scene.rows, context);
      if (scene.columnLabels) assert.equal(scene.columnLabels.length, scene.columns, context);
      break;
    }
    case 'number-line':
      finite(scene.min); finite(scene.max);
      assert.ok(scene.min < scene.max, `${context}: empty axis domain`);
      if (scene.logarithmic) assert.ok(scene.min > 0, `${context}: logarithmic axis includes zero`);
      for (const value of [...scene.points.map((point) => point.value), ...(scene.jumps ?? []).flatMap((jump) => [jump.from, jump.to])]) {
        finite(value);
        assert.ok(value >= scene.min - 1e-12 && value <= scene.max + 1e-12,
          `${context}: quantity ${value} falls outside [${scene.min}, ${scene.max}]`);
        if (scene.logarithmic) assert.ok(value > 0, `${context}: nonpositive logarithmic point`);
      }
      break;
    case 'staircase':
      assert.ok(Number.isInteger(scene.count) && scene.count >= 0, context);
      if (scene.active !== -1) index(scene.active, scene.count);
      if (scene.labels) assert.equal(scene.labels.length, scene.count, context);
      break;
    case 'graph': {
      const ids = new Set(scene.nodes.map((node) => node.id));
      assert.equal(ids.size, scene.nodes.length, `${context}: duplicate graph node`);
      for (const node of scene.nodes) {
        assert.ok(node.x >= 0 && node.x <= 1 && node.y >= 0 && node.y <= 1, `${context}: invalid normalized node coordinates`);
        if (node.value !== undefined) finite(node.value);
      }
      for (const edge of scene.edges) {
        assert.ok(ids.has(edge.from) && ids.has(edge.to), `${context}: dangling graph edge`);
      }
      break;
    }
    case 'balance':
      for (const term of [...scene.left, ...scene.right]) {
        finite(term.value); finite(term.coefficient ?? 1); finite(term.value * (term.coefficient ?? 1));
      }
      break;
    case 'growth':
      finite(scene.base); finite(scene.exponent);
      assert.ok(scene.base > 0, `${context}: real exponential base must be positive`);
      scene.stages.forEach((stage) => finite(stage.value));
      break;
    case 'accumulation': {
      scene.terms.forEach(finite);
      if (scene.active !== -1) index(scene.active, scene.terms.length);
      const prefix = scene.terms.slice(0, scene.active + 1);
      const total = prefix.reduce((accumulator, term) => scene.operation === 'sum' ? accumulator + term : accumulator * term,
        scene.operation === 'sum' ? 0 : 1);
      close(scene.total, total, `${context}: accumulated total`);
      break;
    }
    default: assert.fail(`${context}: unknown scene ${scene.kind}`);
  }
}

for (const lesson of curriculumLessons) {
  test(`lesson ${lesson.order}: scene quantities, notation, and predictions hold at input boundaries`, () => {
    for (const inputs of samples(lesson)) {
      const frames = buildLessonFrames(lesson, inputs);
      for (const frame of frames) {
        const context = `${lesson.id} ${JSON.stringify(inputs)} ${frame.id}`;
        inspectScene(frame.scene, context);
        if (frame.scene.kind === 'balance') {
          let expectedEqual = true;
          if (lesson.order === 16 && frame.id === 'compare-routes') {
            const scale = 10 ** inputs.digits;
            const roundedUnits = Math.floor((2 * inputs.whole * scale + inputs.pieces) / (2 * inputs.pieces));
            expectedEqual = inputs.pieces * roundedUnits === inputs.whole * scale;
          }
          assert.equal(compareContributions(frame.scene.left, frame.scene.right).equal, expectedEqual,
            `${context}: rendered equality must match the exact mathematical relation`);
        }
        for (const entry of frame.variables) {
          if (typeof entry.value === 'number') assert.ok(Number.isFinite(entry.value), context);
          if (typeof entry.previous === 'number') assert.ok(Number.isFinite(entry.previous), context);
        }
        for (const counter of frame.counters ?? []) {
          assert.ok(Number.isSafeInteger(counter.value) && counter.value >= 0, `${context}: noninteger operation count`);
        }
        assert.doesNotMatch([frame.intuition, frame.formal, frame.formula, frame.reading].join('\n'), /\bNaN\b/, context);
        assert.doesNotMatch(frame.formula, /\bundefined\b/, context);
        assert.doesNotThrow(() => katex.renderToString(frame.formula, { throwOnError: true, strict: 'error', trust: false }), context);
        const inlineTexts = [frame.intuition, frame.formal, frame.reading,
          ...(frame.prediction ? [frame.prediction.prompt, ...frame.prediction.choices, frame.prediction.explanation, frame.prediction.hint ?? ''] : [])];
        for (const text of inlineTexts) {
          assert.equal((text.match(/(?<!\\)\$/g) ?? []).length % 2, 0, `${context}: unpaired inline-math delimiter`);
          for (const match of text.matchAll(/\$([^$]+)\$/g)) {
            assert.doesNotThrow(() => katex.renderToString(match[1], { throwOnError: true, strict: 'error', trust: false }), context);
          }
        }
        if (frame.prediction) {
          const { choices, correctIndex, explanation } = frame.prediction;
          assert.ok(choices.length >= 2 && choices.every((choice) => typeof choice === 'string' && choice.trim()), context);
          assert.equal(new Set(choices.map((choice) => choice.trim())).size, choices.length, `${context}: indistinguishable prediction choices`);
          assert.ok(choices[correctIndex], context);
          assert.ok(explanation.trim(), context);
        }
      }
    }
  });
}

test('all distinct displayed Python programs execute for default and boundary inputs', () => {
  const programs = new Map();
  for (const lesson of curriculumLessons) {
    for (const inputs of samples(lesson)) {
      for (const frame of buildLessonFrames(lesson, inputs)) {
        if (frame.code.language === 'python') {
          const source = frame.code.lines.join('\n');
          if (!programs.has(source)) programs.set(source, { source, context: `${lesson.id} ${JSON.stringify(inputs)} ${frame.id}` });
        }
      }
    }
  }
  assert.ok(programs.size > 0);
  const runner = [
    'import contextlib, io, json, sys, traceback',
    'failures = []',
    'for program in json.load(sys.stdin):',
    '    try:',
    '        with contextlib.redirect_stdout(io.StringIO()):',
    '            exec(compile(program["source"], program["context"], "exec"), {"__name__": "__main__"})',
    '    except Exception:',
    '        failures.append({"context": program["context"], "error": traceback.format_exc()})',
    'print(json.dumps(failures))',
  ].join('\n');
  const result = spawnSync('python3', ['-c', runner], {
    input: JSON.stringify([...programs.values()]), encoding: 'utf8', timeout: 30000, maxBuffer: 8 * 1024 * 1024,
  });
  assert.equal(result.status, 0, result.stderr || String(result.error));
  assert.deepEqual(JSON.parse(result.stdout), []);
});

const lessonByOrder = (order) => {
  const lesson = curriculumLessons.find((entry) => entry.order === order);
  assert.ok(lesson, `Missing lesson ${order}`);
  return lesson;
};
const variablesOf = (frame) => Object.fromEntries(frame.variables.map(({ symbol, value }) => [symbol, value]));
const exactGcd = (a, b) => {
  while (b) [a, b] = [b, a % b];
  return a;
};

test('backward and forward Bézout preserve every identity for every selectable input pair', () => {
  for (const order of [9, 10]) {
    const lesson = lessonByOrder(order);
    const mParameter = lesson.parameters.find((entry) => entry.id === 'm');
    const nParameter = lesson.parameters.find((entry) => entry.id === 'n');
    for (let m = mParameter.min; m <= mParameter.max; m++) for (let n = nParameter.min; n <= nParameter.max; n++) {
      const frames = buildLessonFrames(lesson, { m, n });
      const expected = exactGcd(m, n);
      for (const frame of frames) {
        const context = `lesson ${order}, (${m}, ${n}), ${frame.id}`;
        if (frame.scene.kind === 'balance') {
          const total = (terms) => terms.reduce((accumulator, term) => accumulator + (term.coefficient ?? 1) * term.value, 0);
          assert.equal(total(frame.scene.left), total(frame.scene.right), context);
        }
        if (order === 10) {
          const values = variablesOf(frame);
          assert.equal(values["a'"] * m + values["b'"] * n, values.c, context);
          assert.equal(values.a * m + values.b * n, values.d, context);
          assert.equal(exactGcd(values.c, values.d), expected, context);
          assert.ok(values.d > 0, context);
          if (frame.id.startsWith('recipe-')) assert.equal(values.u * m + values.v * n, values.c % values.d, context);
          if (frame.id.startsWith('shift-')) assert.ok(values.d < values.c, context);
        }
      }
      const result = variablesOf(frames.at(-1));
      assert.equal(result.d, expected, `lesson ${order}, (${m}, ${n}) final GCD`);
      assert.equal(result.a * m + result.b * n, expected, `lesson ${order}, (${m}, ${n}) final certificate`);
    }
  }
});

test('assignment lesson preserves old values and demonstrates the failed swap at every input', () => {
  const lesson = lessonByOrder(3);
  for (let a = 1; a <= 20; a++) for (let b = 1; b <= 20; b++) {
    const frames = Object.fromEntries(buildLessonFrames(lesson, { a, b }).map((frame) => [frame.id, variablesOf(frame)]));
    assert.deepEqual(frames.start, { a, b });
    assert.deepEqual(frames['bad-first'], { a: b, b });
    assert.deepEqual(frames.restart, { a, b });
    assert.deepEqual(frames.save, { a, b, t: a });
    assert.deepEqual(frames['copy-b'], { a: b, b, t: a });
    assert.deepEqual(frames.finish, { a: b, b: a, t: a });
    assert.deepEqual(frames.parallel, { a: b, b: a });
  }
});

test('prefix-sum loop distinguishes addition state from restored loop-head invariant', () => {
  const lesson = lessonByOrder(8);
  const cards = [2, 5, 1, 4, 3, 6];
  for (let length = 1; length <= cards.length; length++) {
    for (const frame of buildLessonFrames(lesson, { length })) {
      const { k, s } = variablesOf(frame);
      const count = frame.id.startsWith('add-') ? k + 1 : k;
      assert.equal(s, cards.slice(0, count).reduce((total, card) => total + card, 0), `${length}: ${frame.id}`);
      assert.ok(k >= 0 && k <= length);
      if (frame.id === 'exit') assert.equal(k, length);
    }
  }
});

test('induction examples count exact cells and Fibonacci terms without replacing the symbolic proof', () => {
  const induction = lessonByOrder(5);
  for (let n = 1; n <= 8; n++) {
    const frames = buildLessonFrames(induction, { n });
    for (const frame of frames.filter((entry) => entry.scene.kind === 'grid')) {
      const cells = frame.scene.cells ?? [];
      const rows = frame.scene.rows;
      if (frame.id !== 'rectangle') assert.equal(cells.length, rows * (rows + 1) / 2);
      else {
        assert.equal(cells.filter((cell) => cell.group === 0).length, n * (n + 1) / 2);
        assert.equal(cells.filter((cell) => cell.group === 1).length, n * (n + 1) / 2);
      }
    }
  }
  const fibonacci = [0, 1];
  for (let k = 2; k <= 12; k++) fibonacci[k] = fibonacci[k - 1] + fibonacci[k - 2];
  for (let n = 2; n <= 12; n++) {
    for (const frame of buildLessonFrames(lessonByOrder(7), { n }).filter((entry) => entry.id.startsWith('case-'))) {
      const k = Number(frame.id.slice(5)), values = variablesOf(frame);
      assert.equal(values.a, fibonacci[k - 1]);
      assert.equal(values.b, fibonacci[k]);
      assert.equal(values.bound, 2 ** (k - 1));
      assert.ok(values.b <= values.bound);
    }
  }
});

test('lesson 2 counts the performed operations before and after each separate zero test', () => {
  const lesson = lessonByOrder(2);
  const pairs = [[84, 33], [33, 84], [1, 1], [1, 144], [144, 1], [144, 144]];
  for (let m = 1; m <= 20; m++) for (let n = 1; n <= 20; n++) pairs.push([m, n]);
  for (const [m, n] of pairs) for (const e0 of [0, 1]) {
    const frames = buildLessonFrames(lesson, { m, n, e0 });
    let divisions = 0;
    for (const frame of frames) {
      const counts = Object.fromEntries(frame.counters.map((counter) => [counter.label, counter.value]));
      if (frame.id.startsWith('division-')) {
        divisions++;
        assert.equal(counts.Divisions, divisions);
        assert.equal(counts['Zero checks'], divisions - 1);
        assert.equal(counts.Reductions, divisions - 1);
      }
      if (frame.id.startsWith('reduce-')) {
        assert.equal(counts.Divisions, divisions);
        assert.equal(counts['Zero checks'], divisions);
        assert.equal(counts.Reductions, divisions);
      }
      if (frame.id === 'return') {
        assert.equal(counts.Divisions, divisions);
        assert.equal(counts['Zero checks'], divisions);
        assert.equal(counts.Reductions, divisions - 1);
        assert.equal(variablesOf(frame).gcd, exactGcd(m, n));
      }
    }
    const final = variablesOf(frames.at(-1));
    assert.equal(final.D, divisions); assert.equal(final.C, divisions); assert.equal(final.R, divisions - 1);
  }
  for (const [m, n, e0, divisions] of [[84, 33, 0, 4], [33, 84, 0, 5], [33, 84, 1, 4]]) {
    const program = buildLessonFrames(lesson, { m, n, e0 })[0].code.lines.join('\n');
    const result = spawnSync('python3', ['-c', program], { encoding: 'utf8', timeout: 5000 });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout.trim(), `3 ${divisions} ${divisions} ${divisions - 1}`);
  }
});

test('every exact decimal pattern denotes the controlled rational number', () => {
  const lesson = lessonByOrder(11);
  for (let p = 1; p <= 7; p++) for (let q = 2; q <= 12; q++) {
    const frame = buildLessonFrames(lesson, { p, q }).find((entry) => entry.id === 'decimal-name');
    const decimal = variablesOf(frame).decimal;
    const match = /^(\d+)(?:\.(\d*)(?:\((\d+)\))?)?$/.exec(decimal);
    assert.ok(match, decimal);
    const [, whole, prefix = '', repeat = ''] = match;
    const scale = 10n ** BigInt(prefix.length);
    const cycle = repeat ? 10n ** BigInt(repeat.length) - 1n : 1n;
    const denominator = scale * cycle;
    const numerator = BigInt(whole) * denominator + BigInt(prefix || '0') * cycle + BigInt(repeat || '0');
    assert.equal(numerator * BigInt(q), BigInt(p) * denominator, `${p}/${q}: ${decimal}`);
  }
});

test('sum reindexing preserves the term values, not just index labels', () => {
  const lesson = lessonByOrder(18);
  for (let lower = 0; lower <= 4; lower++) for (let count = 1; count <= 6; count++) {
    const frames = buildLessonFrames(lesson, { lower, count });
    const original = frames.find((frame) => frame.id === 'original').scene;
    assert.equal(original.indexStart, lower);
    assert.deepEqual(original.terms, Array.from({ length: count }, (_, j) => j + lower));
    const matched = frames.find((frame) => frame.id === 'replace-summand').scene;
    const nodes = new Map(matched.nodes.map((node) => [node.id, node]));
    assert.equal(matched.edges.length, count);
    for (const edge of matched.edges) assert.equal(nodes.get(edge.from).value, nodes.get(edge.to).value);
    assert.equal(matched.nodes.filter((node) => node.id.startsWith('new-')).reduce((total, node) => total + node.value, 0), original.total);
  }
});

test('arithmetic pairing counts two full copies, including one-term and constant progressions', () => {
  const lesson = lessonByOrder(19);
  for (let first = 1; first <= 6; first++) for (let difference = 0; difference <= 4; difference++) for (let count = 1; count <= 6; count++) {
    const frames = buildLessonFrames(lesson, { first, difference, count });
    const terms = Array.from({ length: count }, (_, i) => first + i * difference);
    const total = terms.reduce((a, b) => a + b, 0);
    const graph = frames.find((frame) => frame.id === 'pair-columns').scene;
    const nodes = new Map(graph.nodes.map((node) => [node.id, node]));
    assert.equal(graph.edges.length, count);
    assert.equal(graph.nodes.length, 2 * count);
    for (const edge of graph.edges) assert.equal(nodes.get(edge.from).value + nodes.get(edge.to).value, terms[0] + terms.at(-1));
    const final = variablesOf(frames.find((frame) => frame.id === 'divide-two'));
    assert.equal(final.S, total);
    assert.equal(final.n * final['endpoint average'], total);
    assert.equal(variablesOf(frames.find((frame) => frame.id === 'two-copies'))['2S'], 2 * total);
  }
});

test('geometric cancellation aligns equal interior powers and retains the ratio-one and empty branches', () => {
  const lesson = lessonByOrder(20);
  for (let ratio = 1; ratio <= 4; ratio++) for (let count = 0; count <= 6; count++) {
    const frames = buildLessonFrames(lesson, { ratio, count });
    const total = Array.from({ length: count }, (_, i) => ratio ** i).reduce((a, b) => a + b, 0);
    for (const frame of frames) if (Object.hasOwn(variablesOf(frame), 'S')) assert.equal(variablesOf(frame).S, total);
    const initial = frames.find((frame) => frame.id === 'constant-ratio').scene;
    assert.equal(initial.indexStart, 0);
    assert.equal(initial.active, count - 1);
    assert.equal(initial.total, total);
    const graph = frames.find((frame) => frame.id === 'align-cancel').scene;
    if (count) {
      const nodes = new Map(graph.nodes.map((node) => [node.id, node]));
      assert.equal(graph.edges.length, count - 1);
      for (const edge of graph.edges) {
        assert.equal(nodes.get(edge.from).value, nodes.get(edge.to).value);
        close(nodes.get(edge.from).x, nodes.get(edge.to).x, 'Equal powers align in the same column');
      }
    }
    assert.equal((ratio - 1) * total, ratio ** count - 1);
    if (ratio === 1) assert.equal(total, count);
  }
});
