import originalHelp from '../../../content/first20/original-help.json';
import { Lw } from './runtime.js';
const question = q => ({prompt:q.prompt,options:q.choices.map((text,i)=>({id:`help-answer-${i}`,text,correct:i===q.correctIndex,feedback:q.explanation}))});
export function originalHelpExample(entry) {
  return {...entry.helpExample,check:question(entry.simplerHelp.check),frames:entry.helpExample.frames.map(frame=>({
    ...frame,formula:frame.formula || '',visual:{title:frame.title,description:frame.explanation,isOriginalHelp:true,kind:entry.helpExample.kind,
      objects:frame.objects,model:entry.demonstration,machineState:frame.machineState,observerMetadata:frame.observerMetadata},
  }))};
}
for (const entry of originalHelp) {
  const lesson=entry.lessonId==='algorithm-features'?Lw.algorithmFeatures:entry.lessonId==='computational-methods'?Lw.computationalMethods:null;
  const section=lesson?.sections.find(section=>section.id===entry.sectionId);
  if(section && !section.examples.some(example=>example.id===entry.helpExample.id)) section.examples.push(originalHelpExample(entry));
}
export const algorithmHelpEntry=originalHelp.find(entry=>entry.lessonId==='algorithm-e');
