import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const source = new URL('../../../content/fullbook/batch-A.json', import.meta.url);
const generator = fileURLToPath(new URL('../../../scripts/fullbook-batch-A.py', import.meta.url));
const lessons = JSON.parse(readFileSync(source, 'utf8'));
const passages = lessons.flatMap(l => l.sections.flatMap(s => s.passages));
const gcd=(a,b)=>b?gcd(b,a%b):a;
const F=n=>{let a=0n,b=1n;for(let k=0;k<n;k++)[a,b]=[b,a+b];return a;};

test('A contains 26 authored units, each with distinct computed passage scenes and private-source-safe prose', () => {
  assert.deepEqual(lessons.map(l=>l.order),Array.from({length:26},(_,i)=>i+21));
  assert.equal(new Set(lessons.map(l=>l.id)).size,26);
  for(const l of lessons){
    assert.match(l.source.pagination,/one-based/);
    assert.ok(l.sections.flatMap(s=>s.passages).length>=3);
    const p=l.sections.flatMap(s=>s.passages);
    assert.equal(new Set(p.map(x=>JSON.stringify(x.demonstration.states))).size,p.length,'do not replay the identical trace beneath different prose');
    for(const x of p) assert.ok(x.text.length>350,`unit ${l.order} needs substantive teaching`);
  }
  assert.doesNotMatch(JSON.stringify(lessons),/sediment:\/\/|\/workspace\/|file:\/\/|knuth-volume1\.pdf/);
});

test('A diagrams, transitions, helper states and assessments meet the explicit-state contract', () => {
  for(const p of passages){
    const d=p.demonstration;
    assert.ok(d.states.length>=2);
    const ids=new Set(d.states.map(s=>s.id));
    for(const t of d.transitions){assert.ok(ids.has(t.from));assert.ok(ids.has(t.to));assert.ok(t.explanation);}
    assert.ok(d.simplerHelp.states.length>=2);
    assert.notStrictEqual(d.simplerHelp.states,d.states);
    assert.ok(d.simplerHelp.connection);
    for(const check of [d.check,d.simplerHelp.check]){
      assert.ok(check.prompt);assert.ok(check.explanation);
      assert.ok(check.correctIndex>=0&&check.correctIndex<check.choices.length);
      assert.equal(new Set(check.choices).size,check.choices.length);
    }
    for(const s of [...d.states,...d.simplerHelp.states]){
      assert.deepEqual(s.diagram.viewBox,[0,0,720,440]);
      assert.ok(s.computed&&Object.keys(s.computed).length);
      assert.equal(new Set(s.diagram.nodes.map(n=>n.id)).size,s.diagram.nodes.length);
      for(const n of s.diagram.nodes){
        assert.ok(['text','rect','circle','line','path'].includes(n.type));
        for(const [key,value] of Object.entries(n)) if(typeof value==='number') assert.ok(Number.isFinite(value),`${key} is finite`);
        if(n.role==='result')assert.equal(n.result,true,'conclusions must be gated during motion');
        if(n.type==='rect'){assert.ok(n.x+n.width<=705);assert.ok(n.y+n.height<=430);}
        if(n.type==='text')assert.ok(n.fontSize>=14&&n.fontSize<=20);
      }
    }
  }
});

test('A independent integer reference confirms rendered Fibonacci gcd and determinant values', () => {
  for(const order of [44,45]){
    const d=lessons.find(l=>l.order===order).sections[0].passages[0].demonstration;
    for(const s of [...d.states,...d.simplerHelp.states]){
      const c=s.computed;
      if(order===44){assert.deepEqual(c.matrix.map(BigInt),[F(c.n+1),F(c.n),F(c.n),F(c.n-1)]);assert.equal(BigInt(c.determinant),c.n%2?-1n:1n);}
      else{assert.equal(BigInt(c.Fa),F(c.a));assert.equal(BigInt(c.Fb),F(c.b));assert.equal(BigInt(c.gcd),gcd(F(c.a),F(c.b)));}
    }
  }
});

test('A Python exact models pass enumerative, boundary, algebraic and geometry tests', () => {
  const run=spawnSync('python',[generator,'--test'],{encoding:'utf8',maxBuffer:8_000_000});
  assert.equal(run.status,0,run.stderr||run.stdout);
  assert.match(run.stdout,/independent assertions passed/);
});

test('A generated content is reproducible from the checked-in deterministic authoring model', () => {
  const run=spawnSync('python',['-c',`import runpy,json; m=runpy.run_path(${JSON.stringify(generator)}); print(json.dumps(m['build'](),ensure_ascii=False))`],{encoding:'utf8',maxBuffer:20_000_000});
  assert.equal(run.status,0,run.stderr);
  assert.deepEqual(JSON.parse(run.stdout),lessons);
});

test('A primary and rescue questions are unique within each unit and computed grid outputs are correctly bound', () => {
  for(const l of lessons){
    const prompts=[];
    for(const p of l.sections.flatMap(s=>s.passages)){
      prompts.push(p.demonstration.check.prompt,p.demonstration.simplerHelp.check.prompt);
      for(const group of [p.demonstration.states,p.demonstration.simplerHelp.states]){
        const last=group.at(-1);
        if(last.computed.kind==='coefficient-grid') for(let i=0;i<last.computed.rows.length;i++)for(let j=0;j<last.computed.rows[i].length;j++){
          const node=last.diagram.nodes.find(n=>n.id===`cell-${i}-${j}-label`);
          assert.equal(node.text,last.computed.rows[i][j]);
        }
      }
    }
    assert.equal(new Set(prompts).size,prompts.length,`unit ${l.order}: all six transfers differ`);
  }
});

test('A formulas parse strictly including multi-line Iverson brackets', async () => {
  const {default:katex}=await import('katex');
  function walk(v){
    if(Array.isArray(v))return v.forEach(walk);
    if(v&&typeof v==='object')for(const [k,x] of Object.entries(v)){
      if(k==='formula'&&typeof x==='string')katex.renderToString(x,{throwOnError:true,strict:'error'});
      else walk(x);
    }
  }
  walk(lessons);
});
