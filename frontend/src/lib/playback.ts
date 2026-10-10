/** Pure scheduling boundary makes hidden/paused lessons provably timer-free. */
export function schedulePlayback(
  options: { active: boolean; playing: boolean; index: number; frameCount: number; delay: number },
  advance: () => void,
  clock: { setTimeout: (callback: () => void, delay: number) => number; clearTimeout: (timer: number) => void },
): (() => void) | undefined {
  if (!options.active || !options.playing || options.frameCount < 2 || options.index >= options.frameCount - 1) return;
  const timer = clock.setTimeout(advance, options.delay);
  return () => clock.clearTimeout(timer);
}
