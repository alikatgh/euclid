import type {
  AlgorithmStep,
  CodeExecution,
  CodeLanguage,
  CodeLanguageContent,
  CodeLessonContent,
  CodeProgram,
} from '../types';

export type { CodeExecution, CodeLanguage, CodeLine, CodeLessonContent, CodeProgram } from '../types';

type TemplateValues = Record<string, number | null>;

function fillTemplate(template: string, values: TemplateValues): string {
  return template.replace(/\{([A-Za-z][A-Za-z0-9]*)\}/g, (placeholder, key: string) => (
    Object.hasOwn(values, key) ? String(values[key] ?? '—') : placeholder
  ));
}

export function buildCodeProgram(
  content: CodeLessonContent,
  language: CodeLanguage,
  withE0: boolean,
  initialM: number,
  initialN: number,
): CodeProgram {
  const lines = content.languages[language].lines
    .filter((line) => withE0 || !line.onlyWithE0)
    .map(({ onlyWithE0: _onlyWithE0, ...line }) => ({
      ...line,
      text: fillTemplate(line.text, { initialM, initialN }),
    }));

  return { lines, source: `${lines.map((line) => line.text).join('\n')}\n` };
}

function getExplanationKey(step: AlgorithmStep): keyof CodeLanguageContent['explanations'] {
  if (step.type === 'E0_SWAP') return 'e0Swap';
  if (step.type === 'E0_NOOP') return 'e0Noop';
  if (step.phase === 'E2') return 'e2';
  if (step.phase === 'E3') return step.isDummy ? 'e3Dummy' : 'e3';
  return step.isDummy ? 'e1Dummy' : 'e1';
}

function getActiveOperations(step: AlgorithmStep): string[] {
  if (step.type === 'E0_SWAP') return ['e0-check', 'e0-save', 'e0-swap'];
  if (step.type === 'E0_NOOP') return ['e0-check'];
  if (step.phase === 'E2') return ['e2-check', 'e2-return'];
  if (step.phase === 'E3') return ['e2-check', 'e3-reduce'];
  return ['e1-divide', 'e1-remainder'];
}

export function getCodeExecution(
  step: AlgorithmStep,
  language: CodeLanguage,
  content: CodeLessonContent,
): CodeExecution {
  const nextM = step.newM ?? step.nextM ?? step.m;
  const nextN = step.newN ?? step.nextN ?? step.n;
  const explanation = content.languages[language].explanations[getExplanationKey(step)];
  const values = {
    initialM: step.initialM,
    initialN: step.initialN,
    m: step.m,
    n: step.n,
    q: step.q,
    r: step.r,
    nextM,
    nextN,
    temp: step.m,
    pass: step.pass ?? 0,
  };
  const operations = getActiveOperations(step);
  const activeLineIds = content.languages[language].lines
    .filter((line) => line.operation && operations.includes(line.operation))
    .map((line) => line.id);
  const variables: CodeExecution['variables'] = [
    { name: 'm', before: step.m, after: nextM },
    { name: 'n', before: step.n, after: nextN },
  ];

  if (step.phase === 'E0') {
    if (language === 'c' && step.type === 'E0_SWAP') {
      variables.push({ name: 'temp', before: null, after: step.m });
    }
  } else {
    // Python keeps q/r between iterations; C declares fresh block-local values.
    const previousDivision = language === 'python' && step.phase === 'E1'
      ? step.traceHistory.findLast((row) => row.phase === 'E1' && row.pass < (step.pass ?? 1))
      : undefined;
    variables.push(
      {
        name: 'q',
        before: step.phase === 'E1' ? previousDivision?.q ?? null : step.q,
        after: step.q,
      },
      {
        name: 'r',
        before: step.phase === 'E1' ? previousDivision?.r ?? null : step.r,
        after: step.r,
      },
    );
  }

  return {
    activeLineIds,
    title: fillTemplate(explanation.title, values),
    explanation: fillTemplate(explanation.explanation, values),
    variables,
    result: step.phase === 'E2' ? step.n : null,
  };
}
