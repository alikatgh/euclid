import assert from 'node:assert/strict';
import { test } from 'node:test';
import katex from 'katex';
import { mathValuesFromAttributes, normalizeMathValue, renderLinkedMath, splitLinkedNumbers } from './mathConnections.ts';

const linkedValues = (html) => [...html.matchAll(/ data-math-value="([^"]+)"/g)].map((match) => match[1]);
const uniqueValues = (html) => [...new Set(linkedValues(html))].sort();
const mathml = (html) => html.match(/<span class="katex-mathml">([\s\S]*?)<\/span>/)?.[0];

test('normalization compares exact scalar values without substring or floating-point matches', () => {
  for (const [formatted, canonical] of [
    ['00119', '119'], ['+119.00', '119'], ['1.19e2', '119'], ['119e-2', '1.19'],
    ['-0', '0'], ['−00.000', '0'], ['-.50', '-0.5'], ['−12.50', '-12.5'],
    ['100000000000000000001', '100000000000000000001'],
    ['1e100000000000000000000', '1e100000000000000000000'],
    ['120e-100000000000000000000', '1.2e-99999999999999999998'],
  ]) assert.equal(normalizeMathValue(formatted), canonical, formatted);
  assert.notEqual(normalizeMathValue(1), normalizeMathValue(119));
  for (const invalid of ['E1', '119px', '1/19', '', 'NaN', 'Infinity', '1.2.3']) assert.equal(normalizeMathValue(invalid), null);
  assert.deepEqual(mathValuesFromAttributes('1', '119 068 68 1.00 E1'), ['1', '119', '68']);
  assert.deepEqual(mathValuesFromAttributes(null, null), []);
});

test('prose tokenization retains exact text and excludes digits embedded in identifiers', () => {
  const text = 'E0, E1, x2 and 50px: 119 = 1 + 68; −12.50, .5 and 1.19e2.';
  const segments = splitLinkedNumbers(text);
  assert.equal(segments.map(({ text }) => text).join(''), text);
  assert.deepEqual(segments.filter(({ value }) => value !== undefined).map(({ value }) => value), ['119', '1', '68', '-12.5', '0.5', '119']);
  assert.deepEqual(splitLinkedNumbers('E0 E1 x2 _12 50px'), [{ text: 'E0 E1 x2 _12 50px' }]);
  assert.deepEqual(splitLinkedNumbers(''), []);
});

test('KaTeX annotates complete multi-digit values and retains accessible MathML byte for byte', () => {
  const tex = '119 = 1 + 68 + 0';
  const html = renderLinkedMath(tex);
  assert.deepEqual(linkedValues(html), ['119', '1', '68', '0']);
  const original = katex.renderToString(tex, { trust: false, output: 'htmlAndMathml' });
  assert.equal(html.replace(/ data-math-value="[^"]+"/g, ''), original);
  assert.equal(mathml(html), mathml(original));
  assert.doesNotMatch(mathml(html), /data-math-value|tabindex/);
  assert.doesNotMatch(html, /tabindex|role="button"/);
});

test('fraction numerators, denominators and whole-number terms remain distinct literals', () => {
  const html = renderLinkedMath('\\frac{119}{68} = 1\\frac{51}{68}');
  const values = linkedValues(html);
  assert.equal(values.filter((value) => value === '119').length, 1);
  assert.equal(values.filter((value) => value === '68').length, 2);
  assert.equal(values.filter((value) => value === '51').length, 1);
  assert.equal(values.filter((value) => value === '1').length, 1);
  assert.deepEqual(uniqueValues(html), ['1', '119', '51', '68']);
});

test('signed decimals, unary signs and formatted adjacent digit spans share the complete literal', () => {
  assert.deepEqual(uniqueValues(renderLinkedMath('-12.50 + -.5 + 0.00')), ['-0.5', '-12.5', '0']);
  assert.deepEqual(uniqueValues(renderLinkedMath('68 - 12')), ['12', '68'], 'binary minus is not part of the following number');
  assert.deepEqual(linkedValues(renderLinkedMath('1\\mathbf{19}')), ['119', '119']);
  assert.deepEqual(linkedValues(renderLinkedMath('1{.}25')), ['1.25', '1.25', '1.25']);
  assert.deepEqual(uniqueValues(renderLinkedMath('2^{10} + x_{-3}')), ['-3', '10', '2']);
});

test('only numeric text leaves are annotated, never command arguments, classes or layout lengths', () => {
  const tex = '\\color{#119119}{42} \\hspace{2em} \\rule{3em}{0.5em} \\htmlClass{role-68}{17}';
  const options = { strict: false, trust: ({ command }) => command === '\\htmlClass' };
  const html = renderLinkedMath(tex, options);
  assert.deepEqual(uniqueValues(html), ['17', '42']);
  assert.match(html, /class="enclosing role-68"/);
  assert.match(html, /color:#119119/);
  assert.equal(html.replace(/ data-math-value="[^"]+"/g, ''), katex.renderToString(tex, { trust: false, output: 'htmlAndMathml', ...options }));
  assert.deepEqual(uniqueValues(renderLinkedMath('\\text{E1 has 119 and 68}')), ['119', '68']);
});

test('multi-digit scripted bases stay whole while superscripts and subscripts remain separate', () => {
  for (const [tex, expected] of [
    ['1\\times10^{3}', ['1', '10', '3']],
    ['119_2', ['119', '2']],
    ['12.50^{3}', ['12.5', '3']],
    ['-12.50^{3}', ['-12.5', '3']],
    ['119^{2}_3', ['119', '2', '3']],
    ['1\\mathbf{19}^{2}', ['119', '2']],
    ['-10_{-2}', ['-10', '-2']],
    ['10^{3}119', ['10', '119', '3']],
    ['\\frac{10^{3}}{119_2}', ['10', '119', '2', '3']],
  ]) {
    const html = renderLinkedMath(tex);
    assert.deepEqual(uniqueValues(html), expected.sort(), tex);
    assert.equal(html.replace(/ data-math-value="[^"]+"/g, ''), katex.renderToString(tex, { trust: false, output: 'htmlAndMathml' }), tex);
  }
});

test('untrusted TeX stays untrusted, errors remain safe, and mathml-only output is preserved', () => {
  const options = { strict: false, throwOnError: false, trust: false };
  const unsafe = renderLinkedMath('\\href{javascript:alert(119)}{68} \\htmlClass{injected-68}{42}', options);
  assert.doesNotMatch(unsafe, /<a\b|class="[^"]*injected-68/);
  assert.doesNotMatch(unsafe, /(?:href|src)="javascript:/);
  const error = renderLinkedMath('119 \\frac{', options);
  assert.match(error, /class="katex-error"/);
  assert.deepEqual(linkedValues(error), []);
  assert.equal(renderLinkedMath('119 + 68', { output: 'mathml' }), katex.renderToString('119 + 68', { trust: false, output: 'mathml' }));
});
