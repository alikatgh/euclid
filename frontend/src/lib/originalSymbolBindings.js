/** Original Euclid roles override legacy equality, including q = r numerically. */
export function originalSymbolBinding(element,context) {
 const step=context?.originalStep;if(!step)return null;
 const token=element.getAttribute('data-math-token')||element.getAttribute('data-math-value')||'',expression=element.getAttribute('data-math-expression')||'';
 if(element.id==='col3-m-input'||element.id==='col3-n-input'){
  const name=element.id==='col3-m-input'?'m':'n',initial=step[name==='m'?'initialM':'initialN'];
  return {keys:[`initial:${name}`],role:'original input',description:`Original input ${name} = ${initial}. The current ${name} register may have changed during the algorithm.`};
 }
 const dimensions=(element.getAttribute('data-math-values')||'').split(/\s+/).filter(Boolean);
 if(dimensions.length){const names=['m','n'].filter(name=>dimensions.includes(String(step[name])));return {keys:names.length?names.map(name=>`quantity:${name}:${step[name]}`):['geometry:dimensions'],memberships:names.map(name=>`symbol:${name}`),role:'geometric dimensions',description:`This rectangle represents the current dimensions ${dimensions.join(' by ')}. Its sides correspond to the current lengths, not the quotient count.`};}
 const scalar=expression.replace(/\s/g,'').match(/^([mnqr])(?:=|\\leftarrow|←)([0-9]+)$/);
 if(scalar&&String(step[scalar[1]])!==scalar[2]&&(token===scalar[1]||token===scalar[2]))return {keys:[token===scalar[1]?`symbol:${scalar[1]}`:`reference:${scalar[1]}:${scalar[2]}`],memberships:[token===scalar[1]?`reference:${scalar[1]}:${scalar[2]}`:`symbol:${scalar[1]}`],role:'separate worked assignment',description:`${scalar[1]} = ${scalar[2]} in this written example. The current demonstration has ${scalar[1]} = ${step[scalar[1]]}.`};
 let variable=element.closest('[data-register]')?.getAttribute('data-register');
 if(!variable)for(const name of ['m','n','q','r'])if(element.closest(`.text-rod-${name}`)){variable=name;break;}
 if(!variable&&/^[mnqr]$/.test(token))variable=token;
 if(!variable&&/^[mnqr]$/.test(element.getAttribute('data-math-assignment')||''))variable=element.getAttribute('data-math-assignment');
 if(!variable&&element.getAttribute('data-math-original-role'))variable=element.getAttribute('data-math-original-role');
 if(!variable&&element.closest('svg text')){
  const text=element.closest('text'),value=text.textContent,fill=text.getAttribute('fill')||'';
  let offset=0;for(const child of text.childNodes){if(child===element)break;offset+=child.textContent?.length??0;}const before=value.slice(0,offset),after=value.slice(offset+token.length);if(/^[0-9]+$/.test(token)){const local=before.match(/([mnqr])\s*=\s*$/);if(local&&String(step[local[1]])===token)variable=local[1];else if(/^\s+whole copies/.test(after)&&String(step.q)===token)variable='q';}
  const prefix=value.match(/^\s*([mnqr])\s*[=:]/);if(prefix&&String(step[prefix[1]])===token)variable=prefix[1];
  if(!variable&&/^\s*[\d.]+\s*$/.test(value)){const match=fill.match(/(?:color-|rod-)([mnqr])/);if(match)variable=match[1];}
 }
 if(!variable&&/^[0-9]+$/.test(token)&&new RegExp('^([mnqr])(?:=|\\\\leftarrow|←)'+token+'$').test(expression))variable=expression[0];
 if(!variable&&/^(?:\d+(?:\.\d+)?)$/.test(token)){
  const candidates=['m','n','q','r'].filter(name=>String(step[name])===token);
  // Unambiguous step values may link; equal values with different roles may not.
  if(candidates.length===1)variable=candidates[0];
 }
 if(variable){const roles={m:'dividend / current target length',n:'divisor / one measuring unit',q:'quotient / count of whole divisor groups',r:'remainder / leftover length'};return {keys:[token===variable?`symbol:${variable}`:`quantity:${variable}:${step[variable]}`],memberships:[token===variable?`quantity:${variable}:${step[variable]}`:`symbol:${variable}`],role:roles[variable],description:`${variable} = ${step[variable]}: ${roles[variable]}. Equal-looking values in other roles remain separate.`};}
 if(element.hasAttribute('data-math-value')||element.hasAttribute('data-math-values'))return {keys:[`original:unassigned:${element.getAttribute('data-math-occurrence')||expression+':'+element.getAttribute('data-math-offset')}`],role:'number in this expression',description:`${token}: this occurrence. Its numerical value alone does not identify a quotient, remainder, or length.`};
 return null;
}
