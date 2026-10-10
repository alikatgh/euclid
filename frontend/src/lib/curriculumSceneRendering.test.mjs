import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { readFileSync } from 'node:fs';
import { computeAlgorithmSteps } from '../hooks/useAlgorithm.ts';
import { fileURLToPath } from 'node:url';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

// Structural and mathematical renderer regressions, not a browser layout test.
test('scene renderer preserves exact relations, indices, sparse cells and reverse paths', async (context) => {
  const server = await createServer({ root: fileURLToPath(new URL('../..', import.meta.url)), server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' });
  try {
    const { CurriculumScene } = await server.ssrLoadModule('/src/components/CurriculumScene.tsx');
    const render = (scene) => renderToStaticMarkup(createElement(CurriculumScene, { scene, isPlaying: false }));
    const plain = (html) => html.replace(/<[^>]*>/g, '');
    await context.test('growth-stage graphics are labeled groups that expose interactive number descendants', () => {
      const html = render({ kind: 'growth', base: 4, exponent: -1, stages: [
        { label: 'whole', value: 1 }, { label: 'half', value: .5 }, { label: 'quarter', value: .25, active: true },
      ], caption: 'Reciprocal scaling.' });
      const svgs = [...html.matchAll(/<svg\b[^>]*>/g)].map((match) => match[0]);
      assert.equal(svgs.length, 3);
      for (const svg of svgs) { assert.match(svg, /role="group"/); assert.match(svg, /aria-label="[^"]+"/); }
      assert.doesNotMatch(html, /<svg\b[^>]*role="img"/);
      assert.match(html, /data-math-keyboard="true"/);
    });
    await context.test('reference explanation landmark has a distinct accessible name', async () => {
      const { Sidebar } = await server.ssrLoadModule('/src/components/Sidebar.tsx');
      const lesson = JSON.parse(readFileSync(new URL('../../../content/lessons.json', import.meta.url), 'utf8'));
      const steps = computeAlgorithmSteps(84, 33, false, lesson);
      const html = renderToStaticMarkup(createElement(Sidebar, { step: steps[0], steps,
        stepsDefinitions: lesson.algorithm.steps_definition, content: lesson.algorithm.mathematicalReading,
        withE0: false, panels: { formula: true, steps: true, example: true }, onTogglePanel() {},
      }));
      assert.match(html, /<aside\b[^>]*class="explanation-stack"[^>]*aria-label="Algorithm explanation"/);
    });
    await context.test('exact thirds balance as equals while a truncated third remains unequal', () => {
      const exact = render({ kind: 'balance', left: [{ label: 'finite decimal', value: .333, exactValue: '333/1000' }, { label: 'gap', value: 1 / 3000, exactValue: '1/3000' }], right: [{ label: 'third', value: 1 / 3, exactValue: '1/3' }], caption: 'An exact identity.' });
      assert.match(plain(exact), /The two totals are equal/);
      assert.doesNotMatch(plain(exact), /≠/);
      assert.match(plain(exact), /1\/3=1\/3/);
      const rounded = render({ kind: 'balance', left: [{ label: 'truncated', value: .333 }], right: [{ label: 'third', value: 1 / 3, exactValue: '1/3' }], caption: 'The missing piece is nonzero.' });
      assert.match(plain(rounded), /333\/1000≠1\/3/);
    });
    await context.test('array indices and geometric exponents can begin at zero', () => {
      const html = render({ kind: 'accumulation', terms: [2, 5], indexStart: 0, active: 0, total: 2, operation: 'sum', caption: 'Array positions.' });
      assert.match(plain(html), /i = 0/); assert.match(plain(html), /i = 1/);
      assert.doesNotMatch(plain(html), /i = 2/);
      assert.match(html, /data-reading-scroll/);
      assert.match(html, /data-math-keyboard="true"/);
    });
    await context.test('fractions retain exact cell labels and unlisted cells remain empty', () => {
      const html = render({ kind: 'grid', rows: 1, columns: 3, cells: [{ row: 0, column: 0, value: 1 / 3, label: '1/3' }], caption: 'One selected third.' });
      assert.match(plain(html), /1 occupied cells/);
      assert.match(plain(html), /1\/3/);
      assert.equal((html.match(/stroke-dasharray="2 3"/g) ?? []).length, 2);
      assert.doesNotMatch(plain(html), /0\.333333/);
    });
    await context.test('reverse arrows take different curves and operation nodes have roomy cards', () => {
      const html = render({ kind: 'graph', nodes: [{ id: 'a', label: 'Print k; subtract 1', x: .3, y: .2 }, { id: 'b', label: 'k > 0?', x: .7, y: .7 }], edges: [{ from: 'a', to: 'b', label: 'repeat' }, { from: 'b', to: 'a', label: 'yes' }], caption: 'Control flow.' });
      const curves = [...html.matchAll(/d="(M [^"]+ Q [^"]+)"/g)].map((match) => match[1]);
      assert.equal(curves.length, 2); assert.notEqual(curves[0], curves[1]);
      assert.match(html, /rx="10"/);
      assert.match(plain(html), /Print k; subtract 1/);
    });
    await context.test('long axis labels wrap and get a taller viewBox rather than overlap', () => {
      const html = render({ kind: 'number-line', min: -1, max: 1, points: [
        { value: -1, label: 'Left endpoint: negative unit length', active: true },
        { value: 0, label: 'Zero separates negative and positive quantities' },
        { value: 1, label: 'Right endpoint: positive unit length' },
      ], caption: 'Long labels.' });
      assert.match(plain(html), /negative unit length/);
      assert.doesNotMatch(html, /NaN|Infinity/);
      const height = Number(html.match(/viewBox="0 0 720 ([\d.]+)"/)[1]);
      assert.ok(height >= 240);
    });
    await context.test('a flat arithmetic progression has equal column heights', () => {
      const html = render({ kind: 'staircase', count: 3, active: 2, base: 0, values: [5, 5, 5], labels: ['i=0: 5', 'i=1: 5', 'i=2: 5'], caption: 'Difference zero.' });
      const heights = [...html.matchAll(/<rect\b[^>]*\bheight="([\d.]+)(?:px)?"/g)].map((match) => Number(match[1]));
      assert.deepEqual(heights, [204, 204, 204]);
      assert.match(plain(html), /actual term values/);
    });
    await context.test('empty products start at one and empty sums at zero', () => {
      for (const [operation, total] of [['product', 1], ['sum', 0]]) {
        const html = render({ kind: 'accumulation', terms: [], active: -1, total, operation, caption: 'Empty index set.' });
        assert.match(plain(html), new RegExp(`start at ${total}`));
        assert.match(plain(html), new RegExp(`Running ${operation}: ${total}`));
        assert.doesNotMatch(html, /NaN|Infinity/);
      }
    });
  } finally { await server.close(); }
});
