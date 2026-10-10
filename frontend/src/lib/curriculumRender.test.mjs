import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createServer } from 'vite';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { curriculumLessons, defaultInputs, buildLessonFrames } from './curriculum.ts';

// This checks generated React/KaTeX/SVG structure, not browser layout or real input events.
test('every authored scene renders semantic SVG without a React exception', async () => {
  const server = await createServer({ server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' });
  try {
    const { CurriculumScene } = await server.ssrLoadModule('/src/components/CurriculumScene.tsx');
    const kinds = new Set();
    let rendered = 0;
    for (const lesson of curriculumLessons) {
      const initial = defaultInputs(lesson);
      const cases = [initial];
      for (const parameter of lesson.parameters) for (const bound of [parameter.min, parameter.max]) cases.push({ ...initial, [parameter.id]: bound });
      for (const inputs of cases) for (const frame of buildLessonFrames(lesson, inputs)) {
        const html = renderToStaticMarkup(createElement(CurriculumScene, { scene: frame.scene, isPlaying: false, playbackSpeed: 1 }));
        assert.match(html, /<svg\b/, `${lesson.id}/${frame.id} needs geometry`);
        assert.match(html, /<(?:title|desc)\b|aria-label=/, `${lesson.id}/${frame.id} needs an accessible explanation`);
        assert.doesNotMatch(html, /(?:="(?:NaN|Infinity|undefined)"|>NaN<)/, `${lesson.id}/${frame.id} invalid geometry`);
        kinds.add(frame.scene.kind); rendered++;
      }
    }
    assert.ok(rendered >= 100);
    assert.ok(kinds.size >= 7, 'Concepts need distinct geometric representations.');
  } finally { await server.close(); }
});
