#!/usr/bin/env python3
"""Original, deterministic discrete-mathematics authoring and executable models.
Run normally to rebuild batch-A.json; --test runs independent mathematical checks.
No source PDF content is embedded. Fractions and integers are serialized as strings.
"""
from fractions import Fraction as F
from itertools import combinations, permutations, product
from math import comb, factorial, gcd, floor, ceil, log, sqrt, pi, exp
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]

def txt(i,x,y,s,role='input',size=17):return dict(id=i,type='text',x=x,y=y,text=str(s),fontSize=size,anchor='middle',role=role)
def rect(i,x,y,w,h,role='input',**kw):return dict(id=i,type='rect',x=x,y=y,width=w,height=h,role=role,**kw)
def line(i,x,y,x2,y2,role='muted'):return dict(id=i,type='line',x=x,y=y,x2=x2,y2=y2,role=role)
def dot(i,x,y,role='active',r=6):return dict(id=i,type='circle',x=x,y=y,r=r,role=role)
def tile(i,x,y,s,role='input',w=64,h=42):return [rect(i,x,y,w,h,role),txt(i+'-label',x+w/2,y+h/2+6,s,role)]
def state(i,caption,formula,nodes,inv='',data=None):
 return dict(id=str(i),caption=caption,formula=formula,diagram=dict(title=caption,description=caption,viewBox=[0,0,720,440],nodes=nodes,invariant=inv),computed=data or {})
def fib(n):
 a,b=0,1
 for _ in range(n):a,b=b,a+b
 return a
def choose(x,k):
 if k<0:return F(0)
 return F(falling(F(x),k),factorial(k))
def falling(x,k):return prod(x-j for j in range(k))
def rising(x,k):return prod(x+j for j in range(k))
def prod(it):
 r=1
 for x in it:r*=x
 return r
def harmonic(n,r=1):return sum((F(1,k**r) for k in range(1,n+1)),F(0))
def stirling(n,k,first=False):
 row=[1]
 for i in range(1,n+1):row=[0]+[( (i-1 if first else j)*(row[j] if j<len(row) else 0)+row[j-1]) for j in range(1,i+1)]
 return row[k] if 0<=k<len(row) else 0

def snapshot_step(q):
 n,pc,out=q
 if pc=='DONE':return q
 if pc=='CHECK':return (n,'MOVE' if n else 'DONE',out)
 return (n-1,'CHECK',out+1) if n else (0,'DONE',out)
def rewrite_step(s,j,pattern='ab',replacement='ba'):
 if j==1:return s,j
 at=s.find(pattern)
 return (s[:at]+replacement+s[at+len(pattern):],0) if at>=0 else (s,1)

def model(order,small=False):
 """Each branch supplies a different spatial meaning; helper inputs are recomputed."""
 S=[]
 if order==21:
  n=1 if small else 3;q=(n,'CHECK',0)
  for k in range(2*n+3):
   left,pc,out=q; nodes=[txt('in',160,75,'incoming tray'),txt('out',545,75,'delivered tray'),rect('tray-in',50,100,230,190,'muted',fill='none'),rect('tray-out',430,100,230,190,'muted',fill='none'),*tile('badge',300,330,pc,'active',120)]
   for j in range(n):
    done=j<out;nodes+=tile(f'parcel-{j}',(460+j*57 if done else 75+(j-out)*57),165,j+1,'result' if done else 'input',48)
   cap=f'{pc}: {left} waiting, {out} delivered.'
   S.append(state(k,cap,fr'q=({left},\mathrm{{{pc}}},{out})',nodes,'waiting + delivered = original input',dict(waiting=left,pc=pc,output=out)))
   q=snapshot_step(q)
 elif order==22:
  s='ab' if small else 'aabb';j=0
  for k in range(10):
   at=s.find('ab') if j==0 else -1;nodes=[txt('rule',360,65,'Rule 0: first ab → ba; no match → DONE')]
   for t,c in enumerate(s):nodes+=tile(f'position-{t}',100+t*100,145,c,'active' if at<=t<at+2 and at>=0 else 'input',70,60)
   nodes+=[txt('scan',360,265,f'First match starts at {at}' if at>=0 else 'No match remains'),*tile('pc',285,320,'DONE' if j else 'rule 0','result' if j else 'active',150)]
   S.append(state(k,f'Word {s}, control {j}.',fr'(\sigma,j)=(\mathrm{{{s}}},{j})',nodes,'Each rewrite preserves the counts of a and b.',dict(word=s,control=j,match=at)))
   if j:break
   s,j=rewrite_step(s,j)
 elif order==23:
  n=6 if small else 12; values=list(range(2,n+1));deps={v:next(((d,v//d) for d in range(2,v) if v%d==0),None) for v in values}
  for upto in ([2,4,6] if small else [3,6,12]):
   nodes=[txt('meaning',360,45,'Every integer ≥ 2 has a prime factorization')]
   def pos(v):return (65+(v-2)%6*112,130+(v-2)//6*150)
   for v in values:
    x,y=pos(v)
    if deps[v] and v<=upto:
     for d in set(deps[v]):
      xx,yy=pos(d);nodes.append(line(f'dep-{v}-{d}',x,y-23,xx,yy+23,'active'))
   for v in values:
    x,y=pos(v);nodes+=[dot(f'n{v}',x,y,'result' if v<=upto else 'muted',23),txt(f'l{v}',x,y+6,v),txt(f'f{v}',x,y+48,('prime' if not deps[v] else f'{deps[v][0]} × {deps[v][1]}'),size=14)]
   S.append(state(upto,f'Cases through {upto} have smaller supports.',r'n=ab,\quad 2\le a,b<n',nodes,'Every dependency points to a strictly smaller integer.',dict(dependencies={str(v):deps[v] for v in values if v<=upto})))
 elif order==24:
  z=(1,1) if small else (2,1);w=(1,1);points=[z,(z[0]+w[0],z[1]+w[1]),z,(z[0]-z[1],z[0]+z[1])]
  for k,(a,b) in enumerate(points):
   nodes=[line('real',65,300,650,300),line('imag',250,375,250,60),txt('re',630,327,'real'),txt('im',285,60,'imag'),line('vector',250,300,250+75*a,300-75*b,'active'),dot('tip',250+75*a,300-75*b),txt('value',360,400,f'{a} + {b}i')]
   for v in range(-2,5):nodes+=[txt(f'axis{v}',250+75*v,323,v,size=14)]
   cap=['Start with z.','Add 1+i: translate by one in each direction.','Reset to the original z before a different operation.','Multiply z by 1+i: rotate 45° and scale by √2.'][k]
   S.append(state(k,cap,[fr'z={z[0]}+{z[1]}i',fr'z+(1+i)={a}+{b}i',fr'z={z[0]}+{z[1]}i',fr'z(1+i)={a}+{b}i'][k],nodes,'Addition and multiplication each begin from the original z.',dict(real=a,imag=b,operation=['input','add','reset','multiply'][k])))
 elif order==25:
  n=3 if small else 5;fixed=2 if small else 3;cells=[(i,j) for i in range(1,n+1) for j in range(1,i+1)];total=sum(i+j for i,j in cells)
  for stage in range(4):
   nodes=[txt('head',360,35,['Hold row i fixed; vary j across its legal cells.','Visit every row: each legal pair appears once.','Hold column j fixed; vary i down its legal cells.','Visit every column: exactly the same labeled terms.'][stage],size=16)]
   for j in range(1,n+1):nodes.append(txt(f'column{j}',162+(j-1)*100,69,f'j={j}',size=14))
   for i in range(1,n+1):nodes.append(txt(f'row{i}',70,112+(i-1)*53,f'i={i}',size=14))
   for i,j in cells:
    selected=(i==fixed if stage==0 else j==fixed if stage==2 else True);x=120+(j-1)*100;y=85+(i-1)*53
    nodes += [rect(f'cell-{i}-{j}',x,y,84,46,'active' if selected else 'muted',opacity=1 if selected else .2),txt(f'cell-{i}-{j}-label',x+42,y+18,i+j,size=16),txt(f'pair-{i}-{j}',x+42,y+37,f'({i},{j})',size=14)]
   # The selecting outline changes from a horizontal row to a vertical column.
   if stage==0:x,y,w,h=115,80+(fixed-1)*53,fixed*100-6,56
   elif stage==2:x,y,w,h=115+(fixed-1)*100,80+(fixed-1)*53,94,(n-fixed+1)*53+3
   else:x,y,w,h=115,80,n*100-6,n*53+3
   nodes.append(rect('group-selector',x,y,w,h,'active',fill='none'))
   for i in range(1,fixed):nodes.append(dict(**txt(f'missing-{i}',162+(fixed-1)*100,113+(i-1)*53,'no cell',size=14),opacity=1 if stage==2 else 0))
   for j in range(1,n+1):nodes.append(rect(f'column-group{j}',115+(j-1)*100,80+(j-1)*53,94,(n-j+1)*53+3,'active',fill='none',opacity=1 if stage==3 else 0))
   formulas=[fr'\sum_{{j=1}}^{{{fixed}}}({fixed}+j)={sum(fixed+j for j in range(1,fixed+1))}',fr'\sum_{{i=1}}^{{{n}}}\sum_{{j=1}}^i(i+j)={total}',fr'j={fixed}:\quad\sum_{{i={fixed}}}^{{{n}}}(i+{fixed})={sum(i+fixed for i in range(fixed,n+1))}',fr'\sum_{{j=1}}^{{{n}}}\sum_{{i=j}}^{{{n}}}(i+j)={total}']
   notes=[f'i={fixed} is fixed; j runs from 1 through {fixed}.',f'Outer i runs 1…{n}; inner j runs 1…i.',f'j={fixed}: rows i < {fixed} have no cell; i runs {fixed}…{n}.',f'Outer j runs 1…{n}; inner i starts at j and ends at {n}.']
   nodes.append(txt('bounds-note',360,396,notes[stage],size=15))
   S.append(state(stage,notes[stage],formulas[stage],nodes,'Every tile retains its (i,j) identity and value i+j; regrouping neither adds nor loses a term.',dict(n=n,cells=[[i,j,str(i+j)] for i,j in cells],total=str(total),stage=stage,fixedIndex=fixed,selectedPairs=[[i,j] for i,j in cells if (i==fixed if stage==0 else j==fixed if stage==2 else True)])))
 elif order==43:
  n=3 if small else 5;fixed=2 if small else 3;cells=[(i,j) for i in range(1,n+1) for j in range(1,i+1)];total=sum((F(1,j) for i,j in cells),F(0))
  for stage in range(4):
   nodes=[txt('head',360,35,['Rows add the harmonic sums H₁ through Hₙ.','Fix one column: count its identical reciprocal terms.','Regroup the same labeled terms by denominator.','Replace each group by its multiplicity times its term.'][stage],size=16)]
   for i,j in cells:
    x=115+((i if stage>=2 else j)-1)*100;y=85+((j if stage>=2 else i)-1)*53
    nodes += [rect(f'cell-{i}-{j}',x,y,84,46,'active' if (j==fixed or stage>=2) else 'input'),txt(f'cell-{i}-{j}-label',x+42,y+18,str(F(1,j)),size=16),txt(f'pair-{i}-{j}',x+42,y+37,f'({i},{j})',size=14)]
   for j in range(1,n+1):
    nodes.append(dict(**txt(f'index-{j}',70,112+(j-1)*53,f'j={j}' if stage>=2 else f'i={j}',size=14)))
    nodes.append(rect(f'group-{j}',110+((j-1)*100 if stage<2 else (j-1)*100),80+(j-1)*53,94 if stage<2 else (n-j+1)*100-6,(n-j+1)*53+3 if stage<2 else 56,'active',fill='none',opacity=1 if stage>=2 or (stage==1 and j==fixed) else 0))
    for node in tile(f'contribution-{j}',620,85+(j-1)*53,str(F(n-j+1,j)),'result',65,46):node['opacity']=1 if stage==3 else 0;nodes.append(node)
   if stage==0:formula=fr'\sum_{{i=1}}^{{{n}}}H_i=\sum_{{i=1}}^{{{n}}}\sum_{{j=1}}^i\frac1j={total}';note='Each tile keeps its original pair (i,j).'
   elif stage==1:
    formula=fr'j={fixed}:\quad\sum_{{i={fixed}}}^{{{n}}}\frac1{{{fixed}}}=({n}-{fixed}+1)\frac1{{{fixed}}}=\frac{{{n-fixed+1}}}{{{fixed}}}'
    note=f'Column j={fixed} occurs in rows {fixed}…{n}: {n}-{fixed}+1 = {n-fixed+1} copies of 1/{fixed}.'
   else:
    formula=fr'\sum_{{j=1}}^{{{n}}}\frac{{{n}-j+1}}j=({n}+1)H_{{{n}}}-{n}={total}'
    note='A column j contains n−j+1 copies of 1/j; add its single contribution.'
   nodes.append(txt('multiplicity',360,406,note,size=14))
   S.append(state(stage,note,formula,nodes,'Each original pair contributes 1/j once. Group j contains precisely rows i=j,…,n.',dict(n=n,cells=[[i,j,str(F(1,j))] for i,j in cells],total=str(total),stage=stage,fixed=fixed,multiplicities=[n-j+1 for j in range(1,n+1)],contributions=[str(F(n-j+1,j)) for j in range(1,n+1)])))
 elif order==26:
  n=6 if small else 10
  for stage in range(3):
   nodes=[txt('a',205,60,'A: even'),txt('b',515,60,'B: divisible by 3'),rect('A',70,95,350,230,'input',fill='none'),rect('B',300,95,350,230,'active',fill='none')]
   occupied={}
   for k in range(1,n+1):
    a=k%2==0;b=k%3==0
    group=(a,b);slot=occupied.get(group,0);occupied[group]=slot+1
    x=(335 if a and b else 115+(slot%2)*100 if a else 525 if b else 110+slot*100);y=(170+slot*70 if a and b else 145+(slot//2)*95 if a else 145+slot*95 if b else 375)
    role='active' if stage==0 and a or stage==1 and b else 'result' if stage==2 and (a or b) else 'muted';nodes+=tile(f'number{k}',x,y,k,role,40,35)
   A=sum(k%2==0 for k in range(1,n+1));B=sum(k%3==0 for k in range(1,n+1));AB=sum(k%6==0 for k in range(1,n+1))
   S.append(state(stage,['Count A.','Count B; overlap would be counted twice.','Subtract one copy of the overlap.'][stage],fr'|A\cup B|={A}+{B}-{AB}={A+B-AB}',nodes,'Each object has weight [A]+[B]−[A∩B].',dict(n=n,A=A,B=B,intersection=AB,union=A+B-AB)))
 elif order==27:
  n=3 if small else 5
  for stage in range(3):
   nodes=[txt('p',75,65,'plus'),txt('m',75,205,'minus')]
   for k in range(1,n+1):
    nodes+=tile(f'positive{k}',85+(k-1)*100,95,f'1/{k}','result' if k==1 and stage==2 else 'input',78)
    nodes+=tile(f'negative{k+1}',85+(k if stage else k-1)*100,235,f'−1/{k+1}','result' if k==n and stage==2 else 'input',78)
    if stage==2 and k>1:nodes+=[line(f'cancel{k}',124+(k-1)*100,144,124+(k-1)*100,227,'error')]
   nodes+=[txt('total',360,365,f'Uncancelled: 1 − 1/{n+1} = {F(n,n+1)}','result')]
   S.append(state(stage,['Split each reciprocal product into a difference.','Align equal denominators across adjacent terms.','Only the first positive and last negative survive.'][stage],fr'\sum_{{k=1}}^{{{n}}}\frac1{{k(k+1)}}=1-\frac1{{{n+1}}}',nodes,'Cancellation preserves the signed total.',dict(n=n,total=str(sum((F(1,k*(k+1)) for k in range(1,n+1)),F(0))))))
 elif order==28:
  n=3 if small else 5
  for stage in range(3):
   nodes=[txt('numerator',360,65,'numerators'),txt('denominator',360,230,'denominators')]
   for k in range(1,n+1):
    nodes+=tile(f'top{k+1}',85+(k-1)*110,105,k+1,'result' if stage==2 and k==n else 'input',75)
    nodes+=tile(f'bottom{k}',85+(k-1)*110,270,k,'result' if stage==2 and k==1 else 'input',75)
    if stage>0 and k<n:nodes+=[line(f'cancel{k}',120+(k-1)*110,155,120+k*110,262,'active')]
   S.append(state(stage,['Multiply consecutive ratios.','A numerator cancels the next denominator.','The quotient of endpoint factors remains.'][stage],fr'\prod_{{k=1}}^{{{n}}}\frac{{k+1}}k={n+1}',nodes,'Every cancellation divides numerator and denominator by the same nonzero integer.',dict(n=n,total=str(prod(F(k+1,k) for k in range(1,n+1))))))
 elif order==29:
  ns=[1,2,3] if small else [2,4,6]
  for n in ns:
   nodes=[rect('whole',70,125,580,90,'muted',fill='none')];x=70
   for k in range(1,n+1):
    w=580/2**k;nodes+=[rect(f'term{k}',x,125,w,90,'input')];
    if w>=40:nodes+=[txt(f'label{k}',x+w/2,175,f'1/{2**k}',size=14)]
    x+=w
   nodes+=[rect('tail',x,125,650-x,90,'active'),txt('tail-label',360,285,f'Unfilled tail: 1/{2**n}'),txt('partial',360,345,f'Partial sum: {1-F(1,2**n)}')]
   S.append(state(n,f'{n} positive terms leave a controlled gap.',fr'S_{{{n}}}=1-2^{{-{n}}}',nodes,'partial sum + tail = 1 exactly',dict(n=n,partial=str(1-F(1,2**n)),tail=str(F(1,2**n)))))
 elif order==30:
  xs=[F(-1,2),F(0),F(1,2)] if small else [F(-7,3),F(-2),F(7,3)]
  for t,x in enumerate(xs):
   a=floor(x);b=ceil(x);nodes=[line('axis',45,220,675,220)]
   for i in range(-3,4):nodes+=[line(f'tick{i}',360+i*90,211,360+i*90,229),txt(f'lab{i}',360+i*90,260,i)]
   nodes+=[rect('unit',360+a*90,190,90,60,'muted',fill='none'),dot('x',360+float(x)*90,220),txt('x-label',360+float(x)*90,162,str(x)),txt('floor',205,330,f'floor = {a}'),txt('ceil',515,330,f'ceiling = {b}'),txt('frac',360,385,f'fractional part = {x-a}')]
   S.append(state(t,f'Bracket {x} by integers.',fr'{a}\le {x}<{a+1}',nodes,'floor is the left endpoint, even when x is negative.',dict(x=str(x),floor=a,ceiling=b,fraction=str(x-a))))
 elif order==31:
  examples=[(7,3),(-5,3)] if small else [(-8,5)];lo,hi=(-6,9) if small else (-10,5)
  def xpos(v):return 60+(v-lo)*40
  for example,(a,d) in enumerate(examples):
   q=a//d;r=a-q*d;sign=1 if q>=0 else -1
   for stage in range(4):
    nodes=[txt('head',360,40,f'Divide {a} by positive divisor {d}',size=18),line('axis',50,220,675,220)]
    for v in range(lo,hi+1):
     nodes += [line(f'tick{v}',xpos(v),212,xpos(v),228),txt(f'tick-label{v}',xpos(v),251,v,size=14)]
    nodes += [dot('given-location',xpos(a),220,'input',7),txt('given-label',xpos(a),190,f'a={a}',size=16)]
    for k in range(abs(q)):
     start=sign*k*d;end=sign*(k+1)*d
     nodes += [rect(f'quotient-block{k}',min(xpos(start),xpos(end)),275,abs(end-start)*40 if stage>=1 else 0,30,'input'),dict(**line(f'quotient-arrow{k}',xpos(start),290,xpos(end) if stage>=1 else xpos(start),290,'input'),arrow=True),dict(**txt(f'quotient-label{k}',(xpos(start)+xpos(end))/2,326,f'{sign*d:+d}',size=16),opacity=1 if stage>=1 else 0)]
    cursor=0 if stage==0 else q*d if stage==1 else a
    nodes += [dot('division-cursor',xpos(cursor),220,'active',5),dict(**line('remainder-arrow',xpos(q*d),150,xpos(a) if stage>=2 else xpos(q*d),150,'active'),arrow=True,opacity=1 if stage>=2 else 0),dict(**txt('remainder-label',(xpos(q*d)+xpos(a))/2,122,f'+{r}',size=18),opacity=1 if stage>=2 else 0)]
    for k,v in enumerate(range(lo,hi+1)):
     if (v-a)%d==0:nodes.append(dict(**dot(f'class-member{v}',xpos(v),220,'result',11),opacity=1 if stage==3 else 0))
    notes=[f'Locate {a}; the remainder will be an offset, not this coordinate.',f'q = floor({a}/{d}) = {q}; whole blocks stop at {q*d}.',f'From {q*d}, move right by {r} to reach {a}; 0 ≤ {r} < {d}.',f'Locations spaced {d} apart share remainder {r}.']
    nodes += [dict(**txt('division-equation',360,369,f'{a} = ({q}) × {d} + {r}','result',18),opacity=1 if stage>=2 else 0),txt('operation-note',360,409,notes[stage],size=14)]
    formulas=[fr'a={a},\quad d={d}>0',fr'q=\lfloor {a}/{d}\rfloor={q},\quad qd={q*d}',fr'{a}=({q})\cdot {d}+{r},\quad 0\le {r}<{d}',fr'a\equiv {r}\pmod{{{d}}},\quad a=qd+r,\quad 0\le r<d']
    S.append(state(f'{example}-{stage}',notes[stage],formulas[stage],nodes,'The quotient uses floor division; for positive d the remainder is a nonnegative offset smaller than d.',dict(a=a,d=d,q=q,r=r,stage=stage,example=example,blockEndpoint=q*d,classMembers=[v for v in range(lo,hi+1) if (v-a)%d==0])))
 elif order==32:
  m=5 if small else 7;a=2 if small else 3
  for stage in range(3):
   nodes=[txt('top',360,45,f'Residues modulo {m}')]
   for k in range(m):
    x=75+k*85;v=(a*k)%m
    nodes+=tile(f'from{k}',x,90,k,'input',60)
    nodes+=tile(f'to{k}',75+(v if stage else k)*85,260,v if stage else k,'result' if stage==2 else 'active',60)
    if stage:nodes+=[line(f'edge{k}',x+30,138,105+v*85,250,'active')]
   nodes+=[txt('rule',360,365,f'Multiply each label by {a}, then take its remainder')]
   S.append(state(stage,['Start with every residue class once.','Reduce the products and move each tile to its remainder.','No collision: multiplication is invertible for this multiplier.'][stage],fr'r\mapsto {a}r\bmod {m}',nodes,'gcd(multiplier, modulus)=1 makes this a permutation.',dict(modulus=m,multiplier=a,residues=[a*k%m for k in range(m)])))
 elif order==33:
  n=3 if small else 5;k=2 if small else 3;labels='ABCDE'[:n]
  for depth in range(k+1):
   nodes=[txt('head',360,30,'Expand one prefix; every same-depth prefix has equal choices.',size=16),*tile('root',320,55,'∅','input',80,35)]
   for level in range(1,k+1):
    prefix=labels[:level-1];choices=[v for v in labels if v not in prefix]
    for j,v in enumerate(choices):
     x=65+j*110 if level==1 else 100+j*125 if level==2 else 150+j*155;y=110+(level-1)*88
     parentx=360 if level==1 else (105 if level==2 else 140);parenty=90 if level==1 else 150+(level-2)*88
     nodes.append(dict(**line(f'branch-{prefix+v}',parentx,parenty,x+40,y-5,'active'),opacity=1 if level<=depth else 0))
     for node in tile('prefix-'+prefix+v,x,y,prefix+v,'active' if j==0 else 'input',80,40):node['opacity']=1 if level<=depth else 0;nodes.append(node)
   count=falling(n,depth);factors=[n-j for j in range(depth)]
   note='The empty prefix is one starting choice.' if depth==0 else (f'Each of the {falling(n,depth-1)} length-{depth-1} prefixes has {n-depth+1} unused next badges.')
   nodes += [txt('branch-rule',360,375,note,size=15),txt('count',360,415,(' × '.join(map(str,factors)) or '1')+f' = {count} prefixes','result',18)]
   S.append(state(depth,note,('1' if depth==0 else r'\cdot'.join(map(str,factors)))+f'={count}',nodes,'Only one earlier prefix is expanded in detail; unused-badge count is identical for every prefix at that depth.',dict(n=n,k=depth,count=count,branchFactors=factors,expandedPrefix=labels[:max(0,depth-1)],nextChoices=[v for v in labels if v not in labels[:max(0,depth-1)]])))
 elif order==34:
  n=6 if small else 10;p=2
  for power in (2,4,8):
   nodes=[txt('head',360,50,f'Count factors of {p} inside {n}!')]
   for k in range(1,n+1):
    x=55+(k-1)*64;nodes+=tile(f'factor{k}',x,110,k,'active' if k%power==0 else 'input',48)
    v=0;t=k
    while t%p==0:t//=p;v+=1
    for j in range(v):nodes+=[rect(f'prime-{k}-{j}',x+10,190+j*45,25,32,'result' if p**(j+1)<=power else 'muted'),txt(f'prime-label-{k}-{j}',x+22,213+j*45,p,size=14)]
   total=sum(n//p**j for j in range(1,20));nodes+=[txt('value',360,385,f'ν₂({n}!) = {total};  {n}! = {factorial(n)}')]
   S.append(state(power,f'Multiples of {power} contribute another layer.',fr'\nu_2({n}!)=\sum_{{j\ge1}}\lfloor {n}/2^j\rfloor={total}',nodes,'A factor divisible by 2^r is counted in exactly r layers.',dict(n=n,prime=p,power=power,valuation=total,factorial=str(factorial(n)))))
 elif order==35:
  # Γ(2)=∫t e^-t dt; decreasing f=e^-t gives rigorous rectangle bounds for Γ(1).
  T=4 if small else 8;counts=[4,8,16]
  for N in counts:
   h=T/N;lo=h*sum(exp(-j*h) for j in range(1,N+1));hi=h*sum(exp(-j*h) for j in range(N));tail=exp(-T)
   nodes=[line('xaxis',65,310,665,310),line('yaxis',65,310,65,75),txt('f',360,45,'Γ(1): area under exp(−t)')]
   for j in range(N):nodes+=[rect(f'bar{j}',65+570*j/N,310-210*exp(-(j+1)*h),570/N,210*exp(-(j+1)*h),'input')]
   path='M '+' L '.join(f'{65+570*j/100:.2f},{310-210*exp(-T*j/100):.2f}' for j in range(101));nodes+=[dict(id='curve',type='path',d=path,fill='none',role='active'),txt('bounds',360,355,f'Approx. bounds: {floor((lo+tail-1e-12)*1e5)/1e5:.5f} to {ceil((hi+tail+1e-12)*1e5)/1e5:.5f}'),txt('tail',360,392,f'Tail beyond {T}: exp(−{T}) ≈ {tail:.6f}',size=15)]
   S.append(state(N,f'{N} rectangles bracket the finite integral.',r'\Gamma(1)=\int_0^\infty e^{-t}\,dt=1',nodes,'Right rectangles ≤ integral ≤ left rectangles; the tail is added to both bounds.',dict(T=T,N=N,lower=lo+tail,upper=hi+tail,tail=tail,roundoffAllowance=1e-12)))
 elif order==36:
  x=3 if small else 5;k=3
  for upto in range(1,k+1):
   nodes=[txt('a',360,45,'ordinary: same factor'),txt('b',360,175,'falling: decrease the factor'),txt('c',360,305,'rising: increase the factor')]
   for j in range(k):
    for row,v in enumerate((x,x-j,x+j)):nodes+=tile(f'factor-{row}-{j}',115+j*150,70+row*130,v,'active' if j<upto else 'muted',85)
   S.append(state(upto,f'Multiply the first {upto} factors in each row.',fr'{x}^{{{upto}}}={x**upto},\quad {x}^{{\underline{{{upto}}}}}={falling(x,upto)},\quad {x}^{{\overline{{{upto}}}}}={rising(x,upto)}',nodes,'Factor position j determines x, x−j, or x+j.',dict(x=x,k=upto,ordinary=x**upto,falling=falling(x,upto),rising=rising(x,upto))))
 elif order==37:
  n=3 if small else 5;k=2;labels='ABCDE'[:n];subsets=list(combinations(labels,k));marked=labels[-1];excluded=[x for x in subsets if marked not in x];included=[x for x in subsets if marked in x]
  for stage in range(5):
   nodes=[txt('head',360,35,['List all ordered two-member choices.','Group the two orders of each fixed subset.','Forget order: each two-card group becomes one subset.','Split by whether the marked member is present.','Add the disjoint excluding and including families.'][stage],size=16)]
   for z,subset in enumerate(subsets):
    for order,word in enumerate(permutations(subset)):
     if stage==0:x=50+((2*z+order)%5)*132;y=85+((2*z+order)//5)*65
     else:x=50+(z%5)*132+order*54;y=95+(z//5)*105
     for node in tile('ordered-'+''.join(word),x,y,''.join(word),'input',50 if stage else 115,40):node['opacity']=1 if stage<2 else 0;nodes.append(node)
    groupx=45+(z%5)*132;groupy=90+(z//5)*105
    nodes.append(rect('fiber-'+''.join(subset),groupx,groupy,115,52,'active',fill='none',opacity=1 if stage==1 else 0))
    family=included if marked in subset else excluded
    if stage>=3:x=45+family.index(subset)*105;y=235 if marked in subset else 115
    else:x=55+(z%5)*132;y=100+(z//5)*105
    for node in tile('subset-'+''.join(subset),x,y,'{'+''.join(subset)+'}','active' if marked in subset else 'input',90,42):node['opacity']=1 if stage>=2 else 0;nodes.append(node)
   if stage>=3:
    nodes += [txt('exclude',360,90,f'Exclude {marked}: choose 2 from the other {n-1} → {len(excluded)}',size=16),txt('include',360,210,f'Include {marked}: choose 1 more from the other {n-1} → {len(included)}',size=16)]
   nodes.append(txt('rule',360,350,(f'Every subset has 2! = 2 orders: {n*(n-1)} / 2 = {len(subsets)}.' if stage<3 else f'C({n-1},2) + C({n-1},1) = {len(excluded)} + {len(included)} = {len(subsets)}'), 'result',17))
   if stage==4:nodes += [*tile('exclude-parent',90,365,f'C({n-1},2)={len(excluded)}','input',145,34),*tile('include-parent',485,365,f'C({n-1},1)={len(included)}','active',145,34),dict(**line('exclude-to-sum',235,380,315,395,'input'),arrow=True),dict(**line('include-to-sum',485,380,405,395,'active'),arrow=True),txt('child',360,415,f'C({n},2) = {len(subsets)}','result',19)]
   formula=fr'\binom{{{n}}}2=\frac{{{n}\cdot {n-1}}}{{2!}}={len(subsets)}' if stage<3 else fr'\binom{{{n}}}2=\binom{{{n-1}}}2+\binom{{{n-1}}}1={len(excluded)}+{len(included)}'
   S.append(state(stage,nodes[0]['text'],formula,nodes,'Each unordered subset has exactly two orderings; the marked member partitions subsets into two disjoint families.',dict(n=n,k=k,stage=stage,row=[comb(n,j) for j in range(n+1)],subsets=[list(x) for x in subsets],ordered=[list(x) for x in permutations(labels,k)],marked=marked,excluded=[list(x) for x in excluded],included=[list(x) for x in included])))
 elif order==38:
  n=2 if small else 3;words=list(product('ab',repeat=n))
  for stage in range(3):
   nodes=[txt('head',360,50,'One choice from every factor')]
   for i,word in enumerate(words):
    k=word.count('b'); peers=[w for w in words if w.count('b')==k];idx=peers.index(word)
    x=65+(i%4)*165 if stage==0 else 45+k*165;y=100+(i//4)*95 if stage==0 else 100+idx*75
    nodes+=tile(f'word-{i}',x,y,''.join(word),'active' if stage==1 else 'result' if stage==2 else 'input',100,45)
   nodes+=[txt('counts',360,395,'Coefficients: '+', '.join(str(comb(n,k)) for k in range(n+1)))]
   S.append(state(stage,['Expand into individual choice words.','Group words by how many b choices they contain.','Each group contributes one binomial coefficient.'][stage],fr'(a+b)^{{{n}}}=\sum_{{k=0}}^{{{n}}}\binom{{{n}}}k a^{{{n}-k}}b^k',nodes,'A choice word appears exactly once; commutativity allows grouping.',dict(n=n,counts=[sum(w.count('b')==k for w in words) for k in range(n+1)])))
 elif order==39:
  r=2 if small else 4;k=3
  for stage in range(3):
   vals=[-r-j for j in range(k)] if stage==0 else [r+j for j in range(k)];nodes=[txt('head',360,60,'Pull one minus sign out of every factor')]
   for j,v in enumerate(vals):nodes+=tile(f'factor{j}',125+j*155,145,v,'active' if stage else 'input',90)
   nodes+=[txt('sign',360,255,f'Outside sign: {(-1)**k if stage else 1}'),txt('denom',360,315,f'Divide by {k}! = {factorial(k)}'),txt('result',360,380,f'Coefficient = {choose(-r,k)}','result')]
   S.append(state(stage,['Use the polynomial definition at a negative upper index.','Extract k minus signs, retaining their product.','Reverse the positive factors to recognize a binomial coefficient.'][stage],fr'\binom{{-{r}}}{{{k}}}=(-1)^{{{k}}}\binom{{{r+k-1}}}{{{k}}}={choose(-r,k)}',nodes,'No negative-integer factorial is introduced.',dict(r=r,k=k,value=str(choose(-r,k)))))
 elif order==40:
  r,s,n=(2,2,2) if small else (3,4,3);A='ABC'[:r];B='abcd'[:s]
  cases=[[(aa,bb) for aa in combinations(A,k) for bb in combinations(B,n-k)] for k in range(n+1)]
  terms=list(map(len,cases));allpairs=[(k,aa,bb) for k,case in enumerate(cases) for aa,bb in case]
  for frame in range(2*(n+1)+1):
   final=frame==2*(n+1);k=min(frame//2,n);assembled=frame%2==1
   ac=list(combinations(A,k));bc=list(combinations(B,n-k));nodes=[txt('head',360,35,f'Choose {n}: group A = {A}; group B = {B}',size=17)]
   if final:
    for kk,term in enumerate(terms):
     x=35+kk*170;nodes += [rect(f'case-bin{kk}',x,95,155,240,'muted',fill='none'),txt(f'case-name{kk}',x+77,78,f'k={kk}',size=16),txt(f'case-count{kk}',x+77,365,f'{term} '+('choice' if term==1 else 'choices'),'result',16)]
   else:
    nodes += [txt('A-choices',70,92,f'A: choose {k}',size=14),txt('B-choices',405,75,f'B: choose {n-k}',size=14)]
    for ii,aa in enumerate(ac):nodes.append(txt('A-choice-'+''.join(aa),70,177+ii*64,''.join(aa) or '∅',size=16))
    for jj,bb in enumerate(bc):nodes.append(txt('B-choice-'+''.join(bb),160+jj*82,120,''.join(bb) or '∅',size=16))
   for kk,aa,bb in allpairs:
    ident='choice-'+(''.join(aa) or 'empty')+'-'+(''.join(bb) or 'empty')
    if final:
     z=cases[kk].index((aa,bb));x=42+kk*170+(z%3)*48;y=110+(z//3)*35;w=43;h=28
    elif kk==k:
     x=121+bc.index(bb)*82;y=145+ac.index(aa)*64;w=78;h=48
    else:x=121;y=145;w=78;h=48
    for node in tile(ident,x,y,''.join(aa+bb),'active',w,h):
     node['opacity']=1 if final or (kk==k and assembled) else 0
     if node['type']=='text':node['fontSize']=14
     nodes.append(node)
   if final:
    formula=fr'\sum_{{k=0}}^{{{n}}}\binom{{{r}}}k\binom{{{s}}}{{{n}-k}}='+ '+'.join(map(str,terms))+fr'={sum(terms)}=\binom{{{r+s}}}{{{n}}}'
    note='Every chosen set enters exactly one bin, determined by its A count.';caption='Add the disjoint split cases after counting each Cartesian product.'
   else:
    formula=fr'k={k}:\quad\binom{{{r}}}{{{k}}}\binom{{{s}}}{{{n-k}}}={len(ac)}\cdot {len(bc)}'+(f'={terms[k]}' if assembled else '')
    note=f'{len(ac)} A choices × {len(bc)} B choices'+(f' = {terms[k]} different sets.' if assembled else '; pair each row with every column.')
    caption=f'Fix k={k}. '+('Every row-column pair is one chosen set.' if assembled else 'List the actual subsets in each group before multiplying their counts.')
   nodes.append(txt('count-note',360,413,note,size=14))
   S.append(state(frame,caption,formula,nodes,'A and B are disjoint; each subset pair determines exactly one union, and k is recoverable from that union.',dict(r=r,s=s,n=n,terms=terms,total=sum(terms),k=k,assembled=assembled,final=final,AChoices=[list(x) for x in ac],BChoices=[list(x) for x in bc],caseSets=[[''.join(aa+bb) for aa,bb in case] for case in cases])))
 elif order==41:
  degree=2 if small else 3;vals=[x**degree for x in range(5)];rows=[vals]
  while len(rows[-1])>1:rows.append([b-a for a,b in zip(rows[-1],rows[-1][1:])])
  stages=list(range(degree+4))
  if not small:stages.insert(4,3.5)
  for frame,stage in enumerate(stages):
   upto=0 if stage==0 else 1 if stage==1 else min(int(stage)-1,degree);extract=stage>=degree+2;convert=stage==degree+3
   nodes=[txt('head',360,35,f'From differences of x^{degree} to falling-factorial coefficients',size=16)]
   for row,values in enumerate(rows[:degree+1]):
    for j,v in enumerate(values):
     x=65+j*110+row*55;y=80+row*53;shown=row==0 or (row<=upto and (stage!=1 or j==1))
     for node in tile(f'd{row}-{j}',x,y,v,'active' if (stage==1 and ((row==0 and j in (1,2)) or (row==1 and j==1))) else 'input',60,38):node['opacity']=1 if shown else .08;nodes.append(node)
     if row:
      for side,px in [('left',x-25),('right',x+85)]:nodes.append(dict(**line(f'{side}{row}-{j}',px,y-15,x+30,y-3,'active'),opacity=1 if shown else 0))
   focusrow=1 if stage==1 else min(upto,degree);focusj=1 if stage in (1,3.5) else 0
   nodes.append(rect('difference-focus',60+focusj*110+(max(1,focusrow)-1)*55,75+(max(1,focusrow)-1)*53,180,101,'active',fill='none',opacity=1 if stage and not extract else 0))
   if stage and not extract:
    lhs=rows[focusrow-1][focusj+1];rhs=rows[focusrow-1][focusj];value=rows[focusrow][focusj]
    arithmetic=f'Row {focusrow}, entry {focusj}: {lhs} − {rhs} = {value}'
    formula=fr'\Delta^{{{focusrow}}}f({focusj})={lhs}-{rhs}={value}'
   elif extract:
    arithmetic='Divide each extracted difference by k! to use falling factorials.' if convert else 'Read the first entry of each row: these multiply C(x,k).'
    terms=[fr'{rows[k][0]}\binom x{{{k}}}' for k in range(degree+1)]
    formula=fr'x^{{{degree}}}='+ '+'.join(terms)
    if convert:formula=fr'x^{{{degree}}}='+ '+'.join(fr'{F(rows[k][0],factorial(k))}x^{{\underline{{{k}}}}}' for k in range(1,degree+1))
   else:arithmetic='Start with f(0), f(1), …; each new entry is right minus left.';formula=fr'f(x)=x^{{{degree}}},\quad\Delta f(x)=f(x+1)-f(x)'
   nodes.append(txt('arithmetic',360,301,arithmetic,size=14))
   for k in range(degree+1):
    x=65+k*155 if extract else 65+k*55;y=339 if extract else 80+k*53
    value=(f'{rows[k][0]}/{k}! = {F(rows[k][0],factorial(k))}' if convert else str(rows[k][0]))
    for node in tile(f'coefficient{k}',x,y,value,'active',132,42):
     node['opacity']=1 if extract else 0
     if node['type']=='text':node['fontSize']=15
     nodes.append(node)
    nodes.append(dict(**txt(f'coefficient-index{k}',x+66,326,f'k={k}',size=14),opacity=1 if extract else 0))
    nodes.append(rect(f'coefficient-magnitude{k}',x,390,100*float(F(rows[k][0],factorial(k) if convert else 1))/max(row[0] for row in rows[:degree+1]),10,'active',opacity=1 if extract else 0))
   nodes.append(txt('basis-key',360,419,'Coefficient of falling x underlined k = Δ^k f(0) / k!' if convert else ('Coefficient of C(x,k) = Δ^k f(0)' if extract else 'Use exactly the same subtraction rule in every difference row.'),size=14))
   S.append(state(frame,arithmetic,formula,nodes,'The Newton coefficient is the first entry Δ^k f(0); C(x,k)=x underlined k / k!, so division by k! changes the basis.',dict(degree=degree,rows=rows,stirling=[stirling(degree,k) for k in range(degree+1)],stage=stage,upto=upto,extracted=extract,converted=convert,newton=[rows[k][0] for k in range(degree+1)],fallingCoefficients=[str(F(rows[k][0],factorial(k))) for k in range(degree+1)])))
 elif order==42:
  n=4 if small else 8
  for upto in (1,n//2,n):
   nodes=[line('axis',70,315,665,315),txt('head',360,45,'Reciprocal rectangles: width 1, height 1/k')]
   for k in range(1,n+1):
    h=200/k;nodes+=[rect(f'bar{k}',70+(k-1)*580/n,315-h,580/n-3,h,'input' if k<=upto else 'muted'),txt(f'lab{k}',70+(k-.5)*580/n,343,k,size=14)]
   path='M '+' L '.join(f'{70+580*(x-1)/n:.2f},{315-200/x:.2f}' for x in [1+n*j/100 for j in range(101)]);nodes+=[dict(id='curve',type='path',d=path,fill='none',role='active'),txt('sum',360,392,f'H{upto} = {harmonic(upto)}')]
   S.append(state(upto,f'The first {upto} bars sum to {harmonic(upto)}.',fr'H_{{{upto}}}=\sum_{{k=1}}^{{{upto}}}\frac1k',nodes,'The decreasing curve lies below each left-endpoint rectangle.',dict(n=upto,H=str(harmonic(upto)),lower=log(upto+1),upper=1+log(upto))))
 elif order==44:
  ns=[1,2,3] if small else [3,4,5]
  for n in ns:
   vals=[fib(n+1),fib(n),fib(n),fib(n-1)];nodes=[txt('head',360,50,'One matrix step adds neighboring counts')]
   for i,v in enumerate(vals):nodes+=tile(f'm{i}',205+(i%2)*165,110+(i//2)*105,v,'active',115,70)
   nodes+=[line('diag1',250,150,440,255,'input'),line('diag2',425,150,275,255,'active'),txt('det',360,360,f'Determinant: {vals[0]*vals[3]} − {vals[1]*vals[2]} = {(-1)**n}')]
   S.append(state(n,f'Matrix power {n} carries consecutive Fibonacci numbers.',fr'Q^{{{n}}}=\begin{{pmatrix}}{vals[0]}&{vals[1]}\\{vals[2]}&{vals[3]}\end{{pmatrix}}',nodes,'det(Q^n) = (−1)^n',dict(n=n,matrix=vals,determinant=vals[0]*vals[3]-vals[1]*vals[2])))
 elif order==45:
  a,b=(6,4) if small else (15,9);target=gcd(fib(a),fib(b));k=0
  while True:
   nodes=[txt('head',360,45,'Euclid acts on indices; the value gcd stays fixed'),txt('indices',120,105,'indices'),txt('values',120,240,'Fibonacci values')]
   for j,v in enumerate((a,b)):
    nodes+=tile(f'index{j}',240+j*210,75,v,'active',140,60);nodes+=tile(f'value{j}',240+j*210,210,fib(v),'input',140,60);nodes+=[line(f'link{j}',310+j*210,143,310+j*210,200)]
   nodes+=[txt('gcd',360,355,f'gcd({fib(a)}, {fib(b)}) = {target}'),txt('step',360,400,f'Next indices: ({b}, {a%b})' if b else 'Zero index: stop')]
   S.append(state(k,f'Index pair ({a},{b}) preserves the same value gcd.',fr'\gcd(F_{{{a}}},F_{{{b}}})={target}',nodes,'This is a gcd identity, not equality of numeric remainders.',dict(a=a,b=b,Fa=str(fib(a)),Fb=str(fib(b)),gcd=str(target))))
   if b==0:break
   a,b=b,a%b;k+=1
 elif order==46:
  ns=[1,2,3] if small else [4,5,6];phi=(1+sqrt(5))/2;psi=(1-sqrt(5))/2
  for n in ns:
   lead=phi**n/sqrt(5);correction=-psi**n/sqrt(5);target=fib(n);scale=150;center=360
   nodes=[line('axis',60,230,660,230),line('exact',center,140,center,285,'result'),txt('exact-label',center,120,f'Exact integer F{n} = {target}'),dot('lead',center+(lead-target)*scale,230),line('correction',center+(lead-target)*scale,230,center,230,'active'),txt('lead-label',360,335,f'φ^{n}/√5 ≈ {lead:.6f}'),txt('correction-label',360,385,f'Correction −ψ^{n}/√5 ≈ {correction:+.6f}')]
   S.append(state(n,f'The small second-root contribution restores the integer.',fr'F_{{{n}}}=\frac{{\phi^{{{n}}}-\psi^{{{n}}}}}{{\sqrt5}}={target}',nodes,'Geometry uses rounded floats; F_n is computed with integer recurrence.',dict(n=n,exact=str(target),leadingApprox=lead,correctionApprox=correction,errorBound=abs(psi)**n/sqrt(5))))
 else:raise ValueError(order)
 return S

PLAN={21: {'id': 'a-computation-is-a-complete-snapshot', 'title': 'A computation is a complete snapshot', 'section': '1.1 Algorithms'}, 22: {'id': 'rules-a-machine-can-actually-carry-out', 'title': 'Rules a machine can actually carry out', 'section': '1.1 Algorithms'}, 23: {'id': 'strong-induction-and-the-first-failure', 'title': 'Strong induction and the first failure', 'section': '1.2.1 Mathematical Induction'}, 24: {'id': 'real-numbers-and-two-dimensional-numbers', 'title': 'Real numbers and two-dimensional numbers', 'section': '1.2.2 Numbers, Powers, and Logarithms'}, 25: {'id': 'distribute-and-change-the-order-of-a-sum', 'title': 'Distribute and change the order of a sum', 'section': '1.2.3 Sums and Products'}, 26: {'id': 'turn-a-condition-into-a-number', 'title': 'Turn a condition into a number', 'section': '1.2.3 Sums and Products'}, 27: {'id': 'cancel-along-a-chain', 'title': 'Cancel along a chain', 'section': '1.2.3 Sums and Products'}, 28: {'id': 'multiply-a-whole-family-of-terms', 'title': 'Multiply a whole family of terms', 'section': '1.2.3 Sums and Products'}, 29: {'id': 'when-an-infinite-sum-has-a-value', 'title': 'When an infinite sum has a value', 'section': '1.2.3 Sums and Products'}, 30: {'id': 'floors-ceilings-and-fractional-parts', 'title': 'Floors ceilings and fractional parts', 'section': '1.2.4 Integer Functions and Elementary Number Theory'}, 31: {'id': 'remainders-and-congruence-classes', 'title': 'Remainders and congruence classes', 'section': '1.2.4 Integer Functions and Elementary Number Theory'}, 32: {'id': 'why-prime-moduli-rearrange-residues', 'title': 'Why prime moduli rearrange residues', 'section': '1.2.4 Integer Functions and Elementary Number Theory'}, 33: {'id': 'count-arrangements-without-listing-them-all', 'title': 'Count arrangements without listing them all', 'section': '1.2.5 Permutations and Factorials'}, 34: {'id': 'how-large-is-a-factorial', 'title': 'How large is a factorial', 'section': '1.2.5 Permutations and Factorials'}, 35: {'id': 'extend-factorials-carefully', 'title': 'Extend factorials carefully', 'section': '1.2.5 Permutations and Factorials'}, 36: {'id': 'falling-and-rising-factorial-powers', 'title': 'Falling and rising factorial powers', 'section': '1.2.5 Permutations and Factorials'}, 37: {'id': 'choose-groups-and-grow-pascal-s-triangle', 'title': "Choose groups and grow Pascal's triangle", 'section': '1.2.6 Binomial Coefficients'}, 38: {'id': 'expand-a-power-by-tracking-choices', 'title': 'Expand a power by tracking choices', 'section': '1.2.6 Binomial Coefficients'}, 39: {'id': 'transform-binomial-coefficients-safely', 'title': 'Transform binomial coefficients safely', 'section': '1.2.6 Binomial Coefficients'}, 40: {'id': 'count-the-same-choice-in-two-stages', 'title': 'Count the same choice in two stages', 'section': '1.2.6 Binomial Coefficients'}, 41: {'id': 'change-from-powers-to-factorial-powers', 'title': 'Change from powers to factorial powers', 'section': '1.2.6 Binomial Coefficients'}, 42: {'id': 'watch-harmonic-sums-grow-slowly', 'title': 'Watch harmonic sums grow slowly', 'section': '1.2.7 Harmonic Numbers'}, 43: {'id': 'rearrange-harmonic-sums', 'title': 'Rearrange harmonic sums', 'section': '1.2.7 Harmonic Numbers'}, 44: {'id': 'fibonacci-identities-from-local-moves', 'title': 'Fibonacci identities from local moves', 'section': '1.2.8 Fibonacci Numbers'}, 45: {'id': 'fibonacci-divisibility-follows-euclid', 'title': 'Fibonacci divisibility follows Euclid', 'section': '1.2.8 Fibonacci Numbers'}, 46: {'id': 'recover-fibonacci-values-from-roots', 'title': 'Recover Fibonacci values from roots', 'section': '1.2.8 Fibonacci Numbers'}}
# All teaching prose and assessments below are original to this companion.
CONTENT={}
def lesson(n,pages,passages,check,helpcheck,helpintro,limits=''):
 CONTENT[n]=dict(pages=pages,passages=passages,check=check,helpcheck=helpcheck,helpintro=helpintro,limits=limits)
def p(title,text,formula=''):return dict(title=title,text=text,formula=formula)
def q(prompt,choices,index,why):return dict(prompt=prompt,choices=choices,correctIndex=index,explanation=why)
lesson(21,'39–40',[
p('What must a snapshot remember?', 'Earlier lessons used Euclid to watch numbers change. Now ask a deeper question: do the visible numbers determine the next action? A parcel robot with three waiting parcels may be about to test the tray or about to move a parcel. These are different states, even though the tray looks identical.\n\nOur state is (n, c, o): n is the nonnegative number waiting, c is CHECK, MOVE, or DONE, and o is the number already delivered. CHECK changes only the control badge. MOVE transfers one parcel and returns to CHECK. DONE changes nothing. Output history belongs in the state if a later observer can distinguish it. Omitting o would lose information about what this machine has already reported.',r'q=(n,c,o),\quad n,o\in\mathbb N_0'),
p('Specify a whole computational method', 'Let Q contain all triples just described, not only the triples visited in this example. Let I = {(n,CHECK,0): n ≥ 0} be the allowed initial states. Let Ω contain every triple with badge DONE. Define f on every member of Q: CHECK tests whether n is zero; MOVE with n>0 changes (n,MOVE,o) to (n−1,CHECK,o+1); MOVE with n=0 changes its badge to DONE; DONE is fixed. This otherwise branch matters: f must be total even on a state that ordinary runs never visit.\n\nFor input x∈I, define x₀=x and xₖ₊₁=f(xₖ). Termination means that some finite xₖ lies in Ω. It does not mean that a simulation merely exhausted its frame budget.',r'f:Q\to Q,\qquad f(q)=q\ (q\in\Omega)'),
p('Prove termination, not just one successful run', 'For every active snapshot use the nonnegative rank R(n,CHECK,o)=2n+1 and R(n,MOVE,o)=2n. Every transition that stays active strictly decreases R. A transition from CHECK with n=0 enters DONE; the otherwise MOVE case also enters DONE. There cannot be infinitely many strict decreases of a nonnegative integer. Thus every allowed input terminates. From (n,CHECK,0), the machine takes exactly 2n+1 transitions to DONE, including the final empty-tray test.\n\nThe invariant n+o=N, where N is the original input size, is preserved during these runs. At termination n=0, so o=N. Termination and output correctness are separate conclusions.',r'R_{k+1}<R_k\quad\text{while both states are active}'),
p('One run cannot certify every input', 'Change CHECK so that an odd positive n returns to itself forever. The empty input and every even input might still have a successful run after further changes, but that evidence would not establish an algorithm on all nonnegative inputs. A computational method can contain nonterminating computations; an algorithm must terminate for every input in its declared domain.\n\nThe empty input is not an error: it takes one CHECK→DONE transition. Two DONE states with different output histories are both fixed yet observably distinct. The complete-state requirement and the universal quantifier over inputs are the new ideas beyond the earlier Euclidean trace.',r'\forall x\in I\ \exists k\ge0:\ f^k(x)\in\Omega')],
q('A machine stores only (waiting, badge), but emits a receipt number after every move. What must be established before this is a complete state?', ['That all trays have the same size','That omitted receipt history cannot affect future behavior or observable output','That one input terminates'],1,'A complete snapshot must determine the future relevant to the specification. Observable receipt history must be represented, or its irrelevance must be justified.'),
q('With one waiting parcel, how many transitions reach DONE from CHECK?', ['1','2','3'],2,'CHECK→MOVE, MOVE→CHECK with zero waiting, CHECK→DONE. The last test is an actual transition.'),'Use one parcel and watch only the badge or parcel change on each beat.')
lesson(22,'40–41',[
p('Put control beside the word', 'A word alone need not identify a computation. Our snapshot is (σ,j): σ is a finite word over the finite alphabet {a,b}, and j is a rule number. Rule 0 searches left to right for the first adjacent ab. If found, it replaces that occurrence by ba and stays at rule 0. If absent, it leaves the word unchanged and enters terminal rule 1. Rule 1 is fixed.\n\nIn aabb, the first ab begins at position 1 when positions start at zero. Replacing it produces abab. Both the word and the control number are part of the new snapshot; they are updated as one mathematical step.',r'(\sigma,j)\in\{a,b\}^{*}\times\{0,1\}'),
p('Make every primitive instruction effective', 'More generally, a rule has a pattern θ, replacement φ, no-match destination a, and match destination b. If σ=uθv and u is the shortest possible prefix, the successor word is uφv and the new control is b. If no occurrence exists, retain σ and branch to a. Every word and rule table is finite. Scanning, comparing symbols, and replacing a finite substring are operations that can be carried out mechanically.\n\nWe permit an empty pattern explicitly: its first occurrence is at offset zero, so it inserts the replacement before the word. Without that policy “find a match” would be ambiguous. A terminal control number leaves the complete state unchanged.',r'f(\sigma,j)=(u\phi_jv,b_j)\quad\text{at the first match}'),
p('Effectiveness does not supply termination', 'For this ab→ba system, count pairs of positions r<s with σᵣ=a and σₛ=b. Swapping one adjacent ab to ba removes exactly that pair; its relations to every other letter are unchanged. The nonnegative pair count therefore decreases by one per successful rewrite. Once no ab remains, one final failed search halts. This proves termination for every finite input word.\n\nNow replace a by aa and return to the same rule. Every step is equally effective, but input a grows forever. Finite instructions, deterministic instructions, and terminating instructions are different properties.',r'V(\sigma)=\#\{(r,s):r<s,\sigma_r=a,\sigma_s=b\}'),
p('Encoding is a promise you must keep', 'A finite alphabet can encode numbers, lists, and control positions, but a proposed encoding must say which strings are legal and how each primitive operation changes them. Arbitrary real numbers cannot all be represented by finite strings, because there are only countably many such strings. An instruction like “replace the word by the answer to any undecidable question” is not made effective merely by naming it.\n\nTry tracing baab: the first change is baba, not bbaa. Choosing a later match would define a different transition rule even if it eventually produced the same terminal word.',r'\text{finite description}\ne\text{proof of universal termination}')],
q('Rule: replace the first aa by b and go to rule 4; otherwise go to rule 7. From (aaaa,2), what is the successor?', ['(bba,4)','(aab,4)','(baa,4)'],2,'Only the first occurrence is replaced: empty prefix + b + aa = baa. Replacement and control update happen together.'),
q('What happens to (ba,0) in the smaller ab→ba machine?', ['The word stays ba and control becomes 1','The word becomes ab','The machine is already terminal before taking a step'],0,'There is no ab. The failed search is a transition to terminal control 1; the word is retained.'),'Start with only ab. One swap changes the word; one failed search then changes the badge.')
lesson(23,'44–54',[
p('Let a new case use several earlier cases', 'Consider the claim P(n): every integer n≥2 can be written as a product of primes. A prime n is already a product with one factor. A composite n can be split as n=ab with 2≤a,b<n. The proof for n may need both P(a) and P(b), rather than only P(n−1). The dependency picture shows these strictly smaller supports.\n\nFor instance, 12 can use 3 and 4, while 4 uses 2 twice. A repeated factor is allowed. The finite picture illustrates the proof pattern; the statement concerns every integer at least 2.',r'P(n):\ n=p_1p_2\cdots p_t\quad\text{with each }p_i\text{ prime}'),
p('State the induction hypothesis at its full strength', 'Strong induction from base b says: if P(b) holds, and for every n>b the truth of all P(k) with b≤k<n implies P(n), then P(n) holds for every n≥b. The hypothesis is not a license to assume the conclusion P(n). In the prime-factorization example b=2. The prime case needs no earlier hypothesis. In the composite case both factors are smaller, so their prime products may be concatenated.\n\nThis proves existence of a factorization, not its uniqueness. Uniqueness requires additional number-theoretic reasoning and does not follow from the dependency graph.',r'\bigl(\forall k\in\mathbb Z,\ b\le k<n\Rightarrow P(k)\bigr)\Rightarrow P(n)'),
p('The first failure would have nowhere to hide', 'Suppose a failure exists, and choose the least integer m≥2 for which P(m) is false. It cannot be prime, because then it supplies its own factorization. If m=ab is composite, both a and b lie between 2 and m−1. By minimality neither can fail. Their factorizations multiply to one for m, contradicting the choice of m.\n\nThis least-counterexample proof uses the well-ordering of nonnegative integers: every nonempty set has a least member. Ordinary induction gives the same strength by applying it to the bundled proposition Q(n)=P(2)∧P(3)∧⋯∧P(n).',r'Q(n)=\bigwedge_{k=2}^{n}P(k)'),
p('A missing base can invalidate an attractive recurrence', 'Suppose a proposed construction reduces n to n−2. One base case generally covers only one parity; the other parity needs its own base or another reduction. For example, every integer n≥8 can be formed from 3-unit and 5-unit pieces: 8=3+5, 9=3+3+3, and 10=5+5 are bases; for n≥11 reduce to n−3≥8 and append a 3-unit piece.\n\nAn animation of successful cases up to 50 is not this proof. The arbitrary n argument and the explicit bases explain why no later failure can occur.',r'n\ge11\Rightarrow n-3\ge8')],
q('To prove P(n) for all n≥4 using only P(n−3)→P(n), which starting cases suffice?', ['Only P(4)','P(4), P(5), P(6)','P(4), P(7), P(10)'],1,'Subtracting 3 preserves the residue class. Consecutive bases 4,5,6 cover all three classes; 4,7,10 cover just one.'),
q('Why may a proof about 6 use facts about 2 and 3?', ['Because they are both strictly smaller than 6 and in the proven domain','Because testing 6 proves every integer','Because 6 is assumed true'],0,'Strong induction supplies all earlier cases in the domain. It never supplies the current case.'),'Build only cases 2 through 6, and follow each composite down to its smaller factors.')
lesson(24,'59–65',[
p('An exact point need not have a finite decimal name', 'An integer, a rational number, and a real number describe progressively larger domains. A finite decimal is rational, but a real value such as √2 has no finite decimal expansion. A displayed 1.4142 is an approximation, not a new definition of √2. One exact way to specify a real value is a nested sequence of nonempty closed intervals with rational endpoints whose widths approach zero.\n\nComplex numbers add a second coordinate: z=a+bi, with real a,b and i²=−1. The scene starts with z=2+i. Adding 1+i translates it to 3+2i. Multiplying the original z by 1+i instead gives 1+3i. These are two operations on the same original point, not consecutive updates.',r'(a+bi)(c+di)=(ac-bd)+(ad+bc)i'),
p('Bind algebra to plane geometry', 'For z=a+bi, |z| means its magnitude: the distance √(a²+b²) from the origin. The bar in z̄ denotes its conjugate a−bi, and arg z names an angle from the positive real axis to a nonzero z. Addition acts coordinate by coordinate. Multiplication combines a scale and a rotation: |zw|=|z||w|, and angles add modulo 2π. Here |1+i|=√2 and its angle is π/4, so multiplying by 1+i rotates 45 degrees and stretches by √2. Conjugation changes a+bi into a−bi, reflecting across the real axis; z times its conjugate is a²+b².\n\nThe square root in |z|=√(a²+b²) means the nonnegative real square root. In particular, a complex number can have nonzero magnitude without being positive or negative; the usual ordering on real numbers does not extend to an ordered field structure on the complex plane.',r'\overline z=a-bi,\quad z\overline z=|z|^2=a^2+b^2'),
p('Powers need a declared domain', 'For a positive real base b, define bˣ=exp(x ln b) for real x. The ordinary exponent laws then hold, and logarithms base b require b≠1. Integer powers of a complex number are unambiguous; negative integer powers require a nonzero base. Fractional complex powers require a branch choice or a set of possible values.\n\nHere arg z is an angle of the nonzero point z in the complex plane. Every complex logarithm of a nonzero z has the form ln|z|+i(arg z+2πk), where k is any integer. The principal value chooses one angle interval. Once a branch is chosen, a familiar law may fail literally: principal Log(−1)+Log(−1)=2πi, whereas principal Log(1)=0.',r'\log z=\ln|z|+i(\arg z+2\pi k),\quad k\in\mathbb Z'),
p('Keep exact arithmetic separate from drawn coordinates', 'The integer-coordinate scene computes addition and multiplication exactly; its pixel coordinates are only a representation. An angle label such as 45° is exact here, while a decimal magnitude such as 1.414214 is rounded. A finite set of plotted points cannot prove identities for all complex numbers.\n\nThe multiplication formula follows by distributing four terms and replacing i² by −1. Expanding (ac−bd)²+(ad+bc)² proves |zw|²=(a²+b²)(c²+d²); taking nonnegative square roots proves the magnitude rule. This proof applies to every real a,b,c,d, including zero.',r'|zw|^2=(a^2+b^2)(c^2+d^2)')],
q('Multiplying z=3−2i by i should move it where?', ['−2+3i','2+3i','3+2i'],1,'i(3−2i)=3i−2i²=2+3i. It is a 90° counterclockwise rotation, not conjugation.'),
q('Starting from 1+i, which operation lands at 2i?', ['Add 1+i','Take the conjugate','Multiply by 1+i'],2,'(1+i)²=1+2i+i²=2i, while addition gives 2+2i.'),'Use the point 1+i, so multiplication by 1+i lands directly above the origin.','General complex analysis and branch-cut continuation are reading-led; this is an introductory domain-safe model.')
lesson(25,'69–76',[
p('Each square owns one pair of indices', 'A finite double sum is best understood as a collection of labeled terms. In the triangular scene, cell (i,j) exists exactly when 1≤j≤i≤n, and carries value i+j. Summing row by row fixes i and visits j=1,…,i. Summing column by column fixes j and visits i=j,…,n. The cells do not move into a different mathematical set; only the grouping changes.\n\nFor a rectangular set of indices, multiplying two sums distributes into every pair: each aᵢ from the first sum meets each bⱼ from the second. Missing a cell would omit a product; counting it twice would change the result.',r'\left(\sum_{i=1}^{r}a_i\right)\left(\sum_{j=1}^{s}b_j\right)=\sum_{i=1}^{r}\sum_{j=1}^{s}a_ib_j'),
p('Change bounds when changing the outer index', 'The precise triangular identity is Σᵢ₌₁ⁿΣⱼ₌₁ⁱ aᵢⱼ = Σⱼ₌₁ⁿΣᵢ₌ⱼⁿ aᵢⱼ. The outer variable is a fixed parameter during the inner sum. A symbol used as a summation index is bound only inside that summation; renaming it is harmless if every occurrence and bound is renamed consistently.\n\nFor n=0 the index set is empty and both totals are zero. For n=1 both descriptions contain the single pair (1,1). The reason the formula survives these boundaries is that it describes the same index set, not that we patched the endpoints afterward.',r'\{(i,j):1\le j\le i\le n\}=\{(i,j):1\le j\le n,\ j\le i\le n\}'),
p('Prove a rearrangement by matching terms', 'Finite addition is associative and commutative, so any bijection of the finite index set preserves the sum. A proof therefore has two parts: every old pair occurs in the new description, and every new pair was legal before. In a change of variable k=n−j, reverse the endpoints as well as the summand; an increasing old index becomes a decreasing new index.\n\nThe rectangular distributive law follows by expanding one factor at a time. The triangular interchange follows from the two equivalent inequalities above. Neither proof depends on the example values i+j; they work for any real or complex aᵢⱼ.',r'\sum_{j=0}^{n}a_j=\sum_{k=0}^{n}a_{n-k}'),
p('Infinite sums require another theorem', 'Finiteness is doing real work. For infinite families, convergence of one ordering alone does not authorize arbitrary rearrangement or interchange. Absolute convergence supplies a safe hypothesis for the usual rearrangement theorem. Later lessons separate that analytic issue from this finite algebra.\n\nA common mistake is to swap the two summation signs while leaving the inner bound i untouched. That can make an index refer to itself or introduce cells above the diagonal. Before simplifying algebra, sketch the legal cells and check a corner such as (1,n).',r'\text{finite bijection first; algebra second}')],
q('Which bounds describe 0≤j≤i≤4 after j becomes the outer index?', ['0≤j≤4 and 0≤i≤j','0≤j≤4 and j≤i≤4','0≤i≤4 and j≤i≤4'],1,'For a fixed column j, legal rows run from i=j through 4. The pair set is unchanged.'),
q('In the n=3 triangle, how many cells belong to column j=2?', ['1','2','3'],1,'Its rows are i=2 and i=3; i=1 would violate j≤i.'),'Shrink the triangular board to three rows and trace one column by hand.')
lesson(26,'72;77–78',[
p('A yes-or-no statement can be a counting weight', 'For a proposition P whose truth is defined, write [P]=1 when P is true and [P]=0 when P is false. In the scene, A means “the label is even” and B means “the label is divisible by 3.” Adding [A] over labels counts A. Multiplying a defined number by [A] keeps it exactly when A is true.\n\nThe overlapping boxes are not merely categories: an object in both boxes receives two copies when [A]+[B] is used. Subtracting [A and B] removes the extra copy. Objects in neither box receive zero throughout.',r'[P]=\begin{cases}1&P\text{ true}\\0&P\text{ false}\end{cases}'),
p('Verify an identity on all truth possibilities', 'The formula [A or B]=[A]+[B]−[A and B] is a pointwise identity. For truth pairs (false,false), (true,false), (false,true), and (true,true), the right side is respectively 0,1,1,1. Summing over a finite universe gives inclusion–exclusion for two sets. Also [A and B]=[A][B], and [not A]=1−[A].\n\nFor finite U and a real-valued function w defined on U, Σₓ∈U w(x)[P(x)] equals the sum of w over the elements satisfying P. This is weighted filtering, not only counting.',r'|A\cup B|=|A|+|B|-|A\cap B|'),
p('A bracket does not repair an undefined expression', 'The tempting term [x≠0]/x is still undefined at x=0 in ordinary arithmetic: its denominator is zero before any simplification. Likewise, 0 times an undefined value is not automatically zero. Define a piecewise function instead, or restrict the summation domain to x≠0 before dividing.\n\nThis distinction is useful in code too. A short-circuit conditional that avoids evaluating an invalid expression has semantics different from blindly multiplying its value by a boolean. The mathematical specification should make the safe branch explicit.',r'g(x)=\begin{cases}1/x&x\ne0\\0&x=0\end{cases}'),
p('Count exact cases instead of hoping overlap disappears', 'Exactly one of A,B is true when [A]+[B]−2[A and B]=1. This differs from “at least one.” For three conditions, an object satisfying all three is counted three times by the individual counts, subtracted three times by pairwise intersections, and then added once by the triple intersection. Checking the weight of one object proves the general counting rule.\n\nFor labels 1 through 10, the even labels number 5, multiples of 3 number 3, and their intersection has only 6. Thus at least one condition holds for 7 labels, whereas exactly one holds for 6.',r'[A\text{ xor }B]=[A]+[B]-2[A\land B]')],
q('Among labels 1 through 12, how many are divisible by exactly one of 2 and 3?', ['8','6','10'],1,'There are 6 multiples of 2, 4 of 3, and 2 of both. Exactly one gives 6+4−2·2=6.'),
q('For label 6, what weight gives “at least one” of even or divisible by 3?', ['1+1−1=1','1+1=2','1−1=0'],0,'Both conditions hold, but the union counts the object once.'),'Use only labels 1 through 6; the overlap consists of one visible object.')
lesson(27,'73–80;146–147',[
p('Move equal pieces into alignment', 'A telescoping sum hides equal positive and negative terms at neighboring indices. For k≥1, 1/[k(k+1)]=1/k−1/(k+1). Put positive terms in one row and negative terms in another. Shift the second row by one position so equal denominators align. Every interior reciprocal cancels, leaving 1−1/(n+1).\n\nThe shift is a change of indexing, not a change of value. A minus sign belongs to the entire term. In particular, the final negative term has no partner, and dropping it would give the wrong sum.',r'\sum_{k=1}^{n}\frac1{k(k+1)}=1-\frac1{n+1}\quad(n\ge0)'),
p('Expose the endpoint formula before substituting values', 'For any sequence b₀,b₁,…,bₙ, the difference sum Σₖ₌₀ⁿ⁻¹(bₖ₊₁−bₖ)=bₙ−b₀. For n=0 it is an empty sum, hence zero, and both endpoints coincide. For one term it is simply b₁−b₀. These checks prevent off-by-one formulas.\n\nTo obtain the reciprocal example, choose bₖ=−1/(k+1). Then bₖ₊₁−bₖ=1/[(k+1)(k+2)] and shift the summation index. Alternatively use positive reciprocals and reverse the sign of the difference.',r'\sum_{k=0}^{n-1}\Delta b_k=b_n-b_0,\quad\Delta b_k=b_{k+1}-b_k'),
p('Weights leave a correction: summation by parts', 'The forward differences are Δbₖ=bₖ₊₁−bₖ and Δaₖ=aₖ₊₁−aₖ: each is the next value minus the current one. Expand aₖ₊₁bₖ₊₁−aₖbₖ as aₖ(bₖ₊₁−bₖ)+bₖ₊₁(aₖ₊₁−aₖ). Summing this identity telescopes the left side. Moving the second sum to the other side gives a discrete analogue of integration by parts. It is valid for any finite real or complex sequences with all indicated indices defined.\n\nThe shifted bₖ₊₁ in the correction is essential. With aₖ=k and bₖ=k, the left side is Σₖ₌₀ⁿ⁻¹ k=n(n−1)/2; the endpoint expression n²−Σₖ₌₀ⁿ⁻¹(k+1) gives the same value.',r'\sum_{k=0}^{n-1}a_k\Delta b_k=a_nb_n-a_0b_0-\sum_{k=0}^{n-1}b_{k+1}\Delta a_k'),
p('Use the proof to choose what to telescope', 'When a term contains a difference, first ask which neighboring values created it. When it contains a weight times a difference, try summation by parts so that the new difference of the weight is simpler. Constant weights disappear from the correction; linear weights become constants.\n\nNo convergence assumption is needed for these finite identities. Passing to an infinite endpoint requires a separate limit argument. The diagram proves neither that every sum telescopes nor that an infinite terminal term can be silently discarded.',r'\Delta(c)=0,\qquad\Delta(k)=1')],
q('For n≥1, what is Σ from k=1 to n of 1/[(k+2)(k+3)]?', ['1−1/(n+1)','1/3−1/(n+3)','1/2−1/(n+2)'],1,'The terms are 1/(k+2)−1/(k+3); the first positive is 1/3 and the last negative is −1/(n+3).'),
q('For three terms 1/2+1/6+1/12, what survives cancellation?', ['1−1/4','1−1/3','1/4'],0,'Write the terms as 1−1/2, 1/2−1/3, and 1/3−1/4. The sum is 3/4.'),'Keep just three adjacent differences, so both uncancelled endpoints fit in one glance.')
lesson(28,'76–80',[
p('A product visits factors, not terms to add', 'The notation ∏ₖ₌₁ⁿ aₖ means multiply the n listed factors. It obeys a recursion P₀=1 and Pₙ=Pₙ₋₁aₙ. The empty product is 1 because multiplying by it must leave another product unchanged. By contrast, the empty sum is 0.\n\nIn the scene, factor k is (k+1)/k. The numerator of one factor matches the denominator of the next, so all interior factors cancel. For n≥1 the answer is n+1. For n=0 the product is empty and the same formula gives 1.',r'\prod_{k=1}^{n}\frac{k+1}{k}=n+1'),
p('Cancellation has a nonzero contract', 'More generally, if b₀,…,bₙ are all nonzero, then ∏ₖ₌₁ⁿ(bₖ/bₖ₋₁)=bₙ/b₀. Each denominator cancels a matching numerator. The formula can sometimes be extended after algebraic simplification, but the original quotient expression is undefined when a denominator vanishes.\n\nA zero factor makes a defined product zero. An even number of negative factors gives a positive product; an odd number gives a negative product. Neither observation changes the empty-product convention.',r'\prod_{k=1}^{n}\frac{b_k}{b_{k-1}}=\frac{b_n}{b_0}\quad(b_j\ne0)'),
p('Separate laws that look alike', 'For finite scalar products, ∏(aₖbₖ)=(∏aₖ)(∏bₖ), because multiplication is associative and commutative. But ∏(aₖ+bₖ) is generally not ∏aₖ+∏bₖ. Expanding the product requires one choice from every pair and includes all mixed choices. In the formula, S is the subset of positions where we choose aₖ; positions outside S choose bₖ. The sum over S visits every such subset once. Already (a+b)(c+d)=ac+ad+bc+bd.\n\nA product of matrices cannot be freely reordered, even though parentheses can be changed. State the domain before importing a scalar identity into another algebraic setting.',r'\prod_{k=1}^{n}(a_k+b_k)=\sum_{S\subseteq\{1,\ldots,n\}}\prod_{k\in S}a_k\prod_{k\notin S}b_k'),
p('Count the factors before you simplify', 'The integer interval m≤k≤n contains n−m+1 indices when m≤n, and none when m>n. Thus a constant product over m≤k≤n equals c to that number of factors; the empty case uses c⁰=1 by the product convention, including when c=0 in this combinatorial setting. This convention should not be confused with an indeterminate analytic limit.\n\nTaking logarithms is safe for positive real factors and converts products to sums. With negative or complex factors, branch choices prevent an unrestricted logarithm law. A direct product proof avoids that issue.',r'\ln\left(\prod_{k=1}^{n}a_k\right)=\sum_{k=1}^{n}\ln a_k\quad(a_k>0)')],
q('What is the defined product ∏ from k=2 to 5 of (k+2)/(k+1)?', ['7/3','6/2','7'],0,'The factors are 4/3,5/4,6/5,7/6. Only 7 in the numerator and 3 in the denominator remain.'),
q('If there are no factors at all, which value keeps Pₙ=Pₙ₋₁aₙ valid at n=1?', ['0','1','Undefined'],1,'P₁=a₁ must equal P₀a₁ for every a₁, so the neutral starting value is 1.'),'Use three ratios, 2/1, 3/2, 4/3, and pair equal nonzero factors.')
lesson(29,'69–72;144–146',[
p('An infinite sum is a limit of finite sums', 'For a real sequence a₁,a₂,…, define the partial sum Sₙ=Σₖ₌₁ⁿaₖ. The infinite series has value S when, for every ε>0, some N makes |Sₙ−S|<ε for all n≥N. The picture shows finite partial sums of 1/2+1/4+1/8+⋯. After n terms the unfilled length is exactly 2⁻ⁿ.\n\nThis is more than a pleasing plot: given ε, choose N with 2⁻ᴺ<ε. Every later gap is smaller. A controlled tail converts the finite calculation into a proof of convergence.',r'S_n=1-2^{-n},\qquad |1-S_n|=2^{-n}'),
p('A term approaching zero is necessary, not sufficient', 'If Sₙ converges, then aₙ=Sₙ−Sₙ₋₁ approaches zero. The converse is false. The harmonic terms 1/n approach zero, but grouping indices 2ʲ<k≤2ʲ⁺¹ gives 2ʲ terms each at least 1/2ʲ⁺¹. Each group adds at least 1/2, so the partial sums exceed every fixed bound.\n\nFor a geometric series Σₖ₌₀∞rᵏ, the finite identity Sₙ=(1−rⁿ⁺¹)/(1−r) leads to convergence only when |r|<1. At r=1 the sums grow; at r=−1 they oscillate. A finite formula does not itself authorize a limit.',r'\sum_{k=0}^{\infty}r^k=\frac1{1-r}\quad(|r|<1)'),
p('Absolute convergence protects rearrangements', 'A series is absolutely convergent if Σ|aₖ| converges. It is conditionally convergent if Σaₖ converges but Σ|aₖ| does not. For example, the alternating harmonic series converges: consecutive pairs are positive, the even partial sums increase, the odd partial sums decrease, and their gap tends to zero. Its tail after n terms has magnitude at most 1/(n+1). Its absolute-value series is harmonic and diverges.\n\nAbsolute convergence permits arbitrary permutations without changing the sum. Conditional convergence does not: taking positive terms until a target is exceeded, then negative terms until it is crossed downward, can produce a different limit.',r'\sum |a_k|<\infty\Rightarrow\text{every rearrangement has the same sum}'),
p('A stopping rule needs a bound, not a flat-looking curve', 'To approximate a convergent sum within 1/1000, choose a truncation from a proven tail estimate. For the picture’s geometric sum, n=10 suffices because 2⁻¹⁰=1/1024<1/1000. Merely observing that consecutive screen values round to the same decimal says little about the remaining tail.\n\nThe displayed model is exact for its finite rational sums. It does not claim to compute infinitely many additions or to prove convergence from a finite number of trials. The epsilon argument, not the animation, is the proof.',r'\text{displayed finite data}+\text{proved tail bound}\Rightarrow\text{certified accuracy}')],
q('For Σ from k=1 to infinity of 3⁻ᵏ, the tail after n terms is 1/(2·3ⁿ). What is the least n ensuring tail <1/100?', ['3','4','5'],1,'At n=3 the tail is 1/54, too large. At n=4 it is 1/162<1/100.'),
q('After three terms of 1/2+1/4+⋯, what remains before reaching 1?', ['1/16','1/8','0'],1,'The exact partial sum is 7/8. Infinitely many future terms together have total 1/8.'),'Use a single unit bar and fill only its first three geometric pieces.')
lesson(30,'87–89',[
p('Find the two neighboring integer fences', 'For a real x, floor(x) is the greatest integer not exceeding x, and ceiling(x) is the least integer not smaller than x. On a number line, floor is the fence at or to the left; ceiling is the fence at or to the right. At an integer the two fences coincide.\n\nFor −7/3, the floor is −3 and the ceiling is −2. Truncation toward zero would give −2, so it is not floor. The fractional part {x}=x−floor(x) is 2/3, a nonnegative distance from the left fence, even though x is negative.',r'\lfloor x\rfloor\le x<\lfloor x\rfloor+1,\qquad\lceil x\rceil-1<x\le\lceil x\rceil'),
p('Use integer quantifiers to turn pictures into implications', 'For any integer m, floor(x)≥m if and only if x≥m. Also floor(x)<m if and only if x<m. These follow from the interval containing x and the fact that no integer lies strictly between consecutive integers. For ceiling, ceiling(x)≤m if and only if x≤m, and ceiling(x)>m if and only if x>m.\n\nThe qualification “m is an integer” is essential. For x=1.8 and m=1.5, x≥m is true while floor(x)≥m is false. Inequalities must not lose that domain condition.',r'm\in\mathbb Z:\quad\lfloor x\rfloor<m\iff x<m'),
p('Translate and reflect the integer grid', 'Adding an integer m translates all fences, so floor(x+m)=floor(x)+m. Reflecting the line reverses order, giving floor(−x)=−ceiling(x). If x is not an integer, ceiling(x)=floor(x)+1; at an integer they are equal instead.\n\nWrite x=a+u and y=b+v, where a,b are integers and 0≤u,v<1. Then floor(x+y)=a+b+floor(u+v). The final floor is either 0 or 1: the extra unit is a carry created by the fractional parts. This proves a useful bound without guessing from examples.',r'\lfloor x\rfloor+\lfloor y\rfloor\le\lfloor x+y\rfloor\le\lfloor x\rfloor+\lfloor y\rfloor+1'),
p('Equality at a fence changes the answer', 'A floor interval includes its left endpoint and excludes its right endpoint. A ceiling interval does the reverse. Replacing a strict inequality by a non-strict one at an endpoint can add an entire unwanted integer case. Test x=0, a negative integer, and values just to either side of an integer.\n\nFor n≥0 objects packed at most d per box with positive integer d, the minimum box count is ceiling(n/d). It is zero for n=0. The equivalent expression floor((n−1)/d)+1 also works at n=0: floor(−1/d)=−1. Replacing floor by truncation toward zero would break that empty-input case when d>1.',r'\{x\}=x-\lfloor x\rfloor\in[0,1)')],
q('What are floor(−11/4), ceiling(−11/4), and its fractional part?', ['−2, −3, −3/4','−3, −2, 1/4','−3, −2, 3/4'],1,'−11/4=−3+1/4 lies one quarter to the right of −3.'),
q('At x=0, which statement is correct?', ['floor=−1, ceiling=0','floor=0, ceiling=1','floor=ceiling=0'],2,'The integer point itself is both the greatest integer below and the least integer above it.'),'Use only −1/2, 0, and 1/2 so the change at zero is unmistakable.')
lesson(31,'88–90',[
p('A remainder is a representative; congruence is a relation', 'For integer a and positive integer m, define a mod m = a−m floor(a/m). It is the unique remainder r with 0≤r<m for which a=qm+r with integer q. For example, −8=−2·5+2, so −8 mod 5=2. A programming language that truncates division toward zero may return a different signed remainder.\n\nThe relation a≡b (mod m) means that m divides a−b. It is equivalent to the equality of their chosen remainders, but it is a statement about a pair of numbers, not a number-valued operation.',r'a=qm+r,\quad q=\lfloor a/m\rfloor,\quad0\le r<m'),
p('Multiplication maps residue classes to residue classes', 'If a≡b and c≡d modulo m, then a+c≡b+d and ac≡bd. The proof writes a=b+um and c=d+vm and expands; every difference is a multiple of m. Thus modular arithmetic can reduce intermediate sums and products without changing the final residue.\n\nThe scene multiplies every residue by a fixed multiplier. It is a permutation exactly when that multiplier is relatively prime to m. When gcd(a,m)=1, Bézout gives integers u,v with ua+vm=1, so u is a multiplicative inverse of a modulo m.',r'\gcd(a,m)=1\Rightarrow\exists u:\ ua\equiv1\pmod m'),
p('Cancellation needs the right modulus', 'From ax≡ay modulo m, division by a is valid modulo m only when gcd(a,m)=1. In general let d=gcd(a,m); then m divides a(x−y) exactly when m/d divides x−y. The valid reduced conclusion is x≡y modulo m/d.\n\nFor 2x≡2y modulo 6, x=1 and y=4 are a counterexample to cancellation modulo 6: both products have remainder 2, yet the original residues differ. They do agree modulo 3, as the general rule predicts.',r'ax\equiv ay\pmod m\iff x\equiv y\pmod{m/\gcd(a,m)}'),
p('The source’s real remainder extension has different bounds', 'The source also defines x mod y=x−y floor(x/y) for real x and nonzero real y. When y>0 the result lies in [0,y); when y<0 it lies in (y,0]. Its separate convention at y=0 is x mod 0=x. The runtime here uses positive integer moduli only; the real extension should not be confused with integer divisibility.\n\nModulo 1, every integer remainder is zero and all integers are congruent. Modular inverses in the usual nontrivial residue system are discussed for m≥2. Never infer that dividing a congruence is harmless because adding and multiplying are harmless.',r'y<0\Rightarrow y<x\bmod y\le0')],
q('Which quotient and remainder express −13=q·5+r with 0≤r<5?', ['q=−2, r=−3','q=−3, r=2','q=−3, r=−2'],1,'Floor(−13/5)=−3, so the whole blocks stop at −15; moving right by 2 reaches −13.'),
q('What is −1 mod 5 using the positive-modulus definition?', ['−1','0','4'],2,'−1=(−1)·5+4 and 0≤4<5.'),'First divide 7 by 3, then −5 by 3 on the same number line. Whole blocks reach q·3; a rightward offset gives the remainder.')
lesson(32,'89–90',[
p('A prime prevents nonzero collisions', 'Let p be prime and let a be an integer not divisible by p. If ax≡ay modulo p, then p divides a(x−y). Because p does not divide a, it divides x−y. Thus multiplying the nonzero residues 1,…,p−1 by a is injective, hence a permutation of this finite set.\n\nThe picture includes residue 0 so the whole map is visible; 0 stays 0 and the remaining tiles rearrange. The theorem below uses the product of only the nonzero residues, because including zero would destroy the cancellable product.',r'\{a,2a,\ldots,(p-1)a\}\pmod p=\{1,2,\ldots,p-1\}'),
p('Cancel the product to obtain Fermat’s theorem', 'Multiply every nonzero residue before and after the permutation. This gives aᵖ⁻¹(p−1)!≡(p−1)! modulo p. None of the factors in (p−1)! is divisible by p, so the product is invertible and may be canceled. Therefore aᵖ⁻¹≡1 when p does not divide a.\n\nMultiplying by a gives aᵖ≡a. The latter formula is true even when p divides a, because then both sides are zero modulo p. Do not apply the exponent p−1 version to multiples of p.',r'p\nmid a\Rightarrow a^{p-1}\equiv1\pmod p,\qquad a^p\equiv a\pmod p'),
p('Combine coprime moduli by an explicit construction', 'Let r,s≥2 be coprime integers and suppose x≡u modulo r and x≡v modulo s. Set x=u+rt. Since r has an inverse r⁻¹ modulo s, choose t≡(v−u)r⁻¹ modulo s. This constructs a solution. If x and y satisfy both conditions, r and s divide x−y; coprimality makes rs divide x−y. Thus the solution is unique modulo rs.\n\nFor x≡2 modulo 5 and x≡1 modulo 3, write x=2+5t. Then 2t≡2 modulo 3, so t≡1 and x≡7 modulo 15.',r'x=u+r\bigl((v-u)r^{-1}\bmod s\bigr)\pmod{rs}'),
p('Do not turn the theorem into a false primality test', 'A composite modulus may satisfy a Fermat congruence for some bases. For example, 2³⁴⁰≡1 modulo 341 although 341=11·31. Checking one base is therefore not a proof of primality. When a shares a factor with the modulus, multiplication can have collisions, and the permutation proof fails.\n\nFor noncoprime r,s, simultaneous congruences are compatible only when u≡v modulo gcd(r,s), and a compatible solution is unique modulo lcm(r,s), not necessarily rs. For instance, x≡0 modulo 4 and x≡1 modulo 6 have no solution because their parity requirements conflict.',r'341=11\cdot31,\qquad 2^{340}\equiv1\pmod{341}')],
q('Why does multiplication by 6 rearrange all ten nonzero residues modulo 11 without collision?', ['Because 6 is even','Because gcd(6,11)=1 permits cancellation modulo 11','Because every multiplier works for every modulus'],1,'If 6x≡6y modulo 11, coprimality gives x≡y. An injective map of the finite nonzero residue set is a permutation.'),
q('For p=5 and a=2, why may the product 1·2·3·4 be canceled modulo 5?', ['It equals 1 as an integer','It has no factor 5 and therefore has an inverse modulo 5','Every nonzero integer may be canceled modulo every modulus'],1,'The product is coprime to 5. Nonzero alone is not enough for composite moduli.'),'Use p=5 and multiplier 2, then ignore the fixed zero tile when multiplying the nonzero residues.')
lesson(33,'98–99',[
p('An ordered choice uses a shrinking supply', 'Five distinct badges can fill three ordered positions in 5·4·3 ways. There are five choices for the first slot, four remaining choices for the second, and three for the third. The scene displays one particular prefix, but the count beside it counts all possible prefixes of that length. Do not confuse one displayed arrangement with the whole collection.\n\nFor n distinct objects and 0≤k≤n ordered slots without replacement, the count is n(n−1)⋯(n−k+1)=n!/(n−k)!. It is also called a falling factorial.',r'P(n,k)=n^{\underline k}=\frac{n!}{(n-k)!}'),
p('Factorial is the full-length special case', 'When k=n, every object is placed and the count is n!. Define 0!=1: there is exactly one ordering of no objects, the empty ordering. Likewise P(n,0)=1, since making no choices is one possible result. If k>n, no injective arrangement exists and its counting value is zero; the factorial quotient should not be evaluated at a negative factorial.\n\nThe multiplication rule counts a decision tree when every prefix at the same depth has the same number of possible next choices. With constraints that change that number, summing branch counts may be necessary.',r'n!=\prod_{j=1}^{n}j,\qquad0!=1'),
p('Repeated labels require a quotient argument', 'Suppose n badges carry repeated labels with multiplicities m₁,…,mᵣ summing to n. Temporarily label every badge individually. There are n! labeled arrangements. For any fixed visible word, rearranging the identities within each repeated label produces exactly m₁!⋯mᵣ! labeled arrangements. Every visible word has the same number of preimages, so division gives n!/(m₁!⋯mᵣ!).\n\nFor the multiset A,A,B,B,C, this yields 5!/(2!2!1!)=30 visible words. Simply applying the distinct-object formula would overcount.',r'\#\text{multiset words}=\frac{n!}{\prod_{j=1}^{r}m_j!}'),
p('Identify what the observer can distinguish', 'A lineup, a subset, and a necklace have different equivalences. A subset forgets all k! orders of its chosen members. A circular seating may identify rotations, but reflections need not be equivalent; repeated labels can also change orbit sizes. Never divide by a symmetry count without checking that every outcome is overcounted equally.\n\nOur model checks distinct-object counts against explicit enumeration for n≤7. That verifies the implementation on small cases. The arbitrary-length multiplication and equal-fiber arguments prove the formulas for all allowed n.',r'\text{equal-size fibers justify division}')],
q('How many ways can six distinct badges fill three ordered slots without reuse?', ['20','120','216'],1,'Successive choices give 6·5·4=120. Twenty would forget order; 216 would allow reuse.'),
q('With three distinct badges and two ordered slots, how many outcomes are there?', ['3','6','9'],1,'Three choices for the first slot leave two for the second. Reusing a badge is not allowed.'),'Use only A, B, C and two slots; distinguish one visible prefix from the count of all prefixes.')
lesson(34,'99–101',[
p('A factorial contains layers of prime factors', 'The symbol νₚ(n!) means the number of copies of prime p in the prime factorization of n!. To count those copies, count how many factors contribute at least one p, how many contribute an additional p, and so on. Multiples of p contribute the first layer, multiples of p² the second, and multiples of p³ the third. Thus the exponent is the sum of floor(n/pʲ) for j≥1. Only finitely many terms are nonzero.\n\nFor 10! and p=2 the layers contribute 5+2+1=8. The factor 8 is correctly counted three times, because 8 contains three copies of 2. Each colored block in the scene represents one copy, not one whole integer factor.',r'\nu_p(n!)=\sum_{j\ge1}\left\lfloor\frac n{p^j}\right\rfloor\quad(p\text{ prime})'),
p('Prove the layer count by interchanging finite sums', 'Let νₚ(k) be the largest e≥0 with pᵉ dividing k, for positive integer k and prime p. Then νₚ(n!)=Σₖ₌₁ⁿνₚ(k). Express νₚ(k) as Σⱼ≥₁[pʲ divides k], and interchange the finite nonzero terms. The inner count of multiples of pʲ is floor(n/pʲ).\n\nPrimality matters because prime exponents add in products. For a composite “base” such as 4, separate factors 2 and 2 can combine into a factor 4; counting only multiples of powers of 4 misses such contributions. The displayed valuation function is deliberately defined for prime p.',r'\nu_p(ab)=\nu_p(a)+\nu_p(b)\quad(p\text{ prime})'),
p('Compare exact growth with a controlled preview', 'Here e≈2.71828 is the base of natural logarithms, and exp(x)=eˣ is the natural exponential function. Stirling’s leading estimate is Lₙ=√(2πn)(n/e)ⁿ for positive integer n. Its asymptotic meaning is n!/Lₙ→1, not that their difference tends to zero. A useful quantitative form is Lₙ exp(1/(12n+1))<n!<Lₙ exp(1/(12n)). We use this classical bound as a stated result here; its analytic proof belongs to the later asymptotic-analysis material.\n\nCompute relative error as |Lₙ−n!|/n!, rather than only absolute error. An estimate can have a small relative error while missing by an enormous integer amount.',r'\sqrt{2\pi n}(n/e)^n<n!<\sqrt{2\pi n}(n/e)^n e^{1/(12n)}'),
p('Large integers and logarithms answer different questions', 'Exact factorials use integer arithmetic. A decimal digit count can be estimated from log₁₀(n!)=Σₖ₌₁ⁿlog₁₀k, but a floating estimate near an integer boundary needs an error bound before flooring. Logarithms help compare scales without overflowing; they do not reproduce every digit.\n\nTrailing decimal zeros equal min(ν₂(n!),ν₅(n!)); in a factorial the 5-count is the smaller one. At n=0 the factorial is 1 and all prime valuations are zero. Stirling’s displayed expression is reserved for n≥1.',r'\text{trailing zeros of }n!=\nu_5(n!)')],
q('How many trailing decimal zeros does 30! have?', ['5','6','7'],2,'Multiples of 5 supply six factors, and 25 supplies one additional factor of 5. Thus ν₅(30!)=6+1=7.'),
q('Why does factor 4 appear in two prime-2 layers of 6!?', ['Because 4=2·2','Because it has two decimal digits','Because all even factors are counted twice'],0,'Each layer records one factor of 2; 4 is divisible by 2 and by 4.'),'Use 6!, where only the first two layers are nonempty.','Stirling’s approximation and explicit error bound are stated previews, not proved here; exact valuations are proved and modeled.')
lesson(35,'101–105',[
p('A smooth extension needs more than a lookup table', 'Factorials prescribe values at nonnegative integers, but infinitely many functions agree there. The gamma function is a principled extension: for real x>0, Γ(x)=∫₀∞tˣ⁻¹e⁻ᵗ dt. This positive improper integral converges. Near zero, tˣ⁻¹ is integrable exactly for x>0; at infinity the exponential dominates every fixed power.\n\nThe scene uses x=1, where the curve is simply e⁻ᵗ. It brackets the area on [0,T] by left and right rectangles, then adds the exact tail e⁻ᵀ. The printed decimal endpoints are rounded approximations to analytical bounds. The inequality between the exact rectangle sums and the integral follows from monotonicity.',r'\Gamma(x)=\int_0^\infty t^{x-1}e^{-t}\,dt\quad(x>0)'),
p('Integration by parts recovers the recurrence', 'For x>0, integration by parts gives Γ(x+1)=xΓ(x). The endpoint tˣe⁻ᵗ vanishes both at zero and infinity, so there is no leftover boundary term. Also Γ(1)=∫₀∞e⁻ᵗdt=1. Induction then yields Γ(n+1)=n! for every nonnegative integer n.\n\nThe half-integer value Γ(1/2)=√π follows by substituting t=u² and using the Gaussian integral. That Gaussian integral is a separate theorem, not established by our one-dimensional rectangle display. The recurrence therefore gives Γ(3/2)=√π/2 and Γ(5/2)=3√π/4.',r'\Gamma(x+1)=x\Gamma(x),\qquad\Gamma(n+1)=n!'),
p('The recurrence alone does not select gamma', 'If h(x) is any nonconstant positive function of period 1 with h(1)=1, then G(x)=h(x)Γ(x) also satisfies G(x+1)=xG(x) and agrees with factorial values at positive integers. For example, h(x)=exp(c sin(2πx)) with nonzero real c has these properties. Thus interpolation and recurrence do not imply uniqueness.\n\nA classical characterization adds positivity and logarithmic convexity on x>0, together with G(1)=1; these select Γ. We state this characterization to explain what extra structure is needed, without pretending to prove the characterization here.',r'h(x+1)=h(x)\Rightarrow G(x+1)=xG(x)'),
p('Continuation and numerical accuracy have boundaries', 'The source also gives Euler’s limit Γ(x)=lim as m→∞ of mˣm!/[x(x+1)⋯(x+m)], initially for x>0. The integral route here is an equivalent standard construction; the equivalence is not proved by the rectangle animation.\n\nThe recurrence extends Γ to negative noninteger real arguments, and complex analysis gives a meromorphic continuation to the complex plane. It has poles at 0,−1,−2,…, so writing Γ(0) as an ordinary finite value is invalid. Two advanced source formulas deserve precise statements. Reflection: Γ(z)Γ(1−z)=π/sin(πz) for complex z not an integer. Hankel: 1/Γ(z)=(1/(2πi))∫_H eᵗt⁻ᶻdt, valid for every complex z, with the reciprocal gamma extended as an entire function. The contour H comes from −∞ below the negative real axis, circles the origin counterclockwise at a fixed positive radius, then returns above the negative axis. Use t⁻ᶻ=exp(−z Log t), with −π<arg(t)<π and the corresponding limiting values on the two rays. A radius-to-zero limit is not being asserted for arbitrary z. These are stated complex-analysis theorems; proving them requires analytic continuation, contour integration, and branch conventions beyond this unit. At a gamma pole, reciprocal gamma is zero rather than an undefined ordinary quotient.\n\nFor the displayed x=1 integral, decreasing e⁻ᵗ gives rigorous finite rectangle bounds. Increasing the rectangle count tightens their difference; increasing T controls the omitted tail. A generic numerical quadrature output without a proven bound would not certify an arbitrary gamma value.',r'\Gamma\text{ has poles at }0,-1,-2,\ldots')],
q('For the Γ(1) integral, if the finite interval ends at T=ln 5, how much exact area remains beyond T?', ['0','1/ln 5','1/5'],2,'The tail is exp(−T). At T=ln 5, exp(−ln 5)=1/5. Refining rectangles on [0,T] does not remove this tail.'),
q('For Γ(1), what must be added to the area from 0 to T?', ['Nothing','e⁻ᵀ','T e⁻ᵀ'],1,'The integral of e⁻ᵗ from T to infinity is e⁻ᵀ exactly.'),'Bracket the simplest gamma integral, x=1, on a shorter interval before increasing the rectangle count.','Euler’s limit and its beta-integral/dominated-convergence bridge are supplied; its x=1 and x=2 witnesses are exact. Complex continuation, reflection, Hankel’s contour formula, and the log-convex uniqueness theorem are precisely stated but reading-led, not interactively proved. No general-purpose gamma quadrature accuracy claim.')
lesson(36,'105–106',[
p('Three rows, three meanings of a power', 'An ordinary power xᵏ multiplies k copies of x. A falling factorial x underlined k multiplies x,x−1,…,x−k+1. A rising factorial x overlined k multiplies x,x+1,…,x+k−1. Here k is a nonnegative integer and x may be real or complex. Every empty product at k=0 is 1.\n\nFor x=5 and k=3, the three values are 125,60,210. The rows make the difference visible: position j changes the factor only in the falling and rising rows. A notation that hides this shift can encourage invalid ordinary exponent laws.',r'x^{\underline k}=\prod_{j=0}^{k-1}(x-j),\quad x^{\overline k}=\prod_{j=0}^{k-1}(x+j)'),
p('Split a factorial power with a shifted base', 'Split the product for x underlined (m+n) after the first m factors. The remaining factors start at x−m, so x underlined (m+n) equals (x underlined m)((x−m) underlined n). For rising powers, the second base is x+m. These formulas hold for nonnegative integer m,n and every real or complex x because they are product identities.\n\nThey are not the ordinary exponent law with the same base in both factors. For instance, 5 underlined 2 times 5 underlined 1 is 100, but 5 underlined 3 is 60.',r'x^{\underline{m+n}}=x^{\underline m}(x-m)^{\underline n}'),
p('Reverse the factors or negate each one', 'Reversing the order of a rising product gives x overlined k=(x+k−1) underlined k. Extracting a minus sign from every factor gives x overlined k=(−1)ᵏ(−x) underlined k. These are polynomial identities and remain meaningful even when a factor is zero.\n\nFor positive x where the gamma quotients are finite, x overlined k=Γ(x+k)/Γ(x). Similarly x underlined k=Γ(x+1)/Γ(x−k+1) where that quotient is defined. At a gamma pole, use the product polynomial or an explicitly justified continuation, rather than dividing undefined values.',r'x^{\overline k}=(x+k-1)^{\underline k}=(-1)^k(-x)^{\underline k}'),
p('Discrete differences lower the degree cleanly', 'Let Δf(x)=f(x+1)−f(x). Factoring the common k−1 factors in (x+1) underlined k minus x underlined k gives Δ(x underlined k)=k x underlined (k−1) for k≥1. This is why factorial powers are natural for discrete summation.\n\nSumming from x=0 through n−1 yields Σₓ₌₀ⁿ⁻¹ x underlined k = n underlined (k+1)/(k+1) for k≥0. The starting endpoint 0 underlined (k+1) vanishes. The formula includes k=0: summing n copies of 1 gives n.',r'\Delta x^{\underline k}=k x^{\underline{k-1}}')],
q('Which expression equals 7 underlined 5 after its first two factors are split off?', ['(7 underlined 2)(7 underlined 3)','(7 underlined 2)(5 underlined 3)','(7 underlined 3)(5 underlined 2)'],1,'After factors 7 and 6, the remaining three are 5,4,3. Their starting base is 7−2=5.'),
q('For x=3 and k=3, what is the rising product?', ['3·2·1=6','3·3·3=27','3·4·5=60'],2,'Rising means each successive factor is one larger.'),'Use base 3 and compare the same three factor positions in all three rows.')
lesson(37,'110–116',[
p('Forget the order, but keep the members', 'For nonnegative integer n and integer k with 0≤k≤n, the binomial coefficient counts k-element subsets of n distinct objects. Each subset has k! ordered listings. The n underlined k injective listings therefore divide into equal groups of k!, giving n!/[k!(n−k)!].\n\nChoosing the omitted objects instead gives a bijection between k-subsets and (n−k)-subsets, which proves symmetry. The empty subset is unique, so choosing zero objects gives 1. If k<0 or k>n, no such subset exists and the counting value is 0.',r'\binom nk=\frac{n!}{k!(n-k)!}=\binom n{n-k}\quad(0\le k\le n)'),
p('Build Pascal’s triangle by a disjoint decision', 'Mark one of the n objects. A k-subset either excludes it, leaving a k-subset of the other n−1 objects, or includes it, leaving a (k−1)-subset of those objects. The two cases do not overlap and cover every subset. Their counts add.\n\nThe scene draws an edge from each contributing parent to its child. Missing parents outside the triangle have count zero. Row zero begins with one empty subset. The sum of row n is 2ⁿ because each of the n objects can independently be included or excluded.',r'\binom nk=\binom{n-1}k+\binom{n-1}{k-1}\quad(n\ge1)'),
p('The algebraic extension has a different domain', 'For any real or complex r and nonnegative integer k, define C(r,k)=r underlined k/k!. This polynomial definition agrees with subset counts when r=n is a nonnegative integer, but a noninteger upper index no longer literally counts subsets. Define C(r,k)=0 for negative integer k.\n\nPascal’s identity extends to all r by polynomial algebra for each fixed nonnegative k. Symmetry C(r,k)=C(r,r−k) does not transfer unqualified: r−k may not even be an integer lower index. Keep counting arguments in their declared integer domain.',r'\binom rk=\frac{r^{\underline k}}{k!}\quad(k\in\mathbb N_0)'),
p('A diagonal sum can be partitioned by the largest member', 'For fixed integer m≥0, Σₖ₌₀ⁿ C(k,m)=C(n+1,m+1). Count (m+1)-subsets of {1,…,n+1} by their largest member k+1, where 0≤k≤n. The other m members must come from {1,…,k}, giving C(k,m) possibilities for this case.\n\nThis “hockey-stick” identity follows by repeated Pascal addition too. Terms with k<m vanish automatically. A precise convention for out-of-range lower indices makes the boundary cases painless.',r'\sum_{k=0}^{n}\binom{k}{m}=\binom{n+1}{m+1}\quad(n,m\ge0)')],
q('How many 3-subsets of an 8-element set contain a specified member?', ['C(7,3)=35','C(8,2)=28','C(7,2)=21'],2,'Include the specified member, then choose the other two from the remaining seven.'),
q('Why does C(3,2) equal 3 when C is the marked member?', ['Exclude C: 1 subset; include C: 2 subsets','There are three orders of each pair','Every binomial coefficient equals its upper index'],0,'Excluding C leaves {A,B}; including C gives {A,C} and {B,C}. The disjoint cases total 1+2=3.'),'Use A, B, C: group the two orders of each pair, then split the three subsets by whether they contain C.')
lesson(38,'116–119',[
p('Every factor contributes one choice', 'Expand (a+b)ⁿ with n a nonnegative integer. A term in the full distributive expansion is specified by a word of n choices, each a or b. If exactly k positions choose b, the term becomes aⁿ⁻ᵏbᵏ. There are C(n,k) such position sets, so equal monomials combine into the finite binomial theorem.\n\nThe scene preserves each choice word while regrouping it by its number of b’s. Coefficients arise from how many words land in a group; they are not additional choices made after the expansion.',r'(a+b)^n=\sum_{k=0}^{n}\binom nk a^{n-k}b^k'),
p('Substitution produces useful sum identities', 'Set a=b=1 to obtain Σₖ C(n,k)=2ⁿ. Set a=1,b=−1 to obtain Σₖ(−1)ᵏC(n,k)=0 for n≥1. For n=0, both sums are 1 because the expansion contains its one empty product. Differentiating the finite polynomial (1+z)ⁿ gives Σₖ kC(n,k)zᵏ⁻¹=n(1+z)ⁿ⁻¹. At z=1 this yields Σₖ kC(n,k)=n2ⁿ⁻¹ for n≥1.\n\nThese manipulations are finite polynomial operations, so no infinite-series convergence issue arises.',r'\sum_{k=0}^{n}k\binom nk=n2^{n-1}\quad(n\ge1)'),
p('A noninteger exponent gives an infinite expansion', 'For real r and real z with |z|<1, the generalized binomial theorem says (1+z)ʳ=Σₖ≥₀ C(r,k)zᵏ, using the falling-product definition of C(r,k). The ratio of successive nonzero term magnitudes approaches |z|, giving absolute convergence inside this interval. The coefficient recurrence (k+1)cₖ₊₁=(r−k)cₖ makes the resulting series satisfy (1+z)F′=rF with F(0)=1; uniqueness of this differential equation identifies F=(1+z)ʳ.\n\nFor r=−1 the coefficients alternate signs and the formula is the geometric series for 1/(1+z). This is the model’s separately controlled generalized example.',r'(1+z)^r=\sum_{k\ge0}\binom rkz^k\quad(|z|<1)'),
p('Boundary points require their own analysis', 'Do not substitute z=1 or z=−1 merely because a plot looks smooth inside the convergence interval. For r=−1 and z=1, the partial sums 1−1+1−1+⋯ oscillate even though 1/(1+1)=1/2 exists. At z=−1 the function itself has a pole and the series terms are all 1.\n\nFor a nonnegative integer exponent, the series terminates and the finite theorem is valid for every real or complex z. The domain changes because there are only finitely many nonzero coefficients, not because endpoint convergence was silently assumed.',r'r\in\mathbb N_0\Rightarrow\binom rk=0\quad(k>r)')],
q('What is the coefficient of x² in (2+x)⁵?', ['10','40','80'],2,'Choose the two x positions in C(5,2)=10 ways; the remaining three positions contribute 2³=8. The coefficient is 80.'),
q('In (a+b)², why is the mixed coefficient 2?', ['The words ab and ba have the same scalar product','There are only two terms in the full expansion','a and b must be equal'],0,'The distinct choice words ab and ba both become the monomial ab.'),'Use only two factors, making all four choice words visible.')
lesson(39,'111;114–120',[
p('Start from factors when the upper index is negative', 'For integer k≥0 and real r, C(r,k)=r(r−1)⋯(r−k+1)/k!. Replacing r by −r gives k negative factors. Extracting each minus sign leaves r(r+1)⋯(r+k−1), which is the reversed falling product for upper index r+k−1. Thus C(−r,k)=(−1)ᵏC(r+k−1,k).\n\nFor example C(−4,3)=−20. It is perfectly defined by a polynomial product even though (−4)! is not an ordinary factorial. The diagram tracks the sign separately from the positive factors.',r'\binom{-r}{k}=(-1)^k\binom{r+k-1}{k}\quad(k\ge0)'),
p('Prefer a division-free identity when a denominator may vanish', 'For k≥1, canceling a common product gives kC(r,k)=rC(r−1,k−1). Dividing by k is safe in this domain. Another absorption relation is (r−k)C(r,k)=rC(r−1,k). This division-free form is valid for all real r and fixed nonnegative integer k. The quotient version C(r,k)=rC(r−1,k)/(r−k) requires r≠k.\n\nAt r=k, both sides of the division-free equation are zero, but dividing by r−k would be invalid. A correct identity can have a misleading solved form.',r'k\binom rk=r\binom{r-1}{k-1}\quad(k\ge1)'),
p('Choose in stages and then change which stage comes first', 'For integers 0≤k≤m≤n, choosing an m-subset and then a k-subset inside it gives C(n,m)C(m,k). Choose the k-subset first instead, then add m−k members from the remaining n−k objects. This gives C(n,k)C(n−k,m−k). It is the same nested pair of subsets counted in two orders.\n\nFactorial cancellation verifies the algebra in the integer domain. For polynomial extensions, fix lower indices and prove an identity as a polynomial in the upper variable; equality at infinitely many nonnegative integers then proves the polynomial identity. Numerical agreement at a few points alone is not that proof.',r'\binom nm\binom mk=\binom nk\binom{n-k}{m-k}'),
p('Write the side condition beside the rewrite', 'A useful transformation records which variables are integers, which denominators must be nonzero, and whether out-of-range coefficients use the zero convention. Avoid applying factorial formulas with a negative-integer factorial or extending symmetry to a noninteger lower index.\n\nFor a fixed lower k, C(r,k) is a polynomial of degree k, so identities can survive at values where an intermediate quotient fails. Resolve this by using the polynomial identity itself, not by assigning a value to 0/0. The ability to manipulate symbols depends on maintaining these domains.',r'\text{valid identity}\ne\text{every rearranged quotient is defined}')],
q('What is C(−3,4) using the polynomial definition?', ['−15','15','Undefined because (−3)! is undefined'],1,'Upper-index negation gives (−1)⁴C(6,4)=15. No negative factorial is needed.'),
q('For C(−2,3), how many minus signs are extracted?', ['2','3','0'],1,'There are three factors −2,−3,−4; the sign is (−1)³ and the value is −4.'),'Use C(−2,3), pull out its three signs, and retain the positive factors 2,3,4.')
lesson(40,'120–124;130',[
p('Every final set determines its own split', 'Take disjoint groups A and B of sizes r and s. To choose n objects from their union, let k be the number chosen from A. For this fixed k there are C(r,k)C(s,n−k) possibilities. Different k values describe disjoint cases, and every chosen n-set has exactly one such k. Summing gives Vandermonde’s identity.\n\nThe scene uses r=3, s=4, n=3. The case totals are 4,18,12,1, which add to 35=C(7,3). A bin depicts a case count, not a single representative set multiplied accidentally by the same count again.',r'\sum_k\binom rk\binom s{n-k}=\binom{r+s}n'),
p('Make the finite support explicit', 'For nonnegative integer r,s,n, only max(0,n−s)≤k≤min(r,n) can contribute. Using zero coefficients outside the counting range permits a simpler sum from k=0 to n. If n>r+s, both sides are zero. If n=0, the single empty choice contributes 1.\n\nThe proof depends on the two groups being disjoint. If one object belonged to both categories and could be chosen twice through different descriptions, the product count would need correction. Counting by a property works when the property assigns each outcome to exactly one case.',r'\max(0,n-s)\le k\le\min(r,n)'),
p('Use polynomial coefficients for the generalized identity', 'The notation [zⁿ] means the coefficient multiplying the power zⁿ; for example, [z²](1+3z+7z²)=7. Multiply (1+z)ʳ and (1+z)ˢ and take the coefficient of zⁿ. For integer r,s this is ordinary polynomial multiplication. For real r,s, generalized binomial series converge absolutely when |z|<1, and the coefficient of fixed degree n uses only n+1 terms. The product is (1+z)ʳ⁺ˢ, so the same finite convolution identity holds for real upper indices and nonnegative integer n.\n\nThis is a separate algebraic/analytic justification. A half-object subset interpretation does not become valid merely because the formula extends.',r'[z^n](1+z)^r(1+z)^s=\sum_{k=0}^{n}\binom rk\binom s{n-k}'),
p('More groups produce multinomial coefficients', 'For disjoint groups, repeat the two-stage partition to obtain multiway convolutions. In a related assignment problem, place n distinct objects into labeled categories with prescribed sizes k₁,…,kₘ summing to n. The count is n!/(k₁!⋯kₘ!), obtained by choosing each category’s members from those remaining.\n\nThis coefficient also appears in (x₁+⋯+xₘ)ⁿ: each term records one category choice per factor. Category labels matter; forgetting them changes the equivalence relation and generally changes the count.',r'\binom n{k_1,\ldots,k_m}=\frac{n!}{k_1!\cdots k_m!},\quad\sum_jk_j=n')],
q('Choose four objects from groups of sizes 2 and 5. How many choices use exactly one from the size-2 group?', ['10','20','30'],1,'Choose one of the two, then three of the five: C(2,1)C(5,3)=2·10=20.'),
q('Choosing two from groups of sizes 2 and 2, what are the three case totals for k=0,1,2?', ['1,4,1','2,2,2','0,4,0'],0,'Both from the second group gives 1; one from each gives 2·2=4; both from the first gives 1.'),'Use two badges in each group and choose two, so all three possible split sizes are visible.')
lesson(41,'125–135',[
p('Differences uncover a better polynomial basis', 'The forward difference Δf(x)=f(x+1)−f(x) replaces neighboring values by their difference. For f(x)=x³ at x=0,1,2,3,4, the successive rows begin 0,1,8,27,64; then 1,7,19,37; then 6,12,18; then 6,6. A degree-three polynomial has a constant third difference.\n\nOrdinary powers are natural for derivatives; falling factorials are natural for differences because Δx underlined k=k x underlined (k−1). Equivalently, ΔC(x,k)=C(x,k−1). Here Δᵏf(0) is the first entry after k rounds of taking adjacent differences, with Δ⁰f(0)=f(0); d denotes the degree of the polynomial. The difference table therefore gives the Newton expansion f(x)=Σₖ Δᵏf(0)C(x,k) for any polynomial f.',r'f(x)=\sum_{k=0}^{d}\Delta^k f(0)\binom xk\quad(\deg f\le d)'),
p('Partition fibers to convert ordinary powers', 'Let S(n,k) count partitions of an n-element labeled set into k nonempty unlabeled blocks. Count functions from that set into x labeled targets, first for nonnegative integer x. There are xⁿ functions. Alternatively, partition the domain into its k nonempty fibers, then assign distinct target labels to those blocks in x underlined k ways. Thus xⁿ=Σₖ S(n,k)x underlined k. Since both sides are polynomials, the identity extends to every real or complex x.\n\nThe bases are S(0,0)=1, S(n,0)=0 for n>0, and zero outside 0≤k≤n. Adding a new element either puts it in one of k existing blocks or makes a new singleton, proving S(n+1,k)=kS(n,k)+S(n,k−1).',r'x^n=\sum_{k=0}^{n}S(n,k)x^{\underline k}'),
p('First-kind coefficients undo the change of basis', 'Let c(n,k) be the unsigned Stirling number of the first kind, counting permutations of n labels with k cycles. Insert the newest label after one of the n existing labels in a cycle, or make it a singleton cycle. This proves c(n+1,k)=n c(n,k)+c(n,k−1), with c(0,0)=1 and the same zero conventions.\n\nThe signed coefficient s(n,k)=(−1)ⁿ⁻ᵏc(n,k) expands the falling factorial: x underlined n=Σₖs(n,k)xᵏ. Induction follows by multiplying by x−n. These signed first-kind and second-kind triangular coefficient arrays are inverse changes of basis; the unsigned array alone does not supply the inverse signs.',r'x^{\underline n}=\sum_{k=0}^{n}(-1)^{n-k}c(n,k)x^k'),
p('Use the new basis to sum a polynomial', 'For cubes, the second-kind coefficients are S(3,1)=1, S(3,2)=3, S(3,3)=1. Thus x³=x underlined 1+3x underlined 2+x underlined 3. Sum from x=0 through N−1 and apply the falling-factorial antidifference term by term. This yields N underlined 2/2 + N underlined 3 + N underlined 4/4, equal to [N(N−1)/2]².\n\nThe implementation checks small set partitions exhaustively and verifies polynomial identities coefficient by coefficient. A table of evaluated points is useful testing, but the fiber argument and induction establish the identities in general.',r'\sum_{x=0}^{N-1}x^3=\left(\frac{N(N-1)}2\right)^2')],
q('What is the coefficient of x underlined 2 in the expansion of x⁴?', ['6','7','12'],1,'It is S(4,2)=2S(3,2)+S(3,1)=2·3+1=7.'),
q('How many partitions of {A,B} into one nonempty block exist?', ['1','2','0'],0,'Only {A,B}. The two blocks are not labeled bins, and neither may be empty.'),'Start with squares, whose second differences are constant; then identify the two possible partition counts.')
lesson(42,'144–146',[
p('Small positive increments can still escape every bound', 'Define H₀=0 and Hₙ=Σₖ₌₁ⁿ1/k for integer n≥1. Every new bar has smaller height, so the growth slows. But in the group 2ʲ<k≤2ʲ⁺¹ there are 2ʲ terms, each at least 1/2ʲ⁺¹. Every such group contributes at least 1/2. After m groups, H₂ᵐ≥1+m/2.\n\nAs m can be arbitrarily large, the harmonic sequence is unbounded. This is a proof of divergence; an upward-looking finite chart would not be one. Shrinking terms alone do not imply a finite sum.',r'H_{2^m}\ge1+\frac m2\quad(m\ge0)'),
p('A decreasing curve brackets the rectangles', 'The function 1/x is positive and decreasing on x>0. On [k,k+1], its integral is at most 1/k. Summing gives ln(n+1)≤Hₙ. On [k−1,k] for k≥2, its integral is at least 1/k, giving Hₙ≤1+ln n. These inequalities hold for n≥1 and use the natural logarithm.\n\nThe lower curve area and upper rectangle sum are different objects. The picture helps identify which lies above which, while the monotonicity argument supplies the bound for every interval.',r'\ln(n+1)\le H_n\le1+\ln n\quad(n\ge1)'),
p('A limiting offset refines the logarithmic scale', 'The sequence Hₙ−ln n decreases and stays positive. Indeed, its change is 1/(n+1)−ln(1+1/n)<0 because the integral of 1/x on [n,n+1] exceeds its right-endpoint rectangle. The lower integral bound keeps Hₙ−ln n above zero. Hence it has a limit, called Euler’s constant γ.\n\nThis establishes the existence of γ without computing its decimal digits. The stronger expansion Hₙ=ln n+γ+1/(2n)−1/(12n²)+⋯ requires an error-controlled asymptotic theorem and is deferred to later material. A rounded estimate of the offset is not its exact definition.',r'\gamma=\lim_{n\to\infty}(H_n-\ln n)'),
p('Use bounds as a scale estimate', 'To roughly double a large harmonic total, n must grow far more than by a factor of two; the leading growth is logarithmic. Doubling n adds a quantity approaching ln 2, not another copy of Hₙ. The exact rational model and logarithmic bounds are different kinds of information and are labeled accordingly.\n\nAt n=0 the definition H₀=0 still works, but the bounds involving ln n do not. Every use of the logarithm must retain n≥1. Later algorithm costs often contain harmonic sums because a success probability or contribution at stage k is proportional to 1/k.',r'H_{2n}-H_n=\sum_{k=n+1}^{2n}\frac1k')],
q('How large is the lower bound 1+m/2 for H₆₄?', ['4','6','7'],0,'64=2⁶, so the six dyadic groups contribute at least 3 beyond the initial 1.'),
q('In the group k=3,4, what guaranteed lower total comes from replacing both terms by 1/4?', ['1/4','1/2','1'],1,'There are two terms, each at least 1/4, so their sum is at least 1/2.'),'Use the first four bars and inspect the two-term group from 3 through 4.')
lesson(43,'146–149',[
p('The same reciprocal appears in many rows', 'Write H₁,H₂,…,Hₙ as rows of a triangular grid. Row i contains 1,1/2,…,1/i. The column for reciprocal 1/j begins at row j and ends at row n, so it contains n−j+1 copies. Count by columns instead of rows to evaluate Σᵢ₌₁ⁿHᵢ.\n\nThe total is Σⱼ₌₁ⁿ(n−j+1)/j=(n+1)Hₙ−n. Every tile retains its pair (i,j) when the grouping changes. This is a finite reindexing identity, so convergence of an infinite series is irrelevant.',r'\sum_{i=1}^{n}H_i=(n+1)H_n-n'),
p('A second identity separates diagonal and off-diagonal terms', 'Expand Hₙ²=ΣᵢΣⱼ1/(ij). The strict lower and strict upper triangles have equal totals after swapping i and j. The diagonal contributes Hₙ⁽²⁾=Σₖ1/k². The sum Σₖ Hₖ/k is the lower triangle including the diagonal. It therefore equals half the square total plus half the diagonal total.\n\nThis proof explains the plus sign: the diagonal is included once in the desired triangle but only half a time in half of the square. Add the missing half.',r'\sum_{k=1}^{n}\frac{H_k}{k}=\frac{H_n^2+H_n^{(2)}}2'),
p('Higher reciprocal powers have a convergence threshold', 'For real r, define the finite generalized harmonic sum Hₙ⁽ʳ⁾=Σₖ₌₁ⁿk⁻ʳ. If r>1, the infinite sum converges to ζ(r). The integral comparison bounds the tail after n≥1 between (n+1)¹⁻ʳ/(r−1) and n¹⁻ʳ/(r−1). These bounds tend to zero.\n\nIf r≤1, then k⁻ʳ≥1/k for k≥1, so the series diverges by comparison with the harmonic series. The symbol ζ(r) has an advanced analytic continuation elsewhere, but that continuation is not the value of this divergent positive-term series.',r'\frac{(n+1)^{1-r}}{r-1}\le\sum_{k=n+1}^{\infty}k^{-r}\le\frac{n^{1-r}}{r-1}\quad(r>1)'),
p('Choose a rearrangement that simplifies multiplicity', 'When a harmonic number appears inside another finite sum, expand its definition and inspect how often each reciprocal occurs. A weight depending on the row may require summing those weights across the column. Summation by parts is another route when the differences of the weight simplify.\n\nFor n=0 both displayed finite identities give zero. Rational arithmetic keeps all finite examples exact; the model does not equate a finite Hₙ⁽²⁾ with ζ(2). A limit value and a partial sum differ by the positive tail, even when their rounded displays happen to agree.',r'H_0=H_0^{(2)}=0')],
q('What is H₁+H₂+H₃+H₄?', ['25/12','77/12','125/12'],1,'H₄=25/12, so (4+1)H₄−4=125/12−48/12=77/12.'),
q('In the three-row grid, how many copies of 1/2 occur?', ['1','2','3'],1,'They occur in H₂ and H₃, so the column contributes 2·(1/2)=1.'),'Use only H₁,H₂,H₃ and count the repeated half-sized tile.')
lesson(44,'152–155',[
p('A local two-slot update carries the entire sequence', 'Define F₀=0, F₁=1, and Fₙ₊₂=Fₙ₊₁+Fₙ for every n≥0. The vector (Fₙ₊₁,Fₙ) updates by the matrix Q with rows (1,1) and (1,0). Multiplication replaces the first slot by the sum and the second by the old first slot.\n\nA separate counting interpretation uses a length-m walkway tiled by pieces of length 1 or 2. Its count Tₘ satisfies T₀=T₁=1 and Tₘ=Tₘ₋₁+Tₘ₋₂ by examining the first tile. Thus Tₘ=Fₘ₊₁; the index shift is essential.',r'Q=\begin{pmatrix}1&1\\1&0\end{pmatrix},\quad Q\binom{F_{n+1}}{F_n}=\binom{F_{n+2}}{F_{n+1}}'),
p('Multiply transformations to obtain an addition law', 'Induction on n≥1 gives Qⁿ with entries Fₙ₊₁,Fₙ in its first row and Fₙ,Fₙ₋₁ in its second. The base n=1 is Q itself. Multiplication by Q adds neighboring Fibonacci entries and proves the next case.\n\nUse Qᵐ⁺ⁿ=QᵐQⁿ. Comparing an off-diagonal entry yields Fₘ₊ₙ=FₘFₙ₊₁+Fₘ₋₁Fₙ for m≥1,n≥0. It is a theorem for arbitrary indices, not a pattern guessed from a few values. The n=0 case reduces to Fₘ=Fₘ·1+Fₘ₋₁·0.',r'F_{m+n}=F_mF_{n+1}+F_{m-1}F_n'),
p('A determinant explains the alternating sign', 'The determinant of Q is −1. Determinants multiply, so det(Qⁿ)=(−1)ⁿ. Substituting its Fibonacci entries gives Cassini’s identity Fₙ₊₁Fₙ₋₁−Fₙ²=(−1)ⁿ for n≥1. The two diagonal products in the scene differ by precisely one, with a sign that alternates at each matrix step.\n\nAt n=1 this reads 1·0−1²=−1. The formula as written uses Fₙ₋₁, so n=0 is excluded unless negative-index Fibonacci numbers are introduced. Q⁰ is the identity matrix and needs no negative-index convention.',r'F_{n+1}F_{n-1}-F_n^2=(-1)^n\quad(n\ge1)'),
p('Extract consequences without erasing their hypotheses', 'Any common divisor of Fₙ and Fₙ₊₁ divides the left side of Cassini’s identity and hence divides 1. Thus consecutive Fibonacci numbers are coprime. The determinant argument does not claim that every pair is coprime; F₆=8 and F₉=34 have gcd 2.\n\nA tiling proof of an addition identity must distinguish whether a double tile crosses the chosen seam. Ignoring the crossing case loses arrangements. The matrix proof packages both possibilities in the two terms of the product.',r'\gcd(F_n,F_{n+1})=1\quad(n\ge0)')],
q('Using the addition law, what is F₇ if F₃=2,F₄=3,F₅=5?', ['2·5+1·3=13','3·5=15','2+5=7'],0,'Take m=3,n=4: F₇=F₃F₅+F₂F₄=2·5+1·3=13.'),
q('At n=2, what is the determinant F₃F₁−F₂²?', ['−1','0','1'],2,'2·1−1²=1=(−1)².'),'Use matrix powers one through three so every count is small and the alternating determinant is clear.')
lesson(45,'154–156',[
p('Run Euclid on the indices, track a different invariant', 'For nonnegative m,n, not both zero, the Fibonacci gcd theorem states gcd(Fₘ,Fₙ)=F_gcd(m,n). The display runs Euclid on (m,n); beneath each index it computes the corresponding Fibonacci value. The index remainders are not claimed to be the remainders of the values.\n\nWith indices 15 and 9, the index chain is (15,9),(9,6),(6,3),(3,0). The value pairs are (610,34),(34,8),(8,2),(2,0). Every pair has value gcd 2, although 610 mod 34=32 is not F₆=8.',r'\gcd(F_m,F_n)=F_{\gcd(m,n)}'),
p('Use the addition identity to preserve common divisors', 'For m≥1 and n≥0, Fₘ₊ₙ=FₘFₙ₊₁+Fₘ₋₁Fₙ. For n≥1, Fₙ is positive, and modulo Fₙ this is Fₘ₊ₙ≡FₘFₙ₊₁. Consecutive Fibonacci numbers Fₙ,Fₙ₊₁ are coprime, so multiplying by Fₙ₊₁ does not change the gcd with Fₙ. Hence gcd(Fₘ₊ₙ,Fₙ)=gcd(Fₘ,Fₙ).\n\nRepeatedly subtract n from the larger index m to obtain gcd(Fₘ,Fₙ)=gcd(Fₘ mod ₙ,Fₙ), where the subscript denotes the Fibonacci number at the index remainder. To avoid ambiguous typography, read this as “F at (m modulo n).”',r'\gcd(F_{m+n},F_n)=\gcd(F_m,F_n)'),
p('Finish at zero and recover the theorem', 'Euclid’s algorithm on nonnegative indices reaches (d,0), where d=gcd(m,n). The preserved value gcd is then gcd(F_d,F₀)=gcd(F_d,0)=F_d, proving the result. When one initial index is zero, the same endpoint argument applies immediately. If both are zero, one may extend the theorem by defining gcd(0,0)=0; our main claim excludes that pair to avoid a convention dispute.\n\nAs a consequence, if a positive integer d divides n, then F_d divides Fₙ. The converse needs care at the repeated small values F₁=F₂=1; divisibility of values does not always identify divisibility of indices.',r'\gcd(F_m,F_n)=\gcd(F_{m\bmod n},F_n)\quad(n>0)'),
p('Distinguish an invariant from an equality of remainders', 'Preserving a gcd is weaker than preserving an individual number or a numerical remainder. The counterexample in the opening trace is intentional: F₁₅ mod F₉=32, while F_(15 mod 9)=F₆=8. Both 32 and 8 have gcd 2 with F₉=34, which is exactly what the proof needs.\n\nInteger arithmetic is used throughout; no rounded Binet values enter the gcd. A single off-by-one or floating error could change divisibility completely. The independent tests compare the theorem with ordinary integer gcd for many index pairs.',r'F_{m\bmod n}\ne F_m\bmod F_n\quad\text{in general}')],
q('What is gcd(F₁₂,F₁₈), given F₆=8?', ['F₃₀','6','8'],2,'gcd(12,18)=6, so the theorem gives F₆=8. The gcd of indices is not itself the value gcd.'),
q('For indices (6,4), why does the endpoint (2,0) give value gcd 1?', ['Because F₂=1 and F₀=0','Because 2 and 0 have gcd 1','Because every Fibonacci pair is coprime'],0,'The endpoint value pair is (F₂,F₀)=(1,0), whose gcd is 1.'),'Use indices 6 and 4; only two Euclidean reductions are needed.')
lesson(46,'156–158',[
p('Package a recurrence as coefficients', 'Let G(z)=Σₙ≥₀Fₙzⁿ. Treat this first as a formal power series: it is a sequence of coefficients, and multiplication is defined coefficient by coefficient. Subtract zG and z²G from G. Every coefficient of degree at least 2 vanishes by the recurrence, the constant term is zero, and the coefficient of z is one. Therefore (1−z−z²)G=z.\n\nSince the denominator has nonzero constant coefficient, it has a unique formal-series inverse. No analytic convergence claim is needed for this algebraic derivation. As an analytic series, G converges for |z|<1/φ, where φ=(1+√5)/2 is the positive root of r²=r+1.',r'G(z)=\frac z{1-z-z^2}'),
p('Split the denominator into two geometric streams', 'Let φ=(1+√5)/2 and ψ=(1−√5)/2. They satisfy φ+ψ=1, φψ=−1, and each root obeys r²=r+1. Factoring the denominator and using partial fractions gives G(z)=(1/√5)(1/(1−φz)−1/(1−ψz)). Taking the coefficient of zⁿ gives Binet’s formula.\n\nIndependently verify it: at n=0 the numerator is zero; at n=1 it is √5; and both root powers satisfy the Fibonacci recurrence. A second-order recurrence with those two initial values has a unique sequence, so the formula holds for every n≥0.',r'F_n=\frac{\phi^n-\psi^n}{\sqrt5}'),
p('A small exact error makes nearest-integer recovery possible', 'Because |ψ|<1, the exact real number φⁿ/√5 differs from Fₙ by |ψ|ⁿ/√5≤1/√5<1/2 for n≥0. Thus Fₙ is the nearest integer to φⁿ/√5. The scene draws the leading term near the exact integer and shows the correction from the second root; the drawn coordinates use rounded floats, while the integer label comes from the recurrence.\n\nThe error bound concerns exact real arithmetic. It does not bound the numerical error introduced by storing φ and repeatedly raising an approximation to powers.',r'\left|F_n-\frac{\phi^n}{\sqrt5}\right|=\frac{|\psi|^n}{\sqrt5}<\frac12'),
p('Floating computation can invalidate the rounding shortcut', 'A floating approximation to φ has a small relative error, but exponentiation magnifies it. Eventually the resulting absolute error exceeds half a unit, and rounding produces the wrong integer. The model’s separate precision check compares the ordinary double-precision expression with exact Fibonacci recurrence values and records an actual mismatch; it does not hide the failure behind the theorem.\n\nFor reliable large integers, use the integer recurrence or a tested fast-doubling method. If using high-precision real arithmetic, carry a certified numerical error bound in addition to the exact ψ correction. Algebraic exactness and machine accuracy are different obligations.',r'\text{total error}\le\text{numerical error}+|\psi|^n/\sqrt5')],
q('A computed approximation to φⁿ/√5 has certified numerical error 0.3, while |ψ|ⁿ/√5<0.1. Is rounding guaranteed to recover Fₙ?', ['Yes, because total error is <0.4<1/2','No approximation can ever be rounded safely','Yes, regardless of the numerical error'],0,'Triangle inequality bounds its distance to the exact integer by less than 0.4. Both sources of error must be included.'),
q('Why do the two root streams cancel at n=0?', ['Both zeroth powers are 1, so their difference is 0','Both roots are 0','The smaller root is discarded'],0,'Binet uses (φ⁰−ψ⁰)/√5=(1−1)/√5=0. Dropping the second root would not give the exact value.'),'Use n=1,2,3 and compare the small signed correction with the nearby exact integer.')

def grid_states(title,rows,labels,formula,caption,kind='coefficient-grid'):
 """A computed matrix with row/column ownership, not a register listing."""
 states=[];height=min(65,270/max(1,len(rows)));width=min(220,600/max(1,max(map(len,rows))));ox=(720-width*max(map(len,rows)))/2
 for t in range(3):
  nodes=[txt('head',360,45,title,size=18)]
  for i,row in enumerate(rows):
   for j,v in enumerate(row):
    output=(j==len(row)-1)
    revealed=not output or t==2 or (t==1 and i==0)
    display=str(v) if revealed else '?'
    role='result' if output and revealed else 'active' if t==1 and i==0 else 'input'
    nodes+=[rect(f'cell-{i}-{j}',ox+j*width,85+i*height,width-8,height-10,role),txt(f'cell-{i}-{j}-label',ox+j*width+(width-8)/2,85+i*height+(height-10)/2+5,display,role,14 if len(display)>11 else 17)]
  nodes+=[txt('axis',360,385,labels,size=15)]
  states.append(state(t,caption[t],formula,nodes,'Each cell has its declared row and column index.',dict(kind=kind,rows=[[str(v) for v in row] for row in rows])))
 return states

def numberline_states(title,values,labels,formula,caption):
 low=min(float(v) for v in values)-.5;high=max(float(v) for v in values)+.5
 S=[]
 for upto in range(1,len(values)+1):
  nodes=[txt('head',360,55,title),line('axis',70,240,650,240)]
  for j,v in enumerate(values):
   x=70+(float(v)-low)/(high-low)*580;y=240
   nodes+=[dot(f'point{j}',x,y,'active' if j==upto-1 else 'input' if j<upto else 'muted'),line(f'leader{j}',x,y,105+j*510/max(1,len(values)-1),310+(j%2)*50),txt(f'label{j}',105+j*510/max(1,len(values)-1),334+(j%2)*50,labels[j],size=14)]
  S.append(state(upto,caption[min(upto-1,len(caption)-1)],formula,nodes,'Positions are computed from the displayed numerical values.',dict(values=[str(v) for v in values],revealed=upto)))
 return S

def supplemental(order,boundary=False,small=False):
 """Focused proof witnesses or counterexamples, independently computed from main scenes."""
 if order==21:
  if boundary:
   S=[]
   for t in range(3):
    nodes=[dot('loop',360,210,'active',65),txt('state',360,217,'odd CHECK'),dict(id='loop-arrow',type='path',d='M 405 158 C 570 65 570 360 408 260',fill='none',role='error'),txt('count',360,370,f'{t} transitions; the complete state is unchanged')]
    S.append(state(t,'An effective self-loop never reaches DONE.',r'f(1,\mathrm{CHECK},0)=(1,\mathrm{CHECK},0)',nodes,'A repeated nonterminal snapshot repeats its future.',dict(waiting=1,pc='CHECK',output=0,step=t)))
   return S
  n=1 if small else 3;seq=[];q0=(n,'CHECK',0)
  while q0[1]!='DONE':seq.append(q0);q0=snapshot_step(q0)
  seq.append(q0);S=[]
  for upto in (0,len(seq)//2,len(seq)-1):
   nodes=[txt('head',360,45,'A nonnegative rank falls at every active step')]
   for j,(a,c,o) in enumerate(seq):
    rank=2*a+(c=='CHECK') if c!='DONE' else 0;x=70+j*560/max(1,len(seq)-1);y=330-rank*30
    nodes+=[rect(f'bar{j}',x, y,45,330-y,'result' if j<=upto else 'muted'),txt(f'r{j}',x+22,y-10,rank),txt(f's{j}',x+22,360,j,size=14)]
   S.append(state(upto,f'Rank witness through transition {upto}.',r'R(n,C)=2n+1,\quad R(n,M)=2n',nodes,'No infinite strictly decreasing sequence of nonnegative integers exists.',dict(ranks=[2*a+(c=='CHECK') if c!='DONE' else 0 for a,c,o in seq])))
  return S
 if order==22:
  if boundary:
   S=[]
   for t in range(3):
    word='a'*(t+1);nodes=[txt('rule',360,60,'Rule: first a → aa, return to rule 0')]
    for j in range(t+1):nodes+=tile(f'a{j}',160+j*105,175,'a','active' if j==0 else 'input',70)
    nodes+=[txt('length',360,340,f'Length {len(word)}; a match still exists')]
    S.append(state(t,'A finite effective rule can keep growing forever.',r'|\sigma_{t+1}|=|\sigma_t|+1',nodes,'Input a always has another a to replace.',dict(word=word,control=0)))
   return S
  word='ab' if small else 'aabb';S=[]
  for t in range(4):
   pairs=[(i,j) for i in range(len(word)) for j in range(i+1,len(word)) if word[i]=='a' and word[j]=='b'];nodes=[txt('head',360,45,'Count a-before-b pairs, not just adjacent matches')]
   for i,j in pairs:nodes+=[dict(id=f'pair{i}-{j}',type='path',d=f'M {170+i*100} 215 Q {170+(i+j)*50} {70+15*(j-i)} {170+j*100} 215',fill='none',role='active')]
   for j,c in enumerate(word):nodes+=tile(f'letter{j}',140+j*100,230,c,'input',60)
   nodes+=[txt('count',360,365,f'V = {len(pairs)}')];S.append(state(t,f'{word} has {len(pairs)} a-before-b pairs.',fr'V(\sigma)={len(pairs)}',nodes,'One adjacent ab→ba swap removes exactly one such pair.',dict(word=word,pairs=pairs,V=len(pairs))))
   word,j=rewrite_step(word,0)
   if j:break
  return S
 if order==23:
  if boundary:return grid_states('A step of −2 preserves parity',([[4,6],[5,7]] if small else [[4,6,8],[5,7,9]]),'Top row has base 4; bottom row needs base 5',r'n\mapsto n-2',['Two residue classes need support.','A proof starting at 4 reaches only even cases.','An odd base or another reduction is necessary.'])
  vals=[8,9,10] if small else [8,9,10,11,12,13];S=[]
  for upto in (1,3,len(vals)):
   nodes=[txt('head',360,40,'Build amounts from 3-unit and 5-unit pieces')]
   for i,n in enumerate(vals):
    a,b=next((a,b) for a in range(n//3+1) for b in range(n//5+1) if 3*a+5*b==n);nodes+=[txt(f'amount{i}',65,95+i*50,n)]
    x=110
    for j,v in enumerate([3]*a+[5]*b):nodes+=[rect(f'piece{i}-{j}',x,68+i*50,v*27,33,'input' if i<upto else 'muted'),txt(f'label{i}-{j}',x+v*13.5,90+i*50,v,size=14)];x+=v*27+6
   S.append(state(upto,'Three bases allow an arbitrary later case to subtract 3.',r'n\ge11\Rightarrow n-3\ge8',nodes,'Each row has total length equal to its amount.',dict(amounts=vals)))
  return S
 if order==24:
  if boundary:return numberline_states('Principal angles: a full turn returns to zero',[0,pi,2*pi],['Log(1): 0','Log(−1): πi','twice Log(−1): 2πi'],r'\operatorname{Log}((-1)^2)\ne2\operatorname{Log}(-1)',['One positive real has angle zero.','A negative real has principal angle π.','The sum differs by a full turn; literal log additivity fails.'])
  z=(1,1) if small else (2,1);a,b=z;u,v=a-b,a+b
  return grid_states('Squared lengths before and after multiplication',[[a*a,b*b,a*a+b*b],[u*u,v*v,u*u+v*v]],'columns: real², imaginary², their sum',r'|z(1+i)|^2=2|z|^2',['Compute two perpendicular square areas.','Multiply coordinates by 1+i.','The total squared length doubles.'])
 if order==25:
  if boundary:
   rows=[[('✓' if j<=i else '×') for j in range(1,4)] for i in range(1,4)]
   return grid_states('Which index pairs are actually legal?',rows,'Rows i=1,2,3; columns j=1,2,3',r'1\le j\le i\le3',['The triangle excludes the upper-right cells.','Pair (1,3) is not in the original sum.','Keeping old bounds after swapping can add illegal cells.'])
  a=[2,3] if small else [2,4];b=[1,3] if small else [1,3,5];rows=[[x*y for y in b] for x in a]
  return grid_states('Every pair contributes one product',rows,'Each row selects a factor from the first sum',fr'({"+".join(map(str,a))})({"+".join(map(str,b))})={sum(a)*sum(b)}',['Distribute the first row of products.','The second row has its own first-factor choice.','All cells sum to the product of the two sums.'])
 if order==26:
  if boundary:
   return grid_states('Zero weight does not define division by zero',([[0,'undefined'],[1,'1']] if small else [[0,'undefined'],[1,'1'],[2,'1/2']]),'columns: x, 1/x; the x=0 cell has no value',r'g(0)=0\text{ must be defined separately}',['Identify the point where division fails.','A bracket does not turn undefined into a number.','Define the zero branch before evaluating a quotient.'])
  return grid_states('Check all four truth pairs',([[0,1,0,1],[1,1,1,1]] if small else [[0,0,0,0],[0,1,0,1],[1,0,0,1],[1,1,1,1]]),'columns: [A], [B], [A and B], [A or B]',r'[A\lor B]=[A]+[B]-[A\land B]',['List all truth possibilities.','Only the last row has an overlap.','Subtracting the overlap gives the correct union in every row.'])
 if order==27:
  if boundary:return grid_states('The endpoints also handle empty and one-term sums',([[0,0,0],[1,F(1,2),F(1,2)]] if small else [[0,0,0],[1,F(1,2),F(1,2)],[2,F(2,3),F(2,3)]]),'columns: n, direct sum, 1−1/(n+1)',r'\sum_{k=1}^{0}\frac1{k(k+1)}=0',['At n=0 no terms are visited.','At n=1 the one reciprocal is 1/2.','The same endpoint formula covers both.'])
  n=3 if small else 5
  return grid_states('Summation by parts with aₖ=bₖ=k',[[k,k+1,1,k,k+1] for k in range(n)],'columns: k, b(k+1), Δa, aΔb, b(k+1)Δa',fr'\sum_{{k=0}}^{{{n-1}}}k={n*n}-\sum_{{k=0}}^{{{n-1}}}(k+1)', ['Expand each product difference.','The correction uses b(k+1), not b(k).','Endpoint n² minus the correction gives the weighted sum.'])
 if order==28:
  if boundary:return grid_states('Defined products and forbidden quotients',[["empty",1],["2·0·3",0],["2/0","undefined"]],'An empty product is a neutral value, not a failed division',r'\prod_{k\in\varnothing}a_k=1',['No factors leaves the multiplicative identity.','A defined zero factor makes the product zero.','Division by zero does not produce either value.'])
  return grid_states('A product of sums includes mixed choices',[[2*5,2*7],[3*5,3*7]],'row choices 2 or 3; column choices 5 or 7',r'(2+3)(5+7)=10+14+15+21=60',['Choose one number from each parenthesis.','The mixed choices are distinct cells.','The diagonal alone would omit two products.'])
 if order==29:
  if boundary:
   rows=[[2**j,2**j,F(1,2**(j+1)),F(1,2)] for j in range(2 if small else 3)]
   return grid_states('Harmonic blocks cannot shrink below one half',rows,'columns: block start, count, lower height, lower area',r'\sum_{k=2^j+1}^{2^{j+1}}\frac1k\ge\frac12',['Each block contains twice as many terms as the previous.','Its terms are at least the last reciprocal in that block.','Every complete block adds at least one half.'])
  n=4 if small else 6;vals=[sum((F((-1)**(k-1),k) for k in range(1,j+1)),F(0)) for j in range(1,n+1)]
  return numberline_states('Alternating harmonic partial sums bracket a limit',vals,[str(v) for v in vals],r'|R_n|\le1/(n+1)',['Odd sums lie above the eventual limit.','Even sums lie below it.','The gap between consecutive bounds tends to zero.'])
 if order==30:
  if boundary:return numberline_states('Crossing a fence by one tenth',[F(-21,10),F(-2),F(-19,10)],['floor −3','floor −2','floor −2'],r'\lfloor-2\rfloor=-2',['Left of −2, floor is −3.','Exactly at −2, floor changes to −2.','Just right of −2, floor remains −2.'])
  a,b=(F(1,4),F(1,2)) if small else (F(3,4),F(2,3));S=[]
  for stage in range(3):
   nodes=[txt('head',360,45,'Fractional parts can create one integer carry'),rect('unit',80,110,360,70,'muted',fill='none'),rect('partA',80,110,360*float(a),70,'input'),rect('partB',80+(360*float(a) if stage else 0),110 if stage else 240,360*float(b),70,'active'),line('fence',440,90,440,325,'result'),txt('total',360,380,f'{a}+{b}={a+b}; carry = {floor(a+b)}')]
   S.append(state(stage,['Start with two fractional lengths.','Place them end to end.','Crossing the unit fence contributes one to the floor.'][stage],fr'\lfloor {a}+{b}\rfloor={floor(a+b)}',nodes,'The sum of two fractional parts lies in [0,2).',dict(a=str(a),b=str(b),sum=str(a+b),carry=floor(a+b))))
  return S
 if order==31:
  if boundary:return grid_states('A negative real divisor changes the remainder interval',[[x,-3,floor(F(x,-3)),F(x)-(-3)*floor(F(x,-3))] for x in (-5,-1,0,4)],'columns: x, y, floor(x/y), x mod y',r'-3<x\bmod(-3)\le0',['Use the same floor-based definition.','The remainder has the divisor’s sign or is zero.','These bounds differ from the positive-modulus convention.'])
  m=6;a=2;rows=[[k,a*k%m] for k in range(m)]
  return grid_states('Multiplication by 2 collides modulo 6',rows,'columns: original residue, reduced doubled residue',r'2\cdot1\equiv2\cdot4\pmod6,\quad1\not\equiv4\pmod6',['Compute every image, including zero.','Inputs separated by 3 collide.','Cancellation keeps only congruence modulo 3.'])
 if order==32:
  if boundary:
   a,m=2,341;rows=[];v=a%m
   for j in range(9):rows.append([2**j,v]);v=v*v%m
   return grid_states('Repeated squaring exposes a composite false positive',rows,'columns: exponent, 2^exponent mod 341',r'341=11\cdot31,\quad2^{340}\bmod341=1',['Square residues to build binary powers.','340=256+64+16+4 combines four rows.','The final residue is 1 despite the composite modulus.'])
  r,s,u,v=(3,4,1,2) if small else (5,3,2,1);N=r*s;S=[]
  for stage in range(3):
   nodes=[txt('head',360,45,f'Align residues {u} mod {r} and {v} mod {s}')]
   for k in range(N):
    x=50+(k%8)*82;y=115+(k//8)*115;aa=k%r==u;bb=k%s==v
    nodes+=tile(f'candidate{k}',x,y,k,'result' if aa and bb and stage==2 else 'active' if (aa if stage==0 else bb) else 'muted',55)
   solution=next(k for k in range(N) if k%r==u and k%s==v)
   S.append(state(stage,[f'The first condition retains integers with remainder {u} modulo {r}.',f'The second condition retains integers with remainder {v} modulo {s}.','The common cell satisfies both remainder conditions.'][stage],fr'x\equiv{solution}\pmod{{{N}}}',nodes,'Exactly one representative in 0,…,rs−1 solves both.',dict(r=r,s=s,u=u,v=v,solution=solution)))
  return S
 if order==33:
  if boundary:return grid_states('Slot counts at the domain boundaries',[[n,k,len(list(permutations(range(n),k)))] for n,k in ((0,0),(3,0),(3,3),(3,4))],'columns: objects n, slots k, enumerated outcomes',r'P(n,0)=1,\quad P(n,k)=0\ (k>n)',['Empty selection is one outcome.','Full arrangements use every label.','Too many slots have no injective outcome.'])
  word='AAB' if small else 'AABB';words=sorted(set(permutations(word)));rows=[[''.join(w),prod(factorial(word.count(c)) for c in set(word))] for w in words]
  return grid_states('Equal-size groups of labeled arrangements',rows,'columns: visible word, number of hidden identity orders',fr'{len(word)}!/{prod(factorial(word.count(c)) for c in set(word))}={len(words)}',['List each visible multiset word once.','Every word has the same number of labeled preimages.','The common fiber size justifies division.'])
 if order==34:
  if boundary:return grid_states('Composite factors do not have additive valuations',[[2,0],[2,0],[4,1]],'columns: number, largest exponent e with 4^e dividing it',r'\nu_4(2)+\nu_4(2)=0\ne1=\nu_4(4)',['Each factor 2 contains no whole factor 4.','Their product does contain a factor 4.','The prime valuation proof cannot use base 4 unchanged.'])
  ns=[2,3,4] if small else [4,8,12];rows=[]
  for n in ns:
   L=sqrt(2*pi*n)*(n/exp(1))**n;rows.append([n,str(factorial(n)),f'{L:.4g}',f'{abs(L-factorial(n))/factorial(n):.5f}'])
  return grid_states('Relative error is different from absolute error',rows,'columns: n, exact n!, leading estimate, relative error',r'L_n=\sqrt{2\pi n}(n/e)^n',['Compare the estimate against exact integer factorial.','The missed integer amount need not decrease.','Relative error shrinks even while absolute size grows.'])
 if order==35:
  if boundary:
   vals=[F(1),F(5,4),F(2)] if small else [F(1),F(5,4),F(3,2),F(7,4),F(2)];rows=[[str(x),f'{exp(.2*__import__("math").sin(2*pi*float(x))):.5f}'] for x in vals]
   return grid_states('A periodic multiplier preserves the recurrence',rows,'columns: x, h(x)=exp(0.2 sin(2πx))',r'G(x)=h(x)\Gamma(x),\quad h(x+1)=h(x)',['At integers the multiplier is 1.','Between integers it differs from 1.','Recurrence and integer agreement therefore do not imply uniqueness.'])
  rows=[];c=F(1)
  for j in range(3 if small else 4):rows.append([str(F(1,2)+j),str(c)+'√π']);c*=F(1,2)+j
  return grid_states('Half-integer gamma values share one exact base',rows,'columns: x, Γ(x), assuming Γ(1/2)=√π',r'\Gamma(x+1)=x\Gamma(x)',['Begin at the separately established Gaussian value.','Multiply by the previous argument at each step.','The rational coefficient is exact.'])
 if order==36:
  if boundary:return grid_states('The product polynomial survives a gamma pole',[[2,0,1],[2,2,2],[2,3,0]],'columns: x, k, x falling k',r'2^{\underline3}=2\cdot1\cdot0=0',['At k=0 use the empty product.','At k=2 the ordinary finite product is defined.','At k=3 a zero factor is valid; Γ(0) is not a finite denominator.'])
  k=2 if small else 3;rows=[[x,falling(x,k),falling(x+1,k)-falling(x,k),k*falling(x,k-1)] for x in range(5)]
  return grid_states('A difference lowers factorial degree',rows,'columns: x, falling power, forward difference, k·lower power',fr'\Delta x^{{\underline{{{k}}}}}={k}x^{{\underline{{{k-1}}}}}', ['Compute neighboring falling products.','Subtract to form the difference.','Factoring proves equality with the lower-degree expression.'])
 if order==37:
  if boundary:return grid_states('Noninteger upper indices are polynomial values',[[k,str(choose(F(1,2),k))] for k in range(3 if small else 5)],'columns: integer k, C(1/2,k)',r'\binom{1/2}{2}=-\frac18',['Use the falling-product definition.','Negative coefficients are possible.','These values do not count literal subsets.'])
  n,k=(3,1) if small else (4,2);sets=list(combinations(range(1,n+1),k));rows=[[''.join(map(str,c)),('include '+str(n) if n in c else 'exclude '+str(n))] for c in sets]
  return grid_states('Partition subsets by one marked member',rows,'Every subset belongs to exactly one of the two cases',fr'\binom{{{n}}}{{{k}}}=\binom{{{n-1}}}{{{k}}}+\binom{{{n-1}}}{{{k-1}}}', ['Enumerate each subset once.','Ask whether the marked final member occurs.','Count the disjoint include and exclude cases.'])
 if order==38:
  z=F(1) if boundary else (F(1,3) if small else F(1,2));N=3 if small else 6;rows=[]
  for n in range(N):
   partial=sum(((-z)**k for k in range(n+1)),F(0));rows.append([n,str(partial),str(abs((-z)**(n+1)/(1+z)))])
  return grid_states('Boundary oscillation' if boundary else 'A controlled generalized binomial series',rows,'columns: last degree n, partial sum, exact tail magnitude',r'(1+z)^{-1}=\sum_{k\ge0}(-z)^k\quad(|z|<1)', ['Compute the finite geometric partial sum.','Keep its exact remainder instead of discarding it.','At z=1 the tail stays 1/2.' if boundary else 'Inside |z|<1 the tail tends to zero.'])
 if order==39:
  if boundary:return grid_states('Do not solve an identity by dividing by zero',[[3,3,str(choose(3,3)),0],[4,3,str(choose(4,3)),1]],'columns: r, k, C(r,k), r−k',r'(r-k)\binom rk=r\binom{r-1}k',['The polynomial coefficient at r=k is 1.','The division-free identity reads 0=0 there.','Its quotient form has denominator zero and is unavailable.'])
  n,m,k=(4,2,1) if small else (6,4,2)
  return grid_states('Count a nested pair of subsets in either order',[[comb(n,m),comb(m,k),comb(n,m)*comb(m,k)],[comb(n,k),comb(n-k,m-k),comb(n,k)*comb(n-k,m-k)]],'columns: first choices, second choices, total nested pairs',fr'\binom{{{n}}}{{{m}}}\binom{{{m}}}{{{k}}}=\binom{{{n}}}{{{k}}}\binom{{{n-k}}}{{{m-k}}}', ['Choose the larger subset, then the smaller.','Reverse the choice order.','The same nested objects have equal totals.'])
 if order==40:
  if boundary:
   r,s,n=F(1,2),F(3,2),3;rows=[[k,str(choose(r,k)),str(choose(s,n-k)),str(choose(r,k)*choose(s,n-k))] for k in range(n+1)]
   return grid_states('A polynomial convolution beyond subset counting',rows,'columns: k, C(1/2,k), C(3/2,3−k), product',r'\sum_{k=0}^{3}\binom{1/2}k\binom{3/2}{3-k}=\binom23=0',['Compute coefficients by falling products.','Some contributions are negative.','They cancel to zero; a subset story is not the justification.'])
  r,s,n=(2,1,2) if small else (2,3,3);sets=list(combinations(range(r+s),n));rows=[[ ''.join(chr(65+j) for j in c),sum(j<r for j in c)] for c in sets]
  return grid_states('Every subset determines exactly one split count',rows,'columns: chosen subset, members from the first group',fr'\#\text{{subsets}}=\binom{{{r+s}}}{{{n}}}={len(sets)}',['Enumerate the union’s subsets independently.','Compute k from the subset itself.','Grouping by k recovers the product-sum cases.'])
 if order==41:
  if boundary:
   n=3;return grid_states('Signed first-kind coefficients undo the basis change',[[k,stirling(n,k,True),(-1)**(n-k)*stirling(n,k,True)] for k in range(n+1)],'columns: k, unsigned c(3,k), signed coefficient',r'x^{\underline3}=x^3-3x^2+2x',['Count unsigned cycle coefficients.','Apply the alternating sign (−1)^(n−k).','The resulting polynomial equals x(x−1)(x−2).'])
  n=2 if small else 3;parts=list(partitions(n));S=[]
  for stage in range(3):
   nodes=[txt('head',360,40,'Partition labeled objects into unlabeled nonempty blocks')]
   for row,blocks in enumerate(parts):
    x=90
    for b,block in enumerate(blocks):
     nodes+=[rect(f'block{row}-{b}',x,75+row*60,45*len(block)+10,45,'active' if stage==1 and len(blocks)==2 else 'input',fill='none')]
     for pos,v in enumerate(block):nodes+=[dot(f'object{row}-{v}',x+28+pos*45,98+row*60,'input',14),txt(f'label{row}-{v}',x+28+pos*45,104+row*60,chr(65+v),size=14)]
     x+=45*len(block)+25
    nodes+=[txt(f'k{row}',570,104+row*60,f'{len(blocks)} blocks',size=14)]
   S.append(state(stage,'A block partition is counted once, regardless of block order.',fr'S({n},k)\text{{ counts nonempty block partitions}}',nodes,'Blocks are canonically ordered by their smallest member.',dict(partitions=parts,counts=[sum(len(b)==k for b in parts) for k in range(n+1)])))
  return S
 if order==42:
  if boundary:
   ns=[1,2,3] if small else [1,2,4,8];vals=[float(harmonic(n))-log(n) for n in ns]
   return numberline_states('The harmonic-logarithmic offset decreases',vals,[f'n={n}: {v:.4f}' for n,v in zip(ns,vals)],r'H_n-\ln n\downarrow\gamma',['The first offset is 1.','Increasing n lowers the offset.','The finite values illustrate the proved monotone bound.'])
  n=2 if small else 4;S=[]
  for stage in range(3):
   nodes=[txt('left-title',180,50,'left endpoints'),txt('right-title',520,50,'right endpoints'),line('left-axis',50,290,310,290),line('right-axis',390,290,650,290)]
   for k in range(1,n+1):nodes+=[rect(f'leftbar{k}',50+(k-1)*240/n,290-140/k,240/n,140/k,'active' if stage!=1 else 'muted')]
   for k in range(2,n+1):nodes+=[rect(f'rightbar{k}',390+(k-2)*240/(n-1),290-140/k,240/(n-1),140/k,'active' if stage else 'muted')]
   for side,T,ox,w in [('left',n+1,50,240/n),('right',n,390,240/(n-1))]:
    path='M '+' L '.join(f'{ox+w*(t-1):.2f},{290-140/t:.2f}' for t in [1+(T-1)*j/100 for j in range(101)])
    nodes+=[dict(id=side+'-curve',type='path',d=path,fill='none',role='input')]
   nodes+=[txt('left-bound',180,350,f'ln({n+1}) ≤ H{n}'),txt('right-bound',520,350,f'H{n} − 1 ≤ ln({n})'),txt('both',360,400,f'H{n} = {harmonic(n)} exactly')]
   S.append(state(stage,['The left-endpoint rectangles lie above the curve.','The right-endpoint rectangles from k=2 lie below it.','Integrating both comparisons gives the two logarithmic bounds.'][stage],fr'\ln({n+1})\le H_{{{n}}}\le1+\ln({n})',nodes,'A decreasing positive function is bracketed by endpoint rectangles.',dict(n=n,H=str(harmonic(n)),lower=log(n+1),upper=1+log(n))))
  return S
 if order==43:
  if boundary:
   ns=[1,2] if small else [2,3,4];rows=[[n,str(harmonic(n,2)),str(F(1,n+1)),str(F(1,n))] for n in ns]
   return grid_states('Reciprocal-square tails have shrinking bounds',rows,'columns: n, H_n^(2), lower tail, upper tail',r'\frac1{n+1}\le\zeta(2)-H_n^{(2)}\le\frac1n',['Compute exact finite reciprocal-square sums.','Integral comparison brackets the uncomputed tail.','Both bounds tend to zero; r=1 has no such finite tail.'])
  n=2 if small else 3;S=[]
  for stage in range(3):
   nodes=[txt('head',360,45,'Split the reciprocal-product square at its diagonal')]
   for i in range(1,n+1):
    for j in range(1,n+1):nodes+=tile(f'ij{i}-{j}',160+(j-1)*135,100+(i-1)*82,str(F(1,i*j)),'result' if i==j and stage==2 else 'active' if i>=j and stage>=1 else 'input',105,60)
   S.append(state(stage,['The whole square sums to H_n².','Select the lower triangle including its diagonal.','Add half the diagonal to half the square.'][stage],fr'\sum_{{k=1}}^{{{n}}}\frac{{H_k}}k=\frac{{H_{{{n}}}^2+H_{{{n}}}^{{(2)}}}}2',nodes,'Off-diagonal cells pair by transposition; diagonal cells have no distinct partner.',dict(n=n,square=str(harmonic(n)**2),diagonal=str(harmonic(n,2)),triangle=str(sum((harmonic(k)/k for k in range(1,n+1)),F(0))))))
  return S
 if order==44:
  if boundary:return grid_states('Consecutive pairs are special',[[0,1,gcd(fib(0),fib(1))],[fib(3),fib(4),gcd(fib(3),fib(4))],[fib(6),fib(9),gcd(fib(6),fib(9))]],'columns: first Fibonacci value, second value, gcd',r'\gcd(F_n,F_{n+1})=1',['Even the pair F₀,F₁ has gcd 1.','Consecutive values remain coprime.','A nonconsecutive pair can share a factor.'])
  n=3 if small else 4;ways=tilings(n);S=[]
  for stage in range(3):
   nodes=[txt('head',360,40,f'Length {n} walkway: split by its first plank')]
   for row,way in enumerate(ways):
    x=160
    for j,w in enumerate(way):nodes+=[rect(f'plank{row}-{j}',x,85+row*62,w*75-5,38,'active' if j==0 and stage else 'input'),txt(f'label{row}-{j}',x+(w*75-5)/2,110+row*62,w,size=14)];x+=w*75
   S.append(state(stage,'Single-first and double-first tilings are disjoint.',fr'T_{{{n}}}=T_{{{n-1}}}+T_{{{n-2}}}={len(ways)}=F_{{{n+1}}}',nodes,'Plank lengths in each row sum to the walkway length.',dict(n=n,tilings=ways,count=len(ways))))
  return S
 if order==45:
  if boundary:
   m,n=(6,4) if small else (15,9);r=m%n;rows=[[m,n,r],[fib(m),fib(n),fib(m)%fib(n)],[fib(m),fib(n),fib(r)]]
   return grid_states('The two remainder operations differ',rows,'rows: indices; numeric remainder; Fibonacci at index remainder',fr'F_{{{m}}}\bmod F_{{{n}}}={fib(m)%fib(n)}\ne {fib(r)}=F_{{{r}}}' if fib(m)%fib(n)!=fib(r) else fr'\gcd(F_{{{m}}},F_{{{n}}})={gcd(fib(m),fib(n))}', ['First reduce indices.','Separately reduce their Fibonacci values.','Only the gcd preservation is the theorem.'])
  a,b=(4,2) if small else (6,3);rows=[[fib(a+b),fib(b),gcd(fib(a+b),fib(b))],[fib(a)*fib(b+1),fib(b),gcd(fib(a)*fib(b+1),fib(b))],[fib(a),fib(b),gcd(fib(a),fib(b))]]
  return grid_states('Coprime neighboring values allow gcd cancellation',rows,'columns: first value, fixed F_n, gcd',r'\gcd(F_{m+n},F_n)=\gcd(F_mF_{n+1},F_n)=\gcd(F_m,F_n)',['Apply the addition identity modulo F_n.','The neighboring factor F_(n+1) is coprime to F_n.','Cancel that factor inside the gcd.'])
 if order==46:
  if boundary:
   phi=(1+sqrt(5))/2;bad=next(n for n in range(2,100) if round(phi**n/sqrt(5))!=fib(n));rows=[[n,str(fib(n)),str(round(phi**n/sqrt(5))),round(phi**n/sqrt(5))-fib(n)] for n in (bad-1,bad,bad+1)]
   return grid_states('An actual double-precision rounding failure',rows,'columns: n, exact recurrence, rounded float, integer error',r'\operatorname{round}(\widehat\phi^n/\widehat{\sqrt5})\text{ need not equal }F_n',['Compare against an independent integer recurrence.','The first tested mismatch is recorded, not concealed.','The exact nearest-integer theorem does not bound floating error.'])
  n=4 if small else 6;rows=[]
  for j in range(n+1):rows.append([j,fib(j),fib(j-1) if j>=1 else 0,fib(j-2) if j>=2 else 0,fib(j)-(fib(j-1) if j>=1 else 0)-(fib(j-2) if j>=2 else 0)])
  bridge=[];source_degree=2 if small else 3;coefficient=fib(source_degree);selected=source_degree+2;operands=[fib(selected),fib(selected-1),fib(selected-2)]
  for stage in range(4):
   nodes=[txt('head',360,35,'Multiplication by z changes degree, not coefficient.',size=17)]
   for d in range(n+1):nodes.append(txt(f'degree{d}',80+d*85,85,f'z^{d}',size=14))
   for row,shift in enumerate((0,1,2)):
    degree=source_degree+(shift if stage>=shift else 0);x=50+degree*85;y=115+row*72
    nodes += [txt(f'series{row}',35,y+27,['G','zG','z²G'][row],size=16)]
    for node in tile(f'shifted-F3-{row}',x,y,coefficient,'input' if row==0 else 'active',60,42):node['opacity']=0 if stage==3 else 1;nodes.append(node)
   if stage==3:
    for node in nodes:
     if node['id'].startswith(('degree','series')):node['opacity']=0
    for j,name in enumerate(('G','zG','z²G')):nodes.append(txt(f'selected-series{j}',210+j*145,128,name,size=17))
    for j,value in enumerate(operands):nodes+=tile(f'coefficient5-{j}',165+j*145,150,value,'active',90,60)
    nodes += [txt('minus1',290,186,'−',size=20),txt('minus2',435,186,'−',size=20),txt('result5',360,275,f'{operands[0]} − {operands[1]} − {operands[2]} = 0','result',20)]
    formula=fr'[z^{{{selected}}}](G-zG-z^2G)=F_{{{selected}}}-F_{{{selected-1}}}-F_{{{selected-2}}}={operands[0]}-{operands[1]}-{operands[2]}=0';caption=f'At degree {selected}, subtract the coefficients arriving from degrees {selected-1} and {selected-2}.'
   else:
    formula=[fr'F_{{{source_degree}}}z^{{{source_degree}}}={coefficient}z^{{{source_degree}}}',fr'z({coefficient}z^{{{source_degree}}})={coefficient}z^{{{source_degree+1}}}',fr'z^2({coefficient}z^{{{source_degree}}})={coefficient}z^{{{source_degree+2}}}'][stage];caption=[f'Start with coefficient F{source_degree}={coefficient} at degree {source_degree}.',f'Multiply by z: coefficient {coefficient} moves one degree right.',f'Multiply the original term by z²: coefficient {coefficient} moves two degrees right.'][stage]
   nodes.append(txt('shift-rule',360,391,caption,size=14))
   bridge.append(state(f'shift-{stage}',caption,formula,nodes,f'The coefficient remains {coefficient} during a degree shift; coefficient subtraction aligns equal powers of z.',dict(kind='coefficient-shift-bridge',stage=stage,coefficient=coefficient,sourceDegree=source_degree,targetDegrees=[source_degree,source_degree+1,source_degree+2],selectedDegree=selected,operands=operands,remainder=0)))
  return bridge+grid_states('Cancel coefficients in G−zG−z²G',rows,'columns: degree, G, zG, z²G, remaining coefficient',r'(1-z-z^2)G=z',['Shifts insert zero coefficients at the start.','Subtract matching degrees, not neighboring columns.','Only degree one survives.'])
 raise ValueError(order)

def partitions(n):
 if n==0:yield [];return
 for p0 in partitions(n-1):
  for i in range(len(p0)):
   p1=[b[:] for b in p0];p1[i].append(n-1);yield p1
  yield [b[:] for b in p0]+[[n-1]]
def tilings(n):
 if n==0:return [[]]
 return [[k]+tail for k in (1,2) if k<=n for tail in tilings(n-k)]

TARGETED={
21:[
q('For two waiting parcels at CHECK, what rank does the next MOVE state have?', ['5','4','2'],1,'CHECK has rank 2·2+1=5; MOVE has rank 2·2=4. The test changes the badge before moving a parcel.'),
q('In the one-parcel proof scene, which rank belongs to MOVE before the parcel moves?', ['2','1','0'],0,'MOVE with n=1 has rank 2n=2. The subsequent transfer reaches CHECK with rank 1.'),
q('A deterministic nonterminal state returns to itself. Can waiting longer make that same run halt?', ['Yes, if enough frames are shown','No, its future repeats the same state','Only if the input was even'],1,'A fixed nonterminal state stays fixed on every iteration. It never enters the terminal set.'),
q('After the displayed odd CHECK self-loop takes one more step, which object changes?', ['The badge becomes DONE','The tray empties','Nothing in the complete state'],2,'The transition maps the entire nonterminal snapshot to itself.')],
22:[
q('How many a-before-b pairs are in abab before its first rewrite?', ['2','3','4'],1,'The a at position 0 pairs with b at 1 and 3; the a at 2 pairs with b at 3. One adjacent swap removes exactly one of these three pairs.'),
q('In the small word ab, what happens to its pair count after replacing ab by ba?', ['It stays 1','It drops from 1 to 0','It rises to 2'],1,'The only a-before-b pair disappears; no new one is created.'),
q('Under a→aa with control returning to the same rule, what proves input a never halts?', ['Every word still contains a match','The alphabet is infinite','A finite rule cannot be executed'],0,'Every step preserves at least one a and adds another, so the no-match terminal branch is never taken.'),
q('From aa under the growth rule, what is the next word?', ['aaaa','a','aaa'],2,'Only the first a is replaced by aa; the other a remains.')],
23:[
q('Using 3-unit and 5-unit pieces, which earlier amount supports the induction step for 14?', ['11','9','14'],0,'Subtract one 3-unit piece: 14−3=11, which is smaller and at least the base threshold 8.'),
q('Which three base amounts are needed before repeatedly adding 3?', ['8 only','8,9,10','8,11,14'],1,'Consecutive bases 8,9,10 cover all residues modulo 3.'),
q('A proposed proof has only base P(5) and step P(n−2)→P(n). Which case remains unsupported?', ['7','9','6'],2,'Subtracting 2 preserves parity. The odd base cannot establish the even case 6.'),
q('On the two-row parity board, can a chain starting at 4 reach 7 by adding 2?', ['No, the parity stays even','Yes, after two additions','Yes, every increasing sequence reaches 7'],0,'Adding 2 preserves evenness, so an odd case needs another base.')],
24:[
q('If |z|²=13, what is |z(1+i)|²?', ['13','13√2','26'],2,'Squared magnitudes multiply, and |1+i|²=2.'),
q('For z=1+i, what is the squared magnitude after multiplying by 1+i?', ['2','4','8'],1,'The product is 2i, whose squared magnitude is 4.'),
q('Why can principal complex logarithms fail to add literally when two factors are multiplied?', ['Arguments may cross the chosen branch and differ by 2π','Complex multiplication is not associative','The magnitude formula fails'],0,'The product angle is reduced to the chosen principal interval, while the sum of principal angles may differ by a full turn.'),
q('Which number is principal Log(1)?', ['2πi','πi','0'],2,'The principal argument of 1 is zero and ln|1|=0.')],
25:[
q('In (2+5)(3+4), which contribution is omitted by keeping only 2·3 and 5·4?', ['2·4+5·3','2+5+3+4','Nothing'],0,'Distribution includes every pair, including the two off-diagonal mixed choices.'),
q('For the small rectangular grid (2+3)(1+3), how many pair cells exist?', ['2','4','6'],1,'There are two choices from each sum, giving a 2 by 2 product grid.'),
q('For 1≤j≤i≤4, is the pair (i,j)=(2,4) allowed?', ['Yes, because both indices are at most 4','No, because j exceeds i','Only after swapping the summation order'],1,'Reordering cannot change membership in the index set; 4≤2 is false.'),
q('In the three-row triangle, which corner is excluded?', ['(1,1)','(3,1)','(1,3)'],2,'The upper-right corner violates j≤i.')],
26:[
q('For truth values A=true and B=true, what weight counts exactly one of A and B?', ['2','1','0'],2,'Exactly one is false when both hold. The weight is 1+1−2·1=0.'),
q('In the four-case proof table, what is [A and B] when A is false and B true?', ['0','1','2'],0,'A conjunction is false unless both conditions are true.'),
q('Which definition safely assigns a value at x=0 while using 1/x elsewhere?', ['Evaluate [x≠0]/x at all x','Define g(0)=0 and g(x)=1/x only for x≠0','Assume 0/0=0'],1,'A piecewise definition avoids evaluating the undefined division on the zero branch.'),
q('Does multiplying an undefined quotient by zero make it defined?', ['Yes','No'],1,'Ordinary multiplication requires defined operands. The invalid expression must be avoided or separately defined.')],
27:[
q('With aₖ=k and bₖ=k for k=0,…,4, what is Σ from k=0 to 3 of aₖΔbₖ?', ['6','10','16'],0,'Δbₖ=1. Directly 0+1+2+3=6; by parts it is 16−(1+2+3+4)=6.'),
q('In the small by-parts scene, why does the correction use k+1?', ['Because b is evaluated at k+1 in the product identity','Because every sum starts at 1','Because k is never zero'],0,'Expanding Δ(aₖbₖ) yields aₖΔbₖ+bₖ₊₁Δaₖ.'),
q('What is Σ from k=0 to −1 of (bₖ₊₁−bₖ), with the empty-sum convention?', ['b₁−b₀','0','Undefined in every context'],1,'No indices are included. The endpoint identity at n=0 gives b₀−b₀=0.'),
q('For one term 1/[1·2], which endpoint formula is correct?', ['1−1/2','1−1/3','1/2−1/3'],0,'The first positive is 1 and the last negative is −1/2.')],
28:[
q('What is (1+4)(2+3) after every mixed choice is counted?', ['14','25','10'],1,'The four products are 2,3,8,12, totaling 25. The diagonal alone gives 14.'),
q('In the displayed 2×2 product grid, what does the upper-right cell represent?', ['2·7','3·5','2+7'],0,'The row selects 2 and the column selects 7. One cell represents their product.'),
q('Which expression is undefined in ordinary real arithmetic?', ['An empty product','2·0·3','2/0'],2,'An empty product is 1 and the product with a zero factor is 0. A zero denominator is not defined.'),
q('If a defined product contains a zero factor, what is its value?', ['1','0','Always undefined'],1,'Multiplication by zero is defined; division by zero is a separate issue.')],
29:[
q('For the alternating harmonic series, what bound suffices after 20 terms?', ['Tail magnitude ≤1/21','Tail magnitude ≤1/20²','The tail is exactly zero'],0,'Alternating decreasing terms give an error no larger than the first omitted term.'),
q('In the small alternating scene, which lies below the limit: S₂ or S₁?', ['S₁','S₂','Both are equal'],1,'S₁=1 is an upper bound, while S₂=1/2 is a lower bound.'),
q('Why do harmonic terms tending to zero not establish convergence?', ['A block can still contain enough terms to contribute at least 1/2','The terms eventually become negative','The partial sums are undefined'],0,'Dyadic blocks have growing lengths that offset their shrinking individual terms.'),
q('What lower total do four terms each at least 1/8 guarantee?', ['1/8','1/4','1/2'],2,'Four times 1/8 equals 1/2, exactly the block argument.')],
30:[
q('If fractional parts are 4/5 and 3/5, what extra carry enters floor(x+y)?', ['0','1','2'],1,'Their sum is 7/5, whose floor is 1. Two fractional parts sum to less than 2.'),
q('In the smaller 1/4+1/2 bar, is there an integer carry?', ['No, the total is 3/4','Yes, the total exceeds 1'],0,'The combined bar does not reach the unit fence.'),
q('What is floor(−3−1/10)?', ['−3','−4','3'],1,'−3.1 lies to the left of −3, in the interval [−4,−3).'),
q('At the exact fence −2, which floor interval owns the point?', ['[−3,−2)','[−2,−1)'],1,'Floor intervals include their left endpoint, so −2 belongs to the interval beginning at −2.')],
31:[
q('Which residues collide when multiplied by 3 modulo 8?', ['0 and 4','1 and 5','None'],2,'gcd(3,8)=1, so multiplication by 3 is invertible and has no collisions.'),
q('In the multiplication-by-2 modulo-6 scene, which input shares the image of 1?', ['2','3','4'],2,'2·1 mod 6=2 and 2·4 mod 6=2.'),
q('Under x mod y=x−y floor(x/y), what is 5 mod (−3)?', ['2','−1','−2'],1,'floor(5/−3)=−2, giving 5−(−3)(−2)=−1.'),
q('For a negative divisor y, which interval contains x mod y?', ['[0,−y)','(y,0]','[y,0)'],1,'Multiplying 0≤x/y−floor(x/y)<1 by negative y reverses the inequalities.')],
32:[
q('Which pair of requirements is incompatible?', ['x≡0 mod 4 and x≡1 mod 6','x≡1 mod 4 and x≡3 mod 6','x≡2 mod 3 and x≡1 mod 5'],0,'The first pair demands x be both even and odd. Noncoprime congruences must agree modulo their gcd.'),
q('For the small CRT scene x≡1 mod 3 and x≡2 mod 4, what is the solution in 0,…,11?', ['2','6','10'],2,'10 is 1 modulo 3 and 2 modulo 4; coprimality makes it unique modulo 12.'),
q('A composite N passes a Fermat test at one base. What may you conclude?', ['N is prime','That congruence alone does not prove primality','Every base will pass'],1,'A pseudoprime at one base is a counterexample to the converse of Fermat’s theorem.'),
q('Why is the displayed modulus 341 definitely composite?', ['Because 2³⁴⁰ mod 341=1','Because 341=11·31','Because it is odd'],1,'The explicit nontrivial factorization proves compositeness, regardless of the passing congruence.')],
33:[
q('How many visible words use the multiset A,A,A,B?', ['4','6','24'],0,'There are 4! labeled orders and 3! hidden permutations of the A identities per visible word, giving 4.'),
q('For A,A,B, how many labeled identity orders represent each visible word?', ['1','2','3'],1,'The two A identities can be swapped without changing the visible word.'),
q('How many injective arrangements fill all five ordered slots without reuse using only four distinct objects?', ['120','1','0'],2,'There are too few objects to fill every slot without reuse.'),
q('How many empty arrangements are there when zero slots are required?', ['0','1','It depends on n'],1,'The empty arrangement is one outcome for every n≥0.')],
34:[
q('An estimate misses an exact value 1,000,000 by 2,000. What is its relative error?', ['0.002','2,000','0.2'],0,'Relative error divides the absolute error by the exact magnitude: 2,000/1,000,000=0.002.'),
q('In the Stirling comparison, which quantity is divided by n! to get relative error?', ['The signed index n','The absolute difference between estimate and n!','The prime valuation'],1,'Relative error measures the miss as a fraction of the exact quantity.'),
q('Why does summing floor(n/4ʲ) not generally count all powers of 4 in n!?', ['Composite factors can form by combining 2s from different factors','4 has no divisors','Factorials cannot contain 4'],0,'The additive prime-exponent argument fails for a composite base: 2·2 creates a 4 even though neither factor contains one.'),
q('What is the exponent of 4 dividing the product 2·2?', ['0','1','2'],1,'2·2=4 has one factor of 4, despite each factor 2 having zero.')],
35:[
q('Given Γ(1/2)=√π, what rational multiplier of √π equals Γ(9/2)?', ['105/16','35/8','9/2'],0,'Multiply the successive arguments 1/2,3/2,5/2,7/2: their product is 105/16.'),
q('To move from Γ(3/2) to Γ(5/2), what factor is used?', ['5/2','3/2','1/2'],1,'Γ(x+1)=xΓ(x) uses the previous argument x=3/2.'),
q('What extra property in the stated classical characterization rules out arbitrary positive periodic multipliers?', ['Only agreement at integers','Only the recurrence','Logarithmic convexity, with positivity and normalization'],2,'The recurrence and integer values alone permit periodic modifications. The stated characterization requires the stronger shape condition.'),
q('If h has period 1, why does h(x)Γ(x) preserve the gamma recurrence?', ['Because h(x+1)=h(x)','Because h must be constant','Because Γ has no poles'],0,'The equal periodic factors appear on both sides of G(x+1)=xG(x).')],
36:[
q('What is Δ(x underlined 4)?', ['4x³','4(x underlined 3)','x underlined 3'],1,'Factoring neighboring falling products gives Δ(x underlined k)=k(x underlined k−1).'),
q('For the smaller k=2 proof, what is Δ(x underlined 2) at x=3?', ['3','6','9'],1,'The difference is 2x=6; directly 4·3−3·2=6.'),
q('How should 3 underlined 4 be evaluated at a gamma-quotient pole?', ['Use the finite product 3·2·1·0=0','Assign Γ(0)=1','Declare the polynomial undefined'],0,'The product definition is a polynomial and remains defined; an undefined gamma quotient is not the right evaluation route.'),
q('In 2 underlined 3, which factor makes the product zero?', ['2','1','0'],2,'The falling factors are 2,1,0.')],
37:[
q('How many 2-subsets of {1,2,3,4,5} exclude the marked member 5?', ['4','6','10'],1,'Choose two from the remaining four: C(4,2)=6.'),
q('In the small three-object singleton scene, how many subsets include marked member 3?', ['1','2','3'],0,'The only singleton containing 3 is {3}.'),
q('Why can C(1/2,2) be negative without contradicting subset counting?', ['Subset counts may be negative','The polynomial extension is not a literal subset count at noninteger upper index','Its value is undefined'],1,'The counting interpretation requires a nonnegative integer upper index; the algebraic extension has a larger domain.'),
q('Compute C(1/2,2) from its two falling factors.', ['1/8','−1/8','−1/4'],1,'(1/2)(−1/2)/2=−1/8.')],
38:[
q('For z=1/4 in the inverse binomial series, what is the exact tail magnitude after degrees 0 through 2?', ['1/80','1/64','1/16'],0,'The tail is z³/(1+z)=(1/64)/(5/4)=1/80.'),
q('For z=1/3, does the magnitude of the next term increase or decrease?', ['Increase by factor 3','Decrease by factor 1/3','Stay fixed'],1,'The inverse-series terms form a geometric sequence with magnitude ratio |z|=1/3.'),
q('At z=1, why does the inverse-series expansion fail to converge to 1/2?', ['Its partial sums alternate between 1 and 0','Its sum is a finite polynomial','The function value does not exist'],0,'The function value exists, but the series partial sums oscillate and have no limit.'),
q('At z=1, what is the exact distance from each partial sum 0 or 1 to 1/2?', ['0','1/4','1/2'],2,'The gap does not shrink, so the convergence criterion fails.')],
39:[
q('How many nested choices K⊂M⊂{1,…,5} with |K|=1, |M|=3 exist?', ['10','30','60'],1,'Choose M in C(5,3)=10 ways and K inside it in 3 ways, totaling 30.'),
q('In the smaller n=4,m=2,k=1 case, how many nested pairs occur?', ['6','8','12'],2,'Choose the pair in 6 ways and one of its two members in 2 ways.'),
q('At r=k=4, why cannot C(r,k)=rC(r−1,k)/(r−k) be evaluated directly?', ['C(4,4) is zero','The denominator is zero','The polynomial definition fails'],1,'C(4,4)=1 is defined, but this quotient form has denominator zero.'),
q('What does the division-free absorption equation say at r=k=3?', ['0=0','1=0','3=1'],0,'Both (r−k)C(r,k) and rC(r−1,k) vanish; it does not license division by r−k.')],
40:[
q('Which statistic assigns a selected subset to exactly one Vandermonde case?', ['Its number of members from the first disjoint group','An arbitrary order of its members','The order in which it was discovered'],0,'The integer k is determined by the final subset itself, so cases are disjoint.'),
q('In the small groups {A,B} and {C}, choosing two, how many subsets have k=1?', ['1','2','3'],1,'The sets {A,C} and {B,C} each use one member from the first group.'),
q('For real upper indices 1/2 and 3/2, why may the degree-3 convolution total zero?', ['Negative polynomial coefficients can cancel','There are negative numbers of subsets','All four terms individually vanish'],0,'The algebraic coefficients include both signs. Their sum is C(2,3)=0, not a count of fractional subsets.'),
q('Which identity does the smaller generalized example verify?', ['C(2,3)=0','C(2,3)=1','C(2,3)=3'],0,'The two upper indices add to 2, and the degree is 3.')],
41:[
q('How many functions from three labeled objects to two labeled targets have both targets used?', ['3','6','8'],1,'Partition into two nonempty fibers in S(3,2)=3 ways, then label those blocks in 2 underlined 2=2 ways, totaling 6.'),
q('For the two-object partition scene, how many partitions have two nonempty blocks?', ['0','1','2'],1,'Only {{A},{B}}; swapping the block order does not create another partition.'),
q('What is the coefficient of x² in x underlined 3?', ['3','−3','−2'],1,'x(x−1)(x−2)=x³−3x²+2x. Unsigned c(3,2)=3 needs the sign (−1)^(3−2).'),
q('Why is the first-kind coefficient at n=3,k=2 negated in the falling-power expansion?', ['Because (−1)^(n−k)=−1','Because all coefficients are negative','Because x must be negative'],0,'The sign convention is tied to n−k, independently of the value of x.')],
42:[
q('Which integral comparison is valid for H₁₀?', ['ln(11)≤H₁₀≤1+ln(10)','ln(10)≤H₁₀≤ln(11)','H₁₀=ln(10)'],0,'Left endpoint rectangles give the lower integral bound ln(n+1), while right endpoint rectangles after the first term give the upper bound 1+ln n.'),
q('Why does the right-hand integral comparison omit the first term 1?', ['The interval before k=1 would reach x=0, where 1/x is not integrable','The first term is zero','It changes the definition of Hₙ'],0,'The upper-bound argument sums right endpoint rectangles only for k=2,…,n over [1,n], then adds the omitted first term 1.'),
q('What proves Hₙ−ln n has a finite limit?', ['It looks flat in a finite graph','It is decreasing and bounded below','Hₙ is bounded'],1,'The monotone convergence theorem applies to the offset, even though Hₙ itself diverges.'),
q('Why is the change 1/(n+1)−ln(1+1/n) negative?', ['The integral over [n,n+1] exceeds its right-endpoint rectangle','Every logarithm is greater than 1','1/(n+1) is negative'],0,'For decreasing 1/x, the right-endpoint rectangle lies below the integral.')],
43:[
q('If Hₙ=3 and Hₙ^(2)=2 in a symbolic identity, what is Σₖ₌₁ⁿHₖ/k?', ['11/2','9/2','7/2'],0,'Half the square plus half the diagonal is (3²+2)/2=11/2.'),
q('Why is half the diagonal added after taking half of the reciprocal square?', ['The lower triangle includes the diagonal fully','The off-diagonal terms are negative','The diagonal was counted twice already'],0,'Half of the square contains only half of the needed diagonal weight.'),
q('For reciprocal squares after n=10, which interval bounds the remaining tail?', ['[1/11,1/10]','[0,1/100]','[1/10,1]'],0,'Integral comparison for r=2 gives 1/(n+1)≤tail≤1/n.'),
q('Do these positive tail bounds imply that Hₙ^(2) already equals ζ(2)?', ['Yes','No, a positive tail remains'],1,'A finite partial sum is strictly below the infinite positive-term sum.')],
44:[
q('How many tilings of a length-5 walkway start with a double plank?', ['2','3','5'],1,'The remaining walkway has length 3, with T₃=F₄=3 tilings.'),
q('In the smaller length-3 scene, how many tilings start with a single plank?', ['1','2','3'],1,'After the first single, the length-2 remainder has tilings 1+1 and 2.'),
q('Does Cassini imply gcd(F₆,F₉)=1?', ['Yes, every Fibonacci pair is coprime','No, it proves coprimality only for consecutive indices','Yes, because 6 and 9 differ by 3'],1,'F₆=8 and F₉=34 have gcd 2. Consecutive pairs are the special case.'),
q('What is gcd(F₀,F₁)?', ['0','1','Undefined because one value is zero'],1,'The values are 0 and 1; their greatest common divisor is 1.')],
45:[
q('Why can the factor Fₙ₊₁ be removed from gcd(FₘFₙ₊₁,Fₙ)?', ['It equals 1 for all n','It is coprime to Fₙ','All factors can be removed from gcd'],1,'Consecutive Fibonacci values are coprime, so this factor contributes no divisor shared with Fₙ.'),
q('In the smaller m=4,n=2 proof, what is the fixed second value F₂?', ['1','2','3'],0,'F₂=1, so every first value in that three-row witness has gcd 1 with it.'),
q('If Fₘ mod Fₙ differs from F_(m mod n), does the Fibonacci gcd theorem fail?', ['Yes','No, it only requires their gcd with Fₙ to agree'],1,'The proof preserves common divisors, not equality of the remainder values.'),
q('For m=6,n=4, compare F₆ mod F₄ with F_(6 mod 4).', ['Both equal 1','They are 2 and 1','They are 1 and 2'],1,'F₆=8,F₄=3, so the numeric remainder is 2; the index remainder is 2 and F₂=1. Both have gcd 1 with 3.')],
46:[
q('In (1−z−z²)G, what is the coefficient of z⁵?', ['F₅','F₅−F₄−F₃=0','1'],1,'The recurrence cancels every degree at least 2. Only degree one survives.'),
q('Why is the remaining coefficient at degree one exactly 1?', ['F₁−F₀=1−0','Every degree has coefficient 1','A shift doubles F₁'],0,'G contributes F₁=1, zG contributes F₀=0, and z²G contributes zero at degree one.'),
q('If double precision gives the wrong rounded integer, which theorem has been contradicted?', ['Binet’s exact formula','The exact nearest-integer theorem','Neither; numerical approximation added uncontrolled error'],2,'The mathematical theorem concerns exact φ and √5, while the computation stores approximations.'),
q('Which value in the precision-check scene is the integer oracle?', ['The rounded root expression','The exact recurrence value','The drawn coordinate'],1,'The recurrence uses integer addition and supplies the reference against which floating arithmetic is checked.')]
}

def mark_results(states):
 for s in states:
  for node in s['diagram']['nodes']:
   # Revealed mathematical conclusions stay gated until the verification phase.
   if node.get('role')=='result' or (node.get('type')=='text' and any(sign in node.get('text','') for sign in (' = ',' ≤ ',' ≥ '))):node['result']=True;node['phase']='result'
 return states

def gamma_euler(small=False):
 S=[];x=1 if small else 2
 for N in ([1,2,4] if small else [2,4,8]):
  exact=F(factorial(N)*N**x,prod(range(x,x+N+1)))
  nodes=[txt('head',360,45,f'Euler product approximation to Γ({x}) at N={N}')]
  if x==1:
   nodes+=[rect('denominator',120,140,480,65,'active',fill='none'),rect('numerator',120,140,480*float(exact),65,'input',fill='none'),txt('unit',360,255,f'{N} selected units out of {N+1}'),txt('gap',360,315,f'Gap from 1: {1-exact}')]
  else:
   unit=240/(N+2)
   nodes+=[rect('denominator',180,90,(N+1)*unit,(N+2)*unit,'active',fill='none'),rect('numerator',180,330-N*unit,N*unit,N*unit,'input',fill='none'),txt('width',180+(N+1)*unit/2,360,f'outer width {N+1}'),txt('height',530,165,f'outer height {N+2}'),txt('inner',530,235,f'inner square {N} × {N}'),txt('gap',530,295,f'gap: {1-exact}')]
  nodes+=[txt('ratio',360,408,f'Exact ratio = {exact}; limit = Γ({x}) = 1','result')]
  formula=fr'\frac{{N^{{{x}}}N!}}{{{x}({x}+1)\cdots({x}+N)}}\bigg|_{{N={N}}}={exact}'
  S.append(state(N,'Cancel matching factorial factors before comparing areas.',formula,nodes,'The finite rational ratio is below 1; the separate limit proof establishes convergence.',dict(x=x,N=N,numerator=str(factorial(N)*N**x),denominator=str(prod(range(x,x+N+1))),ratio=str(exact),gap=str(1-exact))))
 return S

def euler_passage():
 text=('The source’s Euler limit is another exact definition, not a polynomial interpolation through integer factorials. For real x>0, define L_N(x)=N! Nˣ/[x(x+1)⋯(x+N)], where N is a positive integer. The claim is Γ(x)=lim as N→∞ of L_N(x). Our scene computes these finite ratios with exact rational arithmetic for x=2. Cancelling N! leaves N²/[(N+1)(N+2)]; the inner square and outer rectangle show why the ratio is below 1 and approaches it. The smaller help uses x=1 and the ratio N/(N+1).\n\n'
 'Advanced bridge to the integral definition: repeated integration by parts, with the base integral ∫₀¹uˣ⁻¹du=1/x, gives ∫₀¹uˣ⁻¹(1−u)ᴺdu=N!/[x(x+1)⋯(x+N)]. Multiply by Nˣ and substitute t=Nu to get L_N(x)=∫₀ᴺtˣ⁻¹(1−t/N)ᴺdt. Extend the integrand by zero beyond N. For each fixed t>0 it tends to tˣ⁻¹e⁻ᵗ, and 0≤(1−t/N)ᴺ≤e⁻ᵗ on 0≤t≤N. The dominating function tˣ⁻¹e⁻ᵗ is integrable for x>0. The dominated convergence theorem therefore proves the limit equals Γ(x).\n\n'
 'This bridge uses improper integration, integration by parts, and dominated convergence as prerequisites. It does not infer an infinite limit from the three displayed ratios. For nonpositive noninteger arguments, continuation is handled separately; direct substitutions at poles are excluded.')
 S=mark_results(gamma_euler());H=mark_results(gamma_euler(True))
 d=dict(id='a-35-euler',title='Euler’s finite products converge to gamma',model=dict(kind='exact-euler-gamma-limit',arithmetic='Exact integer products and reduced rational quotients.',limitations='The spatial witness evaluates x=1 and x=2; the stated dominated-convergence argument covers every real x>0.'),states=S,transitions=[{'from':a['id'],'to':b['id'],'action':'increase-product-length','explanation':b['caption']} for a,b in zip(S,S[1:])],check=q('Why does the Euler-limit proof require x>0 when passing the limit through the integral?', ['Because three increasing sample ratios prove every limit','Because t^(x−1)e^(−t) is a common integrable majorant and the integrands converge for almost every t','Because every finite product already equals gamma'],1,'For x>0 the majorant is integrable both near zero and at infinity. Together with almost-everywhere convergence, this supplies the hypotheses of dominated convergence; finite plotted evidence does not.'),simplerHelp=dict(intro='Use x=1, where cancellation leaves a single fraction N/(N+1).',model=dict(kind='exact-euler-gamma-limit-smaller',x=1),states=H,steps=[dict(action='increase N',text=s['caption']) for s in H],connection='The missing fraction is 1/(N+1), which tends to zero. The main square/rectangle ratio has the same limiting value by a different finite product.',check=q('For the smaller x=1 example at N=2, what fraction of the bar is filled?', ['1/2','2/3','3/4'],1,'Cancel the factorials to get N/(N+1)=2/3; the remaining gap is 1/3.')))
 return dict(id='unit-35-euler-limit',title='Connect the source’s Euler limit to the integral',text=text,formula=r'\Gamma(x)=\lim_{N\to\infty}\frac{N!N^x}{x(x+1)\cdots(x+N)}\quad(x>0)',demonstration=d)


def animate_target_scene(order,mode,states):
 """Move mathematical objects and reveal evaluated fields, retaining exact records."""
 if order not in (26,42,43,45):return states
 for t,s in enumerate(states):
  nodes=s['diagram']['nodes'];data=s['computed']
  if mode==0 and order==26:
   for node in nodes:
    if node['id'].startswith('number'):
     k=int(node['id'].split('-')[0][6:]);node['opacity']=1 if (k%2==0 or (t>0 and k%3==0) or t==2) else .12
   # The overlap contributes once to each count, then one duplicate is removed.
   for k in range(6,data['n']+1,6):
    original=next(n for n in nodes if n['id']==f'number{k}')
    x=original['x']+(55 if t==1 else 0);y=original['y']
    for node in tile(f'overlap-copy{k}',x,y,k,'active',40,35):node['opacity']=1 if t==1 else 0;node['phase']='transform';nodes.append(node)
   nodes.append(txt('copy-note',360,420,['Reveal the even-number contribution.','The overlap has two counting copies.','Remove the extra overlap copy.'][t],size=14))
  elif mode==0 and order==42:
   upto=data['n']
   for node in nodes:
    if node['id'].startswith('bar'):
     k=int(node['id'][3:]);node['height']=node['height'] if k<=upto else 0;node['y']=315-node['height'];node['phase']='transform'
   count=len([node for node in nodes if node['id'].startswith('bar')]);frontier=70+upto*580/count
   nodes.append(line('sum-frontier',frontier,90,frontier,315,'active'))
  elif mode==0 and order==45:
   # Length is the INDEX, never the numerical Fibonacci remainder.
   for node in nodes:
    if node['type']=='text' and node['id'].startswith(('index','value')):node['phase']='result';node['result']=True
   largest=states[0]['computed']['a'];unit=360/largest;a=data['a'];b=data['b']
   nodes += [rect('index-length',240,292,a*unit,20,'input'),rect('index-remainder',240+(a-a%b if b else 0)*unit,292,(a%b if b else a)*unit,20,'active'),txt('length-label',110,309,'index division',size=14)]
   for q in range(largest+1):
    x=240+min(q*b,a)*unit
    nodes.append(dict(**line(f'division-cut{q}',x,285,x,320,'active'),opacity=1 if b and 0<q*b<a else 0))
  elif mode==1 and order==42:
   for node in nodes:
    if node['id'].startswith('rightbar'):node['opacity']=1 if t>=1 else 0
   for side,ox,ninterval in [('left',50,data['n']),('right',390,data['n']-1)]:
    T=ninterval+1;w=240/ninterval
    pts=[(ox,290)]+[(ox+w*(x-1),290-140/x) for x in [1+ninterval*j/60 for j in range(61)]]+[(ox+240,290)]
    nodes.append(dict(id=side+'-integral-area',type='path',d='M '+' L '.join(f'{x:.3f},{y:.3f}' for x,y in pts)+' Z',role='active',opacity=.2 if t==2 else 0,phase='transform'))
  elif mode==1 and order==43:
   n=data['n']
   for node in nodes:
    if node['id'].startswith('ij'):
     i,j=map(int,node['id'].split('-label')[0][2:].split('-'));label=node['type']=='text'
     row,col=max(i,j),min(i,j);x=160+(col-1)*135;y=100+(row-1)*82
     if t==1:
      # Two separately labeled half-contributions share the lower-triangle cell.
      x+=55 if i<j else 0
      node['x']=x+(24 if label else 0);node['y']=y+(36 if label else 0)
      if label:node['text']=str(F(1,2*i*j));node['fontSize']=15
      else:node['width']=48
     elif t==2:
      node['x']=x+(52.5 if label else 0);node['y']=y+(36 if label else 0);node['opacity']=0 if i<j else 1
   for i in range(1,n+1):
    x=160+(i-1)*135+(55 if t==1 else 0);y=100+(i-1)*82
    for node in tile(f'diagonal-half{i}',x,y,str(F(1,2*i*i)),'active',48,60):
     node['opacity']=1 if t==1 else 0
     if node['type']=='text':node['fontSize']=15
     nodes.append(node)
   nodes.append(txt('pair-note',360,400,['Each cell contributes to the full square.','Take half the square, plus another half-diagonal.','Merge equal half-terms into the lower triangle.'][t],size=14))
  elif 'rows' in data:
   rows=data['rows'];height=min(65,270/len(rows));width=min(220,600/max(map(len,rows)));ox=(720-width*max(map(len,rows)))/2
   # A field selector follows the actual proof operation, not an elapsed-time bar.
   col=[0,max(0,len(rows[0])-2),len(rows[0])-1][t]
   nodes.append(rect('evaluated-field',ox+col*width-3,80,width-2,len(rows)*height,'active',fill='none',phase='transform'))
   for node in nodes:
    if node['id'].startswith('cell-'):
     _,i,j,*_=node['id'].split('-');i=int(i);j=int(j)
     if j==len(rows[i])-1:node['opacity']=1 if t==2 or (t==1 and i==0) else 0
  elif 'revealed' in data:
   upto=data['revealed']
   for node in nodes:
    for prefix in ('point','leader','label'):
     if node['id'].startswith(prefix) and node['id'][len(prefix):].isdigit():node['opacity']=1 if int(node['id'][len(prefix):])<upto else 0
   current=next(n for n in nodes if n['id']==f'point{upto-1}')
   nodes.append(dict(**line('offset-selector',current['x'],190,current['x'],232,'active'),arrow=True))
 return states

def teach_a(order,mode,states):
 """Reviewed learner explanations for the repaired mathematical operations."""
 for scene in states:
  c=scene['computed'];t=int(float(scene['id'])) if scene['id'].replace('.','',1).isdigit() else 0;meaning=None
  if mode==0:
   if order==25:
    stage=c['stage'];n=c['n'];j=c['fixedIndex']
    meaning=(f'The first coordinate i names a row and the second coordinate j names a column. Holding i={j} fixed leaves j=1,…,{j}; each tile contributes i+j.' if stage==0 else f'For each row i=1,…,{n}, the legal columns are j=1,…,i. Every labeled pair contributes exactly once.' if stage==1 else f'Column j={j} contains only rows i={j},…,{n}. Rows with i<{j} contain no such cell, which explains the new lower bound i=j.' if stage==2 else f'The outer index now visits columns j=1,…,{n}; within column j, i runs from j through {n}. The unchanged tile identities prove that the swapped sum has the same total {c["total"]}.')
   elif order==26:meaning=f'A is the condition “even” and B is “divisible by 3”. Their counts are {c["A"]} and {c["B"]}; the {c["intersection"]} overlap members each enter both counts, so removing one duplicate per overlap leaves {c["union"]} union members. A condition bracket is 1 when true and 0 when false.'
   elif order==31:
    meaning=[f'a={c["a"]} names the marked location and d={c["d"]} is the positive block length. The quotient will count signed whole blocks, while the remainder will be a rightward offset.',f'The quotient is q=floor({c["a"]}/{c["d"]})={c["q"]}. The signed d-length blocks therefore stop at qd={c["blockEndpoint"]}, at or to the left of a.',f'The offset r=a−qd={c["r"]} moves right from {c["blockEndpoint"]} to {c["a"]}. Its length is nonnegative and smaller than d={c["d"]}, which is the required remainder convention.',f'Numbers separated by d={c["d"]} occupy different locations but have the same remainder r={c["r"]}. The ringed locations are representatives of that congruence class.'][c["stage"]]
   elif order==33:meaning=f'A prefix is the sequence of badges already placed. At depth {c["k"]}, {c["count"]} prefixes are possible; a length-j prefix always leaves n−j unused badges. The expanded branch is one witness of the same branching count that applies to every prefix at its depth.'
   elif order==37:
    meaning=(f'The letters name {c["n"]} distinct objects. AB and BA are different ordered listings with the same two members; every fixed pair therefore has 2!=2 listings.' if c['stage']<2 else f'Forgetting order identifies each two-card group with one subset. The {len(c["ordered"])} listings thus yield {len(c["subsets"])} subsets by division by 2!.' if c['stage']==2 else f'The marked member is {c["marked"]}. Exactly {len(c["excluded"])} subsets exclude it and {len(c["included"])} include it; every subset belongs to one family, so the two parent counts add to {len(c["subsets"])}.')
   elif order==40:
    meaning=(f'Each bin collects sets with one fixed A-count k. The bins are disjoint because every set has exactly one such count; their totals {", ".join(map(str,c["terms"]))} sum to {c["total"]}.' if c['final'] else f'k={c["k"]} is the number selected from group A. The row labels list its {len(c["AChoices"])} possible subsets and the column labels list the {len(c["BChoices"])} possible subsets of B. Each row-column pair gives one distinct union.'+ (f' This Cartesian product contains {c["terms"][c["k"]]} sets.' if c['assembled'] else ''))
   elif order==41:
    meaning=(f'Δ means “next value minus current value”. Each new table cell takes the difference of its two parents. {scene["caption"]}' if not c['extracted'] else f'Δ^k f(0) is the first entry after k difference rounds. For x^{c["degree"]} the first entries {", ".join(map(str,c["newton"]))} multiply C(x,k) in the Newton expansion.' if not c['converted'] else f'C(x,k)=x underlined k/k!, so each extracted difference must be divided by k!. The Newton coefficients {", ".join(map(str,c["newton"]))} become falling-factorial coefficients {", ".join(c["fallingCoefficients"])}; the bars use one common numerical scale.')
   elif order==42:meaning=f'H{c["n"]} is the sum of the first {c["n"]} reciprocal terms. Each newly included rectangle has width 1 and height 1/k, so its area contributes exactly 1/k; the visible accumulated sum is {c["H"]}. The decreasing curve explains the separate integral bounds.'
   elif order==43:meaning=f'i records the original harmonic row and j names its denominator. Column j occurs in rows j,…,{c["n"]}, hence contains {c["n"]}−j+1 equal copies of 1/j. Its contribution is ({c["n"]}−j+1)/j; adding the column contributions preserves the original total {c["total"]}.'
   elif order==45:meaning=f'The two indices are a={c["a"]} and b={c["b"]}; their Fibonacci values are {c["Fa"]} and {c["Fb"]}. The lower strip divides the index a into b-length blocks and an index remainder. Replacing (a,b) by (b,a mod b) preserves the Fibonacci-value gcd {c["gcd"]}; it does not equate the two different remainder operations.'
   elif order==46:
    if c.get('kind')=='coefficient-shift-bridge':meaning=f'F{c["sourceDegree"]}={c["coefficient"]} is the coefficient attached to degree {c["sourceDegree"]}. Multiplication by z adds one to the degree while retaining that coefficient; z² adds two. At degree {c["selectedDegree"]}, G−zG−z²G has coefficient {c["operands"][0]}−{c["operands"][1]}−{c["operands"][2]}=0 by the Fibonacci recurrence.'
    elif 'rows' in c:meaning='Each row fixes one power of z. Its G column contains Fₙ, the zG column contains Fₙ₋₁, and the z²G column contains Fₙ₋₂; absent negative-index coefficients are zero. Subtracting equal-degree coefficients leaves only the coefficient 1 of z.'
  elif order==32 and mode==1:meaning=f'x is a candidate integer. The first condition requires remainder {c["u"]} on division by {c["r"]}; the second requires remainder {c["v"]} on division by {c["s"]}. Their common candidate is {c["solution"]}, and all solutions differ by {c["r"]*c["s"]}.'
  elif order==26:meaning=('The four columns record [A], [B], [A and B], and [A or B]. Every row checks that adding the first two indicators and subtracting their overlap equals the union indicator.' if mode==1 else 'At x=0 the quotient 1/x is undefined. Multiplication by an indicator cannot give that undefined expression a value; a zero branch must be defined separately before evaluating the quotient.')
  elif order==42:meaning=(f'Left-endpoint reciprocal rectangles lie above the decreasing curve, while right-endpoint rectangles lie below it. Their exact areas give ln({c["n"]+1})≤H{c["n"]}≤1+ln({c["n"]}); here H{c["n"]}={c["H"]}.' if mode==1 else 'Each marked point is Hₙ−ln n at its labeled integer n. The computed offsets decrease; the accompanying monotonicity argument, rather than finitely many points alone, establishes convergence to the Euler constant.')
  elif order==43:meaning=(f'Cell (i,j) has value 1/(ij). Off-diagonal cells pair with their transposes; two half-cells merge into one lower-triangle contribution. A diagonal cell needs its extra half, giving (Hₙ²+Hₙ⁽²⁾)/2={c["triangle"]}.' if mode==1 else 'Hₙ⁽²⁾ adds reciprocal squares through n. The uncomputed tail is bounded below by 1/(n+1) and above by 1/n using integrals of 1/x²; both bounds shrink to zero.')
  elif order==45:meaning=('The fixed second Fibonacci value keeps the same gcd while the addition identity removes a multiple of it. Consecutive Fibonacci values are coprime, which permits cancellation of the neighboring factor inside the gcd.' if mode==1 else 'The first row takes a remainder of indices, the second takes a remainder of Fibonacci values, and the third evaluates Fibonacci at the index remainder. These are different operations; the theorem preserves the gcd rather than claiming their remainders agree.')
  if meaning:scene['teachingExplanation']=meaning
 return states

def make_demo(order,mode,text,check,helpcheck):
 if mode:
  check,helpcheck=TARGETED[order][(mode-1)*2:(mode-1)*2+2]
 main=model(order) if mode==0 else supplemental(order,boundary=mode==2)
 helper=model(order,True) if mode==0 else supplemental(order,boundary=mode==2,small=True)
 if order==46 and mode<2:
  main=supplemental(46) if mode==0 else model(46)
  helper=supplemental(46,small=True) if mode==0 else model(46,True)
  check,helpcheck=(TARGETED[46][0],TARGETED[46][1]) if mode==0 else (CONTENT[46]['check'],CONTENT[46]['helpcheck'])
 main=teach_a(order,mode,animate_target_scene(order,mode,main));helper=teach_a(order,mode,animate_target_scene(order,mode,helper))
 # At a fixed minimal counterexample, focus one row at a time instead of adding unrelated data.
 if mode==2 and helper==main:
  helper=json.loads(json.dumps(helper))
  for j,s in enumerate(helper):
   nodes=s['diagram']['nodes'];cellrows=sorted({int(n['id'].split('-')[1]) for n in nodes if n['id'].startswith('cell-')})
   if cellrows:
    target=cellrows[min(j,len(cellrows)-1)]
    for node in nodes:
     if node['id'].startswith('cell-'):
      row=int(node['id'].split('-')[1]);node['opacity']=1 if row==target else .16
    s['caption']='Inspect one case: '+s['caption'];s['diagram']['description']=s['caption']
  # Minimal-domain fixtures are intentional: shrinking a four-case truth domain can remove the counterexample.
 demo_id=f'a-{order}-{mode}'
 transitions=[dict(from_=a['id'],to=b['id'],action='compute-next-case',explanation=b['caption']) for a,b in zip(main,main[1:])]
 for t in transitions:t['from']=t.pop('from_')
 helpintro=CONTENT[order]['helpintro'] if mode==0 else ('Follow the smaller computed proof witness one step at a time.' if mode==1 else 'Inspect the boundary case before trying to apply the general rule.')
 return dict(id=demo_id,title=text['title'],model=dict(kind=['authored-spatial-exact-model','focused-proof-witness','computed-boundary-counterexample'][mode],generator=f'scripts/fullbook-batch-A.py:model({order}) / supplemental({order})',arithmetic='Integers and reduced rational fractions unless explicitly labeled floating approximations.',limitations='Finite computed witnesses illustrate the separate general proof; no finite enumeration is presented as proof of an infinite theorem.'),states=mark_results(main),transitions=transitions,check=check,simplerHelp=dict(intro=helpintro,model=dict(kind='computed-smaller-or-minimal-counterexample',parentLesson=order,mode=mode),states=mark_results(helper),steps=[dict(action='step',text=s['caption']) for s in helper],connection=('The smaller scene uses the same definitions. '+text['title']+'. Return to the general statement and retain its domain restrictions.'),check=helpcheck),accessibility=dict(reducedMotion='Show these same computed states as discrete frames.',stateDescription='Read the caption, diagram description, and labeled mathematical objects.',playback='Pause, replay, and backward navigation select the same authored state without recomputation drift.'))

def build():
 lessons=[]
 for order in range(21,47):
  c=CONTENT[order];orig=c['passages']
  # Keep three substantial passages, each with a distinct mathematical representation.
  layouts={24:[[0],[1,3],[2]],26:[[0],[1,3],[2]],27:[[0],[2],[1,3]],29:[[0],[2,3],[1]],33:[[0],[2,3],[1]],34:[[0],[2,3],[1]],35:[[0],[1],[2,3]],36:[[0],[1,3],[2]],37:[[0],[1,3],[2]],40:[[0],[1,3],[2]],41:[[0],[1,3],[2]],42:[[0],[1],[2,3]],43:[[0],[1,3],[2]]}
  groups=layouts.get(order,[[0],[1,2],[3]])
  merged=[p(' · '.join(orig[i]['title'] for i in group),'\n\n'.join(orig[i]['text'] for i in group),orig[group[0]]['formula']) for group in groups]
  if order==22:merged[2]['text']='The displayed counterexample uses only the finite instruction a→aa and returns to the same rule. Every word in its run still contains a, so an effective next step is always possible and the terminal branch is never taken. This separates effective encoding from universal termination.\n\n'+merged[2]['text']
  if order==23:merged[1]['text']+='\n\nThe accompanying construction uses amounts 8, 9, and 10 as its three bases, then adds a 3-unit piece. It is a second strong-induction witness: a new amount n≥11 can use the already established amount n−3.'
  if order==28:merged[2]['text']='The boundary scene separates three cases: no factors gives 1; a defined zero factor gives 0; a zero denominator is undefined. These are different mathematical situations even if a programming language displays a similar empty or zero value.\n\n'+merged[2]['text']
  if order==44:merged[1]['text']+='\n\nThe accompanying small walkway enumerates the recurrence combinatorially: remove its first single plank or its first double plank. The remaining lengths are m−1 and m−2, so the two disjoint classes sum to T_m=F_(m+1). This is a concrete witness of the same local recurrence used in the matrix proof.'

  # The second formula remains in a visible dedicated paragraph, never silently dropped.

  merged[1]['secondaryFormula']=orig[groups[1][-1]]['formula']
  passages=[]
  for mode,pp in enumerate(merged):
   passage=dict(id=f'unit-{order}-passage-{mode}',title=pp['title'],text=pp['text'],formula=pp['formula'])
   if mode==1 and len(groups[1])>1:
    second=orig[groups[1][-1]]['formula']
    passage['formula']=chr(92)+'begin{gathered}'+pp['formula']+chr(92)*2+'{}'+second+chr(92)+'end{gathered}'
   passage['demonstration']=make_demo(order,mode,pp,c['check'],c['helpcheck']);passages.append(passage)
  if order==35:passages.append(euler_passage())
  info=PLAN[order]
  lessons.append(dict(id=info['id'],order=order,title=info['title'],source=dict(book='Donald E. Knuth, The Art of Computer Programming, Volume 1, third edition',section='§'+info['section'],pdfPages=c['pages'],pagination='one-based supplied private ebook, not printed pages'),provenance='Original explanations, examples, diagrams, finite models and assessments after the cited concepts. No source prose, scans, exercise bank or private PDF is distributed.',scope=c['limits'] or 'The stated conceptual objectives are taught with original finite models, general proof arguments and boundary checks. Source historical notes and exercise bank are not reproduced.',sections=[dict(id=f'unit-{order}-core',title='Concrete model, precise argument, and boundary',passages=passages)]))
 return lessons

def selftest():
 checks=0
 def ck(cond):
  nonlocal checks
  assert cond;checks+=1
 # Snapshot totality, terminal fixed points, and universal finite-domain enumeration.
 for n in range(15):
  for o in range(5):
   for pc in ('CHECK','MOVE','DONE'):
    new=snapshot_step((n,pc,o));ck(new[0]>=0 and new[1] in ('CHECK','MOVE','DONE'))
    if pc=='DONE':ck(new==(n,pc,o))
  q0=(n,'CHECK',0)
  for _ in range(2*n+1):q0=snapshot_step(q0);ck(q0[0]+q0[2]==n)
  ck(q0==(0,'DONE',n))
 for length in range(8):
  for letters in product('ab',repeat=length):
   word=''.join(letters);original=word;j=0;steps=0
   while not j:
    old=sum(word[i]=='a' and word[k]=='b' for i in range(len(word)) for k in range(i+1,len(word)));word,j=rewrite_step(word,j);steps+=1
    new=sum(word[i]=='a' and word[k]=='b' for i in range(len(word)) for k in range(i+1,len(word)));ck(j==1 or new==old-1);ck(steps<=length*length+1)
   ck(word=='b'*original.count('b')+'a'*original.count('a'))
 ck(rewrite_step('ab',0,'','c')==('cab',0))
 # Finite sums, exact telescoping and product, floor/mod boundaries.
 for n in range(15):
  cells={(i,j) for i in range(1,n+1) for j in range(1,i+1)};ck(cells=={(i,j) for j in range(1,n+1) for i in range(j,n+1)})
  ck(sum((F(1,k*(k+1)) for k in range(1,n+1)),F(0))==F(n,n+1));ck(prod(F(k+1,k) for k in range(1,n+1))==n+1)
  ck(sum((harmonic(k) for k in range(1,n+1)),F(0))==(n+1)*harmonic(n)-n)
  ck(sum((harmonic(k)/k for k in range(1,n+1)),F(0))==(harmonic(n)**2+harmonic(n,2))/2)
  ck(sum(x**3 for x in range(n))==(n*(n-1)//2)**2)
  if n:ck(log(n+1)<=float(harmonic(n))<=1+log(n))
 for a in range(-40,41):
  for d in range(1,9):
   x=F(a,d);ck(floor(x)<=x<floor(x)+1);ck(ceil(x)-1<x<=ceil(x));ck(floor(-x)==-ceil(x))
  for m in range(1,15):ck(a-m*floor(F(a,m))==a%m)
 for a in range(-4,5):
  for b in range(-4,5):
   u,v=a-b,a+b;ck(u*u+v*v==2*(a*a+b*b))
 for p0 in (2,3,5,7,11,13):
  for a in range(p0):
   ck(pow(a,p0,p0)==a)
   if a:ck(len({a*k%p0 for k in range(1,p0)})==p0-1)
 ck(pow(2,340,341)==1 and 11*31==341)
 for n in range(8):
  for k in range(n+2):ck(len(list(permutations(range(n),k)))==(falling(n,k) if k<=n else 0))
  for prime in (2,3,5,7):
   t=factorial(n);count=0
   while t%prime==0 and t:count+=1;t//=prime
   ck(count==sum(n//prime**j for j in range(1,10)))
 for n in range(8):
  for k in range(n+1):ck(len(list(combinations(range(n),k)))==comb(n,k))
 for r in range(5):
  for s in range(5):
   for n in range(r+s+2):ck(sum(choose(r,k)*choose(s,n-k) for k in range(n+1))==choose(r+s,n))
 for r in (F(-3),F(-1,2),F(1,2),F(4)):
  for k in range(7):
   ck(choose(-r,k)==(-1)**k*choose(r+k-1,k));ck(choose(r,k)==choose(r-1,k)+choose(r-1,k-1))
   if k:ck(k*choose(r,k)==r*choose(r-1,k-1))
 for n in range(7):
  pp=list(partitions(n));ck(len({str(p0) for p0 in pp})==len(pp))
  for k in range(n+1):ck(sum(len(p0)==k for p0 in pp)==stirling(n,k))
  for x in range(-3,9):
   ck(x**n==sum(stirling(n,k)*falling(x,k) for k in range(n+1)))
   ck(falling(x,n)==sum((-1)**(n-k)*stirling(n,k,True)*x**k for k in range(n+1)))
 # Independently count permutation cycles for unsigned first kind.
 for n in range(7):
  counts=[0]*(n+1)
  for perm in permutations(range(n)):
   seen=set();cycles=0
   for x in range(n):
    if x not in seen:
     cycles+=1
     while x not in seen:seen.add(x);x=perm[x]
   counts[cycles]+=1
  ck(counts==[stirling(n,k,True) for k in range(n+1)])
 for n in range(25):
  if n:ck(fib(n+1)*fib(n-1)-fib(n)**2==(-1)**n)
  ck(gcd(fib(n),fib(n+1))==1)
  if n<12:ck(len(tilings(n))==fib(n+1))
  for m in range(25):
   ck(gcd(fib(n),fib(m))==fib(gcd(n,m)))
   if m:ck(fib(m+n)==fib(m)*fib(n+1)+fib(m-1)*fib(n))
 for n in range(20):
  # Exact quadratic-field root powers (a+b√5)/2^n independently recover F_n.
  a,b=1,0
  for _ in range(n):a,b=a+5*b,a+b
  ck(F(2*b,2**n)==fib(n))
 for x in range(1,6):
  for N in range(1,12):ck(F(factorial(N)*N**x,prod(range(x,x+N+1)))==F(factorial(x-1)*N**x,prod(range(N+1,N+x+1))))
 lessons=build();ck(len(lessons)==26)
 for l in lessons:
  ck(len(l['sections'][0]['passages'])>=3)
  for p0 in l['sections'][0]['passages']:
   d=p0['demonstration'];ck(len(d['states'])>=2);ck(0<=d['check']['correctIndex']<len(d['check']['choices']))
   for s in d['states']+d['simplerHelp']['states']:
    ids=[n['id'] for n in s['diagram']['nodes']];ck(len(ids)==len(set(ids)))
    for node in s['diagram']['nodes']:
     if 'x' in node:ck(15<=node['x']<=705)
     if 'y' in node:ck(15<=node['y']<=425)
     if node['type']=='rect':ck(node['width']>=0 and node['height']>=0 and node['x']+node['width']<=705 and node['y']+node['height']<=430)
   if l['order']==35:
    for s in model(35):ck(s['computed']['lower']-1e-12<=1<=s['computed']['upper']+1e-12)
 print(f'Batch A: {checks} deterministic independent assertions passed.')
 return checks

if __name__=='__main__':
 if '--test' in sys.argv:selftest()
 else:
  target=ROOT/'content/fullbook/batch-A.json';target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n');print(target)
