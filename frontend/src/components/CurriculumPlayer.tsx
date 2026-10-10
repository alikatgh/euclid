import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useReducedMotion } from 'framer-motion';
import type { CurriculumLesson, LessonParameter, Prediction } from '../types/curriculum';
import { buildLessonFrames, defaultInputs, lessonCatalog } from '../lib/curriculum';
import { renderLinkedMath } from '../lib/mathConnections';
import { schedulePlayback } from '../lib/playback';
import { useTextScale } from '../hooks/useTextScale';
import { useTheme } from '../hooks/useTheme';
import { CurriculumScene } from './CurriculumScene';
import { LinkedNumber, LinkedSymbol, LinkedText, MathConnectionStatus, MathConnections } from './MathConnections';
import MathematicalText from './MathematicalText';

function ParameterControl({ parameter, value, onChange }: { parameter: LessonParameter; value: number; onChange: (value: number) => void }) {
  const [draft, setDraft] = useState(String(value));
  const [error, setError] = useState('');
  useEffect(() => { setDraft(String(value)); setError(''); }, [value]);
  function apply() {
    const next = Number(draft);
    const step = parameter.step ?? 1;
    if (!draft.trim() || !Number.isFinite(next) || next < parameter.min || next > parameter.max || Math.abs((next - parameter.min) / step - Math.round((next - parameter.min) / step)) > 1e-8) {
      setError(`Use ${parameter.min}–${parameter.max}, in steps of ${step}.`);
      return;
    }
    setError(''); onChange(next);
  }
  return <div className="curriculum-parameter">
    <label htmlFor={`parameter-${parameter.id}`}>{parameter.label}</label>
    <input id={`parameter-${parameter.id}`} type="number" min={parameter.min} max={parameter.max} step={parameter.step ?? 1} value={draft} onChange={(event) => setDraft(event.target.value)} onBlur={apply} onKeyDown={(event) => { if (event.key === 'Enter') apply(); }} aria-describedby={`parameter-help-${parameter.id}`} aria-invalid={Boolean(error)} />
    <input type="range" aria-label={`Adjust ${parameter.label}`} min={parameter.min} max={parameter.max} step={parameter.step ?? 1} value={value} onChange={(event) => onChange(event.target.valueAsNumber)} />
    <small id={`parameter-help-${parameter.id}`}>{error || parameter.description}</small>
  </div>;
}

function PredictionExercise({ prediction }: { prediction: Prediction }) {
  const [answer, setAnswer] = useState<number | null>(null);
  return <section className="curriculum-prediction" aria-label="Prediction exercise">
    <h3>Predict before you move on</h3>
    <p><MathematicalText text={prediction.prompt} /></p>
    <div className="curriculum-choices">{prediction.choices.map((choice, index) => <button type="button" key={index} aria-pressed={answer === index} onClick={() => setAnswer(index)} className={answer === index ? index === prediction.correctIndex ? 'is-correct' : 'is-incorrect' : ''}>
      <span className="choice-marker">{String.fromCharCode(65 + index)}</span><MathematicalText text={choice} interactive={false} />
    </button>)}</div>
    {prediction.hint && <details><summary>Show a hint</summary><p><MathematicalText text={prediction.hint} /></p></details>}
    {answer !== null && <p className="curriculum-feedback" role="status"><strong>{answer === prediction.correctIndex ? 'Yes. ' : 'Try that reasoning again. '}</strong><MathematicalText text={prediction.explanation} /></p>}
  </section>;
}

function BoundCodeLine({ text, bindings }: { text: string; bindings: Record<string, number | string> }) {
  return <>{text.split(/([A-Za-z_][A-Za-z0-9_]*)/).map((token, index) => Object.hasOwn(bindings, token)
    ? <LinkedSymbol key={index} symbol={token} value={bindings[token]} />
    : <LinkedText key={index} text={token} />)}</>;
}

export function CurriculumPlayer({ lesson, active = true }: { lesson: CurriculumLesson; active?: boolean }) {
  const [inputs, setInputs] = useState(() => defaultInputs(lesson));
  const [index, setIndex] = useState(0);
  const [isPlaying, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [copyStatus, setCopyStatus] = useState('');
  const latestCode = useRef('');
  const [tab, setTab] = useState<'reading' | 'code'>('reading');
  const { fontScale, setFontScale } = useTextScale();
  const { theme, toggleTheme } = useTheme();
  const reducedMotion = useReducedMotion();
  const model = useMemo(() => {
    try { return { frames: buildLessonFrames(lesson, inputs), error: null }; }
    catch (error) { return { frames: [], error: error instanceof Error ? error.message : 'Unable to build this lesson.' }; }
  }, [lesson, inputs]);
  const frames = model.frames;
  const frame = frames[Math.min(index, frames.length - 1)];
  const sourceCode = frame?.code.lines.join('\n') ?? '';
  latestCode.current = sourceCode;
  useEffect(() => { setCopyStatus(''); }, [sourceCode]);
  async function copyCode() {
    const requestedCode = sourceCode;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(requestedCode);
      setCopyStatus(latestCode.current === requestedCode ? 'Copied.' : 'Copied the code from the previous step.');
    } catch { setCopyStatus('Clipboard unavailable. Select and copy the code below.'); }
  }
  const bindings = useMemo(() => Object.fromEntries(frame?.variables.map((variable) => [variable.symbol, variable.value]) ?? []), [frame]);
  const formulaHtml = useMemo(() => frame ? renderLinkedMath(frame.formula, { displayMode: true, throwOnError: false, trust: false }, frame.formulaBinding === 'none' ? {} : bindings) : '', [frame, bindings]);
  const seek = useCallback((next: number) => { setPlaying(false); setIndex(Math.max(0, Math.min(frames.length - 1, next))); }, [frames.length]);
  const togglePlay = useCallback(() => {
    if (isPlaying) setPlaying(false);
    else { if (index >= frames.length - 1) setIndex(0); setPlaying(true); }
  }, [isPlaying, index, frames.length]);
  useEffect(() => { if (!active) setPlaying(false); }, [active]);
  useEffect(() => {
    return schedulePlayback({ active, playing: isPlaying, index, frameCount: frames.length, delay: 3200 / speed }, () => {
      const next = Math.min(index + 1, frames.length - 1);
      setIndex(next);
      if (next === frames.length - 1 || frames[next].prediction) setPlaying(false);
    }, window);
  }, [active, isPlaying, index, frames, speed]);
  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (!active) return;
      if (event.defaultPrevented || event.isComposing || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (event.target instanceof HTMLElement && event.target.closest('input,textarea,select,button,a,[contenteditable],[role="button"],[data-reading-scroll],summary')) return;
      if (event.key === 'ArrowRight') { event.preventDefault(); seek(index + 1); }
      else if (event.key === 'ArrowLeft') { event.preventDefault(); seek(index - 1); }
      else if (event.key === ' ' && !event.repeat) { event.preventDefault(); togglePlay(); }
    };
    window.addEventListener('keydown', keydown);
    return () => window.removeEventListener('keydown', keydown);
  }, [active, index, seek, togglePlay]);
  function changeInput(id: string, value: number) { setPlaying(false); setIndex(0); setInputs((previous) => ({ ...previous, [id]: value })); }
  return <div className="curriculum-player">
    <header className="curriculum-heading">
      <div><p className="curriculum-eyebrow">Lesson {lesson.order.toString().padStart(2, '0')} · {lesson.sources.map((source) => source.section).join(' / ')}</p><h1>{lesson.title}</h1><p>{lesson.subtitle}</p></div>
      <div className="curriculum-display-controls"><button type="button" onClick={() => setFontScale((size) => Math.max(.85, +(size - .1).toFixed(2)))} disabled={fontScale <= .85} aria-label="Decrease text size">A−</button><button type="button" onClick={() => setFontScale((size) => Math.min(1.35, +(size + .1).toFixed(2)))} disabled={fontScale >= 1.35} aria-label="Increase text size">A+</button><button type="button" onClick={toggleTheme}>{theme === 'dark' ? 'Light' : 'Dark'} theme</button></div>
    </header>
    {model.error || !frame ? <p role="alert">{model.error || 'This lesson has no frames.'}</p> : <MathConnections as="main" className="curriculum-workspace" resetKey={`${lesson.id}:${JSON.stringify(inputs)}`}>
      <section className="curriculum-laboratory" aria-label="Interactive visual model">
        <details className="curriculum-inputs" open><summary>Change the example</summary><div className="curriculum-parameters">{lesson.parameters.map((parameter) => <ParameterControl key={parameter.id} parameter={parameter} value={inputs[parameter.id]} onChange={(value) => changeInput(parameter.id, value)} />)}</div></details>
        <div className="curriculum-scene-heading"><span className="curriculum-eyebrow">State {index + 1} of {frames.length}</span><h2>{frame.title}</h2></div>
        <CurriculumScene scene={frame.scene} isPlaying={isPlaying} playbackSpeed={speed} />
        <div className="curriculum-formula" dangerouslySetInnerHTML={{ __html: formulaHtml }} />
        <p className="curriculum-intuition"><MathematicalText text={frame.intuition} /></p>
        <div className="curriculum-variables">{frame.variables.map((variable, position) => <div key={`${variable.symbol}-${position}`} title={variable.meaning}>
          <span><LinkedSymbol symbol={variable.symbol} value={variable.value} /> = <LinkedNumber value={variable.value} /></span>
          {variable.previous !== undefined && <small>was <LinkedNumber value={variable.previous} /></small>}<small>{variable.meaning}</small>
        </div>)}</div>
        {frame.counters && <div className="curriculum-counters">{frame.counters.map((counter) => <div key={counter.label}><strong><LinkedNumber value={counter.value} /></strong><span>{counter.label}</span><small>{counter.unit}</small></div>)}</div>}
        <MathConnectionStatus />
        <div className="curriculum-transport" aria-label="Playback controls">
          <button type="button" onClick={() => seek(0)} aria-label="Reset lesson" disabled={index === 0 && !isPlaying}>↺</button>
          <button type="button" onClick={() => seek(index - 1)} disabled={index === 0}>Previous</button>
          <button type="button" className="curriculum-play" onClick={togglePlay} aria-pressed={isPlaying}>{isPlaying ? 'Pause' : index === frames.length - 1 ? 'Replay' : 'Play'}</button>
          <button type="button" onClick={() => seek(index + 1)} disabled={index === frames.length - 1}>Next</button>
          <label>Speed <select value={speed} onChange={(event) => setSpeed(Number(event.target.value))}><option value={.5}>0.5×</option><option value={1}>1×</option><option value={2}>2×</option></select></label>
          <input type="range" aria-label="Lesson step" min={0} max={frames.length - 1} value={index} onChange={(event) => seek(event.target.valueAsNumber)} />
        </div>
        <p className="curriculum-shortcuts">← → step · Space play / pause · Escape clears linked values{reducedMotion ? ' · Reduced motion enabled' : ''}. Playback pauses at prediction questions.</p>
      </section>
      <section className="curriculum-reading" aria-label="Mathematics and code">
        <div className="curriculum-tabs" role="group" aria-label="Reading view"><button type="button" onClick={() => setTab('reading')} aria-pressed={tab === 'reading'}>Read the mathematics</button><button type="button" onClick={() => setTab('code')} aria-pressed={tab === 'code'}>Follow the code</button></div>
        <div className="curriculum-reading-scroll">
          {tab === 'reading' ? <>
            <section><p className="curriculum-eyebrow">Precision</p><h2>The formal statement</h2><p className="curriculum-formal"><MathematicalText text={frame.formal} /></p></section>
            <section className="curriculum-notation"><h3>Read the symbols</h3><p><MathematicalText text={frame.reading} /></p></section>
          </> : <section><p className="curriculum-eyebrow">{frame.code.language === 'python' ? 'Python' : 'Pseudocode'} · highlighted lines describe this state</p><div className="curriculum-code-actions"><button type="button" onClick={copyCode}>Copy code</button><span role="status">{copyStatus}</span></div><div className="curriculum-code" role="region" aria-label="Current code" tabIndex={0} data-reading-scroll>
            {frame.code.lines.map((line, position) => <div key={position} className={frame.code.activeLines.includes(position + 1) ? 'active-line' : ''} aria-current={frame.code.activeLines.includes(position + 1) ? 'step' : undefined}><span className="line-number" aria-hidden="true">{position + 1}</span><code><BoundCodeLine text={line} bindings={bindings} /></code></div>)}
          </div><p className="curriculum-code-note">Symbol highlights show the current binding in the state below the diagram. A source line describes a transition; intermediate assignment states are made explicit in the lesson.</p></section>}
          {frame.prediction && <PredictionExercise key={`${frame.id}:${JSON.stringify(inputs)}`} prediction={frame.prediction} />}
          <details className="curriculum-goals"><summary>What you should be able to do</summary><ul>{lesson.objectives.map((objective) => <li key={objective}>{objective}</li>)}</ul>{lesson.prerequisites.length > 0 && <p>Builds on: {lesson.prerequisites.map((id, position) => <Fragment key={id}>{position > 0 && ', '}{lessonCatalog.some((item) => item.id === id) ? <a href={`#lesson=${encodeURIComponent(id)}`}>{lessonCatalog.find((item) => item.id === id)!.title}</a> : id}</Fragment>)}.</p>}</details>
          {lesson.countingNote && <details><summary>What the counters mean</summary><p><MathematicalText text={lesson.countingNote} /></p></details>}
          <footer className="curriculum-sources"><h3>Reference and scope</h3>{lesson.sources.map((source, position) => <Fragment key={position}><p>{source.url ? <a href={source.url} target="_blank" rel="noreferrer">{source.title}</a> : source.title}, {source.section}.</p><p>{source.note}</p></Fragment>)}<p>All explanations, visual models, and exercises here are newly written. No book pages are included.</p></footer>
        </div>
      </section>
      <span className="sr-only" role="status" aria-live="polite">Step {index + 1} of {frames.length}: {frame.title}{isPlaying ? '. Playing.' : '. Paused.'}</span>
    </MathConnections>}
  </div>;
}
