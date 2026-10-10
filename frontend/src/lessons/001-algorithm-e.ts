/**
 * Lesson 1: Algorithm E (Euclid's Algorithm)
 * Donald Knuth, The Art of Computer Programming, Vol. 1, §1.1
 *
 * Reference implementation of LessonSpec.
 * Every lesson in Euclid must adhere to this standard of quality.
 */
import type {
  DiagramNode,
  DiagramScene,
  FormulaSet,
  LessonSpec,
  StepContext,
  TraceRow,
  TraceStep,
  WorkedParagraph,
} from '../lesson-core/types.ts';
import { tone } from '../lesson-core/tex.ts';

export interface AlgorithmEInput {
  [key: string]: number;
  m: number;
  n: number;
}

export interface AlgorithmEStep extends TraceStep {
  phase: 'E0' | 'E1' | 'E2' | 'E3';
  pass?: number;
  badge: string;
  isDummy?: boolean;
  e0Type?: 'E0_SWAP' | 'E0_NOOP';
  values: {
    m: number;
    n: number;
    q: number | null;
    r: number | null;
  };
  next?: {
    m: number;
    n: number;
    q: number | null;
    r: number | null;
  };
  terminal?: boolean;
  factorM?: number;
  factorN?: number;
}

function gcd(a: number, b: number): number {
  return b === 0 ? a : gcd(b, a % b);
}

export const algorithmE: LessonSpec<AlgorithmEInput, AlgorithmEStep> = {
  id: 'algorithm-e',
  order: 1,
  navigationLabel: 'Lesson 1 · Algorithm E',
  title: "Algorithm E (Euclid's Algorithm)",
  subtitle: 'Donald Knuth, The Art of Computer Programming, Vol. 1, §1.1',
  source: {
    book: 'The Art of Computer Programming, Vol. 1',
    section: '§1.1',
  },

  variables: [
    { key: 'm', symbol: 'm', tone: 'primary', meaning: 'The dividend or target length being measured.' },
    { key: 'n', symbol: 'n', tone: 'secondary', meaning: 'The divisor or measuring stick unit.' },
    { key: 'q', symbol: 'q', tone: 'accent', meaning: 'The quotient: whole copies of stick n that fit into rod m.' },
    { key: 'r', symbol: 'r', tone: 'alert', meaning: 'The remainder: leftover length after removing q copies of n.' },
  ],

  inputs: [
    { key: 'm', label: 'm', min: 1, max: 9999 },
    { key: 'n', label: 'n', min: 1, max: 9999 },
  ],

  defaultInput: { m: 119, n: 544 },

  presets: [
    { name: '119 & 544 (Knuth TAOCP)', input: { m: 119, n: 544 } },
    { name: '144 & 89 (Lamé Fibonacci)', input: { m: 144, n: 89 } },
    { name: '35 & 64 (Coprime, GCD=1)', input: { m: 35, n: 64 } },
    { name: '48 & 18 (m > n)', input: { m: 48, n: 18 } },
    { name: '252 & 105', input: { m: 252, n: 105 } },
    { name: '2166 & 6099 (Large)', input: { m: 2166, n: 6099 } },
  ],

  variants: [
    { id: 'standard', label: 'Standard (Without E0)' },
    { id: 'with-e0', label: 'With Step E0 (Optimized)' },
  ],

  views: [
    { id: 'tape', label: 'Tape' },
    { id: 'tiling', label: '2D Tiling' },
  ],

  stepDefinitions: [
    {
      id: 'E0',
      name: 'Ensure m ≥ n',
      description: 'If $m < n$, exchange $m \\leftrightarrow n$ directly in memory.',
      optional: true,
      enabledIn: ['with-e0'],
    },
    {
      id: 'E1',
      name: 'Find remainder',
      description: 'Divide $m$ by $n$ and let $r$ be the remainder ($0 \\le r < n$).',
    },
    {
      id: 'E2',
      name: 'Is it zero?',
      description: 'If $r = 0$, the algorithm terminates; $n$ is the answer.',
    },
    {
      id: 'E3',
      name: 'Reduce',
      description: 'Set $m \\leftarrow n$, $n \\leftarrow r$, and go back to step E1.',
    },
  ],

  maxSteps: 100,

  run(input: AlgorithmEInput, variant: string): AlgorithmEStep[] {
    const steps: AlgorithmEStep[] = [];
    let curM = input.m;
    let curN = input.n;
    const withE0 = variant === 'with-e0';

    if (withE0) {
      if (curM < curN) {
        steps.push({
          phase: 'E0',
          pass: 0,
          badge: 'Step E0: Ensure m ≥ n',
          e0Type: 'E0_SWAP',
          values: { m: curM, n: curN, q: null, r: null },
          next: { m: curN, n: curM, q: null, r: null },
        });
        const tmp = curM;
        curM = curN;
        curN = tmp;
      } else {
        steps.push({
          phase: 'E0',
          pass: 0,
          badge: 'Step E0: Ensure m ≥ n',
          e0Type: 'E0_NOOP',
          values: { m: curM, n: curN, q: null, r: null },
          next: { m: curM, n: curN, q: null, r: null },
        });
      }
    }

    let pass = 1;
    while (true) {
      const q = Math.floor(curM / curN);
      const r = curM % curN;
      const isDummy = pass === 1 && input.m < input.n && !withE0;

      // Step E1
      steps.push({
        phase: 'E1',
        pass,
        badge: isDummy ? `Pass ${pass} (Step E1): Dummy Division` : `Pass ${pass} (Step E1): Find Remainder`,
        isDummy,
        values: { m: curM, n: curN, q, r },
      });

      // Step E2 if r == 0
      if (r === 0) {
        const finalGcd = curN;
        steps.push({
          phase: 'E2',
          pass,
          badge: `Pass ${pass} (Step E2): Termination (GCD Found)`,
          isDummy: false,
          values: { m: curM, n: curN, q, r: 0 },
          terminal: true,
          factorM: Math.round(input.m / finalGcd),
          factorN: Math.round(input.n / finalGcd),
        });
        break;
      }

      // Step E3: reduce
      const nextM = curN;
      const nextN = r;
      steps.push({
        phase: 'E3',
        pass,
        badge: isDummy ? `Pass ${pass} (Step E3): Cumbersome Swap` : `Pass ${pass} (Step E3): Reduce`,
        isDummy,
        values: { m: curM, n: curN, q, r },
        next: { m: nextM, n: nextN, q: null, r: null },
      });

      curM = nextM;
      curN = nextN;
      pass++;
      if (pass > 80) break; // safeguard
    }

    return steps;
  },

  formula(step: AlgorithmEStep, ctx: StepContext<AlgorithmEInput, AlgorithmEStep>): FormulaSet {
    const { m, n, q, r } = step.values;
    const initialGcd = gcd(ctx.input.m, ctx.input.n);

    if (step.phase === 'E0') {
      if (step.e0Type === 'E0_SWAP') {
        return {
          compact: `m \\longleftrightarrow n \\quad (${tone('primary', m)} \\longleftrightarrow ${tone('secondary', step.next?.m ?? n)})`,
          full: `m \\longleftrightarrow n \\quad (${tone('primary', m)} \\longleftrightarrow ${tone('secondary', step.next?.m ?? n)})`,
          reference: { label: 'KNUTH §1.1', tex: `m < n \\implies m \\leftrightarrow n` },
          invariant: `\\gcd(${m}, ${n}) = \\gcd(${step.next?.m ?? n}, ${step.next?.n ?? m}) = ${initialGcd}`,
        };
      }
      return {
        compact: `${tone('primary', m)} \\ge ${tone('secondary', n)}`,
        full: `${tone('primary', m)} \\ge ${tone('secondary', n)}`,
        reference: { label: 'KNUTH §1.1', tex: `m \\ge n` },
        invariant: `\\gcd(${m}, ${n}) = ${initialGcd}`,
      };
    }

    if (step.phase === 'E3') {
      const nextM = step.next?.m ?? n;
      const nextN = step.next?.n ?? r ?? 0;
      return {
        compact: `m \\leftarrow ${tone('primary', nextM)}, \\; n \\leftarrow ${tone('secondary', nextN)}`,
        full: `m \\leftarrow ${tone('primary', nextM)}, \\quad n \\leftarrow ${tone('secondary', nextN)}`,
        reference: { label: 'KNUTH §1.1', tex: `\\text{Replace } (m, n) \\leftarrow (n, r)` },
        invariant: `\\gcd(${m}, ${n}) = \\gcd(${nextM}, ${nextN}) = ${initialGcd}`,
      };
    }

    if (step.phase === 'E2') {
      return {
        compact: `${tone('alert', 'r = 0')} \\implies \\gcd = ${tone('result', `\\mathbf{${n}}`)}`,
        full: `${tone('alert', 'r = 0')} \\implies \\gcd = ${tone('result', `\\mathbf{${n}}`)}`,
        reference: {
          label: 'KNUTH §1.1',
          tex: `\\frac{${tone('primary', m)}}{${tone('secondary', n)}} = ${tone('result', `\\mathbf{${q ?? 0}}`)} \\quad (\\text{Exact})`,
        },
        invariant: `\\gcd(${ctx.input.m}, ${ctx.input.n}) = \\mathbf{${n}}`,
      };
    }

    // Phase E1
    const safeQ = q ?? 0;
    const safeR = r ?? 0;
    return {
      compact: `${tone('primary', m)} = (${tone('accent', safeQ)} \\times ${tone('secondary', n)}) + ${tone('alert', safeR)}`,
      full: `${tone('primary', m)} = (${tone('accent', safeQ)} \\times ${tone('secondary', n)}) + ${tone('alert', safeR)}`,
      reference: {
        label: 'KNUTH §1.1',
        tex: `\\frac{${tone('primary', m)}}{${tone('secondary', n)}} = ${tone('accent', safeQ)}\\frac{${tone('alert', safeR)}}{${tone('secondary', n)}}`,
      },
      invariant: `\\gcd(${m}, ${n}) = \\gcd(${n}, ${safeR}) = ${initialGcd}`,
    };
  },

  diagram(step: AlgorithmEStep, ctx: StepContext<AlgorithmEInput, AlgorithmEStep> & { view: string }): DiagramScene {
    const { m, n, q, r } = step.values;
    const isTape = ctx.view !== 'tiling';

    if (isTape) {
      const sceneW = 620;
      const sceneH = 460;
      const nodes: DiagramNode[] = [];
      const padX = 36;
      const innerW = sceneW - padX * 2;
      const maxVal = Math.max(m, n, 1);
      const scaleX = (val: number) => Math.max(4, Math.round((val / maxVal) * innerW));

      // Target rod m
      nodes.push({
        id: 'label-m',
        type: 'text',
        x: padX,
        y: 44,
        text: `Target rod · m = ${m}`,
        tone: 'primary',
        weight: 'bold',
      });
      nodes.push({
        id: 'rect-m',
        type: 'rect',
        x: padX,
        y: 60,
        width: scaleX(m),
        height: 48,
        tone: 'primary',
        value: m,
        title: `Target rod m = ${m}`,
      });
      if (scaleX(m) >= 64) {
        nodes.push({
          id: 'text-m-inside',
          type: 'text',
          x: padX + scaleX(m) / 2,
          y: 90,
          text: `m = ${m}`,
          anchor: 'middle',
          tone: 'muted',
          weight: 'bold',
        });
      }

      // Measuring stick copies
      const yMeasure = 160;
      if (step.phase === 'E0' && step.e0Type === 'E0_NOOP') {
        nodes.push({
          id: 'label-n-ready',
          type: 'text',
          x: padX,
          y: yMeasure - 16,
          text: `Measuring stick · n = ${n}`,
          tone: 'secondary',
          weight: 'bold',
        });
        nodes.push({
          id: 'rect-n-ready',
          type: 'rect',
          x: padX,
          y: yMeasure,
          width: scaleX(n),
          height: 48,
          tone: 'secondary',
          dashed: true,
          value: n,
        });
      } else if (step.isDummy) {
        nodes.push({
          id: 'label-dummy',
          type: 'text',
          x: padX,
          y: yMeasure - 16,
          text: `0 copies of n = ${n}`,
          tone: 'secondary',
          weight: 'bold',
        });
        nodes.push({
          id: 'rect-dummy',
          type: 'rect',
          x: padX,
          y: yMeasure,
          width: scaleX(n),
          height: 48,
          tone: 'secondary',
          dashed: true,
          value: n,
        });
        nodes.push({
          id: 'text-dummy-sub',
          type: 'text',
          x: padX,
          y: yMeasure + 78,
          text: `Remainder · r = ${r ?? m}`,
          tone: 'alert',
          weight: 'bold',
        });
        nodes.push({
          id: 'text-dummy-msg',
          type: 'text',
          x: padX,
          y: yMeasure + 104,
          text: 'No whole stick fits. The entire target remains.',
          tone: 'muted',
        });
      } else {
        const copies = q ?? 0;
        nodes.push({
          id: 'label-copies',
          type: 'text',
          x: padX,
          y: yMeasure - 16,
          text: copies === 1 ? `1 copy of n = ${n}` : `${copies} copies of n = ${n}`,
          tone: 'secondary',
          weight: 'bold',
        });

        let curX = padX;
        const stickW = scaleX(n);
        for (let i = 0; i < copies; i++) {
          nodes.push({
            id: `rect-copy-${i}`,
            type: 'rect',
            x: curX,
            y: yMeasure,
            width: stickW,
            height: 48,
            tone: 'secondary',
            value: n,
          });
          curX += stickW;
        }

        if (r !== null && r > 0) {
          nodes.push({
            id: 'rect-rem',
            type: 'rect',
            x: curX,
            y: yMeasure,
            width: scaleX(r),
            height: 48,
            tone: 'alert',
            value: r,
          });
          nodes.push({
            id: 'label-rem',
            type: 'text',
            x: padX,
            y: yMeasure + 78,
            text: `Remainder · r = ${r}`,
            tone: 'alert',
            weight: 'bold',
          });
        } else if (r === 0) {
          nodes.push({
            id: 'label-exact',
            type: 'text',
            x: padX,
            y: yMeasure + 78,
            text: `Exact fit · r = 0 · n = ${n} divides both inputs`,
            tone: 'result',
            weight: 'bold',
          });
        }
      }

      return {
        width: sceneW,
        height: sceneH,
        nodes,
        description: `Euclid tape visualization: target rod m=${m}, measuring unit n=${n}, quotient=${q}, remainder=${r}.`,
      };
    }

    // 2D Tiling view
    const sceneW = 620;
    const sceneH = 460;
    const nodes: DiagramNode[] = [];
    const padX = 40;
    const padY = 50;
    const boxW = sceneW - padX * 2;
    const boxH = sceneH - padY * 2;

    if (m < n) {
      nodes.push({
        id: 'tile-dummy-1',
        type: 'text',
        x: sceneW / 2,
        y: sceneH / 2 - 20,
        text: `No square of side ${n} fits inside width ${m}.`,
        anchor: 'middle',
        tone: 'muted',
        weight: 'bold',
      });
      nodes.push({
        id: 'tile-dummy-2',
        type: 'text',
        x: sceneW / 2,
        y: sceneH / 2 + 16,
        text: 'Step E3 exchanges the dimensions.',
        anchor: 'middle',
        tone: 'primary',
      });
      return {
        width: sceneW,
        height: sceneH,
        nodes,
        description: `2D Tiling: cannot fit square of side ${n} in rectangle of width ${m}.`,
      };
    }

    const rectAspect = m / Math.max(n, 1);
    let drawW = boxW * 0.85;
    let drawH = drawW / rectAspect;
    if (drawH > boxH * 0.75) {
      drawH = boxH * 0.75;
      drawW = drawH * rectAspect;
    }
    const startX = padX + (boxW - drawW) / 2;
    const startY = padY + (boxH - drawH) / 2;

    nodes.push({
      id: 'tile-outer',
      type: 'rect',
      x: startX,
      y: startY,
      width: drawW,
      height: drawH,
      tone: 'primary',
      outline: true,
    });
    nodes.push({
      id: 'tile-w-label',
      type: 'text',
      x: startX + drawW / 2,
      y: startY - 14,
      text: `Width = ${m}`,
      anchor: 'middle',
      tone: 'primary',
      weight: 'bold',
    });
    nodes.push({
      id: 'tile-h-label',
      type: 'text',
      x: startX - 14,
      y: startY + drawH / 2 + 5,
      text: `Height = ${n}`,
      anchor: 'end',
      tone: 'secondary',
      weight: 'bold',
    });

    const copies = q ?? 0;
    const squareSide = drawH;
    let curX = startX;
    for (let i = 0; i < copies; i++) {
      nodes.push({
        id: `tile-sq-${i}`,
        type: 'rect',
        x: curX,
        y: startY,
        width: squareSide,
        height: squareSide,
        tone: 'secondary',
        value: n,
      });
      if (squareSide >= 44) {
        nodes.push({
          id: `tile-sq-txt-${i}`,
          type: 'text',
          x: curX + squareSide / 2,
          y: startY + squareSide / 2 + 5,
          text: `${n}×${n}`,
          anchor: 'middle',
          tone: 'muted',
          weight: 'bold',
        });
      }
      curX += squareSide;
    }

    const remW = drawW - copies * squareSide;
    if (remW > 2 && r !== null && r > 0) {
      nodes.push({
        id: 'tile-rem-rect',
        type: 'rect',
        x: curX,
        y: startY,
        width: remW,
        height: squareSide,
        tone: 'alert',
        value: r,
      });
      nodes.push({
        id: 'tile-rem-txt',
        type: 'text',
        x: curX + remW / 2,
        y: startY + squareSide / 2 + 5,
        text: `r=${r}`,
        anchor: 'middle',
        tone: 'muted',
        weight: 'bold',
      });
    }

    return {
      width: sceneW,
      height: sceneH,
      nodes,
      description: `2D Tiling: ${m}×${n} rectangle tiled by ${copies} squares of size ${n}×${n} and leftover ${r}×${n}.`,
    };
  },

  narrate(step: AlgorithmEStep, ctx: StepContext<AlgorithmEInput, AlgorithmEStep>): string {
    const { m, n, q, r } = step.values;
    const nextM = step.next?.m ?? n;
    const nextN = step.next?.n ?? r;

    if (step.phase === 'E0') {
      if (step.e0Type === 'E0_SWAP') {
        return `Because $m < n$ ($${m} < ${n}$), step E0 exchanges the inputs upfront: $m \\leftarrow ${nextM}$, $n \\leftarrow ${nextN}$. Exchanging the arguments leaves their common divisors unchanged and skips a division pass with quotient zero.`;
      }
      return `Here $m \\ge n$ ($${m} \\ge ${n}$), so step E0 leaves $m = ${m}$ and $n = ${n}$ unchanged. We proceed directly to step E1 with this pair.`;
    }

    if (step.phase === 'E1') {
      if (step.isDummy) {
        return `Dividing $m = ${m}$ by $n = ${n}$ gives quotient $q = 0$ and remainder $r \\leftarrow ${r}$, because ${n} fits 0 times into ${m}. The entire target rod remains as leftover remainder.`;
      }
      if (r === 0) {
        return `The division is exact: $\\frac{${m}}{${n}} = ${q}$, or $${m} = ${q} \\cdot ${n}$. We obtain quotient $q = ${q}$ and set remainder $r \\leftarrow 0$.`;
      }
      return `Dividing $${m}$ by $${n}$ gives quotient $q = ${q}$ and remainder $r \\leftarrow ${r}$: indeed, $${m} = (${q} \\times ${n}) + ${r}$, where $0 < ${r} < ${n}$. Next, step E2 tests whether $r = 0$.`;
    }

    if (step.phase === 'E2') {
      return `Remainder $r = 0$! Divisor of size $n = ${n}$ measures target $m = ${m}$ with zero leftover. The algorithm terminates with $\\gcd(${ctx.input.m}, ${ctx.input.n}) = ${n}$.`;
    }

    // Step E3
    if (step.isDummy) {
      return `Since $r = ${r} \\ne 0$, step E2 does not terminate. Step E3 sets $m \\leftarrow n$ ($${nextM}$) and $n \\leftarrow r$ ($${nextN}$), exchanging the pair so that $m \\ge n$ for the next pass.`;
    }
    return `At E2 the test $r = 0$ is false, since $r = ${r} \\ne 0$. E3 therefore assigns $m \\leftarrow n$ ($${nextM}$) and $n \\leftarrow r$ ($${nextN}$), then returns to E1. The new pair has the exact same common divisors: $\\gcd(${m}, ${n}) = \\gcd(${nextM}, ${nextN})$.`;
  },

  workedExample: {
    title: 'Worked example',
    sourceNote: 'Following Algorithm E · The Art of Computer Programming, Vol. 1, §1.1.',
    intro(input: AlgorithmEInput, variant: string): string {
      if (variant === 'with-e0') {
        if (input.m < input.n) {
          return `To apply Algorithm E, let $m = ${input.m}$ and $n = ${input.n}$. We include the optional step E0 before E1. Since $${input.m} < ${input.n}$, this comparison will exchange the inputs before the first division, avoiding the initial division with quotient zero.`;
        }
        return `To apply Algorithm E, let $m = ${input.m}$ and $n = ${input.n}$. We include the optional step E0 before E1. Since $${input.m} \\ge ${input.n}$, its comparison will leave the inputs unchanged; the first division uses the given pair.`;
      }
      return `To apply Algorithm E, let $m = ${input.m}$ and $n = ${input.n}$. We begin at E1 and follow the successive divisions. In each pass, the quotient and remainder determine either a new pair of integers or the answer.`;
    },
    paragraphs(steps: readonly AlgorithmEStep[], input: AlgorithmEInput, _variant: string): WorkedParagraph[] {
      const paragraphs: WorkedParagraph[] = [];
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        if (step.phase === 'E0') {
          paragraphs.push({
            chunks: [
              {
                stepIndex: i,
                text: step.e0Type === 'E0_SWAP'
                  ? `Because $m < n$ ($${step.values.m} < ${step.values.n}$), E0 exchanges the inputs, giving $m \\leftarrow ${step.next?.m}$ and $n \\leftarrow ${step.next?.n}$. Exchanging the arguments leaves their common divisors unchanged.`
                  : `Here $m \\ge n$ ($${step.values.m} \\ge ${step.values.n}$), so condition $m < n$ is false. E0 leaves $m = ${step.values.m}$ and $n = ${step.values.n}$ unchanged, proceeding to E1.`,
              },
            ],
          });
        } else if (step.phase === 'E1') {
          const nextStep = steps[i + 1];
          if (nextStep && (nextStep.phase === 'E3' || nextStep.phase === 'E2')) {
            const e1Text = step.isDummy
              ? `Dividing $${step.values.m}$ by $${step.values.n}$ gives the proper fraction $\\frac{${step.values.m}}{${step.values.n}} < 1$. The quotient is therefore $q = 0$, and we set $r \\leftarrow ${step.values.r}$: indeed, $${step.values.m} = 0 \\cdot ${step.values.n} + ${step.values.r}$, with $0 < ${step.values.r} < ${step.values.n}$. Next, E2 tests whether $r = 0$.`
              : step.values.r === 0
                ? `The division is exact: $\\frac{${step.values.m}}{${step.values.n}} = ${step.values.q}$, or $${step.values.m} = ${step.values.q} \\cdot ${step.values.n}$. We obtain quotient $q = ${step.values.q}$ and set the remainder $r \\leftarrow 0$.`
                : `The division $\\frac{${step.values.m}}{${step.values.n}} = ${step.values.q}\\frac{${step.values.r}}{${step.values.n}}$ gives quotient $q = ${step.values.q}$ and remainder $r \\leftarrow ${step.values.r}$. Thus $${step.values.m} = ${step.values.q} \\cdot ${step.values.n} + ${step.values.r}$, where $0 < ${step.values.r} < ${step.values.n}$. Next, E2 tests whether $r = 0$.`;

            const secondText = nextStep.phase === 'E2'
              ? `At E2 the remainder is zero, so the algorithm terminates with $n = ${nextStep.values.n}$. Hence $\\gcd(${input.m}, ${input.n}) = ${nextStep.values.n}$. Both original integers are multiples of this answer.`
              : nextStep.isDummy
                ? `Since $r = ${nextStep.values.r} \\ne 0$, E2 does not terminate. E3 sets $m \\leftarrow ${nextStep.next?.m}$ and $n \\leftarrow ${nextStep.next?.n}$, exchanging the inputs before returning to E1.`
                : `Since $r = ${nextStep.values.r} \\ne 0$, E2 does not terminate. E3 sets $m \\leftarrow ${nextStep.next?.m}$ and $n \\leftarrow ${nextStep.next?.n}$, preserving $\\gcd(${nextStep.values.m}, ${nextStep.values.n}) = \\gcd(${nextStep.next?.m}, ${nextStep.next?.n})$, and we repeat E1.`;

            paragraphs.push({
              chunks: [
                { stepIndex: i, text: e1Text },
                { stepIndex: i + 1, text: secondText },
              ],
            });
            i++; // skip nextStep since chunked together
          } else {
            paragraphs.push({
              chunks: [{ stepIndex: i, text: `E1 computes quotient $q = ${step.values.q}$ and remainder $r = ${step.values.r}$.` }],
            });
          }
        }
      }
      return paragraphs;
    },
    principles: {
      title: 'Why the calculation works',
      paragraphs: [
        'If $d$ divides both $m$ and $n$, then it divides $r = m - qn$. Conversely, if $d$ divides both $n$ and $r$, then it divides $m = qn + r$. The two pairs therefore have exactly the same common divisors, and $\\gcd(m, n) = \\gcd(n, r)$.',
        'Every remainder satisfies $0 \\le r < n$. If $r > 0$, E3 makes it the next value of $n$, so the positive values of $n$ strictly decrease. They cannot decrease indefinitely; eventually $r = 0$. At that point $\\gcd(m, n) = \\gcd(n, 0) = n$, and the preserved common divisors identify the answer for the original inputs.',
      ],
    },
  },

  code: {
    title: 'Algorithm E in code',
    intro: 'Next and Play follow the highlighted code with the rods.',
    languages: {
      c: {
        label: 'C',
        lines: [
          { id: 'include', text: '#include <stdio.h>' },
          { id: 'blank-1', text: '' },
          { id: 'fn-start', text: 'int gcd(int m, int n) {' },
          { id: 'e0-if', text: '    if (m < n) {', phase: 'E0', variants: ['with-e0'] },
          { id: 'e0-temp', text: '        int temp = m;', phase: 'E0', variants: ['with-e0'] },
          { id: 'e0-swap-m', text: '        m = n;', phase: 'E0', variants: ['with-e0'] },
          { id: 'e0-swap-n', text: '        n = temp;', phase: 'E0', variants: ['with-e0'] },
          { id: 'e0-end', text: '    }', phase: 'E0', variants: ['with-e0'] },
          { id: 'loop-start', text: '    while (1) {' },
          { id: 'e1-div', text: '        int q = m / n;', phase: 'E1' },
          { id: 'e1-rem', text: '        int r = m - q * n;', phase: 'E1' },
          { id: 'e2-check', text: '        if (r == 0) {', phase: 'E2' },
          { id: 'e2-return', text: '            return n;', phase: 'E2' },
          { id: 'e2-end', text: '        }', phase: 'E2' },
          { id: 'e3-m', text: '        m = n;', phase: 'E3' },
          { id: 'e3-n', text: '        n = r;', phase: 'E3' },
          { id: 'loop-end', text: '    }' },
          { id: 'fn-end', text: '}' },
          { id: 'blank-2', text: '' },
          { id: 'main-start', text: 'int main(void) {' },
          { id: 'main-call', text: '    printf("%d\\n", gcd({m}, {n}));' },
          { id: 'main-ret', text: '    return 0;' },
          { id: 'main-end', text: '}' },
        ],
        activeLines(step: AlgorithmEStep): string[] {
          if (step.phase === 'E0') {
            return step.e0Type === 'E0_SWAP' ? ['e0-if', 'e0-temp', 'e0-swap-m', 'e0-swap-n'] : ['e0-if'];
          }
          if (step.phase === 'E1') return ['e1-div', 'e1-rem'];
          if (step.phase === 'E2') return ['e2-check', 'e2-return'];
          return ['e3-m', 'e3-n'];
        },
        explain(step: AlgorithmEStep, ctx: StepContext<AlgorithmEInput, AlgorithmEStep>): { title: string; explanation: string } {
          const { m, n, q, r } = step.values;
          if (step.phase === 'E0') {
            return step.e0Type === 'E0_SWAP'
              ? {
                  title: 'E0 · exchange the inputs',
                  explanation: `The test ${m} < ${n} is true. Save m in temp = ${m}, then assign m: ${m} → ${step.next?.m} and n: ${n} → ${step.next?.n}. The temporary variable preserves original m.`,
                }
              : {
                  title: 'E0 · keep the inputs',
                  explanation: `The test ${m} < ${n} is false, so skip the swap block. m stays ${m}, and n stays ${n}. Continue to E1.`,
                };
          }
          if (step.phase === 'E1') {
            return {
              title: `E1 · division, pass ${step.pass}`,
              explanation: `Compute quotient q = ${q} and remainder r = m - q*n = ${r}. In C, this is equivalent to integer division and modulo.`,
            };
          }
          if (step.phase === 'E2') {
            return {
              title: 'E2 · return the GCD',
              explanation: `r == 0 is true. Return n (${n}) as the greatest common divisor of the inputs gcd(${ctx.input.m}, ${ctx.input.n}).`,
            };
          }
          return {
            title: `E3 · reduce, pass ${step.pass}`,
            explanation: `Assign m = n (${step.next?.m}) and n = r (${step.next?.n}). Loop back to step E1 with the reduced pair.`,
          };
        },
      },

      python: {
        label: 'Python',
        lines: [
          { id: 'py-fn', text: 'def gcd(m, n):' },
          { id: 'py-e0-if', text: '    if m < n:', phase: 'E0', variants: ['with-e0'] },
          { id: 'py-e0-swap', text: '        m, n = n, m', phase: 'E0', variants: ['with-e0'] },
          { id: 'py-loop', text: '    while True:' },
          { id: 'py-e1-divmod', text: '        q, r = divmod(m, n)', phase: 'E1' },
          { id: 'py-e2-if', text: '        if r == 0:', phase: 'E2' },
          { id: 'py-e2-ret', text: '            return n', phase: 'E2' },
          { id: 'py-e3-reduce', text: '        m, n = n, r', phase: 'E3' },
          { id: 'py-blank', text: '' },
          { id: 'py-call', text: 'print(gcd({m}, {n}))' },
        ],
        activeLines(step: AlgorithmEStep): string[] {
          if (step.phase === 'E0') {
            return step.e0Type === 'E0_SWAP' ? ['py-e0-if', 'py-e0-swap'] : ['py-e0-if'];
          }
          if (step.phase === 'E1') return ['py-e1-divmod'];
          if (step.phase === 'E2') return ['py-e2-if', 'py-e2-ret'];
          return ['py-e3-reduce'];
        },
        explain(step: AlgorithmEStep, ctx: StepContext<AlgorithmEInput, AlgorithmEStep>): { title: string; explanation: string } {
          const { m, n, q, r } = step.values;
          if (step.phase === 'E0') {
            return step.e0Type === 'E0_SWAP'
              ? {
                  title: 'E0 · exchange the inputs',
                  explanation: `In Python, tuple assignment m, n = n, m swaps the values atomically without requiring a temporary variable: m becomes ${step.next?.m}, n becomes ${step.next?.n}.`,
                }
              : {
                  title: 'E0 · keep the inputs',
                  explanation: `m < n is false, so skip the swap statement. The numbers are already in descending order.`,
                };
          }
          if (step.phase === 'E1') {
            return {
              title: `E1 · division, pass ${step.pass}`,
              explanation: `divmod(${m}, ${n}) computes quotient q = ${q} and remainder r = ${r} in one operation.`,
            };
          }
          if (step.phase === 'E2') {
            return {
              title: 'E2 · return the GCD',
              explanation: `r == 0 is true. Return n (${n}), which equals gcd(${ctx.input.m}, ${ctx.input.n}).`,
            };
          }
          return {
            title: `E3 · reduce, pass ${step.pass}`,
            explanation: `Parallel assignment m, n = n, r shifts the pair to (${step.next?.m}, ${step.next?.n}) and repeats the loop.`,
          };
        },
      },
    },
  },

  trace: {
    title: 'TAOCP §1.1 Trace Table',
    caption: 'Table 1 Matrix',
    columns: [
      { key: 'pass', label: 'Pass', tone: 'muted' },
      { key: 'm', label: 'm', tone: 'primary' },
      { key: 'n', label: 'n', tone: 'secondary' },
      { key: 'q', label: 'q', tone: 'accent' },
      { key: 'r', label: 'r', tone: 'alert' },
    ],
    rows(steps: readonly AlgorithmEStep[], activeIndex: number): TraceRow[] {
      const rows: TraceRow[] = [];
      const seen = new Set<string>();

      for (let i = 0; i <= activeIndex && i < steps.length; i++) {
        const step = steps[i];
        const passKey = step.phase === 'E0' ? 'E0' : `Pass ${step.pass}`;
        if (seen.has(passKey)) {
          // Update row with latest values for that pass
          const existing = rows.find(r => r.label === passKey);
          if (existing) {
            existing.stepIndex = i;
            if (step.values.q !== null) existing.cells.q = step.values.q;
            if (step.values.r !== null) existing.cells.r = step.values.r;
          }
          continue;
        }

        seen.add(passKey);
        rows.push({
          stepIndex: i,
          label: passKey,
          cells: {
            pass: passKey,
            m: step.values.m,
            n: step.values.n,
            q: step.values.q ?? '—',
            r: step.values.r ?? (step.phase === 'E0' ? 'swap' : '—'),
          },
        });
      }

      return rows;
    },
  },

  help: {
    title: 'Smaller worked example · original run paused',
    frames: [
      {
        explanation: 'The target contains fourteen exact units; the measuring stick contains six.',
        diagram: {
          width: 500,
          height: 240,
          description: '14 units measured by sticks of length 6.',
          nodes: [
            { id: 'target-bar', type: 'rect', x: 40, y: 50, width: 280, height: 32, tone: 'primary', value: 14 },
            { id: 'target-lbl', type: 'text', x: 40, y: 38, text: 'Target rod · m = 14', tone: 'primary', weight: 'bold' },
            { id: 'stick-bar', type: 'rect', x: 40, y: 120, width: 120, height: 32, tone: 'secondary', dashed: true, value: 6 },
            { id: 'stick-lbl', type: 'text', x: 40, y: 108, text: 'Measuring stick · n = 6', tone: 'secondary', weight: 'bold' },
          ],
        },
      },
      {
        explanation: 'Place one six-unit copy against the target; eight target units are still uncovered.',
        diagram: {
          width: 500,
          height: 240,
          description: 'First copy of stick length 6 placed against 14.',
          nodes: [
            { id: 'target-bar', type: 'rect', x: 40, y: 50, width: 280, height: 32, tone: 'primary', value: 14 },
            { id: 'copy-1', type: 'rect', x: 40, y: 120, width: 120, height: 32, tone: 'secondary', value: 6 },
            { id: 'copy-1-lbl', type: 'text', x: 40, y: 108, text: '1 copy of 6 placed (8 units remain)', tone: 'secondary', weight: 'bold' },
          ],
        },
      },
      {
        explanation: 'A second six-unit copy fits. A third would exceed the target, so two units remain: $14 = (2 \\times 6) + 2$.',
        diagram: {
          width: 500,
          height: 240,
          description: 'Two copies of 6 fit, leaving 2 units remainder.',
          nodes: [
            { id: 'target-bar', type: 'rect', x: 40, y: 50, width: 280, height: 32, tone: 'primary', value: 14 },
            { id: 'copy-1', type: 'rect', x: 40, y: 120, width: 120, height: 32, tone: 'secondary', value: 6 },
            { id: 'copy-2', type: 'rect', x: 160, y: 120, width: 120, height: 32, tone: 'secondary', value: 6 },
            { id: 'rem-bar', type: 'rect', x: 280, y: 120, width: 40, height: 32, tone: 'alert', value: 2 },
            { id: 'rem-lbl', type: 'text', x: 40, y: 180, text: 'q = 2 whole copies, remainder r = 2', tone: 'result', weight: 'bold' },
          ],
        },
      },
    ],
    check: {
      prompt: 'With 17 counters and trays of 5, how many counters remain after filling as many trays as possible?',
      options: [
        {
          id: 'opt-2',
          text: '2',
          correct: true,
          feedback: 'Correct! Three trays use 15 counters (3 × 5 = 15); two counters remain, and 2 < 5.',
        },
        {
          id: 'opt-3',
          text: '3',
          correct: false,
          feedback: 'Three is the number of trays filled (the quotient), not the leftover remainder.',
        },
        {
          id: 'opt-5',
          text: '5',
          correct: false,
          feedback: 'The remainder must be strictly smaller than the tray size 5.',
        },
      ],
    },
  },
};
