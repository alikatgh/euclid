/**
 * Lesson Core quality gate.
 *
 * `validateLessonSpec` executes a lesson against all of its presets plus a
 * deterministic fuzz sweep and returns a list of human-readable violations.
 * An empty list means the lesson meets the Lesson 1 bar mechanically.
 * Runs in Node (npm test) and in the browser (dev-mode banner).
 */
import type {
  CheckQuestion, DiagramScene, LessonInput, LessonSpec, StepContext, Tone, TraceStep,
} from './types.ts';

export type TexValidator = (tex: string) => void;

export interface ValidateOptions {
  /** Throws on invalid TeX. Pass KaTeX (`strict: 'error'`) in tests. */
  renderTex?: TexValidator;
  /** Random inputs per variant (default 60). */
  fuzzRuns?: number;
}

const TONES: readonly Tone[] = ['primary', 'secondary', 'accent', 'alert', 'result', 'muted'];
const BANNED = /\b(TODO|TBD|FIXME|lorem ipsum|placeholder|xxx)\b/i;
const MIN_PROSE = 20;

/** Small deterministic PRNG so fuzzing is reproducible per lesson id. */
function rng(seedText: string): () => number {
  let seed = 2166136261;
  for (const ch of seedText) seed = Math.imul(seed ^ ch.charCodeAt(0), 16777619);
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function inlineTex(text: string): string[] {
  return [...text.matchAll(/\$([^$]+)\$/g)].map(m => m[1]);
}

export function validateLessonSpec<I extends LessonInput, S extends TraceStep>(
  spec: LessonSpec<I, S>,
  options: ValidateOptions = {},
): string[] {
  const errors: string[] = [];
  const where = (path: string) => `${spec.id ?? '?'}: ${path}`;
  const fail = (path: string, message: string) => errors.push(`${where(path)} ${message}`);
  const prose = (path: string, value: unknown, min = MIN_PROSE) => {
    if (typeof value !== 'string' || value.trim().length < min) fail(path, `must be teaching prose of at least ${min} characters`);
    else {
      if (BANNED.test(value)) fail(path, 'contains placeholder text');
      tex(path, value, true);
    }
  };
  const label = (path: string, value: unknown) => {
    if (typeof value !== 'string' || !value.trim()) fail(path, 'must be a non-empty string');
    else if (BANNED.test(value)) fail(path, 'contains placeholder text');
  };
  const tex = (path: string, value: string, inline = false) => {
    if (!options.renderTex) return;
    for (const expr of inline ? inlineTex(value) : [value]) {
      try { options.renderTex(expr); } catch (e) { fail(path, `has invalid TeX "${expr}": ${(e as Error).message.split('\n')[0]}`); }
    }
  };
  const unique = (path: string, values: string[]) => {
    if (new Set(values).size !== values.length) fail(path, 'must have unique ids');
  };

  /* ---------------- static fields */
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(spec.id ?? '')) fail('id', 'must be kebab-case');
  if (!Number.isInteger(spec.order) || spec.order < 1) fail('order', 'must be a positive integer');
  if (!spec.navigationLabel?.startsWith(`Lesson ${spec.order} · `)) fail('navigationLabel', `must start with "Lesson ${spec.order} · "`);
  label('title', spec.title); label('subtitle', spec.subtitle);
  label('source.book', spec.source?.book); label('source.section', spec.source?.section);

  const varKeys = (spec.variables ?? []).map(v => v.key);
  if (!varKeys.length) fail('variables', 'must declare at least one variable');
  unique('variables', varKeys);
  for (const v of spec.variables ?? []) {
    label(`variables.${v.key}.symbol`, v.symbol);
    if (!TONES.includes(v.tone)) fail(`variables.${v.key}.tone`, `must be one of ${TONES.join(', ')}`);
    prose(`variables.${v.key}.meaning`, v.meaning, 8);
  }

  const inputKeys = (spec.inputs ?? []).map(f => f.key);
  if (!inputKeys.length) fail('inputs', 'must declare at least one learner input');
  unique('inputs', inputKeys);
  for (const f of spec.inputs ?? []) {
    label(`inputs.${f.key}.label`, f.label);
    if (!Number.isInteger(f.min) || !Number.isInteger(f.max) || f.min >= f.max) fail(`inputs.${f.key}`, 'needs integer min < max');
  }
  const inRange = (input: I) => (spec.inputs ?? []).every(f => Number.isInteger(input?.[f.key]) && input[f.key] >= f.min && input[f.key] <= f.max);
  if (!inRange(spec.defaultInput)) fail('defaultInput', 'must provide every input within its range');

  if ((spec.presets ?? []).length < 3) fail('presets', 'needs at least 3 presets (typical, edge, large)');
  unique('presets', (spec.presets ?? []).map(p => p.name));
  unique('presets(input)', (spec.presets ?? []).map(p => JSON.stringify(p.input)));
  for (const p of spec.presets ?? []) { label(`presets.${p.name}`, p.name); if (!inRange(p.input)) fail(`presets.${p.name}`, 'input out of range'); }

  const variantIds = (spec.variants ?? []).map(v => v.id);
  if (!variantIds.length) fail('variants', 'needs at least one variant');
  unique('variants', variantIds);
  (spec.variants ?? []).forEach(v => label(`variants.${v.id}.label`, v.label));
  const viewIds = (spec.views ?? []).map(v => v.id);
  if (!viewIds.length) fail('views', 'needs at least one view');
  unique('views', viewIds);
  (spec.views ?? []).forEach(v => label(`views.${v.id}.label`, v.label));

  const defs = spec.stepDefinitions ?? [];
  if (defs.length < 2) fail('stepDefinitions', 'needs at least 2 steps');
  unique('stepDefinitions', defs.map(d => d.id));
  for (const d of defs) {
    label(`stepDefinitions.${d.id}.name`, d.name);
    prose(`stepDefinitions.${d.id}.description`, d.description, 12);
    if (d.optional && !(d.enabledIn ?? []).every(id => variantIds.includes(id))) fail(`stepDefinitions.${d.id}.enabledIn`, 'references an unknown variant');
    if (d.optional && !(d.enabledIn ?? []).length) fail(`stepDefinitions.${d.id}.enabledIn`, 'optional steps must name the variants that enable them');
  }
  if (!Number.isInteger(spec.maxSteps) || spec.maxSteps < 2) fail('maxSteps', 'must be an integer ≥ 2');

  label('workedExample.title', spec.workedExample?.title);
  prose('workedExample.sourceNote', spec.workedExample?.sourceNote, 12);
  label('workedExample.principles.title', spec.workedExample?.principles?.title);
  if (!(spec.workedExample?.principles?.paragraphs ?? []).length) fail('workedExample.principles', 'must state at least one principle (invariant/termination)');
  (spec.workedExample?.principles?.paragraphs ?? []).forEach((p, i) => prose(`workedExample.principles[${i}]`, p, 40));

  label('code.title', spec.code?.title); prose('code.intro', spec.code?.intro, 12);
  for (const lang of ['c', 'python'] as const) {
    const listing = spec.code?.languages?.[lang];
    if (!listing) { fail(`code.${lang}`, 'is required'); continue; }
    label(`code.${lang}.label`, listing.label);
    if (listing.lines.length < 3) fail(`code.${lang}.lines`, 'must be a complete runnable program');
    unique(`code.${lang}.lines`, listing.lines.map(l => l.id));
  }

  label('trace.title', spec.trace?.title); label('trace.caption', spec.trace?.caption);
  const columnKeys = (spec.trace?.columns ?? []).map(c => c.key);
  if (columnKeys.length < 2) fail('trace.columns', 'needs at least 2 columns');
  unique('trace.columns', columnKeys);

  label('help.title', spec.help?.title);
  if ((spec.help?.frames ?? []).length < 2) fail('help.frames', 'needs its own smaller example with at least 2 frames');
  (spec.help?.frames ?? []).forEach((f, i) => { prose(`help.frames[${i}].explanation`, f.explanation); scene(`help.frames[${i}].diagram`, f.diagram); });
  check('help.check', spec.help?.check);

  if (errors.length) return errors; // dynamic checks need a sound static shape

  /* ---------------- dynamic execution */
  const random = rng(spec.id);
  const fuzz: I[] = [];
  for (let i = 0; i < (options.fuzzRuns ?? 60); i++) {
    const input = {} as Record<string, number>;
    for (const f of spec.inputs) {
      // Bias half the samples to small values, where edge cases live.
      const hi = i % 2 ? f.max : Math.min(f.max, f.min + 20);
      input[f.key] = f.min + Math.floor(random() * (hi - f.min + 1));
    }
    fuzz.push(input as I);
  }
  const inputs: I[] = [spec.defaultInput, ...spec.presets.map(p => p.input), ...fuzz];
  const reached = new Set<string>();

  for (const variant of variantIds) {
    for (const [k, input] of inputs.entries()) {
      const tag = `run(${JSON.stringify(input)}, ${variant})`;
      const deep = k <= spec.presets.length; // full per-step checks on default + presets
      let steps: S[];
      try { steps = spec.run(input, variant); } catch (e) { fail(tag, `throws: ${(e as Error).message}`); continue; }
      if (JSON.stringify(steps) !== JSON.stringify(spec.run(input, variant))) fail(tag, 'is not deterministic');
      if (!Array.isArray(steps) || steps.length < 2) { fail(tag, 'must produce at least 2 steps'); continue; }
      if (steps.length > spec.maxSteps) fail(tag, `exceeds maxSteps (${steps.length} > ${spec.maxSteps})`);
      const terminals = steps.filter(s => s.terminal).length;
      if (terminals !== 1 || !steps[steps.length - 1].terminal) fail(tag, 'must have exactly one terminal step, and it must be last');

      steps.forEach((step, index) => {
        const at = `${tag}[${index}]`;
        const def = defs.find(d => d.id === step.phase);
        if (!def) { fail(at, `phase "${step.phase}" is not a stepDefinition`); return; }
        if (def.optional && !def.enabledIn?.includes(variant)) fail(at, `optional phase ${def.id} ran in variant ${variant}`);
        reached.add(step.phase);
        label(`${at}.badge`, step.badge);
        for (const key of varKeys) if (!(key in step.values)) fail(at, `values is missing "${key}"`);
        for (const [key, v] of Object.entries({ ...step.values, ...(step.next ?? {}) })) {
          if (!varKeys.includes(key)) fail(at, `unknown variable "${key}"`);
          if (v !== null && !Number.isFinite(v)) fail(at, `${key} is not finite`);
        }
        if (!deep && index % 5) return;
        const ctx: StepContext<I, S> = { input, variant, steps, index };
        try {
          const f = spec.formula(step, ctx);
          for (const key of ['compact', 'full', 'invariant'] as const) { label(`${at}.formula.${key}`, f[key]); tex(`${at}.formula.${key}`, f[key]); }
          if (f.reference) { label(`${at}.formula.reference.label`, f.reference.label); tex(`${at}.formula.reference`, f.reference.tex); }
        } catch (e) { fail(`${at}.formula`, `throws: ${(e as Error).message}`); }
        for (const view of viewIds) {
          try { scene(`${at}.diagram(${view})`, spec.diagram(step, { ...ctx, view })); }
          catch (e) { fail(`${at}.diagram(${view})`, `throws: ${(e as Error).message}`); }
        }
        try { prose(`${at}.narrate`, spec.narrate(step, ctx)); } catch (e) { fail(`${at}.narrate`, `throws: ${(e as Error).message}`); }
        for (const lang of ['c', 'python'] as const) {
          const listing = spec.code.languages[lang];
          const visible = new Set(listing.lines.filter(l => !l.variants || l.variants.includes(variant)).map(l => l.id));
          try {
            const active = listing.activeLines(step, ctx);
            if (!active.length) fail(`${at}.code.${lang}`, 'must highlight at least one line');
            for (const id of active) if (!visible.has(id)) fail(`${at}.code.${lang}`, `highlights missing/hidden line "${id}"`);
            const ex = listing.explain(step, ctx);
            label(`${at}.code.${lang}.title`, ex.title); prose(`${at}.code.${lang}.explanation`, ex.explanation);
          } catch (e) { fail(`${at}.code.${lang}`, `throws: ${(e as Error).message}`); }
        }
        try {
          const rows = spec.trace.rows(steps, index);
          for (const row of rows) {
            if (!Number.isInteger(row.stepIndex) || row.stepIndex < 0 || row.stepIndex >= steps.length) fail(`${at}.trace`, 'row points to a missing step');
            for (const key of Object.keys(row.cells)) if (!columnKeys.includes(key)) fail(`${at}.trace`, `unknown column "${key}"`);
          }
        } catch (e) { fail(`${at}.trace`, `throws: ${(e as Error).message}`); }
      });
      if (!steps.length || !spec.trace.rows(steps, steps.length - 1).length) fail(`${tag}.trace`, 'final step must have at least one trace row');

      try {
        prose(`${tag}.workedExample.intro`, spec.workedExample.intro(input, variant));
        const paragraphs = spec.workedExample.paragraphs(steps, input, variant);
        if (!paragraphs.length) fail(`${tag}.workedExample`, 'needs paragraphs');
        const covered = new Set<number>();
        for (const p of paragraphs) for (const c of p.chunks) {
          if (!Number.isInteger(c.stepIndex) || c.stepIndex < 0 || c.stepIndex >= steps.length) fail(`${tag}.workedExample`, 'chunk points to a missing step');
          covered.add(c.stepIndex);
          if (deep) prose(`${tag}.workedExample.chunk`, c.text, 12);
        }
        for (let i = 0; i < steps.length; i++) if (!covered.has(i)) { fail(`${tag}.workedExample`, `step ${i} has no worked-example chunk`); break; }
      } catch (e) { fail(`${tag}.workedExample`, `throws: ${(e as Error).message}`); }
      if (errors.length > 40) return errors;
    }
  }
  for (const d of defs) if (!reached.has(d.id)) fail(`stepDefinitions.${d.id}`, 'is never reached by any preset, variant or fuzz input');
  return errors;

  function scene(path: string, s: DiagramScene) {
    if (!s || !(s.width > 0) || !(s.height > 0)) { fail(path, 'needs positive width and height'); return; }
    label(`${path}.description`, s.description);
    if (!s.nodes?.length) { fail(path, 'must draw at least one node'); return; }
    const ids = new Set<string>();
    for (const n of s.nodes) {
      if (!n.id || ids.has(n.id)) fail(path, `node id "${n.id}" must be unique and stable`);
      ids.add(n.id);
      if (n.tone && !TONES.includes(n.tone)) fail(path, `node ${n.id} has unknown tone`);
      for (const [k, v] of Object.entries(n)) if (typeof v === 'number' && !Number.isFinite(v)) fail(path, `node ${n.id}.${k} is not finite`);
      if ((n.type === 'rect' && (n.width < 0 || n.height < 0)) || (n.type === 'circle' && n.r < 0)) fail(path, `node ${n.id} has negative size`);
      if (n.type === 'text') { label(`${path}.${n.id}.text`, n.text); tex(`${path}.${n.id}`, n.text, true); }
    }
  }
  function check(path: string, q: CheckQuestion | undefined) {
    if (!q) { fail(path, 'is required'); return; }
    prose(`${path}.prompt`, q.prompt, 15);
    if ((q.options ?? []).length < 2) fail(path, 'needs at least 2 options');
    if ((q.options ?? []).filter(o => o.correct).length !== 1) fail(path, 'needs exactly one correct option');
    unique(`${path}.options`, (q.options ?? []).map(o => o.id));
    if (new Set((q.options ?? []).map(o => o.text)).size !== (q.options ?? []).length) fail(path, 'options must have distinct text');
    (q.options ?? []).forEach(o => { label(`${path}.${o.id}.text`, o.text); prose(`${path}.${o.id}.feedback`, o.feedback, 15); });
  }
}

/** Registry-level rules: unique ids and orders. */
export function validateRegistry(specs: readonly LessonSpec<any, any>[]): string[] {
  const errors: string[] = [];
  const ids = specs.map(s => s.id), orders = specs.map(s => s.order);
  if (new Set(ids).size !== ids.length) errors.push('registry: lesson ids must be unique');
  if (new Set(orders).size !== orders.length) errors.push('registry: lesson orders must be unique');
  return errors;
}
