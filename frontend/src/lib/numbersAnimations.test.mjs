import {test} from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {mkdtempSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
const root=resolve(import.meta.dirname,'../..'),temp=mkdtempSync(join(tmpdir(),'euclid-number-scenes-'));
execFileSync(join(root,'node_modules/.bin/tsc'),['--ignoreConfig','--jsx','react-jsx','--module','commonjs','--target','es2023','--moduleResolution','node','--ignoreDeprecations','6.0','--skipLibCheck','--outDir',temp,join(root,'src/components/NumbersAnimatedDemo.tsx'),join(root,'src/components/numbersDemoMotion.ts')]);
writeFileSync(join(temp,'package.json'),'{"type":"commonjs"}');
const require=createRequire(join(root,'package.json'));
// The temporary emitted files resolve the application's existing React install.
const Module=require('node:module');process.env.NODE_PATH=join(root,'node_modules');Module._initPaths();
const {NumbersAnimatedDemo}=require(join(temp,'NumbersAnimatedDemo.js'));const {bindNumbersMotion}=require(join(temp,'numbersDemoMotion.js'));
const {renderToStaticMarkup}=require('react-dom/server'),React=require('react');
const kinds=['fraction-refinement','long-division-cycle','nested-exact-intervals','branching-multiplication','factor-concatenation','factor-group-repetition','reciprocal-exponent-track','positive-root-square','root-power-reciprocal','equivalent-root-routes','real-exponent-brackets','power-log-inverse','log-exponent-interval','decreasing-power-log','exponent-path-addition','log-quotient-power','change-base-units','false-log-sum','exact-rounded-strips','additive-error-bound','round-order','indexed-accumulation','formula-summands','empty-sum','reindex-square-cards','dummy-index-rename','reindex-reverse','arithmetic-gaps','arithmetic-pairing','signed-arithmetic-pairing','geometric-shift','geometric-signed-cancellation','geometric-unit-ratio','geometric-empty-boundaries'];
const render=(kind,frameIndex,helpMode=false)=>renderToStaticMarkup(React.createElement(NumbersAnimatedDemo,{exampleId:kind,frameIndex,visual:{model:{kind},helpMode}}));
test('all 34 authored models render every main/help state without fallback or invalid coordinates',()=>{for(const kind of kinds)for(let stage=0;stage<6;stage++)for(const help of [false,true]){const html=render(kind,stage,help);assert(!html.includes('No authored'));assert(!/NaN|Infinity|undefined/.test(html));assert(html.includes('role="img"'));const ids=[...html.matchAll(/data-move="([^"]+)"/g)].map(x=>x[1]);assert.equal(new Set(ids).size,ids.length,`${kind}: duplicate persistent identity`);}});
test('every actual authored model and state is covered, with exact sums and reindexing examples',()=>{const lessons=JSON.parse(readFileSync(join(root,'../content/first20/lessons11-20.json'),'utf8'));const demos=lessons.flatMap(l=>l.sections.flatMap(s=>s.passages.map(p=>p.demonstration)));assert.deepEqual(new Set(demos.map(d=>d.model.kind)),new Set(kinds));for(const d of demos)for(const [frameIndex,state]of d.states.entries()){const html=renderToStaticMarkup(React.createElement(NumbersAnimatedDemo,{exampleId:d.id,frameIndex,visual:{model:d.model,state}}));assert(!html.includes('No authored'));assert(!/NaN|Infinity|undefined/.test(html));}assert(render('formula-summands',1).includes('running sum = 0'));assert(render('formula-summands',2).includes('running sum = 29'));assert(render('formula-summands',3,true).includes('running sum = 5'));assert(render('dummy-index-rename',2).includes('2 + 4 = 6 ≠ 23'));assert(render('geometric-empty-boundaries',2).includes('Two terms: 1 + 2 = 3'));});
test('literal multiplication accounts for all 81 units',()=>{const html=render('branching-multiplication',4);assert.equal([...html.matchAll(/data-move="power-unit-/g)].length,81);assert(html.includes('81 units'));assert(html.includes('3 × 3 × 3 × 3 = 81'));});
test('exact boundary identities and signed cancellation are preserved',()=>{assert(render('empty-sum',0).includes('running sum = 0'));assert(render('geometric-empty-boundaries',0).includes('No terms: S = 0'));assert(render('geometric-unit-ratio',2).includes('division by 0 is forbidden'));assert(render('geometric-signed-cancellation',4).includes('(16 − 1) / (2 − 1) = 15'));assert(render('signed-arithmetic-pairing',4).includes('12 / 2 = 6'));assert(render('exact-rounded-strips',2).includes('100× magnified gap: 0.01'));});
class FakeElement{constructor(attrs){this.a=new Map(Object.entries(attrs));}getAttribute(k){return this.a.get(k)??null}setAttribute(k,v){this.a.set(k,String(v))}hasAttribute(k){return this.a.has(k)}}
test('in-flight pause, resume, seek/reset and reduced motion are deterministic',()=>{let id=0,queue=new Map();global.requestAnimationFrame=f=>{queue.set(++id,f);return id};global.cancelAnimationFrame=id=>queue.delete(id);global.matchMedia=()=>({matches:false});const e=new FakeElement({'data-move':'unit','data-x':'0','data-y':'0','data-o':'1'});const svg={isConnected:true,querySelectorAll:()=>[e]};const step=t=>{const fs=[...queue.values()];queue.clear();fs.forEach(f=>f(t))};bindNumbersMotion(svg,'demo:false:0',false);e.setAttribute('data-x','100');bindNumbersMotion(svg,'demo:false:1',false);step(100);step(400);const mid=e.getAttribute('transform');assert.notEqual(mid,'translate(0 0)');assert.notEqual(mid,'translate(100 0)');bindNumbersMotion(svg,'demo:false:1',true);assert.equal(e.getAttribute('transform'),mid);step(1000);assert.equal(e.getAttribute('transform'),mid);bindNumbersMotion(svg,'demo:false:1',false);step(1100);step(1800);assert.equal(e.getAttribute('transform'),'translate(100 0)');e.setAttribute('data-x','0');bindNumbersMotion(svg,'demo:false:0',false);assert.equal(e.getAttribute('transform'),'translate(0 0)');global.matchMedia=()=>({matches:true});e.setAttribute('data-x','100');bindNumbersMotion(svg,'demo:false:1',false);assert.equal(e.getAttribute('transform'),'translate(100 0)');});
process.on('exit',()=>rmSync(temp,{recursive:true,force:true}));

test('number scenes conserve identities while coordinates, units, and signed counts tell the operation',()=>{
 const moves=html=>new Map([...html.matchAll(/<g\s[^>]*data-move="([^"]+)"[^>]*>/g)].map(m=>[m[1],Object.fromEntries([...m[0].matchAll(/([\w-]+)="([^"]*)"/g)].map(a=>[a[1],a[2]]))]));
 for(const help of [false,true]){
  const old=moves(render('reindex-square-cards',0,help)),renamed=moves(render('reindex-square-cards',2,help));
  for(let i=0;i<3;i++)assert.equal(old.get('fixed-term-'+i).transform,renamed.get('fixed-term-'+i).transform,'renaming must not move the values');
 }
 const signed=moves(render('signed-arithmetic-pairing',3));
 assert.equal([...signed].filter(([id,a])=>id.startsWith('pair-unit-')&&a['data-o']==='1').length,12,'signed pairing leaves exactly 12 positive tokens, two copies of S=6');
 const helpSigned=moves(render('signed-arithmetic-pairing',3,true));
 assert.equal([...helpSigned].filter(([id,a])=>id.startsWith('pair-unit-')&&a['data-o']==='1').length,4);
 const paired=moves(render('arithmetic-pairing',4));assert.equal([...paired].filter(([id,a])=>id.startsWith('pair-unit-')&&a['data-o']==='1').length,30);
 const shifted=moves(render('geometric-shift',2));assert.equal(shifted.get('geometric-copy-0')['data-x'],'205');assert.equal(shifted.get('geometric-original-0')['data-x'],'105');
 const canceled=moves(render('geometric-signed-cancellation',3));
 assert.deepEqual([...canceled].filter(([id,a])=>/^geometric-(copy|original)-\d$/.test(id)&&a['data-o']==='1').map(([id])=>id),['geometric-original-0','geometric-copy-3']);
 const root=moves(render('root-power-reciprocal',3));assert.equal([...root].filter(([id,a])=>id.startsWith('root-cell-')&&a['data-o']==='1').length,64);
 assert(render('root-power-reciprocal',3).includes('1 selected piece / 64 equal pieces'));
 assert(render('positive-root-square',2).includes('root-side-units'));
});
test('reciprocal, fractional log, and zoom scenes expose truthful scales and certificates',()=>{
 for(let s=0;s<5;s++){
  const html=render('reciprocal-exponent-track',s),width=Number(html.match(/data-move="power-length"[^>]*data-w="([^"]+)"/)[1]);
  assert.equal(width,110*2**(2-s));assert(html.includes('Amount scale: 1 unit = one quarter of this bar'));
 }
 const log=render('log-exponent-interval',2);assert(log.includes('81 &lt; 128'));assert(log.includes('data-move="value-dot" data-x="174.375"'));
 assert(render('decreasing-power-log',2).includes('Right on the exponent axis moves left on the value axis.'));
 assert.equal((520-515.8)*100,420.00000000000455);
 const rounding=render('exact-rounded-strips',2);assert(rounding.includes('0.99'));assert(rounding.includes('1.00'));assert(rounding.includes('100× magnified gap: 0.01'));
 assert(render('fraction-refinement',1).includes('6 selected of 8 equal pieces'));
 assert(render('fraction-refinement',1,true).includes('2 selected of 4 equal pieces'));
});
test('causal phases hide conclusions until objects settle, and pause freezes phase and result visibility',()=>{
 let id=0,queue=new Map();global.requestAnimationFrame=f=>{queue.set(++id,f);return id};global.cancelAnimationFrame=id=>queue.delete(id);global.matchMedia=()=>({matches:false});
 const source=new FakeElement({'data-move':'source','data-motion-phase':'source','data-x':'0'}),unit=new FakeElement({'data-move':'unit','data-x':'0'}),result=new FakeElement({'data-result':'true'}),attrs=new Map();
 const svg={isConnected:true,setAttribute:(k,v)=>attrs.set(k,v),querySelectorAll:q=>q==='[data-move]'?[source,unit]:q==='[data-result]'?[result]:[]};
 const step=t=>{const fs=[...queue.values()];queue.clear();fs.forEach(f=>f(t))};
 bindNumbersMotion(svg,'phase:false:0');source.setAttribute('data-x','100');unit.setAttribute('data-x','100');bindNumbersMotion(svg,'phase:false:1');
 assert.equal(result.getAttribute('opacity'),'0');assert.equal(attrs.get('data-motion-phase'),'select');step(100);step(180);
 assert.notEqual(source.getAttribute('transform'),'translate(0 0)');assert.equal(unit.getAttribute('transform'),'translate(0 0)');
 step(450);assert.equal(attrs.get('data-motion-phase'),'transform');const midpoint=unit.getAttribute('transform'),phase=attrs.get('data-motion-progress');bindNumbersMotion(svg,'phase:false:1',true);step(1000);
 assert.equal(unit.getAttribute('transform'),midpoint);assert.equal(attrs.get('data-motion-progress'),phase);assert.equal(result.getAttribute('opacity'),'0');
 bindNumbersMotion(svg,'phase:false:1',false);step(1100);step(1800);assert.equal(result.getAttribute('opacity'),'1');assert.equal(attrs.get('data-motion-phase'),'settled');assert.equal(unit.getAttribute('transform'),'translate(100 0)');
 source.setAttribute('data-x','0');unit.setAttribute('data-x','0');bindNumbersMotion(svg,'phase:false:0');assert.equal(result.getAttribute('opacity'),'1');assert.equal(unit.getAttribute('transform'),'translate(0 0)');
 global.matchMedia=()=>({matches:true});unit.setAttribute('data-x','100');bindNumbersMotion(svg,'phase:false:1');assert.equal(result.getAttribute('opacity'),'1');assert.equal(attrs.get('data-motion-phase'),'settled');
});
