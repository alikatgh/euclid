import type { AlgorithmStep } from '../types/index.ts';

/** Abstract operations, not CPU instructions, source lines, or animation frames. */
export interface AlgorithmOperationCounts {
  remainderDivisions: number;
  zeroTests: number;
  orderingTests: number;
  exchanges: number;
  pairUpdates: number;
  returns: number;
}

export function countAlgorithmOperations(steps: AlgorithmStep[], throughIndex = steps.length - 1): AlgorithmOperationCounts {
  const result: AlgorithmOperationCounts = {
    remainderDivisions: 0, zeroTests: 0, orderingTests: 0, exchanges: 0, pairUpdates: 0, returns: 0,
  };
  for (const step of steps.slice(0, throughIndex + 1)) {
    if (step.phase === 'E0') {
      result.orderingTests++;
      if (step.type === 'E0_SWAP') result.exchanges++;
    }
    if (step.phase === 'E1') result.remainderDivisions++;
    // The reference player combines the unsuccessful E2 test and E3 update.
    if (step.phase === 'E3') { result.zeroTests++; result.pairUpdates++; }
    if (step.phase === 'E2') { result.zeroTests++; result.returns++; }
  }
  return result;
}
