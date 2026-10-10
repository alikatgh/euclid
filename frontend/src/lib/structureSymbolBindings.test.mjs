import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {structureSymbolBinding as binding} from './structureSymbolBindings.js';
const lessons=['D','E'].flatMap(batch=>JSON.parse(readFileSync(new URL(`../../../content/fullbook/batch-${batch}.json`,import.meta.url))));
function contexts(order){const lesson=lessons.find(l=>l.order===order);return lesson.sections.flatMap(s=>s.passages).flatMap(p=>{const d=p.demonstration;return [d,...(d.simplerHelp?[d.simplerHelp]:[])].flatMap(x=>(x.states??[]).map(state=>({frame:{visual:{order,state,model:x.model??d.model,helpMode:x!==d}}})));});}
function element(token,expression='',id='',offset=-1,more={}){const attrs={'data-math-token':token,'data-math-expression':expression,'data-math-offset':String(offset),...more};const group={getAttribute:k=>k==='data-diagram-node'?id:null};return {getAttribute:k=>attrs[k]??null,closest:q=>q==='[data-diagram-node]'&&id?group:null,textContent:expression};}
function context(order,predicate){const c=contexts(order).find(x=>predicate(x.frame.visual.state));assert.ok(c,`fixture ${order}`);return c;}
function key(c,t,e,id='',offset=-1,more={}){return binding(element(t,e,id,offset,more),c)?.keys;}
test('real D identity distinguishes equal payloads and addresses',()=>{const c=context(88,s=>s.diagram.nodes.some(n=>n.id==='card-A'));assert.deepEqual(key(c,'A','A'),['object:A']);assert.deepEqual(key(c,'7','A:7','card-A-label',2),['node-value:A']);assert.deepEqual(key(c,'7','B:7','card-B-label',2),['node-value:B']);assert.deepEqual(key(c,'12','@12','address-A',1),['node-address:A']);assert.equal(binding(element('a','a linked list'),c),null);assert.equal(binding(element('A','A list contains nodes', '',0),c),null);});
test('formula f(B) selects authored B and physical node shares key',()=>{const c=context(116,s=>s.diagram.nodes.some(n=>n.id==='node-B'));assert.deepEqual(key(c,'B','f(B)'),['object:B']);assert.deepEqual(key(c,null,'','node-B'),['object:B']);});
test('weighted fold separates equal slot and child numerals and sums products',()=>{const c=context(116,s=>s.data?.node==='A'&&s.data?.childIds?.includes('C')&&s.diagram.nodes.some(n=>n.id==='fold-product-C'));const exp='2 × 2 = 4';assert.deepEqual(key(c,'2',exp,'fold-product-C',0),['child-slot:A:2']);assert.deepEqual(key(c,'2',exp,'fold-product-C',4),['node-value:C']);assert.deepEqual(key(c,'4',exp,'fold-product-C',8),['fold-product:A:C']);const p=binding(element(null,'','fold-value-C'),c);assert.ok(p.memberships.includes('node-value:C'));assert.ok(p.memberships.includes('operation:sum'));});
test('AST constant occurrences and operators retain separate identities',()=>{const c=context(113,s=>s.diagram.nodes.some(n=>n.id==='node-a'));const labels=c.frame.visual.state.diagram.nodes.filter(n=>n.id.startsWith('label-'));const constants=labels.filter(n=>/^\d+$/.test(n.text));for(const n of constants){const id=n.id.slice(6);assert.deepEqual(key(c,n.text,n.text,n.id,0),[`ast:value:${id}`]);assert.ok(binding(element(null,'',`node-${id}`),c).memberships.includes(`ast:value:${id}`));}});
test('product-rule original and derivative factors select distinct actual main/help subtrees',()=>{
 let checked=0,helpChecked=0;
 for(const c of contexts(114)){
  const state=c.frame.visual.state,names=state.data?.identities;
  if(!names||!state.diagram.nodes.some(n=>n.id===`factor-title-${names.du}`))continue;
  for(const name of ['u','v']){
   const original=names[name],derivative=names['d'+name];
   assert.deepEqual(key(c,name,`original ${name}`,`factor-title-${original}`),[`object:${original}`]);
   assert.deepEqual(key(c,name+'′',`new ${name}′`,`factor-title-${derivative}`),[`object:${derivative}`]);
   assert.deepEqual(key(c,name+'′',`${name}′`),[`object:${derivative}`]);
   assert.deepEqual(key(c,null,'',`node-${derivative}`),[`object:${derivative}`]);
  }
  checked++;if(c.frame.visual.helpMode)helpChecked++;
 }
 assert.ok(checked>0);assert.ok(helpChecked>0,'actual smaller-help product-rule states must be covered');
});
test('array arithmetic distinguishes stride four from offset four',()=>{const c=context(103,s=>s.diagram.nodes.some(n=>n.id==='physical-address'));const e='address = b + s × offset = 100 + 4 × 4 = 116';const first=e.indexOf('4'),second=e.indexOf('4',first+1);assert.deepEqual(key(c,'4',e,'physical-address',first),['array:stride']);assert.deepEqual(key(c,'4',e,'physical-address',second),['array:offset']);assert.deepEqual(key(c,'116',e,'physical-address',e.indexOf('116')),['array:address']);});
test('parallel edge identities and edge counts remain distinct',()=>{const c=context(120,s=>s.diagram.nodes.some(n=>n.id==='arc-0'));assert.deepEqual(key(c,'2','e0:2','arc-label-0',3),['graph-edge-count:e0']);assert.deepEqual(key(c,'2','e1:2','arc-label-1',3),['graph-edge-count:e1']);assert.deepEqual(key(c,null,'','arc-0'),['graph-edge:e0']);});
test('every D/E main/help physical node resolves without errors or undefined keys',()=>{let count=0;for(const l of lessons)for(const c of contexts(l.order))for(const n of c.frame.visual.state.diagram?.nodes??[]){const result=binding(element(null,'',n.id),c);if(result){count++;assert.ok(result.keys.length);assert.ok(result.keys.every(k=>typeof k==='string'&&!k.includes('undefined')));assert.ok(result.role&&result.description);}}assert.ok(count>1000);});
test('sparse polynomial coefficient and exponent stay distinct',()=>{const c=context(99,s=>s.diagram.nodes.some(n=>n.id==='P-3'));assert.deepEqual(key(c,'2','2x^3','P-3-label',0),['polynomial:coefficient:P:3']);assert.deepEqual(key(c,'3','2x^3','P-3-label',3),['polynomial:exponent:P:3']);});
test('pivot substitution preserves two distinct old values both printed 2',()=>{const c=context(105,s=>s.evidence?.operandCells&&s.diagram.nodes.some(n=>n.id==='actual-substitution'));const e='new d = 2 − (4 × 1) / 2';assert.deepEqual(key(c,'2',e,'actual-substitution',e.indexOf('2')),['pivot:operand:d']);assert.deepEqual(key(c,'2',e,'actual-substitution',e.lastIndexOf('2')),['pivot:operand:a']);assert.ok(binding(element(null,'','old-cell-0-0'),c).memberships.includes('pivot:operand:a'));});
