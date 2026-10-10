/** Original, executable lessons. Every rendered quantity comes from a lesson's model. */
export interface LessonParameter {
  id: string;
  label: string;
  min: number;
  max: number;
  initial: number;
  step?: number;
  description: string;
}
export type LessonInputs = Record<string, number>;
export interface LessonSource {
  title: string;
  section: string;
  note: string;
  url?: string;
}
export interface LessonVariable {
  symbol: string;
  value: number | string;
  meaning: string;
  previous?: number | string;
}
export interface LessonCounter {
  label: string;
  value: number;
  unit: string;
}
export interface Prediction {
  prompt: string;
  hint?: string;
  choices: string[];
  correctIndex: number;
  explanation: string;
}
export interface SceneNode {
  id: string;
  label: string;
  value?: number;
  /** Normalized coordinates from 0 to 1. */
  x: number;
  y: number;
  active?: boolean;
}
export type LessonScene =
  | { kind: 'division'; m: number; n: number; q: number; r: number; highlight?: 'quotient' | 'remainder' | 'divisor' }
  | { kind: 'registers'; registers: LessonVariable[]; arrows: { from: string; to: string; label?: string }[]; note?: string }
  // Explicit cells: only listed cells are occupied; without cells, fill the rectangle.
  | { kind: 'grid'; rows: number; columns: number; cells?: { row: number; column: number; value?: number; label?: string; group?: number; active?: boolean }[]; caption: string; rowLabels?: string[]; columnLabels?: string[] }
  | { kind: 'number-line'; min: number; max: number; points: { value: number; label: string; active?: boolean }[]; jumps?: { from: number; to: number; label?: string }[]; logarithmic?: boolean; caption: string }
  // active is a zero-based focused step index; -1 means none. base labels first step (default 1).
  | { kind: 'staircase'; count: number; active: number; base?: number; values?: number[]; caption: string; labels?: string[] }
  | { kind: 'graph'; nodes: SceneNode[]; edges: { from: string; to: string; label?: string; active?: boolean }[]; caption: string; directed?: boolean }
  // Each term contributes (coefficient ?? 1) * value; unequal sides are allowed.
  | { kind: 'balance'; left: { label: string; value: number; coefficient?: number; exactValue?: string }[]; right: { label: string; value: number; coefficient?: number; exactValue?: string }[]; caption: string }
  // stages carry exact values; base/exponent describe the current exponential stage.
  | { kind: 'growth'; base: number; exponent: number; stages: { label: string; value: number; active?: boolean }[]; caption: string }
  // active is a zero-based current term index, -1 means no terms accumulated. total includes active.
  | { kind: 'accumulation'; terms: number[]; active: number; total: number; operation: 'sum' | 'product'; indexStart?: number; caption: string };

export interface LessonFrame {
  id: string;
  title: string;
  /** Plain-language physical intuition, with optional $inline TeX$. */
  intuition: string;
  /** Rigorous text, including assumptions, bounds, or proof obligations. */
  formal: string;
  /** TeX without dollar delimiters; rendered using linked KaTeX. */
  formula: string;
  /** General theorems/quantified statements must not borrow a worked example's live variable bindings. */
  formulaBinding?: 'state' | 'none';
  /** Explain how to read the notation aloud and what its symbols mean. */
  reading: string;
  variables: LessonVariable[];
  scene: LessonScene;
  /** activeLines are 1-based source line numbers. */
  code: { language: 'python' | 'text'; lines: string[]; activeLines: number[] };
  counters?: LessonCounter[];
  prediction?: Prediction;
}
export interface CurriculumLesson {
  id: string;
  order: number;
  title: string;
  subtitle: string;
  /** Section references locate the concepts, not copied book passages. */
  sources: LessonSource[];
  prerequisites: string[];
  objectives: string[];
  parameters: LessonParameter[];
  buildFrames: (inputs: LessonInputs) => LessonFrame[];
  /** Explain exactly what is counted; do not count animation frames as operations. */
  countingNote?: string;
}
