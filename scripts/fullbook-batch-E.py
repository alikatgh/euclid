#!/usr/bin/env python3
"""Original, deterministic tree lessons. No source images/text are distributed.
Run --test for semantic checks; default regenerates only batch-E.json.
"""
from __future__ import annotations
from collections import Counter, deque
from fractions import Fraction
from itertools import combinations, product
import copy, json, math, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
PLAN=ROOT/'content/fullbook/source-plan-E.json'
# Binary node: (identity, left-or-None, right-or-None); ordered node: (identity, children).
def B(v,l=None,r=None): return (v,l,r)
def T(v,*children): return (v,tuple(children))
def border(t,kind='in'):
    if t is None:return []
    v,l,r=t; a,b=border(l,kind),border(r,kind)
    return [v]+a+b if kind=='pre' else a+[v]+b if kind=='in' else a+b+[v]
def bdict(t):
    if t is None:return {}
    v,l,r=t
    return {v:(l[0] if l else None,r[0] if r else None),**bdict(l),**bdict(r)}
def forder(f,kind='pre'):
    ans=[]
    for v,ch in f:
        if kind=='pre':ans.append(v)
        ans+=forder(ch,kind)
        if kind=='post':ans.append(v)
    return ans
def fdict(f):
    ans={}
    for v,ch in f:ans[v]=[t[0] for t in ch];ans.update(fdict(ch))
    return ans
def binary(f):
    if not f:return None
    (v,ch),*rest=f
    return B(v,binary(ch),binary(rest))
def forest(t):
    if t is None:return ()
    v,l,r=t
    return (T(v,*forest(l)),)+forest(r)
def contour(t):
    """All three moments at each nonempty node, including return control."""
    out=[]; words={k:[] for k in ('pre','in','post')}
    def walk(t,anc):
        if t is None:return
        v,l,r=t
        for phase,sub in [('pre',l),('in',r),('post',None)]:
            words[phase].append(v)
            out.append({'node':v,'phase':phase,'ancestors':anc[:], 'outputs':copy.deepcopy(words)})
            if sub:walk(sub,anc+[v])
    walk(t,[]);return out

def inorder_stack(t):
    nodes=bdict(t);p=t[0] if t else None;s=[];out=[];trace=[]
    def snap(action):trace.append({'action':action,'p':p,'stack':s[:],'output':out[:]})
    snap('initialize')
    while p is not None or s:
        if p is not None:
            s.append(p);p=nodes[p][0];snap('push; descend left')
        else:
            p=s.pop();snap('pop pending ancestor')
            out.append(p);snap('visit after left subtree')
            p=nodes[p][1];snap('resume right subtree')
    return trace

def threaded(t,head='H'):
    nodes=bdict(t);order=border(t);out={}
    if head in nodes:raise ValueError('sentinel identity must be distinct from data nodes')
    for i,v in enumerate(order):
        l,r=nodes[v];out[v]={'L':l if l else order[i-1] if i else head,'LT':0 if l else 1,
                            'R':r if r else order[i+1] if i+1<len(order) else head,'RT':0 if r else 1}
    out[head]={'L':t[0] if t else head,'LT':0 if t else 1,'R':head,'RT':0}
    return out

def successor(nodes,v):
    q=nodes[v]['R']
    if nodes[v]['RT']==1:return q
    while nodes[q]['LT']==0:q=nodes[q]['L']
    return q

def predecessor(nodes,v,head='H'):
    if v==head:
        q=nodes[head]['L']
        if q==head:return head
        while nodes[q]['RT']==0:q=nodes[q]['R']
        return q
    q=nodes[v]['L']
    if nodes[v]['LT']==1:return q
    while nodes[q]['RT']==0:q=nodes[q]['R']
    return q

def insert_right(nodes,p,q):
    """Book Algorithm I, original node identities; q is a fresh address."""
    assert q not in nodes
    nodes=copy.deepcopy(nodes);old=nodes[p].copy()
    nodes[q]={'L':p,'LT':1,'R':old['R'],'RT':old['RT']}
    nodes[p]['R']=q;nodes[p]['RT']=0
    if nodes[q]['RT']==0:nodes[successor(nodes,q)]['L']=q
    return nodes

def copy_threads(nodes):
    prefix='copy:'
    while any(prefix+v in nodes for v in nodes):prefix='copy:'+prefix
    m={v:prefix+v for v in nodes}
    return {m[v]:{**n,'L':m[n['L']],'R':m[n['R']]} for v,n in nodes.items()},m

def encode(f,kind):
    d=fdict(f);roots=[t[0] for t in f]
    if kind in ('pre','post'):order=forder(f,kind)
    else:
        order=roots[:];pending=roots[:]
        while pending:
            v=pending.pop() if kind=='family' else pending.pop(0)
            order.extend(d[v]);pending.extend(d[v])
    idx={v:i for i,v in enumerate(order)}
    if kind=='post':return {'kind':kind,'records':[{'id':v,'degree':len(d[v])} for v in order]}
    # Explicit child indexes retain provenance; this teaching format is deliberately redundant.
    return {'kind':kind,'roots':[idx[v] for v in roots], 'records':[{'id':v,'children':[idx[w] for w in d[v]],'degree':len(d[v])} for v in order]}
def decode(enc):
    a=enc['records'];seen=set()
    if enc['kind']=='post':
        stack=[]
        for r in a:
            d=r['degree']
            if type(d)!=int or d<0 or d>len(stack) or r['id'] in seen:raise ValueError('invalid degree/identity')
            seen.add(r['id']);ch=stack[-d:] if d else []
            if d:del stack[-d:]
            stack.append(T(r['id'],*ch))
        return tuple(stack)
    def get(i):
        if not 0<=i<len(a) or i in seen:raise ValueError('cycle/shared/bad index')
        seen.add(i);r=a[i];return T(r['id'],*[get(j) for j in r['children']])
    f=tuple(get(i) for i in enc['roots'])
    if len(seen)!=len(a) or len({r['id'] for r in a})!=len(a):raise ValueError('unreachable/duplicate')
    return f

def fold_records(records,local):
    s=[];trace=[]
    for r in records:
        d=r['degree']
        if type(d)!=int or d<0 or d>len(s):raise ValueError('stack underflow or invalid degree')
        children=s[-d:] if d else []
        if d:del s[-d:]
        v=local(r['id'],children);s.append(v)
        trace.append({'node':r['id'],'degree':d,'children':children[:],'value':v,'stack':s[:]})
    return s,trace

# Immutable AST: constants ('c', rational string), variables ('v', name), operators.
ARITY={'+':2,'-':2,'*':2,'/':2,'pow':2,'neg':1,'ln':1,'exp':1}
def C(n):return ('c',str(Fraction(n)))
def V(name='x'):return ('v',name)
def ast_valid(a):
    if not isinstance(a,tuple) or not a:return False
    if a[0]=='c':
        try: return len(a)==2 and Fraction(a[1]) is not None
        except (ValueError,ZeroDivisionError):return False
    if a[0]=='v':return len(a)==2 and isinstance(a[1],str)
    return a[0] in ARITY and len(a)==ARITY[a[0]]+1 and all(ast_valid(x) for x in a[1:])
def fmt(a):
    op=a[0]
    if op in ('c','v'):return a[1]
    if op in ('ln','exp','neg'):return f'{op}({fmt(a[1])})'
    return '('+fmt(a[1])+{'pow':'^'}.get(op,op)+fmt(a[2])+')'
def ev(a,env):
    op=a[0]
    if op=='c':return Fraction(a[1])
    if op=='v':return env[a[1]]
    u=ev(a[1],env)
    if op=='neg':return -u
    if op=='ln':
        if u<=0:raise ValueError('real logarithm needs positive argument')
        return math.log(u)
    if op=='exp':return math.exp(u)
    v=ev(a[2],env)
    if op=='+':return u+v
    if op=='-':return u-v
    if op=='*':return u*v
    if op=='/':return u/v
    if op=='pow':
        if isinstance(v,Fraction) and v.denominator==1:return u**int(v)
        if u<=0:raise ValueError('real general power needs positive base')
        return u**v
    raise ValueError(op)
def simp(op,*xs):
    if op=='+':
        if xs[0]==C(0):return xs[1]
        if xs[1]==C(0):return xs[0]
    if op=='*':
        if C(0) in xs:return C(0)
        if xs[0]==C(1):return xs[1]
        if xs[1]==C(1):return xs[0]
    if op=='pow' and xs[1]==C(1):return xs[0]
    if op=='neg' and xs[0]==C(0):return C(0)
    return (op,*xs)
def diff(a,x='x'):
    op=a[0]
    if op=='c':return C(0)
    if op=='v':return C(int(a[1]==x))
    u=a[1];du=diff(u,x)
    if op=='neg':return simp('neg',du)
    if op=='ln':return ('/',du,u)
    if op=='exp':return simp('*',('exp',u),du)
    v=a[2];dv=diff(v,x)
    if op in ('+','-'):return simp(op,du,dv)
    if op=='*':return simp('+',simp('*',du,v),simp('*',u,dv))
    if op=='/':return ('/',('-',simp('*',du,v),simp('*',u,dv)),('pow',v,C(2)))
    if op=='pow':
        if v[0]=='c':
            n=Fraction(v[1])
            if n==0:return C(0)
            return simp('*',simp('*',C(n),simp('pow',u,C(n-1))),du)
        return simp('*',a,simp('+',simp('*',dv,('ln',u)),simp('*',v,('/',du,u))))
    raise ValueError(op)
def postfix(a):
    if a[0] in ('c','v'):return [a]
    return sum((postfix(x) for x in a[1:]),[])+[(a[0],)]
def eval_postfix(tokens,env):
    s=[];tr=[]
    for tok in tokens:
        op=tok[0]
        if op in ('c','v'):s.append(ev(tok,env))
        else:
            n=ARITY[op]
            if len(s)<n:raise ValueError('missing operands')
            args=s[-n:];del s[-n:];s.append(ev((op,*[C(x) for x in args]),{}))
        tr.append({'token':tok,'stack':[str(x) for x in s]})
    if len(s)!=1:raise ValueError('extra operands')
    return s[0],tr

# Canonical recursive polynomial: constant integer or {'var', 'terms': exponent→child}.
# Highest variable first; terms always include exponent 0 (possibly the zero constant).
def poly_tree(terms,variables=('x','y')):
    terms={tuple(k):v for k,v in terms.items() if v}
    if not terms:return 0
    levels=[i for i in range(len(variables)) if any(k[i] for k in terms)]
    if not levels:return sum(terms.values())
    i=max(levels);groups={0:{}}
    for k,v in terms.items():
        e=k[i];kk=list(k);kk[i]=0;groups.setdefault(e,{})[tuple(kk)]=v
    return {'var':variables[i],'terms':{str(e):poly_tree(g,variables) for e,g in sorted(groups.items())}}
def poly_flat(t,variables=('x','y')):
    if isinstance(t,int):return {(0,)*len(variables):t} if t else {}
    i=variables.index(t['var']);out={}
    for e,ch in t['terms'].items():
        for k,c in poly_flat(ch,variables).items():
            kk=list(k);kk[i]+=int(e);out[tuple(kk)]=out.get(tuple(kk),0)+c
    return {k:v for k,v in out.items() if v}
def poly_add(p,q):
    d=poly_flat(p)
    for k,v in poly_flat(q).items():d[k]=d.get(k,0)+v
    return poly_tree(d)
def poly_value(t,x,y):return sum(c*x**a*y**b for (a,b),c in poly_flat(t).items())

def components(vertices,edges):
    adj={v:set() for v in vertices}
    for u,v in edges:adj[u].add(v);adj[v].add(u)
    todo=set(vertices);parts=[]
    while todo:
        seen={min(todo)};q=list(seen)
        while q:
            for w in adj[q.pop()]-seen:seen.add(w);q.append(w)
        todo-=seen;parts.append(sorted(seen))
    return parts

def cycle_rank(vertices,edges):return len(edges)-len(vertices)+len(components(vertices,edges))
def root_arcs(vertices,edges,root,outward=False):
    if len(components(vertices,edges))!=1 or len(edges)!=len(vertices)-1:raise ValueError('not a free tree')
    adj={v:[] for v in vertices}
    for u,v in edges:adj[u].append(v);adj[v].append(u)
    seen={root};q=[root];arcs=[]
    while q:
        p=q.pop(0)
        for v in sorted(adj[p]):
            if v not in seen:seen.add(v);q.append(v);arcs.append((p,v) if outward else (v,p))
    return arcs

def divergence(vertices,arcs,counts=None):
    b={v:0 for v in vertices}
    for i,(u,v) in enumerate(arcs):c=counts[i] if counts else 1;b[u]+=c;b[v]-=c
    return b

def euler(arcs,start=None):
    """Distinct arc tickets, loops and parallel arcs allowed. Hierholzer trace."""
    if not arcs:return [],[]
    vertices=set(sum(([u,v] for u,v in arcs),[]));b=divergence(vertices,arcs)
    plus=[v for v in vertices if b[v]==1];minus=[v for v in vertices if b[v]==-1]
    if any(abs(z)>1 for z in b.values()) or not (all(z==0 for z in b.values()) or len(plus)==len(minus)==1):raise ValueError('degree imbalance')
    if len(components(vertices,arcs))!=1:raise ValueError('disconnected support')
    start=start if start is not None else plus[0] if plus else arcs[0][0]
    if start not in vertices or (plus and start!=plus[0]):raise ValueError('wrong start')
    adj={v:[] for v in vertices}
    for i,(u,v) in enumerate(arcs):adj[u].append(i)
    stack=[(start,None)];reverse=[];used=[];tr=[]
    while stack:
        v,_=stack[-1]
        if adj[v]:
            i=adj[v].pop(0);used.append(i);stack.append((arcs[i][1],i));action='spend ticket'
        else:
            v,i=stack.pop()
            if i is not None:reverse.append(i)
            action='close detour; prepend on return'
        tr.append({'action':action,'cursor':stack[-1][0] if stack else start,'used':used[:], 'stack':[v for v,_ in stack],'reverse':reverse[:]})
    ans=reverse[::-1]
    assert len(ans)==len(arcs)
    return ans,tr

def last_exits(arcs,tour,root):
    out={}
    for i in tour:
        u,v=arcs[i]
        if u!=root:out[u]=i
    return out

def union_trace(n,pairs):
    p=list(range(n));tr=[]
    def root(i):
        while p[i]!=i:i=p[i]
        return i
    for a,b in pairs:
        r,s=root(a),root(b)
        if r!=s:p[r]=s
        tr.append({'pair':[a,b],'roots':[r,s],'parent':p[:]})
    return tr

# Declarative SVG authoring. Geometric position encodes actual ancestry/order.
def text(id,x,y,s,role='input',size=16):return {'id':id,'type':'text','x':x,'y':y,'text':str(s),'fontSize':size,'anchor':'middle','role':role}
def circle(id,x,y,role='input',r=20):return {'id':id,'type':'circle','x':x,'y':y,'r':r,'role':role}
def rect(id,x,y,w,h,role='input'):return {'id':id,'type':'rect','x':x,'y':y,'width':w,'height':h,'role':role}
def line(id,x,y,x2,y2,role='input'):return {'id':id,'type':'line','x':x,'y':y,'x2':x2,'y2':y2,'role':role,'strokeWidth':2}
def arrow(id,a,b,role='input',curved=False):
    x,y=a;xx,yy=b;dx=xx-x;dy=yy-y;norm=math.hypot(dx,dy) or 1
    ex,ey=xx-23*dx/norm,yy-23*dy/norm;sx,sy=x+22*dx/norm,y+22*dy/norm
    if curved:
        midx=(sx+ex)/2+28;midy=min(sy,ey)-45
        path={'id':id,'type':'path','d':f'M {sx} {sy} Q {midx} {midy} {ex} {ey}','fill':'none','role':role,'strokeWidth':2}
        dx,dy=ex-midx,ey-midy;norm=math.hypot(dx,dy) or 1
    else:path=line(id,sx,sy,ex,ey,role)
    dx,dy=dx/norm,dy/norm
    head={'id':id+'-head','type':'path','d':f'M {ex-8*dx+4*dy} {ey-8*dy-4*dx} L {ex} {ey} L {ex-8*dx-4*dy} {ey-8*dy+4*dx}','fill':'none','role':role,'strokeWidth':2}
    return [path,head]
def state(id,caption,nodes,formula='',invariant='',data=None):
    return {'id':id,'caption':caption,'formula':formula,'diagram':{'title':caption.split('.')[0], 'description':caption,'viewBox':[0,0,720,440],'nodes':nodes,'invariant':invariant},'data':data or {}}
def tree_positions(f,x0=40,x1=480,y0=70,dy=90):
    d=fdict(f);pos={};leaves=[]
    def size(v):return max(1,sum(size(w) for w in d[v]))
    total=sum(size(t[0]) for t in f) or 1
    def place(v,lo,hi,depth):
        pos[v]=((lo+hi)/2,y0+depth*dy)
        s=sum(size(w) for w in d[v]) or 1;cur=lo
        for w in d[v]:
            end=cur+(hi-lo)*size(w)/s;place(w,cur,end,depth+1);cur=end
    cur=x0
    for t in f:
        end=cur+(x1-x0)*size(t[0])/total;place(t[0],cur,end,0);cur=end
    return pos

def tree_nodes(f,active=None,done=(),positions=None,labels=None,edge_role='input'):
    d=fdict(f);p=positions or tree_positions(f);ns=[]
    for v,ch in d.items():
        for w in ch:ns+=arrow('edge-'+v+'-'+w,p[v],p[w],edge_role)
    for v,(x,y) in p.items():
        role='active' if v==active else 'result' if v in done else 'input'
        ns += [circle('node-'+v,x,y,role),text('label-'+v,x,y+5,(labels or {}).get(v,v),role)]
    if active in p:
        x,y=p[active];ns+=[{'id':'walker','type':'circle','x':x-28,'y':y-25,'r':7,'role':'active'}]
    return ns

def bforest(t):
    if t is None:return ()
    return (T(t[0],*[bforest(c)[0] for c in t[1:] if c]),)
def bpositions(t,x0=60,x1=480,y=65,dy=85):
    out={}
    def rec(t,a,b,y):
        if not t:return
        out[t[0]]=((a+b)/2,y);rec(t[1],a,(a+b)/2,y+dy);rec(t[2],(a+b)/2,b,y+dy)
    rec(t,x0,x1,y);return out

def bnodes(t,active=None,done=()):return tree_nodes(bforest(t),active,done,bpositions(t))
def stack_nodes(values,title='pending',x=565,y=325):
    ns=[text('stack-title',x+40,45,title,size=15)]
    for i,v in enumerate(values):
        yy=y-i*42;ns +=[rect('stack-box-'+str(i),x,yy,80,35,'active' if i==len(values)-1 else 'input'),text('stack-value-'+str(i),x+40,yy+23,str(v),'result' if i==len(values)-1 else 'input',size=14)]
    return ns

def ribbon(values,y=392,prefix='visit',id='ribbon'):
    return [text(id+'-'+prefix if id=='ribbon' else id,350,y,prefix+': '+(' '.join(map(str,values)) or '∅'),'result',size=15)]
def check(prompt,choices,index,why):return {'prompt':prompt,'choices':choices,'correctIndex':index,'explanation':why}
def demo(id,title,kind,states,helpstates,helpintro,connection,assessment,helpcheck,model=None):
    return {'id':id,'title':title,'model':{'kind':kind,'deterministic':True,**(model or {})},'states':states,
      'transitions':[{'from':a['id'],'to':b['id'],'action':b['caption'].split('.')[0], 'explanation':b['caption']} for a,b in zip(states,states[1:])],
      'check':assessment,'simplerHelp':{'intro':helpintro,'states':helpstates,'steps':[{'action':s['id'],'text':s['caption']} for s in helpstates], 'connection':connection,'check':helpcheck},
      'accessibility':{'reducedMotion':'Display the identical semantic frames as discrete steps.','stateDescription':'Read caption, active object and diagram invariant.','playback':'Seek/back/pause/replay preserve the frame and object identities; help returns to this frame.'}}

def passage(id,title,prose,formula='',demonstration=None):
    p={'id':id,'title':title,'text':prose,'formula':formula}
    if demonstration:p['demonstration']=demonstration
    return p

def lesson(order,passages,scope,pages=None):
    p=next(x for x in json.load(open(PLAN))['lessons'] if x['order']==order)
    refs=p['source_sections']
    return {'id':p['id'],'order':order,'title':p['title'], 'source':{'book':'Donald E. Knuth, The Art of Computer Programming, Volume 1, third edition','section':'; '.join('§'+x['section']+' '+x['title'] for x in refs),'pdfPages':pages or str(refs[0]['pdf_page_start']), 'pagination':'one-based supplied ebook, not printed'},
      'provenance':'Original explanations, examples, diagrams and assessments. Models are executed by scripts/fullbook-batch-E.py; no textbook pages, exercise text or source images are distributed.', 'scope':scope,
      'sections':[{'id':p['id']+'-ideas','title':'Build the idea, then justify it','passages':passages}]}

BASE=B('M',B('D',None,B('G')),B('T',B('P'),None))
SMALL=B('R',B('L'),None)
F=(T('A',T('B'),T('C',T('D'))),T('E',T('F')))
SMALLF=(T('U',T('V')),T('W'))

def family_build(small=False):
    f=(T('R',T('L')),) if small else (T('R',T('A',T('C')),T('B')),)
    d=fdict(f);pos=tree_positions(f,x0=80,x1=640,y0=70,dy=100);ids=forder(f);states=[]
    for k in range(1,len(ids)+1):
        visible=set(ids[:k]);ns=[]
        for v,ch in d.items():
            if v not in visible:continue
            for w in ch:
                if w in visible:ns+=arrow('family-'+v+w,pos[v],pos[w])
            x,y=pos[v];ns +=[circle('node-'+v,x,y,'active' if v==ids[k-1] else 'input'),text('label-'+v,x,y+5,v)]
        if k==len(ids):
            # Enclosures display genuinely disjoint descendant sets, not extra graph edges.
            ns +=[{**rect('partition-A',65,135,295,210,'muted'),'fill':'none'},text('partition-label',210,365,'One whole descendant family',size=14)] if not small else []
        ns+=ribbon(ids[:k],410,'identities')
        states.append(state('family-'+str(k),f'Attach {ids[k-1]} once. Each nonroot has exactly one parent.',ns,
                            r'|T|=1+\sum_i|T_i|','Child families are disjoint.',{'identities':ids[:k]}))
    return states

def sharing_states(small=False):
    nsbase=[rect('outer',50,60,620,295,'muted'),text('outer-label',360,88,'A finite container of references'),rect('ref1',80,130,110,60),text('ref1-label',135,167,'reference 1'),rect('box',430,150,150,90),text('box-name',505,175,'object Q')]
    if not small:nsbase +=[rect('ref2',240,130,110,60),text('ref2-label',295,167,'reference 2')]
    out=[]
    for k,value in enumerate([4,9,9] if not small else [2,5]):
        ns=copy.deepcopy(nsbase)+arrow('ref1-arrow',(190,160),(430,195),'active')
        if not small:ns+=arrow('ref2-arrow',(350,160),(430,195),'active')
        ns +=[text('contents',505,212,'value '+str(value),'result' if k else 'input',18)]
        if k==2:ns +=[{'id':'cycle','type':'path','arrow':True,'d':'M 575 220 C 680 320 310 340 300 188','fill':'none','role':'error','strokeWidth':3},text('cycle-label',445,325,'back-reference: stop expanding',size=15)]
        out.append(state('sharing-'+str(k),['Two references designate one object, not two equal copies.','One mutation changes the value seen through every reference.','A back-reference creates a cycle; an ancestor-set test reports it.'][k] if not small else ['A handle names one little box.','Replace the content; the handle still names the same box.'][k],ns,'','Identity stays Q even when its content changes.',{'value':value,'references':1 if small else 2,'cycle':k==2}))
    return out

def traversal_states(t):
    out=[]
    for i,e in enumerate(contour(t)):
        ns=bnodes(t,e['node'],e['outputs'][e['phase']])+[text('moment',590,85,e['phase']+' moment','active')]
        for j,k in enumerate(('pre','in','post')):ns +=ribbon(e['outputs'][k],345+j*32,k,k+'-ribbon')
        out.append(state('moment-'+str(i),f"At {e['node']}: {e['phase']} visit fires. "+{'pre':'This is before either child trip.','in':'The left trip is complete; the right trip has not started.','post':'Both child trips are complete; return to the parent.'}[e['phase']],ns,
            r'\operatorname{in}(v)=\operatorname{in}(L)\,v\,\operatorname{in}(R)','One event per node per order.',e))
    return out

def stack_states(t):
    out=[]
    for i,e in enumerate(inorder_stack(t)):
        ns=bnodes(t,e['p'],e['output'])+stack_nodes(e['stack'])+ribbon(e['output'])+[text('current-p',590,95,'P = '+str(e['p'] or 'null'),'active')]
        out.append(state('stack-'+str(i),e['action'].capitalize()+'. '+('The top entry remembers where to resume.' if e['stack'] else 'No pending ancestor remains.'),ns,r'\text{while }P\ne\varnothing\text{ or }S\ne[]','The stack holds ancestors whose own visit is still pending.',e))
    return out

def thread_scene(t,nodes,active=None,target=None,show=('R',),head='H'):
    p=bpositions(t,x0=60,x1=500,y=70,dy=68);p[head]=(615,75);ns=bnodes(t,active)+[rect('header',585,50,60,45,'muted'),text('header-label',615,79,head)]
    # bnodes uses default y; use exact positions for consistent endpoints.
    ns=tree_nodes(bforest(t),active,positions={v:xy for v,xy in p.items() if v!=head})+[rect('header',585,50,60,45,'muted'),text('header-label',615,79,head)]
    if active in nodes:
        for key in show:
            n=nodes[active];q=n[key]
            if q in p:
                ns+=arrow('selected-'+key,p[active],p[q],'active' if n[key+'T']==1 else 'result',n[key+'T']==1)
                ns +=[text('tag-'+key,350,350+(0 if key=='R' else 28),key+': '+('thread (tag 1)' if n[key+'T'] else 'child (tag 0)')+' → '+q,size=16)]
    if target:ns+=ribbon([target],415,'successor')
    return ns

def thread_states(t):
    n=threaded(t);order=border(t);out=[]
    for i,v in enumerate(order):
        q=successor(n,v)
        out.append(state('thread-'+str(i),f"Successor of {v} is {q}. "+('Follow the tagged return guide directly.' if n[v]['RT'] else 'Enter the right child and descend only through real left children.'),thread_scene(t,n,v,q),r'\mathrm{RTAG}=1\Rightarrow \mathrm{succ}(P)=\mathrm{RLINK}(P)','Curved arrows are threads; straight arrows are children.',{'node':v,'successor':q,'links':n}))
    return out

def insertion_states(t,p,q):
    n=threaded(t);nn=insert_right(n,p,q)
    def rec(t):
        if t is None:return None
        if t[0]==p:return B(p,t[1],B(q,None,t[2]))
        return B(t[0],rec(t[1]),rec(t[2]))
    nt=rec(t);assert nn==threaded(nt)
    out=[state('before-insert',f'Before insertion, inspect the right link at {p}.',thread_scene(t,n,p),data={'tree':t,'links':n}),
         state('after-insert',f'Insert fresh {q} to the right of {p}; inherit the old right link and repair its leftmost predecessor thread.',thread_scene(nt,nn,q,show=('L','R')),r'\mathrm{in}(T_{new})=\cdots P\,Q\cdots','All child and thread invariants hold after the atomic update.',{'tree':nt,'links':nn})]
    cp,m=copy_threads(nn);pos=bpositions(nt,x0=30,x1=300,y=85,dy=78)
    ns=tree_nodes(bforest(nt),positions=pos)
    pos2={v:(x+340,y) for v,(x,y) in pos.items()};ns+=[]
    ns2=tree_nodes(bforest(nt),positions=pos2,labels={v:v+"′" for v in pos2})
    for node in ns2:node['id']='copy-'+node['id']
    ns+=ns2+[text('original-label',170,355,'Original addresses'),text('copy-label',510,355,'Fresh addresses'),text('copy-invariant',360,403,'Map every child, thread and header through φ',size=15)]
    out.append(state('copy-complete','Copy values and remap every pointer, including header links. No copied pointer targets the original.',ns,r'\phi(\mathrm{link}(v))=\mathrm{link}_{copy}(\phi(v))','Corresponding shapes and values agree; address sets are disjoint.',{'copy':cp,'map':m,'original':nn}))
    return out

def build_first():
    lessons=[]
    dm=demo('recursive-families','Build disjoint child families','recursive-partition',family_build(),family_build(True),'Hang one little mobile from a larger one.','Each attachment creates a parent relation; the whole hanging part is a subtree.',check('A binary node has only a right child Z. Is it the same binary shape as one with only a left child Z?',['Yes, degree is one in both','No, the occupied slot differs','Only if Z is a leaf'],1,'Binary structure remembers the two slots, even when one is empty.'),check('A mobile has a root R and one attached piece L. How many roots does this one tree have?',['Two','One','Zero'],1,'L roots a subtree; R is the root of the whole tree.'))
    lessons.append(lesson(106,[passage('recursive-definition','Build from smaller disjoint pieces','A finite rooted tree T is nonempty. Choose one distinguished root r; partition every other node into disjoint nonempty sets T₁,…,Tₖ, each itself a rooted tree. The children of r are their roots. The construction terminates because every child tree has fewer nodes. An ordered tree additionally remembers the list order of these child trees. A forest is an ordered list of zero or more such trees.',r'T=\{r\}\sqcup T_1\sqcup\cdots\sqcup T_k',dm),passage('levels','Names belong to a chosen root','The degree of a node is its number of children, not its total undirected degree. A leaf has degree zero. Set the root level to zero; each parent-to-child step adds one. The subtree rooted at v contains v and all its descendants. Subtrees rooted at different children are disjoint, but the subtree at a parent contains those at its children. This distinction prevents a mistaken claim that all subtrees are disjoint.',r'\ell(\mathrm{child})=\ell(\mathrm{parent})+1'),passage('binary-slots','Two slots are extra information','A binary tree is either empty, or a root together with a left binary tree and a right binary tree. Its two slots have names. A root with just a left child and a root with just a right child are different binary shapes, even though both have one child. An ordinary one-child ordered tree has no empty first slot to distinguish those cases. Therefore “at most two children” is insufficient as a definition of a binary tree.',r'B=\varnothing\quad\text{or}\quad (r,L,R)'),passage('size-induction','Why the recursive definition is safe','Prove statements about all finite trees by node-count induction: establish the one-node case, assume the claim for each strictly smaller child tree, and combine them at the root. Unique parenthood follows because the child sets form a partition at every step. Sharing one physical child between two parents violates that partition, even if a drawing looks tree-like. The animation is one instance of this definition, not an induction proof for all sizes.',r'|T|=1+\sum_{i=1}^k|T_i|')],'Finite rooted ordered trees, forests, binary slots and size induction; geometric drawing is not part of node identity.','489–501'))
    dm=demo('shared-list','References can converge','object-identity-graph',sharing_states(),sharing_states(True),'A label on a handle points to a small box.','The pointer is a reference; replacing the box contents does not create a new identity.',check('Objects P and Q have equal contents today; only P is changed. What follows?',['Q must change too','Nothing about Q unless P and Q are the same object','The graph must contain a cycle'],1,'Equality of contents does not imply shared identity.'),check('You replace the content of box Q. What must change about its handle?',['Its destination','Nothing','It must split into two'],1,'A handle names an object, not the old value.'))
    lessons.append(lesson(107,[passage('nested-syntax','Parentheses describe nesting','A recursively nested list consists of atoms and sublists in a specified order. In (a,(b,c),d), the inner list is one element of the outer list; b and c are not siblings of a. An atom is treated as indivisible at this level. Empty sublists are legitimate objects, distinct from a missing pointer. Finite nesting can be expanded into a tree of occurrences, but an implementation need not allocate a fresh object for every occurrence.',demonstration=dm),passage('sharing','Equal contents versus one object','Let two references lead to the same inner object Q. Reading either reference observes Q; changing Q once is observed through both. Two separately allocated objects with equal contents do not have this property. A shared acyclic structure is a directed acyclic graph of identities, while its expanded occurrence tree may duplicate whole substructures and be much larger. Counting references and counting distinct allocated objects answer different questions.'),passage('cycles','A finite graph can have infinite expansion','A reference from a descendant back to an ancestor creates a cycle. The allocated graph may still have only three objects, but recursively printing all descendants without a stopping rule does not terminate. Use an active-ancestor set to detect back-edges while expanding: enter marks an object active; return removes it. Encountering an active identity reports a cycle. A separate completed/visited set avoids revisiting shared objects when the task is to count each identity once.'),passage('limits','Which promise makes recursion valid?','Finite trees justify structural recursion directly because every recursive argument is a smaller subtree. On arbitrary lists-with-sharing, the implementation must specify whether it visits occurrences or distinct identities; on cyclic graphs it must additionally specify a termination policy. A visited set intentionally changes occurrence semantics. Two references to an already completed node indicate sharing, not necessarily a cycle. The box example establishes the difference concretely, not a universal garbage-collection algorithm.')],'Nested list syntax, identity, sharing and cycles; full generalized-list storage and collection algorithms belong to the later list-structure units.','496–501'))
    dm=demo('timed-visits','One walk, three visit timings','contour-events',traversal_states(BASE),traversal_states(SMALL),'Walk from R to its single left child L and back.','Ring before the child trip for preorder, after the left trip for inorder, and after both trips for postorder.',check('For root K with left child H and right child N, which inorder output is correct?',['K H N','H K N','H N K'],1,'Inorder visits left subtree, root, right subtree.'),check('R has only a left leaf L. Which postorder is correct?',['R L','L R','R R'],1,'Finish the child before visiting its parent.'),{'input':BASE,'trace':contour(BASE)})
    lessons.append(lesson(108,[passage('visit-events','Arrival is not necessarily a visit','A traversal is a control walk through the tree plus a rule for when to emit a node. For a nonempty binary node v, there are three meaningful moments: before the left subtree, between left and right, and after the right subtree. Preorder, inorder and postorder emit at those moments respectively. Returning to a node is not an accidental duplicate visit: it is the moment needed to decide which child work has finished.',demonstration=dm),passage('recursive-orders','Define the three output words','Let ε be the empty word, and write concatenation by adjacency. Every traversal of the empty tree produces ε. For T=(v,L,R), preorder is v followed by preorder(L) and preorder(R); inorder places v between the two child outputs; postorder puts v last. The left/right slots remain fixed throughout. Reflecting the picture without changing those slots is merely redrawing; exchanging the slots changes the tree.',r'\mathrm{pre}(T)=v\,\mathrm{pre}(L)\,\mathrm{pre}(R),\quad\mathrm{post}(T)=\mathrm{post}(L)\,\mathrm{post}(R)\,v'),passage('once','Exactly once is a theorem','Induct on node count. The empty case emits nothing. For a nonempty tree, the induction hypothesis says each child emits all and only its own nodes once. Those node sets are disjoint and exclude v. Adding one emission of v therefore emits every node exactly once. The same proof works for all three positions of v. The computed ribbons verify our implementation on this input; they do not replace the induction.'),passage('empty','Boundary cases expose bad stopping rules','A single node has identical one-letter outputs for all three orders. An empty binary tree produces no events. A right-only child does not become a left child because it is the only one: inorder emits the parent first in that case. In the example M(D(∅,G),T(P,∅)), the three complete words are M D G T P, D G M P T, and G D P T M. Compare the moments, not just memorized sequences.')],'Binary-tree visit timings, recursive definitions and induction, with an executed contour walk.','505–510'))
    dm=demo('pending-ancestors','The stack remembers unfinished work','iterative-inorder-stack',stack_states(BASE),stack_states(SMALL),'Keep one return card for R while you visit L.','A card means “my left trip is underway; visit me when it finishes.”',check('A completely left-skewed tree has 8 nodes. What peak number of pending ancestor entries can the descent require?',['1','3','8'],2,'All eight nodes are pushed before the first pop. Height counts nodes here.'),check('After visiting L in R with left leaf L, which card must be resumed?',['R','L again','No card'],0,'R was waiting for its left subtree to finish.'),{'input':BASE,'trace':inorder_stack(BASE)})
    lessons.append(lesson(109,[passage('derive-stack','Replace suspended calls with cards','An inorder call first asks its left child to finish. Before following that child, save the current node on a last-in-first-out stack S. When the current pointer P is null, the top card identifies the next pending node: pop it, visit it, then set P to its right child. Continue while either P is nonnull or S is nonempty. The frames distinguish pushing, popping, visiting and resuming; popping alone does not emit anything.',demonstration=dm),passage('stack-invariant','What a pending ancestor actually means','At the descent test, every stack entry is an ancestor whose own visit and right-subtree work have not yet occurred. The top entry is the nearest such ancestor. P names the next subtree to traverse, or null when that subtree is complete. Previously emitted nodes form an initial segment of the desired inorder word. During the pop/visit microsteps, P temporarily names a node rather than an unvisited subtree; the control label is therefore part of the state.',r'S=[a_1,\ldots,a_k],\quad a_k\text{ resumes next}'),passage('proof-stack','Restore the caller’s stack','A useful induction statement is stronger than “the output is right”: traversing a subtree starting above an arbitrary existing stack prefix emits exactly that subtree’s inorder word and restores the prefix. The empty case goes directly to resumption. For a nonempty node, the saved card survives the left traversal, is popped once, and is followed by the right traversal. This proves both output order and correct return behavior.'),passage('cost','Linear work does not imply constant storage','Each of n nodes is pushed, popped and visited exactly once. Child tests and pointer updates add only constant work per node, so total time is O(n). The stack contains at most h nodes where h is the number of nodes on a longest root-to-leaf path; auxiliary space is O(h). A balanced tree may have logarithmic height, but a chain has h=n. For the empty tree there are no pushes and no visits.',r'\text{time}=O(n),\qquad \text{auxiliary space}=O(h)')],'An explicit control-state refinement of source Algorithm T; no MIX machine execution is claimed.','508–510'))
    dm=demo('threaded-successor','Empty child slots become return guides','tagged-inorder-links',thread_states(BASE),thread_states(SMALL),'L has no right child, so its spare right slot points back to R.','The guide answers “who comes next?”; it is not a new child.',check('Q has a real right child S whose leftmost descendant is V. Where is Q’s inorder successor?',['S always','V','Q’s parent always'],1,'With a real right subtree, successor is its leftmost node.'),check('L’s right link returns to R and is tagged 1. Should traversal descend into it as a child?',['Yes','No'],1,'Tag 1 means a thread, not a subtree.'),{'input':BASE,'links':threaded(BASE)})
    lessons.append(lesson(110,[passage('tags','Reuse only absent child links','A threaded binary tree keeps real left and right child links. When a child slot is absent, its link may instead point to the inorder predecessor or successor. A separate tag says which meaning applies: here 0 means child and 1 means thread. The diagram uses straight child arrows and curved return guides with an explicit tag label. Threads are navigation information, not extra tree edges.',demonstration=dm),passage('successor','Two cases for the next node','To compute successor(P), inspect its right link. If RTAG(P)=1, that link already names the successor. Otherwise enter the real right subtree, then follow real left-child links while LTAG=0. Stop at its leftmost node. Predecessor is the left/right mirror. Correctness follows directly from the recursive inorder definition: after P comes the first node of its right subtree, or the first ancestor for which P lay in the left subtree.',r'\operatorname{succ}(P)=\begin{cases}\operatorname{RLINK}(P)&\operatorname{RTAG}(P)=1,\\\operatorname{leftmost}(\operatorname{RLINK}(P))&\operatorname{RTAG}(P)=0.\end{cases}'),passage('header','State the header convention, including empty','Use a separate sentinel H. For a nonempty tree, H.L points to the root with tag 0; H.R points to H with tag 0. The first node’s predecessor thread and the last node’s successor thread point to H. For an empty tree, H.L=H and LTAG(H)=1; H.R=H and RTAG(H)=0 still. H is not a data node. Under this convention successor(H) finds the first node, or returns H for the empty tree. Our predecessor helper treats H explicitly to return the last node.'),passage('cost-thread','No explicit stack is not the same as one-step queries','A successor operation may descend a long left chain, so its worst-case time is O(h). A whole inorder traversal is O(n): across the traversal each relevant child edge is descended only a bounded number of times, and every node is emitted once. Thread tags cost storage and must be maintained by updates. Right-only threading is another valid tradeoff; then empty left children remain null and the successor descent tests for null instead of LTAG.')],'Two-sided inorder threading, Algorithm S, explicit sentinel convention and costs.','511–520'))
    dm=demo('safe-thread-update','Repair links before resuming traversal','threaded-insertion-copy',insertion_states(BASE,'M','Q'),insertion_states(SMALL,'L','X'),'Insert a fresh card X after leaf L.','The new card points backward to L and forward to the old successor; remapping makes an independent copy.',check('When inserting Q as P’s right child above an existing right subtree, which old thread may need repair?',['The predecessor thread of that subtree’s leftmost node','Every node’s child links','The root’s left child unconditionally'],0,'That leftmost node previously had P as predecessor; its new predecessor is Q.'),check('A copied node still threads to the original header. Is the copy independent?',['Yes','No'],1,'The header is part of the address map and must be copied too.'),{'input':BASE,'insertion':{'parent':'M','fresh':'Q'}})
    lessons.append(lesson(111,[passage('insert-right','One inserted node inherits one old region','Let Q be a fresh address inserted as the right child of P. Q receives P’s old right link and right tag. P.R becomes Q with child tag 0. Q.L becomes a predecessor thread to P with tag 1. If the old right link was a real subtree, that whole subtree becomes Q’s right subtree; Q is inserted between P and the old subtree in inorder. This update changes the shape deliberately while retaining every old node.',demonstration=dm),passage('repair-thread','Repair the one predecessor that changed','If Q inherited a real right subtree, let V be that subtree’s leftmost node. V’s left thread previously named P; replace it with Q. No other predecessor or successor relationship changes except the inserted adjacency. If Q inherited a successor thread, no such V exists and no repair is needed. The transition displays the completed atomic update; an actual implementation must not allow another traversal to observe partially updated tags and links.'),passage('copy-map','Copy shape with an address correspondence','For an independent copy, allocate fresh addresses for all data nodes and the sentinel. Let φ map each old address to its fresh partner. Copy values and tags; replace every pointer target v by φ(v), whether it is a child, a thread or the header. Then corresponding trees have equal values and shape but disjoint address sets. Copying only real children leaves threads pointing into the old tree, which breaks independence.',r'\mathrm{link}_{new}(\phi(v))=\phi(\mathrm{link}_{old}(v))'),passage('verify-update','Check structure and navigation separately','Reconstruct the child-only tree while ignoring tagged threads, then compute its inorder word independently. Every absent left/right child must carry exactly the predecessor/successor from that word, using H at the boundaries. Check that a copy has no pointer into the source address set. The executable model tests empty, one-node, skewed and branching shapes; insertion is defined only at an existing data node, so insertion into an empty tree requires separately installing a root and its header links.')],'Source Algorithm I right insertion, complete thread invariants and fresh-address copying; concurrency and deletion algorithms are outside this unit.','519–525'))
    return lessons

def conversion_states(f):
    bt=binary(f);d=fdict(f);p=tree_positions(f,x0=40,x1=650,y0=70,dy=100)
    s=[state('forest','Begin with an ordered forest. Roots and siblings have a fixed left-to-right order.',tree_nodes(f,positions=p),data={'forest':f})]
    links=bdict(bt);ns=[]
    for v,(l,r) in links.items():
        if l:ns+=arrow('child-'+v+l,p[v],p[l],'input')
        if r:ns+=arrow('sibling-'+v+r,p[v],p[r],'active');ns +=[text('sibling-tag-'+v,(p[v][0]+p[r][0])/2,p[v][1]-28,'next',size=14)]
    for v,(x,y) in p.items():ns +=[circle('node-'+v,x,y),text('label-'+v,x,y+5,v)]
    s.append(state('two-links','Keep only first-child arrows and add next-sibling arrows, including between forest roots.',ns,r'L=\text{first child},\quad R=\text{next sibling}','A right link is a sibling relation in the forest.',{'binary':bt}))
    ns=bnodes(bt)+[text('binary-note',580,70,'Binary slots',size=16)]+ribbon(border(bt,'pre'),365,'preorder')+ribbon(border(bt,'in'),402,'inorder')
    s.append(state('binary','Interpret first-child as left and next-sibling as right. The same identities move into binary geometry.',ns,data={'binary':bt,'pre':border(bt,'pre'),'in':border(bt,'in')}))
    s.append(state('roundtrip','Decode sibling chains into ordered families. Every original child list and forest root is recovered.',tree_nodes(f,done=forder(f),positions=p)+ribbon(forder(f,'post'),405,'forest postorder'),r'\operatorname{decode}(\operatorname{encode}(F))=F','No nodes are created or lost.',{'decoded':forest(bt)}))
    return s

def ast_to_forest(a):
    labels={}
    def rec(a,path='a'):
        labels[path]=a[1] if a[0] in ('c','v') else {'pow':'^','neg':'−','*':'×'}.get(a[0],a[0])
        return T(path,*[rec(c,path+str(i)) for i,c in enumerate(a[1:])]) if a[0] not in ('c','v') else T(path)
    return (rec(a),),labels

def expression_states(a,env):
    f,labels=ast_to_forest(a);p=tree_positions(f,x0=35,x1=480,y0=65,dy=85)
    # Occurrence postorder aligns exactly with postfix instruction order.
    ids=forder(f,'post');value,tr=eval_postfix(postfix(a),env);out=[]
    for i,e in enumerate(tr):
        ns=tree_nodes(f,ids[i],ids[:i+1],p,labels)+stack_nodes(e['stack'],'value stack')
        ns+=ribbon([labels[v] for v in ids[:i+1]],402,'postfix')
        out.append(state('expr-'+str(i),'Read '+str(e['token'][1] if e['token'][0] in ('c','v') else e['token'][0])+'. '+('Push its value.' if e['token'][0] in ('c','v') else 'Pop the right operand last in the saved child list; apply the operator in original order.'),ns,fmt(a)+'='+str(value) if i==len(tr)-1 else '', 'Stack values represent completed subexpressions in left-to-right order.',e))
    return out

def factor_card(identity,x,y,title,ast,role='input',width=150):
    """A collapsed AST root, carrying its stable root identity and complete expression."""
    return [rect('node-'+identity,x-width/2,y-38,width,76,role),
            text('factor-title-'+identity,x,y-13,title,role,14),
            text('label-'+identity,x,y+15,fmt(ast),role,16)]

def product_bridge_states(a,path):
    u,v=a[1:];du,dv=diff(u),diff(v);uid=path+'0';vid=path+'1';duid='D-'+uid;dvid='D-'+vid
    left=('*',du,v);right=('*',u,dv);constructed=('+',left,right)
    data={'sourceNode':path,'source':a,'sourceU':u,'sourceV':v,'derivativeU':du,'derivativeV':dv,
          'identities':{'u':uid,'v':vid,'du':duid,'dv':dvid},'leftContribution':left,'rightContribution':right,
          'constructedDerivative':constructed,'derivative':diff(a)}
    out=[]
    ns=factor_card(uid,190,145,'original u · '+uid,u)+factor_card(vid,530,145,'original v · '+vid,v)
    ns +=[text('product-title',360,40,'A product has TWO sources of change','active',20),
           text('product-promise',360,245,'Keep both original factor trees unchanged',size=17),
           text('child-results',360,305,'Already computed: u′ = '+fmt(du)+'; v′ = '+fmt(dv),'result',16),
           text('product-plan',360,385,'Change u while keeping v; then keep u while changing v',size=15)]
    out.append(state('product-'+path+'-identify','Identify the original child trees u and v. Their derivatives are separate new trees; do not replace the originals.',ns,r'D(uv)=(Du)v+u(Dv)','Original u and v remain available for both product contributions.',{**data,'stage':'identify-originals'}))
    for join in [False,True]:
        ns=[]
        if join:ns+=arrow('sum-left',(360,80),(180,155),'active')+arrow('sum-right',(360,80),(540,155),'active')
        for name,opx,children in [('left',180,[(duid,95,du,'new u′ · D('+uid+')','result'),(vid,265,v,'original v · '+vid,'input')]),('right',540,[(uid,455,u,'original u · '+uid,'input'),(dvid,625,dv,'new v′ · D('+vid+')','result')])]:
            ns +=[circle('product-op-'+path+'-'+name,opx,155,'active'),text('product-op-label-'+path+'-'+name,opx,160,'×','active',20)]
            for identity,x,ast,title,role in children:
                # Connect to the card boundary, never through its text.
                ns +=[line('product-wire-'+identity,opx+(x-opx)*0.21,173,x,210,'active')]
                ns +=factor_card(identity,x,250,title,ast,role,145)
        ns +=[text('left-mechanism',180,325,'differentiate u; keep v',size=16),text('right-mechanism',540,325,'keep u; differentiate v',size=16)]
        if join:
            ns +=[circle('sum-op-'+path,360,80,'result'),text('sum-label-'+path,360,85,'+','result',22),text('product-total',360,380,'ADD the two contributions: u′·v + u·v′','result',18),text('product-no-early-simplify',360,418,'The factor 1 is still visible; simplify only after constructing both terms',size=14)]
        else:
            ns +=[text('product-title',360,60,'Construct both products before adding them','active',19),text('two-branches',360,385,'Left: '+fmt(left)+'     Right: '+fmt(right),'result',15)]
        out.append(state('product-'+path+('-join' if join else '-branches'),
          ('Join the two products with +. Only after this construction may unit factors be simplified.' if join else 'Build u′ times the ORIGINAL v and the ORIGINAL u times v′. Keep the new derivatives distinct from their source trees.'),ns,
          'D('+fmt(a)+')='+fmt(constructed) if join else r'(Du)v\qquad u(Dv)',
          'Both changing-factor contributions are present; neither original child is overwritten.',{**data,'stage':'join' if join else 'construct-products'}))
    return out

def fixed_power_bridge_state(a,path):
    u,n=a[1:];du=diff(u);exponent=Fraction(n[1]);outer=('*',n,('pow',u,C(exponent-1)));raw=('*',outer,du)
    uid=path+'0';ns=factor_card(uid,185,120,'original inside u',u,width=250)+factor_card('D-'+uid,535,120,'new inside derivative u′',du,'result',250)
    ns +=[text('power-rule-title',360,35,'A power rule still needs the inside derivative','active',19),
           text('outer-slope',360,235,'Outer slope: '+fmt(outer),'active',18),
           text('chain-factor',360,285,'CHAIN FACTOR: D('+fmt(u)+') = '+fmt(du),'result',18),
           text('raw-chain',360,350,'Multiply the outer slope by this inside derivative','active',16),
           text('keep-unit-factor',360,409,'Even an inside derivative of 1 is a computed factor',size=16)]
    return state('chain-'+path,'Apply the fixed-power rule to the outer operation, then multiply by the already-computed derivative of the inner expression. The factor '+fmt(du)+' stays visible here.',ns,
        'D('+fmt(a)+')='+fmt(raw),'The chain factor is computed before a unit factor is simplified.',
        {'sourceNode':path,'source':a,'inner':u,'innerDerivative':du,'outerDerivative':outer,'constructedDerivative':raw,'derivative':diff(a),'stage':'chain-factor'})

def diff_states(a):
    f,labs=ast_to_forest(a);p=tree_positions(f,x0=35,x1=670,y0=55,dy=74);ids=forder(f,'post');nodes={}
    def rec(a,path='a'):
        nodes[path]=a
        if a[0] not in ('c','v'):
            for i,c in enumerate(a[1:]):rec(c,path+str(i))
    rec(a);out=[]
    for i,v in enumerate(ids):
        if nodes[v][0]=='*':
            out.extend(product_bridge_states(nodes[v],v));continue
        if nodes[v][0]=='pow' and nodes[v][2][0]=='c' and Fraction(nodes[v][2][1])!=0:
            out.append(fixed_power_bridge_state(nodes[v],v))
        da=diff(nodes[v]);ns=tree_nodes(f,v,ids[:i+1],p,labs)
        # Long expressions stay in the formula/caption; concise local rewrite in SVG.
        ns +=[text('rewrite',360,382,'Differentiate node '+labs[v]+': '+('leaf rule' if nodes[v][0] in ('c','v') else nodes[v][0]+' rule'),'active',17),text('preserved',360,412,'Source tree remains unchanged',size=15)]
        out.append(state('differentiate-'+str(i),f'At {labs[v]}, use already-computed child derivatives. The local result is {fmt(da)}.',ns,'D('+fmt(nodes[v])+')='+fmt(da),'Build a new immutable AST; retain the original domain.',{'sourceNode':v,'source':nodes[v],'derivative':da}))
    d=diff(a);df,dl=ast_to_forest(d);dp=tree_positions(df,x0=30,x1=680,y0=50,dy=66)
    ns=tree_nodes(df,done=forder(df),positions=dp,labels=dl)
    for n in ns:n['id']='derived-'+n['id']
    ns +=[text('derived-title',360,405,'New derivative tree; every operator has valid arity',size=15)]
    out.append(state('derivative-tree','Assemble the derivative AST. Product and chain factors remain explicit.',ns,'D('+fmt(a)+')='+fmt(d),'The source AST is unchanged.',{'source':a,'derivative':d}))
    return out

def encoding_states(f):
    result=[state('source-tree','Start from this ordered forest; identities will move into storage order.',tree_nodes(f,positions=tree_positions(f,x0=45,x1=650,y0=70,dy=90)),data={'forest':f})]
    for kind in ('pre','family','level','post'):
        e=encode(f,kind);a=e['records'];p={r['id']:(65+i*112,165) for i,r in enumerate(a)};ns=[]
        for i,r in enumerate(a):
            x,y=p[r['id']];ns +=[rect('node-'+r['id'],x-35,y-27,70,54),text('label-'+r['id'],x,y+4,r['id']),text('address-'+r['id'],x,110,'index '+str(i),size=14),text('degree-'+r['id'],x,220,'d='+str(r['degree']),size=14)]
            if 'children' in r:
                ns +=[text('children-'+r['id'],x,257,'ch:'+(','.join(map(str,r['children']))) if r['children'] else 'ch: ∅',size=14)]
        ns +=[text('mode',360,50,kind+' order','active',20),text('provenance',360,320,'Every record keeps its source node identity',size=16)]
        if kind=='family':ns +=[text('policy',360,360,'Choose newest pending family (LIFO)',size=16)]
        if kind=='level':ns +=[text('policy',360,360,'Choose oldest pending family (FIFO queue)',size=16)]
        if kind=='post':ns +=[text('policy',360,360,'Only identities and child counts are stored',size=16)]
        result.append(state('encoding-'+kind,f'{kind.capitalize()} order: '+', '.join(r['id'] for r in a)+'. Decode and compare every ordered child list.',ns,r'\operatorname{decode}(E(F))=F','Record indices are addresses; node IDs provide provenance.',{'encoding':e,'roundtrip':decode(e)}))
    return result

def fold_states(f,values):
    local=lambda v,ch:sum((i+1)*a for i,a in enumerate(ch)) if ch else values[v]
    records=encode(f,'post')['records'];results,tr=fold_records(records,local);out=[];done=[]
    p=tree_positions(f,x0=30,x1=475,y0=55,dy=74);families=fdict(f)
    for i,e in enumerate(tr):
        v=e['node'];d=e['degree'];before=tr[i-1]['stack'][:] if i else []
        child_ids=families[v];weights=list(range(1,d+1));products=[w*x for w,x in zip(weights,e['children'])]
        common={**e,'childIds':child_ids,'weights':weights,'products':products,'stackBefore':before,'stackAfter':e['stack'][:]}
        if d==0:
            done.append(v);ns=tree_nodes(f,v,done,p)+stack_nodes([str(x) for x in e['stack']],'subtree values',x=575,y=218)
            ns +=[text('leaf-value',350,318,'Leaf '+v+': given value '+str(e['value']),'result',19),text('leaf-push',350,368,'Push this one value; no child values are consumed',size=16)]+ribbon([r['id'] for r in records[:i+1]],420,'postorder')
            out.append(state('fold-'+str(i),f'Leaf {v} has supplied value {e["value"]}. Its degree is zero, so it consumes no older stack values.',ns,'f('+v+')='+str(e['value']),'A leaf introduces its assigned value, not a sum.',{**common,'stage':'leaf'}));continue
        for stage in ['ordered-slots','weight-each-child','sum-products']:
            final=stage=='sum-products';display_stack=e['stack'] if final else before
            ns=tree_nodes(f,v,done+([v] if final else []),p)+stack_nodes([str(x) for x in display_stack],'subtree values',x=575,y=218)
            ns +=[text('operation-name',350,268,'ORDERED WEIGHTED SUM: slot i supplies weight i','active',16)]
            for j,(cid,value,w,product_value) in enumerate(zip(child_ids,e['children'],weights,products)):
                x=60+(j+.5)*(600/d);width=min(250,600/d-10)
                ns +=[rect('fold-value-'+cid,x-width/2,283,width,66,'active'),text('fold-slot-'+cid,x,304,'slot '+str(w)+': child '+cid,'active',15)]
                label=('weight '+str(w)+', value '+str(value)) if stage=='ordered-slots' else str(w)+' × '+str(value)+' = '+str(product_value)
                ns +=[text('fold-product-'+cid,x,334,label,'result' if stage!='ordered-slots' else 'input',16)]
            if final:
                ns +=[text('weighted-total',350,385,'Weighted total: '+' + '.join(map(str,products))+' = '+str(e['value']),'result',18)]
                caption=f'Add the weighted contributions {products}: their sum is {e["value"]}. Consume the original child group and push this result.'
                formula='+'.join(map(str,products))+'='+str(e['value'])
            elif stage=='weight-each-child':
                ns +=[text('weight-instruction',350,385,'Multiply EACH value by its slot number before adding',size=16)]
                caption='Keep child order. '+ '; '.join('slot '+str(w)+' contributes '+str(w)+' × '+str(x)+' = '+str(z) for w,x,z in zip(weights,e['children'],products))+'.'
                formula=r'\quad '.join(str(w)+r'\cdot '+str(x)+'='+str(z) for w,x,z in zip(weights,e['children'],products))
            else:
                ns +=[text('weight-instruction',350,385,'These are weighted slots, not plain addition of child values',size=16)]
                caption=f'For {v}, retrieve children {child_ids} in their original order. Values {e["children"]} occupy slots {weights}; slot numbers are the weights.'
                formula=r'f('+v+r')=\sum_{i=1}^{'+str(d)+r'}i\,f(c_i)'
            ns+=ribbon([r['id'] for r in records[:i]],420,'completed before '+v)
            out.append(state('fold-'+str(i)+'-'+stage,caption,ns,formula,'Child identity, order, value and slot weight stay bound together.',{**common,'stage':stage,'stack':display_stack[:]}))
        done.append(v)
    return out


def linked_states(f):
    p=tree_positions(f,x0=45,x1=650,y0=65,dy=90);d=fdict(f);parents={c:v for v,ch in d.items() for c in ch};out=[]
    for layer in ('first child','next sibling','parent'):
        ns=tree_nodes(f,positions=p);links=[]
        if layer=='first child':links=[(v,ch[0]) for v,ch in d.items() if ch]
        if layer=='parent':links=list(parents.items())
        if layer=='next sibling':links=[(a,b) for ch in [[t[0] for t in f]]+list(d.values()) for a,b in zip(ch,ch[1:])]
        for u,v in links:ns +=arrow('layer-'+u+v,p[u],p[v],'active',layer=='parent')
        ns +=[text('layer-label',360,355,layer.upper()+' field','active',19),text('cost-label',360,402,'One field means one precisely specified relation',size=16)]
        out.append(state('links-'+layer.replace(' ','-'),'Inspect the '+layer+' links. They answer a different navigation question from the other fields.',ns,data={'layer':layer,'links':links,'parents':parents}))
    return out

def union_states(n,pairs):
    out=[]
    for i,e in enumerate(union_trace(n,pairs)):
        p=e['parent'];roots=[v for v in range(n) if p[v]==v]
        def sub(v):return T(str(v),*[sub(w) for w in range(n) if p[w]==v and w!=v])
        f=tuple(sub(r) for r in roots);pos=tree_positions(f,x0=45,x1=660,y0=80,dy=85);ns=tree_nodes(f,positions=pos)
        ns +=[text('merge',360,360,'relation '+str(e['pair'][0])+' ≡ '+str(e['pair'][1]),'active',18),text('representatives',360,402,'Find roots '+str(e['roots'])+'; merge only if different',size=15)]
        out.append(state('union-'+str(i),'Find the two representatives, then link one root to the other if they differ.',ns,r'a\equiv b\iff \operatorname{root}(a)=\operatorname{root}(b)','Parent pointers form a forest; roots point to themselves in this model.',e))
    return out

def poly_nodes(t):
    labels={};edge_labels={};links={}
    def rec(t,path='p',parent=None):
        labels[path]=str(t) if isinstance(t,int) else t['var']
        if isinstance(t,int):ch=[]
        else:
            ch=[]
            for e,z in t['terms'].items():
                kid=path+'e'+e;ch.append(rec(z,kid,path));edge_labels[(path,kid)]=e
        links[path]={'parent':parent,'children':[c[0] for c in ch]}
        return T(path,*ch)
    f=(rec(t),);p=tree_positions(f,x0=45,x1=670,y0=65,dy=102);ns=tree_nodes(f,positions=p,labels=labels)
    for (u,v),e in edge_labels.items():
        x,y=p[u];xx,yy=p[v];ns +=[text('exponent-'+v,(x+xx)/2+15,(y+yy)/2,'e='+e,size=14)]
    return ns,links

def polynomial_states(p,q):
    out=[];flat=poly_flat(p);inputs=[('start',p,'Start with P. Coefficients live below decreasing variable names.')]
    for k,c in sorted(poly_flat(q).items()):
        flat[k]=flat.get(k,0)+c;t=poly_tree(flat)
        inputs.append(('term-'+str(k),t,f'Add coefficient {c} at exponent vector {k}. Combine like terms, remove zeros and collapse constant-only variable levels.'))
    for i,(_,t,cap) in enumerate(inputs):
        ns,links=poly_nodes(t);ns +=[text('canonical',360,385,'Ordered exponents; no zero positive-exponent branch',size=15),text('root-kind',360,414,'root: '+('constant' if isinstance(t,int) else 'variable '+t['var']),'active',16)]
        out.append(state('poly-'+str(i),cap,ns,r'P=\sum_e g_e\,v^e','Highest variable is outermost; exponent zero is always represented.',{'tree':t,'flat':[{'exponents':list(k),'coefficient':c} for k,c in sorted(poly_flat(t).items())],'links':links}))
    return out

def build_middle():
    lessons=[]
    dm=demo('forest-binary','Keep first children and chain siblings','left-child-right-sibling',conversion_states(F),conversion_states(SMALLF),'U has child V, and W is a second root.','U.left is V; U.right is W. W is U’s sibling in the forest, not its child.',check('Forest A(B,C),D is encoded with first-child/next-sibling links. What is binary inorder?',['B C A D','A B C D','C B D A'],0,'Forest postorder B C A D equals binary inorder under this encoding.'),check('U has child V and the next forest root is W. Which binary link reaches W from U?',['Left','Right','Neither'],1,'Right means next sibling, including the chain of forest roots.'),{'forest':F,'binary':binary(F)})
    lessons.append(lesson(112,[passage('two-links','An arbitrary-size family needs only two link kinds','In an ordered forest, store L(v) as the first child of v, or null if it has none. Store R(v) as v’s next sibling, or null if it is the last. Chain the forest roots as siblings too. Now reinterpret L and R as binary left and right children. The representation uses one binary node per forest node; it never needs a separate array sized to the largest family.',demonstration=dm),passage('bijection','Decode by following sibling chains','An empty forest maps to the empty binary tree. For a nonempty forest with first tree (v,C) and remaining forest S, its encoding is (v,encode(C),encode(S)). Conversely, the left subtree decodes to v’s child forest and the right subtree decodes to the remaining roots. Structural induction on node count proves these operations are inverses. This is a bijection between ordered forests and binary trees, not between one rooted tree and every binary tree.',r'\beta((v,C),S)=(v,\beta(C),\beta(S))'),passage('order-match','The traversal correspondence has an easy trap','Forest preorder emits a root, then its child forest, then its remaining sibling forest: precisely binary preorder. Forest postorder emits children, then the root, then remaining siblings: precisely binary inorder. Binary postorder instead visits the remaining sibling forest before the root, so it is generally different. In the worked forest, preorder is A B C D E F and forest postorder is B D C A F E.',r'\mathrm{pre}(F)=\mathrm{pre}(\beta(F)),\quad\mathrm{post}(F)=\mathrm{in}(\beta(F))'),passage('meaning','Binary ancestry is representation ancestry','A forest sibling becomes a binary descendant along a right link. Therefore “parent” in the binary encoding is not automatically the original forest parent. Any algorithm that needs original parenthood must interpret the link meanings or store additional parent links. Empty forests, several roots, long sibling chains and one-child chains all round-trip; node identities and left-to-right family order are preserved.')],'Exact forest/binary bijection and traversal correspondences, with round-trip models.','531–535'))
    expr=('/',('-',C(14),C(5)),C(3));small=('-',C(8),C(3))
    dm=demo('expression-stack','Operators consume ordered operands','arity-checked-expression',expression_states(expr,{}),expression_states(small,{}),'Place 8 then 3 on a stack; the subtraction node combines them as 8−3.','Postfix delays the operator until its operands are ready; stack pop order must be corrected to source child order.',check('Postfix tokens 18 6 3 / - denote which value?',['4','16','-16'],1,'Compute 6/3=2 first, then 18−2=16. The top operand is the right one.'),check('For postfix 8 3 -, which operand is subtracted?',['8','3','Both'],1,'The most recently pushed value is the right operand.'),{'ast':expr,'postfix':postfix(expr),'value':str(ev(expr,{}))})
    lessons.append(lesson(113,[passage('meaningful-arity','Syntax is part of the data structure','An expression tree has one operator or operand at every node. Constants and variables have arity zero; unary negation and logarithm have arity one; addition, subtraction, multiplication, division and exponentiation have arity two here. Arity is a property of the operator, not a guess from nearby symbols. Unary negation and binary subtraction must be represented by different operation tags even when both print a minus sign.',demonstration=dm),passage('polish','Prefix and postfix need operator signatures','Preorder lists an operator before its operands, producing prefix notation. Postorder lists it after its operands, producing postfix notation. With known arities and unambiguous operand tokens, a parser can recover the tree without parentheses. A label sequence alone is insufficient when arities are unspecified: “−” could consume one item or two. The executable evaluator validates arity and rejects missing operands or extra roots.'),passage('evaluation','The top of the stack is the rightmost child','Scan postfix from left to right. Push an operand’s value. At a d-ary operator, remove the top d values as a group in their existing bottom-to-top order, evaluate the operator on that ordered group, and push the result. For binary subtraction, pop the right operand b, then the left a, and compute a−b. Reversing that order is invisible for addition and multiplication, which makes subtraction and division essential tests.',r'\text{stack }[\ldots,a,b]\xrightarrow{-}[\ldots,a-b]'),passage('domain','A valid syntax tree can still have undefined value','Arity correctness does not imply numerical definedness. A division node requires a nonzero denominator; a real logarithm requires a positive argument. Missing variable bindings are errors too. This model evaluates rational arithmetic exactly with fractions and exposes division by zero. It does not silently return a made-up value, and it does not claim that every syntactically valid expression is defined for all real inputs.')],'Expression arity, prefix/postfix and exact stack evaluation; full language parsing and optimization are outside scope.','535–537'))
    expr=('*',V(),('pow',('+',V(),C(2)),C(2)));small=('pow',('+',V(),C(1)),C(2))
    dm=demo('differentiate-ast','Produce a new expression tree','symbolic-derivative-ast',diff_states(expr),diff_states(small),'Differentiate (x+1)²: first the inside, then the square.','The chain factor is the derivative of the inside; the product rule separately accounts for changing each factor.',check('With a constant a, what is d[a(x²+1)]/dx?',['a(2x)','a′(x²+1) only','2a'],0,'a is constant with respect to x, so its derivative is zero and the remaining factor contributes 2x.'),check('For (3x+1)², which chain factor multiplies 2(3x+1)?',['1','3','2'],1,'The inside 3x+1 has derivative 3.'),{'source':expr,'derivative':diff(expr),'exactValues':[{'x':x,'derivative':str(ev(diff(expr),{'x':Fraction(x)}))} for x in (-2,0,3)]})
    lessons.append(lesson(114,[passage('postorder-transform','Differentiate structure, not printed characters','Traverse the source expression in postorder. A leaf yields derivative 1 if it is the selected variable x, otherwise 0; every other variable is held constant. At each operator, combine the already-computed child derivatives with the original child expressions. The result is a new immutable AST. Source occurrences remain unchanged, and reused immutable subexpressions are safe; a mutable pointer implementation would need copies or an explicit sharing policy.',demonstration=dm),passage('product-chain','Why two product terms and an inside factor appear','For differentiable u and v, subtract u(x)v(x) from u(x+h)v(x+h), then add and subtract u(x+h)v(x). Divide by h. The two resulting difference quotients converge to u′v and uv′ because differentiability implies continuity. This proves the product rule. For a composite g(u(x)), the chain rule multiplies g′(u(x)) by u′(x); when the inner increment vanishes, the derivative definition supplies the same limit. Thus x(x+2)² differentiates to (x+2)²+x·2(x+2), including both sources of change.',r'D(uv)=(Du)v+u(Dv),\qquad D(g\circ u)=(g\prime\circ u)Du'),passage('rules-domain','Carry conditions with local rewrite rules','Addition, subtraction and negation act on derivatives componentwise. D(ln u)=Du/u for u>0. The quotient rule is ((Du)v−u(Dv))/v² for v≠0. For a fixed integer n, D(uⁿ)=n·uⁿ⁻¹Du wherever the power is defined and differentiable, with the zero-exponent constant handled separately. For variable real exponent v, D(uᵛ)=uᵛ[(Dv)ln u+v(Du)/u] on u>0; this follows by writing uᵛ=exp(v ln u) and applying product and chain rules. We do not extend that logarithmic formula blindly to negative bases.',r'D(u^v)=u^v\left((Dv)\ln u+v\frac{Du}{u}\right)\quad(u>0)'),passage('simplify-carefully','A shorter formula must keep the original domain','The constructor removes simple zero and unit factors, but it is not a complete algebra system. The derivative still carries the source domain separately: simplifying 0·(1/x) to 0 must not claim the source was defined at x=0. Correctness of the transformation follows by structural induction using the calculus rules at each node. Exact rational polynomial and quotient checks independently test the program; finite differences, when used, are only approximate diagnostics and never a proof.')],'Executed immutable AST differentiation for arithmetic, negation, logarithm, exponential and powers; simple local simplification, not canonical symbolic algebra. Source rules visually verified on PDF537.','537–542'))
    dm=demo('sequence-orders','Move identities into sequential storage','forest-sequential-encodings',encoding_states(F),encoding_states(SMALLF),'Place U, its child V, and the other root W onto a strip.','An address is a position on the strip; provenance remembers which node was moved there.',check('Roots A and D have children B and E respectively; B has child C. Which level order is correct?',['A B C D E','A D B E C','A D E B C'],1,'A queue lists both roots, then their children, then the grandchild.'),check('For forest U(V),W, which node appears first in postorder?',['U','V','W'],1,'V must appear before its parent U.'),{'forest':F,'encodings':[encode(F,k) for k in ('pre','family','level','post')]})
    lessons.append(lesson(115,[passage('storage-order','Traversal order can replace some explicit links','A sequential representation assigns consecutive addresses to nodes in a chosen order. Our demonstration keeps IDs, child indices and degrees for preorder, family order and level order, deliberately retaining redundant provenance so every relationship can be checked. Its postorder format stores only IDs and degrees. These teaching records are not a claim to reproduce the book’s exact packed memory layout or its byte counts.',demonstration=dm),passage('pre-scope','Preorder makes each subtree a contiguous interval','In preorder, a nonleaf’s first child is next in storage. Every subtree occupies one consecutive interval; a SCOPE address can name the first address after that interval. A leaf at address i has scope i+1 when nodes occupy one word. The source discusses replacing explicit child links and recovering some tags from a full scan. Recoverability is not free random access: omitting a field can save space but increase navigation work.',r'\mathrm{subtree}(v)=[\mathrm{addr}(v),\mathrm{scope}(v))'),passage('family-level','Two ways to choose the next family','Family order first lists forest roots. Then list the children of the most recently listed node whose family is not yet processed: pending families form a stack. Equivalently it is reverse binary postorder under the first-child/next-sibling encoding. Level order instead processes pending families in FIFO order, so all depth-k nodes precede depth-(k+1) nodes. A queue is essential; replacing it with a stack produces family order, not breadth-first order.'),passage('post-degrees','Postorder with degrees reconstructs child groups','For each postorder record (v,d), pop the top d already-completed trees as an ordered group, make them v’s children, and push that tree. Degree zero consumes nothing. The sequence is invalid if d is negative or exceeds the stack size; duplicate IDs are invalid in this identity-preserving model. At the end, remaining trees are forest roots. A single-tree encoding must leave exactly one; a valid forest may leave several. This is a different representation-specific sufficiency claim from preorder tag redundancy.')],'Four executed, round-tripped sequential orders with explicit format provenance; compact SCOPE/tag/link-node variants explained rather than simulated as MIX storage.','554–559'))
    vals={'B':7,'D':2,'F':4};sv={'V':3,'W':2}
    dm=demo('bottom-up-fold','Consume exactly the completed child group','postorder-degree-fold',fold_states(F,vals),fold_states(SMALLF,sv),'A parent waits until its child’s value is ready.','Degree tells exactly how many finished subtree results to consume, not how many arbitrary recent nodes.',check('The top child values are [4,9], left to right. For f(v)=f(c₁)+2f(c₂), what is the result?',['17','22','13'],1,'Keep child order: 4+2·9=22. Reversing gives 17.'),check('After folding U(V),W, how many root values remain?',['One','Two','Three'],1,'U’s and W’s trees are separate forest roots.'),{'forest':F,'leafValues':vals,'records':encode(F,'post')['records']})
    lessons.append(lesson(116,[passage('local-function','A function may depend on the node and its child results','Suppose f(v) can be computed from v and the ordered values f(c₁),…,f(c_d) of its children. Examples include subtree size, height, expression value, and structural checksums. Process nodes in postorder, so these inputs exist before v is evaluated. Our worked function assigns specified integer values to leaves and, at a nonleaf, uses the weighted sum Σ i·f(cᵢ); this intentionally makes child order matter.',demonstration=dm),passage('consume-group','The top d results belong together','Maintain a stack of completed subtree results. At a record of degree d, the top d entries, from bottom to top within that group, are f(c₁),…,f(c_d). Read them in that order, remove them, then push f(v). For d=0, do not use the programming-language slice “everything after −0”: it would consume the entire stack. The executable model handles zero explicitly and rejects underflow.',r'[\ldots,f(c_1),\ldots,f(c_d)]\longmapsto[\ldots,f(v)]'),passage('induction-fold','The proof restores the older stack prefix','Fix an arbitrary stack prefix before a subtree’s postorder block. For a leaf, push its value and leave the prefix untouched. By induction, each child block adds exactly its child result above that prefix, in family order. The parent step consumes those d results and replaces them by f(v). Therefore the whole block adds exactly one result without disturbing older completed trees. Repeating this across a forest leaves one result per root.'),passage('work-fold','Separate traversal cost from local computation','The structural stack work is linear in the number of nodes because each result is pushed once and popped at most once. Total computation also includes the costs of the local functions; symbolic expressions can grow large, so linear visits do not imply linear output size. A star can leave many child results on the stack even though its height is small. Unlike the ancestor stack for binary inorder, this value stack is not automatically bounded by tree height.')],'Exact integer bottom-up Algorithm F with ordered child groups, forest outputs and a size-induction correctness proof.','558–559'))
    dm=demo('link-layers','Choose the question each field answers','parent-child-sibling-links',linked_states(F),linked_states(SMALLF),'One rope goes down to the first child; another goes back to the parent.','Each rope type is a separate field with a different relation.',check('Only PARENT links are stored for n nodes. Without an index, how do you list every child of v?',['Read one fixed field','Scan potential nodes and compare parents','Follow v’s parent once'],1,'Upward links encode structure but do not provide a direct child enumeration index.'),check('V is the first child of U. What should PARENT(V) contain?',['U','V','W'],0,'A real parent field returns the forest parent, not the next sibling.'),{'forest':F})
    ud=demo('equivalence-forest','Merge equivalence classes through roots','parent-forest-union',union_states(5,[(0,1),(2,3),(1,2),(0,3),(3,4)]),union_states(3,[(0,1),(1,2)]),'Join two groups by tying one root to the other.','Root equality is a test for membership in the same equivalence class.',check('A pair already has equal representatives. What should a simple union routine do?',['Add a back edge','Leave the forest unchanged','Split both groups'],1,'Joining equal roots can create cycles; the relation is already implied.'),check('After 0≡1 and 1≡2, are 0 and 2 in one class?',['Yes','No'],0,'Transitivity puts all three in one class.'),{'pairs':[(0,1),(2,3),(1,2),(0,3),(3,4)]})
    lessons.append(lesson(117,[passage('navigation-fields','Add fields for the operations you need','First-child and next-sibling links efficiently enumerate families. Adding PARENT lets each node reach its original parent in one pointer read; adding a previous-sibling link makes backward sibling movement direct. These are separate meanings. A binary inorder thread may lead to an ancestor but is not generally the forest parent. Null, child and thread states must not be confused just because their machine fields have the same width.',demonstration=dm),passage('reciprocity','An update must restore every advertised relation','If a node is inserted between siblings a and b in a doubly linked family, update a.next, new.prev, new.next and b.prev, as well as the new node’s parent. If insertion changes the first child, update the parent’s first-child field too. Empty and one-child families require boundary handling. Circular/ring conventions replace null family ends by specified return links; the sentinel policy must be stated before traversal. More links usually simplify some navigation while increasing update obligations and storage.'),passage('equivalence','Parent-only trees are useful for equivalence classes','An equivalence relation is reflexive, symmetric and transitive, and partitions a set into disjoint classes. Start with each element as its own root. To process a pair a≡b, follow parent links to both roots and, if they differ, attach one root to the other. Representatives agree exactly when the processed relations imply membership in the same class. Our model uses root.parent=root, unlike the source’s null-root sentinel; neither convention changes the partition.',r'a\equiv b\iff\mathrm{root}(a)=\mathrm{root}(b)',ud),passage('cost-representation','State costs before claiming a better representation','Parent-only storage uses one link per node, but finding every child may require a whole scan. Simple union by root linking can form a chain, so find can take O(n) steps; this unit does not silently credit it with the stronger bounds of rank balancing and path compression. Three- or four-directional links cost correspondingly more fields. Moving INFO values into newly created leaves can permit field sharing, but also increases node count; reduced field width alone does not prove a memory saving.')],'Parent/child/sibling and ring tradeoffs, field reciprocity, INFO relocation, and executed elementary equivalence Algorithm E; optimized union-find is not claimed.','559–565'))
    p=poly_tree({(1,1):2,(0,1):3,(2,0):1});q=poly_tree({(1,1):-2,(0,1):-3,(2,0):-1,(0,0):5})
    sp=poly_tree({(1,0):3,(0,0):1});sq=poly_tree({(1,0):-3})
    dm=demo('polynomial-trie','Merge coefficients and collapse canceled levels','canonical-polynomial-tree',polynomial_states(p,q),polynomial_states(sp,sq),'Two x drawers contain +3 and −3; their sum disappears, leaving the constant 1.','Variable nodes group equal exponents; normalization removes canceled positive-exponent branches.',check('With variable order x<y, what root remains after adding y(x+1) and −y(x+1)+7x?',['y','x','a zero constant'],1,'All y terms cancel, leaving 7x; a constant-only y level is collapsed.'),check('What remains from 3x+1 plus −3x?',['x','1','0'],1,'Only matching x coefficients cancel.'),{'P':p,'Q':q,'sum':poly_add(p,q)})
    lessons.append(lesson(118,[passage('recursive-polynomial','A coefficient can itself be a polynomial','Fix a variable order, here x<y. A polynomial is either a constant or a sum Σ gₑvᵉ, where v is the highest variable still present and every coefficient gₑ uses only lower variables. Store exponents in increasing order, include exponent zero even when its coefficient is zero, and omit zero coefficients at positive exponents. The child reached along exponent e is the coefficient polynomial, not another copy of the monomial.',r'P=\sum_e g_e v^e,\qquad \operatorname{vars}(g_e)<v',dm),passage('canonical','Normalization chooses a unique structural form','Combine equal exponent vectors, discard zero terms, and choose the highest variable with a positive exponent. Recursively normalize each coefficient. If no positive exponent survives, collapse the variable node to its constant coefficient; if everything cancels, use one zero constant. For a fixed variable order and exact coefficients, this yields a canonical recursive structure. The term dictionary in the model is an independent representation used to check that normalization preserves the polynomial.'),passage('addition','Merge equal powers, then repair structure','To add two polynomials, align their outer variables, group matching exponents and recursively add the coefficients. A coefficient may become zero and remove a branch; cancellation can make the entire root become a lower-variable polynomial or a constant. Our executable teaching model rebuilds normalized immutable nodes from exact exponent dictionaries. Its materialized parent/child view is rebuilt consistently after each step; it does not claim to execute the source’s in-place four-directional ring Algorithm A.'),passage('links-and-cost','The trie is algebra, the ring is an implementation','The source stores UP, DOWN, LEFT and RIGHT links, together with exponent EXP and coefficient-or-variable CV. This demonstration actually mutates a bounded instance: insert a fresh coefficient into the circular sibling ring, cancel and unlink it, collapse a constant-only coefficient, then collapse the root from y to x. The surviving x children retain their identities, but their UP links must be changed to the surviving root address. Each committed operation is checked against an independent exponent dictionary; noncanonical intermediate headers are explicitly marked. This executes the insertion, unlink and collapse mechanics, not every branch of general Algorithm A. Tree storage is not always smaller or faster than a sparse list; workload and coefficient costs determine that tradeoff.')],'Canonical recursive multivariate polynomial trees and exact addition/cancellation. Source recursive formula visually checked on PDF565; in-place ring algorithm is explained, not claimed executed.','565–570'))
    return lessons

class MutablePolynomialRing:
    """Bounded mutation primitives on source-style UP/DOWN/LEFT/RIGHT/EXP/CV nodes.
    Root LEFT/RIGHT self-links are a harmless explicit convention for unused fields.
    Each nonconstant has a circular ordered coefficient ring, starting at exponent 0.
    """
    def __init__(self,t):
        self.pool={};self.serial=0;self.root=self.allocate(t,None,0)
    def allocate(self,t,up,exp):
        v='r'+str(self.serial);self.serial+=1
        self.pool[v]={'UP':up,'DOWN':None,'LEFT':v,'RIGHT':v,'EXP':exp,'CV':t if isinstance(t,int) else t['var']}
        if not isinstance(t,int):
            members=[self.allocate(ch,v,int(e)) for e,ch in t['terms'].items()]
            self.pool[v]['DOWN']=members[0]
            for i,w in enumerate(members):self.pool[w]['LEFT']=members[i-1];self.pool[w]['RIGHT']=members[(i+1)%len(members)]
        return v
    def children(self,v):
        start=self.pool[v]['DOWN']
        if start is None:return []
        ans=[];w=start
        while True:
            assert w in self.pool and w not in ans,'broken/cyclic ring'
            ans.append(w);w=self.pool[w]['RIGHT']
            if w==start:return ans
    def term(self,v,e):return next(w for w in self.children(v) if self.pool[w]['EXP']==e)
    def as_tree(self,v=None):
        v=self.root if v is None else v;n=self.pool[v]
        return n['CV'] if n['DOWN'] is None else {'var':n['CV'],'terms':{str(self.pool[w]['EXP']):self.as_tree(w) for w in self.children(v)}}
    def validate(self,canonical=True):
        seen=set()
        def walk(v,parent):
            assert v not in seen;seen.add(v);n=self.pool[v];assert n['UP']==parent
            if n['DOWN'] is None:assert isinstance(n['CV'],int);return
            assert n['CV'] in ('x','y');ch=self.children(v);exps=[self.pool[w]['EXP'] for w in ch]
            assert exps==sorted(set(exps)) and exps[0]==0
            if canonical:assert len(ch)>=2
            for w in ch:
                z=self.pool[w];assert self.pool[z['LEFT']]['RIGHT']==w and self.pool[z['RIGHT']]['LEFT']==w
                if z['DOWN'] is not None:assert z['CV']<n['CV']
                if canonical and z['EXP']>0:assert poly_flat(self.as_tree(w))
                walk(w,v)
        walk(self.root,None);assert seen==set(self.pool),'unreachable live allocation'
        if canonical:assert self.as_tree()==poly_tree(poly_flat(self.as_tree()))
    def insert_constant(self,parent,exp,value):
        assert exp>0 and value!=0
        children=self.children(parent);assert all(self.pool[w]['EXP']!=exp for w in children)
        before=next((w for w in children if self.pool[w]['EXP']>exp),children[0]);after=self.pool[before]['LEFT']
        fresh=self.allocate(value,parent,exp);self.pool[fresh]['LEFT']=after;self.pool[fresh]['RIGHT']=before
        self.pool[after]['RIGHT']=fresh;self.pool[before]['LEFT']=fresh
        self.validate();return fresh
    def cancel_constant_term(self,parent,exp,delta):
        w=self.term(parent,exp);n=self.pool[w];assert exp>0 and n['DOWN'] is None
        assert n['CV']+delta==0,'this bounded primitive handles exact cancellation'
        left,right=n['LEFT'],n['RIGHT'];assert left!=w and right!=w
        self.pool[left]['RIGHT']=right;self.pool[right]['LEFT']=left
        del self.pool[w];self.validate(canonical=False);return w
    def collapse(self,v):
        children=self.children(v);assert len(children)==1;zero=children[0];z=self.pool[zero];assert z['EXP']==0
        retained=self.children(zero);self.pool[v]['CV']=z['CV'];self.pool[v]['DOWN']=z['DOWN']
        for w in retained:self.pool[w]['UP']=v
        del self.pool[zero];self.validate(canonical=True)
        return {'retired':zero,'reparented':retained}

def ring_mutation_trace(small=False):
    terms={(0,0):1,(1,0):2} if small else {(1,0):1,(0,1):3,(1,1):2}
    m=MutablePolynomialRing(poly_tree(terms));expected=dict(terms);trace=[]
    def snap(action,focus=(),canonical=True):
        m.validate(canonical);assert poly_flat(m.as_tree())=={k:v for k,v in expected.items() if v}
        trace.append({'action':action,'root':m.root,'nodes':copy.deepcopy(m.pool),'tree':m.as_tree(),'focus':list(focus),'canonical':canonical,'flat':[{'exponents':list(k),'coefficient':v} for k,v in sorted(expected.items()) if v]})
    snap('Begin with reciprocal coefficient rings and correct parent links.')
    target=m.root if small else m.term(m.root,1)
    fresh=m.insert_constant(target,2,5);expected[(2,0) if small else (2,1)]=5
    snap('Insert a fresh exponent-2 coefficient. Repair both neighboring LEFT/RIGHT links and set its UP.',[fresh,target])
    gone=m.cancel_constant_term(target,2,-5);expected[(2,0) if small else (2,1)]=0
    snap('Cancel the exponent-2 coefficient and unlink it from both directions of the ring.',[target])
    gone=m.cancel_constant_term(target,1,-2);expected[(1,0) if small else (1,1)]=0
    snap('Cancel exponent 1. Only exponent zero remains: this intermediate header now needs collapse.',[target],False)
    info=m.collapse(target)
    snap('Collapse the coefficient header into its constant term while preserving its outer parent and sibling links.',[target])
    if not small:
        gone=m.cancel_constant_term(m.root,1,-3);expected[(0,1)]=0
        snap('Cancel the remaining y coefficient and unlink its node. The y root has only its exponent-zero coefficient.',[m.root],False)
        info=m.collapse(m.root)
        snap('Collapse the root from y to x. Keep the x coefficient children and repair every retained child’s UP to the surviving root.',[m.root]+info['reparented'])
    return trace

def ring_mutation_states(small=False):
    trace=ring_mutation_trace(small);out=[];previous={}
    for i,e in enumerate(trace):
        nodes=e['nodes'];labels={}
        def child_ids(v):
            start=nodes[v]['DOWN'];ans=[]
            if start is None:return ans
            w=start
            while not ans or w!=start:ans.append(w);w=nodes[w]['RIGHT']
            return ans
        def rec(v):labels[v]=v;return T(v,*[rec(w) for w in child_ids(v)])
        f=(rec(e['root']),);pos=tree_positions(f,x0=45,x1=515,y0=50,dy=85);ns=tree_nodes(f,positions=pos,labels=labels)
        ns +=[text('address-lane-title',610,35,'address: CV / EXP',size=14)]
        for row,(v,(x,y)) in enumerate(pos.items()):
            n=nodes[v]
            ns +=[text('address-'+v,610,69+row*30,v+': '+str(n['CV'])+(' / e'+str(n['EXP']) if n['UP'] else ' / ROOT'),size=14)]
            if v in e['focus'] and n['UP']:
                ns+=arrow('up-'+v,(x,y),pos[n['UP']],'active',True)
        # Show the selected sibling ring, including the wraparound, with R/L reciprocity explicit.
        selected=next((v for v in e['focus'] if nodes[v]['DOWN']),next((v for v in nodes if nodes[v]['DOWN'] and all(nodes[w]['DOWN'] is None for w in child_ids(v))),e['root']))
        ch=child_ids(selected)
        if len(ch)>1:
            for j,v in enumerate(ch):
                w=nodes[v]['RIGHT'];a=pos[v];b=pos[w]
                if j==len(ch)-1:
                    x,y=a;xx,yy=b;ns +=[{'id':'ring-'+v,'type':'path','d':f'M {x} {y+48} Q {(x+xx)/2} {y+95} {xx} {yy+48}','fill':'none','strokeWidth':2,'role':'active','arrow':True}]
                else:ns+=arrow('ring-'+v,(a[0],a[1]+8),(b[0],b[1]+8),'active')
            ns+=[text('reciprocal-ring',360,345,'Ring invariant: RIGHT(LEFT(v)) = v = LEFT(RIGHT(v))',size=14)]
        for v,xy in previous.items():
            if v not in pos:
                ns +=[{**circle('node-'+v,*xy),'opacity':0},{**text('label-'+v,xy[0],xy[1]+5,''),'opacity':0}]
        previous=pos
        ns +=[text('ring-action',360,384,'Live nodes: '+str(len(nodes))+'; canonical: '+str(e['canonical']),'result',16),text('ring-hint',360,415,'Straight: DOWN family; curved orange: UP / ring return',size=14)]
        out.append(state('mutable-ring-'+str(i),e['action'],ns,'','Every live child has the correct UP; every sibling link is reciprocal.',e))
    return out

def graph_nodes(vertices,edges,active_edges=(),directed=False,positions=None,counts=None,cursor=None):
    p=positions or {v:(360+235*math.cos(2*math.pi*i/len(vertices)-math.pi/2),210+145*math.sin(2*math.pi*i/len(vertices)-math.pi/2)) for i,v in enumerate(vertices)};ns=[];used_labels=[]
    for i,(u,v) in enumerate(edges):
        role='active' if i in active_edges else 'input'
        if u==v:
            x,y=p[u];sgn=1 if y<130 else -1;ns +=[{'id':'arc-'+str(i),'type':'path','arrow':True,'d':f'M {x-12} {y+sgn*17} C {x-85} {y+sgn*80} {x+85} {y+sgn*80} {x+12} {y+sgn*17}','fill':'none','role':role,'strokeWidth':3},text('arc-label-'+str(i),x,y+sgn*62,'e'+str(i),size=14)]
        else:
            curved=directed and ((v,u) in edges[:i] or (u,v) in edges[:i])
            if directed:ns+=arrow('arc-'+str(i),p[u],p[v],role,curved)
            else:
                ax,ay=p[u];bx,by=p[v];dx,dy=bx-ax,by-ay;length=math.hypot(dx,dy)
                ns +=[line('arc-'+str(i),ax+22*dx/length,ay+22*dy/length,bx-22*dx/length,by-22*dy/length,role)]
            x,y=p[u];xx,yy=p[v];lab='e'+str(i)+((':'+str(counts[i])) if counts is not None else '')
            lx=(x+xx)/2+12;ly=((y+yy)/4+min(y,yy)/2-29) if curved else (y+yy)/2-9
            width=len(lab)*8
            for ox,oy in [(0,0),(-30,22),(30,-22),(-35,-30),(35,30),(0,48)]:
                tx,ty=lx+ox,ly+oy
                if all(abs(tx-px)>(width+pw)/2+4 or abs(ty-py)>18 for px,py,pw in used_labels):break
            used_labels.append((tx,ty,width));ns +=[text('arc-label-'+str(i),tx,ty,lab,role,14)]
    for v,(x,y) in p.items():ns +=[circle('node-'+v,x,y,'active' if v==cursor else 'input'),text('label-'+v,x,y+5,v)]
    if cursor in p:ns +=[circle('walker',p[cursor][0]-28,p[cursor][1]-26,'active',7)]
    return ns

def surgery_states(n=4):
    vs=[chr(65+i) for i in range(n)];steps=[[]]+[[(vs[j],vs[j+1]) for j in range(i)] for i in range(1,n)]+[[(vs[j],vs[j+1]) for j in range(n-1)]+[(vs[0],vs[-1])]]
    out=[]
    for i,es in enumerate(steps):
        c=len(components(vs,es));r=cycle_rank(vs,es);ns=graph_nodes(vs,es,active_edges=[len(es)-1])+[text('graph-counts',360,395,f'n={n}; m={len(es)}; components={c}; cycle rank={r}',size=16)]
        cap='Start with isolated vertices.' if not es else 'Add an edge between different components; they merge.' if r==0 else 'An extra edge inside one component creates a cycle.'
        out.append(state('surgery-'+str(i),cap,ns,r'm-n+c='+str(r),'For a forest, m=n−c.',{'vertices':vs,'edges':es,'components':components(vs,es),'cycleRank':r}))
    # Delete an actual tree edge rather than a cycle edge: independently disconnect the tree.
    es=steps[-2][1:];c=len(components(vs,es));out.append(state('delete-bridge','Return to the tree, then remove its first edge. The graph disconnects.',graph_nodes(vs,es)+[text('graph-counts',360,395,f'components={c}; edges={len(es)}',size=17)],data={'vertices':vs,'edges':es,'components':components(vs,es),'cycleRank':cycle_rank(vs,es)}))
    return out

FLOW_V=['S','A','B','T'];FLOW_E=[('S','A'),('A','T'),('S','B'),('B','A'),('A','S')]
FLOW_P=[1,1,0,0,0];FLOW_C=[[-1,0,1,1,0],[1,0,0,0,1]]
def flow_states(small=False):
    if small:
        vs=['S','A','T'];es=[('S','A'),('A','T'),('A','S')];rows=[([1,1,0],'One trip follows S→A→T.'),([2,1,1],'Add one closed detour S→A→S, then finish at T.')]
    else:
        vs=FLOW_V;es=FLOW_E;rows=[(FLOW_P,'A spanning-tree path carries one unit from S to T.'),(FLOW_C[0],'A fundamental cycle is signed: −1 cancels one traversal of e0.'),(FLOW_C[1],'The second fundamental cycle has zero divergence.'),([2,1,1,1,2],'Add the path plus C1 plus 2C2. All resulting counts are nonnegative integers.')]
    p={'S':(100,200),'A':(350,100),'B':(350,300),'T':(620,200)};out=[]
    for i,(row,cap) in enumerate(rows):
        b=divergence(vs,es,row);ns=graph_nodes(vs,es,[j for j,x in enumerate(row) if x],True,{v:p[v] for v in vs},row)
        ns +=[text('balance',360,390,'out − in: '+', '.join(v+'='+str(b[v]) for v in vs),size=15)]
        out.append(state('flow-'+str(i),cap,ns,r'Bf=\mathbf1_S-\mathbf1_T' if sum(abs(x) for x in b.values()) else r'Bc=0','Signs are coefficients in an algebraic basis, not permission to execute against arrows.',{'vertices':vs,'edges':es,'counts':row,'divergence':b}))
    final=rows[-1][0];tickets=[e for e,c in zip(es,final) for _ in range(c)];tour,_=euler(tickets,'S');walk=['S']+[tickets[i][1] for i in tour]
    out.append(state('flow-walk','Expand each positive count into distinct tickets; a directed walk realizes exactly those counts.',graph_nodes(vs,es,directed=True,positions={v:p[v] for v in vs},counts=final)+ribbon(walk,405,'walk'),data={'walk':walk,'counts':final,'tickets':tickets,'tour':tour}))
    return out

def root_states(small=False):
    vs=['A','B','C'] if small else ['A','B','C','D','E'];es=[('A','B'),('B','C')] if small else [('A','B'),('B','C'),('B','D'),('D','E')]
    p={v:(80+i*140,200+(45 if i%2 else -45)) for i,v in enumerate(vs)};out=[]
    for i,(r,outward) in enumerate([(vs[0],False),(vs[-1],False),(vs[-1],True)]):
        arcs=root_arcs(vs,es,r,outward);ns=graph_nodes(vs,arcs,directed=True,positions=p,cursor=r)+[text('root-flag',360,65,'ROOT = '+r,'active',20),text('orientation',360,365,'away from root: child links' if outward else 'toward root: parent links',size=18)]
        out.append(state('root-'+str(i),('Reverse every parent arrow for the outward convention.' if outward else f'Choose {r} as root. Each nonroot follows its unique path toward {r}.'),ns,r'\deg^-(R)=0,\ \deg^-(v)=1\ (v\ne R)' if outward else r'\deg^+(R)=0,\ \deg^+(v)=1\ (v\ne R)','The underlying undirected edge set stays fixed.',{'root':r,'outward':outward,'arcs':arcs,'vertices':vs,'underlying':es}))
    return out

EULER_E=[('A','B'),('B','A'),('A','C'),('C','D'),('D','A'),('B','C'),('C','B')]
def euler_states(arcs,start):
    tour,tr=euler(arcs,start);vs=sorted(set(sum(([a,b] for a,b in arcs),[])));out=[]
    p={v:(180+125*math.cos(2*math.pi*i/len(vs)),195+100*math.sin(2*math.pi*i/len(vs))) for i,v in enumerate(vs)}
    for i,e in enumerate(tr):
        ns=graph_nodes(vs,arcs,e['used'],True,p,cursor=e['cursor'])+stack_nodes(e['stack'],'walk stack',x=540,y=305)
        # Show at most six stack positions in geometry; full trace remains in data/caption.
        if len(e['stack'])>6:
            ns=graph_nodes(vs,arcs,e['used'],True,p,cursor=e['cursor'])+stack_nodes(e['stack'][-6:],'top six frames',x=540,y=305)
        ns+=ribbon(['e'+str(x) for x in e['reverse']],400,'reverse output')
        out.append(state('euler-'+str(i),e['action'].capitalize()+'. '+str(len(e['used']))+' distinct arc tickets have been spent.',ns,'','Use every arc identity once; repeated vertices are allowed.',e))
    walk=[start]+[arcs[i][1] for i in tour];last=last_exits(arcs,tour,start)
    ns=graph_nodes(vs,arcs,list(last.values()),True,p,cursor=start)+[text('last-exits',555,85,'LAST EXITS',size=17),text('toward-root',555,119,'point toward '+start,size=16)]+ribbon(['e'+str(x) for x in tour],372,'final trail')+ribbon(walk,410,'vertices')
    out.append(state('last-exits','Reverse the return output to obtain the trail. Nonroot last-exit tickets form an inward tree toward the terminal root.',ns,r'\deg^+(v)=\deg^-(v)','Do not include the terminal root’s last exit in the selected tree.',{'tour':tour,'walk':walk,'lastExits':last,'arcs':arcs}))
    return out

def build_last():
    lessons=[]
    dm=demo('free-tree-surgery','Connect components without closing a loop','graph-edge-surgery',surgery_states(),surgery_states(3),'Connect three islands by two bridges, then try adding a third bridge.','Joining separate islands reduces the component count; joining already connected islands closes a loop.',check('A simple graph has 5 vertices and 4 edges but is disconnected. Must it be a tree?',['Yes, because m=n−1','No; edge count alone is insufficient','Yes, if one vertex is isolated'],1,'A triangle plus a separate one-edge component has 5 vertices and 4 edges, but is not a tree.'),check('Three islands are joined in a chain. Remove either bridge. What happens?',['Still connected','Disconnected'],1,'The unique connecting route used that bridge.'),{'n':4})
    lessons.append(lesson(119,[passage('graph-domain','Forget the root, keep the edges','Here a graph is finite, nonempty, simple and undirected: no loops and no parallel edges. A walk may repeat vertices and edges; a simple path repeats no vertex. A cycle is a closed route of at least three edges with no repeated internal vertex. A free tree is connected and has no cycles. Directed arcs and multigraph conventions are treated separately in the next units.',demonstration=dm),passage('unique-path','Connected and acyclic means one simple route','Connectedness supplies a path between any two distinct vertices. If two different simple paths joined the same pair, take their first divergence and their next reunion; the two intervening portions form a cycle. Therefore an acyclic connected graph has exactly one simple path between each pair. Conversely a cycle supplies two different simple routes between vertices on that cycle, contradicting uniqueness. This proves the characterization; the finite animation only illustrates it.'),passage('edges-count','Why n−1 edges follows, and what it does not say alone','Every finite acyclic graph with at least one edge has a leaf: an endpoint of a longest simple path cannot have another neighbor without extending the path or making a cycle. Remove a leaf and its one edge; repeat by induction. A forest with n vertices and c components has m=n−c edges. Thus a connected forest has n−1 edges. Conversely, a connected graph contains a spanning tree with n−1 edges; if it already has exactly that many, no additional cycle edge remains.',r'm=n-c\quad\text{for a forest};\qquad c=1\Rightarrow m=n-1'),passage('bridges','Every tree edge is indispensable','Removing an edge uv of a tree disconnects u from v, because any remaining path would combine with uv into a cycle. Conversely, if a connected graph loses connectedness whenever any edge is deleted, it cannot contain a cycle: removing one cycle edge would leave an alternative route. A one-vertex graph with no edges satisfies the tree characterizations vacuously. The numerical equalities require finite graphs; do not subtract infinite cardinalities as though this proof applied.')],'Finite free-tree equivalences, paths/walks/cycles, bridge and leaf arguments; tests are distinguished from general proofs.','576–580'))
    dm=demo('flow-cycle-basis','Separate a path from circulations','signed-flow-basis',flow_states(),flow_states(True),'Take one route to the finish; add a closed detour that returns to where it started.','The detour changes edge counts but adds no net source or sink.',check('Nonnegative integer counts satisfy every flow balance equation but include a separate closed cycle unreachable from the used start-to-stop route. Are they realizable by one walk?',['Yes','No','Only if the cycle is balanced'],1,'The positive-count support must also be weakly connected. A separate balanced cycle cannot be visited.'),check('Add S→A→S once to S→A→T. Does the net excess outflow at S change?',['Yes, to 2','No, it stays 1'],1,'The detour leaves S once and reenters it once.'),{'vertices':FLOW_V,'edges':FLOW_E,'path':FLOW_P,'cycles':FLOW_C})
    lessons.append(lesson(120,[passage('backbone','A spanning tree chooses independent cycle coordinates','For this flow model, forget arc directions but retain distinct edge identities: opposite or parallel arcs become parallel undirected edges rather than being merged. In that connected underlying multigraph with n vertices and m edge occurrences, choose a spanning tree. Each of the m−n+1 non-tree edges closes a unique cycle with the tree path joining its endpoints; a loop, if present, is a one-edge cycle. Assign an arbitrary reference direction to each edge, and record +1 for traversing with it, −1 against it, 0 otherwise. These signed fundamental-cycle vectors are algebraic objects; they need not be directed executable cycles.',demonstration=dm),passage('incidence','Conservation is a linear equation','Let B have one column per directed edge: +1 at its tail, −1 at its head, zero elsewhere. For a loop these contributions cancel in the same row. For an edge-count vector f, Bf is outgoing count minus incoming count at each vertex. A start-to-stop walk has Bf=1_s−1_t; if s=t, this is zero. A fixed signed spanning-tree path p has the same divergence. Thus f−p is a circulation in the nullspace of B.',r'Bf=\mathbf1_s-\mathbf1_t,\qquad Bc_j=0'),passage('basis-proof','Why the fundamental cycles span uniquely','Each fundamental cycle contains its own non-tree edge with coefficient +1 and no other non-tree edge. Subtract from a circulation the matching multiple of every such cycle. The remainder is supported only on tree edges. At a leaf, zero divergence forces its sole remaining edge coefficient to be zero; deleting leaves repeatedly makes every coefficient zero. This proves spanning. The unique non-tree coordinates prove independence, hence cycle-space dimension m−n+1 for a connected graph.',r'f=p+\sum_{j=1}^{m-n+1}\alpha_j c_j'),passage('walk-conditions','Linear solutions are not automatically executions','For a realizable directed walk, each final edge count must be a nonnegative integer, with the specified endpoint imbalance, and all vertices touching positive-count edges must lie in one weakly connected component containing the endpoints when the walk is nonempty. These conditions are also sufficient: replace an edge with f_e distinct parallel tickets and apply the directed Euler-trail theorem. They describe possible walks in the flow graph, not whether a particular program’s data-dependent branch tests will actually choose that walk.')],'Spanning-tree cycle basis, signed incidence equations, uniqueness proof and exact count realization; no electrical-voltage law or program-path feasibility is inferred.','580–587'))
    dm=demo('root-conventions','The root fixes the parent directions','inward-outward-arborescence',root_states(),root_states(True),'Put the root flag at one end of a three-node chain; every parent arrow points toward it.','Move the flag and recompute the unique next step toward the root.',check('Under the source’s inward convention, what are the outdegrees of the root and every other node?',['Root 0, others 1','Root 1, others 0','All 1'],0,'Every nonroot has one parent arrow; the root has no parent.'),check('Move the root from A to C on A—B—C. Which parent arrow does B use?',['B→A','B→C'],1,'The unique route toward the new root starts toward C.'),{'sourceConvention':'toward root','comparisonConvention':'away from root'})
    lessons.append(lesson(121,[passage('source-convention','The source points parent arcs toward the root','The book’s oriented tree is a rooted-unordered tree drawn as a digraph with arcs from children toward parents. Every nonroot has outdegree one, the root has outdegree zero, and every vertex can reach the root. In modern terminology this is an inward arborescence. An outward arborescence reverses all arrows: root indegree zero, every other indegree one, and the root reaches every vertex. State which convention is being used before applying a degree test.',demonstration=dm),passage('reachability','Degree constraints need a global condition','Choose a root R in a free tree. For each v≠R, direct its first edge on the unique simple path toward R. Each step decreases distance to R, so cycles are impossible and all paths terminate there. Conversely the inward degree rules plus reachability to R give n−1 arcs and a connected underlying graph, hence a free tree. Degree rules alone are insufficient: a root with no outgoing arc can coexist with a separate directed cycle whose vertices each have outdegree one.'),passage('equivalence-levels','Forgetting information changes what counts as the same','An ordered-tree isomorphism preserves the root and each child’s position. A rooted-unordered isomorphism preserves the root and parent relationships but may permute siblings. A free-tree isomorphism ignores the root too. Labels, if designated as data to preserve, add another requirement. Merely moving a drawing on the page changes none of these structures. Reordering unlike child subtrees changes an ordered tree but need not change its rooted-unordered class.'),passage('directed-graphs','Weak connectivity is weaker than reachability','A directed graph may have loops and several distinct arcs with the same endpoints. Its underlying simple graph forgets directions, drops loops and merges duplicates. Connectivity of that underlying graph is weak connectivity. Strong connectivity requires directed paths between every pair. The source calls a digraph rooted when some R is reachable from every vertex; this is weaker than strong connectivity and is not the outward “root reaches all” convention. A chain aimed at its final vertex is rooted but not strongly connected.')],'Source inward oriented-tree convention, outward contrast, rooted/ordered/free equivalence and directed connectivity.','591–595'))
    dm=demo('euler-tickets','Spend every arc ticket exactly once','hierholzer-and-last-exits',euler_states(EULER_E,'A'),euler_states([('U','V'),('V','U')],'U'),'There is one ticket U→V and one ticket V→U. Spend both and return home.','Tickets are arcs; revisiting a vertex is allowed, but spending a ticket twice is not.',check('Two disjoint directed triangles are balanced at every vertex. Is there one closed trail using every arc?',['Yes','No','Only if vertices may repeat'],1,'Balance is necessary but disconnected nonisolated support makes one tour impossible.'),check('U→V→U visits U twice. Does that alone invalidate an Euler trail?',['Yes','No'],1,'An Euler trail forbids repeated arcs, not repeated vertices.'),{'arcs':EULER_E,'tour':euler(EULER_E,'A')[0]})
    lessons.append(lesson(122,[passage('trail-domain','A trail spends arcs, not vertices','Give every directed arc its own identity, including loops and parallel arcs. An Euler trail uses each arc exactly once; vertices may repeat. The source uses “Eulerian trail” for a closed tour. Here we explicitly distinguish a closed Euler circuit from an open Euler trail. A loop contributes one to both indegree and outdegree and remains a distinct ticket to spend. Isolated vertices do not affect a tour through the nonempty arc support.',demonstration=dm),passage('degree-and-connectivity','The exact existence conditions','For a closed circuit with at least one arc, every nonisolated vertex has equal indegree and outdegree, and the nonisolated support is weakly connected. For an open trail from s to t, s has outdegree−indegree=1, t has −1, all others have zero, and that support is weakly connected. Necessity follows by pairing every arrival with a departure except at the two endpoints. For the empty arc set, our implementation returns an empty tour; choosing its resting vertex is a separate convention.',r'\deg^+(v)-\deg^-(v)=\mathbf1_{v=s}-\mathbf1_{v=t}'),passage('splicing-proof','Why taking detours can finish the tour','In a balanced finite digraph, following unused outgoing arcs cannot first get stuck away from the starting vertex: arrivals and departures would be unbalanced there. This yields a closed detour. If unused arcs remain, weak connectivity supplies a vertex of the current tour incident with unused support; balance of the remaining arcs supplies an unused departure there. Build another closed detour and splice it in. Repeat until no arc remains. Our stack implementation records return tickets in reverse order, then reverses them. For an open trail, add one temporary t→s arc, construct a circuit, then cut at that arc.'),passage('last-exit-tree','Saving the last exit explains the rooted tree','In a completed closed tour ending at R, select each nonroot vertex’s last outgoing ticket. If such a ticket leads to another nonroot, that vertex’s last exit occurs strictly later in the tour; otherwise the walk could not leave it and eventually finish at R. Strictly increasing positions rule out a selected cycle. Every nonroot has one selected exit, so all selected paths reach R: an inward spanning tree. Conversely, in a balanced digraph with a chosen inward spanning tree, save each nonroot’s tree exit until its other outgoing tickets are spent. A maximal no-repeated-ticket walk from R then uses every arc. The proof follows any supposed unused ticket along reserved parent exits toward R, contradicting maximality.')],'Directed Euler circuits and open trails, constructive splicing/Hierholzer model, last-exit inward trees and reserved-exit theorem; enumeration formulas from the exercise bank are not reproduced.','595–598'))
    return lessons

# Focused companions for formal passages: new computed cases, not duplicated main traces.
def attributes(f,attribute):
    d=fdict(f);parent={c:v for v,ch in d.items() for c in ch}
    def value(v):
        if attribute=='degree':return len(d[v])
        if attribute=='level':return 0 if v not in parent else 1+value(parent[v])
        return 1+sum(value(c) for c in d[v])
    vals={v:value(v) for v in d};pos=tree_positions(f,x0=60,x1=650,y0=65,dy=90);out=[]
    for i,v in enumerate(forder(f,'post')):
        ns=tree_nodes(f,v,positions=pos)+[text('attribute',360,370,f'{attribute}({v}) = {vals[v]}','active',19),text('values',360,408,', '.join(w+':'+str(vals[w]) for w in d),size=15)]
        out.append(state('attribute-'+str(i),f'Compute {attribute} at {v}: {vals[v]}. '+('Children have already been handled.' if attribute=='size' else 'Use the stated root and child relation.'),ns,data={'attribute':attribute,'values':vals,'node':v,'forest':f}))
    return out

def binary_boundary_states():
    out=[]
    for name,t in [('empty',None),('one',B('K')),('left-only',B('K',B('J'))),('right-only',B('K',None,B('J')))]:
        ns=bnodes(t)+[text('case',570,70,name,'active',18)]
        if t is None:ns +=[rect('empty-slot',210,130,120,90,'muted'),text('empty-label',270,180,'empty')]
        for i,k in enumerate(('pre','in','post')):ns+=ribbon(border(t,k),325+35*i,k,k)
        out.append(state(name,'Inspect the '+name+' binary tree. Empty slots remain on their named side.',ns,data={'tree':t,'pre':border(t,'pre'),'in':border(t,'in'),'post':border(t,'post')}))
    return out

def cost_states():
    out=[]
    for n in [1,3,5]:
        skew=None
        for i in range(n):skew=B(chr(65+i),skew)
        tr=inorder_stack(skew);peak=max(len(e['stack']) for e in tr);push=sum(e['action'].startswith('push') for e in tr)
        ns=bnodes(skew)+[rect('cost-space',550,300-peak*35,60,peak*35,'active'),text('cost-peak',580,330,'peak '+str(peak)),text('cost-push',580,375,'pushes '+str(push),size=15)]
        # Compress a chain vertically to fit; maintain the explicit slot geometry.
        p=bpositions(skew,x0=40,x1=470,y=55,dy=60);ns=tree_nodes(bforest(skew),positions=p)+ns[-3:]
        out.append(state('cost-'+str(n),f'A left chain of {n} nodes makes {push} pushes and reaches stack height {peak}.',ns,r'h=n','These are exact counts, not a fitted complexity curve.',{'n':n,'pushes':push,'peak':peak}))
    return out

def identity_comparison():
    out=[]
    for same in [False,True]:
        objs={'P':4,'Q':4};targets=['P','P' if same else 'Q'];objs['P']=9;observed=[objs[t] for t in targets]
        ns=[rect('p',90,170,150,80),text('p-title',165,198,'P: '+str(objs['P'])),rect('q',475,170,150,80),text('q-title',550,198,'Q: '+str(objs['Q'])),text('target1',165,90,'handle 1'),text('target2',550,90,'handle 2')]
        ns+=arrow('h1',(165,110),(165,170),'active')+arrow('h2',(550,110),(165,170) if same else (550,170),'active')
        ns+=[text('reads',360,350,'After writing P=9, handles read '+str(observed),'result',17)]
        out.append(state('identity-'+str(same),'Two handles '+('share P.' if same else 'name distinct objects with initially equal contents.'),ns,data={'targets':targets,'values':objs,'observations':observed}))
    return out

def cycle_detection_states(small=False):
    children={'A':['B','C'],'B':['C'],'C':[]} if small else {'A':['B','C'],'B':['D'],'C':['D'],'D':[]};out=[]
    for cyc in [False,True]:
        g=copy.deepcopy(children)
        if cyc:g['C' if small else 'D']=['A']
        active=set();done=set();events=[]
        def visit(v):
            if v in active:events.append((v,'cycle'));return
            if v in done:events.append((v,'shared completed'));return
            active.add(v);events.append((v,'enter'))
            for w in g[v]:visit(w)
            active.remove(v);done.add(v)
        visit('A');es=[(v,w) for v,ch in g.items() for w in ch];ns=graph_nodes(list(g),es,directed=True)+[text('detect',360,404,'cycle' if cyc else 'sharing without a cycle','error' if cyc else 'result',17)]
        out.append(state('detect-'+str(cyc),'Use separate active and completed sets. '+(('C' if small else 'D')+' points back to active ancestor A.' if cyc else ('B and A both reach C; that is sharing.' if small else 'C reaches completed D; that is sharing.')),ns,data={'graph':g,'events':events,'cycle':cyc}))
    return out

def domain_states(expressions,points):
    out=[]
    for i,(a,x) in enumerate(zip(expressions,points)):
        try:value=str(ev(a,{'x':Fraction(x)}));error=False
        except (ValueError,ZeroDivisionError) as ex:value='undefined';error=True
        f,labs=ast_to_forest(a);ns=tree_nodes(f,'a',positions=tree_positions(f,x0=50,x1=650,y0=65,dy=85),labels=labs)+[text('binding',360,370,'x = '+str(x)),text('domain-result',360,410,value,'error' if error else 'result',18)]
        out.append(state('domain-'+str(i),fmt(a)+' at x='+str(x)+' is '+value+'. A syntax tree does not guarantee defined arithmetic.',ns,data={'ast':a,'x':x,'defined':not error,'value':value}))
    return out

def derivative_rule_states(expressions):
    out=[]
    for i,a in enumerate(expressions):
        f,labs=ast_to_forest(a);ns=tree_nodes(f,'a',positions=tree_positions(f,x0=50,x1=650,y0=60,dy=80),labels=labs)+[text('rule',360,385,'Apply '+a[0]+' rule to the source node','active',18)]
        out.append(state('rule-'+str(i),'Transform '+fmt(a)+' into derivative '+fmt(diff(a))+'. Domain assumptions are retained.',ns,'D('+fmt(a)+')='+fmt(diff(a)),data={'ast':a,'derivative':diff(a)}))
    return out

def scope_states(f):
    order=forder(f);d=fdict(f);index={v:i for i,v in enumerate(order)}
    def sub(v):return [v]+sum((sub(c) for c in d[v]),[])
    out=[]
    for v in order:
        ids=sub(v);lo=index[v];hi=lo+len(ids);ns=[]
        for i,w in enumerate(order):
            x=75+i*108;role='active' if lo<=i<hi else 'muted';ns +=[rect('node-'+w,x-35,145,70,65,role),text('label-'+w,x,185,w,role),text('address-'+w,x,120,str(i),size=14)]
        ns +=[rect('scope-band',40+lo*108,230,(hi-lo)*108-20,35,'active'),text('scope-equation',360,330,v+': interval ['+str(lo)+','+str(hi)+')','active',18)]
        out.append(state('scope-'+v,'The subtree of '+v+' occupies exactly '+str(ids)+'. Scope is the first address after it.',ns,data={'node':v,'order':order,'subtree':ids,'interval':[lo,hi]}))
    return out

def degree_rebuild_states(f):
    records=encode(f,'post')['records'];stack=[];out=[]
    for i,r in enumerate(records):
        d=r['degree'];ch=stack[-d:] if d else []
        if d:del stack[-d:]
        stack.append(T(r['id'],*ch));ns=tree_nodes(tuple(stack),active=r['id'],positions=tree_positions(tuple(stack),x0=50,x1=650,y0=80,dy=95))
        ns +=[text('record',360,355,'record ('+r['id']+','+str(d)+')','active',18),text('roots-left',360,405,'completed roots: '+', '.join(t[0] for t in stack),size=15)]
        out.append(state('rebuild-'+str(i),'Consume '+str(d)+' completed roots and attach them under '+r['id']+'.',ns,data={'record':r,'stackForest':copy.deepcopy(stack)}))
    return out

def graph_counterexamples():
    specs=[(['A','B','C','D','E'],[('A','B'),('B','C'),('C','A'),('D','E')]),(['A'],[]),(['A','B','C'],[('A','B'),('B','C')])];out=[]
    for i,(vs,es) in enumerate(specs):
        c=len(components(vs,es));rank=cycle_rank(vs,es);ok=c==1 and rank==0
        ns=graph_nodes(vs,es)+[text('candidate',360,400,f'n={len(vs)}, m={len(es)}, c={c}: '+('tree' if ok else 'not a tree'),'result' if ok else 'error',17)]
        out.append(state('counterexample-'+str(i),'Check connectedness and cycle rank separately; edge count alone does not decide.',ns,data={'vertices':vs,'edges':es,'components':c,'cycleRank':rank,'isTree':ok}))
    return out

def euler_condition_states():
    candidates=[[('A','B'),('B','A'),('C','D'),('D','C')],[('A','B'),('B','C')],[('A','B'),('A','C')],[('A','A')]];out=[]
    for i,arcs in enumerate(candidates):
        vs=sorted(set(sum(([u,v] for u,v in arcs),[])));b=divergence(vs,arcs)
        try:tour,_=euler(arcs);ok=True;reason='Euler trail exists'
        except ValueError as ex:ok=False;tour=[];reason=str(ex)
        ns=graph_nodes(vs,arcs,directed=True)+[text('conditions',360,385,reason,'result' if ok else 'error',18),text('balances',360,416,str(b),size=14)]
        out.append(state('conditions-'+str(i),'Inspect every degree and the support connectivity. '+reason+'.',ns,data={'arcs':arcs,'divergence':b,'exists':ok,'tour':tour}))
    return out

def isomorphism_states(small=False):
    fs=[(T('R',T('A'),T('B',T('C'))),),(T('R',T('B',T('C')),T('A')),)]
    if small:fs=[(T('R',T('X'),T('Y')),),(T('R',T('Y'),T('X')),)]
    def code(t,ordered):
        ch=[code(c,ordered) for c in t[1]]
        return (t[0] if small else '')+'('+''.join(ch if ordered else sorted(ch))+')'
    out=[]
    for i,f in enumerate(fs):
        ns=tree_nodes(f,positions=tree_positions(f,x0=70,x1=650,y0=75,dy=90))+[text('ordered-code',360,355,'ordered shape: '+code(f[0],True),size=16),text('unordered-code',360,403,'unordered shape: '+code(f[0],False),size=16)]
        out.append(state('equivalence-'+str(i),'Swap labelled leaves, preserving their labels as data. Ordered structure changes.' if small else 'Swap unlike child families. Ordered shape changes, rooted-unordered shape does not.',ns,data={'forest':f,'orderedCode':code(f[0],True),'unorderedCode':code(f[0],False)}))
    return out

def reach_set(vertices,arcs,start):
    seen={start};q=[start]
    while q:
        v=q.pop()
        for a,b in arcs:
            if a==v and b not in seen:seen.add(b);q.append(b)
    return seen

def connectivity_states(small=False):
    vs=['U','V'] if small else ['A','B','C'];forward=list(zip(vs,vs[1:]));out=[]
    for i,arcs in enumerate([forward,forward+[(vs[-1],vs[0])]]):
        strong=all(len(reach_set(vs,arcs,v))==len(vs) for v in vs)
        ns=graph_nodes(vs,arcs,directed=True)+[text('connected-kind',360,385,'weakly connected; '+('strongly connected' if strong else 'not strongly connected'),'result',17),text('return-path',360,413,'reachable from '+vs[-1]+': '+','.join(sorted(reach_set(vs,arcs,vs[-1]))),size=15)]
        out.append(state('connectivity-'+str(i),'Follow directed paths from every vertex. '+('The added return arc completes the directed cycle.' if i else 'The final vertex has no outgoing arc, so it cannot return.'),ns,data={'vertices':vs,'arcs':arcs,'stronglyConnected':strong}))
    return out

def root_reachability_states(small=False):
    vs=['R','U'] if small else ['R','A','B'];bad=[('U','U')] if small else [('A','B'),('B','A')];good=[('U','R')] if small else [('A','B'),('B','R')];out=[]
    for i,arcs in enumerate([bad,good]):
        valid=all('R' in reach_set(vs,arcs,v) for v in vs)
        ns=graph_nodes(vs,arcs,directed=True,cursor='R')+[text('reach-root',360,380,'Every nonroot has outdegree 1; R has outdegree 0',size=15),text('global-test',360,413,'all reach R: '+str(valid),'result' if valid else 'error',18)]
        out.append(state('root-reach-'+str(i),'Keep the local degree constraints, '+('but a closed component cannot reach R.' if not valid else 'and now make every parent chain reach R.'),ns,data={'vertices':vs,'arcs':arcs,'allReachRoot':valid,'root':'R'}))
    return out

def reserved_exit_states():
    arcs=EULER_E;root='A';tour,_=euler(arcs,root);reserved=last_exits(arcs,tour,root);used=[];v=root;out=[]
    while len(used)<len(arcs):
        choices=[i for i,(u,w) in enumerate(arcs) if u==v and i not in used]
        normal=[i for i in choices if reserved.get(v)!=i]
        if not choices:raise AssertionError('reserved-exit construction stuck')
        i=(normal or choices)[0];used.append(i);v=arcs[i][1]
        ns=graph_nodes(['A','B','C','D'],arcs,list(reserved.values()),True,cursor=v)+ribbon(['e'+str(j) for j in used],405,'spent')
        out.append(state('reserve-'+str(len(used)),f'Spend e{i}; keep each nonroot parent ticket until its other outgoing tickets are spent.',ns,data={'arcs':arcs,'reserved':reserved,'used':used[:],'cursor':v}))
    assert v==root;return out


def add_focused_demos(lessons):
    """Each formal passage receives its own computed small experiment or counterexample."""
    q=lambda p,c,i,e:check(p,c,i,e)
    fixtures={
    (106,'levels'):(attributes((T('K',T('L',T('N')),T('M')),),'level'),attributes((T('U',T('V')),),'level'),q('Root level is zero. What is its grandchild’s level?',['1','2','3'],1,'Two parent-to-child steps give level 2.')),
    (106,'binary-slots'):(binary_boundary_states(),binary_boundary_states()[1:3],q('How many binary trees are there with zero nodes?',['None','One empty tree','Two slot choices'],1,'The empty tree is a single allowed binary object.')),
    (106,'size-induction'):(attributes((T('K',T('L',T('N')),T('M')),),'size'),attributes((T('U',T('V')),),'size'),q('A root has child subtrees of sizes 2 and 4. Its size is?',['6','7','8'],1,'Count the root once in addition to the disjoint children.')),
    (107,'sharing'):(identity_comparison(),sharing_states(True),q('Distinct equal boxes are copied independently. Must mutation propagate?',['Yes','No'],1,'Equal content is different from shared identity.')),
    (107,'cycles'):(cycle_detection_states(),cycle_detection_states(True),q('An edge reaches a currently active ancestor. What does that establish?',['A directed cycle','Only equal contents','A leaf'],0,'The current descent path plus that back edge closes a cycle.')),
    (107,'limits'):(cycle_detection_states()[::-1],cycle_detection_states(True)[::-1],q('A completed node is reached through another branch, but no active ancestor is reached. What may this indicate?',['Sharing without a cycle','Necessarily a cycle','A missing root'],0,'Completed-node reuse is not by itself a back edge.')),
    (108,'recursive-orders'):(traversal_states(B('Q',B('N'),B('S'))),traversal_states(B('U',None,B('V'))),q('Root Q has children N and S. Which postorder is correct?',['Q N S','N S Q','N Q S'],1,'Emit both child outputs before Q.')),
    (108,'once'):(traversal_states(B('K',B('H')))[::2],traversal_states(B('Z')),q('A binary tree has 12 nodes. How many emissions occur in one complete inorder traversal?',['12','24','Depends on shape'],0,'Disjoint child traversals plus one root emission give exactly one per node.')),
    (108,'empty'):(binary_boundary_states(),binary_boundary_states()[:2],q('What does preorder emit for an empty binary tree?',['A null data node','Nothing','The header'],1,'Null and header are not data nodes.')),
    (109,'stack-invariant'):(stack_states(B('Q',B('N'),B('S'))),stack_states(B('U',B('V'))),q('A node remains on the descent stack. Has its own inorder visit happened?',['Yes','No'],1,'The card records a visit still pending after left-subtree completion.')),
    (109,'proof-stack'):(stack_states(B('Q',None,B('S'))),stack_states(B('U')),q('After a complete child-subtree traversal, what happens to the caller’s older stack prefix?',['It is restored unchanged','It is cleared','It is reversed'],0,'The inductive contract preserves older suspended work.')),
    (109,'cost'):(cost_states(),cost_states()[:2],q('Is an inorder ancestor stack always O(log n)?',['Yes','No, a chain needs O(n)'],1,'A tree need not be balanced.')),
    (110,'successor'):(thread_states(B('Q',B('N'),B('W',B('S')))),thread_states(B('U',None,B('V'))),q('A node’s right tag is 1. Where is its successor?',['At that right link','At the leftmost real child of that link','Always at the root'],0,'A tagged right thread directly names the successor.')),
    (110,'header'):(header_states(),header_states()[:2],q('For an empty tree, H.L=H has what left tag?',['0 child','1 thread'],1,'The source’s empty-header left tag is 1.')),
    (110,'cost-thread'):(thread_states(B('K',None,B('R',B('P',B('N'))))),thread_states(SMALL),q('Can one successor query descend several left edges?',['Yes','No'],0,'The right subtree’s minimum can be deep.')),
    (111,'repair-thread'):(insertion_states(B('K',None,B('R',B('N'))),'K','L')[:2],insertion_states(B('U'),'U','V')[:2],q('Insertion replaces a right thread by a new right child. Is a deep leftmost-thread repair needed?',['Yes','No'],1,'No old real right subtree was inherited.')),
    (111,'copy-map'):(insertion_states(B('K',B('J')),'J','L')[1:],insertion_states(B('U'),'U','V')[1:],q('Which pointers must be mapped when copying?',['Only child links','Children, threads and header links','Only the root'],1,'Every target must enter the fresh address set.')),
    (111,'verify-update'):(thread_states(B('K',B('J',B('I')))),header_states(),q('Can a copied thread target an original data address?',['Yes','No'],1,'That would violate the no-cross-copy invariant.')),
    (112,'bijection'):(conversion_states((T('K',T('L'),T('M')),)),conversion_states((T('U'),)),q('What forest corresponds to an empty binary tree?',['One empty ordinary tree','The empty forest','No valid forest'],1,'The bijection includes empty forest ↔ empty binary tree.')),
    (112,'order-match'):(conversion_states((T('K',T('L'),T('M')),T('N')))[2:],conversion_states(SMALLF)[2:],q('Forest postorder corresponds to which binary order?',['Postorder','Inorder','Level order'],1,'Left child forest, root, right sibling forest is binary inorder.')),
    (112,'meaning'):(conversion_states((T('K',T('L'),T('M'),T('N')),)),conversion_states(SMALLF),q('In the binary representation, a right child usually means what in the original forest?',['A sibling','An original child','A root only'],0,'Right links are next-sibling links.')),
    (113,'polish'):(expression_states(('*',('+',C(2),C(5)),C(3)),{}),expression_states(('+',C(2),C(3)),{}),q('Prefix “− 9 4” with binary minus corresponds to which postfix?',['9 4 −','− 4 9','4 9 −'],0,'Postorder preserves operand order and places the operator last.')),
    (113,'evaluation'):(expression_states(('/',C(3),C(8)),{}),expression_states(('-',C(6),C(2)),{}),q('Postfix 3 8 / evaluates to?',['8/3','3/8','5'],1,'The first operand is the numerator.')),
    (113,'domain'):(domain_states([('/',C(2),V()),('ln',V())],[0,-1]),domain_states([('/',C(1),V()),('/',C(1),V())],[1,0]),q('A well-formed division tree has denominator zero. What follows?',['Evaluate to zero','Report undefined arithmetic','Reverse operands'],1,'Syntactic validity does not remove the division domain condition.')),
    (114,'product-chain'):(diff_states(('*',V(),('+',V(),C(1)))),diff_states(('*',C(3),V())),q('For u=x² and v=x+4, what is the product-rule structure?',['u′v+uv′','u′v′','u+v'],0,'Either factor can change; both contributions are required.')),
    (114,'rules-domain'):(derivative_rule_states([('ln',('+',V(),C(3))),('/',V(),('+',V(),C(1))),('pow',V(),V())]),derivative_rule_states([('ln',V()),('pow',V(),C(2))]),q('The real logarithmic formula for D(uᵛ) safely assumes what about u?',['u>0','u<0','No condition'],0,'Real ln(u) and division by u require a positive base in this formula.')),
    (114,'simplify-carefully'):(domain_states([('*',C(0),('/',C(1),V())),C(0)],[0,0]),domain_states([('/',V(),V()),C(1)],[0,0]),q('Simplifying x/x to 1 should do what to the original exclusion x=0?',['Erase it','Retain it'],1,'Equivalent formulas on a domain need not have identical natural domains.')),
    (115,'pre-scope'):(scope_states(F),scope_states(SMALLF),q('A leaf occupies address 5 in one-word preorder storage. Its scope is?',['5','6','The root address'],1,'The interval [5,6) contains exactly that leaf.')),
    (115,'family-level'):(encoding_states((T('K',T('L',T('N')),T('M')),T('Q',T('S'))))[2:4],encoding_states(SMALLF)[2:4],q('Which structure selects pending families for level order?',['FIFO queue','LIFO stack','Priority by label'],0,'Oldest pending families preserve depth order.')),
    (115,'post-degrees'):(degree_rebuild_states(F),degree_rebuild_states(SMALLF),q('The first postorder record claims degree 2. Is it valid with an empty stack?',['Yes','No'],1,'No completed children are available to consume.')),
    (116,'consume-group'):(fold_states((T('K',T('L'),T('M')),),{'L':4,'M':9}),fold_states((T('U',T('V')),),{'V':2}),q('A degree-zero node consumes how many previous results?',['All','Zero','One'],1,'It is a leaf and has no child results.')),
    (116,'induction-fold'):(degree_rebuild_states((T('K'),T('L',T('M')))),degree_rebuild_states(SMALLF),q('A completed earlier forest root lies below the next tree’s child results. Is it consumed by that next tree?',['Yes','No'],1,'The local subtree contract preserves the older prefix.')),
    (116,'work-fold'):(fold_states((T('K',T('A'),T('B'),T('C'),T('D')),),dict(A=1,B=2,C=3,D=4)),fold_states((T('U',T('V'),T('W')),),dict(V=1,W=2)),q('Can a height-two star require many pending child values?',['Yes','No'],0,'All leaf values accumulate before the root consumes them.')),
    (117,'reciprocity'):(linked_states((T('K',T('L'),T('X'),T('M')),)),linked_states((T('U',T('V')),)),q('Insert a new first child. Which parent field must change?',['The first-child link','The parent’s own parent always','No field'],0,'The parent must now lead directly to the inserted child.')),
    (117,'cost-representation'):(union_states(5,[(0,1),(1,2),(2,3),(3,4)]),union_states(3,[(0,1),(1,2)]),q('Does simple unbalanced root linking guarantee logarithmic find time?',['Yes','No'],1,'Repeated attachments can form a linear chain.')),
    (118,'canonical'):(polynomial_states(poly_tree({(0,2):1,(1,0):2}),poly_tree({(0,2):-1})),polynomial_states(poly_tree({(1,0):1}),poly_tree({(1,0):-1})),q('A variable node has only its exponent-zero coefficient left. What normalization applies?',['Keep an unnecessary level','Replace it by that coefficient'],1,'No positive power remains, so the variable is absent.')),
    (118,'addition'):(polynomial_states(poly_tree({(2,0):3}),poly_tree({(0,1):2,(2,0):-1})),polynomial_states(poly_tree({(1,0):2}),poly_tree({(1,0):4})),q('What is the x² coefficient after 3x²+2y is added to −x²?',['2','3','4'],0,'Only like exponent vectors combine: 3−1=2.')),
    (118,'links-and-cost'):(ring_mutation_states(),ring_mutation_states(True),q('A coefficient subtree is replaced after cancellation. Which navigation relation must be repaired in a mutable linked model?',['Its parent link','The numerical variable order must reverse','Every unrelated coefficient'],0,'The replacement’s UP link must name its actual parent.')),
    (119,'unique-path'):(surgery_states(3)[2:4],surgery_states(3)[1:3],q('Two different simple routes join the same vertices. What do their diverging/rejoining pieces contain?',['A cycle','An isolated vertex','An empty tree'],0,'Together those pieces form a closed route without repeated internal vertices.')),
    (119,'edges-count'):(graph_counterexamples(),surgery_states(3)[:3],q('A forest has 9 vertices and 3 components. How many edges?',['6','8','12'],0,'For a forest m=n−c=6.')),
    (119,'bridges'):(surgery_states(4)[-2:],surgery_states(3)[-2:],q('Remove one edge from a tree with at least two vertices. What happens?',['It stays connected','It splits into two components'],1,'Its endpoints had only one simple connecting path.')),
    (120,'incidence'):(flow_states(True),flow_states(True)[:2],q('For a closed directed walk, outgoing minus incoming count is what at every vertex?',['0','1','Its degree'],0,'Every arrival is paired with a departure.')),
    (120,'basis-proof'):(flow_states()[1:3],flow_states(True),q('A connected graph has 7 edges and 5 vertices. Its cycle-space dimension is?',['2','3','5'],1,'There are m−n+1=7−5+1=3 independent fundamental cycles.')),
    (120,'walk-conditions'):(euler_condition_states(),euler_condition_states()[1:3],q('Can a signed cycle-basis vector alone be interpreted as a directed execution when it has a negative count?',['Yes','No'],1,'Signed basis coordinates are algebraic; final directed counts must all be nonnegative integers.')),
    (121,'reachability'):(root_reachability_states(),root_reachability_states(True),q('Root outdegree 0 and other outdegrees 1, but a separate directed cycle exists. Is this an inward tree?',['Yes','No'],1,'The cycle cannot reach the specified root.')),
    (121,'equivalence-levels'):(isomorphism_states(),isomorphism_states(True),q('Swap unlike children at one parent. Which equivalence may change?',['Ordered-tree equivalence','Rooted-unordered equivalence necessarily','Free-tree equivalence necessarily'],0,'Child position is part of the ordered structure.')),
    (121,'directed-graphs'):(connectivity_states(False),connectivity_states(True),q('A→B→C is weakly connected. Is it strongly connected?',['Yes','No'],1,'There is no directed path from C back to A.')),
    (122,'degree-and-connectivity'):(euler_condition_states(),euler_condition_states()[1:3],q('In an open Euler trail, the start’s outdegree minus indegree is?',['−1','0','1'],2,'There is one departure without a matching earlier arrival.')),
    (122,'splicing-proof'):(euler_states([('A','B'),('B','A'),('A','C'),('C','A')],'A'),euler_states([('U','V'),('V','U')],'U'),q('A balanced residual graph has unused arcs touching a tour vertex. What can you build there?',['A closed unused detour','A new isolated vertex','A repeated ticket'],0,'Balance lets the unused walk return to its start for splicing.')),
    (122,'last-exit-tree'):(reserved_exit_states(),euler_states([('U','V'),('V','U')],'U')[-2:],q('Which selected tree ticket must wait until other outgoing tickets at its nonroot vertex are spent?',['The reserved parent/last-exit ticket','Every first entrance','The root’s nonexistent parent ticket'],0,'Saving that exit prevents trapping unused work away from the terminal root.')),
    }
    for l in lessons:
        for s in l['sections']:
            for p in s['passages']:
                if 'demonstration' in p:continue
                states,hs,c=fixtures[(l['order'],p['id'])]
                # Help checks test the smaller mechanism, with a second new question from the passage's concept.
                intro='Use the smaller example first. '+hs[0]['caption']
                p['demonstration']=demo(l['id']+'-'+p['id'],p['title'],'focused-'+p['id'],states,hs,intro,'Return to the formal claim: '+p['title']+'. The finite scene is an example; the passage supplies the general reasoning.',c,copy.deepcopy(c),{'semanticFocus':p['id'],'workedCaseCount':len(states),'helpCaseCount':len(hs)})
    return lessons

def header_states():
    out=[]
    for i,t in enumerate([None,B('K'),B('K',B('J'))]):
        n=threaded(t);ns=thread_scene(t,n)+[text('header-fields',360,365,'H.L='+n['H']['L']+'; LT='+str(n['H']['LT'])+'; H.R=H; RT=0',size=17),text('first',360,405,'successor(H) = '+successor(n,'H'),'result',17)]
        out.append(state('header-'+str(i),'Inspect the header for '+('an empty tree.' if t is None else 'a nonempty tree.'),ns,data={'links':n,'successorH':successor(n,'H'),'predecessorH':predecessor(n,'H')}))
    return out

def smaller_check(states):
    """An assessment computed from the help model, separate from the transfer question."""
    s=states[-1];d=s.get('data',{})
    if 'observations' in d:
        ans=str(d['observations']);return check('After the displayed write, what do the two handles read?',[ans,str(list(reversed(d['observations'])))+' with new identities','Two independent unchanged values'],0,'Follow the actual target identities, then read those objects.')
    if 'value' in d and 'references' in d:
        a=str(d['value']);return check('What is now inside the smaller box?',[str(int(d['value'])+1),a,'A different box identity'],1,'The mutation replaced contents, not the identity of the box.')
    if 'attribute' in d:
        a=d['values'][d['node']];return check('For the highlighted '+d['node']+', what is its '+d['attribute']+'?',[str(a+1),str(a),str(a+2)],1,'Apply this attribute’s definition to the highlighted node in the smaller tree.')
    if 'token' in d and 'stack' in d:
        a=' | '.join(d['stack']);return check('What ordered value stack remains after the last smaller postfix token?',[a,'No values remain',a+' | 0'],0,'The last operator consumes only its own ordered operands and pushes one result.')
    if 'cycle' in d and 'events' in d:
        return check('Does this smaller graph contain a reference back to an active ancestor?',['Yes','No'],0 if d['cycle'] else 1,'The active-ancestor test distinguishes a cycle from a second reference to completed work.')
    if 'unorderedCode' in d:
        return check('After this smaller sibling swap, does the rooted-unordered labelled structure change?',['Yes','No'],1,'The same labelled children belong to the same parent; only their order changed.')
    if 'stronglyConnected' in d:
        return check('Can every vertex in the final smaller graph reach every other by following arrows?',['Yes','No'],0 if d['stronglyConnected'] else 1,'Test the direction of paths, not just the connectedness of the underlying drawing.')
    if 'allReachRoot' in d:
        return check('Can every smaller vertex reach the specified root by following its parent arrows?',['Yes','No'],0 if d['allReachRoot'] else 1,'An isolated directed cycle or loop can obey local degree rules while missing the root.')
    if 'output' in d:
        a=' '.join(d['output']) or 'empty';return check('What visit word has the smaller trace emitted at this point?',[a,' '.join(reversed(d['output']))+' again','the header only'],0,'Read only visit events, not every arrival or pop.')
    if 'outputs' in d:
        a=' '.join(d['outputs']['in']) or 'empty';return check('What inorder word does this smaller tree produce?',['the root only',a,'no data nodes'],1,'Emit between left and right trips.')
    if 'successorH' in d:
        return check('Where does successor(H) lead in this smaller case?',[d['successorH'],'H.R unconditionally','A newly allocated node'],0,'The header’s left relation and the thread tags select the first data node, if any.')
    if 'successor' in d:
        return check('Where does the highlighted node’s successor operation finish?',[d['successor'],'Its own node again','A fresh node'],0,'Follow a right thread directly, or descend the real right subtree to its leftmost node.')
    if 'defined' in d:
        return check('Is the displayed smaller expression defined at its displayed input?',['Yes','No'],0 if d['defined'] else 1,'Check the displayed denominator or logarithm domain before simplifying.')
    if 'derivative' in d:
        return check('Which local derivative is built for the smaller source expression?',[fmt(d['derivative']),fmt(d.get('source',d.get('ast',V())))+' unchanged','0 for every variable'],0,'Use the selected variable and the operator’s derivative rule, including any inside factor.')
    if 'encoding' in d:
        a=' '.join(r['id'] for r in d['encoding']['records']);return check('Which node sequence is stored in the smaller final encoding?',[a,a+' H','Only its last root'],0,'Storage order contains every node once; the header is not a record.')
    if 'stackForest' in d:
        a=len(d['stackForest']);return check('How many completed roots remain on the smaller reconstruction stack?',[str(a),str(a+1),str(a+2)],0,'Each remaining stack tree is one forest root.')
    if 'stack' in d and 'degree' in d:
        a=str(d['value']);return check('What result did the smaller highlighted node just push?',[a,str(d['value']+1),str(d['value']+2)],0,'Consume exactly its ordered child group, then use its local rule.')
    if 'isTree' in d:
        return check('Does the smaller displayed graph satisfy the free-tree conditions?',['Yes','No'],0 if d['isTree'] else 1,'Both connectedness and absence of cycles matter.')
    if 'components' in d:
        c=len(d['components']) if isinstance(d['components'],list) else d['components'];return check('How many connected pieces are in the final smaller graph?',[str(c+1),str(c),str(c+2)],1,'Count separate reachable components after the displayed edge change.')
    if 'exists' in d:return check('Do the smaller candidate’s arc degrees and support admit an Euler trail?',['Yes','No'],0 if d['exists'] else 1,'Degree constraints and weak connectivity are both tested.')
    if 'root' in d:return check('Which vertex is the root flag in the final smaller view?',[d['root'],'No root is chosen','Every vertex'],0,'The flag specifies the distinguished root; arrows follow the stated orientation convention.')
    if 'flat' in d:
        a=len(d['flat']);return check('How many nonzero monomial coefficients remain in the smaller result?',[str(a+1),str(a),str(a+2)],1,'Ignore the mandatory zero-exponent placeholder if its coefficient is zero.')
    if 'parent' in d:
        p=d['parent'];a=sum(i==v for i,v in enumerate(p));return check('How many equivalence classes remain in the smaller forest?',[str(a),str(a+1),str(a+2)],0,'There is one class per root, identified here by a self-parent.')
    if 'peak' in d:return check('What peak pending-stack height is shown for the smaller chain?',[str(d['peak']),str(d['peak']+1),'0'],0,'Every node on the initial left descent is saved.')
    if 'interval' in d:return check('What is the smaller highlighted subtree’s scope endpoint?',[str(d['interval'][1]),str(d['interval'][0]),str(d['interval'][1]+1)],0,'Scope is the first address after the subtree, not the subtree’s starting address.')
    if 'lastExits' in d:return check('How many nonroot last-exit tickets are selected in the smaller tour?',[str(len(d['lastExits'])),str(len(d['lastExits'])+1),'Every ticket'],0,'Select one outgoing last exit for each nonroot, and none for the terminal root.')
    if 'tree' in d and isinstance(d['tree'],(list,tuple)):
        a=len(border(d['tree']));return check('How many actual data nodes are in the smaller displayed tree?',[str(a),str(a+1),str(a+2)],0,'Count node identities; empty slots and the header are not data nodes.')
    if 'links' in d and 'copy' in d:return check('Does the smaller copy point back into the original address set?',['Yes','No'],1,'The address map replaces every child, thread and sentinel target.')
    if 'copy' in d:return check('Does the smaller copied header have its own fresh identity?',['Yes','No'],0,'A complete independent copy includes the header in its address map.')
    if 'pre' in d:
        a=' '.join(d['pre']) or 'empty';return check('What is the preorder word of this smaller binary case?',[a,'the header first','each node twice'],0,'Emit each data node before its left and right subtrees.')
    if 'decoded' in d:
        a=len(d['decoded']);return check('How many forest roots does the smaller round trip recover?',[str(a),str(a+1),str(a+2)],0,'A right-sibling chain between roots recovers separate trees.')
    if 'forest' in d:
        a=len(forder(d['forest']));return check('How many distinct nodes belong to this smaller forest?',[str(a),str(a+1),str(a+2)],0,'Count each node identity once across the disjoint root trees.')
    if 'walk' in d:
        a=len(d['walk'])-1;return check('How many arc traversals does the smaller realized walk contain?',[str(a),str(a+1),str(a+2)],0,'A walk of k arcs has k+1 vertex positions, counting repetitions.')
    if 'divergence' in d:
        total=sum(d['divergence'].values());return check('What is the sum of outgoing-minus-incoming counts over all vertices?',[str(total),'1','2'],0,'Each directed edge contributes one positive and one negative count.')
    if 'parents' in d:
        a=len(d['links']);return check('How many '+d['layer']+' links are selected in this smaller layer?',[str(a),str(a+1),str(a+2)],0,'Count the actual links in this named relation, not all tree edges.')
    return check('In this smaller scene, are a navigation link and the object it names the same thing?',['Yes','No'],1,'An identity is the object; a link is a stored relation pointing to that identity.')


def focused_help_check(order,pid,states):
    fixes={
      (107,'limits'):check('A second reference reaches C after C is completed. Does that alone establish a cycle?',['Yes','No'],1,'Only a return to a currently active ancestor certifies a back-edge cycle.'),
      (108,'once'):check('In the one-node tree Z, how often is Z emitted by each traversal order?',['Once','Three times','Never'],0,'There are three different order rules, each emitting its one node once.'),
      (109,'proof-stack'):check('After the one-node subtree U is completely traversed, does it leave one of its own pending cards?',['Yes','No'],1,'Its single push is matched by its pop; older caller cards would be untouched.'),
      (110,'cost-thread'):check('The smaller tree’s final node has a right thread to H. How many real left-child descents does that final successor query make?',['Zero','One','Two'],0,'The right tag is 1, so the query returns its thread target immediately.'),
      (112,'bijection'):check('Decoding the single binary node U produces which forest?',['One tree consisting of U','The empty forest','Two trees'],0,'A binary leaf has no child forest and no remaining sibling forest.'),
      (112,'meaning'):check('In the recovered smaller forest U(V),W, is W an original child of U?',['Yes','No'],1,'W was linked through the binary right slot because it is a second forest root.'),
      (113,'polish'):check('In the smaller expression 2+3, where does the + token appear in postfix?',['Before both operands','After both operands','Between the operands'],1,'Postorder finishes both child expressions before emitting their operator.'),
      (114,'rules-domain'):check('For the smaller square x², which derivative does the fixed-power rule produce?',['2x','x','2'],0,'Multiply by the exponent and lower it by one, then multiply by D(x)=1.'),
      (116,'work-fold'):check('Just before evaluating U with leaf children V and W, how many child values are waiting?',['One','Two','Zero'],1,'Both leaves finish before their parent, so both results accumulate.'),
      (118,'canonical'):check('After x plus −x cancels in the smaller case, what is the canonical root?',['A variable node x','The constant zero','An empty untyped pointer'],1,'Zero is represented explicitly as one constant; no positive exponent survives.'),
      (118,'links-and-cost'):check('After 1+2x plus −2x collapses to 1, does a variable child remain to carry a parent link?',['Yes','No'],1,'The entire structure is now one constant 1; obsolete variable children are removed.'),
      (119,'unique-path'):check('In the smaller three-island chain, how many simple routes join its two endpoints?',['One','Two','Three'],0,'No cycle provides an alternative route.'),
      (119,'bridges'):check('The smaller chain loses one of its two bridges. Is there another route around the missing bridge?',['Yes','No'],1,'A tree has no cycle supplying a detour, so its components separate.'),
      (122,'last-exit-tree'):check('In the smaller U→V→U tour ending at U, which ticket is the nonroot’s last exit?',['U→V','V→U','Both tickets'],1,'Only V is a nonroot; its last exit points toward terminal root U.')
    }
    return fixes.get((order,pid),smaller_check(states))

def normalize_content(lessons):
    for l in lessons:
        for sec in l['sections']:
            for p in sec['passages']:
                d=p['demonstration']
                if d['model']['kind'].startswith('focused-'):d['simplerHelp']['check']=focused_help_check(l['order'],p['id'],d['simplerHelp']['states'])
                for group in [d['states'],d['simplerHelp']['states']]:
                    for s in group:
                        for n in s['diagram']['nodes']:
                            if n.get('role')=='result' and n['type']=='text':n['result']=True
                            # Use supported role-based color semantics; no source artwork.
                d['model']['implementation']='scripts/fullbook-batch-E.py'
    return lessons


def shapes(n):
    if n==0:return [None]
    return [B('?',l,r) for k in range(n) for l in shapes(k) for r in shapes(n-1-k)]
def label_shape(t):
    i=0
    def f(t):
        nonlocal i
        if t is None:return None
        name='N'+str(i);i+=1
        return B(name,f(t[1]),f(t[2]))
    return f(t)

def assert_tour(arcs,tour):
    assert sorted(tour)==list(range(len(arcs)))
    assert all(arcs[a][1]==arcs[b][0] for a,b in zip(tour,tour[1:]))
def brute_euler(arcs):
    if not arcs:return True
    def go(v,left):
        if not left:return True
        return any(go(arcs[i][1],left-{i}) for i in left if arcs[i][0]==v)
    return any(go(v,set(range(len(arcs)))) for v in set(u for u,v in arcs))

def semantic_tests():
    counts=Counter()
    for n in range(7):
        for shape in shapes(n):
            t=label_shape(shape);f=forest(t);counts['binary_shapes']+=1
            assert binary(f)==t
            for kind in ('pre','family','level','post'):
                enc=encode(f,kind);assert decode(enc)==f;counts['sequence_roundtrips']+=1
            assert forder(f,'pre')==border(t,'pre') and forder(f,'post')==border(t,'in')
            assert [r['id'] for r in encode(f,'family')['records']]==border(t,'post')[::-1]
            tr=inorder_stack(t);assert tr[-1]['output']==border(t);assert all(len(set(e['stack']))==len(e['stack']) for e in tr)
            events=contour(t)
            for kind in ('pre','in','post'):assert [e['node'] for e in events if e['phase']==kind]==border(t,kind)
            nodes=threaded(t);order=border(t);assert successor(nodes,'H')==(order[0] if order else 'H')
            assert predecessor(nodes,'H')==(order[-1] if order else 'H')
            for i,v in enumerate(order):
                assert successor(nodes,v)==(order[i+1] if i+1<len(order) else 'H')
                assert predecessor(nodes,v)==(order[i-1] if i else 'H')
                nn=insert_right(nodes,v,'fresh');seq=[];q=successor(nn,'H')
                while q!='H':seq.append(q);q=successor(nn,q);assert len(seq)<=n+1
                assert seq==order[:i+1]+['fresh']+order[i+1:]
                # Reconstruct only child links, then independently regenerate every thread.
                def rebuild(v):
                    if v=='H':return None
                    z=nn[v];return B(v,rebuild(z['L']) if z['LT']==0 else None,rebuild(z['R']) if z['RT']==0 else None)
                nt=rebuild(nn['H']['L']);assert threaded(nt)==nn;counts['thread_insertions']+=1
            cp,m=copy_threads(nodes);assert set(cp).isdisjoint(nodes)
            assert all(z[k] in cp for z in cp.values() for k in ('L','R'))
            assert all(cp[m[v]]['L']==m[z['L']] and cp[m[v]]['R']==m[z['R']] for v,z in nodes.items())
            # Ordered fold checked against a separate recursive evaluator.
            def rec(t):return sum((i+1)*rec(c) for i,c in enumerate(t[1])) if t[1] else len(t[0])+1
            result,_=fold_records(encode(f,'post')['records'],lambda v,ch:sum((i+1)*x for i,x in enumerate(ch)) if ch else len(v)+1)
            assert result==[rec(t) for t in f]
    collision=threaded(B('copy:H',B('copy:copy:H'),B('copy:copy:copy:H')))
    fresh,mapping=copy_threads(collision)
    assert set(fresh).isdisjoint(collision)
    assert all(z[k] in fresh for z in fresh.values() for k in ('L','R'))
    counts['adversarial_copy_namespaces']=1
    for recs in [[{'id':'X','degree':1}],[{'id':'X','degree':-1}]]:
        try:decode({'kind':'post','records':recs});raise AssertionError('bad degree accepted')
        except ValueError:pass
    # All simple undirected graphs on at most five vertices: edge-count characterization.
    for n in range(1,6):
        vs=list(range(n));possible=list(combinations(vs,2))
        for mask in range(1<<len(possible)):
            es=[e for i,e in enumerate(possible) if mask>>i&1];c=len(components(vs,es))
            # Independent disjoint-set cycle oracle.
            parent=list(range(n))
            def find(x):
                while parent[x]!=x:x=parent[x]
                return x
            acyclic=True
            for u,v in es:
                a,b=find(u),find(v)
                if a==b:acyclic=False
                else:parent[a]=b
            assert (c==1 and acyclic)==(c==1 and len(es)==n-1)
            assert acyclic==(len(es)==n-c)
            if c==1 and acyclic:
                for r in vs:
                    arcs=root_arcs(vs,es,r);outdeg=Counter(u for u,v in arcs)
                    assert outdeg[r]==0 and all(outdeg[v]==1 for v in vs if v!=r)
            counts['simple_graphs']+=1
    # Directed multigraph tickets on three vertices, including loops and parallel arcs.
    # Independent exhaustive permutation/backtracking existence, up to four tickets.
    poss=list(product(range(3),repeat=2))
    for m in range(5):
        for arcidx in __import__('itertools').combinations_with_replacement(range(9),m):
            arcs=[poss[i] for i in arcidx];expected=brute_euler(arcs)
            try:tour,_=euler(arcs);actual=True;assert_tour(arcs,tour)
            except ValueError:actual=False
            assert actual==expected,(arcs,actual,expected);counts['directed_multigraphs']+=1
            if actual and arcs and arcs[tour[0]][0]==arcs[tour[-1]][1]:
                root=arcs[tour[0]][0];last=last_exits(arcs,tour,root)
                for v in last:
                    seen=set();w=v
                    while w!=root:assert w not in seen;seen.add(w);w=arcs[last[w]][1]
    # Exact dual-number arithmetic independent of symbolic construction for polynomials/quotients.
    def dual(a,x):
        op=a[0]
        if op=='c':return Fraction(a[1]),Fraction(0)
        if op=='v':return (x,Fraction(1)) if a[1]=='x' else (Fraction(3),Fraction(0))
        u,du=dual(a[1],x)
        if op=='neg':return -u,-du
        v,dv=dual(a[2],x)
        if op=='+':return u+v,du+dv
        if op=='-':return u-v,du-dv
        if op=='*':return u*v,du*v+u*dv
        if op=='/':return u/v,(du*v-u*dv)/(v*v)
        if op=='pow':return u**int(v),int(v)*u**(int(v)-1)*du
    atoms=[V(),V('a'),C(2),C(-1)]
    exprs=[(op,a,b) for op in ('+','-','*','/') for a in atoms for b in atoms]+[('pow',('+',V(),C(2)),C(3)),('*',V(),('pow',('+',V(),C(2)),C(2)))]
    for a in exprs:
        assert ast_valid(a) and ast_valid(diff(a));source=copy.deepcopy(a)
        for x in map(Fraction,[-3,-1,1,2,4]):
            try:value,der=dual(a,x);actual=ev(diff(a),{'x':x,'a':Fraction(3)});post,_=eval_postfix(postfix(a),{'x':x,'a':Fraction(3)})
            except ZeroDivisionError:continue
            assert actual==der and ev(a,{'x':x,'a':Fraction(3)})==post==value;counts['exact_ast_cases']+=1
        assert a==source
    assert not ast_valid(('+',V()))
    for a in [('ln',('+',V(),C(2))),('exp',('*',C(2),V())),('pow',V(),V())]:
        for x in [1.,2.,3.]:
            h=1e-5;approx=(ev(a,{'x':x+h})-ev(a,{'x':x-h}))/(2*h);exact_rule=ev(diff(a),{'x':x})
            assert abs(approx-exact_rule)<=2e-7*max(1,abs(exact_rule));counts['approximate_sanity_checks']+=1
    # Canonical polynomial dictionaries across coefficient cancellations, with exact evaluations.
    mons=[(0,0),(1,0),(0,1),(1,1)]
    polys=[]
    for coeffs in product([-1,0,1],repeat=4):
        d={k:c for k,c in zip(mons,coeffs) if c};p=poly_tree(d);assert poly_flat(p)==d;polys.append((d,p));counts['canonical_polynomials']+=1
    for da,a in polys:
        for db,b in polys:
            d={k:da.get(k,0)+db.get(k,0) for k in set(da)|set(db)};d={k:c for k,c in d.items() if c};c=poly_add(a,b)
            assert poly_flat(c)==d and c==poly_tree(d)
            assert poly_value(c,2,-3)==poly_value(a,2,-3)+poly_value(b,2,-3);counts['polynomial_additions']+=1
    assert divergence(FLOW_V,FLOW_E,FLOW_P)==dict(S=1,A=0,B=0,T=-1)
    for c in FLOW_C:assert all(v==0 for v in divergence(FLOW_V,FLOW_E,c).values())
    reserved_exit_states();counts['reserved_exit_constructions']=1
    for small in (False,True):
        trace=ring_mutation_trace(small);assert trace[-1]['tree']==(1 if small else poly_tree({(1,0):1}))
        counts['mutable_polynomial_ring_stages']+=len(trace)
    for tr in [union_trace(5,[(0,1),(2,3),(1,2),(0,3),(3,4)])]:
        edges=[]
        for e in tr:
            edges.append(e['pair']);cs=components(list(range(5)),edges);p=e['parent']
            def rt(v):
                seen=set()
                while p[v]!=v:assert v not in seen;seen.add(v);v=p[v]
                return v
            assert sorted(sorted(v for v in range(5) if rt(v)==r) for r in set(rt(v) for v in range(5)))==sorted(cs)
    return dict(counts)


def structural_tests(lessons):
    assert [l['order'] for l in lessons]==list(range(106,123))
    demos=[]
    for l in lessons:
        ps=[p for s in l['sections'] for p in s['passages']];assert len(ps)>=3
        for p in ps:
            assert len(p['text'])>250
            d=p['demonstration'];demos.append(d);assert len(d['states'])>=2 and len(d['simplerHelp']['states'])>=2
            for c in [d['check'],d['simplerHelp']['check']]:assert 0<=c['correctIndex']<len(c['choices']) and len(set(c['choices']))==len(c['choices'])
            assert d['check']['prompt']!=d['simplerHelp']['check']['prompt']
            for ss in [d['states'],d['simplerHelp']['states']]:
                assert len({s['id'] for s in ss})==len(ss)
                for s in ss:
                    ns=s['diagram']['nodes'];assert ns and len({n['id'] for n in ns})==len(ns),(l['order'],p['id'],s['id'])
                    for n in ns:
                        for k in ['x','y','x2','y2','r','height','width']:
                            if k in n:assert isinstance(n[k],(int,float)) and math.isfinite(n[k])
                        if n['type']=='text':assert 20<=n['x']<=700 and 20<=n['y']<=430,(l['order'],p['id'],s['id'],n)
            assert len(d['transitions'])==len(d['states'])-1
    return {'lessons':len(lessons),'demonstrations':len(demos),'mainStates':sum(len(d['states']) for d in demos),'helpStates':sum(len(d['simplerHelp']['states']) for d in demos)}

def add_notation_readings(lessons):
    readings = {
      (106,'recursive-definition'): 'Read the symbol ⊔ as “disjoint union”: put these node sets together without sharing a node. The braces {r} mean the set containing only the root. T₁ through Tₖ are the child trees, with k naming how many child trees there are.',
      (106,'levels'): 'The letter ℓ names a level number. Thus ℓ(child)=ℓ(parent)+1 says that following one child edge increases the number of steps from the root by one.',
      (106,'binary-slots'): 'In (r,L,R), r is the root node, L the left child tree, and R the right child tree. The symbol ∅ means an empty tree. The order of L and R matters even when one is empty.',
      (106,'size-induction'): 'The bars in |T| mean “number of nodes in tree T”. The 1 counts the root. The sum adds |T₁|, then |T₂|, and so on through |Tₖ|: the node counts of all k child trees. Disjoint child trees ensure that no node is counted twice.',
      (114,'postorder-transform'): 'AST means abstract syntax tree: a tree whose nodes record the operators and operands of an expression. D means “take the derivative with respect to x”. It creates a new expression describing the rate of change; it does not evaluate the original expression at a chosen number.',
      (114,'product-chain'): 'Read Du and u′ as the derivative of u with respect to x. In g′, the prime means the derivative of g with respect to its own input. The circle ∘ means composition: (g∘u)(x)=g(u(x)), so u runs first and g uses its result. Multiplication by Du supplies the rate at which that inner input changes.',
      (120,'incidence'): 'B is the incidence matrix: each column records where one directed edge leaves and arrives. The bold symbol 1_s is a vector with 1 in the row for the start vertex s and 0 in every other row; 1_t does the same for the stop vertex. The vector c_j records the signed edge counts of fundamental cycle j. Consequently Bc_j=0 says that this cycle has no net surplus departure at any vertex.',
      (120,'basis-proof'): 'In the formula, f is the complete edge-count vector and p is a chosen start-to-stop path vector. The index j names a fundamental cycle; c_j is that cycle’s signed edge-count vector, and α_j tells how many signed copies to add. The summation adds these contributions for all m−n+1 non-tree edges. This is a vector equation: it must hold separately for every edge.',
      (122,'degree-and-connectivity'): 'Read deg⁺(v) as the number of outgoing arcs at vertex v and deg⁻(v) as the number of incoming arcs. The indicator 1_{v=s} is 1 when v is the start s and 0 otherwise; the indicator for t works the same way. Thus the formula gives +1 at a distinct start, −1 at a distinct stop, and 0 elsewhere. When start and stop coincide, the two indicators cancel.'
    }
    for lesson in lessons:
        for section in lesson['sections']:
            for passage in section['passages']:
                reading=readings.get((lesson['order'],passage['id']))
                if reading:
                    passage['text'] += '\n\n'+reading
                    passage['demonstration']['states'][0]['teachingExplanation']=reading
    return lessons

def build():return add_notation_readings(normalize_content(add_focused_demos(build_first()+build_middle()+build_last())))
if __name__=='__main__':
    if '--test' in sys.argv:
        result=semantic_tests();lessons=build();result.update(structural_tests(lessons));print(json.dumps(result,sort_keys=True));sys.exit()
    lessons=build();structural_tests(lessons)
    path=ROOT/'content/fullbook/batch-E.json';path.write_text(json.dumps(lessons,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'written':str(path),'lessons':len(lessons),'bytes':path.stat().st_size}))
