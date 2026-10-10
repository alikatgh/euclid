import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import katex from 'katex';
const root=fileURLToPath(new URL('../../../',import.meta.url));
const lessons=JSON.parse(fs.readFileSync(new URL('../../../content/fullbook/batch-C.json',import.meta.url),'utf8'));
const demos=lessons.flatMap(l=>l.sections.flatMap(s=>s.passages.map(p=>({lesson:l,passage:p,d:p.demonstration}))));
test('Batch C has 23 substantive lessons, 92 operation-focused main/help pairs',()=>{
 assert.deepEqual(lessons.map(l=>l.order),Array.from({length:23},(_,i)=>65+i));
 assert.equal(demos.length,92);
 for(const {lesson,passage,d} of demos){
  assert.ok(passage.text.length>350,`${lesson.order}: substantive explanatory prose`);
  assert.ok(d.states.length>=2); assert.ok(d.simplerHelp.states.length>=2);
  assert.notEqual(d.model.smallerExample,d.simplerHelp.model.smallerExample);
  for(const check of [d.check,d.simplerHelp.check]){assert.ok(check.prompt.length>15);assert.equal(new Set(check.choices).size,check.choices.length);assert.ok(check.correctIndex>=0&&check.correctIndex<check.choices.length);}
  for(const formula of [passage.formula,...d.states.map(s=>s.formula),...d.simplerHelp.states.map(s=>s.formula)])if(formula)assert.doesNotThrow(()=>katex.renderToString(formula,{throwOnError:true,strict:'error'}));
 }
});
test('Every diagram has finite geometry and stable unique object identities',()=>{
 for(const {lesson,d} of demos)for(const states of [d.states,d.simplerHelp.states])for(const s of states){
  assert.equal(new Set(s.diagram.nodes.map(n=>n.id)).size,s.diagram.nodes.length,`${lesson.order}/${s.id}`);
  assert.deepEqual(s.diagram.viewBox,[0,0,720,440]);
  for(const n of s.diagram.nodes){for(const k of ['x','y','x2','y2','width','height','r','fontSize'])if(k in n)assert.ok(Number.isFinite(n[k]),`${lesson.order}/${n.id}/${k}`);if('x' in n)assert.ok(n.x>=0&&n.x<=720);if('y' in n)assert.ok(n.y>=0&&n.y<=440);}
 }
});
test('Actual interpreter, independent oracles and exhaustive finite semantic tests pass',()=>{
 const output=execFileSync('python',[`${root}scripts/fullbook-batch-C.py`,'--test'],{encoding:'utf8'});
 assert.match(output,/28947 independent\/invariant assertions passed/);
});
test('Content exactly regenerates from deterministic model and authored prose',()=>{
 assert.match(execFileSync('python',[`${root}scripts/fullbook-batch-C.py`,'--check'],{encoding:'utf8'}),/Authored 23 lessons/);
});
test('Machine and assembler limits are stated to learners; original program listings are visible',()=>{
 const text=n=>lessons.find(l=>l.order===n).sections.flatMap(s=>s.passages.map(p=>p.text)).join('\n');
 assert.match(text(82),/I\/O opcodes 34–38 are excluded/);assert.match(text(82),/Floating-point/);
 assert.match(text(71),/restricted assembler/);assert.match(text(74),/Save|save/);
 assert.match(text(72),/LOOP \| ADD \| DATA\+4,1/);assert.match(text(77),/RETURN \| JSJ \| 0/);
 assert.match(text(85),/known item count/);assert.match(text(87),/lengths/);
});
test('Every MIX listing line links to its actual executed address or explicit assembly-only data',()=>{
 for(const order of [72,77]){
  const p=lessons.find(l=>l.order===order).sections[0].passages[0],d=p.demonstration;
  assert.equal(p.visualLinks.paragraphs.length,p.text.split(/\n\s*\n/).length);
  for(const link of d.model.sourceVisualLinks){
   const st=d.states[link.frameIndex];
   assert.equal(p.visualLinks.paragraphs[link.sourceLine+1],link.frameIndex);
   if(link.op==='CON'){assert.equal(st.data.assemblyOnly,true);assert.equal(st.data.address,link.address);assert.match(st.caption,/not an executed instruction/);}
   else if(link.address!==null)assert.equal(st.data.fetchedAddress,link.address,`${order}/${link.op}`);
   else assert.equal(link.frameIndex,0);
  }
  assert.equal(d.states[p.visualLinks.takeaway].data.opcode,5);
 }
});
test('Sum prefix invariant and sticky-overflow demonstration are actual computed visible states',()=>{
 const p=lessons.find(l=>l.order===72).sections[0].passages[1];
 for(const states of [p.demonstration.states,p.demonstration.simplerHelp.states])for(const st of states){
  assert.equal(st.data.A.value,st.data.prefix.reduce((a,b)=>a+b,0));
  assert.equal(st.data.k,st.data.prefix.length);
  assert.ok(st.diagram.nodes.some(n=>n.id==='index-equation'&&n.text.includes('I1=')));
 }
 const a=lessons.find(l=>l.order===67).sections[0].passages[0].demonstration.states;
 assert.ok(a.some(st=>st.data.overflow===true&&st.data.A.value===0));
 assert.ok(a.some(st=>st.data.overflow===true&&st.data.A.value===1));
 for(const st of a.slice(1))assert.ok(st.diagram.nodes.some(n=>n.id==='machine-flags'));
});
test('Checks explain their particular rule and help uses independent applied questions',()=>{
 for(const l of lessons){
  const ps=l.sections.flatMap(s=>s.passages),main=ps.map(p=>p.demonstration.check.prompt),help=ps.map(p=>p.demonstration.simplerHelp.check.prompt);
  assert.equal(new Set(main).size,4);assert.equal(new Set(help).size,4);
  assert.ok(help.every(q=>!main.includes(q)));
  for(const p of ps)for(const q of [p.demonstration.check,p.demonstration.simplerHelp.check]){
   assert.doesNotMatch(q.explanation,/The computed model gives/);
   assert.doesNotMatch(q.choices.join(' '),/Only when the animation is paused|A different state|No retained state/);
  }
 }
});

test('Independent portable C/D review oracles cover arithmetic, ownership, queues, graphs and rational pivots',()=>{
 const output=execFileSync('python',[`${root}scripts/fullbook-independent-cd.py`],{encoding:'utf8'});
 const count=Number(output.match(/Independent C\/D review: (\d+) assertions passed/)?.[1]);
 assert.ok(count>=79195,`Independent oracle must execute at least its original assertion coverage; got ${count}`);
});
test('Domain and activation passages visualize their actual proof obligations',()=>{
 const invalid=lessons.find(l=>l.order===73).sections[0].passages[3].demonstration;
 for(const d of [invalid,invalid.simplerHelp]){const last=d.states.at(-1);assert.equal(last.data.rejected,true);assert.equal(last.data.mutated,false);assert.notEqual(last.data.duplicate,last.data.missing);}
 const activation=lessons.find(l=>l.order===78).sections[0].passages[3].demonstration;
 for(const d of [activation,activation.simplerHelp])assert.ok(d.states.some(st=>st.data.expectedReturn!==null&&st.data.expectedReturn!==st.data.static));
});

test('Requested teaching scenes move semantic identities in every main/help sequence',()=>{
 for(const {lesson,d} of demos.filter(({lesson})=>[65,66,70,76,81,84].includes(lesson.order))){
  for(const sequence of [d,d.simplerHelp]){
   const changes=sequence.states.slice(1).flatMap((s,i)=>{
    const before=new Map(sequence.states[i].diagram.nodes.map(n=>[n.id,n]));
    return s.diagram.nodes.filter(n=>before.has(n.id)&&['x','y','width','height','opacity'].some(k=>n[k]!==before.get(n.id)[k]));
   });
   assert.ok(changes.length,`${lesson.order}/${d.id}: stable semantic identity moves`);
   for(let i=1;i<sequence.states.length;i++){const old=new Map(sequence.states[i-1].diagram.nodes.map(n=>[n.id,n]));assert.ok(sequence.states[i].diagram.nodes.some(n=>n.type!=='text'&&old.has(n.id)&&['x','y','width','height','opacity'].some(k=>n[k]!==old.get(n.id)[k])),`${lesson.order}/${d.id}/${i}: geometry moves at each transition`);}
  }
 }
});
test('Selected MIX bytes travel from actual source slots to actual operation destinations',()=>{
 for(const {d} of demos.filter(({lesson})=>lesson.order===66))for(const seq of [d,d.simplerHelp]){
  const [before,after]=seq.states.map(s=>new Map(s.diagram.nodes.map(n=>[n.id,n])));
  const f=seq.model.field,L=Math.floor(f/8),R=f%8,n=R-Math.max(L,1)+1,isload=seq.model.operation==='load';
  for(let p=Math.max(L,1);p<=R;p++){
   const from=isload?p:6-n+p-Math.max(L,1),to=isload?6-n+p-Math.max(L,1):p;
   assert.equal(before.get(`transfer-byte-${p}`).x,208+75*from);
   assert.equal(after.get(`transfer-byte-${p}`).x,208+75*to);
   assert.equal(before.get(`transfer-byte-${p}`).y,isload?78:193);
   assert.equal(after.get(`transfer-byte-${p}`).y,isload?193:78);
   assert.equal(before.get(`transfer-byte-value-${p}`).text,after.get(`transfer-byte-value-${p}`).text);
  }
  assert.equal(after.has('transfer-sign'),L===0);
 }
});
test('Observer log contains exactly the already committed snapshots, in order',()=>{
 for(const {d} of demos.filter(({lesson})=>lesson.order===84))for(const seq of [d,d.simplerHelp])for(const s of seq.states){
  const count=seq.model.trace.findIndex(t=>JSON.stringify(t.after)===JSON.stringify(s.data.traced))+1;
  const entries=s.diagram.nodes.filter(n=>/^log-entry-\d+$/.test(n.id));
  assert.equal(entries.filter(n=>n.opacity===1).length,count);
  for(let j=0;j<entries.length;j++){
   const value=s.diagram.nodes.find(n=>n.id===`log-value-${j}`);
   assert.equal(value.opacity,j<count?1:0);
   assert.equal(value.text,`${j+1}: ${seq.model.trace[j].after.A.value}`);
  }
 }
});
test('Interpreter stack tokens show exactly the committed operand stack',()=>{
 for(const {d} of demos.filter(({lesson})=>lesson.order===81))for(const seq of [d,d.simplerHelp])if(seq.model.focus!==2)for(const s of seq.states){
  const visible=s.diagram.nodes.filter(n=>n.id.startsWith('stack-value-')&&n.opacity===1&&n.y===306).sort((a,b)=>a.x-b.x);
  assert.deepEqual(visible.map(n=>Number(n.text)),s.data.stack);
 }
});
test('Word magnitudes and inclusion-exclusion terms expose their computed construction',()=>{
 for(const {d} of demos.filter(({lesson})=>lesson.order===65))for(const seq of [d,d.simplerHelp])for(const st of seq.states){
  const b=seq.model.base,w=st.data;assert.equal(w.bytes.reduce((sum,v,i)=>sum+v*b**(4-i),0),Math.abs(w.value));
  assert.ok(st.diagram.nodes.find(n=>n.id==='magnitude-expansion').text.endsWith(`= ${Math.abs(w.value)}`));
  assert.equal(st.diagram.nodes.filter(n=>n.id.startsWith('place-weight-')).length,5);
 }
 for(const {d} of demos.filter(({lesson})=>lesson.order===76))for(const seq of [d,d.simplerHelp])if(seq.model.focus!==2)seq.states.forEach((st,k)=>{
  assert.equal(st.diagram.nodes.filter(n=>/^fixed-label-\d+$/.test(n.id)&&n.role==='active').length,k);
  assert.ok(st.diagram.nodes.find(n=>n.id==='fixed-subset-label').text.includes(String(Math.abs(seq.model.terms[k]))));
 });
});
test('MIX execution bridges expose the fetched word, real operands and exact committed calculation',()=>{
 for(const {lesson,d} of demos.filter(({lesson})=>[68,72,77,82].includes(lesson.order)))for(const seq of [d,d.simplerHelp])for(const st of seq.states){
  if(st.data.fetchedAddress===undefined)continue;
  const t=seq.model.executedTrace.find(t=>t.before.pc===st.data.fetchedAddress&&t.after.clock===st.data.clock);
  const get=id=>st.diagram.nodes.find(n=>n.id===id)?.text;
  assert.ok(get('instruction-identity').includes(`@${t.before.pc}:`));
  assert.ok(get('instruction-identity').includes(t.instruction.bytes.join(',')));
  assert.ok(get('instruction-address-equation').endsWith(`= ${t.effectiveAddress}`));
  assert.ok(get('instruction-operands'));assert.ok(get('instruction-equation'));
  const c=t.opcode,f=t.field;
  if(c===1||c===2){
   const w=t.before.memory[String(t.effectiveAddress)],L=Math.floor(f/8),R=f%8;
   const magnitude=w.bytes.slice(Math.max(L,1)-1,R).reduce((a,v)=>a*64+v,0),operand=magnitude*(L===0?w.sign:1);
   assert.ok(get('instruction-operands').includes(`= ${operand}`));
   assert.ok(get('instruction-equation').includes(`${t.before.A.value} ${c===1?'+':'−'} (${operand}) = ${t.after.A.value}`));
  }
  if(c===4&&t.after.undefined)assert.match(get('instruction-equation'),/unspecified/);
  if(c===32)assert.match(get('instruction-equation'),/Patch address .*I, F, C stay unchanged/);
  assert.equal(st.diagram.nodes.find(n=>n.id==='instruction-equation').result,true);
 }
});
test('C approved visual and learner-prose baseline preserves models, source, state IDs, assessments and source links',async()=>{
 // Approved 2026-10-10: symbol readings and concrete smaller-example prose added; models/results independently unchanged.
 const {createHash}=await import('node:crypto');
 const preserved=JSON.stringify(lessons,(k,v)=>k==='diagram'?undefined:v);
 assert.equal(createHash('sha256').update(preserved).digest('hex'),'b7dc3ba2031cad3218a7e6dca27791a39e09073c9ce3cad34c2a63e8c3f82649');
});

test('C learner readings bind symbols and smaller inputs without animator boilerplate',()=>{
 const p=(n,i)=>lessons.find(l=>l.order===n).sections[0].passages[i];
 assert.match(p(68,0).text,/PC is the program counter/);
 assert.match(p(69,3).text,/f_i counts how often it executes/);
 assert.match(p(81,0).text,/σ is its stack sequence/);
 assert.match(p(84,0).text,/keep only the guest machine fields/);
 for(const [n,i] of [[65,0],[66,0],[68,0],[69,3],[81,0],[84,0],[85,0],[86,0],[87,2]]){
  const d=p(n,i).demonstration;
  assert.ok(d.states[0].teachingExplanation);
  assert.ok(d.simplerHelp.states[0].teachingExplanation);
 }
 const field=p(66,0).demonstration.simplerHelp;
 assert.equal(field.model.field,45);assert.match(field.intro,/5:5.*F=45/);
 assert.match(field.states[0].teachingExplanation,/selects only the last byte/);
 const schedule=p(85,0).demonstration.simplerHelp;
 assert.equal(schedule.model.schedule.at(-1).issued,2);
 assert.equal(schedule.model.schedule.at(-1).time,8);
 assert.match(schedule.states[0].teachingExplanation,/n=2.*I=2.*C=3/);
 const packed=p(87,2).demonstration.simplerHelp;
 assert.deepEqual(packed.model.records,['AB','C']);assert.equal(packed.model.capacity,2);
 assert.match(packed.states[0].teachingExplanation,/N=3.*B=2/);
 for(const l of lessons)for(const x of l.sections[0].passages){
  const h=x.demonstration.simplerHelp;
  assert.doesNotMatch(h.intro,/Set aside the large example/);
  assert.equal(h.steps.length,h.states.length,'Every helper frame has its own explanation, never the last-frame caption early');
  h.states.forEach((state,i)=>assert.equal(h.steps[i].text,state.teachingExplanation||state.caption));
  assert.doesNotMatch(h.connection,/selected field, control point, or owned object/);
  assert.notEqual(h.steps.at(-1).text,x.title+'. '+x.text.split('\n\n')[0]);
 }
});
