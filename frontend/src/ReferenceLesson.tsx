import { useState, useEffect, useCallback, useRef } from 'react';
import type { CodeLanguage, CodeLessonContent, LessonData } from './types';
import { useAlgorithm } from './hooks/useAlgorithm';
import { schedulePlayback } from './lib/playback';
import { useTextScale } from './hooks/useTextScale';
import { useTheme } from './hooks/useTheme';
import { Header } from './components/Header';
import { Toolbar } from './components/Toolbar';
import { VisualizerCanvas } from './components/VisualizerCanvas';
import { Sidebar } from './components/Sidebar';
import { CodeWalkthrough } from './components/CodeWalkthrough';
import MathematicalText from './components/MathematicalText';
import { LinkedNumber, MathConnections } from './components/MathConnections';
import { countAlgorithmOperations } from './lib/algorithmOperations';
import { getStepReading } from './lib/mathematicalReading';
import './components/ReadingPanel.css';
import fallbackLesson from '../../content/lessons.json';

export function ReferenceLesson({ active = true }: { active?: boolean }) {
  const { theme, toggleTheme } = useTheme();

  // Bundle the authored lesson so the complete app works on a static host.
  const lessonData = fallbackLesson as unknown as LessonData;

  // Algorithm State
  const [m, setM] = useState<number>(119);
  const [n, setN] = useState<number>(544);
  const [withE0, setWithE0] = useState<boolean>(false);
  const [viewType, setViewType] = useState<'tape' | 'tiling'>('tape');
  const [currentStepIdx, setCurrentStepIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [lessonView, setLessonView] = useState<'explanation' | CodeLanguage>('explanation');
  const [explanationPanels, setExplanationPanels] = useState({ formula: true, steps: true, example: true });

  // Compute Steps
  const steps = useAlgorithm(m, n, withE0, lessonData);

  useEffect(() => { if (!active) setIsPlaying(false); }, [active]);

  // Autoplay loop
  useEffect(() => {
    return schedulePlayback({ active, playing: isPlaying, index: currentStepIdx, frameCount: steps.length, delay: Math.round(1600 / playbackSpeed) }, () => {
      const nextStep = Math.min(currentStepIdx + 1, steps.length - 1);
      if (nextStep === steps.length - 1) setIsPlaying(false);
      setCurrentStepIdx(nextStep);
    }, window);
  }, [active, isPlaying, currentStepIdx, steps.length, playbackSpeed]);

  const handleSeekStep = useCallback((stepIdx: number) => {
    setIsPlaying(false);
    setCurrentStepIdx(Math.max(0, Math.min(stepIdx, steps.length - 1)));
  }, [steps.length]);

  const handleNext = useCallback(() => {
    setIsPlaying(false);
    setCurrentStepIdx((prev) => Math.min(prev + 1, steps.length - 1));
  }, [steps.length]);

  const handlePrev = useCallback(() => {
    setIsPlaying(false);
    setCurrentStepIdx((prev) => Math.max(prev - 1, 0));
  }, []);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    setCurrentStepIdx(0);
  }, []);

  const handleMChange = (value: number) => {
    if (value === m) return;
    handleReset();
    setM(value);
  };

  const handleNChange = (value: number) => {
    if (value === n) return;
    handleReset();
    setN(value);
  };

  const handleToggleE0 = (value: boolean) => {
    if (value === withE0) return;
    handleReset();
    setWithE0(value);
  };

  const handleTogglePlay = useCallback(() => {
    if (steps.length === 0) return;
    if (currentStepIdx >= steps.length - 1) {
      setCurrentStepIdx(0);
      setIsPlaying(true);
    } else {
      setIsPlaying((prev) => !prev);
    }
  }, [currentStepIdx, steps.length]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!active) return;
      if (e.defaultPrevented || e.isComposing || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      const target = e.target;
      if (target instanceof HTMLElement && (
        target.isContentEditable ||
        target.closest('input, textarea, select, button, a[href], [data-reading-scroll], [role="button"], [role="slider"], [role="spinbutton"], [role="textbox"]')
      )) return;

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

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [active, handleNext, handlePrev, handleTogglePlay]);

  // Font Scaling State
  const { fontScale, setFontScale } = useTextScale();

  const handleIncreaseFontSize = () => {
    setFontScale((prev) => Math.min(1.35, +(prev + 0.1).toFixed(2)));
  };

  const handleDecreaseFontSize = () => {
    setFontScale((prev) => Math.max(0.85, +(prev - 0.1).toFixed(2)));
  };

  const handleResetFontSize = () => {
    setFontScale(1.0);
  };

  const currentStep = steps[currentStepIdx] || steps[0];
  const operations = countAlgorithmOperations(steps, currentStepIdx);
  const currentReadingRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (currentReadingRef.current) currentReadingRef.current.scrollTop = 0;
  }, [currentStep]);
  const codeContent = lessonData?.algorithm.codeWalkthrough || fallbackLesson.algorithm.codeWalkthrough as CodeLessonContent;
  const readingContent = lessonData?.algorithm.mathematicalReading || fallbackLesson.algorithm.mathematicalReading;

  return (
    <div className="h-full w-full flex flex-col bg-page text-main py-2.5 px-3.5 font-sans transition-colors duration-150 overflow-hidden">
      <div className="max-w-[1600px] w-full mx-auto flex-1 flex flex-col gap-2.5 min-h-0">
        <Header
          applicationName={lessonData?.application?.name || fallbackLesson.application.name}
          title={lessonData?.algorithm.title || "Algorithm E (Euclid's Algorithm)"}
          subtitle={lessonData?.algorithm.subtitle || 'Donald Knuth, The Art of Computer Programming'}
          withE0={withE0}
          onToggleE0={handleToggleE0}
          theme={theme}
          onToggleTheme={toggleTheme}
          fontScale={fontScale}
          onIncreaseFontSize={handleIncreaseFontSize}
          onDecreaseFontSize={handleDecreaseFontSize}
          onResetFontSize={handleResetFontSize}
        />

        {currentStep && (
          <MathConnections as="main" className="lesson-layout" resetKey={`${m}:${n}:${withE0}`}>
            {/* Col 1: Visualizer Canvas (Geometry) */}
            <div className="visual-reading-column">
              <div className="visual-reading-diagram">
                <VisualizerCanvas
                  step={currentStep}
                  viewType={viewType}
                  playbackSpeed={playbackSpeed}
                  labels={lessonData?.algorithm.visualization || fallbackLesson.algorithm.visualization}
                />
              </div>
              <section ref={currentReadingRef} className="current-reading" aria-labelledby="current-reading-title" tabIndex={0} data-reading-scroll>
                <h2 id="current-reading-title">{readingContent.currentStepTitle}</h2>
                <p className="mathematical-prose"><MathematicalText text={getStepReading(currentStep, readingContent)} /></p>
                <p className="text-xs text-muted mt-2" title="Abstract operations completed. An E3 frame includes the unsuccessful E2 test; timeline frames are not operation counts.">
                  Completed: <LinkedNumber value={operations.remainderDivisions} /> remainder divisions · <LinkedNumber value={operations.zeroTests} /> zero tests
                  {withE0 && <> · <LinkedNumber value={operations.orderingTests} /> ordering test</>}
                </p>
              </section>
            </div>

            {/* The same geometry and transport continue through either language. */}
            <div className="lesson-reading-column flex flex-col gap-2.5 min-h-0 min-w-0 overflow-hidden">
              <div className="shrink-0 flex flex-wrap items-center gap-x-3 gap-y-1.5">
                <span className="text-xs font-mono text-dim">{codeContent.continueLabel}</span>
                <div role="group" aria-label={codeContent.continueLabel} className="flex border border-border bg-surface">
                  {(['explanation', 'c', 'python'] as const).map((view) => (
                    <button key={view} type="button" aria-pressed={lessonView === view} onClick={() => setLessonView(view)} className={`px-2.5 py-1.5 text-xs font-mono focus-visible:outline-2 focus-visible:outline-blue-600 ${lessonView === view ? 'bg-blue-600 text-white font-bold' : 'text-main hover:bg-border'}`}>
                      {view === 'explanation' ? codeContent.explanationTabLabel : codeContent.languageLabels[view]}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex-1 min-h-0">
                {lessonView === 'explanation' ? (
                  <Sidebar
                    step={currentStep}
                    steps={steps}
                    stepsDefinitions={lessonData?.algorithm.steps_definition || fallbackLesson.algorithm.steps_definition}
                    content={readingContent}
                    withE0={withE0}
                    panels={explanationPanels}
                    onTogglePanel={(panel) => setExplanationPanels((previous) => ({ ...previous, [panel]: !previous[panel] }))}
                  />
                ) : (
                  <CodeWalkthrough key={lessonView} step={currentStep} language={lessonView} withE0={withE0} content={codeContent} />
                )}
              </div>
            </div>

            {/* Col 3: Controls, Presets, Scrubber & TAOCP Trace Table */}
            <Toolbar
              m={m}
              n={n}
              onMChange={handleMChange}
              onNChange={handleNChange}
              presets={lessonData?.algorithm.presets || []}
              viewType={viewType}
              onViewTypeChange={setViewType}
              isPlaying={isPlaying}
              onTogglePlay={handleTogglePlay}
              onNext={handleNext}
              onPrev={handlePrev}
              onReset={handleReset}
              canNext={currentStepIdx < steps.length - 1}
              canPrev={currentStepIdx > 0}
              currentStep={currentStepIdx}
              totalSteps={steps.length}
              steps={steps}
              onSeekStep={handleSeekStep}
              playbackSpeed={playbackSpeed}
              onPlaybackSpeedChange={setPlaybackSpeed}
            />
          </MathConnections>
        )}
      </div>
    </div>
  );
}

export default ReferenceLesson;
