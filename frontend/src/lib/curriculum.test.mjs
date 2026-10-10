import assert from 'node:assert/strict';
import { test } from 'node:test';
import { buildLessonFrames, curriculumLessons, defaultInputs, lessonCatalog, validateLessonInputs } from './curriculum.ts';
import { renderLinkedMath } from './mathConnections.ts';

test('catalog preserves reference lesson and exactly nineteen original lessons in sequence', () => {
  assert.equal(lessonCatalog.length, 20);
  assert.equal(lessonCatalog[0].id, 'algorithm-e');
  assert.deepEqual(lessonCatalog.map((lesson) => lesson.order), Array.from({ length: 20 }, (_, index) => index + 1));
  assert.equal(new Set(lessonCatalog.map((lesson) => lesson.id)).size, 20);
});

test('every lesson has a complete deterministic model, a source, and meaningful predictions', () => {
  for (const lesson of curriculumLessons) {
    assert.ok(lesson.sources.length > 0, lesson.id);
    assert.ok(lesson.objectives.length >= 2, lesson.id);
    assert.ok(lesson.parameters.length >= 1, `${lesson.id} must be manipulable`);
    for (const source of lesson.sources) {
      assert.ok(source.title && source.section && source.note);
      assert.ok(!source.url || /^https:\/\/(?:www\.)?(?:cs\.stanford\.edu|www-cs-faculty\.stanford\.edu|informit\.com|pearson\.com)\//.test(source.url), 'No private/unverified source links in distributable lessons');
    }
    const inputs = defaultInputs(lesson);
    const frames = buildLessonFrames(lesson, inputs);
    assert.deepEqual(buildLessonFrames(lesson, inputs), frames, `${lesson.id} is not deterministic`);
    assert.ok(frames.length >= 3, `${lesson.id} lacks staged reasoning`);
    assert.ok(frames.some((frame) => frame.prediction), `${lesson.id} needs a prediction`);
    assert.ok(frames.some((frame) => frame.variables.length > 0), `${lesson.id} must bind concrete quantities`);
    assert.ok(frames.every((frame) => frame.code.lines.length > 0), lesson.id);
    assert.equal(new Set(frames.map((frame) => frame.id)).size, frames.length);
    for (const parameter of lesson.parameters) {
      for (const invalid of [NaN, Infinity, -Infinity, parameter.min - 1, parameter.max + 1]) {
        assert.throws(() => validateLessonInputs(lesson, { ...inputs, [parameter.id]: invalid }), RangeError);
      }
    }
  }
});

test('symbol bindings link live numeric values without changing MathML or trusting HTML', () => {
  const plain = renderLinkedMath('m+n=17');
  const linked = renderLinkedMath('m+n=17', {}, { m: 12, n: 5 });
  assert.match(linked, /data-math-value="12">m/);
  assert.match(linked, /data-math-value="5">n/);
  assert.equal(linked.match(/<math[\s\S]*?<\/math>/)?.[0], plain.match(/<math[\s\S]*?<\/math>/)?.[0]);
  assert.doesNotMatch(renderLinkedMath('m', {}, { m: '"><script>alert(1)</script>' }), /<script>/);
});

test('symbol bindings recompute without retaining previous numeric identity', () => {
  const first = renderLinkedMath('x', {}, { x: 3 });
  const second = renderLinkedMath('x', {}, { x: 8 });
  assert.match(first, /data-math-value="3">x/);
  assert.doesNotMatch(second, /data-math-value="3"/);
  assert.match(second, /data-math-value="8">x/);
});

test('decorated symbols never inherit a different unadorned state binding', () => {
  for (const tex of ['a_0', "a'", String.raw`\widehat{T}`, String.raw`D_{E0}`, 'b^n']) {
    const html = renderLinkedMath(tex, {}, { a: 937, T: 938, D: 939, b: 940, n: 941 });
    assert.doesNotMatch(html, /data-math-value="(?:937|938|939|940|941)"/, tex);
  }
  const literals = renderLinkedMath('a_0+12', {}, { a: 937 });
  assert.match(literals, /data-math-value="0"/);
  assert.match(literals, /data-math-value="12"/);
  assert.match(renderLinkedMath('a_0+a', {}, { a: 937 }), /data-math-value="937">a/);
});
