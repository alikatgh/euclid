import { fullBookSymbolBinding } from './fullBookSymbolBindings.js';
import { originalSymbolBinding } from './originalSymbolBindings.js';
import { earlyBookSymbolBinding } from './earlyBookSymbolBindings.js';
/** Semantic extension of the recovered data-math-linked contract.
 * A displayed value is never an entity ID. Unknown numbers remain occurrence-local.
 * Optional authored data-math-keys and data-math-role take precedence over inference.
 */
export const SYMBOL_SELECTOR = '[data-math-token], [data-math-value], [data-math-values], [data-math-keys]';
const operators = { 'Σ':'sum','∑':'sum','Π':'product','∏':'product','+':'addition','−':'subtraction','-':'subtraction','×':'multiplication','·':'multiplication','÷':'division','/':'division','=':'equality','≠':'inequality','<':'less than','>':'greater than','≤':'at most','≥':'at least','∈':'membership','∉':'non-membership','→':'mapping','←':'assignment','⇒':'implication','⇔':'equivalence','√':'square root','∞':'infinity','∀':'for every','∃':'there exists','∅':'empty set','∫':'integral','∂':'partial derivative','∇':'gradient','≡':'congruence or defined identity','≈':'approximate equality','∝':'proportional to','∼':'asymptotic equivalence','⊂':'proper subset','⊆':'subset','⊃':'proper superset','⊇':'superset','∪':'set union','∩':'set intersection','∧':'logical and','∨':'logical or','¬':'logical not','⊕':'exclusive or','⊗':'tensor product','±':'plus or minus','⌊':'floor: greatest integer at most the value','⌋':'floor: greatest integer at most the value','⌈':'ceiling: least integer at least the value','⌉':'ceiling: least integer at least the value','!':'factorial','|':'divisibility, absolute value or conditioning in context','^':'power','₌':'index equality' };
const sup = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9','ⁱ':'i','ʲ':'j','ᵏ':'k','ⁿ':'n'};
const sub = {'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9','ᵢ':'i','ⱼ':'j','ₙ':'n','ₖ':'k'};
export function splitMathSymbols(text, math=false) {
 const out=[];const re=/[A-Za-z](?:_[A-Za-z0-9]+|[₀₁₂₃₄₅₆₇₈₉ᵢⱼₙₖ]+)|(?<![\p{L}\p{N}_])\d+(?:\.\d+)?(?![\p{L}\p{N}_])|[⁰¹²³⁴⁵⁶⁷⁸⁹]+|[ⁱʲᵏⁿ]|[₀₁₂₃₄₅₆₇₈₉]+|[ᵢⱼₙₖ]|[Σ∑Π∏+−×·÷=≠<>≤≥∈∉→←⇒⇔√∞∀∃∅∫∂∇≡≈∝∼⊂⊆⊃⊇∪∩∧∨¬⊕⊗±⌊⌋⌈⌉!|^₌\/]|(?<![\p{L}])[A-Za-zα-ωΑ-Ω](?=[ⁱʲᵏⁿ]|[^\p{L}]|$)/gu;
 let end=0;for(const m of String(text).matchAll(re)) {
  const token=m[0],letter=/^[\p{L}]$/u.test(token)&&!operators[token];
  if(letter&&!math&&/^[aAI]$/.test(token)&&!(/^(?:[²³^_+−×=<>≤≥]|\s*[=<>≤≥])/.test(text.slice(m.index+1))||(/[[{(]\s*$/.test(text.slice(0,m.index))&&/^\s*[\]},)]/.test(text.slice(m.index+1)))||/\b(?:at|contains|symbol|variable|quantity|value|node|vertex|root|object|register)\s*$/.test(text.slice(0,m.index))))continue;
  if(m.index>end)out.push({text:text.slice(end,m.index)});
  out.push({text:token,token:[...token].map(c=>sup[c]??sub[c]??c).join(''),kind:operators[token]?'operator':letter||/^[A-Za-z][₀-₉ᵢⱼₙₖ_]/.test(token)?'symbol':'number',script:sup[token[0]]?'exponent':sub[token[0]]?'subscript':undefined,offset:m.index});end=m.index+token.length;
 }if(end<text.length)out.push({text:text.slice(end)});return out;
}
/** Render through React, never split a React-owned Text node behind its back. */
export function symbolTextChildren(value, jsx, svg=false) {
 if(typeof document==='undefined')return value;
 if(Array.isArray(value))value=value.every(v=>typeof v==='string'||typeof v==='number')?value.join(''):value;
 if(value&&typeof value==='object'&&!Array.isArray(value)&&['span','tspan'].includes(value.type)&&!value.props?.['data-math-value'])return jsx.jsx(value.type,{...value.props,children:symbolTextChildren(value.props.children,jsx,svg)},value.key);
 if(typeof value!=='string'&&typeof value!=='number')return value;
 const text=String(value);return splitMathSymbols(text,svg&&/^[A-Za-z](?::\s*[+−-]?\d+(?:\.\d+)?)?$/.test(text.trim())).map((part,i)=>part.token===undefined?part.text:jsx.jsx(svg?'tspan':'span',{
  'data-math-token':part.token,'data-math-kind':part.kind,'data-math-script':part.script,'data-math-expression':text,'data-math-offset':part.offset,
  'data-math-value':part.kind==='number'&&!part.script?part.token:undefined,children:part.text,
 },i));
}
/** Only generated KaTeX markup is inspected; no user HTML is accepted. */
export function annotateSymbolMath(html, tex) {
 if(typeof document==='undefined')return html;
 const template=document.createElement('template');template.innerHTML=html;
 const rendered=template.content.querySelector('.katex-html');if(!rendered)return html;
 const semantics=new Map();
 const mathml=template.content.querySelector('math');
 for(const atom of mathml?.querySelectorAll('mi,mn,mo')??[]) {
  const token=atom.textContent.trim();let script, bound, indexSymbol, base, term, assignment, sumStart, scaledSum, shiftAddend;
  for(let child=atom,parent=atom.parentElement;parent&&parent!==mathml;child=parent,parent=parent.parentElement){
   const tag=parent.tagName.toLowerCase(),children=[...parent.children],at=children.indexOf(child);
   if(['msub','msup','msubsup','munder','mover','munderover'].includes(tag)&&at>0){
    base=children[0]?.textContent;const lower=tag==='msub'||tag==='munder'||((tag==='msubsup'||tag==='munderover')&&at===1);script=lower?'subscript':'exponent';
    if(/[∑Σ∏Π]/.test(children[0]?.textContent??'')){bound=lower?'lower':'upper';indexSymbol=children[1]?.querySelector('mi')?.textContent;}
    break;
   }
  }
  if(atom.parentElement?.tagName.toLowerCase()==='msub'&&atom.parentElement.firstElementChild===atom)term=token+'_'+atom.parentElement.lastElementChild.textContent;
  if(/[∑Σ]/.test(token))sumStart=atom.parentElement?.children[1]?.textContent?.match(/=([0-9]+)/)?.[1];if(term?.startsWith('S_'))scaledSum=atom.parentElement?.previousElementSibling?.textContent==='r';
  const previous=atom.previousElementSibling, beforePrevious=previous?.previousElementSibling,next=atom.nextElementSibling;if(/^\d+(?:\.\d+)?$/.test(token)&&/^[+−-]$/.test(previous?.textContent??'')&&/^[jk]$/.test(beforePrevious?.textContent??''))shiftAddend=true;if(/^\d+(?:\.\d+)?$/.test(token)&&previous?.textContent==='='&&/^[A-Za-zα-ω]$/.test(beforePrevious?.textContent??'')&&(!next||/^[,;:]$/.test(next.textContent??'')))assignment=beforePrevious.textContent;
  if(!semantics.has(token))semantics.set(token,[]);semantics.get(token).push({script,bound,indexSymbol,base,term,assignment,sumStart,scaledSum,shiftAddend});
 }
 const euclidEquation=/^(?:\\htmlClass|[0-9])/.test(tex)&&/\\(?:times|cdot)/.test(tex)&&tex.includes('=')&&tex.includes('+');
 let numericIndex=0;let index=0;
 for(const leaf of [...rendered.querySelectorAll('span')]) {
  if(leaf.children.length||!leaf.textContent?.trim())continue;
  const text=leaf.textContent.trim();if(!/^(?:\d+(?:\.\d+)?|[\p{L}]|[Σ∑Π∏+−×·÷=≠<>≤≥∈∉→←⇒⇔√∞∀∃∅∫∂∇≡≈∝∼⊂⊆⊃⊇∪∩∧∨¬⊕⊗±⌊⌋⌈⌉!|^₌\/])$/u.test(text))continue;
  const token=leaf.getAttribute('data-math-value')||text;
  leaf.setAttribute('data-math-token',token);leaf.setAttribute('data-math-kind',operators[text]?'operator':/^\d/.test(token)?'number':'symbol');
  leaf.setAttribute('data-math-expression',tex);if(euclidEquation&&/^\d/.test(token)){const roles=['m','q','n','r'];if(numericIndex<4)leaf.setAttribute('data-math-original-role',roles[numericIndex++]);}leaf.setAttribute('data-math-offset',String(index++));
  const candidates=semantics.get(text)??semantics.get(token)??[];
  const inScript=Boolean(leaf.closest('.msupsub'));
  const scriptBase=leaf.closest('.msupsub')?.previousElementSibling?.textContent;let semantic=candidates.find(candidate=>!candidate.used&&Boolean(candidate.script)===inScript&&(!inScript||!scriptBase||candidate.base===scriptBase))??candidates.find(candidate=>!candidate.used&&Boolean(candidate.script)===inScript)??candidates[0];
  if(inScript&&candidates.some(c=>c.script==='subscript')&&candidates.some(c=>c.script==='exponent')) {
   const positioned=leaf.closest('[style*="top:"]');const siblings=[...(positioned?.parentElement?.children??[])].filter(el=>el.style?.top);
   if(siblings.length>1){const lowest=Math.max(...siblings.map(el=>parseFloat(el.style.top)));semantic=candidates.find(c=>!c.used&&c.script===(parseFloat(positioned.style.top)===lowest?'subscript':'exponent'))??semantic;}
  }
  if(semantic)semantic.used=true;if(semantic?.term)leaf.setAttribute('data-math-term',semantic.term);
  if(semantic?.sumStart!==undefined)leaf.setAttribute('data-math-sum-start',semantic.sumStart);if(semantic?.scaledSum)leaf.setAttribute('data-math-scaled-sum','true');
  if(semantic?.shiftAddend)leaf.setAttribute('data-math-shift-addend','true');
  if(semantic?.assignment)leaf.setAttribute('data-math-assignment',semantic.assignment);
  if(semantic?.script)leaf.setAttribute('data-math-script',semantic.script);
  if(semantic?.bound){leaf.setAttribute('data-math-bound',semantic.bound);if(semantic.indexSymbol)leaf.setAttribute('data-math-index-symbol',semantic.indexSymbol);}

 }
 return template.innerHTML;
}
const clean = value=>String(value??'').replace(/\\(?:left|right|,|;|!|quad|qquad)/g,'').replace(/\\(?:mathrm|text|operatorname)\{([^{}]*)\}/g,'$1').replace(/\\sum/g,'Σ').replace(/[∑]/g,'Σ').replace(/\\(?:leq?|geq?|times|cdot)/g,m=>m.includes('le')?'≤':m.includes('ge')?'≥':'×').replace(/\\([A-Za-z]+)/g,'$1').replace(/[{}\s]/g,'');
const attrKeys=el=>(el?.getAttribute('data-math-keys')||'').split(/\s+/).filter(Boolean);
const numberName = text=>/^-?\d+(?:\.\d+)?$/.test(text);
function contextInfo(context) {
 const visual=context?.frame?.visual??context?.visual??{};
 return {visual,state:visual.state??{},kind:visual.model?.kind??'',scope:context?.scope??'original',help:Boolean(visual.helpMode)};
}
/** Conservative fallback plus authored bindings for the first summation lessons. */
export function resolveSymbol(element, context={}, occurrence='unknown') {
 const info=contextInfo(context),{state,kind,help}=info;
 const external=originalSymbolBinding(element,context)||fullBookSymbolBinding(element,context)||earlyBookSymbolBinding(element,context);
 if(external){const written=element.getAttribute('data-math-token')??element.getAttribute('data-math-value');const lexical=written&&numberName(written)?[`written:number:${written}`]:[];const scope=keys=>[...new Set(keys)].map(k=>`${info.scope}|${k}`);return {...external,localKeys:external.keys,token:element.getAttribute('data-math-token')||element.textContent?.trim()||'',keys:scope(external.keys),matchKeys:scope([...external.keys,...(external.memberships??[]),...lexical])};}

 const explicit=element.hasAttribute('data-math-keys')?element:element.closest('text[data-math-keys]');const authored=attrKeys(explicit);
 const token=element.getAttribute('data-math-token')??element.getAttribute('data-math-value')??element.textContent?.trim()??'';
 const expression=element.getAttribute('data-math-expression')??element.closest('[data-math-expression]')?.getAttribute('data-math-expression')??element.parentElement?.textContent??token;
 const script=element.getAttribute('data-math-script');const declared=element.getAttribute('data-math-role')??explicit?.getAttribute('data-math-role');
 const isNumber=numberName(token);let keys=[],role='',description='';const indexKind=/^(?:indexed-accumulation|formula-summands|empty-sum|reindex-square-cards|reindex-reverse)$/.test(kind);
 const symbol=operators[token];
 if(authored.length) { keys=authored;role=declared||'authored entity';description=explicit.getAttribute('data-math-description')||`${token}: ${role}.`; }
 else if(symbol) {
  role=symbol;keys=[`operator:${symbol}:${clean(expression)}`];
  description=token==='Σ'||token==='∑'?'Σ (sigma) means summation: evaluate each selected term, then add those values.':`${token}: ${symbol} in this expression.`;
  if(symbol==='sum')keys=['operation:sum'];if(symbol==='product'){keys=['operation:product'];description='Π (capital pi) means multiply the selected factors, one for each allowed index.';}
 } else if(!isNumber) {
  role=/^[jk]$/.test(token)&&indexKind?(kind.startsWith('reindex')?(token==='k'?'old index':'new index'):'summation index'):'symbol';
  keys=[`symbol:${token}`];
  description=/^[jk]$/.test(token)&&indexKind&&!kind.startsWith('reindex')?`${token} is the summation index. It selects a term; the selected term supplies the value to add.`:token==='k'&&indexKind?'k selects the original term. Its value identifies the index, not the amount being added.':token==='j'&&indexKind?'j is the new index. It selects the same term through the change-of-index rule.':`${token}: the same symbol in this worked example. Matching uses are highlighted.`;
 } else if(script==='exponent') {
  role='exponent';keys=[`exponent:${token}:${clean(expression)}`];description=`${token}: exponent. It tells which power to take; it is not the base or a term's value.`;
 } else if(script==='subscript') {
  role='subscript';keys=[`subscript:${token}:${clean(expression)}`];description=`${token}: subscript or index identifying this particular term.`;
 } else {
  role='matching displayed number';keys=[`written:number:${token}`];description=`${token}: matching displayed values in this example. These numbers may have different mathematical roles; this is a written-value link.`;
 }
 // Literal assignments and powers are independent roles, even when both print 2.
 const normalized=clean(expression);
 if(isNumber&&!authored.length&&!script) {
  const at=Number(element.getAttribute('data-math-offset')??-1),before=expression.slice(0,at),after=expression.slice(at+token.length);
  const plain=!element.closest('.katex-html')&&at>=0&&/^(?:\s*[,;:.]|\s*$|\s+(?:is|terms|gaps|pieces|means|counts)\b)/.test(after)?before.match(/([A-Za-zα-ω])\s*=\s*$/)?.[1]:null;
  const assignment=element.getAttribute('data-math-assignment')||plain;
  if(assignment){role='assigned value';keys=[`value:${assignment}:${token}`,`symbol:${assignment}`];description=`${token}: the value assigned to ${assignment} here.`;}
 }
 if(indexKind&&!authored.length) {
  const objs=state.objects??[];const terms=objs.filter(o=>o.role==='term'||o.role==='collected'||/^term-/.test(o.id??''));
  const computed=state.computed??{};const old=computed.oldIndices??terms.map(o=>o.data?.oldIndex??o.data?.index).filter(v=>v!==undefined);
  const fresh=computed.newIndices??terms.map(o=>o.data?.newIndex).filter(v=>v!==undefined);
  const values=computed.values??terms.map(o=>o.value==='unevaluated'&&kind==='formula-summands'?(o.data?.index??0)**2:o.value);
  const offset=computed.offset??(help?1:3);
  if(symbol==='sum')keys=['operation:sum'];if(symbol==='product'){keys=['operation:product'];description='Π (capital pi) means multiply the selected factors, one for each allowed index.';}
  const compound=element.getAttribute('data-math-term')||token.replace(/[₀-₉]/g,c=>sub[c]);const matchTerm=compound.match(/^a_?([0-9]+|[ijkn])$/);if(matchTerm){const i=/^\d+$/.test(matchTerm[1])?terms.findIndex(o=>(o.data?.index??o.data?.oldIndex)===Number(matchTerm[1])):-1;const cursor=objs.find(o=>o.role==='index')?.value;const selected=terms.findIndex(o=>(o.data?.index??o.data?.oldIndex)===cursor);keys=[i>=0?`term:value:${i}`:selected>=0?`term:value:${selected}`:'term:family'];role='indexed summand';description=i>=0?`This is the value of the term at index ${matchTerm[1]}. The subscript identifies which term, not its amount.`:'The indexed term: use the index to select a value, then add that value to the sum.';}
  if(token==='k')keys=['symbol:k','index:old'];
  if(token==='j')keys=['symbol:j',kind.startsWith('reindex')?'index:new':'index:old'];
  if(isNumber) {
   const num=Number(token), position=Number(element.getAttribute('data-math-offset')??0), before=expression.slice(0,position), after=expression.slice(position+token.length);
   const localPhrase=element.closest('.katex-html')?expression:expression.slice(Math.max(0,position-24),position+token.length+8);const indexAssignment=before.match(/([jk])\s*=\s*$/);const inIndexList=[...expression.matchAll(/(?:labels|indices|bounds|addresses)\s+[0-9, …a-z]+/gi)].some(m=>position>=m.index&&position<m.index+m[0].length);const explicitIndex=Boolean(indexAssignment)||inIndexList||/\b(?:index|indices|bounds?|old k|new j|address)\b/i.test(localPhrase)||/^[kj]=/.test(normalized)||Boolean(element.getAttribute('data-math-bound'));
   const newIndex=kind.startsWith('reindex')&&(/new j|new address|j\s*=/i.test(expression)||normalized.startsWith('j='));
   const shifting=/reindex-square/.test(kind)&&(element.getAttribute('data-math-shift-addend')==='true'||!element.closest('.katex-html')&&/(?:[+−-]|subtract|add)\s*$/.test(before));
   // KaTeX script roles distinguish the square exponent from a shifted index.
   if(element.hasAttribute('data-math-bound')){const side=element.getAttribute('data-math-index-symbol')==='j'&&kind.startsWith('reindex')?'new':'old';const list=side==='new'?fresh:old;const i=list.indexOf(num);keys=[i>=0?`index:${side}:${i}`:`bound:${element.getAttribute('data-math-bound')}`];role=`${element.getAttribute('data-math-bound')} summation bound`;description=`${token}: the ${role}, specifying which index is selected. It is not a summand value.`;}
   else if(script==='exponent'&&num===2){keys=['operation:square'];role='square exponent';description='2 is the exponent: square the recovered side length to count the pieces.';}
   else if(shifting&&num===offset&&!/index|indices|bounds/.test(expression)){keys=['shift:offset'];role='index shift';description=`${token}: the fixed index shift. Recover the old side with k = j + ${offset}.`;}
   else if(explicitIndex) {
    const list=newIndex&&fresh.length?fresh:old;const i=list.indexOf(num);
    if(i>=0){keys=[`index:${newIndex?'new':'old'}:${i}`];role=kind.startsWith('reindex')?(newIndex?'new index':'old index'):'summation index';description=`${token}: ${role} of term ${i+1}. This address selects the term; it is not its value.`;}
   } else if(!script) {
    const sequence=values.every(v=>typeof v==='number')?values.map(String).join('\\s*\\+\\s*'):null;
    const inExpansion=sequence&&[...expression.matchAll(new RegExp(sequence,'g'))].some(m=>position>=m.index&&position<m.index+m[0].length);
    const indexedAssignment=/a(?:_[0-9]+|[₀-₉]+)\s*=\s*$/.test(before);
    const knownOccurrence=indexedAssignment||inExpansion||(element.closest('.katex-html')&&sequence&&new RegExp(sequence).test(normalized));
    const i=knownOccurrence?values.findIndex(v=>typeof v==='number'&&v===num):-1;
    if(i>=0&&values.filter(v=>v===num).length===1){keys=[`term:value:${i}`];role='summand value';description=`${token}: the value contributed by term ${i+1}. Σ adds the selected term values.`;}
   }
  }
 }
 // Preserve the original three lessons' explicitly authored numeric-link contract.
 if(!(Number(context?.frame?.visual?.order)>=4)&&(element.hasAttribute('data-math-value')||element.hasAttribute('data-math-values'))){keys=[element.getAttribute('data-math-value'),...(element.getAttribute('data-math-values')||'').split(/\s+/)].filter(Boolean).map(v=>`legacy:value:${v}`);role='worked value';description=`${token}: matching numerical uses in this original worked example.`;}

 if(kind.startsWith('geometric')&&symbol==='sum'){
  const at=Number(element.getAttribute('data-math-offset')??0),start=element.getAttribute('data-math-sum-start')??expression.slice(at+token.length).match(/^\s*\(?k\s*=\s*([0-9]+)/)?.[1];
  if(start==='1'){keys=['geometric:scaled'];description='Σ adds the shifted, multiplied copies, with indices starting at 1. These are the orange terms of rSₙ.';}
  else{keys=['operation:sum'];description='Σ adds the original terms, starting at index 0. These are the blue terms of Sₙ.';}
 }
 const memberships=(element.getAttribute('data-math-memberships')||explicit?.getAttribute('data-math-memberships')||'').split(/\s+/).filter(Boolean);
 const diagram=element.closest('[data-diagram-node]');
 if(diagram&&!authored.length&&isNumber&&!script) {const id=diagram.getAttribute('data-diagram-node');keys.push(`entity:${id.endsWith('-label')?id.slice(0,-6):id}`);description=`${token} is printed on ${id.replace(/-label$/, '').replace(/-/g,' ')}. Other highlighted numerals share its displayed value; their mathematical roles may differ.`;}
 const scopeKeys=ks=>[...new Set(ks)].map(k=>`${info.scope}|${k}`);
 if(!authored.length&&/geometric|arithmetic/.test(kind)&&!isNumber){const compound=element.getAttribute('data-math-term')||token;const count=state.computed?.termCount;if(/^S(?:_?n|_?\d+)?$/.test(compound)&&(compound==='S'||compound==='S_n'||count===Number(compound.replace(/^S_?/,''))))keys=[element.getAttribute('data-math-scaled-sum')==='true'||/Doubled|2S/.test(expression)?'geometric:scaled':'symbol:S'];const meanings={n:'n counts the terms. The number of gaps or the last exponent can be different.',a:'a is the value of the first term.',d:'d is the fixed amount added between neighboring terms.',r:'r is the common ratio: multiply by this factor to reach the next term.',k:'k is the index or exponent position. The term value is computed from it.',S:'S is the total of one original sum.'};if(meanings[token])description=meanings[token];}
 return {keys:scopeKeys(keys),matchKeys:scopeKeys([...keys,...memberships,...(isNumber?[`written:number:${token}`]:[])]),localKeys:keys,token,role,description};
}


function bindVisualEntities(root,context) {
 const {kind,state,help}=contextInfo(context);
 const set=(el,keys,memberships,role,description)=>{if(!el)return;const attrs={'data-math-keys':keys,'data-math-memberships':memberships,'data-math-role':role,'data-math-description':description};for(const [key,value] of Object.entries(attrs))if(el.getAttribute(key)!==value)el.setAttribute(key,value);};
 for(const el of root.querySelectorAll('[data-move],[data-motion-id]')) {
  const id=el.getAttribute('data-move')||el.getAttribute('data-motion-id');let m;
  if((m=id.match(/^sum-(\d+)-unit-/)))set(el,`term:value:${m[1]}`,`operation:sum term:family index:old:${m[1]}`,'summand units',`These units contribute the value of term ${Number(m[1])+1} to the sum.`);
  if((m=id.match(/^fixed-term-(\d+)$/)))set(el,`term:value:${m[1]}`,`operation:sum term:family index:old:${m[1]} index:new:${m[1]}`,'summand value',`The same square for term ${Number(m[1])+1} remains unchanged when its address changes.`);
  if((m=id.match(/^old-tag-(\d+)$/)))set(el,`index:old:${m[1]}`,'index:old symbol:k','old index','The old index k selects this square and gives its side length.');
  if((m=id.match(/^new-tag-(\d+)$/)))set(el,`index:new:${m[1]}`,'index:new symbol:j','new index','The new address j selects this same square after reindexing.');
  if((m=id.match(/^reindex-cell-(\d+)-/)))set(el,`term:value:${m[1]}`,`operation:sum term:family index:old:${m[1]}`,'summand units','One physical piece in this term; changing its address does not change the piece.');
  if((m=id.match(/^geometric-original-(\d+)$/)))set(el,`geometric:original:${m[1]}`,'operation:sum symbol:S','original summand',`The original term at exponent ${m[1]}.`);
  if((m=id.match(/^geometric-copy-(\d+)$/)))set(el,`geometric:copy:${m[1]}`,'geometric:scaled symbol:r','scaled summand',`The copy of term ${m[1]}, multiplied by the ratio.`);
  if((m=id.match(/^gap-term-(\d+)$/)))set(el,`arithmetic:term:${m[1]}`,`symbol:n${m[1]==='0'?' symbol:a':''}`,'arithmetic term',`Term ${Number(m[1])+1}; n counts these piles, a is the first pile's value.`);
  if((m=id.match(/^gap-(\d+)$/)))set(el,`arithmetic:gap:${m[1]}`,'symbol:d','common difference','Each gap adds the common difference d.');
 }
 if(/^(indexed-accumulation|formula-summands|empty-sum)$/.test(kind)) {
  const objects=(state.objects??[]).filter(o=>o.role==='term'||o.role==='collected'||/^term-/.test(o.id??''));const start=kind==='formula-summands'&&!help?2:1;
  for(const text of root.querySelectorAll('svg text')){
   const value=text.textContent?.trim()||'';let m;
   if((m=value.match(/^index (\d+)$/))){const i=Number(m[1])-start;set(text,`index:old:${i}`,'index:old symbol:k symbol:j','index address',`${m[1]} is the address of term ${i+1}; it does not give the value being added.`);}
   if(/^running sum =/.test(value))set(text,'sum:total','operation:sum symbol:S','running total','The accumulator stores the sum of the term values already selected.');
   if(/^upper 0$/.test(value))set(text,'bound:upper','','upper bound','0 is the upper bound. Since it is below the lower bound 1, no index is selected.');
   if(/^lower 1$/.test(value))set(text,'bound:lower','','lower bound','1 is the starting index, not a summand value. The upper bound 0 is smaller.');
   if(/^\d+$/.test(value)) {const matches=objects.map((o,i)=>({o,i})).filter(({o})=>String(o.value)===value);if(matches.length===1)set(text,`term:value:${matches[0].i}`,'operation:sum','summand value',`${value} is the value contributed by term ${matches[0].i+1}.`);}
  }
 }
 if(/geometric|arithmetic/.test(kind))for(const text of root.querySelectorAll('svg text')){
  const value=text.textContent?.trim()||'';let m;
  if((m=value.match(/^k = (\d+)$/)))set(text,`index:power:${m[1]}`,'symbol:k','exponent index',`${m[1]} counts doublings from the first term. It is not the term's value.`);
  if((m=value.match(/^(?:r\s*=\s*|×)([12])$/)))set(text,'symbol:r','','common ratio',`${m[1]} is the repeated multiplier r, not an exponent or a term address.`);
  if((m=value.match(/^(?:d\s*=\s*)?\+(\d+)$/)))set(text,'symbol:d','','common difference',`${m[1]} is the amount d added at every gap.`);
 }
 for(const el of root.querySelectorAll('[data-diagram-node]')){const id=el.getAttribute('data-diagram-node');set(el,`entity:${id.endsWith('-label')?id.slice(0,-6):id}`,'','diagram object',`This is ${id.replace(/-label$/, '').replace(/-/g,' ')} in the current diagram.`);}
}

/** Event delegation works for React, KaTeX and recovered D3 labels. */
export function mountSymbolConnections(root,context={},onChange=()=>{}) {
 let hovered=null,focused=null,pinned=null,disposed=false,queued=false;const linked=new Set();const handlers=[];
 const descriptions=new WeakMap();let sequence=0;const ids=new WeakMap();
 const tooltip=root.ownerDocument.createElement('span');tooltip.className='math-symbol-tooltip';tooltip.setAttribute('role','tooltip');tooltip.hidden=true;
 Object.assign(tooltip.style,{position:'fixed',zIndex:'1000',maxWidth:'min(23rem, calc(100vw - 24px))',padding:'7px 10px',border:'1px solid var(--color-border, #888)',background:'var(--color-surface, #fff)',color:'var(--color-text-main, #222)',boxShadow:'0 2px 8px #0002',font:'13px/1.4 sans-serif',pointerEvents:'none'});
 root.append(tooltip);
 const visible=el=>!root.closest('.hidden,[hidden],[inert]')&&!el.closest('[hidden]')&&![...ancestors(el,root)].some(n=>n.getAttribute('opacity')==='0'||n.getAttribute('aria-hidden')==='true'&&n.tagName.toLowerCase()!=='span');
 function* ancestors(el,end){for(let n=el;n&&n!==end;n=n.parentElement)yield n;}
 const find=target=>{const el=target instanceof Element?target.closest(SYMBOL_SELECTOR):null;return el&&root.contains(el)&&visible(el)?el:null;};
 const resolve=el=>{if(!ids.has(el))ids.set(el,++sequence);el.setAttribute('data-math-occurrence',String(ids.get(el)));const value=resolveSymbol(el,context,String(ids.get(el)));descriptions.set(el,value);return value;};
 const annotate=()=>{
  bindVisualEntities(root,context);
  for(const el of root.querySelectorAll(SYMBOL_SELECTOR)) {
   if(el.closest('.math-symbol-tooltip'))continue;
   const value=resolve(el);el.setAttribute('data-math-role',value.role);el.setAttribute('data-math-resolved',value.keys.join(' '));
   const button=el.closest('button,a[href],input,select,textarea');
   // Tokens in passage buttons are focusable, but retain their parent's native action.
   if(!el.matches('input,select,textarea')&&value.token&&el.matches('[data-math-token],[data-math-value]')) {
    el.classList.add('linked-number');el.closest('svg')?.setAttribute('role','group');if(!button||button===el){el.setAttribute('role','button');el.setAttribute('data-math-keyboard','true');}
    if(button&&button!==el){el.removeAttribute('tabindex');el.removeAttribute('role');el.removeAttribute('data-math-keyboard');}else el.setAttribute('tabindex',visible(el)?'0':'-1');el.setAttribute('aria-label',`${value.token}. ${value.description}`);
   }
   const html=el.closest('.katex-html');if(html){html.removeAttribute('aria-hidden');}
  }
 };
 const update=()=>{
  if(disposed)return;
  for(const el of linked)el.removeAttribute('data-math-linked');linked.clear();
  if(hovered&&!find(hovered))hovered=null;if(focused&&!find(focused))focused=null;if(pinned&&!find(pinned))pinned=null;
  const selected=hovered||pinned||focused;
  if(!selected){root.removeAttribute('data-math-selection');if(!tooltip.hidden)tooltip.hidden=true;onChange('',[]);return;}
  const current=resolve(selected),keys=new Set(current.keys);
  for(const el of root.querySelectorAll(SYMBOL_SELECTOR))if(visible(el)&&resolve(el).matchKeys.some(k=>keys.has(k))){el.setAttribute('data-math-linked','true');linked.add(el);}
  selected.setAttribute('data-math-linked','true');linked.add(selected);
  root.setAttribute('data-math-selection',current.keys.join(' '));if(tooltip.textContent!==current.description)tooltip.textContent=current.description;if(tooltip.hidden)tooltip.hidden=false;
  const rect=selected.getBoundingClientRect();const width=root.ownerDocument.defaultView?.innerWidth??800,height=root.ownerDocument.defaultView?.innerHeight??600;
  tooltip.style.left=`${Math.max(12,Math.min(rect.left,width-370))}px`;tooltip.style.top=`${Math.min(height-95,Math.max(8,rect.bottom+8))}px`;
  onChange(current.description,pinned?[current.token]:[]);
 };
 const clear=()=>{hovered=null;focused=null;pinned=null;update();};
 const toggle=el=>{pinned=pinned===el?null:el;hovered=null;focused=null;update();};
 const listen=(el,event,handler,options)=>{el.addEventListener(event,handler,options);handlers.push(()=>el.removeEventListener(event,handler,options));};
 listen(root,'pointerover',e=>{hovered=find(e.target);update();});
 listen(root,'pointerout',e=>{hovered=find(e.relatedTarget);update();});
 listen(root,'pointerleave',()=>{hovered=null;update();});
 listen(root,'focusin',e=>{focused=find(e.target)||(e.target instanceof Element&&e.target.matches('button')?find(e.target.querySelector(SYMBOL_SELECTOR)):null);update();});
 listen(root,'focusout',e=>{focused=find(e.relatedTarget);update();});
 listen(root,'click',e=>{const el=find(e.target);if(el&&!el.matches('input,select,textarea')){toggle(el);if(el.closest('button,a[href]')&&e.target!==el.closest('button,a[href]'))e.stopPropagation();}},true);
 listen(root,'keydown',e=>{if(e.target instanceof Element&&e.target.matches('button')&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){const tokens=[...e.target.querySelectorAll(SYMBOL_SELECTOR)].filter(visible);if(tokens.length){e.preventDefault();e.stopPropagation();const index=tokens.indexOf(focused);focused=tokens[(index+(e.key==='ArrowRight'?1:-1)+tokens.length)%tokens.length];hovered=null;pinned=null;update();}return;}if(e.key==='Escape'){clear();return;}const el=find(e.target);if(el&&e.target===el&&!el.matches('button,a[href],input')&&(e.key===' '||e.key==='Enter')){e.preventDefault();e.stopPropagation();if(!e.repeat)toggle(el);}},true);
 listen(root.ownerDocument,'keydown',e=>{if(e.key==='Escape')clear();});
 listen(root.ownerDocument,'pointerdown',e=>{if(!root.contains(e.target))clear();});
 listen(root.ownerDocument.defaultView,'hashchange',clear);
 const observer=new MutationObserver(records=>{if(records.every(record=>record.target===tooltip||tooltip.contains(record.target)||record.attributeName==='opacity'&&!['0','1'].includes(record.target.getAttribute('opacity'))))return;if(queued)return;queued=true;queueMicrotask(()=>{queued=false;if(!disposed){annotate();update();}});});
 observer.observe(root,{subtree:true,childList:true,attributes:true,attributeFilter:['data-math-token','data-math-value','data-math-keys','opacity','hidden']});
 annotate();update();return {clear,dispose(){disposed=true;observer.disconnect();handlers.forEach(f=>f());for(const el of linked)el.removeAttribute('data-math-linked');root.removeAttribute('data-math-selection');tooltip.remove();}};
}

/** D3 owns these text nodes, so its existing observer may wrap them directly. */
export function legacySvgSegments(text){return splitMathSymbols(text,/^[A-Za-z]$/.test(text.trim())).map(part=>({text:part.text,value:part.token}));}
