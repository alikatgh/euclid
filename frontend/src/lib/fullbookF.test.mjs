import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import katex from 'katex';
const source=new URL('../../../content/fullbook/batch-F.json',import.meta.url);
const lessons=JSON.parse(readFileSync(source,'utf8'));
const allPassages=lessons.flatMap(l=>l.sections.flatMap(s=>s.passages));

test('F: all 22 units have distinct substantive focus, runnable scene data and independent smaller help',()=>{
 assert.deepEqual(lessons.map(l=>l.order),Array.from({length:22},(_,i)=>123+i));
 assert.equal(allPassages.length,88);
 for(const l of lessons){
  assert.ok(l.source.pdfPages&&l.source.pagination.includes('one-based'));
  const ps=l.sections.flatMap(s=>s.passages);
  assert.equal(new Set(ps.map(p=>p.demonstration.check.prompt)).size,4);
  for(const p of ps){
   assert.ok(p.text.length>300);const d=p.demonstration;
   assert.ok(d.model.semanticFamily===l.id);
   assert.ok(d.states.length&&d.simplerHelp.states.length);
   assert.notDeepEqual(d.states,d.simplerHelp.states);
   for(const c of [d.check,d.simplerHelp.check]){assert.ok(c.explanation.length>=30);assert.ok(c.correctIndex>=0&&c.correctIndex<c.choices.length);}
   for(const s of [...d.states,...d.simplerHelp.states]){
    assert.deepEqual(s.diagram.viewBox,[0,0,720,440]);
    assert.equal(new Set(s.diagram.nodes.map(n=>n.id)).size,s.diagram.nodes.length);
    assert.doesNotThrow(()=>katex.renderToString(s.formula,{throwOnError:true}));
    for(const n of s.diagram.nodes){for(const k of ['x','y','x2','y2','width','height','r']) if(k in n)assert.ok(Number.isFinite(n[k]));}
   }
   assert.doesNotThrow(()=>katex.renderToString(p.formula,{throwOnError:true}));
   for(const t of d.transitions){assert.ok(d.states.some(s=>s.id===t.from));assert.ok(d.states.some(s=>s.id===t.to));}
  }
 }
});

test('F: exact Python algorithms exhaustively check tree, graph and allocator invariants',()=>{
 const path=fileURLToPath(new URL('../../../scripts/fullbook-batch-F.py',import.meta.url));
 const report=JSON.parse(execFileSync('python',[path,'--test'],{encoding:'utf8'}));
 assert.equal(report.three_node_graphs_times_roots_restoration,12288);
 assert.equal(report.binary_shapes_exhaustive_n0_to_8,2056);
 assert.equal(report.boundary_neighbor_cases,4);
 assert.equal(report.authored_passages,88);
});

test('F: independent edge-subset tree enumeration verifies unlabeled rooted/free counts',()=>{
 // This oracle enumerates graph edge subsets, not Prüfer words or product recurrences.
 const rootedCounts=[0,1,1,2,4,9],freeCounts=[0,1,1,1,2,3];
 for(let n=2;n<=5;n++){
  const pairs=[];for(let a=0;a<n;a++)for(let b=a+1;b<n;b++)pairs.push([a,b]);
  const rooted=new Set(),free=new Set();
  const canonical=(g,v,parent=-1)=>'('+g[v].filter(u=>u!==parent).map(u=>canonical(g,u,v)).sort().join('')+')';
  for(let mask=0;mask<2**pairs.length;mask++){
   if(mask.toString(2).replaceAll('0','').length!==n-1)continue;
   const g=Array.from({length:n},()=>[]);
   pairs.forEach(([a,b],i)=>{if(mask&(1<<i)){g[a].push(b);g[b].push(a);}});
   const seen=new Set([0]),stack=[0];while(stack.length){for(const u of g[stack.pop()])if(!seen.has(u)){seen.add(u);stack.push(u);}}
   if(seen.size!==n)continue;
   const codes=g.map((_,v)=>canonical(g,v));codes.forEach(c=>rooted.add(c));free.add(codes.sort()[0]);
  }
  assert.equal(rooted.size,rootedCounts[n]);assert.equal(free.size,freeCounts[n]);
 }
});

test('F: independent full-binary shape enumeration verifies path sums and Huffman example optimum',()=>{
 const trees=n=>n===0?[null]:Array.from({length:n},(_,i)=>trees(i).flatMap(l=>trees(n-1-i).map(r=>[l,r]))).flat();
 const sums=(t,d=0)=>{if(t===null)return {i:0,e:d,n:0};const a=sums(t[0],d+1),b=sums(t[1],d+1);return {i:d+a.i+b.i,e:a.e+b.e,n:1+a.n+b.n};};
 for(let n=0;n<=6;n++)for(const t of trees(n)){const s=sums(t);assert.equal(s.e,s.i+2*n);}
 const permutations=a=>a.length===0?[[]]:a.flatMap((x,i)=>permutations(a.filter((_,j)=>i!==j)).map(p=>[x,...p]));
 const leafDepths=(t,d=0)=>t===null?[d]:[...leafDepths(t[0],d+1),...leafDepths(t[1],d+1)];
 const weights=[3,4,8,10];let optimum=Infinity;
 for(const t of trees(3))for(const ws of permutations(weights)){const depths=leafDepths(t);optimum=Math.min(optimum,ws.reduce((a,w,i)=>a+w*depths[i],0));}
 assert.equal(optimum,47);
 const worked=lessons.find(l=>l.order===129).sections[0].passages[2].demonstration;
 assert.ok(worked.states.at(-1).diagram.nodes.some(n=>n.text?.includes('total cost 47')));
});

test('F: scene endpoints bind to exact byte accounting and declare source-specific limitations',()=>{
 const allocation=lessons.find(l=>l.order===137).sections[0].passages[2].demonstration;
 assert.ok(allocation.states.some(s=>s.diagram.nodes.some(n=>n.text==='capacity 64 = reserved 36 + free 28')));
 const pointer=lessons.find(l=>l.order===133).sections[0].passages[2].demonstration;
 assert.ok(pointer.states.at(-1).caption.includes('restored'));
 assert.ok(lessons.find(l=>l.order===132).sections[0].passages[1].text.includes('not a literal implementation'));
 assert.ok(lessons.find(l=>l.order===126).sections[0].passages[0].text.includes('n−1'));
 assert.ok(lessons.find(l=>l.order===123).sections[0].passages[1].text.includes('proves the theorem'));
});


test('F: independent mixed-atom reachability and byte-cell allocation oracles',()=>{
 const path=fileURLToPath(new URL('../../../scripts/fullbook-batch-F.py',import.meta.url));
 const python="import runpy,itertools,random,copy,sys\nm=runpy.run_path(sys.argv[1])\nassert m['rooted_counts'](10)==[0,1,1,2,4,9,20,48,115,286,719]\nassert m['free_counts'](10)==[0,1,1,1,2,3,6,11,23,47,106]\n# Independent worklist ignores all outgoing fields at original atomic nodes.\ncount=0\nfor targets in itertools.product([None,'0','1'],repeat=4):\n for bits in itertools.product([0,1],repeat=2):\n  g={str(i):dict(a=targets[2*i],b=targets[2*i+1],atom=bits[i]) for i in range(2)}\n  for root in g:\n   seen=set();todo=[root]\n   while todo:\n    x=todo.pop()\n    if x is None or x in seen:continue\n    seen.add(x)\n    if not g[x]['atom']:todo += [g[x]['a'],g[x]['b']]\n   original=copy.deepcopy(g);actual,frames=m['reverse_mark'](g,root)\n   assert actual==seen and g==original and frames[-1]['graph']==g\n   count+=1\nrng=random.Random(1047)\nfor _ in range(3000):\n g={str(i):dict(a=rng.choice([None,'0','1','2']),b=rng.choice([None,'0','1','2']),atom=rng.randrange(2)) for i in range(3)}\n root=rng.choice(list(g));seen=set();todo=[root]\n while todo:\n  x=todo.pop()\n  if x is None or x in seen:continue\n  seen.add(x)\n  if not g[x]['atom']:todo += [g[x]['a'],g[x]['b']]\n actual,frames=m['reverse_mark'](g,root);assert actual==seen and frames[-1]['graph']==g\n count+=1\n# Address-cell oracle: free runs and occupied labels are independent of block metadata.\nalloccases=0\nfor cls in ['Heap','TaggedHeap']:\n for policy in ['first','best']:\n  for seed in range(25):\n   rng=random.Random(seed);h=m[cls](128);cells=[None]*128;live={};serial=0\n   for _ in range(100):\n    if live and rng.random()<.45:\n     name=rng.choice(list(live));h.free(name)\n     cells=[None if x==name else x for x in cells];del live[name]\n    else:\n     name='n'+str(serial);serial+=1;request=rng.randrange(1,41)\n     need=max(h.minimum,((request+h.o+3)//4)*4)\n     runs=[];i=0\n     while i<128:\n      if cells[i] is not None:i+=1;continue\n      j=i\n      while j<128 and cells[j] is None:j+=1\n      if j-i>=need:runs.append((i,j-i))\n      i=j\n     chosen=(min(runs,key=lambda z:(z[1],z[0])) if policy=='best' else runs[0]) if runs else None\n     old=copy.deepcopy(h.blocks);ok=h.alloc(name,request,policy)\n     assert ok==bool(chosen)\n     if chosen:\n      start,size=chosen;reserved=need if size-need>=h.minimum else size\n      cells[start:start+reserved]=[name]*reserved;live[name]=(start,reserved)\n     else:assert h.blocks==old\n    actual=[]\n    for b in h.blocks:actual += [b['id']]*b['size']\n    assert actual==cells\n    if cls=='TaggedHeap':m['validate_tags'](h)\n    alloccases+=1\n# Matching rejects group/group equality as an output, but emits asymmetric elementary/group pair.\nassert m['corresponding']({'G':{'A':{}}},{'G':{'A':{}}})==[('G','A')]\nassert m['corresponding']({'G':{}},{'G':{'A':{}}})==[('G',)]\nassert m['corresponding']({'G':{'A':{}}},{'G':{}})==[('G',)]\nprint({'mixed_atom_restoration_cases':count,'independent_cell_allocator_steps':alloccases,'canonical_counts_n10':'verified','asymmetric_correspondence':'verified'})\n";
 const result=execFileSync('python',['-c',python,path],{encoding:'utf8'});
 assert.ok(result.includes("'mixed_atom_restoration_cases': 3648"));
 assert.ok(result.includes("'independent_cell_allocator_steps': 10000"));
});

test('F: passage-specific help and source-sensitive correspondence/tag mechanics remain explicit',()=>{
 for(const l of lessons){
  const ps=l.sections.flatMap(s=>s.passages),main=new Set(ps.map(p=>p.demonstration.check.prompt));
  const helper=ps.map(p=>p.demonstration.simplerHelp.check.prompt);
  assert.equal(new Set(helper).size,ps.length);
  for(const q of helper){assert.ok(!main.has(q));assert.ok(!q.startsWith('Smaller-example transfer:'));}
 }
 const match=lessons.find(l=>l.order===136).sections[0].passages[1];
 assert.ok(match.formula.includes('elem'));
 assert.ok(match.demonstration.states.some(s=>s.caption.includes('Both current items are groups')));
 assert.ok(match.demonstration.states.at(-1).caption.includes('right item is a group'));
 const unlink=lessons.find(l=>l.order===139).sections[0].passages[2].demonstration.states;
 assert.equal(unlink.length,4);
 assert.ok(unlink[1].caption.includes('Unlink free neighbor at 0'));
 assert.ok(unlink[2].caption.includes('Unlink free neighbor at 32'));
 assert.ok(unlink[3].diagram.nodes.some(n=>n.text==='free-list head: 0'));
 const reclaimed=lessons.find(l=>l.order===130).sections[0].passages[2].demonstration.states.at(-1);
 for(const n of reclaimed.diagram.nodes.filter(n=>/^e[A-D]-/.test(n.id)))assert.equal(n.opacity,0,'retired references must not remain visually stored');
 const collision=lessons.find(l=>l.order===135).sections[0].passages[3].demonstration.states;
 assert.ok(collision.at(-1).diagram.nodes.some(n=>n.text?.includes('2 matches, still ambiguous')));
});

test('F: bounded marking, qualification and slot inventories move stable semantic objects in every main/help passage',()=>{
 const fields=['x','y','x2','y2','width','height','r','opacity'];
 for(const order of [132,135,142]){
  for(const p of lessons.find(l=>l.order===order).sections[0].passages){
   for(const [mode,states] of [['main',p.demonstration.states],['help',p.demonstration.simplerHelp.states]]){
    let moved=false;
    const ids=states[0].diagram.nodes.filter(n=>/^(work-|rescan-|qualifier-|inventory-token-|slot-search-)/.test(n.id)).map(n=>n.id);
    assert.ok(ids.length,`${order} ${mode}: authored motion objects`);
    for(const s of states)for(const id of ids)assert.ok(s.diagram.nodes.some(n=>n.id===id),`${id}: stable identity`);
    for(let i=1;i<states.length;i++){
     const previous=new Map(states[i-1].diagram.nodes.map(n=>[n.id,n]));
     for(const n of states[i].diagram.nodes){const before=previous.get(n.id);if(ids.includes(n.id)&&before&&n.type!=='text'&&fields.some(k=>n[k]!==before[k]))moved=true;}
    }
    assert.ok(moved,`${order} ${p.id} ${mode}: geometric movement, not text/color-only changes`);
    for(const s of states)for(const n of s.diagram.nodes.filter(n=>/^(work-status|qualifier-status-)/.test(n.id))){assert.equal(n.result,true);assert.equal(n.phase,'result');}
   }
  }
 }
});

test('F: completed-work markers and qualifier cursor endpoints follow the computed objects',()=>{
 const worked=order=>lessons.find(l=>l.order===order).sections[0].passages[2].demonstration;
 const marking=worked(132);
 for(const [states,expected] of [[marking.states,['A','B','D','C']],[marking.simplerHelp.states,['A','B']]]){
  states.forEach((s,i)=>{const nodes=new Map(s.diagram.nodes.map(n=>[n.id,n])),vertex=nodes.get('v'+expected[i]);assert.equal(nodes.get('work-cursor').x,vertex.x+38);assert.equal(nodes.get('work-cursor').y,vertex.y);});
 }
 const recovered=marking.states.at(-1).diagram.nodes;
 assert.equal(recovered.find(n=>n.id==='rescan-cursor').opacity,1);
 assert.ok(recovered.find(n=>n.id==='work-status').text.includes('recovered by rescan'));
 const qualification=worked(135);
 assert.deepEqual(qualification.states.map(s=>s.diagram.nodes.find(n=>n.id==='qualifier-cursor-x').y),[325,135,55]);
 assert.deepEqual(qualification.simplerHelp.states.map(s=>s.diagram.nodes.find(n=>n.id==='qualifier-cursor-x').y),[325,55]);
 assert.ok(qualification.simplerHelp.states.at(-1).diagram.nodes.find(n=>n.id==='qualifier-status-x').text.includes('exhausted'));
});

test('F: availability membership moves without moving physical slots or allocating on failure',()=>{
 const d=lessons.find(l=>l.order===142).sections[0].passages[2].demonstration;
 for(const states of [d.states,d.simplerHelp.states]){
  const initial=states[0].diagram.nodes.filter(n=>/^slot\d+$/.test(n.id));
  for(const s of states)for(const slot of initial){const current=s.diagram.nodes.find(n=>n.id===slot.id);assert.deepEqual([current.x,current.y,current.width,current.height],[slot.x,slot.y,slot.width,slot.height]);}
  const tokens=s=>s.diagram.nodes.filter(n=>/^inventory-token-\d+$/.test(n.id)).map(n=>[n.id,n.x,n.y]);
  assert.notDeepEqual(tokens(states[0]),tokens(states[1]));
  assert.deepEqual(tokens(states.at(-2)),tokens(states.at(-1)),'failed request preserves inventory membership');
  assert.ok(states.at(-1).diagram.nodes.find(n=>n.id==='request').text.includes('FAIL'));
 }
});

test('F: qualifier pointers remain local and never cross an ancestor record at authored endpoints',()=>{
 const lesson=lessons.find(l=>l.order===135);
 for(const p of lesson.sections[0].passages)for(const states of [p.demonstration.states,p.demonstration.simplerHelp.states])for(const s of states){
  const vertices=s.diagram.nodes.filter(n=>n.type==='circle'&&n.id.startsWith('v'));
  for(const route of s.diagram.nodes.filter(n=>n.id.startsWith('qualifier-route-'))){
   const cursor=s.diagram.nodes.find(n=>n.id===route.id.replace('route','cursor'));
   assert.equal(route.y,cursor.y+12);assert.equal(route.y2,route.y);assert.equal(route.x,cursor.x);
   assert.ok(route.x-route.x2>0&&route.x-route.x2<50,'short local pointer, no leaf-to-ancestor chord');
   for(const v of vertices){const x=Math.max(route.x2,Math.min(route.x,v.x));assert.ok(Math.hypot(v.x-x,v.y-route.y)>v.r,'pointer stays outside record circles and their center text');}
  }
 }
});
test('F causal bridges enumerate subtree choices, conserve split bytes and derive weighted depths',()=>{
 const states=lessons.flatMap(l=>l.sections.flatMap(s=>s.passages.flatMap(p=>[...p.demonstration.states,...p.demonstration.simplerHelp.states])));
 const proofs=states.filter(s=>s.id.includes('-derive-'));
 const nodeCount=t=>t===null?0:1+nodeCount(t[0])+nodeCount(t[1]);
 for(const s of proofs){const c=s.computed;
  if('leftShapes' in c){assert.equal(c.leftShapes.length,c.leftCount);assert.equal(c.rightShapes.length,c.rightCount);c.leftShapes.forEach(t=>assert.equal(nodeCount(t),c.leftSize));c.rightShapes.forEach(t=>assert.equal(nodeCount(t),c.rightSize));assert.equal(new Set(c.rightShapes.map(JSON.stringify)).size,c.rightCount);}
  if('depth' in c){assert.deepEqual(c.after.map((v,i)=>v-c.before[i]),[c.depth,c.depth+2,1]);}
  if('leaves' in c){assert.ok(c.leaves.every(l=>l.newDepth-l.oldDepth===1));assert.equal(c.leaves.reduce((a,l)=>a+l.weight,0),c.increment);assert.equal(c.priorCost+c.increment,c.afterCost);}
  if('blocks' in c){assert.ok(c.rounded>=c.request&&c.rounded/2<c.request);assert.equal(c.blocks.reduce((n,b)=>n+b.size,0),c.capacity);let end=0;for(const b of c.blocks){assert.equal(b.start,end);assert.equal(b.start%b.size,0);end+=b.size;}assert.equal(end,c.capacity);}
 }
 assert.ok(proofs.some(s=>s.computed.rightCount===5));
 const full=lessons.find(l=>l.order===140).sections[0].passages[0].demonstration.states;
 assert.deepEqual(full.filter(s=>s.computed).map(s=>s.computed.blocks.map(b=>b.size)),[[64],[32,32],[16,16,32]]);
 assert.equal(full.at(-1).diagram.nodes.find(n=>n.id==='block0label').text,'A');
});
test('F approved bridge and learner-prose baseline preserves models, source, state IDs and assessments',async()=>{
 const {createHash}=await import('node:crypto');
 // Approved 2026-10-10: contextual notation and smaller-example readings intentionally change prose only.
 const clean=x=>Array.isArray(x)?x.filter(y=>!(typeof y?.id==='string'&&y.id.includes('-derive-'))).map(clean):x&&typeof x==='object'?Object.fromEntries(Object.entries(x).filter(([k])=>!['diagram','transitions','steps'].includes(k)).map(([k,v])=>[k,clean(v)])):x;
 assert.equal(createHash('sha256').update(JSON.stringify(clean(lessons))).digest('hex'),'89368e2a4c12564d29d5b20be37238f7fc11d36dbedaa966ba99a73421b70aaa');
});

test('F first-use notation has concrete smaller-example readings',()=>{
 const p=(n,i)=>lessons.find(l=>l.order===n).sections[0].passages[i];
 assert.match(p(125,0).text,/coefficient of z\^n counts rooted shapes/);
 assert.match(p(125,3).text,/1 when n is even and 0 otherwise/);
 assert.match(p(131,0).text,/R denotes the objects reachable/);
 assert.match(p(135,0).text,/A_0=DAY and A_1=ARRIVAL/);
 assert.match(p(143,1).text,/MAX=2\^w−1/);
 const arena=p(137,0).demonstration.simplerHelp;
 assert.match(arena.states[0].teachingExplanation,/C=32.*r=5.*8 bytes/);
 assert.equal(arena.steps[0].text,arena.states[0].teachingExplanation);
 const buddies=p(140,0).demonstration.simplerHelp;
 assert.match(buddies.intro,/2\^4=16 bytes/);
 for(const l of lessons)for(const x of l.sections[0].passages){
  const h=x.demonstration.simplerHelp;
  assert.doesNotMatch(h.intro,/Use fewer objects and keep one obligation/);
  assert.doesNotMatch(h.connection,/same invariant:.*separate computed input/);
 }
});

test('F134 absent-qualifier result has a separate explanation lane',()=>{
 const d=lessons.find(l=>l.order===134).sections[0].passages[3].demonstration;
 for(const states of [d.states,d.simplerHelp.states]){
  const nodes=states.at(-1).diagram.nodes;
  const status=nodes.find(n=>n.id==='qualifier-status-x');
  const explanation=nodes.find(n=>n.id==='boundary-verified');
  const footer=nodes.find(n=>n.id==='footer');
  assert.ok(explanation.y-status.y>=20);
  assert.ok(footer.y-explanation.y>=20);
 }
});
