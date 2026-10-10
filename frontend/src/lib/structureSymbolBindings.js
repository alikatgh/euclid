/** D/E semantic bindings. Identity comes from an authored object/field or trace role,
 * never from equal numerical values. All keys are local; the caller supplies scope. */
const uniq=a=>[...new Set(a.filter(Boolean))];
const bind=(keys,role,description,memberships=[])=>({keys:uniq(keys),memberships:uniq(memberships),role,description});
const attr=(e,n)=>e?.getAttribute?.(n)??null;
const object=id=>`object:${id}`;
const number=s=>/^[-−]?\d+(?:\.\d+)?$/.test(String(s??''));
const normalize=s=>String(s??'').replace(/[₀₁₂₃₄₅₆₇₈₉]/g,c=>'₀₁₂₃₄₅₆₇₈₉'.indexOf(c));
const operation={'Σ':'sum','∑':'sum','+':'addition','−':'subtraction','-':'subtraction','×':'multiplication','·':'multiplication','*':'multiplication','/':'division','÷':'division','^':'power','=':'equality','≠':'inequality','→':'mapping','←':'assignment','∅':'empty'};
const cache=new WeakMap();
function diagramIdentity(id,d){
 let m;
 if((m=id.match(/^copy-(?:node|label)-(.+)$/)))return d.map?.[m[1]]??`copy:${m[1]}`;
 if((m=id.match(/^derived-(?:node|label)-(.+)$/)))return `derived:${m[1]}`;
 if((m=id.match(/^(?:node|label)-(.+)$/)))return m[1];
 if((m=id.match(/^card-(.+?)(?:-label)?$/)))return m[1];
 if((m=id.match(/^(?:vertex-label|vertex|vlabel|task-token-label|task-token|entity-label|entity)-(.+)$/)))return m[1];
 if((m=id.match(/^(stack|queue|deque)-(.+?)(?:-label)?$/)))return `${m[1]}:${m[2]}`;
 if((m=id.match(/^pool-slot-(\d+)(?:-label)?$/)))return `pool:${m[1]}`;
 if((m=id.match(/^(cell-\d+-\d+)(?:-value)?$/)))return m[1];
 if((m=id.match(/^(c-?\d+--?\d+)(?:-label|-offset)?$/)))return m[1];
 if(id==='header'||id==='header-label')return 'H';
 return null;
}
function index(state,d){
 if(cache.has(state))return cache.get(state);
 const nodes=state.diagram?.nodes??[],byId=new Map(nodes.map(n=>[n.id,n])),ids=new Set();
 for(const n of nodes){const id=diagramIdentity(n.id,d);if(id!==null&&(n.type==='circle'||n.type==='rect'))ids.add(id);}
 const result={nodes,byId,ids};cache.set(state,result);return result;
}
function info(el,context){
 const visual=context?.frame?.visual??context?.visual??{},state=visual.state??{},d=state.data??state.evidence??{};
 const idx=index(state,d),group=el?.closest?.('[data-diagram-node]');
 const id=attr(el,'data-diagram-node')??attr(group,'data-diagram-node')??'';
 const raw=attr(el,'data-math-token')??attr(el,'data-math-value'),token=raw===null?null:normalize(raw);
 const expression=attr(el,'data-math-expression')??idx.byId.get(id)?.text??el?.textContent??'';
 return {el,visual,state,d,...idx,id,raw,token,expression,physical:raw===null,offset:Number(attr(el,'data-math-offset')??-1),script:attr(el,'data-math-script'),term:attr(el,'data-math-term'),order:Number(visual.order??context.order),model:visual.model??{}};
}
function numericOrdinal(c){
 const matches=[...c.expression.matchAll(/[-−]?\d+(?:\.\d+)?/g)];
 // SVG/prose offsets are character offsets. KaTeX offsets are not, so do not guess.
 if(c.el?.closest?.('.katex-html'))return -1;
 return matches.findIndex(m=>c.offset>=m.index&&c.offset<m.index+m[0].length);
}
function objBinding(c,id){
 const memberships=[`ast:value:${id}`,`ast:exponent:${id}`,`ast:operator:${id}`,`node-value:${id}`,`node-degree:${id}`,`node-depth:${id}`,`node-address:${id}`,`node-indegree:${id}`];
 const d=c.d;
 const astLabel=c.byId.get(`${id.startsWith('derived:')?'derived-':''}label-${id.replace(/^derived:/,'')}`)?.text;
 if(/^[a-z]$/.test(astLabel??'')&&/^a\d*$/.test(id.replace(/^derived:/,'')))memberships.push(`variable:${astLabel}`);
 if(d.p===id)memberships.push('pointer:P');
 if(d.node===id||d.cursor===id||d.active===id)memberships.push('pointer:cursor');
 if(d.root===id)memberships.push('tree:root');
 for(const name of ['pre','in','post'])if(d.outputs?.[name]?.includes(id))memberships.push(`traversal:${name}`);
 for(const name of ['head','tail'])if(d[name]===id)memberships.push(`pointer:${name}`);
 if(d.links&&!Array.isArray(d.links))for(const [source,z] of Object.entries(d.links)){
  if(z===id)memberships.push(`pointer:next:${source}`);
  if(z&&typeof z==='object')for(const k of ['L','R','LEFT','RIGHT','UP','DOWN','next','prev'])if(z[k]===id)memberships.push(`pointer:${k}:${source}`);
 }
 for(const [i,e] of (d.arcs??d.edges??c.model.arcs??c.model.edges??[]).entries())if(e.includes(id))memberships.push(`graph-edge:e${i}`);
 return bind([object(id)],'node identity',`${id} identifies this particular node. Its stored value, address, degree and links are separate roles.`,memberships);
}
const field=(id,key,role,description,extra=[])=>bind([key],role,description,[object(id),...extra]);
function astBinding(c,identity){
 const path=identity?.replace(/^derived:/,'');if(!path||!/^a\d*$/.test(path)&&!/^D-a\d*$/.test(path))return null;
 const token=c.token;
 if(c.physical)return objBinding(c,identity);
 if(token&&operation[token])return field(identity,`ast:operator:${identity}`,'expression-tree operator',`${token} is the operator at this expression node; its ordered children are its operands.`,[`operation:${operation[token]}`]);
 const label=c.byId.get(c.id)?.text??'';
 const parentId=path.slice(0,-1),derived=identity.startsWith('derived:')?'derived-':'';
 const parentLabel=c.byId.get(`${derived}label-${parentId}`)?.text;
 const exponent=c.script==='exponent'||(path.endsWith('1')&&parentLabel==='^')||(c.offset>0&&c.expression[c.offset-1]==='^');
 if(number(token))return field(identity,exponent?`ast:exponent:${identity}`:`ast:value:${identity}`,exponent?'power exponent':'constant occurrence',`${token} is ${exponent?'the exponent':'a constant'} at expression node ${identity}. Equal constants in other nodes are separate occurrences.`);
 if(token&&/^[a-z]$/.test(token)&&(!/^(original|new)/.test(label)||c.id.startsWith('label-'))){
  return bind([`variable:${token}`],'expression variable',`${token} is this expression's variable; its several occurrences refer to the same variable.`,[object(identity)]);
 }
 return null;
}
function weightedFold(c){
 const d=c.d;if(!Array.isArray(d.childIds)||!Array.isArray(d.weights))return null;
 const parent=d.node;let m=c.id.match(/^fold-(value|slot|product)-(.+)$/);
 if(m){
  const child=m[2],i=d.childIds.indexOf(child);if(i<0)return null;
  const slot=`child-slot:${parent}:${i+1}`,value=`node-value:${child}`,product=`fold-product:${parent}:${child}`;
  if(c.physical)return bind([object(child)],'ordered child contribution',`Child ${child} occupies slot ${i+1}; its value ${d.children[i]} is multiplied by weight ${d.weights[i]}.`,[slot,value,product,'tree:child-index','operation:sum','operation:weighted-fold']);
  if(c.token===child)return objBinding(c,child);
  if(m[1]==='slot'&&number(c.token))return field(child,slot,'ordered child slot',`${c.token} is the child position and its weight, not the child's value.`,['tree:child-index']);
  if(m[1]==='product'){
   if(operation[c.token])return bind([`fold-operation:${parent}:${child}`],'weight multiplication',`Multiply ${child}'s value by its ordered slot number before summing.`,['operation:multiplication','operation:weighted-fold']);
   const ordinal=numericOrdinal(c);
   if(number(c.token)&&ordinal>=0){const key=ordinal===0?slot:ordinal===1?value:product;const role=ordinal===0?'slot weight':ordinal===1?'child subtree value':'weighted contribution';return field(child,key,role,`${c.token} is the ${role} for child ${child} in slot ${i+1}.`,ordinal===0?['tree:child-index']:ordinal===2?['operation:sum']:[]);}
  }
 }
 if(c.id==='weighted-total'){
  if(c.physical)return field(parent,`node-value:${parent}`,'fold result',`The sum of weighted child contributions is f(${parent})=${d.value}.`,['operation:sum']);
  if(c.token==='+')return bind(['operation:sum'],'sum weighted contributions','Add the weighted contributions, after multiplying each child value by its slot.');
  const i=numericOrdinal(c);if(number(c.token)&&i>=0)return i<d.childIds.length?field(d.childIds[i],`fold-product:${parent}:${d.childIds[i]}`,'weighted contribution',`${c.token} is the contribution of child ${d.childIds[i]}, not its unweighted value.`,['operation:sum']):field(parent,`node-value:${parent}`,'fold result',`${c.token} is the new value f(${parent}) after all weighted contributions are added.`);
 }
 if(c.id==='leaf-value'&&number(c.token))return field(parent,`node-value:${parent}`,'supplied leaf value',`${c.token} is the value assigned to leaf ${parent}.`);
 if(c.token==='i')return bind(['tree:child-index'],'ordered child index','i identifies a child slot and supplies that slot’s weight. It is not a child’s stored value.');
 if(c.token==='Σ'||c.token==='∑')return bind(['operation:sum'],'sum weighted contributions','Sum the weighted child contributions, keeping the slot order.');
 return null;
}
function pointer(c){
 const d=c.d;let m;
 if(c.id==='current-p'){
  if(c.token&&c.token!=='P'&&c.ids.has(c.token))return objBinding(c,c.token);
  return bind(['pointer:P'],'current subtree pointer',`P currently ${d.p==null?'is null':`points to node ${d.p}`}. P is a pointer variable, not a node named P.`);
 }
 if(c.id==='walker')return bind(['pointer:cursor'],'traversal cursor',`The cursor is at ${d.node??d.cursor??d.active??d.p??'the current control position'}.`);
 if((m=c.id.match(/^(?:selected|tag)-([LR])(?:-head)?$/))&&d.node&&d.links?.[d.node]){
  const side=m[1],owner=d.node,z=d.links[owner],target=z[side],key=`pointer:${side}:${owner}`;
  if(c.token&&c.token===String(target)&&c.token!==side)return objBinding(c,target);
  if(number(c.token))return field(owner,`thread-tag:${side}:${owner}`,'link tag',`${c.token} tags ${owner}'s ${side} link: 0 means a real child, 1 means a navigation thread.`,[key]);
  return bind([key],'tagged tree link',`${owner}.${side} points to ${target}; its tag says ${z[side+'T']?'thread':'child'}.`,[object(owner),object(target)]);
 }
 if((m=c.id.match(/^(next|prev|field)-(.+?)(?:-tip|-end|-end-tip|-null)?$/))&&d.links&&!Array.isArray(d.links)){
  const owner=m[2],which=m[1]==='field'?'next':m[1],z=d.links[owner];if(z===undefined)return null;
  const target=z&&typeof z==='object'?z[which]:which==='next'?z:null;const key=`pointer:${which}:${owner}`;
  return bind([key,...(number(c.token)&&target!=null?[`node-address:${target}`]:[])],`${which} link`,`${owner}'s ${which} field ${target==null?'is null':`names node ${target}`}. It is not ${owner}'s stored value.`,[object(owner),target==null?'':object(target)]);
 }
 if((m=c.id.match(/^(head|tail)(?:-pointer|-pointer-tip)?$/))){
  const name=m[1];if(c.token&&c.ids.has(c.token))return objBinding(c,c.token);
  return bind([`pointer:${name}`],`${name} pointer`,`${name} currently names ${d[name]??'null'}.`,d[name]!=null?[object(d[name])]:[]);
 }
 if(c.token==='P'&&c.order>=109&&c.order<=111&&!c.id)return bind(['pointer:P'],'tree pointer','P is the traversal/link-operation pointer. Follow it to its current target; do not confuse its name with a node label.');
 return null;
}
function edgeBinding(c){
 let m=c.id.match(/^arc(?:-label)?-(\d+)(?:-head)?$/);
 if(m){const i=Number(m[1]),edge=(c.d.arcs??c.d.edges??c.model.arcs??c.model.edges??[])[i],key=`graph-edge:e${i}`;
  if(number(c.token)&&c.expression.includes(':')&&c.offset>c.expression.indexOf(':'))return bind([`graph-edge-count:e${i}`],'edge traversal count',`${c.token} is the count on edge e${i}; another edge with the same count remains a different edge.`,[key]);
  return bind([key],'edge identity',`e${i}${edge?` connects ${edge[0]} to ${edge[1]}`:''}. Parallel arcs have separate identities.`,[...(edge??[]).map(object),`graph-edge-count:e${i}`]);}
 const term=normalize(c.term??c.token??'');m=term.match(/^e_?(\d+)$/);
 if(!m&&!c.id&&c.script==='subscript'&&number(c.token)&&/e[_\{]/.test(c.expression))m=[null,c.token];
 if(m)return bind([`graph-edge:e${m[1]}`],'edge identity',`The subscript identifies edge e${m[1]}, not a count or value.`);
 m=c.id.match(/^(?:edge|child|sibling|layer)-(.+?)(?:-head|-tip)?$/);
 if(m){
  const pair=[...(c.d.links&&Array.isArray(c.d.links)?c.d.links:[]),...(c.d.edges??[]),...(c.d.arcs??[])].find(([a,b])=>`${a}-${b}`===m[1]||`${a}${b}`===m[1]);
  const endpoints=pair??[...c.ids].flatMap(a=>[...c.ids].filter(b=>`${a}-${b}`===m[1]||`${a}${b}`===m[1]).map(b=>[a,b]))[0];
  if(endpoints)return bind([`structure-edge:${endpoints[0]}:${endpoints[1]}`],'structural link',`This link relates node ${endpoints[0]} to node ${endpoints[1]}.`,endpoints.map(object));
 }
 return null;
}
function arrayBinding(c){
 const d=c.d;let m;
 if((m=c.id.match(/^(slot|content|token|index|address)-(\d+)$/))&&Array.isArray(d.cells)&&(!d.cells.length||typeof d.cells[0]!=='object'||d.cells[0]===null)){
  const i=m[2],key=`array-cell:${i}`,role={slot:'array cell',content:'cell value',token:'cell value',index:'cell index',address:'cell address'}[m[1]];
  const specific=m[1]==='slot'?key:`array-${m[1]==='content'||m[1]==='token'?'value':m[1]}:${i}`;
  return bind([specific],role,`${role} of cell ${i}. An index, address and stored value have different roles even when their numerals agree.`,[key,`array-value:${i}`,`array-index:${i}`,`array-address:${i}`].filter(x=>m[1]==='slot'||x===key));
 }
 const roles={
  'top-count':['stack:top','stack size','T counts occupied stack cells; it is not a stored item.'],
  'top-pointer':['stack:top','stack boundary','This pointer marks the next free stack position.'],
  'count':['queue:count','queue occupancy','The count records how many queue cells are occupied.'],
  'head-name':['pointer:h','queue head index','h is the next removal index in this circular queue.'],
  'head-physical':['pointer:h','queue head index','h identifies the next cell to remove.'],
  'tail-name':['pointer:t','queue tail index','t is the next insertion index in this circular queue.'],
  'tail-physical':['pointer:t','queue tail index','t identifies the next cell to fill.']
 };
 const r=roles[c.id.replace(/-tip$/,'')];if(r)return bind([r[0]],r[1],r[2]);
 if(c.id==='pointers'&&['h','t'].includes(c.token))return bind([`pointer:${c.token}`],'circular index',`${c.token} is a queue index, not a payload value.`);
 if(c.id==='pointers'&&number(c.token)){const i=numericOrdinal(c);if(i===0||i===1)return bind([i===0?'pointer:h':'pointer:t'],'circular index',`${c.token} is the current ${i===0?'head':'tail'} index.`);}
 if(c.id==='gap'){
  const roles=['stack:left-boundary','stack:right-boundary','storage:free-count'];const i=numericOrdinal(c);
  if(number(c.token)&&i>=0)return bind([roles[i]],'storage boundary/count','L, R and free capacity are separate quantities; their equal values are not interchangeable.');
  if(c.token==='L'||c.token==='R')return bind([c.token==='L'?roles[0]:roles[1]],'stack boundary',`${c.token} marks one stack’s boundary.`);
 }
 return null;
}
function sparseRoles(c){
 if(c.order===99){
  const m=c.id.match(/^([PQ])-(-?\d+|H)(?:-label)?$/);
  if(m){const id=`${m[1]}:${m[2]}`,coefficient=`polynomial:coefficient:${id}`,exponent=`polynomial:exponent:${id}`;
   if(c.physical)return bind([object(id)],'sparse polynomial term','This term has its own coefficient and exponent.',[coefficient,exponent,`polynomial:${m[1]}`]);
   if(c.token==='x')return bind(['variable:x'],'polynomial variable','x is the indeterminate shared by these terms.',[object(id)]);
   if(number(c.token)){const exp=c.script==='exponent'||c.offset>c.expression.indexOf('^')&&c.expression.includes('^');return field(id,exp?exponent:coefficient,exp?'term exponent':'term coefficient','Coefficient and exponent are different fields, even when their numbers agree.');}
   return bind([object(id)],'term identity','This is one term record in the sparse polynomial.');
  }
  if(['P','Q'].includes(c.token))return bind([`polynomial:${c.token}`],'polynomial identity',`${c.token} identifies this input polynomial.`);
 }
 if(c.order!==105)return null;
 const cells=c.d.operandCells??{},m=c.id.match(/^(old-cell|old-value|current-value)-(\d+)-(\d+)$/);
 if(m){const id=`${m[1].startsWith('old')?'old-':''}cell-${m[2]}-${m[3]}`,operand=Object.entries(cells).find(([,p])=>p[0]===Number(m[2])&&p[1]===Number(m[3]))?.[0];
  const key=m[1].startsWith('old')&&operand?`pivot:operand:${operand}`:`node-value:${id}`;
  return c.physical?bind([object(id)],'matrix cell identity','Old source cells and updated cells retain distinct value roles.',[key]):field(id,key,'matrix entry value','This operand comes from the specified matrix cell; another equal entry is not the same operand.');
 }
 let operand=['a','b','c','d'].includes(c.token)?c.token:null;
 if(number(c.token)){
  const roles={'operand-row':['a','b'],'operand-column':['c','d'],'actual-substitution':['d','b','c','a']};operand=roles[c.id]?.[numericOrdinal(c)]??null;
 }
 if(operand&&cells[operand])return bind([`pivot:operand:${operand}`],'old pivot operand',`${operand} is the old value at cell (${cells[operand].join(',')}); read it before updating the target.`,[object(`old-cell-${cells[operand].join('-')}`)]);
 return null;
}
function coordinates(c){
 if(c.order!==103)return null;
 const d=c.d, ordinal=numericOrdinal(c);
 const roles={
  'row-width':['array:columns'], 'lower-row':['array:lower-row'], 'lower-column':['array:lower-column'],
  'memory-inputs':['array:base','array:stride'],
  'row-subtraction':['array:row-label','array:lower-row','array:relative-row'],
  'column-subtraction':['array:column-label','array:lower-column','array:relative-column'],
  'whole-row-count':['array:relative-row','array:columns','array:row-contribution'],
  'within-count':['array:row-contribution','array:relative-column','array:offset'],
  'address-inputs':['array:base','array:stride','array:offset'],
  'physical-address':['array:base','array:stride','array:offset','array:address'],
  'selection-name':['array:row-label','array:column-label'],
  'flatten-count':['array:row-label','array:column-label','array:relative-row','array:relative-column','array:relative-row','array:columns','array:relative-column','array:offset'],
  'column-count':['array:relative-column','array:rows','array:relative-row','array:offset'],
 };
 const keys=roles[c.id];
 if(keys&&number(c.token)&&ordinal>=0&&keys[ordinal])return bind([keys[ordinal]],keys[ordinal].slice(6).replaceAll('-',' '),'This numeral has its own array-coordinate role; equal labels, offsets and cell sizes remain distinct.');
 const symbols={i:'row-label',j:'column-label',r:'relative-row',c:'relative-column',C:'columns',R:'rows',b:'base',s:'stride'};
 if(symbols[c.token]&&(keys||!c.id))return bind([`array:${symbols[c.token]}`],'array coordinate or layout parameter',`${c.token} is the ${symbols[c.token].replaceAll('-',' ')} in this array mapping.`);
 if(c.physical&&keys)return bind(keys,'array mapping step','This step converts labels to relative coordinates, then a cell offset, then a physical address.');
 const m=c.id.match(/^(c-?\d+--?\d+)-(label|offset)$/);
 if(m){const cell=d.cells?.find(x=>x.id===m[1]);if(!cell)return null;
  if(m[2]==='offset')return field(cell.id,`array-cell-offset:${cell.id}`,'cell offset','This offset identifies the selected cell in sequential storage.',cell.i===d.selected?.[0]&&cell.j===d.selected?.[1]?['array:offset']:[]);
  if(number(c.token)&&ordinal>=0){const key=ordinal===0?'row-label':'column-label';return field(cell.id,`array-cell-${key}:${cell.id}`,key,'This number labels one coordinate of this particular cell.',cell.i===d.selected?.[0]&&cell.j===d.selected?.[1]?[`array:${key}`]:[]);}
 }
 return null;
}
function derivativeRoles(c){
 if(c.order!==114)return null;
 const names=c.d.identities;
 const base=c.token?.replace(/′$/,'');
 if(names&&['u','v'].includes(base)){
  const prime=/′$/.test(c.token)||c.script==='superscript'||c.script==='prime'||/[′']/.test(c.term??'');
  const id=names[(prime?'d':'')+base];if(id)return objBinding(c,id);
 }
 if(/^product-op-/.test(c.id))return bind([`derivative:${c.id}`],'product-rule branch','One product-rule branch differentiates one factor while preserving the other factor.', ['operation:multiplication']);
 if(/^sum-op-/.test(c.id))return bind(['derivative:product-rule-sum'],'product-rule sum','Add the two distinct branches u′v and uv′.', ['operation:sum']);
 if(c.id==='chain-factor')return bind(['derivative:inner'],'chain-rule inner derivative','This factor is the derivative of the inner expression, even when its value is one.');
 return null;
}
function polynomialRoles(c){
 if(c.order!==118)return null;
 let m=c.id.match(/^address-(r\d+)$/);
 if(m&&c.d.nodes?.[m[1]]){
  const id=m[1];if(c.physical)return bind([object(id)],'polynomial node fields','The side label records this persistent node’s coefficient/variable and exponent.', [`polynomial:exponent:${id}`,`polynomial:coefficient:${id}`]);
  if(c.token==='x'||c.token==='y')return field(id,`polynomial:variable:${c.token}`,'polynomial variable','The variable at this polynomial level is distinct from its coefficient and exponent.');
  if(c.token==='e'||number(c.token)&&/e\s*$/.test(c.expression.slice(0,c.offset)))return field(id,`polynomial:exponent:${id}`,'term exponent','This exponent belongs to this specific polynomial term.');
  if(number(c.token))return field(id,`polynomial:coefficient:${id}`,'term coefficient','This coefficient is stored at this specific polynomial node.');
  return objBinding(c,id);
 }
 if((m=c.id.match(/^(up|ring)-(r\d+)(?:-head)?$/)))return bind([`pointer:${m[1]==='up'?'UP':'RIGHT'}:${m[2]}`],'polynomial navigation link','This navigation pointer preserves the identity of the linked polynomial node.');
 return null;
}
function graphCounts(c){
 if(c.order<119||c.order>122)return null;
 if(c.id==='graph-counts'||c.id==='candidate'){
  const before=c.expression.slice(0,c.offset);const roles=[['cycle rank', 'graph:cycle-rank'],['components','graph:component-count'],['edges','graph:edge-count'],['n=','graph:vertex-count'],['m=','graph:edge-count'],['c=','graph:component-count']];
  let match=roles.map(([word,key])=>({at:before.lastIndexOf(word),key})).sort((a,b)=>b.at-a.at)[0];
  if(number(c.token)&&match?.at>=0)return bind([match.key],'graph count',`${c.token} is the ${match.key.split(':')[1].replaceAll('-',' ')}, not a node or edge identity.`);
 }
 if(!c.id&&['n','m','c'].includes(c.token))return bind([{n:'graph:vertex-count',m:'graph:edge-count',c:'graph:component-count'}[c.token]],'graph size parameter',`${c.token} counts ${c.token==='n'?'vertices':c.token==='m'?'edge identities':'connected components'}.`);
 if(c.order===120&&!c.id&&c.token==='B'&&/B[fcp]|incidence|column|matrix/.test(c.expression))return bind(['graph:incidence-matrix'],'incidence matrix','B is the signed vertex–edge incidence matrix, not the node named B.');
 if(c.id==='root-flag'||c.id==='root-flag-label')return c.token&&c.ids.has(c.token)?objBinding(c,c.token):bind(['tree:root'],'chosen root',`The distinguished root is ${c.d.root??'the flagged vertex'}.`);
 return null;
}
function proseArticle(c){
 if(c.id||c.token!=='a'&&c.token!=='A')return false;
 const mathematical=/\\|[=+×^_]|D\(|\ba\s*\(/.test(c.expression);
 if(c.token==='a')return !mathematical;
 if(c.expression.trim()==='A')return false;
 const at=c.offset>=0?c.offset:c.expression.indexOf('A');
 return /^\s+(?:tree|binary|rooted|root|node|forest|graph|path|cycle|list|pointer|stack|queue|single|finite|shared|new|valid|different|complete|connected|directed|child|function|value|polynomial|variable|constant|representation|copy|leaf|loop|trail|record)\b/i.test(c.expression.slice(at+1));
}
/** Return null for unrelated material; no mutation and no scope-prefixing. */
export function structureSymbolBinding(element,context={}){
 const c=info(element,context);if(!(c.order>=88&&c.order<=122))return null;
 if(proseArticle(c))return null;
 let answer=sparseRoles(c)??coordinates(c)??derivativeRoles(c)??polynomialRoles(c)??weightedFold(c)??pointer(c)??arrayBinding(c)??graphCounts(c)??edgeBinding(c);if(answer)return answer;
 const identity=diagramIdentity(c.id,c.d);
 if(identity!==null&&c.ids.has(identity)){
  answer=astBinding(c,identity);if(answer)return answer;
  if(c.physical)return objBinding(c,identity);
  if(c.token===identity||c.token===identity.replace(/^copy:/,''))return objBinding(c,identity);
  if(number(c.token))return field(identity,`node-value:${identity}`,'stored node value',`${c.token} is the value stored at ${identity}; equal values at other nodes do not merge their identities.`);
  return objBinding(c,identity);
 }
 let m=c.id.match(/^(address|degree|count|exponent)-(.+)$/);
 if(m&&c.ids.has(m[2]))return field(m[2],`${m[1]==='count'?'node-indegree':m[1]==='exponent'?'polynomial:exponent':'node-'+m[1]}:${m[2]}`,m[1]==='count'?'incoming-edge count':m[1],`${c.token??c.expression} describes ${m[1]} of node ${m[2]}, not its identity.`);
 if(c.id==='attribute'&&c.d.node)return field(c.d.node,`node-${c.d.attribute}:${c.d.node}`,c.d.attribute,`${c.d.attribute}(${c.d.node}) = ${c.d.values?.[c.d.node]}.`);
 if(c.id==='header-fields')return bind(['tree:header-convention'],'header fields','The sentinel fields have fixed tag/link conventions, separate from data-node values.');
 if((m=c.id.match(/^stack-(?:value|box)-(\d+)$/))){
  const i=Number(m[1]),value=c.d.stack?.[i];
  if(c.ids.has(String(value)))return objBinding(c,String(value));
  return bind([`stack-entry:${i}`],'stack entry',`This is stack position ${i}; its value is not identified with another equal stack value.`);
 }
 if(/^(?:pre|in|post)-ribbon$/.test(c.id)||c.id.startsWith('ribbon-')||['output','ready','frontier-label','visited-label'].includes(c.id)){
  if(c.token&&c.ids.has(c.token))return objBinding(c,c.token);
  const name=c.id.match(/^(pre|in|post)-ribbon$/)?.[1]??c.id.replace(/^ribbon-/,'');
  return c.physical?bind([`traversal:${name}`],'traversal sequence',`This ribbon lists the ordered ${name} events, not new copies of the nodes.`):null;
 }
 if(c.token&&c.ids.has(c.token))return objBinding(c,c.token);
 if(!c.id&&['h','n','d'].includes(c.token)&&c.order>=106&&c.order<=118){
  const key=c.token==='h'?'tree:height':c.token==='n'?'tree:node-count':c.d.node?`node-degree:${c.d.node}`:'tree:degree';
  return bind([key],'tree parameter',c.token==='h'?'h is the maximum root-to-leaf height.':c.token==='n'?'n counts nodes.':'d counts ordered children; it is not a child value.');
 }
 if(c.token&&operation[c.token])return bind([`operation:${operation[c.token]}`],'mathematical operator',`${c.token} denotes ${operation[c.token]} in this structural computation.`);
 return null;
}
