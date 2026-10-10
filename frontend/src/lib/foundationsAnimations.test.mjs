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
 element.dataset.x='100';notify();frame(100);frame(132);
 const midway=attributes.get('transform'),beforePause=writes;
 assert.notEqual(midway,'translate(0 0)');assert.notEqual(midway,'translate(100 0)');
 svg.dataset.paused='true';notify();frame(148);
 assert.equal(callbacks.size,0);assert.equal(writes,beforePause);
 for(let i=0;i<500;i++)frame(164+i*16);
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
test('every Euclid package reconstructs its value from the fixed original pair',()=>{
 for(let m=2;m<=80;m++)for(let n=2;n<=40;n++){const rows=euclidPackages(m,n);for(const row of rows)assert.equal(row.a*m+row.b*n,row.value);assert.equal(rows.at(-1).value,gcd(m,n));}
 assert.deepEqual(euclidPackages(26,15).map(({value,a,b})=>[value,a,b]),[[26,1,0],[15,0,1],[11,1,-1],[4,-1,2],[3,3,-5],[1,-4,7]]);
 assert.deepEqual(euclidPackages(14,6).at(-1),{id:'r2',value:2,a:1,b:-2,q:2});
});
test('all authored main and smaller-help states are renderable, finite and genuinely change object positions',()=>{
 for(const lesson of lessons)for(const section of lesson.sections)for(const passage of section.passages){
  const d=passage.demonstration,main=d.states.map((state,i)=>render({exampleId:passage.id,frameIndex:i,frame:{id:state.id},visual:{model:d.model,state}}));
  const help=[-1,...d.simplerHelp.steps.map((_,i)=>i)].map(i=>render({exampleId:passage.id,visual:{model:d.model,helpMode:true,helpStepIndex:i,helpContent:d.simplerHelp}}));
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
