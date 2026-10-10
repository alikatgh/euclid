# Euclid Lesson Standards & Engine Rules

This rule defines the core architectural and pedagogical constraints for creating lessons in Euclid.

## Architectural Constraints
1. **Single Source of Truth**: The TypeScript file in `frontend/src/lessons/` implementing `LessonSpec<Input, Step>` is the sole definition of a lesson.
2. **No Custom DOM or CSS**: All presentation is handled by `LessonWorkbench.tsx` and the styling in `frontend/public/assets/original.css`.
3. **Purity**:
   - `run()` must be pure and deterministic. Given identical inputs and variant, it must produce identical step arrays.
   - Diagram rendering functions must return JSON-serializable `DiagramScene` objects, never mutated DOM elements or direct D3 selections.
4. **Accessible Semantics**:
   - Every diagram must have a descriptive label.
   - Shapes representing mathematical quantities must include `value: number` so numbers are linked across panels.
   - Text elements in diagrams must have valid coordinates and readable contrast.

## Pedagogical Constraints
1. **Explain Every Step**:
   - The user must never be left wondering what happened between step $i$ and step $i+1$.
   - Formulas must show the transition from old to new values (e.g. $m \leftarrow n, n \leftarrow r$).
2. **Both C and Python Walkthroughs**:
   - Code must be idiomatic, complete, and compile/run cleanly.
   - Every step must highlight the specific source line(s) causing the transition.
   - Variable inspection must report exact values before and after the step.
3. **Independent Smaller Help**:
   - The "I still don’t understand" section must NEVER simply replay the main example with smaller font.
   - It must instantiate its own independent miniature problem (e.g. $m=14, n=6$ for Algorithm E) with a dedicated comprehension check question.

## Verification Checklist for Agents
Before submitting any lesson:
1. `validateLessonSpec(myLesson, { renderTex: ... })` returns 0 errors.
2. `npm test` passes all tests.
3. `npm run build` succeeds without type errors.
4. `npm run lint` passes without errors.
