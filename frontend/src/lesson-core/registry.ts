/**
 * Lesson Registry for the Euclid Core Engine.
 *
 * Every lesson adhering to the Lesson 1 standard is registered here.
 */
import type { LessonSpec } from './types.ts';
import { algorithmE } from '../lessons/001-algorithm-e.ts';

export const coreLessons: readonly LessonSpec<any, any>[] = [
  algorithmE,
];

export function getCoreLesson(id: string): LessonSpec<any, any> | undefined {
  return coreLessons.find((l) => l.id === id);
}
