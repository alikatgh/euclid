/** Same-panel semantic diagrams: selection, transformation, then verified results.
 * Keeps displayed endpoints truthful, pauses without scheduling animation frames,
 * and interpolates edge endpoints as well as node locations. */
type Values={x:number;y:number;o:number;w:number;h:number;r:number;ex:number;ey:number};
type State={svg:SVGSVGElement;key:string;elapsed:number;last:number;raf:number;paused:boolean;from:Map<string,Values>;target:Map<string,Values>;current:Map<string,Values>};
const live=new WeakMap<SVGSVGElement,State>();
const total=1100;
const keys=['x','y','o','w','h','r','ex','ey'] as const;
const get=(e:Element):Values=>Object.fromEntries(keys.map(k=>[k,Number(e.getAttribute(`data-${k}`)??(k==='o'?1:0))])) as Values;
const ease=(p:number)=>{const x=Math.max(0,Math.min(1,p));return x*x*(3-2*x)};
function paint(c:State,p:number){
 c.svg.setAttribute('data-motion-phase',p===1?'settled':p<.18?'select':p<.86?'transform':'verify');
 c.svg.setAttribute('data-motion-progress',String(p));
 c.svg.querySelectorAll('[data-diagram-node]').forEach(e=>{
  const id=e.getAttribute('data-diagram-node')!,t=c.target.get(id);if(!t)return;const f=c.from.get(id)??t;
  const phase=e.getAttribute('data-phase');const q=phase==='source'?ease(p/.18):phase==='result'?ease((p-.86)/.14):ease((p-.18)/.68);
  const v=Object.fromEntries(keys.map(k=>[k,f[k]+(t[k]-f[k])*q])) as Values;c.current.set(id,v);
  e.setAttribute('transform',`translate(${v.x} ${v.y})`);e.setAttribute('opacity',String(v.o));
  const s=e.querySelector('[data-diagram-shape]');
  if(s?.tagName.toLowerCase()==='rect'){s.setAttribute('width',String(Math.max(0,v.w)));s.setAttribute('height',String(Math.max(0,v.h)));}
  if(s?.tagName.toLowerCase()==='circle')s.setAttribute('r',String(Math.max(0,v.r)));
  if(s?.tagName.toLowerCase()==='line'){s.setAttribute('x2',String(v.ex));s.setAttribute('y2',String(v.ey));}
 });
 c.svg.querySelectorAll('[data-diagram-result]').forEach(e=>e.setAttribute('opacity',p===1?'1':'0'));
}
function frame(c:State,now:number){
 c.raf=0;if(c.paused||!c.svg.isConnected){c.last=0;return;}
 if(typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches){c.elapsed=total;paint(c,1);return;}
 c.elapsed+=c.last?now-c.last:0;c.last=now;const p=Math.min(1,c.elapsed/total);paint(c,p);
 if(p<1)c.raf=requestAnimationFrame(t=>frame(c,t));
}
export function bindFullBookMotion(svg:SVGSVGElement|null,key:string,paused=false){
 if(!svg)return;const target=new Map<string,Values>();svg.querySelectorAll('[data-diagram-node]').forEach(e=>target.set(e.getAttribute('data-diagram-node')!,get(e)));
 let c=live.get(svg);if(!c){c={svg,key,elapsed:total,last:0,raf:0,paused,from:new Map(target),current:new Map(target),target};live.set(svg,c);paint(c,1);return;}
 if(c.raf)cancelAnimationFrame(c.raf);c.raf=0;
 const change=c.key!==key;const prefix=(k:string)=>k.slice(0,k.lastIndexOf(':'));const index=(k:string)=>Number(k.slice(k.lastIndexOf(':')+1));
 const reset=prefix(c.key)!==prefix(key)||index(key)<index(c.key);
 if(change){c.from=new Map(c.current);c.target=target;c.elapsed=0;c.key=key;for(const[id,v]of target)if(!c.from.has(id))c.from.set(id,{...v,o:0});}
 c.paused=paused;c.last=0;
 const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(reset||reduced||(change&&paused)){c.elapsed=total;paint(c,1);}
 else if(c.elapsed<total){paint(c,c.elapsed/total);if(!paused)c.raf=requestAnimationFrame(t=>frame(c!,t));}
 else paint(c,1);
}
