/**
 * Generic Lesson Workbench component.
 *
 * Renders any `LessonSpec` into the exact 3-column interactive layout
 * established by Lesson 1 (Donald Knuth §1.1 Algorithm E).
 *
 * Column 1: Diagram (SVG) + "What is happening" (narrative + help mode)
 * Column 2: Explanation stack (Live Formula, Steps, Worked Example) OR Code Walkthrough (C / Python)
 * Column 3: Inputs & Presets + Playback player + Trace Table
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import katex from 'katex';
import type {
  DiagramNode,
  LessonInput,
  LessonSpec,
  StepContext,
  TraceStep,
} from './types.ts';
import { fill, KATEX_OPTIONS, prepareTex, TONE_CLASS, TONE_FILL, TONE_STROKE } from './tex.ts';

export interface LessonWorkbenchProps<I extends LessonInput, S extends TraceStep> {
  spec: LessonSpec<I, S>;
  onNavigateNext?: () => void;
  nextLessonLabel?: string;
  onNavigatePrev?: () => void;
  prevLessonLabel?: string;
}

/** Renders a string containing inline $...$ TeX expressions. */
export function MathText({ text, className = '' }: { text: string; className?: string }) {
  const parts = useMemo(() => {
    const segments: Array<{ isMath: boolean; content: string }> = [];
    const regex = /\$([^$]+)\$/g;
    let last = 0;
    let match: RegExpExecArray | null;
    while ((match = regex.exec(text)) !== null) {
      if (match.index > last) {
        segments.push({ isMath: false, content: text.slice(last, match.index) });
      }
      segments.push({ isMath: true, content: match[1] });
      last = match.index + match[0].length;
    }
    if (last < text.length) {
      segments.push({ isMath: false, content: text.slice(last) });
    }
    return segments;
  }, [text]);

  return (
    <span className={className}>
      {parts.map((p, idx) => {
        if (!p.isMath) return <span key={idx}>{p.content}</span>;
        try {
          const html = katex.renderToString(prepareTex(p.content), KATEX_OPTIONS);
          return <span key={idx} dangerouslySetInnerHTML={{ __html: html }} />;
        } catch {
          return <code key={idx}>{p.content}</code>;
        }
      })}
    </span>
  );
}

/** Renders a block TeX expression. */
export function MathBlock({ tex, className = '' }: { tex: string; className?: string }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(prepareTex(tex), KATEX_OPTIONS);
    } catch {
      return null;
    }
  }, [tex]);

  if (!html) return <div className={`font-mono text-xs ${className}`}>{tex}</div>;
  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}

export function LessonWorkbench<I extends LessonInput, S extends TraceStep>({
  spec,
  onNavigateNext,
  nextLessonLabel,
}: LessonWorkbenchProps<I, S>) {
  // Input state
  const [input, setInput] = useState<I>(() => ({ ...spec.defaultInput }));
  const [variant, setVariant] = useState<string>(() => spec.variants[0]?.id ?? 'standard');
  const [view, setView] = useState<string>(() => spec.views[0]?.id ?? 'default');

  // Compute execution trace
  const steps = useMemo(() => {
    return spec.run(input, variant);
  }, [spec, input, variant]);

  // Playback state
  const [stepIndex, setStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(1);
  const [isStepListOpen, setIsStepListOpen] = useState<boolean>(false);

  // Tab: 'explanation' | 'c' | 'python'
  const [activeTab, setActiveTab] = useState<'explanation' | 'c' | 'python'>('explanation');

  // Panel collapse state in Column 2
  const [panels, setPanels] = useState({ formula: true, steps: true, example: true });

  // Help mode state
  const [helpOpen, setHelpOpen] = useState<boolean>(false);
  const [helpFrame, setHelpFrame] = useState<number>(0);
  const [helpAnswer, setHelpAnswer] = useState<string | null>(null);

  // Copy status
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'failed'>('idle');

  // Scroll containers
  const currentReadingRef = useRef<HTMLElement>(null);
  const workedExampleBodyRef = useRef<HTMLElement>(null);
  const stepTimelineRef = useRef<HTMLDivElement>(null);

  // Clamp stepIndex when steps change
  const currentStep = steps[Math.max(0, Math.min(stepIndex, steps.length - 1))] ?? steps[0];
  const totalSteps = steps.length;
  const isTerminal = currentStep?.terminal || stepIndex >= totalSteps - 1;

  // Auto-play timer
  useEffect(() => {
    if (!isPlaying || isTerminal || helpOpen) return;
    const interval = Math.round(1600 / speed);
    const timer = window.setTimeout(() => {
      setStepIndex((idx) => {
        const next = Math.min(idx + 1, totalSteps - 1);
        if (next === totalSteps - 1) setIsPlaying(false);
        return next;
      });
    }, interval);
    return () => window.clearTimeout(timer);
  }, [isPlaying, isTerminal, helpOpen, speed, totalSteps, stepIndex]);

  // Reset scroll on step change
  useEffect(() => {
    if (currentReadingRef.current) {
      currentReadingRef.current.scrollTop = 0;
    }
  }, [stepIndex, helpOpen, helpFrame]);

  // Navigation handlers
  const handleNext = useCallback(() => {
    setIsPlaying(false);
    setHelpOpen(false);
    setStepIndex((idx) => Math.min(idx + 1, totalSteps - 1));
  }, [totalSteps]);

  const handlePrev = useCallback(() => {
    setIsPlaying(false);
    setHelpOpen(false);
    setStepIndex((idx) => Math.max(0, idx - 1));
  }, []);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    setHelpOpen(false);
    setStepIndex(0);
  }, []);

  const handleTogglePlay = useCallback(() => {
    setHelpOpen(false);
    if (isTerminal) {
      setStepIndex(0);
      setIsPlaying(true);
    } else {
      setIsPlaying((p) => !p);
    }
  }, [isTerminal]);

  // Keyboard navigation
  useEffect(() => {
    if (helpOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      const target = e.target as HTMLElement | null;
      if (target && target.closest('input, textarea, select, button, a[href], [data-reading-scroll]')) return;

      if (e.key === 'ArrowRight') {
        e.preventDefault();
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        handlePrev();
      } else if (e.key === ' ') {
        e.preventDefault();
        if (!e.repeat) handleTogglePlay();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [helpOpen, handleNext, handlePrev, handleTogglePlay]);

  // Context for step-dependent calculations
  const stepCtx: StepContext<I, S> = useMemo(() => {
    return {
      input,
      variant,
      steps,
      index: Math.max(0, Math.min(stepIndex, steps.length - 1)),
    };
  }, [input, variant, steps, stepIndex]);

  // Formulas for current step
  const formulaSet = useMemo(() => {
    return spec.formula(currentStep, stepCtx);
  }, [spec, currentStep, stepCtx]);

  // Diagram for current step
  const diagramScene = useMemo(() => {
    return spec.diagram(currentStep, { ...stepCtx, view });
  }, [spec, currentStep, stepCtx, view]);

  // Worked example paragraphs
  const workedParagraphs = useMemo(() => {
    return spec.workedExample.paragraphs(steps, input, variant);
  }, [spec, steps, input, variant]);

  // Code listing for active language
  const codeListing = activeTab === 'c' ? spec.code.languages.c : activeTab === 'python' ? spec.code.languages.python : null;

  const codeData = useMemo(() => {
    if (!codeListing) return null;
    const visibleLines = codeListing.lines
      .filter((l) => !l.variants || l.variants.includes(variant))
      .map((l) => ({
        ...l,
        text: fill(l.text, input),
      }));
    const source = visibleLines.map((l) => l.text).join('\n') + '\n';
    const activeLineIds = codeListing.activeLines(currentStep, stepCtx);
    const explanation = codeListing.explain(currentStep, stepCtx);
    return { lines: visibleLines, source, activeLineIds, explanation };
  }, [codeListing, variant, input, currentStep, stepCtx]);

  // Copy code handler
  const handleCopyCode = async () => {
    if (!codeData) return;
    try {
      await navigator.clipboard.writeText(codeData.source);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2000);
    } catch {
      setCopyStatus('failed');
      setTimeout(() => setCopyStatus('idle'), 2000);
    }
  };

  // Trace table rows
  const traceRows = useMemo(() => {
    return spec.trace.rows(steps, stepIndex);
  }, [spec, steps, stepIndex]);

  // Helper diagram scene when help is active
  const helpFrameData = spec.help.frames[Math.max(0, Math.min(helpFrame, spec.help.frames.length - 1))];

  return (
    <main className="lesson-layout" aria-label={spec.title}>
      {/* ================================= COLUMN 1 ================================= */}
      <div className="visual-reading-column">
        {/* Diagram panel */}
        <div className="visual-reading-diagram">
          <section className="bg-surface border border-border flex flex-col overflow-hidden h-full min-h-0 shadow-sm">
            {/* Header: Badge & Formula */}
            <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 px-3.5 py-2 border-b border-border bg-surface-elevated shrink-0 min-h-[38px]">
              <span className="text-sm font-semibold text-main">
                {helpOpen ? `Help · Frame ${helpFrame + 1} of ${spec.help.frames.length}` : currentStep.badge}
              </span>
              <div className="font-math max-w-full overflow-x-auto">
                {!helpOpen && <MathBlock tex={formulaSet.compact} className="text-xs sm:text-sm text-main" />}
              </div>
            </div>

            {/* SVG Visual Pane */}
            <div
              tabIndex={0}
              role="region"
              aria-label="Algorithm diagram"
              data-reading-scroll="true"
              className="euclid-diagram-pane w-full flex-1 min-h-0 bg-surface p-2 flex items-start justify-center overflow-auto"
            >
              {helpOpen && helpFrameData ? (
                <svg
                  viewBox={`0 0 ${helpFrameData.diagram.width} ${helpFrameData.diagram.height}`}
                  role="img"
                  aria-label={helpFrameData.diagram.description}
                  className="euclid-geometry w-full block max-h-full"
                  style={{ height: `${helpFrameData.diagram.height}px` }}
                >
                  {helpFrameData.diagram.nodes.map((node) => (
                    <RenderShape key={node.id} node={node} />
                  ))}
                </svg>
              ) : (
                <svg
                  viewBox={`0 0 ${diagramScene.width} ${diagramScene.height}`}
                  role="img"
                  aria-label={`${currentStep.badge}. ${diagramScene.description}`}
                  className="euclid-geometry w-full block max-h-full"
                  style={{ height: `${diagramScene.height}px` }}
                >
                  {diagramScene.nodes.map((node) => (
                    <RenderShape key={node.id} node={node} />
                  ))}
                </svg>
              )}
            </div>
          </section>
        </div>

        {/* Current Reading ("What is happening") */}
        <section
          ref={currentReadingRef}
          className="current-reading"
          aria-labelledby="current-reading-title"
          tabIndex={0}
          data-reading-scroll="true"
        >
          <h2 id="current-reading-title">
            {helpOpen ? spec.help.title : 'What is happening'}
          </h2>

          <p className="mathematical-prose">
            {helpOpen ? (
              <MathText text={helpFrameData?.explanation ?? ''} />
            ) : (
              <MathText text={spec.narrate(currentStep, stepCtx)} />
            )}
          </p>

          {/* Help controls & assessment */}
          <div className="flex flex-wrap gap-1.5 pt-2">
            <button
              type="button"
              className="features-control border border-border px-2.5 py-1 text-xs hover:bg-border transition-colors font-medium text-main"
              onClick={() => {
                setIsPlaying(false);
                setHelpOpen((h) => !h);
                setHelpFrame(0);
                setHelpAnswer(null);
              }}
            >
              {helpOpen ? 'Back to the original explanation' : 'I still don’t understand'}
            </button>

            {helpOpen && (
              <>
                <button
                  type="button"
                  className="features-control border border-border px-2 py-1 text-xs hover:bg-border disabled:opacity-40 text-main"
                  disabled={helpFrame === 0}
                  onClick={() => setHelpFrame((f) => Math.max(0, f - 1))}
                >
                  Previous
                </button>
                <button
                  type="button"
                  className="features-control border border-border px-2 py-1 text-xs hover:bg-border text-main"
                  onClick={() => setHelpFrame(0)}
                >
                  Replay
                </button>
                <button
                  type="button"
                  className="features-control border border-border px-2 py-1 text-xs hover:bg-border disabled:opacity-40 text-main"
                  disabled={helpFrame >= spec.help.frames.length - 1}
                  onClick={() => setHelpFrame((f) => Math.min(spec.help.frames.length - 1, f + 1))}
                >
                  Next
                </button>
              </>
            )}
          </div>

          {/* Comprehension check when on final help frame */}
          {helpOpen && helpFrame === spec.help.frames.length - 1 && (
            <section className="features-check mt-3 pt-3 border-t border-border">
              <h3 className="text-xs font-semibold text-muted mb-2">Comprehension Check:</h3>
              <p className="text-xs text-main mb-2 font-medium">
                <MathText text={spec.help.check.prompt} />
              </p>
              <div className="features-answer-options flex flex-col gap-1">
                {spec.help.check.options.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    aria-pressed={helpAnswer === opt.id}
                    onClick={() => setHelpAnswer(opt.id)}
                    className={`features-answer border border-border px-2.5 py-1.5 text-xs text-left transition-colors ${
                      helpAnswer === opt.id ? 'bg-border border-blue-500 font-semibold text-main' : 'hover:bg-border/60 text-main'
                    }`}
                  >
                    <MathText text={opt.text} />
                  </button>
                ))}
              </div>
              {helpAnswer && (
                <p role="status" className="features-answer-feedback text-xs mt-2 text-muted">
                  {spec.help.check.options.find((o) => o.id === helpAnswer)?.correct ? (
                    <span className="text-green-500 font-bold">Correct! </span>
                  ) : (
                    <span className="text-amber-500 font-bold">Try again. </span>
                  )}
                  {spec.help.check.options.find((o) => o.id === helpAnswer)?.feedback}
                </p>
              )}
            </section>
          )}
        </section>
      </div>

      {/* ================================= COLUMN 2 ================================= */}
      <div className="lesson-reading-column flex flex-col gap-2.5 min-h-0 min-w-0 overflow-hidden">
        {/* Tab switcher: Explanation | C | Python */}
        <div className="shrink-0 flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <span className="text-xs font-mono text-dim">Continue in code</span>
          <div role="group" aria-label="Code walkthrough tabs" className="flex border border-border bg-surface">
            <button
              type="button"
              aria-pressed={activeTab === 'explanation'}
              onClick={() => setActiveTab('explanation')}
              className={`px-2.5 py-1.5 text-xs font-mono focus-visible:outline-2 focus-visible:outline-blue-600 ${
                activeTab === 'explanation' ? 'bg-blue-600 text-white font-bold' : 'text-main hover:bg-border'
              }`}
            >
              Explanation
            </button>
            <button
              type="button"
              aria-pressed={activeTab === 'c'}
              onClick={() => setActiveTab('c')}
              className={`px-2.5 py-1.5 text-xs font-mono focus-visible:outline-2 focus-visible:outline-blue-600 ${
                activeTab === 'c' ? 'bg-blue-600 text-white font-bold' : 'text-main hover:bg-border'
              }`}
            >
              C
            </button>
            <button
              type="button"
              aria-pressed={activeTab === 'python'}
              onClick={() => setActiveTab('python')}
              className={`px-2.5 py-1.5 text-xs font-mono focus-visible:outline-2 focus-visible:outline-blue-600 ${
                activeTab === 'python' ? 'bg-blue-600 text-white font-bold' : 'text-main hover:bg-border'
              }`}
            >
              Python
            </button>
          </div>
        </div>

        {/* Tab content */}
        <div className="flex-1 min-h-0">
          {activeTab === 'explanation' ? (
            <aside className="explanation-stack">
              {/* Live Formula Section */}
              <section className="bg-surface border border-border p-3 shrink-0 shadow-sm">
                <div className={`panel-heading flex items-center justify-between ${panels.formula ? 'mb-2' : ''}`}>
                  <div className="panel-heading-copy flex items-center gap-2 flex-1">
                    <span className="text-xs font-semibold uppercase tracking-wider text-dim font-mono">Live Formula</span>
                    {panels.formula && (
                      <div className="ml-auto flex items-center gap-2.5 text-xs sm:text-sm font-mono">
                        {spec.variables.map((v) => {
                          const val = currentStep.values[v.key];
                          const toneCls = TONE_CLASS[v.tone];
                          return (
                            <span key={v.key} title={v.meaning}>
                              <span className="italic font-math text-xs">{v.symbol}</span>:
                              <strong className={`ml-1 font-bold ${toneCls}`}>
                                {val === null ? '—' : val}
                              </strong>
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-label="Toggle Live Formula panel"
                    aria-checked={panels.formula}
                    className="panel-toggle ml-2"
                    onClick={() => setPanels((p) => ({ ...p, formula: !p.formula }))}
                  >
                    <span>{panels.formula ? 'On' : 'Off'}</span>
                    <span className="panel-toggle-track" aria-hidden="true" />
                  </button>
                </div>

                {panels.formula && (
                  <div className="bg-page border border-border py-2.5 px-3 min-h-[58px] overflow-x-auto flex flex-col items-center gap-1 font-math">
                    <MathBlock tex={formulaSet.full} className="text-base sm:text-lg leading-tight text-main" />
                    {formulaSet.reference && (
                      <div className="flex items-center gap-2 text-xs text-muted pt-1 border-t border-border/50">
                        <span className="font-sans text-[10px] uppercase tracking-wider text-dim">
                          {formulaSet.reference.label}:
                        </span>
                        <MathBlock tex={formulaSet.reference.tex} className="text-sm leading-tight" />
                      </div>
                    )}
                    {formulaSet.invariant && (
                      <div className="flex items-center gap-2 text-xs text-dim pt-1 border-t border-border/40">
                        <span className="font-sans text-[9px] uppercase tracking-wider text-dim font-mono">
                          Invariant:
                        </span>
                        <MathBlock tex={formulaSet.invariant} className="text-xs sm:text-sm text-main leading-tight" />
                      </div>
                    )}
                  </div>
                )}
              </section>

              {/* Algorithm Steps Section */}
              <section className="bg-surface border border-border p-3 shrink-0 shadow-sm">
                <div className={`panel-heading flex items-center justify-between ${panels.steps ? 'mb-2' : ''}`}>
                  <div className="panel-heading-copy flex items-center gap-2 flex-1">
                    <h2 className="text-xs font-semibold uppercase tracking-wider text-dim font-mono">
                      {spec.title} Steps
                    </h2>
                    {panels.steps && (
                      <span className="ml-auto text-[10px] font-mono text-dim">
                        {spec.variants.find((v) => v.id === variant)?.label}
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-label="Toggle Algorithm Steps panel"
                    aria-checked={panels.steps}
                    className="panel-toggle ml-2"
                    onClick={() => setPanels((p) => ({ ...p, steps: !p.steps }))}
                  >
                    <span>{panels.steps ? 'On' : 'Off'}</span>
                    <span className="panel-toggle-track" aria-hidden="true" />
                  </button>
                </div>

                {panels.steps && (
                  <div className="flex flex-col gap-1.5 relative">
                    {spec.stepDefinitions.map((d) => {
                      const isActive = currentStep.phase === d.id;
                      const isDimmed = d.optional && !d.enabledIn?.includes(variant);
                      return (
                        <div
                          key={d.id}
                          className={`relative flex items-center gap-2.5 py-1.5 px-2.5 transition-colors border ${
                            isActive
                              ? 'border-blue-500 bg-blue-500/10'
                              : isDimmed
                              ? 'opacity-35 bg-page border-transparent'
                              : 'bg-page border-transparent'
                          }`}
                        >
                          <span
                            className={`relative z-10 font-mono text-xs font-bold px-2 py-0.5 transition-colors ${
                              isActive ? 'bg-blue-600 text-white' : 'bg-border text-muted'
                            }`}
                          >
                            {d.id}
                          </span>
                          <div className="relative z-10 text-xs sm:text-[13px] text-muted leading-snug">
                            <strong className={isActive ? 'text-main font-semibold' : 'text-main'}>
                              {d.name}:
                            </strong>{' '}
                            <MathText text={d.description} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>

              {/* Worked Example Section */}
              <section className="worked-example" data-collapsed={!panels.example} aria-labelledby="worked-example-title">
                <header className="worked-example-heading">
                  <div className="panel-heading flex items-center justify-between">
                    <h2 id="worked-example-title" className="text-sm font-semibold text-main">
                      {spec.workedExample.title}
                    </h2>
                    <button
                      type="button"
                      role="switch"
                      aria-label="Toggle Worked Example panel"
                      aria-checked={panels.example}
                      className="panel-toggle ml-2"
                      onClick={() => setPanels((p) => ({ ...p, example: !p.example }))}
                    >
                      <span>{panels.example ? 'On' : 'Off'}</span>
                      <span className="panel-toggle-track" aria-hidden="true" />
                    </button>
                  </div>
                  {panels.example && (
                    <p className="text-xs text-muted mt-1">{spec.workedExample.sourceNote}</p>
                  )}
                </header>

                {panels.example && (
                  <article
                    ref={workedExampleBodyRef}
                    className="worked-example-body mathematical-prose"
                    tabIndex={0}
                    aria-label={spec.workedExample.title}
                    data-reading-scroll="true"
                  >
                    <p className="reading-intro">
                      <MathText text={spec.workedExample.intro(input, variant)} />
                    </p>

                    {workedParagraphs.map((p, pIdx) => (
                      <p key={pIdx} className="reading-paragraph">
                        {p.chunks.map((chunk, cIdx) => {
                          const isActiveChunk = chunk.stepIndex === stepIndex;
                          return (
                            <React.Fragment key={cIdx}>
                              {cIdx > 0 ? ' ' : null}
                              <span
                                className={`reading-chunk ${
                                  isActiveChunk ? 'border-b-2 border-blue-500 bg-blue-500/10' : ''
                                }`}
                                data-active-step={isActiveChunk ? 'true' : undefined}
                                aria-current={isActiveChunk ? 'step' : undefined}
                              >
                                <MathText text={chunk.text} />
                              </span>
                            </React.Fragment>
                          );
                        })}
                      </p>
                    ))}

                    <section className="reading-principles border-t border-border mt-3 pt-2">
                      <h3 id="reading-principles-title" className="text-xs font-semibold text-main mb-1">
                        {spec.workedExample.principles.title}
                      </h3>
                      {spec.workedExample.principles.paragraphs.map((pr, prIdx) => (
                        <p key={prIdx} className="text-xs text-muted mb-1.5">
                          <MathText text={pr} />
                        </p>
                      ))}
                    </section>
                  </article>
                )}
              </section>
            </aside>
          ) : (
            /* Code Walkthrough (C / Python) */
            <section
              aria-label={`${codeListing?.label} code walkthrough`}
              className="h-full min-h-0 min-w-0 flex flex-col bg-surface border border-border"
            >
              <header className="px-3 pt-3 pb-2 shrink-0">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="text-sm font-semibold text-main">{spec.code.title}</h2>
                  <button
                    type="button"
                    onClick={handleCopyCode}
                    className="shrink-0 border border-border px-2 py-1 text-xs font-mono hover:bg-border focus-visible:outline-2 focus-visible:outline-blue-600 text-main"
                  >
                    {copyStatus === 'copied' ? 'Copied' : copyStatus === 'failed' ? 'Copy Failed' : 'Copy source'}
                  </button>
                </div>
                <p className="mt-1 text-xs text-muted leading-relaxed">{spec.code.intro}</p>
              </header>

              <div
                tabIndex={0}
                role="region"
                aria-label="Code listing"
                className="min-h-0 flex-1 overflow-auto border-y border-border py-2 focus-visible:outline-2 focus-visible:outline-blue-600 bg-page"
              >
                <pre className="text-xs sm:text-sm leading-[1.65] font-mono min-w-max m-0">
                  <code>
                    {codeData?.lines.map((l, lineIdx) => {
                      const isActive = codeData.activeLineIds.includes(l.id);
                      return (
                        <span
                          key={l.id}
                          data-code-line={l.id}
                          data-active={isActive}
                          className={`grid grid-cols-[2.3rem_1fr_2rem] border-l-2 pr-2 ${
                            isActive ? 'border-blue-600 bg-blue-500/10' : 'border-transparent'
                          }`}
                        >
                          <span aria-hidden="true" className="text-dim text-right pr-2 select-none">
                            {lineIdx + 1}
                          </span>
                          <span className="text-main">{l.text || ' '}</span>
                          <span
                            aria-hidden="true"
                            className={`text-xs self-center text-right select-none ${
                              isActive ? 'text-rod-m font-bold' : 'text-dim'
                            }`}
                          >
                            {l.phase || ''}
                          </span>
                        </span>
                      );
                    })}
                  </code>
                </pre>
              </div>

              {/* Execution explanation below code */}
              <div className="px-3 py-3 shrink-0 max-h-[44%] overflow-y-auto" aria-label="Step execution details">
                <div className="flex items-baseline justify-between gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-main">{codeData?.explanation.title}</h3>
                  <span className="font-mono text-xs text-dim shrink-0">{currentStep.badge}</span>
                </div>
                <p className="mt-1 text-xs text-dim">Variables · Before → After</p>
                <dl className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs sm:text-sm mt-1">
                  {spec.variables.map((v) => {
                    const before = currentStep.values[v.key];
                    const after = currentStep.next?.[v.key] ?? before;
                    const toneCls = TONE_CLASS[v.tone];
                    return (
                      <div key={v.key} className="flex items-baseline gap-1.5">
                        <dt className={`${toneCls} font-bold`}>{v.symbol}</dt>
                        <dd>
                          {before !== after && (
                            <>
                              <span className="text-muted">{before === null ? '—' : before}</span>
                              <span className="text-dim"> → </span>
                            </>
                          )}
                          <strong className={toneCls}>{after === null ? '—' : after}</strong>
                        </dd>
                      </div>
                    );
                  })}
                </dl>
                <p className="mt-2 text-xs sm:text-sm text-muted leading-relaxed">
                  <MathText text={codeData?.explanation.explanation ?? ''} />
                </p>
              </div>
            </section>
          )}
        </div>
      </div>

      {/* ================================= COLUMN 3 ================================= */}
      <div className="lesson-controls-column flex min-h-0 flex-col gap-2.5 max-lg:shrink-0 max-lg:h-[40rem]">
        <aside className="flex flex-col gap-2.5 h-full min-w-0 overflow-y-auto overscroll-contain">
          {/* Inputs & Presets Section */}
          <section className="bg-surface border border-border p-3 shrink-0 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-dim font-mono">
                Inputs & Presets
              </span>
              {spec.views.length > 1 && (
                <div className="flex bg-page border border-border overflow-hidden">
                  {spec.views.map((v) => (
                    <button
                      key={v.id}
                      onClick={() => setView(v.id)}
                      className={`px-2 py-0.5 text-[11px] font-mono transition-colors ${
                        view === v.id ? 'bg-border text-main font-semibold' : 'text-muted hover:text-main'
                      }`}
                    >
                      {v.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Algorithm Variant Switch */}
            {spec.variants.length > 1 && (
              <div className="flex bg-page border border-border overflow-hidden mb-2">
                {spec.variants.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => {
                      setVariant(v.id);
                      setStepIndex(0);
                      setIsPlaying(false);
                    }}
                    className={`flex-1 py-1 px-1 text-[11px] font-mono transition-colors text-center truncate ${
                      variant === v.id ? 'bg-border text-main font-semibold' : 'text-muted hover:text-main'
                    }`}
                    title={v.label}
                  >
                    {v.label}
                  </button>
                ))}
              </div>
            )}

            {/* Numeric inputs */}
            <div className="flex items-center gap-2 mb-2">
              {spec.inputs.map((inp, idx) => (
                <React.Fragment key={inp.key}>
                  {idx > 0 && <span className="text-xs text-dim font-mono">&</span>}
                  <div className="flex items-center gap-1.5 flex-1">
                    <label htmlFor={`input-${inp.key}`} className="font-mono text-xs font-semibold text-muted">
                      {inp.label}:
                    </label>
                    <input
                      id={`input-${inp.key}`}
                      type="number"
                      min={inp.min}
                      max={inp.max}
                      value={input[inp.key] ?? inp.min}
                      onChange={(e) => {
                        const val = Math.min(inp.max, Math.max(inp.min, Math.trunc(e.target.valueAsNumber) || inp.min));
                        setInput((prev) => ({ ...prev, [inp.key]: val }));
                        setStepIndex(0);
                        setIsPlaying(false);
                      }}
                      className="w-full bg-page border border-border px-2 py-1 text-xs font-mono text-main outline-none focus:border-blue-500"
                    />
                  </div>
                </React.Fragment>
              ))}
            </div>

            {/* Presets */}
            {spec.presets.length > 0 && (
              <div className="flex flex-col gap-1 pt-2 border-t border-border/60">
                <span className="text-[10px] font-mono uppercase tracking-wider text-dim">Presets:</span>
                <div className="grid grid-cols-2 gap-1 max-h-[84px] overflow-y-auto pr-0.5">
                  {spec.presets.map((p) => {
                    const isSelected = Object.entries(p.input).every(([k, v]) => input[k] === v);
                    return (
                      <button
                        key={p.name}
                        onClick={() => {
                          setInput({ ...p.input });
                          setStepIndex(0);
                          setIsPlaying(false);
                        }}
                        className={`text-[10px] font-mono px-1.5 py-1 text-left border transition-colors truncate ${
                          isSelected
                            ? 'bg-border border-border text-main font-semibold'
                            : 'bg-page border-border text-muted hover:text-main hover:border-muted'
                        }`}
                        title={p.name}
                      >
                        {p.name}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </section>

          {/* Playback Controls Section */}
          <section className="execution-player bg-surface border border-border p-3 shrink-0 shadow-sm flex flex-col gap-1.5" aria-label="Algorithm playback">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-main">Playback</h2>
              <span className="text-xs text-muted whitespace-nowrap tabular-nums">
                {currentStep.badge.split(':')[0]} · {stepIndex + 1} / {totalSteps}
              </span>
            </div>

            {/* Seek bar */}
            <input
              type="range"
              min={0}
              max={Math.max(0, totalSteps - 1)}
              step={1}
              value={stepIndex}
              disabled={totalSteps < 2}
              onChange={(e) => {
                setIsPlaying(false);
                setStepIndex(e.currentTarget.valueAsNumber);
              }}
              aria-label="Seek to algorithm step"
              className="execution-player__seek w-full"
              style={{ '--player-progress': `${totalSteps > 1 ? (stepIndex / (totalSteps - 1)) * 100 : 0}%` } as React.CSSProperties}
            />

            {/* Control buttons */}
            <div className="flex flex-wrap items-center gap-1">
              <div className="flex items-center gap-1" role="group" aria-label="Playback controls">
                <button
                  type="button"
                  onClick={handleReset}
                  className="flex h-9 w-9 shrink-0 items-center justify-center border border-border bg-page text-main transition-colors hover:bg-border"
                  aria-label="Restart from first step"
                  title="Restart from first step"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 10a8 8 0 1 1 1 7M4 4v6h6" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={handlePrev}
                  disabled={stepIndex === 0}
                  className="flex h-9 w-9 shrink-0 items-center justify-center border border-border bg-page text-main transition-colors hover:bg-border disabled:opacity-40"
                  aria-label="Previous step"
                  title="Previous step (Left Arrow)"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M5 4h2v16H5zM19 4 8 12l11 8z" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={handleTogglePlay}
                  className="flex h-11 w-11 shrink-0 items-center justify-center bg-blue-600 hover:bg-blue-500 text-white transition-colors"
                  aria-label={isPlaying ? 'Pause playback' : isTerminal ? 'Replay' : 'Play steps'}
                  title="Play / Pause (Spacebar)"
                >
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                    {isPlaying ? <path d="M6 4h4v16H6zM14 4h4v16h-4z" /> : <path d="m7 4 13 8-13 8z" />}
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={handleNext}
                  disabled={stepIndex >= totalSteps - 1}
                  className="flex h-9 w-9 shrink-0 items-center justify-center border border-border bg-page text-main transition-colors hover:bg-border disabled:opacity-40"
                  aria-label="Next step"
                  title="Next step (Right Arrow)"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17 4h2v16h-2zM5 4l11 8-11 8z" />
                  </svg>
                </button>
              </div>

              <select
                value={speed}
                onChange={(e) => setSpeed(Number(e.currentTarget.value))}
                aria-label="Playback speed"
                className="ml-auto h-9 min-w-[3.5rem] shrink-0 bg-page border border-border px-1.5 text-xs text-main tabular-nums"
              >
                <option value={0.5}>0.5×</option>
                <option value={1}>1×</option>
                <option value={1.5}>1.5×</option>
                <option value={2}>2×</option>
              </select>
            </div>

            {/* Step list dropdown */}
            <div className="pt-1 border-t border-border/60">
              <button
                type="button"
                onClick={() => setIsStepListOpen((o) => !o)}
                aria-expanded={isStepListOpen}
                className="flex min-h-7 w-full items-center justify-between text-xs font-medium text-muted hover:text-main"
              >
                <span>Step list</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d={isStepListOpen ? 'm6 15 6-6 6 6' : 'm6 9 6 6 6-6'} />
                </svg>
              </button>

              {isStepListOpen && (
                <div
                  ref={stepTimelineRef}
                  className="execution-player__steps flex flex-wrap gap-1 max-h-28 overflow-y-auto overscroll-contain p-1 border border-border/40 mt-1"
                >
                  {steps.map((st, idx) => {
                    const isCur = idx === stepIndex;
                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setIsPlaying(false);
                          setStepIndex(idx);
                        }}
                        aria-current={isCur ? 'step' : undefined}
                        className={`py-1 px-2 text-center font-mono text-xs border transition-colors ${
                          isCur
                            ? 'bg-blue-600 border-blue-600 text-white font-bold'
                            : 'bg-page border-border text-muted hover:text-main hover:bg-border'
                        }`}
                      >
                        {st.phase}
                        {st.pass ? `.${st.pass}` : ''}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </section>

          {/* Trace Table Section */}
          <section className="bg-surface border border-border p-3 flex-1 flex flex-col overflow-hidden shadow-sm min-h-32">
            <div className="flex items-center justify-between mb-2 shrink-0">
              <span className="text-xs font-semibold uppercase tracking-wider text-dim font-mono">
                {spec.trace.title}
              </span>
              <span className="text-[10px] font-mono text-dim">{spec.trace.caption}</span>
            </div>

            <div className="border border-border bg-page flex-1 overflow-y-auto min-h-0">
              <table className="w-full text-left font-mono text-xs border-collapse">
                <thead>
                  <tr className="border-b border-border bg-surface text-dim text-[11px] sticky top-0 z-10">
                    {spec.trace.columns.map((col) => (
                      <th key={col.key} className="py-1 px-2 font-semibold">
                        {col.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {traceRows.length === 0 ? (
                    <tr>
                      <td colSpan={spec.trace.columns.length} className="py-3 text-center text-dim text-[11px]">
                        No passes recorded yet
                      </td>
                    </tr>
                  ) : (
                    traceRows.map((row, rIdx) => {
                      const isActiveRow = currentStep.pass !== undefined
                        ? row.label === `Pass ${currentStep.pass}` || (currentStep.phase === 'E0' && row.label === 'E0')
                        : row.stepIndex === stepIndex;

                      return (
                        <tr
                          key={rIdx}
                          onClick={() => {
                            setIsPlaying(false);
                            setStepIndex(row.stepIndex);
                          }}
                          className={`cursor-pointer transition-colors border-b border-border/40 ${
                            isActiveRow ? 'bg-blue-600/15 text-blue-400 font-bold' : 'hover:bg-surface text-muted'
                          }`}
                          title={`Jump to step ${row.stepIndex + 1}`}
                        >
                          {spec.trace.columns.map((col) => {
                            const val = row.cells[col.key];
                            const toneCls = col.tone ? TONE_CLASS[col.tone] : '';
                            return (
                              <td key={col.key} className={`py-1 px-2 ${toneCls}`}>
                                {val ?? '—'}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* Navigation to next lesson */}
          {nextLessonLabel && (
            <button
              type="button"
              onClick={onNavigateNext}
              className="shrink-0 border border-border bg-surface px-3 py-2 text-sm text-main hover:bg-border text-left"
            >
              {nextLessonLabel} →
            </button>
          )}
        </aside>
      </div>
    </main>
  );
}

/** Helper component to render an individual SVG node. */
function RenderShape({ node: n }: { node: DiagramNode }) {
  const stroke = n.tone ? TONE_STROKE[n.tone] : 'var(--border-color)';
  const fill = n.tone ? TONE_FILL[n.tone] : 'none';

  switch (n.type) {
    case 'rect':
      return (
        <rect
          id={n.id}
          x={n.x}
          y={n.y}
          width={Math.max(0, n.width)}
          height={Math.max(0, n.height)}
          fill={n.outline ? 'none' : fill}
          stroke={stroke}
          strokeWidth={1.5}
          strokeDasharray={n.dashed ? '5 4' : undefined}
          opacity={n.opacity ?? 1}
          data-math-value={n.value}
        >
          {n.title && <title>{n.title}</title>}
        </rect>
      );
    case 'circle':
      return (
        <circle
          id={n.id}
          cx={n.x}
          cy={n.y}
          r={Math.max(0, n.r)}
          fill={n.outline ? 'none' : fill}
          stroke={stroke}
          strokeWidth={1.5}
          opacity={n.opacity ?? 1}
          data-math-value={n.value}
        />
      );
    case 'line':
      return (
        <line
          id={n.id}
          x1={n.x}
          y1={n.y}
          x2={n.x2}
          y2={n.y2}
          stroke={stroke}
          strokeWidth={1.5}
          strokeDasharray={n.dashed ? '5 4' : undefined}
          opacity={n.opacity ?? 1}
        />
      );
    case 'path':
      return (
        <path
          id={n.id}
          d={n.d}
          fill="none"
          stroke={stroke}
          strokeWidth={1.5}
          strokeDasharray={n.dashed ? '5 4' : undefined}
          opacity={n.opacity ?? 1}
        />
      );
    case 'text':
      return (
        <text
          id={n.id}
          x={n.x}
          y={n.y}
          fill={stroke}
          textAnchor={n.anchor ?? 'start'}
          fontWeight={n.weight ?? 'normal'}
          fontSize={n.size === 'sm' ? 12 : n.size === 'lg' ? 16 : 14}
          fontFamily="var(--font-sans)"
          opacity={n.opacity ?? 1}
        >
          {n.text}
        </text>
      );
    default:
      return null;
  }
}
