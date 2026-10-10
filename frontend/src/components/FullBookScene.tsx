import { symbolTextChildren } from '../lib/symbolConnections.js';
import * as JSX from 'react/jsx-runtime';
import { bindFullBookMotion } from './fullBookMotion';
export interface DiagramNode {id:string;type:'rect'|'circle'|'line'|'path'|'text';x?:number;y?:number;width?:number;height?:number;r?:number;x2?:number;y2?:number;d?:string;text?:string;fontSize?:number;anchor?:'start'|'middle'|'end';fill?:string;stroke?:string;strokeWidth?:number;opacity?:number;role?:'input'|'active'|'result'|'muted'|'error';phase?:'source'|'transform'|'result';result?:boolean;arrow?:boolean}
export interface SemanticDiagram {title:string;description?:string;viewBox?:number[];nodes:DiagramNode[];invariant?:string}
interface Props {exampleId:string;frameIndex:number;paused?:boolean;visual?:{state?:{diagram?:SemanticDiagram};helpMode?:boolean;[key:string]:unknown}}
const tones={input:'#4389ef',active:'#d47b16',result:'#3d9a73',muted:'currentColor',error:'#ed5363'};
function Shape({node:n,marker}:{node:DiagramNode;marker:string}){
 const color=tones[n.role??'input'];const stroke=n.stroke??color;const fill=n.fill??(n.type==='text'?'currentColor':'none');
 const common={stroke,strokeWidth:n.strokeWidth??1.5,fill};
 switch(n.type){
  case 'rect':return <rect data-diagram-shape width={Math.max(0,n.width??0)} height={Math.max(0,n.height??0)} {...common}/>;
  case 'circle':return <circle data-diagram-shape r={Math.max(0,n.r??0)} {...common}/>;
  case 'line':return <line data-diagram-shape x2={(n.x2??n.x??0)-(n.x??0)} y2={(n.y2??n.y??0)-(n.y??0)} markerEnd={n.arrow?`url(#${marker})`:undefined} {...common}/>;
  case 'path':return <path d={n.d??''} markerEnd={n.arrow?`url(#${marker})`:undefined} {...common}/>;
  case 'text':return <text fontSize={n.fontSize??16} textAnchor={n.anchor??'start'} fill={n.fill??'currentColor'} stroke="none">{symbolTextChildren(n.text??'', JSX, true)}</text>;
 }
}
/** The shared renderer only draws authored, computed objects. All geometry,
 * identity, examples and invariants come from each topic's own semantic model. */
export function FullBookScene({visual,exampleId,frameIndex,paused=false}:Props){
 const d=visual?.state?.diagram;
 if(!d)return <p role="alert">This demonstration is missing its computed diagram.</p>;
 const key=`${exampleId}:${visual?.helpMode?'help':'main'}:${frameIndex}`;
 const marker=`fullbook-${exampleId.replace(/[^a-zA-Z0-9_-]/g,'-')}-${visual?.helpMode?'help':'main'}-arrow`;
 return <svg ref={svg=>bindFullBookMotion(svg,key,paused)} viewBox={(d.viewBox??[0,0,720,440]).join(' ')} role="img" aria-label={[d.title,d.description].filter(Boolean).join('. ')} style={{display:'block',width:'100%',height:'auto',overflow:'visible',color:'var(--color-text-main, currentColor)'}} data-fullbook-scene={exampleId}>
  <title>{d.title}</title><desc>{d.description??d.title}</desc>
  <defs><marker id={marker} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 Z" fill="context-stroke"/></marker></defs>
  {d.nodes.map(n=><g key={n.id} data-diagram-node={n.id} data-phase={n.phase} data-x={n.x??0} data-y={n.y??0} data-o={n.opacity??1} data-w={n.width??0} data-h={n.height??0} data-r={n.r??0} data-ex={(n.x2??n.x??0)-(n.x??0)} data-ey={(n.y2??n.y??0)-(n.y??0)} transform={`translate(${n.x??0} ${n.y??0})`} opacity={n.opacity??1}>
   <g data-diagram-result={n.result || (n.type==='text' && n.role==='result')?'true':undefined}><Shape node={n} marker={marker}/></g>
  </g>)}
 </svg>;
}
