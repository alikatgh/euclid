#!/usr/bin/env python3
"""Deterministic original lessons 47–64. Run --test for independent model checks.
Private source locators are documentation, not bundled book content.
"""
from fractions import Fraction as F
from math import comb, factorial, log, exp, sqrt, pi
from itertools import permutations, product, combinations, combinations_with_replacement
from pathlib import Path
import json, sys, unittest
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'content/fullbook/source-plan-B.json'
def fs(x): return str(x) if isinstance(x,(int,F)) else f'{x:.6g}'
def tex(x):
    x=F(x)
    return str(x.numerator) if x.denominator==1 else rf'\frac{{{x.numerator}}}{{{x.denominator}}}'
def txt(i,x,y,text,role='input',size=16): return dict(id=i,type='text',x=x,y=y,text=str(text),role=role,fontSize=size,anchor='middle')
def rect(i,x,y,w,h,role='input',**kw): return dict(id=i,type='rect',x=x,y=y,width=w,height=h,role=role,**kw)
def line(i,x,y,x2,y2,role='muted',**kw): return dict(id=i,type='line',x=x,y=y,x2=x2,y2=y2,role=role,**kw)
def path(i,pts,role='active',**kw): return dict(id=i,type='path',d=' '.join(('M' if j==0 else 'L')+f'{float(x):.3f},{float(y):.3f}' for j,(x,y) in enumerate(pts)),role=role,fill='none',**kw)
def state(i,caption,formula,nodes,inv='',data=None):
    return dict(id=str(i),caption=caption,formula=formula,diagram=dict(title=caption,description=caption,viewBox=[0,0,720,440],nodes=nodes,invariant=inv),computed=data or {})
def axes(): return [line('x-axis',55,335,665,335),line('y-axis',55,335,55,60)]
def conv(a,b):
    if not a or not b:return []
    out=[F(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return out

def shelf(a,shift=1):
    ss=[]
    for t in range(3):
        nodes=[]
        for j in range(len(a)+shift):
            x=75+j*72
            nodes += [line(f'shelf{j}',x-27,255,x+27,255),txt(f'index{j}',x,285,f'z^{j}','muted')]
        for i,xv in enumerate(a):
            x=75+(i+(shift if t>0 else 0))*72
            nodes += [rect(f'card{i}',x-25,175,50,65,'result' if t==2 else 'active'),txt(f'value{i}',x,214,fs(xv))]
        if t: nodes += [txt('zero',75,214,'0','muted')]
        cap=['Store each coefficient at its exponent.','Multiplication moves every card right.','Read the vacated coefficients as zero.'][t]
        ss.append(state(t,cap,rf'[z^n]z^{{{shift}}}G(z)=a_{{n-{shift}}}',nodes,'a_j = 0 for j < 0',dict(input=list(map(fs,a)),shift=shift,stage=t)))
    return ss

def convolution(a,b):
    c=conv(a,b);ss=[]
    for n in range(len(c)):
        nodes=[txt('cols',380,48,'Columns: exponent i, coefficient aᵢ'),txt('row-index-heading',80,112,'Index',size=14),txt('row-value-heading',145,112,'bⱼ',size=14)]
        for i,x in enumerate(a):
            nodes.append(txt(f'i{i}',230+i*100,83,f'i={i}','muted',14))
            nodes.append(txt(f'a{i}',230+i*100,113,f'aᵢ={fs(x)}',size=15))
            for j,y in enumerate(b):
                active=i+j==n; xx=187+i*100; yy=133+j*64
                nodes += [rect(f'pair{i}-{j}',xx,yy,86,52,'active' if active else 'muted',opacity=1 if active else .28),txt(f'prod{i}-{j}',xx+43,yy+32,fs(x*y),'active' if active else 'muted')]
        for j,y in enumerate(b):
            nodes.append(txt(f'j{j}',80,166+j*64,f'j={j}','muted',14))
            nodes.append(txt(f'b{j}',145,166+j*64,fs(y),size=15))
        nodes.append(txt('sum',355,385,f'Total size {n}: {fs(c[n])}','result',20))
        ss.append(state(n,f'Collect pairs whose sizes add to {n}.',rf'c_{{{n}}}=\sum_{{i+j={n}}}a_i b_j={tex(c[n])}',nodes,'A pair contributes to exactly one diagonal.',dict(a=list(map(fs,a)),b=list(map(fs,b)),n=n,value=fs(c[n]))))
    return ss

def transform(a,mode):
    if mode=='weight':out=[i*x for i,x in enumerate(a)]; rule=r'[z^n]zG\prime(z)=na_n'; labels=['Original coefficient','Weight by its shelf number']
    elif mode=='parity':out=[x if i%2==0 else 0 for i,x in enumerate(a)];rule=r'\frac{G(z)+G(-z)}2=\sum_{n\text{ even}}a_nz^n';labels=['Keep both signed copies','Cancel the odd shelves']
    else:out=[F(0)]+[F(x,i+1) for i,x in enumerate(a)];rule=r'\int_0^zG(t)\,dt=\sum_{n\ge0}\frac{a_n}{n+1}z^{n+1}';labels=['Start with coefficient cards','Divide, then shift one shelf']
    ss=[]
    for t,arr in enumerate([a,out]):
        nodes=[]
        for i,x in enumerate(arr):
            xx=75+i*90;hh=abs(float(x))*15
            nodes +=[rect(f'v{i}',xx-26,300-hh,52,hh,'active' if t==0 else 'result'),txt(f'label{i}',xx,320,str(i)),txt(f'num{i}',xx,280-hh,fs(x))]
        nodes.append(txt('legend',355,380,'Horizontal position = exponent; height = coefficient'))
        ss.append(state(t,labels[t],rule,nodes,'All transformations are coefficientwise formal identities.',dict(input=list(map(fs,a)),output=list(map(fs,out)),mode=mode,stage=t)))
    return ss

def recurrence(u,v,n):
    a=[F(u),F(v)]
    for k in range(2,n):a.append(2*a[-1]+a[-2])
    ss=[]
    for k in range(2,n):
        nodes=[]
        for i,x in enumerate(a):
            xx=75+i*84;nodes +=[rect(f'coef{i}',xx-32,210,64,56,'result' if i==k else 'input',opacity=1 if i<=k else .15),txt(f'value{i}',xx,244,fs(x) if i<=k else '?'),txt(f'index{i}',xx,289,str(i),'muted')]
        for i in [k-2,k-1]:nodes.append(line(f'use{i}',75+i*84,205,75+k*84,170,'active'))
        nodes.append(txt('weights',75+k*84,145,f'2×{fs(a[k-1])} + {fs(a[k-2])}'))
        ss.append(state(k,f'Compute coefficient {k} from the previous two.',rf'a_{{{k}}}=2a_{{{k-1}}}+a_{{{k-2}}}={tex(a[k])}',nodes,rf'(1-2z-z²)G(z) = {u} + ({v}-2·{u})z',dict(sequence=list(map(fs,a[:k+1])),u=u,v=v)))
    return ss

def labeled(n):
    ss=[]
    for k in range(n+1):
        nodes=[];subsets=list(combinations(range(n),k))
        for r,sub in enumerate(subsets):
            yy=100+r*48
            for i in range(n):
                xx=210+i*64;nodes +=[dict(id=f'item{r}-{i}',type='circle',x=xx,y=yy,r=18,role='active' if i in sub else 'muted'),txt(f'lab{r}-{i}',xx,yy+5,chr(65+i))]
        nodes.append(txt('count',355,390,f'{len(subsets)} ways to choose the first group','result'))
        ss.append(state(k,f'Assign {k} of {n} distinct labels to the first group.',rf'\binom{{{n}}}{{{k}}}={len(subsets)}',nodes,'The two groups partition the labels; order within a group is ignored.',dict(n=n,k=k,count=len(subsets))))
    return ss

def symmetric(xs,repeat=False):
    ss=[]
    for degree in range(1,4):
        indices=list((combinations_with_replacement if repeat else combinations)(range(len(xs)),degree));values=[];nodes=[]
        for j,inds in enumerate(indices):
            value=1
            for i in inds:value*=xs[i]
            values.append(value); xx=110+(j%5)*120;yy=110+(j//5)*85
            nodes += [rect(f'term{j}',xx-47,yy-24,94,58,'active'),txt(f'product{j}',xx,yy,'·'.join(map(lambda i:str(xs[i]),inds))),txt(f'value{j}',xx,yy+24,str(value),'result')]
        total=sum(values);nodes.append(txt('total',355,387,f'{"h" if repeat else "e"}_{degree} = {total}','result',20))
        ss.append(state(degree,f'Choose {degree} positions {"with" if repeat else "without"} replacement.',rf'{"h" if repeat else "e"}_{{{degree}}}={total}',nodes,'Different monomials retain their multiplicity.',dict(xs=xs,degree=degree,repeat=repeat,value=total)))
    return ss

def scan(xs):
    n=len(xs);m=xs[-1];j=n-1;updates=0;ss=[]
    for k in range(n-1,-2,-1):
        if k<n-1 and k>=0 and xs[k]>m:m=xs[k];j=k;updates+=1
        nodes=[]
        for i,x in enumerate(xs):
            xx=80+i*90;nodes +=[rect(f'item{i}',xx-30,270-x*18,60,x*18,'result' if i==j else ('active' if i==k else 'input')),txt(f'value{i}',xx,250-x*18,x),txt(f'index{i}',xx,305,i+1,'muted')]
        nodes +=[line('comparison-cursor',80+max(0,k)*90,345,80+max(0,k)*90,320,'active',arrow=True,opacity=1 if k>=0 else 0),rect('retained-maximum',80+j*90-35,270-m*18-5,70,m*18+10,'active',fill='none'),line('finished-scan',50,330,80+(n-1)*90+30,330,'result',opacity=1 if k<0 else 0)]
        for op in range(n-1):
            nodes.append(rect(f'comparison-token{op}',95+op*55,395,35,16,'active',opacity=1 if op<min(n-1,n-1-k) else 0))
        nodes +=[txt('maximum',355,65,f'Maximum {m}, rightmost index {j+1}','result'),txt('counts',355,370,f'Comparisons {min(n-1,n-1-k)}; updates {updates}','result')]
        ss.append(state(k,f'{"Initialize at the last item" if k==n-1 else ("Finish" if k<0 else "Compare the next item on the left")}.',rf'm=\max_{{{max(0,k)+1}\le i\le {n}}}X_i',nodes,'Strict > updates preserve the rightmost equal maximum.',dict(xs=xs,k=k,m=m,j=j,updates=updates,comparisons=min(n-1,n-1-k))))
    return ss

def records(perm):
    m=0;r=0
    for x in reversed(perm):
        if x>m:r+=1;m=x
    return r

def average(n):
    perms=list(permutations(range(1,n+1)));ss=[]
    for suffix in range(1,n+1):
        hits=sum(p[-suffix]==max(p[-suffix:]) for p in perms)
        for phase in range(2):
            nodes=[txt('event',355,38,f'Suffix length {suffix}: does its LEFT edge hold its maximum?',size=16)]
            for j,p in enumerate(perms):
                xx=75+(j%6)*105;yy=110+(j//6)*62;left=n-suffix;maximum=max(p[left:]);at=p.index(maximum);hit=p[left]==maximum
                nodes.append(rect(f'p{j}',xx-44,yy-25,88,42,'muted'))
                nodes.append(rect(f'suffix{j}',xx-(n-1)*9+left*18-9,yy-17,suffix*18,27,'active',fill='none'))
                for i,value in enumerate(p):nodes.append(txt(f'v{j}-{i}',xx-(n-1)*9+i*18,yy+3,value,'input',14))
                nodes += [line(f'left-edge{j}',xx-(n-1)*9+left*18,yy+20,xx-(n-1)*9+left*18,yy+29,'active',arrow=True),rect(f'maximum{j}',xx-(n-1)*9+at*18-8,yy-16,16,24,'result',fill='none',opacity=1 if phase else 0),txt(f'hit{j}',xx+41,yy+30,'✓' if hit else '×','result',14)]
                nodes[-1]['opacity']=1 if phase else 0
            nodes += [txt('prob',355,390,f'{hits} successes / {len(perms)} equally likely permutations = 1/{suffix}','result',18),txt('witness',355,424,'Outline = whole suffix; green box = its maximum; ✓ requires the left edge.',size=14)]
            nodes[-2]['opacity']=1 if phase else 0
            formula=(rf'I_{{{suffix}}}=[X_{{{n-suffix+1}}}=\max(X_{{{n-suffix+1}}},\ldots,X_{{{n}}})]' if not phase else rf'\Pr(I_{{{suffix}}}=1)='+r'\frac{'+str(hits)+'}{'+str(len(perms))+'}='+tex(F(1,suffix)))
            ss.append(state(f'{suffix}-{phase}','Select the whole suffix before testing its left edge.' if not phase else 'Locate each suffix maximum, mark successes, then count them.',formula,nodes,'Values are distinct and permutations are equally likely; success means the suffix maximum is at its leftmost position.',dict(n=n,suffix=suffix,hits=hits,total=len(perms),phase=phase,witnesses=[dict(permutation=list(p),left=n-suffix,maximum=max(p[-suffix:]),hit=p[-suffix]==max(p[-suffix:])) for p in perms])))
    return ss

def record_pgf(n):
    p=[F(1)];ss=[]
    for j in range(2,n+1):
        p=conv(p,[F(j-1,j),F(1,j)]);nodes=axes()
        for k,v in enumerate(p):
            xx=105+k*88;h=float(v)*220;nodes +=[rect(f'p{k}',xx-27,335-h,54,h,'result'),txt(f'k{k}',xx,362,k),txt(f'val{k}',xx,318-h,fs(v))]
        mean=sum(k*v for k,v in enumerate(p));var=sum((F(k)-mean)**2*v for k,v in enumerate(p))
        nodes +=[txt('moments',360,65,f'Mean {fs(mean)}; variance {fs(var)}')]
        ss.append(state(j,f'Insert rank {j}: a new record has probability 1/{j}.',rf'G_{{{j}}}(z)=\frac{{{j-1}+z}}{{{j}}}G_{{{j-1}}}(z)',nodes,'Bar areas are exact probabilities and sum to one.',dict(j=j,probabilities=list(map(fs,p)),mean=fs(mean),variance=fs(var))))
    return ss

def coin(n,p):
    ss=[];distribution=[F(1)]
    for j in range(1,n+1):
        distribution=conv(distribution,[1-p,p]);nodes=[]
        for k,v in enumerate(distribution):
            xx=100+k*115;nodes +=[rect(f'bar{k}',xx-32,315-float(v)*180,64,float(v)*180,'result'),txt(f'v{k}',xx,292-float(v)*180,fs(v)),txt(f'k{k}',xx,343,k)]
        for k in range(j):
            xx=100+k*115;nodes +=[line(f'no{k}',xx,75,xx,98,'muted'),line(f'yes{k}',xx,75,xx+115,98,'active')]
        nodes +=[txt('branches',355,42,f'No head: {fs(1-p)}   Head: {fs(p)}'),txt('mean',355,390,f'Mean {fs(j*p)}; variance {fs(j*p*(1-p))}')]
        ss.append(state(j,f'Add independent coin {j}.',rf'G(z)=({tex(1-p)}+{tex(p)}z)^{{{j}}}',nodes,'Every old mass splits into two outgoing masses with total unchanged.',dict(n=j,p=fs(p),probabilities=list(map(fs,distribution)))))
    return ss

def envelope(a,b):
    ss=[];N=10;scale=235/((a+b)*N)
    probes=[('choose',1),('upper',1),('upper',2),('upper',5),('upper',10),('lower',10),('lower',2),('proof',2)]
    for stage,(mode,n) in enumerate(probes):
        nodes=[line('x-axis',55,325,665,325),line('y-axis',55,325,55,80)]
        for name,c,role in [('lower',a,'muted'),('upper',a+b,'active')]:nodes.append(path(name,[(55+58*j,325-scale*c*j) for j in range(1,N+1)],role))
        nodes.append(path('actual',[(55+58*j,325-scale*(a*j+b)) for j in range(1,N+1)],'result'))
        x=55+58*n;actual=a*n+b;bound=(a+b)*n if mode!='lower' else a*n;gap=bound-actual if mode!='lower' else actual-bound
        nodes += [line('gap-probe',x,325-scale*actual,x,325-scale*bound,'active',opacity=1 if mode not in ('choose','proof') else 0),line('probe-guide',x,325,x,325-scale*max(actual,bound),'muted',opacity=.35 if mode not in ('choose','proof') else 0),txt('probe-n',x,347,f'n={n}',size=14)]
        nodes += [txt('constants',355,35,f'Fix c={a}, C={a+b}, n₀=1 before choosing n.',size=17),txt('labels',355,65,f'{a}n ≤ {a}n+{b} ≤ {a+b}n, for every integer n ≥ 1',size=16)]
        if mode=='choose':proof='One pair of constants must work for the whole tail n ≥ 1.'
        elif mode=='upper':proof=f'At n={n}: upper {bound} − actual {actual} = {gap} = {b}({n}−1).'
        elif mode=='lower':proof=f'At n={n}: actual {actual} − lower {bound} = {gap}.'
        else:proof=f'For ALL n ≥ 1: upper gap {b}(n−1) ≥ 0; lower gap {b} > 0.'
        nodes += [txt('proof',355,389,proof,size=15),txt('scope',355,422,'Sampled gaps illustrate the algebra; the algebra proves every n ≥ n₀.',size=14)]
        formula=(rf'({a+b})n-({a}n+{b})={b}(n-1)\ge0\quad(n\ge1)' if mode in ('upper','proof') else rf'({a}n+{b})-{a}n={b}>0' if mode=='lower' else rf'c={a},\quad C={a+b},\quad n_0=1')
        ss.append(state(stage,proof,formula,nodes,'The constants and threshold remain fixed; the algebraic nonnegative gaps establish the inequality for every integer n≥1.',dict(a=a,b=b,c=a,C=a+b,n0=1,mode=mode,n=n,actual=actual,lower=a*n,upper=(a+b)*n,gap=gap)))
    return ss

def error_intervals(n):
    # x=1/n, inverse 1/(1+x), exact two-term error x²/(1+x)
    x=F(1,n);truth=1/(1+x);approx=1-x;err=truth-approx;bound=x*x;ss=[]
    for stage in range(3):
        nodes=[line('axis',80,250,640,250)]
        def xx(v):return 100+float((v-approx)/(bound))*480
        nodes +=[line('interval',xx(approx),210,xx(approx+bound),210,'active',strokeWidth=12),dict(id='truth',type='circle',x=xx(truth),y=210,r=9,role='result',opacity=1 if stage>0 else 0),txt('left',100,280,fs(approx)),txt('right',580,280,fs(approx+bound)),txt('fact',355,100,f'n={n}; exact error {fs(err)}'),txt('meaning',355,365,['The bar is a certified possible interval.','The exact value sits inside the interval.','Error scales as 1/n², not as 1/n.'][stage])]
        ss.append(state(stage,'Invert only after controlling the denominator.',rf'\frac1{{1+1/{n}}}=1-\frac1{{{n}}}+\frac{{1/{n}^2}}{{1+1/{n}}}',nodes,'n ≥ 1 keeps 1+1/n ≥ 1.',dict(n=n,truth=fs(truth),approx=fs(approx),error=fs(err),bound=fs(bound))))
    return ss

def integral(n,power=2):
    S=sum(k**power for k in range(n));I=F(n**(power+1),power+1);endpoint=-F(n**power,2);corr=F(power*n**(power-1),12);ss=[]
    for stage in range(5):
        endpoint_applied=stage>=2;correction_applied=stage>=4;operand_frame=stage in (1,3)
        nodes=[line('x-axis',55,315,420,315),line('y-axis',55,315,55,110)];sx=350/n;sy=165/n**power
        for k in range(n):nodes.append(rect(f'bar{k}',55+k*sx,315-k**power*sy,sx,k**power*sy,'input',opacity=.45))
        for k in range(n+1):nodes.append(txt(f'tick{k}',55+k*sx,341,k,'muted',13))
        nodes.append(txt('axis-label',420,341,'x','muted',14))
        nodes.append(path('curve',[(55+350*j/80,315-(n*j/80)**power*sy) for j in range(81)],'active'))
        for tag,x,y in [('left',55,315),('right',405,150)]:nodes.append(dict(id='endpoint-'+tag,type='circle',x=x,y=y,r=6,role='active',opacity=1 if stage==1 else 0))
        tangent_slope=power*n**(power-1)*sy/sx
        nodes += [line('tangent-left',55,315,115,315,'active',opacity=1 if stage==3 else 0),line('tangent-right',380,150+25*tangent_slope,430,150-25*tangent_slope,'active',opacity=1 if stage==3 else 0)]
        approx=I+(endpoint if endpoint_applied else 0)+(corr if correction_applied else 0)
        area_scale=180/float(I);base=315;eh=float(-endpoint)*area_scale;ch=float(corr)*area_scale
        pieces=[txt('area-key',555,95,'Signed area pieces',size=14),rect('integral-piece',465,base-float(approx)*area_scale,48,float(approx)*area_scale,'input'),rect('endpoint-piece',465 if not endpoint_applied else 540,base-180,48,eh,'error',opacity=.35 if not endpoint_applied else 1),rect('derivative-piece',610 if not correction_applied else 465,base-float(I+endpoint+corr)*area_scale if correction_applied else base-ch,48,ch,'active',opacity=.35 if not correction_applied else 1),txt('integral-key',489,341,'net',size=13),txt('endpoint-key',564,341,'−end',size=13),txt('derivative-key',634,341,'+deriv',size=13)]
        for node in pieces:
            if operand_frame:node['opacity']=0
            nodes.append(node)
        for j,(name,value) in enumerate((('f(0)',0),(f'f({n})',n**power)) if stage!=3 else (('f′(0)',0),(f'f′({n})',power*n**(power-1)))):
            nodes += [dict(**txt(f'operand-name{j}',495+j*115,132,name,size=17),opacity=1 if operand_frame else 0),rect(f'operand-box{j}',450+j*115,148,90,52,'active',opacity=1 if operand_frame else 0),dict(**txt(f'operand-value{j}',495+j*115,180,value,size=21),opacity=1 if operand_frame else 0)]
        nodes.append(dict(**txt('operand-heading',555,95,'Endpoint slopes' if stage==3 else 'Endpoint heights',size=16),opacity=1 if operand_frame else 0))
        derivation=f'−({n**power}−0)/2 = {fs(endpoint)}' if stage==1 else f'({power*n**(power-1)}−0)/12 = {fs(corr)}'
        nodes.append(dict(**txt('derived-correction',555,256,derivation,'result',18),opacity=1 if operand_frame else 0))
        captions=['Compare the left rectangles with the integral.','Read the two endpoint heights, subtract, then halve with a minus sign.','Remove the derived endpoint correction from the integral.','Read the two endpoint slopes; divide their difference by 12.','Add the derived slope correction to recover the exact polynomial sum.']
        step=[f'Integral = {fs(I)}',f'Endpoint heights: f(0)=0, f({n})={n**power}',f'{fs(I)} + ({fs(endpoint)}) = {fs(approx)}',f'f′(x)={power}x^{power-1}; f′({n})={power*n**(power-1)}',f'{fs(I+endpoint)} + {fs(corr)} = {S}'][stage]
        nodes += [txt('eq',355,60,f'Sum {S}; corrected area {fs(approx)}','result'),txt('step',355,386,step,size=17),txt('operation',355,421,captions[stage],size=14)]
        formula=(rf'-\frac{{f({n})-f(0)}}2=-\frac{{{n**power}-0}}2={tex(endpoint)}' if stage==1 else rf'\frac{{f\prime({n})-f\prime(0)}}{{12}}=\frac{{{power*n**(power-1)}-0}}{{12}}={tex(corr)}' if stage==3 else rf'\sum_{{k=0}}^{{{n-1}}} k^{{{power}}}={S}')
        ss.append(state(stage,captions[stage],formula,nodes,'The sum includes 0 and excludes n. Endpoint heights and slopes are evaluated from f(x)=x^power; the displayed quadratic and cubic correction is exact.',dict(n=n,power=power,sum=S,integral=fs(I),endpoint=fs(endpoint),correction=fs(corr),stage=stage,approx=fs(approx),endpointValues=[0,n**power],endpointSlopes=[0,power*n**(power-1)])))
    return ss

def bernoulli(n):
    B=[F(1)]
    for m in range(1,n+1):B.append(-sum(F(comb(m+1,k))*B[k] for k in range(m))/(m+1))
    return B

def bernpoly(m,x):return sum(F(comb(m,k))*v*x**(m-k) for k,v in enumerate(bernoulli(m)))
def bern_scene(m):
    ss=[]
    for tiles in [1,2,3]:
        nodes=[line('axis',70,235,650,235)]
        for tile in range(3):
            pts=[(70+(tile+j/60)*190,235-230*float(bernpoly(m,F(j,60)))) for j in range(61)]
            nodes.append(path(f'tile{tile}',pts,'active',opacity=1 if tile<tiles else .1))
            nodes.append(txt(f'tick{tile}',70+tile*190,360,tile))
        nodes +=[txt('polynomial',355,70,f'B{m}(fractional part of x)'),txt('value',355,398,f'B{m}(0)={fs(bernoulli(m)[m])}; repeated every unit')]
        ss.append(state(tiles,'Repeat the same correction tile on each integer interval.',rf'B_{{{m}}}(x)=\sum_{{k=0}}^{{{m}}}\binom{{{m}}}kB_k x^{{{m}-k}}',nodes,'B1 jumps at integers; Bm is endpoint-continuous for m > 1.',dict(m=m,B=list(map(fs,bernoulli(m))),tiles=tiles)))
    return ss

def residual(n,kind):
    ss=[]
    for j in [n,2*n,4*n]:
        if kind=='harmonic':
            h=sum((F(1,k) for k in range(1,j+1)),F(0));center=float(h)-log(j)-1/(2*j)+1/(12*j*j)-1/(120*j**4);width=F(1,252*j**6);lo=center;hi=center+float(width);label='Euler constant γ'
        else:
            center=log(factorial(j))-(j+.5)*log(j)+j-F(1,12*j);width=F(1,360*j**3);lo=float(center);hi=float(center+width);label='Stirling constant σ'
        nodes=[line('interval',100,220,610,220,'active',strokeWidth=12),line('left',100,200,100,240),line('right',610,200,610,240),txt('n',355,80,f'n = {j}: bracket for {label}'),txt('lo',150,275,f'{lo:.10f}',size=15),txt('hi',560,275,f'{hi:.10f}',size=15),txt('bound',355,365,f'Analytic bracket width {fs(width)}'),txt('zoom',355,400,'Each frame rescales the shrinking interval.','muted')]
        ss.append(state(j,'Peel away the growing terms and bound what remains.',rf'\text{{bracket width}}={tex(width)}',nodes,'Endpoint decimals are illustrative; the symbolic width is rigorous.',dict(n=j,kind=kind,lo=lo,hi=hi,width=fs(width))))
    return ss

def peak(n):
    ss=[];width=sqrt(n);mapping=[dict(s=j,t=n+j*width,exactLog=n*log(1+j/width)-j*width,quadratic=-j*j/2) for j in (-1,0,1)]
    for stage in range(5):
        nodes=[line('t-axis',55,255,665,255),line('height-axis',55,255,55,65),txt('peak-title',355,32,f'Exact normalized density, peak t={n}, width √{n}={fs(width)}',size=16)]
        points=[]
        for j in range(121):
            t=2*n*j/120;value=0 if t==0 else exp(n*log(t/n)-t+n)
            points.append((55+580*j/120,255-165*value))
        nodes.append(path('density',points,'input'))
        nodes += [txt('t-zero',55,277,'0',size=13),txt('t-end',635,277,str(2*n),size=13),txt('t-symbol',665,277,'t',size=14),line('s-axis',180,345,540,345,'muted',opacity=1 if stage>=2 else 0)]
        for item in mapping:
            j=item['s'];t=item['t'];upperx=55+580*t/(2*n);lowerx=345+j*110
            nodes += [line(f'width{j}',upperx,85,upperx,255,'active',opacity=1 if stage>=1 else 0),dict(id=f'original{j}',type='circle',x=upperx,y=255,r=5,role='input',opacity=1 if stage>=1 else 0),dict(**txt(f't-value{j}',upperx,301,fs(t),size=14),opacity=1 if stage>=1 else 0)]
            mapped_y=345-65*item['exactLog'] if stage>=3 else 345 if stage>=2 else 255
            nodes += [dict(id=f'mapped{j}',type='circle',x=lowerx if stage>=2 else upperx,y=mapped_y,r=5,role='input',opacity=1 if stage>=1 else 0),line(f'map-arrow{j}',upperx,306,lowerx,315,'active',arrow=True,opacity=1 if stage==2 else 0),dict(**txt(f's-value{j}',lowerx,332,f's={j}',size=14),opacity=1 if stage>=2 else 0),dict(id=f'quadratic{j}',type='circle',x=lowerx,y=345-65*item['quadratic'],r=8,role='active',opacity=1 if stage==4 else 0)]
            nodes.append(dict(**txt(f'log-value{j}',lowerx,410,f'{item["exactLog"]:.3f}'+(f' ≈ {item["quadratic"]:.1f}' if stage==4 else ''),size=14),opacity=1 if stage>=3 else 0))
        nodes.append(dict(**txt('mapped-axis-label',575,349,'log height' if stage>=3 else 's',size=14),opacity=1 if stage>=2 else 0))
        caption=['Locate the peak of the exact density.','Mark t=n−√n, n, n+√n on the original t scale.','Apply s=(t−n)/√n: the three locations become −1, 0, 1.','Evaluate the exact logarithmic height at those three s coordinates.','Compare with −s²/2: a local approximation, not an exact identity.'][stage]
        formula=(rf't={n}+s\sqrt{{{n}}},\quad s=(t-{n})/\sqrt{{{n}}}' if stage<=2 else rf'L(s)={n}\log(1+s/\sqrt{{{n}}})-s\sqrt{{{n}}}' if stage==3 else r'L(s)=-s^2/2+O(n^{-1/2})\quad(s\text{ in a fixed bounded interval})')
        nodes.append(txt('scale',355,435,caption,size=13))
        ss.append(state(stage,caption,formula,nodes,'The coordinate map is exact. Blue markers are exact finite-n log heights; orange rings are the quadratic approximation. Floating plot values do not prove a uniform tail bound.',dict(n=n,stage=stage,peak=n,width=width,mapping=mapping,approximation=stage==4)))
    return ss

def pqr(n,K=24):
    P=sum((F((n-k)**k*factorial(n-k),factorial(n)) for k in range(n+1)),F(0))
    Q=sum((F(factorial(n),factorial(n-k)*n**k) for k in range(1,n+1)),F(0))
    terms=[F(1)]
    for k in range(1,K+2):terms.append(terms[-1]*F(n,n+k))
    low=sum(terms[:-1]);rho=F(n,n+K+2);tail=terms[-1]/(1-rho)
    return P,Q,low,tail,terms

def upper_decimal(value):
    from decimal import Decimal, localcontext, ROUND_CEILING
    with localcontext() as ctx:
        ctx.prec=3;ctx.rounding=ROUND_CEILING
        return str(Decimal(value.numerator)/Decimal(value.denominator))

def pq_scene(n):
    P,Q,R,E,terms=pqr(n,18);ss=[]
    for count in [3,8,18]:
        partial=sum(terms[:count+1]);nextterm=terms[count+1];bound=nextterm/(1-F(n,n+count+2));nodes=[]
        for k in range(19):
            xx=65+k*32;hh=float(terms[k])*210;nodes.append(rect(f'term{k}',xx,325-hh,25,hh,'result' if k<=count else 'muted',opacity=1 if k<=count else .2))
        nodes +=[txt('title',355,65,f'R({n}): retain terms 0 through {count}'),txt('partial',355,370,f'Partial sum ≈ {float(partial):.8f}'),txt('tail',355,404,f'Proven omitted tail ≤ {upper_decimal(bound)}')]
        ss.append(state(count,'Turn an infinite sum into a certified interval.',rf'0<R({n})-\sum_{{k=0}}^{{{count}}}t_k\le\frac{{t_{{{count+1}}}}}{{1-{n}/({n}+{count}+2)}}',nodes,'Later term ratios decrease, so a geometric tail dominates.',dict(n=n,K=count,P=fs(P),Q=fs(Q),Rlower=fs(partial),Rerror=fs(bound))))
    return ss

def budget(n):
    # Exact rational error propagation: (1+1/n)*(2-1/n), with uncertainty 1/n² in each input.
    a=1+F(1,n);b=2-F(1,n);e=F(1,n*n);total=abs(a)*e+abs(b)*e+e*e;ss=[]
    components=[abs(b)*e,abs(a)*e,e*e];labels=['B times error in A','A times error in B','Product of both errors']
    for stage in range(3):
        nodes=[];x=80
        for i,v in enumerate(components):
            w=550*float(v/total);nodes +=[rect(f'budget{i}',x,170,w,64,'result' if i<=stage else 'muted',opacity=1 if i<=stage else .15),txt(f'label{i}',355,285+i*34,f'{labels[i]}: {fs(v)}','result' if i<=stage else 'muted')];x+=w
        nodes +=[txt('value',355,80,f'n={n}; product center {fs(a*b)}'),txt('bound',355,407,f'Total guaranteed absolute error ≤ {fs(total)}')]
        ss.append(state(stage,'Multiply the centers and carry every error contribution.',r'|(A+e_A)(B+e_B)-AB|\le |B|\delta_A+|A|\delta_B+\delta_A\delta_B',nodes,'Both input errors have absolute value at most 1/n².',dict(n=n,A=fs(a),B=fs(b),delta=fs(e),bound=fs(total),components=list(map(fs,components)))))
    return ss

def check(prompt,choices,correct,explanation):return dict(prompt=prompt,choices=choices,correctIndex=correct,explanation=explanation)
def teach_b(order,states):
    for scene in states:
        c=scene['computed'];meaning=None
        if order==53:meaning=f'The bars are the input values. The pointer visits them right to left, while the outlined bar retains maximum {c["m"]} at the rightmost index {c["j"]+1}. A comparison causes an update only for a strictly larger value; equality preserves the previous rightmost maximum. The tokens count {c["comparisons"]} actual comparisons.'
        elif order==54 and 'witnesses' in c:meaning=f'Every displayed permutation is equally likely. The suffix is its rightmost {c["suffix"]} positions, and the indicator is 1 exactly when the largest value in that suffix is at its left edge. There are {c["hits"]} successes among {c["total"]} permutations, giving probability 1/{c["suffix"]}.'
        elif order==54 and 'probabilities' in c:meaning='The bar over j is the probability of exactly j updates after initialization. These probabilities sum to one; their probability-weighted update counts give the mean, which need not itself be an integer outcome.'
        elif order==57:meaning=f'f(n)={c["a"]}n+{c["b"]} is compared with g(n)=n using the fixed constants c={c["c"]}, C={c["C"]}, and threshold n₀=1. For every integer n≥1, the upper difference is {c["b"]}(n−1)≥0 and the lower difference is {c["b"]}>0. Moving the probe changes n, never the witnesses; the algebra proves the entire tail.'
        elif order==59:
            meaning=[f'f(x)=x^{c["power"]}; the sum uses rectangles at the left endpoints 0,…,{c["n"]-1}. Their heights give sum {c["sum"]}, while the integral area is {c["integral"]}.',f'The endpoint heights f(0)={c["endpointValues"][0]} and f({c["n"]})={c["endpointValues"][1]} produce the correction −(f(n)−f(0))/2={c["endpoint"]}. The minus sign matches the left-endpoint convention.',f'The derived endpoint contribution {c["endpoint"]} changes the integral {c["integral"]} into {c["approx"]}. A changing slope can leave another correction.',f'The endpoint slopes are f′(0)={c["endpointSlopes"][0]} and f′({c["n"]})={c["endpointSlopes"][1]}. The Euler weight B₂/2!=(1/6)/2=1/12 turns their difference into {c["correction"]}.',f'Adding the slope correction {c["correction"]} gives {c["sum"]}. For the displayed quadratic or cubic, polynomial integration makes the remaining Euler correction zero, so this result is exact.'][c['stage']]
        elif order==62 and 'mapping' in c:
            meaning=[f'n={c["n"]} locates the exact density peak because its logarithmic derivative n/t−1 vanishes there. The drawn height is normalized to one.',f'The second logarithmic derivative at the peak is −1/n. Displacements of size √n therefore change the logarithmic height by order one; the marked locations are n−√n, n, n+√n.',f'The new coordinate is s=(t−n)/√n. The three original locations become s=−1,0,1 exactly; this is a relabeling of positions, not an approximation.',f'The lower points are exact finite-n logarithmic heights L(s)=n log(1+s/√n)−s√n at s=−1,0,1. They use the same three locations after the exact coordinate change.',f'The orange rings are the quadratic values −s²/2, compared with the blue exact log heights. Their visible separation is approximation error; the local expansion applies on fixed bounded s intervals and does not by itself bound the unseen tail.'][c['stage']]
        if meaning:scene['teachingExplanation']=meaning
    return states

def demo(id,title,kind,main,helpstates,c,hc,connection):
    order=int(id.split('-')[0][1:]);main=teach_b(order,main);helpstates=teach_b(order,helpstates)
    return dict(id=id,title=title,model=dict(kind=kind,arithmetic='Exact integers/Fractions except explicitly labeled curve and transcendental displays',computedStates=[s['computed'] for s in main]),states=main,transitions=[dict(from_=a['id'],to=b['id'],action='Step',explanation=b['caption']) for a,b in zip(main,main[1:])],check=c,simplerHelp=dict(intro='Try the smaller concrete case below. Follow one change at a time, then connect it to the formula.',model=dict(kind=kind+'-smaller',computedStates=[s['computed'] for s in helpstates]),states=helpstates,steps=[dict(action='Step',text=s['caption']) for s in helpstates],connection=connection,check=hc))

# Each passage receives its own concrete trace. These are worked instances, never
# substitutes for the universal proof in the accompanying text.
V={
47:[('Coefficient shift',shelf([2,0,5,1]),shelf([1,3])),('A longer shift',shelf([3,1,4],2),shelf([2,1],2)),('A zero coefficient is a position',shelf([0,2,0,4]),shelf([0,2]))],
48:[('Read a product diagonal',convolution([1,2,1],[2,1]),convolution([1,1],[1,2])),('Prefix sums are convolution',convolution([2,1,3],[1,1,1]),convolution([2,3],[1,1])),('Signed coefficients cancel',convolution([1,-1],[1,1,1]),convolution([1,-1],[1,1]))],
49:[('Position weights',transform([2,3,1,2],'weight'),transform([1,2,1],'weight')),('Parity cancellation',transform([2,3,1,2],'parity'),transform([1,2,3],'parity')),('Integration changes positions',transform([3,4,3],'integrate'),transform([2,2],'integrate'))],
50:[('Build a recurrence sequence',recurrence(2,3,6),recurrence(1,1,4)),('Change the initial conditions',recurrence(1,4,6),recurrence(2,1,4)),('Check the boundary numerator',recurrence(0,2,6),recurrence(0,1,4))],
51:[('Partition distinct labels',labeled(3),labeled(2)),('Compare OGF product weights',convolution([1,1,1],[1,1]),convolution([1,1],[1,1])),('Bernoulli coefficients',bern_scene(2),bern_scene(1))],
52:[('Distinct-variable choices',symmetric([2,3,5]),symmetric([1,2])),('Repeated-variable choices',symmetric([1,2],True),symmetric([1],True)),('Power-sum reconstruction',symmetric([1,3,4]),symmetric([2,3]))],
53:[('Strict comparisons keep ties',scan([3,7,2,7,4]),scan([2,2])),('An update on every comparison',scan([5,4,3,2]),scan([3,2,1])),('No update is also a valid execution',scan([1,2,3,4]),scan([1,2]))],
54:[('Uniform inputs',average(3),average(2)),('One suffix at a time',average(4),average(3)),('Distribution and expectation differ',record_pgf(4),record_pgf(3))],
55:[('Insert a new rank',record_pgf(4),record_pgf(3)),('Read moments from mass',record_pgf(5),record_pgf(3)),('Longer inputs retain exact probabilities',record_pgf(6),record_pgf(4))],
56:[('Split mass with a biased coin',coin(3,F(1,3)),coin(2,F(1,2))),('Change the bias',coin(3,F(2,3)),coin(2,F(1,3))),('A deterministic boundary',coin(3,F(1)),coin(2,F(0)))],
57:[('Prove two fixed envelopes',envelope(3,5),envelope(1,2)),('Change constants, keep quantifiers',envelope(2,7),envelope(2,1)),('A tight order need not be an exact equivalent',envelope(5,2),envelope(3,1))],
58:[('An exact inverse remainder',error_intervals(4),error_intervals(2)),('A smaller input parameter',error_intervals(10),error_intervals(3)),('Error propagation through a product',budget(8),budget(2))],
59:[('Rectangles versus area',integral(4),integral(2)),('Endpoint correction',integral(5),integral(3)),('Derivative correction',integral(4,3),integral(2,3))],
60:[('The discontinuous first tile',bern_scene(1),bern_scene(1)),('The continuous second tile',bern_scene(2),bern_scene(2)),('An exact polynomial termination',integral(5,3),integral(3,3))],
61:[('Harmonic residual brackets',residual(4,'harmonic'),residual(2,'harmonic')),('Factorial residual brackets',residual(4,'factorial'),residual(2,'factorial')),('Exponentiation needs an error budget',budget(12),budget(3))],
62:[('Find the dominant neighborhood',peak(9),peak(4)),('Rescale the neighborhood',peak(25),peak(4)),('Bound a removed tail',pq_scene(5),pq_scene(2))],
63:[('Finite and infinite families',pq_scene(4),pq_scene(2)),('Control the infinite tail',pq_scene(8),pq_scene(3)),('The sum-to-area correction',integral(6),integral(2))],
64:[('Carry every product error',budget(10),budget(2)),('Compute before fitting',pq_scene(12),pq_scene(3)),('Audit the final precision',budget(20),budget(4))]
}

# A transfer problem uses data not used by its associated trace.
def numeric_check(prompt,answer,explanation):
    answer=F(answer);choices=[fs(answer+1),fs(answer),fs(answer-1)]
    return check(prompt,choices,1,explanation)
def question(order,j,help=False):
    """Passage-specific transfer checks; distractors represent conceptual errors.

    A help check stays on the same concept with a smaller instance or a single
    proof step. No generic answer±1 distractors or lesson-wide cloned prompts.
    """
    def q(prompt,choices,correct,why):return check(prompt,choices,correct,why)
    if order==47:
        if j==0:
            return q('G=1+0z+3z². What is [z²]G?' if help else 'G=2+0z+5z². What is [z²]G?', ['3','3z²','0'] if help else ['5z²','5','0'],0 if help else 1,'The coefficient operator returns the number on the exponent-2 shelf. It does not return the whole monomial or discard the zero-position shelf.')
        if j==1:
            return q('To shift G=2+z left one position and remain a power series, which expression works?' if help else 'To shift a general G left two positions within Q[[z]], which expression works?', ['(G−2)/z','G/z','zG'] if help else ['G/z²','z²G','(G−a₀−a₁z)/z²'],0 if help else 2,'Remove the leading coefficients before division so no negative exponents remain. Bare division leaves negative powers when those coefficients are nonzero; multiplication shifts in the opposite direction.')
        return q('At z=1 the factorial terms are 1,1,2,6,24,… . Can their numerical sum converge?' if help else 'Σn!zⁿ is a formal series. May we therefore evaluate it at z=1 as a convergent numerical sum?', ['No; these terms do not approach zero','Yes; all formal series converge','No; the formal coefficient sequence is invalid'] if help else ['Yes; every formal series converges at 1','No; the terms n! do not tend to zero','No; factorial coefficients cannot form a formal series'],0 if help else 1,'A formal series is its full indexed coefficient sequence, including zeros. Formal existence imposes no convergence requirement. At z=1 the factorial terms fail the necessary zero-term condition, although the formal object is valid.')
    if order==48:
        if j==0:
            return q('Which pairs contribute to [z¹]FG?' if help else 'Which products contribute to [z³]FG?', ['a₀b₁+a₁b₀','a₁b₁','a₀b₀'] if help else ['a₃b₃','a₀b₃+a₁b₂+a₂b₁+a₃b₀','a₀b₀+a₁b₁+a₂b₂+a₃b₃'],0 if help else 1,'Exponents add, so select exactly i+j equal to the target degree. Matching equal indices or multiplying only the target-index coefficients selects the wrong diagonals.')
        if j==1:
            return q('G=2+3z. What is [z¹]G/(1−z)?' if help else 'A visible ones row contains only b₀,b₁,b₂. Can its degree-4 product coefficient certify the infinite prefix sum?', ['5','6','3'] if help else ['Yes; three ones represent all ones','No; b₃ and b₄ may contribute to degree 4','Only the largest coefficient matters'],0 if help else 1,'The infinite ones row accumulates a₀+…+aₙ, giving 2+3=5 in the small case. A truncated row must extend through the target degree; omitted high-index ones can remove valid pairs. This is addition of contributions, not their product or largest value.')
        return q('What is the coefficient of z in (1−z)(1+z)?' if help else 'Why is multiplication of three formal series associative?', ['0, because 1 and −1 cancel','−1, because the negative term wins','2, because there are two pairs'] if help else ['All infinite numerical series can be rearranged','Every coefficient regroups a finite set of triples i+j+k=n','Negative coefficients are forbidden'],0 if help else 1,'Signed contributions are added algebraically, so 1+(−1)=0. At each fixed degree there are only finitely many index triples; finite regrouping proves associativity without analytic convergence or nonnegative coefficients.')
    if order==49:
        if j==0:
            return q('For G=1+2z+3z², what is [z²]zG′?' if help else 'Which operation multiplies aₙ by n² without changing its exponent?', ['6','3','2'] if help else ['G″','(z d/dz)²G','z²G'],0 if help else 1,'Each Euler operator z d/dz weights by the original exponent while restoring its position. Two applications give n²; G″ instead gives n(n−1) and lowers degrees. A bare shift does not weight coefficients. In the small case 2·3=6.')
        if j==1:
            return q('For G=1+2z+3z², where does 3 remain after the even filter?' if help else 'With ω³=1 and ω≠1, which exponents survive (G(z)+ω⁻¹G(ωz)+ω⁻²G(ω²z))/3?', ['At exponent 2','At exponent 1','It cancels'] if help else ['n≡0 mod 3','All n','n≡1 mod 3'],0 if help else 2,'A finite geometric weight is one exactly when n−r is divisible by the filter modulus, and zero otherwise. Filtering preserves exponents; it does not compress shelves. Even exponent 2 remains at 2.')
        return q('What is ∫₀ᶻ(2+2t)dt?' if help else 'Why does integrating G′ from zero to z give G−a₀ rather than G?', ['2z+z²','2+2z','2z+2z²'] if help else ['Differentiation erased the constant; the zero lower endpoint fixes the new constant to zero','Integration always returns G regardless of constants','All coefficients must be divided by zero'],0 if help else 0,'Integrate each monomial by dividing by its new exponent and shifting right. The constant of the definite formal integral is zero; differentiation cannot recover a₀. In the small case the linear term becomes z², not 2z².')
    if order==50:
        if j==0:
            u,v=(1,1) if help else (3,4)
            return q(f'For a₀={u}, a₁={v}, aₙ=2aₙ₋₁+aₙ₋₂ (n≥2), what numerator accompanies 1−2z−z²?', [f'{u}+{v}z',f'{u}'+('−' if v-2*u<0 else '+')+f'{abs(v-2*u)}z','1'],1,'The numerator is a₀+(a₁−2a₀)z: the shifted recurrence removes an additional 2a₀z. Merely copying the two initial values misses that boundary subtraction; numerator 1 generally encodes different initial values.')
        if j==1:
            return q('Can 1−z have a formal inverse in Q[[z]]?' if help else 'Which denominator has no multiplicative inverse in Q[[z]]?', ['Yes; its constant is 1','No; it has a numerical zero at z=1','Only after selecting initial values'] if help else ['2−z','1+z²','z−z²'],0 if help else 2,'The constant coefficient of a product is the product of the constants. An inverse needs constant product 1, so a zero denominator constant is impossible; any nonzero rational constant allows recursive inversion. Numerical zeros away from zero and recurrence initial values do not decide this.')
        return q('If the recurrence starts with a₀=0,a₁=1, what must [z⁰]G equal?' if help else 'After checking a rational G through degree 20, what proves the recurrence for every n≥2?', ['0','1','2'] if help else ['Twenty correct values are a proof','Multiplying by the denominator and comparing coefficients at arbitrary degree n','A plot without visible disagreement'],0 if help else 1,'The initial constant must be a₀, so it is zero in the small case. An arbitrary-degree coefficient equation covers every n; finitely many values or a plot only test the implementation.')
    if order==51:
        if j==0:
            n=2 if help else 4
            return q(f'Choose a first group of size {1 if help else 2} from {n} distinct labels. How many label allocations precede building the two structures?', ['2','1','4'] if help else ['4','6','16'],0 if help else 1,'Choose the first group by a binomial coefficient; the complement is then forced. This gives C(2,1)=2 or C(4,2)=6. Treating labels as interchangeable loses choices, while unrestricted assignments ignore the fixed group size.')
        if j==1:
            return q('The ordinary product (1+z)(1+z) has coefficient 2 at z. Does that coefficient include an extra factorial?' if help else 'For aₙ=bₙ=1, what sequence is recovered from the EGF product eᶻeᶻ?', ['No; ordinary coefficients are raw values','Yes; all series are exponential','Only when z=1'] if help else ['n+1','2ⁿ/n!','2ⁿ'],0 if help else 2,'An EGF stores its sequence divided by n!, so n![zⁿ]e²ᶻ=2ⁿ. The number 2ⁿ/n! is only the stored coefficient; n+1 belongs to the OGF product (1−z)⁻². Ordinary coefficients have no extra recovery factorial.')
        return q('The inverse series starts 1−z/2+… . What is B₁, after multiplying the coefficient by 1!?' if help else 'In z/(eᶻ−1)=1−z/2+z²/12+…, what is B₂?', ['−1/2','1/2','0'] if help else ['1/12','1/6','1/24'],0 if help else 1,'The generating function stores B₂/2!, so B₂=2!/12=1/6; neither the raw coefficient nor another division is correct. For n=1, multiplication by 1! leaves the coefficient −1/2 unchanged; changing its sign or setting it to zero would violate the reciprocal identity.')
    if order==52:
        if j==0:
            return q('For variables 1,2, what is e₂?' if help else 'For variables 2,3,5, does e₂ include a term 3²?', ['2','5','7'] if help else ['Yes; every square is a pair','No; elementary sums use distinct indices','Only if the variables are positive'],0 if help else 1,'Elementary e₂ selects two distinct positions once, so for 1,2 it is only 1·2=2. Repeating the same index, as in 3², belongs to a homogeneous sum. Positivity does not change the selection rule.')
        if j==1:
            return q('With the one variable x₁=2, what is h₂?' if help else 'Given p₁=3, p₂=5 and h₁=3, what does 2h₂=p₁h₁+p₂ give?', ['0','2','4'] if help else ['14','7','4'],2 if help else 1,'Repetition is allowed, so one variable contributes its square: 2²=4. For the recurrence, divide 3·3+5=14 by the index 2 to obtain 7. Omitting division or forbidding repeated variables changes the quantity.')
        return q('For variables 2,3, p₁=5 and p₂=13. What is e₂=(p₁²−p₂)/2?' if help else 'To use [zⁿ]G=(1/(2πi))∮G(z)/zⁿ⁺¹ dz on a circle, what must be supplied?', ['6','19','12'] if help else ['Only a formal coefficient sequence','Analyticity on and inside the circle and positive orientation','Any contour through a pole'],0 if help else 1,'Newton’s minus sign removes same-index squares: (25−13)/2=6, rather than adding them or omitting the divisor. Cauchy extraction needs analytic hypotheses and counterclockwise orientation; formal existence alone does not authorize integration, and crossing a singularity invalidates the stated formula.')
    if order==53:
        if j==0:
            return q('Scan [2,2] from the right with strict > updates. Which index wins?' if help else 'If strict > is changed to ≥ in a right-to-left maximum scan, which tied maximum is returned?', ['1','2','Both indices'] if help else ['The rightmost','The leftmost','No maximum can be found'],1,'Strict comparison keeps the already seen rightmost tie. Allowing equality replaces it with each earlier equal maximum, leaving the leftmost. Both versions still find a maximum, but they have different index specifications.')
        if j==1:
            n=3 if help else 6
            return q(f'A decreasing list has {n} entries. Under the stated right-to-left scan, how many value comparisons, loop tests and updates occur?', [f'{n-1}, {n}, {n-1}',f'{n}, {n}, {n}',f'{n-1}, {n-1}, {n-1}'],0,'There is one comparison/update per earlier entry, giving n−1. The loop test also runs once to terminate, giving n. Counting initialization as an update or omitting the final test creates the other totals.')
        return q('With one entry, how many loop tests and value comparisons occur?' if help else 'A scan with n=7 makes A=2 updates. How many comparison exits take the skip edge?', ['1 test, 0 comparisons','0 tests, 0 comparisons','1 test, 1 comparison'] if help else ['5','6','4'],0 if help else 2,'Comparison flow is n−1=A+skips; hence 6−2=4 skips. The singleton still executes the final loop test but has no earlier entry to compare. Counting n comparison exits incorrectly includes the terminal test.')
    if order==54:
        if j==0:
            n=2 if help else 5
            return q(f'In a uniform permutation of distinct values, why is a designated first position of a {n}-item suffix its maximum with probability 1/{n}?', ['Each possible maximum position is equally likely','Every real dataset has this property','The indicators must first be proved independent'],0,'Uniform relative ordering makes the maximum position symmetric. Tied or nonuniform datasets need a different model. Independence among several record indicators is unnecessary for this single-suffix probability.')
        if j==1:
            return q('Two record indicators have means 1/2 and 1/3. What is the mean of their sum?' if help else 'E[A]=Hₙ−1 is logarithmic. Does that make the maximum scan logarithmic-time?', ['5/6 without requiring independence','1/6 by multiplying means','5/6 only if independent'] if help else ['Yes, updates are the only work','No; n−1 comparisons still occur on every input','Only if n is a power of two'],0 if help else 1,'Linearity adds means without independence, yielding 5/6 in the small case. Expected updates count only one kind of work: the scan still compares all earlier entries, so its stated ordinary cost remains linear. The input size being a power of two is irrelevant.')
        return q('A three-item all-equal list is scanned with strict >. What is A?' if help else 'An expected update count is 13/12. What does that say about one run?', ['0','H₃−1','2'],0,'Every equality fails the strict improvement test, so A=0. H₃−1 belongs to the uniform distinct-permutation model and is invalid for this tied input; n−1 is only the worst-case number of updates.' ) if help else q('An expected update count is 13/12. What does that say about one run?', ['Its integer count may differ; 13/12 is an average under the input model','Every run makes 13/12 updates','Every run makes at most 13/12 updates'],0,'Each run has an integer update count; a fractional mean combines different outcomes and is neither an individual count nor a worst-case bound. The uniform distinct-permutation model must not be transferred unchanged to tied inputs.')
    if order==55:
        if j==0:
            return q('At suffix size 2, the relative rank is uniformly 1 or 2. What update PGF factor results?' if help else 'Why can the Bernoulli factors for the permutation record count be multiplied?', ['(1+z)/2','1+z','z²'],0,'The two ranks give no update or one update with probability 1/2; normalization makes the factor sum to one at z=1.') if help else q('Why can the Bernoulli factors for the permutation record count be multiplied?', ['All indicator variables are always independent','The bijection makes the relative ranks independent uniforms','Linearity of expectation proves independence'],1,'The rank-sequence bijection maps n! equally likely permutations to the full product of rank choices, establishing independence. Being an indicator alone does not establish it, and linearity applies even to dependent variables.')
        if j==1:
            return q('For G=(1+z)/2, G′(1)=1/2 and G″(1)=0. What is the variance?' if help else 'A PGF has G′(1)=3/2 and G″(1)=3/2. What is the variance?', ['1/4','0','1/2'] if help else ['3/2','3/4','3'],0 if help else 1,'Use G″(1)+G′(1)−G′(1)². This gives 1/4 or 3/4. G″ alone is the factorial second moment, not variance; omitting the squared mean leaves the raw second moment.')
        return q('From p₁,₀=1, what is p₂,₁?' if help else 'Why does pₙ,ⱼ=((n−1)pₙ₋₁,ⱼ+pₙ₋₁,ⱼ₋₁)/n preserve total mass one?', ['1/2','1','0'] if help else ['The two sums contribute (n−1)/n and 1/n','Each coefficient equals one','All but one coefficient vanish'],0,'Summing over all indices shifts the second total without changing it. The old total is one, so the weighted totals add to one. At n=2, the new-record branch gets mass 1/2. Normalization is about the sum of masses, not each mass or concentration at a single outcome.')
    if order==56:
        if j==0:
            return q('Two independent fair coins have what probability of exactly one head?' if help else 'B is a fair Bernoulli variable and X=B+B. Which is its PGF?', ['1/2','1/4','1'] if help else ['(1+z)²/4','(1+z²)/2','z'],0 if help else 1,'Independent coins have the two disjoint one-head outcomes HT and TH, totaling 1/2. Reusing the same B instead makes the sum only 0 or 2, with probability 1/2 each. Multiplying marginal PGFs needs independence; equal marginals are insufficient.')
        if j==1:
            return q('For two independent p=1/3 coins, what is Var(S)?' if help else 'If X=Y and Var(X)=1, what is Var(X+Y)?', ['2/3','4/9','2/9'] if help else ['2','4','1'],1,'For independent coins add two variances (1/3)(2/3), giving 4/9; adding means would give 2/3. If X=Y, covariance is 1 and X+Y=2X has variance 4, so variance addition without the cross term fails.')
        return q('In the p=0 help scene, what is P(|S−0|≥1)?' if help else 'A variable has variance 2. Which Chebyshev bound applies to P(|X−E[X]|≥1/2)?', ['0','1','1/2'] if help else ['8 as a probability','1 after capping the bound','1/8'],0 if help else 1,'Chebyshev gives σ²/t²=8 before capping, so the usable probability bound is min(1,8)=1; taking its reciprocal is invalid. In the deterministic p=0 case σ²=0, all mass is at zero and any positive deviation has probability zero.')
    if order==57:
        if j==0:
            return q('For f(n)=n+2, which fixed bound holds for all n≥1?' if help else 'Which quantifier order defines f=O(g)?', ['f(n)≤3n','Choose Cₙ=f(n)/n separately','Check n=1 only'] if help else ['For each n choose a new Cₙ','Choose C>0,n₀; then all n≥n₀ obey |f|≤C|g|','Check a million points'],0 if help else 1,'The fixed witness in the small case follows from 3n−(n+2)=2(n−1)≥0. A bound needs one constant and threshold covering every tail index; changing the constant with n or finite testing does not establish that quantifier.')
        if j==1:
            return q('For f(n)=2n+1, which lower bound works for every n≥1?' if help else 'Under the absolute-value convention, which statement about f(n)=−3n is correct?', ['2n≤f(n)','3n≤f(n)','f(n)=o(n)'] if help else ['f=Θ(n)','f has no growth class because it is negative','f=o(n)'],0,'The magnitude of −3n is 3n, giving matching fixed bounds; its ratio magnitude to n is not tending to zero. In the small case f−2n=1, whereas 3n exceeds f for n>1. Signs do not prohibit a bound written with absolute values.')
        return q('Does f(n)=3n+1 satisfy f∼n?' if help else 'If f=Θ(n), does it follow that f/n→1?', ['No; the ratio tends to 3','Yes; both grow linearly','Only because f is positive'] if help else ['Yes; Θ specifies the leading coefficient','No; f=7n is a counterexample','No function in Θ(n) can have a ratio limit'],0 if help else 1,'Asymptotic equivalence requires ratio limit one. Θ only supplies upper and lower constant bounds: 3n+1 has ratio limit 3 and 7n has limit 7. Some Θ(n) functions do have a ratio limit, so denying all such limits is also wrong.')
    if order==58:
        if j==0:
            return q('What exact error remains in 1/(1+1/2)≈1−1/2?' if help else 'Two independently written O(1/n) terms are subtracted. What can be concluded?', ['1/6','0','1/4'] if help else ['The result is exactly zero','The result is O(1/n), possibly nonzero','The result must be Θ(n)'],0 if help else 1,'The exact small remainder is x²/(1+x)=(1/4)/(3/2)=1/6. Distinct O-terms can represent different functions, so cancellation is not guaranteed; triangle inequality still preserves their upper order.')
        if j==1:
            return q('If |ε|≤1/2, how small can |1+ε| be?' if help else 'If log T=log A+O(n⁻²), A>0, what error statement follows?', ['At least 1/2','It may be zero','Exactly 1'],0,'Reverse triangle inequality gives |1+ε|≥1−|ε|≥1/2. It need not equal one, but cannot vanish under this bound.') if help else q('If log T=log A+O(n⁻²), A>0, what error statement follows?', ['T=A+O(n⁻²) for every growing A','T=A(1+O(n⁻²))','T=A exactly'],1,'Exponentiation makes the small logarithmic error a relative error. Multiplying by an unbounded A changes the absolute scale, and an O-term need not be zero.')
        return q('For A=B=1 and |e_A|,|e_B|≤1/2, which guaranteed product-error bound includes the cross term?' if help else 'An expansion is proved for each fixed order m as n→∞. May m be replaced by n without another argument?', ['1','5/4','1/4'] if help else ['Yes; more terms always improve accuracy','No; constants and thresholds may depend on m','Only if the first coefficient is positive'],1,'The small product budget is 1/2+1/2+1/4=5/4; omitting the cross term underestimates it. In an asymptotic expansion the fixed-order error constants may grow with order, so a varying-order conclusion needs uniform estimates. Coefficient positivity alone supplies none.')
    if order==59:
        if j==0:
            return q('For f(x)=x² on [0,2], is the left-rectangle sum below or above the integral?' if help else 'Why is Σₖ₌₀³k²=14 smaller than ∫₀⁴x²dx=64/3?', ['Below; each left rectangle lies under the increasing curve','Above; the rectangles have width one','Equal; both describe area'] if help else ['The left-endpoint rectangles lie below the increasing curve','The integral discards the endpoint at zero','All sums underestimate all integrals'],0,'Monotonic increase on each unit interval places its left rectangle below the curve. Width alone does not decide the sign; changing a single endpoint does not change the integral, and decreasing functions reverse this comparison.')
        if j==1:
            return q('For f(x)=x on [0,2], what is the half-open endpoint correction?' if help else 'Why does the sawtooth remainder vanish for a linear f on integer endpoints?', ['−1','+1','0'] if help else ['The derivative is constant and each sawtooth tile has zero integral','Every continuous f has zero remainder','The sawtooth is zero everywhere'],0,'The endpoint term is −(f(b)−f(a))/2, giving −1 for the small linear example. A constant slope factors out of each zero-mean tile. The sawtooth is not identically zero, and varying slopes generally retain a remainder.')
        return q('For f=x³ on [0,2], what is Δf′/12?' if help else 'For f=x² on [0,3], the integral plus endpoint correction is 9/2. Which first derivative correction yields the exact sum 5?', ['1','2','0'] if help else ['−1/2','1/2','3'],0 if help else 1,'Use the difference of endpoint slopes divided by 12. For x³ on [0,2] it is (12−0)/12=1; for x² on [0,3] it is (6−0)/12=1/2. The sign is positive here and the derivative correction is distinct from the endpoint value correction.')
    if order==60:
        if j==0:
            return q('B₁(t)=t−1/2. What happens when this tile repeats across an integer?' if help else 'Using 1+3B₁+3B₂=0 and B₁=−1/2, what is B₂?', ['It jumps from 1/2 back to −1/2','It stays continuous','It becomes identically zero'] if help else ['1/12','1/6','−1/6'],0 if help else 1,'The recurrence gives 3B₂=1/2, hence B₂=1/6. The polynomial B₁ has unequal endpoint values, so its periodic version jumps; zero mean does not mean zero values or continuity.')
        if j==1:
            return q('B₂(0)=B₂(1)=1/6. Why does repeating this tile cause no value jump?' if help else 'For the half-open Euler formula through B₂, if ∫ₐᵇ|f″|dx=6, what follows from the supremum bound?', ['Adjacent endpoint values match','Every derivative must match too','The tile is constant'] if help else ['R₂=+1/2 exactly','|R₂|≤1/2','R₂=0'],0 if help else 1,'The bound is |R₂|≤(1/12)∫|f″|=1/2; it supplies neither equality nor zero. Matching tile endpoint values gives continuity only; the nonconstant tile can have differing endpoint derivatives.')
        return q('The fourth derivative of a cubic is zero. What does this do to the fourth-order remainder integral?' if help else 'May the first omitted Euler correction bound the remainder for every smooth function?', ['It makes that remainder exactly zero','It only makes it approximately zero','It makes every earlier remainder zero'],0,'A zero integrand gives an exactly zero fourth-order remainder. It says nothing by itself about lower-order remainders.') if help else q('May the first omitted Euler correction bound the remainder for every smooth function?', ['Yes; smoothness is enough','No; the stated derivative-sign hypotheses or another suitable theorem are required','No Euler remainder can ever be bounded'],1,'Smoothness permits integration by parts but does not force first-omitted-term control. The additional sign condition supplies that stronger theorem; general integral bounds remain available without it.')
    if order==61:
        if j==0:
            return q('The harmonic bracket has width 1/(252n⁶). How does doubling n change its width?' if help else 'Hₙ−log n decreases and is bounded below. What has been established?', ['It becomes 1/64 as wide','It becomes half as wide','It becomes zero'],0,'Replacing n by 2n multiplies n⁶ by 64. The finite width shrinks but remains positive; decimal labels do not set it to zero.') if help else q('Hₙ−log n decreases and is bounded below. What has been established?', ['An exact decimal value for γ','Existence of a finite limit γ','Convergence of every Bernoulli expansion at fixed n'],1,'Monotone bounded convergence proves existence of the limit, not its exact decimal value or convergence of a separate infinite asymptotic expansion.')
        if j==1:
            return q('Does a small factorial residual bracket by itself prove its limit equals (1/2)log(2π)?' if help else 'Euler summation gives n!∼C√n(n/e)ⁿ. What identifies C?', ['No; the Wallis comparison identifies the constant','Yes; a rounded residual is exact','No such limit exists'],0,'A bracket illustrates an approximation; the independent Wallis comparison determines the exact constant. Numerical proximity is not equality, and the residual convergence argument still establishes a limit.') if help else q('Euler summation gives n!∼C√n(n/e)ⁿ. What identifies C?', ['Local endpoint derivatives alone','The central-binomial comparison from Wallis integrals, giving C=√(2π)','Replacing C by the nearest integer'],1,'Local correction terms leave an undetermined integration constant. Wallis gives binom(2n,n)∼4ⁿ/√(πn); comparison with (√2/C)4ⁿ/√n yields C=√(2π). Rounding cannot identify that constant.')
        return q('In exp(x), where does its x²/2 term come from?' if help else 'When exponentiating 1/(12n)+O(n⁻³), which term appears at order n⁻²?', ['The quadratic Taylor term','An independent Euler correction','It never appears'],0,'The exponential Taylor series contains x²/2. It is produced by exponentiation even if the exponent has no quadratic term.') if help else q('When exponentiating 1/(12n)+O(n⁻³), which term appears at order n⁻²?', ['0','1/(288n²)','1/(144n²)'],1,'The quadratic Taylor contribution is (1/(12n))²/2=1/(288n²). Omitting it loses an order of precision; forgetting the Taylor divisor doubles it. The stated exponent error is too small to alter this coefficient.')
    if order==62:
        if j==0:
            n=4 if help else 16
            return q(f'For t^{n}e⁻ᵗ, which peak and width scale follow from the log derivatives?', [f'Peak {n}, width scale {int(n**.5)}',f'Peak {int(n**.5)}, width scale {n}',f'Peak {n}, width scale 1'],0,'The first log derivative n/t−1 vanishes at t=n; the second there is −1/n. An order-√n displacement therefore changes log height by order one. Swapping peak and width or keeping a fixed width confuses these roles.')
        if j==1:
            return q('If n=4 and s=1, where is t=n+s√n in the smaller peak scene?' if help else 'A Gaussian approximation is uniform on every fixed bounded s-interval. Does that alone justify integration over all s?', ['6','5','8'] if help else ['Yes; pointwise Taylor expansions control all tails','No; an integrable tail bound is still needed','No; local expansions have no use'],0 if help else 1,'The scaled location is 4+1·2=6. Bounded-interval control does not control an unbounded integration domain; the exponentially bounded outer part supplies the missing step. Local expansion remains useful once that tail is controlled.')
        return q('For fixed r>0, does the upper bound 2e⁻ⁿʳ mean the removed tail is exactly zero?' if help else 'A local remainder obeys |r(v)|≤Cv³/². What order follows after integration against ne⁻ⁿᵛ on a fixed neighborhood?', ['No; it is positive but exponentially controlled','Yes; sufficiently small means zero','It grows exponentially'],0,'The bound controls a nonzero positive tail; it tends to zero faster than every fixed inverse power, but does not turn the tail into zero.') if help else q('A local remainder obeys |r(v)|≤Cv³/². What order follows after integration against ne⁻ⁿᵛ on a fixed neighborhood?', ['O(n⁻³/²), by the gamma-moment integral','O(n³/²)','Zero exactly'],0,'Extending the nonnegative majorant to infinity gives CΓ(5/2)n⁻³/² after q=nv. This bounds the integrated remainder without making it zero. The separately controlled exponential tail does not reverse the power of n.')
    if order==63:
        if j==0:
            return q('In the smaller family rows, which family continues after every finite prefix?' if help else 'For positive integer n, which definition requires an infinite-tail argument?', ['R','P','Q'] if help else ['Only P','Only R','All three'],0 if help else 1,'P and Q end at k=n, while R has positive terms for all k≥0. Similar leading growth does not change these exact supports; an R prefix is a lower bound rather than the full sum.')
        if j==1:
            return q('A positive omitted tail starts with t and later ratios are ≤1/2. What upper bound follows?' if help else 'Why does Q(n)+R(n)=n!eⁿ/nⁿ hold exactly?', ['t/2','2t','t²'] if help else ['Their asymptotic leading terms match','Their reindexed ranges partition j≥0 in Σnʲ/j!','Every displayed finite R prefix equals R'],1,'The geometric bound in the small case is t/(1−1/2)=2t, not t/2 or t². For the identity, Q covers 0≤j<n and R covers j≥n; these disjoint ranges exhaust the exponential series. Matching leading terms or truncating R cannot prove exact equality.')
        return q('In the small polynomial sum-to-area scene, why is an endpoint correction necessary?' if help else 'A derivation of P has final error O(n⁻¹/²). Can it determine the coefficient multiplying n⁻¹/²?', ['Sampled rectangles and the smooth area differ','The integral is always exactly the sample sum','Rounding the area removes the error'],0,'The left rectangles differ from the smooth area even when both values are exact. Endpoint and derivative corrections account for this structure; rounding does not supply a derivation.') if help else q('A derivation of P has final error O(n⁻¹/²). Can it determine the coefficient multiplying n⁻¹/²?', ['Yes; that coefficient must be zero','No; the unknown error is already of that size','Yes; fitting three values proves it'],1,'An O(n⁻¹/²) remainder can contain any fixed multiple of n⁻¹/². A sharper estimate is needed to isolate that coefficient; neither declaring it zero nor numerical fitting removes the ambiguity.')
    if order==64:
        if j==0:
            return q('For A=B=1 and errors at most 1/4, what product-error bound includes all three terms?' if help else 'To retain absolute O(n⁻²) after multiplying by a √n-sized factor, which input error suffices?', ['1/2','9/16','1/16'] if help else ['O(n⁻³/²)','O(n⁻⁵/²)','O(n⁻¹)'],1,'The small budget is 1/4+1/4+1/16=9/16; dropping linear or cross terms is unsafe. Multiplication by √n adds 1/2 to the error exponent, so n⁻⁵/² becomes n⁻². The larger errors miss the target precision.')
        if j==1:
            return q('For γ(3,3), which x,y satisfy x+1=3 and x+y=3?' if help else 'To apply the fixed-y theorem to γ(n,n), which substitution is valid?', ['x=3,y=0','x=2,y=1','x=2,y=3'] if help else ['x=n,y=0','x=n−1,y=1','x=n−1,y=n'],1,'Both arguments must match simultaneously: x=n−1 and y=1 (x=2 for n=3). Taking x=n shifts the first argument incorrectly; y=n generally changes the second argument and violates the fixed-y condition.')
        return q('If two interval errors are multiplied, may the e_Ae_B cross term simply be discarded from a guaranteed bound?' if help else 'The stated expansions give constants +1/3 in R and −1/3 in Q. What should their sum do?', ['No; include its absolute bound unless separately absorbed into a proved bound','Yes; products of errors are always zero','Only positive errors can be bounded'],0,'The product expansion contains e_Ae_B for either sign of error. Its absolute value is bounded by δ_Aδ_B; a bound must include it or justify absorbing it elsewhere.') if help else q('The stated expansions give constants +1/3 in R and −1/3 in Q. What should their sum do?', ['Retain constant 2/3','Cancel the constants and reproduce the Stirling expansion of Q+R','Equal the expansion of P'],1,'The exact Q+R identity requires cancellation of complementary constant and 1/n corrections. Adding +1/3 and −1/3 gives zero; P is a different family and its constant −2/3 does not belong in this audit.')
    raise ValueError((order,j))

CONTENT={}
def lesson(order,scope,passages):CONTENT[order]=(scope,passages)
def passage(title,text,formula,bridge):return (title,text,formula,bridge)

lesson(47,'Formal power series over the rationals; coefficient storage, finite algebra and the distinction from analytic evaluation. No convergence theorem is inferred from a finite display.',[
passage('A sequence is an indexed object',
'Imagine numbered shelves, with one card on every shelf, including cards labeled zero. The exponent is the shelf address, not a quantity to add to the card. In the scene, [2,0,5,1] means G(z)=2+0z+5z²+z³. The zero at address 1 matters: removing its position would change the sequence.\n\nFormally, Q[[z]] is the set of all sequences (a₀,a₁,…) of rational coefficients equipped with coefficientwise addition and convolution multiplication. Here z is an indeterminate. Equality means that for every integer n≥0, the nth coefficients agree. The notation [zⁿ]G reads “the coefficient at exponent n in G.” It returns a number, not the term aₙzⁿ.',
r'G(z)=\sum_{n\ge0}a_nz^n,\qquad [z^n]G(z)=a_n',
'Each card is aₙ, and its shelf address is n. The formal sum is a compact name for all the cards.'),
passage('Shifts preserve values but change addresses',
'Multiplication by z moves every card one shelf to the right. Multiplication by zᵐ makes m empty leading shelves. Define aⱼ=0 for j<0; then the shift law works for every n≥0, including the boundary. A left shift is different: subtract the first m terms before dividing by zᵐ. Otherwise negative powers appear, taking us outside ordinary formal power series.\n\nIn the longer-shift scene, [3,1,4] becomes [0,0,3,1,4]. The 3 is still 3, but it now contributes at exponent 2. This is the operation later used to line up recurrence terms with different indices. It is an algebraic reindexing, not an approximation.',
r'[z^n]z^mG(z)=a_{n-m},\quad \frac{G(z)-\sum_{j=0}^{m-1}a_jz^j}{z^m}=\sum_{n\ge0}a_{n+m}z^n',
'The blank leading shelves enforce the initial-condition bookkeeping in the displayed formula.'),
passage('Formal existence does not promise a numerical value',
'Every sequence defines a formal series, even aₙ=n!. At any fixed nonzero real z, the magnitudes n!|z|ⁿ eventually increase because the ratio of successive magnitudes is (n+1)|z|. The terms do not approach zero, so this numerical series cannot converge. Its coefficients remain perfectly meaningful formally.\n\nBy contrast, Σzⁿ=1/(1−z) is both a formal identity and, when |z|<1, an analytic identity. Formal validity alone does not authorize substituting z=2. Ordinary generating functions store aₙ directly; exponential generating functions store aₙ/n!, making the recovered sequence n![zⁿ]G. The convention must be declared before reading a shelf.',
r'\sum_{n\ge0}n!z^n\in\mathbb Q[[z]],\qquad \sum_{n\ge0}z^n=\frac1{1-z}',
'The small shelf example is exact coefficient algebra. It makes no claim about an infinite numerical sum.')])

lesson(48,'Convolution, prefix sums and combinatorial products, including cancellations. The models multiply finite polynomials exactly; the text justifies formal infinite products coefficient by coefficient.',[
passage('Why a product uses a diagonal',
'Choose one term aᵢzⁱ from the first series and one bⱼzʲ from the second. Their product has exponent i+j. To find the coefficient at exponent n, collect exactly the pairs on the diagonal i+j=n. There are at most n+1 such pairs, even if both series are infinite. This finiteness makes multiplication well-defined in Q[[z]] without a convergence assumption.\n\nThe grid uses F=1+2z+z² and G=2+z. The diagonal at n=2 contributes 2·1+1·2=4. Pair identity matters: the cell at (1,1) and the cell at (2,0) are different choices, although their total size agrees.',
r'[z^n]F(z)G(z)=\sum_{i=0}^{n}a_i b_{n-i}',
'Each cell is one product aᵢbⱼ. An active diagonal is the condition i+j=n.'),
passage('A column of ones accumulates prefixes',
'If every bⱼ=1, convolution adds a₀ through aₙ. Thus multiplying G by 1/(1−z) forms the generating function of its prefix sums. The scene shows a finite visible portion. Its last diagonals do not represent the infinite all-ones series unless enough ones have been included: coefficients through n need b₀,…,bₙ.\n\nFor counting, suppose aᵢ counts first objects of size i and bⱼ counts second objects of size j. An ordered pair of choices of total size n has aᵢbⱼ possibilities for a fixed split. The product rule assumes that any allowed first choice may be combined with any allowed second choice; restrictions linking the choices require a different model. This is combinatorial independence, not automatically probabilistic independence.',
r'[z^n]\frac{G(z)}{1-z}=\sum_{i=0}^n a_i',
'A row of ones gives one copy of each coefficient along the active diagonal.'),
passage('Cancellation is algebra, not negative objects',
'Formal coefficients may be signed. In (1−z)(1+z+z²), the middle diagonals cancel and the result is 1−z³. This is a finite version of (1−z)Σzⁿ=1. Every canceled contribution has a partner on the same exponent diagonal.\n\nNegative coefficients usually do not count ordinary objects directly; they may encode subtraction or inclusion–exclusion. Do not interpret a negative cell as a negative number of physical choices. The empty polynomial list represents zero in our executable model, so multiplying it gives zero. Associativity follows by regrouping the finite set of triples i+j+k=n, not by rearranging an uncontrolled numerical infinite sum.',
r'(1-z)(1+z+z^2)=1-z^3',
'Positive and negative cells meet only when their exponent addresses agree.')])

lesson(49,'Scaling, sign filters, formal differentiation/integration and roots-of-unity filters over characteristic-zero coefficient fields. Complex prerequisites for the periodic extension are explicit.',[
passage('Weights come from positions',
'Substituting cz multiplies the coefficient on shelf n by cⁿ. Differentiating instead brings the exponent down and lowers it by one: G′ has coefficient (n+1)aₙ₊₁ at exponent n. Multiplying the derivative by z returns each weighted card to its old position, leaving coefficient naₙ. The constant term becomes zero.\n\nThese are formal operations over Q, R or C. No limits are needed to define them coefficientwise. Repeating z d/dz applies another factor n, so any polynomial weight p(n) can be implemented by p(z d/dz). Ordinary repeated differentiation G″ instead gives n(n−1) and a shift; these operations must not be confused.',
r'G(cz)=\sum c^na_nz^n,\qquad zG\prime(z)=\sum na_nz^n',
'Height changes by the shelf number; the z in zG′ puts the result back at its original address.'),
passage('Parity is a cancellation filter',
'At an even exponent, replacing z by −z leaves the sign unchanged. At an odd exponent, it reverses the sign. Adding the original and sign-flipped copies, then dividing by two, keeps only even positions. It does not compress those positions: a₂ remains attached to z². To obtain the sequence a₀,a₂,a₄,… one must subsequently rename z² as a new variable.\n\nAdvanced extension: over C let m≥1 and ω=e²πⁱ/ᵐ. The average m⁻¹Σⱼ₌₀ᵐ⁻¹ω⁻ʳʲG(ωʲz) keeps exponents n≡r mod m. The proof is a finite geometric sum: its weight is one when m divides n−r and zero otherwise. This complex filter is formal coefficient algebra; it is not an assertion of convergence on the unit circle.',
r'\frac{G(z)+G(-z)}2=\sum_{n\text{ even}}a_nz^n',
'The vanished odd bars are zero coefficients, not missing exponent positions.'),
passage('Integration divides and shifts',
'Integrating the monomial aₙzⁿ from zero to z creates aₙzⁿ⁺¹/(n+1). The division uses characteristic zero; it is not generally defined over a finite field when n+1 vanishes in that field. Choosing lower endpoint zero fixes the constant term to zero. An indefinite antiderivative has an arbitrary added constant.\n\nThe example [3,4,3] becomes [0,3,2,1]. Differentiating this result recovers the original exactly. Integrating a derivative recovers G−a₀, because differentiation erased the constant. When the series also converges in a disk, these formal rules agree with analytic differentiation and integration inside that disk; the formal statement alone does not settle boundary convergence.',
r'\int_0^zG(t)\,dt=\sum_{n\ge0}\frac{a_n}{n+1}z^{n+1},\quad \int_0^zG\prime(t)dt=G(z)-a_0',
'Each original card is divided by its new exponent and placed one shelf to the right.')])

lesson(50,'A second-order linear recurrence solved by exact formal algebra, with initial-condition and inverse-series proofs. The example is original and is checked against independent matrix powering.',[
passage('Derive the numerator, do not guess it',
'Let a₀=2, a₁=3, and aₙ=2aₙ₋₁+aₙ₋₂ for every integer n≥2. The first terms are 2,3,8,19,46,111. Define G=Σₙ≥₀aₙzⁿ. Sum the recurrence only from n=2. Its left side is G−2−3z; the two right sides are 2z(G−2) and z²G. Subtracting gives (1−2z−z²)G=2−z.\n\nEvery removed term has a reason: a₀ and a₁ are not governed by the recurrence. If one silently starts at n=0, nonexistent negative-index terms create a wrong numerator. The animation builds the same coefficients directly, so the formal equation and the computed sequence can be compared.',
r'G(z)-2-3z=2z(G(z)-2)+z^2G(z),\quad G(z)=\frac{2-z}{1-2z-z^2}',
'Two arrows into the new coefficient represent two copies of its immediate predecessor and one of the earlier term.'),
passage('The inverse exists because its constant is nonzero',
'A series D=d₀+d₁z+… over a field has a formal multiplicative inverse exactly when d₀≠0. To solve DH=1, set h₀=1/d₀ and then hₙ=−d₀⁻¹Σᵢ₌₁ⁿdᵢhₙ₋ᵢ. This uniquely determines one coefficient at a time. No analytic pole argument is needed. Our denominator has d₀=1, so its formal inverse exists.\n\nChanging the initial values to a₀=1,a₁=4 changes only the numerator, to 1+2z. The homogeneous recurrence and denominator remain unchanged. Conversely, multiply the proposed rational G by its denominator and compare coefficients: the constant and linear terms verify the two initial values; every later coefficient verifies the recurrence. This supplies a proof for all indices, beyond the finite trace.',
r'G(z)=\frac{u+(v-2u)z}{1-2z-z^2},\qquad (a_0,a_1)=(u,v)',
'The smaller sequence changes the initial cards, while the same two incoming weights govern later cards.'),
passage('Boundary checks make the solution trustworthy',
'With u=0,v=2 the numerator is 2z, so the constant coefficient must be zero. The coefficient of z² is 4. Checking n=2 is a useful way to catch a missing shifted initial term before doing any partial fractions. A zero numerator produces the all-zero sequence; the denominator being nonzero as a formal series is what matters.\n\nOver R one can factor 1−2z−z²=(1−(1+√2)z)(1−(1−√2)z), then expand each geometric factor formally. This leads to a closed form in the two roots, but radicals are optional for recovering coefficients. The rational generating function already specifies a unique exact sequence. A finite prefix confirms the implementation; coefficient comparison proves that this specification satisfies the recurrence for every n≥2.',
r'[z^0]G=u,\quad [z^1]G=v,\quad [z^2]G=2v+u',
'The zero initial coefficient is retained as a real boundary condition, not dropped from the sequence.')])

lesson(51,'Ordinary versus exponential generating functions, standard formal exp/log series, and Bernoulli normalization. Generalized binomial and Stirling-number bridges are stated with their domains.',[
passage('Labels create the binomial factor',
'Suppose aᵢ counts structures on an i-element labeled set and bⱼ counts another kind. To make an ordered pair of structures on n labels, first choose the i labels of the first group, then build both structures. There are binom(n,i)aᵢbₙ₋ᵢ possibilities. With three labels and a first group of size one, the scene displays the three choices explicitly.\n\nStore counts as exponential generating functions A(z)=Σaₙzⁿ/n! and B(z)=Σbₙzⁿ/n!. Ordinary multiplication then supplies exactly the binomial factor after multiplying the coefficient by n!. The labels are distinct; choosing unlabeled sizes alone would not require this factor. Empty structures use size zero and 0!=1, so the boundary fits the same law.',
r'n![z^n]A(z)B(z)=\sum_{i=0}^n\binom ni a_i b_{n-i}',
'The circles are distinct labels; each highlighted subset is one of the binomially many allocations.'),
passage('Same multiplication, different recovery rule',
'An OGF stores raw counts. An EGF stores counts divided by factorials. For sequences aₙ=bₙ=1, the OGF product (1−z)⁻² has nth coefficient n+1. The EGF product eᶻeᶻ=e²ᶻ recovers n!·2ⁿ/n!=2ⁿ, the number of assignments of n labels to either group. Confusing the two conventions changes the counting problem.\n\nUseful standard formal series over Q are eᶻ=Σzⁿ/n! and −log(1−z)=Σₙ≥₁zⁿ/n. Formal exp(H) requires H(0)=0, and formal log(1+H) has the same requirement. Analytically, exp converges everywhere while the displayed logarithm series converges for |z|<1. More generally (1+z)ʳ=Σ binom(r,n)zⁿ with falling-product binomial coefficients, formal for any rational r. For an integer r≥0 this terminates; for a negative integer it does not.',
r'(1-z)^{-2}=\sum_{n\ge0}(n+1)z^n,\qquad e^{2z}=\sum_{n\ge0}2^n\frac{z^n}{n!}',
'The unweighted grid counts size splits. The labeled allocation scene supplies the extra combinatorial factor.'),
passage('Named series need explicit conventions',
'Bernoulli numbers in this companion are defined by z/(eᶻ−1)=ΣBₙzⁿ/n!, with B₁=−1/2. Although the written quotient has a zero denominator constant, cancel z first: it is the inverse of (eᶻ−1)/z, whose constant term is one. Its first terms are 1−z/2+z²/12−z⁴/720+…; the coefficient z²/12 corresponds to B₂=1/6, not 1/12.\n\nTwo useful bridges to earlier counting numbers are (eᶻ−1)ᵏ/k!=Σₙ≥ₖ{n brace k}zⁿ/n! for partitions into k nonempty labeled blocks, and (−log(1−z))ᵏ/k!=Σₙ≥ₖ[n bracket k]zⁿ/n! for permutations with k cycles, using unsigned cycle numbers. These identities hold for fixed nonnegative integer k; they state which objects and normalization each coefficient represents. The coefficient rows show the normalization explicitly; these same Bernoulli numbers will later enter summation corrections.',
r'\frac{z}{e^z-1}=\sum_{n\ge0}B_n\frac{z^n}{n!},\quad B_0=1,\ B_1=-\frac12,\ B_2=\frac16',
'The inverse-series row stores B₂/2!=1/12. Multiplying by 2! recovers B₂=1/6; the smaller example shows the same normalization directly.')])

lesson(52,'Elementary and complete homogeneous symmetric sums, power-sum identities and analytic coefficient extraction. The contour formula is an advanced bridge rather than a prerequisite for the finite models.',[
passage('A product encodes distinct selections',
'Fix m variables x₁,…,xₘ in a commutative characteristic-zero field. Expanding ∏ⱼ(1+xⱼz), choose either 1 or xⱼz from each factor. The coefficient eᵣ sums products over r distinct indices; e₀=1 and eᵣ=0 for r>m. With variables 2,3,5, the degree-two selections contribute 6,10,15, so e₂=31.\n\nThe subscript r is the number of selected variables; it is not one of their numerical values. Different selections may give equal products and are still counted separately. This finite argument proves the coefficient identity exactly, for every m and r in the stated domains. The scene enumerates the three-variable instance.',
r'E(z)=\prod_{j=1}^{m}(1+x_jz)=\sum_{r=0}^{m}e_rz^r',
'Every box corresponds to a different subset of variable positions, not just a numerical product.'),
passage('Allowing repetition changes the generating function',
'For complete homogeneous sums hᵣ, use nondecreasing index tuples and allow the same variable several times. Each factor is now 1+xⱼz+xⱼ²z²+…=(1−xⱼz)⁻¹. For variables 1 and 2, h₂=1+2+4=7, whereas e₂=2. The product remembers how many times each factor supplied its variable.\n\nLet pₖ=Σⱼxⱼᵏ. Taking a formal logarithm of H(z)=∏(1−xⱼz)⁻¹ gives log H=Σₖ≥₁pₖzᵏ/k. Differentiating and comparing coefficients yields r hᵣ=Σₖ₌₁ʳpₖhᵣ₋ₖ, with h₀=1. Thus power sums determine the homogeneous sums recursively. The argument is legal because H has constant one, so its formal logarithm exists.',
r'H(z)=\prod_j(1-x_jz)^{-1},\quad \log H(z)=\sum_{k\ge1}\frac{p_k}{k}z^k,\quad rh_r=\sum_{k=1}^rp_kh_{r-k}',
'Repeated variable positions are now allowed; the two-variable helper makes the extra squares visible.'),
passage('Recover information algebraically or analytically',
'For E(z), logarithmic differentiation gives r eᵣ=Σₖ₌₁ʳ(−1)ᵏ⁻¹pₖeᵣ₋ₖ. In particular e₂=(p₁²−p₂)/2. For 1,3,4, p₁=8 and p₂=26, giving e₂=19, matching the subset products 3+4+12. This is Newton’s identity with its signs and initial value stated.\n\nAdvanced analytic bridge: if G is analytic on a neighborhood of the closed disk |z|≤ρ with ρ>0, Cauchy’s formula gives [zⁿ]G=(2πi)⁻¹∮|z|=ρ G(z)z⁻ⁿ⁻¹dz for n≥0, counterclockwise. Parameterizing z=ρeⁱᶿ explains extraction: integration kills all nonzero Fourier frequencies. This requires complex integration and an actual analytic function; a formal series with zero convergence radius does not permit this contour. Finite symmetric-polynomial extraction needs no contour at all.',
r're_r=\sum_{k=1}^r(-1)^{k-1}p_ke_{r-k},\quad [z^n]G=\frac1{2\pi i}\oint_{|z|=\rho}\frac{G(z)}{z^{n+1}}\,dz',
'The finite subset total verifies one Newton identity. The infinite analytic theorem needs its separate disk hypothesis.')])

lesson(53,'Right-to-left maximum scan with the source’s rightmost-tie policy, exact comparisons and updates, and flow conservation. Costs are abstract operations, not animation frames or measured wall time.',[
passage('Choose a tie policy before counting',
'Let X₁,…,Xₙ be a nonempty list of totally ordered values. Initialize m=Xₙ and j=n. Scan k=n−1 down to 1; update m and j only when Xₖ>m. The output is the largest value and its rightmost position. In [3,7,2,7,4], the first encountered 7 is at position 4. The equal 7 at position 2 does not replace it.\n\nBefore a comparison at position k, the invariant is m=max{Xᵢ:k<i≤n}, with j the rightmost maximizing index in that suffix. A strict improvement extends the invariant by changing the representative; otherwise the suffix maximum stays unchanged. At k=0 the suffix is the whole list. Initialization, preservation and termination together prove correctness, including duplicates.',
r'm=X_j=\max_{k<i\le n}X_i,\qquad X_k>m\Rightarrow (m,j)\leftarrow(X_k,k)',
'The highlighted winner retains its identity when an equal-height bar is compared.'),
passage('Separate fixed work from data-dependent work',
'There are n−1 value comparisons and n−1 decrements. The “all tested?” loop test runs n times, including the final successful termination test. Initialization and return each run once. Only the number A of strict improvements depends on the input order; 0≤A≤n−1.\n\nIn a strictly decreasing list scanned from the right, every comparison improves the current maximum, so A=n−1. In a list whose last item is a maximum, A=0. A cost model assigning c₀ to initialization/return, cₜ to the loop test, c꜀ to comparison/decrement and cᵤ to an update gives T=c₀+cₜn+c꜀(n−1)+cᵤA. Actual machine instructions can have different costs; an animation frame is not a unit of algorithmic time.',
r'N_{\rm compare}=n-1,\quad N_{\rm test}=n,\quad 0\le A\le n-1',
'The smaller descending list makes every update visible; comparison and update counters still count different events.'),
passage('Flow counts must balance',
'View the algorithm as a directed control-flow graph. The test node receives one entry from initialization and n−1 entries from decrements: n total. It sends one flow to termination and n−1 to comparison. The comparison node splits its n−1 visits into A improvement edges and n−1−A skip edges. Both paths reunite before decrement. At every internal node, incoming and outgoing visit totals agree.\n\nFor n=1, there is one loop test and no value comparisons or updates. The empty list is excluded because “the maximum” and its position are undefined here; an implementation needs a separately specified empty-input result. These boundaries are useful checks on a frequency equation. A correct output alone does not establish that an operation count is correct.',
r'n=1+(n-1),\qquad n-1=A+(n-1-A)',
'The no-update trace still contains every comparison and the final termination test.')])

lesson(54,'Expected record counts under uniform permutations of distinct values, with exact permutation enumeration and a proof by indicator variables. Nonuniform inputs and ties are outside that distribution model.',[
passage('An average needs a probability space',
'The notation Pr(event), also written P(event), means the probability of that event. E[X] means the average value of X over the declared equally likely permutations. Assume the n values are distinct and every relative ordering is equally likely. We can replace the values by ranks 1,…,n without changing the scan’s decisions. The sample space is the n! permutations, each with probability 1/n!. For n=3 the scene shows all six, not a simulation.\n\nThe random variable A counts updates after initialization. Let Iₖ indicate that the leftmost item of a suffix of length k is largest in that suffix. Initialization is the inevitable record k=1 and is excluded from A; hence A=Σₖ₌₂ⁿIₖ. Each suffix maximum is equally likely to occupy any one of its k positions, so E[Iₖ]=P(Iₖ=1)=1/k. The values themselves need no numeric distribution beyond the assumed uniform order.',
r'A=\sum_{k=2}^{n}I_k,\qquad \Pr(I_k=1)=\frac1k',
'Highlighted permutations are the equally likely outcomes satisfying one record event.'),
passage('Linearity avoids an independence detour',
'For any finite collection of integrable random variables, expectation distributes over their sum, whether or not they are independent. Therefore E[A]=Σₖ₌₂ⁿ1/k=Hₙ−1. The four-item enumeration checks the suffix probabilities exactly, but the symmetry argument proves the result for every n.\n\nThis expectation can be far smaller than the worst-case n−1, yet the scan still performs n−1 comparisons. A logarithmic expected update count does not turn this maximum-finding algorithm into a logarithmic-time algorithm under the usual cost model. Moreover, E[A] describes an average over the declared input distribution; it does not assert that a particular input has about that many updates.',
r'\mathbb E[A]=H_n-1,\qquad H_n=\sum_{k=1}^{n}\frac1k',
'Each suffix contributes its own small probability; adding these weights gives the expected total.'),
passage('A mean is neither a worst case nor a distribution',
'A probability-generating function (PGF) for the update count A is the polynomial whose coefficient of zʲ is the probability P(A=j). For n=4, the update PGF is (z+1)(z+2)(z+3)/24. Its coefficients are 1/4,11/24,1/4,1/24 for A=0,1,2,3. These sum to one and have mean 13/12. The mean is not a possible integer update count, which is perfectly normal.\n\nIf the input is already sorted increasingly, A=0 with certainty under the right-to-left scan; if sorted decreasingly, A=n−1. Ties can also change record probabilities: an all-equal list has A=0. Uniform distinct permutations are a model, not a claim about every real dataset. To predict timing, one must additionally specify operation costs and the relevant hardware behavior. Later lessons derive the full distribution and its variance.',
r'G_4(z)=\frac{(z+1)(z+2)(z+3)}{24},\qquad \mathbb E[A]=\frac{13}{12}',
'The bars show how the same average can combine very different update counts.')])

lesson(55,'Exact record-count PGFs, their rank-insertion recurrence, moments and variance. The first record is excluded throughout; the independent relative-rank construction is justified.',[
passage('Insertion gives a product law',
'In the Bernoulli factor (k−1+z)/k, the constant coefficient (k−1)/k is the probability of no update, and the coefficient 1/k of z is the probability of one update. Read a uniform permutation from the right and record the relative rank of each new item among those seen so far. For suffix length k this rank is one of 1,…,k. The map from permutations to such rank sequences is bijective: reconstruct the permutation by inserting ranks in reverse. There are ∏ₖ₌₁ⁿk=n! possible sequences. Uniform permutations therefore give independent uniform relative ranks.\n\nAn update at suffix length k occurs exactly when the new rank is k. Its Bernoulli PGF is (k−1+z)/k. Since initialization is excluded, G₁(z)=1 and Gₙ(z)=((n−1+z)/n)Gₙ₋₁(z). This proves the product formula, not merely its first few coefficients. The animation splits exact probability mass at each new rank.',
r'G_n(z)=\mathbb E[z^A]=\prod_{k=2}^{n}\frac{k-1+z}{k}',
'Every insertion splits a mass between unchanged update count and count plus one.'),
passage('Differentiate to read the moments',
'Write pⱼ=P(A=j) for the probability of j updates. Var(A)=E[(A−E[A])²] is the mean squared deviation from the mean. For a nonnegative integer-valued random variable with finite support, G(z)=Σpⱼzʲ. Setting z=1 gives total probability. Differentiating once yields G′(1)=Σjpⱼ=E[A]. Differentiating twice yields E[A(A−1)], not E[A²]. Add the first derivative to recover the second moment, then subtract the squared mean for variance.\n\nThe model computes mean and variance directly from the bars using exact rational arithmetic. These are compared independently with Hₙ−1 and Hₙ−Hₙ⁽²⁾, where Hₙ⁽²⁾=Σₖ₌₁ⁿ1/k². The formulas follow by adding the independent Bernoulli means and variances; alternatively differentiate log G near z=1, where every factor is nonzero.',
r'\mathbb E[A]=G\prime(1),\quad \operatorname{Var}(A)=G\prime\prime(1)+G\prime(1)-G\prime(1)^2=H_n-H_n^{(2)}',
'Bar locations supply the factors j and j²; bar heights supply their exact probability weights.'),
passage('Coefficient recurrence and boundary audits',
'Writing pₙ,ⱼ=[zʲ]Gₙ gives pₙ,ⱼ=((n−1)pₙ₋₁,ⱼ+pₙ₋₁,ⱼ₋₁)/n, with missing indices assigned zero. This makes nonnegativity obvious. Summing over j preserves total mass one. At n=1 all mass is at zero; at n≥2 the largest possible update count is n−1.\n\nMultiplying Gₙ by n! yields ∏ₖ₌₁ⁿ⁻¹(z+k), whose coefficients are integer permutation counts. They connect to unsigned Stirling cycle numbers: n!pₙ,ⱼ=[n bracket j+1]. This is an algebraic identity between distributions, not a claim that a particular permutation has the same number of records and cycles. Exact enumeration through n=7 checks the implemented probabilities against actual scan executions.',
r'p_{n,j}=\frac{(n-1)p_{n-1,j}+p_{n-1,j-1}}n,\qquad p_{1,0}=1',
'The longer trace still conserves total probability at every insertion, including zero-probability boundaries.')])

lesson(56,'Independent biased coins, expectation, covariance and Chebyshev bounds with deterministic boundary cases. The model enumerates distributions exactly and makes no simulation-based proof claims.',[
passage('Convolve only when the trials are independent',
'Let B₁,…,Bₙ be independent Bernoulli variables with P(Bᵢ=1)=p and P(Bᵢ=0)=1−p, where 0≤p≤1. The head count S=ΣBᵢ has PGF ((1−p)+pz)ⁿ. Each old mass splits into a no-head branch and a head branch. The first scene uses p=1/3, so all probabilities remain rational.\n\nIndependence is the step that lets E[z^(X+Y)] factor as E[z^X]E[z^Y]. Without it, multiplying marginal PGFs may be wrong. For example, if B₂=B₁ is the same fair coin reused, their sum takes only 0 or 2; its PGF is (1+z²)/2, not (1+z)²/4. Marginal fairness alone does not give independent trials.',
r'G_S(z)=((1-p)+pz)^n,\qquad \Pr(S=k)=\binom nk p^k(1-p)^{n-k}',
'Each incoming mass is split with the same stated bias; the two branch weights add to one.'),
passage('Expectation always adds; variance has a cross term',
'The covariance Cov(X,Y)=E[(X−E[X])(Y−E[Y])] measures how the two deviations from their means vary together. For finite expectations, E[X+Y]=E[X]+E[Y]. With finite second moments, Var(X+Y)=Var(X)+Var(Y)+2Cov(X,Y). Independence implies zero covariance, although the converse need not hold. For our independent coins, E[S]=np and Var(S)=np(1−p).\n\nChanging p from 1/3 to 2/3 reflects the head-count distribution around n/2: successes and failures exchange roles. The variance stays the same because p(1−p) is unchanged, while the mean moves. A large variance indicates greater squared spread around the mean; it does not by itself reveal whether a distribution is symmetric, unimodal or approximately normal.',
r'\mathbb E[S]=np,\qquad \operatorname{Var}(S)=np(1-p)',
'The reflected distribution has a different center but the same mean squared distance from its center.'),
passage('A deviation bound is a guarantee, often a loose one',
'For any X with mean μ and finite variance σ², Markov’s inequality applied to the nonnegative variable (X−μ)² gives P(|X−μ|≥t)≤σ²/t² for t>0. A probability cannot exceed one, so use min(1,σ²/t²). No independence assumption is needed for this final inequality; it may have been needed to calculate σ².\n\nWhen σ²=0, X=μ almost surely, so every positive deviation has probability zero. Our p=1 scene is this deterministic boundary: all mass moves right at every trial. For n=3,p=1/3, the exact probability |S−1|≥1 is 5/9, while Chebyshev gives 2/3. The bound is valid but not exact. Gaussian approximations would need additional hypotheses and an approximation error analysis.',
r'\Pr(|X-\mu|\ge t)\le\min\left(1,\frac{\sigma^2}{t^2}\right),\quad t>0',
'The helper with p=0 never moves its mass. Zero variance is a separate, fully determined case.')])

lesson(57,'Modern eventually-everywhere O, Ω and Θ definitions on integer n→∞, explicit witnesses, signed functions and the limits of finite plots. Ω is not the alternative infinitely-often convention.',[
passage('Choose constants before the infinite tail',
'For real-valued functions f and g on the positive integers, f=O(g) as n→∞ means there exist constants C>0 and n₀ such that for every n≥n₀, |f(n)|≤C|g(n)|. The order of these quantifiers matters. A different C chosen after seeing each n proves nothing useful.\n\nFor f(n)=3n+5 and g(n)=n, choose C=8 and n₀=1. Then 8n−(3n+5)=5(n−1)≥0 for every n≥1. The drawn points illustrate this algebraic proof. No finite plot, however long, rules out a later violation by a different function. O describes membership in a growth class; the familiar equality sign f=O(g) is notation for that membership.',
r'f=O(g)\iff \exists C>0\ \exists n_0\ \forall n\ge n_0:\ |f(n)|\le C|g(n)|',
'The upper ray is chosen once. The nonnegative gap proves it stays above the curve beyond the stated threshold.'),
passage('Lower bounds and matching orders',
'We use the modern eventually-everywhere convention: f=Ω(g) means there exist c>0,n₀ such that |f(n)|≥c|g(n)| for every n≥n₀. Some historical analytic uses of Ω mean “infinitely often”; that is not the convention here. A function is Θ(g) when it is both O(g) and Ω(g), with thresholds enlarged if necessary so both bounds hold together.\n\nFor f(n)=2n+7, lower constant c=2 and upper constant C=9 work for n≥1. Thus f=Θ(n). But f is also O(n²); an upper bound alone need not be tight. Absolute values allow signed functions such as −n to have order Θ(n). If g vanishes at some tail index, O(g) requires f to vanish there too, so dividing the definition by g without checking nonzero values is unsafe.',
r'f=\Theta(g)\iff \exists c,C>0\ \exists n_0\ \forall n\ge n_0:\ c|g(n)|\le |f(n)|\le C|g(n)|',
'The two rays trap the entire tail. Their constants may be far apart without invalidating Θ.'),
passage('Order classes are coarser than ratios',
'For f(n)=5n+2, f/n→5, so f is asymptotic to 5n, written f∼5n. It is not asymptotic to n, because that ratio tends to 5 rather than 1. Both n and 5n nevertheless belong to the same Θ class. Tight order does not identify a leading constant.\n\nThe statement f=o(g) means that for every ε>0 there exists n₀ such that |f(n)|≤ε|g(n)| for all n≥n₀. This is stronger than O(g) and, when g is eventually nonzero, equivalent to f/g→0. Constant factors and thresholds remain important for finite inputs: an asymptotic comparison does not by itself tell which implementation wins at the input size you actually have.',
r'f\sim g\iff f/g\to1,\qquad f=o(g)\iff \forall\varepsilon>0\ \exists n_0\ \forall n\ge n_0:\ |f(n)|\le\varepsilon|g(n)|',
'The gap between the example and its leading ray is constant, while its ratio to n tends to a nonunit constant.')])

lesson(58,'Safe algebra of bounded error terms, exact reciprocal remainders, relative versus absolute error and fixed-order asymptotic expansions. Denominator conditions and nonconvergence warnings are explicit.',[
passage('An O-term is an unknown function under a bound',
'The expression A(n)+O(g(n)) means A(n)+r(n), where r is some function satisfying a fixed eventual bound |r(n)|≤C|g(n)|. Two written O(g) terms need not be the same function. Consequently O(g)−O(g) is O(g), not necessarily zero. You can add bounds using the triangle inequality and multiply them using absolute values.\n\nThe reciprocal example has an exact remainder: 1/(1+x)=1−x+x²/(1+x), for x≠−1. Set x=1/n with n≥1. The omitted term lies between 0 and 1/n². The interval in the scene is therefore a proved enclosure, not a confidence interval or a fitted trend. Its actual error is 1/[n(n+1)].',
r'\frac1{1+x}=1-x+\frac{x^2}{1+x},\qquad 0<\frac1{n(n+1)}\le\frac1{n^2}',
'The interval endpoints come from an exact identity and a denominator bound.'),
passage('Division and exponentiation need local control',
'If ε(n)=O(1/n), then ε→0. Eventually |ε|≤1/2, so 1+ε is bounded away from zero and 1/(1+ε)=1−ε+O(ε²). Without the nonzero denominator, inversion can amplify a small absolute error arbitrarily. For example, replacing a tiny denominator by zero is not a harmless approximation.\n\nIf T=A(1+δ) with A≠0, δ is a relative error and Aδ is the absolute error. If log T=log A+r with positive T,A and r=O(n⁻ᵖ), p>0, then T/A=eʳ=1+O(n⁻ᵖ). This follows from the mean value theorem for exp on a bounded neighborhood of zero. It does not imply an absolute O(n⁻ᵖ) error when A grows.',
r'\varepsilon=O(n^{-1})\Rightarrow (1+\varepsilon)^{-1}=1-\varepsilon+O(n^{-2})',
'A smaller 1/n produces a quadratically shrinking certified inverse-error interval.'),
passage('Fix the truncation order before taking the limit',
'An asymptotic expansion f(n)=Σⱼ₌₀ᵐcⱼn⁻ʲ+O(n⁻ᵐ⁻¹) asserts a statement for each fixed m as n→∞. The hidden constant may depend on m. It does not authorize letting m grow with n or summing infinitely many terms at a fixed n. Euler–Maclaurin expansions later provide important divergent examples.\n\nFor multiplying approximations A+e_A and B+e_B with |e_A|≤δ_A, |e_B|≤δ_B, retain the cross-error e_Ae_B too. The total absolute error is at most |B|δ_A+|A|δ_B+δ_Aδ_B. The colored segments in the scene are these three contributions, not arbitrary accuracy scores. A claimed precision must survive every intermediate scaling and addition.',
r'|(A+e_A)(B+e_B)-AB|\le |B|\delta_A+|A|\delta_B+\delta_A\delta_B',
'The final interval is built from all three error contributions. Dropping the smallest one requires an explicit bound.')])

lesson(59,'Euler summation with the half-open endpoint convention, integration-by-parts derivation and exact polynomial examples. Calculus terms receive a geometric bridge; arbitrary nonsmooth functions are not covered.',[
passage('An integral measures the area between samples',
'For a continuous nonnegative function f on [0,n], the integral ∫₀ⁿf(x)dx is the area under its curve, defined as a limit of ever-finer rectangle sums. The discrete sum Σₖ₌₀ⁿ⁻¹f(k) instead uses unit-width rectangles at the left endpoints. These are different quantities even though they have the same units. Our convention includes 0 and excludes n throughout this lesson.\n\nFor f(x)=x² and n=4, the discrete area is 0+1+4+9=14, while the smooth area is 64/3. The increasing curve lies above the left rectangles. The overlay makes the discrepancy visible without pretending the curve is made of the displayed finite samples. The integral value is computed from the antiderivative x³/3, not estimated from the pixels.',
r'S_n=\sum_{k=0}^{n-1}f(k),\qquad I_n=\int_0^nf(x)\,dx',
'Unit rectangles encode sampled values. The continuous area between their edges is the source of the correction.'),
passage('The first correction comes from integration by parts',
'The derivative f′(x) is the local slope, the limit of the change in f divided by the change in x. Suppose f is continuously differentiable on [0,n]. On each unit interval [k,k+1], integrate (x−k−1/2)f′(x) by parts. Its boundary contribution is (f(k)+f(k+1))/2, and its remaining integral is −∫ₖᵏ⁺¹f. Summing these identities makes the interior endpoint contributions add and leaves half-weights at the two outer endpoints.\n\nWriting {x}=x−floor(x), we obtain Sₙ=Iₙ−(f(n)−f(0))/2+∫₀ⁿ({x}−1/2)f′(x)dx. The repeated sawtooth has zero mean on each unit interval. For a linear f the derivative is constant, so the remainder vanishes. For curved f the changing slope interacts with the sawtooth and another correction is needed.',
r'S_n=I_n-\frac{f(n)-f(0)}2+\int_0^n\left(\{x\}-\frac12\right)f\prime(x)\,dx',
'The endpoint subtraction fixes the gross rectangle bias; the slope-weighted tile measures what remains.'),
passage('Curvature leaves a derivative correction',
'Let B₁(t)=t−1/2 and B₂(t)=t²−t+1/6. Since B₂′=2B₁ and B₂(0)=B₂(1)=1/6, another integration by parts gives Sₙ=Iₙ−Δf/2+Δf′/12−(1/2)∫₀ⁿB₂({x})f″(x)dx. Here Δf=f(n)−f(0) and Δf′=f′(n)−f′(0) are whole-interval endpoint differences; f should be twice continuously differentiable. The first derivative correction compares endpoint slopes.\n\nFor x², ∫ on each unit tile of B₂ is zero, so the remainder vanishes and the first correction gives the exact square sum. For x³ the same happens: f″ is linear and ∫₀¹tB₂(t)dt=0 as well. The cubic example yields n⁴/4−n³/2+n²/4=n²(n−1)²/4. Exactness here follows from polynomial integration, not from observing three matching decimal places. Higher-order functions generally retain a remainder.',
r'S_n=I_n-\frac{\Delta f}2+\frac{\Delta f\prime}{12}-\frac12\int_0^nB_2(\{x\})f^{\prime\prime}(x)\,dx',
'The cubic rectangles become an exact sum after the area, endpoint and derivative contributions are combined.')])

lesson(60,'Bernoulli numbers and polynomials, repeated integration by parts, an explicit fixed-order Euler–Maclaurin remainder bound and polynomial termination. The even-order supremum estimate is identified as a theorem.',[
passage('Generate the correction coefficients',
'The defining formal identity is (ΣBₖzᵏ/k!)((eᶻ−1)/z)=1. Equating coefficients gives B₀=1 and, for m≥1, Σₖ₌₀ᵐbinom(m+1,k)Bₖ=0. This recurrence computes B₁=−1/2, B₂=1/6, B₃=0 and B₄=−1/30 exactly. There is no numerical fitting.\n\nDefine Bₘ(t)=Σₖ₌₀ᵐbinom(m,k)Bₖtᵐ⁻ᵏ. Differentiation gives Bₘ′=mBₘ₋₁. The first polynomial t−1/2 becomes a sawtooth when repeated as B₁({x}); it jumps at integers. For m>1 the recurrence gives Bₘ(1)=Bₘ(0), so those repeated tiles are continuous. The helper repeats fewer tiles of the same function; no unrelated graph is substituted.',
r'B_m=-\frac1{m+1}\sum_{k=0}^{m-1}\binom{m+1}{k}B_k,\qquad B_m\prime(t)=mB_{m-1}(t)',
'The first tile encodes a signed distance from the midpoint of each unit interval.'),
passage('Every integration by parts has a boundary and a remainder',
'The notation f∈C²ᵖ[a,b] means that f has continuous derivatives through order 2p on [a,b]. The superscript in f⁽ʳ⁾ denotes the rth derivative, obtained by differentiating r times. Let a<b be integers, p≥1 fixed, and f∈C²ᵖ[a,b]. Repeated integration by parts gives the half-open Euler–Maclaurin formula: Σₖ₌ₐᵇ⁻¹f(k)=∫ₐᵇf−Δf/2+Σᵣ₌₁ᵖ B₂ᵣΔf⁽²ʳ⁻¹⁾/(2r)!+R₂ₚ, where R₂ₚ=−∫ₐᵇB₂ₚ({x})f⁽²ᵖ⁾(x)dx/(2p)!. The minus sign is important for even order. Odd Bernoulli numbers beyond B₁ vanish, so only even correction indices remain. To see the parity, put F(z)=z/(eᶻ−1). Algebra gives F(−z)=F(z)+z, hence F(z)+z/2 is even; its odd coefficients are zero.\n\nFor p=1, B₂(t)=(t−1/2)²−1/12 lies between −1/12 and 1/6 on [0,1]. Therefore |R₂|≤(1/12)∫|f″|. More generally the Bernoulli supremum theorem gives |B₂ₚ(t)|≤|B₂ₚ| for 0≤t≤1, yielding |R₂ₚ|≤|B₂ₚ|∫|f⁽²ᵖ⁾|/(2p)!. The general supremum theorem is stated here; its Fourier-series proof is outside this unit. The p=1 bound is proved directly above.',
r'R_{2p}=-\frac1{(2p)!}\int_a^bB_{2p}(\{x\})f^{(2p)}(x)\,dx,\quad |R_{2p}|\le\frac{|B_{2p}|}{(2p)!}\int_a^b|f^{(2p)}(x)|\,dx',
'The B₂ tile gives a visible signed weight; its maximum magnitude supplies the rigorous integral bound.'),
passage('More corrections are not automatically better',
'For a polynomial f of degree d, choose 2p>d. Then f⁽²ᵖ⁾=0 and the remainder is exactly zero. The formula becomes a finite exact identity. For a general smooth function, however, high derivatives and Bernoulli numbers can grow rapidly; increasing p may eventually enlarge the correction and error bound at a fixed interval.\n\nA “first omitted term” bound is stronger than the general integral bound and requires additional conditions. The source supplies one such sign condition: for even m, with derivatives through m+4 continuous, if f⁽ᵐ⁺²⁾(x)f⁽ᵐ⁺⁴⁾(x)>0 throughout the open interval, its remainder is a fraction between zero and one of the next correction. We use that theorem for 1/x and log x in the next lesson; we do not assume it for arbitrary f. The cubic scene is a termination example, where a sufficiently high derivative vanishes, not an empirical argument for convergence of all Euler expansions.',
r'f\text{ polynomial of degree }d<2p\Rightarrow R_{2p}=0',
'The cubic’s exact sum comes from vanishing higher derivatives. A smooth nonpolynomial may not terminate.')])

lesson(61,'Derivation of harmonic and factorial expansions from Euler summation, rigorous fixed-order remainders, existence of constants, Wallis identification of the Stirling constant and relative-error conversion. Decimal residuals are illustrative, not certified interval endpoints.',[
passage('Subtract the growing harmonic area',
'For n≥1, Hₙ=Σₖ₌₁ⁿ1/k is exact rational arithmetic. The sequence Hₙ−log n decreases: log(1+1/n)>1/(n+1), by integrating 1/x over [n,n+1]. It is bounded below by zero using rectangle comparison. Hence it has a limit γ. This proves existence; a plot settling near a decimal would not.\n\nApply Euler summation to f(x)=1/x, whose mth derivative is (−1)ᵐm!/xᵐ⁺¹. Subtract the limiting constant and evaluate the endpoint corrections. The result through B₄ is Hₙ=log n+γ+1/(2n)−1/(12n²)+1/(120n⁴)−εₙ, with 0<εₙ<1/(252n⁶). The source’s first-omitted-term theorem applies because the required even-order derivative products are positive on x>0. Solving this inequality for γ gives the shrinking bracket in the scene. Decimal endpoints are rounded illustrations; the symbolic bracket width is the guaranteed error statement.',
r'H_n=\log n+\gamma+\frac1{2n}-\frac1{12n^2}+\frac1{120n^4}-\varepsilon_n,\quad 0<\varepsilon_n<\frac1{252n^6}',
'The helper peels the same corrections from a shorter harmonic sum, leaving a wider guaranteed bracket.'),
passage('Logarithms turn a product into a summation problem',
'Because log n!=Σₖ₌₁ⁿlog k, Euler summation applies to f(x)=log x. Its rth derivative for r≥1 is (−1)ʳ⁻¹(r−1)!/xʳ. Subtracting the bulk (n+1/2)log n−n leaves a limit σ: with one derivative correction, the remaining integral has an integrable x⁻² majorant, so its tail tends to zero. Evaluating further endpoint terms gives log n!=(n+1/2)log n−n+σ+1/(12n)−1/(360n³)+O(n⁻⁵).\n\nThe constant is not determined by local derivative corrections alone. Here is the missing bridge. If n!∼C√n(n/e)ⁿ, then binom(2n,n)∼(√2/C)4ⁿ/√n. Let Jₘ=∫₀^(π/2)sinᵐt dt. Integration by parts gives Jₘ=(m−1)Jₘ₋₂/m. Thus J₂ₙ=(π/2)binom(2n,n)/4ⁿ and J₂ₙ₊₁=4ⁿ/((2n+1)binom(2n,n)). The inequalities J₂ₙ₊₁≤J₂ₙ≤J₂ₙ₋₁ squeeze J₂ₙ/J₂ₙ₊₁→1. Their product is π/[2(2n+1)], so binom(2n,n)∼4ⁿ/√(πn). Comparing constants proves C=√(2π) and σ=(1/2)log(2π).',
r'\log n!=\left(n+\frac12\right)\log n-n+\frac12\log(2\pi)+\frac1{12n}-\frac1{360n^3}+O(n^{-5})',
'The residual interval isolates a constant, while the integral argument identifies that constant exactly.'),
passage('Exponentiate with enough intermediate precision',
'Write L=(n+1/2)log n−n+(1/2)log(2π). If log n!=L+1/(12n)−1/(360n³)+O(n⁻⁵), then n!=eᴸ exp(1/(12n)−1/(360n³)+O(n⁻⁵)). Expanding exp to the desired fixed order gives n!=√(2πn)(n/e)ⁿ(1+1/(12n)+1/(288n²)−139/(51840n³)+O(n⁻⁴)). The 1/(288n²) term comes from squaring 1/(12n) and dividing by 2; it is not a new Euler correction.\n\nAn absolute error in log n! becomes a relative error in n!, because exponentiation multiplies the bulk. The error ledger is a smaller rational exercise in carrying such intermediate errors; it is not an alternative numerical proof of Stirling’s theorem. For both harmonic and factorial expansions, n→∞ with truncation order fixed. The Bernoulli corrections grow factorially in order, so extending the displayed expansion to an infinite convergent series at a fixed n is generally invalid.',
r'n!=\sqrt{2\pi n}(n/e)^n\left(1+\frac1{12n}+\frac1{288n^2}-\frac{139}{51840n^3}+O(n^{-4})\right)',
'The error blocks remind us to keep cross terms when converting a logarithmic expansion into a multiplicative one.')])

lesson(62,'Incomplete gamma as partial area, peak localization, square-root scaling and the source’s monotone change of variables with an explicit exponential tail bound. The full fixed-y expansion is a stated theorem supported by its derivation structure.',[
passage('A partial gamma integral measures incomplete area',
'Here the two-argument symbol γ(a,x) names the incomplete gamma function; the Euler constant γ in the previous lesson is a different object. For a>0 and x≥0, define γ(a,x)=∫₀ˣtᵃ⁻¹e⁻ᵗdt and Γ(a)=∫₀∞tᵃ⁻¹e⁻ᵗdt. Their ratio lies in [0,1] and measures the fraction of the total area accumulated by x. The improper integral at zero exists because a>0; the exponential controls the infinite tail. For integer n≥0, Γ(n+1)=n! by integration by parts.\n\nThe shape tⁿe⁻ᵗ for n>0 peaks at t=n: its logarithmic derivative n/t−1 changes from positive to negative there. Its second log derivative at the peak is −1/n. Thus a displacement of order √n produces an order-one change in the log height. The picture normalizes the peak height to one to avoid enormous numbers; it does not claim to have numerically integrated the whole density.',
r'\gamma(a,x)=\int_0^x t^{a-1}e^{-t}dt,\quad \frac d{dt}\log(t^ne^{-t})=\frac nt-1',
'The curve’s peak and the two square-root markers are derived from slopes, rather than guessed from the plot.'),
passage('Rescaling explains the Gaussian term, but tails still need proof',
'Set t=n+s√n with fixed real s. Then log((tⁿe⁻ᵗ)/(nⁿe⁻ⁿ))=n log(1+s/√n)−s√n=−s²/2+s³/(3√n)+O(n⁻¹), uniformly for s in any fixed bounded interval. The leading local shape is therefore e⁻ˢ²/². This local Taylor estimate by itself does not justify integrating over all real s.\n\nFor the upper part I₁=∫ₙ∞tⁿe⁻ᵗdt, use t=n(1+u), then v=u−log(1+u), u≥0. Since dv/du=u/(1+u)>0 for u>0, the substitution is one-to-one away from the endpoint and dt=n(1+1/u)dv. Consequently I₁=e⁻ⁿnⁿ∫₀∞ne⁻ⁿᵛh(v)dv, with h(v)=1+1/u(v). Fix r>0. Since h decreases, the discarded part satisfies 0≤∫ᵣ∞ne⁻ⁿᵛh(v)dv≤h(r)e⁻ⁿʳ. This is smaller than every fixed inverse power of n. It legitimizes restricting the expansion to a small neighborhood before integrating.',
r'v=u-\log(1+u),\quad \int_r^\infty ne^{-nv}h(v)dv\le h(r)e^{-nr}',
'The smaller peak has the same square-root scaling. The analytic tail bound, not the finite graph, controls the unseen region.'),
passage('Integrate a controlled local expansion',
'Near v=0, put w=√(2v) and write u=w+aw²+bw³+cw⁴+dw⁵+O(w⁶). Substituting into v=u²/2−u³/3+u⁴/4−u⁵/5+… and matching powers gives a−1/3=0, a²/2−a+b+1/4=0, and −a²+ab+a−b+c−1/5=0. Thus a=1/3, b=1/36, c=−1/270; the next coefficient equation is d−1/4320=0. Expanding 1+1/u gives 1/w+2/3+w/12−2w²/135+w³/864+O(w⁴), or h(v)=(2v)⁻¹/²+2/3+(√2/12)v¹/²−(4/135)v+(√2/432)v³/²+O(v²). This is a controlled local expansion: w=u√(1−2u/3+…) is analytic near zero with derivative one, so the analytic inverse-function theorem gives an analytic u(w); the reciprocal has just the displayed simple pole.\n\nFor α>−1, substitution q=nv gives ∫₀∞ne⁻ⁿᵛvᵅdv=Γ(α+1)n⁻ᵅ. If a local remainder is bounded by Cvᵅ on [0,r], this identity bounds its integrated error by CΓ(α+1)n⁻ᵅ; the exponentially small outer tail is handled separately. This is the formal-to-integral bridge missing from a termwise picture.\n\nWe can now recover the stated gamma coefficients instead of fitting them. Use x in place of n and let J=I₁/(e⁻ˣxˣ). The gamma moments give J=√(πx/2)(1+1/(12x)+1/(288x²))+2/3−4/(135x)+O(x⁻²). Normalize by Γ(x+1)/(e⁻ˣxˣ)=√(2πx)(1+1/(12x)+1/(288x²)+O(x⁻³)). For real x this uses the real-argument Stirling extension, obtainable by applying Euler summation to the Euler-limit product; it is a stated extension here. The matching half-density factors cancel. The remaining x⁻³/² coefficient in I₁/Γ is (−4/135−1/18)/√(2π)=−23/(270√(2π)). Taking the complement gives γ(x+1,x)/Γ(x+1)=1/2−(2/3)/√(2πx)+(23/270)/(√(2π)x³/²)+O(x⁻⁵/²).\n\nFor γ(x+1,x+y)/Γ(x+1), take x→∞ with y fixed, not y of order √x. On the short oriented interval from 0 to y, x log(1+s/x)−s=−s²/(2x)+O(x⁻²) uniformly, so its exponential integrates to y−y³/(6x)+O(x⁻²). Multiplying by e⁻ˣxˣ/Γ(x+1)=(2πx)⁻¹/²(1−1/(12x)+O(x⁻²)) adds y/√(2πx)+(−y/12−y³/6)/(√(2π)x³/²)+O(x⁻⁵/²). This proves the displayed fixed-y formula from the controlled local expansion and the stated Stirling extension. A negative fixed y is handled by the same oriented integral. The tail scene shows a separate exact positive-series enclosure used in the next lesson; it illustrates the same obligation to bound what is omitted.',
r'\frac{\gamma(x+1,x+y)}{\Gamma(x+1)}=\frac12+\frac{y-2/3}{\sqrt{2\pi x}}+\frac{23/270-y/12-y^3/6}{\sqrt{2\pi}\,x^{3/2}}+O(x^{-5/2})',
'The retained bars are exact terms, and the stated geometric bound certifies the invisible remainder. Local shape alone would not do that.')])

lesson(63,'The source’s P, Q and R families with visually verified definitions, exact finite evaluation and rational interval evaluation of R; incomplete-gamma and sum-to-integral bridges. Higher P coefficients are stated rather than falsely derived by a coarse remainder.',[
passage('Similar-looking sums can have different corrections',
'For a positive integer n define P(n)=Σₖ₌₀ⁿ(n−k)ᵏ(n−k)!/n!, Q(n)=Σₖ₌₁ⁿn!/((n−k)!nᵏ), and R(n)=Σₖ≥₀n!nᵏ/(n+k)!. These are the exact source definitions. P and Q are finite; R is infinite. Since n≥1, the last P term has 0ⁿ=0, and no 0⁰ ambiguity occurs. Their leading scale is similar, but their constant corrections differ.\n\nFor n=4, exact evaluation gives P=17/8 and Q=71/32. The scene focuses on R’s positive terms; its displayed partial sum is a lower bound, and the next passage supplies the upper bound. Never replace a finite definition by an infinite look-alike because the first few terms appear similar. For P, changing variable j=n−k gives P(n)=Σⱼ₌₀ⁿjⁿ⁻ʲj!/n!, a useful bridge to Stirling’s formula.',
r'P(n)=\sum_{k=0}^{n}\frac{(n-k)^k(n-k)!}{n!},\quad Q(n)=\sum_{k=1}^{n}\frac{n!}{(n-k)!n^k},\quad R(n)=\sum_{k\ge0}\frac{n!n^k}{(n+k)!}',
'The R bars correspond to actual terms of an infinite sum. Fading a bar means omitting it, so its mass needs a bound.'),
passage('Use an exact identity before approximating',
'Reindexing Q gives (n!/nⁿ)Σⱼ₌₀ⁿ⁻¹nʲ/j!, while R gives (n!/nⁿ)Σⱼ₌ₙ∞nʲ/j!. The ranges are disjoint and cover every nonnegative integer. Hence Q+R=n!eⁿ/nⁿ exactly. Repeated integration by parts gives γ(n,n)/(n−1)!=1−e⁻ⁿΣⱼ₌₀ⁿ⁻¹nʲ/j!, so R=(n!eⁿ/nⁿ)γ(n,n)/(n−1)!. This is an exact sum-to-integral identity, before any asymptotic expansion.\n\nFor certified computation, let tₖ=n!nᵏ/(n+k)! and retain k=0,…,K. The next term is tₖ₊₁ and all later ratios are at most ρ=n/(n+K+2)<1. Therefore 0<R−Σₖ₌₀ᴷtₖ≤tᴷ⁺¹/(1−ρ), where tᴷ⁺¹ here means the term t indexed by K+1, not a power. The formula below writes the index unambiguously. All values and this bound are exact rationals in our model. Rounded decimal labels do not change the rational enclosure.',
r'Q(n)+R(n)=\frac{n!e^n}{n^n},\quad 0<R(n)-\sum_{k=0}^{K}t_k\le\frac{t_{K+1}}{1-n/(n+K+2)}',
'The geometric comparison bounds every unseen positive bar using the first omitted bar and a maximum ratio.'),
passage('P needs a different sum-to-area bridge',
'In the reindexed P sum, apply Stirling to j! for j≥1; handle j=0 separately rather than substituting into 1/j. This gives P(n)=(√(2π)/n!)Σⱼ₌₁ⁿjⁿ⁺¹/²e⁻ʲ(1+1/(12j)+O(j⁻²)). The Stirling remainder can be bounded uniformly for integer j≥1. Euler summation applied to f(x)=xⁿ⁺¹/²e⁻ˣ relates its sampled sum to γ(n+3/2,n) plus half the final endpoint and a controlled remainder. The polynomial area scene isolates the endpoint mechanism in a simpler exact example; it is not a numerical evaluation of this changing-exponent f.\n\nThe source’s coarse Euler remainder here is O(nⁿe⁻ⁿ), which after division by n! is O(n⁻¹/²). The extra Stirling terms also contribute only O(n⁻¹/²): split the sum at j=n/2. On j≥n/2 the relative correction is O(1/n); below n/2, jⁿe⁻ʲ/(nⁿe⁻ⁿ)≤(√e/2)ⁿ, an exponential bound that absorbs polynomial factors. Thus P(n)=√(2π)γ(n+3/2,n)/n!+1/2+O(n⁻¹/²), where the 1/2 comes from the final endpoint after Stirling normalization.\n\nNow match the gamma theorem with x=n+1/2 and y=−1/2. Its normalized ratio is 1/2−(7/6)/√(2πn)+O(n⁻³/²). Also Γ(n+3/2)/n!=√n(1+O(1/n)), from the exact half-integer gamma formula and factorial Stirling. Multiplication therefore gives √(πn/2)−7/6+1/2+O(n⁻¹/²)=√(πn/2)−2/3+O(n⁻¹/²). This explicitly derives the constant, but the coarse error cannot justify the next coefficient. The sharper stated expansion is P(n)=√(πn/2)−2/3+(11/24)√(π/(2n))+4/(135n)−(71/1152)√(π/(2n³))+O(n⁻²). Obtaining all these coefficients requires a sharper method than the displayed coarse Euler remainder. We explicitly separate that stated source result from the derivation completed here.',
r'P(n)=\sqrt{\frac{\pi n}{2}}-\frac23+O(n^{-1/2})',
'The smaller polynomial shows exactly how area and endpoint terms arise. Its exactness is not transferred to the nonpolynomial P calculation.')])

lesson(64,'Composition of gamma and Stirling expansions for Q/R, explicit precision bookkeeping and high-precision verification. The source’s sharper P expansion is a stated result; constants hidden in asymptotic O-terms are not presented as numerical certificates.',[
passage('Scale the required precision backward',
'Suppose a normalized factor is 1/2+c n⁻¹/²+d n⁻³/²+O(n⁻⁵/²), and it will be multiplied by a factor of size √n. Its final remainder becomes O(n⁻²). To claim absolute O(n⁻²), the normalized input must therefore be accurate through O(n⁻⁵/²); stopping at O(n⁻³/²) would leave only O(n⁻¹). This backward precision audit prevents needless work and false accuracy claims.\n\nFor actual interval errors, use the exact inequality |(A+e_A)(B+e_B)−AB|≤|B|δ_A+|A|δ_B+δ_Aδ_B when |e_A|≤δ_A and |e_B|≤δ_B. The scene computes all three contributions with rational values. An asymptotic O-term is different: unless its constant and threshold are supplied, it describes eventual order, not a guaranteed numerical interval at n=10.',
r'\sqrt n\,O(n^{-5/2})=O(n^{-2})',
'The widths of the three blocks are computed error contributions; their sum is an actual bound, unlike an unspecified O constant.'),
passage('Use the exact Q/R split to avoid duplicate analysis',
'Let S(n)=n!eⁿ/nⁿ. Stirling gives S=√(2πn)(1+1/(12n)+1/(288n²)+O(n⁻³)). To use the gamma theorem for R/S=γ(n,n)/Γ(n), set x=n−1 and y=1, because x+1=n and x+y=n. The fixed-y hypothesis is respected. Then expand powers of n−1 in powers of n: (n−1)⁻¹/²=n⁻¹/²(1+1/(2n)+O(n⁻²)).\n\nSubstitution into the normalized theorem yields R/S=1/2+(1/√(2π))(1/(3√n)+1/(540n³/²))+O(n⁻⁵/²). Multiplying by S gives R=√(πn/2)+1/3+(1/12)√(π/(2n))+4/(135n)+(1/288)√(π/(2n³))+O(n⁻²). The coefficient 4/135 is 1/36+1/540: one part comes from Stirling normalization and the other from the gamma expansion. Finally Q=S−R, so odd half-density corrections change sign while shared terms remain. The exact rational R enclosure in the scene provides a check independent of these asymptotic manipulations.',
r'R(n)=\sqrt{\frac{\pi n}{2}}+\frac13+\frac1{12}\sqrt{\frac\pi{2n}}+\frac4{135n}+\frac1{288}\sqrt{\frac\pi{2n^3}}+O(n^{-2})',
'The exact partial sum and tail bound test the composed approximation without assuming the approximation is correct.'),
passage('Audit the final answer and its limits',
'The complementary result is Q(n)=√(πn/2)−1/3+(1/12)√(π/(2n))−4/(135n)+(1/288)√(π/(2n³))+O(n⁻²). Adding the displayed Q and R expansions cancels the constant and 1/n terms and reproduces the Stirling expansion of S. This structural check catches a sign error even when finite numerical values happen to be close. P has constant −2/3, not −1/3; similar leading growth does not make these families interchangeable.\n\nAll limits here take integer n→∞ with expansion orders and any shift parameters fixed. For a fixed α,β, log expansion gives (n+α)ⁿ⁺ᵝ=nⁿ⁺ᵝeᵅ(1+α(β−α/2)/n+O(n⁻²)); allowing α to grow with n would invalidate this derivation without new uniform estimates. The executable tests compare P/Q exactly and R through certified rational tails against high-precision reference evaluations. Such tests validate the implementation and can expose errors; the universal asymptotic claim comes from the controlled derivation and its stated source theorem, not the numerical samples.',
r'Q(n)=\sqrt{\frac{\pi n}{2}}-\frac13+\frac1{12}\sqrt{\frac\pi{2n}}-\frac4{135n}+\frac1{288}\sqrt{\frac\pi{2n^3}}+O(n^{-2})',
'The helper repeats the error audit at a smaller n, where omitted contributions are easier to see.')])


def exponential_scene(n):
    x=F(1,n);states=[]
    for degree in (1,2,3):
        terms=[x**k/F(factorial(k)) for k in range(degree+1)]
        center=sum(terms);first=x**(degree+1)/factorial(degree+1);bound=first/(1-x/F(degree+2))
        nodes=[]
        # Magnify the correction above 1. Each rectangle is one Taylor contribution.
        cursor=90
        for k in range(1,4):
            v=x**k/factorial(k);width=float(v/(x+x*x/2+x*x*x/6))*520
            nodes +=[rect(f'term{k}',cursor,170,width,64,'result' if k<=degree else 'muted',opacity=1 if k<=degree else .15),txt(f'label{k}',355,280+k*30,f'order {k}: {fs(v)}')];cursor+=width
        nodes +=[txt('head',355,65,f'Approximate exp(1/{n}), keeping degree {degree}'),txt('center',355,120,f'Exact rational center = {fs(center)}'),txt('bound',355,415,f'Omitted positive tail ≤ {fs(bound)}')]
        states.append(state(degree,'Exponentiation creates its own quadratic and cubic terms.',rf'e^{{1/{n}}}=\sum_{{k=0}}^{{{degree}}}\frac{{(1/{n})^k}}{{k!}}+r,\quad 0<r\le {tex(bound)}',nodes,'A geometric majorant bounds the exponential Taylor tail.',dict(n=n,degree=degree,center=fs(center),bound=fs(bound))))
    return states

def tail_scene(n):
    states=[];r=1-log(2)
    for size in (n,2*n,4*n):
        nodes=axes();maximum=2*size*exp(-size*r)
        pts=[(55+580*j/100,335-220*exp(-size*j/100)) for j in range(101)]
        nodes.append(path('majorant',pts,'active'))
        nodes.append(dict(id='tail-area',type='path',d='M55,335 '+' '.join(f'L{x:.3f},{y:.3f}' for x,y in pts)+' L635,335 Z',role='result',opacity=.25))
        nodes +=[txt('threshold',355,58,'Tail starts at v = r = 1 − log 2'),txt('bound',355,382,f'n={size}; tail ≤ 2(2/e)^n ≈ {2*(2/exp(1))**size:.4g}'),txt('axis-label',355,414,'Horizontal: v − r; vertical: normalized majorant','muted',14)]
        states.append(state(size,'An exponential majorant controls the discarded area.',rf'\int_r^\infty ne^{{-nv}}h(v)\,dv\le 2e^{{-nr}}=2(2/e)^n',nodes,'At u=1, r=1−log 2 and h(r)=2. Later h is no larger.',dict(n=size,r=r,bound=2*(2/exp(1))**size)))
    return states

def families_scene(n):
    lists=[[(F((n-k)**k*factorial(n-k),factorial(n))) for k in range(n+1)],[(F(factorial(n),factorial(n-k)*n**k)) for k in range(1,n+1)],pqr(n,n+4)[4][:-1]]
    states=[]
    for focus in range(3):
        nodes=[]
        for row,values in enumerate(lists):
            base=140+row*105;nodes.append(txt(f'name{row}',45,base-22,'PQR'[row]))
            for k,v in enumerate(values):
                x=90+k*48;h=float(v)*65
                nodes.append(rect(f'{row}-term{k}',x,base-h,35,h,'active' if row==focus else 'muted',opacity=1 if row==focus else .3))
            nodes.append(txt(f'end{row}',355,base+24,'finite: all terms shown' if row<2 else 'infinite: more terms continue →','muted',14))
        P,Q,R,E,_=pqr(n,n+4)
        nodes.append(txt('value',355,42,[f'P({n}) = {fs(P)}',f'Q({n}) = {fs(Q)}',f'R({n}): shown prefix ≈ {float(R):.6f}'][focus],'result'))
        states.append(state(focus,'Compare actual term families before using a shared leading scale.',rf'n={n}',nodes,'P/Q terminate; the R row is only a partial sum.',dict(n=n,P=fs(P),Q=fs(Q),Rlower=fs(R),Rerror=fs(E),focus=focus)))
    return states

V[61][2]=('Exponentiation creates cross terms',exponential_scene(12),exponential_scene(2))
V[62][2]=('Prove the discarded area is small',tail_scene(4),tail_scene(2))
V[63][0]=('Compare finite and infinite term families',families_scene(4),families_scene(2))
# Tie explanatory text to these specific representations.
a=CONTENT[61][1][2];CONTENT[61][1][2]=(a[0],a[1].replace('The error ledger is a smaller rational exercise in carrying such intermediate errors; it is not an alternative numerical proof of Stirling’s theorem.','The scene expands exp(1/n) with exact rational terms and a geometric bound on its positive tail. It exposes the quadratic and cubic contributions created by exponentiation; it is not an alternative numerical proof of Stirling’s theorem.'),a[2],'The helper’s exponential has a larger argument, making the quadratic and cubic terms easier to see.')
a=CONTENT[62][1][2];CONTENT[62][1][2]=(a[0],a[1].replace('The tail scene shows a separate exact positive-series enclosure used in the next lesson; it illustrates the same obligation to bound what is omitted.','The tail scene chooses u=1, so r=1−log 2 and h(r)=2. Its shaded majorant has total area 2e⁻ⁿʳ. Each frame rescales its height, while the certified area label decreases exponentially.'),a[2],'The shaded region is the majorant after v=r. Its area is evaluated analytically, not counted from pixels.')
a=CONTENT[63][1][0];CONTENT[63][1][0]=(a[0],a[1].replace('The scene focuses on R’s positive terms; its displayed partial sum is a lower bound, and the next passage supplies the upper bound.','The three rows show the actual terms of P, Q and R. The P and Q rows terminate; R continues beyond the displayed prefix. Its partial sum is a lower bound, and the next passage supplies the upper bound.'),a[2],'Finite rows end because their definitions end. The infinite R row needs an explicit bound for its unseen continuation.')
a=CONTENT[63][1][1];CONTENT[63][1][1]=(a[0],a[1].replace('Therefore 0<R−Σₖ₌₀ᴷtₖ≤tᴷ⁺¹/(1−ρ), where tᴷ⁺¹ here means the term t indexed by K+1, not a power. The formula below writes the index unambiguously.','Therefore the omitted mass is at most the first omitted term divided by 1−ρ, as the indexed formula below states.'),a[2],a[3])


def factorial_series_scene(z,maxn):
    """Exact evaluated factorial terms; coefficient existence is separate."""
    z=F(z);terms=[F(factorial(n))*z**n for n in range(maxn+1)];ss=[]
    for stage,focus in enumerate([1,maxn//2,maxn]):
        nodes=[line('axis',55,330,665,330),txt('heading',360,45,f'Formal coefficient aₙ=n!; evaluate at z={fs(z)}'),txt('subheading',360,78,'Bar height = |n! zⁿ|; exact labels, fixed scale','muted',14)]
        step=560/(maxn+1)
        for n,value in enumerate(terms):
            x=75+n*step;h=210*float(abs(value)/max(map(abs,terms)))
            nodes +=[rect(f'term{n}',x,330-h,step-12,h,'active' if n==focus else 'input'),txt(f'v{n}',x+(step-12)/2,320-h,fs(value),size=14),txt(f'n{n}',x+(step-12)/2,356,f'n={n}','muted',14)]
        ratio=abs(z)*(focus+1)
        nodes +=[txt('ratio',360,393,f'At n={focus}: |tₙ₊₁/tₙ| = {fs(ratio)}', 'result',16)]
        caps=['Early terms alone do not settle convergence.','Track the exact ratio of neighboring terms.','The ratio eventually exceeds 2, so terms cannot tend to zero.']
        ss.append(state(stage,caps[stage],r't_n=n!z^n,\qquad |t_{n+1}/t_n|=(n+1)|z|',nodes,'For fixed z≠0, eventually (n+1)|z|≥2. Formal coefficients remain valid.',dict(z=fs(z),terms=list(map(fs,terms)),focus=focus,ratio=fs(ratio))))
    return ss

def bernoulli_coeff_scene(maxn):
    """Compute inverse-series coefficients independently of Bernoulli recurrence."""
    d=[F(1,factorial(n+1)) for n in range(maxn+1)];c=[F(1)]
    for n in range(1,maxn+1):c.append(-sum(d[k]*c[n-k] for k in range(1,n+1)))
    ss=[]
    for focus in ([1,2,maxn] if maxn>2 else [1,2]):
        nodes=[txt('heading',360,45,'The coefficient stores Bₙ / n!, not Bₙ'),txt('inverse',360,82,'Invert D(z)=(eᶻ−1)/z; its constant is 1','muted',15)]
        step=500/(maxn+1)
        for n in range(maxn+1):
            x=160+n*step
            nodes +=[txt(f'index{n}',x,125,f'n={n}','muted',14),rect(f'cell{n}',x-35,145,70,52,'active' if n==focus else 'muted'),txt(f'c{n}',x,177,fs(c[n]),size=15),txt(f'factor{n}',x,236,f'×{factorial(n)}','active' if n==focus else 'muted',15),line(f'arrow{n}',x,250,x,277,'active',arrow=True),rect(f'out{n}',x-35,287,70,52,'result' if n==focus else 'muted'),txt(f'b{n}',x,319,fs(c[n]*factorial(n)),'result' if n==focus else 'muted',15)]
        nodes +=[txt('crow',65,177,'cₙ',size=16),txt('brow',65,319,'Bₙ',size=16),txt('audit',360,392,f'[z^{focus}] C(z)D(z) = 0; B{focus} = {fs(c[focus]*factorial(focus))}',size=15)]
        ss.append(state(focus,'Recover the Bernoulli number by multiplying its stored coefficient by n!.',rf'B_{{{focus}}}={factorial(focus)}\,[z^{{{focus}}}]\frac z{{e^z-1}}={tex(c[focus]*factorial(focus))}',nodes,'Cancel z before inversion; C(z)D(z)=1 coefficient by coefficient.',dict(n=focus,denominator=list(map(fs,d)),coefficients=list(map(fs,c)),bernoulli=list(map(lambda n:fs(c[n]*factorial(n)),range(maxn+1))))))
    return ss

V[47][2]=('Formal existence versus evaluated terms',factorial_series_scene(F(1,2),6),factorial_series_scene(F(1),4))
V[51][2]=('Recover Bernoulli numbers from stored coefficients',bernoulli_coeff_scene(4),bernoulli_coeff_scene(2))

def build():
    plan=json.loads(PLAN.read_text());out=[]
    ranges={47:'164–166',48:'166–167',49:'168–169',50:'166',51:'167–171',52:'171–174',53:'178–180',54:'180–184',55:'182–188',56:'181–188',57:'193–202',58:'193–202',59:'203–204',60:'204–206',61:'206–208',62:'211–215',63:'210–216',64:'215–217'}
    for source in plan['lessons']:
        order=source['order'];scope,passages=CONTENT[order];pp=[]
        for j,(title,text,formula,bridge) in enumerate(passages):
            name,main,helpstates=V[order][j]
            # Helps with identical polynomial need fewer repeated tiles, not unrelated data.
            if order==60: helpstates=helpstates[:2] if j<2 else helpstates
            for s in main+helpstates:
                for node in s['diagram']['nodes']:
                    if node.get('role')=='result':node['result']=True;node['phase']='result'
            d=demo(f'b{order}-p{j+1}-demo',name,f'batch-b-{order}-{j}',main,helpstates,question(order,j),question(order,j,True),bridge)
            for tr in d['transitions']:tr['from']=tr.pop('from_')
            pp.append(dict(id=f'b{order}-p{j+1}',title=title,text=text,formula=formula,demonstration=d))
        out.append(dict(id=source['id'],order=order,title=source['title'],source=dict(book='Donald E. Knuth, The Art of Computer Programming, Volume 1, third edition',section='; '.join('§'+s['section']+' '+s['title'] for s in source['source_sections']),pdfPages=ranges[order],pagination='One-based supplied ebook pages, not printed page numbers'),provenance='Original explanations, examples, scenes and assessments after the cited concepts. Source equation images were inspected privately; no source images, source prose or exercise bank are included.',scope=scope,sections=[dict(id=f'b{order}-section',title=source['title'],passages=pp)]))
    return out

class ModelTests(unittest.TestCase):
    def test_gamma_reversion_and_composed_coefficients(self):
        # Formal polynomial composition, separate from the displayed narration.
        u=[F(0),F(1),F(1,3),F(1,36),F(-1,270),F(1,4320)]
        total=[F(0)]*7;power=[F(1)]
        for k in range(1,7):
            power=conv(power,u)[:7]
            if k>=2:
                for j,value in enumerate(power):total[j]+=F((-1)**k,k)*value
        self.assertEqual(total,[F(0),F(0),F(1,2),F(0),F(0),F(0),F(0)])
        unit=u[1:];inverse=[F(1)]
        for n in range(1,5):inverse.append(-sum(unit[k]*inverse[n-k] for k in range(1,n+1)))
        self.assertEqual([1+inverse[1],*inverse[2:]],[F(2,3),F(1,12),F(-2,135),F(1,864)])
        self.assertEqual(F(-4,135)-F(1,18),F(-23,270))
        self.assertEqual(F(1,3)*F(1,2)+F(23,270)-F(1,12)-F(1,6),F(1,540))
        self.assertEqual(F(1,36)+F(1,540),F(4,135))
        self.assertEqual(F(-7,6)+F(1,2),F(-2,3))

    def test_convolution_evaluation(self):
        # A different oracle: product values and polynomial interpolation uniqueness.
        for a in ([1,2,3],[0,0],[-2,1],[F(1,2),F(2,3)]):
            for b in ([2,0,1],[1,-1],[F(3,5)]):
                c=conv(a,b)
                for z in range(len(c)+1):self.assertEqual(sum(v*z**i for i,v in enumerate(c)),sum(v*z**i for i,v in enumerate(a))*sum(v*z**i for i,v in enumerate(b)))
        self.assertEqual(conv([], [1]),[])
    def test_recurrence_matrix_oracle(self):
        def mul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
        def power(n):
            M=[[2,1],[1,0]];R=[[1,0],[0,1]]
            while n:
                if n&1:R=mul(R,M)
                M=mul(M,M);n//=2
            return R
        for u in range(-2,3):
            for v in range(-2,3):
                a=[u,v]
                for k in range(2,24):a.append(2*a[-1]+a[-2])
                for k in range(1,24):
                    M=power(k-1);self.assertEqual(a[k],M[0][0]*v+M[0][1]*u)
    def test_symmetry_by_independent_product(self):
        for xs in ([1,2],[2,3,5],[-1,2,4]):
            c=[F(1)]
            for x in xs:c=conv(c,[1,x])
            for r in range(len(xs)+1):self.assertEqual(c[r],sum(__import__('functools').reduce(lambda a,b:a*b,(xs[i] for i in inds),1) for inds in combinations(range(len(xs)),r)))
            p1=sum(xs);p2=sum(x*x for x in xs);self.assertEqual(c[2],F(p1*p1-p2,2))
    def test_scan_exhaustive_ties(self):
        for n in range(1,6):
            for xs in product(range(3),repeat=n):
                end=scan(list(xs))[-1]['computed'];m=max(xs);j=max(i for i,x in enumerate(xs) if x==m)
                self.assertEqual((end['m'],end['j'],end['comparisons']),(m,j,n-1));self.assertTrue(0<=end['updates']<=n-1)
    def test_record_distributions_by_permutation(self):
        for n in range(1,8):
            counts=[0]*n
            for perm in permutations(range(1,n+1)):counts[records(perm)-1]+=1
            p=[F(1)]
            for k in range(2,n+1):p=conv(p,[F(k-1,k),F(1,k)])
            self.assertEqual(p,[F(x,factorial(n)) for x in counts]);mean=sum(k*v for k,v in enumerate(p));var=sum((k-mean)**2*v for k,v in enumerate(p))
            self.assertEqual(mean,sum((F(1,k) for k in range(2,n+1)),F(0)))
            self.assertEqual(var,sum((F(1,k)-F(1,k*k) for k in range(1,n+1)),F(0)))
    def test_coins_by_outcome_enumeration(self):
        for n in range(1,7):
            for p in (F(0),F(1,3),F(1,2),F(1)):
                expected=[F(0)]*(n+1)
                for bits in product([0,1],repeat=n):
                    weight=F(1)
                    for b in bits:weight*=p if b else 1-p
                    expected[sum(bits)]+=weight
                actual=[F(1)]
                for _ in range(n):actual=conv(actual,[1-p,p])
                self.assertEqual(actual,expected);self.assertEqual(sum(actual),1)
    def test_bernoulli_inverse_and_polynomial(self):
        B=bernoulli(14);self.assertEqual(B[:5],[1,F(-1,2),F(1,6),0,F(-1,30)])
        a=[F(B[k],factorial(k)) for k in range(15)];b=[F(1,factorial(k+1)) for k in range(15)];self.assertEqual(conv(a,b)[:15],[1]+[0]*14)
        for m in range(2,12):self.assertEqual(bernpoly(m,F(0)),bernpoly(m,F(1)))
        # Sum-of-powers identity via Bernoulli polynomial values is independent of Euler scene.
        for d in range(1,7):
            for n in range(1,12):self.assertEqual(sum(k**d for k in range(n)),(bernpoly(d+1,F(n))-bernpoly(d+1,F(0)))/(d+1))
    def test_euler_exact_and_quadrature(self):
        for n in range(1,15):
            for power in (2,3):
                end=integral(n,power)[-1]['computed'];self.assertEqual(F(end['approx']),end['sum'])
        # Composite Simpson integrates x²/x³ exactly, separate from antiderivative model.
        for n in (2,4,6):
            for d in (2,3):
                h=F(n,20);q=h/3*sum((1 if i in (0,20) else (4 if i%2 else 2))*(i*h)**d for i in range(21))
                self.assertEqual(q,F(n**(d+1),d+1))
    def test_reciprocal_and_interval_products(self):
        for n in range(1,101):
            s=error_intervals(n)[-1]['computed'];self.assertEqual(F(s['truth'])-F(s['approx']),F(s['error']));self.assertLessEqual(F(s['error']),F(s['bound']))
            b=budget(n)[-1]['computed'];A=F(b['A']);B=F(b['B']);e=F(b['delta'])
            for sa,sb in product([-1,1],repeat=2):self.assertLessEqual(abs((A+sa*e)*(B+sb*e)-A*B),F(b['bound']))
    def test_pqr_independent_and_precision(self):
        from decimal import Decimal as D, localcontext
        with localcontext() as context:
            context.prec=80
            def decimal(f):return D(f.numerator)/D(f.denominator)
            for n in (1,2,4,8,16,32,64):
                P,Q,R,E,terms=pqr(n,160)
                P2=sum(F(j**(n-j)*factorial(j),factorial(n)) for j in range(n+1))
                self.assertEqual(P,P2)
                # Independent transcendental oracle: the exact complementary exponential sum.
                S=D(factorial(n))*D(n).exp()/D(n)**n
                ref=S-decimal(Q)
                self.assertLessEqual(decimal(R),ref+D('1e-70'))
                self.assertLessEqual(ref,decimal(R+E)+D('1e-70'))
            self.assertEqual(pqr(4)[0],F(17,8));self.assertEqual(pqr(4)[1],F(71,32))
    def test_harmonic_stirling_bounds(self):
        from decimal import Decimal as D, localcontext
        with localcontext() as context:
            context.prec=75
            # Standard reference constants; these numerical comparisons supplement the proofs.
            gamma=D('0.577215664901532860606512090082402431042159335939923598805767234884867726')
            pi80=D('3.141592653589793238462643383279502884197169399375105820974944592307816406')
            for n in (1,2,4,10,30):
                h=sum((D(1)/k for k in range(1,n+1)));center=h-D(n).ln()-D(1)/(2*n)+D(1)/(12*n*n)-D(1)/(120*n**4)
                self.assertLess(center,gamma);self.assertLess(gamma-center,D(1)/(252*n**6))
                center=D(factorial(n)).ln()-(D(n)+D('.5'))*D(n).ln()+n-D(1)/(12*n)
                sigma=(2*pi80).ln()/2;self.assertLess(center,sigma);self.assertLess(sigma-center,D(1)/(360*n**3))
    def test_exponential_tail_enclosures(self):
        from decimal import Decimal as D, localcontext
        with localcontext() as context:
            context.prec=60
            for n in range(1,25):
                for s in exponential_scene(n):
                    c=s['computed'];center=F(c['center']);bound=F(c['bound']);actual=(D(1)/n).exp()
                    low=D(center.numerator)/center.denominator;high=low+D(bound.numerator)/bound.denominator
                    self.assertLess(low,actual);self.assertLess(actual,high)
    def test_schema_and_geometry(self):
        lessons=build();self.assertEqual([x['order'] for x in lessons],list(range(47,65)))
        for l in lessons:
            self.assertEqual(len(l['sections'][0]['passages']),3)
            for p in l['sections'][0]['passages']:
                self.assertGreater(len(p['text']),500)
                d=p['demonstration'];self.assertGreaterEqual(len(d['states']),2);self.assertGreaterEqual(len(d['simplerHelp']['states']),2)
                for c in (d['check'],d['simplerHelp']['check']):self.assertEqual(len(c['choices']),len(set(c['choices'])))
                for s in d['states']+d['simplerHelp']['states']:
                    ids=[o['id'] for o in s['diagram']['nodes']];self.assertEqual(len(ids),len(set(ids)))
                    for node in s['diagram']['nodes']:
                        for key in ('x','x2'):self.assertTrue(0<=node.get(key,1)<=720,(l['order'],node))
                        for key in ('y','y2'):self.assertTrue(0<=node.get(key,1)<=440,(l['order'],node))
                        if node['type']=='rect':self.assertGreaterEqual(node['height'],0)

if __name__=='__main__':
    if '--test' in sys.argv:unittest.main(argv=[sys.argv[0]])
    elif '--check' in sys.argv:
        stored=json.loads((ROOT/'content/fullbook/batch-B.json').read_text());assert stored==build(), 'Generated batch B content is stale';print('Batch B generated content is current')
    else:
        target=ROOT/'content/fullbook/batch-B.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(build(),indent=2,ensure_ascii=False)+'\n');print(f'Wrote {target}: 18 lessons, 54 passages')
