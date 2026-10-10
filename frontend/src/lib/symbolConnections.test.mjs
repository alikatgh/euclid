import test from 'node:test';
import assert from 'node:assert/strict';
import {splitMathSymbols,resolveSymbol} from './symbolConnections.js';
const node=(attrs,text='')=>({attrs, textContent:text, parentElement:{textContent:text},getAttribute(key){return this.attrs[key]??null},hasAttribute(key){return key in this.attrs},closest(){return null}});
const context={scope:'finite:main',frame:{visual:{model:{kind:'indexed-accumulation'},state:{objects:[{id:'term-1',role:'collected',value:2,data:{index:1}},{id:'term-2',role:'collected',value:5,data:{index:2}},{id:'term-3',role:'collected',value:1,data:{index:3}}]}}}};
test('mathematical a is distinguished from an English article',()=>{const tokens=splitMathSymbols('An arithmetic progression starts at a and adds a fixed difference d each time.').filter(p=>p.token);assert.deepEqual(tokens.map(t=>t.token),['a','d']);assert.equal(splitMathSymbols('Take a (small) example.').filter(p=>p.token).length,0);});
test('plain and Unicode indexed terms remain whole while operator names remain prose',()=>{assert.deepEqual(splitMathSymbols('a_j, a₁, S₄; log and gcd',true).filter(p=>p.token).map(p=>p.token),['a_j','a1','S4']);assert.equal(splitMathSymbols('log sin gcd max').filter(p=>p.token).length,0);});
test('uppercase SVG node A is an identity, not an English article',()=>assert.equal(splitMathSymbols('A: 7',true)[0].token,'A'));
test('both forms of sigma select the same operation',()=>{for(const token of ['Σ','∑'])assert.deepEqual(resolveSymbol(node({'data-math-token':token}),context).keys,['finite:main|operation:sum']);});
test('unknown equal numbers get an explicitly lexical fallback',()=>{const a=resolveSymbol(node({'data-math-token':'7'}),{scope:'x'},'one');const b=resolveSymbol(node({'data-math-token':'7'}),{scope:'x'},'two');assert.deepEqual(a.keys,b.keys);assert.match(a.description,/displayed values/);assert.match(a.description,/different mathematical roles/);});
test('collected summands keep their value identities',()=>{const result=resolveSymbol(node({'data-math-token':'5','data-math-expression':'2+5+1=8','data-math-offset':'2'}),context);assert.deepEqual(result.keys,['finite:main|term:value:1']);});
test('index 2 is separate from summand value 2',()=>{const index=resolveSymbol(node({'data-math-token':'2','data-math-expression':'index 2','data-math-offset':'6'}),context);const value=resolveSymbol(node({'data-math-token':'2','data-math-expression':'2+5+1=8','data-math-offset':'0'}),context);assert.deepEqual(index.keys,['finite:main|index:old:1']);assert.deepEqual(value.keys,['finite:main|term:value:0']);});
test('summation upper bound is not treated as a square exponent',()=>{const result=resolveSymbol(node({'data-math-token':'3','data-math-bound':'upper','data-math-index-symbol':'j','data-math-script':'exponent'}),context);assert.equal(result.role,'upper summation bound');assert.deepEqual(result.keys,['finite:main|index:old:2']);});
test('old numerical multi-memberships remain available to original lessons',()=>{const result=resolveSymbol(node({'data-math-values':'119 544'}));assert.deepEqual(result.keys,['original|legacy:value:119','original|legacy:value:544']);});
test('wrong sums and index questions do not borrow a summand value identity',()=>{
 for(const expression of ['not 1+2+3 = 6','When j=2, which value is selected?']){
  const position=expression.indexOf('2');const result=resolveSymbol(node({'data-math-token':'2','data-math-expression':expression,'data-math-offset':String(position)}),context);
  assert.ok(!result.keys.includes('finite:main|term:value:0'));
 }
 const result=resolveSymbol(node({'data-math-token':'2','data-math-expression':'j=2','data-math-offset':'2'}),context);
 assert.deepEqual(result.keys,['finite:main|index:old:1']);
});
test('the two geometric sums select their own original and scaled rows',()=>{
 const geometric={scope:'geometric:main',frame:{visual:{order:20,model:{kind:'geometric-shift'},state:{computed:{termCount:4}}}}};
 const first=resolveSymbol(node({'data-math-token':'∑','data-math-sum-start':'0'}),geometric);
 const second=resolveSymbol(node({'data-math-token':'∑','data-math-sum-start':'1'}),geometric);
 assert.deepEqual(first.keys,['geometric:main|operation:sum']);assert.deepEqual(second.keys,['geometric:main|geometric:scaled']);
 const compound=resolveSymbol(node({'data-math-token':'S4'}),geometric);assert.deepEqual(compound.keys,['geometric:main|symbol:S']);
});
test('initial input controls remain original inputs after a register swap',()=>{
 const input=node({'data-math-value':'119'});input.id='col3-m-input';const result=resolveSymbol(input,{originalStep:{initialM:119,initialN:544,m:544,n:119,q:4,r:68}});
 assert.deepEqual(result.keys,['original|initial:m']);assert.match(result.description,/Original input m = 119/);
});
test('original two-dimensional geometry belongs to both current length roles',()=>{
 const result=resolveSymbol(node({'data-math-values':'544 119'}),{originalStep:{initialM:119,initialN:544,m:544,n:119,q:4,r:68}});
 assert.deepEqual(result.keys,['original|quantity:m:544','original|quantity:n:119']);
});
test('Unicode script letters and bracketed random variables are mathematical tokens',()=>{
 assert.deepEqual(splitMathSymbols('rⁿ zʲ E[A]').filter(t=>t.token).map(t=>t.token),['r','n','z','j','E','A']);
 const tokens=splitMathSymbols('Sₙ=Σₖ₌₁ⁿaₖ').filter(t=>t.token);
 assert.ok(tokens.some(t=>t.token==='k'&&t.script==='subscript'));assert.ok(tokens.some(t=>t.token==='n'&&t.script==='exponent'));assert.ok(tokens.some(t=>t.token==='1'&&t.script==='subscript'));
});

test('a separate q=4 example is not the current quotient q=1',()=>{
 const step={m:5,n:4,q:1,r:1,initialM:5,initialN:4};
 for(const token of ['q','4']){const result=resolveSymbol(node({'data-math-token':token,'data-math-expression':'q=4','data-math-assignment':token==='4'?'q':''}),{originalStep:step});assert.deepEqual(result.keys,[token==='q'?'original|symbol:q':'original|reference:q:4']);assert.match(result.description,/q = 4 in this written example/);}
});
test('lexical fallback reaches written SVG numerals without collapsing authored role selections',()=>{
 const scope={scope:'example',frame:{visual:{order:21,state:{diagram:{nodes:[]}}}}};
 const reading=resolveSymbol(node({'data-math-token':'7','data-math-expression':'Seven, written 7'}),scope);
 const diagram=node({'data-diagram-node':'parcel-0-label'},'7');
 const visual=node({'data-math-token':'7','data-math-expression':'7'});visual.closest=selector=>selector==='[data-diagram-node]'?diagram:null;
 const label=resolveSymbol(visual,scope);assert.ok(label.matchKeys.includes(reading.keys[0]));
 const position=resolveSymbol(node({'data-math-token':'2','data-math-keys':'position:2','data-math-role':'position'}),scope);
 const value=resolveSymbol(node({'data-math-token':'2','data-math-keys':'value:2','data-math-role':'value'}),scope);
 assert.ok(position.matchKeys.includes('example|written:number:2'));assert.ok(value.matchKeys.includes('example|written:number:2'));
 assert.ok(!position.keys.some(k=>value.matchKeys.includes(k)),'Selecting an authored position must not select an equal-valued payload');
});
