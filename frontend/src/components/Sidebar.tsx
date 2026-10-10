import { Fragment, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LatexFormula } from './LatexFormula';
import type { AlgorithmStep, MathematicalReadingContent, StepDefinition } from '../types';
import MathematicalText from './MathematicalText';
import { getReadingIntro, getWorkedExample } from '../lib/mathematicalReading';

interface SidebarProps {
  step: AlgorithmStep;
  steps: AlgorithmStep[];
  stepsDefinitions: StepDefinition[];
  content: MathematicalReadingContent;
  withE0: boolean;
  panels: { formula: boolean; steps: boolean; example: boolean };
  onTogglePanel: (panel: 'formula' | 'steps' | 'example') => void;
}

export const Sidebar = ({ step, steps, stepsDefinitions, content, withE0, panels, onTogglePanel }: SidebarProps) => {
  const sidebarRef = useRef<HTMLElement>(null);
  const articleRef = useRef<HTMLElement>(null);
  const paragraphs = useMemo(() => getWorkedExample(steps, content), [steps, content]);

  useEffect(() => {
    if (!panels.example) return;
    const article = articleRef.current;
    const sidebar = sidebarRef.current;
    const active = article?.querySelector<HTMLElement>('.reading-chunk[data-active-step="true"]');
    if (!article || !sidebar || !active) return;
    const revealInPane = (pane: HTMLElement) => {
      const paneBounds = pane.getBoundingClientRect();
      const activeBounds = active.getBoundingClientRect();
      const inset = Math.min(12, pane.clientHeight / 4);
      const visibleTop = paneBounds.top + pane.clientTop + inset;
      const visibleBottom = paneBounds.top + pane.clientTop + pane.clientHeight - inset;
      if (activeBounds.height > visibleBottom - visibleTop || activeBounds.top < visibleTop) {
        pane.scrollTop += activeBounds.top - visibleTop;
      } else if (activeBounds.bottom > visibleBottom) {
        pane.scrollTop += activeBounds.bottom - visibleBottom;
      }
    };
    const revealCurrentChunk = () => {
      // The article and the enclosing sidebar can each clip the same passage.
      // Reveal locally in both panes; never scroll the page or react to manual scrolling.
      revealInPane(article);
      revealInPane(sidebar);
    };
    let frame = 0;
    const scheduleReveal = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(revealCurrentChunk);
    };
    scheduleReveal();
    const observer = new ResizeObserver(scheduleReveal);
    observer.observe(article);
    observer.observe(sidebar);
    // A formula animation can change a preceding panel's height after navigation.
    for (const panel of sidebar.children) observer.observe(panel);
    // Block paragraph geometry changes when font scaling wraps inline passages.
    if (active.parentElement) observer.observe(active.parentElement);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [step.stepIndex, paragraphs, panels.example, panels.formula, panels.steps]);

  return (
    <aside ref={sidebarRef} className="explanation-stack">
      {/* 1. Live Formula & Current Values */}
      <section className="bg-surface border border-border p-3 shrink-0 shadow-sm">
        <div className={`panel-heading ${panels.formula ? 'mb-2' : ''}`}>
          <div className="panel-heading-copy">
            <span className="text-xs font-semibold uppercase tracking-wider text-dim font-mono">
              Live Formula
            </span>
            <div hidden={!panels.formula} className="ml-auto flex items-center gap-2.5 text-xs sm:text-sm">
              <span><span className="font-math italic text-xs font-normal">m</span>: <motion.strong data-math-value={String(step.m)} key={`m-${step.m}`} initial={{ scale: 1.25 }} animate={{ scale: 1 }} transition={{ duration: 0.2 }} className="text-rod-m font-math inline-block font-bold">{step.m}</motion.strong></span>
              <span><span className="font-math italic text-xs font-normal">n</span>: <motion.strong data-math-value={String(step.n)} key={`n-${step.n}`} initial={{ scale: 1.25 }} animate={{ scale: 1 }} transition={{ duration: 0.2 }} className="text-rod-n font-math inline-block font-bold">{step.n}</motion.strong></span>
              <span><span className="font-math italic text-xs font-normal">q</span>: <motion.strong data-math-value={step.q !== null ? String(step.q) : undefined} key={`q-${step.q}`} initial={{ scale: 1.25 }} animate={{ scale: 1 }} transition={{ duration: 0.2 }} className="text-rod-q font-math inline-block font-bold">{step.q !== null ? step.q : '—'}</motion.strong></span>
              <span><span className="font-math italic text-xs font-normal">r</span>: <motion.strong data-math-value={step.r !== null ? String(step.r) : undefined} key={`r-${step.r}`} initial={{ scale: 1.25 }} animate={{ scale: 1 }} transition={{ duration: 0.2 }} className="text-rod-r font-math inline-block font-bold">{step.r !== null ? step.r : '—'}</motion.strong></span>
            </div>
          </div>
          <PanelToggle label="Live Formula" enabled={panels.formula} controls="live-formula-content" onToggle={() => onTogglePanel('formula')} />
        </div>

        <div id="live-formula-content" hidden={!panels.formula} className="bg-page border border-border py-2.5 px-3 min-h-[58px] overflow-x-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={step.equation + step.badge}
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="w-full min-w-max flex items-center justify-center"
            >
              <LatexFormula step={step} />
            </motion.div>
          </AnimatePresence>
        </div>
      </section>

      {/* 2. Knuth's Step Flow Tracker with gliding layout indicator */}
      <section className="bg-surface border border-border p-3 shrink-0 shadow-sm">
        <div className={`panel-heading ${panels.steps ? 'mb-2' : ''}`}>
          <div className="panel-heading-copy">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-dim font-mono">
              Knuth's Algorithm Steps
            </h2>
            <span hidden={!panels.steps} className="ml-auto text-[10px] font-mono text-dim">
              {withE0 ? 'With E0' : 'Standard'}
            </span>
          </div>
          <PanelToggle label="Knuth's Algorithm Steps" enabled={panels.steps} controls="algorithm-steps-content" onToggle={() => onTogglePanel('steps')} />
        </div>

        <div id="algorithm-steps-content" hidden={!panels.steps} className="flex flex-col gap-1.5 relative">
          {stepsDefinitions.map((def) => {
            const isE0 = def.id === 'E0';
            const isSkipped = isE0 && !withE0;
            const isActive = step.phase === def.id;

            return (
              <div
                key={def.id}
                className={`relative flex items-center gap-2.5 py-1.5 px-2.5 transition-colors ${
                  isSkipped ? 'opacity-35 bg-page' : 'bg-page'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="active-step-glow"
                    className="absolute inset-0 border border-blue-500 bg-blue-500/10 pointer-events-none"
                    transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                  />
                )}
                <span
                  className={`relative z-10 font-mono text-xs font-bold px-2 py-0.5 transition-colors ${
                    isActive ? 'bg-blue-600 text-white' : 'bg-border text-muted'
                  }`}
                >
                  {def.id}
                </span>
                <div className="relative z-10 text-xs sm:text-[13px] text-muted leading-snug">
                  <strong className={isActive ? 'text-main font-semibold' : 'text-main'}>
                    {def.name}:
                  </strong>{' '}
                  <MathematicalText text={def.description} />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="worked-example" data-collapsed={!panels.example} aria-labelledby="worked-example-title">
        <header className="worked-example-heading">
          <div className="panel-heading">
            <h2 id="worked-example-title">{content.title}</h2>
            <PanelToggle label={content.title} enabled={panels.example} controls="worked-example-content" onToggle={() => onTogglePanel('example')} />
          </div>
          <p hidden={!panels.example}>{content.sourceNote}</p>
        </header>
        <article id="worked-example-content" hidden={!panels.example} ref={articleRef} className="worked-example-body mathematical-prose" tabIndex={0} aria-label={content.title} data-reading-scroll>
          <p className="reading-intro"><MathematicalText text={getReadingIntro(step.initialM, step.initialN, withE0, content)} /></p>
          {paragraphs.map((paragraph) => (
            <p key={paragraph.id} className="reading-paragraph">
              {paragraph.chunks.map((chunk, index) => {
                const isCurrent = chunk.stepIndex === step.stepIndex;
                return (
                  <Fragment key={chunk.id}>
                    {index > 0 ? ' ' : null}
                    <span
                      className="reading-chunk"
                      data-reading-chunk={chunk.id}
                      data-step-index={chunk.stepIndex}
                      data-step-phase={chunk.phase}
                      data-active-step={isCurrent ? 'true' : undefined}
                      aria-current={isCurrent ? 'step' : undefined}
                    >
                      <MathematicalText text={chunk.text} />
                    </span>
                  </Fragment>
                );
              })}
            </p>
          ))}
          <section className="reading-principles" aria-labelledby="reading-principles-title">
            <h3 id="reading-principles-title">{content.principles.title}</h3>
            <p><MathematicalText text={content.principles.invariant} /></p>
            <p><MathematicalText text={content.principles.termination} /></p>
          </section>
        </article>
      </section>
    </aside>
  );
};

function PanelToggle({ label, enabled, controls, onToggle }: {
  label: string;
  enabled: boolean;
  controls: string;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-label={label}
      aria-checked={enabled}
      aria-controls={controls}
      title={`${enabled ? 'Hide' : 'Show'} ${label}`}
      className="panel-toggle"
      onClick={onToggle}
    >
      <span>{enabled ? 'On' : 'Off'}</span>
      <span className="panel-toggle-track" aria-hidden="true" />
    </button>
  );
}
