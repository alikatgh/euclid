# AGENTS.md — Euclid Lesson Standards & Agent Protocol

This file defines the mandatory architecture, coding rules, and quality gates for any AI agent (ChatGPT, Claude, Gemini, Codex, etc.) working on the **Euclid** codebase.

---

## 1. Absolute Rule: The Lesson 1 Standard

Every lesson in Euclid must deliver the exact depth, interactivity, and visual craftsmanship established by **Lesson 1: Algorithm E** (`frontend/src/lessons/001-algorithm-e.ts`).

### ⛔ Hard Prohibitions
1. **NO custom page layouts or ad-hoc components**: You MUST NEVER create custom React layout containers, custom CSS stylesheets, or one-off lesson components. The `LessonWorkbench` component owns 100% of the UI, layout, typography, controls, and accessibility.
2. **NO incomplete lessons**: A lesson is NEVER just static prose or a basic SVG. Every lesson MUST contain all 10 required dimensions:
   - Interactive Inputs & Presets (minimum 3 presets).
   - Pure, deterministic, terminating execution state engine (`run(input, variant)`).
   - Live Formula (compact, full, reference, and invariant) with semantic TeX coloring.
   - Scaled semantic SVG diagram scene with accessible roles and labels.
   - "What is happening" step-by-step narrative.
   - Worked example with paragraphs chunked and mapped 1-to-1 to execution steps.
   - Deep mathematical principles (invariant and termination arguments).
   - Full runnable code walkthroughs in **both C and Python**, with step-to-line highlighting and variable before/after tracking.
   - Multi-column trace table with click-to-seek row jumps.
   - "I still don’t understand" smaller worked example with its own independent miniature model and transfer assessment question.
3. **NO placeholder tokens**: `TODO`, `FIXME`, `TBD`, `lorem ipsum`, or unassigned variables are strictly banned. The automated contract gate will immediately fail any lesson containing them.

---

## 2. Architecture: Pure Data + Pure Functions (`LessonSpec`)

Lessons are authored as TypeScript modules implementing `LessonSpec<Input, Step>`:
```ts
import type { LessonSpec } from '../lesson-core/types.ts';

export const myLesson: LessonSpec<MyInput, MyStep> = {
  id: 'my-lesson-id',
  order: 4,
  navigationLabel: 'Lesson 4 · Assignment changes state',
  title: 'Assignment changes state',
  subtitle: 'Donald Knuth, The Art of Computer Programming, Vol. 1, §1.1',
  source: { book: 'The Art of Computer Programming, Vol. 1', section: '§1.1' },
  // ... all 10 required fields
};
```

### Where files live:
- Types & Engine: `frontend/src/lesson-core/`
  - `types.ts`: The definitive type contract.
  - `contract.ts`: The automated validation and fuzzing engine.
  - `tex.ts`: Semantic TeX coloring and KaTeX configuration.
  - `LessonWorkbench.tsx`: The canonical 3-column UI workbench.
  - `registry.ts`: The core registry list.
- Lessons: `frontend/src/lessons/`
  - `001-algorithm-e.ts`: Reference gold standard.
  - `_TEMPLATE.ts`: Copy-paste template for new lessons.
- Automated tests: `frontend/src/lib/lessonCore.test.mjs`

---

## 3. The 10 Required Lesson Dimensions

### 1. Variables & Semantic Palette
Declare all tracked variables using semantic tones:
- `primary`: Target / main quantity (e.g. `m`).
- `secondary`: Measure / divisor (e.g. `n`).
- `accent`: Multiplier / quotient / index (e.g. `q`).
- `alert`: Remainder / active change (e.g. `r`).
- `result`: Final answer / GCD.
- `muted`: Auxiliary or static values.

### 2. Inputs & Presets
- At least 1 numeric input with sensible integer `min` and `max`.
- At least 3 presets:
  1. Canonical/typical textbook example.
  2. Edge case (e.g. coprime, zero, boundary condition).
  3. Non-trivial or large case.

### 3. Runnable State Engine (`run`)
- Must be a pure function: `run(input: I, variant: string): S[]`.
- Must terminate within `maxSteps` (typically ≤ 100).
- Must emit at least 2 steps, with exactly one terminal step marked `terminal: true` at the very end.
- Every step must have a unique descriptive `badge` (e.g. `"Pass 1 (Step E1): Find Remainder"`).

### 4. Mathematical Formulas
Return a `FormulaSet` for every step:
- `compact`: TeX for the diagram pane header.
- `full`: TeX for the main Live Formula line.
- `reference`: (Optional) Citation to textbook formula/equation.
- `invariant`: Mathematical relation conserved across the entire calculation.
*Use `tone('primary', val)` to apply palette colors cleanly.*

### 5. SVG Diagram Scene
Return a `DiagramScene`: `{ width, height, nodes, description }`.
- Nodes use standard primitives: `rect`, `circle`, `line`, `path`, `text`.
- Every node must have a stable unique `id`, finite coordinates, and valid dimensions.
- Use `tone` and `value` on shapes so numbers connect interactively.

### 6. "What is happening" Narrative
- Concrete, plain-English explanation of what changed in the current step, with inline TeX ($...$) for symbols.

### 7. Worked Example & Principles
- `intro(input, variant)`: Contextual setup explaining initial parameters.
- `paragraphs(steps, input, variant)`: Step-linked chunks where the active step is highlighted as the user steps through playback.
- `principles`: Rigorous mathematical proof of why the algorithm works (invariant preservation + termination argument).

### 8. Code Walkthrough (C & Python)
- Full, valid programs in both C and Python.
- `activeLines(step, ctx)`: Returns line IDs executed during this step.
- `explain(step, ctx)`: Step explanation with variable before → after tracking.

### 9. Trace Table
- Declares table columns matching key state variables.
- `rows(steps, activeIndex)`: Emits rows for passes completed so far. Clicking any row seeks to that step.

### 10. "I Still Don't Understand" (Smaller Example + Check)
- A separate, smaller pedagogical model with at least 2 visual frames.
- A multiple-choice transfer question with:
  - 1 correct option and ≥ 1 plausible distractors.
  - Detailed feedback for every option explaining *why* it is right or wrong.

---

## 4. Verification Gate: Definition of Done

Before declaring any work complete or pushing:
```bash
# 1. Run all unit and contract tests (including LessonSpec contract validation):
npm test

# 2. Verify TypeScript types and production build:
npm run build

# 3. Verify zero lint errors:
npm run lint
```
Every single check MUST pass. If any contract error or warning is reported, fix it immediately.

---

## 5. Converting Lessons 2–144

When assigned to convert legacy lessons from `content/first20/` or `content/fullbook/`:
1. Read `docs/LESSON-CONVERSION-SPEC.md`.
2. Inspect the source passage, formulas, and existing verification states in `content/`.
3. Extract the underlying executable algorithm/computation into a typed `run()` function.
4. Provide C and Python reference code.
5. Populate all 10 fields according to `_TEMPLATE.ts`.
6. Register the lesson in `frontend/src/lesson-core/registry.ts`.
7. Run `npm test` to verify the automated contract passes 100%.
