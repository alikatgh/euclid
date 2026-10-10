/** Translate authored teaching content into the deployed app's existing reading/demo schema.
 * No shell, typography, layout or controls are created by this adapter.
 */
const labels = {
  contents: 'Lesson contents', demonstration: 'Worked demonstration', previous: 'Previous', next: 'Next',
  restart: 'Restart demonstration', check: 'Check your understanding', correct: 'Correct', tryAgain: 'Try again',
  complete: 'Checked', summaryTitle: 'What to take away', backToFirst: 'Review this lesson',
};
const inline = text => text && !text.startsWith('$') ? `$${text}$` : (text || '');
function check(question) {
  return {prompt: question.prompt, options: question.choices.map((text,index) => ({
    id: `answer-${index}`, text, correct: index === question.correctIndex,
    feedback: question.explanation,
  }))};
}
function sourceNote(source,provenance) {
  return [source.book || source.title, source.section, source.pdfPages ? `Supplied ebook PDF pages ${source.pdfPages} (one-based; not printed pagination).` : source.pages,
    provenance].filter(Boolean).join(' · ');
}
function adaptPassage(lesson,section,passage,index) {
  const demo=passage.demonstration;
  const mainId=demo.id;
  const helper=demo.simplerHelp;
  const mainFrames=demo.states.map((state,frameIndex) => {
    const transition=demo.transitions.find(t=>t.to===state.id);
    return {
      title: state.caption, formula: inline(state.formula || passage.formula), explanation: transition?.explanation || state.caption,
      visual: {title: demo.title, description: state.caption, model:demo.model, state, states:demo.states, transition,
        helpMode:false, lessonId:lesson.id, order:lesson.order, labels:{}, frameIndex},
    };
  });
  const helpFrames=[{action:"Start",text:helper.intro},...helper.steps].map((step,helpFrameIndex) => ({
    title:step.action[0].toUpperCase()+step.action.slice(1), formula:inline(passage.formula),
    explanation:helper.connection,
    visual:{title:helper.intro,description:step.text,model:demo.model,state:demo.states[Math.max(0,Math.min(helpFrameIndex-1,demo.states.length-1))],states:demo.states,
      transition:{action:step.action,explanation:step.text},helpMode:true,helpContent:helper,helpStepIndex:helpFrameIndex-1,lessonId:lesson.id,order:lesson.order,labels:{}},
  }));
  const textParagraphs=Array.isArray(passage.text)?passage.text:passage.text.split(/\n\s*\n/).filter(Boolean);
  const definition=textParagraphs.shift() || passage.title;
  const paragraphs=[...textParagraphs, inline(passage.formula)];
  const examples=[{id:mainId,label:demo.title,frames:mainFrames,check:check(demo.check)},
    {id:`${mainId}-help`,label:'I still don’t understand',frames:helpFrames,check:check(helper.check)}];
  const link = frameIndex=>({exampleId:mainId,frameIndex:Math.min(frameIndex,mainFrames.length-1)});
  return {id:`${section.id}-${passage.id}-${index}`,title:passage.title,question:demo.check.prompt,definition,paragraphs,
    takeaway:helper.connection,visual:{definition:link(0),paragraphs:paragraphs.map((_,i)=>link(i+1)),takeaway:link(mainFrames.length-1)},
    examples,check:check(demo.check)};
}
export function adaptLessons(lessons) {
  const sorted=[...lessons].sort((a,b)=>a.order-b.order);
  return sorted.map((lesson,index)=>{
    const sections=lesson.sections.flatMap(section=>section.passages.map((passage,i)=>adaptPassage(lesson,section,passage,i)));
    return {id:lesson.id,order:lesson.order,title:lesson.title,subtitle:lesson.scope || lesson.source.section,
      intro:lesson.scope || '',sourceNote:sourceNote(lesson.source,lesson.provenance),
      navigationLabel:`Lesson ${lesson.order} · ${lesson.title}`,
      previousLessonLabel:index?`Lesson ${sorted[index-1].order} · ${sorted[index-1].title}`:'Lesson 3 · Computational methods',
      visualControls:{play:'Play demonstration',pause:'Pause demonstration',replay:'Replay demonstration',frame:'Show visual frame',read:'Select a passage to see it illustrated.'},
      labels:{...labels,summary:sections.map(section=>section.takeaway).join(' ')},sections};
  });
}
