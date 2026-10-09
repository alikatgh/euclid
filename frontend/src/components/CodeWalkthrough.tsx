import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { AlgorithmStep, CodeLanguage, CodeLessonContent } from '../types';
import { buildCodeProgram, getCodeExecution } from '../lib/codeWalkthrough';
import { LinkedNumber, LinkedText } from './MathConnections';

interface CodeWalkthroughProps {
  step: AlgorithmStep;
  language: CodeLanguage;
  withE0: boolean;
  content: CodeLessonContent;
}

const variableColors: Record<string, string> = {
  m: 'text-rod-m', n: 'text-rod-n', q: 'text-rod-q', r: 'text-rod-r', temp: 'text-muted',
};

function highlightVariables(source: string) {
  return source.split(/("(?:\\.|[^"\\])*"|\b(?:m|n|q|r|temp)\b)/g).map((part, index) => (
    variableColors[part]
      ? <span key={index} className={variableColors[part]}>{part}</span>
      : part.startsWith('"') ? part : <LinkedText key={index} text={part} />
  ));
}

export function CodeWalkthrough({ step, language, withE0, content }: CodeWalkthroughProps) {
  const program = useMemo(
    () => buildCodeProgram(content, language, withE0, step.initialM, step.initialN),
    [content, language, withE0, step.initialM, step.initialN],
  );
  const execution = getCodeExecution(step, language, content);
  const activeLineKey = execution.activeLineIds.join(',');
  const sourceRef = useRef<HTMLDivElement>(null);
  const [copyResult, setCopyResult] = useState<{ source: string; status: 'copied' | 'failed' } | null>(null);
  const copyStatus = copyResult?.source === program.source ? copyResult.status : 'idle';

  // Scroll only the source pane. The diagram and transport never move when a
  // statement becomes active, including after a font-size or viewport change.
  useLayoutEffect(() => {
    const pane = sourceRef.current;
    if (!pane) return;
    const revealActive = () => {
      const active = Array.from(pane.querySelectorAll<HTMLElement>('[data-active="true"]'));
      if (!active.length) return;
      const bounds = pane.getBoundingClientRect();
      const first = active[0].getBoundingClientRect();
      const last = active[active.length - 1].getBoundingClientRect();
      if (first.top < bounds.top + 8 || last.bottom > bounds.bottom - 8) {
        pane.scrollTop += first.top - bounds.top - Math.max(8, (pane.clientHeight - (last.bottom - first.top)) / 2);
      }
    };
    revealActive();
    const observer = new ResizeObserver(revealActive);
    observer.observe(pane);
    return () => observer.disconnect();
  }, [activeLineKey, program, step.stepIndex]);

  const copySource = async () => {
    try {
      await navigator.clipboard.writeText(program.source);
      setCopyResult({ source: program.source, status: 'copied' });
    } catch {
      setCopyResult({ source: program.source, status: 'failed' });
    }
  };

  return (
    <section aria-label={`${content.languageLabels[language]} code walkthrough`} className="h-full min-h-0 min-w-0 flex flex-col bg-surface border border-border">
      <header className="px-3 pt-3 pb-2 shrink-0">
        <div className="flex items-start justify-between gap-2">
          <h2 className="text-sm font-semibold">{content.title}</h2>
          <button type="button" onClick={copySource} className="shrink-0 border border-border px-2 py-1 text-xs font-mono hover:bg-border focus-visible:outline-2 focus-visible:outline-blue-600">
            {copyStatus === 'copied' ? content.copiedLabel : content.copyLabel}
          </button>
        </div>
        <p className="mt-1 text-xs text-muted leading-relaxed">{content.intro}</p>
        <p role="status" className="text-xs text-muted">{copyStatus === 'failed' ? content.copyFailedLabel : copyStatus === 'copied' ? content.copiedLabel : ''}</p>
      </header>

      <div ref={sourceRef} tabIndex={0} role="region" aria-label={content.sourceLabel} onKeyDown={(event) => { if (["ArrowLeft", "ArrowRight", " "].includes(event.key)) event.stopPropagation(); }} className="min-h-0 flex-1 overflow-auto border-y border-border py-2 focus-visible:outline-2 focus-visible:outline-blue-600">
        <pre style={{ lineHeight: 1.5 }} className="text-sm leading-[1.65] font-mono min-w-max m-0"><code>
          {program.lines.map((line, index) => {
            const active = execution.activeLineIds.includes(line.id);
            return (
              <span key={line.id} data-code-line={line.id} data-active={active} className={`grid grid-cols-[2.3rem_1fr_2rem] border-l-2 pr-2 ${active ? 'border-blue-600 bg-blue-500/10' : 'border-transparent'}`}>
                <span aria-hidden="true" className="text-dim text-right pr-2 select-none">{index + 1}</span>
                <span>{highlightVariables(line.text || ' ')}{'\n'}</span>
                <span aria-hidden="true" className={`text-xs self-center text-right select-none ${active ? 'text-rod-m font-bold' : 'text-dim'}`}>{line.phase}</span>
              </span>
            );
          })}
        </code></pre>
      </div>

      <div className="px-3 py-3 shrink-0 max-h-[44%] overflow-y-auto" aria-label={content.executionLabel}>
        <div className="flex items-baseline justify-between gap-2 mb-1">
          <h3 className="text-sm font-semibold">{execution.title}</h3>
          <span className="font-mono text-xs text-dim shrink-0">{step.phase}{step.pass ? ` · ${step.pass}` : ''}</span>
        </div>
        <p className="mt-2 mb-1 text-xs text-dim">{content.variablesLabel} · {content.beforeAfterLabel}</p>
        <dl className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-sm">
          {execution.variables.map((variable) => (
            <div key={variable.name} className="flex items-baseline gap-1.5">
              <dt className={`${variableColors[variable.name]} font-bold`}>{variable.name}</dt>
              <dd>
                {variable.before !== variable.after && <><span className="text-muted">{variable.before !== null ? <LinkedNumber value={variable.before} /> : '—'}</span><span className="text-dim"> → </span></>}
                <strong className={variableColors[variable.name]}>{variable.after !== null ? <LinkedNumber value={variable.after} /> : '—'}</strong>
              </dd>
            </div>
          ))}
        </dl>
        <p className="mt-2 text-sm text-muted leading-relaxed"><LinkedText text={execution.explanation} /></p>
        {execution.result !== null && <p className="mt-2 font-mono text-sm text-rod-gcd font-semibold">{content.resultLabel}: <LinkedNumber value={execution.result} /></p>}
      </div>
    </section>
  );
}
