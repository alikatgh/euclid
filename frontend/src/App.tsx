import { useEffect, useState } from 'react';
import ReferenceLesson from './ReferenceLesson';
import { CurriculumPlayer } from './components/CurriculumPlayer';
import { curriculumLessons, lessonCatalog } from './lib/curriculum';
import './components/Curriculum.css';

function selectedFromHash() {
  const id = new URLSearchParams(window.location.hash.slice(1)).get('lesson');
  if (lessonCatalog.some((lesson) => lesson.id === id)) return id!;
  if (id !== null) window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#lesson=algorithm-e`);
  return 'algorithm-e';
}

export function App() {
  const [selected, setSelected] = useState(selectedFromHash);
  const [catalogOpen, setCatalogOpen] = useState(false);
  const selectedIndex = lessonCatalog.findIndex((lesson) => lesson.id === selected);
  const lesson = curriculumLessons.find((entry) => entry.id === selected);
  useEffect(() => { document.title = `Euclid · ${lessonCatalog[selectedIndex].order}. ${lessonCatalog[selectedIndex].title}`; }, [selectedIndex]);
  useEffect(() => {
    const update = () => setSelected(selectedFromHash());
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);
  function choose(id: string) {
    setSelected(id);
    setCatalogOpen(false);
    window.location.hash = new URLSearchParams({ lesson: id }).toString();
  }
  return <div className="curriculum-shell">
    <nav className="curriculum-nav" aria-label="Lesson navigation">
      <button type="button" className="curriculum-brand" onClick={() => setCatalogOpen(!catalogOpen)} aria-expanded={catalogOpen} aria-controls="lesson-catalog">Euclid <span>Course map {catalogOpen ? '−' : '+'}</span></button>
      <label className="curriculum-select-label"><span className="sr-only">Choose lesson</span><select value={selected} onChange={(event) => choose(event.target.value)}>
        {lessonCatalog.map((entry) => <option value={entry.id} key={entry.id}>{entry.order}. {entry.title}</option>)}
      </select></label>
      <span className="curriculum-count">{selectedIndex + 1} / {lessonCatalog.length}</span>
      <button type="button" aria-label="Previous lesson" disabled={selectedIndex === 0} onClick={() => choose(lessonCatalog[selectedIndex - 1].id)}>←</button>
      <button type="button" aria-label="Next lesson" disabled={selectedIndex === lessonCatalog.length - 1} onClick={() => choose(lessonCatalog[selectedIndex + 1].id)}>→</button>
    </nav>
    <main id="lesson-catalog" className="curriculum-catalog" hidden={!catalogOpen}>
      <p className="curriculum-eyebrow">First twenty lessons · Review edition</p>
      <h1>From seeing an algorithm to reading its mathematics.</h1>
      <p>Keep the original Euclid player as a reference, then work through state, proof, numbers, and sums. Each new lesson connects a change you can see to the notation and code that describe it.</p>
      <p className="curriculum-source-note">Original explanations and worked examples, with section references to The Art of Computer Programming, Volume 1, §§1.1–1.2.3. This is the opening sequence, not full-volume coverage.</p>
      <div className="curriculum-catalog-grid">{lessonCatalog.map((entry) => <button type="button" key={entry.id} onClick={() => choose(entry.id)} aria-current={entry.id === selected ? 'page' : undefined}>
        <span className="curriculum-eyebrow">Lesson {entry.order.toString().padStart(2, '0')}</span><strong>{entry.title}</strong><span>{entry.subtitle}</span>
      </button>)}</div>
    </main><div className="curriculum-content" key={selected} hidden={catalogOpen}>
      {lesson ? <CurriculumPlayer lesson={lesson} active={!catalogOpen} /> : <ReferenceLesson active={!catalogOpen} />}
    </div>
  </div>;
}
export default App;
