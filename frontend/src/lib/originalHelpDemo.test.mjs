import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as jsx from 'react/jsx-runtime';
import { renderToStaticMarkup } from 'react-dom/server';
const source=fs.readFileSync(new URL('../components/OriginalHelpDemo.tsx',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2023}}).outputText;
const sandbox={exports:{},require:name=>name==='react/jsx-runtime'?jsx:{bindNumbersMotion:()=>{}}};
vm.runInNewContext(compiled,sandbox);
const {OriginalHelpDemo}=sandbox.exports;
const entries=JSON.parse(fs.readFileSync(new URL('../../../content/first20/original-help.json',import.meta.url),'utf8'));
const render=(entry,index)=>{const frame=entry.helpExample.frames[index];return renderToStaticMarkup(jsx.jsx(OriginalHelpDemo,{exampleId:entry.helpExample.id,frameIndex:index,frame,visual:{...frame,kind:entry.helpExample.kind,model:entry.demonstration},paused:true}));};
const moves=html=>[...html.matchAll(/data-move="([^"]+)" data-x="([^"]+)" data-y="([^"]+)" data-o="([^"]+)"/g)].map(m=>({id:m[1],x:+m[2],y:+m[3],opacity:+m[4]}));
test('all 61 original-lesson help states render with valid, unique motion objects',()=>{
 let count=0;
 for(const entry of entries)for(let i=0;i<entry.helpExample.frames.length;i++){
  const html=render(entry,i);assert.ok(html.includes('viewBox="0 0 640 400"'));
  assert.ok(!/NaN|Infinity|\[object Object\]/.test(html),`${entry.helpExample.id}/${i}`);
  const objects=moves(html);assert.equal(new Set(objects.map(o=>o.id)).size,objects.length);
  for(const object of objects)for(const value of [object.x,object.y,object.opacity])assert.ok(Number.isFinite(value));
  count++;
 }
 assert.equal(entries.length,12);assert.equal(count,61);
});
test('all moving helper scenes change authored coordinates; fixed-point scenes deliberately stay fixed',()=>{
 for(const entry of entries){
  const positions=entry.helpExample.frames.map((_,i)=>JSON.stringify(moves(render(entry,i))));
  if(entry.helpExample.kind==='fixed-loop'){
   assert.equal(positions[0],positions[1],'Applying a→a must not invent movement in the fixed state');
   assert.ok(render(entry,4).includes('In Ω: finished'));
  }else assert.ok(new Set(positions).size>1,entry.helpExample.id);
 }
});
test('parcel and letter identities move to the exact authored successor locations',()=>{
 const parcel=entries.find(e=>e.helpExample.kind==='parcel-machine');
 assert.equal(moves(render(parcel,1)).find(o=>o.id==='parcel').x,170);
 assert.equal(moves(render(parcel,2)).find(o=>o.id==='parcel').x,470);
 assert.deepEqual(moves(render(parcel,3)),moves(render(parcel,4)),'The fixed output must not acquire a changing machine coordinate');
 const letters=entries.find(e=>e.helpExample.kind==='letter-rewrite');
 assert.equal(moves(render(letters,0)).find(o=>o.id==='a1').x,176);
 assert.equal(moves(render(letters,1)).find(o=>o.id==='a1').x,272);
 assert.equal(moves(render(letters,1)).find(o=>o.id==='b1').x,176);
});
