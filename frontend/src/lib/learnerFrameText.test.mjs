import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { adaptLessons } from '../recovered/adaptLessons.js';

const authoring = 'AUTHORING_SENTINEL: animate copies; retain all renderer identities.';
const question = { prompt:'Which value?', choices:['One','Two'], correctIndex:1, explanation:'Two is the computed value.' };
function fixture() {
  return [{id:'learner-text-fixture',order:21,title:'A checked example',source:{book:'Test source',section:'Test section'},sections:[{id:'section',passages:[{
    id:'passage',title:'Keep the mathematical reading',text:'Original mathematical definition.\n\nOriginal derivation.',formula:'1+1=2',
    demonstration:{id:'demo',title:'A worked example',model:{kind:'test'},check:question,
      states:[{id:'start',caption:'One item is present.'},{id:'end',caption:'Two items are present.',teachingExplanation:'One original item plus one added item gives two.'}],
      transitions:[{from:'before',to:'start',action:'draw',targets:['item'],explanation:authoring},{from:'start',to:'end',action:'copy',targets:['item'],explanation:authoring}],
      simplerHelp:{intro:'Use a smaller example.',connection:'The same addition rule applies.',check:question,
        states:[{id:'help-start',caption:'The first item.'},{id:'help-end',caption:'The two items.',teachingExplanation:'Explicit helper teaching takes precedence.'}],
        steps:[{action:'observe',text:'Vetted helper step explains the first item.'},{action:'compare',text:'Fallback helper wording.'}],
        transitions:[{from:'help-start',to:'help-end',action:'copy',targets:['item'],explanation:authoring}]}
    }
  }]}]}];
}

test('animation-author metadata never becomes main teaching prose',()=>{
  const section=adaptLessons(fixture())[0].sections[0],frames=section.examples[0].frames;
  assert.equal(frames[0].explanation,'One item is present.');
  assert.equal(frames[1].explanation,'One original item plus one added item gives two.');
  for(const frame of frames) {
    assert.ok(!frame.title.includes('AUTHORING_SENTINEL'));
    assert.ok(!frame.explanation.includes('AUTHORING_SENTINEL'));
    assert.ok(!frame.visual.description.includes('AUTHORING_SENTINEL'));
    assert.equal(frame.visual.transition.explanation,authoring,'Animation metadata remains available to visuals');
  }
  assert.equal(section.definition,'Original mathematical definition.');
  assert.deepEqual(section.paragraphs,['Original derivation.','$1+1=2$']);
});

test('explicit helper teaching wins, while vetted helper steps remain a fallback',()=>{
  const frames=adaptLessons(fixture())[0].sections[0].examples[1].frames;
  assert.equal(frames[0].explanation,'Vetted helper step explains the first item.');
  assert.equal(frames[1].explanation,'Explicit helper teaching takes precedence.');
  assert.equal(frames[1].visual.transition.explanation,authoring);
  assert.ok(frames.every(frame=>!frame.explanation.includes('AUTHORING_SENTINEL')));
});

test('missing explicit text falls back to caption without exposing author instructions',()=>{
  const data=fixture(),demo=data[0].sections[0].passages[0].demonstration;
  delete demo.states[1].teachingExplanation;
  delete demo.simplerHelp.states[1].teachingExplanation;
  demo.simplerHelp.steps=[];
  const examples=adaptLessons(data)[0].sections[0].examples;
  assert.equal(examples[0].frames[1].explanation,'Two items are present.');
  assert.equal(examples[1].frames[1].explanation,'The two items.');
});

test('legacy smaller helpers use their own formula and preserve an intentional empty step formula',()=>{
  const data=fixture(),helper=data[0].sections[0].passages[0].demonstration.simplerHelp;
  delete helper.states;
  helper.formula='14-2\\cdot6=2';
  helper.steps=[
    {action:'observe',text:'First inspect the smaller values.',formula:''},
    {action:'derive',text:'Now derive the smaller equation.',formula:'2=14-2\\cdot6'},
    {action:'check',text:'Check the helper equation.'},
  ];
  const frames=adaptLessons(data)[0].sections[0].examples[1].frames;
  assert.equal(frames[0].formula,'$14-2\\cdot6=2$','Constructed start uses the helper formula');
  assert.equal(frames[1].formula,'','Blank is intentional; it must not reveal the main formula');
  assert.equal(frames[2].formula,'$2=14-2\\cdot6$');
  assert.equal(frames[3].formula,'$14-2\\cdot6=2$');
});

test('a legacy helper can intentionally hide its formula until a step derives one',()=>{
  const data=fixture(),helper=data[0].sections[0].passages[0].demonstration.simplerHelp;
  delete helper.states;
  helper.formula='';
  helper.steps=[{action:'derive',text:'Derive two from two ones.',formula:'1+1=2'}];
  const frames=adaptLessons(data)[0].sections[0].examples[1].frames;
  assert.equal(frames[0].formula,'');
  assert.equal(frames[1].formula,'$1+1=2$');
  delete helper.formula;
  delete helper.steps[0].formula;
  assert.equal(adaptLessons(data)[0].sections[0].examples[1].frames[0].formula,'$1+1=2$','Old content without a helper formula retains its compatibility fallback');
});

test('explicit-state formulas preserve blanks and independently authored helper defaults',()=>{
  const data=fixture(),passage=data[0].sections[0].passages[0],demo=passage.demonstration;
  demo.states[0].formula='';
  demo.states[1].formula='2=1+1';
  demo.simplerHelp.formula='14-2\\cdot6=2';
  demo.simplerHelp.states[0].formula='';
  let examples=adaptLessons(data)[0].sections[0].examples;
  assert.equal(examples[0].frames[0].formula,'');
  assert.equal(examples[0].frames[1].formula,'$2=1+1$');
  assert.equal(examples[1].frames[0].formula,'');
  assert.equal(examples[1].frames[1].formula,'$14-2\\cdot6=2$');
  delete demo.states[0].formula;
  delete demo.simplerHelp.formula;
  examples=adaptLessons(data)[0].sections[0].examples;
  assert.equal(examples[0].frames[0].formula,'$1+1=2$');
  assert.equal(examples[1].frames[1].formula,'$1+1=2$');
});


test('every authored explicit helper step list aligns one-to-one with its states',()=>{
  const content=new URL('../../../content/',import.meta.url);
  const files=['first20/lessons4-10.json','first20/lessons11-20.json',...readdirSync(new URL('fullbook/',content)).filter(name=>/^batch-[A-F]\.json$/.test(name)).map(name=>'fullbook/'+name)];
  const mismatches=[];
  for(const file of files)for(const lesson of JSON.parse(readFileSync(new URL(file,content),'utf8')))for(const section of lesson.sections)for(const passage of section.passages){
    const helper=passage.demonstration.simplerHelp;
    if(helper.states?.length&&Array.isArray(helper.steps)&&helper.states.length!==helper.steps.length)mismatches.push({lesson:lesson.order,passage:passage.id,states:helper.states.length,steps:helper.steps.length});
  }
  assert.deepEqual(mismatches,[],'Each helper step must narrate the state at the same index, including its initial state');
});

test('helper narration binds by corresponding state index without overriding explicit elaboration',()=>{
  const data=fixture(),helper=data[0].sections[0].passages[0].demonstration.simplerHelp;
  helper.states=[{id:'h0',caption:'Initial state.'},{id:'h1',caption:'Intermediate state.',teachingExplanation:'Vetted explanation of the intermediate result.'},{id:'h2',caption:'Final state.'}];
  helper.steps=[{action:'start',text:'Narrate the initial state.'},{action:'change',text:'Fallback intermediate narration.'},{action:'finish',text:'Narrate only the final state.'}];
  const frames=adaptLessons(data)[0].sections[0].examples[1].frames;
  assert.deepEqual(frames.map(frame=>frame.explanation),['Narrate the initial state.','Vetted explanation of the intermediate result.','Narrate only the final state.']);
  assert.equal(frames[1].visual.description,'Intermediate state.','A vetted explanation may elaborate rather than equal the caption');
});


test('an intentionally blank passage formula never creates an empty reading button',()=>{
 const data=fixture(),passage=data[0].sections[0].passages[0];passage.formula='';passage.visualLinks={paragraphs:[1]};
 const section=adaptLessons(data)[0].sections[0];
 assert.deepEqual(section.paragraphs,['Original derivation.']);
 assert.equal(section.visual.paragraphs.length,1);assert.equal(section.visual.paragraphs[0].frameIndex,1);
 assert.equal(section.examples[0].frames[0].formula,'','A deliberately blank frame remains blank');
});
