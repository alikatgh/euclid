#!/usr/bin/env python3
"""Original, deterministic linear-structure companions. No source pages embedded.
Run --test for independent model checks, --check for reproducibility, default writes JSON.
"""
from __future__ import annotations
import argparse, copy, itertools, json, math, random
from collections import deque
from fractions import Fraction
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'content/fullbook/source-plan-D.json'
OUT = ROOT/'content/fullbook/batch-D.json'

def snap(out, action, caption, **data):
    out.append(dict(action=action,caption=caption,data=copy.deepcopy(data)))

def pointer_trace(small=False):
    ids=['A','B'] if small else ['A','B','C']
    addresses=dict(zip(ids,[12,27,41])); values={i:7 for i in ids}
    links={i:(ids[k+1] if k+1<len(ids) else None) for k,i in enumerate(ids)}
    out=[]
    def frame(action,caption):
        pointers={i:(addresses[v] if v else None) for i,v in links.items()}
        assert all(p is None or p in addresses.values() for p in pointers.values())
        snap(out,action,caption,addresses=addresses,values=values,links=links,pointers=pointers)
    frame('identify','Equal values belong to different node identities. Links contain addresses, not values.')
    addresses['B']=63
    frame('relocate-and-repair','Move node B to address 63 and repair the pointer in A; the abstract successor stays B.')
    values['B']=9
    frame('change-field','Only B’s value changes. A and B remain different objects even when values agree.')
    return out

def representation_trace(small=False):
    ids=list('ABC' if small else 'ABCDE'); out=[]; target=len(ids)-1
    for mode in ['array','linked']:
        visited=[]
        for i in ([target] if mode=='array' else range(target+1)):
            visited.append(ids[i]); snap(out,'read-'+mode, f'{mode.title()} lookup: visit {ids[i]}; {len(visited)} data-node reads so far.', ids=ids,mode=mode,target=target,visited=visited,answer=ids[target] if i==target else None)
    return out

def end_trace(small=False):
    out=[]; structures={k:[] for k in ['stack','queue','deque']}; removed={k:[] for k in structures}
    values=list('AB' if small else 'ABC')
    snap(out,'empty','The rules restrict which end may be used; they do not prescribe memory layout.',structures=structures,removed=removed)
    for v in values:
        for a in structures.values(): a.append(v)
        snap(out,'insert-right',f'Insert token {v} at the right end in all three structures.',structures=structures,removed=removed)
    for k,a in structures.items(): removed[k].append(a.pop() if k=='stack' else a.pop(0))
    snap(out,'remove','The stack releases its newest token; the queue its oldest. This deque chooses left.',structures=structures,removed=removed)
    structures['deque'].insert(0,'Z')
    snap(out,'insert-left','Only the unrestricted deque is given this left-end insertion.',structures=structures,removed=removed)
    return out

def search_trace(small=False):
    adj={'A':['B','C'],'B':[],'C':[]} if small else {'A':['B','C'],'B':['D','E'],'C':['F'],'D':[],'E':[],'F':[]}
    out=[]
    for policy in ['stack','queue']:
        pending=['A']; seen={'A'}; emitted=[]
        snap(out,'start-'+policy,f'Start {policy} scheduling with A pending.',adj=adj,policy=policy,pending=pending,emitted=emitted,active=None)
        while pending:
            v=pending.pop() if policy=='stack' else pending.pop(0);emitted.append(v)
            children=adj[v] if policy=='queue' else list(reversed(adj[v]))
            for u in children:
                if u not in seen: seen.add(u);pending.append(u)
            assert len(pending)==len(set(pending));assert set(pending).isdisjoint(emitted)
            snap(out,'visit-'+v,f'Visit {v}; place its newly discovered children on the {policy}.',adj=adj,policy=policy,pending=pending,emitted=emitted,active=v)
    return out

def array_stack_trace(small=False):
    cap=2 if small else 4; cells=[None]*cap;top=0;out=[]
    ops=[('pop',None)]+[('push',chr(65+i)) for i in range(cap+1)]+[('pop',None),('push','Z')]
    snap(out,'empty','T counts occupied cells; the next free cell is at index T.',cells=cells,top=top,base=100,stride=3,error=None)
    for op,v in ops:
        error=None
        if op=='push':
            if top==cap:error='overflow'
            else:cells[top]=v;top+=1
        elif top==0:error='underflow'
        else:top-=1;v=cells[top];cells[top]=None
        assert 0<=top<=cap and all(x is None for x in cells[top:])
        snap(out,error or op,f'{error.title()}: no memory changes.' if error else f'{op.title()} {v}; the occupied-prefix boundary is now T = {top}.',cells=cells,top=top,base=100,stride=3,error=error)
    return out

def circular_queue(cap,ops):
    if cap<=0:raise ValueError('capacity must be positive')
    a=[None]*cap;head=tail=count=0;out=[]
    def frame(action,caption,error=None):
        logical=[a[(head+j)%cap] for j in range(count)]
        assert len([v for v in a if v is not None])==count
        assert tail==(head+count)%cap
        snap(out,action,caption,cells=a,head=head,tail=tail,count=count,logical=logical,error=error)
    frame('empty','Empty: head = tail = 0 and count = 0.')
    for op,value in ops:
        if op not in ['put','get']:raise ValueError('unknown queue operation')
        if op=='put' and value is None:raise ValueError('None is reserved for an unoccupied slot')
        if op=='put':
            if count==cap:frame('overflow','Full: reject insertion without overwriting an unread token.','overflow');continue
            a[tail]=value;tail=(tail+1)%cap;count+=1
            frame('enqueue',f'Write {value}; advance tail modulo {cap}; count = {count}.')
        else:
            if count==0:frame('underflow','Empty: reject removal before reading a cell.','underflow');continue
            value=a[head];a[head]=None;head=(head+1)%cap;count-=1
            frame('dequeue',f'Read {value}; advance head modulo {cap}; count = {count}.')
    return out

def queue_trace(small=False):
    c=2 if small else 4
    return circular_queue(c,[('put',chr(65+i)) for i in range(c)]+[('put','X'),('get',None),('get',None),('put','Y'),('put','Z')]+[('get',None)]* (c+1))

def shared_trace(small=False):
    c=4 if small else 7;a=[None]*c;L=0;R=c;out=[]
    def f(action,caption):
        assert 0<=L<=R<=c and all(v is None for v in a[L:R]);snap(out,action,caption,cells=a,L=L,R=R)
    f('empty','Both stacks share one unused interval.')
    for i in range(c+1):
        side='left' if i%2==0 else 'right';value=chr(65+i)
        if L==R:f('overflow','The stacks meet. Neither end may overwrite the other stack.');continue
        if side=='left':a[L]=value;L+=1
        else:R-=1;a[R]=value
        f('push-'+side,f'Push {value} on the {side}; the shared gap shrinks by one.')
    return out+relocation_trace(small)

def relocation_trace(small=False):
    source=['A','B'] if small else ['A','B','C'];src=1;dst=2;n=len(source);cells=[None]+source+[None,None];original=cells[:];out=[]
    snap(out,'plan-overlap','The destination is one cell higher and overlaps the source; copy from the high end.',cells=cells,mode='relocation',src=src,dst=dst,length=n,original=original,copied=[],active=None)
    copied=[]
    for k in range(n-1,-1,-1):
        cells[dst+k]=cells[src+k];copied.append(k)
        assert all(cells[dst+j]==original[src+j] for j in copied)
        assert all(cells[src+j]==original[src+j] for j in range(k))
        snap(out,'copy-backward',f'Copy source index {src+k} into {dst+k}; every unread source cell is preserved.',cells=cells,mode='relocation',src=src,dst=dst,length=n,original=original,copied=copied,active=k)
    for i in range(src,src+n):
        if not dst<=i<dst+n:cells[i]=None
    snap(out,'release-old-only','Release only old source cells outside the destination; moved token identities survive.',cells=cells,mode='relocation',src=src,dst=dst,length=n,original=original,copied=copied,active=None)
    assert cells[dst:dst+n]==source
    return out

def pool_trace(small=False):
    universe=list(range(1,4 if small else 6));free=universe[:];live=[];reserved=[];out=[];values={}
    def f(action,caption):
        parts=[set(free),set(live),set(reserved)]
        assert set.union(*parts)==set(universe) and sum(map(len,parts))==len(universe)
        snap(out,action,caption,universe=universe,free=free,live=live,reserved=reserved,values=values)
    f('initialize','Every slot belongs to the free list; the live list is empty.')
    for v in ['K','L']:
        p=free.pop(0);reserved.append(p);f('reserve',f'Detach address {p} from AVAIL; the allocator temporarily owns it.')
        values[p]=v;reserved.remove(p);live.insert(0,p);f('publish',f'Initialize {v} and link address {p} at the live head.')
    p=live.pop();reserved.append(p);f('unlink',f'Unlink address {p}; no live link reaches the retired slot.')
    reserved.remove(p);free.insert(0,p);values.pop(p);f('recycle',f'Return address {p} to AVAIL; its slot can be reused, not its old object lifetime.')
    p=free.pop(0);reserved.append(p);f('reserve','Reallocate the first available address.')
    values[p]='M';reserved.remove(p);live.append(p);f('publish','The reused slot holds M. A stale reference to K would be invalid.')
    while free:
        p=free.pop(0);reserved.append(p);f('reserve',f'Reserve remaining slot {p}; AVAIL advances without changing pool size.')
        values[p]='N'+str(p);reserved.remove(p);live.append(p);f('publish',f'Publish the initialized node at {p}; the remaining free count is {len(free)}.')
    before=(free[:],live[:],reserved[:],values.copy())
    f('allocation-overflow','AVAIL is null: reject allocation without stealing a live slot or losing an owner.')
    assert before==(free,live,reserved,values)
    return out

def linked_queue_trace(small=False):
    out=[];links={};head=tail=None;retired=[]
    ops=[('put','A'),('get',None),('put','B')]+([] if small else [('put','C'),('get',None),('get',None),('get',None)])
    def f(action,caption):
        order=[];p=head
        while p is not None:
            assert p not in order;order.append(p);p=links[p]
        assert (head is None)==(tail is None)
        assert (tail is None or links[tail] is None)
        assert not order or order[-1]==tail
        snap(out,action,caption,links=links,head=head,tail=tail,order=order,retired=retired)
    f('empty','Without a sentinel, both endpoints are null in an empty queue.')
    for op,v in ops:
        if op=='put':
            links[v]=None
            if tail is None:head=v
            else:links[tail]=v
            tail=v;f('enqueue',f'Append {v}; if the queue was empty, initialize both endpoints.')
        elif head is None:f('underflow','Reject removal from the empty queue; neither endpoint changes.')
        else:
            p=head;head=links.pop(p);retired.append(p)
            if head is None:tail=None
            f('dequeue',f'Remove {p}; reset the tail too if this was the last node.')
    return out

def topological(adj):
    if any(len(us)!=len(set(us)) or any(u not in adj for u in us) for us in adj.values()):raise ValueError('simple graph with every target declared required')
    indeg={v:0 for v in adj}
    for us in adj.values():
        for u in us:indeg[u]+=1
    remaining=set(adj);ready=sorted(v for v in adj if indeg[v]==0);output=[];out=[]
    def f(action,caption,active=None):
        assert all(indeg[v]==sum(v in adj[u] for u in remaining) for v in remaining)
        snap(out,action,caption,adj=adj,indeg=indeg,remaining=sorted(remaining),ready=ready,output=output,active=active)
    f('count','Count each incoming edge from the unprocessed graph.')
    while ready:
        v=ready.pop(0);remaining.remove(v);output.append(v)
        for u in adj[v]:
            indeg[u]-=1
            if indeg[u]==0:ready.append(u)
        f('remove-'+v,f'Emit {v}; remove its outgoing edges and enqueue newly zero counts.',v)
    if remaining:
        # Following an actual predecessor in the residual graph must repeat.
        v=min(remaining);walk=[]
        while v not in walk:
            walk.append(v);v=min(u for u in remaining if v in adj[u])
        cycle=list(reversed(walk[walk.index(v):]+[v]))
        assert all(b in adj[a] for a,b in zip(cycle,cycle[1:]))
        f('cycle','No vertex is ready, but vertices remain: a residual directed cycle is a witness.')
        out[-1]['data']['cycle']=cycle
    return out

def topo_trace(small=False):
    adj={'A':['B'],'B':['C'],'C':[]} if small else {'A':['C'],'B':['C','D'],'C':['E'],'D':['E'],'E':[]}
    out=topological(adj);cycle=topological({'P':['Q'],'Q':['P']} if small else {'P':['Q'],'Q':['R'],'R':['P']})
    return out+cycle

def ring_trace(small=False):
    ids=['A'] if small else ['A','B','C'];links={'H':ids[0],**{v:(ids[i+1] if i+1<len(ids) else 'H') for i,v in enumerate(ids)}};out=[]
    def f(action,caption,active='H'):
        p=links['H'];seen=[]
        while p!='H':assert p not in seen;seen.append(p);p=links[p]
        assert set(seen)==set(links)-{'H'}
        snap(out,action,caption,links=links,order=seen,active=active)
    f('sentinel','H is a sentinel, not a data token. Traversal ends by identity at H.')
    p=links['H']
    while p!='H':f('visit',f'Visit {p}; follow its successor even if it returns to H.',p);p=links[p]
    f('stop','The cursor returns to H; do not read H as a data value.')
    x='X';links[x]=links['H'];links['H']=x;f('splice','Splice X after H: initialize X’s successor, then publish H’s link.',x)
    tail=next(k for k,v in links.items() if v=='H');links[tail]='Y';links['Y']='Z';links['Z']='H'
    f('concatenate','Transfer the disjoint Y,Z chain before H and repair the closing link.','Y')
    return out

def validate_poly(a):
    if any(not isinstance(e,int) or e<0 or not isinstance(c,int) for e,c in a.items()):raise ValueError('nonnegative integer exponents and integer coefficients required')

def poly_merge(a,b):
    validate_poly(a);validate_poly(b)
    a=sorted(((e,c) for e,c in a.items() if c),reverse=True);b=sorted(((e,c) for e,c in b.items() if c),reverse=True)
    i=j=0;result={};out=[]
    snap(out,'start','Two decreasing exponent streams; the header lies beyond every data exponent.',left=a,right=b,i=i,j=j,result=result)
    while i<len(a) or j<len(b):
        if j==len(b) or i<len(a) and a[i][0]>b[j][0]:e,c=a[i];i+=1;action='copy-left'
        elif i==len(a) or b[j][0]>a[i][0]:e,c=b[j];j+=1;action='copy-right'
        else:e=a[i][0];c=a[i][1]+b[j][1];i+=1;j+=1;action='cancel' if c==0 else 'combine'
        if c:result[e]=c
        assert all(v!=0 for v in result.values())
        snap(out,action,f'Exponent {e}: coefficient {c}; '+('omit the canceled term.' if c==0 else 'append one canonical term.'),left=a,right=b,i=i,j=j,result=result,exponent=e)
    return out

def poly_multiply(a,b):
    validate_poly(a);validate_poly(b)
    result={};out=[];processed=[]
    snap(out,'start-product','Each grid cell represents one pair of input terms.',left=sorted(a.items(),reverse=True),right=sorted(b.items(),reverse=True),result=result,pair=None,processed=processed)
    for e,c in sorted(a.items(),reverse=True):
        for f,d in sorted(b.items(),reverse=True):
            g=e+f;result[g]=result.get(g,0)+c*d;processed.append([e,f])
            if result[g]==0:del result[g]
            snap(out,'accumulate',f'({c}x^{e})({d}x^{f}) contributes {c*d}x^{g}; combine like exponents.',left=sorted(a.items(),reverse=True),right=sorted(b.items(),reverse=True),result=result,pair=[e,f],contribution=c*d,processed=processed)
    return out

def polynomial_trace(small=False):
    a={1:1,0:1} if small else {3:2,1:-1,0:3};b={1:1,0:-1} if small else {3:-2,2:1,0:-3}
    return poly_merge(a,b)+poly_multiply(a,b)

def doubly_trace(small=False):
    order=['H','A'] if small else ['H','A','B','C'];out=[]
    def make(order):return {p:{'prev':order[(i-1)%len(order)],'next':order[(i+1)%len(order)]} for i,p in enumerate(order)}
    links=make(order)
    def f(action,caption,phase='committed',staged=None):
        if phase=='committed':
            assert all(links[links[x]['next']]['prev']==x and links[links[x]['prev']]['next']==x for x in links)
        snap(out,action,caption,links=links,order=order,phase=phase,staged=staged)
    f('initial','At an operation boundary, next and prev are reciprocal, including the sentinel H.')
    left='A';right=links[left]['next'];new={'prev':left,'next':right}
    f('prepare','Prepare X privately with both neighbors. The published list is unchanged.',staged={'id':'X',**new})
    links['X']=new;links[left]['next']='X'
    f('first-publish','Inside a protected update: A.next = X, but the right neighbor still points back to A. Do not traverse concurrently.','updating')
    links[right]['prev']='X';order.insert(order.index(left)+1,'X');f('commit-insert','Repair the right neighbor’s prev. Both reciprocal equations hold again.')
    left=links['X']['prev'];right=links['X']['next'];links[left]['next']=right
    f('unlink-forward','Inside a protected deletion: bypass X forward; the backward route is not yet repaired.','updating')
    links[right]['prev']=left;del links['X'];order.remove('X');f('commit-delete','Repair backward, then retire X. Deallocation happens only after both bypass links are valid.')
    return out

def events_trace(small=False):
    arrivals=[(1,'A',2),(2,'B',1)] if small else [(1,'A',3),(2,'B',2),(4,'C',1)]
    events=[];seq=0
    for t,v,d in arrivals:events.append((t,1,seq,'arrive',v,d));seq+=1
    events.sort();out=[];waiting=[];busy=None;now=0;area=0;done=[]
    def f(action,caption,active=None):
        snap(out,action,caption,events=events,waiting=waiting,busy=busy,now=now,area=area,done=done,active=active)
    f('initialize','Order by (time, priority, serial). Completion has priority 0; arrival priority 1.')
    while events:
        t,priority,serial,kind,v,d=events.pop(0);assert t>=now
        area+=(t-now)*len(waiting);now=t
        if kind=='arrive':waiting.append((v,d))
        else:assert busy==v;busy=None;done.append(v)
        if busy is None and waiting:
            busy,duration=waiting.pop(0);events.append((now+duration,0,seq,'finish',busy,0));seq+=1;events.sort()
        f(kind,f'At time {now}, {kind} {v}. Process one event and schedule only future completion.',v)
    return out

def membership_trace(small=False):
    entities=['A','B'] if small else ['A','B','C'];waiting=entities[:];calendar=[{'id':'timeout-'+v,'entity':v,'time':5+i} for i,v in enumerate(entities)];out=[];canceled=[];fired=[]
    def f(action,caption):
        assert len(waiting)==len(set(waiting));assert not set(canceled)&set(fired)
        snap(out,action,caption,entities=entities,waiting=waiting,calendar=calendar,canceled=canceled,fired=fired)
    f('two-memberships','Each entity has its own waiting membership and a separately identified timeout event.')
    v=waiting.pop(0);f('leave-waiting',f'{v} begins service and leaves the waiting rail; its timeout still exists until canceled.')
    e=next(e for e in calendar if e['entity']==v);calendar.remove(e);canceled.append(e['id']);f('cancel-exact-event',f'Cancel {e["id"]} by event identity. Other entities and timeouts remain.')
    while calendar:
        e=calendar.pop(0);fired.append(e['id']);waiting.remove(e['entity']);f('timeout',f'{e["id"]} fires; remove {e["entity"]} from the waiting rail.')
    return out

def offset(i,j,rows,cols,lo=(0,0),column=False):
    r=i-lo[0];c=j-lo[1]
    if not (0<=r<rows and 0<=c<cols):raise IndexError('coordinate outside rectangular domain')
    return c*rows+r if column else r*cols+c

def triangular_offset(i,j,n):
    if not (0<=j<=i<n):raise IndexError('coordinate outside lower triangle')
    return i*(i+1)//2+j

def array_trace(small=False):
    rows,cols=(2,2) if small else (2,3);lo=(2,-1);out=[];selected=(3,-1) if small else (3,0);base,stride=(20,2) if small else (100,4)
    r=selected[0]-lo[0];c=selected[1]-lo[1];k=r*cols+c
    captions=[('select-cell',f'Choose cell {selected}. Row numbering begins at {lo[0]}; column numbering begins at {lo[1]}.','grid','select'),('subtract-bounds',f'Count from those beginnings: r = {selected[0]} − ({lo[0]}) = {r}; c = {selected[1]} − ({lo[1]}) = {c}.','grid','subtract'),('count-whole-rows',f'{r} complete earlier row × {cols} cells per row = {r*cols} cells before the selected row.','grid','rows'),('count-within-row',f'Within the selected row, pass {c} more cells. Total cells before the target: {r*cols} + {c} = {k}.','grid','within'),('map-row',f'Flatten row by row: the selected cell keeps its identity and arrives at offset {k}.','row','flatten'),('locate-address',f'Base address {base}; each cell occupies {stride} address units. Address = {base} + {stride} × {k} = {base+stride*k}.','row','address'),('invert-row',f'Dividing offset {k} by row length {cols} gives quotient {r}, remainder {c}. Add lower bounds to recover {selected}.','row','inverse'),('map-column',f'Column-major instead passes {c} complete columns of {rows} cells, then {r} cells: offset {c*rows+r}.','column','column')]
    for action,caption,mode,stage in captions:
        cells=[dict(id=f'c{i}-{j}',i=i,j=j,offset=offset(i,j,rows,cols,lo,mode=='column')) for i in range(lo[0],lo[0]+rows) for j in range(lo[1],lo[1]+cols)]
        snap(out,action,caption,cells=cells,rows=rows,cols=cols,lo=lo,mode=mode,stage=stage,selected=selected,r=r,c=c,rowContribution=r*cols,withinContribution=c,rowOffset=k,base=base,stride=stride,address=base+stride*k)
    n=3 if small else 4;cells=[dict(id=f't{i}-{j}',i=i,j=j,offset=triangular_offset(i,j,n)) for i in range(n) for j in range(i+1)]
    snap(out,'select-triangle','A triangle has one cell in its first row, then two, then three; its rows do not all have equal length.',cells=cells,rows=n,cols=n,lo=(0,0),mode='triangle',stage='triangle-select')
    snap(out,'pack-triangle','Row i begins after 1 + 2 + … + i cells; add column j to locate its cell.',cells=cells,rows=n,cols=n,lo=(0,0),mode='triangle',stage='triangle-offset')
    return out

def sparse_snapshot(entries,rows,cols):
    entries={p:Fraction(v) for p,v in entries.items() if v}
    rs=[[p for p in sorted(entries) if p[0]==i] for i in range(rows)]
    cs=[[p for p in sorted(entries,key=lambda p:(p[1],p[0])) if p[1]==j] for j in range(cols)]
    assert {p for r in rs for p in r}=={p for c in cs for p in c}==set(entries)
    return dict(entries=[{'id':f'cell-{i}-{j}','i':i,'j':j,'value':str(v)} for (i,j),v in sorted(entries.items())],rowLinks=[[f'cell-{i}-{j}' for i,j in r] for r in rs],columnLinks=[[f'cell-{i}-{j}' for i,j in c] for c in cs],rows=rows,cols=cols)

def sparse_trace(small=False):
    rows=cols=2 if small else 3;entries={(0,0):2,(1,1):4};out=[]
    snap(out,'initial','A nonzero cell is one object, reachable by two sorted routes.',**sparse_snapshot(entries,rows,cols))
    entries[0,1]=3;snap(out,'insert','Insert cell (0,1) into both its row and column routes.',**sparse_snapshot(entries,rows,cols),active=[0,1])
    entries[0,1]+=-3
    if entries[0,1]==0:del entries[0,1]
    snap(out,'cancel','Add −3 to the same coordinate; exact zero removes the one cell from both routes.',**sparse_snapshot(entries,rows,cols),active=[0,1])
    if not small:
        entries[2,0]=-1;snap(out,'insert-second','Insert (2,0); its column route now connects rows 0 and 2.',**sparse_snapshot(entries,rows,cols),active=[2,0])
    return out

def pivot_trace(matrix,p=0,q=0):
    if not matrix or not matrix[0] or any(len(row)!=len(matrix[0]) for row in matrix):raise ValueError('nonempty rectangular matrix required')
    if not (0<=p<len(matrix) and 0<=q<len(matrix[0])):raise IndexError('pivot coordinate outside matrix')
    A=[[Fraction(v) for v in row] for row in matrix];m=len(A);n=len(A[0]);a=A[p][q]
    if not a:raise ValueError('pivot must be nonzero')
    B=copy.deepcopy(A);out=[];other_i=next((i for i in range(m) if i!=p),None);other_j=next((j for j in range(n) if j!=q),None)
    def f(action,caption,active=None,stage='boundary',target=None,pending=None):
        entries={(i,j):B[i][j] for i in range(m) for j in range(n) if B[i][j]}
        target=target or ([active[0],other_j] if action=='scale-column' and active is not None and other_j is not None else [other_i,other_j] if other_i is not None and other_j is not None else None)
        operands=operand_cells=None
        if target:
            i,j=target;operands={name:str(v) for name,v in dict(a=a,b=A[p][j],c=A[i][q],d=A[i][j]).items()};operand_cells=dict(a=[p,q],b=[p,j],c=[i,q],d=[i,j])
        snap(out,action,caption,**sparse_snapshot(entries,m,n),pivot=[p,q],active=active,original=[[str(v) for v in r] for r in A],dense=[[str(v) for v in r] for r in B],stage=stage,target=target,operands=operands,operandCells=operand_cells,pendingResult=str(pending) if pending is not None else None)
    f('original',f'The left matrix keeps the old values. Choose pivot a = {a}; zero labels without circles mean no stored sparse cell.')
    B[p][q]=1/a
    for j in range(n):
        if j!=q:B[p][j]=A[p][j]/a
    f('normalize-row',f'In the changing matrix, the pivot becomes 1/{a} = {1/a}, and other pivot-row values divide by {a}. The old matrix stays unchanged.',[p,q])
    for i in range(m):
        if i==p:continue
        for j in range(n):
            if j==q:continue
            old=B[i][j];new=A[i][j]-A[i][q]*A[p][j]/a
            if new!=old:
                f('select-old-operands',f'For target ({i},{j}), read a={a} at the old pivot, b={A[p][j]} in its old row, c={A[i][q]} in its old column, and d={A[i][j]} at the old target.',[i,j],'select',[i,j])
                f('calculate-correction',f'Keep the target unchanged while calculating: {A[i][j]} − ({A[p][j]} × {A[i][q]})/{a} = {new}.',[i,j],'calculate',[i,j],new)
                B[i][j]=new;change='fill-in' if old==0 else 'cancellation' if new==0 else 'update'
                f(change,f'Now replace the target with {new}. '+('Zero removes its stored cell from both routes.' if new==0 else 'A previously absent position gains a stored cell.' if old==0 else 'Both routes still reach this one updated cell.'),[i,j],'commit',[i,j],new)
        B[i][q]=-A[i][q]/a;f('scale-column',f'After the other cells in row {i}, its pivot-column value becomes −({A[i][q]})/{a} = {B[i][q]}.',[i,q])
    return out

TRACES={88:pointer_trace,89:representation_trace,90:end_trace,91:search_trace,92:array_stack_trace,93:queue_trace,94:shared_trace,95:pool_trace,96:linked_queue_trace,97:topo_trace,98:ring_trace,99:polynomial_trace,100:doubly_trace,101:events_trace,102:membership_trace,103:array_trace,104:sparse_trace,105:lambda small=False:pivot_trace([[2,2],[1,0]] if small else [[2,4,0],[1,2,3],[3,0,1]])}

# Scene geometry is derived from each snapshot, never a stock register diagram.
def txt(id,x,y,text,role='input',size=16,result=False):return dict(id=id,type='text',x=x,y=y,text=str(text),fontSize=size,anchor='middle',role=role,result=result)
def box(id,x,y,w=72,h=44,role='input',opacity=1):return dict(id=id,type='rect',x=x,y=y,width=w,height=h,role=role,opacity=opacity)
def line(id,x,y,x2,y2,role='input'):return dict(id=id,type='line',x=x,y=y,x2=x2,y2=y2,role=role,strokeWidth=2)
def arrow(id,x,y,x2,y2,role='input'):
    angle=math.atan2(y2-y,x2-x);a=8;b=4
    return [line(id,x,y,x2,y2,role),dict(id=id+'-tip',type='path',d=f'M {x2-a*math.cos(angle)+b*math.sin(angle):.2f} {y2-a*math.sin(angle)-b*math.cos(angle):.2f} L {x2:.2f} {y2:.2f} L {x2-a*math.cos(angle)-b*math.sin(angle):.2f} {y2-a*math.sin(angle)+b*math.cos(angle):.2f}',fill='none',role=role)]
def cards(nodes,ids,y,prefix='card',start=80,step=105,labels=None):
    pos={v:(start+k*step,y) for k,v in enumerate(ids)}
    for v,(x,y) in pos.items():nodes.extend([box(prefix+'-'+str(v),x,y,78),txt(prefix+'-'+str(v)+'-label',x+39,y+28,(labels or {}).get(v,v))])
    return pos

def link_chain(nodes,ids,pos,prefix='next',yshift=22,ring=False):
    for k,v in enumerate(ids):
        u=ids[k+1] if k+1<len(ids) else ids[0] if ring else None
        x,y=pos[v]
        if u is not None:
            xx,yy=pos[u]
            if xx>x:nodes+=arrow(prefix+'-'+str(v),x+78,y+yshift,xx,yy+yshift)
            else:
                nodes.append(dict(id=prefix+'-'+str(v),type='path',d=f'M {x+39} {y+44} L {x+39} {y+80} L {xx+39} {y+80} L {xx+39} {yy+44}',fill='none',role='active'))
                nodes+=arrow(prefix+'-'+str(v)+'-last',xx+39,y+80,xx+39,yy+44)
        else:nodes.append(txt(prefix+'-'+str(v)+'-null',x+90,y+28,'∅',size=18))

def array_scene(s):
    d=s['data'];nodes=[];stage=d['stage'];triangle=d['mode']=='triangle'
    for cell in d['cells']:
        i,j=cell['i'],cell['j'];rr=i-d['lo'][0];cc=j-d['lo'][1];selected=not triangle and [i,j]==list(d['selected'])
        x=65+cc*90;y=95+rr*70;w=76
        if d['mode'] in ['row','column']:x=45+cell['offset']*105;y=150;w=85
        if triangle:x=150+j*90;y=60+i*75;w=80
        counted=not triangle and ((stage=='rows' and rr<d['r']) or (stage=='within' and (rr<d['r'] or rr==d['r'] and cc<d['c'])))
        role='active' if selected else 'result' if counted else 'muted'
        n=box(cell['id'],x,y,w,48,role);n['strokeWidth']=3 if selected else 1.5;nodes.extend([n,txt(cell['id']+'-label',x+w/2,y+23,f'({i},{j})',role,14)])
        if d['mode'] in ['row','column'] or stage=='triangle-offset':nodes.append(txt(cell['id']+'-offset',x+w/2,y+42,'offset '+str(cell['offset']),'muted',14,result=stage in ['flatten','column','triangle-offset']))
        if selected:nodes+=arrow('selected-cell',x+w/2,y-25,x+w/2,y-3,'active')
    if triangle:
        formula=r'\tau(i,j)=\frac{i(i+1)}2+j';invariant='Unequal row lengths produce triangular-number offsets'
    else:
        i,j=d['selected'];lr,lc=d['lo'];r,c=d['r'],d['c'];C=d['cols'];k=d['rowOffset']
        if d['mode']=='grid':
            nodes.append(txt('row-width',195,70,f'C = {C} cells in each row','input',16))
            nodes.append(txt('selection-name',520,100,f'selected cell ({i},{j})','active',17))
            nodes.append(txt('lower-row',520,137,f'first row label: ℓr = {lr}','input',15))
            nodes.append(txt('lower-column',520,169,f'first column label: ℓc = {lc}','input',15))
            nodes.append(txt('memory-inputs',520,208,f'base {d["base"]}; {d["stride"]} units per cell','input',15))
        if stage=='select':
            nodes.append(txt('selection-explain',355,295,'Coordinates are labels; first count from the lower bounds.','input',17));formula=rf'(i,j)=({i},{j}),\quad(\ell_r,\ell_c)=({lr},{lc})'
        elif stage=='subtract':
            nodes.append(txt('row-subtraction',355,280,f'r = i − ℓr = {i} − ({lr}) = {r}','result',20,True));nodes.append(txt('column-subtraction',355,320,f'c = j − ℓc = {j} − ({lc}) = {c}','result',20,True));nodes.append(txt('digit-meaning',355,360,'r counts earlier rows; c counts earlier cells within this row.','input',16));formula=rf'r={i}-({lr})={r},\quad c={j}-({lc})={c}'
        elif stage=='rows':
            nodes.append(txt('whole-row-count',355,285,f'{r} complete earlier row × {C} cells per row = {r*C}','result',19,True));nodes.append(txt('row-block-meaning',355,330,'The green cells form whole rows before the selected row.','input',16));formula=rf'rC={r}\cdot {C}={r*C}'
        elif stage=='within':
            nodes.append(txt('within-count',355,285,f'whole-row cells {r*C} + within-row cells {c} = {k}','result',19,True));nodes.append(txt('count-meaning',355,330,'Count every earlier cell once; do not count the selected cell.','input',16));formula=rf'\rho=rC+c={r}\cdot {C}+{c}={k}'
        elif stage=='flatten':
            nodes.append(txt('flatten-count',355,270,f'({i},{j}) → ({r},{c}) → {r} × {C} + {c} = offset {k}','result',19,True));nodes.append(txt('flatten-meaning',355,315,'The same selected cell follows all counted earlier cells.','input',16));formula=rf'\rho({i},{j})=({i}-({lr}))\cdot {C}+({j}-({lc}))={k}'
        elif stage=='address':
            nodes.append(txt('address-inputs',355,265,f'base b = {d["base"]}; cell size s = {d["stride"]}; offset = {k}','input',17));nodes.append(txt('physical-address',355,315,f'address = b + s × offset = {d["base"]} + {d["stride"]} × {k} = {d["address"]}','result',19,True));formula=rf'\operatorname{{addr}}({i},{j})={d["base"]}+{d["stride"]}\cdot {k}={d["address"]}'
        elif stage=='inverse':
            nodes.append(txt('inverse-divmod',355,265,f'divmod({k}, {C}) = ({r}, {c})','result',20,True));nodes.append(txt('restore-bounds',355,315,f'add lower bounds: ({r}+{lr}, {c}+({lc})) = ({i},{j})','result',18,True));formula=rf'{k}={r}\cdot {C}+{c},\quad 0\le {c}<{C}'
        else:
            column=c*d['rows']+r;nodes.append(txt('column-count',355,270,f'{c} earlier columns × {d["rows"]} cells + {r} = offset {column}','result',19,True));nodes.append(txt('column-meaning',355,315,'Column-major uses the height as its column stride.','input',16));formula=rf'\kappa=cR+r={c}\cdot {d["rows"]}+{r}={column}'
        invariant='Coordinates name the cell; offsets count preceding cells; addresses count memory units'
    nodes.append(txt('scene-status',355,425,s['action'].replace('-',' '),'muted',14))
    return dict(title='From a named cell to a counted memory position',description=s['caption'],viewBox=[0,0,720,440],nodes=nodes,invariant=invariant),formula

def pivot_scene(s):
    d=s['data'];nodes=[];old=d['original'];current=d['dense'];op=d['operands'];pos=d['operandCells'];target=d['target'];stage=d['stage'];p,q=d['pivot']
    nodes.extend([txt('old-title',205,40,'OLD values: keep these','input',18),txt('new-title',540,40,'Changing sparse matrix','input',18)])
    for which,M,x0 in [('old',old,130),('current',current,470)]:
        for j in range(d['cols']):nodes.append(txt(which+'-column-'+str(j),x0+j*70,75,'col '+str(j),'muted',14))
        for i,row in enumerate(M):
            nodes.append(txt(which+'-row-'+str(i),x0-60,111+i*60,'row '+str(i),'muted',14))
            for j,value in enumerate(row):
                x=x0+j*70;y=105+i*60;names=[name for name,ij in (pos or {}).items() if ij==[i,j]] if which=='old' else []
                selected=names or which=='current' and (d['active'] or target)==[i,j];role='active' if selected else 'muted';zero=Fraction(value)==0
                if not zero:nodes.append(dict(id=(f'old-cell-{i}-{j}' if which=='old' else f'cell-{i}-{j}'),type='circle',x=x,y=y,r=24,role=role,strokeWidth=3 if names else 1.5))
                label=(names[0]+'='+value) if names else value
                nodes.append(txt(f'{which}-value-{i}-{j}',x,y+5,label,role,14,result=which=='current' and ((stage=='commit' and target==[i,j]) or (s['action']=='normalize-row' and i==p) or (s['action']=='scale-column' and d['active']==[i,j]))))
                if names and zero:nodes.append(box('old-absent-target',x-25,y-23,50,46,'active'))
        if which=='old' and pos:
            a,b,c,z=[pos[k] for k in ['a','b','c','d']]
            for name,fromij,toij in [('pivot-row',a,b),('pivot-column',a,c),('target-row',c,z),('target-column',b,z)]:
                x=x0+fromij[1]*70;y=105+fromij[0]*60;xx=x0+toij[1]*70;yy=105+toij[0]*60
                if x!=xx:nodes+=arrow('old-'+name,x+24,y,xx-24,yy,'active')
                elif y!=yy:
                    if abs(yy-y)>65:
                        nodes.append(dict(id='old-'+name,type='path',d=f'M {x-24} {y} L {x-34} {y} L {x-34} {yy} L {xx-24} {yy}',fill='none',role='active',arrow=True))
                    else:nodes+=arrow('old-'+name,x,y+24,xx,yy-24,'active')
    nodes+=arrow('calculation-direction',325,162,387,162,'active')
    nodes.append(txt('zero-convention',355,260,'0 without a circle = an absent sparse cell','muted',15))
    if op:
        a,b,c,z=[op[k] for k in ['a','b','c','d']]
        nodes.append(txt('operand-row',355,289,f'a = {a} (old pivot); b = {b} (old pivot row)','input',16))
        nodes.append(txt('operand-column',355,318,f'c = {c} (old pivot column); d = {z} (old target)','input',16))
        substitution=f'new d = {z} − ({b} × {c}) / {a}'
        if stage in ['calculate','commit']:substitution+=' = '+d['pendingResult']
        if s['action']=='normalize-row':substitution=f'new pivot = 1 / {a} = {d["dense"][p][q]}'
        if s['action']=='scale-column':substitution=f'new column value = −({c}) / {a} = {d["dense"][d["active"][0]][q]}'
        reveal=stage in ['calculate','commit'] or s['action'] in ['normalize-row','scale-column']
        nodes.append(txt('actual-substitution',355,357,substitution,'result' if reveal else 'active',20,result=reveal))
        if stage=='select':nodes.append(txt('commit-status',355,390,'Read the four old values; the target has not changed.','input',15))
        elif stage=='calculate':nodes.append(txt('commit-status',355,390,'The calculation is ready; the target still holds its old value.','input',15))
        elif stage=='commit':nodes.append(txt('commit-status',355,390,'Replace the target now; remove its circle if the answer is zero.','result',15,True))
        else:nodes.append(txt('commit-status',355,390,'Old operands remain available as the right-hand matrix changes.','input',15))
        formula=rf'd-\frac{{bc}}{{a}}={z}-\frac{{({b})({c})}}{{{a}}}'+('='+d['pendingResult'] if stage in ['calculate','commit'] else '')
        if s['action']=='normalize-row':formula=rf'a\gets\frac1{{{a}}}={d["dense"][p][q]},\quad b\gets b/a'
        if s['action']=='scale-column':formula=rf'c\gets-\frac{{{c}}}{{{a}}}={d["dense"][d["active"][0]][q]}'
    else:formula=r'a\ne0,\quad a\gets1/a'
    nodes.append(txt('scene-status',355,425,s['action'].replace('-',' '),'muted',14))
    return dict(title='Read old crossing values, calculate, then replace one cell',description=s['caption'],viewBox=[0,0,720,440],nodes=nodes,invariant='The old matrix supplies every right-hand-side operand; missing cells have value zero'),formula

def scene(order,s):
    d=s['data'];nodes=[];invariant='';formula=''
    if order==88:
        pos={}
        for k,address in d['addresses'].items():
            x={12:55,27:220,41:385,63:550}[address];pos[k]=(x,140)
            nodes.extend([box('card-'+k,x,140,78),txt('card-'+k+'-label',x+39,168,f'{k}: {d["values"][k]}')])
        for k,(x,y) in pos.items():
            nodes.append(txt('address-'+k,x+39,y-22,'@'+str(d['addresses'][k]),'muted'))
            nodes.append(txt('field-'+k,x+39,y+72,'next '+str(d['pointers'][k] if d['pointers'][k] is not None else '∅'),'active',14))
        for index,(v,u) in enumerate(d['links'].items()):
            x,y=pos[v]
            if u is None:
                nodes.append(txt('next-'+v+'-null',x+95,y+27,'∅',size=18));continue
            xx,yy=pos[u]
            obstacle=any(min(x,xx)<ox<max(x,xx) for name,(ox,oy) in pos.items() if name not in [v,u])
            if xx>x and not obstacle:nodes+=arrow('next-'+v,x+78,y+22,xx,yy+22)
            else:
                rail=65+index*20
                nodes.append(dict(id='next-'+v,type='path',d=f'M {x+78} {y+22} L {x+90} {y+22} L {x+90} {rail} L {xx-12} {rail} L {xx-12} {yy+22}',fill='none',role='active'))
                nodes+=arrow('next-'+v+'-end',xx-12,yy+22,xx,yy+22,'active')
        invariant='Node identity ≠ stored value ≠ address'
        formula=r'\operatorname{next}(A)=B,\quad \operatorname{ptr}(A)= '+str(d['pointers']['A'])
    elif order==89:
        ids=d['ids'];pos=cards(nodes,ids,150,step=115,start=55)
        if d['mode']=='linked':link_chain(nodes,ids,pos)
        for v in d['visited']:
            x,y=pos[v];nodes.append(box('visited-'+v,x,y,78,44,'active',.25))
        if d['mode']=='array':
            x,y=pos[ids[d['target']]];nodes+=arrow('direct',80,70,x+39,y,'active');nodes.append(txt('calculation',350,65,f'base + {d["target"]} × stride','active'))
        nodes.append(txt('reads',350,330,f'{len(d["visited"])} node reads', 'result',20,True));invariant='Both layouts answer the same logical query'
        formula=r'k='+str(d['target'])+r',\quad R='+str(len(d['visited']))
    elif order==90:
        for row,(k,vs) in enumerate(d['structures'].items()):
            y=80+row*110;nodes.append(txt('name-'+k,80,y+27,k));pos=cards(nodes,vs,y,k,start=155,step=90)
            nodes.append(txt('released-'+k,590,y+27,'out: '+','.join(d['removed'][k]),'result',16,True))
            if vs:nodes+=arrow('exit-'+k,155+(len(vs)-1 if k=='stack' else 0)*90+39,y-25,155+(len(vs)-1 if k=='stack' else 0)*90+39,y,'active')
        invariant='Left and right end names stay fixed';formula=r'\text{stack: LIFO}\qquad\text{queue: FIFO}'
    elif order==91:
        adj=d['adj'];coords={'A':(330,60),'B':(190,150),'C':(470,150),'D':(90,235),'E':(275,235),'F':(530,235)}
        for v,us in adj.items():
            x,y=coords[v]
            for u in us:
                xx,yy=coords[u];nodes+=arrow('edge-'+v+u,x,y+20,xx,yy-20,'muted')
        for v in adj:
            x,y=coords[v];nodes.extend([dict(id='vertex-'+v,type='circle',x=x,y=y,r=24,role='result' if v in d['emitted'] else 'active' if v==d['active'] else 'input'),txt('vlabel-'+v,x,y+6,v)])
        # Task cards move through the actual pending/emitted sequences. The graph stays fixed.
        nodes.extend([box('frontier-container',150,290,460,38,'muted'),box('visited-container',150,355,460,38,'muted'),txt('frontier-label',75,315,d['policy']+' pending','active',14),txt('visited-label',75,380,'visited','muted',15)])
        nodes.append(txt('frontier-order',380,347,'bottom → top' if d['policy']=='stack' else 'front → rear','muted',14))
        for v in adj:
            if v in d['pending']:
                x=165+d['pending'].index(v)*70;y=293;opacity=1;role='active'
            elif v in d['emitted']:
                x=165+d['emitted'].index(v)*70;y=358;opacity=1;role='input'
            else:
                gx,gy=coords[v];x=gx-22;y=gy-16;opacity=0;role='muted'
            nodes.extend([box('task-token-'+v,x,y,44,30,role,opacity),{**txt('task-token-label-'+v,x+22,y+21,v,role,15),'opacity':opacity}])
        if d['pending']:
            next_index=len(d['pending'])-1 if d['policy']=='stack' else 0;xx=187+next_index*70
            nodes+=arrow('next-task-gate',xx,270,xx,289,'active')
            nodes.append(txt('next-task-label',xx+35,280,'next','active',14))
        active=d['active'];cx,cy=coords[active] if active else coords['A']
        nodes.append(dict(id='visit-cursor',type='circle',x=cx,y=cy,r=33,role='active',strokeWidth=3,opacity=1 if active else 0))
        invariant='Work-card identities move from discovered frontier to visited exactly once';formula=r'|\mathrm{visited}|='+str(len(d['emitted']))
    elif order==94 and d.get('mode')=='relocation':
        a=d['cells'];start=65;step=85
        for i,v in enumerate(a):
            x=start+i*step;nodes.extend([box('move-slot-'+str(i),x,165,78,54,'active' if d['dst']<=i<d['dst']+d['length'] else 'muted'),txt('move-slot-'+str(i)+'-value',x+39,197,v or '·'),txt('move-index-'+str(i),x+39,248,str(i),'muted',14)])
        nodes.append(txt('source-span',350,65,f'old source [{d["src"]},{d["src"]+d["length"]})','muted'))
        nodes.append(txt('target-span',350,95,f'new target [{d["dst"]},{d["dst"]+d["length"]})','active'))
        if d['active'] is not None:
            k=d['active'];x=start+(d['src']+k)*step+39;xx=start+(d['dst']+k)*step+39
            nodes.append(dict(id='copy-route',type='path',d=f'M {x} 162 L {x} 125 L {xx} 125 L {xx} 162',fill='none',role='active',arrow=True))
        nodes.append(txt('copy-order',350,335,'copied offsets: '+', '.join(map(str,d['copied'])),'result',18,True))
        invariant='Copied destinations are correct; all unread sources remain intact';formula=r'k=n-1,n-2,\ldots,0\quad(\mathrm{dst}>\mathrm{src})'
    elif order in (92,94):
        a=d['cells'];step=min(86,580/len(a));start=55
        for i,v in enumerate(a):
            x=start+i*step;role=('active' if order==92 and i<d['top'] else 'muted') if order==92 else ('active' if i<d['L'] else 'result' if i>=d['R'] else 'muted')
            nodes.extend([box('slot-'+str(i),x,160,step-5,58,role),txt('content-'+str(i),x+(step-5)/2,195,v or '·'),txt('index-'+str(i),x+(step-5)/2,246,str(i),'muted',14)])
            if order==92:nodes.append(txt('address-'+str(i),x+(step-5)/2,130,'@'+str(d['base']+d['stride']*i),'muted',14))
        if order==92:
            nodes+=arrow('top-pointer',start+d['top']*step,290,start+d['top']*step,222,'active');nodes.append(txt('top-count',350,335,'T = '+str(d['top'])+(' · '+d['error'] if d['error'] else ''),'result',20,True));invariant='Occupied indices are exactly 0 ≤ i < T';formula=r'\operatorname{addr}(i)=100+3i,\quad T='+str(d['top'])
        else:
            nodes+=arrow('left-growth',60,95,240,95,'active')+arrow('right-growth',620,95,440,95,'result')
            nodes.append(txt('gap',350,330,f'L={d["L"]}, R={d["R"]}, free={d["R"]-d["L"]}','result',20,True));invariant='Left stack [0,L), right stack [R,M), unused [L,R)';formula=r'0\le L='+str(d['L'])+r'\le R='+str(d['R'])+r'\le M='+str(len(a))
    elif order==93:
        a=d['cells'];c=len(a);pos={}
        for i,v in enumerate(a):
            angle=2*math.pi*i/c-math.pi/2;x=350+145*math.cos(angle);y=215+125*math.sin(angle);pos[i]=(x,y)
            nodes.extend([box('slot-'+str(i),x-37,y-25,74,50,'active' if v else 'muted'),txt('token-'+str(i),x,y+5,v or '·'),txt('index-'+str(i),x,y-35,'index '+str(i),'muted',14)])
        for i,(x,y) in pos.items():
            xx,yy=pos[(i+1)%c];vx=xx-x;vy=yy-y;dist=math.hypot(vx,vy)
            nodes+=arrow('wrap-'+str(i),x+vx*40/dist,y+vy*40/dist,xx-vx*40/dist,yy-vy*40/dist,'muted')
        hx,hy=pos[d['head']];tx,ty=pos[d['tail']]
        nodes+=arrow('head-physical',300,270,hx-30,hy+28,'active')
        nodes+=arrow('tail-physical',400,270,tx+30,ty+28,'input')
        nodes.append(txt('head-name',280,285,'h','active',14));nodes.append(txt('tail-name',420,285,'t','input',14))
        nodes.append(txt('count',350,212,'count '+str(d['count']),'result',19,True))
        nodes.append(txt('pointers',350,242,f'h={d["head"]}  t={d["tail"]}','active',18))
        nodes.append(txt('logical',350,400,'FIFO: '+(' → '.join(d['logical']) or 'empty'),'result',18,True));invariant='t ≡ h + count (mod M), with 0 ≤ count ≤ M';formula=r't=('+str(d['head'])+'+'+str(d['count'])+r')\bmod '+str(c)+'='+str(d['tail'])
    elif order==95:
        for row,key in enumerate(['live','reserved','free']):
            y=70+row*115;nodes.append(txt('owner-'+key,62,y+26,key,'muted',14));ids=d[key];pos=cards(nodes,ids,y,'pool-slot',start=120,step=100,labels={p:f'@{p} '+str(d['values'].get(p,'')) for p in ids})
            if key!='reserved':link_chain(nodes,ids,pos,key+'-link')
        invariant='Pool = live ⊎ reserved ⊎ free; no slot disappears';formula=r'|P|='+str(len(d['live']))+'+'+str(len(d['reserved']))+'+'+str(len(d['free']))+'='+str(len(d['universe']))
    elif order==96:
        ids=d['order'];pos=cards(nodes,ids,165,start=110,step=170);link_chain(nodes,ids,pos)
        nodes.append(txt('head',180,85,'head = '+str(d['head'] or '∅'),'active',19));nodes.append(txt('tail',490,85,'tail = '+str(d['tail'] or '∅'),'active',19))
        if ids:
            nodes+=arrow('head-pointer',180,100,pos[ids[0]][0]+39,160,'active')+arrow('tail-pointer',490,100,pos[ids[-1]][0]+39,160,'active')
        nodes.append(txt('retired',350,330,'retired: '+', '.join(d['retired']),'muted'));invariant='head = ∅ iff tail = ∅; a nonempty tail links to ∅';formula=r'|Q|='+str(len(ids))
    elif order==97:
        vs=list(d['adj']);coords={v:(110+i*120,145+(i%2)*75) for i,v in enumerate(vs)}
        for v,us in d['adj'].items():
            x,y=coords[v]
            for u in us:
                xx,yy=coords[u];vx=xx-x;vy=yy-y;distance=math.hypot(vx,vy)
                nodes+=arrow('edge-'+v+u,x+vx*28/distance,y+vy*28/distance,xx-vx*28/distance,yy-vy*28/distance,'active' if v in d['remaining'] else 'muted')
        for v,(x,y) in coords.items():
            nodes.extend([dict(id='vertex-'+v,type='circle',x=x,y=y,r=26,role='active' if v in d['ready'] else 'input' if v in d['remaining'] else 'muted'),txt('vertex-label-'+v,x,y+6,v),txt('count-'+v,x,y+54,'in '+str(d['indeg'][v]),'result',15,True)])
        nodes.append(txt('ready',350,65,'ready: '+', '.join(d['ready']),'active'))
        nodes.append(txt('output',350,330,'order: '+', '.join(d['output']),'result',18,True))
        if d.get('cycle'):nodes.append(txt('cycle',350,375,'cycle: '+' → '.join(d['cycle']),'error'))
        invariant='Incoming counts refer only to edges from remaining vertices';formula=r'c(v)=|\{u\in R:u\to v\}|'
    elif order==98:
        ids=['H']+d['order'];pos={}
        for k,v in enumerate(ids):
            angle=2*math.pi*k/len(ids)-math.pi/2;pos[v]=(350+225*math.cos(angle),215+135*math.sin(angle))
        for v,u in d['links'].items():
            x,y=pos[v];xx,yy=pos[u];dx=xx-x;dy=yy-y;dist=math.hypot(dx,dy)
            nodes+=arrow('next-'+v,x+dx*29/dist,y+dy*29/dist,xx-dx*29/dist,yy-dy*29/dist,'active')
        for v,(x,y) in pos.items():nodes.extend([dict(id='node-'+v,type='circle',x=x,y=y,r=27,role='active' if v==d['active'] else 'muted' if v=='H' else 'input'),txt('label-'+v,x,y+6,v)])
        invariant='Exactly one sentinel, reached again after every data node';formula=r'\operatorname{next}^{'+str(len(ids))+r'}(H)=H'
    elif order==99:
        a=d['left'];b=d['right'];product='pair' in d
        if product:
            for j,(e,c) in enumerate(a):nodes.append(txt('left-'+str(e),215+j*130,65,f'{c}x^{e}'))
            for i,(f,v) in enumerate(b):
                nodes.append(txt('right-'+str(f),75,120+i*65,f'{v}x^{f}'))
                for j,(e,c) in enumerate(a):
                    active=d['pair']==[e,f];revealed=[e,f] in d['processed'];nodes.extend([box(f'pair-{e}-{f}',160+j*130,90+i*65,115,48,'active' if active else 'muted'),txt(f'pair-label-{e}-{f}',217+j*130,120+i*65,f'{c*v}x^{e+f}' if revealed else '·', 'active' if active else 'input',15,result=active)])
        else:
            for row,(key,terms,cursor) in enumerate([('P',a,d['i']),('Q',b,d['j'])]):
                y=85+row*100;nodes.append(txt('stream-'+key,45,y+25,key));ids=[str(e) for e,c in terms]+['H'];labels={str(e):f'{c}x^{e}' for e,c in terms};labels['H']='H'
                pos=cards(nodes,ids,y,key,start=85,step=120,labels=labels);link_chain(nodes,ids,pos,key+'-link',ring=True)
                x=85+min(cursor,len(terms))*120;nodes+=arrow('cursor-'+key,x+39,y-23,x+39,y,'active')
        text=' + '.join(f'{c}x^{e}' for e,c in sorted(d['result'].items(),reverse=True)) or '0'
        nodes.append(txt('result',350,380,'result: '+text,'result',18,True));invariant='One nonzero coefficient per exponent; output exponents decrease';formula=r'P(x)+Q(x)' if not product else r'[x^k](PQ)=\sum_{i+j=k}p_iq_j'
    elif order==100:
        ids=list(d['links']);pos=cards(nodes,ids,155,start=40,step=125)
        for v,l in d['links'].items():
            x,y=pos[v]
            for direction,delta,role in [('next',8,'active'),('prev',35,'muted')]:
                u=l[direction];xx,yy=pos[u]
                if abs(xx-x)<150:
                    if xx>x:nodes+=arrow(direction+'-'+v,x+78,y+delta,xx,y+delta,role)
                    else:nodes+=arrow(direction+'-'+v,x,y+delta,xx+78,y+delta,role)
                else:nodes.append(dict(id=direction+'-'+v,type='path',d=f'M {x+39} {y+delta} L {x+39} {95 if direction=="next" else 255} L {xx+39} {95 if direction=="next" else 255} L {xx+39} {y+delta}',fill='none',role=role,arrow=True))
        if d['staged']:
            nodes.extend([box('card-X',290,300,78,44,'muted'),txt('card-X-label',329,328,'X private','muted',14)])
        nodes.append(txt('phase',350,390,d['phase'],'error' if d['phase']=='updating' else 'result',20,True));invariant='Reciprocity is required at committed boundaries, not half-writes';formula=r'\operatorname{prev}(\operatorname{next}(v))=v' if d['phase']=='committed' else r'\text{protected intermediate: reciprocal invariant suspended}'
    elif order==101:
        nodes.append(line('time-axis',65,180,650,180));nodes.append(txt('clock',350,65,'clock = '+str(d['now']),'active',21))
        for t in range(8):nodes.extend([line('tick-'+str(t),85+t*75,173,85+t*75,187,'muted'),txt('ticklabel-'+str(t),85+t*75,210,t,'muted',14)])
        for k,e in enumerate(d['events']):
            t,priority,serial,kind,v,duration=e;x=85+t*75;y=120-(k%2)*40
            nodes.extend([line('event-stem-'+str(serial),x,y+12,x,173,'active'),txt('event-'+str(serial),x,y,f'{kind[0]}:{v}','active',15)])
        nodes+=arrow('clock-hand',85+d['now']*75,255,85+d['now']*75,186,'active')
        nodes.append(txt('worker',350,295,'tool: '+(d['busy'] or 'idle')+'   waiting: '+','.join(v for v,_ in d['waiting'])))
        nodes.append(txt('area',350,345,'waiting-time area = '+str(d['area']),'result',18,True));invariant='The simulation clock never decreases';formula=r'W=\sum_k q_k(t_{k+1}-t_k)='+str(d['area'])
    elif order==102:
        pos={v:(190+i*155,200) for i,v in enumerate(d['entities'])}
        nodes.extend([line('waiting-rail',70,90,650,90,'active'),line('calendar-rail',70,330,650,330,'muted'),txt('waiting-name',350,55,'waiting-list link fields','active'),txt('calendar-name',350,385,'independent timeout event identities','muted')])
        for v,(x,y) in pos.items():
            nodes.extend([box('entity-'+v,x-35,y-25,70,50),txt('entity-label-'+v,x,y+5,v)])
            if v in d['waiting']:nodes+=arrow('wait-membership-'+v,x,y-27,x,92,'active')
            e=next((e for e in d['calendar'] if e['entity']==v),None)
            if e:nodes+=arrow('event-reference-'+e['id'],x,328,x,y+27,'muted');nodes.append(txt('event-label-'+e['id'],x,357,e['id'],'muted',14))
        invariant='Canceling one membership never changes the entity identity';formula=r'|Q|='+str(len(d['waiting']))+r',\quad |E|='+str(len(d['calendar']))
    elif order==103:return array_scene(s)
    elif order==105:return pivot_scene(s)
    elif order==104:
        rows=d['rows'];cols=d['cols'];sx=125;sy=95;startx=190;starty=110
        for i in range(rows):
            nodes.append(txt('row-head-'+str(i),80,starty+i*sy+6,'row '+str(i),'active',15))
            row=d['rowLinks'][i]
            if row:
                first=next(e for e in d['entries'] if e['id']==row[0]);nodes+=arrow('row-head-link-'+str(i),130,starty+i*sy,startx+first['j']*sx-28,starty+i*sy,'active')
            else:nodes.append(txt('empty-row-'+str(i),150,starty+i*sy+6,'∅','muted',14))
        for j in range(cols):
            nodes.append(txt('col-head-'+str(j),startx+j*sx,45,'col '+str(j),'muted',15))
            col=d['columnLinks'][j]
            if col:
                first=next(e for e in d['entries'] if e['id']==col[0]);nodes+=arrow('col-head-link-'+str(j),startx+j*sx,65,startx+j*sx,starty+first['i']*sy-28,'input')
            else:nodes.append(txt('empty-col-'+str(j),startx+j*sx,82,'∅','muted',14))
        for paths,key,role in [(d['rowLinks'],'row','active'),(d['columnLinks'],'col','input')]:
            coord={e['id']:(startx+e['j']*sx,starty+e['i']*sy) for e in d['entries']}
            for k,path in enumerate(paths):
                for a,b in zip(path,path[1:]):
                    x,y=coord[a];xx,yy=coord[b];nodes+=arrow(key+'-'+a,x+26 if key=='row' else x,y+26 if key=='col' else y,xx-26 if key=='row' else xx,yy-26 if key=='col' else yy,role)
        for e in d['entries']:
            x=startx+e['j']*sx;y=starty+e['i']*sy;active=[e['i'],e['j']]==d.get('active');nodes.extend([dict(id=e['id'],type='circle',x=x,y=y,r=27,role='active' if active else 'input'),txt(e['id']+'-value',x,y+5,e['value'],size=16,result=True)])
        if order==105:
            p,q=d['pivot'];nodes.extend([box('pivot-cross-row',135,starty+p*sy-34,cols*sx,68,'active',.13),box('pivot-cross-col',startx+q*sx-34,70,68,rows*sy,'active',.13)])
        invariant='Each stored nonzero has one identity shared by row and column routes';formula=r'd\gets d-\frac{bc}{a},\quad a\ne0' if order==105 else r'A_{ij}=0\iff(i,j)\notin\operatorname{support}(A)'
    nodes.append(txt('scene-status',350,425,s['action'].replace('-',' '),'muted',14))
    return dict(title=s['action'].replace('-',' ').capitalize(),description=s['caption'],viewBox=[0,0,720,440],nodes=nodes,invariant=invariant),formula

# Original prose: concrete representation, formal contract, reasoning, and limits.
CONTENT={
88:dict(scope='Values, node identity, addresses, fields, null, and relocation; a language-neutral memory model, not a garbage collector.', passages=[
('A label is not the parcel', 'Imagine three parcels all labeled 7. Replacing one parcel’s label does not replace the others. A node is the parcel: an object with its own identity and fields. A value is a field’s current content. An address tells us where a node is stored. These three notions can coincide accidentally in a tiny example, but an implementation must not confuse them. In the scene, A, B, and C are identities, the labels are values, and the @ numbers are addresses. Duplicate values deliberately expose the distinction.',r'\mathrm{value}(A)=\mathrm{value}(B)\;\not\Rightarrow\;A=B'),
('A pointer encodes a relationship', 'Let V be a finite set of live nodes and let addr: V → M injectively assign memory addresses. A successor field is an abstract function next: V → V ∪ {null}; its concrete pointer stores addr(next(v)) when a successor exists. Here null is a separate marker ∅, not an ordinary node. A machine could reserve address zero for it, but that is a representation convention. A raw pointer does not inherently know a node’s type, owner, or lifetime. Those constraints must come from the program’s contract.',r'\operatorname{ptr}(v)=\operatorname{addr}(\operatorname{next}(v))\quad(\operatorname{next}(v)\ne\mathrm{null})'),
('Relocation changes an encoding', 'Move B to a different address while retaining B’s identity. If A still contains B’s old address, the picture’s abstract arrow and the machine’s lookup disagree. Our transition relocates B and repairs every inbound pointer as one protected operation. This is a semantic demonstration of the required repair, not an implementation of a moving collector. Editing B’s value afterward illustrates the other direction: a field update can change data without moving either a node or any incoming link.',r'\operatorname{addr}_{new}(B)=63\quad\Rightarrow\quad\operatorname{ptr}_{new}(A)=63'),
('What must stay true', 'At each completed operation, every nonnull pointer must designate a live node of the expected kind. That rule is necessary but not sufficient: a stale pointer can land on a newly allocated object at the same address. Object lifetime therefore matters as well as numeric address validity. The finite trace checks target existence and repairs addresses; it does not prove memory safety for arbitrary programs. When transferring this reasoning to a language with references, ask which parts the runtime enforces and which ownership rules the program still supplies.',r'\forall v\in V:\ \operatorname{next}(v)\in V\cup\{\mathrm{null}\}')],check=('Two live nodes have equal text labels. What makes them the same object?', ['Equal labels alone','The same object identity','Adjacent addresses'],1,'Equality of stored values says nothing about identity. Distinct nodes may store identical values.'),help=('Use two parcels, A and B, initially both labeled 7. Follow the string from A while B changes shelf.', 'The parcel is identity, its shelf is address, its label is value, and the string is the successor relationship.',('B moves from shelf 8 to shelf 20. A’s pointer stores 8. What needs repair?',['A’s pointer must become 20','Both parcel labels must change','Nothing; equal labels repair pointers'],0,'A concrete pointer encodes the destination address, so relocation requires updating it.'))),
89:dict(scope='Operation-driven layout choice and explicit access-count assumptions; no cache, allocator, or benchmark claim.',passages=[
('Ask what the program does often','A list is an abstract ordered sequence before it is a memory layout. An array and a linked chain can represent the same identities in the same order. They differ in how the program reaches an element and changes the order. A useful design question is therefore specific: do we mostly ask for the kth element, scan all elements, insert beside a known node, or grow unpredictably? Without an operation mix, calling one representation faster hides the actual decision. The scene performs one identical last-element query under two layouts.',r'L=(v_0,v_1,\ldots,v_{n-1})'),
('Count only what the model counts','Assume a random-access machine where arithmetic and reading one known address each cost a constant. An array computes the address of index k directly, then reads one data node. A singly linked chain starts at its head and follows k successor fields before it reads the kth node. Our displayed counter counts visited data nodes: one versus k+1. It excludes arithmetic, cache misses, pointer-field reads, and allocation. Naming the cost unit prevents an illustrative counter from being mistaken for a real elapsed-time measurement.',r'R_{array}(k)=1,\qquad R_{linked}(k)=k+1\quad(0\le k<n)'),
('A different operation changes the verdict','Inserting after a known linked node can change a constant number of links, provided a free node is already available. Inserting at array position k while preserving order generally shifts n−k elements. But if only a value is given, finding the predecessor may dominate linked insertion. The phrase “known node” is an essential precondition, not a technicality. A linked node also needs link storage; an array may need spare capacity. Both representation cost and the search needed before an update belong in a fair comparison.',r'T_{insert,array}(k)=\Theta(n-k+1),\qquad T_{splice,known}=\Theta(1)'),
('Separate an argument from one instance','For every legal k, array addressing is a fixed arithmetic expression; linked access follows a path of length k. That reasoning establishes the asymptotic access bounds under the stated machine assumptions. The animation merely checks one instance and verifies that both answers have the same identity. It cannot establish that arrays win on every workload. A tiny linked list, a cached node reference, variable-size records, or stable-address requirements can change the engineering choice even while the abstract cost statements remain true.',r'\operatorname{answer}_{array}(k)=\operatorname{answer}_{linked}(k)=v_k')],check=('You repeatedly insert after a node whose pointer you already have. Which missing fact most affects the comparison?',['Whether allocation is available and array order must be preserved','Whether node labels are alphabetic','Whether the list is drawn horizontally'],0,'Known-node insertion avoids a linked search, but allocation and the array’s order-preserving shifts still matter.'),help=('Use three cards and ask for the third. Compare a numbered shelf with a chain whose first card is known.','Index arithmetic jumps to a shelf; links supply the next address one at a time.',('In a head-only chain, reading index 3 visits how many data nodes?',['1','3','4'],2,'With zero-based indices, the path visits indices 0, 1, 2, and 3.'))),
90:dict(scope='Stack, queue, and unrestricted deque abstract end rules, with restricted variants explained; storage is intentionally abstract.',passages=[
('The rule belongs to the ends','A stack, queue, and deque can contain the same sequence of tokens yet permit different next operations. Fix left and right in the drawing. Here a stack inserts and removes on the right; a queue inserts right and removes left; an unrestricted deque allows insertion and deletion at either end. The word “top” identifies the stack’s chosen active end, not a direction in physical memory. Rotating a drawing cannot change the rule. These abstract interfaces work with either sequential or linked storage.',r'\mathrm{stack}:\ \mathrm{push}_R,\mathrm{pop}_R;\qquad\mathrm{queue}:\ \mathrm{push}_R,\mathrm{pop}_L'),
('Run one history under different rules','Insert A, then B, then C. Removing from the stack returns C because C arrived most recently; removing from the queue returns A because A has waited longest. The deque may choose either end, so its behavior is not fixed by its name alone. Our trace chooses left removal, then inserts Z at the left, an operation excluded from the chosen stack and queue interfaces. Each token keeps its identity across the transition so that an exit cannot be confused with a relabeling.',r'\mathrm{pop}_R(A,B,C)=((A,B),C),\quad\mathrm{pop}_L(A,B,C)=((B,C),A)'),
('Give empty operations a contract','A removal operation needs a precondition n>0. If n=0, this companion reports underflow and preserves the sequence; another API might return an optional value or throw an exception. Whichever convention is chosen, it must be distinguishable from successfully returning a legitimate data value. An input-restricted deque permits insertion at only one end but deletion at either; an output-restricted deque reverses that restriction. These are interface constraints rather than claims that the unused end is physically inaccessible.',r'\mathrm{precondition}(\mathrm{pop}) : |L|>0'),
('Why the order laws hold','A stack removal selects the last surviving insertion at its active end; that is last-in, first-out. A queue removal selects the earliest insertion not yet removed; that is first-in, first-out. Induction on a legal operation history proves these statements: insertion establishes a new last element and deletion removes the specified endpoint without changing the others’ relative order. Our finite model compares resulting sequences, but the induction explains arbitrary histories. Neither law says what scheduling policy is fair when new operations keep arriving forever.',r'\mathrm{FIFO}:\ i<j\ \land\ i,j\text{ pending}\Rightarrow i\text{ precedes }j')],check=('Insert P, Q, R, remove once, then insert S. Which token leaves next in a queue?',['Q','R','S'],0,'The first removal takes P; Q remains the earliest unremoved insertion.'),help=('Use just A and B. Keep the end labels fixed and watch which token exits.','The same two-token row demonstrates why newest-first and oldest-first differ.',('After inserting A then B, which leaves a stack first?',['A','B','Either, without choosing an end'],1,'The active-end stack removes the most recently inserted surviving token, B.'))),
91:dict(scope='Original tree-scheduling transfer of §2.2.1’s container rules; graph deduplication is discussed, not a complete graph-search API or a claim that the source uses this example.',passages=[
('Pending work is part of the algorithm','Suppose visiting a task reveals smaller tasks that should be done later. The pending structure determines what “later” means. A queue keeps tasks in discovery order and therefore finishes the current tree level before the next. A stack returns to the most recently saved task, producing a depth-first route. The scene uses a fixed rooted tree and the same children in both runs. We reverse the push order for a stack so that the left child is visited first; otherwise an unnoticed implementation detail would reverse siblings.',r'\mathrm{pending}\subseteq V,\qquad \mathrm{visited}\cap\mathrm{pending}=\varnothing'),
('Follow the frontier, not just the route','After A is visited, B and C are pending. Queue scheduling takes B and then C before B’s children; stack scheduling takes B and proceeds through B’s descendants while C waits. The frontier is not a picture of all unvisited vertices: it contains only discovered tasks that have not yet been processed. Vertices can exist in the input without having entered that frontier. Watching both the highlighted tree vertex and the pending sequence explains the route causally rather than asking the learner to memorize the names breadth-first and depth-first.',r'\mathrm{queue}:\ \mathrm{take\ oldest};\qquad\mathrm{stack}:\ \mathrm{take\ newest}'),
('Discovery needs its own bookkeeping','On a tree, each nonroot vertex has exactly one parent, so discovering the same vertex twice is impossible. On a general graph, two parents may point to the same vertex, or a cycle may return to an ancestor. Mark a vertex when it is scheduled, not only after it is processed, if the policy is to enqueue each identity once. Maintain a set D of discovered vertices and admit child u only when u∉D. Without this extra state, changing the container alone does not make a safe graph traversal.',r'u\notin D\Rightarrow D\gets D\cup\{u\},\quad\mathrm{schedule}(u)'),
('State what the order guarantees','For an unweighted graph, queue discovery produces nondecreasing shortest-path distance from the start when every edge is considered and vertices are marked on discovery. Our tree makes this statement easy to see, but the shortest-path theorem is broader than the illustration. Stack discovery does not generally have that distance property. Both finite tree runs visit exactly the same identities once; their different orders are not different answers to a membership query. Order becomes consequential when work has side effects, costs, or a goal test that stops early.',r'\mathrm{BFS}:\ d(v_{k+1})\ge d(v_k)')],check=('A is parent of B and C; B is parent of D. With left-first scheduling, who comes third?',['Queue: C; stack: D','Queue: D; stack: C','Both: D'],0,'The queue keeps C ahead of newly discovered D. The stack pursues B’s child before returning to C.'),help=('Try the tree with only A and its two children B and C. See that both policies agree before adding a grandchild.','A policy difference needs deferred work at different depths; the smaller tree isolates the pending operation.',('Why do both policies visit A,B,C in this smaller trace?',['Their rules are identical','There is no deeper child to overtake C','A stack is always breadth-first'],1,'With no grandchildren, left-first stack and queue schedules coincide on this tree.'))),
92:dict(scope='Fixed-capacity contiguous stack with checked bounds and zero-based indexing; machine overflow is a separate implementation concern.',passages=[
('Reserve a row of equal-size cells','Sequential allocation assigns equal-size records to consecutive slots. Let the first address be b, each record occupy c address units, and indices run from 0 through M−1. Slot i then starts at b+ci. This affine formula is why known-index access does not require following links. In the scene b=100 and c=3; neighboring boxes are three address units apart even though each is one logical stack element. A field within a record would add its own checked offset.',r'\operatorname{addr}(i)=b+ci,\quad 0\le i<M,\quad c>0'),
('T is a count and a boundary','Use T to count occupied slots, so the live prefix is [0,T) and the next free slot, if any, is T. Pushing writes the new value at index T and then increments T. Popping first decrements T, then reads the old last element at that index. Our model clears a popped slot only to make the drawing unambiguous; clearing is not needed for the abstract stack semantics, though references may need release in a managed language. The numerical invariant is always 0≤T≤M.',r'\mathrm{push}(x):\ A[T]\gets x;\ T\gets T+1'),
('Check before an invalid memory access','When T=M, there is no slot T, so push must reject before writing. When T=0, decrementing would produce −1, so pop must reject before changing T. The trace deliberately attempts both errors, and it retains the exact prior state. Reporting an error after an out-of-bounds access is not a safe repair. Arithmetic itself can overflow on a real fixed-width machine; this Python model uses exact integers and validates domain bounds, while an actual implementation must additionally check the address range b+c(M−1).',r'\mathrm{push}:T<M;\qquad\mathrm{pop}:T>0'),
('The prefix invariant proves the interface','Initially T=0 represents the empty sequence. A legal push extends the occupied prefix by one and places its value at the new last position. A legal pop shortens the prefix by one and returns exactly its old last value. Induction therefore connects the memory representation to stack LIFO behavior. Tests cover boundary transitions and many generated histories; they support the implementation, while the invariant argument handles arbitrary legal histories. Resizing, concurrent updates, and variable-size elements require additional rules beyond this fixed-capacity model.',r'\mathrm{abstract}(A,T)=(A[0],\ldots,A[T-1])')],check=('Base 40, stride 4, capacity 5: where is slot 3, and may T=5 accept a push?',['Address 52; no','Address 43; yes','Address 60; no'],0,'40+4·3=52. T=5 equals capacity, so slot T is outside the allocated domain.'),help=('Use two slots to see empty, one item, full, and rejected insertion without distracting interior cells.','T marks the boundary between occupied and unused slots.',('With capacity 2 and T=1, where is the next push written?',['Index 0','Index 1','Index 2'],1,'The next free slot is index T; after the write T becomes 2.'))),
93:dict(scope='Counted circular buffer using all M slots; contrasted with the one-unused-slot convention, not conflated with it.',passages=[
('Reuse storage without moving survivors','A queue need not shift every remaining item when its first item leaves. Keep a head index h naming the next item to remove and a tail index t naming the next place to insert. Treat indices modulo capacity M, so advancing beyond M−1 returns to 0. The queue’s logical order can cross the physical end of the array. The scene draws the actual storage cycle while displaying the abstract FIFO order below it; wrapping changes neither token identity nor waiting order.',r'\operatorname{advance}(i)=(i+1)\bmod M,\quad M>0'),
('Equal indices need another fact','This version stores an explicit count n and uses all M cells. Its invariant is t≡h+n (mod M), with 0≤n≤M. Thus h=t occurs both when n=0 and when n=M. Looking only at the indices cannot distinguish these states. Another valid design reserves one unused cell and calls the buffer full when advancing t would meet h; that design stores at most M−1 items. Mixing its full test with our all-slots interpretation would waste or overwrite data.',r't\equiv h+n\pmod M,\qquad \mathrm{empty}\iff n=0,\quad\mathrm{full}\iff n=M'),
('Read the old endpoint before advancing','For enqueue with n<M, write at t, advance t, and increase n. For dequeue with n>0, read at h, advance h, and decrease n. The order makes explicit which token is returned. The trace first fills the buffer, rejects one overflow, removes two tokens, then wraps new tokens into the freed cells. It finally empties the buffer and rejects underflow. A rejected operation changes neither indices nor storage. None of these operations moves surviving tokens between slots.',r'Q_j=A[(h+j)\bmod M],\quad 0\le j<n'),
('Prove order through the representation map','The representation map reads n cells starting at h around the ring. A legal enqueue adds a value exactly after its current last mapped cell because t≡h+n. A legal dequeue removes exactly its first mapped cell by advancing h. Both preserve the congruence and the FIFO sequence. This proof works for M=1 too, where head and tail are always equal and count carries all state distinction. It assumes sequential operations; publishing indices safely between concurrent producers and consumers requires a separate memory-ordering argument.',r'\mathrm{enqueue}(Q,x)=Q\mathbin{\|}(x),\quad\mathrm{dequeue}(Q)=\mathrm{tail}(Q)')],check=('Capacity 5, h=4, count=3. What is t, and which physical indices contain FIFO items?',['t=2; 4,0,1','t=1; 4,0,1','t=2; 0,1,2'],0,'t=(4+3) mod 5=2; the occupied cells begin at h and wrap as 4,0,1.'),help=('A two-place circular shelf makes equal endpoints unavoidable: compare count 0 with count 2.','The extra count turns ambiguous equal indices into a definite empty or full state.',('In a two-slot counted buffer, h=t=1 and count=2 means what?',['Empty','Full','Invalid solely because h=t'],1,'Both slots are occupied; the explicit count distinguishes full from empty.'))),
94:dict(scope='Opposing stacks and a safe overlapping relocation subroutine modeled; general multiple-table allocation discussed without claiming a complete allocator.',passages=[
('Let two tables borrow the same slack','Giving two stacks separate fixed capacities can fail one stack while unused cells remain in the other region. Instead place one stack at the low end of a shared area and another at the high end. Let L be the first unused cell after the left stack and R the first occupied cell of the right stack. Their occupied intervals are [0,L) and [R,M); the shared gap is [L,R). Only the total occupancy determines whether another push fits.',r'\mathrm{used}=L+(M-R),\quad\mathrm{free}=R-L'),
('Opposite growth makes collision simple','A left push writes at L and increments L. A right push decrements R and writes at R. Both first require L<R. The scene alternates pushes until the boundary indices meet; the next attempted push is rejected without changing a value. Every slot has a visible role: left-owned, right-owned, or unused. This is stronger than counting total elements alone because it states exactly where each owner may write. A left pop and a right pop reverse their respective endpoint updates.',r'0\le L\le R\le M'),
('More tables require a relocation policy','Three or more independently growing contiguous tables cannot all enjoy the simple two-ended arrangement. A manager may move a table into a larger gap and adjust its base address. If source and destination overlap, movement order matters: moving a block to higher addresses requires copying from its high end downward, while moving lower requires copying low to high. Otherwise a write can destroy an unread source item. A temporary buffer is another correct solution. Raw external pointers also need repair when a table relocates.',r'\mathrm{overlap\ move\ right}:\ i=n-1,n-2,\ldots,0'),
('Name the limits of this demonstration','The executable trace establishes the two-stack ownership partition, full-condition behavior, and a backward-copy overlapping relocation. It does not implement the source’s more general table-reallocation strategy or optimize future growth. The protected-move argument explains one necessary part of such an allocator, not the whole algorithm. For the two-stack case, induction is short: a successful push transfers exactly one gap cell to one owner; a successful pop returns exactly one endpoint cell to the gap. Collision is precisely L=R, independent of how unbalanced the two stacks are.',r'|[0,L)|+|[L,R)|+|[R,M)|=M')],check=('Copy slots 2,3,4 into slots 3,4,5 using the same array. Which direction preserves unread values?',['Copy index 4 first, then 3, then 2','Copy index 2 first','Either direction without temporary storage'],0,'The destination is higher and overlaps; copying backward prevents a write to slot 3 from destroying its old content before it is read.'),help=('Four cells, two growing ends. Watch the unused gap disappear one cell at a time.','The gap is shared capacity, while the boundary indices record ownership.',('Capacity 6, L=2, R=4: how many cells remain available?',['2','4','6'],0,'The unused interval is [2,4), containing cells 2 and 3.'))),
95:dict(scope='Fixed-size storage pool with live/reserved/free ownership, linked publication, recycling, and lifetime caveats; no garbage collector.',passages=[
('Unused cells can form a list too','Linked structures need a way to obtain a node when inserting data. Put unused fixed-size slots on a free list whose head is AVAIL. Allocation removes its first slot; recycling pushes a retired slot back. The links inside free slots have allocator meaning, while links inside live nodes have data-structure meaning. A slot cannot safely serve both roles at once. In the partition formula, P means all pool slots, L the live slots, R the reserved slots, and F the free slots. The dotted union symbol ⊎ means these sets do not overlap. Our three-rail scene makes a normally hidden state explicit: a reserved slot belongs to an in-progress operation until it is initialized and published.',r'P=L\;\dot\cup\;R\;\dot\cup\;F'),
('Separate reservation from publication','Allocation first checks AVAIL≠null. It reads the free head p, advances AVAIL to p’s former successor, and takes ownership of p. The program then initializes p’s value and live successor before making a live predecessor or head point to p. Publishing first could expose an uninitialized link. Each frame checks that the universe of slots is exactly partitioned into live, reserved, and free sets. At completed operation boundaries the reserved set is empty; during a multi-step update it accounts for otherwise missing storage.',r'p\gets\mathrm{AVAIL};\quad\mathrm{AVAIL}\gets\mathrm{freeNext}(p)'),
('Unlink before recycling','Deletion first removes every live route by which the structure owns the node, then retires it, then gives its slot to the allocator. Recycling while a live link still points there would let the same address belong to unrelated logical structures. The example allocates two nodes, removes one, and reuses its slot for M. The numeric address repeats, but the old object lifetime does not. An external pointer to the former object is stale even if the slot now contains a valid new node.',r'\mathrm{liveReachable}(p)\Rightarrow p\notin F'),
('Conservation catches concrete mistakes','A lost slot violates coverage of the pool; double allocation or double free violates disjointness. These are checkable invariants over finite slot identities, not assumptions about their labels. A full free list is not required: it may be empty when every slot is live. Allocation must then fail or invoke a separately specified recovery policy. The fixed-size model does not address fragmentation, variable-size allocation, tracing reachability from arbitrary roots, or concurrent reclamation. Those topics require additional state beyond this useful first conservation law.',r'|P|=|L|+|R|+|F|')],check=('A node has been bypassed in one list but is still owned by another. May its slot go to AVAIL?',['Yes, because one link was removed','No, another live owner still needs it','Yes, if its value is zero'],1,'Recycling requires retiring all live ownership, not merely removing one occurrence.'),help=('Use a three-slot pool and allocate only two objects. Follow one slot through free, reserved, live, retired, and free again.','The rails classify ownership, not different physical memories.',('A pool has 5 slots: 2 live and 1 reserved. How many are free?',['2','3','4'],0,'The disjoint ownership partition accounts for all five slots: 5−2−1=2.'))),
96:dict(scope='Nonsentinel singly linked queue endpoint model, linked stack rules, and sentinel comparison; assumes allocator operations are supplied.',passages=[
('Two endpoints save a traversal','A linked queue keeps a head h for removal and a tail t for insertion. The live successor chain runs from h to t, and next(t)=null. An empty nonsentinel queue has both endpoints null. The tail avoids scanning the chain on every enqueue, but it creates an invariant that must be maintained together with the head. In contrast, a linked stack needs only its top: insertion and removal both modify that same end. Neither interface implies that nodes are consecutive in memory.',r'h=\mathrm{null}\iff t=\mathrm{null}'),
('Handle the first and last nodes explicitly','To enqueue a new initialized node p, set next(p)=null. If the queue is empty, set both h and t to p; otherwise link the former tail to p and then update t. To dequeue, reject an empty queue, save the head’s value, and advance h to next(h). If h becomes null, set t to null too. Forgetting that final update leaves a dangling tail after removing the last node. Our trace empties and refills the structure specifically to expose this boundary.',r'\mathrm{dequeue}:\ h\gets\operatorname{next}(h);\quad h=\mathrm{null}\Rightarrow t\gets\mathrm{null}'),
('A sentinel changes the empty convention','A dummy header can make the head node always present, with real data beginning at its successor. In one common queue design, tail equals the header when no data remain. That does not mean the queue contains a data item: the sentinel is administrative storage. Sentinel and nonsentinel formulas must not be mixed. Our executable scene uses no sentinel; the circular-list lesson will make a sentinel visible. For a stack, a new node can point to the old top before the top pointer is changed.',r'\mathrm{stack\ push}(p):\ \operatorname{next}(p)\gets\mathrm{top};\ \mathrm{top}\gets p'),
('Prove endpoints and sequence together','The endpoint equations alone could hold even if a middle link forms a cycle. A full representation invariant also requires that following successors from h visits each owned live node exactly once and ends at t. Each snapshot reconstructs that chain and checks its last identity. A legal enqueue extends it by one and a legal dequeue removes exactly its first node, preserving FIFO order. The model assumes sequential protected operations and correctly supplied fresh nodes; allocation ownership and safe reclamation were separate obligations in the preceding lesson.',r'\operatorname{walk}(h)=(v_0,\ldots,v_{n-1}),\quad v_{n-1}=t')],check=('A one-node nonsentinel queue removes its only item. What must its endpoints become?',['Head null, tail unchanged','Both null','Head unchanged, tail null'],1,'The queue is empty, so both endpoints must follow the empty representation convention.'),help=('Enqueue A, remove A, then enqueue B. This smaller history isolates both empty transitions.','The first insertion and last deletion are where the two endpoints must change together.',('Why set next(B)=null before appending B?',['B becomes the last node','It sorts the queue','It frees the previous tail'],0,'A tail must have no live successor; initialization establishes that before publication.'))),
97:dict(scope='Incoming-count topological sort and explicit residual cycle witness on finite simple directed graphs; deterministic ready-queue tie order.',passages=[
('Constraints are directed edges','A precedence constraint u→v says u must appear before v. A topological ordering lists every vertex once while respecting every edge. Write π(v) for the position of vertex v in that proposed ordering; the inequality π(u)<π(v) says u occupies an earlier position. It exists exactly when the finite directed graph has no directed cycle. A partial order can be supplied through generating constraints; the input need not list every transitive consequence. Our adjacency lists contain each edge once and include every vertex, including isolated ones. Multiple legal orderings may exist, so different tie policies can produce different correct answers.',r'\pi(u)<\pi(v)\quad\text{for every edge }u\to v'),
('Counts describe the remaining problem','Maintain R, the unprocessed vertices, and c(v), the number of incoming edges to v from R. Initially count all edges and enqueue every zero-count vertex. Removing a ready vertex u satisfies its own prerequisites, then deletes its outgoing contributions: decrement c(v) once for each u→v. A vertex enters the ready queue when its count first becomes zero. The displayed counts are recomputed by assertion from the residual graph after each emission, making the relation between edge removal and newly ready work explicit.',r'c(v)=|\{u\in R:u\to v\}|'),
('An empty queue is not always success','If the ready queue empties and R is empty, the ordering is complete. If R is nonempty, every remaining vertex has an incoming edge from another remaining vertex. Repeatedly following one such predecessor must repeat a vertex because R is finite. The repeated segment, reversed into edge direction, is a directed cycle witness. A leftover vertex need not itself lie on a cycle: it could merely depend on one. The model displays an actual edge-checked cycle rather than incorrectly labeling every residual vertex cyclic.',r'R\ne\varnothing\land\forall v\in R:c(v)>0\Rightarrow\text{a directed cycle exists}'),
('Correctness and cost use different arguments','Every emitted vertex has no remaining prerequisite, so appending it cannot place it before an unprocessed predecessor. Induction proves the output prefix respects all constraints. In an acyclic nonempty residual graph, the predecessor-following argument rules out all positive counts, so another ready vertex exists. Here V is the vertex set, E the directed edge set, T the amount of work, and S the storage required; |V| and |E| count their members. With adjacency lists, each vertex enters and leaves the queue once and each edge causes one decrement, giving O(|V|+|E|) work. The explicit cycle witness uses extra traversal only on failure; the source’s count-based method and our small witness extension are distinguished.',r'T=O(|V|+|E|),\quad S=O(|V|+|E|)')],check=('Constraints U→W and V→W leave U and V ready. Which output is valid?',['U,V,W and V,U,W','Only U,V,W','W,U,V'],0,'U and V have no constraint between them, but W must follow both.'),help=('First use A→B→C. Then compare a two-vertex directed ring where no vertex can start.','A zero incoming count means every predecessor has already left the residual graph.',('A vertex remains after the algorithm detects a cycle. Must it lie on that cycle?',['Yes','No; it can depend on the cycle','No vertex can remain'],1,'Residual dependents also keep positive incoming counts; an explicit witness distinguishes them.'))),
98:dict(scope='Sentinel-based circular traversal and protected splicing; concatenation transfers a disjoint data chain and is not a concurrency-safe primitive.',passages=[
('Closing the chain changes the stopping rule','A circular list replaces the final null successor with a link back into the structure. Every node therefore has a successor, and repeated traversal never encounters null. A list can be represented by a pointer to one data node, stopping when that identity returns, or by a distinguished sentinel H. Here H is permanent administrative storage and next(H)=H represents an empty data list. The sentinel must be recognized by identity or an unambiguous tag, never merely by a data value that might also occur in a real node.',r'\mathrm{empty}\iff\operatorname{next}(H)=H'),
('Traverse exactly one circuit','Start at next(H), process the current data node, and advance until the cursor is H. Do not process H as a data element. The trace highlights each actual node and the closing link; a return to H is a successful stop rather than an accidental cycle. A loop that waits for null would run forever on a well-formed ring. Conversely, finding an unexpected repeated data node before reaching H indicates a malformed structure, which our validation detects instead of treating it as completion.',r'p\gets\operatorname{next}(H);\quad\text{while }p\ne H:\ \mathrm{visit}(p);\ p\gets\operatorname{next}(p)'),
('Splicing preserves identities and membership','To insert X after a known node A, initialize next(X) to A’s former successor and then set next(A)=X. Preparing the new link first prevents losing the rest of the ring. Concatenating disjoint lists likewise redirects boundary links rather than copying values. Our demonstration transfers a small Y,Z chain before H and repairs the closing link as a protected change. A general two-header concatenation must also reset the donor header to an empty ring; otherwise two owners would claim the same data nodes.',r'\operatorname{next}(X)\gets\operatorname{next}(A);\quad\operatorname{next}(A)\gets X'),
('A sentinel simplifies some boundaries, not every cost','The sentinel gives a uniform insertion point even when no data exist, and deletion can test for H instead of null. It does not automatically give a constant-time pointer to the last data node. If only H is known in a singly linked ring, finding the predecessor of H still needs a scan unless an extra tail pointer is maintained. The checked invariant is one finite circuit through H containing every owned data node exactly once. That statement explains both traversal termination and the ownership precondition behind safe splicing.',r'\operatorname{next}^{n+1}(H)=H\quad\text{with no earlier return}')],check=('Two rings share one data node. Is the usual disjoint-ring concatenation valid?',['Yes, links ignore identity','No, the disjointness precondition fails','Yes, if values differ'],1,'Shared identities can create incorrect cycles and duplicate ownership when boundary links are rewired.'),help=('Use H and one data node A. Trace H→A→H, then insert X beside H.','The simplest nonempty ring already contains the closing edge and the sentinel stopping test.',('What does an empty sentinel ring point to?',['Null','The sentinel itself','An arbitrary recycled node'],1,'The invariant uses next(H)=H for the empty data list.'))),
99:dict(scope='Exact univariate integer sparse polynomial merge and product; multivariate exponent-vector generalization explained, not MIX field packing or a full symbolic algebra system.',passages=[
('Represent only nonzero terms','A sparse polynomial stores pairs (e,c) for the term cx^e, with e a nonnegative integer and c a nonzero integer. Keep exponents strictly decreasing and represent zero by an empty data list with a header. Canonical order makes equal powers meet during merging and forbids two independent nodes for the same exponent. The source uses several variables and packed exponent fields; this executable model deliberately uses one variable and exact integers, avoiding word-width assumptions while preserving the essential merge and cancellation decisions.',r'P(x)=\sum_{e\in E}c_ex^e,\quad E\subset\mathbb N_0\text{ finite},\quad c_e\ne0'),
('Addition is a synchronized walk','Compare the leading unconsumed exponents. Copy the larger exponent because it cannot meet a later, smaller exponent on the other side. When exponents agree, add coefficients, consume both terms, and omit the result if the coefficient becomes zero. One exhausted stream contributes its remaining terms. The two cursor arrows identify the actual comparison, and the result below accumulates only canonical nonzero terms. Each step consumes at least one input term, so the merge terminates and uses O(m+n) comparisons for m and n terms.',r'[x^e](P+Q)=[x^e]P+[x^e]Q'),
('Multiplication creates contributions, then combines them','A term cx^e times dx^f contributes cd·x^(e+f). Different term pairs can produce the same exponent, so the grid of pairwise products is not yet a canonical output list. The model accumulates contributions by exponent, deleting a key whenever its exact coefficient becomes zero. This is the algebraic equivalent of repeatedly merging scaled, exponent-shifted copies of a polynomial into an accumulator. In several variables, exponents become vectors and multiplication adds them componentwise under a chosen consistent monomial ordering.',r'[x^k](PQ)=\sum_{e+f=k}c_ed_f'),
('Cancellation changes storage, not just a label','If a coefficient becomes zero, retaining its node violates our sparse representation convention. Deleting it must preserve list links and recycle storage correctly in a linked implementation; the model’s map removes the corresponding term identity. Exact integer arithmetic makes equality to zero unambiguous. Approximate coefficients would need a deliberately chosen numerical policy and would no longer satisfy the same canonical equality rule automatically. Evaluation at finitely many sample x values helps catch mistakes but is not, by itself, a proof that arbitrary symbolic polynomials are equal.',r'c_e=0\Rightarrow e\notin\operatorname{support}(P)')],check=('What is (x+2)(x−2) in canonical sparse form?',['x²−4','x²+0x−4 with a stored zero node','x²−2'],0,'The +2x and −2x contributions cancel, leaving only the nonzero x² and constant terms.'),help=('Use x+1 and x−1. Their two streams cancel the constants in addition, while their 2×2 product grid cancels the x terms.','A term’s exponent is its address in the algebraic result; equal exponents combine even when they came from different pairs.',('When adding 3x² and −3x², how many data terms remain?',['One zero term','Two terms','None'],2,'Canonical sparse form omits exact zero coefficients; only the header remains.'))),
100:dict(scope='Doubly linked sentinel ring with visible private preparation and protected inconsistent intermediates; no claim of lock-free or atomic multiword updates.',passages=[
('Each neighboring relation has two fields','In a doubly linked list, next(v) points forward and prev(v) points backward. For every published node v, the neighboring fields must agree: prev(next(v))=v and next(prev(v))=v. A sentinel H closes both directions and represents empty data by next(H)=prev(H)=H. These equations permit deletion when the node itself is known, because it directly names both neighbors. They do not tell us which list owns an arbitrary node or whether it is already retired.',r'\operatorname{prev}(\operatorname{next}(v))=v,\quad\operatorname{next}(\operatorname{prev}(v))=v'),
('Insertion affects four fields','To insert X between A and B, first privately prepare prev(X)=A and next(X)=B. Then publish next(A)=X and prev(B)=X. The scene distinguishes the private prepared node from the published list. After the first publication, the reverse link is temporarily stale; the frame explicitly labels this protected intermediate. A general-purpose traversal must not observe it as a completed data structure. A lock, transaction, or suitable atomic abstraction is needed if another participant might inspect the list during these separate writes.',r'X.prev\gets A;\ X.next\gets B;\ A.next\gets X;\ B.prev\gets X'),
('Deletion bypasses before retiring','Let A=prev(X) and B=next(X). Set next(A)=B and prev(B)=A, then retire X once no remaining owner or permitted reader can use it. Only two neighbor fields need rewiring, but the node’s ownership and reclamation obligations do not disappear. A singleton data list works with the same formulas because both neighbors are H. The executable trace shows the inconsistent forward-only bypass and the repaired committed boundary, rather than silently pretending the two machine assignments happen simultaneously.',r'A.next\gets B;\quad B.prev\gets A'),
('Choose the level where an invariant holds','An invariant may describe public operation boundaries without holding after each individual instruction. That is legitimate only when the implementation prevents observers from depending on it during the update. Our assertion checks reciprocal links at every committed boundary; the explicitly marked intermediate frames instead explain which equation is suspended. This distinction is important in proofs and animations: interpolating arrows cannot establish atomicity. The demonstration covers sequential protected list surgery, not concurrent memory reclamation, compare-and-swap protocols, or safe iteration while another thread deletes nodes.',r'\mathrm{committed}\Rightarrow\forall v:\ v.next.prev=v=v.prev.next')],check=('After A.next=X is published but B.prev still equals A, may a general backward traversal assume reciprocity?',['Yes; one correct direction is enough','No; the update is not committed','Only when X’s value is zero'],1,'The backward route is stale until B.prev=X. The intermediate requires protection from ordinary observers.'),help=('Use only sentinel H and data node A, then insert X between A and H. Both neighbor roles remain visible.','Four field assignments express two new neighbor relationships; both directions must agree at the boundary.',('Delete the only data node from a sentinel ring. What are H’s links afterward?',['Both H','Both null','One H and one old node'],0,'The empty-ring convention closes both directions directly onto H.'))),
101:dict(scope='Original single-tool workshop discrete-event model with deterministic equal-time priorities and exact waiting-time area; semantic continuations, not a coroutine language interpreter.',passages=[
('Advance to the next change','A discrete-event simulation represents changes scheduled at particular simulated times. Between consecutive event times, a system state may remain constant, so incrementing a clock through every unused tick wastes effort and can obscure the model. Our original workshop has arriving jobs, one tool, and a FIFO waiting line. An arrival may begin service immediately or wait; a completion releases the tool and may schedule another completion. Write ℰ for the set of future events and t(e) for event e’s scheduled time. The minimum over ℰ chooses the next event time. The event calendar holds future changes, while the waiting line holds entities awaiting a resource. They are different structures.',r't_{next}=\min\{t(e):e\in\mathcal E\}'),
('An event needs both identity and order','Order events lexicographically by (time, priority, serial). This model processes a completion before an arrival at the same time, then uses an increasing serial number to break any remaining tie. A tie policy is part of the model, not an implementation accident. Remove exactly the first calendar event, advance the clock to its time, execute its transition, and insert any newly scheduled events in order. The tool’s busy job and future completion represent a suspended process that will resume later, analogous to a coroutine continuation.',r'e_1<e_2\iff(t_1,p_1,s_1)<_{lex}(t_2,p_2,s_2)'),
('Statistics belong to intervals','Let W be the accumulated waiting-time area, measured in job-time units. If q jobs wait throughout [t_old,t_new), add q(t_new−t_old) to the waiting-time area before applying the event at t_new. Using the queue length after the event would charge a job for time it did not wait or fail to charge one that just left. The model records this area exactly with integer times and compares it against an independent per-job waiting calculation. Busy time, queueing time, and turnaround time are different quantities and should never share a label merely because each involves the clock.',r'W\gets W+q\,(t_{new}-t_{old})'),
('State the simulation’s assumptions','Service durations are positive, event times never precede the current clock, and the input contains finitely many arrivals. These assumptions ensure the example terminates without an infinite cascade of same-time events. A more general simulator may need cancellation, priority changes, random inputs, or a rule against infinitely many events in finite simulated time. The scene executes the workshop’s state transitions; it does not interpret the source’s complete simulation program or claim to model every real-world workshop detail. Correctness means fidelity to this stated model.',r't_{k+1}\ge t_k,\qquad\mathrm{duration}>0')],check=('Three jobs wait from time 5 up to time 9, then one leaves. How much waiting-time area is added for that interval?',['8','12','16'],1,'Use the pre-event queue length: 3×(9−5)=12 job-time units.'),help=('Two arrivals and one tool make the difference between the calendar and waiting line visible without many simultaneous events.','The calendar schedules when a process resumes; the queue records who is waiting for the resource.',('A completion and arrival occur at the same time. Which runs first here?',['Whichever was drawn first','Completion, because priority 0 precedes 1','There can never be ties'],1,'The explicit (time, priority, serial) key determines the same-time policy.'))),
102:dict(scope='Separate waiting and timeout memberships with identity-targeted cancellation; an original bounded scenario, not a complete event simulator.',passages=[
('One job can have two memberships','A waiting job may also own a timeout event. These are two relationships of one entity, not two copies of the job. If intrusive linked lists are used, each membership needs separate link fields: changing waitNext must not overwrite eventNext. Alternatively, a separate event record can point to the job. The scene uses one central entity card and two rails, with timeout records carrying their own identities. This makes cancellation target an event record rather than an ambiguous value or timestamp.',r'\mathrm{waitNext}(v)\ \text{and}\ \mathrm{eventNext}(v)\text{ are distinct fields}'),
('Leaving one list does not leave every list','Let Q be the set of waiting jobs and ℰ the set of scheduled events; these are different kinds of object. When A starts service, remove A from the waiting line. Its timeout still exists until the event calendar is explicitly updated. The trace pauses between those steps so the temporary outstanding membership is visible. If the timeout should no longer apply, cancel its exact event identity before normal event processing resumes. Removing A from the waiting line alone would not prevent a later timeout callback from acting on a job already in service. The intended transition is therefore a coordinated change across structures.',r'v\notin Q\;\not\Rightarrow\;\operatorname{timeout}(v)\notin\mathcal E'),
('Cancellation has a precise postcondition','After cancel(e), event e must never fire. Our calendar physically removes that exact record. Another implementation could retain a tombstone and skip it when extracted, but then the canceled flag and identity check become part of the representation invariant. Canceling “the event at time 5” is unsafe when several events share that time. Similarly, recycling the job while some event still points to it creates a lifetime error even if its waiting-list membership has been removed correctly.',r'\mathrm{canceled}\cap\mathrm{fired}=\varnothing'),
('Coordinate ownership at system boundaries','A full application must define what happens when service begins at exactly the timeout time. An explicit event-order policy or an atomic state check resolves the race; neither the two rails nor doubly linked pointers decide it automatically. This smaller model performs cancellation before processing remaining timeouts and checks that canceled events never fire. It is an illustration of multi-membership and ownership, not a complete concurrent scheduler. Its lesson transfers to caches, operating-system task lists, and subscriptions whenever one entity participates in several indexes.',r'\mathrm{retire}(v)\Rightarrow\text{no live membership or event owns }v')],check=('Jobs J and K both have timeouts at time 8. J begins service. What should cancellation identify?',['Time 8 alone','J’s specific timeout event','Every event at time 8'],1,'Equal times do not imply equal events; cancel only the record belonging to J’s timeout.'),help=('Use two jobs and two timeout records. Remove A from the waiting rail, then cancel only timeout-A.','The single entity card shows shared identity, while separate connectors show independent memberships.',('Does deleting a waiting-list link automatically cancel a timeout?',['Yes','No, the calendar membership is separate','Only if labels match'],1,'The event calendar must be updated explicitly under the model’s coordinated transition.'))),
103:dict(scope='Exact rectangular row/column-major offsets, packed lower triangles, and general-dimensional mixed-radix row-major indexing with nonzero lower bounds and repeated-divmod inverse; no hardware address arithmetic.',passages=[
('Coordinates need a linear storage rule','A two-dimensional array has a row index i and column index j, but ordinary memory supplies one address. Suppose rows run from ℓr to ℓr+R−1 and columns from ℓc to ℓc+C−1, with R,C positive integers. Subtracting the lower bounds gives zero-based coordinates r=i−ℓr and c=j−ℓc. Row-major storage places complete rows consecutively, so r rows contribute rC cells and c advances within the chosen row. Our non-square example prevents row and column dimensions from being accidentally interchangeable.',r'\rho(i,j)=(i-\ell_r)C+(j-\ell_c)'),
('A changed stride changes the layout, not the cell','Column-major storage instead completes one column at a time, giving offset cR+r. The scene retains every cell’s identity and coordinates while moving it to its row-major or column-major position. With base address b and s address units per element, the physical address is b+s·offset. Both layouts are bijections onto offsets 0 through RC−1; they merely assign different offsets to the same coordinates. Algorithms that traverse the fast-varying dimension may exploit locality, but that is outside this exact address-count model.',r'\kappa(i,j)=(j-\ell_c)R+(i-\ell_r),\qquad\operatorname{addr}=b+s\,\mathrm{offset}'),
('A triangle has unequal row lengths','For a lower triangular domain 0≤j≤i<n, row i contains i+1 entries. Before it lie 1+2+…+i=i(i+1)/2 entries, so the packed row-major offset is i(i+1)/2+j. This is not a single affine function of i and j because the row stride changes. The scene shows the triangular arrangement and the offset on each cell rather than padding missing cells with pretend storage. Symmetry or known zeros may justify triangular storage, but the storage rule itself does not imply either property of the represented matrix.',r'\tau(i,j)=\frac{i(i+1)}2+j,\quad 0\le j\le i<n'),
('Invert the map to check the formula','For row-major offset k, quotient and remainder on division by C recover r=⌊k/C⌋ and c=k mod C; add the lower bounds to recover i,j. The analogous column-major inverse divides by R. This establishes uniqueness and coverage for all valid rectangular coordinates, not merely a few sampled cells. For the triangle, row i begins at its triangular number and ends just before the next; these consecutive intervals prove bijectivity. Bounds and finite-machine overflow still require validation before computing a real memory address.',r'k=rC+c,\quad0\le c<C\Rightarrow r=\lfloor k/C\rfloor,\ c=k\bmod C')],check=('A 3×4 array has lower bounds (−1,2). What is the row-major offset of (1,4)?',['10','6','8'],0,'r=1−(−1)=2 and c=4−2=2, so 2·4+2=10.'),help=('Use a 2×2 tray with lower bounds (2,−1), then a three-row triangle. Read coordinates and offsets as different labels.','Flattening changes placement; it does not rename the underlying cell.',('In a lower triangle, what is the offset of (3,1)?',['7','4','10'],0,'Three earlier rows contain 1+2+3=6 cells; add column offset 1 to obtain 7.'))),
104:dict(scope='Canonical sparse matrix with sorted row/column routes sharing cell identity and atomic structural updates; not a complete in-place orthogonal-list allocator.',passages=[
('Zeros need not occupy data nodes','A sparse matrix can store only nonzero entries. Each stored cell has a row, a column, a value, and enough links to join its row list and column list. The same cell object belongs to both routes. Maintaining separate copied values in unrelated row and column structures would introduce a synchronization problem: an update could change one copy but not the other. In our diagram horizontal and vertical routes meet at one circle with one identity, while absent positions have the precise implied value zero. The source uses circular lists with header nodes and LEFT/UP links traversing decreasing coordinates. This teaching diagram instead shows routes in increasing row/column order without drawing circular return links. Shared cell identity and membership are preserved, but these arrows are not a literal rendering of the source’s link orientation.',r'\operatorname{support}(A)=\{(i,j):A_{ij}\ne0\}'),
('Insert through both dimensions','To insert a new nonzero at (i,j), locate its predecessor in row i and in column j, respecting the chosen increasing coordinate order. Prepare the cell’s row and column successors, then splice it into both routes as a protected operation. Searching for predecessors can dominate the constant number of link writes. The model reconstructs both sorted routes after each semantic update and checks that they contain exactly the same cell identities. It illustrates the required result, not a claim that rebuilding routes is the source’s efficient pointer algorithm.',r'\bigcup_i\mathrm{row}_i=\bigcup_j\mathrm{col}_j=\operatorname{support}(A)'),
('A duplicate coordinate means one coefficient','Adding a contribution at a coordinate already present changes that cell’s value; it must not create a second matrix entry for the same coordinate. If the new exact value is zero, remove the cell from both its row and its column before retiring it. The trace inserts (0,1), then adds its negative and erases it. A removed horizontal circle must not linger on the vertical route. Row and column membership tests are therefore independent checks of one shared object, not two separately counted nonzeros.',r'A_{ij}\gets A_{ij}+\delta;\quad A_{ij}=0\Rightarrow\mathrm{remove}(i,j)'),
('Compare with a dense oracle','In the formula, S is the set of stored coordinates and Â is the reconstructed dense matrix. Dense reconstruction fills every unrepresented coordinate with zero and places each stored value at its unique coordinate. Comparing that result before and after operations tests matrix semantics independently of link order. Additional structural checks enforce sorted rows, sorted columns, and identical membership. The finite model uses exact rational values, so deletion by equality to zero is well-defined. Floating-point sparsity thresholds, memory reclamation, and concurrent route updates need additional policies; a visually sparse picture alone cannot guarantee any of those properties.',r'\widehat A_{ij}=\begin{cases}\mathrm{value}(i,j)&(i,j)\in S\\0&(i,j)\notin S\end{cases}')],check=('A stored cell becomes zero. What must change before its storage is recycled?',['Only its row link','Both its row and column routes must bypass it','Only its displayed value'],1,'One shared cell participates in two routes; leaving either route attached creates a stale reference.'),help=('Use a 2×2 grid with diagonal entries. Add a single off-diagonal cell, then cancel it exactly.','Two crossing routes reach the same circle, so insertion and removal have two structural obligations.',('A row traversal and a column traversal reach (1,1). How many cell objects should represent that entry?',['Two','One','One per traversal'],1,'Both routes designate the same stored cell identity.'))),
105:dict(scope='Exact rational source-convention pivot transform with fill-in and cancellation, verified against PDF page 482; structural semantic model rather than full Algorithm S pointer choreography.',passages=[
('Name the pivot convention before calculating','Several operations are called pivoting. This lesson follows the source’s displayed transform, not ordinary Gaussian elimination: a pivot a becomes 1/a; other pivot-row entries b become b/a; other pivot-column entries c become −c/a; a remaining entry d becomes d−bc/a. Require a≠0. All b,c,d on the right refer to the old matrix. The sign on the column and reciprocal pivot are essential. All calculations here use exact fractions.',r'\begin{pmatrix}a&b\\c&d\end{pmatrix}\longmapsto\begin{pmatrix}1/a&b/a\\-c/a&d-bc/a\end{pmatrix},\quad a\ne0'),
('Preserve operands until their last use','Let A be the original matrix and B the changing output matrix. The pivot is at row p and column q, so a=A[p,q]. For target (i,j), b=A[p,j] is in the old pivot row, c=A[i,q] is in the old pivot column, and d=A[i,j] is its old value. A missing sparse cell has value zero; it is not an unknown input. First normalize the pivot row. To update another row, retain its original pivot-column value c until every off-column entry d has received its correction −c(b/a). Only then replace c by −c/a. Using the newly scaled c too early would divide by a twice and introduce the wrong sign. Our model explicitly keeps an immutable old matrix as an oracle-friendly implementation; the source’s sparse algorithm economizes storage by ordering updates carefully. Frames show partial transformation states, not matrices that already satisfy every final pivot equation.',r'B_{ij}=A_{ij}-\frac{A_{iq}A_{pj}}{A_{pq}}\quad(i\ne p,\ j\ne q)'),
('Arithmetic determines the new support','An old zero d can become nonzero when both crossing operands are nonzero; this is fill-in and requires a new sparse cell. A nonzero d can become exactly zero and require deletion from both routes. The main example contains both: 2−1·4/2 cancels one cell, while 0−3·4/2 creates −6 at another. After each semantic cell update, row and column routes are regenerated and their shared identities checked. This validates structural outcomes, while deliberately not claiming to animate every predecessor-pointer step of Algorithm S.',r'd=0,\ bc\ne0\Rightarrow d-bc/a\ne0'),
('Exactness and numerical stability are different questions','Fractions preserve exact cancellation, so equality to zero is decisive here. Floating-point implementations must address rounding, small pivots, and an explicit sparsity policy; substituting a tolerance is an algorithmic choice with consequences. A zero pivot is rejected before any mutation. Independent tests evaluate the four-case formula directly on small matrices and compare every final entry, including negative and fractional pivots. Those tests establish evidence for this implementation, not numerical stability of a larger solver or correctness of an entire matrix-inversion procedure.',r'B_{pq}=1/A_{pq},\quad B_{pj}=A_{pj}/A_{pq},\quad B_{iq}=-A_{iq}/A_{pq}')],check=('Under this convention, pivot [[3,6],[2,4]] at its upper-left entry. What is the lower-right result?',['0','4','8'],0,'d−bc/a = 4−(6·2)/3 = 0, so the lower-right sparse cell is removed.'),help=('Use [[2,2],[1,0]]. Its one off-pivot update creates −1 from an absent zero cell.','The crossing row and column supply the two factors; the reciprocal and negative-column rules complete this specific transform.',('For [[2,2],[1,0]], what becomes of the lower-left pivot-column entry?',['1/2','−1/2','0'],1,'The source convention sends c to −c/a, so 1 becomes −1/2.')))
}

def check(q):
    prompt,choices,correct,explanation=q
    return dict(prompt=prompt,choices=choices,correctIndex=correct,explanation=explanation)

def calculated_checks(order,trace):
    first=trace[0]['data'];last=trace[-1]['data'];# All answers below come from inputs or invariant predicates.
    def number(prompt,value,explanation):
        choices=[str(value+1),str(value),str(value-1)]
        return (prompt,choices,1,explanation)
    if order==88:
        return [number('How many distinct node identities exist before relocation?',len(first['addresses']),'Count identities, even when every value is 7.'),number('After relocating B, what concrete address does A’s successor pointer contain?',trace[1]['data']['pointers']['A'],'The abstract target B is unchanged; its address encoding must follow the relocation.'),number('After the final field update, what value belongs to B?',last['values']['B'],'This is a value-field change; neither B’s identity nor its address changes.')]
    if order==89:
        n=len(first['ids']);return [number('How many data-node reads does the direct array query use?',1,'This cost model counts visited data nodes, not arithmetic or cache misses.'),number('How many data-node reads does the head-only linked query use?',n,'The target is the last node, so every preceding node must be visited.'),('Which extra assumption makes linked insertion after a node constant-time?',['The predecessor is already known and a new node is available','The values are sorted','All nodes have equal values'],0,'Locating a predecessor or obtaining storage can add costs excluded from the constant-size splice.')]
    if order==90:
        removed=next(s['data']['removed'] for s in trace if s['action']=='remove');return [('Which token does this stack release first?',list('ABC'),list('ABC').index(removed['stack'][0]),'The latest surviving insertion leaves the chosen active end.'),('Which token does this queue release first?',list('ABC'),0,'A entered first, so FIFO removes A first.'),('Which structure in the displayed interfaces may insert Z at the left?',['Only the unrestricted deque','All three','Only the stack'],0,'The interfaces fix the stack’s active right end and the queue’s insertion right end.')]
    if order==91:
        q=[s for s in trace if s['data']['policy']=='queue'][-1]['data']['emitted'];st=[s for s in trace if s['data']['policy']=='stack'][-1]['data']['emitted']
        return [('What is the third queue-visited identity?',list('BCD'),list('BCD').index(q[2]),'The queue processes pending siblings before their newly discovered descendants.'),('What is the third stack-visited identity?',list('BCD'),list('BCD').index(st[2]),'Reversed child pushes preserve left-first order while the stack pursues the newest pending task.'),number('How many distinct vertices does either completed run visit?',len(first['adj']),'The two policies change order, not the reachable identity set in this finite tree.')]
    if order==92:
        return [number('With base 100 and stride 3, what is slot 1’s starting address?',103,'The address rule is base + stride × index.'),number('At T equal to capacity, how many additional pushes fit without a pop?',0,'The next free index would be outside the allocated domain.'),('Does a rejected underflow change T?',['No','Yes, it becomes −1','Yes, it becomes capacity'],0,'Bounds are checked before mutation or reading an invalid slot.')]
    if order==93:
        m=len(first['cells']);return [number('What count denotes a full buffer in this all-slots model?',m,'Explicit count allows all M cells to hold data.'),number(f'What index follows index {m-1} when advancing modulo {m}?',0,'The circular successor wraps at the physical end of the array.'),('If h=t, which extra value distinguishes empty from full?',['The count','The alphabetic first token','The cell color alone'],0,'Count 0 means empty and count M means full; equal indices by themselves are ambiguous.')]
    if order==94:
        m=len(first['cells']);return [number('How many shared gap cells exist initially?',m,'L=0 and R=M initially, so R−L=M.'),number('How many gap cells remain when L=R?',0,'Meeting boundaries mean the allocated regions cover the entire area.'),('Why must an overlapping move to higher addresses copy backward?',['To preserve unread source values','To sort the records','To turn addresses into pointers'],0,'A forward copy would overwrite a later source cell before its value is read.')]
    if order==95:
        n=len(first['universe']);return [number('How many slots belong to the pool throughout this trace?',n,'Allocation changes ownership, not the finite universe of slots.'),('Immediately after detaching AVAIL, who owns the uninitialized slot?',['The operation’s reserved set','Both live and free lists','Nobody'],0,'Reserved ownership maintains the disjoint conservation invariant between allocator and publication steps.'),('When an address is reused for M, is a stale pointer to its previous object valid?',['No','Yes, the number is equal','Yes, unless M is zero'],0,'A new object lifetime does not revive references to the retired object.')]
    if order==96:
        return [('After removing the only node, which endpoints become null?',['Both head and tail','Only head','Only tail'],0,'The nonsentinel empty convention requires both endpoints to be null.'),('What successor must a newly appended tail have?',['Null','The old head','Itself'],0,'The queue’s forward chain must terminate at its tail.'),('What does a linked stack need for endpoint access?',['Only a top pointer','A full-array scan','A separate pointer to every node'],0,'Both push and pop use the same head end of the linked chain.')]
    if order==97:
        initial=trace[0]['data'];return [number('How many vertices are initially ready in the acyclic example?',len(initial['ready']),'Ready means incoming count zero, not simply small outdegree.'),('What changes when an emitted vertex has an edge to v?',['v’s residual incoming count decreases by one','v’s outgoing count increases','v must be emitted immediately even if its count remains positive'],0,'The removed predecessor no longer contributes to c(v); only a transition to zero makes v ready.'),('What is demonstrated by the final '+ '→'.join(trace[-1]['data']['cycle'])+' witness?',['No topological order exists for that graph','Every graph has only one order','Residual vertices are always isolated'],0,'Following the directed cycle would require a vertex to occur before itself.')]
    if order==98:
        return [('What is the stopping identity for this ring traversal?',['H','Any node with a repeated value','Null'],0,'H is the sentinel, and circular links do not use null as their normal terminator.'),number('How many new data identities are added by the final Y,Z transfer?',2,'The transferred chain consists of two distinct nodes; values are not copied into old nodes.'),('Does a known sentinel alone guarantee constant-time access to the last node?',['No','Yes','Only when values are sorted'],0,'A singly linked ring still needs a tail pointer or predecessor scan.')]
    if order==99:
        a=dict(first['left']);b=dict(first['right']);highest=max(a)+max(b);return [number('How many distinct powers can a canonical term node represent?',1,'Each node carries one exponent and its nonzero coefficient.'),number('What is the largest possible exponent among pairwise products of these input terms?',highest,'Exponents add; the leading nonzero coefficients have a nonzero product over integers.'),('When two product pairs yield the same exponent, what happens?',['Their coefficient contributions add','The later pair overwrites the first','Two permanent duplicate exponent nodes are created'],0,'Multiplication accumulates all contributions to each power, then removes exact zeros.')]
    if order==100:
        return [number('How many fields are assigned when inserting X between two known neighbors?',4,'The two private X links and the two neighbor links must all be set.'),('After only the first neighbor publication, what is the scene’s status?',['Protected intermediate','A fully reciprocal committed list','An empty list'],0,'The reverse neighbor field is not yet repaired, so ordinary traversal must not observe the half-update.'),number('How many neighbor bypass fields are changed when removing known X?',2,'The predecessor’s next and successor’s prev bypass X; reclamation remains a separate obligation.')]
    if order==101:
        return [number('What is the first event time in this input?',first['events'][0][0],'The clock jumps directly to the least scheduled event time.'),('For equal timestamps, which key component is compared next?',['Priority','Job label length','Service duration'],0,'The specified order is (time, priority, serial).'),number('What exact waiting-time area is accumulated by the completed trace?',last['area'],'Sum pre-event queue length times elapsed time; equivalently sum each job’s waiting time.')]
    if order==102:
        return [number('How many entities initially have both memberships?',len(first['entities']),'Every initial job belongs to the waiting line and owns one timeout record.'),number('How many timeout records are explicitly canceled when A begins service?',len(last['canceled']),'Only timeout-A is canceled; other event identities remain live.'),('Can a canceled event appear in the fired set under this model?',['No','Yes, if its time arrives','Yes, if another event has the same time'],0,'Cancellation’s postcondition excludes the exact canceled identity from every future firing.')]
    if order==103:
        R,C=first['rows'],first['cols'];return [number('How many storage offsets does the rectangular example require?',R*C,'A rectangular R×C domain contains exactly RC cells.'),number('How much does increasing the row index by one change a row-major offset?',C,'A complete row contains C elements, so the row stride is C.'),number('How much does increasing the column index by one change a column-major offset?',R,'A complete column contains R elements, so the column stride is R.')]
    if order==104:
        return [number('How many cell identities represent one stored coordinate?',1,'Row and column routes share the same object.'),number('How many routes must be repaired when a cell is inserted or deleted?',2,'The cell participates in one row list and one column list.'),('How are repeated contributions at an existing coordinate represented?',['Add to the existing value and remove on exact zero','Create a duplicate coordinate','Discard the new contribution'],0,'Canonical sparse storage has at most one cell per coordinate.')]
    if order==105:
        A=first['original'];a=Fraction(A[0][0]);b=Fraction(A[0][1]);c=Fraction(A[1][0]);v=Fraction(A[1][1])-b*c/a
        return [('What is the new pivot value for a='+str(a)+'?', [str(1/a),str(a),str(-1/a)],0,'This convention sends the pivot to its reciprocal, not to 1.'),('What is the new entry at (1,1) in this example?', [str(v+1),str(v),str(v-1)],1,'Use the old matrix operands in d−bc/a.'),('When may a zero pivot be accepted?',['Never under this transform','When the row has another nonzero','Whenever sparse storage is used'],0,'All four update cases divide by the pivot, so zero must be rejected before any mutation.')]
    raise AssertionError(order)

# Focus windows correspond to the four authored claims; no passage replays an unchanged full trace.
def windows(order,trace):
    n=len(trace)
    if order==88:return [[0,1],[0,1,2],[1,2],[0,2]]
    if order==89:
        return [[0,1],[1,2,3] if n>3 else [1,2],[max(0,n-2),n-1],[0,n-1]]
    if order==91:
        q=next(i for i,s in enumerate(trace) if s['action']=='start-queue')
        return [[0,1],[2,min(3,q-1),q+1,min(q+2,n-1)],[q,min(q+1,n-1),n-1],[q-1,n-1]]
    if order==94:
        k=next(i for i,s in enumerate(trace) if s['action']=='plan-overlap')
        return [[0,1],list(range(1,min(k,5))),list(range(k,n)),[0,k-1]]
    if order==95:
        return [[0,1],[0,1,2,3,4],[4,5,6,7,8],[0,n-2,n-1]]
    if order==97:
        return [[0,1],[1,2,min(3,n-3)],[n-2,n-1],[0,n-3]]
    if order==99:
        k=next(i for i,s in enumerate(trace) if s['action']=='start-product')
        return [[0,1],[0]+list(range(1,k)),list(range(k,n)),[k-1,n-1]]
    if order==100:return [[0,1],[1,2,3],[3,4,5],[0,2,3,4,5]]
    if order==103:return [list(range(6)),[4,5,7],[8,9],[4,6,7]]
    if order==105:return [[0,1,2],list(range(1,min(n,5))),list(range(2,n)),[0,n-1]]
    return [[0,1],list(range(1,min(n,5))),list(range(max(0,n-3),n)),[0,n-1]]

def focus_nodes(nodes,order,focus):
    for node in nodes:
        id=node['id']
        if focus==0 and any(s in id for s in ['node-','entity-','slot-','vertex-','cell-']):node['role']='active' if node.get('role')!='error' else 'error'
        if focus==1 and any(s in id for s in ['next-','prev-','pointer','cursor','edge-','wrap-','rail','pair-']):node['role']='active'
        if focus==2 and any(s in id for s in ['result','retired','gap','count','area','output','phase','field-']):node['role']='active' if node.get('role')!='error' else 'error'
        if focus==3 and node.get('type')=='text' and node.get('result'):node['role']='result'

def states_for(order,trace,indices,prefix,focus):
    result=[]
    for k,i in enumerate(dict.fromkeys(indices)):
        s=trace[i];diagram,formula=scene(order,s);focus_nodes(diagram['nodes'],order,focus)
        result.append(dict(id=f'{prefix}-{i}',caption=s['caption'],formula=formula,diagram=diagram,evidence=s['data'],traceIndex=i,operation=s['action']))
    # Deleted nodes retain identity with zero opacity; private nodes appear without borrowing another example.
    allnodes={node['id']:node for st in result for node in st['diagram']['nodes']}
    for st in result:
        present={node['id'] for node in st['diagram']['nodes']}
        for id,node in allnodes.items():
            if id not in present:st['diagram']['nodes'].append({**copy.deepcopy(node),'opacity':0})
    return result

PAGES={88:'377–382',89:'377–382',90:'385–391',91:'385–391',92:'394–396',93:'395–396',94:'396–407',95:'408–413',96:'413–417',97:'418–429',98:'436–440',99:'440–445',100:'446–449',101:'449–472',102:'449–472',103:'475–477',104:'478–482',105:'482–485'}
KINDS={88:'identity-address-relocation',89:'representation-access-cost',90:'end-operation-semantics',91:'pending-work-scheduling',92:'checked-array-stack',93:'counted-circular-buffer',94:'opposing-stack-ownership',95:'free-list-conservation',96:'linked-queue-endpoints',97:'incoming-count-topological-sort',98:'sentinel-ring-splicing',99:'sparse-polynomial-arithmetic',100:'protected-doubly-linked-updates',101:'ordered-discrete-event-calendar',102:'independent-list-memberships',103:'array-index-bijections',104:'orthogonal-shared-cell-routes',105:'exact-source-pivot-transform'}

def aligned_checks(order,trace,small=False):
    def q(main,help,choices,index,reason):return (help if small else main,choices,index,reason)
    Q={
88:[
q('Two parcels both store 7. What can you conclude about their identities?','A and B both say 7. Must they be the same parcel?',['They must be the same object','They may still be distinct objects','Their addresses must agree'],1,'A field value is separate from the identity of the object that owns it.'),
q('A successor field stores 27 and addr(B)=27. What does the pointer encode?','A’s link contains B’s shelf number. What is that number?',['B’s value','B’s address','A’s lifetime'],1,'A concrete pointer encodes the address of the destination, not its stored value.'),
q('B moves from address 27 to 63 while remaining A’s successor. What must A store afterward?','Move B to shelf 63. Where must A’s link point?',['27','63','B’s current data value'],1,'Relocation preserves the abstract target but changes its concrete address encoding.'),
q('A retired object’s address is reused. Does a numerically valid old pointer establish the same object lifetime?','A new parcel uses an old parcel’s shelf. Is the old reference automatically valid?',['Yes, equal address proves equal lifetime','No, the original object lifetime ended','Yes, when labels match'],1,'Address reuse creates a new lifetime; target existence alone does not establish a valid reference.')],
89:[
q('Before choosing array or links, which information is most useful?','What should we ask before choosing a shelf or chain?',['Which operations dominate the workload','Which drawing looks shorter','Whether labels are alphabetic'],0,'The representation choice depends on the operations and constraints the program actually needs.'),
q('A head-only chain accesses zero-based index 4. How many data nodes are visited under this cost convention?','A head-only chain accesses its fifth card. How many cards are visited?',['1','4','5'],2,'The chain visits indices 0 through 4; this counter counts data nodes, not total machine instructions.'),
q('What precondition makes a linked splice after a node constant-size work?','What must be known before a quick insertion beside a linked card?',['Its predecessor position is already known and a fresh node is available','Only the new value is known','The whole chain is sorted'],0,'Finding the location and obtaining storage are separate costs from the fixed number of link changes.'),
q('Does one access-count trace prove that arrays are fastest for every workload?','Does this one lookup decide every future layout choice?',['Yes','No; its cost assumptions and operation are specific','Only if the last label is E'],1,'A finite example illustrates the stated model; it cannot establish a universal engineering preference.')],
90:[
q('Which pair of end operations defines the queue interface used here?','Where does a waiting line admit and release tokens?',['Insert right, remove left','Insert right, remove right','Insert anywhere, remove anywhere'],0,'The queue’s FIFO interface uses opposite insertion and removal ends.'),
q('After A,B are inserted in that order, which token leaves a right-end stack first?','Put A then B on a plate stack. Which leaves first?',['A','B','Either without a choice'],1,'The stack removes its most recent surviving insertion.'),
q('What does this contract require when removal is requested on an empty structure?','What happens if there is no token to remove?',['Report underflow and preserve the structure','Invent a zero-valued token','Move an endpoint past its valid domain'],0,'An unsuccessful empty removal is explicitly distinguished from returning a legitimate value.'),
q('What is the induction step behind the FIFO law?','Why does taking the first token preserve the waiting order?',['Removal keeps the other tokens’ relative order','Removal sorts values','New tokens move to the front'],0,'Removing the oldest token leaves all other surviving insertions in their original order.')],
91:[
q('What data structure determines which discovered task is deferred longest?','What chooses which pending task comes next?',['The pending container’s selection rule','The vertex label spelling','The physical edge length'],0,'Stack and queue policies select different endpoints of the same notion of pending work.'),
q('A has children B,C and B has child D. Which queued task follows B?','B is processed while C waits; D is discovered. Who goes next in a queue?',['C','D','A'],0,'C entered the pending queue before D, so the frontier explains the breadth-first choice.'),
q('Two parents discover the same graph vertex before either copy is processed. When should it be marked to avoid duplicate scheduling?','When should a task be marked so a second parent cannot schedule it again?',['When first scheduled','Only after it finishes','Only when its value changes'],0,'Marking on discovery prevents multiple pending copies of the same identity.'),
q('Which property does queue-based unweighted search guarantee under the stated discovery rule?','How do visited distances change in the breadth-first run?',['They never decrease','They strictly increase at every vertex','They equal stack depths in every graph'],0,'Queue processing completes earlier distance layers before later ones; siblings may have equal distances.')],
92:[
q('With base 40 and stride 4, where does slot 3 start?','Four address units per slot: what is 40+4·3?',['43','52','60'],1,'Sequential addressing uses base plus stride times the zero-based slot index.'),
q('When T=2 in a capacity-4 stack, which slot receives the next successful push?','Two slots are occupied from index 0. Which is next free?',['Index 1','Index 2','Index 3'],1,'T is both the occupied count and the first unused index.'),
q('At T=0, when must a pop reject underflow?','Should we read slot −1 before reporting an empty stack?',['Before decrementing T or reading storage','After reading slot −1','Only after returning a value'],0,'The bounds check protects the invalid access; an error after the access is too late.'),
q('Which memory sequence does the prefix invariant interpret as the abstract stack?','Which cells count as the stack’s data?',['A[0] through A[T−1]','All allocated cells including unused ones','A[T] alone'],0,'The representation map uses exactly the occupied prefix, connecting updates to LIFO behavior.')],
93:[
q('In a capacity-5 circular buffer, which index follows 4?','Which shelf comes after the last shelf in the ring?',['0','5','3'],0,'Index advancement is modulo capacity, so the physical endpoint wraps to zero.'),
q('In the counted all-slots convention, h=t and count=M means what?','Equal endpoints with every slot occupied means what?',['Empty','Full','Invalid solely because endpoints agree'],1,'Explicit count distinguishes full from empty even when the two indices are equal.'),
q('During dequeue, which index names the token to read before advancing?','Which pointer marks the next token to leave?',['The old head','The new tail','An arbitrary occupied slot'],0,'FIFO removal reads the oldest token at the current head, then advances that endpoint.'),
q('Why does enqueue at t append to the logical FIFO sequence?','Why is the tail the right place for the new token?',['t≡h+count identifies the first position after the logical sequence','Physical index t is always largest','Every occupied cell is shifted first'],0,'The representation map and congruence put the insertion immediately after the current logical last token.')],
94:[
q('With capacity 8, L=3 and R=6, how many cells belong to shared slack?','How many indices are in the gap [3,6)?',['2','3','5'],1,'The half-open shared gap has length R−L, independent of either stack’s imbalance.'),
q('What condition blocks either opposing-stack push?','When do the two growing ends have no room left?',['L=R','L=0','R=M'],0,'Meeting boundaries leave an empty shared gap; any further push would overwrite an owner.'),
q('An overlapping block moves one position right. Which source end should be copied first?','To shift cards right without a spare copy, start at which end?',['The high-address end','The low-address end','Either end without a check'],0,'Backward copying preserves source cells that would otherwise be overwritten before being read.'),
q('What does a successful opposing-stack push transfer in the ownership proof?','What changes hands when one token is pushed?',['Exactly one unused gap cell','Every cell in both stacks','No storage ownership'],0,'A legal push moves one boundary by one and preserves the disjoint three-interval partition.')],
95:[
q('What is AVAIL in the fixed-size pool model?','What does the free-list head point to?',['The first unused slot','The last live data value','A count of matrix rows'],0,'Unused slots form their own chain; AVAIL identifies its first slot, not a data value.'),
q('After a free slot is detached but before publication, which ownership set contains it?','Who owns a newly reserved, uninitialized slot?',['Reserved','Both live and free','No set'],0,'The reserved set accounts for the in-progress operation without losing or double-owning storage.'),
q('When may a deleted data node be recycled?','What must happen before a retired slot returns to AVAIL?',['After its live ownership routes have been removed','Before unlinking so allocation is faster','Whenever its value happens to be zero'],0,'Recycling must not leave a live structure reaching a slot the allocator can reuse.'),
q('Which pair of failures does the pool partition detect?','What goes wrong if a slot is missing or counted twice?',['Lost slots and duplicate ownership','Only sortedness errors','Only arithmetic overflow'],0,'Coverage accounts for every slot; disjointness forbids double allocation or double free.')],
96:[
q('What additional endpoint allows enqueue without traversing a singly linked queue?','Which saved pointer avoids walking to the last card?',['Tail','A pointer to every value','A second head with the same meaning'],0,'A tail names the last node directly while the head supports front removal.'),
q('After removing the only node of a nonsentinel queue, what are the endpoints?','The last waiting card leaves. What becomes null?',['Both head and tail','Only head','Only tail'],0,'Empty and nonempty boundary transitions must preserve head-null iff tail-null.'),
q('In a dummy-header queue, what can tail equal when no data remain?','Can an empty sentinel queue still have its header node?',['The header itself','Only a retired data node','No pointer can exist'],0,'The sentinel is administrative storage; tail may designate it while the data sequence is empty.'),
q('Why are matching head/tail empty tests insufficient to prove the whole queue correct?','Could a middle link be wrong even with sensible endpoints?',['A middle cycle or lost node can still violate the chain','Endpoint tests already prove all links','Equal values force the chain to be correct'],0,'The full invariant reconstructs the complete successor walk, not only its endpoint values.')],
97:[
q('For every precedence edge U→V, what must a topological order satisfy?','If U must happen before V, where must U appear?',['Before V','After V','At the same index as V'],0,'The position map must strictly respect each directed precedence constraint.'),
q('What exactly does incoming count c(v) count after some vertices have been emitted?','Do counts include predecessors that already left the graph?',['Only incoming edges from remaining vertices','All original incoming edges forever','Outgoing edges to already emitted vertices'],0,'The maintained count describes the residual problem and decreases as predecessors are removed.'),
q('The ready queue is empty but vertices remain. What does a repeated predecessor walk produce?','Following predecessors forever in a finite leftover graph must find what?',['A directed cycle witness','A sorted list with no edges','Proof that every leftover vertex lies on one cycle'],0,'A repeated vertex supplies an actual cycle; other leftovers may merely depend on it.'),
q('Why is adjacency-list topological sorting O(|V|+|E|)?','How often is each edge used to decrease an incoming count?',['Once per edge, with constant queue work per vertex','Once for every possible vertex ordering','Once per pair of vertices whether adjacent or not'],0,'The cost charges each emitted vertex and each outgoing edge a constant number of operations.')],
98:[
q('What is the empty-data representation in a sentinel ring?','Where does H point when there are no data cards?',['H.next=H','H.next is an arbitrary data value','H must be deallocated'],0,'The sentinel remains present and closes the empty ring directly onto itself.'),
q('Which condition ends one traversal of this sentinel ring?','When should the cursor stop after following the links?',['The cursor returns to H by identity','A value equals an earlier value','A normal null link appears'],0,'Circular traversal stops at its designated sentinel, not at null or a possibly repeated value.'),
q('To insert X after A, which link should be prepared before publishing A.next=X?','What must X point to before A points to X?',['A’s former successor','X’s own value','An unrelated free-list head'],0,'Initializing X’s successor first preserves the rest of the live ring during publication.'),
q('Does a singly linked ring with only H stored necessarily provide constant-time last-node access?','Does keeping H also tell us its predecessor immediately?',['No; a tail pointer or scan is still needed','Yes, circularity supplies every predecessor','Yes, if values are equal'],0,'A sentinel simplifies stopping and empty cases without creating a reverse link or saved tail.')],
99:[
q('What makes a sparse polynomial representation canonical here?','How many nonzero nodes may use one exponent?',['Exactly one per stored exponent, in decreasing order','Arbitrarily many duplicate exponent nodes','A required stored zero coefficient'],0,'Canonical form combines equal powers and omits zero coefficients.'),
q('When an addition merge sees equal exponents with coefficients 5 and −5, what should it emit?','Equal powers have opposite coefficients. What remains?',['No term for that exponent','Two nodes preserving the inputs','One required zero-valued node'],0,'Consume both input terms, add their coefficients, and omit the exact zero result.'),
q('Why is the grid of pairwise products not yet the final canonical product?','Can two different term pairs land on the same power?',['Yes; their coefficients must accumulate at that exponent','No; every pair has a unique exponent','The later contribution must overwrite the earlier one'],0,'Different exponent pairs can have the same sum, so all their coefficients must be combined.'),
q('Why does exact integer arithmetic make sparse zero deletion unambiguous?','What test decides whether an integer-coefficient term disappears?',['Exact coefficient equality to zero','Whether its printed decimal looks small','Whether its exponent is largest'],0,'Exact coefficients have a decisive zero test; approximate coefficients require an additional numerical policy.')],
100:[
q('Which equation expresses forward/backward neighbor reciprocity?','Following next then prev should return where?',['prev(next(v))=v','prev(next(v))=null for every node','next(v)=v for every data node'],0,'The adjacent backward field must return to the same node identity.'),
q('After X’s private links and A.next are set, but B.prev is stale, may ordinary observers assume insertion is complete?','Is one repaired neighbor direction enough to finish insertion?',['No; the protected update is incomplete','Yes; private links alone finish it','Only if X has value zero'],0,'Insertion sets four fields; a half-published relationship does not yet satisfy reciprocity.'),
q('Before retiring X between A and B, which neighbor links must bypass it?','Which two directions must go around the removed card?',['A.next=B and B.prev=A','Only A.next=B','Only X’s own fields'],0,'Both live directions must bypass X before its storage can be reclaimed under the ownership rules.'),
q('At which displayed states does this model promise the reciprocal invariant?','Do protected half-write frames claim to be valid public lists?',['At committed operation boundaries','After every individual assignment without protection','Only after the program exits'],0,'The model explicitly suspends reciprocity during protected intermediates and restores it before publication completes.')],
101:[
q('When can an event simulation skip clock ticks without missing a modeled change?','Why can the clock jump to the next appointment?',['The modeled state stays constant until the next event','Real time has stopped','The queue is always empty'],0,'Event-driven simulation advances between scheduled state changes under its explicit model assumptions.'),
q('Which rule decides two events with equal times in this workshop?','What breaks a tie before the serial number is used?',['Priority, then serial','Job value, then queue length','Whichever arrow happens to animate first'],0,'The lexicographic (time,priority,serial) key makes the event order deterministic.'),
q('Two jobs wait from time 3 until time 7. How much waiting-time area belongs to that interval?','What is 2 waiting jobs × 4 time units?',['4','8','14'],1,'Use the queue length before the event across the half-open interval, giving 2·(7−3)=8.'),
q('Which stated assumption excludes an endless chain of zero-duration services in this example?','What is required of every service duration?',['It is strictly positive','It may be negative','It depends on label spelling'],0,'Positive service durations and finitely many arrivals exclude the demonstrated model’s zero-time infinite cascade.')],
102:[
q('Why does an entity in two intrusive lists need separate link fields?','Can one next field simultaneously describe two independent rails?',['Each membership has its own successor relationship','Duplicate fields create duplicate entity identities','A timestamp automatically acts as both links'],0,'The same entity can have distinct neighbors in the two structures; one field cannot encode both independent routes.'),
q('A job leaves the waiting line to begin service. Is its timeout automatically removed?','Does deleting the upper connector also erase the lower one?',['No; the calendar must be updated explicitly','Yes; all memberships are identical','Only if its label is A'],0,'Leaving one data structure does not perform a separate calendar mutation.'),
q('Two timeout events share time 8. Which identifier should cancel only J’s timeout?','How do we avoid canceling another job’s equal-time event?',['J’s exact timeout event identity','The time 8 alone','The first event with any label'],0,'Cancellation applies to one event identity; equal timestamps do not make two records interchangeable.'),
q('What must be settled before retiring an entity that participates in several structures?','May a job be freed while a future event still owns a reference?',['Every live membership and event ownership must be removed or made safe','Only its first membership matters','Equal labels remove the need for ownership checks'],0,'A system boundary must coordinate all ownership routes, or a later event can reach retired storage.')],
103:[
q('For a 3×4 array with lower bounds (−1,2), what is the row-major offset of (1,4)?','Subtract the bounds: row offset 2 and column offset 2, with row length 4. What is 2·4+2?',['6','8','10'],2,'Subtract lower bounds before applying the row-major stride formula.'),
q('When switching a cell from row-major to column-major storage, what stays the same?','Does folding by columns change the cell’s coordinate identity?',['The cell’s coordinates and identity','Its physical offset must always stay fixed','Its row value becomes its column value'],0,'The layout changes the coordinate-to-address map, not which logical cell is represented.'),
q('What is the packed lower-triangle offset of (3,1)?','Rows before row 3 contain 1+2+3 cells. Add column 1: what offset results?',['4','7','10'],1,'The offset is 3·4/2+1=7; unequal row lengths require triangular numbers.'),
q('In row-major storage with 4 columns, which zero-based coordinates correspond to offset 11?','Divide 11 by 4: which quotient/remainder give the row and column?',['(2,3)','(3,2)','(1,1)'],0,'Quotient floor(11/4)=2 is the row; remainder 3 is the column, before adding any lower bounds.')],
104:[
q('A row walk and a column walk reach the same nonzero coordinate. How many cell objects should that entry have?','Do the two routes meet one circle or two copies?',['One shared cell identity','Two independent values','One object for every visit'],0,'Orthogonal routes reference one stored matrix entry, preventing divergent row and column copies.'),
q('What must insertion at a previously absent coordinate update?','A new circle needs connections to which routes?',['Its row and its column routes','Only its row','Only the value array'],0,'The new cell belongs to both sorted dimensions and must be reachable from both.'),
q('An added contribution cancels an existing cell exactly. What structural change follows?','A stored value becomes zero. What happens to its circle?',['Remove it from both routes','Leave a zero node permanently','Create a duplicate coordinate'],0,'Canonical sparse form omits zero entries and requires both routes to bypass the retired cell.'),
q('How does the independent dense reconstruction interpret an absent coordinate?','What value fills a grid position with no sparse cell?',['Zero','An unspecified previous value','The nearest stored value'],0,'The sparse representation contract gives absent coordinates exact value zero, enabling a dense semantic oracle.')],
105:[
q('Under the source convention, what becomes of a nonzero pivot a?','Does this operation replace a by 1 or by its reciprocal?',['1/a','Always 1','Always 0'],0,'This is the source’s reciprocal-pivot transform, not ordinary Gaussian row normalization.'),
q('Why retain the original pivot-column value c until all other entries in its row are updated?','May we replace c by −c/a before using c in d−bc/a without adjusting the formula?',['No; using the scaled value would change sign and divide by a again','Yes; c never enters the off-column update','Yes; any nonzero substitute works'],0,'The right-hand-side operands refer to the old matrix; premature overwriting changes the calculation.'),
q('If d=0 but b and c are nonzero and a≠0, what happens at that off-pivot coordinate?','A formerly absent zero gets the nonzero correction −bc/a. What is needed?',['A new sparse cell: fill-in','No change because old zeros are ignored','Deletion of the pivot'],0,'The exact new value is nonzero, so the support grows and both routes must include a new cell.'),
q('Do exact Fraction tests establish floating-point stability for a larger solver?','Does exact cancellation here prove rounded arithmetic will behave identically?',['No; rounding and pivot conditioning need separate analysis','Yes, all numerical issues disappear','Only if the diagram has few cells'],0,'Exact arithmetic verifies this algebraic transform; numerical stability is a distinct property of approximate computation.')]
    }
    return Q[order]


def mixed_radix_offset(indices,shape,lower=None):
    shape=tuple(shape);lower=tuple(lower if lower is not None else [0]*len(shape));indices=tuple(indices)
    if not shape or len(lower)!=len(shape) or len(indices)!=len(shape) or any(not isinstance(v,int) for v in lower+indices) or any(not isinstance(n,int) or n<=0 for n in shape):raise ValueError('positive integer dimensions and matching index/lower tuples required')
    digits=tuple(i-l for i,l in zip(indices,lower))
    if any(not isinstance(x,int) or not 0<=x<n for x,n in zip(digits,shape)):raise IndexError('index tuple outside half-open bounds')
    k=0
    for x,n in zip(digits,shape):k=k*n+x
    return k

def mixed_radix_inverse(k,shape,lower=None):
    shape=tuple(shape);lower=tuple(lower if lower is not None else [0]*len(shape))
    if not shape or len(lower)!=len(shape) or any(not isinstance(v,int) for v in lower) or any(not isinstance(n,int) or n<=0 for n in shape):raise ValueError('positive integer dimensions and matching lower tuple required')
    if not isinstance(k,int) or not 0<=k<math.prod(shape):raise IndexError('offset outside storage domain')
    digits=[0]*len(shape)
    for t in range(len(shape)-1,-1,-1):k,digits[t]=divmod(k,shape[t])
    assert k==0
    return tuple(x+l for x,l in zip(digits,lower))

def mixed_trace(small=False):
    shape=(1,2,2) if small else (2,2,3);lower=(0,0,0) if small else (2,-1,4);digits=(0,1,1) if small else (1,1,2)
    indices=tuple(x+l for x,l in zip(digits,lower));strides=tuple(math.prod(shape[t+1:]) for t in range(3));out=[];acc=0;recovered={}
    cells=[dict(digits=list(ds),indices=[x+l for x,l in zip(ds,lower)],offset=mixed_radix_offset([x+l for x,l in zip(ds,lower)],shape,lower)) for ds in itertools.product(*(range(n) for n in shape))]
    def f(action,caption,stage,axis=None,quotient=None,remainder=None):
        snap(out,action,caption,shape=shape,lower=lower,indices=indices,digits=digits,strides=strides,cells=cells,accumulator=acc,stage=stage,axis=axis,quotient=quotient,remainder=remainder,recovered=recovered,total=math.prod(shape))
    f('name-three-digits','Subtract each lower bound to obtain a plane digit, a row digit, and a slot digit.',0)
    for t in range(3):
        old=acc;acc=acc*shape[t]+digits[t]
        f('consume-'+str(t+1),f'Consume digit {t+1}: {old} × {shape[t]} + {digits[t]} = {acc}. Each remaining block has {strides[t]} slots.',t+1,t)
    assert acc==mixed_radix_offset(indices,shape,lower)
    q=acc
    for t in range(2,-1,-1):
        old=q;q,r=divmod(q,shape[t]);recovered[t]=r
        f('recover-'+str(t+1),f'Divide {old} by radix {shape[t]}: quotient {q}, remainder {r}; recover coordinate digit {t+1}.',6-t,t,q,r)
    assert tuple(recovered[t]+lower[t] for t in range(3))==indices and q==0
    f('verify-bijection','All three recovered digits match the selected cell; adding lower bounds recovers the original coordinates.',7)
    return out

def mixed_scene(st):
    d=st['data'];nodes=[];shape=d['shape'];stage=d['stage'];target=list(d['digits']);flattened=stage>=3
    # Plane containers hold actual row/slot positions before the same cells flatten.
    for a in range(shape[0]):
        x=85+a*310
        if not flattened:nodes.extend([box('plane-'+str(a),x-20,85,shape[2]*62+35,160,'muted'),txt('plane-title-'+str(a),x+(shape[2]-1)*31+27,65,'plane '+str(a+d['lower'][0])+' (digit '+str(a)+')','muted',15)])
    for cell in d['cells']:
        a,b,c=cell['digits'];k=cell['offset'];id=f'tensor-{a}-{b}-{c}'
        chosen=(cell['digits'][:stage]==target[:stage]) if stage in [1,2] else cell['digits']==target
        if stage in [4,5,6]:chosen=all(cell['digits'][int(t)]==v for t,v in d['recovered'].items())
        x=55+k*(600/d['total']) if flattened else 85+a*310+c*62;y=175 if flattened else 108+b*65;w=(600/d['total']-4) if flattened else 54
        nodes.extend([box(id,x,y,w,44,'active' if chosen else 'muted'),txt(id+'-value',x+w/2,y+27,str(k) if flattened else f'{b},{c}','active' if chosen else 'muted',14,result=stage==3)])
        if flattened:nodes.append(txt(id+'-coord',x+w/2,y+64,f'{a}{b}{c}','muted',14))
    nodes.append(txt('target-coordinates',355,285,'indices '+str(tuple(d['indices']))+' → digits '+str(tuple(target)),'input',16))
    if stage<=3:
        consumed=min(stage,3);remaining=math.prod(shape[consumed:]);offset=d['accumulator']*remaining
        nodes.append(txt('block-count',355,325,f'{d["accumulator"]} prefixes × {remaining} slots per block = {offset}','result',18,True))
        if stage>0:
            nodes.append(txt('stride-readout',355,365,f'axis {stage}: stride {d["strides"][stage-1]}','active',17))
        formula=r'k_{'+str(consumed)+r'}='+str(d['accumulator'])+r',\qquad\text{block start}='+str(offset)
    elif stage<7:
        t=d['axis'];nodes.append(txt('divmod',355,325,f'radix {shape[t]}: quotient {d["quotient"]}, remainder {d["remainder"]}','result',18,True))
        nodes.append(txt('recovered',355,365,'recovered: '+', '.join(f'd{int(t)+1}={v}' for t,v in sorted(d['recovered'].items())),'result',17,True))
        formula=r'\operatorname{divmod}(q,n_{'+str(t+1)+r'})=('+str(d['quotient'])+','+str(d['remainder'])+')'
    else:
        nodes.append(txt('verified',355,325,'offset '+str(d['accumulator'])+' ↔ '+str(tuple(d['indices'])),'result',20,True));nodes.append(txt('total',355,365,str(d['total'])+' cells ↔ offsets 0…'+str(d['total']-1),'result',18,True));formula=r'0\le k<\prod_{t=1}^{3}n_t='+str(d['total'])
    nodes.append(txt('mixed-action',355,415,st['action'].replace('-',' '),'muted',14))
    return dict(title='Planes, rows, slots, then inverse digits',description=st['caption'],viewBox=[0,0,720,440],nodes=nodes,invariant='Each positive radix fixes one digit range; the last axis varies fastest'),formula

def mixed_states(trace,prefix):
    states=[]
    for i,s in enumerate(trace):
        diagram,formula=mixed_scene(s);states.append(dict(id=prefix+'-'+str(i),caption=s['caption'],formula=formula,diagram=diagram,evidence=s['data'],traceIndex=i,operation=s['action']))
    allnodes={n['id']:n for s in states for n in s['diagram']['nodes']}
    for s in states:
        present={n['id'] for n in s['diagram']['nodes']}
        s['diagram']['nodes'].extend({**copy.deepcopy(n),'opacity':0} for id,n in allnodes.items() if id not in present)
    return states

def mixed_passage(lesson_id):
    id=lesson_id+'-p5';main=mixed_trace();help=mixed_trace(True);states=mixed_states(main,id);hs=mixed_states(help,id+'-help')
    title='An index tuple is a mixed-radix number'
    prose=('Let d≥1 be the number of axes, with positive integer lengths n₁,…,n_d. Coordinate i_t has the half-open domain ℓ_t≤i_t<ℓ_t+n_t. Subtract its lower bound to obtain digit δ_t=i_t−ℓ_t, so 0≤δ_t<n_t. In row-major order the last digit changes fastest. Increasing digit t by one skips every possible combination of later digits: its stride is the product of n_u for u>t. The empty product for the last axis equals 1. Summing each digit times its stride gives the offset k; a c-unit record at base b begins at b+ck. The source’s inclusive zero-based upper bounds d_t correspond to our lengths n_t=d_t+1.\n\n'
    'For shape 2×2×3, the strides are 6,3,1: one plane contains six slots and one row contains three. Our selected coordinates (3,0,6), with lower bounds (2,−1,4), become digits (1,1,2). They select one plane, then one row, then its third slot. The same calculation can be evaluated without building a stride table: start h₀=0 and set h_t=h_{t−1}n_t+δ_t. This trace computes 1, then 3, then offset 11, retaining the same cell identities while the planes flatten.\n\n'
    'Invert from the last axis backward. Repeated division with remainder by n_d,n_{d−1},…,n₁ recovers each digit; add its lower bound to recover the coordinate. Here divmod(11,3)=(3,2), divmod(3,2)=(1,1), and divmod(1,2)=(0,1). The unique remainder at each step proves uniqueness, while repeated quotient reduction recovers a valid tuple for every 0≤k<∏n_t. Thus the map is a bijection for arbitrary positive dimensions; exhaustive finite tests check the implementation rather than replace this argument. An axis of length 1 is valid and contributes only digit zero. Empty or invalid dimensions and out-of-range coordinates are rejected.')
    formula=r'k=\sum_{t=1}^{d}(i_t-\ell_t)\prod_{u=t+1}^{d}n_u,\qquad \ell_t\le i_t<\ell_t+n_t,\quad \prod_{u=d+1}^{d}n_u=1'
    transitions=[dict(**{'from':a['id']},to=b['id'],action=b['operation'],explanation=b['caption']) for a,b in zip(states,states[1:])]
    demo=dict(id=id+'-demo',title=title,model=dict(kind='general-row-major-mixed-radix',shape=[2,2,3],lower=[2,-1,4],arithmetic='Exact integers',computed=True,domain='d≥1; n_t positive integers; lower_t ≤ i_t < lower_t+n_t',authoringScript='scripts/fullbook-batch-D.py'),states=states,transitions=transitions,check=check(('A row-major array has shape 3×4×5. Holding the last two coordinates fixed, how much does increasing the first coordinate by one change the offset?',['5','20','60'],1,'The first-axis stride is the product of later lengths: 4×5=20. The full 60-cell product is the total storage size, not this stride.')),simplerHelp=dict(intro='Use one plane containing two rows of two slots. The first digit must be zero; only the row and slot choices remain.',model=dict(kind='general-row-major-mixed-radix',shape=[1,2,2],lower=[0,0,0],smallerExample=True,computed=True),states=hs,steps=[dict(action=s['operation'],text=s['caption']) for s in hs],connection='A plane groups rows and a row groups slots. Multiplying by the next radix converts the accumulated prefix into smaller units before adding the next digit.',check=check(('In shape 1×2×2, move from digits (0,0,1) to (0,1,1). How much does the offset increase?',['1','2','4'],1,'Only the row digit increases. Each row contains two slots, so its stride is 2, even though the whole array contains four cells.'))),accessibility=dict(reducedMotion='Use the same computed plane-to-shelf and divmod snapshots as discrete steps.',stateDescription='Read coordinate digits, prefix counts, current stride, quotient, and remainder.'))
    return dict(id=id,title=title,text=prose,formula=formula,demonstration=demo)

def build():
    plan=json.loads(PLAN.read_text());lessons=plan['lessons'] if isinstance(plan,dict) else plan;output=[]
    for item in lessons:
        order=item['order'];c=CONTENT[order];main=TRACES[order](False);help_trace=TRACES[order](True)
        main_windows=windows(order,main);help_windows=windows(order,help_trace)
        main_checks=aligned_checks(order,main);help_checks=aligned_checks(order,help_trace,True)
        passages=[]
        for p,(title,text,formula) in enumerate(c['passages']):
            id=f'{item["id"]}-p{p+1}';states=states_for(order,main,main_windows[p],id,p);help_states=states_for(order,help_trace,help_windows[p],id+'-help',p)
            transitions=[]
            for before,after in zip(states,states[1:]):
                skipped=after['traceIndex']!=before['traceIndex']+1
                transitions.append(dict(from_=before['id'],to=after['id'],action=('compare-computed-boundaries' if skipped else after['operation']),explanation=('Compare these computed boundary snapshots; omitted operations are not claimed to be one instruction. ' if skipped else '')+after['caption']))
            for t in transitions:t['from']=t.pop('from_')
            demo=dict(id=id+'-demo',title=title,model=dict(kind=KINDS[order],arithmetic='Exact integers and fractions; no approximate arithmetic.',focus=p+1,scope=c['scope'],traceLength=len(main),computed=True,authoringScript='scripts/fullbook-batch-D.py'),states=states,transitions=transitions,check=check(main_checks[p]),simplerHelp=dict(intro=c['help'][0]+' Focus: '+title.lower()+'.',model=dict(kind=KINDS[order],smallerExample=True,traceLength=len(help_trace),computed=True),states=help_states,steps=[dict(action=st['operation'],text=st['caption']) for st in help_states],connection=c['help'][1],check=check(help_checks[p])),accessibility=dict(reducedMotion='The same computed snapshots are available as discrete steps without interpolation.',stateDescription='Read the caption, formula, object labels, and invariant for this snapshot.',playback='Seeking and help return preserve the exact authored position; operation intermediates are explicitly labeled.'))
            passages.append(dict(id=id,title=title,text=text,formula=formula,demonstration=demo))
        if order==103:passages.append(mixed_passage(item['id']))
        sections=[dict(id=item['id']+'-understand',title='Build the representation',passages=passages[:2]),dict(id=item['id']+'-reason',title='Reason about changes and limits',passages=passages[2:])]
        sec=item['source_sections'][0]
        output.append(dict(id=item['id'],order=order,title=item['title'],source=dict(book='Donald E. Knuth, The Art of Computer Programming, Volume 1, third edition',section='§'+sec['section']+' '+sec['title'],pdfPages=PAGES[order],pagination='One-based supplied 1094-page ebook; not print pagination.',verification=('Formula (13), including reciprocal normalization and the negative pivot-column sign, visually verified on PDF page 482; Algorithm S text inspected on 483–485.' if order==105 else 'Array and triangular-index formulas visually verified on PDF pages 475–477; nonzero lower bounds are derived explicitly.' if order==103 else 'Circular-buffer formulas visually checked on PDF pages 395–396. This lesson deliberately uses an explicitly counted all-slots variant rather than conflating capacity conventions.' if order==93 else 'Relevant section text inspected in the supplied PDF at the cited one-based pages. The model, examples, notation choices, and limits are original and explicit.')),provenance='Original explanation, diagrams, examples, executable semantic models, and assessments. No source pages, source figures, exercise text, or answer-bank material are reproduced.',scope=c['scope'],sections=sections))
    return output

def run_tests():
    counts={}
    # Exhaustive counted-buffer histories against an unrelated deque specification.
    cases=0
    for cap in range(1,5):
        for bits in itertools.product([0,1],repeat=7):
            ops=[('put',str(i)) if bit else ('get',None) for i,bit in enumerate(bits)]
            trace=circular_queue(cap,ops);ref=deque()
            for (op,value),st in zip(ops,trace[1:]):
                old=list(ref)
                if op=='put' and len(ref)<cap:ref.append(value)
                elif op=='get' and ref:ref.popleft()
                assert st['data']['logical']==list(ref)
                if st['data']['error']:assert list(ref)==old
            cases+=1
    counts['circular-buffer histories']=cases
    # All simple directed graphs on four labeled vertices; independent permutation oracle.
    cases=0;vs=list('ABCD');edges=[(a,b) for a in vs for b in vs if a!=b]
    for mask in range(1<<len(edges)):
        adj={v:[] for v in vs}
        for k,(a,b) in enumerate(edges):
            if mask>>k&1:adj[a].append(b)
        trace=topological(adj);d=trace[-1]['data'];perms=itertools.permutations(vs)
        valid=any(all(p.index(a)<p.index(b) for a,us in adj.items() for b in us) for p in perms)
        assert (not d['remaining'])==valid
        if valid:assert all(d['output'].index(a)<d['output'].index(b) for a,us in adj.items() for b in us)
        else:assert all(b in adj[a] for a,b in zip(d['cycle'],d['cycle'][1:]))
        cases+=1
    counts['four-vertex directed graphs']=cases
    # Dense coefficient convolution and elementwise addition, including all-zero polynomials.
    polys=[{e:c for e,c in enumerate(cs) if c} for cs in itertools.product([-1,0,1],repeat=3)]
    cases=0
    for a in polys:
        for b in polys:
            expected_add={e:a.get(e,0)+b.get(e,0) for e in range(3)};expected_add={e:c for e,c in expected_add.items() if c}
            expected_mul={k:sum(a.get(e,0)*b.get(k-e,0) for e in range(3)) for k in range(5)};expected_mul={e:c for e,c in expected_mul.items() if c}
            assert poly_merge(a,b)[-1]['data']['result']==expected_add
            assert poly_multiply(a,b)[-1]['data']['result']==expected_mul
            cases+=1
    counts['polynomial pairs']=cases
    cases=0
    for R in range(1,7):
        for C in range(1,7):
            for lr,lc in [(-2,3),(0,0),(5,-4)]:
                for col in [False,True]:
                    vals=[]
                    for i in range(lr,lr+R):
                        for j in range(lc,lc+C):
                            k=offset(i,j,R,C,(lr,lc),col);vals.append(k)
                            r,c=(k%R,k//R) if col else (k//C,k%C)
                            assert (r+lr,c+lc)==(i,j)
                    assert sorted(vals)==list(range(R*C));cases+=1
    counts['array bijections']=cases
    for n in range(1,51):
        coords=[(i,j) for i in range(n) for j in range(i+1)]
        assert [triangular_offset(i,j,n) for i,j in coords]==list(range(len(coords)))
    counts['triangular packing bijections']=50
    mixed_cases=0;mixed_cells=0
    for dimensions in range(1,5):
        for shape in itertools.product(range(1,5),repeat=dimensions):
            for lower in [tuple([0]*dimensions),tuple(2-t*3 for t in range(dimensions))]:
                tuples=itertools.product(*(range(l,l+n) for l,n in zip(lower,shape)))
                for expected,indices in enumerate(tuples):
                    k=mixed_radix_offset(indices,shape,lower)
                    assert k==expected and mixed_radix_inverse(k,shape,lower)==indices
                    assert k==sum((indices[t]-lower[t])*math.prod(shape[t+1:]) for t in range(dimensions))
                    mixed_cells+=1
                mixed_cases+=1
    counts['mixed-radix dimension/bound domains']=mixed_cases;counts['mixed-radix tuple round trips']=mixed_cells
    for small in [False,True]:
        mt=mixed_trace(small);md=mt[-1]['data'];assert mixed_radix_inverse(md['accumulator'],md['shape'],md['lower'])==md['indices']
    for shape in [(),(0,2),(-1,3)]:
        try:mixed_radix_offset((0,)*len(shape),shape);raise AssertionError('invalid dimension accepted')
        except ValueError:pass
    for bad in [-1,12]:
        try:mixed_radix_inverse(bad,(2,2,3));raise AssertionError('invalid offset accepted')
        except IndexError:pass
    cases=0
    for values in itertools.product(range(-2,3),repeat=4):
        if values[0]==0:continue
        a,b,c,d=map(Fraction,values);expected=[[1/a,b/a],[-c/a,d-b*c/a]]
        actual=pivot_trace([list(values[:2]),list(values[2:])])[-1]['data']['dense']
        assert [[Fraction(v) for v in r] for r in actual]==expected;cases+=1
    rng=random.Random(88)
    for _ in range(100):
        A=[[Fraction(rng.randrange(-4,5),rng.randrange(1,5)) for j in range(3)] for i in range(3)];p=rng.randrange(3);q=rng.randrange(3)
        if A[p][q]==0:A[p][q]=Fraction(1,3)
        a=A[p][q];expected=[[1/a if (i,j)==(p,q) else A[i][j]/a if i==p else -A[i][j]/a if j==q else A[i][j]-A[i][q]*A[p][j]/a for j in range(3)] for i in range(3)]
        trace=pivot_trace(A,p,q);assert [[Fraction(v) for v in r] for r in trace[-1]['data']['dense']]==expected
        for st in trace:
            d=st['data'];rows={x for r in d['rowLinks'] for x in r};cols={x for r in d['columnLinks'] for x in r};assert rows==cols=={e['id'] for e in d['entries']}
        cases+=1
    try:pivot_trace([[0,1],[1,1]]);raise AssertionError('zero pivot accepted')
    except ValueError:pass
    counts['exact pivot cases']=cases
    for small in [False,True]:
        # Reference FCFS job start times independently produce the queue waiting integral.
        arrivals=[(1,'A',2),(2,'B',1)] if small else [(1,'A',3),(2,'B',2),(4,'C',1)]
        end=wait=0
        for time,name,duration in arrivals:start=max(time,end);wait+=start-time;end=start+duration
        trace=events_trace(small);assert trace[-1]['data']['area']==wait and trace[-1]['data']['now']==end
        assert [s['data']['now'] for s in trace]==sorted(s['data']['now'] for s in trace)
        for order,fn in TRACES.items():
            trace=fn(small)
            assert trace and all('data' in s for s in trace)
            if order==95:
                for st in trace:
                    d=st['data'];joined=d['live']+d['reserved']+d['free'];assert sorted(joined)==d['universe'] and len(joined)==len(set(joined))
            if order==100:
                assert any(s['data']['phase']=='updating' for s in trace)
                assert any(any(d['links'].get(l['next'],{}).get('prev')!=v for v,l in d['links'].items()) for d in [s['data'] for s in trace] if d['phase']=='updating')
    counts['main/smaller topic traces']=36
    lessons=build();assert [l['order'] for l in lessons]==list(range(88,106))
    for l in lessons:
        ps=[p for s in l['sections'] for p in s['passages']];assert len(ps)==(5 if l['order']==103 else 4)
        assert sum(len(p['text'].split()) for p in ps)>=260
        for p in ps:
            demo=p['demonstration'];assert len(demo['states'])>=2
            assert demo['check']['correctIndex'] in range(len(demo['check']['choices']))
            assert demo['simplerHelp']['check']['correctIndex'] in range(len(demo['simplerHelp']['check']['choices']))
            for st in demo['states']+demo['simplerHelp']['states']:
                nodes=st['diagram']['nodes'];assert len({n['id'] for n in nodes})==len(nodes)
                for n in nodes:
                    for coord in ['x','y','x2','y2','width','height','r']:
                        if coord in n:assert isinstance(n[coord],(int,float)) and math.isfinite(n[coord])
                    if n['type']=='text' and n.get('opacity',1)>0:
                        assert 15<=n['x']<=705 and 15<=n['y']<=435,(l['order'],p['id'],n)
    counts['authored passages with main/help']=73
    return counts

def main():
    global PLAN
    PLAN=ROOT/'content/fullbook/source-plan-D.json'
    parser=argparse.ArgumentParser();parser.add_argument('--test',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.test:print(json.dumps(run_tests(),indent=2));return
    data=json.dumps(build(),ensure_ascii=False,indent=2)+'\n'
    if args.check:
        assert OUT.read_text()==data,'batch-D.json is not reproducible from its authoring script';print('Batch D reproducibility passed');return
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(data);print(f'Wrote 18 lessons / 73 passages to {OUT}')

if __name__=='__main__':main()
