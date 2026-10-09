import React, { useMemo } from 'react';
import type { AlgorithmStep } from '../types';
import { renderLinkedMath } from '../lib/mathConnections';

const roleMathOptions = {
  trust: (context: { command: string }) => context.command === '\\htmlClass',
  strict: false,
};

interface LatexFormulaProps {
  step: AlgorithmStep;
  displayMode?: 'full' | 'compact';
}

export const LatexFormula: React.FC<LatexFormulaProps> = ({ step, displayMode = 'full' }) => {
  const rendered = useMemo(() => {
    try {
      if (step.phase === 'E0') {
        if (step.type === 'E0_NOOP') {
          return {
            primary: renderLinkedMath(`\\htmlClass{text-rod-m}{${step.m}} \\ge \\htmlClass{text-rod-n}{${step.n}}`, roleMathOptions),
            secondary: null,
            invariant: null,
          };
        }
        const tex = `m \\longleftrightarrow n \\quad \\big(\\htmlClass{text-rod-m}{${step.m}} \\longleftrightarrow \\htmlClass{text-rod-n}{${step.newM || step.n}}\\big)`;
        return {
          primary: renderLinkedMath(tex, roleMathOptions),
          secondary: null,
          invariant: displayMode === 'full'
            ? renderLinkedMath(`\\gcd(${step.m}, ${step.newM || step.n}) = \\gcd(${step.newM || step.n}, ${step.m})`, roleMathOptions)
            : null,
        };
      }

      if (step.phase === 'E3') {
        const tex = `m \\leftarrow \\htmlClass{text-rod-m}{${step.nextM}}, \\quad n \\leftarrow \\htmlClass{text-rod-n}{${step.nextN}}`;
        return {
          primary: renderLinkedMath(tex, roleMathOptions),
          secondary: null,
          invariant: displayMode === 'full' && step.nextN !== undefined
            ? renderLinkedMath(`\\gcd(${step.m}, ${step.n}) = \\gcd(${step.nextM}, ${step.nextN})`, roleMathOptions)
            : null,
        };
      }

      if (step.r === 0) {
        const tex1 = `\\htmlClass{text-rod-r}{r = 0} \\implies \\gcd = \\htmlClass{text-rod-gcd}{\\mathbf{${step.n}}}`;
        const tex2 = `\\frac{\\htmlClass{text-rod-m}{${step.m}}}{\\htmlClass{text-rod-n}{${step.n}}} = \\htmlClass{text-rod-gcd}{\\mathbf{${step.q}}} \\quad (\\text{Exact})`;
        const verTex = step.verification
          ? `\\gcd(${step.initialM}, ${step.initialN}) = \\mathbf{${step.verification.gcd}} \\; \\big(${step.initialM} = ${step.verification.factorM} \\cdot \\mathbf{${step.verification.gcd}}, \\; ${step.initialN} = ${step.verification.factorN} \\cdot \\mathbf{${step.verification.gcd}}\\big)`
          : null;
        return {
          primary: renderLinkedMath(tex1, roleMathOptions),
          secondary: displayMode === 'full' ? renderLinkedMath(tex2, roleMathOptions) : null,
          invariant: displayMode === 'full' && verTex ? renderLinkedMath(verTex, roleMathOptions) : null,
        };
      }

      // Step E1: Both standard division equation and Knuth mixed fraction
      const tex1 = `\\htmlClass{text-rod-m}{${step.m}} = (\\htmlClass{text-rod-q}{${step.q}} \\times \\htmlClass{text-rod-n}{${step.n}}) + \\htmlClass{text-rod-r}{${step.r}}`;
      const tex2 = `\\frac{\\htmlClass{text-rod-m}{${step.m}}}{\\htmlClass{text-rod-n}{${step.n}}} = \\htmlClass{text-rod-q}{${step.q}}\\frac{\\htmlClass{text-rod-r}{${step.r}}}{\\htmlClass{text-rod-n}{${step.n}}}`;
      const invTex = `\\gcd(\\htmlClass{text-rod-m}{${step.m}}, \\htmlClass{text-rod-n}{${step.n}}) = \\gcd(\\htmlClass{text-rod-n}{${step.n}}, \\htmlClass{text-rod-r}{${step.r}})`;

      return {
        primary: renderLinkedMath(tex1, roleMathOptions),
        secondary: displayMode === 'full' ? renderLinkedMath(tex2, roleMathOptions) : null,
        invariant: displayMode === 'full' ? renderLinkedMath(invTex, roleMathOptions) : null,
      };
    } catch {
      return null;
    }
  }, [step, displayMode]);

  if (!rendered) {
    return <span className="font-math">{step.equation}</span>;
  }

  return (
    <div className="flex flex-col items-center gap-1 font-math">
      <div
        dangerouslySetInnerHTML={{ __html: rendered.primary }}
        className="text-base sm:text-lg leading-tight"
      />
      {rendered.secondary && (
        <div className="flex items-center gap-2 text-xs text-muted pt-1 border-t border-border/50">
          <span className="font-sans text-[10px] uppercase tracking-wider text-dim">Knuth §1.1:</span>
          <div
            dangerouslySetInnerHTML={{ __html: rendered.secondary }}
            className="text-sm leading-tight"
          />
        </div>
      )}
      {rendered.invariant && (
        <div className="flex items-center gap-2 text-xs text-dim pt-1 border-t border-border/40">
          <span className="font-sans text-[9px] uppercase tracking-wider text-dim font-mono">
            {step.r === 0 ? 'Verification:' : 'Invariant:'}
          </span>
          <div
            dangerouslySetInnerHTML={{ __html: rendered.invariant }}
            className="text-xs sm:text-sm text-main leading-tight"
          />
        </div>
      )}
    </div>
  );
};
