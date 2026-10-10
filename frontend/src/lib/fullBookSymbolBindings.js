/** Full-book semantic identities. Equal printed numerals are never a binding rule.
 * Family scopes are supplied by symbolConnections; memberships are passive matches.
 * Only authored node IDs, operand roles and current-frame facts justify links here. */
import {structureSymbolBinding} from './structureSymbolBindings.js';
const unique=xs=>[...new Set(xs.filter(Boolean))];
const binding=(keys,role,description,memberships=[])=>({keys:unique(keys),memberships:unique(memberships),role,description});
const attr=(e,k)=>e?.getAttribute?.(k)??null;
const isNumber=t=>/^[-−]?\d+(?:\.\d+)?$/.test(t);
const normalized=t=>String(t??'').replace(/[₀₁₂₃₄₅₆₇₈₉]/g,c=>'₀₁₂₃₄₅₆₇₈₉'.indexOf(c)).replace(/_/g,'');
function info(element,context){
 const visual=context?.frame?.visual??context?.visual??{};const state=visual.state??{};
 const group=element?.closest?.('[data-diagram-node]');const id=attr(element,'data-diagram-node')??attr(group,'data-diagram-node')??'';
 const nodes=state.diagram?.nodes??[];const node=nodes.find(n=>n.id===id);
 const token=attr(element,'data-math-token')??attr(element,'data-math-value');
 const expression=attr(element,'data-math-expression')??element?.closest?.('[data-math-expression]')?.getAttribute?.('data-math-expression')??node?.text??element?.textContent??'';
 return {element,visual,state,model:visual.model??{},order:Number(visual.order),nodes,node,id,token:token===null?null:normalized(token),raw:token,expression,script:attr(element,'data-math-script'),offset:Number(attr(element,'data-math-offset')??-1),physical:token===null};
}
function memberConcept(key,role,description){return binding([key],role,description);}
function graphObject(c){
 let m=c.id.match(/^(?:v|t)([A-Za-z0-9][A-Za-z0-9-]*)$/);
 if(m&&c.nodes.some(n=>n.id==='v'+m[1]&&n.type==='circle'))return m[1];
 m=c.id.match(/^(?:rootline|root|fields|name)([A-Za-z0-9-]+)$/);if(m&&c.nodes.some(n=>n.id==='v'+m[1]))return m[1];
 return null;
}
function mixBinding(c){
 const {order,id,token,physical,nodes,model,state,expression,script}=c;const byte=id.match(/^([wvp])(\d+)-(\d)$/);let field=model.field??state.data?.field;
 if(field===undefined){const t=model.executedTrace?.find(t=>t.after?.clock===state.data?.clock);field=t?.field;}
 const L=Number.isInteger(field)?Math.floor(field/8):null,R=Number.isInteger(field)?field%8:null;
 const registerForRow=row=>{const label=String(nodes.find(n=>n.id==='label-'+row)?.text??'');if(order===66)return row===1?'R':null;const m=label.match(/\b(A|X|I[1-6]|J)\b/);return m?.[1]??null;};
 const registerKey=r=>'mix:register:'+r;
 if(isNumber(token)&&c.offset>=0&&!script){
  const before=expression.slice(0,c.offset),a=before.match(/\b(A|X|J|PC|I[1-6]|F|L|R|M)\s*=\s*$/);
  if(a){const name=a[1],key=name==='F'?'mix:field':name==='L'?'mix:field:left':name==='R'?'mix:field:right':name==='M'?'mix:effective-address':registerKey(name);return binding([key],'assigned machine value',`${token} is the value of ${name} in this assignment; equal values in other roles are separate.`);}
 }
 const meanings={A:['accumulator','A is the accumulator register; its value is separate from an instruction address.'],X:['extension register','X is the extension register, including the low half of an A:X product.'],J:['return register','J stores the return address saved by a taken ordinary jump.'],PC:['program counter','PC identifies the instruction address, not its opcode or operand value.'],M:['effective address','M is the encoded address plus the contents of the selected index register.'],F:['field selector','F encodes L:R as 8L+R, or selects the opcode-specific variant.'],L:['left field endpoint','L is the first included byte/sign position; position zero is the sign.'],R:['right field endpoint','R is the last included field position.'],b:['byte base','b is the number of values a MIX byte can hold; place weights are powers of b.']};
 if(token!==null&&!isNumber(token)){
  if(token==='w')return memberConcept('mix:word','MIX word','w is the sign-plus-five-byte word.');
  if(token==='s')return memberConcept('mix:sign','word sign','s is the separate positive or negative sign.');
  if(/^d[1-5]$/.test(token))return memberConcept(`mix:byte:0:${token.slice(1)}`,'positional digit','This digit belongs to its specified byte compartment.');
  if(token==='d'||token==='dj')return memberConcept('mix:digits','positional digits','Each digit contributes its value times the corresponding base-place weight.');
  if(token==='Σ'||token==='∑')return memberConcept('operation:sum','summation','Add the selected operand or term contributions.');
  if(/^I[1-6]$/.test(token))return memberConcept(registerKey(token),'index register',`${token} contains the signed index value added to the encoded address.`);
  if(token==='R'&&((order===67&&script!=='subscript'&&/CMP|field|register/.test(expression))||order===66&&/register\s*R|R\s*register/i.test(expression)))return memberConcept(registerKey('R'),'selected register','R is the selected register; this is not the right endpoint of L:R.');
  if(meanings[token]){const [role,description]=meanings[token];let key=token==='F'?'mix:field':token==='L'?'mix:field:left':token==='R'?'mix:field:right':token==='M'?'mix:effective-address':token==='b'?'mix:base':registerKey(token);return memberConcept(key,role,description);}
  if(token==='I'&&/index|AA|A\s*I\s*F\s*C|selector/.test(expression))return memberConcept('mix:index-selector','index selector','I selects an index register; the selected register’s contents are added, not the selector number.');
  if(token==='C'&&order!==76)return memberConcept('mix:opcode','opcode','C is the opcode byte selecting the instruction family.');
  if(token==='P'&&order===68)return memberConcept(registerKey('PC'),'instruction address before execution','P is PC before this instruction; P+1 is its sequential continuation.');
 }
 if(byte){
  const kind=byte[1],row=Number(byte[2]),position=Number(byte[3]),reg=registerForRow(row);const cell=`mix:byte:${row}:${position}`;const positionKey=`mix:position:${position}`;
  const members=['mix:word',positionKey,reg?registerKey(reg):'mix:memory',reg?registerKey('R'):null,position===0?'mix:sign':'mix:magnitude',order===65?'operation:sum':null];
  if(position>0)members.push('mix:base','mix:digits',`mix:place-weight:${position}`);
  if(L!==null){
   const count=Math.max(0,R-Math.max(L,1)+1),registerField=order===66&&row===1;
   const selected=registerField?((position===0&&L===0)||(position>=6-count&&position<=5)):position>=L&&position<=R;
   if(selected)members.push('mix:field');
   if(position===(registerField?(L===0?0:6-count):L))members.push('mix:field:left');
   if(position===(registerField?(count?5:0):R))members.push('mix:field:right');
   if(order===66&&position>0&&selected){const memoryPosition=registerField?Math.max(L,1)+position-(6-count):position;members.push(`mix:transfer-byte:${memoryPosition}`);}
  }
  if(kind==='p')return binding([positionKey],'byte position',`Position ${position} identifies ${position===0?'the sign':'a digit compartment'}; it is not the stored digit.`,['mix:positions',...members.filter(k=>k?.startsWith('mix:field'))]);
  if(kind==='v')members.splice(members.indexOf(positionKey),1);
  return binding([cell],position===0?'sign representation':'stored byte',`${reg?reg+' register':'memory word'}, position ${position}: the stored digit and its compartment share identity.`,members);
 }
 let m=id.match(/^transfer-byte-(?:value-)?(\d)$/);
 if(m){const position=Number(m[1]),count=Math.max(0,R-Math.max(L,1)+1),registerPosition=6-count+position-Math.max(L,1);return binding([`mix:transfer-byte:${position}`],'transferred byte','This selected byte retains its value while moving to the operation’s destination.',['mix:field','mix:memory',registerKey('R'),`mix:byte:0:${position}`,`mix:byte:1:${registerPosition}`]);}
 if(/^transfer-sign/.test(id))return binding(['mix:transfer-sign'],'transferred sign','Only a field including position zero transfers the sign.',['mix:field','mix:field:left','mix:sign',registerKey('R')]);
 if(id.startsWith('place-weight-'))return binding([`mix:place-weight:${Number(id.slice(13))+1}`],'positional contribution','This byte is multiplied by its base-place weight.',['mix:base','mix:magnitude','operation:sum']);
 if(id==='signed-word-token'||id==='signed-word-value')return binding([isNumber(token)?'mix:magnitude':'mix:word-representation'],'signed word magnitude','This magnitude is located in the lane belonging to its separate sign.',['mix:word','mix:sign','mix:magnitude']);
 if(/^(?:positive|negative)-(?:lane|label)$/.test(id))return binding(['mix:sign:'+id.split('-')[0]],'sign lane','This lane represents a sign, independently of the magnitude.',['mix:sign']);
 const physicalRoles={
  'effective':['mix:effective-address'], 'instruction-address-equation':['mix:effective-address','mix:index-selector'],
  'fetch-address':[registerKey('PC')], 'executed-code-cursor':[registerKey('PC')],
  'decode-values':['mix:opcode','mix:field'], 'instruction-identity':['mix:opcode','mix:field',registerKey('PC')],
  'magnitude-expansion':['mix:magnitude','mix:base','operation:sum'], 'signed-word-token':['mix:word','mix:sign'], 'signed-word-value':['mix:word','mix:sign'],
  'prefix-equation':[registerKey('A'),'operation:sum'], 'index-equation':[registerKey('I1'),'mix:effective-address'],
 };
 if(physicalRoles[id])return binding([`mix:display:${id}`],'MIX operation display','This display exposes the named machine quantities and their actual computed relationship.',physicalRoles[id]);
 if(id==='detail'||id==='instruction-operands'||id==='instruction-equation'||id==='instruction-calculation-panel'){
  const label=String(nodes.find(n=>n.id==='instruction-equation')?.text??expression);const regs=[...label.matchAll(/\b(A|X|J|PC|I[1-6])\b/g)].map(m=>registerKey(m[1]));
  return binding([`mix:display:${id}`],'executed operands and result','The operands, calculation and destination belong to this committed instruction.',[...regs,'mix:effective-address',/←.*\+|prefix|sum/i.test(label)?'operation:sum':null]);
 }
 if(id==='stage-1'||id==='stage-label-1')return binding(['mix:decode'],'instruction decode','Decode the address, index, field and opcode bytes.',['mix:opcode','mix:field','mix:index-selector']);
 if(id==='stage-2'||id==='stage-label-2')return binding(['mix:address-calculation'],'effective address calculation','Add the encoded address to the selected index-register contents.',['mix:effective-address','mix:index-selector']);
 if(id==='stage-0'||id==='stage-label-0')return binding(['mix:fetch'],'instruction fetch','Read the instruction word at PC.',[registerKey('PC')]);
 if(id==='stage-4'||id==='stage-label-4')return binding(['mix:continuation'],'continuation','Retain the next instruction address.',[registerKey('PC'),registerKey('J')]);
 if((m=id.match(/^code-address-(\d+)$/)))return binding([`mix:instruction-address:${m[1]}`],'instruction address','This number identifies a code location, not its contents.',[registerKey('PC')]);
 // Bind a literal only when the immediately preceding assignment names its role.
 if(isNumber(token)&&c.offset>=0&&!script){const before=expression.slice(0,c.offset);const a=before.match(/\b(A|X|J|PC|I[1-6]|F|L|R|M)\s*=\s*$/);if(a){const name=a[1];return binding([`mix:value:${name}:${token}`],'assigned machine value',`${token} is the current value of ${name}, not every equal numeral.`,[name==='F'?'mix:field':name==='L'?'mix:field:left':name==='R'?'mix:field:right':name==='M'?'mix:effective-address':registerKey(name)]);}}
 return null;
}
function processBinding(c){
 const {order,id,token,state,nodes}=c;let m;
 if((m=id.match(/^(?:card|name|val)-(\d+)$/))&&nodes.some(n=>n.id==='card-'+m[1])){
  const j=m[1],label=String(nodes.find(n=>n.id==='name-'+j)?.text??'quantity'),members=[];
  if(/sum|total|probability/i.test(label))members.push('operation:sum');
  if(/time|finish/i.test(label))members.push('buffer:time');
  if(order===78){if(label==='calls')members.push('code:call-count');if(/inline|shared/.test(label))members.push('code:body','code:call-count');if(/shared/.test(label))members.push('code:linkage','code:per-call');}
  return binding([`computed:quantity:${j}`],label,`This is the ${label} quantity in this worked comparison; other equal numerals retain their own roles.`,members);
 }
 if(order===78){const roles={k:['code:call-count','number of calls'],B:['code:body','routine body size or cost'],L:['code:linkage','one-time linkage cost'],C:['code:per-call','per-call overhead']};if(roles[token])return memberConcept(roles[token][0],roles[token][1],`${token} denotes ${roles[token][1]} in this comparison.`);}
 if([69,85,86].includes(order)){
  const data=state.data??{};const counts={E:'EMPTY',F:'FILLING',R:'READY',P:'PROCESSING'};
  if(token&&order===86&&counts[token])return memberConcept('buffer:state:'+counts[token],'buffer-state count',`${token} counts buffers currently ${counts[token]}; it is not an item number.`);
  if(token==='I')return memberConcept('buffer:input-service','input service time','I is the service time for one device input.');
  if(token==='C')return memberConcept('buffer:cpu-service','computation service time','C is the service time for one CPU item.');
  if(token==='t'||/^T[12]?$/.test(token??''))return memberConcept('buffer:time','elapsed schedule time','This is elapsed model service time.');
  if(token==='k')return memberConcept('buffer:pool','buffer count','k counts the independently owned buffers.');
  if(token==='n')return memberConcept('buffer:items','item count','n counts the input items issued and consumed.');
  if((m=id.match(/^(?:buffer-|buf-(?:name|state|item)-)(\d+)$/))){const j=Number(m[1]),status=data.states?.[j];return binding([`buffer:${j}`],'physical buffer','This buffer keeps its identity while ownership and contents change.',['buffer:pool',status?'buffer:state:'+status:null,id.startsWith('buf-item')?'buffer:items':null]);}
  if(/^device/.test(id))return binding(['buffer:device'],'input device','The device owns a filling buffer during input.',['buffer:input-service','buffer:state:FILLING']);
  if(/^cpu/.test(id))return binding(['buffer:cpu'],'CPU consumer','The CPU owns a processing buffer during computation.',['buffer:cpu-service','buffer:state:PROCESSING']);
  if(id==='time')return binding(['buffer:time'],'elapsed time','The current schedule time, not a buffer index.');
  if(id==='queue')return binding(['buffer:queue'],'ready queue','Ready buffers retain FIFO order.',['buffer:state:READY']);
  if(id==='done')return binding(['buffer:completed'],'completed items','These payload identifiers have been consumed.',['buffer:items']);
 }
 if([73,74,75].includes(order)){
  if((m=id.match(/^(?:object-|name-)(\d+)$/))&&nodes.some(n=>n.id==='object-'+m[1]))return binding(['object:'+m[1]],'permutation object','This label identifies an object, not an array index or a numeric total.',['permutation:domain']);
  if((m=id.match(/^(cell|value|index)-(\d+)$/))){const key=m[2];if(m[1]==='index')return binding(['permutation:index:'+key],'array position','The address selects a successor cell; it is separate from the stored successor.');return binding(['permutation:cell:'+key],'successor cell','This cell stores an image or tagged predecessor.',['permutation:mapping',m[1]==='cell'?'permutation:index:'+key:null]);}
  if(token==='p'||token==='π')return memberConcept('permutation:mapping','permutation mapping','The permutation maps each object to exactly one successor.');
  if(token==='n')return memberConcept('permutation:domain','permutation size','n counts the permuted objects.');
  if(/^arrow-|edge-label-/.test(id))return binding(['permutation:edge:'+id.replace(/^(?:arrow-|edge-label-)/,'')],'successor link','This arrow follows the actual permutation image.',['permutation:mapping']);
 }
 if(order===79||order===80){
  if(token==='i')return memberConcept('coroutine:counter','retained producer counter','i is retained across suspension; resumption does not restart it.');
  if(token==='T'||token==='Σ'||token==='∑')return memberConcept(token==='T'?'coroutine:total':'operation:sum','consumer total','The consumer adds each handed-off payload exactly once.');
  if(/^producer-/.test(id))return binding(['coroutine:producer:'+id.replace(/^producer-/,'').replace(/-(?:text|pc)$/,'')],'producer continuation','This is a saved producer location.',['coroutine:counter']);
  if(/^consumer-/.test(id))return binding(['coroutine:consumer:'+id.replace(/^consumer-/,'').replace(/-(?:text|pc)$/,'')],'consumer continuation','This is a saved consumer location.',['coroutine:total','operation:sum']);
  if(id==='total')return binding(['coroutine:total'],'consumer accumulator','The total includes only already consumed payloads.',['operation:sum']);
  if(id==='retained')return binding(['coroutine:retained'],'retained local state','The producer counter and pending payload survive suspension.',['coroutine:counter']);
  if(/^handoff/.test(id))return binding(['coroutine:handoff'],'control and payload handoff','Transfer control with the retained pending value.',['coroutine:total']);
 }
 if(order===87){
  if(token==='B')return memberConcept('packing:capacity','physical block capacity','B counts character positions in each physical block.');
  if(token==='N')return memberConcept('packing:payload','payload length','N is total payload characters; padding is excluded.');
  if(token==='c')return memberConcept('packing:consumed','consumed prefix length','c counts characters already consumed.');
  if((m=id.match(/^(?:pack|char)-(\d+)-(\d+)$/)))return binding([`packing:position:${m[1]}:${m[2]}`],'physical payload slot','This character position belongs to a particular physical block.',['packing:capacity','packing:payload']);
  if(id==='cursor')return binding(['packing:consumed'],'consumed prefix','This tracks how much logical payload has been packed.');
 }
 return null;
}
function allocatorBinding(c){
 const {id,token,physical,order,nodes,state,expression,script}=c;const block=id.match(/^block(\d+)(label|size|addr|head|foot)?$/);const buddy=order===140;
 if(isNumber(token)&&!c.physical){
  if(buddy&&script==='exponent')return binding([`buddy:order-value:${token}`],'power-of-two order',`${token} is the exponent determining block size, not a byte count.`);
  if(c.offset>=0&&!script){const before=expression.slice(0,c.offset);
   if(/(?:offset|address|start|x\s*=)\s*$/i.test(before))return binding([`allocator:offset:${token}`],'arena offset','This number identifies a block position, not its size.');
   if(/(?:size|capacity|reserve|rounded to)\s*$/i.test(before))return binding([`allocator:size-value:${token}`],'byte count','This number is a byte capacity, distinct from the same numeral used as an address.');
  }
 }
 if(token!==null&&!isNumber(token)){
  const meanings=buddy?{x:['buddy:offset','block offset','x is an arena-relative block offset, not a block size.'],k:['buddy:order','buddy order','k is the order: the block size is 2^k bytes.'],B:['allocator:base','arena base','B is the arena base; XOR applies to offsets relative to it.']}:{p:['allocator:start','block start','p is a block start address.'],q:['allocator:next-start','neighbor start','q is the next block’s start.'],s:['allocator:size','block size','s is a block size measured in bytes.'],C:['allocator:capacity','arena capacity','C is total arena capacity.'],r:['allocator:request','payload request','r is the requested payload size.'],h:['allocator:overhead','metadata overhead','h is reserved metadata overhead.'],a:['allocator:alignment','alignment','a is the required alignment.']};
  if(meanings[token]){const [key,role,description]=meanings[token];return memberConcept(key,role,description);}
  if((token==='2'&&script==='exponent')||token==='k'&&buddy)return memberConcept('buddy:order','buddy order','The exponent determines the power-of-two block size.');
  if(token==='Σ'||token==='∑'){
   const source=String(expression),offset=c.offset;
   let subset=null;
   const bounds=[...source.matchAll(/\\sum(?:_\{([^}]*)\}|_([^\s{]))?/g)];
   let sumIndex=0;
   if(bounds.length>1){const html=c.element?.closest?.('.katex-html');const atoms=[...(html?.querySelectorAll?.('[data-math-token]')??[])].filter(el=>['Σ','∑'].includes(attr(el,'data-math-token')));sumIndex=atoms.indexOf(c.element);}
   if(bounds[sumIndex]){const bound=bounds[sumIndex][1]??bounds[sumIndex][2]??'';if(/live|allocated|reserved/i.test(bound))subset='live';else if(/free/i.test(bound))subset='free';}
   if(subset)return memberConcept(`operation:sum:${subset}`,'byte accounting',`Sum only ${subset} block sizes; the complementary subset is a separate sum.`);
   return memberConcept('operation:sum','byte accounting','Sum the displayed block or slot contributions without merging their identities.');
  }
 }
 if(block){const start=Number(block[1]),suffix=block[2]??'',key=`allocator:block:${start}`;const label=String(nodes.find(n=>n.id===`block${start}label`)?.text??'');const members=['allocator:partition','allocator:start','allocator:size',`allocator:offset:${start}`,`allocator:size-of:${start}`,buddy?'buddy:offset':null,buddy?'buddy:order':null,buddy?'buddy:size':null,'operation:sum'];if(label&&label!=='free')members.push('object:'+label);members.push(label==='free'?'operation:sum:free':'operation:sum:live');const size=Number(nodes.find(n=>n.id===`block${start}size`)?.text);if(Number.isFinite(size)){members.push(`allocator:size-value:${size}`);if(buddy&&size>0&&Number.isInteger(Math.log2(size)))members.push(`buddy:order-value:${Math.log2(size)}`);}
  if(suffix==='addr')return binding([`allocator:offset:${start}`],'block address',`${start} is the start offset of this block, separate from its byte count.`,['allocator:start',buddy?'buddy:offset':null,key]);
  if(suffix==='size')return binding([`allocator:size-of:${start}`],'block byte count','This size belongs to this particular block; another equal size is a different block.',['allocator:size',`allocator:size-value:${size}`,buddy?'buddy:order':null,buddy?'buddy:size':null,Number.isFinite(size)&&size>0&&Number.isInteger(Math.log2(size))?`buddy:order-value:${Math.log2(size)}`:null,key]);
  if(suffix==='head'||suffix==='foot')return binding([`allocator:tag:${start}:${suffix}`],'boundary tag','This endpoint metadata describes its owning block.',[key,'allocator:overhead',`allocator:size-of:${start}`]);
  return binding([key],'memory block','The half-open byte interval beginning at this offset; its payload, size and address have distinct roles.',members);
 }
 let m=id.match(/^(?:slot|size|used)(\d+)$/)||id.match(/^inventory-token-(?:label-)?(\d+)$/);
 if(m){const j=m[1];const role=id.startsWith('size')?'slot capacity':id.startsWith('used')?'slot payload':'physical slot';return binding([`allocator:slot:${j}`],role,'This stable slot has its own capacity, payload and free/assigned membership.',['allocator:capacity','allocator:partition','operation:sum']);}
 if(buddy&&(/^(?:buddy|xor|alignment|round-request|split-status)/.test(id)||/^\d+$/.test(id)||/^t\d+$/.test(id))){
  if(/^t?\d+$/.test(id)){const start=id.replace(/^t/,'');return binding([`allocator:block:${start}`],'buddy block','This is a fixed-size aligned interval at the displayed offset.',['buddy:offset','buddy:order','buddy:size',`allocator:offset:${start}`]);}
  return binding([`buddy:display:${id}`],'buddy relation','XOR flips the size bit; equal size, alignment and free status are required before merging.',['buddy:offset','buddy:order','buddy:size','allocator:alignment','allocator:request']);
 }
 if(id==='account'||id==='inventory')return binding(['allocator:accounting'],'capacity accounting','Live/reserved and free bytes partition the arena.',['allocator:capacity','allocator:partition','operation:sum']);
 if(id==='end'||id==='axis')return binding(['allocator:address-axis'],'arena address scale','Addresses identify positions, not sizes.',['allocator:start','allocator:capacity',buddy?'buddy:offset':null]);
 if(token!==null&&/^[A-Z]$/.test(token)&&nodes.some(n=>/^block\d+label$/.test(n.id)&&n.text===token))return memberConcept('object:'+token,'allocation identity',`${token} names one live allocation; its name is not its address or size.`);
 return null;
}
function treeBinding(c){
 const {id,token,physical,order,nodes,state,expression}=c;const object=graphObject(c);
 if(order===144&&(token==='P'||token==='Q'))return memberConcept('pointer:'+token,'pointer register',`${token} holds an object identity or null, not the object's payload.`);
 if(order===125&&['A','a','F','f'].includes(token))return memberConcept(token==='A'||token==='a'?'tree:rooted-classes':'tree:free-classes','tree-shape count','Rooted and free isomorphism classes have different counting roles.');
 if(order===126&&token==='n')return memberConcept('graph:vertices','labeled vertex count','n counts labeled vertices; their names are distinct from degree values.');
 if((order===134||order===135)&&/^A\d*$/.test(token??''))return memberConcept('qualification:name','requested qualifier name','The requested name sequence is matched against candidate ancestor names.');
 if(order===135&&/^d[j0-9]*$/.test(token??''))return memberConcept('qualification:ancestry','ancestor steps','This counts steps outward along the candidate ancestor chain.');
 if(order===136&&token==='p')return memberConcept('record:relative-path','relative field path','p is the containing-name path used to compare corresponding fields.');
 if(object){
  const memberships=['graph:vertices'];if(order===125)memberships.push('tree:rooted-classes','tree:free-classes');if(order===134||order===135)memberships.push('qualification:name','qualification:ancestry');if(order===144){const footer=String(nodes.find(n=>n.id==='footer')?.text??'');for(const pointer of ['P','Q'])if(new RegExp('\\b'+pointer+'='+object+'(?:;|\\s|$)').test(footer))memberships.push('pointer:'+pointer);}if(/^root/.test(id)||nodes.some(n=>n.id==='root'+object))memberships.push('graph:roots');
  if(c.node?.role==='result')memberships.push('graph:reachable');if(c.node?.role==='error')memberships.push('graph:garbage');
  if(token!==null&&isNumber(token)&&String(c.node?.text??'').includes(':'))return binding([`graph:reference-count:${object}`],'reference count','This is the count on this object, not its identity.',[`object:${object}`,'graph:reference-count']);
  return binding([`object:${object}`],'object identity',`${object} identifies this object, irrespective of its contents or location.`,memberships);
 }
 if(token!==null&&(!isNumber(token)||(c.offset>=0&&/\b(?:vertex|node|object|label)\s*$/i.test(expression.slice(0,c.offset))))&&nodes.some(n=>n.id==='v'+token&&n.type==='circle'))return memberConcept('object:'+token,'object identity',`${token} names this particular vertex/object.`);
 if(token!==null&&!isNumber(token)){
  if(token==='Σ'||token==='∑')return memberConcept('operation:sum','summation','Add the displayed depth, weight or case contributions.');
  const concepts={I:['tree:internal-depth','internal path length','I adds depths of internal (circle) vertices.'],E:['tree:external-depth','external path length','E adds depths of external/null (square) positions.'],d:['tree:depth','depth','d counts edges from the root, not node identity or weight.'],n:['tree:count','internal node count','n counts internal vertices.'],W:['tree:weighted-cost','weighted path length','W sums weight times depth over leaves.'],w:['tree:weight','leaf weight','w is a leaf weight, separate from its depth.'],R:['graph:reachable','reachable set','R contains exactly the objects reachable from roots.'],V:['graph:vertices','allocated vertices','V is the set of graph objects.'],G:['graph:garbage','unreachable garbage','G consists of allocated objects outside the reachable set.'],H:['graph:frontier-capacity','frontier capacity','H bounds the number of retained work items.']};
  if(concepts[token]&&((['I','E','d','n','W','w'].includes(token)&&order>=124&&order<=129)||(['R','V','G','H'].includes(token)&&order>=130&&order<=133))){const [key,role,description]=concepts[token];return memberConcept(key,role,description);}
 }
 let m=id.match(/^(r[01]*)(t)?$/);
 if(m&&(order===127||order===128)){const key=m[1],shape=nodes.find(n=>n.id===key),external=shape?.type==='rect';return binding([`tree:node:${key}`],external?'external position':'internal vertex','Its displayed number is depth; the stable path identifies the vertex.',[external?'tree:external-depth':'tree:internal-depth','tree:depth','tree:count','operation:sum']);}
 if(order===129){
  m=id.match(/^(?:weighted-leaf-|weight-before-|depth-before-|cost-before-)(\d+)$/);
  if(m){const leaf=m[1],role=id.startsWith('depth')?'leaf depth':id.startsWith('cost')?'weighted contribution':'leaf weight';return binding([`tree:leaf:${leaf}`],role,'This particular leaf contributes its weight times its depth.',['tree:weight','tree:depth','tree:weighted-cost','operation:sum']);}
  if(/^tree\d/.test(id))return binding([`tree:component:${id.replace(/(?:depth|t)$/,'')}`],'Huffman subtree','This component contains weighted leaves; a new parent raises their depths by one.',['tree:depth','tree:weight','tree:weighted-cost','operation:sum']);
  if(/cost|selected-weights|depth-step/.test(id))return binding([`tree:cost-display:${id}`],'weighted-depth calculation','Merge cost is the sum of weights whose leaves gain one level.',['tree:weighted-cost','tree:weight','tree:depth','operation:sum']);
 }
 if(order===124){
  if(/^catalog-([01])-/.test(id)){const side=id.match(/^catalog-([01])-/)[1];return binding([`catalan:shape:${id}`],'ordered subtree alternative','This is one concrete subtree shape; empty child positions are counted explicitly.',[`catalan:${side==='0'?'left':'right'}-choices`,'catalan:choices','tree:count']);}
  if(/^pair/.test(id))return binding([`catalan:${id}`],'ordered subtree pair','One cell pairs a left choice with a right choice.',['catalan:choices','operation:sum']);
  if(token==='C'||/^C\d+$/.test(token??''))return memberConcept('catalan:choices','Catalan count','C counts the distinct ordered subtree shapes of the specified size.');
  if(/catalog|product|total|leftlabel|rightlabel/.test(id))return binding([`catalan:display:${id}`],'Catalan construction','Enumerate choices, pair them and add disjoint root-size cases.',['catalan:choices','tree:count','operation:sum']);
 }
 if(id==='sum'||/increment|depth-contribution|role-key/.test(id))return binding([`tree:depth-display:${id}`],'path-length accounting','Add the depth contributions belonging to the internal and external positions.',['tree:depth','tree:internal-depth','tree:external-depth','tree:count','operation:sum']);
 if(/^e[A-Za-z0-9]+-\d+$/.test(id))return binding([`graph-edge:${id}`],'stored graph link','This edge belongs to its source object and its particular child/link slot.',['graph:edges','graph:reachable']);
 if(/^qualifier-(?:cursor|route|status)-/.test(id))return binding(['qualification:candidate:'+id.replace(/^qualifier-(?:cursor|route|status)-/,'')],'qualification candidate','This candidate follows ancestors in the requested qualifier order.',['qualification:name','qualification:ancestry']);
 if(order===136&&/^(?:[01]-|t[01]-|left$|right$|paired-path|relative-path|match$)/.test(id))return binding(['record:item:'+id.replace(/^t([01]-)/,'$1')],'corresponding record field','Field identity is determined by its relative qualified path.',['record:relative-path']);
 if(/work-|rescan-/.test(id))return binding([`graph:work:${id}`],'pending or completed work','This marker identifies the processed object or an obligation recovered by scanning.',['graph:reachable','graph:frontier-capacity']);
 if(id==='footer'&&order>=130&&order<=133)return binding(['graph:status'],'reachability status','This reports the reachable set, pending frontier or reclaimed objects.',['graph:reachable','graph:frontier-capacity','graph:garbage']);
 return null;
}
/** Return null for unknown semantics so the conservative occurrence-local fallback wins. */
function familyBinding(element,context={}){
 const c=info(element,context);if(!Number.isFinite(c.order)||c.order<21)return null;
 if(c.order>=88&&c.order<=122)return structureSymbolBinding(element,context);
 if(c.order>=65&&c.order<=87){
  const process=processBinding(c);if(process)return process;
  if([65,66,67,68,70,71,72,77,82,83,84].includes(c.order)){const result=mixBinding(c);if(result)return result;}
  if(c.order===76){let m=c.id.match(/^signed-term-(?:value-)?(\d+)$/);if(m)return binding([`inclusion:term:${m[1]}`],'signed correction','This particular intersection correction contributes to the partial total.',['operation:sum','inclusion:terms']);if(c.token==='Σ'||c.token==='∑')return memberConcept('operation:sum','inclusion-exclusion sum','Add signed intersection counts; alternating signs cancel multiply counted objects.');if(c.token==='k')return memberConcept('inclusion:order','intersection order','k selects how many fixed-label conditions are imposed.');if(/fixed-label|fixed-subset/.test(c.id))return binding([`inclusion:${c.id.replace('fixed-label-value-','fixed-label-')}`],'fixed-label condition','This identifies a fixed-label condition or its selected intersection.',['inclusion:order','inclusion:terms']);if(/^card-[12]|^val-[12]|joined-total/.test(c.id))return binding([`inclusion:${c.id}`],'correction or partial total','The correction is added to the current partial total.',['operation:sum','inclusion:terms']);}
  if(c.order===81){if(c.token==='σ')return memberConcept('interpreter:stack','object stack','σ is the stack sequence.');if(c.token==='pc'||c.token==='PC')return memberConcept('interpreter:pc','object program counter','The object PC chooses the next object-language instruction.');if(/^stack-(?:token|value)-/.test(c.id)){const key=c.id.replace(/^stack-(?:token|value)-/,'');return binding([`interpreter:operand:${key}`],'stack operand','This operand retains identity while it moves or is consumed.',['interpreter:stack']);}if(/object-(?:code|fetch)/.test(c.id))return binding([`interpreter:${c.id}`],'object instruction','This is an object-code location, separate from an operand value.',['interpreter:pc']);}
  return null;
 }
 if(c.order>=137&&c.order<=143)return allocatorBinding(c);
 if(c.order>=123&&c.order<=136||c.order===144)return treeBinding(c);
 return null;
}

const reverseIndexes=new WeakMap();
/** Passive reverse references make a selected object illuminate the source symbol
 * naming its role. They do not add any primary keys or equate printed values. */
function reverseReferences(c,context,selectionKeys){
 if(!c.state||typeof c.state!=='object')return [];
 let index=reverseIndexes.get(c.state);
 if(!index){
  index=new Map();
  for(const node of c.nodes){
   const physical={getAttribute:name=>name==='data-diagram-node'?node.id:null,closest:()=>null,textContent:node.text??''};
   const b=familyBinding(physical,context);if(!b)continue;
   for(const role of [...b.keys,...(b.memberships??[])]){if(!index.has(role))index.set(role,new Set());for(const key of b.keys)index.get(role).add(key);}
  }
  reverseIndexes.set(c.state,index);
 }
 return unique(selectionKeys.flatMap(key=>[...(index.get(key)??[])]));
}
export function fullBookSymbolBinding(element,context={}){
 const c=info(element,context),answer=familyBinding(element,context);
 if(!answer)return null;
 if(isNumber(c.token)&&c.node&&String(c.node.text??'').trim()!==c.raw){
  const aggregate=/^(?:mix:display:|tree:depth-display:|tree:cost-display:|buddy:display:|allocator:accounting$|catalan:display:|graph:status$)/;
  if(answer.keys.some(key=>aggregate.test(key)))return null;
 }
 if(c.token!==null&&!isNumber(c.token))answer.memberships=unique([...(answer.memberships??[]),...reverseReferences(c,context,answer.keys)]);
 return answer;
}
