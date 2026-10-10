/**
 * TeX conventions for lessons.
 *
 * Lessons colour symbols with `\tone{primary}{119}` instead of raw
 * `\htmlClass`. That keeps the palette semantic and lets the engine map
 * each tone to the original Euclid colour classes.
 */
import type { Tone } from './types.ts';

export const TONE_CLASS: Record<Tone, string> = {
  primary: 'text-rod-m',
  secondary: 'text-rod-n',
  accent: 'text-rod-q',
  alert: 'text-rod-r',
  result: 'text-rod-gcd',
  muted: 'text-muted',
};

/** Fill/stroke CSS variables for diagram shapes, per tone. */
export const TONE_STROKE: Record<Tone, string> = {
  primary: 'var(--color-m)',
  secondary: 'var(--color-n)',
  accent: 'var(--color-q)',
  alert: 'var(--color-r)',
  result: 'var(--color-gcd)',
  muted: 'var(--text-muted)',
};
export const TONE_FILL: Record<Tone, string> = {
  primary: 'var(--fill-rod-m)',
  secondary: 'var(--fill-rod-n)',
  accent: 'var(--lc-fill-accent)',
  alert: 'var(--fill-rod-r)',
  result: 'var(--fill-rod-gcd)',
  muted: 'var(--bg-surface-elevated)',
};

/** Shorthand for authors: `tone('primary', 119)` → `\tone{primary}{119}`. */
export function tone(t: Tone, body: string | number): string {
  return `\\tone{${t}}{${body}}`;
}

/** Converts lesson TeX into KaTeX input. Unknown tones are left intact so KaTeX reports them. */
export function prepareTex(tex: string): string {
  return tex.replace(/\\tone\{(primary|secondary|accent|alert|result|muted)\}/g, (_, t: Tone) => `\\htmlClass{${TONE_CLASS[t]}}`);
}

/** KaTeX options used everywhere (renderer and tests). Only \htmlClass is trusted. */
export const KATEX_OPTIONS = {
  throwOnError: true,
  strict: (errorCode: string) => (errorCode === 'htmlExtension' ? 'ignore' : 'error'),
  output: 'htmlAndMathml' as const,
  trust: (ctx: { command: string }) => ctx.command === '\\htmlClass',
};

/** Fills `{key}` placeholders. Missing keys stay visible so tests catch them. */
export function fill(template: string, values: Record<string, unknown>): string {
  return template.replace(/\{([A-Za-z][A-Za-z0-9]*)\}/g, (match, key: string) =>
    Object.hasOwn(values, key) ? String(values[key] ?? '—') : match);
}
