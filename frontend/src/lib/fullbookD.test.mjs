import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import katex from 'katex';
const root=new URL('../../../',import.meta.url);
const lessons=JSON.parse(readFileSync(new URL('content/fullbook/batch-D.json',root),'utf8'));
const passages=lessons.flatMap(l=>l.sections.flatMap(s=>s.passages));
const allStates=passages.flatMap(p=>[...p.demonstration.states,...p.demonstration.simplerHelp.states]);
test('D contains all 18 original lessons, 73 substantive passages, and no private source artifact',()=>{
 assert.deepEqual(lessons.map(l=>l.order),Array.from({length:18},(_,i)=>88+i));
 assert.equal(passages.length,73);
 for(const l of lessons){assert.ok(l.scope.length>70);assert.ok(l.source.section&&l.source.pdfPages);assert.ok(l.sections.flatMap(s=>s.passages).reduce((n,p)=>n+p.text.split(/\s+/).length,0)>=260);}
 for(const p of passages){assert.ok(p.text.length>380, p.id);assert.ok(p.demonstration.states.length>=2);assert.ok(p.demonstration.simplerHelp.states.length>=2);}
 assert.doesNotMatch(JSON.stringify(lessons),/\/workspace\/|file:\/\/|knuth-volume1\.pdf/);
});
test('D strict KaTeX and text control-character audit pass',()=>{
 for(const p of passages){
  const formulas=[p.formula,...p.demonstration.states.map(s=>s.formula),...p.demonstration.simplerHelp.states.map(s=>s.formula)];
  for(const formula of formulas){assert.doesNotMatch(formula,/[\x00-\x1f\x7f]/);assert.doesNotThrow(()=>katex.renderToString(formula,{throwOnError:true,strict:'error'}),p.id+' '+formula);}
 }
});
test('D diagrams have real snapshot evidence, unique stable IDs, and finite in-bounds geometry',()=>{
 for(const st of allStates){assert.deepEqual(st.diagram.viewBox,[0,0,720,440]);assert.ok(st.evidence);assert.ok(st.operation);assert.equal(new Set(st.diagram.nodes.map(n=>n.id)).size,st.diagram.nodes.length);
  for(const n of st.diagram.nodes){
   for(const value of Object.values(n))if(typeof value==='number')assert.ok(Number.isFinite(value));
   if(n.type==='rect'){assert.ok(n.x>=0&&n.y>=0&&n.x+n.width<=720&&n.y+n.height<=440,st.id+'/'+n.id);}
   if(n.type==='circle'){assert.ok(n.x-n.r>=0&&n.x+n.r<=720&&n.y-n.r>=0&&n.y+n.r<=440,st.id+'/'+n.id);}
   if(n.type==='text'){assert.equal(typeof n.text,'string');assert.ok(n.x>=15&&n.x<=705&&n.y>=15&&n.y<=435);}
  }
 }
});
test('D transitions, answer choices and independent help states are well formed',()=>{
 for(const p of passages){const d=p.demonstration;const ids=new Set(d.states.map(s=>s.id));
  for(const t of d.transitions){assert.ok(ids.has(t.from)&&ids.has(t.to));assert.ok(t.explanation.length>20);}
  for(const c of [d.check,d.simplerHelp.check]){assert.ok(c.prompt.length>15);assert.equal(new Set(c.choices).size,c.choices.length);assert.ok(c.correctIndex>=0&&c.correctIndex<c.choices.length);assert.ok(c.explanation.length>=30);}
  assert.ok(d.simplerHelp.model.smallerExample);assert.ok(d.simplerHelp.states.every(s=>!ids.has(s.id)));
 }
});
test('D buffer conservation and orthogonal route identity agree with actual displayed snapshots',()=>{
 for(const l of lessons)for(const p of l.sections.flatMap(s=>s.passages))for(const st of [...p.demonstration.states,...p.demonstration.simplerHelp.states]){const d=st.evidence;
  if(l.order===93){assert.equal(d.tail,(d.head+d.count)%d.cells.length);assert.equal(d.count,d.logical.length);assert.deepEqual(d.logical,Array.from({length:d.count},(_,i)=>d.cells[(d.head+i)%d.cells.length]));}
  if(l.order===95){const slots=[...d.live,...d.reserved,...d.free];assert.deepEqual([...slots].sort((a,b)=>a-b),d.universe);assert.equal(new Set(slots).size,slots.length);}
  if(l.order===104||l.order===105){const a=d.rowLinks.flat().sort(),b=d.columnLinks.flat().sort();assert.deepEqual(a,b);assert.deepEqual(a,d.entries.map(e=>e.id).sort());assert.equal(new Set(a).size,a.length);}
  if(l.order===100&&d.phase==='committed')for(const [v,n] of Object.entries(d.links)){assert.equal(d.links[n.next].prev,v);assert.equal(d.links[n.prev].next,v);}
  if(l.order===102)assert.ok(d.canceled.every(id=>!d.fired.includes(id)));
 }
});
test('D deterministic authoring and exhaustive independent reference models pass',()=>{
 const script=new URL('scripts/fullbook-batch-D.py',root).pathname;
 assert.match(execFileSync('python3',[script,'--check'],{encoding:'utf8'}),/reproducibility passed/);
 const counts=JSON.parse(execFileSync('python3',[script,'--test'],{encoding:'utf8'}));
 assert.equal(counts['four-vertex directed graphs'],4096);assert.equal(counts['exact pivot cases'],600);assert.equal(counts['polynomial pairs'],729);
});
test('D polynomial products are not revealed before their processed contribution, and routed doubly links are directed',()=>{
 for(const l of lessons)for(const p of l.sections.flatMap(s=>s.passages))for(const st of [...p.demonstration.states,...p.demonstration.simplerHelp.states]){
  if(l.order===99&&'pair' in st.evidence){const d=st.evidence;
   for(const [e,c] of d.left)for(const [f,v] of d.right){const node=st.diagram.nodes.find(n=>n.id===`pair-label-${e}-${f}`);assert.ok(node);
    if(d.processed.some(([a,b])=>a===e&&b===f)){assert.equal(node.text,`${c*v}x^${e+f}`);if(d.pair?.[0]===e&&d.pair?.[1]===f)assert.equal(node.result,true);}
    else assert.equal(node.text,'·','unprocessed pair must not leak its product');
   }
  }
  if(l.order===100)for(const n of st.diagram.nodes)if(n.type==='path'&&/^(next|prev)-/.test(n.id)&&!n.id.endsWith('-tip')&&n.opacity!==0)assert.equal(n.arrow,true,'wrap link direction');
 }
});
test('Array scope and sparse-route source convention are explicit',()=>{
 const array=lessons.find(l=>l.order===103),sparse=lessons.find(l=>l.order===104);
 assert.doesNotMatch(array.scope,/arbitrary-dimensional extension explained/);
 assert.match(array.scope,/general-dimensional mixed-radix/);
 const text=sparse.sections.flatMap(s=>s.passages.map(p=>p.text)).join(' ');
 assert.match(text,/source uses circular lists with header nodes and LEFT\/UP links traversing decreasing coordinates/);
 assert.match(text,/instead shows routes in increasing row\/column order/);
});
test('D103 general mixed-radix passage computes 3D prefixes, inversion, and separately smaller help',()=>{
 const lesson=lessons.find(l=>l.order===103),ps=lesson.sections.flatMap(s=>s.passages);assert.equal(ps.length,5);
 const p=ps[4],demo=p.demonstration;assert.equal(demo.model.kind,'general-row-major-mixed-radix');
 assert.match(p.formula,/\\sum_\{t=1\}\^\{d\}/);assert.match(p.text,/empty product/);assert.match(p.text,/half-open/);
 for(const [states,shape,expected] of [[demo.states,[2,2,3],11],[demo.simplerHelp.states,[1,2,2],3]]){
  for(const st of states){const d=st.evidence;assert.deepEqual(d.shape,shape);assert.equal(d.total,shape.reduce((a,b)=>a*b,1));
   for(const cell of d.cells){const k=cell.digits.reduce((acc,digit,t)=>acc*shape[t]+digit,0);assert.equal(cell.offset,k);}
   if(d.stage===3)for(const n of st.diagram.nodes.filter(n=>/^tensor-.*-value$/.test(n.id)&&n.opacity!==0))assert.equal(n.result,true);
  }
  assert.equal(states[3].evidence.accumulator,expected);
  for(const st of states.slice(1,4)){const active=st.diagram.nodes.filter(n=>n.type==='rect'&&/^tensor-/.test(n.id)&&n.role==='active'&&n.opacity!==0);assert.equal(active.length,shape.slice(st.evidence.stage).reduce((a,b)=>a*b,1));}
  const last=states.at(-1).evidence;assert.deepEqual([0,1,2].map(t=>last.recovered[t]+last.lower[t]),last.indices);
 }
 assert.deepEqual(demo.states.slice(1,4).map(s=>s.evidence.accumulator),[1,3,11]);
 assert.deepEqual(demo.simplerHelp.states.slice(1,4).map(s=>s.evidence.accumulator),[0,1,3]);
});
test('D91 frontier task cards and visit cursor move according to computed scheduling state',()=>{
 const l=lessons.find(l=>l.order===91);let moved=false;
 for(const p of l.sections.flatMap(s=>s.passages))for(const states of [p.demonstration.states,p.demonstration.simplerHelp.states]){
  const positions=new Map();
  for(const st of states){const d=st.evidence;
   for(const v of Object.keys(d.adj)){const token=st.diagram.nodes.find(n=>n.id===`task-token-${v}`);assert.ok(token);
    if(d.pending.includes(v)){assert.equal(token.x,165+70*d.pending.indexOf(v));assert.equal(token.y,293);assert.equal(token.opacity,1);}
    else if(d.emitted.includes(v)){assert.equal(token.x,165+70*d.emitted.indexOf(v));assert.equal(token.y,358);assert.equal(token.opacity,1);}
    else assert.equal(token.opacity,0);
    const prior=positions.get(v);if(prior&&token.opacity===1&&prior.opacity===1&&(prior.x!==token.x||prior.y!==token.y))moved=true;positions.set(v,token);
   }
   const cursor=st.diagram.nodes.find(n=>n.id==='visit-cursor');assert.ok(cursor);
   if(d.active){const vertex=st.diagram.nodes.find(n=>n.id===`vertex-${d.active}`);assert.equal(cursor.x,vertex.x);assert.equal(cursor.y,vertex.y);assert.equal(cursor.opacity,1);}else assert.equal(cursor.opacity,0);
  }
 }
 assert.equal(moved,true,'scheduling must move task geometry, not only labels');
});
test('D103 2D bridge derives selected coordinates, counted blocks, offsets, and physical addresses',()=>{
 const l=lessons.find(l=>l.order===103);const d=l.sections[0].passages[0].demonstration;
 for(const [states,selected,k,address] of [[d.states,[3,0],4,116],[d.simplerHelp.states,[3,-1],2,24]]){
  assert.deepEqual(states.map(s=>s.evidence.stage),['select','subtract','rows','within','flatten','address']);
  for(const st of states){const e=st.evidence;assert.deepEqual(e.selected,selected);assert.equal(e.r,selected[0]-e.lo[0]);assert.equal(e.c,selected[1]-e.lo[1]);assert.equal(e.rowContribution,e.r*e.cols);assert.equal(e.rowOffset,e.rowContribution+e.withinContribution);assert.equal(e.rowOffset,k);assert.equal(e.address,address);assert.equal(e.address,e.base+e.stride*e.rowOffset);}
  assert.match(states.at(-1).formula,new RegExp(`=${address}$`));
  const before=states[0].diagram.nodes.find(n=>n.id===`c${selected[0]}-${selected[1]}`),after=states[4].diagram.nodes.find(n=>n.id===before.id);assert.notEqual(before.x,after.x);
 }
});
test('D105 keeps old a,b,c,d and target unchanged until the explicit commit',()=>{
 const l=lessons.find(l=>l.order===105);let cancellations=0,fillins=0;
 for(const p of l.sections.flatMap(s=>s.passages))for(const states of [p.demonstration.states,p.demonstration.simplerHelp.states]){
  for(let k=0;k<states.length;k++){const st=states[k],d=st.evidence;if(!d.operands)continue;
   for(const [name,ij] of Object.entries(d.operandCells))assert.equal(d.operands[name],d.original[ij[0]][ij[1]]);
   if(d.stage==='select'||d.stage==='calculate'){const [i,j]=d.target;assert.equal(d.dense[i][j],d.operands.d,'target must retain old value until commit');}
   if(d.stage==='commit'){const [i,j]=d.target;assert.equal(d.dense[i][j],d.pendingResult);const old=d.operands.d;if(d.pendingResult==='0')cancellations++;if(old==='0'&&d.pendingResult!=='0')fillins++;}
   assert.ok(st.diagram.nodes.some(n=>n.id==='zero-convention'&&n.text.includes('absent sparse cell')));
  }
 }
 assert.ok(cancellations>0&&fillins>0);
 const states=l.sections[1].passages[0].demonstration.states;
 const exact=states.find(s=>s.evidence.stage==='calculate'&&s.evidence.operands.d==='2'&&s.evidence.operands.b==='4');assert.ok(exact);assert.equal(exact.evidence.pendingResult,'0');
 assert.match(exact.diagram.nodes.find(n=>n.id==='actual-substitution').text,/2 − \(4 × 1\) \/ 2 = 0/);
});
