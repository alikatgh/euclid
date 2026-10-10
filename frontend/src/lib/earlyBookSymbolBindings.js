/** Authored A/B families: pair/slot identity is separate from printed magnitude. */
export function earlyBookSymbolBinding(element,context) {
 const visual=context?.frame?.visual??{},order=Number(visual.order),state=visual.state??{},computed=state.computed??{};
 if(order<21||order>64)return null;
 const token=element.getAttribute('data-math-token')||'',node=element.closest('[data-diagram-node]'),id=node?.getAttribute('data-diagram-node')||'';
 const bind=(keys,memberships,role,description)=>({keys,memberships,role,description});let m;
 if([25,43].includes(order)&&Array.isArray(computed.cells)) {
  if((m=id.match(/^(?:cell-|pair-)(\d+)-(\d+)(?:-label)?$/))){const [i,j]=m.slice(1).map(Number),selected=!computed.selectedPairs||computed.selectedPairs.some(p=>p[0]===i&&p[1]===j);return bind([`pair:${i}:${j}`],[...(selected?['operation:sum']:[]),`symbol:i`,`symbol:j`],'indexed pair',`The contribution at row i=${i}, column j=${j}. A repeated value in another cell is a different contribution.`);}
  if((m=id.match(/^(row|column)(\d+)$/)))return bind([`index:${m[1]}:${m[2]}`],[`symbol:${m[1]==='row'?'i':'j'}`],'index',`${m[1]} ${m[2]} selects a family of legal pairs, not their numerical values.`);
 }
 if(order===27&&/^(positive|negative)\d+(?:-label)?$/.test(id))return bind([`telescoping:${id.replace(/-label$/,'')}`],['operation:sum'],'signed summand','This signed contribution belongs to the telescoping sum. Equal opposite terms can cancel; their identities remain distinct.');
 if(order===28&&/^(top|bottom)\d+(?:-label)?$/.test(id))return bind([`product:${id.replace(/-label$/,'')}`],['operation:product'],'product factor','This is a numerator or denominator factor in the finite product.');
 if(order===29&&(m=id.match(/^(?:term|label)(\d+)$/)))return bind([`partial:term:${m[1]}`],['operation:sum','symbol:S'],'partial-sum term','One included geometric term. The unfilled tail is a separate quantity.');
 if(order===47) {
  if((m=id.match(/^(?:card|value)(\d+)$/)))return bind([`coefficient:${m[1]}`],['symbol:a','symbol:G'],'coefficient card',`Coefficient a_${m[1]}; shifting its exponent changes its slot, not this card's value.`);
  if((m=id.match(/^(?:index|shelf)(\d+)$/)))return bind([`degree:${m[1]}`],['symbol:n','symbol:z'],'exponent slot',`The slot for degree ${m[1]}. Degree is distinct from the coefficient stored here.`);
 }
 if(order===48) {
  if((m=id.match(/^(?:pair|prod)(\d+)-(\d+)$/))){const i=Number(m[1]),j=Number(m[2]);return bind([`convolution:${i}:${j}`],[...(i+j===computed.n?['operation:sum','symbol:c']:[]),'symbol:i','symbol:j'],'coefficient product',`The product a_${i} b_${j} has degree ${i+j}. Only degree ${computed.n} contributes to this coefficient.`);}
  if((m=id.match(/^([ijab])(\d+)$/)))return bind([`input:${m[1]}:${m[2]}`],[`symbol:${m[1]}`],'coefficient or index',`${m[1]}_${m[2]} in this convolution; its role and index are preserved.`);
 }
 if([55,56].includes(order)) {
  if((m=id.match(/^(?:p|val|v)(\d+)$/)))return bind([`probability:${m[1]}`],['symbol:G'],'probability mass',`The probability attached to outcome ${m[1]}; it is not the outcome's number.`);
  if((m=id.match(/^k(\d+)$/)))return bind([`outcome:${m[1]}`],['symbol:k'],'outcome index',`Outcome ${m[1]} names a bin; the bar height is its probability.`);
 }
 if(order===59) {
  if((m=id.match(/^operand-(?:name|box|value)(\d+)$/)))return bind([`endpoint:operand:${m[1]}`],['symbol:f'],'endpoint operand','The value at this endpoint is an operand of the displayed correction.');
  if(id==='curve')return bind(['function:f'],['symbol:f'],'function graph','The graph of f whose samples and integral are compared.');
 }
 if(token==='∏'||token==='Π')return bind(['operation:product'],[],'product','Π (capital pi) means multiply the selected factors, one for each allowed index.');
 return null;
}
