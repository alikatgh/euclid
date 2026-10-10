# Euclid Course Migration Specification (Lessons 2–144)

> **Instructions for the AI Agent executing this migration**:
> You are tasked with converting legacy lessons in the Euclid repository (`content/first20/` and `content/fullbook/`) into typed `LessonSpec` modules adhering to the **Lesson 1: Algorithm E** standard.
>
> Follow this document systematically for every lesson you migrate.

---

## 1. Context & Objective

In Euclid, Lesson 1 (`frontend/src/lessons/001-algorithm-e.ts`) is a rich interactive workbench featuring:
1. Interactive input parameters & presets.
2. A pure, deterministic state machine (`run(input, variant)`).
3. A live formula with semantic coloring and mathematical invariants.
4. An SVG diagram scene with styled primitives and value binding.
5. "What is happening" step-by-step narrative.
6. A worked example with chunked text linked to execution steps.
7. Rigorous mathematical principles (invariants & termination).
8. Interactive code walkthroughs in **both C and Python**.
9. A state trace table with row-seeking.
10. A dedicated "I still don’t understand" smaller example and assessment question.

Legacy lessons 2–144 were authored primarily as passages with precomputed animation snapshots. Your mission is to elevate each lesson into a fully interactive `LessonSpec` module without discarding any existing mathematical rigor or pedagogical content.

---

## 2. File Location & Naming Conventions

- Every migrated lesson must be created in:
  `frontend/src/lessons/<padded-order>-<kebab-id>.ts`
  *Example*: `frontend/src/lessons/002-what-makes-an-algorithm.ts`
- The template to copy is:
  `frontend/src/lessons/_TEMPLATE.ts`
- Reference standard to emulate:
  `frontend/src/lessons/001-algorithm-e.ts`

---

## 3. Step-by-Step Conversion Procedure

For each lesson $L$ from order 2 to 144:

### Step 3.1: Locate Existing Content
1. Search for the lesson ID or order in:
   - `content/first20/lessons4-10.json` (Lessons 4–10)
   - `content/first20/lessons11-20.json` (Lessons 11–20)
   - `content/fullbook/batch-*.json` (Lessons 21–144)
   - `content/deployed-original.json` (Lessons 2 & 3: `algorithmFeatures` and `computationalMethods`)
2. Read the source book section, title, scope, passages, and formulas.

### Step 3.2: Formalize the Computational State Machine
1. **Inputs (`inputs`, `defaultInput`, `presets`)**:
   - Determine what the learner can vary (e.g. initial counter $n$, array length $k$, seed, base).
   - Set sensible bounds (`min` and `max`).
   - Create at least 3 curated presets representing typical, boundary, and non-trivial scenarios.
2. **State Machine (`run(input, variant)`)**:
   - Write a deterministic TypeScript function `run()` that steps through the computation.
   - Each state snapshot must record variable values before (`values`) and after (`next`).
   - Tag the final terminating state with `terminal: true`.
   - Ensure the loop terminates within `maxSteps`.

### Step 3.3: Visual Diagram & Formulas
1. **Diagram (`diagram(step, ctx)`)**:
   - Translate the existing diagram shapes/nodes into a `DiagramScene`.
   - Use standard nodes: `rect`, `circle`, `line`, `path`, `text`.
   - Tag quantities with `value` and semantic tones (`primary`, `secondary`, `accent`, `alert`, `result`, `muted`).
2. **Formulas (`formula(step, ctx)`)**:
   - Return `{ compact, full, reference, invariant }`.
   - Use `tone('primary', val)` to color key quantities.
   - Always formulate an invariant relation that holds during the computation.

### Step 3.4: Code Walkthrough (C and Python)
1. Write a complete, syntactically valid C program implementing the algorithm.
2. Write a complete Python implementation.
3. Map each step in `run()` to the executed line IDs using `activeLines(step, ctx)`.
4. Provide step-by-step code explanation with variable changes (`before → after`).

### Step 3.5: Narrative, Worked Example, and Smaller Help
1. **Narrative (`narrate`)**:
   - Explain the current transition in clear mathematical prose with inline TeX ($...$).
2. **Worked Example (`workedExample`)**:
   - Adapt the original textbook passages into `paragraphs` chunked to the execution steps.
   - Preserve the original `principles` (invariant & termination).
3. **Smaller Example (`help`)**:
   - Extract or author a miniature version of the problem (at least 2 frames).
   - Include the transfer assessment question (`check`) with 1 correct answer and clear explanatory feedbacks for all options.

### Step 3.6: Register & Validate
1. Add the exported spec to `frontend/src/lesson-core/registry.ts`.
2. Add a test in `frontend/src/lib/lessonCore.test.mjs` verifying the lesson satisfies the contract.
3. Run:
   ```bash
   cd frontend
   npm test
   npm run build
   npm run lint
   ```
4. Verify there are **0 errors** and **0 contract violations**.

---

## 4. Quality Checklist

Every lesson will be rejected by the automated test suite if any of the following occur:
- ❌ Missing any of the 10 required fields.
- ❌ Fewer than 3 presets.
- ❌ Missing C or Python code listing.
- ❌ Non-terminating `run()` or missing `terminal: true` flag.
- ❌ Invalid LaTeX syntax in any formula or prose.
- ❌ Placeholders like `TODO`, `FIXME`, `TBD`, or `lorem ipsum`.
- ❌ Diagram nodes with negative dimensions, NaN coordinates, or duplicate IDs.
- ❌ Assessment questions with duplicate options or missing feedbacks.
