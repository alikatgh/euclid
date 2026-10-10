/** Coordinate interpolation, owned by the mounted SVG rather than a second React runtime. */
type Point = {x:number;y:number;o:number;w:number;h:number};
type Controller={ current:Map<string,Point>; from:Map<string,Point>; target:Map<string,Point>; elapsed:number; last:number; raf:number; key:string; paused:boolean; svg:SVGSVGElement };
const live=new WeakMap<SVGSVGElement,Controller>();
const read=(e:Element):Point=>({x:+(e.getAttribute('data-x')??0),y:+(e.getAttribute('data-y')??0),o:+(e.getAttribute('data-o')??1),w:+(e.getAttribute('data-w')??0),h:+(e.getAttribute('data-h')??0)});
const duration=850;
function paint(c:Controller,t:number){
 c.svg.querySelectorAll('[data-move]').forEach(e=>{const id=e.getAttribute('data-move')!,to=c.target.get(id)!;if(!to)return;const from=c.from.get(id)??to;const p={} as Point;for(const k of ['x','y','o','w','h'] as const)p[k]=from[k]+(to[k]-from[k])*t;c.current.set(id,p);e.setAttribute('transform',`translate(${p.x} ${p.y})`);e.setAttribute('opacity',String(p.o));if(e.hasAttribute('data-w'))e.setAttribute('width',String(p.w));if(e.hasAttribute('data-h'))e.setAttribute('height',String(p.h));});
}
function tick(c:Controller,now:number){c.raf=0;if(c.paused||!c.svg.isConnected)return;if(typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches){c.elapsed=duration;paint(c,1);return;}c.elapsed+=c.last?now-c.last:0;c.last=now;const p=Math.min(c.elapsed/duration,1);paint(c,p*p*(3-2*p));if(p<1)c.raf=requestAnimationFrame(t=>tick(c,t));}
export function bindNumbersMotion(svg:SVGSVGElement|null,key:string,paused=false){
 if(!svg)return;let c=live.get(svg);const targets=new Map<string,Point>();svg.querySelectorAll('[data-move]').forEach(e=>targets.set(e.getAttribute('data-move')!,read(e)));
 const reduced=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(!c){c={svg,key,current:new Map(targets),from:new Map(targets),target:targets,elapsed:duration,last:0,raf:0,paused};live.set(svg,c);paint(c,1);return;}
 if(c.raf)cancelAnimationFrame(c.raf);c.raf=0;
 const changed=key!==c.key;const reset=key.split(':').slice(0,-1).join(':')!==c.key.split(':').slice(0,-1).join(':')||Number(key.split(':').at(-1))<Number(c.key.split(':').at(-1));
 if(changed){c.from=new Map(c.current);c.target=targets;c.elapsed=0;c.key=key;for(const [id,to]of targets)if(!c.from.has(id))c.from.set(id,{...to,o:0});}
 c.paused=paused;c.last=0;
 if(reduced||reset||(changed&&paused)){c.elapsed=duration;paint(c,1);}else if(c.elapsed<duration){paint(c,Math.min(c.elapsed/duration,1)**2*(3-2*Math.min(c.elapsed/duration,1)));if(!paused)c.raf=requestAnimationFrame(t=>tick(c!,t));}else paint(c,1);
}
