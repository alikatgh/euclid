import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import katex from 'katex';
import { adaptLessons } from '../recovered/adaptLessons.js';
const root=new URL('../../../',import.meta.url);
const json=relative=>JSON.parse(fs.readFileSync(new URL(relative,root),'utf8'));
const first=json('content/first20/lessons4-10.json');
const lastUrl=new URL('content/first20/lessons11-20.json',root);
const last=fs.existsSync(lastUrl)?JSON.parse(fs.readFileSync(lastUrl,'utf8')):[];
const source=[...first,...last];
const lessons=adaptLessons(source);
test('original design adapter retains the ordered authored lesson registry',()=>{
 assert.equal(first.length,7); assert.equal(last.length,10); assert.equal(lessons.length,17); assert.deepEqual(lessons.map(l=>l.order),source.map(l=>l.order));
 assert.equal(new Set(lessons.map(l=>l.id)).size,lessons.length);
});
test('every passage keeps its wording, formula, check, main model, and smaller help in original slots',()=>{
 for(let l=0;l<lessons.length;l++){
  const adapted=lessons[l];const passages=source[l].sections.flatMap(s=>s.passages);
  assert.equal(adapted.sections.length,passages.length);
  for(let p=0;p<passages.length;p++){
   const section=adapted.sections[p],original=passages[p];
   assert.equal(section.title,original.title);assert.ok(section.title);
   const full=[section.definition,...section.paragraphs.slice(0,-1)].join('\n\n');
   assert.equal(full,Array.isArray(original.text)?original.text.join('\n\n'):original.text);
   assert.equal(section.examples.length,2);assert.equal(section.examples[0].frames.length,original.demonstration.states.length);
   assert.equal(section.examples[1].frames.length,original.demonstration.simplerHelp.states?.length ?? original.demonstration.simplerHelp.steps.length+1);
   assert.equal(section.examples[1].frames[0].visual.helpStepIndex,original.demonstration.simplerHelp.states?.length ? 0 : -1);
   assert.ok(section.examples[0].frames.every(f=>!f.visual.helpMode));
   assert.ok(section.examples[1].frames.every(f=>f.visual.helpMode));
   for(const example of section.examples){assert.equal(example.check.options.filter(o=>o.correct).length,1);assert.ok(example.frames.length>1);}
   for(const binding of [section.visual.definition,...section.visual.paragraphs,section.visual.takeaway]){
    const example=section.examples.find(x=>x.id===binding.exampleId);assert.ok(example);assert.ok(binding.frameIndex>=0&&binding.frameIndex<example.frames.length);
   }
  }
 }
});
test('every authored display formula parses safely in KaTeX',()=>{
 for(const lesson of lessons)for(const section of lesson.sections)for(const example of section.examples)for(const frame of example.frames){
  const formula=frame.formula.replace(/^\$|\$$/g,'');assert.doesNotThrow(()=>katex.renderToString(formula,{throwOnError:true,trust:false}),`${lesson.id}/${section.id}/${frame.title}`);
 }
});
test('all exact preserved stylesheet asset references are bundled',()=>{
 const css=fs.readFileSync(new URL('frontend/public/assets/original.css',root),'utf8');
 for(const match of css.matchAll(/url\(\/assets\/([^)]*)\)/g))assert.ok(fs.existsSync(new URL('frontend/public/assets/'+match[1],root)),match[1]);
});
test('all original first-three sections have appended help without rewriting the saved baseline',()=>{
 const original=json('content/deployed-original.json');const help=json('content/first20/original-help.json');
 assert.ok(help.find(x=>x.lessonId==='algorithm-e'));
 for(const [id,key] of [['algorithm-features','algorithmFeatures'],['computational-methods','computationalMethods']]){
  for(const section of original[key].sections){const entry=help.find(e=>e.lessonId===id&&e.sectionId===section.id);assert.ok(entry);assert.ok(entry.helpExample.frames.length>1);}
 }
});
