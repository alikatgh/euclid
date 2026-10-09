export interface Preset {
  name: string;
  m: number;
  n: number;
}

export interface StepDefinition {
  id: string;
  name: string;
  description: string;
  rule: string;
  is_optional: boolean;
}

export interface KnuthProse {
  opening: string;
  start_example: string;
  e1_dummy: string;
  e2_noop: string;
  e3_swap: string;
  e0_proposal: string;
  e2_terminate: string;
}

export interface PedagogicalNotes {
  dummy_pass_explanation: string;
  e0_benefit: string;
  geometric_intuition: string;
  invariant_explanation?: string;
  verification_explanation?: string;
}

export interface VisualizationLabels {
  target: string;
  measure: string;
  copies: string;
  oneCopy: string;
  remainder: string;
  dummy: string;
  next: string;
  exact: string;
  verification: string;
  ready: string;
  grouped: string;
  tilingDummy: string;
  tilingNext: string;
  tilingReduction: string;
  rotate: string;
  reassignment: string;
  swapExplanation: string;
  fromStick: string;
  fromRemainder: string;
  fromTarget: string;
  newTarget: string;
  newMeasure: string;
  readyForDivision: string;
  nextPass: string;
  predictedRemainder: string;
  invariant: string;
}

export type CodeLanguage = 'c' | 'python';

export interface CodeLine {
  id: string;
  text: string;
  phase?: 'E0' | 'E1' | 'E2' | 'E3';
  operation?: string;
}

export interface CodeSourceLine extends CodeLine {
  onlyWithE0?: boolean;
}

export interface CodeExplanation {
  title: string;
  explanation: string;
}

export interface CodeLanguageContent {
  lines: CodeSourceLine[];
  explanations: {
    e0Swap: CodeExplanation;
    e0Noop: CodeExplanation;
    e1: CodeExplanation;
    e1Dummy: CodeExplanation;
    e3: CodeExplanation;
    e3Dummy: CodeExplanation;
    e2: CodeExplanation;
  };
}

export interface CodeLessonContent {
  title: string;
  intro: string;
  explanationTabLabel: string;
  continueLabel: string;
  sourceLabel: string;
  executionLabel: string;
  variablesLabel: string;
  beforeAfterLabel: string;
  resultLabel: string;
  copyLabel: string;
  copiedLabel: string;
  copyFailedLabel: string;
  languageLabels: Record<CodeLanguage, string>;
  languages: Record<CodeLanguage, CodeLanguageContent>;
}

export interface CodeProgram {
  lines: CodeLine[];
  source: string;
}

export interface CodeExecution {
  activeLineIds: string[];
  title: string;
  explanation: string;
  variables: Array<{
    name: 'm' | 'n' | 'q' | 'r' | 'temp';
    before: number | null;
    after: number | null;
  }>;
  result: number | null;
}

export interface MathematicalReadingContent {
  title: string;
  currentStepTitle: string;
  sourceNote: string;
  intro: {
    standard: string;
    withE0Swap: string;
    withE0Noop: string;
  };
  division: {
    properFraction: string;
    mixedNumber: string;
    exact: string;
  };
  nextCheck: string;
  e0Swap: string;
  e0Noop: string;
  reduction: string;
  reductionDummy: string;
  workedReduction: string;
  workedReductionDummy: string;
  e0Aside: string;
  termination: string;
  principles: {
    title: string;
    invariant: string;
    termination: string;
  };
}

export interface WorkedExampleChunk {
  id: string;
  text: string;
  /** Conceptual asides have no executing step. */
  stepIndex?: number;
  phase?: AlgorithmStep['phase'];
}

export interface WorkedExampleParagraph {
  id: string;
  startStep: number;
  endStep: number;
  chunks: WorkedExampleChunk[];
  text: string;
}

export interface LessonData {
  application?: {
    name: string;
  };
  algorithm: {
    id: string;
    title: string;
    subtitle: string;
    description: string;
    visualization?: VisualizationLabels;
    codeWalkthrough?: CodeLessonContent;
    mathematicalReading?: MathematicalReadingContent;
    presets: Preset[];
    steps_definition: StepDefinition[];
    knuth_prose: KnuthProse;
    pedagogical_notes: PedagogicalNotes;
  };
}

export type StepType = 'E0_SWAP' | 'E0_NOOP' | 'DIVISION' | 'REDUCE';

export interface TraceRow {
  pass: number;
  phase: 'E0' | 'E1' | 'E2' | 'E3';
  m: number;
  n: number;
  q: number | null;
  r: number | null;
  isDummy?: boolean;
  stepIndex: number;
}

export interface AlgorithmStep {
  type: StepType;
  phase: 'E0' | 'E1' | 'E2' | 'E3';
  activeFlowId: string;
  stepIndex: number;
  pass?: number;
  badge: string;
  initialM: number;
  initialN: number;
  m: number;
  n: number;
  q: number | null;
  r: number | null;
  nextM?: number;
  nextN?: number;
  newM?: number;
  newN?: number;
  isDummy?: boolean;
  equation: string;
  formulaParts: {
    m: string | number;
    q?: string | number;
    n?: string | number;
    r?: string | number;
    text: string;
  };
  explanation: string;
  knuthQuote: string;
  callout: string;
  traceHistory: TraceRow[];
  verification?: {
    factorM: number;
    factorN: number;
    gcd: number;
  };
}
