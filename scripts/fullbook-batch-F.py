#!/usr/bin/env python3
"""Original exact models and authored scenes for companion units 123–144.
Run --test for exhaustive small-instance checks; run without flags to regenerate JSON.
Private source material is never copied into the output.
"""
import json, math, itertools, heapq, copy, sys
from pathlib import Path
from functools import lru_cache
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'content/fullbook/source-plan-F.json'

@lru_cache(None)
def binary(n):
    if n==0:return (None,)
    return tuple((l,r) for k in range(n) for l in binary(k) for r in binary(n-1-k))
def paths(t,d=0):
    if t is None:return (0,d,0,1)
    a,b=paths(t[0],d+1),paths(t[1],d+1)
    return (d+a[0]+b[0],a[1]+b[1],1+a[2]+b[2],a[3]+b[3])
def catalan(n):return math.comb(2*n,n)//(n+1)
def rooted_counts(n):
    a=[0,1]+[0]*max(0,n-1)
    for m in range(2,n+1):
        numerator=sum(sum(d*a[d] for d in range(1,k+1) if k%d==0)*a[m-k] for k in range(1,m))
        assert numerator%(m-1)==0
        a[m]=numerator//(m-1)
    return a[:n+1]
def free_counts(n):
    a=rooted_counts(n)
    return [0]+[a[k]-(sum(a[j]*a[k-j] for j in range(1,k))-(a[k//2] if k%2==0 else 0))//2 for k in range(1,n+1)]
def prufer_decode(code):
    n=len(code)+2; degree=[0]+[1]*n
    for x in code:degree[x]+=1
    edges=[]
    for x in code:
        leaf=next(i for i in range(1,n+1) if degree[i]==1)
        edges.append((leaf,x));degree[leaf]-=1;degree[x]-=1
    edges.append(tuple(i for i in range(1,n+1) if degree[i]==1))
    return edges

def prufer_encode(edges):
    adj=adjacency(edges); ans=[]
    while len(adj)>2:
        v=min(v for v in adj if len(adj[v])==1); u=next(iter(adj[v]));ans.append(u)
        adj[u].remove(v);del adj[v]
    return ans

def adjacency(edges,n=None):
    g={i:set() for i in range(1,(n or max(max(e) for e in edges))+1)}
    for a,b in edges:g[a].add(b);g[b].add(a)
    return g

def root_code(g,v,p=None):return '('+''.join(sorted(root_code(g,u,v) for u in g[v] if u!=p))+')'
def free_code(g):return min(root_code(g,v) for v in g)
def rooted_encode(edges,root):
    g=adjacency(edges); out=[]
    while len(g)>1:
        v=min(v for v in g if v!=root and len(g[v])==1);u=next(iter(g[v]));out.append(u);g[u].remove(v);del g[v]
    return out

def rooted_decode(code):
    available=set(range(1,len(code)+2));edges=[]
    for i,x in enumerate(code):
        v=min(available-set(code[i:]));edges.append((v,x));available.remove(v)
    return edges,next(iter(available))

def huffman(weights):
    h=[(w,i,str(i)) for i,w in enumerate(weights)];heapq.heapify(h); steps=[]; cost=0; serial=len(h)
    while len(h)>1:
        a,b=heapq.heappop(h),heapq.heappop(h);cost+=a[0]+b[0]
        c=(a[0]+b[0],serial,(a[2],b[2]));serial+=1;heapq.heappush(h,c)
        steps.append(dict(pair=[a[0],b[0]],sum=c[0],cost=cost,forest=copy.deepcopy(sorted(h))))
    return cost,steps
@lru_cache(None)
def optimal_merge(ws):
    if len(ws)<2:return 0
    return min(ws[i]+ws[j]+optimal_merge(tuple(sorted([ws[k] for k in range(len(ws)) if k not in (i,j)]+[ws[i]+ws[j]]))) for i in range(len(ws)) for j in range(i+1,len(ws)))

def reachable(g,roots):
    seen=set();todo=list(roots)
    while todo:
        x=todo.pop()
        if x is None or x in seen:continue
        seen.add(x);todo.extend(g[x])
    return seen

def mark_stack(g,roots):
    seen=set();todo=[];frames=[]
    for r in roots:
        if r not in seen:seen.add(r);todo.append(r)
    frames.append((set(seen),list(todo),None))
    while todo:
        x=todo.pop()
        for y in g[x]:
            if y is not None and y not in seen:seen.add(y);todo.append(y)
        frames.append((set(seen),list(todo),x))
    return seen,frames

def bounded_mark(g,roots,capacity):
    assert capacity>=1
    marked=set(roots);pending=list(roots)[:capacity];done=set();frames=[];scans=0
    while True:
        if not pending:
            scans+=1
            # Persistent mark minus processed bits is an explicit teaching variant.
            remaining=sorted(marked-done)
            if not remaining:break
            pending=remaining[:capacity]
        x=pending.pop();done.add(x)
        for y in g[x]:
            if y is not None and y not in marked:
                marked.add(y)
                if len(pending)<capacity:pending.append(y)
        frames.append((set(marked),list(pending),set(done),scans))
    return marked,frames

def reverse_mark(graph,root):
    # Exact Algorithm E control, with original ATOM bits preserved on restoration.
    g=copy.deepcopy(graph);p=root;t=None;pc=2;frames=[];mark=set()
    def snap(action):frames.append(dict(graph=copy.deepcopy(g),p=p,t=t,marked=sorted(mark),action=action))
    snap('Begin with the original links')
    while True:
        if pc==2:mark.add(p);snap('Mark the current object');pc=6 if g[p]['atom'] else 4
        elif pc==4:
            q=g[p]['a']
            if q is not None and q not in mark:
                g[p]['atom']=1;g[p]['a']=t;t,p=p,q;snap('Reverse the A field to save the return path');pc=2
            else:pc=5
        elif pc==5:
            q=g[p]['b']
            if q is not None and q not in mark:
                g[p]['b']=t;t,p=p,q;snap('Reverse the B field to save the return path');pc=2
            else:pc=6
        else:
            if t is None:break
            q=t
            if g[q]['atom']:
                g[q]['atom']=0;t=g[q]['a'];g[q]['a']=p;p=q;snap('Restore A and its temporary control bit');pc=5
            else:t=g[q]['b'];g[q]['b']=p;p=q;snap('Restore B and return to the parent');pc=6
        assert len(frames)<10000
    assert g==graph and p==root
    snap('All original links and ATOM bits are restored')
    return mark,frames

class Heap:
    def __init__(self,size,alignment=4,overhead=0,minblock=4):
        assert size>0 and size%alignment==0
        self.size=size;self.a=alignment;self.o=overhead;self.minimum=minblock;self.blocks=[dict(start=0,size=size,id=None,payload=0)];self.probes=0
    def validate(self):
        cursor=0
        for b in self.blocks:
            assert b['start']==cursor and b['size']>0 and b['start']%self.a==0 and b['size']%self.a==0
            assert b['payload']+ (self.o if b['id'] else 0)<=b['size'];cursor+=b['size']
        assert cursor==self.size and len({b['id'] for b in self.blocks if b['id']})==sum(b['id'] is not None for b in self.blocks)
    def alloc(self,name,payload,policy='first',maxint=2**31-1):
        assert name not in [b['id'] for b in self.blocks]
        if payload<=0 or payload>maxint-self.o-(self.a-1):return False
        needed=max(self.minimum,((payload+self.o+self.a-1)//self.a)*self.a); candidates=[]
        for i,b in enumerate(self.blocks):
            if b['id'] is None:
                self.probes+=1
                if b['size']>=needed:
                    candidates.append(i)
                    if policy=='first':break
        if not candidates:return False
        i=min(candidates,key=lambda k:(self.blocks[k]['size'],self.blocks[k]['start'])) if policy=='best' else candidates[0]
        old=self.blocks[i];size=needed if old['size']-needed>=self.minimum else old['size']
        new=[dict(start=old['start'],size=size,id=name,payload=payload)]
        if size<old['size']:new.append(dict(start=old['start']+size,size=old['size']-size,id=None,payload=0))
        self.blocks[i:i+1]=new;self.validate();return True
    def free(self,name):
        b=next(b for b in self.blocks if b['id']==name);b['id']=None;b['payload']=0
        out=[]
        for b in self.blocks:
            if out and out[-1]['id'] is None and b['id'] is None:out[-1]['size']+=b['size']
            else:out.append(copy.deepcopy(b))
        self.blocks=out;self.validate()
    def snapshot(self):return copy.deepcopy(self.blocks)
class TaggedHeap(Heap):
    """Physical merge decisions use boundary tags; array snapshots are instrumentation."""
    def __init__(self,size):
        super().__init__(size,overhead=8,minblock=16);self.links={};self.head=None;self.tags={};self.reindex()
    def reindex(self):
        free=[b['start'] for b in self.blocks if b['id'] is None];self.head=free[0] if free else None
        self.links={x:[free[i-1] if i else None,free[i+1] if i+1<len(free) else None] for i,x in enumerate(free)}
        self.refresh_tags()
    def refresh_tags(self):
        self.tags={}
        for b in self.blocks:
            tag=(b['size'],b['id'] is not None)
            self.tags[b['start']]=tag;self.tags[b['start']+b['size']-4]=tag
    def alloc(self,name,payload,policy='first',maxint=2**31-1):
        ok=super().alloc(name,payload,policy,maxint)
        if ok:self.reindex()
        return ok
    def unlink(self,address):
        prev,nxt=self.links.pop(address)
        if prev is None:self.head=nxt
        else:self.links[prev][1]=nxt
        if nxt is not None:self.links[nxt][0]=prev
    def free(self,name):
        b=next(b for b in self.blocks if b['id']==name);start,size=b['start'],b['size'];remove={start}
        # Guard bounds first; neighboring allocation status and size come from tags.
        if start>0:
            left_size,left_live=self.tags[start-4]
            if not left_live:
                left=start-left_size;self.unlink(left);remove.add(left);start=left;size+=left_size
        right=b['start']+b['size']
        if right<self.size:
            right_size,right_live=self.tags[right]
            if not right_live:self.unlink(right);remove.add(right);size+=right_size
        self.blocks=[x for x in self.blocks if x['start'] not in remove]+[dict(start=start,size=size,id=None,payload=0)]
        self.blocks.sort(key=lambda b:b['start'])
        if self.head is not None:self.links[self.head][0]=start
        self.links[start]=[None,self.head];self.head=start;self.refresh_tags();self.validate()
        assert set(self.links)=={b['start'] for b in self.blocks if b['id'] is None}
        for x,(prev,nxt) in self.links.items():
            if prev is not None:assert self.links[prev][1]==x
            if nxt is not None:assert self.links[nxt][0]==x

class Buddy:
    def __init__(self,size):
        assert size>0 and size&(size-1)==0
        self.size=size;self.free={(0,size)};self.live={}
    def alloc(self,name,request):
        if request<=0:return False
        size=1<<(request-1).bit_length();c=sorted((s,x) for x,s in self.free if s>=size)
        if not c:return False
        s,x=c[0];self.free.remove((x,s))
        while s>size:s//=2;self.free.add((x+s,s))
        self.live[name]=(x,s,request);self.validate();return True
    def release(self,name):
        x,s,_=self.live.pop(name)
        while (x^s,s) in self.free:
            self.free.remove((x^s,s));x=min(x,x^s);s*=2
        self.free.add((x,s));self.validate()
    def validate(self):
        blocks=list(self.free)+[(x,s) for x,s,_ in self.live.values()];cells=[]
        for x,s in blocks:assert x%s==0 and s&(s-1)==0;cells.extend(range(x,x+s))
        assert sorted(cells)==list(range(self.size))
    def snapshot(self):return sorted([dict(start=x,size=s,id=None,payload=0) for x,s in self.free]+[dict(start=x,size=s,id=k,payload=p) for k,(x,s,p) in self.live.items()],key=lambda b:b['start'])

def resolve(records,query):
    ans=[]
    for key,r in records.items():
        if r['name']!=query[0]:continue
        parent=r['parent'];qi=1
        while parent is not None and qi<len(query):
            if records[parent]['name']==query[qi]:qi+=1
            parent=records[parent]['parent']
        if qi==len(query):ans.append(key)
    return ans

def fullpath(records,k):
    return (() if records[k]['parent'] is None else fullpath(records,records[k]['parent']))+(records[k]['name'],)
def build_table(items):
    records={};stack=[(0,None)];heads={};trace=[]
    for key,level,name in items:
        if level<=0:raise ValueError('Level numbers must be positive')
        if level<=stack[-1][0]:
            while stack[-1][0]>level:stack.pop()
            if stack[-1][0]!=level:raise ValueError('Mixed sibling levels')
            previous=stack.pop()[1];records[previous]['sibling']=key
        parent=stack[-1][1]
        records[key]=dict(name=name,parent=parent,child=None,sibling=None,previousSame=heads.get(name))
        heads[name]=key
        if parent is not None and records[parent]['child'] is None:records[parent]['child']=key
        stack.append((level,key));trace.append(copy.deepcopy(records))
    return records,trace

def records_model():
    return build_table([('h',1,'HARBOR'),('a',3,'ARRIVAL'),('d',5,'DATE'),('x',7,'DAY'),('b',3,'DEPARTURE'),('e',5,'DATE'),('y',7,'DAY')])[0]

def corresponding(left,right,path=()):
    # Dictionaries encode named child groups; empty dictionary is elementary.
    if not left or not right:return [path]
    pairs=[]
    for name,children in left.items():
        if name in right:pairs.extend(corresponding(children,right[name],path+(name,)))
    return pairs

def tree_positions(g,root=None):
    root=root if root is not None else next(iter(g));levels={root:0};queue=[root]
    for x in queue:
        for y in g[x]:
            if y not in levels:levels[y]=levels[x]+1;queue.append(y)
    pos={}
    for depth in range(max(levels.values())+1):
        ids=[x for x in queue if levels[x]==depth]
        for j,x in enumerate(ids):pos[x]=(60+600*(j+1)/(len(ids)+1),65+min(85,300/max(1,max(levels.values())))*depth)
    return pos

def node(id,type,**kw):return dict(id=str(id),type=type,**kw)
def txt(id,x,y,text,role='input',size=17):return node(id,'text',x=x,y=y,text=str(text),fontSize=size,anchor='middle',role=role)
def line(id,x,y,x2,y2,role='muted'):return node(id,'line',x=x,y=y,x2=x2,y2=y2,role=role)
def diagram(title,description,nodes,invariant=''):return dict(title=title,description=description,viewBox=[0,0,720,440],nodes=nodes,invariant=invariant)
def state(id,caption,formula,diag):return dict(id=str(id),caption=caption,formula=formula,diagram=diag)
def graph_scene(g,title,marked=(),active=None,roots=(),labels=None,positions=None,footer='',deleted=()):
    ids=list(g);pos=positions or {x:(90+(i%4)*175,115+(i//4)*140) for i,x in enumerate(ids)};nodes=[]
    for x in g:
        for j,y in enumerate(g[x]):
            if y is not None and y in pos:
                a,b=pos[x],pos[y]
                if x==y:nodes.append(node(f'e{x}-{j}','path',d=f'M {a[0]+26} {a[1]-8} C {a[0]+80} {a[1]-70}, {a[0]+80} {a[1]+65}, {a[0]+26} {a[1]+8}',role='active',arrow=True))
                else:
                    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);ux,uy=dx/length,dy/length
                    blocked=any(z not in (x,y) and 0<((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length**2<1 and abs((p[0]-a[0])*dy-(p[1]-a[1])*dx)/length<32 for z,p in pos.items())
                    if blocked:
                        # Lift over intervening circles rather than cutting through their labels.
                        cx,cy=(a[0]+b[0])/2,min(a[1],b[1])-100
                        la=math.hypot(cx-a[0],cy-a[1]);lb=math.hypot(cx-b[0],cy-b[1])
                        ax,ay=a[0]+29*(cx-a[0])/la,a[1]+29*(cy-a[1])/la
                        bx,by=b[0]+29*(cx-b[0])/lb,b[1]+29*(cy-b[1])/lb
                        edge=node(f'e{x}-{j}','path',d=f'M {ax} {ay} Q {cx} {cy} {bx} {by}',role='active' if x==active else 'muted',fill='none')
                    else:edge=line(f'e{x}-{j}',a[0]+29*ux,a[1]+29*uy,b[0]-29*ux,b[1]-29*uy,'active' if x==active else 'muted')
                    edge['arrow']=not isinstance(g[x],set);nodes.append(edge)
    retired_edges={f'e{x}-{j}' for x in g for j,y in enumerate(g[x]) if x in deleted or y in deleted}
    for link in nodes:
        if link['id'] in retired_edges:link['opacity']=0
    for x in ids:
        px,py=pos[x];role='error' if x in deleted else 'active' if x==active else 'result' if x in marked else 'input'
        nodes.extend([node('v'+str(x),'circle',x=px,y=py,r=27,role=role),txt('t'+str(x),px,py+6,(labels or {}).get(x,x),role)])
        if x in roots:nodes.extend([txt('root'+str(x),px,py-52,'root',size=14),line('rootline'+str(x),px,py-40,px,py-28,'active')])
    if footer:nodes.append(txt('footer',360,405,footer,size=16))
    return diagram(title,'Objects are vertices; visible links are stored relationships. Red retained positions identify reclaimed objects; their old links are hidden.' if deleted else 'Objects are vertices; each drawn link is a stored relationship.',nodes,'Identity belongs to an object, not its screen coordinates.')

def tree_scene(t,title,external=False):
    ns=[]
    def visit(t,x,y,span,key,depth):
        if t is None:
            if external:ns.extend([node(key,'rect',x=x-13,y=y-13,width=26,height=26,role='result'),txt(key+'t',x,y+5,depth,size=14)])
            return
        ns.extend([node(key,'circle',x=x,y=y,r=18,role='input'),txt(key+'t',x,y+5,depth,size=14)])
        for j,child in enumerate(t):
            nx=x+(-span if j==0 else span)
            if child is not None or external:ns.append(line(key+f'e{j}',x,y+18,nx,y+57))
            visit(child,nx,y+72,span/2,key+str(j),depth+1)
    visit(t,360,65,155,'r',0)
    i,e,n,s=paths(t);ns.append(txt('sum',360,414,f'n={n}    I={i}    E={e}    external={s}',size=16))
    return diagram(title,'Depth is distance downward from the root; squares are null subtrees.',ns,'Every internal vertex owns two child positions.')

def heap_scene(blocks,title,capacity,tagged=False,footer=''):
    ns=[];scale=640/capacity
    for b in blocks:
        x=40+b['start']*scale;w=b['size']*scale;key='block'+str(b['start']);role='input' if b['id'] else 'result'
        ns.append(node(key,'rect',x=x,y=135,width=w-2,height=110,role=role))
        ns.append(txt(key+'label',x+w/2,175,b['id'] or 'free',role,size=14))
        ns.append(txt(key+'size',x+w/2,210,b['size'],role,size=14))
        ns.append(txt(key+'addr',x,280,b['start'],size=14))
        if tagged:
            ns.extend([node(key+'head','rect',x=x+2,y=137,width=4*scale-3,height=105,role='active'),node(key+'foot','rect',x=x+w-4*scale,y=137,width=4*scale-3,height=105,role='active')])
    ns.append(txt('end',680,280,capacity,size=14));ns.append(txt('axis',360,320,'byte address →',size=16))
    free=sum(b['size'] for b in blocks if not b['id']);payload=sum(b['payload'] for b in blocks)
    ns.append(txt('account',360,370,f'capacity {capacity} = reserved {capacity-free} + free {free}',size=16))
    if footer:ns.append(txt('footer',360,411,footer,size=15))
    return diagram(title,'Block width is proportional to its actual byte count; gaps never disappear silently.',ns,'Live and free intervals partition the entire arena; endpoints are half-open.')

def check(prompt,choices,index,explanation):return dict(prompt=prompt,choices=choices,correctIndex=index,explanation=explanation)
def demo(kind,states,small,assessment,smallcheck,model=None,intro='',connection=''):
    return dict(id=kind,title=next(s for s in states if '-derive-' not in s['id'])['diagram']['title'],model=dict(kind=kind,**(model or {})),states=states,transitions=[dict(from_=a['id'],to=b['id'],action=b['caption'],explanation=b['caption']) for a,b in zip(states,states[1:])],check=assessment,simplerHelp=dict(intro=intro,model=dict(kind=kind+'-smaller'),states=small,steps=[dict(action=s['diagram']['title'],text=s.get('teachingExplanation',s['caption'])) for s in small],connection=connection,check=smallcheck))

def fix_transitions(d):
    for t in d['transitions']:t['from']=t.pop('from_')
    return d

def infinity_frames(depth):
    out=[]
    for d in range(1,depth+1):
        g={};pos={}
        for k in range(d):
            g[f'p{k}']=[f'p{k+1}',f'f{k}'];pos[f'p{k}']=(220+k*65,65+k*65);g[f'f{k}']=[];pos[f'f{k}']=(95+k*65,120+k*65)
        g[f'p{d}']=[];pos[f'p{d}']=(220+d*65,65+d*65)
        out.append(state(d,f'Expose {d} levels of this explicitly defined infinite spine. The drawing is a prefix, not a proof.',r'\forall j\ge0:\ p_j\to p_{j+1}',graph_scene(g,'An infinite definition, a finite window',marked=[f'p{k}' for k in range(d+1)],positions=pos,footer='p continues by definition; f is a terminal side branch')))
    return out

def catalan_frames(n):
    out=[];total=0
    for k in range(n):
        product=catalan(k)*catalan(n-1-k);total+=product;ns=[]
        ns.extend([node('root','circle',x=360,y=65,r=21,role='active'),line('left',350,85,200,135),line('right',370,85,520,135),txt('leftlabel',195,160,f'left: {k} nodes'),txt('rightlabel',525,160,f'right: {n-1-k} nodes')])
        # A genuine Cartesian-product grid, with one cell per pair of subtrees.
        a,b=catalan(k),catalan(n-1-k)
        for i in range(a):
            for j in range(b):ns.append(node(f'pair{i}-{j}','rect',x=210+j*42,y=205+i*32,width=32,height=24,role='result'))
        ns.extend([txt('product',360,360,f'{a} left shapes × {b} right shapes = {product} pairs'),txt('total',360,405,f'accumulated disjoint cases: {total}')])
        out.append(state(k,f'The split with {k} nodes left contributes {product} distinct pairs.',rf'C_{n}=\sum_{{i=0}}^{{{n-1}}}C_iC_{{{n-1}-i}}',diagram('Choose a root split, then pair shapes','Each cell is one ordered pair; different left sizes cannot overlap.',ns)))
        catalog=[]
        catalog.extend([txt('catalog-rule',360,30,f'Root uses 1 node: {n} − 1 = {k} left + {n-1-k} right',size=18),txt('catalog-left',180,78,f'Left: C{k} = {a} concrete '+('shape' if a==1 else 'shapes'),size=16),txt('catalog-right',530,78,f'Right: C{n-1-k} = {b} concrete '+('shape' if b==1 else 'shapes'),size=16)])
        def miniature(t,x,y,span,key):
            if t is None:
                catalog.append(node(key,'rect',x=x-3,y=y-3,width=6,height=6,role='muted'));return
            catalog.append(node(key,'circle',x=x,y=y,r=5,role='input'))
            for side,child in enumerate(t):
                nx=x+(-span if side==0 else span);catalog.append(line(key+'edge'+str(side),x,y+5,nx,y+26,'muted'));miniature(child,nx,y+30,span/2,key+str(side))
        for side,size in enumerate((k,n-1-k)):
            shapes=binary(size);step=320/len(shapes)
            for index,t in enumerate(shapes):
                x=25+side*355+(index+.5)*step
                miniature(t,x,125,min(16,step/4),f'catalog-{side}-{index}')
                catalog.append(txt(f'catalog-number-{side}-{index}',x,265,'empty' if t is None else str(index+1),size=13))
        catalog.extend([txt('catalog-meaning',360,310,'Circle = one internal node; tiny square = empty child.',size=15),txt('catalog-count',360,353,f'Count these alternatives: C{k}={a}, C{n-1-k}={b}.',size=17),txt('catalog-next',360,398,'Each left choice pairs with every right choice.',size=17)])
        proof=state('catalog',f'Enumerate the ordered subtree shapes before multiplying their counts. The root is excluded from the remaining {n-1} nodes.',rf'{k}+{n-1-k}={n}-1',diagram('Retrieve counts from actual shape alternatives','These are distinct ordered binary trees, generated independently from the Catalan formula.',catalog))
        proof['computed']={'leftSize':k,'rightSize':n-1-k,'leftCount':a,'rightCount':b,'leftShapes':binary(k),'rightShapes':binary(n-1-k)}
        out[-1]['_bridges']=[proof]
    return out

def canonical_frames(n):
    graphs={}
    for code in itertools.product(range(1,n+1),repeat=n-2):
        g=adjacency(prufer_decode(code));graphs.setdefault(free_code(g),g)
    out=[]
    for i,g in enumerate(graphs.values()):
        codes={root_code(g,v) for v in g};weights={v:max([len_component(g,u,v) for u in g[v]] or [0]) for v in g};centers=[v for v,w in weights.items() if w==min(weights.values())]
        out.append(state(i,f'This free shape gives {len(codes)} distinct rooted shapes, not {n}: symmetric root positions coincide.',r'F(z)=A(z)-\tfrac12A(z)^2+\tfrac12A(z^2)',graph_scene(g,'Root positions form symmetry classes',marked=centers,positions=tree_positions(g,centers[0]),labels={v:f'{v}' for v in g},footer=f'{len(codes)} rooted classes; centroid(s): '+', '.join(map(str,centers)))))
    return out

def len_component(g,u,parent):return 1+sum(len_component(g,v,u) for v in g[u] if v!=parent)
def prufer_frames(code):
    edges=prufer_decode(code);g=adjacency(edges);original=copy.deepcopy(g);positions=tree_positions(g);out=[];seq=[]
    out.append(state(0,'Start with the actual tree decoded from the selected word.',f'n={len(code)+2}',graph_scene(g,'Encode by removing the smallest leaf',positions=positions,footer='output: empty')))
    while len(g)>2:
        leaf=min(v for v in g if len(g[v])==1);v=next(iter(g[leaf]));seq.append(v);g[v].remove(leaf);del g[leaf]
        display={x:list(g.get(x,[])) for x in original}
        out.append(state(len(out),f'Remove leaf {leaf}; append its neighbor {v}.',r'\deg(v)=1+\#\{i:c_i=v\}',graph_scene(display,'One deleted leaf, one emitted label',positions=positions,active=v,deleted=set(original)-set(g),footer='output: '+', '.join(map(str,seq)))))
    return out

def path_frames(small=False):
    trees=[None,(None,None),((None,None),None)] if small else [(None,None),((None,None),None),((None,None),(None,(None,None)))]
    out=[]
    for i,t in enumerate(trees):
        after=state(i,f'This tree has {paths(t)[2]} internal vertices, I={paths(t)[0]} and E={paths(t)[1]}.',r'E=I+2n',tree_scene(t,'Count every null child as an external vertex',True))
        if t is not None:
            leaves=[]
            def find(v,path=()):
                if v is None:return
                if v==(None,None):leaves.append(path)
                for side,child in enumerate(v):find(child,path+(side,))
            find(t);path=max(leaves,key=len);depth=len(path)
            def remove(v,p):
                if not p:return None
                xs=list(v);xs[p[0]]=remove(xs[p[0]],p[1:]);return tuple(xs)
            previous=remove(t,path);I,E,n,_=paths(previous);newI,newE,newn,_=paths(t)
            assert (newI-I,newE-E,newn-n)==(depth,depth+2,1)
            d=tree_scene(previous,'Select one null position before expanding it',True);key='r'+''.join(map(str,path))
            for obj in d['nodes']:
                if obj['id'] in (key,key+'t'):obj['role']='active'
            d['nodes'] += [txt('depth-contribution',360,350,f'Selected square: depth {depth}; current contribution to E is {depth}.',size=16),txt('role-key',360,379,'Circles contribute to I; squares contribute to E.',size=16)]
            proof=state('null-before',f'Select the external position at depth {depth}; it is still a null square, not an internal vertex.',r'E=I+2n',d)
            proof['computed']={'depth':depth,'before':[I,E,n],'after':[newI,newE,newn]}
            after['_bridges']=[proof]
            after['diagram']['nodes'] += [txt('internal-increment',360,345,f'I: {I} + {depth} = {newI}; internal count: {n} + 1 = {newn}',size=16),txt('external-increment',360,375,f'E: {E} − {depth} + 2×({depth}+1) = {newE}; ΔE = {depth+2}',size=16)]
            after['diagram']['nodes'][-2]['result']=True;after['diagram']['nodes'][-1]['result']=True
        out.append(after)
    return out
def complete(n):return None if n==0 else complete_at(1,n)
def complete_at(k,n):return None if k>n else (complete_at(2*k,n),complete_at(2*k+1,n))
def chain(n):return None if n==0 else (chain(n-1),None)
def balance_frames(n):
    return [state(i,f'With the same {n} internal vertices, the depth sum is {paths(t)[0]}.',r'\sum_{k=1}^{n}\lfloor\log_2 k\rfloor\le I\le\frac{n(n-1)}2',tree_scene(t,title)) for i,(t,title) in enumerate([(chain(n),'A chain spends depth on every next node'),(complete(n),'Fill shallow levels before deeper ones')])]
def huffman_frames(weights):
    _,steps=huffman(weights);out=[]
    for i,s in enumerate(steps):
        ns=[]
        # Each surviving heap entry is a subtree. Its weight is spatially nested below its new root.
        forest=s['forest'];w=640/len(forest)
        def draw(t,x,y,span,key,depth=0):
            if isinstance(t,str):ns.extend([node(key,'rect',x=x-18,y=y-14,width=36,height=28,role='input'),txt(key+'t',x,y+5,weights[int(t)],size=14),txt(key+'depth',x,y+31,'d='+str(depth),size=12)]);return
            ns.append(node(key,'circle',x=x,y=y,r=13,role='active'))
            for j,c in enumerate(t):
                nx=x+(-span if j==0 else span);dx=nx-x;length=math.hypot(dx,55);ux,uy=dx/length,55/length
                end=min(18/abs(ux) if ux else float('inf'),14/uy) if isinstance(c,str) else 13
                ns.append(line(key+'e'+str(j),x+13*ux,y+13*uy,nx-end*ux,y+55-end*uy));draw(c,nx,y+55,span/2,key+str(j),depth+1)
        for j,(weight,serial,t) in enumerate(forest):
            x=40+w*(j+.5);draw(t,x,85,min(w/4,85),'tree'+str(serial));ns.append(txt('weight'+str(serial),x,340,weight,size=16))
        ns.append(txt('cost',360,405,f'merge {s["pair"][0]} + {s["pair"][1]}; total cost {s["cost"]}',size=17))
        out.append(state(i,f'Merge the two globally smallest available weights; the new subtree weighs {s["sum"]}.',r'W(T)=W(T\!\downarrow)+a+b',diagram('A merge adds one level to its leaves','The forest contains whole subtrees, not merely a sorted list of numbers.',ns)))
        merged=next(t for _,serial,t in forest if serial==len(weights)+i)
        def leafdepths(t,depth=0):
            if isinstance(t,str):return [(int(t),depth)]
            return leafdepths(t[0],depth+1)+leafdepths(t[1],depth+1)
        leaves=leafdepths(merged);increment=sum(weights[j] for j,d in leaves);prior=s['cost']-increment
        assert increment==s['sum'] and all(d>=1 for j,d in leaves)
        terms=' + '.join(str(weights[j]) for j,d in leaves)
        out[-1]['diagram']['nodes'] += [txt('depth-cost-rule',360,25,f'Every merged leaf gains one level: ΔW = {terms} = {increment}',size=16),txt('depth-cost-total',360,49,f'Previous cost {prior} + added weighted depth {increment} = {s["cost"]}',size=16)]
        out[-1]['diagram']['nodes'][-1]['result']=True
        proofnodes=[txt('merge-input-title',360,35,'Two selected subtrees before adding a shared parent',size=18)]
        for j,(leaf,newdepth) in enumerate(leaves):
            x=70+j*150;olddepth=newdepth-1;weight=weights[leaf]
            proofnodes.extend([node('weighted-leaf-'+str(leaf),'rect',x=x,y=120,width=130,height=110,role='input'),txt('weight-before-'+str(leaf),x+65,152,'weight '+str(weight),size=16),txt('depth-before-'+str(leaf),x+65,184,'depth '+str(olddepth),size=16),txt('cost-before-'+str(leaf),x+65,215,f'{weight}×{olddepth}={weight*olddepth}',size=15)])
        proofnodes.extend([txt('selected-weights',360,285,f'Selected subtree weights: {s["pair"][0]} and {s["pair"][1]}',size=17),txt('depth-step-rule',360,335,'One new parent adds exactly one edge to each selected leaf.',size=16),txt('old-forest-cost',360,390,f'Current total weighted depth before this merge: {prior}',size=17)])
        proof=state('leaf-depths',f'Inspect the actual leaf depths before the merge. Each leaf contributes weight times its depth; the current forest cost is {prior}.',r'W=\sum_\ell w_\ell d_\ell',diagram('Cost counts weighted leaf depth','Each card identifies one leaf in the two selected subtrees before adding a parent.',proofnodes))
        proof['computed']={'leaves':[{'leaf':j,'weight':weights[j],'oldDepth':d-1,'newDepth':d} for j,d in leaves],'priorCost':prior,'increment':increment,'afterCost':s['cost']}
        out[-1]['_bridges']=[proof]
        component=next(j for j,(_,serial,t) in enumerate(forest) if serial==len(weights)+i)
        positions={}
        def locate(t,x,y,span):
            if isinstance(t,str):positions[int(t)]=(x,y);return
            locate(t[0],x-span,y+55,span/2);locate(t[1],x+span,y+55,span/2)
        locate(merged,40+w*(component+.5),85,min(w/4,85))
        for leaf,newdepth in leaves:
            x,y=positions[leaf]
            out[-1]['diagram']['nodes'].append(node('weighted-leaf-'+str(leaf),'rect',x=x-21,y=y-17,width=42,height=34,role='active',phase='transform'))

    return out

GC={'A':['B','C'],'B':['D'],'C':['D'],'D':[],'X':['Y'],'Y':['X']}
def ref_frames(small=False):
    g={'A':['B'],'B':[]} if small else GC;rootsets=[['A'],[]];out=[]
    for i,roots in enumerate(rootsets):
        counts={x:roots.count(x)+sum(v==x for ys in g.values() for v in ys) for x in g};live=reachable(g,roots)
        # Exact recursive zero-count deletion, retaining unreachable cycles.
        left=copy.deepcopy(g);c=counts.copy();q=[x for x in g if c[x]==0]
        while q:
            x=q.pop()
            if x not in left:continue
            for y in left[x]:
                c[y]-=1
                if c[y]==0:q.append(y)
            del left[x]
        out.append(state(i,f'{len(live)} objects are root-reachable; zero-count reclamation leaves {len(left)} objects.',r'rc(v)=\#\text{root slots pointing to }v+\#\text{heap links to }v',graph_scene(g,'Count arrows, then compare with reachability',roots=roots,marked=live,deleted=set(g)-set(left),labels={x:f'{x}:{c[x]}' for x in g},footer='red: reclaimed; unmarked surviving cycles remain garbage')))
    return out

def work_marker(d,current,previous=None,rescanned=False):
    # This cursor identifies the operation already completed, never a future visit.
    vertices={n['id'][1:]:(n['x'],n['y']) for n in d['nodes'] if n['type']=='circle' and n['id'].startswith('v')}
    x,y=vertices[current] if current is not None else (45,340)
    px,py=vertices[previous] if previous is not None else (45,340)
    d['nodes'].extend([
        node('work-cursor','circle',x=x+38,y=y,r=8,role='active',phase='transform'),
        node('work-travel','line',x=px+38,y=py+42,x2=x+38,y2=y+42,arrow=True,opacity=1 if previous is not None else 0,role='active',phase='transform'),
        node('rescan-cursor','rect',x=35 if not rescanned else x+30,y=340 if not rescanned else y+18,width=16,height=12,role='active',opacity=1 if rescanned else 0,phase='transform'),
    ])
    label=txt('work-status',360,375,'processed '+str(current)+(' (recovered by rescan)' if rescanned else '') if current is not None else 'root is marked; its outgoing links are pending',size=15)
    label.update(result=True,phase='result');d['nodes'].append(label)

def mark_frames(small=False,bounded=False):
    g={'A':['B'],'B':[],'X':['X']} if small else GC;out=[]
    if bounded:
        _,trace=bounded_mark(g,['A'],1)
        previous=None;previous_done=set();previous_scans=0
        for i,(seen,stack,done,scans) in enumerate(trace):
            d=graph_scene(g,'A bounded frontier needs a recovery rule',marked=seen,roots=['A'],footer=f'frontier: {stack or "empty"}; processed {len(done)}; rescans {scans}')
            current=next(iter(done-previous_done));work_marker(d,current,previous,scans>previous_scans)
            out.append(state(i,f'Process one marked object. Work not retained in the one-slot frontier is recovered by scanning marked but unprocessed objects.',r'\text{processed}\subseteq\text{marked}\subseteq R',d))
            previous=current;previous_done=done;previous_scans=scans
    else:
        seen,trace=mark_stack(g,['A'])
        for i,(marked,stack,x) in enumerate(trace):out.append(state(i,f'Marked objects: {", ".join(sorted(marked))}. The frontier is {stack or "empty"}.',r'R=\operatorname{Reach}(\text{roots})',graph_scene(g,'Mark before scheduling an object',marked=marked,active=x,roots=['A'],footer='frontier: '+str(stack))))
        out.append(state('sweep','Only after the frontier is empty may every unmarked allocated object be reclaimed.',r'\text{garbage}=V\setminus R',graph_scene(g,'Sweep the unmarked allocated objects',marked=seen,roots=['A'],deleted=set(g)-seen,footer='A cycle is live only if a root reaches it')))
    return out

def reverse_frames(small=False):
    graph={'A':dict(a='B',b=None,atom=0),'B':dict(a=None,b=None,atom=1)} if small else {'A':dict(a='B',b='C',atom=0),'B':dict(a=None,b=None,atom=1),'C':dict(a='B',b='A',atom=0),'X':dict(a='X',b=None,atom=0)}
    _,trace=reverse_mark(graph,'A');out=[]
    for i,s in enumerate(trace):
        g={x:[] if r['atom'] and x not in s['marked'] else [r['a'],r['b']] for x,r in s['graph'].items()}
        d=graph_scene(g,'Borrow a link, then repay it',marked=s['marked'],active=s['p'],roots=['A'],footer=f'P={s["p"]}; return-stack T={s["t"] or "null"}')
        for x,r in s['graph'].items():
            idx=list(g).index(x);d['nodes'].append(txt('fields'+x,90+(idx%4)*175,165+(idx//4)*140,f'A:{r["a"] or "–"} B:{r["b"] or "–"} t:{r["atom"]}',size=14))
        out.append(state(i,s['action']+'. These are the current stored fields, including temporary links.',r'\text{final links}=\text{initial links}',d))
    return out

def qualifier_markers(d,records,query,positions,inspect=False):
    # One stable cursor per candidate follows the actual outward ancestor search.
    for serial,(candidate,record) in enumerate((k,r) for k,r in records.items() if r['name']==query[0]):
        current=candidate;matched=1
        if not inspect:
            for qualifier in query[1:]:
                parent=records[current]['parent'];found=False
                while parent is not None:
                    current=parent
                    if records[current]['name']==qualifier:found=True;matched+=1;break
                    parent=records[current]['parent']
                if not found:break
        x,y=positions[current];cx,cy=positions[candidate];offset=40+serial*18
        d['nodes'].extend([
            node('qualifier-cursor-'+candidate,'circle',x=x+offset,y=y,r=7,role='active',phase='transform'),
            # A local pointer follows the cursor; a straight leaf-to-ancestor
            # chord would cut through intermediate record circles and labels.
            node('qualifier-route-'+candidate,'line',x=x+offset,y=y+12,x2=x+29,y2=y+12,arrow=True,role='active',phase='transform'),
        ])
        result=txt('qualifier-status-'+candidate,270+serial*180,365,candidate+': '+('inspect' if inspect else 'matched' if matched==len(query) else 'exhausted'),size=14)
        result.update(result=True,phase='result');d['nodes'].append(result)

def record_frames(mode,small=False):
    records=records_model()
    if small:records={k:v for k,v in records.items() if k in ['h','a','d','x']}
    g={k:[c for c,r in records.items() if r['parent']==k] for k in records};pos={'h':(360,55),'a':(175,135),'d':(175,230),'x':(175,325),'b':(535,135),'e':(535,230),'y':(535,325)};labels={k:r['name'] for k,r in records.items()};out=[]
    if mode==134:
        for i,partial in enumerate(build_table([('h',1,'HARBOR'),('a',3,'ARRIVAL'),('d',5,'DATE'),('x',7,'DAY')]+([] if small else [('b',3,'DEPARTURE'),('e',5,'DATE'),('y',7,'DAY')]))[1]):
            pg={k:[c for c,r in partial.items() if r['parent']==k] for k in partial};d=graph_scene(pg,'Build links from level-number declarations',positions=pos,active=list(partial)[-1],footer='nonconsecutive levels are valid; siblings share one level')
            for k,r in partial.items():d['nodes'].append(txt('name'+k,(80 if pos[k][0]<360 else 620 if pos[k][0]>360 else 480),pos[k][1]+5,r['name'],size=14))
            out.append(state('build'+str(i),'Add one declaration, linking its parent and previous same-name entry while retaining its unique identity.',r'\mathrm{parent}(c)=p\text{ for each linked child }c',d))
        for i,active in enumerate(['x','d']):
            d=graph_scene(g,'One identity, several link fields',active=active,labels=None,positions=pos,footer='parent ↑     first-child ↓     same-name ⇢')
            for k,r in records.items():d['nodes'].append(txt('name'+k,(80 if pos[k][0]<360 else 620 if pos[k][0]>360 else 480),pos[k][1]+5,r['name'],size=14))
            if 'y' in records:d['nodes'].append(line('same-name',200,325,510,325,'active' if active=='x' else 'muted'))
            out.append(state(i,'The same DAY object participates in containment and the same-name index. These are different relations, not duplicate payload records.',r'\operatorname{id}(x)\ne\operatorname{name}(x)',d))
    elif mode==135:
        queries=[['DAY'],['DAY','ARRIVAL'],['DAY','HARBOR']] if not small else [['DAY'],['DAY','DEPARTURE']]
        for i,q in enumerate(queries):
            matches=resolve(records,q);d=graph_scene(g,'Filter candidates by ancestor order',marked=matches,positions=pos,footer=f'{" OF ".join(q)} → {len(matches)} matches')
            for k,r in records.items():d['nodes'].append(txt('name'+k,(80 if pos[k][0]<360 else 620 if pos[k][0]>360 else 480),pos[k][1]+5,r['name'],size=14))
            qualifier_markers(d,records,q,pos)
            out.append(state(i,f'Qualifiers may skip intervening groups. This query is {"absent" if not matches else "unique" if len(matches)==1 else "ambiguous"}.',r'|\operatorname{matches}(q)|\in\{0,1,>1\}',d))
    else:
        left=[('DATE','DAY'),('DATE','MONTH'),('CARGO','MASS')];right=[('CARGO','MASS'),('DATE','DAY'),('DATE','YEAR')];assert corresponding({'DATE':{'DAY':{},'MONTH':{}},'CARGO':{'MASS':{}}},{'CARGO':{'MASS':{}},'DATE':{'DAY':{},'YEAR':{}}})==[('DATE','DAY'),('CARGO','MASS')]
        if small:left=[('DATE','DAY'),('DATE','MONTH')];right=[('DATE','DAY')]
        for i,path in enumerate(left):
            ns=[]
            for side,items in enumerate([left,right]):
                for j,p in enumerate(items):
                    x=190+side*350;y=100+j*90;role='result' if p==path and p in right else 'input'
                    ns.extend([node(f'{side}-{j}','rect',x=x-130,y=y-25,width=260,height=50,role=role),txt(f't{side}-{j}',x,y+5,' / '.join(p),role,size=16)])
            if path in right:ns.append(line('match',320,100+i*90,410,100+right.index(path)*90,'active'))
            ns.append(txt('result',360,405,'match by qualified path, not by physical order',size=16))
            out.append(state(i,f'{" / ".join(path)} '+('matches the corresponding elementary item.' if path in right else 'has no corresponding elementary item.'),r'\operatorname{key}(v)=\text{relative ancestor-name path of }v',diagram('Match qualified leaves across records','Each lane is a different record. Crossing links preserve semantic correspondence.',ns)))
    return out

def collision_frames(small=False):
    items=[('r',1,'ROOT'),('a',2,'ITEM'),('b',2,'ITEM')] if small else [('r',1,'ROOT'),('a',2,'GROUP'),('c',3,'ITEM'),('b',2,'GROUP'),('d',3,'ITEM')]
    records,_=build_table(items);query=['ITEM','ROOT'] if small else ['ITEM','GROUP','ROOT'];matches=resolve(records,query)
    assert len(matches)==2 and fullpath(records,matches[0])==fullpath(records,matches[1])
    g={k:[c for c,r in records.items() if r['parent']==k] for k in records}
    pos={'r':(360,65),'a':(180,160),'b':(540,160),'c':(180,255),'d':(540,255)};out=[]
    for phase in range(2):
        d=graph_scene(g,'Distinct declarations with the same complete name path',marked=matches if phase else (),positions=pos,footer=' OF '.join(query)+' : '+('2 matches, still ambiguous' if phase else 'inspect both candidates'))
        for k,r in records.items():d['nodes'].append(txt('name'+k,(80 if pos[k][0]<360 else 620 if pos[k][0]>360 else 480),pos[k][1]+5,r['name'],size=15))
        qualifier_markers(d,records,query,pos,inspect=phase==0)
        out.append(state(phase,'The two ITEM identities have identical complete ancestor-name paths. Full qualification still matches both; address order cannot disambiguate them.',r'x\ne y,\quad\operatorname{fullPath}(x)=\operatorname{fullPath}(y)',d))
    return out

def correspondence_stop_frames(small=False):
    left={} if small else {'DATE':{'DAY':{}}}
    right={'VALUE':{}} if small else {'DATE':{'DAY':{'NUMBER':{}}}}
    expected=corresponding(left,right);assert expected==[() if small else ('DATE','DAY')]
    steps=[()] if small else [(),('DATE',),('DATE','DAY')];out=[]
    def elementary(tree,path):
        for name in path:tree=tree[name]
        return not tree
    for i,path in enumerate(steps):
        ns=[]
        for side,tree in enumerate([left,right]):
            x=180+side*360
            def draw(t,p=()):
                y=65+len(p)*82;active=p==path;label=('ROOT' if not p else p[-1])+(' : item' if not t else ' : group')
                ns.extend([node(str(side)+'-'+str(p),'rect',x=x-110,y=y-22,width=220,height=44,role='active' if active else 'input'),txt(str(side)+'-label-'+str(p),x,y+5,label,size=15)])
                for name,ch in t.items():
                    ns.append(line(str(side)+'-edge-'+str(p),x,y+22,x,y+60));draw(ch,p+(name,))
            draw(tree)
        stop=elementary(left,path) or elementary(right,path)
        ns.append(line('paired-path',290,65+len(path)*82,430,65+len(path)*82,'active'))
        ns.append(txt('decision',360,365,'OUTPUT this pair; do not descend' if stop else 'Both groups: descend to equal-name children','result' if stop else 'active',17))
        ns.append(txt('relative-path',360,405,'relative path: '+('/'.join(path) or '(empty at the record roots)'),size=15))
        caption=('Either-side-elementary test succeeds; output the matched pair even though the right item is a group. Its children are not visited.' if stop else 'Both current items are groups. Equal relative paths alone are not output; descend into matching child names.')
        out.append(state(i,caption,r'\operatorname{emit}(u,v)\iff\operatorname{elem}(u)\lor\operatorname{elem}(v)',diagram('Match groups, then stop at either elementary side',caption,ns,'Output requires matching relative paths and at least one elementary item.')))
    if len(out)==1:
        before=copy.deepcopy(out[0]);before['id']='inspect';before['caption']='Inspect the smaller root pair: left is elementary, right is a group. The relative paths are both empty.'
        before['diagram']['nodes']=[n for n in before['diagram']['nodes'] if n['id']!='decision'];out.insert(0,before)
    return out

def allocation_frames(mode,small=False):
    capacity=(48 if small else 64) if mode==139 else (32 if small else 64);h=TaggedHeap(capacity) if mode==139 else Heap(capacity);out=[]
    def add(caption,tagged=False):out.append(state(len(out),caption,r'\text{capacity}=\sum\text{live block sizes}+\sum\text{free block sizes}',tagged_scene(h,'A byte-accurate arena') if tagged else heap_scene(h.snapshot(),'A byte-accurate arena',capacity,tagged)))
    if mode==137:
        add('Initially the entire arena is available. Sizes include alignment padding; this first model has zero header overhead.')
        for name,size in ([('A',5),('B',9)] if small else [('A',9),('B',13),('C',5)]):h.alloc(name,size);add(f'Request {size} payload bytes for {name}; round upward to a multiple of four, then split.')
        h.free('A');add('Free A. A later request must fit one contiguous block, not the total free count.')
        h.alloc('D',7);add('A seven-byte request fits the first adequate free interval after alignment.')
    elif mode in (138,139):
        for name,size in [('A',8),('B',8),('C',8)]:h.alloc(name,size)
        add('Three live objects separate free intervals.',mode==139)
        for name in ['A','C','B']:
            h.free(name);add(f'Return {name}; merge only touching free intervals. Live bytes never move.',mode==139)
    elif mode==143:
        for name in ['A','B','C','D']:h.alloc(name,capacity//4)
        h.free('A');h.free('C');add('The two holes total half the arena, but neither hole spans half.')
        before=h.snapshot();ok=h.alloc('E',capacity//2);assert not ok and before==h.snapshot();add('The large request fails atomically: every block and every live payload stays unchanged.')
        h.free('B');add('Freeing B joins the two holes; this authorized release changes what can fit.')
        assert h.alloc('E',capacity//2);add('Retry succeeds after enough consecutive bytes become available.')
    return out

def tagged_scene(h,title):
    d=heap_scene(h.snapshot(),title,h.size,True)
    # A separate lane exposes actual reciprocal list fields, not implied arrows.
    free=sorted(h.links);positions={x:100+i*210 for i,x in enumerate(free)}
    d['nodes'].append(txt('free-head',360,24,'free-list head: '+str(h.head),size=15))
    for x in free:
        px=positions[x];prev,nxt=h.links[x]
        d['nodes'].extend([node('free-link-'+str(x),'rect',x=px-65,y=40,width=160,height=46,role='active'),txt('free-address-'+str(x),px+15,57,'free @'+str(x),size=14),txt('free-fields-'+str(x),px+15,77,'prev='+str(prev)+' next='+str(nxt),size=14)])
    for b in h.blocks:
        x=40+(b['start']+b['size']/2)*640/h.size
        d['nodes'].append(txt('tag-value-'+str(b['start']),x,119,str(b['size'])+(' live' if b['id'] else ' free')+' at both ends',size=14))
    return d

def tag_unlink_frames(small=False):
    h=TaggedHeap(48 if small else 64)
    for name in ('A','B','C'):assert h.alloc(name,8)
    h.free('A');h.free('C');out=[]
    def add(caption):
        diag=tagged_scene(h,'Release B between two tagged free neighbors')
        diag['invariant']='Within the atomic release, removed free-list entries await the merged replacement; live B remains intact until commit.'
        out.append(state(len(out),caption,r'\operatorname{next}(p)=q\iff\operatorname{prev}(q)=p\quad(p,q\ne\mathrm{null})',diag))
    add('Before release: B is live between free blocks at offsets 0 and 32. Read the neighboring tags before touching their free-list links.')
    original=h.unlink
    def recorded(address):
        original(address)
        add('Unlink free neighbor at '+str(address)+'. Update both adjacent list fields, or the list head at an endpoint. Boundary metadata is not committed yet.')
    h.unlink=recorded
    h.free('B')
    add('Commit the merged interval: one free block at zero spans the arena, its endpoint tags agree, and its prev/next links are null.')
    out[-1]['diagram']['invariant']='One free-list entry represents the merged block; endpoint tags agree and every arena byte is conserved.'
    return out

def buddy_frames(small=False):
    cap=16 if small else 64;b=Buddy(cap);out=[]
    def add(msg):out.append(state(len(out),msg,r'\operatorname{buddy}(x,2^k)=x\mathbin{\mathrm{xor}}2^k',heap_scene(b.snapshot(),'Only sibling intervals recombine',cap,footer='Offsets are relative to a power-of-two aligned arena')))
    add('Begin with one power-of-two arena.')
    for name,request in [('A',3 if small else 9),('B',3 if small else 9)]:
        target=1<<(request-1).bit_length();proofs=[];working=copy.deepcopy(b);size,x=min((s,x) for x,s in working.free if s>=target)
        def proof(msg,stage):
            d=heap_scene(working.snapshot(),'Round, split, then reserve',cap,footer='No new live allocation is committed during these split steps')
            d['nodes'] += [txt('round-request',360,50,f'Request {request}: {target//2} < {request} ≤ {target}, so reserve {target} bytes.',size=17),txt('split-status',360,88,msg,size=16)]
            st=state('split-'+stage,msg,r'r\le 2^k,\quad 2^{k-1}<r',d);st['computed']={'request':request,'rounded':target,'stage':stage,'blocks':working.snapshot(),'selectedStart':x,'selectedSize':size,'capacity':cap};proofs.append(st)
        proof(f'Selected free block: offset {x}, size {size}.','round')
        while size>target:
            parent=size;working.free.remove((x,size));size//=2;working.free.add((x,size));working.free.add((x+size,size));working.validate()
            proof(f'Split {parent} into {size}+{size}; continue with left child at {x}.',str(size))
        b.alloc(name,request);add(f'Reserve {name}: round {request} to a power of two and split larger blocks.')
        out[-1]['_bridges']=proofs
        buddy=x^target;width=cap.bit_length()
        out[-1]['diagram']['nodes'] += [txt('xor-bits',360,55,f'{x:0{width}b} XOR {target:0{width}b} = {buddy:0{width}b}  (buddy offset {buddy})',size=16),txt('xor-condition',360,89,f'Size {target}; offsets {x} and {buddy} are aligned multiples of {target}.',size=16)]
    b.release('A');add('A is free, but its buddy remains live: merging is forbidden.')
    b.release('B');add('Both siblings are free at the same order; merge recursively toward the arena root.')
    return out

def comparison_frames(small=False):
    size=48 if small else 96;heaps={p:Heap(size) for p in ['first','best']};ops=[('a','A',20),('a','B',8),('a','C',12),('a','D',8),('f','A',0),('f','C',0),('a','E',10),('a','F',18)]
    if small:ops=[('a','A',12),('a','B',8),('f','A',0),('a','C',9)]
    out=[]
    for i,(op,name,n) in enumerate(ops):
        ns=[];summ=[]
        for row,(policy,h) in enumerate(heaps.items()):
            ok=h.alloc(name,n,policy) if op=='a' else h.free(name)
            y=90+row*160;ns.append(txt('policy'+policy,360,y-25,f'{policy} fit: {h.probes} free-list probes',size=17))
            for b in h.blocks:
                x=40+b['start']*640/size;w=b['size']*640/size;role='input' if b['id'] else 'result'
                ns.extend([node(f'{policy}{b["start"]}','rect',x=x,y=y,width=w-2,height=65,role=role),txt(f'label{policy}{b["start"]}',x+w/2,y+38,b['id'] or 'free',size=14)])
            summ.append((policy,sum(b['payload'] for b in h.blocks),sum(b['size'] for b in h.blocks if b['id'])))
        ns.append(txt('event',360,405,f'{"allocate" if op=="a" else "free"} {name}'+(f' ({n} bytes)' if op=='a' else ''),size=17))
        out.append(state(i,'Both policies receive the same event, in the same order. Probe count and resulting holes are measured separately.',r'U=\frac{\text{live payload bytes}}{\text{arena bytes}}',diagram('Hold the workload fixed; change one policy','The two lanes have the same address scale and initial capacity.',ns)))
    return out

def slots_frames(small=False):
    sizes=[4,4,8] if small else [4,4,4,8,8,8];requests=[4,8,8] if small else [8,8,8,8];used={};out=[]
    for i,r in enumerate(requests):
        k=next((k for k,s in enumerate(sizes) if s>=r and k not in used),None)
        if k is not None:used[k]=r
        ns=[]
        for j,s in enumerate(sizes):
            x=65+j*105;role='result' if j in used else 'input';ns.extend([node('slot'+str(j),'rect',x=x,y=300-s*18,width=80,height=s*18,role=role),txt('size'+str(j),x+40,330,f'{s} bytes',size=14),txt('used'+str(j),x+40,280,str(used.get(j,'–')),size=16)])
        # Tokens represent membership in availability pools; physical columns stay fixed.
        ns.extend([txt('available-pool',160,352,'free-slot IDs',size=14),txt('assigned-pool',515,352,'assigned-slot IDs',size=14)])
        for j in range(len(sizes)):
            x=(430 if j in used else 65)+j*28
            ns.extend([node('inventory-token-'+str(j),'rect',x=x,y=362,width=22,height=22,role='active',phase='transform'),txt('inventory-token-label-'+str(j),x+11,378,j+1,size=14)])
            ns[-1]['phase']='transform'
        ns.append(node('slot-search-cursor','line',x=40 if k is None else 105+k*105,y=97,x2=40 if k is None else 105+k*105,y2=140,arrow=True,role='active',phase='transform'))
        ns.append(txt('request',360,70,f'request {r}: '+(f'slot {k+1}' if k is not None else 'FAIL despite empty smaller slots'),size=17));ns.append(txt('inventory',360,395,f'payload {sum(used.values())}; reserved inventory {sum(sizes)} bytes',size=16))
        out.append(state(i,'Fixed slot boundaries do not move. A request may use only an empty slot of sufficient capacity.',r'\text{waste}=\sum\text{slot capacities}-\sum\text{live payloads}',diagram('A predicted size mix creates a fixed inventory','Column heights encode capacity; unused small slots cannot combine into a large slot.',ns)))
    return out

def machine_frames(small=False):
    g={};regs={'P':None,'Q':None};values={};out=[];ops=[('new','P',7),('copy','Q','P'),('new','P',7),('link','P','Q'),('follow','P',None)]
    if small:ops=ops[:3]
    for i,(op,a,b) in enumerate(ops):
        if op=='new':key=chr(65+len(g));g[key]=[];values[key]=b;regs[a]=key
        elif op=='copy':regs[a]=regs[b]
        elif op=='link':g[regs[a]]=[regs[b]]
        elif op=='follow':regs[a]=g[regs[a]][0]
        d=graph_scene(g,'Access an object through a held pointer',roots=list(set(v for v in regs.values() if v)),labels={x:f'{x}:7' for x in g},footer=f'P={regs["P"] or "null"}; Q={regs["Q"] or "null"}; identity equal? {regs["P"]==regs["Q"]}')
        out.append(state(i,f'Execute {op}. Equal payload 7 does not imply that two registers hold the same object.',r'\operatorname{value}(P)=\operatorname{value}(Q)\not\Rightarrow P=Q',d))
    return out
# Each paragraph is authored for this concept; scenes are computed above, never inferred from prose.
TEXT={
123:[
('The hypothesis is local finiteness','A rooted tree is connected and has a unique finite route from every vertex to its root. Here each vertex has finitely many children, but there need not be one common bound on their number. The theorem says: if this tree has infinitely many vertices, it contains a sequence v₀,v₁,… beginning at the root, with vⱼ₊₁ a child of vⱼ for every nonnegative integer j. Our downward arrows follow children; the source’s oriented-tree arrows point toward the parent. The existence claim is the same.',r'\forall v:\ |\operatorname{children}(v)|<\infty'),
('Choose a subtree that cannot run out','The root has infinitely many descendants. If every one of its finitely many child subtrees were finite, their finite union together with the root would be finite, a contradiction. At least one child therefore has infinitely many descendants. Repeat this argument at the selected child. Induction supplies a next vertex at every finite stage, and the nested choices form the infinite path. This argument, rather than a large animation, proves the theorem.',r'\text{finite union of finite sets is finite}'),
('Watch a defined infinite spine','The model defines pⱼ to have children pⱼ₊₁ and fⱼ, with fⱼ terminal, for every j≥0. Only a finite window is displayed. The rule defining the family establishes continuation beyond the window; merely drawing a long chain would not. To recognize a child with infinitely many descendants can require information unavailable to an algorithm, so the existence proof is not a general effective path-finding procedure.',r'p_j\to p_{j+1},\quad p_j\to f_j'),
('Why infinitely many children changes everything','Let one root have a separate finite chain of length m for every positive integer m. This tree has arbitrarily large finite depth and infinitely many vertices, but every root-starting path chooses one chain and then ends. Its root has infinitely many children, violating the hypothesis. With finite branching, each finite level is finite; consequently an infinite tree must have unbounded depth. Without finite branching that reasoning and the theorem both fail.',r'\forall m\ \exists\text{ a path of length }m\ \not\Rightarrow\ \exists\text{ infinite path}')],
124:[
('State exactly what a shape remembers','A binary shape is empty or is a root with two distinguished child positions, left and right. Vertices carry no labels, but swapping unequal children changes the shape. Let Cₙ count shapes with n internal vertices, including the empty shape C₀=1. An ordered general tree instead has a finite ordered list of children. These families have related counts, not identical size parameters.',r'C_0=1'),
('Split the size at the root','For n≥1, the left child has some i vertices with 0≤i<n; the right has n−1−i. Choosing one shape on each side gives CᵢCₙ₋₁₋ᵢ possibilities. Different splits cannot coincide because the left size is recoverable, and different pairs cannot coincide because both child shapes are recoverable. This disjoint decomposition proves the recurrence, including the empty-child cases.',r'C_n=\sum_{i=0}^{n-1}C_iC_{n-1-i}'),
('Turn pair construction into a series','Write C(z)=Σₙ≥₀Cₙzⁿ as a formal power series. Multiplication records all ordered pairs, and the extra root contributes z, giving C=1+zC². The solution with constant coefficient 1 is (1−√(1−4z))/(2z), interpreted by its removable formal constant term. Coefficient extraction gives Cₙ=(2n choose n)/(n+1). Our grid enumerates all root splits for n=4 and sums 5+2+2+5=14.',r'C(z)=1+zC(z)^2,\qquad C_n=\frac1{n+1}\binom{2n}{n}'),
('The one-vertex size shift matters','Removing the root of an ordered tree leaves an ordered forest. The first-child/next-sibling encoding maps that forest bijectively to a binary tree on the same remaining vertices. Thus ordered general trees on m≥1 vertices are counted by Cₘ₋₁. Forgetting child order is not this bijection: it identifies shapes under symmetry and leads to different counts. A lone ordered root corresponds to the empty binary shape, not the one-node binary shape.',r'\#\text{ordered trees on }m\text{ vertices}=C_{m-1}')],
125:[
('Unordered children form a multiset','Let aₙ count rooted unlabeled trees with n≥1 vertices, where children have no left-to-right order, and put a₀=0. The children are a multiset of rooted shapes. Each particular k-vertex shape may occur zero, one, two, or more times, contributing 1/(1−zᵏ). Since there are aₖ such shapes, multiply these factors and then attach one root. The identity is formal: any fixed coefficient depends on only finitely many factors.',r'A(z)=z\prod_{k\ge1}(1-z^k)^{-a_k}'),
('Compute coefficients without guessing symmetry factors','Taking the formal logarithmic derivative of A(z)/z gives zA′/A−1=Σₖ≥₁bₖzᵏ, where bₖ=Σd|k d a_d. Matching coefficients yields (n−1)aₙ=Σₖ₌₁ⁿ⁻¹ bₖaₙ₋ₖ. This recurrence produces 1,1,2,4,9,20 for sizes one through six. Independently, the model decodes all small labeled trees, erases labels via sorted parenthesis codes, and checks the resulting distinct rooted isomorphism classes.',r'(n-1)a_n=\sum_{k=1}^{n-1}\left(\sum_{d\mid k}d a_d\right)a_{n-k}'),
('Remove the root using centroids, not division','For a vertex v of an n-vertex free tree, remove v and take the largest component size as its weight. A centroid minimizes this weight. There is one centroid, or two adjacent centroids whose connecting edge divides the tree into equal halves. Use this invariant central element: the unique centroid vertex, or the edge joining the two centroids. A tree marked at its central element represents one free shape. Every other vertex-marked tree corresponds to an edge directed toward that center, by taking the first edge from its marked vertex. Every noncentral edge-marked tree corresponds to that edge directed away from the center. These assignments are reversible; when the center is an edge, its two orientations arise from marking its two endpoint vertices. Hence vertex-marked trees plus undirected-edge-marked trees equal free trees plus directed-edge-marked trees. Cutting a directed marked edge gives an ordered pair of rooted trees, counted by A². Cutting an undirected marked edge gives an unordered pair, counted by (A²+A(z²))/2: distinct pairs occur twice in A², while equal pairs need the diagonal correction. Solving A+(A²+A(z²))/2=F+A² yields F=A−A²/2+A(z²)/2. This is a bijective counting argument, not division by the number of possible root positions.',r'F(z)=A(z)-\frac12 A(z)^2+\frac12 A(z^2)'),
('Check a symmetry counterexample','A four-vertex path gives only two rooted shapes: root at an endpoint or at an interior vertex. A four-vertex star also gives two: root at the center or at a leaf. Together these are the four rooted shapes but only two free shapes. Dividing four by four would give one, which is wrong. Canonicalization uses structure alone; vertex names, drawing positions, and edge orientations introduced only for display must not alter the class.',r'f_n=a_n-\frac12\sum_{i=1}^{n-1}a_i a_{n-i}+\frac12[2\mid n]a_{n/2}')],
126:[
('Two related codes have different lengths','For a labeled undirected tree on {1,…,n}, n≥2, the standard Prüfer word has length n−2. Repeatedly remove the smallest labeled leaf and output its sole neighbor, stopping with two vertices. The source also gives a rooted canonical code: retain the designated root, remove the smallest other leaf, and continue until only that root remains, producing n−1 symbols. We implement both and distinguish their domains.',r'\text{Prüfer length}=n-2;\quad\text{rooted code length}=n-1'),
('Recover the next leaf from the remaining word','In a Prüfer word, the current degree of a remaining vertex equals one plus its occurrences in the remaining suffix. Hence the smallest vertex absent from that suffix is the next leaf. Join it to the first symbol, delete it from availability, and remove that symbol. At the end join the last two vertices. Each added edge removes a leaf from consideration, so decoding cannot create a cycle and yields a connected tree.',r'\deg(v)=1+\operatorname{occurrences}(v)'),
('Invert the actual tree transformations','The example starts with the tree decoded from the word (4,4,2). Its five vertices and four edges are real model data; the animation removes leaves and records the emitted labels. The degree invariant makes each encoding choice equal to the corresponding decoding choice, proving the two maps inverse by induction. For the rooted variant, decode n−1 symbols by the same smallest-absent rule, leaving one vertex as the root.',r'\operatorname{encode}(\operatorname{decode}(c))=c'),
('Count words only after proving bijection','There are n choices in each of n−2 Prüfer positions, so nⁿ⁻² labeled free trees for n≥2. Designating an arbitrary root multiplies by n; fixing one root does not. The rooted n−1 code correspondingly has nⁿ⁻¹ possibilities. For n=2 the Prüfer word is empty and describes the one edge. For n=1 the single-vertex tree is handled separately; a negative word length is not meaningful.',r'\#\text{labeled free trees}=n^{n-2}\quad(n\ge2)')],
127:[
('A null child is a measurable position','Extend a binary tree by placing an external square at every empty child position. Original vertices are internal circles. Every internal vertex has exactly two children in the extended tree; every external vertex has none. If there are n internal and s external vertices, edge counting gives 2n=n+s−1, hence s=n+1. This includes the empty original tree: one external root at depth zero.',r's=n+1'),
('Separate the two sums','Depth counts edges from the root, so the root has depth zero. Internal path length I is the sum of depths over circles; external path length E is the corresponding sum over squares. Neither is height, which is a maximum rather than a sum. Null positions matter because an unsuccessful descent can reach them even though they are not stored data records.',r'I=\sum_{v\text{ internal}}d(v),\qquad E=\sum_{v\text{ external}}d(v)'),
('One expansion proves the identity','Replace an external vertex at depth d by an internal vertex with two external children. Internal path length rises by d. External path length replaces d by 2(d+1), rising by d+2. Therefore E−I rises by exactly 2 while n rises by 1. Starting with n=I=E=0 proves E=I+2n for every finite binary tree. The computed sequence confirms concrete cases but does not replace this induction.',r'\Delta I=d,\quad\Delta E=d+2,\quad E=I+2n'),
('Do not apply the binary constant everywhere','For a full extended t-ary tree with t≥2 child positions per internal node, the same expansion gives ΔE=(t−1)d+t, so E=(t−1)I+tn and the number of external vertices is (t−1)n+1. A partially drawn tree that omits some null positions will not obey the displayed binary identity. Definitions decide which objects must be counted.',r'E=(t-1)I+tn')],
128:[
('A depth budget has limited shallow slots','In a binary tree at most 2ᵈ vertices can occupy depth d. To minimize a sum of n depths, fill the smallest available depths first. A complete tree realizes that capacity pattern, so the lower bound is attainable. Number its internal vertices in breadth-first order from 1 to n; vertex k has depth floor(log₂k). Completeness is sufficient, but when the last level is partial the minimizing shape need not be unique.',r'I_{\min}(n)=\sum_{k=1}^n\lfloor\log_2 k\rfloor'),
('Move depth without changing the count','The scene contrasts a five-vertex chain with a five-vertex complete tree. Both contain five data vertices, yet their depth sums are 10 and 6. A chain maximizes the sum: depth of the jth vertex in any ancestor-first listing is at most j−1, so I≤0+1+⋯+(n−1). Equality is achieved when all vertices lie on one path. External path extrema follow immediately from E=I+2n.',r'I_{\max}(n)=\frac{n(n-1)}2'),
('Evaluate the minimum exactly','For n≥0 let q=floor(log₂(n+1)); then summing the complete levels yields Imin=(n+1)q−2^(q+1)+2. Our implementation uses integer bit lengths, avoiding floating-point errors at powers of two. The empty case n=0 gives zero. This result minimizes an unweighted depth sum; it is not the answer when some leaves are much more likely or costly than others.',r'I_{\min}=(n+1)q-2^{q+1}+2,\quad q=\lfloor\log_2(n+1)\rfloor'),
('Generalize the capacity argument','For t≥2, depth d holds at most tᵈ internal vertices. Fill levels until n places are occupied; the remaining vertices occupy the next depth. With q=floor(log_t((t−1)n+1)), the exact minimum is (n+1/(t−1))q−(t^(q+1)−t)/(t−1)². In one-based breadth-first numbering, parent(k)=floor((k+t−2)/t) for k≥2. The model verifies the formula with exact rational arithmetic against explicit parent chains.',r'I_{\min,t}=\left(n+\frac1{t-1}\right)q-\frac{t^{q+1}-t}{(t-1)^2}')],
129:[
('Weights change what balance should mean','Given m positive leaf weights wᵢ, minimize W=Σwᵢℓᵢ over full binary trees whose leaves carry those weights, with ℓᵢ their depths. Leaf order is unrestricted. Larger weights should tend to be shallower, so minimizing height or making every depth similar is not necessarily optimal. If an application requires alphabetic leaf order, this unrestricted Huffman problem is a different optimization problem.',r'W(T)=\sum_{i=1}^m w_i\ell_i'),
('Why the two smallest can be siblings','Take an optimal tree and a deepest sibling pair of leaves. If a smaller weight occupies a shallower position than a larger weight, exchanging them changes cost by (small−large)(deep−shallow)≤0. Repeated exchanges place the two smallest weights at that deepest pair without increasing the optimum. This exchange argument establishes the greedy choice; sorting once and pairing adjacent original weights would not establish it.',r'(a-b)(d_{\rm deep}-d_{\rm shallow})\le0\quad(a\le b)'),
('Contract the chosen pair','If sibling leaves have weights a,b, replace their parent subtree by a leaf of weight a+b. Expanding it later adds one depth to exactly those weights, adding cost a+b. An optimal solution containing that pair must contract to an optimal smaller solution, or substitution would improve it. Induction therefore justifies repeatedly merging the two currently smallest available weights, including previously merged subtrees. The example uses weights 3,4,8,10.',r'W(T)=W(T_{\rm contracted})+a+b'),
('Verify cost and handle ties honestly','The sum of all merge weights equals weighted path length because every merge counts once for each leaf below it. Our independent oracle explores every possible merge pair at every stage for small positive inputs and compares the minimum with the greedy result. Ties can produce distinct optimal trees; deterministic tie-breaking makes the display reproducible, not uniquely optimal. For one leaf the cost is zero under the empty-code convention.',r'W=\sum_{\text{merges }u}\operatorname{weight}(u)')],
130:[
('Ownership is not the same as one incoming edge','Shared structures allow several root variables or heap fields to refer to the same object. Deleting a single reference does not authorize deleting that object while another live reference remains. A reference count must include every counted root slot and heap link, and every update must adjust counts consistently. Object identity is independent of the value stored inside it.',r'rc(v)=\#\text{root references}+\#\text{heap references}'),
('A zero count permits cascading reclamation','When a count becomes zero, reclaim that object and decrement the counts of its outgoing targets. Those targets may then become zero, forming a cascade. The model recomputes counts and performs this exact cascade. The root A reaches a diamond-shaped shared object D; D is not freed merely because one branch stops referring to it. This argument assumes the count is exact and there are no hidden uncounted references.',r'rc(v)=0\Rightarrow v\text{ has no counted incoming reference}'),
('A positive count does not prove liveness','The disconnected pair X→Y→X has positive counts even with no root path to either object. After removing the last root of the ordinary component, reference counting can reclaim that component but leaves the cyclic garbage. In the scene red objects are actually reclaimed; surviving unmarked cyclic objects are still allocated, despite being unreachable. A one-object self-loop is already a counterexample.',r'rc(v)>0\not\Rightarrow v\in\operatorname{Reach}(\text{roots})'),
('Choose the semantic contract before the collector','Reachability-based liveness is the existence of a path from a complete set of roots through recognized pointer fields. Counts approximate that property operationally but do not characterize it in cyclic graphs. Conversely, omitting an actual root can make any collector unsafe. Counter overflow, weak references, concurrent updates, and finalizers require additional rules beyond this stop-the-world finite-graph model.',r'R=\{v:\exists r\in\text{roots},\ r\leadsto v\}')],
131:[
('Find liveness before changing allocation','Take a finite allocated-object set V, a complete root set, and a pointer graph whose edges target allocated objects or null. Pause mutation during this teaching collector. Start with all mark bits clear. Marking answers which objects are reachable; sweeping answers which allocated objects may become free. Mixing these phases prematurely risks reclaiming a reachable object whose path has not yet been explored.',r'G=V\setminus R'),
('Mark before putting work on the frontier','Mark each root and put newly marked objects on a work stack. Pop an object, inspect each of its pointer fields, and mark and schedule each previously unmarked target. Marking before scheduling prevents duplicate work on shared targets and prevents an infinite loop on cycles. Every discovered object is reachable, since it is a root or follows a pointer from another reachable object.',r'\text{marked}\subseteq R'),
('An empty frontier establishes closure','When the stack becomes empty, every marked object has had its outgoing fields inspected. Thus the marked set contains the roots and is closed under graph edges. Every finite root path stays in this closed set, so R is contained in marked. Combined with the other inclusion, marked=R. Only then does a sweep through V reclaim unmarked objects. The disconnected X,Y cycle is reclaimed; a rooted cycle would be retained.',r'\text{frontier}=\varnothing\Rightarrow\text{marked}=R'),
('Count cost and acknowledge roots','With adjacency lists, stack marking uses O(|R|+|E_R|) work, and sweeping all allocated slots costs O(|V|). Mark storage costs one bit per object plus a possibly large frontier. An atom has no pointer fields to traverse, even if its payload resembles an address. Real implementations must describe root registers, stacks, globals and valid object layouts accurately; our diagram cannot discover references omitted from its input.',r'T=O(|V|+|E_R|)')],
132:[
('The collector also needs memory','An ordinary DFS or marking worklist may need many pending pointers precisely when free storage is exhausted. The frontier must come from a reserved budget, a safe reusable field, or a strategy that repeats work. Simply dropping entries from a full stack is incorrect: some marked objects would never have their outgoing edges examined.',r'|\text{frontier}|\le H'),
('A bounded frontier requires remembered obligations','Our explicit teaching variant uses capacity H≥1, a mark bit, and a separate processed bit per object. Newly discovered objects are marked even if the frontier is full. When the frontier empties, scan for marked-but-unprocessed objects and refill it. Every reachable object is eventually processed because processing grows monotonically and scans recover every unsatisfied obligation. This variant is not a literal implementation of the source’s Algorithm C and openly pays for an extra bit.',r'\text{processed}\subseteq\text{marked}\subseteq R'),
('Watch one frontier slot recover lost scheduling work','With H=1, marking A discovers B and C, but both cannot remain in the frontier. The omitted object keeps its mark and unprocessed status. A later scan finds it and follows its outgoing links. The same graph reaches exactly the same final live set as the unbounded stack model. The independent test compares the results for every two-field graph on three vertices, including sharing, cycles and null fields.',r'\text{pending obligation}=\text{marked}\setminus\text{processed}'),
('Alternative representations make different promises','The source’s bounded-stack rescanning scheme tracks a safe restart position rather than our full processed-bit set. Header-field stacks can avoid a separate pointer array, but only if those fields are genuinely available and the list structure is well formed at every collection point. Interior roots and temporary malformed lists can violate that assumption. Lower auxiliary space may trade for rescanning time; no universal optimal H follows from this small demonstration.',r'\text{space saved}\ne\text{work eliminated}')],
133:[
('A return path can live in borrowed fields','This is the source’s two-link pointer-reversal marking algorithm, expressed with fields A, B, MARK and ATOM. ATOM=1 identifies a payload leaf whose links are ignored. The graph may contain cycles and sharing. Collection is stop-the-world: other code must not read the temporarily altered representation. A few pointer registers P,Q,T replace an external traversal stack; per-node control and mark bits still exist.',r'P=\text{current},\quad T=\text{return-stack top}'),
('Reverse one edge while retaining its missing target','Before descending an unmarked A child, save the child in Q, replace A(P) by T, set the temporary ATOM bit, and move T to P and P to Q. The child that used to occupy the changed field remains recoverable from the current traversal. For a B descent the B field holds the return link and the temporary control bit distinguishes that case. Mark tests prevent following a cycle indefinitely.',r'\text{saved return link}+\text{current child}+\text{phase}\Rightarrow\text{restorable edge}'),
('Restoration is part of correctness','On return, T locates the suspended parent. Its control bit tells whether A or B is borrowed. Save the older T from that field before replacing the field with P, then move P back to the parent and restore the bit. An A return proceeds to inspect B; a B return continues upward. The computed trace displays actual temporary field values, not the original graph behind a decorative cursor.',r'\text{final }(A,B,ATOM)=\text{initial }(A,B,ATOM)'),
('Prove preservation, then check every small graph','The invariant is that suspended ancestors form a return chain in the borrowed fields, with the missing downward edge represented by the next active object and the phase. Descending extends that encoding; returning exactly reverses the corresponding local update. Marking finishes with precisely the original root-reachable objects marked, P restored to its initial root, and every original field restored. Tests exhaust all three-vertex two-link graphs; finite testing is implementation evidence alongside this invariant, not a proof for all graph sizes.',r'\text{marked}=R\quad\land\quad\text{graph restored}')],
134:[
('Choose fields from the operations','A record can belong simultaneously to a containment tree, a sibling list, and an index of equal names. Store separate fields such as parent, firstChild, nextSibling and nextSameName when the intended operations need them. These links describe different relations among the same object identities. Creating a second copy of the payload for each relation would introduce a synchronization problem that multiple linkage avoids.',r'v=(\text{payload},\text{parent},\text{child},\text{sibling},\text{sameName})'),
('One update may have several local obligations','Moving a field to another group changes its containment parent and sibling neighborhood; renaming it changes its name-index membership. Neither action automatically implies the other. A representation invariant should state for each relation which heads own a chain and which reciprocal facts must agree. For example, each child listed under a group must name that group as parent, while every node on a same-name chain must carry that indexed name. The builder reads positive level numbers: an increase opens a child group, an equal level adds a sibling, and a decrease pops to a matching prior level. Nonconsecutive levels are allowed, but a decrease landing between existing levels is rejected as mixed sibling levels.',r'c\in\operatorname{children}(p)\Rightarrow\operatorname{parent}(c)=p'),
('Inspect a hierarchical table with repeated names','The HARBOR record contains ARRIVAL and DEPARTURE groups, each with DATE and DAY entries. The two DAY nodes are distinct even though their strings are equal. A same-name link can connect them for candidate search, while parent links distinguish their containing groups. The scene shows object IDs inside nodes and names below: following the name index must never overwrite the containment links.',r'\operatorname{name}(x)=\operatorname{name}(y)\not\Rightarrow x=y'),
('More links are an explicit tradeoff','An extra parent link may replace repeated root-to-node searches with immediate access, but consumes space and adds maintenance work. An index can accelerate queries while becoming stale if updates forget it. There is no universal best record format independent of the operations and workload. Our model inspects the table and its structural invariants; it also executes a level-number table builder, but does not claim a full compiler, transactional editor, or concurrent index implementation.',r'\text{representation cost}=\text{storage}+\text{query work}+\text{update work}')],
135:[
('A short name starts a candidate set','An unqualified field name can occur in multiple groups. Search all nodes with that name, then test any supplied qualifiers. In the source’s hierarchical qualification convention, DAY OF ARRIVAL may omit the intermediate DATE group: each later name need only occur farther up the ancestor chain. The qualifiers must retain their order and must each match a distinct ancestor position.',r'A_0\ \mathrm{OF}\ A_1\ \mathrm{OF}\cdots\mathrm{OF}\ A_k'),
('Walk ancestors, not adjacent text','For each candidate named A₀, move repeatedly to its parent. Advance to the next requested qualifier only when the current ancestor’s name matches. Reaching the root before consuming all qualifiers rejects that candidate. This is a subsequence test on the ancestor-name chain, not a string substring test or an assumption that all qualifiers are immediate parents.',r'\exists\,0<d_1<\cdots<d_k:\ \operatorname{name}(\operatorname{parent}^{d_j}(v))=A_j'),
('Keep absence and ambiguity separate','DAY alone has two candidates in our HARBOR table. DAY OF ARRIVAL has one, whereas DAY OF HARBOR still has two. A search routine must return absent for zero matches, the unique object for one, and ambiguous for more than one; choosing whichever candidate was encountered first would silently change semantics when storage order changes. The model computes the candidate set before assigning the status.',r'0\to\text{absent},\quad1\to\text{unique},\quad>1\to\text{ambiguous}'),
('Qualification has limits','If two declarations have the same complete ancestor-name chain, no amount of this form of qualification distinguishes them. Such a declaration set needs rejection or an additional naming convention. This unit uses a simplified hierarchical qualification language; it does not claim complete modern COBOL name-resolution rules, lexical-scope shadowing, or overload resolution. Those are separate language contracts.',r'\operatorname{fullPath}(x)=\operatorname{fullPath}(y),\ x\ne y\Rightarrow\text{unresolvable collision}')],
136:[
('Correspondence is structural, not positional','Two records can store matching elementary fields in different orders. Pairing the first leaf with the first leaf is therefore unsafe. Define a correspondence key from an item’s name and all ancestor names relative to its record root; this applies to elementary items and groups alike. The source requires complete relative qualification at equal depth here, unlike the abbreviated qualifiers used for a single-name query. A corresponding pair is output as soon as either side is elementary; if both sides are groups, matching descends into equal-name children.',r'\operatorname{key}(v)=(\text{ancestor names},\text{item name})'),
('Traverse groups but match elementary items','Start from the two specified record roots. If either current item is elementary, output the current pair and stop that descent. Otherwise inspect children of the first group and search the second group for equal names; recursively process each match and skip unmatched subtrees. This preserves equal relative qualification at every recursive step. Our executable model uses child-name dictionaries with unique sibling names; the source implements the same correspondence rule with CHILD, SIB and PARENT links. A production representation must detect forbidden duplicate names rather than silently overwrite them.',r'M=\{(u,v):\operatorname{key}(u)=\operatorname{key}(v),\ \operatorname{elem}(u)\lor\operatorname{elem}(v)\}'),
('Watch reordered fields find one another','The left record has DATE/DAY, DATE/MONTH and CARGO/MASS; the right has CARGO/MASS, DATE/DAY and DATE/YEAR. The diagram’s crossing lines show that DAY and MASS match despite different physical positions. MONTH has no target. Equal terminal words in different groups would not match under our full-relative-path rule. The model compares exact path tuples rather than screen coordinates.',r'\text{DATE/DAY}\ne\text{CARGO/DAY}'),
('Matching does not authorize conversion','Finding a corresponding pair establishes identity of the intended semantic field, not compatible size, numeric representation or destination capacity. A copying operation would next validate types and conversion rules and specify failure behavior. Our scene deliberately stops at matching keys; no actual record bytes are transferred. This separation prevents a correct name search from being mistaken for a safe data-movement implementation.',r'\text{matched names}\not\Rightarrow\text{safe bytewise copy}')],
137:[
('Make every byte belong somewhere','Use a finite arena [0,C) partitioned into disjoint half-open blocks [start,start+size). Each block is either free or reserved for one live allocation. A request is for payload bytes, while block size also includes metadata and alignment. In our first model alignment is four bytes and metadata overhead is zero; later boundary-tag examples account for real overhead explicitly.',r'\operatorname{need}(r)=4\left\lceil\frac{r+h}{4}\right\rceil'),
('First fit and best fit answer different searches','First fit scans the address-ordered free list and stops at the first adequate interval. Best fit scans candidates and chooses the smallest adequate size, breaking ties by address. Both must test the rounded total requirement. A remainder can be split only if it is large enough to form a valid free block; otherwise reserve the entire interval and record the extra internal waste. Search effort is a separate metric from wasted bytes.',r'\text{remainder}=\text{chosen size}-\operatorname{need}(r)'),
('Split without moving live neighbors','The computed arena accepts requests of 9,13 and 5 payload bytes as blocks of 12,16 and 8 bytes. The remaining free block begins at byte 36. Freeing A creates a separate hole; a later seven-byte request rounds to eight and uses that first adequate hole. Widths correspond to actual byte counts, so reserved bytes, payload bytes and free bytes can be checked independently.',r'C=\sum\text{reserved sizes}+\sum\text{free sizes}'),
('Total free bytes do not imply a successful request','External fragmentation occurs when enough free bytes exist in total but no single free interval is large enough. Internal waste is unused space inside a reserved block, including padding under the accounting convention. Before arithmetic, reject nonpositive requests under this model’s contract and check r+h+alignment−1 for machine-integer overflow. A failed search leaves the arena unchanged.',r'\max\text{free block size}<r\le\sum\text{free sizes}')],
138:[
('Freeing is a partition update','The caller returns a currently live allocation exactly once. Returning an interior pointer, the wrong size, or an already free block violates this model’s precondition. Marking its interval free preserves all addresses and payloads of other live allocations. The free list is kept sorted by increasing start address so the possible adjacent predecessor and successor can be identified.',r'[p,p+s)\text{ is one live allocation}'),
('Adjacency is equality of endpoints','Two free intervals can coalesce only when the lower start plus its size equals the upper start. Merely being consecutive entries in the free list does not suffice: a live block may lie between them. After insertion, merge with the next interval when endpoints touch, and then with the preceding interval when endpoints touch. If both neighbors are free, all three become one interval.',r'p+s=q'),
('Return the bridge last','The scene allocates A,B,C, then returns A and C while B remains live. Returning B removes the last live bridge between the neighboring free areas, so they coalesce. The resulting free block spans the full arena. The model checks exact coverage after each operation: no gaps, overlaps, lost bytes or duplicate live IDs can be hidden by the drawing.',r'\text{size after merge}=s_{\rm left}+s_{\rm returned}+s_{\rm right}'),
('Coalescing is not compaction','Coalescing combines already adjacent free regions and never moves a live byte. Compaction relocates live blocks and requires updating every reference or using stable handles. An address-sorted free list can cost linear search time to find the insertion point; once the neighbors are known, the local merge decisions are constant-size work. A good explanation must separate those costs.',r'\text{coalescing preserves every live start address}')],
139:[
('Endpoints reveal neighboring blocks','A boundary-tag layout stores size and allocation status at block boundaries. For the explicit accounting extension here, reserve a four-byte header and a four-byte footer in every block; an eight-byte payload needs at least sixteen bytes before any extra free-list requirements. The free-list links may use free-block payload space, so the minimum free-block size must accommodate those links too.',r'\text{block bytes}=\text{header}+\text{payload}+\text{padding}+\text{footer}'),
('Read only within validated arena bounds','For a block starting at p, its predecessor footer lies immediately before p, unless p is the arena start. A valid footer supplies the predecessor size and status; the successor begins at p+size. Guard the arena ends with allocated sentinels or explicit bounds checks before reading either neighbor. A random previous word is not a valid footer merely because arithmetic produced an address.',r'\operatorname{prevStart}=p-\operatorname{prevSize}'),
('Unlink neighbors before erasing their metadata','There are four cases: neither neighbor free, left only, right only, or both. Remove each free neighbor from the doubly linked free list before combining intervals and rewriting the outside tags. The merged block must appear exactly once in that list, and its header and footer must agree. Our partition scene highlights both ends and demonstrates the two-neighbor case; the executable tests cover all four cases and tag consistency.',r'\operatorname{headerSize}(b)=\operatorname{footerSize}(b)'),
('Local discovery is not free metadata','Boundary tags avoid an address-ordered search for adjacent physical blocks, and double links permit removing known free-list entries locally. This does not make an arbitrary allocation search constant time. The main geometry shows whole block sizes; its color strips indicate where endpoint metadata belongs, not an additional uncounted area outside those blocks. The executed model discovers neighbors from guarded tags, unlinks their reciprocal free-list entries, and verifies tag consistency and minimum size. Its Python array sorting and snapshot reconstruction are visualization instrumentation; they are not claimed to be the constant-time linked implementation.',r'\text{local coalescing work}=O(1)\text{ once block metadata is valid}')],
140:[
('A binary partition constrains possible intervals','Start with an arena of 2ᵐ bytes and represent addresses as offsets from its base. Every block has size 2ᵏ and begins at an offset divisible by 2ᵏ. To satisfy a positive request, round up to a supported power of two, find a free block of at least that order, and repeatedly split it into equal halves. The unused halves go into free sets indexed by order.',r'x\equiv0\pmod{2^k}'),
('XOR identifies a sibling under these assumptions','The two children of a size-2^(k+1) interval differ in exactly bit k. Thus the buddy offset of x is x xor 2ᵏ. For a nonzero arena base B, compute B+((address−B) xor 2ᵏ), not blindly absolute-address XOR unless the alignment makes that equivalent. A buddy must be within this arena, free, and have the same current order.',r'\operatorname{buddy}_k(x)=x\mathbin{\mathrm{xor}}2^k'),
('Merge only the two halves of one parent','Two adjacent eight-byte blocks at offsets 8 and 16 are not buddies: their buddies are 0 and 24. The scene reserves two rounded sixteen-byte blocks; freeing only A cannot merge with live B. After B is freed, its exact free sibling can merge, and the resulting parent may merge again. Every stage remains a disjoint partition of the original arena.',r'\text{merge requires }y=x\mathbin{\mathrm{xor}}2^k\text{ and equal size }2^k'),
('Measure rounding waste and failure','A request just above a power of two can reserve almost twice its payload, even with no external holes. That is internal rounding waste. The implementation stores bookkeeping out of band in this abstract model; a real allocator must account for its own metadata and minimum order. An exact-power request does not round further. If no suitable block exists, report failure without modifying any free set or live allocation.',r'2^{k-1}<r\le2^k\Rightarrow\text{reserved}=2^k')],
141:[
('An experiment needs a specified workload','Compare policies on the identical ordered sequence of allocations and releases, with the same arena, alignment, overhead and tie-breaking. Our first experiment is a fully listed deterministic trace, not a sample from an unnamed random distribution. We measure success, free-list probes, payload utilization, reserved bytes and hole sizes. Different policies may start diverging after the same release because their earlier placement decisions differed.',r'U=\frac{\text{live payload bytes}}{C}'),
('Keep failure semantics identical','If a named allocation fails, a later release of that name must be handled consistently; otherwise one policy receives an invalid workload and the comparison becomes meaningless. The shown trace is chosen to make all its releases valid. First fit counts each inspected free-list entry until success; best fit counts the entire candidate scan. Both models coalesce on release and split with the same minimum remainder.',r'\text{one event stream}\longrightarrow\text{two policy states}'),
('A smaller immediate hole can hurt later','In the trace, first fit places a ten-byte request into an earlier twenty-byte hole, whereas best fit can choose a twelve-byte hole. Those locally reasonable choices leave different possibilities for the next eighteen-byte request. The scene aligns both address lanes and updates measured probe counts from the executed search. No conclusion is inferred from the names “best” and “first.”',r'\text{local remainder minimum}\not\Rightarrow\text{global workload optimum}'),
('Statistical rules require statistical hypotheses','An empirical winner on this trace is a result about this trace. Random studies must specify request-size probabilities, lifetime/departure laws, warm-up, run length and seeds. The source’s fifty-percent discussion concerns steady-state expected block counts under its assumptions, not a universal statement that half the bytes are free or wasted. Correlated lifetimes and near-stack behavior can substantially change the result.',r'\mathbb E[\text{free block count}]\ne\text{free byte fraction}')],
142:[
('A forecast can determine an inventory','Distributed fit pre-partitions storage into fixed slots of different capacities, at most one allocation per slot. Slots are sorted by size, making first adequate empty and smallest adequate empty equivalent searches under the same tie order. The source’s scheme assumes a known size distribution and that every present block is equally likely to depart next, independently of its age. These are consequential workload hypotheses, not implementation details.',r'\Pr(\text{next departure}=v\mid\text{present set})=1/N_{\rm live}'),
('Do not turn an asymptotic reserve into a guarantee','The source discusses roughly N primary slots matched to the size distribution plus √N log₂N maximum-sized overflow slots. Under its probabilistic model this yields reserve overhead of order N^(−1/2) log N relative to primary storage as N grows. A finite instance still pays actual bytes, and mismatched sizes or lifetimes void the inference. Our small deterministic inventory illustrates that risk; it is not a simulation proving the asymptotic theorem.',r'\text{relative reserve}=O(N^{-1/2}\log N)'),
('Let a changed mix exhaust large slots','Our primary inventory has three four-byte and three eight-byte slots. Four consecutive eight-byte requests fill all three large slots and then fail while twelve bytes of small slots remain empty. Since fixed boundaries do not coalesce, those three small slots cannot serve an eight-byte allocation. The smaller example has two four-byte slots and one eight-byte slot, exhibiting the same mismatch with fewer objects.',r'\text{total empty capacity}\not\Rightarrow\text{adequate empty slot}'),
('Plan for measured uncertainty','Separate payload bytes, unused occupied-slot space, empty primary capacity, and any overflow reserve. If observed sizes or lifetime correlations differ from the forecast, reassess the slot plan or use a general allocator. The exact scene has no stochastic claims and no implicit reserve. Its failure is evidence of a concrete counterexample, not a claim that distributed fit is generally ineffective.',r'C=\text{payload}+\text{occupied-slot slack}+\text{empty-slot capacity}')],
143:[
('Classify a failed request before recovering','Failure may mean aggregate exhaustion, external fragmentation, an alignment or metadata constraint, or arithmetic overflow while computing a size. The arena here has two separated holes totaling half its capacity; a half-capacity request still cannot fit. Rejecting it is correct. Failure must have an explicit result and leave the previous live allocations valid.',r'\text{failure}\Rightarrow\text{old live state preserved}'),
('Validate arithmetic before any mutation','For an unsigned w-bit size type, ensure payload plus metadata plus alignment slack does not exceed 2ʷ−1 before adding. Check every computed endpoint against arena bounds. Only after all checks and a suitable free block are found should the allocator commit list and tag changes. Python integers do not overflow; our bounded-size guard deliberately models this implementation obligation instead of relying on Python’s unlimited arithmetic.',r'r\le\mathrm{MAX}-h-(a-1)'),
('A failed search is a no-op, a later release is not','The model snapshots every block, attempts the impossible allocation, and verifies exact equality afterward. It then releases the live block between the holes, coalesces, and retries successfully. The successful retry is caused by a legitimate change in storage state, not by weakening the allocation contract. Search counters may change on failure, but allocation metadata and live payloads do not.',r'\operatorname{heapAfterFailure}=\operatorname{heapBefore}'),
('Moving objects requires moving all references','Compaction can combine nonadjacent holes only by relocating live blocks. Every root and interior pointer must then be updated, or references must use stable handles that are redirected consistently. Unknown raw pointers, pinned objects, and external references can prevent compaction. Reclaiming unreachable objects or spilling data also needs its own correctness contract. No recovery strategy creates capacity when all bytes are genuinely required.',r'\text{relocate}(v)\Rightarrow\text{repair every reference to }v')],
144:[
('Describe the abstract machine before counting steps','A pointer machine has a fixed number of pointer registers, nodes with a fixed number of link and information fields, and instructions such as create, copy a pointer, test equality, read or write a field of a held node, and follow a link. Null is a distinguished non-object value. Only objects currently held in registers are immediately accessible; the machine cannot name an arbitrary distant object by arithmetic unless the model explicitly adds that operation.',r'\text{register}\in V\cup\{\mathrm{null}\}'),
('Aliases refer to one object','Create A containing 7 and copy its pointer from P to Q; both registers now denote A. Create a fresh B also containing 7 into P; values agree but identities differ. Store Q into B’s link and follow that link from P; both registers again denote A. The scene executes these instructions and displays the actual graph and registers after each step.',r'\operatorname{payload}(A)=\operatorname{payload}(B)\quad\text{but }A\ne B'),
('Representation invariants connect the chapter','Tree parent links, same-name indexes, allocation handles and garbage-collection roots are all constrained uses of this linked-node state. A traversal proof specifies which links may be followed; a collector proof specifies which identities remain live; an allocator proof specifies where their finite bytes reside. Changing one representation requires rechecking the algorithms that depend on its invariants. This synthesis is instructional material from the end of the historical section, not an interactive bibliography.',r'\text{algorithm correctness}=\text{state invariant}+\text{valid transitions}'),
('Abstract constant time is a modeling assumption','Treating one pointer operation as unit cost ignores finite address width, cache locality, allocation failure and physical memory limits. A w-bit address field can encode only finitely many locations, so an unbounded-node abstract machine is not a literal finite implementation. Graph-local rewriting machines use a different access rule; this unit does not assert unrestricted constant-factor equivalence. Choose the model whose operations match the question being analyzed.',r'\text{unit-cost abstract step}\ne\text{uniform physical latency}')]
}

def boundary_frames(order,small=False):
    """Separate computed boundary inputs; no replay of the main example."""
    if order==123:
        out=[]
        for depth in ([1,2] if small else [2,3]):
            g={'r':[]};pos={'r':(360,55)}
            for m in range(1,depth+1):
                for j in range(m):
                    key=f'{m}-{j}';g[key]=[f'{m}-{j+1}'] if j+1<m else [];pos[key]=(100+m*140,125+j*75)
                g['r'].append(f'{m}-0')
            out.append(state(depth,'These displayed finite chains stand for one chain of each positive finite length. The root has infinitely many children in the defined family.',r'\text{unbounded finite depth, but no infinite branch}',graph_scene(g,'A family excluded by finite branching',positions=pos,footer='one finite chain for each m≥1; more chains are omitted')))
        return out
    if order==124:return catalan_frames(1 if small else 2)
    if order==125:return canonical_frames(3 if small else 4)
    if order==126:return prufer_frames([] if small else [2])
    if order==127:return [state('empty','The empty original tree has one external root, at depth zero.',r'n=I=E=0,\quad s=1',tree_scene(None,'The empty case still has an external position',True))]
    if order==128:return balance_frames(2 if small else 3)
    if order==129:return huffman_frames([2,2] if small else [1,1,1,1])
    if order==130:
        g={'X':['X']};return [state('cycle','There is no root. X has one incoming reference and is unreachable.',r'rc(X)=1,\quad R=\varnothing',graph_scene(g,'The smallest reference-count counterexample',labels={'X':'X:1'},footer='allocated cyclic garbage'))]
    if order in (131,132):
        g={'X':['X']};seen,tr=mark_stack(g,['X']);out=[]
        for i,(s,todo,x) in enumerate(tr):
            d=graph_scene(g,'A rooted cycle must survive',roots=['X'],marked=s,footer='worklist '+str(todo))
            if order==132:work_marker(d,x)
            out.append(state(i,'A root makes the self-cycle live. Mark-before-schedule makes traversal terminate.',r'R=\{X\}',d))
        return out
    if order==133:
        graph={'X':dict(a='X',b=None,atom=0)};marked,tr=reverse_mark(graph,'X');return [state(i,s['action']+'. The self-link needs no reversal because X is already marked.',r'A(X)=X\text{ before and after}',graph_scene({'X':['X']},'A cycle does not create an infinite descent',marked=s['marked'],roots=['X'])) for i,s in enumerate(tr)]
    if order==134:return record_frames(135,True)[-1:]
    if order==135:return collision_frames(small)
    if order==136:
        ns=[txt('left',180,150,'DATE / DAY'),txt('right',540,150,'CARGO / DAY'),txt('neq',360,260,'same leaf name; different path',size=17)]
        return [state('nomatch','Equal terminal names do not establish correspondence across unequal containing groups.',r'(\mathrm{DATE},\mathrm{DAY})\ne(\mathrm{CARGO},\mathrm{DAY})',diagram('A false positional or name-only match','Two elementary items have incompatible full relative paths.',ns))]
    if order in (137,138,139,143):
        h=TaggedHeap(32 if small else 64) if order==139 else Heap(16 if small else 32)
        h.alloc('A',8);before=h.snapshot();ok=h.alloc('B',h.size+1);assert not ok and h.snapshot()==before
        return [state('failure','The requested block does not fit. A failed search leaves the byte partition unchanged.',r'\text{failed reservation is atomic}',heap_scene(h.snapshot(),'A failure is not a partial allocation',h.size,order==139))]
    if order==140:
        ns=[]
        for x in [0,8,16,24]:
            ns.extend([node(str(x),'rect',x=40+x*20,y=150,width=158,height=90,role='input'),txt('t'+str(x),120+x*20,195,str(x))])
        ns.extend([line('buddy0',120,270,280,270,'result'),line('buddy16',440,270,600,270,'result'),txt('warn',360,340,'8 and 16 touch, but they are not buddies',size=16)])
        ns.extend([txt('xor-example',360,55,'01000 XOR 01000 = 00000; 10000 XOR 01000 = 11000',size=16),txt('alignment-example',360,90,'All slots: size 8; offsets divisible by 8. XOR still selects the sibling.',size=15)])
        return [state('adjacent','At size eight, 8 xor 8 = 0 and 16 xor 8 = 24. The touching middle intervals cannot merge.',r'8\mathbin{\mathrm{xor}}8=0\ne16',diagram('Adjacent is weaker than sibling','Each underlined pair shares a sixteen-byte parent.',ns))]
    if order==141:return comparison_frames(True)[-2:]
    if order==142:return slots_frames(True)
    return machine_frames(True)[-2:]

ASSESS={
123:[('Does finite branching require one common bound on all child counts?',['No; each vertex may have its own finite count.','Yes, the same bound is essential.','Only binary trees qualify.'],0,'Local finiteness is enough for the finite-union step.'),('Why must the chosen infinite-descendant vertex have an infinite-descendant child?',['The largest displayed branch proves it.','A finite union of finite child subtrees would be finite.','Every child is infinite.'],1,'Only at least one child is forced to continue.'),('A finite animation reaches depth 100. What has it proved about arbitrary trees?',['Every tree is infinite.','An infinite branch exists.','Only that this finite prefix was displayed.'],2,'The general theorem requires the argument, not the frame count.'),('One root has chains of every finite length. Which hypothesis fails?',['Unique parent','Finite branching at the root','Finite depth of each vertex'],1,'Infinitely many root children prevent the finite-union argument.')],
124:[('What does C₀ count?',['No possibilities','One empty shape','One leaf with two children'],1,'There is one empty binary shape.'),('For n=3, the split i=1 contributes how many pairs?',['1','2','4'],0,'Each side has exactly one one-node shape, so the product is 1×1=1.'),('How many ordered general trees have five vertices?',['42','5','14'],2,'Removing the ordered root leaves a four-node binary encoding, counted by C₄=14.'),('Does forgetting left and right preserve binary-shape counts?',['Yes','No, it identifies distinct ordered shapes','Only for all even sizes'],1,'The equivalence relation has changed.')],
125:[('Why a product factor (1−zᵏ)⁻¹ per rooted shape?',['The shape may occur any nonnegative number of times','Every child order is distinct','Every shape must appear once'],0,'A particular child shape may be repeated any number of times, with no ordering among those copies.'),('For n=3, what are a₃ and f₃?',['3 and 1','2 and 1','2 and 2'],1,'A path has endpoint-root and middle-root forms, but one free form.'),('For six vertices, exact counts are?',['20 rooted, 6 free','6 rooted, 20 free','20 rooted, 20/6 free'],0,'Both the product recurrence and independent isomorphism enumeration give these integers.'),('Why not divide aₙ by n?',['Some root positions are equivalent under symmetry','n can be zero only','Labels force the division'],0,'Free shapes do not all have n inequivalent rootings.')],
126:[('A standard Prüfer word for six labeled vertices has length?',['5','4','6'],1,'Stop when two vertices remain.'),('In word (3,3), which vertex is removed first?',['3','4','1'],2,'Among labels 1–4, 1 is the smallest absent from the word.'),('How many labeled free trees have five vertices?',['25','125','625'],1,'The bijection gives 5^(5−2)=125.'),('The empty Prüfer word describes which n≥2 tree?',['The single edge on two vertices','No tree','An arbitrary rooted singleton'],0,'The algorithm stops with two vertices; an empty word therefore decodes to the edge between those two labels.')],
127:[('With six internal binary vertices, how many external positions?',['6','7','12'],1,'Counting tree edges both as twice the internal count and as total vertices minus one gives s=n+1.'),('Expanding a square at depth 4 changes E by?',['4','5','6'],2,'Replace depth 4 by two depths 5: increase 6.'),('If n=6 and I=9, what is E?',['15','21','27'],1,'The complete binary extension has E=I+2n, so 9+2×6 gives 21.'),('For a ternary extension with n=2 and I=1, E is?',['5','7','8'],2,'A ternary expansion adds three external children per internal vertex, giving E=2I+3n=2+6=8.')],
128:[('How many binary vertices fit at depth 3?',['At most 6','At most 8','At most 9'],1,'Each vertex has two child positions, so level three has at most 2³=8 vertices.'),('Maximum I for six vertices?',['12','15','18'],1,'All six vertices can lie on one path, achieving the maximum depth sum 0+1+2+3+4+5=15.'),('Minimum I for six vertices?',['8','9','10'],0,'Filling the shallowest available slots gives depths 0,1,1,2,2,2, whose sum is 8.'),('Is every minimum-depth shape uniquely determined?',['Always','No, partial last levels can differ','Only chains minimize'],1,'Capacity saturation need not specify all last-level positions.')],
129:[('Does Huffman require preserving alphabetic leaf order here?',['Yes','No, leaves may be permuted','Only under equal weights'],1,'The exchange proof uses unrestricted leaf placement.'),('Contracting sibling weights 5 and 6 decreases cost by?',['1','11','30'],1,'Contracting the sibling pair removes one level from each leaf, decreasing the weighted sum by 5+6=11.'),('For weights 2,5,9, what is the optimal total merge cost?',['16','23','30'],1,'Merge 2+5=7, then 7+9=16; total 23.'),('With equal weights, must the optimal labeled tree be unique?',['Yes','No','Only for four leaves'],1,'Ties allow different equivalent optimal assignments.')],
130:[('A root slot also points to V. Should it count?',['No','Yes, under this exact count contract','Only if V is a leaf'],1,'All references in the contract must be counted.'),('One of two references to an object is removed. Reclaim it?',['Yes','No, its remaining count is positive','Only if values match'],1,'The surviving reference still needs the object.'),('A disconnected two-object cycle has counts 1,1. Is it live?',['Yes','No, no root reaches it','Only with two roots'],1,'Counts alone do not characterize reachability.'),('Can a self-loop cause a reference-count leak?',['Yes, even one object suffices','No, two objects are necessary','Only a tree can leak'],0,'The self-edge keeps the count positive.')],
131:[('When should an object be marked?',['After all descendants finish','Before scheduling it','Only during sweep'],1,'This avoids duplicate scheduling and cycles.'),('Why is the completed mark set all of R?',['It is closed under edges and contains the roots','Every address looks like a pointer','The scene is finite'],0,'Closure includes every finite root path.'),('A root points into a cycle. Which cycle objects survive?',['None','All reachable from that root','Only the root target'],1,'Traversal marks through the cycle and stops revisits.'),('May an unmarked object be swept while work remains?',['Always','Not under this two-phase contract','If its address is high'],1,'An undiscovered path may still reach it.')],
132:[('Does dropping frontier entries preserve correctness automatically?',['Yes','No, outgoing edges might never be inspected','Only if H=1'],1,'Lost obligations require recovery.'),('What extra state does this teaching variant use?',['A separate processed bit','No state at all','A copied heap'],0,'It differs explicitly from source Algorithm C.'),('With H=1, what recovers marked-but-unprocessed nodes?',['A scan of persistent obligations','Random guessing','Sweeping them free'],0,'Rescanning recovers unscheduled work.'),('Can a header field be reused if another live invariant needs it?',['Freely','No, unless its contents can safely be restored or are unnecessary','Only at odd addresses'],1,'Auxiliary storage must respect the representation contract.')],
133:[('May application code freely traverse borrowed links during collection?',['Yes','No, this model pauses mutation and traversal','Only during A reversal'],1,'The temporary graph is not the application representation.'),('What tells an upward step which field to restore?',['Screen position','The temporary control bit','The leaf value'],1,'The bit distinguishes A and B suspension.'),('What must hold at termination besides correct marks?',['All original links and ATOM bits are restored','Every cycle is broken permanently','All links become null'],0,'Pointer reversal borrows storage; it does not change graph semantics.'),('Does a self-link cause endless descent?',['Yes','No, the object is marked before following its fields','Only if the root is named X'],1,'The object is marked before inspecting its outgoing link, so its self-reference cannot trigger another descent.')],
134:[('Same name implies same object?',['Yes','No','Only in a tree'],1,'Identity and payload equality are separate.'),('Moving a field to another group necessarily changes its name index?',['Always','No, containment and naming are different relations','Only for DAY'],1,'Update obligations depend on which relation changed.'),('Two DAY entries in different groups need what?',['One overwritten parent field','Distinct IDs plus the needed relation fields','Two identical object IDs'],1,'Multiple linkage connects identities without conflating them.'),('What determines whether an extra link is worthwhile?',['Required operations and costs','The name of the algorithm','A universal rule to store all relations'],0,'Extra fields trade space and update work for access speed.')],
135:[('Can DAY OF ARRIVAL skip DATE?',['Yes, under this qualification convention','No, every parent must be named','Only if DATE is absent'],0,'Qualifiers match ordered ancestor positions.'),('What if zero candidates pass?',['Return first DAY','Report absent','Report ambiguous'],1,'Zero and multiple matches have different meanings.'),('DAY OF HARBOR in the example is?',['Unique','Ambiguous','Absent'],1,'Both DAY ancestors include HARBOR.'),('Two nodes with identical full name paths are?',['Automatically the same identity','Not distinguishable by this qualifier language','Resolved by address order'],1,'Storage order is not semantic disambiguation.')],
136:[('Should elementary items be paired by leaf position?',['Yes','No, storage order may differ','Only if names differ'],1,'Keys encode structural correspondence.'),('A duplicate key in one record should?',['Overwrite the earlier entry','Be reported as ambiguous','Choose the shorter payload'],1,'A mapping cannot silently hide duplicate semantic candidates.'),('DATE/MONTH versus DATE/YEAR are?',['A matching pair','Unmatched under exact relative paths','Identical groups'],1,'Different leaf names produce different keys.'),('Does a matching name authorize raw copying?',['Yes','No, types and capacity still need validation','Only if both are elementary'],1,'Name correspondence is only one precondition.')],
137:[('With four-byte alignment and zero overhead, 10 payload bytes reserve?',['10','12','16'],1,'Round upward to the next multiple of four.'),('Best fit selects?',['The earliest adequate address always','The smallest adequate block under its tie rule','The largest free block'],1,'It optimizes the immediate fit, not the whole future workload.'),('Two separated 8-byte holes can satisfy one 12-byte block?',['Yes','No, contiguous storage is required','Only under best fit'],1,'Their sum is not one interval.'),('If rounded size arithmetic would overflow?',['Wrap and continue','Reject before modifying the heap','Allocate the wrapped size'],1,'Wrapping can allocate too little storage and corrupt live data.')],
138:[('When may [4,12) and [12,20) merge?',['When both are free','Whenever either is free','Only if sizes differ'],0,'Touching free intervals may unite.'),('Consecutive free-list entries necessarily touch?',['Yes','No, live intervals can separate them','Only if sorted'],1,'List order is not physical adjacency.'),('Freeing a live block between two free neighbors creates?',['Three permanent holes','One merged free interval','Two copied live blocks'],1,'The returned interval touches free storage on both sides, so all three contiguous intervals form one free block.'),('Does coalescing move live objects?',['Yes','No','Only the right neighbor'],1,'Only adjacent free metadata changes.')],
139:[('Header and footer are four bytes each. Eight payload bytes need at least?',['8','12','16'],2,'Count both metadata boundaries.'),('Before reading a predecessor footer at the arena start?',['Read outside anyway','Use a sentinel or bounds guard','Assume zero'],1,'Boundary conditions prevent invalid reads.'),('When both neighbors are free, their list entries should be?',['Retained alongside the merged entry','Unlinked before merged metadata is installed','Copied into payload'],1,'One merged free interval must have one list entry.'),('Do boundary tags make all allocation searches O(1)?',['Yes','No, they make local neighbor discovery/coalescing efficient','Only with four-byte tags'],1,'Finding a suitable free block is a separate operation.')],
140:[('Request 17 in a byte-granular buddy model reserves?',['17','24','32'],2,'Round to the next power of two.'),('Buddy of offset 24 at size 8?',['16','32','8'],0,'The order-three sibling differs in bit three: flipping that bit in offset 24 gives 16.'),('Can size-eight offsets 8 and 16 merge?',['Yes, because they touch','No, they are not siblings','Only if both free'],1,'Their separate parents begin at 0 and 16.'),('For arena base B, the general buddy formula uses?',['Absolute address XOR always','Offset XOR, then add B','Address plus any free size'],1,'XOR reasoning belongs to the aligned arena offsets.')],
141:[('A fair policy comparison holds what fixed?',['Only policy names','The event stream and allocator conventions','Only final free bytes'],1,'Different inputs would confound the comparison.'),('Best fit probes every free candidate. Is this the same as first-fit work?',['Always','No, the stopping rules differ','Only for empty memory'],1,'Count executed probes, not just successful allocations.'),('A policy wins the given trace. What follows?',['It is universally best','It wins that measured trace under those conventions','All distributions prefer it'],1,'The result is workload-qualified.'),('Does an expected free-block-count ratio determine free-byte fraction?',['Yes','No, block sizes matter','Only if cycles exist'],1,'Counts and byte totals are different statistics.')],
142:[('Can two fixed four-byte slots coalesce for an eight-byte request?',['Yes','No, fixed slot boundaries forbid it','Only at steady state'],1,'Distributed fit preserves slot boundaries.'),('Which lifetime assumption is relevant in the source scheme?',['Equal departure chance among present blocks','Oldest always departs first','Largest always departs first'],0,'Age-independent equal departure is explicit.'),('Four size-eight arrivals and only three adequate slots yield?',['Four successes','A failure on the fourth','Coalescing of small slots'],1,'Total empty small capacity cannot replace an adequate slot.'),('Does O(N^−1/2 log N) mean zero finite overhead?',['Yes','No, actual reserve bytes still count','Only at N=16'],1,'Asymptotic decay is not zero cost or a deterministic guarantee.')],
143:[('A failed allocation may change which of these without breaking atomicity here?',['A diagnostic probe counter','A live payload','The live block boundary'],0,'Operational counters are separate from heap mutation.'),('Check size overflow when?',['After splitting','Before arithmetic and mutation','Only after failure'],1,'A wrapped endpoint could already corrupt storage.'),('Two holes become joined after freeing the intervening object. Why can retry succeed?',['The allocator ignores its contract','The valid heap state changed','Failure secretly moved bytes'],1,'Coalescing creates a larger contiguous interval.'),('Compaction is safe only if?',['Every affected reference is repaired or stable handles are used','Root pointers alone are repaired','Values remain equal'],0,'Interior and external references matter too.')],
144:[('What makes a node immediately accessible?',['Its address is numerically small','A pointer register holds it','Its payload matches a register'],1,'The abstract access rule is pointer-local.'),('P and Q have equal payloads. Must P=Q?',['Yes','No','Only after allocation'],1,'Distinct objects may carry the same value.'),('Copy Q from P, then create a fresh equal-valued object in P. Now?',['P and Q still alias','Values may agree while identities differ','Q becomes null'],1,'Allocation creates a new identity.'),('Why is unit-cost access an assumption?',['Physical latency and finite addresses impose limits','Pointers are mathematically impossible','Trees have no edges'],0,'The abstract cost model deliberately omits physical detail.')]
}

# Independently reviewed passage-specific transfers. These are not recycled
# assessments from adjacent passages; each preserves its passage's hypothesis.
HELP_ASSESS={
123:[
('Every node has at most depth+2 children. Is branching finite locally?','Yes, each particular depth gives a finite bound','No, one global bound is required','Depth+2 is finite at every vertex; a uniform bound is unnecessary.'),
('A vertex has three finite child subtrees. Can its whole subtree be infinite?','No','Yes, by repeating the picture','Three finite sets and one root have a finite union.'),
('The rule pⱼ has child pⱼ₊₁ holds for every j. What justifies continuation?','The rule for every index','The number of visible circles','An all-index definition establishes the family beyond a finite drawing.'),
('A root has one separate chain of length m for each m≥1. Must some branch be infinite?','No, each chosen chain ends','Yes, because depths are unbounded','Unbounded depth with infinitely many root children does not force an infinite branch.')],
124:[
('A lone root has a left leaf. Does moving that leaf to the right preserve its binary shape?','No','Yes, both have two vertices','Binary shapes distinguish the left and right positions even without labels.'),
('A four-node shape has a one-node left subtree. How many right-subtree choices remain?','Two','One','Two nodes remain on the right; its two binary shapes each give a different pair.'),
('In C=1+zC², what contributes the extra factor z?','The new root','Choosing an unordered pair','Multiplication chooses ordered children; the extra root increases size by one.'),
('An ordered general tree has three vertices. Which Catalan coefficient counts it?','C₂=2','C₃=5','Remove its root before applying the forest-to-binary bijection.')],
125:[
('A root has two identical leaf children. Does exchanging them create another unordered shape?','No','Yes','Children form a multiset; permutations of equal occurrences are not new shapes.'),
('With a₁=a₂=1, what is b₂=Σd|2 d·a_d?','3','2','Both divisors contribute: 1·a₁+2·a₂=1+2=3.'),
('A four-vertex path has two centroids. What does their edge do?','Splits it into two equal halves','Separates a single leaf from three vertices','The two-centroid case has adjacent centers whose intervening edge bisects the vertex count.'),
('On a three-vertex path, how many inequivalent root positions exist?','Two','Three','The endpoints are equivalent by reflection; the center gives the other rooted shape.')],
126:[
('A rooted code on three labeled vertices retains its designated root. How long is it?','Two symbols','One symbol','Removing all nonroot vertices emits n−1=2 symbols, unlike the standard code.'),
('For standard word (2), on labels 1,2,3, which leaf is removed first?','1','2','The smallest available label absent from the remaining word is 1.'),
('Decode rooted word (2,2). Which root remains?','2','1','Remove 1 and then 3 as smallest absent labels; both point to the remaining root 2.'),
('How many labeled free trees on three vertices are there?','3','9','The standard one-symbol word has three choices; choosing an additional root would multiply by three.')],
127:[
('A single internal root has how many external positions?','Two','One','Both null child slots become distinct external leaves in the full extension.'),
('One internal root and two external children have I and E equal to what?','I=0, E=2','I=1, E=1','The internal root has depth zero; each external child has depth one.'),
('Expanding an external square at depth one changes E−I by how much?','Two','One','Internal sum increases by 1, external sum by 3, so their difference increases by 2.'),
('For one ternary internal root, how many external children and what E?','Three children, E=3','Two children, E=2','The t-ary rule uses all three slots: E=(3−1)·0+3·1=3.')],
128:[
('Can five binary vertices all fit at depths zero and one?','No, those levels have only three places','Yes, shallow capacity is unlimited','The first two binary levels have capacities 1 and 2, totaling three.'),
('What internal path sum does a three-vertex chain have?','3','2','Its depths are 0, 1 and 2; the sum is 3, the maximum for this size.'),
('Using q=floor(log₂(n+1)), what is Imin when n=3?','2','3','q=2 gives (3+1)·2−2³+2=2, agreeing with depths 0,1,1.'),
('In a ternary tree, which vertex is parent of breadth-first vertex 5?','2','1','The parent formula gives floor((5+3−2)/3)=2; root children are 2,3,4.')],
129:[
('Can a required left-to-right leaf order invalidate a Huffman exchange?','Yes','No, exchanging leaves always preserves every constraint','The exchange assumes unrestricted leaf placement; prescribed order is a different problem.'),
('Weights 1 and 4 occupy depths 1 and 3. What does swapping them do to cost?','Reduces it by 6','Increases it by 6','The change is (1−4)(3−1)=−6, putting the heavier weight shallower.'),
('Merging sibling weights 2 and 3 adds how much to the contracted-tree cost?','5','6','Expansion adds one depth to each original leaf, contributing 2+3=5.'),
('Two leaves both weigh 2. What is their weighted path cost?','4','2','Each leaf has depth one, so 2·1+2·1=4; exchanging equal labels leaves cost unchanged.')],
130:[
('One root and one heap field point to V. What is rc(V)?','2','1','Both counted incoming slots contribute even though their source kinds differ.'),
('A has no references left and its only edge reaches B, whose count is one. What follows?','Reclaim A, then B after decrement','Reclaim A but never inspect B','Deleting A removes B’s sole incoming reference and triggers the next zero-count step.'),
('An unrooted node points to itself. Can exact reference counting alone reclaim it?','No','Yes, because there is no root','Its self-edge maintains a positive count despite the lack of root reachability.'),
('A real root is omitted from the collector input. Can an otherwise correct collector become unsafe?','Yes','No, heap links always reveal all roots','The proof depends on a complete root set; an omitted sole root can hide a live object.')],
131:[
('A reachable child is still undiscovered while the frontier is nonempty. May it be swept now?','No','Yes, its mark is clear','Marking must finish before sweep; a pending path can still discover this live child.'),
('Two marked parents discover the same child. How many times should that child enter the worklist?','Once','Twice','Marking before scheduling lets the second discovery recognize work already scheduled.'),
('A completed marked set contains all roots and is closed under edges. Can a root path leave it?','No','Yes, if the path is long','Induction along a finite root path keeps every successive endpoint in the closed set.'),
('An atom contains a number equal to another object’s address. Must the collector follow it?','No','Yes, every address-looking value is a link','Only declared pointer fields define reachability; atomic payload is not traversed.')],
132:[
('A full frontier drops the only pending pointer to B. What obligation must remain recoverable?','Inspecting B’s outgoing fields','Erasing B’s mark','A discovered object can still hide descendants until its fields are processed.'),
('Marked(B)=1 and processed(B)=0. Is B’s work complete?','No','Yes, marking is enough','The separate processed bit distinguishes discovery from inspection of outgoing fields.'),
('With one slot occupied by B, C is marked but omitted. How can C later be processed?','A scan finds C in marked minus processed','C must already be unreachable','Persistent obligations preserve the work that the limited frontier cannot hold.'),
('Can a live header pointer be overwritten as scratch without restoration?','No','Yes, because the collector needs space','Reusing a field is sound only if its prior meaning is unnecessary or correctly restored.')],
133:[
('Why must ordinary traversal pause while an A link stores a return pointer?','That stored link temporarily has a different meaning','The original graph has become permanently cyclic','Borrowing links preserves the graph only after restoration, not during arbitrary observations.'),
('Returning through an A-reversal frame must restore which control state?','The original A link and ATOM=0','Only the mark bit','The temporary ATOM flag identifies the A frame and must be cleared when restoring its link.'),
('Correct live marks remain, but one original link changed. Has pointer-reversal collection succeeded?','No','Yes, marks are the only output','The algorithm promises both correct marking and restoration of original link and ATOM fields.'),
('The current node already has its mark set and points to itself. Does that edge descend again?','No','Yes','The target’s existing mark blocks a repeated descent, so a self-cycle terminates.')],
134:[
('Two records have the same text name but different parents. Must they share identity?','No','Yes','Naming and containment relate separately allocated records without merging their identities.'),
('A record keeps its name but changes parent. Which relation certainly needs updating?','Containment','Its text name','A parent change affects containment links even when the same-name index can stay unchanged.'),
('A new level-number record decreases to a level absent from the open ancestor stack. Accept it?','No, it mixes sibling levels','Yes, attach it anywhere','The builder requires a matching prior level for siblings; an absent level violates that format.'),
('A workload never navigates backward among siblings. Is an extra backward link automatically worthwhile?','No','Yes, more links always improve total cost','Extra fields impose storage and update costs; usefulness depends on required operations.')],
135:[
('DAY has two candidates and no qualifier. May storage order choose one?','No, the result is ambiguous','Yes, take the first','Candidate enumeration must preserve both semantic possibilities regardless of their storage order.'),
('Ancestors from nearest outward are DATE, ARRIVAL, HARBOR. Does DAY OF HARBOR OF ARRIVAL match?','No','Yes, both names occur','Qualifiers must occur in the requested outward order, not merely somewhere in the chain.'),
('A qualifier matches exactly one of two candidate DAY records. What status results?','Unique','Ambiguous','Status depends on the filtered candidate set, not on the original count of equal names.'),
('Two distinct fields have identical full ancestor-name paths. Can adding more of those names select one?','No','Yes, repeat the same qualifiers','This language cannot distinguish identical complete paths without another naming convention.')],
136:[
('Left record stores A then B; right stores B then A. Which pairs are candidates?','A with A and B with B','A with B and B with A','Equal relative names, not physical positions, define correspondence.'),
('At the same matched path, the left item is elementary and the right is a group. What happens?','Output this pair and stop descending','Reject solely because one side is a group','The source rule stops and outputs when either side is elementary; conversion remains separate.'),
('DATE/DAY and CARGO/DAY have equal terminal names. Do they correspond?','No','Yes','Complete relative qualification includes containing group names, so these keys differ.'),
('A matching source number needs eight bytes but its destination has four. Is name matching enough to copy?','No','Yes','The matching algorithm does not validate representation, conversion or destination capacity.')],
137:[
('With alignment four and no overhead, how many bytes does payload five require?','8','5','The smallest permitted aligned size at least five is eight bytes.'),
('Adequate holes have sizes 20 then 12; need is 8. Which does best fit choose?','12','20','Best fit minimizes adequate block size; first fit would select the earlier 20-byte hole.'),
('A 16-byte hole serves an 8-byte block with minimum remainder four. What remains?','An 8-byte free hole','No free space','Splitting partitions the original 16 bytes into disjoint reserved and free intervals of eight.'),
('Two nonadjacent 4-byte holes face an 8-byte request. Can their totals justify success?','No','Yes','A contiguous request needs one adequate interval; adding separated hole sizes is insufficient.')],
138:[
('May the same allocation be freed twice under this contract?','No','Yes, freeing is always harmless','The precondition requires a currently live allocation; the second release violates it.'),
('Free intervals [0,4) and [8,12) are consecutive list entries. May they merge?','No','Yes','Their endpoints do not touch; the missing interval may contain a live allocation.'),
('Free [0,4), live [4,8), free [8,12): after releasing the live block, what free interval results?','[0,12)','Two separate 6-byte blocks','Both adjacent boundaries disappear, yielding the union of all three contiguous regions.'),
('A live block at offset 20 remains live while nearby holes coalesce. Does its offset change?','No','Yes','Coalescing changes only free-region metadata; moving a live block would be compaction.')],
139:[
('Four-byte endpoint tags surround a four-byte payload. Is eight bytes enough for that allocated block?','No, the tags and payload already need twelve','Yes, the footer is outside the block','Both boundary tags belong inside the reserved size; the model may also impose a larger minimum.'),
('A block starts at arena offset zero. Where is its preceding footer?','Outside the arena, so do not read it','At offset minus four, safe to dereference','The bounds guard must run before attempting a predecessor-footer read.'),
('Unlink middle free node Q between P and R. Which reciprocal links must change?','P.next=R and R.prev=P','Only Q.next','Both neighboring links must bypass Q to preserve reciprocal list navigation.'),
('After constant-size tag coalescing, can finding a large enough block still need a long scan?','Yes','No','Local neighboring-block operations do not eliminate the independent free-list search cost.')],
140:[
('A buddy request for five bytes uses which block size?','8','6','Buddy blocks have power-of-two sizes, so five rounds upward to eight.'),
('At block size four, what is the buddy of relative offset four?','0','8','Flipping the size bit gives 4 xor 4 = 0, its sibling under the same eight-byte parent.'),
('Two free size-four siblings merge. Can their size-eight parent merge with a free size-four neighbor?','No','Yes','Recursive merging requires a free buddy of the same new order, not merely adjacent free space.'),
('Arena base is 100, block offset 8 and size 8. What is its buddy address?','100','116','Compute 100+(8 xor 8)=100; XOR uses offsets relative to the arena base.')],
141:[
('Policies use identical requests but different alignment. Is their utilization comparison controlled?','No','Yes','Alignment changes reserved sizes independently of placement policy and confounds the comparison.'),
('An allocation fails under one policy before a later named release. What must the experiment specify?','How that release is handled consistently','That every release silently frees another block','Failure handling belongs to the workload contract and must not corrupt one policy’s state.'),
('A smaller immediate remainder is observed. Does that prove fewer future failures?','No','Yes','Future success depends on later request sizes and the whole arrangement of holes.'),
('Five free blocks and ten live blocks imply what fraction of bytes is free?','It cannot be determined from counts alone','Exactly one third','The sizes of both kinds of block are required to turn counts into byte fractions.')],
142:[
('Two empty four-byte fixed slots remain. Can an eight-byte request occupy both?','No','Yes','The distributed-fit inventory assigns at most one block to one fixed-boundary slot.'),
('Does reserve overhead O(N^−1/2 log N) guarantee every finite request trace succeeds?','No','Yes','The asymptotic probabilistic conclusion is neither zero reserve nor a deterministic guarantee.'),
('The smaller inventory has one eight-byte slot. What happens to a second eight-byte arrival without release?','It fails although smaller slots may be empty','It combines the two four-byte slots','Only one slot is adequate, and fixed boundaries cannot be coalesced.'),
('Observed lifetimes now correlate strongly with size. Keep the old forecast guarantee without review?','No','Yes','The stated performance model depends on its departure law as well as the size inventory.')],
143:[
('Free bytes total eight, but the largest hole is four. What blocks an eight-byte request?','External fragmentation','Lack of eight free bytes in total','The total is sufficient but no single contiguous interval can satisfy the request.'),
('MAX=31, overhead=4 and alignment=4. Is payload 25 allowed by r≤MAX−h−(a−1)?','No','Yes','The bound is 31−4−3=24, so rejection precedes the potentially overflowing addition.'),
('Retrying unchanged failed input without any state change must create capacity?','No','Yes','A retry succeeds only if a relevant condition changes; failure itself leaves the heap unchanged.'),
('A compactor repairs root pointers but leaves a heap field pointing to an old address. Safe?','No','Yes','Every affected reference, including heap and interior pointers, must follow the moved object.')],
144:[
('A node is reachable through ten links but held in no register. Is it immediately accessible?','No','Yes','The abstract machine accesses held nodes directly; it must follow links to reach this one.'),
('P and Q alias A. Writing A’s payload through P changes what Q reads?','Yes','No','Both pointers denote the same object, so either access observes its updated payload.'),
('A traversal expects child links but receives threaded links without tags. Is its old invariant sufficient?','No','Yes','The meanings of edges changed; traversal must distinguish navigation threads from real children.'),
('A fixed w-bit address field supports arbitrarily many distinct simultaneously addressable locations?','No','Yes','Only finitely many bit patterns exist; an unbounded abstract heap is not a literal finite machine.')]
}

# Correct displaced main questions so they test the claim in their own passage.
ASSESS[124][2]=('What combinatorial operation does C(z)² represent?',['Ordered pairs of child shapes','Unordered multisets','Selecting one labeled root'],0,'The product chooses a left shape and a right shape independently and preserves their positions.')
ASSESS[124][3]=('How many ordered general trees have five vertices?',['42','5','14'],2,'Removing the ordered root leaves a four-node binary encoding, counted by C₄=14.')
ASSESS[126][2]=('Which fact makes leaf-removal encoding invert its decoder?',['Both choose the smallest available label absent from the remaining suffix','Both sort the edges by length','Both ignore vertex labels'],0,'The remaining-word degree invariant identifies exactly the same leaf at every induction step.')
ASSESS[127][1]=('Does internal path length mean the maximum internal depth?',['Yes','No, it sums all internal depths'],1,'Height is a maximum; internal path length adds the depth of every internal vertex.')
ASSESS[128][3]=('In ternary breadth-first numbering, parent of vertex 8 is?',['2','3','4'],1,'The exact formula floor((8+3−2)/3)=3 determines the parent; each parent has three child slots.')
ASSESS[129][1]=('Why may the two least weights be placed at deepest sibling leaves?',['Exchanging lighter weights downward cannot increase weighted depth cost','All optimal trees are balanced','The original sorted pairs must be adjacent'],0,'The cost difference (small−large)(deep−shallow) is nonpositive under unrestricted leaf order.')
ASSESS[130][3]=('A live root was omitted from the root set. Is reachability-based collection necessarily safe?',['Yes','No, it may reclaim an object that root still needs'],1,'The liveness proof requires a complete root set and all recognized pointer fields.')
ASSESS[131][0]=('May an unmarked object be swept while marking work remains?',['Always','Not under this two-phase contract','If its address is high'],1,'An undiscovered path from pending work may still reach the object.')
ASSESS[131][1]=('When should an object be marked?',['After all descendants finish','Before scheduling it','Only during sweep'],1,'Mark-before-schedule prevents repeated scheduling through shared references and cycles.')
ASSESS[131][2]=('Why is the completed mark set all of R?',['It contains roots, is edge-closed, and every marked node was discovered along a root path','Every address-looking payload is followed','The picture has finitely many nodes'],0,'Discovery proves marked⊆R; closure along each finite root path proves R⊆marked.')
ASSESS[131][3]=('Which work is added by sweeping after marking?',['A scan of all allocated slots','Only visiting live edges again','No work at all'],0,'Marking follows reachable edges, while sweep must inspect all allocated objects, including unreachable ones.')
ASSESS[135][1]=('Do qualifiers require adjacent parent names?',['Yes','No, they match an ordered outward subsequence'],1,'Unspecified intermediate ancestors may be skipped, but qualifier order and distinct positions must be preserved.')
ASSESS[136][1]=('At a matching path, only one item is elementary. What is the correspondence step?',['Output the pair and stop this descent','Reject because both must be elementary','Descend through the elementary item'],0,'The source stops when either current item is elementary; byte conversion is a separate later obligation.')
ASSESS[137][2]=('A free block of 20 bytes serves a rounded 12-byte request with minimum free size four. The remainder is?',['8 free bytes','12 free bytes','No free remainder'],0,'A valid split replaces exactly the selected interval by disjoint sizes 12 and 8, preserving total capacity.')
ASSESS[138][0]=('Which allocation may be returned under the liberation precondition?',['A currently live allocation exactly once','Any interior address','An already freed allocation'],0,'Release requires ownership of a live allocation, not an arbitrary address or duplicate release.')
ASSESS[142][1]=('What does shrinking asymptotic reserve fraction establish here?',['A model-qualified limiting overhead rate','Zero finite reserve bytes','Guaranteed success for every trace'],0,'The probabilistic assumptions and actual finite reserve still matter; asymptotic order is not a deterministic guarantee.')
ASSESS[142][3]=('If measured lifetimes violate the forecast departure law, what follows?',['Reassess the slot plan and its performance claims','Keep the same guarantee automatically','Coalesce arbitrary fixed slots'],0,'The forecast conclusions depend on both request-size and lifetime assumptions, so changed evidence needs review.')
ASSESS[144][2]=('Changing a link representation requires what before reusing a traversal?',['Rechecking the traversal invariant against the new link meanings','Only changing colors','Assuming equal payloads imply equal nodes'],0,'Algorithms depend on representation-specific invariants, including which stored relations are valid traversal edges.')

def helper_assessment(order,part):
    q,right,wrong,why=HELP_ASSESS[order][part]
    i=(order+part)%2
    return check(q,[right,wrong] if i==0 else [wrong,right],i,why)

SOURCE_RANGES={123:'608–610',124:'618–619',125:'614–617',126:'620–622',127:'634–636',128:'636–638',129:'638–642',130:'656–658',131:'658–660',132:'660–662',133:'662–665',134:'670–677',135:'672–678',136:'679–681',137:'685–690',138:'690–693',139:'693–695',140:'695–698',141:'698–706',142:'706–708',143:'708–709',144:'722–725'}
FOCUS_NOTES={
123:['Each vertex has finitely many children','An infinite subtree has an infinite child subtree','A finite prefix illustrates a defined infinite family','Infinite branching invalidates the selection argument'],
124:['Empty children are valid shapes','A split determines a disjoint Cartesian product','All root splits contribute to the exact count','Ordered and unordered are different equivalence rules'],
125:['Child shapes are unordered multisets','Sorted structural codes erase labels and coordinates','Different roots may belong to one symmetry class','Free counts need a centroid correction'],
126:['Stop at two vertices for standard Prüfer coding','The absent suffix label is the next leaf','Emitted labels reconstruct the same tree','Two vertices give the empty standard word'],
127:['Squares represent every null position','One expansion increases E minus I by two','Depths are summed, not maximized','The empty tree has one square at depth zero'],
128:['Shallow levels have finite capacity','A chain realizes every successive depth','Rearranging shape changes I but not n','Minimum shapes need not be unique'],
129:['Leaf weights are not interchangeable costs','Two smallest weights can be deepest siblings','Each merge adds its combined weight','Equal weights allow nonunique optimal trees'],
130:['Counts include roots and heap references','Zero counts trigger an exact decrement cascade','Reachable sharing must preserve the target','A cycle may have no root and no zero count'],
131:['Allocated and reachable are different sets','Marking before scheduling prevents revisits','Empty frontier establishes edge closure','A rooted cycle survives; an unrooted cycle does not'],
132:['The work frontier has an explicit capacity','Marked but unprocessed remains an obligation','Rescanning recovers work not held in the stack','Representation assumptions determine usable storage'],
133:['P and T describe current and suspended work','Borrowed fields encode a reversible return path','Every displayed link is its current stored value','An already marked self-link is not followed'],
134:['One record has multiple independent relations','Containment and name-index invariants differ','Same name does not imply same identity','Qualification can reject an absent containing group'],
135:['Start with all equal-name candidates','Qualifiers match an ordered ancestor subsequence','Zero, one and several matches are separate results','Complete-path collisions cannot be resolved by order'],
136:['Correspondence uses a qualified elementary key','Output if either item is elementary; otherwise descend','Reordered leaves can have equal keys','Equal leaf words can still have unequal keys'],
137:['Every byte belongs to one live or free interval','Round and validate before selecting a block','Split changes only one free interval','Failure preserves the prior allocation state'],
138:['Only a currently live block may be returned','Touching free endpoints justify a merge','Returning the bridge permits a three-way union','Failure cannot manufacture an adjacent interval'],
139:['Tags belong inside accounted block sizes','Guard the arena ends before neighboring reads','Unlink neighboring free blocks before rewriting tags','Eight metadata bytes reduce usable capacity'],
140:['Every interval has power-of-two size and alignment','XOR flips the sibling bit relative to arena base','Free same-order siblings merge recursively','Touching intervals need not be buddies'],
141:['Both policies receive the identical event','Count actual free-list probes separately','Placement changes the shape of later holes','One trace never establishes a universal winner'],
142:['Slot boundaries and inventory are fixed','Source performance requires size and lifetime laws','A shifted mix can exhaust the adequate slots','Empty small capacity cannot serve a large request'],
143:['Fragmentation differs from aggregate exhaustion','Size arithmetic is validated before mutation','A failed request is an allocation-state no-op','Recovery must preserve all existing live references'],
144:['Registers hold null or actual object identities','Copy creates aliases; allocation creates identities','Following a link changes the held object','Equal payloads do not imply equal pointers']}

def family(order,small=False):
    if order==123:return infinity_frames(2 if small else 4)
    if order==124:return catalan_frames(2 if small else 4)
    if order==125:return canonical_frames(3 if small else 4)
    if order==126:return prufer_frames([2] if small else [4,4,2])
    if order==127:return path_frames(small)
    if order==128:return balance_frames(3 if small else 5)
    if order==129:return huffman_frames([2,3,7] if small else [3,4,8,10])
    if order==130:return ref_frames(small)
    if order==131:return mark_frames(small)
    if order==132:return mark_frames(small,True)
    if order==133:return reverse_frames(small)
    if order in (134,135,136):return record_frames(order,small)
    if order in (137,138,139,143):return allocation_frames(order,small)
    if order==140:return buddy_frames(small)
    if order==141:return comparison_frames(small)
    if order==142:return slots_frames(small)
    return machine_frames(small)

def focus_frames(frames,order,part,help=False):
    if order==136 and part==1:return correspondence_stop_frames(help)
    if order==139 and part==2:return tag_unlink_frames(help)
    if part==0:frames=frames[:2]
    elif part==1:
        mid=max(0,(len(frames)-2)//2);frames=frames[mid:mid+2]
    elif part==3:frames=boundary_frames(order,help)
    frames=copy.deepcopy(frames)
    if len(frames)==1:
        # Degenerate instances still have an inspect phase and a verified endpoint.
        inspected=copy.deepcopy(frames[0]);verified=copy.deepcopy(frames[0])
        inspected['caption']='Inspect the boundary input before applying the rule. '+inspected['caption']
        for nd in inspected['diagram']['nodes']:
            if nd.get('role')=='result':nd['role']='input'
        verified['caption']='Verify the boundary result: '+verified['caption']
        note=FOCUS_NOTES[order][part]
        note_y={124:315,134:385,135:390,137:410,138:410,139:410,143:410}.get(order,365)
        verified['diagram']['nodes'].append(txt('boundary-verified',360,note_y,note,'result',14))
        verified['diagram']['nodes'][-1]['result']=True
        frames=[inspected,verified]
    for i,s in enumerate(frames):
        s['id']=f'{"help" if help else "main"}-{order}-{part}-{i}'
        s['diagram']['invariant']=FOCUS_NOTES[order][part]
        s['diagram']['title']=(['Identify the objects: ','Follow the invariant: ','Work the concrete trace: ','Test the boundary: '][part])+s['diagram']['title']
        # Endpoint claims wait for the renderer's verify phase; geometry still exists during transform.
        for n in s['diagram']['nodes']:
            if n['id'] in ('sum','total','cost','account','result','inventory'):
                n['result']=True;n['phase']='result'
        s['caption']+=' Focus: '+FOCUS_NOTES[order][part]+'.'
    expanded=[]
    for original in frames:
        bridges=original.pop('_bridges',[])
        for j,bridge in enumerate(bridges):
            bridge['id']=original['id']+'-derive-'+str(j)
            bridge['diagram']['invariant']=original['diagram']['invariant']
            expanded.append(bridge)
        expanded.append(original)
    return expanded

# Learner-facing symbol readings, intentionally separate from renderer instructions.
LEARNER_NOTATION = {(123, 0): 'The vertical bars count members of the children set, and ∞ means unbounded size; the condition '
           'says every individual node has only finitely many immediate children.',
 (125, 0): 'Write A(z)=Σ_{n≥1} a_n z^n: the coefficient of z^n counts rooted shapes of size n. The '
           'variable z records size; it is not a vertex label.',
 (125, 1): 'The condition d|k means d is a positive divisor of k. Thus b_4=1·a_1+2·a_2+4·a_4; the prime on '
           'A′ denotes formal differentiation of the series.',
 (125, 2): 'F(z)=Σ_{n≥1} f_n z^n records free, unrooted shapes, while A(z) records rooted shapes. Products '
           'of these series count pairs whose vertex counts add.',
 (125, 3): 'Here f_n counts free shapes of size n. The bracket [2|n] is 1 when n is even and 0 otherwise; '
           'it enables the equal-half correction only when two halves of size n/2 are possible.',
 (127, 0): 'Here n counts circles and s counts external squares; it does not count the depth labels '
           'printed inside them.',
 (127, 1): 'The notation d(v) means the depth of vertex v. Each sum adds one such depth for every vertex '
           'of its specified kind.',
 (130, 0): 'The abbreviation rc(v) is the reference count of object v; the # sign means count the listed '
           'incoming references, including repeated references from different fields.',
 (131, 0): 'R denotes the objects reachable from roots, G the garbage objects, and V all currently '
           'allocated objects. The set difference V\\R means the allocated objects not in R.',
 (131, 3): 'E_R is the set of outgoing pointer edges from reachable objects. The bars |V| and |E_R| count '
           'objects and edges respectively; T is total work.',
 (132, 0): 'H is the maximum number of pending object pointers the frontier can hold; |frontier| counts '
           'the pointers currently stored there.',
 (133, 0): 'P is the current object, Q is a saved child pointer, and T is the top of the return chain. A '
           'and B are the two link-field names, not the identities of particular nodes.',
 (135, 0): 'A_0 is the requested field name, followed by ancestor names A_1 through A_k in the written '
           'order. For DAY OF ARRIVAL, A_0=DAY and A_1=ARRIVAL; these are names to match, not node IDs.',
 (135, 1): 'The positive integers d_1,…,d_k count parent steps from candidate v. Parent^{d_j}(v) means '
           'follow the parent link d_j times, so the strict inequalities require distinct ancestors in the '
           'requested order.',
 (137, 0): 'C is the arena’s total byte capacity, r the requested payload bytes, and h the metadata '
           'overhead per allocation. The ceiling rounds (r+h)/4 up to a whole number of four-byte units; '
           'here h=0, so request 9 needs 4×3=12 bytes.',
 (138, 0): 'p is the block’s starting byte address and s its size. The interval [p,p+s) includes p but '
           'stops just before p+s, covering exactly s bytes.',
 (138, 1): 'In p+s=q, p and s are the lower block’s start and size, and q is the next block’s start. For '
           'example, [0,8) and [8,16) touch because 0+8=8.',
 (140, 0): 'The exponent m sets the whole arena size; k sets the current block size. x is that block’s '
           'offset from the arena base. The congruence means x is an exact multiple of 2^k.',
 (140, 1): 'XOR compares binary digits and flips a digit exactly where one input has 1 and the other 0. '
           'XOR with 2^k flips only bit k, exchanging the two equal halves of one parent block.',
 (141, 0): 'U is payload utilization and C the full arena capacity in bytes. Reserved padding does not '
           'count as live payload in its numerator.',
 (142, 0): 'N_live counts allocations currently present, and v names one of them. The probability formula '
           'gives every such allocation the same chance to be the next departure.',
 (143, 1): 'In the guard, r is payload size, h metadata overhead, a alignment, and MAX=2^w−1 the largest '
           'representable unsigned size. Subtracting the overhead and worst-case padding before testing r '
           'avoids overflowing the addition itself.',
 (144, 0): 'V is the set of allocated object identities; null is an extra marker outside that set. '
           'Membership in V∪{null} specifies what a pointer register may hold.'}

HELPER_CONNECTIONS = {123: 'The p-chain continues because its defining rule gives every p-node another p-child; an f-node has '
      'none. The larger window uses that same rule, rather than proving infinity by displaying more nodes.',
 124: 'Each distinct left/right pair creates one binary shape with a new root. Empty children count as one '
      'choice, and the root uses one of the total vertices.',
 125: 'Moving the root to symmetric positions can give the same rooted shape. Count distinct structures, '
      'not the number of drawn vertex labels.',
 126: 'At each step the smallest available leaf supplies an edge and its neighbor supplies the next code '
      'symbol. The same rule reconstructs the larger tree.',
 127: 'A circle contributes its depth to I; a square contributes its depth to E. Expanding one square '
      'changes these sums by d and d+2 respectively.',
 128: 'The node count stays fixed while depths change. Filling shallow positions reduces the sum of '
      'depths; it does not change the number of objects.',
 129: 'Merging two available weights adds one depth to every leaf they contain. Their combined weight is '
      'therefore exactly the additional weighted-path cost.',
 130: 'Deleting one pointer removes one incoming reference, not every ownership claim. A disconnected '
      'cycle can still keep positive reference counts.',
 131: 'The root path determines which allocated objects are live. Only after the frontier is exhausted may '
      'the unmarked allocated objects be reclaimed.',
 132: 'A marked but unprocessed object remains an obligation even if it could not fit on the frontier. A '
      'rescan restores that work instead of dropping it.',
 133: 'Borrowed link fields encode the return route temporarily. Every descent must later restore its '
      'original child target and control bit.',
 134: 'The same object may have a parent link, a sibling link and a same-name link. Changing one '
      'relationship does not change the meaning of the other fields.',
 135: 'Candidate names and ancestor names play different roles. A qualifier may skip an intermediate '
      'group, but its matches must stay in ancestor order.',
 136: 'Matching follows complete relative name paths. Different storage order does not change a match, and '
      'equal final names in different groups are insufficient.',
 137: 'The rounded block size includes all required bytes. Reserving one interval transfers bytes from '
      'free to live storage without moving the neighboring blocks.',
 138: 'Only equal endpoints make two free intervals adjacent. Returning the block between two holes '
      'permits a three-way merge while other live addresses stay fixed.',
 139: 'The neighboring footer or header identifies a physical block. Unlink a free neighbor before '
      'replacing its metadata with the merged outside tags.',
 140: 'A split produces two equal halves of one parent. Only those same-size, aligned siblings can merge; '
      'ordinary neighbors need not be buddies.',
 141: 'The same requests and releases are applied to both policies. Compare their actual remaining '
      'intervals and probes rather than deciding from the policy’s name.',
 142: 'Empty bytes in separate undersized slots cannot serve a larger request. The same mismatch explains '
      'failure in the larger fixed inventory.',
 143: 'A failed request leaves every live block unchanged. A later legitimate release may join holes and '
      'make the same request possible.',
 144: 'P and Q contain object identities. Equal payloads can belong to different objects; copying a '
      'pointer makes two registers refer to one object.'}
HELPER_NOTATION = {(137, 0): 'Here C=32 bytes, alignment is 4 and overhead h=0. A request r=5 needs 4 × ceil(5/4)=8 bytes; '
           'the remaining 24 bytes stay free.',
 (138, 0): 'In this 32-byte example, A occupies [0,8), B [8,16), and C [16,24). A start address and a byte '
           'size are different quantities.',
 (140, 0): 'The smaller arena has 2^4=16 bytes. Its four-byte blocks have size 2^2 and start only at '
           'multiples of 4; offset 0 is not the same thing as size 4.'}

def build():
    plan=json.loads(PLAN.read_text());lessons=[]
    for item in plan['lessons']:
        order=item['order'];main=family(order);small=family(order,True);passages=[]
        for j,(title,text,formula) in enumerate(TEXT[order]):
            notation=LEARNER_NOTATION.get((order,j),'')
            if notation:
                first,sep,rest=text.partition('\n\n'); text=first+' '+notation+sep+rest
            states=focus_frames(main,order,j);helpstates=focus_frames(small,order,j,True)
            a=ASSESS[order][j]
            if notation: states[0]['teachingExplanation']=states[0]['caption']+' '+notation
            helper_note=HELPER_NOTATION.get((order,j),notation)
            if helper_note: helpstates[0]['teachingExplanation']=helpstates[0]['caption']+' '+helper_note
            d=demo(f'F-{order}-{j}',states,helpstates,check(*a),helper_assessment(order,j),model=dict(semanticFamily=item['id'],focus=FOCUS_NOTES[order][j],execution='Python integer/set model; generated exact states',scope='Finite worked instances; theorem proofs are in the prose.'),intro=helpstates[0].get('teachingExplanation',helpstates[0]['caption']),connection=HELPER_CONNECTIONS[order])
            passages.append(dict(id=f'{item["id"]}-{j}',title=title,text=text,formula=formula,demonstration=fix_transitions(d)))
        lessons.append(dict(id=item['id'],order=order,title=item['title'],source=dict(book='Donald E. Knuth, The Art of Computer Programming, Volume 1, third edition',section='§'+item['source_sections'][0]['section']+' '+item['source_sections'][0]['title'],pdfPages=SOURCE_RANGES[order],pagination='one-based supplied ebook, not printed'),provenance='Original prose, examples, diagrams and assessments. Source formulas and algorithm conditions checked against the supplied edition; no textbook pages, exercise text or scans are included.',scope=('Selective companion treatment: '+ '; '.join(item.get('objectives',[]))+'. Exact finite models supplement, rather than replace, the mathematical arguments. '+('Implements complete relative qualification with either-side-elementary stopping; not a full COBOL implementation.' if order==136 else '')),sections=[dict(id=item['id']+'-section',title=item['title'],passages=passages)]))
    target=ROOT/'content/fullbook/batch-F.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(lessons,ensure_ascii=False,indent=2)+'\n');return lessons

def tag_table(blocks,tagbytes=4):
    table={}
    for b in blocks:
        assert b['size']>=2*tagbytes
        value=(b['size'],b['id'] is not None)
        table[b['start']]=value;table[b['start']+b['size']-tagbytes]=value
    return table

def validate_tags(h):
    t=tag_table(h.blocks)
    for b in h.blocks:
        assert t[b['start']]==t[b['start']+b['size']-4]
        if b['start']>0:
            size,allocated=t[b['start']-4];assert b['start']-size in t
        nxt=b['start']+b['size']
        if nxt<h.size:assert nxt in t
    return t

def selftest():
    checks={}
    for n in range(9):
        assert len(binary(n))==catalan(n)
        for t in binary(n):
            i,e,k,s=paths(t);assert k==n and s==n+1 and e==i+2*n
        if n:
            q=(n+1).bit_length()-1;minimum=(n+1)*q-2**(q+1)+2
            assert min(paths(t)[0] for t in binary(n))==minimum
            assert max(paths(t)[0] for t in binary(n))==n*(n-1)//2
    checks['binary_shapes_exhaustive_n0_to_8']=sum(len(binary(n)) for n in range(9))
    for t in range(2,6):
        for n in range(101):
            total=0
            for k in range(1,n+1):
                d=0
                while k>1:k=(k+t-2)//t;d+=1
                total+=d
            q=0
            while t**(q+1)<=(t-1)*n+1:q+=1
            expected=(Fraction(n)+Fraction(1,t-1))*q-Fraction(t**(q+1)-t,(t-1)**2)
            assert total==expected
    checks['tary_exact_formula_cases']=404
    a=rooted_counts(8);f=free_counts(8);assert a[1:]==[1,1,2,4,9,20,48,115] and f[1:]==[1,1,1,2,3,6,11,23]
    count=0
    for n in range(2,7):
        rooted=set();free=set()
        for code in itertools.product(range(1,n+1),repeat=n-2):
            edges=prufer_decode(code);assert prufer_encode(edges)==list(code);g=adjacency(edges)
            assert len(edges)==n-1 and len(reachable({k:list(v) for k,v in g.items()},[1]))==n
            free.add(free_code(g));rooted.update(root_code(g,v) for v in g);count+=1
        assert len(rooted)==a[n] and len(free)==f[n]
    for n in range(2,6):
        for code in itertools.product(range(1,n+1),repeat=n-1):
            edges,root=rooted_decode(code);assert rooted_encode(edges,root)==list(code)
    checks['prufer_words_and_independent_isomorphism_oracle']=count
    for m in range(1,6):
        for weights in itertools.combinations_with_replacement(range(1,5),m):assert huffman(weights)[0]==optimal_merge(weights)
    checks['huffman_all_multisets_weights1_to4_sizes1_to5']=sum(math.comb(4+m-1,m) for m in range(1,6))
    cases=0
    ids=['A','B','C'];choices=[None]+ids
    for fields in itertools.product(choices,repeat=6):
        g={x:list(fields[2*i:2*i+2]) for i,x in enumerate(ids)}
        graph={x:dict(a=g[x][0],b=g[x][1],atom=0) for x in ids}
        for root in ids:
            expect=reachable(g,[root]);actual,frames=reverse_mark(graph,root);assert actual==expect
            assert mark_stack(g,[root])[0]==expect
            assert bounded_mark(g,[root],1)[0]==expect;cases+=1
    # Atom payload links must be ignored, including apparent self/cross references.
    graph={'A':dict(a='B',b=None,atom=0),'B':dict(a='C',b='B',atom=1),'C':dict(a=None,b=None,atom=0)}
    assert reverse_mark(graph,'A')[0]=={'A','B'}
    checks['three_node_graphs_times_roots_restoration']=cases
    for policy in ['first','best']:
        for request in range(1,70):
            h=Heap(64,overhead=8,minblock=16);before=h.snapshot();ok=h.alloc('A',request,policy)
            if ok:
                h.validate();validate_tags(h);h.free('A');assert h.blocks==before
            else:assert h.snapshot()==before
        h=Heap(64,overhead=8,minblock=16);before=h.snapshot();assert not h.alloc('X',2**31-1) and before==h.snapshot()
    for leftfree,rightfree in itertools.product([False,True],repeat=2):
        h=TaggedHeap(48)
        for k in ['L','M','R']:assert h.alloc(k,8)
        if leftfree:h.free('L')
        if rightfree:h.free('R')
        validate_tags(h);h.free('M');validate_tags(h)
        freed=next(b for b in h.blocks if b['id'] is None);assert freed['size']==16*(1+leftfree+rightfree)
    checks['boundary_neighbor_cases']=4
    for request in range(1,66):
        b=Buddy(64);before=b.snapshot();ok=b.alloc('A',request)
        if ok:assert b.live['A'][1]==1<<(request-1).bit_length();b.release('A');assert b.snapshot()==before
        else:assert b.snapshot()==before
    for order in itertools.permutations(['A','B','C','D']):
        b=Buddy(64)
        for name in order:assert b.alloc(name,9)
        for name in order:b.release(name)
        assert b.free=={(0,64)}
    checks['buddy_request_and_release_cases']=65+24
    assert corresponding({'DATE':{}},{'DATE':{'DAY':{}}})==[('DATE',)]
    assert corresponding({'X':{}},{'Y':{}})==[]
    try:build_table([('a',1,'A'),('b',3,'B'),('c',5,'C'),('d',4,'D')]);assert False
    except ValueError:pass
    records=records_model()
    for k,r in records.items():
        if r['child'] is not None:assert records[r['child']]['parent']==k
        if r['previousSame'] is not None:assert records[r['previousSame']]['name']==r['name']
    assert resolve(records,['DAY'])==['x','y'];assert resolve(records,['DAY','ARRIVAL'])==['x'];assert resolve(records,['DAY','DEPARTURE','ARRIVAL'])==[]
    assert fullpath(records,'x')!=fullpath(records,'y')
    lessons=build()
    assert len(lessons)==22 and [x['order'] for x in lessons]==list(range(123,145))
    states=0
    for lesson in lessons:
        for p in lesson['sections'][0]['passages']:
            d=p['demonstration'];assert len(p['text'])>300 and d['states'] and d['simplerHelp']['states']
            assert len({s['id'] for s in d['states']})==len(d['states'])
            for s in d['states']+d['simplerHelp']['states']:
                assert len({n['id'] for n in s['diagram']['nodes']})==len(s['diagram']['nodes']);states+=1
                for nd in s['diagram']['nodes']:
                    if nd['type']=='text':assert 15<=nd['x']<=705 and 15<=nd['y']<=430,(lesson['order'],nd)
    checks['authored_passages']=88;checks['computed_main_and_help_states']=states
    print(json.dumps(checks,indent=2));return checks

if __name__=='__main__':
    if '--test' in sys.argv:selftest()
    else:build()
