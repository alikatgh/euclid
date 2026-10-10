"""Independent review oracles: not imported by either authoring model."""
import importlib.util,itertools,random,copy
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parent
def module(letter):
 spec=importlib.util.spec_from_file_location(letter,R/f'fullbook-batch-{letter}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
C=module('C');D=module('D');rng=random.Random(482223);checks=0
def test(x):
 global checks
 assert x;checks+=1
for b in [64,73,100]:
 W=b**5
 for _ in range(300):
  a=rng.randrange(-W+1,W);v=rng.randrange(-W+1,W);oldflag=bool(rng.randrange(2))
  for opcode in [1,2,3]:
   m=C.Machine(b);m.reg[0]=C.Word.number(a,b);m.mem[0]=C.instruction(20,opcode,b=b);m.mem[20]=C.Word.number(v,b);m.overflow=oldflag;m.step()
   if opcode<3:
    z=a+(v if opcode==1 else -v);test(m.reg[0].mag==abs(z)%W);test(m.overflow==(oldflag or abs(z)>=W));test(m.reg[0].value==(1 if z>=0 else -1)*(abs(z)%W))
   else:test(m.reg[0].value*W+m.reg[7].value==a*v);test(m.overflow==oldflag)
  den=rng.randrange(1,W);hi=rng.randrange(den);lo=rng.randrange(W);sgn=rng.choice([-1,1]);ds=rng.choice([-1,1]);m=C.Machine(b);m.reg[0]=C.Word.number(hi,b,sgn);m.reg[0].sign=sgn;m.reg[7]=C.Word.number(lo,b,-sgn);m.reg[7].sign=-sgn;m.mem[0]=C.instruction(20,4,b=b);m.mem[20]=C.Word.number(ds*den,b);m.step()
  test(m.reg[0].value*ds*den+m.reg[7].value==sgn*(hi*W+lo));test(m.reg[0].sign==sgn*ds and m.reg[7].sign==sgn);test(m.reg[7].mag<den)
 for source in range(20,25):
  for destination in range(20,25):
   for count in range(6):
    initial={i:rng.randrange(100) for i in range(20,31)};expected=initial.copy()
    for i in range(count):expected[destination+i]=expected[source+i]
    m=C.Machine(b);m.mem={i:C.Word.number(v,b) for i,v in initial.items()};m.mem[0]=C.instruction(source,7,count,b=b);m.reg[1]=C.Word.number(destination,b);m.step();test(all(m.at(i).value==v for i,v in expected.items()));test(m.reg[1].value==destination+count);test(m.clock==1+2*count)
for n in range(7):
 tr=C.coroutine(n);pending=0;yielded=consumed=0
 for st in tr:
  if st['caption'].startswith('Yield'):yielded+=1
  if st['caption'].startswith('Consumer uses'):consumed+=1
  test(yielded-consumed==(st['held'] is not None));test(0<=yielded-consumed<=1)
 test(yielded==consumed==n);test(tr[-1]['total']==sum(i*i for i in range(1,n+1)))
for n,io,c,k in itertools.product(range(7),range(1,5),range(1,5),range(1,5)):
 tr=C.buffers(n,io,c,k)
 for st in tr:
  test(len(st['states'])==k);test(len(set(st['ready']))==len(st['ready']));test(set(st['ready'])=={i for i,x in enumerate(st['states']) if x=='READY'})
  test((sum(x=='FILLING' for x in st['states'])==int(st['device'] is not None)));test((sum(x=='PROCESSING' for x in st['states'])==int(st['cpu'] is not None)))
  if st['cpu'] and st['device']:test(st['cpu']['buffer']!=st['device']['buffer'])
 test(tr[-1]['output']==list(range(n)));test(tr[-1]['time']==(0 if not n else n*(io+c) if k==1 else io+c+(n-1)*max(io,c)))
for cap in range(1,6):
 for _ in range(70):
  ops=[(rng.choice(['put','get']),rng.randrange(100)) for i in range(30)];ref=[];trace=D.circular_queue(cap,ops)
  for (op,val),st in zip(ops,trace[1:]):
   if op=='put' and len(ref)<cap:ref.append(val)
   elif op=='get' and ref:ref.pop(0)
   test(st['data']['logical']==ref)
# Enumerate all loopless directed graphs through four vertices, independent permutation-order feasibility.
for n in range(1,5):
 edges=[(i,j) for i in range(n) for j in range(n) if i!=j]
 for mask in range(1<<len(edges)):
  adj={str(i):[str(j) for bit,(u,j) in enumerate(edges) if u==i and mask>>bit&1] for i in range(n)}
  tr=D.topological(adj);last=tr[-1]['data'];possible=any(all(p.index(i)<p.index(j) for i in adj for j in adj[i]) for p in itertools.permutations(map(str,range(n))))
  test(possible==(len(last['output'])==n))
  if possible:test(all(last['output'].index(i)<last['output'].index(j) for i in adj for j in adj[i]))
  else:test(last['cycle'][0]==last['cycle'][-1]);test(all(b in adj[a] for a,b in zip(last['cycle'],last['cycle'][1:])))
for _ in range(500):
 rows,cols=rng.randrange(1,5),rng.randrange(1,5);A=[[Fraction(rng.randrange(-4,5),rng.randrange(1,4)) for j in range(cols)] for i in range(rows)];p,q=rng.randrange(rows),rng.randrange(cols)
 if not A[p][q]:A[p][q]=Fraction(2,3)
 original=copy.deepcopy(A);tr=D.pivot_trace(A,p,q);B=[[Fraction(x) for x in r] for r in tr[-1]['data']['dense']];test(A==original)
 # Repeating exactly the same source pivot is an involution, an independent algebraic property.
 returned=[[Fraction(x) for x in r] for r in D.pivot_trace(B,p,q)[-1]['data']['dense']];test(returned==A)
 for st in tr:
  d=st['data'];ids={e['id'] for e in d['entries']};test({v for r in d['rowLinks'] for v in r}==ids=={v for col in d['columnLinks'] for v in col});test(all(Fraction(e['value']) for e in d['entries']))
for rows,cols in itertools.product(range(1,8),repeat=2):
 lo=(-3,2)
 for column in [False,True]:
  offsets=[D.offset(i,j,rows,cols,lo,column) for i in range(lo[0],lo[0]+rows) for j in range(lo[1],lo[1]+cols)]
  test(sorted(offsets)==list(range(rows*cols)))
print('Independent C/D review:',checks,'assertions passed')
