import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import katex from 'katex';
const root=new URL('../../../',import.meta.url);
const lessons=JSON.parse(fs.readFileSync(new URL('content/fullbook/batch-B.json',root),'utf8'));
const passages=lessons.flatMap(l=>l.sections.flatMap(s=>s.passages));
test('batch B covers 47–64 with substantive prose and private-source-free public data',()=>{
 assert.deepEqual(lessons.map(l=>l.order),Array.from({length:18},(_,i)=>47+i));
 assert.equal(passages.length,54);
 for(const l of lessons){assert.ok(l.source.pdfPages);assert.ok(l.scope.length>80);}
 for(const p of passages){assert.ok(p.text.length>500);assert.ok(p.demonstration);assert.ok(p.demonstration.simplerHelp.states.length>=2);}
 assert.doesNotMatch(JSON.stringify(lessons),/\/workspace\/|file:\/\/|knuth-volume1\.pdf/);
});
test('all batch B equations render in strict KaTeX without escaping errors',()=>{
 for(const p of passages){
  const d=p.demonstration;
  for(const formula of [p.formula,...d.states.map(s=>s.formula),...d.simplerHelp.states.map(s=>s.formula)])
   assert.doesNotThrow(()=>katex.renderToString(formula,{throwOnError:true,strict:'error'}),`${p.id}: ${formula}`);
 }
});
test('computed states have bounded geometry, unique identities and gated result nodes',()=>{
 for(const p of passages){const d=p.demonstration;for(const s of [...d.states,...d.simplerHelp.states]){
  assert.deepEqual(s.diagram.viewBox,[0,0,720,440]);assert.ok(Object.keys(s.computed).length);
  const ids=s.diagram.nodes.map(n=>n.id);assert.equal(ids.length,new Set(ids).size);
  for(const n of s.diagram.nodes){
   for(const [k,v] of Object.entries(n))if(typeof v==='number')assert.ok(Number.isFinite(v),`${p.id}/${n.id}/${k}`);
   if(n.role==='result')assert.equal(n.result,true);
   if(n.type==='rect'){assert.ok(n.width>=0&&n.height>=0);assert.ok(n.x+n.width<=720);assert.ok(n.y+n.height<=440);}
  }
 }}
});
test('transitions and both transfer checks point to valid authored content',()=>{
 for(const p of passages){const d=p.demonstration;const ids=new Set(d.states.map(s=>s.id));
  for(const t of d.transitions){assert.ok(ids.has(t.from));assert.ok(ids.has(t.to));assert.ok(t.explanation);}
  for(const c of [d.check,d.simplerHelp.check]){assert.ok(c.correctIndex>=0&&c.correctIndex<c.choices.length);assert.equal(c.choices.length,new Set(c.choices).size);assert.ok(c.explanation.length>40);}
 }
});
test('probability scenes conserve exact displayed mass and avoid variance/second-moment confusion',()=>{
 const fraction=s=>{const [a,b='1']=String(s).split('/');return Number(a)/Number(b);};
 for(const p of passages)for(const s of p.demonstration.states){const c=s.computed;if(c.probabilities){const weights=c.probabilities.map(fraction);assert.ok(Math.abs(weights.reduce((a,b)=>a+b,0)-1)<1e-12);assert.ok(weights.every(v=>v>=0));
  if(c.variance){const mean=weights.reduce((a,v,k)=>a+k*v,0);const variance=weights.reduce((a,v,k)=>a+(k-mean)**2*v,0);assert.ok(Math.abs(fraction(c.variance)-variance)<1e-12);}
 }}
});
test('deterministic authoring and independent standard-library mathematical oracles pass',()=>{
 const script=new URL('scripts/fullbook-batch-B.py',root).pathname;
 assert.match(execFileSync('python3',[script,'--check'],{encoding:'utf8'}),/current/);
 execFileSync('python3',[script,'--test'],{encoding:'utf8',stdio:'pipe'});
});
test('convolution grids distinguish exponent indices from coefficient weights',()=>{
 for(const p of passages)for(const s of [...p.demonstration.states,...p.demonstration.simplerHelp.states]){
  if(!Array.isArray(s.computed.a)||!Array.isArray(s.computed.b))continue;
  const nodes=new Map(s.diagram.nodes.map(n=>[n.id,n]));
  s.computed.a.forEach((v,i)=>{assert.equal(nodes.get(`i${i}`).text,`i=${i}`);assert.equal(nodes.get(`a${i}`).text,`aᵢ=${v}`);});
  s.computed.b.forEach((v,j)=>{assert.equal(nodes.get(`j${j}`).text,`j=${j}`);assert.equal(nodes.get(`b${j}`).text,v);});
 }
});
test('passage checks target distinct claims and helpers do not recycle main prompts',()=>{
 for(const l of lessons){
  const ds=l.sections.flatMap(s=>s.passages.map(p=>p.demonstration));
  const prompts=ds.flatMap(d=>[d.check.prompt,d.simplerHelp.check.prompt]);
  assert.equal(new Set(prompts).size,prompts.length,l.id);
  for(const d of ds)for(const q of [d.check,d.simplerHelp.check])assert.ok(q.explanation.length>90);
 }
});
test('new factorial and Bernoulli scenes verify their exact mathematical meanings',()=>{
 const fact=n=>{let x=1;for(let k=2;k<=n;k++)x*=k;return x;};
 const number=s=>{const [a,b='1']=String(s).split('/');return Number(a)/Number(b);};
 const get=id=>passages.find(p=>p.id===id).demonstration;
 for(const states of [get('b47-p3').states,get('b47-p3').simplerHelp.states])for(const s of states){
  const c=s.computed,z=number(c.z);c.terms.forEach((v,n)=>assert.equal(number(v),fact(n)*z**n));
  assert.equal(number(c.ratio),(c.focus+1)*Math.abs(z));
 }
 for(const states of [get('b51-p3').states,get('b51-p3').simplerHelp.states])for(const s of states){
  const c=s.computed,d=c.denominator.map(number),a=c.coefficients.map(number);
  a.forEach((v,n)=>{
   const diagonal=a.slice(0,n+1).reduce((sum,x,k)=>sum+x*d[n-k],0);
   assert.ok(Math.abs(diagonal-(n===0?1:0))<1e-14);
   assert.ok(Math.abs(number(c.bernoulli[n])-fact(n)*v)<1e-14);
  });
 }
});
test('selected numeric transfer answers agree with independent arithmetic',()=>{
 const number=s=>{const [a,b='1']=String(s).replaceAll('−','-').split('/');return Number(a)/Number(b);};
 const choose=n=>n.choices[n.correctIndex];
 const answer=(id,help=false)=>number(choose(help?passages.find(p=>p.id===id).demonstration.simplerHelp.check:passages.find(p=>p.id===id).demonstration.check));
 const references=[
  ['b47-p1',false,5],['b47-p1',true,3],['b48-p2',true,2+3],['b49-p1',true,2*3],
  ['b51-p1',false,4*3/2],['b51-p1',true,2],['b51-p3',false,2/12],['b51-p3',true,-1/2],
  ['b52-p1',true,1*2],['b52-p2',true,2*2],['b52-p2',false,(3*3+5)/2],['b52-p3',true,(5*5-13)/2],
  ['b53-p1',true,2],['b53-p3',false,7-1-2],['b55-p2',true,0+1/2-(1/2)**2],['b55-p2',false,3/2+3/2-(3/2)**2],['b55-p3',true,1/2],
  ['b56-p1',true,2*(1/2)**2],['b56-p2',false,2**2],['b56-p2',true,2*(1/3)*(2/3)],['b56-p3',true,0],
  ['b58-p1',true,1/(1+1/2)-(1-1/2)],['b58-p3',true,1/2+1/2+1/4],
  ['b59-p2',true,-(2-0)/2],['b59-p3',true,(3*2**2)/12],['b59-p3',false,(2*3)/12],['b60-p1',false,(-1+3/2)/3],['b64-p1',true,1/4+1/4+1/16]
 ];
 for(const [id,help,want] of references)assert.ok(Math.abs(answer(id,help)-want)<1e-14,`${id} ${help?'help':'main'}`);
});
test('certified short tail labels round outward instead of weakening the exact bound',()=>{
 const number=s=>{const [a,b='1']=String(s).split('/');return Number(a)/Number(b);};
 for(const p of passages)for(const s of [...p.demonstration.states,...p.demonstration.simplerHelp.states]){
  if(!s.computed.Rerror || !('K' in s.computed))continue;
  const label=s.diagram.nodes.find(n=>n.id==='tail');
  assert.ok(label);const displayed=Number(label.text.split('≤ ')[1]);
  assert.ok(displayed>=number(s.computed.Rerror),p.id);
 }
});
