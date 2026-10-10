import { useMemo } from 'react';
import type { AlgorithmStep, LessonData } from '../types';

export function computeAlgorithmSteps(
  initM: number,
  initN: number,
  withE0: boolean,
  lesson: LessonData | null
): AlgorithmStep[] {
  // The visualization promises a finite trace only for this explicit domain.
  // In particular, n = 0 would produce NaN remainders and never terminate.
  for (const [name, value] of [['m', initM], ['n', initN]] as const) {
    if (!Number.isFinite(value) || !Number.isInteger(value) || value < 1 || value > 9999) {
      throw new RangeError(`${name} must be a finite positive integer from 1 to 9999`);
    }
  }
  let m = initM;
  let n = initN;
  const steps: AlgorithmStep[] = [];
  const traceHistory: import('../types').TraceRow[] = [];
  const prose = lesson?.algorithm.knuth_prose;
  const notes = lesson?.algorithm.pedagogical_notes;

  // Step E0
  if (withE0) {
    if (m < n) {
      const stepIdx = steps.length;
      traceHistory.push({
        pass: 0,
        phase: 'E0',
        m,
        n,
        q: null,
        r: null,
        isDummy: false,
        stepIndex: stepIdx,
      });
      steps.push({
        type: 'E0_SWAP',
        phase: 'E0',
        activeFlowId: 'flow-e0',
        stepIndex: stepIdx,
        badge: 'Step E0: Ensure m ≥ n',
        initialM: initM,
        initialN: initN,
        m, n, q: null, r: null,
        newM: n, newN: m,
        equation: `m < n (${m} < ${n}) ⟶ swap(m, n)`,
        formulaParts: {
          m: `${m} ⟶ ${n}`,
          n: `${n} ⟶ ${m}`,
          text: `m ↔ n (${m} ↔ ${n})`,
        },
        explanation: `A measuring ruler cannot measure a board shorter than itself—stick ${n} fits 0 times into rod ${m}! Step E0 detects this mismatch upfront and swaps their roles: piece ${n} becomes the target rod (m), and piece ${m} becomes the measuring stick (n).`,
        knuthQuote: prose?.e0_proposal || 'Optional E0 exchanges m and n when m < n, preserving their greatest common divisor before E1.',
        callout: `Why Knuth added Step E0: Without it, the algorithm wastes an entire division pass computing "${m} ÷ ${n} = 0 (remainder ${m})" just to trigger a swap later in Step E3. Step E0 fixes the order upfront.`,
        traceHistory: [...traceHistory],
      });
      const temp = m;
      m = n;
      n = temp;
    } else {
      const stepIdx = steps.length;
      steps.push({
        type: 'E0_NOOP',
        phase: 'E0',
        activeFlowId: 'flow-e0',
        stepIndex: stepIdx,
        badge: 'Step E0: Ensure m ≥ n',
        initialM: initM,
        initialN: initN,
        m, n, q: null, r: null,
        equation: `m ≥ n (${m} ≥ ${n}) ⟶ No swap needed`,
        formulaParts: {
          m, n,
          text: `${m} ≥ ${n} (no swap)`,
        },
        explanation: `Step E0 checks if m < n. Since m (${m}) is already greater than or equal to n (${n}), no swap is needed. Proceed directly to Step E1.`,
        knuthQuote: prose?.e0_proposal || 'Optional E0 exchanges m and n when m < n, preserving their greatest common divisor before E1.',
        callout: 'Values are already in proper order for division.',
        traceHistory: [...traceHistory],
      });
    }
  }

  let pass = 1;
  while (true) {
    const q = Math.floor(m / n);
    const r = m % n;
    const isDummy = (pass === 1 && initM < initN && !withE0);

    const stepIdxE1 = steps.length;
    traceHistory.push({
      pass,
      phase: 'E1',
      m,
      n,
      q,
      r,
      isDummy,
      stepIndex: stepIdxE1,
    });

    // Phase 1: Division (Step E1)
    steps.push({
      type: 'DIVISION',
      phase: 'E1',
      activeFlowId: 'flow-e1',
      stepIndex: stepIdxE1,
      pass,
      badge: isDummy ? `Pass ${pass} (Step E1): Dummy Division` : `Pass ${pass} (Step E1): Find Remainder`,
      initialM: initM,
      initialN: initN,
      m, n, q, r,
      isDummy,
      equation: `${m} = (${q} × ${n}) + ${r}`,
      formulaParts: {
        m, q, n, r,
        text: `${m} = (${q} × ${n}) + ${r}`,
      },
      explanation: isDummy
        ? `Measuring target rod m (${m}) with stick n (${n}). Because stick ${n} is longer than rod ${m}, it fits 0 times (q = 0). The entire rod ${m} remains as leftover remainder (r = ${m}).`
        : `Measuring target rod m (${m}) with stick n (${n}). Stick ${n} fits ${q} time(s), leaving a remainder piece of size r = ${r}.`,
      knuthQuote: isDummy
        ? (prose?.e1_dummy || `With m < n, E1 obtains q = 0 and r = ${r}; E2 then tests this remainder.`)
        : 'E1 computes q and r so that m = q × n + r and 0 ≤ r < n. The following E2 tests r.',
      callout: isDummy
        ? (notes?.dummy_pass_explanation || `Notice that no reduction happened! This entire division was wasted just setting up a swap in Step E3.`)
        : (notes?.geometric_intuition || `Any number dividing both ${m} and ${n} must also divide the leftover remainder ${r}.`),
      traceHistory: [...traceHistory],
    });

    // Phase 2: Zero Check & Termination (Step E2)
    if (r === 0) {
      const stepIdxE2 = steps.length;
      const gcdVal = n;
      const factorM = Math.round(initM / gcdVal);
      const factorN = Math.round(initN / gcdVal);

      steps.push({
        type: 'DIVISION',
        phase: 'E2',
        activeFlowId: 'flow-e2',
        stepIndex: stepIdxE2,
        pass,
        badge: `Pass ${pass} (Step E2): Termination (GCD Found)`,
        initialM: initM,
        initialN: initN,
        m, n, q, r,
        isDummy: false,
        equation: `${m} = (${q} × ${n}) + 0  ⟶  GCD = ${n}`,
        formulaParts: {
          m, q, n, r: 0,
          text: `r = 0 ⟹ GCD = ${n}`,
        },
        explanation: `Remainder r = 0! Stick of size ${n} measures target ${m} with zero leftover piece. The algorithm terminates. Greatest Common Divisor gcd(${initM}, ${initN}) is ${n}.`,
        knuthQuote: prose?.e2_terminate || 'A zero remainder at E2 ends the calculation. The current n is the greatest common divisor of the original pair because each reduction preserved their common divisors.',
        callout: `Complete! In ${pass} division passes, we proved that ${n} is the largest integer that evenly divides both original numbers.`,
        traceHistory: [...traceHistory],
        verification: {
          gcd: gcdVal,
          factorM,
          factorN,
        },
      });
      break;
    }

    // Phase 3: Reduce & Swap (Step E3)
    const nextM = n;
    const nextN = r;
    const stepIdxE3 = steps.length;

    steps.push({
      type: 'REDUCE',
      phase: 'E3',
      activeFlowId: 'flow-e3',
      stepIndex: stepIdxE3,
      pass,
      badge: isDummy ? `Pass ${pass} (Step E3): Cumbersome Swap` : `Pass ${pass} (Step E3): Reduce`,
      initialM: initM,
      initialN: initN,
      m, n, q, r,
      nextM, nextN,
      isDummy,
      equation: `m ← ${nextM},  n ← ${nextN}`,
      formulaParts: {
        m: nextM,
        n: nextN,
        text: `m ← ${nextM}, n ← ${nextN}`,
      },
      explanation: isDummy
        ? `In Step E3, we set m ← n (${nextM}) and n ← r (${nextN}). Look closely: m and n were just swapped! Now m (${nextM}) ≥ n (${nextN}), so real division can finally start on pass 2.`
        : `In Step E3, the previous stick (${nextM}) becomes the new target, and remainder piece (${nextN}) becomes the new measuring stick. Loop back to Step E1.`,
      knuthQuote: isDummy
        ? (prose?.e3_swap || `The zero quotient leaves r = ${r}. E3 therefore exchanges the inputs through m ← ${nextM} and n ← ${nextN}, then repeats E1.`)
        : 'E3 replaces (m, n) with (n, r), a pair with the same greatest common divisor. The next E1 divides this reduced pair.',
      callout: isDummy
        ? `This is why Knuth added Step E0: to replace this whole dummy division pass with a single conditional swap.`
        : `Problem size reduced: gcd(${m}, ${n}) is now simplified to gcd(${nextM}, ${nextN}).`,
      traceHistory: [...traceHistory],
    });

    m = nextM;
    n = nextN;
    pass++;
  }

  return steps;
}

export function useAlgorithm(m: number, n: number, withE0: boolean, lesson: LessonData | null) {
  return useMemo(() => {
    return computeAlgorithmSteps(m, n, withE0, lesson);
  }, [m, n, withE0, lesson]);
}
