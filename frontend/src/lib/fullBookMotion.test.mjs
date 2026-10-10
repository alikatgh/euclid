import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {mkdtempSync,writeFileSync,readFileSync,existsSync,readdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
const root=resolve(import.meta.dirname,'../..'),temp=mkdtempSync(join(tmpdir(),'euclid-fullbook-scenes-'));
execFileSync(join(root,'node_modules/.bin/tsc'),['--ignoreConfig','--jsx','react-jsx','--module','commonjs','--target','es2023','--moduleResolution','node','--ignoreDeprecations','6.0','--skipLibCheck','--outDir',temp,join(root,'src/components/FullBookScene.tsx'),join(root,'src/components/fullBookMotion.ts')]);
writeFileSync(join(temp,'package.json'),'{"type":"commonjs"}');
// Resolve the new shared browser annotation helper from the source checkout.
writeFileSync(join(temp,'FullBookScene.js'),readFileSync(join(temp,'FullBookScene.js'),'utf8').replaceAll('../lib/symbolConnections.js',join(root,'src/lib/symbolConnections.js')));
const require=createRequire(join(root,'package.json'));process.env.NODE_PATH=join(root,'node_modules');require('node:module').Module._initPaths();
const {FullBookScene}=require(join(temp,'FullBookScene.js')),{bindFullBookMotion}=require(join(temp,'fullBookMotion.js'));
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
class Element{constructor(attrs={},tagName='g',child=null){this.a=new Map(Object.entries(attrs).map(([k,v])=>[k,String(v)]));this.tagName=tagName;this.child=child;}setAttribute(k,v){this.a.set(k,String(v));}getAttribute(k){return this.a.get(k)??null;}querySelector(){return this.child;}}
test('semantic diagram motion keeps directed edges, result claims and paused time coherent',()=>{
 let id=0,queue=new Map();global.requestAnimationFrame=f=>{queue.set(++id,f);return id};global.cancelAnimationFrame=i=>queue.delete(i);global.matchMedia=()=>({matches:false});
 const shape=new Element({},'line'),a=new Element({'data-diagram-node':'edge','data-x':0,'data-y':10,'data-ex':80,'data-ey':20},'g',shape),result=new Element();
 const svg=new Element();svg.isConnected=true;svg.querySelectorAll=q=>q==='[data-diagram-node]'?[a]:q==='[data-diagram-result]'?[result]:[];
 const step=t=>{const fs=[...queue.values()];queue.clear();fs.forEach(f=>f(t));};
 bindFullBookMotion(svg,'demo:0');a.setAttribute('data-x',100);a.setAttribute('data-ex',20);bindFullBookMotion(svg,'demo:1');
 assert.equal(result.getAttribute('opacity'),'0');step(100);step(700);
 const pos=a.getAttribute('transform'),edge=shape.getAttribute('x2'),phase=svg.getAttribute('data-motion-progress');assert.notEqual(pos,'translate(0 10)');assert.notEqual(pos,'translate(100 10)');assert.ok(Number(edge)>20&&Number(edge)<80);
 bindFullBookMotion(svg,'demo:1',true);for(let i=0;i<100;i++)bindFullBookMotion(svg,'demo:1',true);assert.equal(queue.size,0);step(9000);assert.equal(a.getAttribute('transform'),pos);assert.equal(svg.getAttribute('data-motion-progress'),phase);assert.equal(result.getAttribute('opacity'),'0');
 bindFullBookMotion(svg,'demo:1',false);step(10000);assert.equal(a.getAttribute('transform'),pos);step(10600);assert.equal(a.getAttribute('transform'),'translate(100 10)');assert.equal(shape.getAttribute('x2'),'20');assert.equal(result.getAttribute('opacity'),'1');
 a.setAttribute('data-x',0);bindFullBookMotion(svg,'demo:0');assert.equal(a.getAttribute('transform'),'translate(0 10)');
 global.matchMedia=()=>({matches:true});a.setAttribute('data-x',90);bindFullBookMotion(svg,'demo:1');assert.equal(a.getAttribute('transform'),'translate(90 10)');assert.equal(queue.size,0);
 global.matchMedia=()=>({matches:false});a.setAttribute('data-x',120);bindFullBookMotion(svg,'demo:2');svg.isConnected=false;step(12000);assert.equal(queue.size,0);
});
test('every full-book authored main and smaller-help diagram renders accessible stable SVG identities',()=>{
 const dir=join(root,'../content/fullbook');let count=0;
 if(!existsSync(dir))return;for(const f of readdirSync(dir).filter(f=>/^batch-[A-F]\.json$/.test(f))){const data=JSON.parse(readFileSync(join(dir,f),'utf8'));for(const lesson of Array.isArray(data)?data:data.lessons)for(const section of lesson.sections)for(const passage of section.passages){
 const d=passage.demonstration;for(const [mode,states]of [['main',d.states],['help',d.simplerHelp.states]])for(const [frameIndex,state]of states.entries()){
 const html=renderToStaticMarkup(React.createElement(FullBookScene,{exampleId:d.id+'-'+mode,frameIndex,visual:{state,helpMode:mode==='help'}}));assert.ok(html.includes('role="img"'));assert.ok(!/missing its computed|(?:data-[a-z-]+|transform|width|height|cx|cy|r)="[^"]*(?:NaN|Infinity)/.test(html),lesson.id+' '+state.id);const ids=[...html.matchAll(/data-diagram-node="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);assert.ok(ids.length);count++;
 }
 }}if(process.env.FULLBOOK_COMPLETE==='1')assert.ok(count>=124*3*4,'both actual main/help states for every passage');
});
