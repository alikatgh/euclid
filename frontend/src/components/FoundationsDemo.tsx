import { symbolTextChildren } from '../lib/symbolConnections.js';
import * as JSX from 'react/jsx-runtime';
import type { ReactNode } from 'react';

/** Pure view for the original lesson player's right-hand demonstration panel.
 * No React singleton or hooks: the recovered original runtime owns playback. */
type Obj = { id: string; label?: string; value?: unknown; role?: string; location?: string; data?: Record<string, unknown> };
type State = { id?: string; caption?: string; formula?: string; objects?: Obj[] };
export type FoundationsDemoProps = { exampleId?: string; frameIndex?: number; frame?: Record<string, unknown>; visual?: { model?: Record<string, unknown> | string; state?: State; transition?: Record<string, unknown>; help?: unknown; helpMode?: boolean; helpContent?: {intro?:string;steps?:{action:string;text:string}[]}; helpStepIndex?:number; lessonId?:string; order?:number }; paused?: boolean; motionPaused?: boolean; reducedMotion?: boolean };
const BLUE='#3b82f6', ORANGE='#f59e0b', RED='#ef4444', ORANGE_INK='var(--color-n, #9a5700)';
const clamp=(n:number,lo:number,hi:number)=>Math.max(lo,Math.min(hi,n));
const asNumber=(x:unknown,fallback:number)=>typeof x==='number'&&Number.isFinite(x)?x:fallback;
const numberValue=(s:State,id:string,fallback:number)=>asNumber(s.objects?.find(o=>o.id===id)?.value,fallback);
const positions = new WeakMap<SVGElement,{x:number;y:number;o:number}>();
type Tween={el:SVGElement;from:{x:number;y:number;o:number};to:{x:number;y:number;o:number}};
type Controller={observer:MutationObserver;elapsed:number;last:number;raf:number;tweens:Tween[];signature:string};
const controllers=new WeakMap<SVGSVGElement,Controller>();
function mountMotion(svg:SVGSVGElement|null){
 if(!svg||controllers.has(svg))return;
 const c:Controller={observer:null as unknown as MutationObserver,elapsed:0,last:0,raf:0,tweens:[],signature:''};
 controllers.set(svg,c);
 const write=(el:SVGElement,v:{x:number;y:number;o:number})=>{positions.set(el,v);el.setAttribute('transform',`translate(${v.x} ${v.y})`);el.setAttribute('opacity',String(v.o));};
 const tick=(time:number)=>{
  c.raf=0;if(!svg.isConnected)return;
  const paused=svg.dataset.paused==='true';
  if(svg.dataset.reduced==='true'||(typeof matchMedia!=='undefined'&&matchMedia('(prefers-reduced-motion: reduce)').matches))c.elapsed=850;else if(paused){c.last=0;return;}else c.elapsed+=c.last?Math.min(64,time-c.last):0;c.last=time;
  const p=clamp((c.elapsed-140)/710,0,1),e=p*p*(3-2*p);
  svg.dataset.operationPhase=p===1?'checked':p===0?'selected':'moving';
  for(const t of c.tweens)write(t.el,{x:t.from.x+(t.to.x-t.from.x)*e,y:t.from.y+(t.to.y-t.from.y)*e,o:t.from.o+(t.to.o-t.from.o)*e});
  if(p<1&&!paused)c.raf=requestAnimationFrame(tick);
 };
 const update=()=>{
  const els=Array.from(svg.querySelectorAll<SVGElement>('[data-motion-id]'));
  const sig=(svg.dataset.frame||'')+'|'+els.map(e=>[e.dataset.motionId,e.dataset.x,e.dataset.y,e.dataset.o].join(':')).join('|');
  if(svg.dataset.paused==='true'&&sig===c.signature){cancelAnimationFrame(c.raf);c.raf=0;c.last=0;return;}
  if(sig===c.signature){if(svg.dataset.paused!=='true'&&c.tweens.length&&!c.raf&&c.elapsed<850){c.last=0;c.raf=requestAnimationFrame(tick);}return;}
  const first=!c.signature;c.signature=sig;cancelAnimationFrame(c.raf);c.elapsed=0;c.last=0;
  const reduced=svg.dataset.paused==='true'||svg.dataset.reduced==='true'||(typeof matchMedia!=='undefined'&&matchMedia('(prefers-reduced-motion: reduce)').matches);
  c.tweens=els.map(el=>{const to={x:Number(el.dataset.x||0),y:Number(el.dataset.y||0),o:Number(el.dataset.o??1)};const from=positions.get(el)||{x:Number(el.dataset.originX??to.x),y:Number(el.dataset.originY??to.y),o:Number(el.dataset.originO??to.o)};if(first||reduced)write(el,to);else write(el,from);return{el,from,to};});
  if(first||reduced){c.elapsed=850;svg.dataset.operationPhase='checked';}else c.raf=requestAnimationFrame(tick);
 };
 c.observer=new MutationObserver(update);c.observer.observe(svg,{subtree:true,childList:true,attributes:true,attributeFilter:['data-x','data-y','data-o','data-paused','data-reduced','data-frame']});update();
}
function Move({id,x,y,o=1,children}:{id:string;x:number;y:number;o?:number;children:ReactNode}){return <g key={id} data-motion-id={id} data-x={x} data-y={y} data-o={o} transform={`translate(${x} ${y})`} opacity={o}>{children}</g>;}
function Tile({id,x,y,size=23,color=BLUE,o=1}:{id:string;x:number;y:number;size?:number;color?:string;o?:number}){return <Move id={id} x={x} y={y} o={o}><rect width={size} height={size} fill={color}/></Move>;}
function Label({x,y,children,size=16,anchor='start',color='currentColor'}:{x:number;y:number;children:ReactNode;size?:number;anchor?:'start'|'middle'|'end';color?:string}){return <text x={x} y={y} fontSize={size} textAnchor={anchor} fill={color===ORANGE?ORANGE_INK:color}>{symbolTextChildren(children, JSX, true)}</text>;}
function Bracket({x,y,w,label}:{x:number;y:number;w:number;label:string}){return <g><path d={`M${x} ${y-5}v5h${w}v-5`} fill="none" stroke="currentColor" opacity=".45"/><Label x={x+w/2} y={y+22} anchor="middle" size={15}>{label}</Label></g>;}
function Arrow({x1,y1,x2,y2,label,color=ORANGE}:{x1:number;y1:number;x2:number;y2:number;label?:string;color?:string}){
 const a=Math.atan2(y2-y1,x2-x1),d=8;
 return <g data-teaching="operation-arrow"><path d={`M${x1} ${y1}L${x2} ${y2}M${x2-d*Math.cos(a-.5)} ${y2-d*Math.sin(a-.5)}L${x2} ${y2}L${x2-d*Math.cos(a+.5)} ${y2-d*Math.sin(a+.5)}`} stroke={color} strokeWidth="2" fill="none"/>{label&&<Label x={(x1+x2)/2} y={Math.min(y1,y2)-10} anchor="middle" size={13}>{label}</Label>}</g>;
}
function Assignment({s,state}:{s:number;help:boolean;state:State}){
 const a=7,b=12,stage=clamp(s,0,6),bad=stage===1||stage===2,copy=bad||stage>=5,parallel=state.id==='parallel'||state.id==='restart-parallel'||state.id==='parallel-before'||state.id==='capture-parallel';
 const x=[95,300,505];
 return <>
  <Label x={50} y={32}>{parallel?(stage===6?'Write both values from the captured pair':'Read both old values before either write'):stage===3?'Reset to the same starting values':bad?'Copying overwrites the old value':'Keep names fixed; copy the current value'}</Label>
  {(parallel||stage<3?['a','b']:['a','b','t']).map((n,i)=><g key={n}><path d={`M${x[i]} 113v116h119V113`} fill="none" stroke="currentColor" opacity=".5"/><Label x={x[i]+60} y={264} anchor="middle" size={22}>{n}</Label></g>)}
  <Move id="original-a" x={x[0]+14} y={copy?286:139} o={copy?.3:1}><rect width="90" height={copy?40:62} fill={RED}/><Label x={45} y={copy?28:40} anchor="middle" size={26}>{a}</Label></Move>
  <Move id="original-b" x={x[1]+14} y={stage===6?286:139} o={stage===6?.3:1}><rect width="90" height={stage===6?40:62} fill={BLUE}/><Label x={45} y={stage===6?28:40} anchor="middle" size={26}>{b}</Label></Move>
  <Move id="copy-b-a" x={copy?x[0]+14:x[1]+14} y={139} o={copy?1:0}><rect width="90" height="62" fill={BLUE}/><Label x={45} y={40} anchor="middle" size={26}>{b}</Label></Move>
  <Move id="copy-a-b-again" x={stage===2?x[1]+14:x[0]+14} y={139} o={stage===2?1:0}><rect width="90" height="62" fill={BLUE}/><Label x={45} y={40} anchor="middle" size={26}>{b}</Label></Move>
  <Move id="save-a-t" x={stage>=4?x[2]+14:x[0]+14} y={139} o={stage>=4&&!parallel?1:0}><rect width="90" height="62" fill={RED}/><Label x={45} y={40} anchor="middle" size={26}>{a}</Label></Move>
  <Move id="copy-t-b" x={stage===6?x[1]+14:parallel?x[0]+14:x[2]+14} y={139} o={stage===6?1:0}><rect width="90" height="62" fill={RED}/><Label x={45} y={40} anchor="middle" size={26}>{a}</Label></Move>
  <Label x={360} y={84} anchor="middle" size={22}>{parallel?'(a, b) ← (b, a)':['a = '+a+', b = '+b,'a ← b','b ← a','a = '+a+', b = '+b,'t ← a','a ← b','b ← t'][stage]}</Label>
  {!parallel&&stage>0&&stage!==3&&<Arrow x1={stage===4||stage===2?215:stage===6?505:300} y1={109} x2={stage===4?505:stage===6?420:stage===2?300:215} y2={109} label={stage===4?'1 · save before overwrite':stage===6?'3 · restore saved 7':stage===2?'copies the new 12 again':stage===5?'2 · copy 12':'copy current b'}/>}
  <Label x={50} y={stage>0&&stage!==3?351:310} size={14}>{bad?'Check: (a, b) = (12, 12); the original 7 is lost.':stage===6?'Check: (a, b) = (12, 7); both originals survive.':stage===4?'Check: a = 7 and t = 7; copying keeps the source.':'A box is a variable; the numbered card is its stored value.'}</Label>
  {parallel&&<><Label x={475} y={150} size={16}>Read old pair: (7, 12)</Label><Label x={475} y={195} size={16}>{stage===6?'Write new pair: (12, 7)':state.id==='parallel-before'?'Capture both before writing':'Captured both: (12, 7)'}</Label></>}{copy&&<Label x={360} y={366} anchor="middle" size={14}>Overwritten copies, no longer stored</Label>}
 </>;
}
function Triangle({s,help,n:requestedN}:{s:number;help:boolean;n?:number}){
 const n=requestedN??(help?3:4),rows=clamp(s+1,0,n),pair=s>=n+1,copied=s>=n,size=help?40:35,gap=size+5,x=82,y=75;
 const cells=Array.from({length:n},(_,r)=>Array.from({length:r+1},(_,c)=>({r,c,id:`${r}-${c}`}))).flat();
 return <><Label x={50} y={32}>{pair?'Two equal triangles fill one rectangle':'Add the next row; keep every old tile'}</Label>
 {cells.map(t=><Tile key={t.id} id={'tri-'+t.id} x={t.r<rows?x+t.c*gap:432+t.c*gap} y={y+t.r*gap} size={size} color={t.r===rows-1&&!pair?ORANGE:BLUE}/>)}
 {cells.map(t=><Tile key={'copy-'+t.id} id={'tri-copy-'+t.id} x={pair?x+(n-t.c)*gap:432+t.c*gap} y={pair?y+(n-1-t.r)*gap:y+t.r*gap} size={size} color={ORANGE} o={copied?1:0}/>)}
 {pair?<><Bracket x={x} y={y+n*gap+6} w={(n+1)*gap-5} label={`${n+1} columns`}/><Label x={410} y={105}>{n} × {n+1} = {n*(n+1)} tiles</Label><Label x={410} y={140}>One triangle: {n*(n+1)} ÷ 2 = {n*(n+1)/2}</Label><Label x={410} y={185} size={15}>A finite picture illustrates the rule.</Label><Label x={410} y={210} size={15}>The general adding step proves it.</Label></>:<><Label x={x} y={292}>{rows} rows; {rows*(rows+1)/2} placed tiles</Label><Label x={432} y={292}>{copied?'Matching copy':rows===n?'All rows are placed':'Waiting tiles'}</Label></>}
 {!pair&&rows>0&&<><path d={`M${x-12} ${y+(rows-1)*gap-4}h${rows*gap+16}v${size+8}H${x-12}z`} stroke={ORANGE} fill="none"/><Label x={410} y={330} size={14}>{rows*(rows-1)/2} old + {rows} new = {rows*(rows+1)/2}</Label></>}
 <Label x={360} y={358} anchor="middle" size={16}>{pair?`2 × (${n===2?'1 + 2':`1 + … + ${n}`}) = ${n} × ${n+1}; halve both sides`:'New total = old total + next row'}</Label></>;
}
function Prime({s,help}:{s:number;help:boolean}){
 const square=s>=3,observations=!help&&s<2,n=help?3:11,total=n*n,unit=help?44:18,gap=unit+3,x=help?190:90,y=70;
 return <><Label x={50} y={32}>{help?'Nine dots can make three equal rows':'Many successful tests do not settle “every input”'}</Label>
 {Array.from({length:total},(_,i)=>{let px=x+(i%n)*gap,py=y+Math.floor(i/n)*gap;if(!square){if(help){px=82+(i%5)*50;py=110+Math.floor(i/5)*50;}else if(i<100){px=82+(i%10)*21;py=70+Math.floor(i/10)*21;}else if(i<110){px=315;py=70+(i-100)*21;}else{px=82+(i-110)*21;py=292;}}if(observations){const starts=[0,11,24,41];const group=i<11?0:i<24?1:i<41?2:3,local=i-starts[group];px=50+group*166+(local%6)*22;py=112+Math.floor(local/6)*24;if(s<0){px=350+(i%8)*2;py=80;}}return <Tile key={i} id={'prime-unit-'+i} x={px} y={py} size={unit} color={i<(help?6:100)?BLUE:i<(help?9:110)?ORANGE:RED} o={observations&&(i>=64||s<0)?0:1}/>;})}
 {!observations&&<><Label x={425} y={92}>{help?'9 = 3 × 3':'f(n) = n² + n + 11'}</Label>
 <Label x={425} y={130} size={15}>{help?'Both factors exceed one.':'f(0), f(1), f(2), f(3) are prime.'}</Label>
 <Label x={425} y={163} size={15}>{help?'So nine is not prime.':'At n = 10: 100 + 10 + 11 = 121.'}</Label>
 <Label x={425} y={246} size={14}>{help?'One square = one unit':'Blue 100 · orange 10 · red 11'}</Label><Label x={425} y={278} size={14}>{square?`${total} units retained; none added`: 'Same count, new arrangement'}</Label>
 <Label x={425} y={211} size={19}>{square?`${total} = ${n} × ${n}`:'Rearrange the same units →'}</Label>
 </>}{observations&&s>=0&&[11,13,17,23].map((v,i)=><Label key={v} x={50+i*166} y={87} size={16}>f({i}) = {v}: prime</Label>)}{square&&<Bracket x={x} y={y+n*gap+7} w={n*gap-3} label={`${n} rows, ${n} columns`}/>}
 <Label x={360} y={364} anchor="middle" size={16}>{help?'Three equal rows prove 9 composite; this is a smaller factoring example.':'One allowed failure refutes a claim about every input.'}</Label></>;
}
function TrialPrime({s,help}:{s:number;help:boolean}){
 const n=help?7:17,limit=Math.floor(Math.sqrt(n)),phase=clamp(s,0,limit+1),d=clamp(phase+1,2,limit),q=Math.floor(n/d),r=n%d,proved=phase>=limit;
 return <g data-teaching="trial-prime">
  <Label x={40} y={34} size={20}>Can {n} make equal rows with a smaller divisor?</Label>
  <Label x={40} y={73} size={16}>{phase===0?'Choose the whole number, then test each possible small divisor':proved?`Any untested factor would be at least ${limit+1}`:`Try divisor ${d}: ${d} equal rows of ${q}, with ${r} left over`}</Label>
  {Array.from({length:(limit+1)**2},(_,i)=><Move key={i} id={'trial-slot-'+i} x={proved?55+(i%(limit+1))*31:55+(i%q)*31} y={proved?104+Math.floor(i/(limit+1))*31:104+Math.floor(i/q)*31} o={proved?1:0}><rect width={25} height={25} fill="none" stroke={ORANGE} strokeDasharray="3 3"/></Move>)}
  {Array.from({length:n},(_,i)=><Tile key={i} id={'trial-unit-'+i} x={phase===0?55+(i%8)*31:proved?55+(i%(limit+1))*31:i<q*d?55+(i%q)*31:340+(i-q*d)*31} y={phase===0?104+Math.floor(i/8)*31:proved?104+Math.floor(i/(limit+1))*31:i<q*d?104+Math.floor(i/q)*31:150} size={25} color={phase>0&&!proved&&i>=q*d?RED:BLUE}/>)}
  <Label x={445} y={105} size={17}>Test every integer 2…{limit}</Label>
  {Array.from({length:limit-1},(_,i)=>i+2).map(v=><Label key={v} x={445} y={143+(v-2)*32} size={16}>{phase>=v-1?`${n} = ${v} × ${Math.floor(n/v)} + ${n%v}  ✓`:`${v}: not tested yet`}</Label>)}
  <Label x={445} y={261} size={14}>✓ means nonzero remainder</Label>
  <Label x={40} y={300} size={17}>{phase===0?`For ${n}, the only trial divisors needed are 2 through ${limit}.`:proved?`${limit+1} × ${limit+1} = ${(limit+1)**2} > ${n}: both factors cannot be that large.`:`${n} = ${d} × ${q} + ${r}; leftover ${r} means ${d} does not divide ${n}.`}</Label>
  <Label x={40} y={335} size={16}>{proved?`If ${n} were composite, a factor would be ≤ √${n}; all 2…${limit} failed.`:`${limit}² ≤ ${n} < ${limit+1}², so floor(√${n}) = ${limit}.`}</Label>
  <Label x={360} y={365} anchor="middle" size={16}>{proved?`${n} is prime. This conclusion is only about ${n}.`:'One square = one unit. Red units cannot complete another equal row.'}</Label>
 </g>;
}
function PredecessorBound({phase,help}:{phase:number;help:boolean}){
 const k=help?3:5,a=help?1:3,b=help?1:2,ca=2**(k-2),cb=2**(k-3),cap=2**(k-1),joined=phase>=1,compare=phase>=2;
 return <g data-teaching="predecessor-bound">
  <Label x={40} y={34} size={19}>At k = {k}, copy both earlier piles and their permitted spaces</Label>
  <Label x={55} y={75} size={17}>F{k-1} = {a} ≤ 2^({k}−2) = {ca}</Label>
  <Label x={370} y={75} size={17}>F{k-2} = {b} ≤ 2^({k}−3) = {cb}</Label>
  <g opacity={joined?.3:0} data-teaching="retained-predecessors">
   {Array.from({length:ca+cb},(_,i)=>{const first=i<ca,j=first?i:i-ca;return <g key={i}><rect x={(first?55:370)+(j%8)*37} y={108+Math.floor(j/8)*37} width={29} height={29} fill="none" stroke={first?BLUE:ORANGE}/>{j<(first?a:b)&&<rect x={(first?61:376)+j*37} y={114} width={17} height={17} fill={first?BLUE:ORANGE}/>}</g>;})}
  </g>
  {Array.from({length:cap},(_,i)=><rect key={i} x={120+(i%8)*37} y={211+Math.floor(i/8)*37} width={29} height={29} fill="none" stroke="currentColor" opacity={compare?1:.12} strokeDasharray="3 3"/>)}
  {Array.from({length:ca+cb},(_,i)=>{const first=i<ca,j=first?i:i-ca,slot=i;return <Move key={i} id={'bound-space-'+i} x={joined?120+(slot%8)*37:(first?55:370)+(j%8)*37} y={joined?211+Math.floor(slot/8)*37:108+Math.floor(j/8)*37}><rect width={29} height={29} fill="none" stroke={first?BLUE:ORANGE} strokeWidth={2}/></Move>;})}
  {Array.from({length:a+b},(_,i)=>{const first=i<a,j=first?i:i-a,slot=first?j:ca+j;return <Move key={i} id={'bound-counter-'+i} x={joined?126+(slot%8)*37:(first?61:376)+j*37} y={joined?217+Math.floor(slot/8)*37:114}><rect width={17} height={17} fill={first?BLUE:ORANGE}/></Move>;})}
  <Label x={40} y={178} size={16}>{joined?`Actual counters: ${a} + ${b} = ${a+b}. Their spaces: ${ca} + ${cb} = ${ca+cb}.`:'Solid square = actual counter. Outline = one permitted space.'}</Label>
  <Label x={460} y={233} size={15}>{compare?`${ca+cb} spaces fit in ${cap}`:'Copy the spaces too'}</Label>
  <Label x={460} y={261} size={15}>{compare?`${cap-ca-cb} ${cap-ca-cb===1?'space stays':'spaces stay'} unused`:'Keep both old bounds'}</Label>
  <Label x={40} y={309} size={17}>{`F${k} = ${a+b} ≤ ${ca} + ${cb} = 3 × ${cb} ≤ 4 × ${cb} = ${cap}`}</Label>
  <Label x={40} y={347} size={phase>=3?18:15}>{phase>=3?'2^(k−2) + 2^(k−3) = 3·2^(k−3) ≤ 4·2^(k−3) = 2^(k−1)':`Target capacity 2^(${k}−1) = ${cap}; extra empty space is allowed.`}</Label>
 </g>;
}
function Fibonacci({s,help}:{s:number;help:boolean}){
 const terms=help?[1,2,3]:[0,1,1,2,3,5,8],visible=clamp(s+2,0,terms.length),bounds=s>=terms.length-1,dx=help?185:92,start=help?110:45;
 return <><Label x={50} y={32}>Copy both preceding piles to construct the next pile</Label>
 {terms.map((count,i)=><g key={i}>{bounds&&i>0&&Array.from({length:2**(i-1)},(_,j)=><rect key={'capacity-'+j} x={start+i*dx+(j%4)*16} y={248-Math.floor(j/4)*17} width={13} height={13} fill="none" stroke="currentColor" strokeDasharray="2 2" opacity=".5"/>)}
 {Array.from({length:count},(_,j)=>{const ready=i<visible,a=Math.max(0,i-2),b=Math.max(0,i-1),source=j<(terms[a]||0)?a:b,sourceJ=source===a?j:j-(terms[a]||0);return <Tile key={j} id={`fib-${i}-${j}`} x={ready?start+i*dx+(j%4)*16:start+source*dx+(Math.max(0,sourceJ)%4)*16} y={ready?248-Math.floor(j/4)*17:248-Math.floor(Math.max(0,sourceJ)/4)*17} size={13} color={i===visible-1?ORANGE:BLUE} o={ready?1:0}/>;})}
 <Label x={start+i*dx+27} y={306} anchor="middle" size={16}>{i<visible?count:'?'}</Label>
 <Label x={start+i*dx+27} y={333} anchor="middle" size={13}>{help?`pile ${i+1}`:`F${i}`}</Label>
 {bounds&&i>0&&<Label x={start+i*dx+27} y={91} anchor="middle" size={13}>≤ {help?4:2**(i-1)}</Label>}
 </g>)}
 {visible>=3&&!bounds&&<><Arrow x1={start+(visible-3)*dx+27} y1={143} x2={start+(visible-1)*dx+14} y2={185} label="copy" color={BLUE}/><Arrow x1={start+(visible-2)*dx+27} y1={162} x2={start+(visible-1)*dx+37} y2={204} label="copy"/><Label x={360} y={358} anchor="middle" size={15}>{terms[visible-3]} + {terms[visible-2]} = {terms[visible-1]}; preceding piles remain</Label></>}
 {bounds&&<Label x={360} y={358} anchor="middle" size={14}>Solid square = 1 counter · dashed square = 1 place of capacity</Label>}
 <Label x={360} y={55} anchor="middle" size={15}>{help?'1 + 2 = 3 ≤ 4':'F₀ = 0, F₁ = 1; Fₖ = Fₖ₋₁ + Fₖ₋₂'}</Label></>;
}
function Receipt({s,help,state}:{s:number;help:boolean;state:State}){
 const cards=help?[2,5,1]:[2,5,1,4],added=clamp(Math.ceil(s/2),0,cards.length),k=numberValue(state,'k',clamp(Math.floor(s/2),0,cards.length)),sum=cards.slice(0,added).reduce((a,b)=>a+b,0),checkpoint=k===added,dx=help?114:88;
 return <><Label x={50} y={32}>{checkpoint?'Checkpoint: total matches the first k cards':'Between instructions: the sum has changed before k'}</Label>
 <path d="M44 220v84h380v-84" fill="none" stroke="currentColor" opacity=".45"/>
 {cards.map((value,i)=><Move key={i} id={`card-${i}`} x={60+i*dx} y={i<added?226:85}><rect width={75} height={65} fill={i%2?ORANGE:BLUE}/>{Array.from({length:value},(_,j)=><circle key={j} cx={18+(j%3)*19} cy={22+Math.floor(j/3)*20} r="5" fill="white"/>)}<Label x={37} y={-12} anchor="middle" size={14}>a{i} = {value}</Label></Move>)}
 <Move id="prefix-boundary" x={50+k*dx} y={state.id==='boundary-before'?60:205}><path d="M0 0v96m-5-5 5 5 5-5" fill="none" stroke={RED} strokeWidth="2"/><Label x={0} y={-7} anchor="middle" size={13}>k</Label></Move><Label x={50} y={333} size={16}>Collected prefix</Label>
 <Label x={480} y={94} size={24}>k = {k}</Label><Label x={480} y={141} size={24}>s = {sum}</Label>
 <Label x={480} y={194} size={16}>{checkpoint?'Invariant holds here':'Update k next'}</Label>
 <Label x={480} y={227} size={16}>{cards.length-k} cards uncounted</Label>
 <Label x={480} y={279} size={16}>{s>=cards.length*2?'k = N: return the full sum':checkpoint?'s = sum of first k entries':'s ≠ sum of first k entries'}</Label>
 <Label x={50} y={364} size={14}>One dot = one unit · first {k} cards total {cards.slice(0,k).reduce((a,b)=>a+b,0)}</Label>
 {added>0&&<Label x={480} y={318} size={15}>{checkpoint?`Check: ${sum} = ${sum}`:`Add: ${sum-cards[added-1]} + ${cards[added-1]} = ${sum}`}</Label>}</>;
}
export function euclidPackages(m:number,n:number){
 const rows=[{id:'r0',value:m,a:1,b:0,q:0},{id:'r1',value:n,a:0,b:1,q:0}];
 while(rows.at(-1)!.value){const c=rows.at(-2)!,d=rows.at(-1)!,q=Math.floor(c.value/d.value),r=c.value-q*d.value;if(!r)break;rows.push({id:'r'+rows.length,value:r,a:c.a-q*d.a,b:c.b-q*d.b,q});}
 return rows;
}
type AlgebraBridge={equation:string;lines:string[];notes:string[];phase:number;positive:number;negative:number;result:number};
function SubstitutionBridge({bridge:b}:{bridge:AlgebraBridge}){
 const phase=clamp(b.phase,0,3),matched=phase===3;
 return <g data-teaching="substitution-bridge">
  <Label x={40} y={35} size={19}>Replace equals by equals; keep the outside sign</Label>
  <Label x={40} y={75} size={14}>Saved equation</Label>
  <rect x={36} y={88} width={214} height={49} rx={4} fill="none" stroke={ORANGE}/>
  <Move id="stored-equation" x={50} y={119}><Label x={0} y={0} size={21} color={ORANGE}>{b.equation}</Label></Move>
  <Label x={40} y={168} size={14}>{['1. Select the matching value','2. Replace the whole value','3. Multiply every inner term','4. Collect equal-sized copies'][phase]}</Label>
  <Label x={40} y={194} size={13}>{b.notes[phase]}</Label>
  <Arrow x1={249} y1={113} x2={287} y2={113}/>
  {b.lines.map((line,i)=><Move key={i} id={'algebra-line-'+i} x={302} y={81+i*47} o={i<=phase?1:.16}><Label x={0} y={0} size={21}>{line}</Label></Move>)}
  <Move id="algebra-active-line" x={286} y={65+phase*47}><path d="M0 0v21" stroke={ORANGE} strokeWidth={4}/></Move>
  <Label x={40} y={258} size={14}>{matched?'Match one slash to one unit:':'Same signed quantity at every line:'} {b.positive} − {b.negative} = {b.result}</Label>
  {Array.from({length:105},(_,i)=><Tile key={'p'+i} id={'bridge-positive-'+i} x={matched&&i>=b.negative?384+(i-b.negative)*15:40+(i%21)*13} y={matched&&i>=b.negative?287:277+Math.floor(i/21)*13} size={10} o={i<b.positive?(matched&&i<b.negative?.2:1):0}/>)}
  {Array.from({length:104},(_,i)=><Move key={'n'+i} id={'bridge-negative-'+i} x={matched?40+(i%21)*13:384+(i%21)*13} y={277+Math.floor(i/21)*13} o={i<b.negative?(matched?.55:1):0}><path d="M0 0L10 10M10 0L0 10" stroke={RED}/></Move>)}
  {matched&&<Label x={384} y={326} size={14}>{b.result} unit{b.result===1?' remains':'s remain'}</Label>}
  <Label x={360} y={361} anchor="middle" size={13}>Square = add one unit · slash = remove one unit · value stays {b.result}</Label>
 </g>;
}
function CoefficientBridge({m,n,cycle,phase}:{m:number;n:number;cycle:number;phase:number}){
 const rows=euclidPackages(m,n),c=rows[cycle],d=rows[cycle+1],r=rows[cycle+2],q=r.q;
 const lines=[`${c.value} − ${q} × ${d.value} = ${r.value}`,`(${c.a} × ${m} + (${c.b}) × ${n}) − ${q} × (${d.a} × ${m} + (${d.b}) × ${n})`,`${c.a} × ${m} + (${c.b}) × ${n} + (${-q*d.a}) × ${m} + (${-q*d.b}) × ${n}`,`(${c.a} − ${q} × ${d.a}) × ${m} + (${c.b} − ${q} × ${d.b}) × ${n} = ${r.value}`];
 return <g data-teaching="coefficient-bridge">
  <Label x={40} y={34} size={19}>Both recipes count the fixed originals {m} and {n}</Label>
  <Label x={40} y={69} size={15}>Length</Label><Label x={326} y={69} size={15} color={BLUE}>copies of {m}</Label><Label x={504} y={69} size={15} color={ORANGE}>copies of {n}</Label>
  {[c,d,r].map((row,i)=><Move key={row.id} id={'coefficient-package-'+row.id} x={40} y={99+i*54} o={i<2||phase>=3?1:.16}>
   {Array.from({length:row.value},(_,j)=><rect key={j} x={j*7} y={0} width={6} height={17} fill={i===1?ORANGE:BLUE}/>)}
   <Label x={205} y={15} size={17}>{row.value}</Label>
   <Label x={310} y={15} size={20} color={BLUE}>{row.a}</Label><Label x={495} y={15} size={20} color={ORANGE}>{row.b}</Label>
  </Move>)}
  <Move id="coefficient-operation" x={286} y={phase>=2?186:133}><Label x={0} y={0} size={15}>− {q} ×</Label><Label x={185} y={0} size={15}>− {q} ×</Label></Move>
  {phase>=2&&<><Label x={325} y={241} size={15}>{c.a} − {q} × ({d.a}) = {r.a}</Label><Label x={503} y={241} size={15}>{c.b} − {q} × ({d.b}) = {r.b}</Label></>}
  <Label x={40} y={277} size={14}>{['Select the old two rows; use quotient '+q,'Replace both lengths by their entire recipes','Distribute −'+q+' to both coefficients','Collect copies in each fixed-original column'][phase]}</Label>
  <Label x={40} y={309} size={phase===0?23:17}>{lines[phase]}</Label>
  <Label x={40} y={348} size={16}>{phase===3?`(${c.a}, ${c.b}) − ${q} × (${d.a}, ${d.b}) = (${r.a}, ${r.b}); ${r.a*m} + (${r.b*n}) = ${r.value}`:`${c.value} = ${c.a} × ${m} + (${c.b}) × ${n};   ${d.value} = ${d.a} × ${m} + (${d.b}) × ${n}`}</Label>
 </g>;
}
type Scene=State & {legacyHelper?:string;helperPhase?:number;trialPhase?:number;boundPhase?:number;bridge?:AlgebraBridge;recipeCycle?:number;recipePhase?:number;kind?:string;scene?:Scene;rows?:number;columns?:number;terms?:number[];active?:number;total?:number;registers?:{symbol:string;value:unknown}[];left?:{value:number;coefficient?:number;label?:string}[];right?:{value:number}[]};
function Euclid({s,help,extended,state}:{s:number;help:boolean;extended:boolean;state:Scene}){
 const m=help?14:26,n=help?6:15,rows=euclidPackages(m,n),last=rows.length-1;
 if(state.bridge)return <SubstitutionBridge bridge={state.bridge}/>;
 if(extended&&state.recipeCycle!==undefined)return <CoefficientBridge m={m} n={n} cycle={state.recipeCycle} phase={state.recipePhase??3}/>;
 if(!extended&&state.kind==='balance'){
  const terms=state.left||[{value:m,coefficient:help?1:-4},{value:n,coefficient:help?-2:7}],add=terms.filter(t=>(t.coefficient??1)>0).reduce((a,t)=>a+t.value*(t.coefficient??1),0),remove=-terms.filter(t=>(t.coefficient??1)<0).reduce((a,t)=>a+t.value*(t.coefficient??1),0),cancel=state.id==='identity'||s>=10,columns=help?14:add>21?21:Math.max(4,add),size=help?25:17,gap=size+3,offset=50;
  return <><Label x={50} y={32}>A signed recipe: add units, then remove matched units</Label>
   <Label x={50} y={65} size={15}>{cancel?'Match each requested removal to one positive unit':`Positive part: ${add} units`}</Label>
   {Array.from({length:help?16:105},(_,i)=><Tile key={'a'+i} id={'signed-add-'+i} x={cancel&&i>=remove?535+(i-remove)*gap:offset+(i%columns)*gap} y={cancel&&i>=remove?216:88+Math.floor(i/columns)*gap} size={size} color={BLUE} o={i<add?(cancel&&i<remove?.15:1):0}/>)}
   {Array.from({length:help?14:104},(_,i)=><Move key={'r'+i} id={'signed-remove-'+i} x={offset+(i%columns)*gap} y={cancel?88+Math.floor(i/columns)*gap:218+Math.floor(i/columns)*gap} o={i<remove?(cancel?.4:1):0}><rect width={size} height={size} fill="none" stroke={RED}/><path d={`M3 3L${size-3} ${size-3}`} stroke={RED}/></Move>)}
   {!cancel&&<Label x={50} y={204} size={15}>Negative part: remove {remove} units</Label>}
   {terms.map((t,i)=><Label key={i} x={510} y={85+i*28} size={14}>{t.coefficient??1} × {t.value} = {(t.coefficient??1)*t.value}</Label>)}
   <Label x={510} y={175} size={14}>{cancel?'Uncancelled units':'One square = one unit'}</Label>
   <Label x={510} y={195} size={14}>{cancel?`r = ${add-remove}`:'Slash = remove one'}</Label>
   <Label x={360} y={352} anchor="middle" size={18}>{add} − {remove} = {add-remove}{cancel?' · the GCD remains':''}</Label></>;

 }
 const cycle=extended?Math.min(Math.floor(s/3),last-1):clamp(s-1,0,last-1),phase=extended?s%3:(s>0?1:0),made=extended?Math.min(last,cycle+(phase>0?2:1)):Math.min(last,s+1),shifted=extended?cycle:Math.max(0,s-1),current=clamp(shifted,0,last-1),isReturn=extended&&s>=((last-1)*3+2),unit=help?18:10;
 return <><Label x={50} y={32}>{extended?`Every recipe uses the fixed originals ${m} and ${n}`:'Keep the leftover; record each exact subtraction'}</Label>
 {rows.map((r,i)=>{
   const archive=i<current,ready=i<=made,slot=i-current,y=archive?318:76+Math.min(2,Math.max(0,slot))*76,x=archive?48+i*108:70,opacity=ready?(archive?.32:1):0,tagged=!extended||i<cycle+2||phase===2||isReturn;
   return <Move key={r.id} id={`recipe-${r.id}`} x={!ready&&i>=2?70+(rows[i-2].value-r.value)*unit:x} y={isReturn&&i===last?174:!ready&&i>=2?76+clamp(i-2-current,0,2)*76:y} o={isReturn&&i!==last?.25:opacity}>
    {Array.from({length:r.value},(_,j)=><rect key={j} x={j*unit*(archive?.3:1)} y={0} width={unit*(archive?.3:1)-1} height={archive?11:28} fill={i%2?ORANGE:BLUE}/>)}
    {archive&&<Label x={0} y={29} size={13}>{r.value} units</Label>}{!archive&&<><Label x={-15} y={21} anchor="end" size={19}>{r.value}</Label>{extended&&<Move id={'tag-'+r.id} x={0} y={state.id==='attach-before'?42:0}><path d={`M${r.value*unit+6} 14H305`} stroke="currentColor" strokeDasharray={tagged?undefined:'4 4'} opacity=".4"/><Label x={323} y={21} size={17}>{tagged?`${r.a} × ${m} + (${r.b}) × ${n}`:'Attach recipe'}</Label></Move>}
    {!extended&&i>1&&<Label x={320} y={21} size={19}>{rows[i-2].value} − {r.q} × {rows[i-1].value} = {r.value}</Label>}</>}
   </Move>;
 })}
 <Label x={360} y={290} anchor="middle" size={15}>{isReturn?`${rows[last-1].value} = ${Math.floor(rows[last-1].value/rows[last].value)} × ${rows[last].value} + 0; return ${rows[last].value} with its recipe`:extended?'The length and its two coefficients move together.':'A common divisor of the two lengths divides their leftover.'}</Label>
 {extended&&!isReturn&&<Label x={360} y={55} anchor="middle" size={14}>{phase===0?(cycle===0?'Initialize: each input starts with its own exact recipe':'Carry: move each length with its own coefficient pair'):phase===1?`Divide: ${rows[cycle].value} = ${rows[cycle+2]?.q??Math.floor(rows[cycle].value/rows[cycle+1].value)} × ${rows[cycle+1].value} + ${rows[cycle+2]?.value??0}`:`Update both coefficients with the same quotient q = ${rows[cycle+2]?.q??0}`}</Label>}
 {extended&&cycle===last-1&&phase===1&&!isReturn&&<><rect x={70} y={228} width={24} height={25} fill="none" stroke={RED}/><Label x={110} y={247} size={15}>0 units: stop before any division by zero</Label></>}
 {!extended&&state.id==='division-4'&&<Label x={360} y={55} anchor="middle" size={15}>Final check: 3 = 3 × 1 + 0; the last nonzero length is 1</Label>}
 {current>0&&<Label x={675} y={337} anchor="end" size={13}>Earlier lengths, kept for reference</Label>}</>;
}
function SmallEuclidHelper({kind,s}:{kind:string;s:number}){
 const record=kind==='record',certificate=kind==='certificate',shift=kind==='shift',finish=kind==='finish';
 if(shift||finish){
  const promoted=shift&&s>=0,inserted=shift&&s>=1,returned=finish&&s>=1;
  const packages=[{id:'fourteen',v:14,a:1,b:0},{id:'six',v:6,a:0,b:1},{id:'two',v:2,a:1,b:-2}];
  return <g data-teaching="small-euclid-packages">
   <Label x={40} y={34} size={19}>{shift?'Move each length together with its exact recipe':'A zero leftover ends the algorithm; keep the two-unit row'}</Label>
   <Label x={40} y={67} size={15}>Fixed originals: 14 and 6</Label>
   {packages.map((r,i)=>{const y=finish?(i===0?304:i===1?105:181):promoted?(i===0?304:i===1?105:inserted?181:246):100+i*73;return <Move key={r.id} id={'small-package-'+r.id} x={70} y={y} o={i===0&&(promoted||finish)?.25:returned&&i===1?.3:1}>
    {Array.from({length:r.v},(_,j)=><rect key={j} x={j*15} y={0} width={13} height={24} fill={i===1?ORANGE:BLUE}/>)}
    <Label x={235} y={19} size={17}>{r.v} = {r.a} × 14 + ({r.b}) × 6</Label>
    <Label x={525} y={19} size={15}>{i===0?'old first row':i===1?(promoted||finish?'first row c':'old second row'):inserted||finish?'second row d':'new remainder'}</Label>
   </Move>;})}
   {finish&&s>=0&&<>{[0,1,2].map(i=><rect key={i} x={70+i*30} y={105} width={28} height={24} fill="none" stroke={BLUE} strokeWidth={2}/>)}<Label x={70} y={155} size={14}>3 groups of 2; every unit is used</Label></>}
   {finish&&<><Label x={40} y={263} size={20}>6 = 3 × 2 + 0</Label><Move id="zero-leftover" x={280} y={s>=0?240:200} o={s>=0?1:0}><rect width={30} height={28} fill="none" stroke={RED}/><Label x={43} y={21} size={15}>0 left over; do not divide by zero</Label></Move></>}
   <Label x={40} y={356} size={16}>{returned?'Return d = 2, a = 1, b = −2; 14 − 2 × 6 = 2':shift?(s<0?'Keep the old rows until the new recipe is ready':s===0?'Promote six with (0, 1); two is still waiting below':'Insert two with (1, −2); both working rows are now ready'):'Keep the current divisor 2 and its recipe (1, −2)'}</Label>
  </g>;
 }
 const removed=certificate?s>=0:!record&&s>=1,matched=certificate?s>=0:!record&&s>=1,tiled=record&&s>=0;
 return <g data-teaching="small-euclid-equation">
  <Label x={40} y={34} size={19}>{record?'Save how the leftover was made':certificate?'Check the recipe, then check the common measuring piece':'Start with fourteen; remove two groups of six'}</Label>
  <Label x={40} y={74} size={16}>14 original units</Label>
  {Array.from({length:14},(_,i)=><Tile key={i} id={'small-fourteen-'+i} x={55+i*39} y={106} size={31} color={BLUE} o={matched&&i<12?.25:1}/>)}
  {[0,1].map(group=><Move key={group} id={'six-group-'+group} x={55+group*6*39} y={tiled||matched?106:181} o={record?(s>=0?1:0):certificate||removed?1:0}>
   <rect width={6*39-8} height={31} fill="none" stroke={ORANGE} strokeWidth={2}/>
   {Array.from({length:6},(_,j)=><path key={j} d={`M${j*39+4} 4l23 23`} stroke={RED} opacity={record?0:1}/>)}
   <Label x={111} y={58} anchor="middle" size={15}>{record?'one six-unit stick':'remove 6'}</Label>
  </Move>)}
  {record&&s>=0&&<Bracket x={55+12*39} y={151} w={70} label="leftover 2"/>}
  {record&&s>=1&&<Label x={55} y={201} size={20}>14 = 2 × 6 + 2</Label>}
  <Move id="saved-small-equation" x={55} y={record&&s>=1?231:267} o={record&&s<0?0:1}>
   <Label x={0} y={0} size={23}>{record?(s>=1?'2 = 14 − 2 × 6':'14 = 2 × 6 + 2'):removed||certificate?'14 − 6 − 6 = 2':'14 units, with nothing removed yet'}</Label>
   {record&&s>=1&&<Label x={0} y={32} size={15}>Subtract the same two sixes from both sides; keep the leftover equation.</Label>}
  </Move>
  {certificate&&s>=1&&<><Label x={40} y={202} size={16}>14 = 7 × 2</Label><Label x={380} y={202} size={16}>6 = 3 × 2</Label>{Array.from({length:10},(_,i)=>{const left=i<7,j=left?i:i-7;return <g key={i}><rect x={(left?40:380)+j*42} y={214} width={34} height={18} fill="none" stroke={ORANGE}/><rect x={(left?43:383)+j*42} y={217} width={12} height={12} fill={BLUE}/><rect x={(left?59:399)+j*42} y={217} width={12} height={12} fill={BLUE}/></g>;})}</>}
  <Label x={360} y={349} anchor="middle" size={16}>{certificate&&s>=1?'Two divides both originals; the signed identity forces every common divisor to divide two.':record?'Same fourteen units: two sixes and the same leftover two.':removed?'Twelve removals match twelve units. The last two stay.':'One square is one unit; no unit has a negative length.'}</Label>
 </g>;
}
function LegacyHelper({kind,s}:{kind:string;s:number}){
 const [lesson,section]=kind.split('/');
 if(lesson==='4'){
  const stage=section==='simultaneous'?(s<1?3:6):section==='safe-swap'?(s<0?3:s+4):section==='lost-value'?(s<0?0:s+1):(s<1?0:1);
  return <><Assignment s={stage} help state={{id:section==='simultaneous'?(s<0?'parallel-before':s===0?'capture-parallel':'parallel'):''}}/>{section==='meaning'&&s===0&&<><rect x={308} y={132} width={106} height={76} fill="none" stroke={ORANGE} strokeWidth={3}/><Label x={360} y={108} anchor="middle" size={15}>Read this 12 first</Label></>}{section==='simultaneous'&&s===0&&<Move id="captured-pair" x={500} y={240}><rect x={-13} y={-26} width={137} height={39} fill="none" stroke={ORANGE}/><Label x={0} y={0} size={18}>(12, 7) saved</Label></Move>}</>;
 }
 if(lesson==='5'){
  if(section==='reach')return <><Label x={40} y={35} size={19}>A start and the same valid next-step rule reach any finite step</Label>{[1,2,3,4].map((n,i)=><g key={n}><rect x={75+i*150} y={180-i*22} width={98} height={55} fill="none" stroke={BLUE}/><Label x={124+i*150} y={215-i*22} anchor="middle" size={19}>P({n})</Label>{i<3&&<Arrow x1={173+i*150} y1={190-i*22} x2={218+i*150} y2={168-i*22} label="same rule"/>}<Move id={'step-check-'+n} x={124+i*150} y={s>=1?137-i*22:105} o={s>=1||s>=0&&i===0?1:0}><Label x={0} y={0} anchor="middle" size={24}>✓</Label></Move></g>)}<Label x={360} y={296} anchor="middle">{s<0?'First justify a starting case and the next-step rule.':s===0?'P(1) is established.':'P(1) → P(2) → P(3) → P(4): no step is skipped.'}</Label><Label x={360} y={338} anchor="middle" size={15}>Four is an example; the proven rule works for any requested finite step.</Label></>;
  const n=section==='claim'?1:section==='geometry'?2:3,stage=section==='claim'?0:section==='geometry'?(s<0?1:s===0?2:3):s<0?1:2;
  return <><Triangle s={stage} help n={n}/><Move id="small-triangle-equation" x={360} y={55} o={s>=1?1:0}><Label x={0} y={0} anchor="middle" size={17}>{section==='claim'?'1 × 2 ÷ 2 = 1':section==='step'?'3 old + 3 new = 6 = 3 × 4 ÷ 2':'Two equal groups: 6 ÷ 2 = 3'}</Label></Move></>;
 }
 if(lesson==='8'){
  const stage=section==='transient'?(s<0?2:s===0?3:4):section==='exit'?(s<0?5:s===0?6:7):section==='termination'?(s<0?0:2):0;
  return <><Receipt s={stage} help state={{id:section==='location'&&s<0?'boundary-before':''}}/>{section==='termination'&&s>=1&&<><rect x={472} y={208} width={196} height={29} fill="none" stroke={ORANGE}/><Label x={480} y={352} size={14}>3 − 1 = 2 remain</Label></>}</>;
 }
 if(lesson==='9'||lesson==='10')return <SmallEuclidHelper kind={section} s={s}/>;
 return <HelpScene model={lesson==='6'?'prime':lesson==='7'?'two-predecessors':''} intro={section==='observations'?'envelopes':section==='quantifier'?'every card':section==='two-bases'?'previous two piles':section==='scope'?'labels on boxes':''} s={s}/>;
}
function HelpScene({model,intro,s}:{model:string;intro:string;s:number}){
 if(/assignment/.test(model)){
  const stage=/snapshot/.test(intro)?(s<1?3:6):/no spare/.test(intro)?(s<0?0:Math.min(2,s+1)):/spare/.test(intro)?(s<0?3:Math.min(6,s+4)):(s<1?0:1);
  return <Assignment s={stage} help state={{id:/snapshot/.test(intro)?'parallel':''}}/>;
 }
 if(/triang/.test(model)){
  const geometry=/2 by 3/.test(intro),base=/one row/.test(intro),n=geometry?2:base?1:3;
  return <Triangle s={/bridge/.test(intro)?(s<0?-1:s===0?0:2):geometry?(s<0?1:s===0?2:3):base?(s<0?-1:0):s<0?1:2} help n={n}/>;
 }
 if(/prime/.test(model)){
  if(/For 7|seven/.test(intro))return <TrialPrime s={s+1} help/>;
  if(/envelope|every card/.test(intro))return <><Label x={50} y={35}>Check individual cases; leave untested cases open</Label>{Array.from({length:8},(_,i)=><Move key={i} id={'envelope-'+i} x={60+i*80} y={i<4&&s>=0?170:95}><rect width="57" height="80" fill={/every card/.test(intro)&&i===4&&s>=0?RED:i<4&&s>=0?BLUE:'none'} stroke="currentColor"/><Label x={28} y={47} anchor="middle" size={24}>{i<4&&s>=0?'✓':/every card/.test(intro)&&i===4&&s>=0?'×':'?'}</Label></Move>)}<Label x={360} y={295} anchor="middle">{/every card/.test(intro)&&s>=0?'One red card refutes “every card is blue.”':'Four checked cases do not settle all the others.'}</Label><Label x={360} y={330} anchor="middle" size={14}>{/every card/.test(intro)?'One counterexample is enough; other cards stay unchanged':'4 observed cards · ? on each untested card'}</Label>{/every card/.test(intro)?<><Label x={360} y={364} anchor="middle" size={16}>Claim: every card is blue</Label>{s>=1&&<path d="M265 356H455" stroke={RED} strokeWidth={2}/>}</>:<Move id="checked-untested-boundary" x={370} y={s>=1?77:96} o={s>=0?1:0}><path d="M0 0v188" stroke={ORANGE} strokeWidth={2}/></Move>}</>;
  if(/15/.test(intro))return <><Label x={50} y={35}>Try two rows, then three rows</Label>{Array.from({length:15},(_,i)=><Tile key={i} id={'fifteen-'+i} x={100+(i%(s>=1?5:8))*40} y={95+Math.floor(i/(s>=1?5:8))*40} size={35} color={i===14&&s<1?RED:BLUE}/>)}<Label x={360} y={290} anchor="middle">{s>=1?'Three equal rows of five: 15 = 3 × 5':'Two rows cannot have equal whole-number lengths.'}</Label></>;
  return <Prime s={s<0?0:3} help/>;
 }
 if(/predecessor/.test(model)){
  if(/small boxes/.test(intro))return <PredecessorBound phase={clamp(s+1,0,3)} help/>;
  const bases=/one counter|previous two piles/.test(intro),scope=/labels on boxes/.test(intro),capacity=/small boxes/.test(intro),merged=s>=0;
  if(scope)return <><Label x={50} y={35}>Only already justified cases may support the next case</Label>{[1,2,3].map((n,i)=><g key={n}><rect x={110+i*195} y={145} width={90} height={65} fill="none" stroke={i===2?ORANGE:BLUE}/><Move id={'scope-'+n} x={155+i*195} y={s>=0?177:110} o={i===2?(s>=1?1:0):s>=0?1:0}><Label x={0} y={5} anchor="middle" size={20}>P({n}) ✓</Label></Move><Label x={155+i*195} y={244} anchor="middle" size={14}>{i===2?'conclusion':'earlier case'}</Label></g>)}{s>=1&&<><Arrow x1={155} y1={135} x2={530} y2={135}/><Arrow x1={350} y1={265} x2={545} y2={265}/></>}<Label x={360} y={320} anchor="middle">P(1) and P(2) → P(3); no arrow points back</Label></>;
  if(capacity)return <><Label x={50} y={35}>Combine the permitted capacities before comparing</Label>{Array.from({length:4},(_,i)=><rect key={i} x={210+i*55} y={205} width={45} height={45} fill="none" stroke="currentColor" strokeDasharray="4 4" opacity={s>=1?1:.2}/>)}{Array.from({length:3},(_,i)=><Move key={i} id={'capacity-place-'+i} x={merged?210+i*55:i<2?120+i*55:440} y={merged?205:110}><rect width={45} height={45} fill="none" stroke={i<2?BLUE:ORANGE} strokeWidth={2}/></Move>)}<Label x={360} y={297} anchor="middle">2 places + 1 place = 3 places ≤ 4 places</Label><Label x={360} y={331} anchor="middle" size={14}>Outlines represent capacity, not actual sequence values</Label></>;
  if(bases)return <><Label x={50} y={35}>Two initial cases support a two-predecessor rule</Label>{[0,1].map(i=><rect key={'empty-'+i} x={180+i*230} y={150} width={42} height={42} fill="none" stroke="currentColor" strokeDasharray="3 3"/>)}{[0,1].map(i=><Tile key={i} id={'base-pile-'+i} x={180+i*230} y={s>=i?150:90} size={42} o={s>=i?1:0}/>)}<Label x={200} y={250} anchor="middle">{s>=0?'First case: 1':'First case: empty'}</Label><Label x={430} y={250} anchor="middle">{s>=1?'Second case: 1':'Second case: empty'}</Label></>;
  return <><Label x={50} y={35}>Actual blocks and available capacity are different</Label>{Array.from({length:4},(_,i)=><rect key={i} x={205+i*55} y="200" width="45" height="45" fill="none" stroke="currentColor" strokeDasharray="4 4" opacity={s>=1?1:.2}/>)}{Array.from({length:3},(_,i)=><Tile key={i} id={'bound-block-'+i} x={merged?205+i*55:i===0?140:365+(i-1)*55} y={merged?200:100} size={45} color={i===0?BLUE:ORANGE}/>)}<Label x={360} y={295} anchor="middle">1 + 2 = 3 ≤ 4; one space may stay empty</Label></>;
 }
 if(/prefix/.test(model)){
  const stage=/receipt says 2/.test(intro)?(s<0?2:s===0?3:4):/all three/.test(intro)?(s<0?5:s===0?6:7):/three remain/.test(intro)?(s<0?0:s===0?1:2):0;
  return <Receipt s={stage} help state={{id:/empty receipt/.test(intro)&&s<0?'boundary-before':''}}/>;
 }
 if(/bezout/.test(model)){
  const substitute=/whole expression|substitute/.test(intro),expanded=substitute&&s>=1,cancel=!substitute&&s>=1;
  if(substitute)return <SubstitutionBridge bridge={{equation:'12 = 2 × 6',lines:['2 = 14 − 12','2 = 14 − (2 × 6)','2 = 1 × 14 + (−2) × 6','2 = 14 − 12'],notes:['Choose the 12 being removed','Keep the minus outside','−1 × 2 = −2 copies of six','14 positive units; remove 12'],phase:clamp(s+1,0,3),positive:14,negative:12,result:2}}/>;
  return <><Euclid s={cancel?10:6} help extended={false} state={{kind:'balance',id:cancel?'identity':'help',left:substitute?(expanded?[{value:8,coefficient:2},{value:14,coefficient:-1}]:[{value:8,coefficient:1},{value:6,coefficient:-1}]):[{value:14,coefficient:1},{value:6,coefficient:-2}]}}/>{/divides/.test(intro)&&s>=1&&<Label x={360} y={325} anchor="middle" size={15}>Common divisor check: 14 = 7 × 2; 6 = 3 × 2</Label>}</>;
 }
 if(/extended/.test(model)){
  if(/fourteen-unit stick|quotient two/.test(intro))return <CoefficientBridge m={14} n={6} cycle={0} phase={clamp(s+1,0,3)}/>;
  const stage=/move the six/.test(intro)?(s<0?2:3):/next division/.test(intro)?(s<0?3:s===0?4:5):/quotient two/.test(intro)?(s<0?0:s===0?1:2):0;
  return <Euclid s={stage} help extended state={{id:/fourteen-unit stick/.test(intro)&&s<0?'attach-before':''}}/>;
 }
 return null;
}
const assignmentStages:Record<string,number>={start:0,'bad-first':1,'bad-second':2,restart:3,reset:3,save:4,'copy-b':5,finish:6,parallel:6};
export function FoundationsDemo({exampleId='',frameIndex=0,frame={},visual={},motionPaused,paused,reducedMotion=false}:FoundationsDemoProps){
 const raw=(visual.state||{}) as Scene,state=(raw.scene||raw),model=typeof visual.model==='string'?visual.model:String(visual.model?.kind||''),key=[exampleId,model,String(visual.lessonId||frame.lessonId||'')].join(' '),id=String(raw.id||frame.id||state.id||''),help=Boolean(visual.helpMode),s=help?(visual.helpStepIndex??frameIndex):frameIndex;
 let scene:ReactNode;
 if(help&&state.legacyHelper)scene=<g data-teaching="legacy-helper"><LegacyHelper kind={state.legacyHelper} s={state.helperPhase??-1}/></g>;
 else if(state.trialPhase!==undefined)scene=<TrialPrime s={state.trialPhase} help={help}/>;
 else if(state.boundPhase!==undefined)scene=<PredecessorBound phase={state.boundPhase} help={help}/>;
 else if(help&&(state.bridge||state.recipeCycle!==undefined))scene=<Euclid s={s} help extended={state.recipeCycle!==undefined} state={state}/>;
 else if(help)scene=<HelpScene model={model} intro={visual.helpContent?.intro||''} s={s}/>;
 else if(/assignment|copy|swap/i.test(key))scene=<Assignment s={assignmentStages[id]??s} help={help} state={{...state,id:/simultaneous/.test(exampleId)&&id==='restart'?'restart-parallel':id}}/>;
 else if(/induction|triang/i.test(key))scene=<Triangle s={help?s:id==='rectangle'?5:typeof state.rows==='number'?state.rows-1:s===0?3:s===1?0:1} help={help}/>;
 else if(/examples|prime|counterexample/i.test(key))scene=<Prime s={help?s:id==='pattern-before'?-1:id==='pattern'?0:id==='universal'?1:id==='counterexample'?3:id==='chosen'?2:s} help={help}/>;
 else if(/predecessor|fibonacci/i.test(key))scene=<Fibonacci s={help?s:id==='bases-before'?-2:id==='bases'?1:id==='general'?6:id.startsWith('case-')?Number(id.split('-')[1])-1:s} help={help}/>;
 else if(/loop|prefix|assertion/i.test(key))scene=<Receipt s={help?s:id==='initialize'?0:id==='exit'?9:/add-(\d+)/.test(id)?2*Number(id.split('-')[1])+1:/advance-(\d+)/.test(id)?2*Number(id.split('-')[1])+2:s} help={help} state={state}/>;
 else if(/extended|ledger|recipe/i.test(key))scene=<Euclid s={help?s:id==='initialize'?0:id==='return'?14:/^(divide|recipe|shift)-(\d+)/.test(id)?3*(Number(id.split('-')[1])-1)+({divide:1,recipe:2,shift:3}[id.split('-')[0]]??0):s} help={help} extended state={{...state,id}}/>;
 else if(/linear|bezout|substitution/i.test(key))scene=<Euclid s={help?s:id==='goal'?0:id==='identity'?10:id.startsWith('division-')?Number(id.split('-')[1])+1:s} help={help} extended={false} state={{...state,id}}/>;
 else return null;
 return <svg ref={mountMotion} viewBox="0 0 720 370" role="img" aria-label={raw.caption||state.caption||'Animated mathematical demonstration'} data-foundations-demo={model||exampleId} data-frame={id||s} data-paused={motionPaused??paused??false} data-reduced={reducedMotion} style={{display:'block',width:'100%',height:'auto',overflow:'visible',fontFamily:'inherit',color:'var(--text-primary, currentColor)'}}><title>{String(frame.title||'Concrete demonstration')}</title><desc>{raw.caption||state.caption||'Objects keep their identity while moving between mathematical states.'}</desc><Label x={690} y={13} anchor="end" size={11}>Target values for this step</Label><g data-label-semantics="destination-state">{scene}</g></svg>;
}
