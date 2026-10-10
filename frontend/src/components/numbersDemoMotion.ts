/** Persistent SVG identities: select a source, transform its objects, then reveal results. */
type Point = {x:number;y:number;o:number;w:number;h:number};
type Controller={ current:Map<string,Point>; from:Map<string,Point>; target:Map<string,Point>; elapsed:number; last:number; raf:number; key:string; paused:boolean; svg:SVGSVGElement };
const live=new WeakMap<SVGSVGElement,Controller>();
const read=(e:Element):Point=>({x:+(e.getAttribute('data-x')??0),y:+(e.getAttribute('data-y')??0),o:+(e.getAttribute('data-o')??1),w:+(e.getAttribute('data-w')??0),h:+(e.getAttribute('data-h')??0)});
const duration=850;
const smooth=(t:number)=>{const p=Math.max(0,Math.min(t,1));return p*p*(3-2*p)};
function paint(c:Controller,progress:number){
 const p=Math.max(0,Math.min(progress,1));
 c.svg.setAttribute?.('data-motion-phase',p===1?'settled':p<.15?'select':p<.85?'transform':'verify');
 c.svg.setAttribute?.('data-motion-progress',String(p));
 c.svg.querySelectorAll('[data-move]').forEach(e=>{
  const id=e.getAttribute('data-move')!,to=c.target.get(id);if(!to)return;
  const from=c.from.get(id)??to,phase=e.getAttribute('data-motion-phase');
  const t=phase==='source'?smooth(p/.15):phase==='result'?smooth((p-.85)/.15):smooth((p-.15)/.7);
  const point={} as Point;for(const k of ['x','y','o','w','h'] as const)point[k]=from[k]+(to[k]-from[k])*t;
  c.current.set(id,point);e.setAttribute('transform',`translate(${point.x} ${point.y})`);e.setAttribute('opacity',String(point.o));
  if(e.hasAttribute('data-w'))e.setAttribute('width',String(point.w));if(e.hasAttribute('data-h'))e.setAttribute('height',String(point.h));
 });
 // Statements of the resulting count/equality must not precede the settled objects.
 c.svg.querySelectorAll('[data-result]').forEach(e=>e.setAttribute('opacity',p===1?'1':'0'));
}
function tick(c:Controller,now:number){
 c.raf=0;if(c.paused||!c.svg.isConnected)return;
 if(typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches){c.elapsed=duration;paint(c,1);return;}
 c.elapsed+=c.last?now-c.last:0;c.last=now;const p=Math.min(c.elapsed/duration,1);paint(c,p);
 if(p<1)c.raf=requestAnimationFrame(t=>tick(c,t));
}
export function bindNumbersMotion(svg:SVGSVGElement|null,key:string,paused=false){
 if(!svg)return;let c=live.get(svg);const targets=new Map<string,Point>();svg.querySelectorAll('[data-move]').forEach(e=>targets.set(e.getAttribute('data-move')!,read(e)));
 const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(!c){c={svg,key,current:new Map(targets),from:new Map(targets),target:targets,elapsed:duration,last:0,raf:0,paused};live.set(svg,c);paint(c,1);return;}
 if(c.raf)cancelAnimationFrame(c.raf);c.raf=0;
 const changed=key!==c.key,reset=key.split(':').slice(0,-1).join(':')!==c.key.split(':').slice(0,-1).join(':')||Number(key.split(':').at(-1))<Number(c.key.split(':').at(-1));
 if(changed){c.from=new Map(c.current);c.target=targets;c.elapsed=0;c.key=key;for(const [id,to]of targets)if(!c.from.has(id))c.from.set(id,{...to,o:0});}
 c.paused=paused;c.last=0;
 if(reduced||reset||(changed&&paused)){c.elapsed=duration;paint(c,1);}
 else if(c.elapsed<duration){paint(c,c.elapsed/duration);if(!paused)c.raf=requestAnimationFrame(t=>tick(c!,t));}
 else paint(c,1);
}
