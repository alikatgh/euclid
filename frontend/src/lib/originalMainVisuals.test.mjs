import * as symbolConnections from './symbolConnections.js';
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as jsx from 'react/jsx-runtime';
import {renderToStaticMarkup} from 'react-dom/server';
const source=fs.readFileSync(new URL('../components/OriginalMainVisualEnhancements.tsx',import.meta.url),'utf8');
const sandbox={exports:{},require:name=>name==='react/jsx-runtime'?jsx:name==='../lib/symbolConnections.js'?symbolConnections:{bindNumbersMotion:()=>{}}};
vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2023}}).outputText,sandbox);
const content=JSON.parse(fs.readFileSync(new URL('../../../content/deployed-original.json',import.meta.url),'utf8'));
const all=[...content.algorithmFeatures.sections.flatMap(s=>s.examples).map(e=>({...e,Component:sandbox.exports.FeatureCauseEffect})),...content.computationalMethods.sections.flatMap(s=>s.examples).map(e=>({...e,Component:sandbox.exports.MethodCauseEffect}))];
const render=(id,i)=>{const e=all.find(e=>e.id===id);return renderToStaticMarkup(jsx.jsx(e.Component,{exampleId:id,frameIndex:i,visual:e.frames[i].visual,paused:true}));};
test('all 18 original ordinary examples and 82 frames have finite causal geometry',()=>{
 let frames=0;for(const e of all)for(let i=0;i<e.frames.length;i++){const html=render(e.id,i);assert.match(html,/original-main-cause-effect/);assert.doesNotMatch(html,/NaN|undefined|Infinity/);const ids=[...html.matchAll(/data-object="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size,`${e.id}/${i}`);frames++;}assert.equal(all.length,18);assert.equal(frames,82);
});
test('the formal output state is a returned value, never an m-register',()=>{
 for(const i of [15,16]){const html=render('euclid-states',i);assert.match(html,/data-object="output-value"/);assert.doesNotMatch(html,/data-object="after-m"/);assert.match(html,/Output state in Ω/);}
 assert.match(render('euclid-states',4),/old n → m and old r → n/);
});
test('GCD proof and arithmetic diagrams follow their actual source frame',()=>{
 assert.match(render('gcd-output-proof',1),/d divides m − qn = r/);
 assert.match(render('gcd-output-proof',2),/d divides qn \+ r = m/);
 assert.match(render('gcd-output-proof',5),/119 = 7 × 17/);
 assert.match(render('gcd-output-proof',5),/544 = 32 × 17/);
 assert.match(render('effective-integer-division',3),/New \(m, n\)/);
 assert.match(render('ineffective-instructions',1),/GCD oracle/);
});
test('state overlap, empty-pattern boundary, and non-output loops remain explicit',()=>{
 assert.match(render('state-model',0),/I ∩ Ω is allowed/);
 assert.match(render('empty-pattern',0),/gap before the first letter/);
 assert.match(render('effective-loop',1),/xₖ = \(a, 0\) for every k/);
 assert.match(render('effective-loop',1),/j = 0: outside/);
 assert.match(render('effective-loop',2),/j = 1: inside/);
});
