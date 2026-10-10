import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import katex from 'katex';
const lessons=['A','B'].flatMap(b=>JSON.parse(readFileSync(new URL(`../../../content/fullbook/batch-${b}.json`,import.meta.url))));
const target=new Set([26,42,43,45,53,59]);
const demos=lessons.filter(l=>target.has(l.order)).flatMap(l=>l.sections.flatMap(s=>s.passages.map(p=>({order:l.order,...p.demonstration}))));
const sets=d=>[d.states,d.simplerHelp.states];
const node=(s,id)=>s.diagram.nodes.find(n=>n.id===id);
test('all six causal-animation units move or reveal actual geometry on EVERY main/help transition',()=>{
 for(const d of demos) for(const ss of sets(d)) for(let i=1;i<ss.length;i++){
  const prev=new Map(ss[i-1].diagram.nodes.map(n=>[n.id,n]));
  assert.ok(ss[i].diagram.nodes.some(n=>n.type!=='text'&&prev.has(n.id)&&['x','y','x2','y2','height','width','opacity','d'].some(k=>n[k]!==prev.get(n.id)[k])),`${d.id}: ${ss[i-1].id} -> ${ss[i].id}`);
 }
});
test('harmonic accumulation exposes exactly the included reciprocal rectangles',()=>{
 const d=demos.find(d=>d.id==='a-42-0');
 for(const ss of sets(d)) for(const s of ss) for(const n of s.diagram.nodes.filter(n=>/^bar\d+$/.test(n.id))){
  const k=Number(n.id.slice(3));assert.equal(n.height,k<=s.computed.n?200/k:0);assert.equal(n.y,315-n.height);
 }
});
test('harmonic regrouping transports each (i,j) tile to its transposed grouping without changing its value',()=>{
 const d=demos.find(d=>d.id==='a-43-0');
 for(const ss of sets(d)) for(const n of ss[0].diagram.nodes.filter(n=>/^cell-\d+-\d+$/.test(n.id))){
  const [,i,j]=n.id.split('-').map(Number);const end=node(ss.at(-1),n.id);assert.equal(end.x-n.x,100*(i-j));assert.equal(end.y-n.y,53*(j-i));assert.equal(node(ss[0],n.id+'-label').text,node(ss.at(-1),n.id+'-label').text);
 }
});
test('Iverson overlap has precisely one removable duplicate per intersection member',()=>{
 const d=demos.find(d=>d.id==='a-26-0');
 for(const ss of sets(d)){
  assert.equal(ss[1].diagram.nodes.filter(n=>/^overlap-copy\d+$/.test(n.id)&&n.opacity===1).length,ss[1].computed.intersection);
  for(const n of ss[1].diagram.nodes.filter(n=>/^overlap-copy\d+$/.test(n.id)))assert.equal(node(ss[2],n.id).opacity,0);
 }
});
test('Euclidean length partition is the index remainder, not the numerical Fibonacci remainder',()=>{
 const d=demos.find(d=>d.id==='a-45-0');
 for(const ss of sets(d))for(const s of ss){const {a,b}=s.computed;const u=360/ss[0].computed.a;assert.equal(node(s,'index-length').width,a*u);assert.equal(node(s,'index-remainder').width,(b?a%b:a)*u);}
});
test('right-to-left scan cursor and tokens are actual comparisons, preserving rightmost ties',()=>{
 for(const d of demos.filter(d=>d.order===53))for(const ss of sets(d))for(const s of ss){const c=s.computed;const arrow=node(s,'comparison-cursor');assert.equal(arrow.x,80+Math.max(0,c.k)*90);assert.equal(arrow.opacity,c.k>=0?1:0);assert.equal(s.diagram.nodes.filter(n=>/^comparison-token/.test(n.id)&&n.opacity===1).length,c.comparisons);assert.equal(node(s,'retained-maximum').x,80+c.j*90-35);assert.equal(node(s,'maximum').role,'result');}
});
const fraction=x=>{const [a,b='1']=String(x).split('/');return Number(a)/Number(b)};
test('Euler correction pieces have proportional signed areas and assemble at the exact net height',()=>{
 for(const d of demos.filter(d=>d.order===59))for(const ss of sets(d))for(const s of ss){const c=s.computed;const scale=180/fraction(c.integral);assert.ok(Math.abs(node(s,'integral-piece').height-fraction(c.approx)*scale)<1e-10);assert.ok(Math.abs(node(s,'endpoint-piece').height+fraction(c.endpoint)*scale)<1e-10);assert.ok(Math.abs(node(s,'derivative-piece').height-fraction(c.correction)*scale)<1e-10);assert.equal(node(s,'eq').role,'result');}
});
test('all affected authored formulas pass strict KaTeX',()=>{for(const l of lessons.filter(l=>target.has(l.order)))for(const section of l.sections)for(const p of section.passages){for(const f of [p.formula,...sets(p.demonstration).flat().map(s=>s.formula)])if(f)katex.renderToString(f,{throwOnError:true,strict:'error'});}});
test('reciprocal-product pairing visibly assembles exact half-square plus half-diagonal contributions',()=>{
 const d=demos.find(d=>d.id==='a-43-1');
 for(const ss of sets(d)){
  const middle=ss[1];const shown=middle.diagram.nodes.filter(n=>n.type==='text'&&n.id.endsWith('-label')&&n.opacity!==0);
  const sum=shown.reduce((a,n)=>a+fraction(n.text),0);assert.ok(Math.abs(sum-fraction(middle.computed.triangle))<1e-12);
  for(const n of middle.diagram.nodes.filter(n=>/^ij\d+-\d+$/.test(n.id)))assert.equal(n.width,48);
 }
});
test('A25 selected column exposes its lower bound and final formula really swaps the sums',()=>{
 const d=lessons.find(l=>l.order===25).sections[0].passages[0].demonstration;
 for(const ss of sets(d)){
  const n=ss[0].computed.n,j=ss[0].computed.fixedIndex;
  assert.deepEqual(ss[2].computed.selectedPairs,Array.from({length:n-j+1},(_,k)=>[j+k,j]));
  if(n===5)assert.deepEqual(ss[2].computed.selectedPairs.map(([i,j])=>i+j),[6,7,8]);
  assert.match(ss[3].formula,/\\sum_\{j=1\}.*\\sum_\{i=j\}/);
  const ids=ss[0].diagram.nodes.filter(n=>/^cell-\d+-\d+$/.test(n.id)).map(n=>n.id);
  for(const s of ss)assert.deepEqual(s.diagram.nodes.filter(n=>/^cell-\d+-\d+$/.test(n.id)).map(n=>n.id),ids);
 }
});
test('A31 depicts signed floor-division blocks and nonnegative remainders, independently of A32 permutation',()=>{
 const l=lessons.find(l=>l.order===31),d=l.sections[0].passages[0].demonstration;
 assert.deepEqual(d.states[2].computed,{a:-8,d:5,q:-2,r:2,stage:2,example:0,blockEndpoint:-10,classMembers:[-8,-3,2]});
 for(const ss of sets(d))for(const s of ss){const c=s.computed;assert.equal(c.q,Math.floor(c.a/c.d));assert.equal(c.a,c.q*c.d+c.r);assert.ok(c.r>=0&&c.r<c.d);assert.equal(node(s,'remainder-arrow').x2-node(s,'remainder-arrow').x,c.stage>=2?c.r*40:0);assert.ok(!s.diagram.nodes.some(n=>/^to\d+$/.test(n.id)));katex.renderToString(s.formula,{throwOnError:true,strict:'error'});}
 assert.deepEqual([...new Set(d.simplerHelp.states.map(s=>s.computed.a))],[7,-5]);
 const p32=lessons.find(l=>l.order===32).sections[0].passages[0].demonstration;assert.equal(p32.states[0].computed.multiplier,3);assert.equal(p32.states[0].computed.modulus,7);
});
const mainDemo=order=>lessons.find(l=>l.order===order).sections[0].passages[0].demonstration;
test('33 expands actual unused-badge branches and multiplies all-prefix counts',()=>{
 for(const ss of sets(mainDemo(33)))for(const s of ss){const c=s.computed;assert.equal(c.count,c.branchFactors.reduce((a,b)=>a*b,1));assert.equal(new Set(c.expandedPrefix).size,c.expandedPrefix.length);assert.ok(c.nextChoices.every(x=>!c.expandedPrefix.includes(x)));}
 assert.equal(mainDemo(33).states.at(-1).computed.count,60);
});
test('37 quotients equal ordering fibers and disjointly classifies subsets by the marked member',()=>{
 for(const ss of sets(mainDemo(37)))for(const s of ss){const c=s.computed;assert.equal(c.ordered.length,c.subsets.length*2);const names=c.subsets.map(x=>x.join(''));assert.equal(new Set(names).size,names.length);assert.ok(c.excluded.every(x=>!x.includes(c.marked)));assert.ok(c.included.every(x=>x.includes(c.marked)));assert.equal(c.excluded.length+c.included.length,c.subsets.length);}
});
test('40 actual subset Cartesian products account for each union exactly once',()=>{
 for(const ss of sets(mainDemo(40)))for(const s of ss){const c=s.computed;assert.equal(c.AChoices.length*c.BChoices.length,c.terms[c.k]);const unions=c.caseSets.flat();assert.equal(unions.length,c.total);assert.equal(new Set(unions).size,c.total);assert.ok(unions.every(x=>x.length===c.n));}
 const c=mainDemo(40).states.find(s=>s.computed.k===1).computed;assert.equal(c.AChoices.length,3);assert.equal(c.BChoices.length,6);assert.equal(c.terms[1],18);
});
test('41 exposes adjacent subtraction, extracts Newton coefficients, then divides by factorial',()=>{
 const d=mainDemo(41);assert.ok(d.states.some(s=>s.caption.includes('8 − 1 = 7')));assert.ok(d.states.some(s=>s.caption.includes('19 − 7 = 12')));
 assert.deepEqual(d.states.at(-1).computed.newton,[0,1,6,6]);assert.deepEqual(d.states.at(-1).computed.fallingCoefficients,['0','1','3','1']);
 for(const ss of sets(d))for(const s of ss){const c=s.computed;for(let r=1;r<c.rows.length;r++)for(let j=0;j<c.rows[r].length;j++)assert.equal(c.rows[r][j],c.rows[r-1][j+1]-c.rows[r-1][j]);}
});
test('43 counts visible reciprocal-column multiplicities before adding contributions',()=>{
 for(const ss of sets(mainDemo(43)))for(const s of ss){const c=s.computed;for(let j=1;j<=c.n;j++){assert.equal(c.cells.filter(x=>x[1]===j).length,c.multiplicities[j-1]);assert.equal(fraction(c.contributions[j-1]),(c.n-j+1)/j);}}
});
test('46 shifts preserve a concrete Fibonacci coefficient before aligned-degree subtraction',()=>{
 for(const ss of sets(mainDemo(46))){const bridge=ss.filter(s=>s.computed.kind==='coefficient-shift-bridge');assert.equal(bridge.length,4);const c=bridge[0].computed;assert.deepEqual(c.targetDegrees,[c.sourceDegree,c.sourceDegree+1,c.sourceDegree+2]);assert.equal(c.operands[0]-c.operands[1]-c.operands[2],0);for(let row=0;row<3;row++)assert.equal(node(bridge[0],'shifted-F3-'+row+'-label').text,String(c.coefficient));}
 assert.notEqual(mainDemo(46).states[0].computed.sourceDegree,mainDemo(46).simplerHelp.states[0].computed.sourceDegree);
});
test('54 success is suffix maximum at its left edge, before probability ratio',()=>{
 for(const d of lessons.find(l=>l.order===54).sections[0].passages.slice(0,2).map(p=>p.demonstration))for(const ss of sets(d))for(const s of ss){const c=s.computed;let count=0;for(const w of c.witnesses){assert.equal(w.maximum,Math.max(...w.permutation.slice(w.left)));assert.equal(w.hit,w.permutation[w.left]===w.maximum);count+=Number(w.hit);}assert.equal(count,c.hits);assert.equal(c.hits*c.suffix,c.total);assert.equal(node(s,'prob').opacity,c.phase?1:0);}
});
test('57 fixes constants before probing n and proves numeric upper/lower gaps',()=>{
 for(const p of lessons.find(l=>l.order===57).sections[0].passages)for(const ss of sets(p.demonstration))for(const s of ss){const c=s.computed;assert.equal(c.c,c.a);assert.equal(c.C,c.a+c.b);assert.equal(c.n0,1);assert.ok(c.lower<=c.actual&&c.actual<=c.upper);assert.equal(c.upper-c.actual,c.b*(c.n-1));assert.equal(c.actual-c.lower,c.b);assert.ok(!s.diagram.nodes.some(n=>n.text?.includes('gap is b')));}
});
test('59 derives corrections from endpoint values and slopes before assembling',()=>{
 for(const p of lessons.find(l=>l.order===59).sections[0].passages)for(const ss of sets(p.demonstration))for(const s of ss){const c=s.computed;assert.equal(-(c.endpointValues[1]-c.endpointValues[0])/2,fraction(c.endpoint));assert.equal((c.endpointSlopes[1]-c.endpointSlopes[0])/12,fraction(c.correction));}
 const ss=mainDemo(59).states;assert.deepEqual(ss[1].computed.endpointValues,[0,16]);assert.deepEqual(ss[3].computed.endpointSlopes,[0,8]);assert.equal(ss[1].computed.approx,'64/3');assert.equal(ss[3].computed.approx,'40/3');
});
test('62 exact coordinate map distinguishes finite-n log values from approximation',()=>{
 for(const p of lessons.find(l=>l.order===62).sections[0].passages.slice(0,2))for(const ss of sets(p.demonstration))for(const s of ss){const c=s.computed;assert.deepEqual(c.mapping.map(x=>x.s),[-1,0,1]);for(const m of c.mapping){assert.ok(Math.abs((m.t-c.n)/c.width-m.s)<1e-12);assert.ok(Math.abs(m.quadratic+m.s*m.s/2)<1e-12);assert.ok(Math.abs(m.exactLog-(c.n*Math.log(m.t/c.n)-m.t+c.n))<1e-12);}if(c.stage===4)assert.match(s.caption,/approximation, not an exact identity/);}
});
