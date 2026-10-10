---
name: euclid-lesson
description: Author or migrate an interactive lesson in the Euclid codebase adhering to the Donald Knuth Lesson 1 standard.
metadata:
  author: Euclid Team
  version: 1.0.0
---

# Euclid Lesson Authoring Skill

Use this skill when authoring a new lesson or migrating an existing lesson to the Euclid core engine.

## Workflow

### Step 1: Analyze the Topic & Computation
1. Identify the core algorithm or mathematical procedure from Volume 1.
2. Determine the tracked variables (e.g. $m, n, q, r$ or pointer indices, array elements, tree nodes).
3. Identify the input domain and ranges (e.g. integers 1–9999).
4. Formulate the core loop / state machine and write a mathematical invariant that holds across all iterations.

### Step 2: Create the Lesson Module
1. Copy `frontend/src/lessons/_TEMPLATE.ts` to `frontend/src/lessons/<order>-<kebab-id>.ts`.
2. Define the input interface `I` and step interface `S extends TraceStep`.
3. Implement `run(input, variant)`:
   - Ensure loop termination.
   - Emit state snapshots with `values` before step, and `next` after step.
   - Tag the final step with `terminal: true`.
4. Implement `formula(step, ctx)`:
   - Return `compact` (diagram header), `full` (live formula), `reference`, and `invariant`.
   - Wrap numbers in `tone('primary', val)` etc.
5. Implement `diagram(step, ctx)`:
   - Construct clear, intuitive geometry using `rect`, `circle`, `line`, and `text`.
   - Ensure shapes have `value` and semantic `tone`.
6. Implement `narrate(step, ctx)`:
   - Write clear mathematical prose describing the operation.
7. Implement `workedExample`:
   - Write an intro explaining the chosen inputs.
   - Formulate `paragraphs` chunked to match execution steps.
   - State `principles` (invariant preservation and finite termination).
8. Implement `code`:
   - Write valid, idiomatic C and Python implementations.
   - Map each step to executed line IDs via `activeLines`.
   - Provide an explanation of the line and track variable values.
9. Implement `trace`:
   - Declare columns and table rows for each pass.
10. Implement `help`:
   - Create a separate, smaller instance with ≥ 2 frames.
   - Write a transfer question with 1 correct option and informative feedbacks.

### Step 3: Register and Validate
1. Add the lesson to `frontend/src/lesson-core/registry.ts`.
2. Add a test in `frontend/src/lib/lessonCore.test.mjs` verifying `validateLessonSpec(myLesson)` has zero errors.
3. Run the validation pipeline:
   ```bash
   cd frontend
   npm test
   npm run build
   npm run lint
   ```
4. If any contract violation is reported, resolve it immediately.
