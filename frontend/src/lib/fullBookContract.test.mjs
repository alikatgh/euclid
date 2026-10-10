import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import katex from 'katex';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const dir=resolve(root,'content/fullbook');
const files=existsSync(dir)?readdirSync(dir).filter(f=>/^batch-[A-F]\.json$/.test(f)).sort():[];
const lessons=files.flatMap(f=>{const v=JSON.parse(readFileSync(resolve(dir,f),'utf8'));return Array.isArray(v)?v:v.lessons;});
function question(q,where){assert.ok(q?.prompt?.trim(),where+' prompt');assert.ok(q.explanation?.length>=15,where+' reasoning');assert.ok(q.choices?.length>=2,where+' choices');assert.ok(Number.isInteger(q.correctIndex)&&q.correctIndex>=0&&q.correctIndex<q.choices.length,where+' correct answer');assert.equal(new Set(q.choices).size,q.choices.length,where+' unique options');}
function diagram(state,where){
 const d=state.diagram;assert.ok(d?.nodes?.length,where+' computed diagram');assert.ok(state.caption?.length,where+' caption');
 const ids=new Set();for(const n of d.nodes){assert.ok(n.id&&!ids.has(n.id),where+' stable unique node '+n.id);ids.add(n.id);assert.ok(['rect','circle','line','path','text'].includes(n.type),where+' primitive');
 for(const k of ['x','y','x2','y2','width','height','r','fontSize','opacity','strokeWidth'])if(n[k]!==undefined)assert.ok(Number.isFinite(n[k]),where+' finite '+k);
 for(const k of ['width','height','r'])if(n[k]!==undefined)assert.ok(n[k]>=0,where+' nonnegative '+k);
 if(n.type==='text')assert.equal(typeof n.text,'string',where+' accessible label');
 }
 if(state.formula)assert.doesNotThrow(()=>katex.renderToString(state.formula,{throwOnError:true,strict:'error'}),where+' formula');
}
test('full-book batches have complete authored main/help contracts and valid notation',()=>{
 const orders=new Set(),ids=new Set(),demoIds=new Set();for(const l of lessons){
 assert.ok(l.order>=21&&l.order<=144&&!orders.has(l.order),'unique order '+l.order);orders.add(l.order);
 assert.ok(l.id&&!ids.has(l.id),'unique id '+l.id);ids.add(l.id);assert.ok(l.title&&l.source?.section&&l.source?.pdfPages,'source locator '+l.id);
 assert.ok(l.sections?.length>=1,'substantive sections '+l.id);let passages=0;
 for(const section of l.sections){assert.ok(section.title&&section.passages?.length,'section '+l.id);
 for(const p of section.passages){passages++;const where=l.id+'/'+p.id;assert.ok(p.title&&p.text?.length>=60,where+' original teaching prose');
 if(p.formula)assert.doesNotThrow(()=>katex.renderToString(p.formula,{throwOnError:true,strict:'error'}),where+' notation');
 const d=p.demonstration;assert.ok(d?.id&&!demoIds.has(d.id),where+' globally unique demonstration id');demoIds.add(d.id);assert.ok(d?.model?.kind&&d.states?.length>=2,where+' computed trace');
 const stateIds=new Set();for(const s of d.states){assert.ok(s.id&&!stateIds.has(s.id),where+' state identity');stateIds.add(s.id);diagram(s,where+'/'+s.id);}
 for(const t of d.transitions??[]){assert.ok(stateIds.has(t.from)&&stateIds.has(t.to),where+' transition endpoints');assert.ok(t.action&&t.explanation,where+' causal transition');}
 if(p.visualLinks){for(const v of [p.visualLinks.definition,p.visualLinks.takeaway,...(p.visualLinks.paragraphs??[])])if(v!==undefined&&v!==null)assert.ok(typeof v==='string'?stateIds.has(v):Number.isInteger(v)&&v>=0&&v<d.states.length,where+' explicit source/frame link');}
 question(d.check,where);const h=d.simplerHelp;assert.ok(h?.intro&&h.connection&&h.states?.length>=2,where+' own smaller model');
 for(const s of h.states)diagram(s,where+'/help/'+s.id);question(h.check,where+'/help');
 }
 }assert.ok(passages>=3,'multiple arguments '+l.id);
 }
});
test('full-book final delivery covers every planned lesson 21–144',{skip:process.env.FULLBOOK_COMPLETE!=='1'},()=>{
 assert.equal(files.length,6);assert.deepEqual(lessons.map(l=>l.order).sort((a,b)=>a-b),Array.from({length:124},(_,i)=>i+21));
});

test('every passage has distinct on-topic assessment prompts rather than cloned or rotated checks',()=>{
 const norm=s=>s.toLowerCase().replace(/^smaller[- ]example transfer[: ]*/,'').replace(/\s+/g,' ').trim();
 for(const l of lessons){const ps=l.sections.flatMap(s=>s.passages);const main=ps.map(p=>norm(p.demonstration.check.prompt)),help=ps.map(p=>norm(p.demonstration.simplerHelp.check.prompt));
 assert.equal(new Set(main).size,main.length,l.id+' main assessments must target distinct passages');
 assert.equal(new Set(help).size,help.length,l.id+' helper assessments must target distinct small-example claims');
 for(const prompt of help)assert.ok(!main.includes(prompt),l.id+' helper may not rotate a main question from another passage');
 }
});
