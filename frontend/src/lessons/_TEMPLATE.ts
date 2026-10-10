/**
 * Euclid Lesson Template
 *
 * Copy this file to create a new lesson:
 *   cp frontend/src/lessons/_TEMPLATE.ts frontend/src/lessons/002-my-lesson.ts
 *
 * All fields are required by the automated contract gate (contract.ts).
 * See frontend/src/lessons/001-algorithm-e.ts for the reference implementation.
 */
import type {
  DiagramNode,
  DiagramScene,
  FormulaSet,
  LessonSpec,
  StepContext,
  TraceRow,
  TraceStep,
  WorkedParagraph,
} from '../lesson-core/types.ts';
import { tone } from '../lesson-core/tex.ts';

// 1. Define learner input parameters
export interface MyLessonInput {
  [key: string]: number;
  x: number;
  y: number;
}

// 2. Define execution step state
export interface MyLessonStep extends TraceStep {
  phase: 'START' | 'LOOP' | 'END';
  badge: string;
  values: {
    x: number;
    y: number;
    result: number | null;
  };
  next?: {
    x: number;
    y: number;
    result: number | null;
  };
  terminal?: boolean;
}

export const myLesson: LessonSpec<MyLessonInput, MyLessonStep> = {
  id: 'my-lesson-id', // kebab-case, unique
  order: 2,           // positive integer, unique
  navigationLabel: 'Lesson 2 · My Lesson Title',
  title: 'My Lesson Title',
  subtitle: 'Donald Knuth, The Art of Computer Programming, Vol. 1, §1.1',
  source: {
    book: 'The Art of Computer Programming, Vol. 1',
    section: '§1.1',
  },

  // Tracked variables
  variables: [
    { key: 'x', symbol: 'x', tone: 'primary', meaning: 'The primary input parameter.' },
    { key: 'y', symbol: 'y', tone: 'secondary', meaning: 'The secondary parameter or counter.' },
    { key: 'result', symbol: 'R', tone: 'result', meaning: 'The computed result or output value.' },
  ],

  // User input controls
  inputs: [
    { key: 'x', label: 'x', min: 1, max: 100 },
    { key: 'y', label: 'y', min: 1, max: 100 },
  ],

  defaultInput: { x: 10, y: 5 },

  // Presets (minimum 3: typical, edge, non-trivial)
  presets: [
    { name: '10 & 5 (Typical)', input: { x: 10, y: 5 } },
    { name: '1 & 1 (Boundary)', input: { x: 1, y: 1 } },
    { name: '42 & 17 (Coprime)', input: { x: 42, y: 17 } },
  ],

  // Variants (algorithm modes or optimizations)
  variants: [
    { id: 'standard', label: 'Standard' },
  ],

  // Visual views
  views: [
    { id: 'main', label: 'Visual' },
  ],

  // Algorithm instructions
  stepDefinitions: [
    { id: 'START', name: 'Initialize', description: 'Set up variables and establish the initial state.' },
    { id: 'LOOP', name: 'Iterate', description: 'Perform the core transition step.' },
    { id: 'END', name: 'Terminate', description: 'Return the final output when the stopping condition holds.' },
  ],

  maxSteps: 50,

  // Pure deterministic state machine
  run(input: MyLessonInput, _variant: string): MyLessonStep[] {
    const steps: MyLessonStep[] = [];
    let curX = input.x;
    let curY = input.y;

    steps.push({
      phase: 'START',
      badge: 'Step 1: Initialize',
      values: { x: curX, y: curY, result: null },
      next: { x: curX, y: curY, result: curX + curY },
    });

    steps.push({
      phase: 'LOOP',
      badge: 'Step 2: Compute',
      values: { x: curX, y: curY, result: curX + curY },
    });

    steps.push({
      phase: 'END',
      badge: 'Step 3: Termination',
      values: { x: curX, y: curY, result: curX + curY },
      terminal: true,
    });

    return steps;
  },

  // Mathematical formulas per step
  formula(step: MyLessonStep, _ctx: StepContext<MyLessonInput, MyLessonStep>): FormulaSet {
    const { x, y, result } = step.values;
    return {
      compact: `${tone('primary', x)} + ${tone('secondary', y)} = ${tone('result', result ?? '?')}`,
      full: `${tone('primary', x)} + ${tone('secondary', y)} = ${tone('result', result ?? '?')}`,
      reference: { label: 'KNUTH §1.1', tex: `x + y = R` },
      invariant: `R \\ge \\min(x, y)`,
    };
  },

  // Semantic diagram scene per step
  diagram(step: MyLessonStep, _ctx: StepContext<MyLessonInput, MyLessonStep> & { view: string }): DiagramScene {
    const { x, y } = step.values;
    const nodes: DiagramNode[] = [
      { id: 'box-x', type: 'rect', x: 50, y: 50, width: Math.max(10, x * 4), height: 40, tone: 'primary', value: x },
      { id: 'box-y', type: 'rect', x: 50, y: 120, width: Math.max(10, y * 4), height: 40, tone: 'secondary', value: y },
      { id: 'lbl-x', type: 'text', x: 50, y: 40, text: `Parameter x = ${x}`, tone: 'primary', weight: 'bold' },
      { id: 'lbl-y', type: 'text', x: 50, y: 110, text: `Parameter y = ${y}`, tone: 'secondary', weight: 'bold' },
    ];

    return {
      width: 600,
      height: 400,
      nodes,
      description: `Diagram showing x=${x} and y=${y}.`,
    };
  },

  // "What is happening" explanation
  narrate(step: MyLessonStep, _ctx: StepContext<MyLessonInput, MyLessonStep>): string {
    return `At step ${step.badge}, parameter $x = ${step.values.x}$ and $y = ${step.values.y}$ combine to produce result $R = ${step.values.result ?? 'pending'}$.`;
  },

  // Worked example & principles
  workedExample: {
    title: 'Worked example',
    sourceNote: 'Following The Art of Computer Programming, Vol. 1, §1.1.',
    intro(input: MyLessonInput, _variant: string): string {
      return `To illustrate the process, consider $x = ${input.x}$ and $y = ${input.y}$. We observe each state transition step by step.`;
    },
    paragraphs(steps: readonly MyLessonStep[], _input: MyLessonInput, _variant: string): WorkedParagraph[] {
      return steps.map((s, idx) => ({
        chunks: [
          { stepIndex: idx, text: `In step ${s.badge}, state has $x = ${s.values.x}$ and $y = ${s.values.y}$.` },
        ],
      }));
    },
    principles: {
      title: 'Why the calculation works',
      paragraphs: [
        'The relation $R \\ge \\min(x, y)$ is preserved across all states of the procedure.',
        'The loop makes strict progress each step and terminates when the base case is reached in finite time.',
      ],
    },
  },

  // Code walkthrough in C and Python
  code: {
    title: 'Procedure in code',
    intro: 'Follow the highlighted instructions as the program steps execute.',
    languages: {
      c: {
        label: 'C',
        lines: [
          { id: 'c-include', text: '#include <stdio.h>' },
          { id: 'c-main', text: 'int compute(int x, int y) {' },
          { id: 'c-step1', text: '    int r = x + y;', phase: 'START' },
          { id: 'c-ret', text: '    return r;', phase: 'END' },
          { id: 'c-end', text: '}' },
        ],
        activeLines(step: MyLessonStep): string[] {
          return step.phase === 'END' ? ['c-ret'] : ['c-step1'];
        },
        explain(step: MyLessonStep, _ctx: StepContext<MyLessonInput, MyLessonStep>): { title: string; explanation: string } {
          return {
            title: step.badge,
            explanation: `Instruction computes with x = ${step.values.x} and y = ${step.values.y}.`,
          };
        },
      },

      python: {
        label: 'Python',
        lines: [
          { id: 'py-def', text: 'def compute(x, y):' },
          { id: 'py-add', text: '    r = x + y', phase: 'START' },
          { id: 'py-ret', text: '    return r', phase: 'END' },
        ],
        activeLines(step: MyLessonStep): string[] {
          return step.phase === 'END' ? ['py-ret'] : ['py-add'];
        },
        explain(step: MyLessonStep, _ctx: StepContext<MyLessonInput, MyLessonStep>): { title: string; explanation: string } {
          return {
            title: step.badge,
            explanation: `Python evaluation with x = ${step.values.x} and y = ${step.values.y}.`,
          };
        },
      },
    },
  },

  // Trace table
  trace: {
    title: 'Computation Trace Table',
    caption: 'State Matrix',
    columns: [
      { key: 'step', label: 'Step', tone: 'muted' },
      { key: 'x', label: 'x', tone: 'primary' },
      { key: 'y', label: 'y', tone: 'secondary' },
      { key: 'result', label: 'Result', tone: 'result' },
    ],
    rows(steps: readonly MyLessonStep[], activeIndex: number): TraceRow[] {
      return steps.slice(0, activeIndex + 1).map((s, idx) => ({
        stepIndex: idx,
        label: s.badge,
        cells: {
          step: s.badge,
          x: s.values.x,
          y: s.values.y,
          result: s.values.result ?? '—',
        },
      }));
    },
  },

  // Smaller worked example for "I still don't understand"
  help: {
    title: 'Smaller worked example · original run paused',
    frames: [
      {
        explanation: 'Consider small values: $x = 2$ and $y = 3$.',
        diagram: {
          width: 400,
          height: 200,
          description: 'Small example with 2 and 3.',
          nodes: [
            { id: 'help-x', type: 'rect', x: 40, y: 40, width: 60, height: 30, tone: 'primary', value: 2 },
            { id: 'help-y', type: 'rect', x: 40, y: 90, width: 90, height: 30, tone: 'secondary', value: 3 },
          ],
        },
      },
      {
        explanation: 'Combining them yields $2 + 3 = 5$.',
        diagram: {
          width: 400,
          height: 200,
          description: 'Combined result 5.',
          nodes: [
            { id: 'help-res', type: 'rect', x: 40, y: 60, width: 150, height: 30, tone: 'result', value: 5 },
          ],
        },
      },
    ],
    check: {
      prompt: 'If $x = 4$ and $y = 2$, what is the combined value?',
      options: [
        { id: 'c6', text: '6', correct: true, feedback: 'Correct! $4 + 2 = 6$.' },
        { id: 'c8', text: '8', correct: false, feedback: 'Eight would be the product $4 \\times 2$, not the sum.' },
      ],
    },
  },
};
