import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fullBookSymbolBinding as bind} from './fullBookSymbolBindings.js';
const lessons=['C','F'].flatMap(b=>JSON.parse(readFileSync(new URL(`../../../content/fullbook/batch-${b}.json`,import.meta.url))));
const context=(order,p=0,si=0,help=false)=>{const l=lessons.find(l=>l.order===order),main=l.sections[0].passages[p].demonstration,d=help?main.simplerHelp:main;return {frame:{visual:{order,lessonId:l.id,state:d.states[si],model:d.model,helpMode:help}}};};
function el(token,id='',expression=token??'',extra={}){const attrs={...extra,...(token!==null?{'data-math-token':token,'data-math-expression':expression}:{'data-diagram-node':id})};const g={getAttribute:k=>k==='data-diagram-node'?id:null};return {getAttribute:k=>attrs[k]??null,closest:q=>q==='[data-diagram-node]'&&id?g:null,textContent:token??''};}
const keys=b=>[...b.keys,...(b.memberships??[])];
const meets=(a,b)=>Boolean(a&&b&&a.keys.some(k=>keys(b).includes(k)));
test('MIX field roles reach exactly selected memory and right-aligned register positions in both directions',()=>{
 for(let p=0;p<4;p++)for(const help of [false,true]){
  const c=context(66,p,0,help),f=c.frame.visual.model.field,L=Math.floor(f/8),R=f%8,n=Math.max(0,R-Math.max(L,1)+1);
  const F=bind(el('F'),c),left=bind(el('L'),c),right=bind(el('R'),c);
  for(let position=0;position<=5;position++){
   const mem=bind(el(null,`w0-${position}`),c),reg=bind(el(null,`w1-${position}`),c),memorySelected=position>=L&&position<=R,registerSelected=(position===0&&L===0)||(n>0&&position>=6-n);
   assert.equal(meets(F,mem),memorySelected,`${p}/${help}: memory ${position}`);
   assert.equal(meets(F,reg),registerSelected,`${p}/${help}: register ${position}`);
   if(memorySelected)assert.ok(meets(mem,F));if(registerSelected)assert.ok(meets(reg,F));
  }
  assert.ok(meets(left,bind(el(null,`w0-${L}`),c)));assert.ok(meets(left,bind(el(null,`w1-${L===0?0:6-n}`),c)));
  assert.ok(meets(right,bind(el(null,`w0-${R}`),c)));assert.ok(meets(right,bind(el(null,`w1-${n?5:0}`),c)));
 }
});
test('Equal MIX position and byte values keep distinct identities while both reach their compartment',()=>{
 const c=context(66),position=bind(el('2','p0-2','2'),c),value=bind(el('2','v0-2','2'),c),box=bind(el(null,'w0-2'),c);
 assert.ok(meets(position,box));assert.ok(meets(value,box));assert.ok(!meets(position,value));assert.ok(!meets(value,position));
 const R=bind(el('R','','CMP(R,M)'),context(67));assert.ok(meets(R,bind(el(null,'w0-2'),context(67))));
});
test('Buddy offset/order roles reach physical blocks; equal address/size numerals remain different roles',()=>{
 const c=context(140,0,3),x=bind(el('x'),c),k=bind(el('k'),c),block=bind(el(null,'block16'),c),size=bind(el('16','block16size','16'),c),address=bind(el('16','block16addr','16'),c);
 assert.ok(meets(x,block));assert.ok(meets(k,block));assert.ok(meets(block,x));assert.ok(meets(size,k));assert.ok(meets(address,x));
 assert.ok(!meets(size,address));assert.ok(!meets(address,size));assert.ok(meets(size,block));assert.ok(meets(address,block));
 const proseSize=bind(el('16','','size 16',{'data-math-offset':'5'}),c);assert.ok(meets(proseSize,size));assert.ok(meets(proseSize,block));assert.ok(!meets(proseSize,address));
});
test('Tree identities, depth contributions and sum membership are source/shape symmetric',()=>{
 let c=context(131);assert.ok(meets(bind(el('A'),c),bind(el(null,'vA'),c)));assert.ok(meets(bind(el(null,'vA'),c),bind(el('A'),c)));
 c=context(127);assert.ok(meets(bind(el('E'),c),bind(el(null,'r'),c)));assert.ok(meets(bind(el(null,'r'),c),bind(el('E'),c)));
 c=context(76);assert.ok(meets(bind(el('Σ'),c),bind(el(null,'signed-term-0'),c)));assert.ok(meets(bind(el(null,'signed-term-0'),c),bind(el('Σ'),c)));
});
test('Live/free allocator summations select only their specified subsets',()=>{
 const c=context(140,0,4),live=bind(el('Σ','',String.raw`\sum_{live} s_i`),c),free=bind(el('Σ','',String.raw`\sum_{free} s_i`),c),allocated=bind(el(null,'block0'),c),available=bind(el(null,'block16'),c);
 assert.ok(meets(live,allocated));assert.ok(!meets(live,available));assert.ok(meets(free,available));assert.ok(!meets(free,allocated));
});
test('All C/F authored physical nodes can be resolved without mutating frozen source models',()=>{
 for(const l of lessons)for(const section of l.sections)for(const p of section.passages)for(const d of [p.demonstration,p.demonstration.simplerHelp])for(const state of d.states){
  const before=JSON.stringify(state),c={frame:{visual:{order:l.order,lessonId:l.id,state,model:d.model}}};
  for(const node of state.diagram.nodes){const result=bind(el(null,node.id),c);if(result){assert.ok(result.keys.length);assert.ok(result.role);assert.ok(result.description);}}
  assert.equal(JSON.stringify(state),before);
 }
});
