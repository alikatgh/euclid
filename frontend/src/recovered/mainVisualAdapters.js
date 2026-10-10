// Add causal diagrams without editing the recovered runtime or original pictures.
import { JSX, React, Ff, Mw, Iw } from './runtime.js';
import { FeatureCauseEffect, MethodCauseEffect } from '../components/OriginalMainVisualEnhancements';
export function EnhancedFeatureVisual(props) { return JSX.jsxs(React.Fragment,{children:[JSX.jsx(Mw,props),JSX.jsx(FeatureCauseEffect,props)]}); }
export function EnhancedMethodVisual(props) { return JSX.jsxs(React.Fragment,{children:[JSX.jsx(Iw,props),JSX.jsx(MethodCauseEffect,props)]}); }
/** Annotate the original geometric canvas in its own scrolling coordinate space. */
function enhanceAlgorithm(root, step) {
 const svg=root?.querySelector('svg.euclid-geometry'); if(!svg||svg.querySelector('[data-causal-proof]'))return;
 const ns='http://www.w3.org/2000/svg',g=document.createElementNS(ns,'g');g.setAttribute('data-causal-proof',step.phase);
 svg.querySelectorAll('rect[data-math-value]').forEach(rect=>{const stroke=rect.getAttribute('stroke')||'';const variable=stroke.includes('color-r')?'r':stroke.includes('color-n')?'n':stroke.includes('color-m')?'m':null;if(variable){rect.setAttribute('data-register',variable);rect.setAttribute('data-operation-phase',step.phase);if(variable==='r'||(variable==='n'&&step.phase==='E1'))rect.setAttribute('stroke-width','3');const label=document.createElementNS(ns,'title');label.textContent=`${variable} = ${rect.getAttribute('data-math-value')}: ${variable==='r'?'leftover after the complete divisor groups':variable==='n'?'one divisor-sized measuring unit':'target length'}`;rect.append(label);}});
 const [,,width,height]=svg.getAttribute('viewBox').split(' ').map(Number); const s=step;
 const gcd=(a,b)=>b?gcd(b,a%b):a, invariant=gcd(s.initialM,s.initialN);
 const lines=s.phase==='E3'?[`Old n = ${s.n} → new m = ${s.nextM??s.n}`,`Old r = ${s.r} → new n = ${s.nextN??s.r}`,`gcd(${s.initialM}, ${s.initialN}) = gcd(${s.nextM??s.n}, ${s.nextN??s.r}) = ${invariant}`]:s.phase==='E0'?[s.type==='E0_SWAP'?`m < n: exchange the two values.`:`m ≥ n: keep the supplied order.`,`No remainder division has occurred.`,`gcd(${s.initialM}, ${s.initialN}) = ${invariant}`]:[`${s.q} whole copies of n = ${s.n}; remainder r = ${s.r}`,s.r===0?`r = 0: return n = ${s.n}`:`${s.r} < ${s.n}: another complete copy cannot fit`,`gcd(${s.initialM}, ${s.initialN}) = gcd(${s.m}, ${s.n}) = ${invariant}`];
 lines.forEach((value,i)=>{const t=document.createElementNS(ns,'text');t.setAttribute('x',width/2);t.setAttribute('y',height+28+i*27);t.setAttribute('text-anchor','middle');t.setAttribute('font-family','var(--font-sans)');t.setAttribute('font-size','14');t.setAttribute('fill',i===2?'var(--color-gcd)':i===1?'var(--color-r)':'var(--color-n)');t.textContent=value;g.append(t);});
 svg.append(g);svg.setAttribute('viewBox',`0 0 ${width} ${height+105}`);svg.style.height=`${height+105}px`;
}
export function OriginalAlgorithmVisual(props) {
 const root=React.useRef(null);
 React.useEffect(()=>{const update=()=>enhanceAlgorithm(root.current,props.step);update();const observer=new MutationObserver(update);observer.observe(root.current,{childList:true,subtree:true});return()=>observer.disconnect();},[props.step,props.viewType]);
 return JSX.jsx('div',{ref:root,style:{height:'100%',minHeight:0},children:JSX.jsx(Ff,props)});
}
