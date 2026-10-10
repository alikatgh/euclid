import type { CurriculumLesson, LessonFrame, LessonInputs } from '../types/curriculum.ts';
import { foundations } from '../lessons/foundations.ts';
import { numbersAndSumsLessons } from '../lessons/numbersAndSums.ts';

export const curriculumLessons: CurriculumLesson[] = [...foundations, ...numbersAndSumsLessons].sort((a, b) => a.order - b.order);
export const lessonCatalog = [
  { id: 'algorithm-e', order: 1, title: 'Euclid’s algorithm', subtitle: 'The original reference lesson · §1.1' },
  ...curriculumLessons,
];

export function defaultInputs(lesson: CurriculumLesson): LessonInputs {
  return Object.fromEntries(lesson.parameters.map((parameter) => [parameter.id, parameter.initial]));
}

export function validateLessonInputs(lesson: CurriculumLesson, inputs: LessonInputs): void {
  for (const parameter of lesson.parameters) {
    const value = inputs[parameter.id];
    if (!Number.isFinite(value) || value < parameter.min || value > parameter.max) {
      throw new RangeError(`${parameter.label} must be between ${parameter.min} and ${parameter.max}`);
    }
    const step = parameter.step ?? 1;
    const units = (value - parameter.min) / step;
    if (Math.abs(units - Math.round(units)) > 1e-8) throw new RangeError(`${parameter.label} must use steps of ${step}`);
  }
}

/** Fail with a helpful error rather than rendering a misleading partial lesson. */
export function buildLessonFrames(lesson: CurriculumLesson, inputs: LessonInputs): LessonFrame[] {
  validateLessonInputs(lesson, inputs);
  const frames = lesson.buildFrames(inputs);
  if (!frames.length || frames.length > 500) throw new Error('A lesson needs 1–500 finite steps.');
  const ids = new Set<string>();
  for (const frame of frames) {
    if (ids.has(frame.id)) throw new Error(`Repeated frame: ${frame.id}`);
    ids.add(frame.id);
    if (!frame.formula || !frame.formal || !frame.reading || !frame.intuition) throw new Error(`Incomplete frame: ${frame.id}`);
    if (frame.code.activeLines.some((line) => !Number.isInteger(line) || line < 1 || line > frame.code.lines.length)) {
      throw new Error(`Invalid source line in ${frame.id}`);
    }
    const prediction = frame.prediction;
    if (prediction && (!Number.isInteger(prediction.correctIndex) || prediction.correctIndex < 0 || prediction.correctIndex >= prediction.choices.length)) {
      throw new Error(`Invalid prediction in ${frame.id}`);
    }
  }
  return frames;
}
