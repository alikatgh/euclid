import React, { useEffect, useRef, useState } from 'react';
import type { AlgorithmStep, Preset } from '../types';
import './Toolbar.css';
import { LinkedNumber, LinkedText, MathConnectionStatus } from './MathConnections';

interface ToolbarProps {
  m: number;
  n: number;
  onMChange: (val: number) => void;
  onNChange: (val: number) => void;
  presets: Preset[];
  viewType: 'tape' | 'tiling';
  onViewTypeChange: (type: 'tape' | 'tiling') => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onNext: () => void;
  onPrev: () => void;
  onReset: () => void;
  canNext: boolean;
  canPrev: boolean;
  currentStep: number;
  totalSteps: number;
  steps: AlgorithmStep[];
  onSeekStep: (stepIdx: number) => void;
  playbackSpeed: number;
  onPlaybackSpeedChange: (speed: number) => void;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  m,
  n,
  onMChange,
  onNChange,
  presets,
  viewType,
  onViewTypeChange,
  isPlaying,
  onTogglePlay,
  onNext,
  onPrev,
  onReset,
  canNext,
  canPrev,
  currentStep,
  totalSteps,
  steps,
  onSeekStep,
  playbackSpeed,
  onPlaybackSpeedChange,
}) => {
  const activeStepObj = steps[currentStep];
  const timelineRef = useRef<HTMLDivElement>(null);
  const [isStepListOpen, setIsStepListOpen] = useState(false);
  const hasSteps = steps.length > 0;
  const seekMax = Math.max(steps.length - 1, 0);
  const seekValue = Math.max(0, Math.min(currentStep, seekMax));
  const isComplete = hasSteps && seekValue === seekMax;
  const phaseLabel = activeStepObj
    ? `${activeStepObj.phase}${activeStepObj.phase !== 'E0' && activeStepObj.pass ? `.${activeStepObj.pass}` : ''}`
    : '—';
  const playLabel = isPlaying ? 'Pause playback' : isComplete ? 'Replay from the first step' : 'Play steps';
  const seekProgress = seekMax > 0 ? (seekValue / seekMax) * 100 : 0;
  const focusStyle = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--border-focus)]';
  const transportStyle = `flex h-9 w-9 shrink-0 items-center justify-center border border-border bg-page text-main transition-colors hover:bg-border disabled:opacity-40 disabled:cursor-not-allowed ${focusStyle}`;
  const rowCount = Math.ceil(steps.length / 4);
  const timelineRows: { step: AlgorithmStep; index: number }[][] = [];
  let rowOffset = 0;

  for (let row = 0; row < rowCount; row += 1) {
    const rowSize = Math.floor(steps.length / rowCount) + (row < steps.length % rowCount ? 1 : 0);
    timelineRows.push(steps.slice(rowOffset, rowOffset + rowSize).map((step, index) => ({
      step,
      index: rowOffset + index,
    })));
    rowOffset += rowSize;
  }

  useEffect(() => {
    const timeline = timelineRef.current;
    const activeButton = timeline?.querySelector<HTMLButtonElement>('[aria-current="step"]');
    if (!timeline || !activeButton) return;

    const keepCurrentStepVisible = () => {
      const timelineBounds = timeline.getBoundingClientRect();
      const buttonBounds = activeButton.getBoundingClientRect();
      const padding = parseFloat(window.getComputedStyle(timeline).paddingTop);
      if (buttonBounds.top < timelineBounds.top + padding) {
        timeline.scrollTop += buttonBounds.top - timelineBounds.top - padding;
      } else if (buttonBounds.bottom > timelineBounds.bottom - padding) {
        timeline.scrollTop += buttonBounds.bottom - timelineBounds.bottom + padding;
      }
    };

    keepCurrentStepVisible();
    const resizeObserver = new ResizeObserver(keepCurrentStepVisible);
    resizeObserver.observe(timeline);
    return () => resizeObserver.disconnect();
  }, [currentStep, steps.length, isStepListOpen]);

  return (
    <aside className="flex flex-col gap-2.5 h-full min-w-0 overflow-y-auto overscroll-contain">
      {/* 1. Algorithm Inputs & Presets Card */}
      <section className="bg-surface border border-border p-3 shrink-0 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-dim font-mono">
            Inputs & Presets
          </span>
          {/* View Mode Toggle */}
          <div className="flex bg-page border border-border overflow-hidden">
            <button
              onClick={() => onViewTypeChange('tape')}
              className={`px-2 py-0.5 text-[11px] font-mono transition-colors ${
                viewType === 'tape' ? 'bg-border text-main font-semibold' : 'text-muted hover:text-main'
              }`}
            >
              Tape
            </button>
            <button
              onClick={() => onViewTypeChange('tiling')}
              className={`px-2 py-0.5 text-[11px] font-mono transition-colors ${
                viewType === 'tiling' ? 'bg-border text-main font-semibold' : 'text-muted hover:text-main'
              }`}
            >
              2D Tiling
            </button>
          </div>
        </div>

        {/* Inputs */}
        <div className="flex items-center gap-2 mb-2">
          <div className="flex items-center gap-1.5 flex-1">
            <label htmlFor="col3-m-input" className="font-mono text-xs font-semibold text-muted">m:</label>
            <input
              id="col3-m-input"
              data-math-value={m}
              type="number"
              min={1}
              max={9999}
              value={m}
              onChange={(e) => onMChange(Math.min(9999, Math.max(1, Math.trunc(e.target.valueAsNumber) || 1)))}
              className="w-full bg-page border border-border px-2 py-1 text-xs font-mono text-main outline-none focus:border-blue-500"
            />
          </div>
          <span className="text-xs text-dim font-mono">&</span>
          <div className="flex items-center gap-1.5 flex-1">
            <label htmlFor="col3-n-input" className="font-mono text-xs font-semibold text-muted">n:</label>
            <input
              id="col3-n-input"
              data-math-value={n}
              type="number"
              min={1}
              max={9999}
              value={n}
              onChange={(e) => onNChange(Math.min(9999, Math.max(1, Math.trunc(e.target.valueAsNumber) || 1)))}
              className="w-full bg-page border border-border px-2 py-1 text-xs font-mono text-main outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Presets List */}
        {presets.length > 0 && (
          <div className="flex flex-col gap-1 pt-2 border-t border-border/60">
            <span className="text-[10px] font-mono uppercase tracking-wider text-dim">Presets:</span>
            <div className="grid grid-cols-2 gap-1 max-h-[84px] overflow-y-auto pr-0.5">
              {presets.map((preset) => {
                const isActive = preset.m === m && preset.n === n;
                return (
                  <button
                    key={preset.name}
                    onClick={() => {
                      onMChange(preset.m);
                      onNChange(preset.n);
                    }}
                    className={`text-[10px] font-mono px-1.5 py-1 text-left border transition-colors truncate ${
                      isActive
                        ? 'bg-border border-border text-main font-semibold'
                        : 'bg-page border-border text-muted hover:text-main hover:border-muted'
                    }`}
                    title={preset.name}
                  >
                    <LinkedText text={preset.name} interactive={false} />
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* 2. Playback Transport, Speed & Timeline Scrubber */}
      <section className="execution-player bg-surface border border-border p-3 shrink-0 shadow-sm flex flex-col gap-1.5" aria-label="Algorithm playback">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-main">
            Playback
          </h2>
          <span className="text-xs text-muted whitespace-nowrap tabular-nums">
            {phaseLabel} · {hasSteps ? seekValue + 1 : 0} / {totalSteps}
          </span>
        </div>

        <input
          type="range"
          min={0}
          max={seekMax}
          step={1}
          value={seekValue}
          disabled={steps.length < 2}
          onChange={(event) => onSeekStep(event.currentTarget.valueAsNumber)}
          aria-label="Seek to algorithm step"
          aria-valuetext={hasSteps ? `Step ${seekValue + 1} of ${totalSteps}, ${phaseLabel}: ${activeStepObj?.badge ?? ''}` : 'No steps available'}
          title="Seek to a step (Arrow keys, Home or End)"
          className={`execution-player__seek ${focusStyle}`}
          style={{ '--player-progress': `${seekProgress}%` } as React.CSSProperties}
        />

        <div className="flex flex-wrap items-center gap-1">
          <div className="flex items-center gap-1" role="group" aria-label="Playback controls">
            <button
              type="button"
              onClick={onReset}
              disabled={!hasSteps}
              className={transportStyle}
              aria-label="Restart from the first step"
              title="Restart from the first step"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" focusable="false">
                <path d="M4 10a8 8 0 1 1 1 7M4 4v6h6" />
              </svg>
            </button>
            <button
              type="button"
              onClick={onPrev}
              disabled={!hasSteps || !canPrev || seekValue === 0}
              aria-label="Previous step"
              className={transportStyle}
              title="Previous step (Left Arrow key)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
                <path d="M5 4h2v16H5zM19 4 8 12l11 8z" />
              </svg>
            </button>
            <button
              type="button"
              onClick={onTogglePlay}
              disabled={!hasSteps}
              className={`flex h-11 w-11 shrink-0 items-center justify-center bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors ${focusStyle}`}
              aria-label={playLabel}
              title={`${playLabel} (Spacebar)`}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
                {isPlaying ? <path d="M6 4h4v16H6zM14 4h4v16h-4z" /> : <path d="m7 4 13 8-13 8z" />}
              </svg>
            </button>
            <button
              type="button"
              onClick={onNext}
              disabled={!hasSteps || !canNext || seekValue === seekMax}
              aria-label="Next step"
              className={transportStyle}
              title="Next step (Right Arrow key)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
                <path d="M17 4h2v16h-2zM5 4l11 8-11 8z" />
              </svg>
            </button>
          </div>
          <label htmlFor="playback-speed" className="sr-only">Playback speed</label>
          <select
            id="playback-speed"
            value={playbackSpeed}
            onChange={(event) => onPlaybackSpeedChange(Number(event.currentTarget.value))}
            title="Playback speed"
            className={`ml-auto h-9 min-w-[3.5rem] shrink-0 bg-page border border-border px-1.5 text-xs text-main tabular-nums ${focusStyle}`}
          >
            {[0.5, 1, 1.5, 2].map((speed) => <option key={speed} value={speed}>{speed}×</option>)}
          </select>
        </div>

        {hasSteps && (
          <div className="pt-1 border-t border-border/60">
            <button
              type="button"
              onClick={() => setIsStepListOpen((open) => !open)}
              aria-expanded={isStepListOpen}
              aria-controls="step-timeline"
              className={`flex min-h-7 w-full items-center justify-between text-xs font-medium text-muted hover:text-main ${focusStyle}`}
              title="Show or hide direct step navigation"
            >
              Step list
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" focusable="false">
                <path d={isStepListOpen ? 'm6 15 6-6 6 6' : 'm6 9 6 6 6-6'} />
              </svg>
            </button>
            <div id="step-timeline" ref={timelineRef} hidden={!isStepListOpen} className="execution-player__steps flex flex-col gap-1 max-h-24 overflow-y-auto overscroll-contain p-1" role="group" aria-label="Direct step navigation">
              {timelineRows.map((row, rowIndex) => (
                <div key={rowIndex} className="grid gap-1 shrink-0" style={{ gridTemplateColumns: `repeat(${row.length}, minmax(0, 1fr))` }}>
                  {row.map(({ step: st, index: idx }) => {
                    const isActive = idx === currentStep;
                    const isPast = idx < currentStep;
                    const phaseLabel = st.phase === 'E0' ? 'E0' : `${st.phase}${st.pass ? `.${st.pass}` : ''}`;

                    return (
                      <button
                        type="button"
                        key={idx}
                        onClick={() => onSeekStep(idx)}
                        aria-current={isActive ? 'step' : undefined}
                        aria-label={`Step ${idx + 1} of ${totalSteps}, ${phaseLabel}: ${st.badge}`}
                        title={`Step ${idx + 1}: ${st.badge} — ${st.equation}`}
                        className={`min-w-0 py-1 px-1 text-center font-mono text-xs border transition-colors ${focusStyle} ${
                          isActive
                            ? 'bg-blue-600 border-blue-600 text-white font-bold'
                            : isPast
                            ? 'bg-surface border-border text-main hover:bg-border'
                            : 'bg-page border-border text-muted hover:text-main hover:border-muted'
                        }`}
                      >
                        {phaseLabel}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        )}
        <MathConnectionStatus />
      </section>

      {/* 3. Donald Knuth TAOCP Execution Trace Table (Vol 1 §1.1 Table 1) */}
      <section className="bg-surface border border-border p-3 flex-1 flex flex-col overflow-hidden shadow-sm min-h-32">
        <div className="flex items-center justify-between mb-2 shrink-0">
          <span className="text-xs font-semibold uppercase tracking-wider text-dim font-mono">
            TAOCP §1.1 Trace Table
          </span>
          <span className="text-[10px] font-mono text-dim">
            Table 1 Matrix
          </span>
        </div>

        <div className="border border-border bg-page flex-1 overflow-y-auto min-h-0">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="border-b border-border bg-surface text-dim text-[11px] sticky top-0 z-10">
                <th className="py-1 px-2 font-semibold">Pass</th>
                <th className="py-1 px-2 font-semibold">m</th>
                <th className="py-1 px-2 font-semibold">n</th>
                <th className="py-1 px-2 font-semibold">q</th>
                <th className="py-1 px-2 font-semibold">r</th>
              </tr>
            </thead>
            <tbody>
              {!activeStepObj || activeStepObj.traceHistory.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-3 text-center text-dim text-[11px]">
                    No passes recorded yet
                  </td>
                </tr>
              ) : (
                activeStepObj.traceHistory.map((row, i) => {
                  const isCurrent = activeStepObj.pass === row.pass && activeStepObj.phase === row.phase;
                  return (
                    <tr
                      key={i}
                      onClick={() => onSeekStep(row.stepIndex)}
                      className={`cursor-pointer transition-colors border-b border-border/40 ${
                        isCurrent ? 'bg-blue-600/15 text-blue-400 font-bold' : 'hover:bg-surface text-muted'
                      }`}
                      title={`Jump to pass ${row.pass}`}
                    >
                      <td className="py-1 px-2">{row.pass === 0 ? 'E0' : `Pass ${row.pass}`}</td>
                      <td className="py-1 px-2 text-rod-m"><LinkedNumber value={row.m} /></td>
                      <td className="py-1 px-2 text-rod-n"><LinkedNumber value={row.n} /></td>
                      <td className="py-1 px-2 text-rod-q">{row.q !== null ? <LinkedNumber value={row.q} /> : '—'}</td>
                      <td className="py-1 px-2 text-rod-r">{row.r !== null ? <LinkedNumber value={row.r} /> : (row.phase === 'E0' ? 'swap' : '—')}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </aside>
  );
};
