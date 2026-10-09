import type {
  AlgorithmStep,
  MathematicalReadingContent,
  WorkedExampleChunk,
  WorkedExampleParagraph,
} from '../types';

export type { MathematicalReadingContent, WorkedExampleChunk, WorkedExampleParagraph } from '../types';

function fillTemplate(template: string, values: Record<string, number>): string {
  return template.replace(/\{([A-Za-z][A-Za-z0-9]*)\}/g, (placeholder, key: string) => (
    Object.hasOwn(values, key) ? String(values[key]) : placeholder
  ));
}

function stepValues(step: AlgorithmStep): Record<string, number> {
  return {
    initialM: step.initialM,
    initialN: step.initialN,
    m: step.m,
    n: step.n,
    q: step.q ?? Math.floor(step.m / step.n),
    r: step.r ?? step.m % step.n,
    nextM: step.newM ?? step.nextM ?? step.m,
    nextN: step.newN ?? step.nextN ?? step.n,
    factorM: step.verification?.factorM ?? step.initialM / step.n,
    factorN: step.verification?.factorN ?? step.initialN / step.n,
  };
}

function getDivisionReading(step: AlgorithmStep, content: MathematicalReadingContent): string {
  const values = stepValues(step);
  const template = values.r === 0
    ? content.division.exact
    : values.q === 0 ? content.division.properFraction : content.division.mixedNumber;
  return fillTemplate(template, values);
}

function getWorkedConsequence(step: AlgorithmStep, content: MathematicalReadingContent): string {
  if (step.phase === 'E2') return getStepReading(step, content);
  const values = stepValues(step);
  return fillTemplate(step.q === 0 ? content.workedReductionDummy : content.workedReduction, values);
}

/** A phase-specific paragraph: E1 calculates; E2 tests; E3 includes the failed E2 test. */
export function getStepReading(step: AlgorithmStep, content: MathematicalReadingContent): string {
  const values = stepValues(step);
  if (step.phase === 'E0') {
    return fillTemplate(step.type === 'E0_SWAP' ? content.e0Swap : content.e0Noop, values);
  }
  if (step.phase === 'E1') {
    return [getDivisionReading(step, content), fillTemplate(content.nextCheck, values)].join(' ');
  }
  if (step.phase === 'E2') return fillTemplate(content.termination, values);
  return fillTemplate(step.q === 0 ? content.reductionDummy : content.reduction, values);
}

/** Complete book-style paragraphs with an independently identified passage for each executing step. */
export function getWorkedExample(
  steps: AlgorithmStep[],
  content: MathematicalReadingContent,
): WorkedExampleParagraph[] {
  const paragraphs: WorkedExampleParagraph[] = [];

  for (let index = 0; index < steps.length; index += 1) {
    const step = steps[index];
    if (step.phase === 'E0') {
      const chunks: WorkedExampleChunk[] = [{
        id: `step-${step.stepIndex}-${step.phase.toLowerCase()}`,
        stepIndex: step.stepIndex,
        phase: step.phase,
        text: getStepReading(step, content),
      }];
      paragraphs.push({
        id: `e0-${step.stepIndex}`,
        startStep: step.stepIndex,
        endStep: step.stepIndex,
        chunks,
        text: chunks.map(({ text }) => text).join(' '),
      });
      continue;
    }

    const following = steps[index + 1];
    const hasConsequence = step.phase === 'E1'
      && following?.pass === step.pass
      && (following.phase === 'E3' || following.phase === 'E2');
    const chunks: WorkedExampleChunk[] = [{
      id: `step-${step.stepIndex}-${step.phase.toLowerCase()}`,
      stepIndex: step.stepIndex,
      phase: step.phase,
      text: hasConsequence ? getDivisionReading(step, content) : getStepReading(step, content),
    }];
    if (hasConsequence) {
      chunks.push({
        id: `step-${following.stepIndex}-${following.phase.toLowerCase()}`,
        stepIndex: following.stepIndex,
        phase: following.phase,
        text: getWorkedConsequence(following, content),
      });
      if (following.phase === 'E3' && following.q === 0) {
        chunks.push({
          id: `pass-${step.pass ?? step.stepIndex}-e0-aside`,
          text: fillTemplate(content.e0Aside, stepValues(following)),
        });
      }
    }
    paragraphs.push({
      id: `pass-${step.pass ?? step.stepIndex}`,
      startStep: step.stepIndex,
      endStep: hasConsequence ? following.stepIndex : step.stepIndex,
      chunks,
      text: chunks.map(({ text }) => text).join(' '),
    });
    if (hasConsequence) index += 1;
  }

  return paragraphs;
}

export function getReadingIntro(
  initialM: number,
  initialN: number,
  withE0: boolean,
  content: MathematicalReadingContent,
): string {
  const template = withE0
    ? initialM < initialN ? content.intro.withE0Swap : content.intro.withE0Noop
    : content.intro.standard;
  return fillTemplate(template, { initialM, initialN });
}
