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
// Resolve the new shared browser annotation helper from the source checkout.
writeFileSync(join(temp,'NumbersAnimatedDemo.js'),readFileSync(join(temp,'NumbersAnimatedDemo.js'),'utf8').replaceAll('../lib/symbolConnections.js',join(root,'src/lib/symbolConnections.js')));
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
 const shifted=moves(render('geometric-shift',15));assert.equal(shifted.get('geometric-copy-0')['data-x'],'205');assert.equal(shifted.get('geometric-original-0')['data-x'],'105');
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
 const log=render('log-exponent-interval',5);assert(log.includes('81 &lt; 128'));assert(log.includes('data-move="log-certified-interval" data-x="320"'));
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

test('reindexing tells a ten-step story with stable physical squares and a self-contained final frame',()=>{
 const book=JSON.parse(readFileSync(join(root,'../content/first20/lessons11-20.json'),'utf8'));
 const passage=book.find(l=>l.order===18).sections[0].passages[0],demo=passage.demonstration;
 for(const [help,authored,offset] of [[false,demo,3],[true,demo.simplerHelp,1]]){
  assert.equal(authored.states.length,10);assert.equal(authored.transitions.length,9);
  const original=render('reindex-square-cards',0,help);
  for(let step=0;step<10;step++){
   const html=render('reindex-square-cards',step,help);
   assert(!/NaN|Infinity|undefined/.test(html));
   for(let i=0;i<3;i++){
    assert.equal([...html.matchAll(new RegExp(`data-reindex-cell="${i}"`,'g'))].length,(offset+i)**2);
    const positions=value=>[...value.matchAll(new RegExp(`<g data-move="reindex-cell-${i}-[^>]+`,'g'))].map(m=>m[0]);
    assert.deepEqual(positions(html),positions(original),'relabeling preserves every cell coordinate');
    assert(html.includes(`old k = ${offset+i}`),'old label remains as an explicit bridge');
   }
   if(step>0&&step<4)assert(html.includes(`New address ${step-1} still selects`));
  }
  assert(render('reindex-square-cards',4,help).includes(`Add ${offset} to BOTH sides`));
  const bounds=render('reindex-square-cards',5,help);assert(bounds.includes(`FIRST: k = ${offset}`));assert(bounds.includes(`LAST: k = ${offset+2}`));
  const final=render('reindex-square-cards',9,help);
  assert(final.includes(`j=0: (0+${offset})²=${offset**2}`));assert(final.includes(`${offset} × ${offset} = ${offset**2} ${offset===1?'piece':'pieces'}`));
  assert(final.includes(help?'1 + 4 + 9 = 14':'9 + 16 + 25 = 50'));assert(!final.includes('WRONG'));
  const wrong=render('reindex-square-cards',8,help);assert(wrong.includes('WRONG'));assert(wrong.includes(help?'5 ≠ 14':'5 ≠ 50'));
 }
 assert.equal(passage.visualLinks.takeaway,'same-sum-confirmed');
});

test('rounding bound is constructed from decimal spacing before measuring or scaling actual error',()=>{
 const book=JSON.parse(readFileSync(join(root,'../content/first20/lessons11-20.json'),'utf8'));
 const passage=book.find(l=>l.order===16).sections.flatMap(s=>s.passages).find(p=>p.demonstration.model.kind==='additive-error-bound');
 const fraction=s=>s.split('/').map(Number).reduce((a,b)=>a/b);
 for(const [help,d,den,c] of [[false,passage.demonstration,100,33],[true,passage.demonstration.simplerHelp,10,3]]){
  assert.equal(d.states.length,8);assert.equal(d.transitions.length,7);
  for(const state of d.states){const x=state.computed;assert.equal(fraction(x.gap),1/den);assert.equal(fraction(x.halfGap),1/(2*den));assert.ok(Math.abs(fraction(x.actual)-(1/3-c/den))<1e-15);assert.equal(fraction(x.totalActual),x.copies/(3*den));assert.equal(fraction(x.totalBound),x.copies/(2*den));}
  assert(render('additive-error-bound',1,help).includes(help?'0.4 − 0.3 = 0.1':'0.34 − 0.33 = 0.01'));
  const mids=render('additive-error-bound',2,help);assert(mids.includes(help?'0.25':'0.325'));assert(mids.includes(help?'0.35':'0.335'));assert(mids.includes('tie rule chooses a neighbor'));
  assert(render('additive-error-bound',3,help).includes(help?'0.1 ÷ 2 = 0.05':'0.01 ÷ 2 = 0.005'));
  const final=render('additive-error-bound',7,help);assert(final.includes(help?'0.1 ≤ 0.15':'0.01 ≤ 0.015'));assert(final.includes('half-gap bound holds either way'));
  const widths=prefix=>[...final.matchAll(new RegExp(`data-move="${prefix}-\\d"[^>]*><rect width="([^"]+)"`,'g'))].map(m=>Number(m[1]));
  assert.deepEqual(widths('actual-error-copy'),Array(3).fill(440*2/9));assert.deepEqual(widths('bound-copy'),Array(3).fill(440/3));
  assert.ok(Math.abs(widths('actual-error-copy').reduce((a,b)=>a+b)/widths('bound-copy').reduce((a,b)=>a+b)-2/3)<1e-14);
 }
});

test('log bounds use midpoint candidates, exact power comparisons, then inverse roots before tightening',()=>{
 const book=JSON.parse(readFileSync(join(root,'../content/first20/lessons11-20.json'),'utf8'));
 const p=book.find(l=>l.order===14).sections.flatMap(s=>s.passages).find(p=>p.demonstration.model.kind==='log-exponent-interval'),d=p.demonstration;
 assert.equal(d.states.length,8);assert.equal(d.simplerHelp.states.length,4);
 assert.equal((1+2)/2,3/2);assert.equal((3/2+2)/2,7/4);
 assert.equal(2**3,8);assert.equal(3**2,9);assert.equal(3**4,81);assert.equal(2**7,128);
 assert(render('log-exponent-interval',1).includes('(1 + 2) ÷ 2 = 3/2'));assert(render('log-exponent-interval',4).includes('(3/2 + 2) ÷ 2 = 7/4'));
 assert(render('log-exponent-interval',2).includes('(2^(3/2))² = 2³ = 8'));assert(render('log-exponent-interval',3).includes('Take positive square roots'));
 assert(render('log-exponent-interval',5).includes('(2^(7/4))⁴ = 2⁷ = 128'));assert(render('log-exponent-interval',6).includes('Take positive fourth roots'));
 const width=stage=>Number(render('log-exponent-interval',stage).match(/data-move="log-certified-interval"[^>]*data-w="([^"]+)"/)[1]);
 assert.equal(width(1),440);assert.equal(width(2),440);assert.equal(width(3),220);assert.equal(width(5),220);assert.equal(width(6),110);assert.equal(width(7),110);
 const final=render('log-exponent-interval',7);assert(final.includes('8 &lt; 9'));assert(final.includes('81 &lt; 128'));assert(final.includes('3/2 &lt; lg 3 &lt; 7/4'));
 for(let i=0;i<4;i++)assert.equal([...render('log-exponent-interval',i,true).matchAll(/data-move="log-root-unit-/g)].length,9);
 assert(render('log-exponent-interval',3,true).includes('log₉3 = 1/2, because 9^(1/2) = 3.'));
 assert.equal(p.visualLinks.takeaway,'certified');
});

test('all 34 helper lessons render their own authored states, examples, and formulas without main-formula fallback',()=>{
 const book=JSON.parse(readFileSync(join(root,'../content/first20/lessons11-20.json'),'utf8'));
 let models=0,states=0;
 for(const lesson of book)for(const section of lesson.sections)for(const passage of section.passages){
  const d=passage.demonstration,h=d.simplerHelp;models++;
  assert(h.states.length>=2,passage.id);assert.equal(h.model.kind,d.model.kind);assert.equal(h.states.length,h.steps.length,passage.id+' needs one helper explanation per actual state');for(const state of d.states)assert.equal(typeof state.formula,'string',passage.id+' has an explicit main formula');
  for(const [frameIndex,state] of h.states.entries()){
   assert.equal(typeof state.formula,'string',`${passage.id}: every help formula is deliberate`);
   assert(state.caption);assert(state.computed,passage.id);
   const html=renderToStaticMarkup(React.createElement(NumbersAnimatedDemo,{exampleId:d.id+'-help',frameIndex,visual:{model:h.model,state,helpMode:true}}));
   assert(!/No authored|NaN|Infinity|undefined/.test(html),passage.id+' '+frameIndex);
   const ids=[...html.matchAll(/data-move="([^"]+)"/g)].map(x=>x[1]);assert.equal(ids.length,new Set(ids).size);
   if(state.renderFrame!==undefined)assert(Number.isInteger(state.renderFrame)&&state.renderFrame>=0);
   states++;
  }
 }
 assert.equal(models,34);assert(states>=120);
 const find=id=>book.flatMap(l=>l.sections.flatMap(s=>s.passages)).find(p=>p.id===id).demonstration.simplerHelp;
 assert.deepEqual(find('factor-growth').model.exactInput.values,[1,2,4]);assert.equal(find('factor-growth').states.length,3,'two doublings do not silently become three');
 assert.equal(find('rational-exponent').model.exactInput.reciprocal,'1/4');assert.equal(find('rational-exponent').states.at(-1).formula,'16^{-1/2}=1/4');
 assert.equal(find('change-base').model.exactInput.target,16);assert.equal(find('change-base').states[1].renderFrame,2);
 assert.equal(find('round-last').model.exactInput.tieRule,'upward');assert.equal(find('round-last').model.exactInput.earlyTotal,2);
 const h=find('finite-boundaries'),state=h.states[1];const html=renderToStaticMarkup(React.createElement(NumbersAnimatedDemo,{exampleId:'boundary-help',frameIndex:1,visual:{model:h.model,state,helpMode:true}}));assert(html.includes('One constant term: S = 1'),'explicit helper renderFrame controls actual scene');
});

test('arithmetic names quantities only after concrete piles, and geometric notation expands into actual values before shifting',()=>{
 const book=JSON.parse(readFileSync(join(root,'../content/first20/lessons11-20.json'),'utf8'));
 const find=id=>book.flatMap(l=>l.sections.flatMap(s=>s.passages)).find(p=>p.id===id);
 const a=find('arithmetic-endpoint'),g=find('geometric-shift');assert.equal(a.demonstration.states.length,8);assert.equal(g.demonstration.states.length,16);
 for(const passage of [a,g])for(const d of [passage.demonstration,passage.demonstration.simplerHelp]){
  for(const state of d.states.slice(0,4))assert.equal(state.formula,'','no generic formula before concrete quantities');
  for(const state of d.states)assert(state.teachingExplanation);
 }
 const arithmetic=render('arithmetic-gaps',7);assert(arithmetic.includes('a=2: first value'));assert(arithmetic.includes('n=4: term count'));assert(arithmetic.includes('d=3: added each time'));assert(arithmetic.includes('2 + (4 − 1) × 3 = 11'));
 const small=render('arithmetic-gaps',7,true);assert(small.includes('1 + (3 − 1) × 2 = 5'));
 const sigma=render('geometric-shift',8);assert(sigma.includes('Σ(k=0…3) 2^k = 1 + 2 + 4 + 8'));assert(sigma.includes('0 = first index'));assert(sigma.includes('3 = last index'));assert(sigma.includes('2^k = each value'));
 for(let stage=10;stage<=13;stage++)assert(render('geometric-shift',stage).includes(`Term ${stage-9}: 2 × ${2**(stage-10)} = ${2**(stage-9)}`));
 const final=render('geometric-shift',15);assert(final.includes('Σ(k=0…3) 2^k = 15'));assert(final.includes('Σ(k=1…4) 2^k = 30'));assert(final.includes('Still 4 terms; each value doubled'));
});
