import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import Module, { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const require=createRequire(import.meta.url),ts=require('typescript'),React=require('react');
const {renderToStaticMarkup}=require('react-dom/server');
const source=fileURLToPath(new URL('../components/FoundationsDemo.tsx',import.meta.url));
const mod=new Module(source);mod.filename=source;mod.paths=Module._nodeModulePaths(fileURLToPath(new URL('.',import.meta.url)));
mod._compile(ts.transpileModule(fs.readFileSync(source,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText,source);
const {FoundationsDemo,euclidPackages}=mod.exports;
const lessons=JSON.parse(fs.readFileSync(new URL('../../../content/first20/lessons4-10.json',import.meta.url),'utf8'));
const gcd=(m,n)=>n?gcd(n,m%n):m;
const render=props=>renderToStaticMarkup(React.createElement(FoundationsDemo,props));
const targets=html=>[...html.matchAll(/data-motion-id="([^"]+)" data-x="([^"]+)" data-y="([^"]+)" data-o="([^"]+)"/g)].map(m=>m.slice(1).join('|')).join(';');
test('every Euclid package reconstructs its value from the fixed original pair',()=>{
 for(let m=2;m<=80;m++)for(let n=2;n<=40;n++){const rows=euclidPackages(m,n);for(const row of rows)assert.equal(row.a*m+row.b*n,row.value);assert.equal(rows.at(-1).value,gcd(m,n));}
 assert.deepEqual(euclidPackages(26,15).map(({value,a,b})=>[value,a,b]),[[26,1,0],[15,0,1],[11,1,-1],[4,-1,2],[3,3,-5],[1,-4,7]]);
 assert.deepEqual(euclidPackages(14,6).at(-1),{id:'r2',value:2,a:1,b:-2,q:2});
});
test('all authored main and smaller-help states are renderable, finite and genuinely change object positions',()=>{
 for(const lesson of lessons)for(const section of lesson.sections)for(const passage of section.passages){
  const d=passage.demonstration,main=d.states.map((state,i)=>render({exampleId:passage.id,frameIndex:i,frame:{id:state.id},visual:{model:d.model,state}}));
  const help=d.simplerHelp.states?d.simplerHelp.states.map((state,i)=>render({exampleId:passage.id,visual:{model:d.model,state,helpMode:true,helpStepIndex:i,helpContent:d.simplerHelp}})):[-1,...d.simplerHelp.steps.map((_,i)=>i)].map(i=>render({exampleId:passage.id,visual:{model:d.model,helpMode:true,helpStepIndex:i,helpContent:d.simplerHelp}}));
  for(const html of [...main,...help]){assert.match(html,/<svg/);assert.doesNotMatch(html,/NaN|undefined|Infinity/);assert.match(html,/data-motion-id=/);}
  assert.ok(new Set(main.map(targets)).size>1,`${passage.id}: main demo must move`);
  assert.ok(new Set(help.map(targets)).size>1,`${passage.id}: smaller help must move`);
 }
});
test('each loop checkpoint and transient frame has the exact intended prefix sum and count',()=>{
 const lesson=lessons.find(l=>l.id==='loop-assertions');
 for(const section of lesson.sections)for(const passage of section.passages)for(const state of passage.demonstration.states){
  const variables=state.variables||[],k=variables.find(v=>v.symbol==='k')?.value,sum=variables.find(v=>v.symbol==='s')?.value;
  const html=render({exampleId:passage.id,frame:{id:state.id},visual:{model:passage.demonstration.model,state}});
  if(typeof k==='number')assert.ok(html.includes(`k = ${k}`),state.id+' count');
  if(typeof sum==='number')assert.ok(html.includes(`s = ${sum}`),state.id+' total');
 }
});
test('sequential swap retains temporary copy; parallel swap reads the old pair without inventing a temporary',()=>{
 const sequential=render({exampleId:'safe-swap-argument',visual:{model:{kind:'assignment-copy'},state:{id:'finish'}}});
 assert.match(sequential,/data-motion-id="save-a-t" data-x="519" data-y="139" data-o="1"/);
 assert.match(sequential,/b ← t/);
 const copy=render({exampleId:'safe-swap-argument',visual:{model:{kind:'assignment-copy'},state:{id:'copy-b'}}});
 assert.match(copy,/data-motion-id="original-b" data-x="314" data-y="139" data-o="1"/);
 const parallel=render({exampleId:'simultaneous-argument',visual:{model:{kind:'assignment-copy'},state:{id:'parallel'}}});
 assert.match(parallel,/\(a, b\) ← \(b, a\)/);
 assert.match(parallel,/Read old pair: \(7, 12\)/);
 assert.match(parallel,/Write new pair: \(12, 7\)/);
 assert.doesNotMatch(parallel,/b ← t|>t<\/text>/);
});

test('every authored numerical scene labels endpoints as targets and has usable static coordinates',()=>{
 for(const lesson of lessons)for(const section of lesson.sections)for(const passage of section.passages){
  for(const [i,state] of passage.demonstration.states.entries()){
   const html=render({exampleId:passage.id,frameIndex:i,frame:{id:state.id},visual:{model:passage.demonstration.model,state},reducedMotion:true});
   assert.match(html,/Target values for this step/);
   assert.match(html,/data-label-semantics="destination-state"/);
   const count=[...html.matchAll(/data-motion-id=/g)].length;
   assert.equal([...html.matchAll(/data-motion-id="[^"]+" data-x="[^"]+" data-y="[^"]+" data-o="[^"]+" transform="translate\([^)]+\)" opacity="[^"]+"/g)].length,count,passage.id);
   assert.doesNotMatch(html,/\\leftarrow|\\qquad|\\text/,'SVG instructions must be readable rather than raw TeX');
  }
 }
});

test('smaller predecessor scenes distinguish two bases, capacity, and forward proof dependencies',()=>{
 const help=(intro,step)=>render({visual:{model:'two-predecessors',helpMode:true,helpStepIndex:step,helpContent:{intro}}});
 const bases=help('The next pile combines the previous two piles.',0);
 assert.match(bases,/data-motion-id="base-pile-0"[^>]*data-o="1"/);
 assert.match(bases,/data-motion-id="base-pile-1"[^>]*data-o="0"/);
 assert.match(help('The next pile combines the previous two piles.',1),/data-motion-id="base-pile-1"[^>]*data-o="1"/);
 const capacity=help('If one pile fits in two small boxes and the other fits in one, together they fit in three.',1);
 assert.match(capacity,/Actual counters: 1 \+ 1 = 2. Their spaces: 2 \+ 1 = 3/);
 assert.match(capacity,/3 spaces fit in 4/);
 const scope=help('Before opening box 3, inspect the labels on boxes 1 and 2.',1);
 assert.match(scope,/P\(1\) and P\(2\) → P\(3\)/);
 assert.match(scope,/data-teaching="operation-arrow"/);
});

test('signed cancellation pairs every removed unit and isolates the exact survivor',()=>{
 const html=render({exampleId:'certificate-argument',visual:{model:'bezout',state:{id:'identity',kind:'balance',left:[{value:26,coefficient:-4},{value:15,coefficient:7}]}}});
 const nodes=[...html.matchAll(/data-motion-id="(signed-(?:add|remove)-\d+)" data-x="([^"]+)" data-y="([^"]+)" data-o="([^"]+)"/g)].map(m=>({id:m[1],x:+m[2],y:+m[3],o:+m[4]}));
 for(let i=0;i<104;i++){
  const a=nodes.find(n=>n.id===`signed-add-${i}`),r=nodes.find(n=>n.id===`signed-remove-${i}`);
  assert.equal(a.x,r.x);assert.equal(a.y,r.y);assert.equal(a.o,.15);assert.equal(r.o,.4);
 }
 assert.equal(nodes.filter(n=>n.id.startsWith('signed-add-')&&n.o===1).length,1);
 assert.match(html,/105 − 104 = 1/);
});

test('foundation animation pauses both its operation phase and coordinates, resumes, and respects reduced motion',()=>{
 const old={MutationObserver:globalThis.MutationObserver,requestAnimationFrame:globalThis.requestAnimationFrame,cancelAnimationFrame:globalThis.cancelAnimationFrame,matchMedia:globalThis.matchMedia};
 let update,serial=0;const queue=new Map();
 globalThis.MutationObserver=class{constructor(fn){update=fn;}observe(){}};
 globalThis.requestAnimationFrame=fn=>{queue.set(++serial,fn);return serial;};
 globalThis.cancelAnimationFrame=id=>queue.delete(id);
 globalThis.matchMedia=()=>({matches:false});
 try{
  const attrs={},el={dataset:{motionId:'unit',x:'0',y:'0',o:'1'},setAttribute:(k,v)=>attrs[k]=v};
  const svg={dataset:{frame:'start',paused:'false',reduced:'false'},isConnected:true,querySelectorAll:()=>[el]};
  const element=FoundationsDemo({exampleId:'assignment',visual:{model:'assignment'}});
  element.props.ref(svg);
  assert.equal(attrs.transform,'translate(0 0)');
  el.dataset.x='100';svg.dataset.frame='copy';update();
  const step=time=>{const pending=[...queue.values()];queue.clear();for(const fn of pending)fn(time);};
  for(let t=100;t<=400;t+=50)step(t);
  const frozen=attrs.transform,phase=svg.dataset.operationPhase;
  assert.equal(phase,'moving');assert.notEqual(frozen,'translate(100 0)');
  svg.dataset.paused='true';update();assert.equal(queue.size,0,'pausing cancels the pending frame immediately');step(450);step(900);
  assert.equal(attrs.transform,frozen);assert.equal(svg.dataset.operationPhase,phase);assert.equal(queue.size,0);
  update();assert.equal(queue.size,0,'further paused mutations must not restart RAF');
  svg.dataset.paused='false';update();step(950);
  assert.equal(attrs.transform,frozen,'first resumed frame must not include paused wall time');
  for(let t=1000;t<=2000;t+=50)step(t);
  assert.equal(attrs.transform,'translate(100 0)');assert.equal(svg.dataset.operationPhase,'checked');
  svg.dataset.reduced='true';el.dataset.x='200';svg.dataset.frame='next';update();
  assert.equal(attrs.transform,'translate(200 0)');assert.equal(queue.size,0);
  svg.dataset.reduced='false';svg.dataset.paused='true';el.dataset.x='0';svg.dataset.frame='replay';update();
  assert.equal(attrs.transform,'translate(0 0)','paused manual replay shows its exact authored state');
 }finally{Object.assign(globalThis,old);}
});


test('the failed second assignment copies current a rightward into b',()=>{
 const html=render({exampleId:'lost-value-argument',visual:{model:'assignment-copy',state:{id:'bad-second'}}});
 assert.match(html,/b ← a/);assert.match(html,/d="M215 109L300 109/);
 assert.match(html,/data-motion-id="copy-a-b-again" data-x="314" data-y="139" data-o="1"/);
 const first=render({exampleId:'lost-value-argument',visual:{model:'assignment-copy',state:{id:'bad-first'}}});
 assert.match(first,/d="M300 109L215 109/);
});

// Preserve the regression introduced by 85e860d; allow the new 140 ms selection phase.
test('paused foundation motion goes idle and resumes without advancing paused time',t=>{
 const callbacks=new Map();let nextId=0,notify,writes=0;
 const globals={
  requestAnimationFrame:callback=>{const id=++nextId;callbacks.set(id,callback);return id;},
  cancelAnimationFrame:id=>callbacks.delete(id),
  MutationObserver:class{constructor(callback){notify=callback;}observe(){}},
  matchMedia:()=>({matches:false}),
 };
 for(const [key,value]of Object.entries(globals)){
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,key);
  Object.defineProperty(globalThis,key,{value,configurable:true,writable:true});
  t.after(()=>{if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete globalThis[key];});
 }
 const attributes=new Map(),element={dataset:{motionId:'tile',x:'0',y:'0',o:'1'},setAttribute:(key,value)=>{writes++;attributes.set(key,value);}};
 const svg={isConnected:true,dataset:{paused:'false',reduced:'false'},querySelectorAll:()=>[element]};
 const frame=time=>{const pending=[...callbacks.values()];callbacks.clear();for(const callback of pending)callback(time);};
 const view=FoundationsDemo({exampleId:'safe-swap-argument',visual:{model:{kind:'assignment-copy'},state:{id:'start'}}});
 view.props.ref(svg);
 element.dataset.x='100';notify();for(let time=100;time<=324;time+=32)frame(time);
 const midway=attributes.get('transform'),beforePause=writes;
 assert.notEqual(midway,'translate(0 0)');assert.notEqual(midway,'translate(100 0)');
 svg.dataset.paused='true';notify();assert.equal(callbacks.size,0);frame(348);
 assert.equal(callbacks.size,0);assert.equal(writes,beforePause);
 for(let i=0;i<500;i++){notify();assert.equal(callbacks.size,0);frame(364+i*16);}
 assert.equal(writes,beforePause);assert.equal(attributes.get('transform'),midway);
 svg.dataset.paused='false';notify();assert.equal(callbacks.size,1);frame(10000);
 assert.equal(attributes.get('transform'),midway);
 for(let i=1;i<=60;i++)frame(10000+i*16);
 assert.equal(attributes.get('transform'),'translate(100 0)');assert.equal(callbacks.size,0);
 element.dataset.x='200';svg.dataset.paused='true';svg.dataset.reduced='true';notify();frame(12000);
 assert.equal(attributes.get('transform'),'translate(200 0)');assert.equal(callbacks.size,0);
 element.dataset.x='300';svg.dataset.paused='false';svg.dataset.reduced='false';notify();
 const beforeDetach=writes;svg.isConnected=false;frame(13000);
 assert.equal(callbacks.size,0);assert.equal(writes,beforeDetach);
});

test('Bezout replacements retain the stored equation, outside sign, distribution and collection',()=>{
 const p=lessons.find(l=>l.order===9).sections.find(s=>s.id==='substitute').passages[0],states=p.demonstration.states;
 assert.equal(states.length,12);
 for(let start=0;start<12;start+=4){
  const group=states.slice(start,start+4);
  assert.deepEqual(group.map(s=>s.scene.bridge.phase),[0,1,2,3]);
  for(const state of group){
   const b=state.scene.bridge,html=render({visual:{model:p.demonstration.model,state}});
   assert.equal(b.positive-b.negative,1);assert.ok(html.includes(b.equation));
   assert.ok(html.includes(b.lines[b.phase]));assert.ok(html.includes(b.notes[b.phase]));
   assert.match(html,/data-teaching="substitution-bridge"/);
  }
 }
 assert.equal(states[1].scene.bridge.lines[1],'1 = 4 − (11 − 2 × 4)');
 assert.equal(states[2].scene.bridge.lines[2],'1 = 4 − 11 + 2 × 4');
 assert.equal(states[3].scene.bridge.lines[3],'1 = (1 + 2) × 4 − 11 = 3 × 4 − 11');
 for(const state of states.filter(s=>s.scene.bridge.phase===3)){
  const html=render({visual:{model:p.demonstration.model,state}}),b=state.scene.bridge;
  const get=(id)=>{const m=html.match(new RegExp(`data-motion-id="${id}" data-x="([^\"]+)" data-y="([^\"]+)"`));return m.slice(1);};
  for(let i=0;i<b.negative;i++)assert.deepEqual(get('bridge-positive-'+i),get('bridge-negative-'+i));
 }
});
test('new Euclid coefficients are visibly subtracted in fixed original columns',()=>{
 const l=lessons.find(l=>l.order===10);
 for(const sec of l.sections)for(const p of sec.passages)for(const state of p.demonstration.states.filter(s=>s.scene.recipeCycle!==undefined)){
  const html=render({visual:{model:p.demonstration.model,state}}),rows=euclidPackages(26,15),i=state.scene.recipeCycle,r=rows[i+2],c=rows[i],d=rows[i+1];
  assert.match(html,/copies of 26/);assert.match(html,/copies of 15/);
  if(state.scene.recipePhase===3)assert.ok(html.includes(`(${c.a}, ${c.b}) − ${r.q} × (${d.a}, ${d.b}) = (${r.a}, ${r.b})`));
 }
 const h=l.sections[0].passages[0].demonstration.simplerHelp;
 for(const state of h.states){const html=render({visual:{model:'extended-euclid',state,helpMode:true}});assert.match(html,/copies of 14/);assert.match(html,/copies of 6/);assert.doesNotMatch(html,/copies of 26/);}
 assert.match(render({visual:{model:'extended-euclid',state:h.states[3],helpMode:true}}),/\(1, 0\) − 2 × \(0, 1\) = \(1, -2\)/);
});
test('expanded algebra source links name actual frames and authored helper equations remain smaller',()=>{
 for(const lesson of lessons.filter(l=>l.order>=9))for(const sec of lesson.sections)for(const p of sec.passages){
  const links=p.visualLinks;if(!links)continue;const ids=p.demonstration.states.map(s=>s.id);
  for(const id of [links.definition,...links.paragraphs,links.takeaway])assert.ok(ids.includes(id),`${p.id}: ${id}`);
  for(const state of p.demonstration.simplerHelp.states||[]){assert.doesNotMatch(state.formula,/26|15/);if(state.formula&&!state.scene?.legacyHelper)assert.match(state.formula,/14|12/);}
 }
});

test('failed swap includes the second no-op write and explains the permanently lost seven',()=>{
 const p=lessons.find(l=>l.order===4).sections.find(s=>s.id==='lost-value').passages[0];
 assert.deepEqual(p.demonstration.states.map(s=>s.id),['start','bad-first','bad-second']);
 assert.match(p.demonstration.states.at(-1).caption,/current a=12.*changes nothing.*7 is already lost/);
 const html=render({visual:{model:p.demonstration.model,state:p.demonstration.states.at(-1)}});assert.match(html,/b ← a/);assert.match(html,/original 7 is lost/);
});
test('particular-prime trace tests every small divisor then justifies the square-root stopping bound',()=>{
 const p=lessons.find(l=>l.order===6).sections.find(s=>s.id==='one-value').passages[0],d=p.demonstration;
 for(const divisor of [2,3,4]){
  const state=d.states[divisor-1],html=render({visual:{model:d.model,state}});
  assert.ok(html.includes(`17 = ${divisor} × ${Math.floor(17/divisor)} + ${17%divisor}`));assert.notEqual(17%divisor,0);
 }
 const final=render({visual:{model:d.model,state:d.states.at(-1)}});assert.match(final,/5 × 5 = 25 &gt; 17/);assert.match(final,/17 is prime/);assert.doesNotMatch(final,/121/);
 const h=d.simplerHelp,small=render({visual:{model:d.model,state:h.states.at(-1),helpMode:true}});assert.match(small,/3 × 3 = 9 &gt; 7/);assert.match(small,/7 is prime/);
});
test('predecessor bound moves actual counters with their distinct capacities into a larger bound',()=>{
 const p=lessons.find(l=>l.order===7).sections.find(s=>s.id==='preserve-bound').passages[0],d=p.demonstration;
 const initial=render({visual:{model:d.model,state:d.states[0]}}),merged=render({visual:{model:d.model,state:d.states[1]}}),final=render({visual:{model:d.model,state:d.states[3]}});
 assert.equal((final.match(/data-motion-id="bound-counter-/g)||[]).length,5);
 assert.equal((final.match(/data-motion-id="bound-space-/g)||[]).length,12);
 assert.notEqual(targets(initial),targets(merged));assert.match(final,/4 spaces stay unused/);
 assert.match(final,/2\^\(k−2\) \+ 2\^\(k−3\) = 3·2\^\(k−3\) ≤ 4·2\^\(k−3\) = 2\^\(k−1\)/);
 const small=render({visual:{model:d.model,state:d.simplerHelp.states.at(-1),helpMode:true}});assert.match(small,/1 space stays unused/);assert.equal((small.match(/data-motion-id="bound-counter-/g)||[]).length,2);
});

test('new authored helper frames keep the displayed formula, explanation and exact scene in sync',async()=>{
 const {adaptLessons}=await import('../recovered/adaptLessons.js');
 for(const lesson of lessons)for(const section of lesson.sections)for(const passage of section.passages){
  const h=passage.demonstration.simplerHelp;if(!h.states)continue;
  const adapted=adaptLessons([{...lesson,sections:[{...section,passages:[passage]}]}])[0].sections[0].examples[1].frames;
  assert.equal(adapted.length,h.states.length);
  for(const [i,frame]of adapted.entries()){
   assert.equal(frame.visual.state,h.states[i]);assert.equal(frame.formula,h.states[i].formula?`$${h.states[i].formula}$`:'');assert.equal(frame.explanation,h.states[i].caption);
   assert.equal(frame.visual.helpStepIndex,i);
   const html=render({visual:frame.visual});assert.match(html,/data-teaching="(?:substitution-bridge|coefficient-bridge|predecessor-bound|trial-prime|legacy-helper)"/);
  }
 }
});

test('all legacy helper operations have explicit matching steps, formulas and renderer phases',()=>{
 let count=0;
 for(const lesson of lessons)for(const section of lesson.sections){const h=section.passages[0].demonstration.simplerHelp;if(!h.states?.[0].scene?.legacyHelper)continue;count++;
  assert.equal(h.states.length,h.steps.length);
  h.states.forEach((state,i)=>{assert.equal(state.scene.helperPhase,i-1);assert.equal(state.caption,h.steps[i].text);assert.equal(state.teachingExplanation,state.caption);assert.equal(state.formula,h.steps[i].formula);});
 }
 assert.equal(count,23);
});
test('legacy no-spare helper never shows a temporary save, while the safe swap does',()=>{
 const lesson=lessons.find(l=>l.order===4);const help=(id,i)=>{const d=lesson.sections.find(s=>s.id===id).passages[0].demonstration;return render({visual:{model:d.model,state:d.simplerHelp.states[i],helpMode:true}});};
 assert.match(help('lost-value',1),/a ← b/);assert.match(help('lost-value',2),/b ← a/);
 assert.match(help('lost-value',2),/original 7 is lost/);assert.doesNotMatch(help('lost-value',1),/t ← a|>t<\/text>/);
 assert.match(help('safe-swap',1),/t ← a/);assert.match(help('safe-swap',3),/b ← t/);
 assert.match(help('simultaneous',1),/\(12, 7\) saved/);assert.match(help('simultaneous',2),/Write new pair: \(12, 7\)/);
});
test('legacy receipt, saved-equation and attached-row helpers enact their exact next action',()=>{
 const help=(order,id,i)=>{const d=lessons.find(l=>l.order===order).sections.find(s=>s.id===id).passages[0].demonstration;return render({visual:{model:d.model,state:d.simplerHelp.states[i],helpMode:true}});};
 assert.match(help(8,'termination',1),/k = 1/);assert.match(help(8,'termination',1),/2 cards uncounted/);
 assert.match(help(8,'transient',1),/k = 1/);assert.match(help(8,'transient',1),/s = 7/);assert.match(help(8,'transient',2),/k = 2/);
 assert.match(help(9,'goal',1),/data-motion-id="six-group-0"[^>]*data-o="0"/);assert.match(help(9,'goal',2),/Twelve removals match twelve units/);
 assert.match(help(9,'record',1),/14 = 2 × 6 \+ 2/);assert.match(help(9,'record',2),/2 = 14 − 2 × 6/);assert.match(help(9,'record',2),/14 = 2 × 6 \+ 2/);
 assert.match(help(9,'certificate',2),/14 = 7 × 2/);assert.match(help(9,'certificate',2),/6 = 3 × 2/);
 assert.match(help(10,'shift',1),/data-motion-id="small-package-two" data-x="70" data-y="246"/);
 assert.match(help(10,'shift',2),/data-motion-id="small-package-two" data-x="70" data-y="181"/);
 assert.match(help(10,'finish',1),/6 = 3 × 2 \+ 0/);assert.match(help(10,'finish',2),/Return d = 2, a = 1, b = −2/);
 assert.doesNotMatch(help(6,'factor',2),/One allowed failure refutes/);
});
