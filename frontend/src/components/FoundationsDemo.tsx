import type { ReactNode } from 'react';

/** Pure view for the original lesson player's right-hand demonstration panel.
 * No React singleton or hooks: the recovered original runtime owns playback. */
type Obj = { id: string; label?: string; value?: unknown; role?: string; location?: string; data?: Record<string, unknown> };
type State = { id?: string; caption?: string; formula?: string; objects?: Obj[] };
export type FoundationsDemoProps = { exampleId?: string; frameIndex?: number; frame?: Record<string, unknown>; visual?: { model?: Record<string, unknown> | string; state?: State; transition?: Record<string, unknown>; help?: unknown; helpMode?: boolean; helpContent?: {intro?:string;steps?:{action:string;text:string}[]}; helpStepIndex?:number; lessonId?:string; order?:number }; paused?: boolean; motionPaused?: boolean; reducedMotion?: boolean };
const BLUE='#3b82f6', ORANGE='#f59e0b', RED='#ef4444';
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
  const p=clamp(c.elapsed/850,0,1),e=p*p*(3-2*p);
  for(const t of c.tweens)write(t.el,{x:t.from.x+(t.to.x-t.from.x)*e,y:t.from.y+(t.to.y-t.from.y)*e,o:t.from.o+(t.to.o-t.from.o)*e});
  if(p<1)c.raf=requestAnimationFrame(tick);
 };
 const update=()=>{
  const els=Array.from(svg.querySelectorAll<SVGElement>('[data-motion-id]'));
  const sig=els.map(e=>[e.dataset.motionId,e.dataset.x,e.dataset.y,e.dataset.o].join(':')).join('|');
  if(sig===c.signature){if(c.tweens.length&&!c.raf&&c.elapsed<850){c.last=0;c.raf=requestAnimationFrame(tick);}return;}
  const first=!c.signature;c.signature=sig;cancelAnimationFrame(c.raf);c.elapsed=0;c.last=0;
  const reduced=svg.dataset.reduced==='true'||(typeof matchMedia!=='undefined'&&matchMedia('(prefers-reduced-motion: reduce)').matches);
  c.tweens=els.map(el=>{const to={x:Number(el.dataset.x||0),y:Number(el.dataset.y||0),o:Number(el.dataset.o??1)};const from=positions.get(el)||{x:Number(el.dataset.originX??to.x),y:Number(el.dataset.originY??to.y),o:Number(el.dataset.originO??to.o)};if(first||reduced)write(el,to);else write(el,from);return{el,from,to};});
  if(first||reduced)c.elapsed=850;else c.raf=requestAnimationFrame(tick);
 };
 c.observer=new MutationObserver(update);c.observer.observe(svg,{subtree:true,childList:true,attributes:true,attributeFilter:['data-x','data-y','data-o','data-paused','data-reduced']});update();
}
function Move({id,x,y,o=1,children}:{id:string;x:number;y:number;o?:number;children:ReactNode}){return <g key={id} data-motion-id={id} data-x={x} data-y={y} data-o={o}>{children}</g>;}
function Tile({id,x,y,size=23,color=BLUE,o=1}:{id:string;x:number;y:number;size?:number;color?:string;o?:number}){return <Move id={id} x={x} y={y} o={o}><rect width={size} height={size} fill={color}/></Move>;}
function Label({x,y,children,size=16,anchor='start',color='currentColor'}:{x:number;y:number;children:ReactNode;size?:number;anchor?:'start'|'middle'|'end';color?:string}){return <text x={x} y={y} fontSize={size} textAnchor={anchor} fill={color}>{children}</text>;}
function Bracket({x,y,w,label}:{x:number;y:number;w:number;label:string}){return <g><path d={`M${x} ${y-5}v5h${w}v-5`} fill="none" stroke="currentColor" opacity=".45"/><Label x={x+w/2} y={y+22} anchor="middle" size={15}>{label}</Label></g>;}
function Assignment({s,state}:{s:number;help:boolean;state:State}){
 const a=7,b=12,stage=clamp(s,0,6),bad=stage===1||stage===2,copy=bad||stage>=5,parallel=state.id==='parallel'||state.id==='restart-parallel';
 const x=[95,300,505];
 return <>
  <Label x={50} y={32}>{stage===3?'Reset to the same starting values':bad?'Copying overwrites the old value':'Keep names fixed; copy the current value'}</Label>
  {(parallel?['a','b']:['a','b','t']).map((n,i)=><g key={n}><path d={`M${x[i]} 113v116h119V113`} fill="none" stroke="currentColor" opacity=".5"/><Label x={x[i]+60} y={264} anchor="middle" size={22}>{n}</Label></g>)}
  <Move id="original-a" x={x[0]+14} y={copy?286:139} o={copy?.3:1}><rect width="90" height="62" fill={RED}/><Label x={45} y={40} anchor="middle" size={26}>{a}</Label></Move>
  <Move id="original-b" x={x[1]+14} y={stage===6?286:139} o={stage===6?.3:1}><rect width="90" height="62" fill={BLUE}/><Label x={45} y={40} anchor="middle" size={26}>{b}</Label></Move>
  <Move id="copy-b-a" x={copy?x[0]+14:x[1]+14} y={139} o={copy?1:0}><rect width="90" height="62" fill={BLUE}/><Label x={45} y={40} anchor="middle" size={26}>{b}</Label></Move>
  <Move id="save-a-t" x={stage>=4?x[2]+14:x[0]+14} y={139} o={stage>=4&&!parallel?1:0}><rect width="90" height="62" fill={RED}/><Label x={45} y={40} anchor="middle" size={26}>{a}</Label></Move>
  <Move id="copy-t-b" x={stage===6?x[1]+14:parallel?x[0]+14:x[2]+14} y={139} o={stage===6?1:0}><rect width="90" height="62" fill={RED}/><Label x={45} y={40} anchor="middle" size={26}>{a}</Label></Move>
  <Label x={360} y={84} anchor="middle" size={22}>{parallel?'(a, b) ← (b, a)':state.formula||['a = '+a+', b = '+b,'a ← b','b ← a','a = '+a+', b = '+b,'t ← a','a ← b','b ← t'][stage]}</Label>
  {parallel&&<><Label x={475} y={150} size={16}>Read old pair: (7, 12)</Label><Label x={475} y={195} size={16}>{stage===6?'Write new pair: (12, 7)':'Capture both: (12, 7)'}</Label></>}{copy&&<Label x={430} y={364} anchor="middle" size={14}>Overwritten copies, no longer stored</Label>}
 </>;
}
function Triangle({s,help,n:requestedN}:{s:number;help:boolean;n?:number}){
 const n=requestedN??(help?3:4),rows=clamp(s+1,0,n),pair=s>=n+1,copied=s>=n,size=help?40:35,gap=size+5,x=82,y=75;
 const cells=Array.from({length:n},(_,r)=>Array.from({length:r+1},(_,c)=>({r,c,id:`${r}-${c}`}))).flat();
 return <><Label x={50} y={32}>{pair?'Two equal triangles fill one rectangle':'Add the next row; keep every old tile'}</Label>
 {cells.map(t=><Tile key={t.id} id={'tri-'+t.id} x={t.r<rows?x+t.c*gap:432+t.c*gap} y={y+t.r*gap} size={size} color={t.r===rows-1&&!pair?ORANGE:BLUE}/>)}
 {cells.map(t=><Tile key={'copy-'+t.id} id={'tri-copy-'+t.id} x={pair?x+(n-t.c)*gap:432+t.c*gap} y={pair?y+(n-1-t.r)*gap:y+t.r*gap} size={size} color={ORANGE} o={copied?1:0}/>)}
 {pair?<><Bracket x={x} y={y+n*gap+6} w={(n+1)*gap-5} label={`${n+1} columns`}/><Label x={410} y={105}>{n} × {n+1} = {n*(n+1)} tiles</Label><Label x={410} y={140}>One triangle: {n*(n+1)} ÷ 2 = {n*(n+1)/2}</Label><Label x={410} y={185} size={15}>A finite picture illustrates the rule.</Label><Label x={410} y={210} size={15}>The general adding step proves it.</Label></>:<><Label x={x} y={292}>{rows} rows; {rows*(rows+1)/2} placed tiles</Label><Label x={432} y={292}>{copied?'Matching copy':'Waiting tiles'}</Label></>}
 <Label x={360} y={336} anchor="middle" size={18}>{pair?'k(k + 1)/2 + (k + 1) = (k + 1)(k + 2)/2':'New total = old total + next row'}</Label></>;
}
function Prime({s,help}:{s:number;help:boolean}){
 const square=s>=3,observations=!help&&s<2,n=help?3:11,total=n*n,unit=help?44:18,gap=unit+3,x=help?190:90,y=70;
 return <><Label x={50} y={32}>{help?'Nine dots can make three equal rows':'Many successful tests do not settle “every input”'}</Label>
 {Array.from({length:total},(_,i)=>{let px=x+(i%n)*gap,py=y+Math.floor(i/n)*gap;if(!square){if(help){px=82+(i%5)*50;py=110+Math.floor(i/5)*50;}else if(i<100){px=82+(i%10)*21;py=70+Math.floor(i/10)*21;}else if(i<110){px=315;py=70+(i-100)*21;}else{px=82+(i-110)*21;py=292;}}if(observations){const starts=[0,11,24,41];const group=i<11?0:i<24?1:i<41?2:3,local=i-starts[group];px=50+group*166+(local%6)*22;py=112+Math.floor(local/6)*24;if(s<0){px=350+(i%8)*2;py=80;}}return <Tile key={i} id={'prime-unit-'+i} x={px} y={py} size={unit} color={i<(help?6:100)?BLUE:ORANGE} o={observations&&(i>=64||s<0)?0:1}/>;})}
 {!observations&&<><Label x={425} y={92}>{help?'9 = 3 × 3':'f(n) = n² + n + 11'}</Label>
 <Label x={425} y={130} size={15}>{help?'Both factors exceed one.':'f(0), f(1), f(2), f(3) are prime.'}</Label>
 <Label x={425} y={163} size={15}>{help?'So nine is not prime.':'At n = 10: 100 + 10 + 11 = 121.'}</Label>
 <Label x={425} y={211} size={19}>{square?`${total} = ${n} × ${n}`:'Rearrange the same units →'}</Label>
 </>}{observations&&s>=0&&[11,13,17,23].map((v,i)=><Label key={v} x={50+i*166} y={87} size={16}>f({i}) = {v}: prime</Label>)}{square&&<Bracket x={x} y={y+n*gap+7} w={n*gap-3} label={`${n} rows, ${n} columns`}/>}
 <Label x={360} y={364} anchor="middle" size={16}>One allowed failure refutes a claim about every input.</Label></>;
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
 <Label x={480} y={279} size={17}>{s>=cards.length*2?'k = N: return the full sum':'s = sum of first k entries'}</Label></>;
}
export function euclidPackages(m:number,n:number){
 const rows=[{id:'r0',value:m,a:1,b:0,q:0},{id:'r1',value:n,a:0,b:1,q:0}];
 while(rows.at(-1)!.value){const c=rows.at(-2)!,d=rows.at(-1)!,q=Math.floor(c.value/d.value),r=c.value-q*d.value;if(!r)break;rows.push({id:'r'+rows.length,value:r,a:c.a-q*d.a,b:c.b-q*d.b,q});}
 return rows;
}
type Scene=State & {kind?:string;scene?:Scene;rows?:number;columns?:number;terms?:number[];active?:number;total?:number;registers?:{symbol:string;value:unknown}[];left?:{value:number;coefficient?:number;label?:string}[];right?:{value:number}[]};
function Euclid({s,help,extended,state}:{s:number;help:boolean;extended:boolean;state:Scene}){
 const m=help?14:26,n=help?6:15,rows=euclidPackages(m,n),last=rows.length-1;
 if(!extended&&state.kind==='balance'){
  const terms=state.left||[{value:m,coefficient:help?1:-4},{value:n,coefficient:help?-2:7}],add=terms.filter(t=>(t.coefficient??1)>0).reduce((a,t)=>a+t.value*(t.coefficient??1),0),remove=-terms.filter(t=>(t.coefficient??1)<0).reduce((a,t)=>a+t.value*(t.coefficient??1),0),cancel=state.id==='identity'||s>=10,columns=help?14:add>70?21:Math.min(21,Math.max(4,terms.find(t=>(t.coefficient??1)>0)?.value||4)),size=help?25:17,gap=size+3,offset=help?56:add<10?220:add<20?140:56;
  return <><Label x={50} y={32}>Use positive units; a minus sign requests removal</Label>
   {Array.from({length:help?16:105},(_,i)=><Tile key={'a'+i} id={'signed-add-'+i} x={offset+(i%columns)*gap} y={cancel&&i<remove?295:76+Math.floor(i/columns)*gap} size={size} color={BLUE} o={i<add?(cancel&&i<remove?.18:1):0}/>)}
   {Array.from({length:help?14:104},(_,i)=><Tile key={'r'+i} id={'signed-remove-'+i} x={offset+(i%columns)*gap} y={cancel?295:210+Math.floor(i/columns)*gap*.75} size={size} color={RED} o={i<remove?(cancel?.18:1):0}/>)}
   <Label x={56} y={61} size={16}>Add {add} units</Label><Label x={56} y={196} size={16}>Remove {remove} units</Label>
   <Label x={360} y={346} anchor="middle" size={18}>{add} − {remove} = {add-remove}{cancel?' · the GCD remains':''}</Label></>;
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
 <Label x={360} y={290} anchor="middle" size={17}>{isReturn?`${rows[last-1].value} = ${Math.floor(rows[last-1].value/rows[last].value)} × ${rows[last].value} + 0; return ${rows[last].value} with its recipe`:extended?'The length and its two coefficients move together.':'A common divisor of the two lengths divides their leftover.'}</Label>
 <Label x={490} y={337} size={13}>Earlier lengths, retained for reference</Label></>;
}
function HelpScene({model,intro,s}:{model:string;intro:string;s:number}){
 if(/assignment/.test(model)){
  const stage=/snapshot/.test(intro)?(s<1?3:6):/spare/.test(intro)?(s<0?3:Math.min(6,s+4)):/no spare/.test(intro)?(s<0?0:Math.min(2,s+1)):(s<1?0:1);
  return <Assignment s={stage} help state={{id:/snapshot/.test(intro)?'parallel':''}}/>;
 }
 if(/triang/.test(model)){
  const geometry=/2 by 3/.test(intro),base=/one row/.test(intro),n=geometry?2:base?1:3;
  return <Triangle s={geometry?(s<0?1:s===0?2:3):base?(s<0?-1:0):s<0?1:2} help n={n}/>;
 }
 if(/prime/.test(model)){
  if(/envelope|every card/.test(intro))return <><Label x={50} y={35}>Check individual cases; leave untested cases open</Label>{Array.from({length:8},(_,i)=><Move key={i} id={'envelope-'+i} x={60+i*80} y={i<4&&s>=0?170:95}><rect width="57" height="80" fill={/every card/.test(intro)&&i===4&&s>=0?RED:i<4&&s>=0?BLUE:'none'} stroke="currentColor"/><Label x={28} y={47} anchor="middle" size={24}>{i<4&&s>=0?'✓':/every card/.test(intro)&&i===4&&s>=0?'×':'?'}</Label></Move>)}<Label x={360} y={295} anchor="middle">{/every card/.test(intro)&&s>=0?'One red card refutes “every card is blue.”':'Four checked cases do not settle all the others.'}</Label></>;
  if(/15/.test(intro))return <><Label x={50} y={35}>Try two rows, then three rows</Label>{Array.from({length:15},(_,i)=><Tile key={i} id={'fifteen-'+i} x={100+(i%(s>=1?5:8))*40} y={95+Math.floor(i/(s>=1?5:8))*40} size={35} color={i===14&&s<1?RED:BLUE}/>)}<Label x={360} y={290} anchor="middle">{s>=1?'Three equal rows of five: 15 = 3 × 5':'Two rows cannot have equal whole-number lengths.'}</Label></>;
  return <Prime s={s<0?0:3} help/>;
 }
 if(/predecessor/.test(model)){
  const bases=/one counter|labels on boxes/.test(intro),merged=s>=0;
  if(bases)return <><Label x={50} y={35}>Two initial cases support a two-predecessor rule</Label>{[0,1].map(i=><Tile key={i} id={'base-pile-'+i} x={180+i*230} y={s>=i?150:90} size={42} o={s>=i?1:0}/>)}<Label x={200} y={250} anchor="middle">First case: 1</Label><Label x={430} y={250} anchor="middle">Second case: 1</Label></>;
  return <><Label x={50} y={35}>Actual blocks and available capacity are different</Label>{Array.from({length:4},(_,i)=><rect key={i} x={205+i*55} y="200" width="45" height="45" fill="none" stroke="currentColor" strokeDasharray="4 4" opacity={s>=1?1:.2}/>)}{Array.from({length:3},(_,i)=><Tile key={i} id={'bound-block-'+i} x={merged?205+i*55:i===0?140:365+(i-1)*55} y={merged?200:100} size={45} color={i===0?BLUE:ORANGE}/>)}<Label x={360} y={295} anchor="middle">1 + 2 = 3 ≤ 4; one space may stay empty</Label></>;
 }
 if(/prefix/.test(model)){
  const stage=/receipt says 2/.test(intro)?(s<0?2:s===0?3:4):/all three/.test(intro)?(s<0?5:s===0?6:7):/three remain/.test(intro)?(s<0?0:s===0?1:2):0;
  return <Receipt s={stage} help state={{id:/empty receipt/.test(intro)&&s<0?'boundary-before':''}}/>;
 }
 if(/bezout/.test(model)){
  const substitute=/8−6/.test(intro),expanded=substitute&&s>=1,cancel=!substitute&&s>=1;
  return <Euclid s={cancel?10:6} help extended={false} state={{kind:'balance',id:cancel?'identity':'help',left:substitute?(expanded?[{value:8,coefficient:2},{value:14,coefficient:-1}]:[{value:8,coefficient:1},{value:6,coefficient:-1}]):[{value:14,coefficient:1},{value:6,coefficient:-2}]}}/>;
 }
 if(/extended/.test(model)){
  const stage=/move the six/.test(intro)?(s<0?2:3):/next division/.test(intro)?(s<0?3:s===0?4:5):/quotient two/.test(intro)?(s<0?0:s===0?1:2):0;
  return <Euclid s={stage} help extended state={{id:/fourteen-unit stick/.test(intro)&&s<0?'attach-before':''}}/>;
 }
 return null;
}
const assignmentStages:Record<string,number>={start:0,'bad-first':1,'bad-second':2,restart:3,reset:3,save:4,'copy-b':5,finish:6,parallel:6};
export function FoundationsDemo({exampleId='',frameIndex=0,frame={},visual={},motionPaused,paused,reducedMotion=false}:FoundationsDemoProps){
 const raw=(visual.state||{}) as Scene,state=(raw.scene||raw),model=typeof visual.model==='string'?visual.model:String(visual.model?.kind||''),key=[exampleId,model,String(visual.lessonId||frame.lessonId||'')].join(' '),id=String(raw.id||frame.id||state.id||''),help=Boolean(visual.helpMode),s=help?(visual.helpStepIndex??frameIndex):frameIndex;
 let scene:ReactNode;
 if(help)scene=<HelpScene model={model} intro={visual.helpContent?.intro||''} s={s}/>;
 else if(/assignment|copy|swap/i.test(key))scene=<Assignment s={assignmentStages[id]??s} help={help} state={{...state,id:/simultaneous/.test(exampleId)&&id==='restart'?'restart-parallel':id}}/>;
 else if(/induction|triang/i.test(key))scene=<Triangle s={help?s:id==='rectangle'?5:typeof state.rows==='number'?state.rows-1:s===0?3:s===1?0:1} help={help}/>;
 else if(/examples|prime|counterexample/i.test(key))scene=<Prime s={help?s:id==='pattern-before'?-1:id==='pattern'?0:id==='universal'?1:id==='counterexample'?3:id==='chosen'?2:s} help={help}/>;
 else if(/predecessor|fibonacci/i.test(key))scene=<Fibonacci s={help?s:id==='bases-before'?-2:id==='bases'?1:id==='general'?6:id.startsWith('case-')?Number(id.split('-')[1])-1:s} help={help}/>;
 else if(/loop|prefix|assertion/i.test(key))scene=<Receipt s={help?s:id==='initialize'?0:id==='exit'?9:/add-(\d+)/.test(id)?2*Number(id.split('-')[1])+1:/advance-(\d+)/.test(id)?2*Number(id.split('-')[1])+2:s} help={help} state={state}/>;
 else if(/extended|ledger|recipe/i.test(key))scene=<Euclid s={help?s:id==='initialize'?0:id==='return'?14:/^(divide|recipe|shift)-(\d+)/.test(id)?3*(Number(id.split('-')[1])-1)+({divide:1,recipe:2,shift:3}[id.split('-')[0]]??0):s} help={help} extended state={{...state,id}}/>;
 else if(/linear|bezout|substitution/i.test(key))scene=<Euclid s={help?s:id==='goal'?0:id==='identity'?10:id.startsWith('division-')?Number(id.split('-')[1])+1:s} help={help} extended={false} state={{...state,id}}/>;
 else return null;
 return <svg ref={mountMotion} viewBox="0 0 720 370" role="img" aria-label={state.caption||'Animated mathematical demonstration'} data-foundations-demo={model||exampleId} data-frame={id||s} data-paused={motionPaused??paused??false} data-reduced={reducedMotion} style={{display:'block',width:'100%',height:'auto',overflow:'visible',fontFamily:'inherit',color:'var(--text-primary, currentColor)'}}><title>{String(frame.title||'Concrete demonstration')}</title><desc>{state.caption||'Objects keep their identity while moving between mathematical states.'}</desc>{scene}</svg>;
}
