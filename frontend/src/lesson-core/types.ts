/**
 * Lesson Core contract.
 *
 * Every lesson in Euclid is a `LessonSpec`: plain data plus pure functions.
 * The `LessonWorkbench` component owns ALL layout, styling, playback,
 * keyboard handling and accessibility. A lesson can never ship its own
 * component, CSS or layout; that is how every lesson gets the Lesson 1
 * (Algorithm E) experience.
 *
 * Every field below is REQUIRED unless marked optional. `validateLessonSpec`
 * (contract.ts) and `npm test` enforce the rules written in the comments.
 * Reference implementation: lessons/algorithm-e.ts
 */

/** Semantic colour slots. They map to the original Euclid palette (CSS vars). */
export type Tone = 'primary' | 'secondary' | 'accent' | 'alert' | 'result' | 'muted';

/** A tracked quantity (m, n, q, r ...). Shown in Live Formula, code variables and trace. */
export interface VariableDef {
  /** Key used in `TraceStep.values`. */
  key: string;
  /** Plain-text symbol shown in the UI, e.g. "m". */
  symbol: string;
  tone: Tone;
  /** One-sentence meaning, used for tooltips and screen readers. */
  meaning: string;
}

/** A numeric input the learner can change (Inputs & Presets panel). */
export interface InputField {
  key: string;
  /** Short label shown before the field, e.g. "m". */
  label: string;
  min: number;
  max: number;
}

export type LessonInput = Record<string, number>;

export interface Preset<I extends LessonInput> {
  /** Name shown on the preset button; say WHY it is interesting, e.g. "35 & 64 (Coprime, GCD=1)". */
  name: string;
  input: I;
}

/** One instruction of the algorithm/procedure (the "Knuth's Algorithm Steps" panel). */
export interface StepDefinition {
  /** Short id shown in the badge, e.g. "E1". Every `TraceStep.phase` must be one of these. */
  id: string;
  name: string;
  /** May contain inline TeX in $...$. */
  description: string;
  /** Optional steps are dimmed unless a variant enables them. */
  optional?: boolean;
  /** Variant ids in which this optional step is active. */
  enabledIn?: string[];
}

/** A variant of the procedure (sidebar "Algorithm:" switch). At least one. */
export interface VariantDef {
  id: string;
  label: string;
}

/** A visual representation of the same state (e.g. "Tape" / "2D Tiling"). At least one. */
export interface ViewDef {
  id: string;
  label: string;
}

/** One frame of execution produced by `run`. */
export interface TraceStep {
  /** Must equal a `StepDefinition.id`. */
  phase: string;
  /** Loop iteration (1-based). Omit for one-off steps. */
  pass?: number;
  /** Diagram panel heading, e.g. "Pass 1 (Step E1): Find Remainder". */
  badge: string;
  /** Values BEFORE the step, keyed by `VariableDef.key`. `null` = not assigned yet. */
  values: Record<string, number | null>;
  /** Values AFTER the step. Omit when nothing changes. */
  next?: Record<string, number | null>;
  /** True only on the final step. Exactly one terminal step per run. */
  terminal?: boolean;
}

export interface StepContext<I extends LessonInput, S extends TraceStep> {
  input: I;
  variant: string;
  steps: readonly S[];
  index: number;
}

/* ---------------------------------------------------------------- Diagram */

interface NodeBase {
  /** Stable id: the same object keeps the same id across frames. */
  id: string;
  tone?: Tone;
  opacity?: number;
  /** Entrance animation. Respects prefers-reduced-motion automatically. */
  animate?: 'grow' | 'fade' | 'draw' | 'none';
  /** Value this shape stands for. Links it to matching numbers elsewhere. */
  value?: number;
  /** Accessible description for this shape. */
  title?: string;
}
export interface RectNode extends NodeBase { type: 'rect'; x: number; y: number; width: number; height: number; outline?: boolean; dashed?: boolean }
export interface LineNode extends NodeBase { type: 'line'; x: number; y: number; x2: number; y2: number; dashed?: boolean; arrow?: boolean }
export interface CircleNode extends NodeBase { type: 'circle'; x: number; y: number; r: number; outline?: boolean }
export interface PathNode extends NodeBase { type: 'path'; d: string; dashed?: boolean; arrow?: boolean }
/** Plain text, or inline TeX when wrapped in $...$. */
export interface TextNode extends NodeBase { type: 'text'; x: number; y: number; text: string; size?: 'sm' | 'md' | 'lg'; anchor?: 'start' | 'middle' | 'end'; weight?: 'normal' | 'bold' }
export type DiagramNode = RectNode | LineNode | CircleNode | PathNode | TextNode;

export interface DiagramScene {
  /** Logical drawing size; the engine scales it to fit the panel. */
  width: number;
  height: number;
  nodes: DiagramNode[];
  /** One sentence describing the whole scene for screen readers. */
  description: string;
}

/* ---------------------------------------------------------------- Panels */

export interface FormulaSet {
  /** TeX for the diagram header (short). */
  compact: string;
  /** TeX for the main Live Formula line. */
  full: string;
  /** Optional reference line, e.g. Knuth's notation. */
  reference?: { label: string; tex: string };
  /** TeX for the invariant that holds at this step. */
  invariant: string;
}

export interface WorkedParagraph {
  /** Each chunk is linked to one step; the active step's chunk is highlighted. */
  chunks: { stepIndex: number; text: string }[];
}

export interface CodeLine {
  id: string;
  text: string;
  /** Step id shown in the gutter. */
  phase?: string;
  /** Only shown in these variants. */
  variants?: string[];
}

export interface CodeListing<I extends LessonInput = LessonInput, S extends TraceStep = TraceStep> {
  /** Tab label, e.g. "C". */
  label: string;
  /** `{inputKey}` placeholders are replaced with the current input values. */
  lines: CodeLine[];
  /** Line ids executed by this step. Must be non-empty and visible in the current variant. */
  activeLines(step: S, ctx: StepContext<I, S>): string[];
  /** Explanation under the code for this step (TeX in $...$ allowed). */
  explain(step: S, ctx: StepContext<I, S>): { title: string; explanation: string };
}

export interface CheckQuestion {
  prompt: string;
  options: { id: string; text: string; correct: boolean; feedback: string }[];
}

export interface HelpFrame {
  explanation: string;
  diagram: DiagramScene;
}

export interface TraceColumn {
  key: string;
  label: string;
  tone?: Tone;
}

export interface TraceRow {
  /** The step this row jumps to when clicked. */
  stepIndex: number;
  label: string;
  cells: Record<string, number | string | null>;
}

/* ---------------------------------------------------------------- Spec */

export interface LessonSpec<I extends LessonInput = LessonInput, S extends TraceStep = TraceStep> {
  /** URL-safe, unique. Becomes the hash route. */
  id: string;
  /** Position in the course (1-based, unique). */
  order: number;
  /** Sidebar label, e.g. "Lesson 1 · Algorithm E". */
  navigationLabel: string;
  title: string;
  /** Source line, e.g. "Donald Knuth, The Art of Computer Programming, Vol. 1, §1.1". */
  subtitle: string;
  source: { book: string; section: string };

  variables: VariableDef[];
  inputs: InputField[];
  defaultInput: I;
  /** At least 3. Cover the typical case, an edge case and a large case. */
  presets: Preset<I>[];
  variants: VariantDef[];
  views: ViewDef[];
  stepDefinitions: StepDefinition[];

  /** Pure and deterministic. Must terminate within `maxSteps` for every valid input. */
  run(input: I, variant: string): S[];
  maxSteps: number;

  formula(step: S, ctx: StepContext<I, S>): FormulaSet;
  diagram(step: S, ctx: StepContext<I, S> & { view: string }): DiagramScene;
  /** "What is happening" text for this step (TeX in $...$ allowed). */
  narrate(step: S, ctx: StepContext<I, S>): string;

  workedExample: {
    title: string;
    sourceNote: string;
    intro(input: I, variant: string): string;
    paragraphs(steps: readonly S[], input: I, variant: string): WorkedParagraph[];
    principles: { title: string; paragraphs: string[] };
  };

  code: {
    title: string;
    intro: string;
    /** Exactly C and Python, like Lesson 1. */
    languages: { c: CodeListing<I, S>; python: CodeListing<I, S> };
  };

  trace: {
    title: string;
    caption: string;
    columns: TraceColumn[];
    rows(steps: readonly S[], index: number): TraceRow[];
  };

  /** "I still don't understand": its OWN smaller example, not a replay of the main run. */
  help: {
    title: string;
    frames: HelpFrame[];
    check: CheckQuestion;
  };
}
