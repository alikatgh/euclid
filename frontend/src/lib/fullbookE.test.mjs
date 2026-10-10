import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const lessons=JSON.parse(readFileSync(resolve(root,'content/fullbook/batch-E.json'),'utf8'));
const passage=(n,id)=>lessons.find(l=>l.order===n).sections.flatMap(s=>s.passages).find(p=>p.id===id);
const demo=(n,id)=>passage(n,id).demonstration;
const nodes=t=>t?[t[0],...nodes(t[1]),...nodes(t[2])]:[];
const order=(t,k)=>!t?[]:k==='pre'?[t[0],...order(t[1],k),...order(t[2],k)]:k==='in'?[...order(t[1],k),t[0],...order(t[2],k)]:[...order(t[1],k),...order(t[2],k),t[0]];
const fOrder=(f,k)=>f.flatMap(([v,ch])=>k==='pre'?[v,...fOrder(ch,k)]:[...fOrder(ch,k),v]);
function decode(e){
 if(e.kind==='post'){const stack=[];for(const r of e.records){assert.ok(r.degree<=stack.length);const ch=r.degree?stack.splice(stack.length-r.degree):[];stack.push([r.id,ch]);}return stack;}
 const get=i=>[e.records[i].id,e.records[i].children.map(get)];return e.roots.map(get);
}
function flatPoly(t,offset=[0,0]){
 if(typeof t==='number')return t?[[offset,t]]:[];
 return Object.entries(t.terms).flatMap(([e,c])=>{const k=[...offset];k[t.var==='x'?0:1]+=Number(e);return flatPoly(c,k);});
}
function evalAst(a,x){
 if(a[0]==='c')return Number(a[1]);if(a[0]==='v')return x;
 const u=evalAst(a[1],x),v=a[2]?evalAst(a[2],x):undefined;
 return ({'+':()=>u+v,'-':()=>u-v,'*':()=>u*v,'/':()=>u/v,pow:()=>u**v,neg:()=>-u,ln:()=>Math.log(u),exp:()=>Math.exp(u)})[a[0]]();
}
function assertTicketTour(arcs,tour){
 assert.deepEqual([...tour].sort((a,b)=>a-b),arcs.map((_,i)=>i));
 for(let i=1;i<tour.length;i++)assert.equal(arcs[tour[i-1]][1],arcs[tour[i]][0]);
}
test('E includes every planned unit with individual formal and smaller-help demonstrations',()=>{
 assert.deepEqual(lessons.map(l=>l.order),Array.from({length:17},(_,i)=>106+i));
 const ids=new Set();let n=0;
 for(const l of lessons)for(const p of l.sections.flatMap(s=>s.passages)){
  assert.ok(p.text.length>250);const d=p.demonstration;assert.ok(!ids.has(d.id));ids.add(d.id);n++;
  assert.ok(d.states.length>=2&&d.simplerHelp.states.length>=2);assert.notEqual(d.check.prompt,d.simplerHelp.check.prompt);
  assert.equal(d.model.implementation,'scripts/fullbook-batch-E.py');
 }
 assert.equal(n,68);
});
test('E traversal words and stack emitted prefixes are independently reconstructed',()=>{
 const d=demo(108,'visit-events'),t=d.model.input;
 for(const k of ['pre','in','post'])assert.deepEqual(d.states.filter(s=>s.data.phase===k).map(s=>s.data.node),order(t,k));
 const it=demo(109,'derive-stack');let previous=[];
 for(const s of it.states){assert.deepEqual(s.data.output,order(it.model.input,'in').slice(0,s.data.output.length));assert.ok(s.data.output.length>=previous.length);previous=s.data.output;}
 assert.deepEqual(previous,order(t,'in'));
});
test('E threads distinguish missing slots and copied addresses never cross back',()=>{
 const d=demo(110,'tags'),t=d.model.input,n=d.model.links,seq=order(t,'in');
 const inspect=t=>{if(!t)return;const [v,l,r]=t,i=seq.indexOf(v);assert.equal(n[v].LT,l?0:1);assert.equal(n[v].RT,r?0:1);assert.equal(n[v].L,l?l[0]:(seq[i-1]??'H'));assert.equal(n[v].R,r?r[0]:(seq[i+1]??'H'));inspect(l);inspect(r);};inspect(t);
 const copied=demo(111,'insert-right').states.at(-1).data;
 for(const [v,z] of Object.entries(copied.copy)){assert.ok(!(v in copied.original));assert.ok(z.L in copied.copy);assert.ok(z.R in copied.copy);}
});
test('E forest conversion and all sequence formats preserve ordered families',()=>{
 const m=demo(112,'two-links').model;
 assert.deepEqual(fOrder(m.forest,'pre'),order(m.binary,'pre'));
 assert.deepEqual(fOrder(m.forest,'post'),order(m.binary,'in'));
 const seq=demo(115,'storage-order').model;
 for(const e of seq.encodings)assert.deepEqual(decode(e),seq.forest);
 assert.deepEqual(seq.encodings.find(e=>e.kind==='family').records.map(r=>r.id),order(m.binary,'post').reverse());
});
test('E expression evaluation keeps noncommutative operand order and derivative is an actual AST',()=>{
 const expr=demo(113,'meaningful-arity').model;assert.equal(evalAst(expr.ast,0),3);assert.equal(expr.value,'3');
 const d=demo(114,'postorder-transform').model;
 for(const x of [-4,-2,-1,0,1,5,11]){
  assert.equal(evalAst(d.source,x),x*(x+2)**2);
  assert.equal(evalAst(d.derivative,x),3*x*x+8*x+4);
 }
 assert.equal(d.derivative[0],'+');
 const bad=demo(114,'simplify-carefully').states;assert.equal(bad[0].data.defined,false);assert.equal(bad[1].data.defined,true);
});
test('E bottom-up fold and canonical polynomial cancellation match independent representations',()=>{
 const d=demo(116,'local-function');const local=t=>t[1].length?t[1].reduce((a,c,i)=>a+(i+1)*local(c),0):d.model.leafValues[t[0]];
 assert.deepEqual(d.states.at(-1).data.stack,d.model.forest.map(local));
 const p=demo(118,'recursive-polynomial').model;const sums=new Map();
 for(const [k,c] of [...flatPoly(p.P),...flatPoly(p.Q)])sums.set(k.join(','),(sums.get(k.join(','))??0)+c);
 const expected=[...sums].filter(([,c])=>c).sort();assert.deepEqual(flatPoly(p.sum).map(([k,c])=>[k.join(','),c]).sort(),expected);assert.equal(p.sum,5);
});
test('E signed flow basis, root convention and Euler last exits carry the necessary conditions',()=>{
 const m=demo(120,'backbone').model;
 const div=row=>Object.fromEntries(m.vertices.map(v=>[v,m.edges.reduce((z,[u,w],i)=>z+row[i]*((u===v?1:0)-(w===v?1:0)),0)]));
 assert.deepEqual(div(m.path),{S:1,A:0,B:0,T:-1});for(const c of m.cycles)assert.deepEqual(Object.values(div(c)),[0,0,0,0]);
 for(const s of demo(121,'source-convention').states){const d=s.data;for(const v of d.vertices){const count=d.arcs.filter(([a,b])=>(d.outward?b:a)===v).length;assert.equal(count,v===d.root?0:1);}}
 const e=demo(122,'trail-domain'),last=e.states.at(-1).data;assertTicketTour(last.arcs,last.tour);
 const end=last.walk.at(-1);for(const v of Object.keys(last.lastExits)){let cur=v;const seen=new Set();while(cur!==end){assert.ok(!seen.has(cur));seen.add(cur);cur=last.arcs[last.lastExits[cur]][1];}}
 const candidates=demo(122,'degree-and-connectivity').states;assert.equal(candidates[0].data.exists,false);assert.equal(candidates[1].data.exists,true);assert.equal(candidates[2].data.exists,false);assert.equal(candidates[3].data.exists,true);
});
test('E exact models pass exhaustive independent semantic oracles in Python',()=>{
 const result=JSON.parse(execFileSync('python',[resolve(root,'scripts/fullbook-batch-E.py'),'--test'],{encoding:'utf8',timeout:20000}));
 assert.equal(result.binary_shapes,197);assert.equal(result.sequence_roundtrips,788);assert.equal(result.thread_insertions,1078);
 assert.equal(result.simple_graphs,1099);assert.equal(result.directed_multigraphs,715);assert.equal(result.polynomial_additions,6561);assert.equal(result.lessons,17);
});

test('E mutable polynomial rings splice, unlink, collapse and repair retained UP links',()=>{
 const states=demo(118,'links-and-cost').states;
 const flatten=(pool,id,offset=[0,0])=>{
  const n=pool[id];if(n.DOWN===null)return n.CV?[[offset,n.CV]]:[];
  const out=[];let c=n.DOWN;const seen=new Set();
  do{
   assert.ok(!seen.has(c));seen.add(c);const z=pool[c];assert.equal(z.UP,id);
   assert.equal(pool[z.LEFT].RIGHT,c);assert.equal(pool[z.RIGHT].LEFT,c);
   const ex=[...offset];ex[n.CV==='x'?0:1]+=z.EXP;out.push(...flatten(pool,c,ex));c=z.RIGHT;
  }while(c!==n.DOWN);return out;
 };
 for(const s of states){const d=s.data;const actual=flatten(d.nodes,d.root).map(([k,c])=>[k.join(','),c]).sort();const expected=d.flat.map(t=>[t.exponents.join(','),t.coefficient]).sort();assert.deepEqual(actual,expected);
  for(const edge of s.diagram.nodes.filter(n=>n.type==='path'&&n.id.startsWith('up-')&&!n.id.endsWith('-head'))){
   const child=edge.id.slice(3),parent=d.nodes[child].UP,target=s.diagram.nodes.find(n=>n.id==='node-'+parent);
   const coords=edge.d.trim().split(/\s+/).map(Number).filter(Number.isFinite);const [x,y]=coords.slice(-2);
   assert.ok(Math.abs(Math.hypot(x-target.x,y-target.y)-23)<1e-8,'UP arrow must end outside the actual parent circle');
  }
 }
 const before=states.at(-2).data,after=states.at(-1).data;
 assert.equal(before.nodes[before.root].CV,'y');assert.equal(after.nodes[after.root].CV,'x');assert.equal(before.root,after.root);
 const survivors=Object.keys(after.nodes).filter(v=>v!==after.root);assert.equal(survivors.length,2);
 for(const v of survivors){assert.ok(v in before.nodes);assert.notEqual(before.nodes[v].UP,after.nodes[v].UP);assert.equal(after.nodes[v].UP,after.root);}
});

test('E116 visibly explains weighted 7 and 2 becoming 11 in three causal stages',()=>{
 const states=demo(116,'local-function').states.filter(s=>s.data.node==='A');
 assert.deepEqual(states.map(s=>s.data.stage),['ordered-slots','weight-each-child','sum-products']);
 for(const s of states){assert.deepEqual(s.data.childIds,['B','C']);assert.deepEqual(s.data.children,[7,2]);assert.deepEqual(s.data.weights,[1,2]);assert.deepEqual(s.data.products,[7,4]);}
 const labels=s=>s.diagram.nodes.filter(n=>n.type==='text').map(n=>n.text);
 assert.ok(labels(states[1]).includes('1 × 7 = 7'));assert.ok(labels(states[1]).includes('2 × 2 = 4'));
 assert.ok(labels(states[2]).includes('Weighted total: 7 + 4 = 11'));
 assert.deepEqual(states[0].data.stack,[7,2]);assert.deepEqual(states[2].data.stack,[11]);
 const small=demo(116,'local-function').simplerHelp.states;
 assert.ok(small.some(s=>s.data.stage==='weight-each-child'&&s.diagram.nodes.some(n=>n.text==='1 × 3 = 3')));
});
test('E114 preserves original factors, constructs both derivative products, then joins them',()=>{
 const d=demo(114,'postorder-transform');const selected=d.states.filter(s=>s.id.startsWith('product-a-'));
 assert.deepEqual(selected.map(s=>s.data.stage),['identify-originals','construct-products','join']);
 const z=selected[1].data;assert.deepEqual(z.sourceU,['v','x']);assert.deepEqual(z.derivativeU,['c','1']);
 assert.deepEqual(z.leftContribution,['*',z.derivativeU,z.sourceV]);assert.deepEqual(z.rightContribution,['*',z.sourceU,z.derivativeV]);
 assert.deepEqual(z.constructedDerivative,['+',z.leftContribution,z.rightContribution]);
 for(const s of selected){assert.ok(s.diagram.nodes.some(n=>n.id==='node-'+z.identities.u));assert.ok(s.diagram.nodes.some(n=>n.id==='node-'+z.identities.v));}
 assert.ok(selected[1].diagram.nodes.some(n=>n.id==='node-'+z.identities.du));assert.ok(selected[1].diagram.nodes.some(n=>n.id==='node-'+z.identities.dv));
 assert.ok(!selected[1].diagram.nodes.some(n=>n.id==='sum-op-a'));assert.ok(selected[2].diagram.nodes.some(n=>n.id==='sum-op-a'));
 const chain=d.states.find(s=>s.id==='chain-a1');assert.deepEqual(chain.data.innerDerivative,['c','1']);assert.ok(chain.diagram.nodes.some(n=>n.id==='chain-factor'&&n.text.includes('= 1')));
 for(const x of [-2,0,3])assert.equal(evalAst(z.constructedDerivative,x),evalAst(d.model.derivative,x));
});

test('tree and flow notation is decoded alongside its first local use',()=>{
 for(const [n,id,needles] of [
  [106,'recursive-definition',['disjoint union','{r}','k naming']],
  [106,'size-induction',['number of nodes','The 1 counts','no node is counted twice']],
  [114,'postorder-transform',['abstract syntax tree','with respect to x']],
  [114,'product-chain',['composition','u runs first']],
  [120,'incidence',['incidence matrix','1 in the row','signed edge counts']],
  [120,'basis-proof',['α_j tells','separately for every edge']],
  [122,'degree-and-connectivity',['outgoing arcs','indicator','two indicators cancel']],
 ]){
   const p=passage(n,id),reading=p.demonstration.states[0].teachingExplanation;
   assert.ok(reading);
   for(const needle of needles){assert.ok(p.text.includes(needle),`${n}/${id}: ${needle}`);assert.ok(reading.includes(needle));}
 }
});
