#!/usr/bin/env python3
"""Original deterministic companion models. Integer MIX subset, not a full MIX installation.
Private source consulted: supplied third-edition Volume 1, PDF 223–367.
Run --test for independent checks; default regenerates batch-C.json.
"""
import copy, itertools, json, math, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SemanticError(ValueError): pass
class Word:
 def __init__(self,sign=1,bs=None,b=64):
  self.b=b; self.sign=sign; self.bs=list(bs or [0]*5)
  if not 64<=b<=100 or sign not in (-1,1) or len(self.bs)!=5 or any(type(x)!=int or not 0<=x<b for x in self.bs): raise SemanticError('invalid word')
 @classmethod
 def number(cls,n,b=64,zero=1):
  if abs(n)>=b**5: raise SemanticError('word magnitude out of range')
  mag=abs(n); bs=[0]*5
  for j in range(4,-1,-1): bs[j]=mag%b; mag//=b
  return cls((-1 if n<0 else 1) if n else zero,bs,b)
 @property
 def mag(self): return sum(x*self.b**(4-i) for i,x in enumerate(self.bs))
 @property
 def value(self): return self.sign*self.mag
 def data(self): return {'sign':self.sign,'bytes':self.bs[:],'value':self.value}
 def __eq__(self,other): return isinstance(other,Word) and self.data()==other.data() and self.b==other.b

def field(f):
 l,r=divmod(f,8)
 if not 0<=l<=r<=5: raise SemanticError('invalid field; floating point is unsupported')
 return l,r

def load(w,f):
 l,r=field(f); bs=w.bs[max(l,1)-1:r] if r else []
 return Word(w.sign if l==0 else 1,[0]*(5-len(bs))+bs,w.b)

def store(dst,src,f):
 l,r=field(f); out=copy.deepcopy(dst); n=r-max(l,1)+1 if r else 0
 if l==0: out.sign=src.sign
 if n: out.bs[max(l,1)-1:r]=src.bs[-n:]
 return out

def instruction(address,c,f=5,i=0,b=64,zero=1):
 if not 0<=i<=6 or abs(address)>=b*b: raise SemanticError('bad encoded address/index')
 return Word((-1 if address<0 else 1) if address else zero,[abs(address)//b,abs(address)%b,i,f,c],b)

OPS={'NOP':(0,0),'ADD':(1,5),'SUB':(2,5),'MUL':(3,5),'DIV':(4,5),'NUM':(5,0),'CHAR':(5,1),'HLT':(5,2),'MOVE':(7,1),'STJ':(32,2),'STZ':(33,5)}
for k,f in [('SLA',0),('SRA',1),('SLAX',2),('SRAX',3),('SLC',4),('SRC',5)]: OPS[k]=(6,f)
for k,f in [('JMP',0),('JSJ',1),('JOV',2),('JNOV',3),('JL',4),('JE',5),('JG',6),('JGE',7),('JNE',8),('JLE',9)]: OPS[k]=(39,f)
for k,j in [('A',0),*[(str(i),i) for i in range(1,7)],('X',7)]:
 for prefix,c,f in [('LD',8,5),('ST',24,5),('CMP',56,5),('INC',48,0),('DEC',48,1),('ENT',48,2),('ENN',48,3)]: OPS[prefix+k]=(c+j,f)
 OPS['LD'+k+'N']=(16+j,5)
 for suffix,f in [('N',0),('Z',1),('P',2),('NN',3),('NZ',4),('NP',5)]: OPS['J'+k+suffix]=(40+j,f)

class Machine:
 def __init__(self,b=64):
  self.b=b; self.mem={}; self.reg=[Word(b=b) for _ in range(8)]; self.j=0; self.pc=0; self.overflow=False; self.cmp=0; self.clock=0; self.halted=False; self.undefined=False; self.trace=[]
 def at(self,p):
  if not 0<=p<4000: raise SemanticError('memory address outside 0..3999')
  return copy.deepcopy(self.mem.get(p,Word(b=self.b)))
 def put(self,p,w): self.at(p); self.mem[p]=copy.deepcopy(w)
 def snapshot(self): return {'pc':self.pc,'A':self.reg[0].data(),'X':self.reg[7].data(),'I':[r.value for r in self.reg[1:7]],'J':self.j,'overflow':self.overflow,'comparison':self.cmp,'clock':self.clock,'halted':self.halted,'undefined':self.undefined,'memory':{str(k):v.data() for k,v in sorted(self.mem.items())}}
 def setreg(self,k,w):
  if 1<=k<=6 and w.mag>=self.b**2: raise SemanticError('undefined index-register overflow')
  self.reg[k]=w
 def add(self,k,v):
  old=self.reg[k]; n=old.value+v; cap=self.b**(2 if 1<=k<=6 else 5)
  if abs(n)>=cap:
   if 1<=k<=6: raise SemanticError('undefined index-register overflow')
   self.overflow=True
  self.setreg(k,Word.number((1 if n>=0 else -1)*(abs(n)%cap),self.b,old.sign if n==0 else (-1 if n<0 else 1)))
 def step(self):
  if self.halted: raise SemanticError('machine halted')
  saved=copy.deepcopy(self.__dict__)
  try: self._step()
  except SemanticError:
   self.__dict__=saved; raise
 def _step(self):
  w=self.at(self.pc); a1,a2,i,f,c=w.bs; address=w.sign*(a1*self.b+a2)
  if i>6: raise SemanticError('index selector outside 0..6')
  m=address+(self.reg[i].value if i else 0)
  if abs(m)>=self.b**2: raise SemanticError('undefined effective-address overflow')
  before=self.snapshot(); oldpc=self.pc; self.pc+=1; cost=1; take=False
  if c==0: pass
  elif c in (1,2,3,4):
   v=load(self.at(m),f); A=self.reg[0]; X=self.reg[7]
   if c in (1,2): self.add(0,v.value*(1 if c==1 else -1)); cost=2
   elif c==3:
    n=A.mag*v.mag; sign=A.sign*v.sign; self.reg[0]=Word.number(n//self.b**5,self.b,sign); self.reg[7]=Word.number(n%self.b**5,self.b,sign); self.reg[0].sign=self.reg[7].sign=sign; cost=10
   else:
    cost=12
    if v.mag==0 or A.mag>=v.mag:
     self.overflow=True; self.undefined=True; self.halted=True # stop instead of inventing unspecified register bits
    else:
     q,r=divmod(A.mag*self.b**5+X.mag,v.mag); self.reg[0]=Word.number(q,self.b); self.reg[0].sign=A.sign*v.sign; self.reg[7]=Word.number(r,self.b); self.reg[7].sign=A.sign
  elif c==5:
   A,X=self.reg[0],self.reg[7]
   if f==2: self.halted=True
   elif f==0:
    n=int(''.join(str(x%10) for x in A.bs+X.bs)); self.overflow|=n>=self.b**5; self.reg[0]=Word.number(n%self.b**5,self.b,A.sign); self.reg[0].sign=A.sign; cost=10
   elif f==1:
    ds=[30+int(x) for x in str(A.mag).zfill(10)]; self.reg[0]=Word(A.sign,ds[:5],self.b); self.reg[7]=Word(X.sign,ds[5:],self.b); cost=10
   else: raise SemanticError('unsupported special instruction')
  elif c==6:
   if f>5 or m<0: raise SemanticError('invalid shift')
   seq=self.reg[0].bs[:] if f<2 else self.reg[0].bs+self.reg[7].bs; n=len(seq)
   if f>=4:
    k=m%n; seq=seq[k:]+seq[:k] if f==4 else (seq[-k:]+seq[:-k] if k else seq)
   else:
    k=min(m,n); seq=seq[k:]+[0]*k if f%2==0 else [0]*k+seq[:n-k]
   self.reg[0].bs=seq[:5]
   if f>=2: self.reg[7].bs=seq[5:]
   cost=2
  elif c==7:
   dest=self.reg[1].value
   for k in range(f): self.at(m+k); self.at(dest+k)
   if dest+f>=self.b**2: raise SemanticError('undefined MOVE index overflow')
   for k in range(f): self.put(dest+k,self.at(m+k))
   self.reg[1]=Word.number(dest+f,self.b,self.reg[1].sign); cost=1+2*f
  elif 8<=c<=23:
   k=(c-8)%8; v=load(self.at(m),f)
   if c>=16: v.sign*=-1
   self.setreg(k,v); cost=2
  elif 24<=c<=33:
   src=self.reg[c-24] if c<32 else Word.number(self.j if c==32 else 0,self.b)
   self.put(m,store(self.at(m),src,f)); cost=2
  elif c==39:
   if f>9: raise SemanticError('invalid jump modifier')
   take=[True,True,self.overflow,not self.overflow,self.cmp<0,self.cmp==0,self.cmp>0,self.cmp>=0,self.cmp!=0,self.cmp<=0][f]
   if f in (2,3): self.overflow=False
  elif 40<=c<=47:
   if f>5: raise SemanticError('invalid register jump')
   v=self.reg[c-40].value; take=[v<0,v==0,v>0,v>=0,v!=0,v<=0][f]
  elif 48<=c<=55:
   k=c-48
   if f in (0,1): self.add(k,m*(1 if f==0 else -1))
   elif f in (2,3):
    v=Word.number(m,self.b,w.sign)
    if f==3: v.sign*=-1
    self.setreg(k,v)
   else: raise SemanticError('invalid address-transfer modifier')
  elif 56<=c<=63:
   lhs=load(self.reg[c-56],f).value; rhs=load(self.at(m),f).value; self.cmp=(lhs>rhs)-(lhs<rhs); cost=2
  else: raise SemanticError('I/O opcodes 34–38 use separate device model; unsupported in this interpreter')
  if take:
   self.at(m)
   if not(c==39 and f==1): self.j=oldpc+1
   self.pc=m
  self.clock+=cost; self.trace.append({'before':before,'after':self.snapshot(),'instruction':w.data(),'effectiveAddress':m,'opcode':c,'field':f,'cost':cost,'jumpTaken':take})
 def run(self,limit=1000):
  for _ in range(limit):
   if self.halted: return self
   self.step()
  raise SemanticError('step limit exceeded')

# Deliberately restricted MIXAL assembler: source triples, forward global/local
# instruction addresses, left-to-right + - * : expressions, ORIG/EQU/CON/END,
# word-part CON and literal pool. No ALF, /, //, cards or implicit undefined symbols.
def assemble(lines,b=64):
 symbols={}; local={str(i):[] for i in range(10)}; locations=[]; pc=0; rows=[]; literals=[]
 def expr(s,here,row,allow_future=False):
  if not s: return 0
  parts=re.findall(r'\d[BF]|[A-Z][A-Z0-9]*|\d+|\*|[+:\-]',s)
  if ''.join(parts)!=s: raise SemanticError('unsupported MIXAL expression')
  def atom(t):
   if t=='*': return here
   if re.fullmatch(r'\d[BF]',t):
    candidates=[(r,p) for r,p in local[t[0]] if r<row] if t[1]=='B' else [(r,p) for r,p in local[t[0]] if r>row]
    if not candidates: raise SemanticError('unresolved local reference')
    return candidates[-1][1] if t[1]=='B' else candidates[0][1]
   if t.isdigit(): return int(t)
   if t not in symbols: raise SemanticError('unresolved symbol '+t)
   return symbols[t]
  sign=1
  if parts and parts[0] in ('+','-'): sign=-1 if parts.pop(0)=='-' else 1
  if not parts: raise SemanticError('empty expression')
  val=sign*atom(parts.pop(0))
  while parts:
   op=parts.pop(0)
   if not parts: raise SemanticError('missing expression operand')
   rhs=atom(parts.pop(0)); val={'+':lambda:val+rhs,'-':lambda:val-rhs,'*':lambda:val*rhs,':':lambda:8*val+rhs}[op]()
  return val
 for row,(label,op,arg) in enumerate(lines):
  here=pc; locations.append(here)
  if label:
   if re.fullmatch(r'\dH',label): local[label[0]].append((row,here))
   else:
    if label in symbols: raise SemanticError('duplicate symbol')
    symbols[label]=expr(arg,here,row) if op=='EQU' else here
  if op=='ORIG': pc=expr(arg,here,row)
  elif op not in ('EQU','END'): rows.append((row,here,op,arg)); pc+=1
  if op=='END': break
 def constant(s,here,row):
  out=Word(b=b)
  for part in s.split(','):
   match=re.fullmatch(r'(.*?)(?:\(([^()]*)\))?',part); val,fs=match.groups(); n=expr(val,here,row); w=Word.number(n,b,-1 if val.startswith('-') else 1)
   out=store(out,w,expr(fs,here,row) if fs else 5)
  return out
 mem={}; listing=[]
 for row,here,op,arg in rows:
  if not 0<=here<4000 or here in mem: raise SemanticError('overlapping/out-of-range assembled location')
  if op=='CON': w=constant(arg,here,row)
  else:
   if op not in OPS: raise SemanticError('unsupported mnemonic '+op)
   c,f=OPS[op]; match=re.fullmatch(r'(.*?)(?:,([0-6]))?(?:\(([^()]*)\))?',arg); a,ix,fs=match.groups()
   if a.startswith('=') and a.endswith('='):
    target=pc+len(literals); literals.append((target,constant(a[1:-1],here,row))); addr=target
   else: addr=expr(a,here,row)
   w=instruction(addr,c,expr(fs,here,row) if fs else f,int(ix or 0),b,-1 if a.startswith('-') else 1)
  mem[here]=w; listing.append({'line':row+1,'address':here,'op':op,'operand':arg,'word':w.data()})
 for p,w in literals:
  if p in mem or not 0<=p<4000: raise SemanticError('invalid literal pool')
  mem[p]=w
 end=[(i,a) for i,(_,op,a) in enumerate(lines) if op=='END']; start=expr(end[0][1],locations[end[0][0]],end[0][0]) if end else min(mem)
 return mem,symbols,start,listing

def run_program(lines,b=64):
 mem,symbols,start,listing=assemble(lines,b); m=Machine(b); m.mem=mem; m.pc=start; m.run(); return m,symbols,listing

SUM=[('', 'ORIG','100'),('START','ENTA','0'),('','ENT1','-4'),('LOOP','ADD','DATA+4,1'),('','INC1','1'),('','J1N','LOOP'),('','STA','TOTAL'),('','HLT','0'),('DATA','CON','7'),('','CON','-2'),('','CON','9'),('','CON','4'),('TOTAL','CON','0'),('','END','START')]
CALL=[('','ORIG','200'),('START','ENTA','11'),('','JMP','TWICE'),('','STA','RESULT'),('','HLT','0'),('TWICE','STJ','RETURN'),('','STA','TEMP'),('','ADD','TEMP'),('RETURN','JSJ','0'),('TEMP','CON','0'),('RESULT','CON','0'),('','END','START')]

def cycles(p):
 if sorted(p)!=list(range(1,len(p)+1)): raise SemanticError('not a permutation of 1..n')
 seen=set(); out=[]
 for start in range(1,len(p)+1):
  if start in seen: continue
  cyc=[]; x=start
  while x not in seen: seen.add(x); cyc.append(x); x=p[x-1]
  out.append(cyc)
 return out

def inverse_trace(p):
 cycles(p); a=[0]+p[:]; out=[{'array':a[1:],'current':0,'savedNext':None,'caption':'Every positive cell still holds its original successor.'}]
 for start in range(1,len(a)):
  if a[start]<0: continue
  prev=start; cur=a[start]
  while cur!=start:
   nxt=a[cur]; a[cur]=-prev
   out.append({'array':a[1:],'current':cur,'savedNext':nxt,'caption':f'Save successor {nxt} before replacing cell {cur} by tagged predecessor −{prev}.'}); prev,cur=cur,nxt
  a[start]=-prev; out.append({'array':a[1:],'current':start,'savedNext':None,'caption':f'Close this cycle: cell {start} receives tagged predecessor −{prev}.'})
 a=[-x for x in a[1:]]; out.append({'array':a,'current':0,'savedNext':None,'caption':'Remove tags only after every cycle is complete; the array is the inverse.'}); return out

def canonical(p):
 cs=cycles(p); cs=[c[c.index(min(c)):]+c[:c.index(min(c))] for c in cs]; cs.sort(key=lambda c:c[0],reverse=True); seq=sum(cs,[]); records=[i for i,x in enumerate(seq) if i==0 or x<min(seq[:i])]; return cs,seq,records

def coroutine(n):
 # Explicit resumable control labels; no Python generator hides continuation state.
 state={'producerPC':'MAKE','consumerPC':'WAIT','next':1,'held':None,'total':0,'done':False}; trace=[]
 while not state['done']:
  if state['consumerPC']=='WAIT':
   if state['producerPC']=='ADVANCE': state['next']+=1; state['producerPC']='MAKE'; action='Resume producer after its last yield; advance retained local counter.'
   elif state['next']>n: state['producerPC']='END'; state['consumerPC']='END'; state['done']=True; action='Send explicit END; consumer terminates without inventing another value.'
   else: state['held']=state['next']**2; state['producerPC']='ADVANCE'; state['consumerPC']='USE'; action=f"Yield {state['held']}; save producer continuation ADVANCE."
  else: state['total']+=state['held']; state['held']=None; state['consumerPC']='WAIT'; action='Consumer uses exactly one value, then resumes its WAIT continuation.'
  trace.append(dict(state,caption=action))
 return trace

def interpret(code):
 stack=[]; pc=0; trace=[]
 for _ in range(100):
  if not 0<=pc<len(code): raise SemanticError('object PC out of range')
  op,arg=code[pc]; old=pc; pc+=1
  if op=='PUSH': stack.append(arg)
  elif op=='ADD':
   if len(stack)<2: raise SemanticError('object stack underflow')
   b=stack.pop(); a=stack.pop(); stack.append(a+b)
  elif op=='DUP':
   if not stack: raise SemanticError('object stack underflow')
   stack.append(stack[-1])
  elif op!='HALT': raise SemanticError('unknown object opcode')
  trace.append({'pc':old,'next':pc,'op':op,'argument':arg,'stack':stack[:],'caption':f'Fetch object instruction {old}: {op}; dispatch one handler; object stack becomes {stack}.'})
  if op=='HALT': return trace
 raise SemanticError('object step limit')

def buffers(count,io,compute,k):
 if min(io,compute,k)<=0 or count<0: raise SemanticError('positive service times/capacity required')
 statuses=['EMPTY']*k; items=[None]*k; ready=[]; device=None; cpu=None; produced=0; output=[]; t=0; trace=[]
 def snap(action):
  trace.append({'time':t,'states':statuses[:],'items':items[:],'ready':ready[:],'device':copy.deepcopy(device),'cpu':copy.deepcopy(cpu),'output':output[:],'issued':produced,'eof':produced==count,'caption':action})
 snap('Start: every buffer is EMPTY; no transfer or computation is active.')
 while len(output)<count:
  if device and device['end']==t:
   i=device['buffer']; statuses[i]='READY'; ready.append(i); device=None; snap(f'Input completes into buffer {i}; only now may the CPU read it.')
  if cpu and cpu['end']==t:
   i=cpu['buffer']; output.append(items[i]); items[i]=None; statuses[i]='EMPTY'; cpu=None; snap(f'Processing finishes; release buffer {i} for later input.')
  if cpu is None and ready:
   i=ready.pop(0); statuses[i]='PROCESSING'; cpu={'buffer':i,'end':t+compute}; snap(f'CPU acquires oldest READY buffer {i}; ownership prevents overwrite.')
  if device is None and produced<count and 'EMPTY' in statuses:
   i=statuses.index('EMPTY'); statuses[i]='FILLING'; items[i]=produced; produced+=1; device={'buffer':i,'end':t+io}; snap(f'Issue input into EMPTY buffer {i}; device busy until time {t+io}.')
  if len(output)==count: break
  ends=[job['end'] for job in (device,cpu) if job]
  if not ends: raise AssertionError('deadlock')
  if cpu is None: snap('CPU waits: no READY buffer exists yet.')
  if device is None and produced<count: snap('Input waits: backpressure leaves no EMPTY buffer.')
  t=min(ends)
 snap('Known-count end of input: issue no speculative extra read; drain all processing.')
 return trace

def pack(records,capacity):
 if capacity<=0: raise SemanticError('capacity must be positive')
 # Lengths are metadata. No ambiguous sentinel is inserted in payload.
 stream=''.join(records); out=[]; buf=''; trace=[{'blocks':[],'buffer':'','consumed':0,'caption':'Start an empty physical block; record lengths are retained separately.'}]
 for i,ch in enumerate(stream):
  buf+=ch
  if len(buf)==capacity: out.append(buf); buf=''
  trace.append({'blocks':out[:],'buffer':buf,'consumed':i+1,'caption':f'Append payload character {i+1}; '+('flush exactly full block.' if not buf else 'retain partial block.')})
 if buf: out.append(buf); buf=''; trace.append({'blocks':out[:],'buffer':buf,'consumed':len(stream),'caption':'Flush final partial block with its valid length; padding is not data.'})
 return trace

def tests():
 checks=0
 def check(ok):
  nonlocal checks
  assert ok; checks+=1
 for b in (64,73,100):
  for sign in (-1,1):
   w=Word(sign,[1,2,3,4,5],b); src=Word(-sign,[8,9,10,11,12],b)
   for l in range(6):
    for r in range(l,6):
     f=8*l+r; got=load(w,f); reference=sum(w.bs[j-1]*b**(r-j) for j in range(max(1,l),r+1)); check(got.mag==reference and got.sign==(sign if l==0 else 1))
     stored=store(w,src,f)
     # Independent position-wise oracle: source byte 5 aligns with destination R.
     for j in range(1,6): check(stored.bs[j-1]==(src.bs[5-r+j-1] if max(1,l)<=j<=r else w.bs[j-1]))
     check(stored.sign==(-sign if l==0 else sign))
  m,s,_=run_program(SUM,b); check(m.at(s['TOTAL']).value==18); check(len(m.trace)==16); check(m.clock==21)
  m,s,_=run_program(CALL,b); check(m.at(s['RESULT']).value==22); check(m.at(s['RETURN']).bs[2:]==[0,1,39]); check(m.j==202)
  for sign in (-1,1):
   m=Machine(b); m.reg[0]=Word.number(0,b,sign); m.mem[0]=instruction(20,1,b=b); m.mem[20]=Word.number(0,b); m.step(); check(m.reg[0].sign==sign)
  for v in [0,1,12345,b**5-1]:
   m=Machine(b); m.reg[0]=Word.number(v,b,-1); m.reg[0].sign=-1; m.mem[0]=instruction(0,5,1,b=b); m.mem[1]=instruction(0,5,0,b=b); m.step(); m.step(); check(m.reg[0].value==-v and m.reg[0].sign==-1)
  for f in (2,3):
   for flag in (False,True):
    m=Machine(b); m.overflow=flag; m.mem[0]=instruction(10,39,f,b=b); m.step(); check(not m.overflow); check(m.pc==(10 if (flag if f==2 else not flag) else 1)); check(m.j==(1 if m.pc==10 else 0))
  m=Machine(b); m.mem[0]=instruction(10,4,b=b); m.step(); check(m.overflow and m.undefined and m.halted)
  m=Machine(b); m.mem[0]=instruction(20,7,3,b=b); m.reg[1]=Word.number(21,b); m.mem[20]=Word.number(7,b); m.step(); check([m.at(i).value for i in range(20,24)]==[7]*4)
  for f in range(6):
   for n in (0,1,5,10,13):
    m=Machine(b); m.reg[0]=Word(-1,[1,2,3,4,5],b); m.reg[7]=Word(1,[6,7,8,9,10],b); m.mem[0]=instruction(n,6,f,b=b); m.step(); check(m.reg[0].sign==-1 and m.reg[7].sign==1)
  for bad in [instruction(0,34,b=b),instruction(0,8,63,b=b),instruction(-1,8,b=b)]:
   m=Machine(b); m.mem[0]=bad; before=m.snapshot()
   try: m.step(); raise AssertionError('should reject')
   except SemanticError: check(m.snapshot()==before)
 # Arithmetic oracle uses integer sign/magnitude arithmetic independently of Word helpers.
 for b in (64,100):
  W=b**5
  for a in (-W+1,-17,-1,0,1,19,W-1):
   for v in (-23,-1,0,1,31):
    for op,c in [('ADD',1),('SUB',2)]:
     m=Machine(b); m.reg[0]=Word.number(a,b,-1); m.mem[0]=instruction(20,c,b=b); m.mem[20]=Word.number(v,b); m.step(); total=a+(v if c==1 else -v); check(m.reg[0].mag==abs(total)%W); check(m.overflow==(abs(total)>=W)); check(m.reg[0].sign==((-1 if a<=0 else 1) if total==0 else (-1 if total<0 else 1)))
    m=Machine(b); m.reg[0]=Word.number(a,b,-1); m.mem[0]=instruction(20,3,b=b); m.mem[20]=Word.number(v,b); m.step(); check(m.reg[0].mag*W+m.reg[7].mag==abs(a*v)); check(m.reg[0].sign==m.reg[7].sign==((-1 if a<=0 else 1)*(-1 if v<0 else 1)))
  for n in (0,1,17,W-1,W+23):
   for v in (-31,-2,1,19):
    m=Machine(b); m.reg[0]=Word.number(n//W,b); m.reg[0].sign=-1; m.reg[7]=Word.number(n%W,b); m.mem[0]=instruction(20,4,b=b); m.mem[20]=Word.number(v,b); m.step()
    if n//W>=abs(v): check(m.undefined and m.overflow)
    else: check(m.reg[0].mag==n//abs(v)); check(m.reg[7].mag==n%abs(v)); check(m.reg[0].sign==(-1 if v>0 else 1)); check(m.reg[7].sign==-1)
  for f in range(6):
   for count in (0,1,5,10,13):
    m=Machine(b); m.reg[0]=Word(-1,[1,2,3,4,5],b); m.reg[7]=Word(1,[6,7,8,9,10],b); m.mem[0]=instruction(count,6,f,b=b); m.step(); original=list(range(1,6 if f<2 else 11)); n=len(original)
    if f>=4: ref=[original[(j+count if f==4 else j-count)%n] for j in range(n)]
    else: ref=[original[j+count if f%2==0 else j-count] if 0<=(j+count if f%2==0 else j-count)<n else 0 for j in range(n)]
    check(m.reg[0].bs+(m.reg[7].bs if f>=2 else [])==ref)
  for reg in range(8):
   for negative in (False,True):
    m=Machine(b); m.mem[0]=instruction(20,8+reg+(8 if negative else 0),b=b); m.mem[20]=Word.number(-25,b); m.step(); check(m.reg[reg].value==(25 if negative else -25))
   m=Machine(b); m.reg[reg]=Word.number(-25,b); m.mem[0]=instruction(20,24+reg,b=b); m.step(); check(m.at(20).value==-25)
   m=Machine(b); m.reg[reg]=Word.number(3,b); m.mem[0]=instruction(20,56+reg,45,b=b); m.mem[20]=Word.number(5,b); m.step(); check(m.cmp==-1)
  m=Machine(b); m.reg[1]=Word.number(0,b,-1); m.mem[0]=instruction(0,48,2,1,b); m.step(); check(m.reg[0].sign==1)
  m=Machine(b); m.mem[0]=instruction(0,48,2,0,b,-1); m.step(); check(m.reg[0].sign==-1)
 lines=[('', 'ORIG','500'),('START','ENTA','2+3*4'),('2H','DECA','1'),('','JAP','2B'),('','JMP','2F'),('2H','HLT','0'),('','END','START')]
 mem,sy,start,listing=assemble(lines); check(mem[500].bs[:2]==[0,20]); check(mem[502].bs[:2]==[7,53]); check(mem[503].bs[:2]==[7,56]); check(start==500)
 for n in range(0,8):
  for p in itertools.permutations(range(1,n+1)):
   inv=inverse_trace(list(p))[-1]['array']; check(all(inv[p[i]-1]==i+1 for i in range(n)))
   cs,seq,records=canonical(list(p)); check(len(records)==len(cs)); reconstructed=[seq[a:z] for a,z in zip(records,records[1:]+[n])]; check(reconstructed==cs)
  D=sum(all(p[i]!=i+1 for i in range(n)) for p in itertools.permutations(range(1,n+1))); check(D==sum((-1)**j*math.factorial(n)//math.factorial(j) for j in range(n+1)))
 for n in range(12):
  tr=coroutine(n); check(tr[-1]['total']==sum(i*i for i in range(1,n+1))); check(tr[-1]['done'])
  for k in (1,2,3):
   for io,c in [(1,4),(4,1),(3,3)]:
    tr=buffers(n,io,c,k); check(tr[-1]['output']==list(range(n))); check(tr[-1]['issued']==n)
    for s in tr:
     check(all(x in ('EMPTY','FILLING','READY','PROCESSING') for x in s['states'])); check(len(s['ready'])==s['states'].count('READY'))
     if s['cpu']: check(s['states'][s['cpu']['buffer']]=='PROCESSING')
     if s['device']: check(s['states'][s['device']['buffer']]=='FILLING')
    if n: check(tr[-1]['time']==(n*(io+c) if k==1 else io+c+(n-1)*max(io,c)))
 for records in [[],[''],['AB','CDEFG','H'],['ABCDE'],['A','','BC']]:
  for cap in range(1,7):
   tr=pack(records,cap); blocks=tr[-1]['blocks']; check(''.join(blocks)==''.join(records)); check(all(0<len(x)<=cap for x in blocks))
 check(interpret([('PUSH',3),('DUP',None),('ADD',None),('HALT',None)])[-1]['stack']==[6])
 print(f'Batch C: {checks} independent/invariant assertions passed.'); return checks

# Geometry is generated from semantic state. Each family has distinct causal layout.
def node(kind,id,**kw): return dict(type=kind,id=id,**kw)
def text(id,x,y,s,role='input',**kw): return node('text',id,x=x,y=y,text=str(s),fontSize=kw.pop('fontSize',17),anchor='middle',role=role,**kw)
def rect(id,x,y,w,h,role='input',**kw): return node('rect',id,x=x,y=y,width=w,height=h,role=role,**kw)
def line(id,x,y,x2,y2,role='active'): return node('line',id,x=x,y=y,x2=x2,y2=y2,role=role,strokeWidth=2,arrow=True)
def diagram(title,desc,nodes,invariant=''): return {'title':title,'description':desc,'viewBox':[0,0,720,440],'nodes':nodes,'invariant':invariant}
def array_diagram(values,active=0,title='Memory cells',saved=None):
 ns=[]; n=max(1,len(values)); size=min(78,620/n)
 for i,v in enumerate(values):
  x=50+i*size; role='active' if i+1==active else ('result' if v<0 else 'input'); ns += [rect(f'cell-{i}',x,170,size-8,60,role),text(f'value-{i}',x+(size-8)/2,207,v,role),text(f'index-{i}',x+(size-8)/2,150,i+1,'muted')]
 if saved is not None: ns += [rect('saved',265,290,190,55,'active'),text('saved-label',360,322,f'saved next = {saved}','active'),line('save-arrow',360,230,360,285)]
 return diagram(title,'Each cell is an address; the number inside is a successor or tagged predecessor.',ns,'Save the original successor before overwriting its cell.')
def word_diagram(rows,title='Separate sign and byte positions',active=None):
 ns=[]
 for ri,(label,w) in enumerate(rows):
  y=75+ri*115; ns += [text('label-'+str(ri),110,y+25,label)]
  for i,v in enumerate([('−' if w['sign']<0 else '+')]+w['bytes']):
   x=205+i*75; role='active' if active is None or i in active else 'muted'; ns += [rect(f'w{ri}-{i}',x,y,65,52,role),text(f'v{ri}-{i}',x+32,y+33,v,role),text(f'p{ri}-{i}',x+32,y-12,i,'muted')]
 # Rows may be independent A/X registers; never imply an unauthored transfer between them.
 return diagram(title,'The sign is position zero, outside the five positional digits.',ns,'Byte magnitudes stay within 0 … b−1; the sign bit is independent.')
def flow_diagram(labels,active,title,detail=''):
 ns=[]
 for i,label in enumerate(labels):
  x=45+(i%3)*225; y=70+(i//3)*140; role='active' if i==active else 'input'; ns += [rect('stage-'+str(i),x,y,190,65,role),text('stage-label-'+str(i),x+95,y+38,label,role)]
  if i<len(labels)-1:
   nx=45+((i+1)%3)*225; ny=70+((i+1)//3)*140
   ns.append(line('edge-'+str(i),x+195,y+32,nx-5,ny+32)) if ny==y else ns.append(node('path','edge-'+str(i),d=f'M {x+95} {y+70} V {y+107} H {nx+95} V {ny-8}',role='active',fill='none',arrow=True))
 if detail: ns.append(text('detail',360,397,detail,'result',result=True))
 return diagram(title,'Control moves between the named operations; highlighted node is the current operation.',ns)
def cycle_diagram(p,visited=None,title='Follow directed images'):
 ns=[]; n=len(p); positions={i+1:(360+145*math.cos(2*math.pi*i/n),200+145*math.sin(2*math.pi*i/n)) for i in range(n)} if n else {}
 for a,b in enumerate(p,1):
  x,y=positions[a]; xx,yy=positions[b]; role='active' if visited and a in visited else 'muted'
  if a==b:
   ns.append(node('path','arrow-'+str(a),d=f'M {x-18} {y-17} C {x-65} {y-80}, {x+65} {y-80}, {x+18} {y-17}',role=role,fill='none',arrow=True))
   ns.append(text('edge-label-'+str(a),x,y-65,f'{a}→{b}','muted',fontSize=14))
  else:
   dist=math.hypot(xx-x,yy-y); dx=(xx-x)/dist; dy=(yy-y)/dist; bend=25 if p[b-1]==a else 0; mx=(x+xx)/2-dy*bend; my=(y+yy)/2+dx*bend
   ns.append(node('path','arrow-'+str(a),d=f'M {x+dx*25} {y+dy*25} Q {mx} {my}, {xx-dx*27} {yy-dy*27}',role=role,fill='none',arrow=True))
   ns.append(text('edge-label-'+str(a),mx-dy*12,my+dx*12,f'{a}→{b}','muted',fontSize=14))
 for a,(x,y) in positions.items():
  role='active' if visited and a in visited else 'input'; ns += [node('circle','object-'+str(a),x=x,y=y,r=23,role=role),text('name-'+str(a),x,y+6,a,role)]
 return diagram(title,'Edges mean an object is renamed to its image, not a swap of the two endpoints.',ns,'Every vertex has exactly one outgoing and one incoming edge.')
def buffer_diagram(s):
 ns=[]; k=len(s['states'])
 for i,st in enumerate(s['states']):
  x=65+i*min(210,570/k); role='active' if st in ('FILLING','PROCESSING') else ('result' if st=='READY' else 'muted')
  ns += [rect('buffer-'+str(i),x,180,170,85,role),text('buf-name-'+str(i),x+85,205,f'buffer {i}'),text('buf-state-'+str(i),x+85,231,st,role),text('buf-item-'+str(i),x+85,253,f"item {s['items'][i]}",'muted',fontSize=14)]
 ns += [rect('device',65,55,200,65,'active' if s['device'] else 'muted'),text('device-label',165,85,'INPUT DEVICE'),text('device-status',165,107,'BUSY' if s['device'] else 'READY','active',fontSize=14),rect('cpu',455,55,200,65,'active' if s['cpu'] else 'muted'),text('cpu-label',555,85,'CPU'),text('cpu-status',555,107,'WORKING' if s['cpu'] else 'WAITING','active',fontSize=14)]
 for name in ('device','cpu'):
  if s[name]:
   x=150+s[name]['buffer']*min(210,570/k); ns.append(line(name+'-ownership',165 if name=='device' else 555,125,x,173))
 ns += [text('time',360,325,f"t = {s['time']}"),text('queue',360,355,f"READY FIFO: {s['ready']}"),text('done',360,391,f"finished items: {s['output']}",'result',result=True)]
 return diagram('Ownership controls overlap','Only a READY buffer can move to PROCESSING. Input requires an EMPTY buffer.',ns,'One owner per buffer; no CPU read while FILLING.')
def packing_diagram(s,capacity):
 ns=[]; blocks=s['blocks']+[s['buffer']]; blocks=blocks[-4:]
 for i,block in enumerate(blocks):
  y=65+i*80
  for j in range(capacity):
   x=110+j*min(75,500/capacity); role='result' if i<len(blocks)-1 else 'active'; ns += [rect(f'pack-{i}-{j}',x,y,60,48,role),text(f'char-{i}-{j}',x+30,y+31,block[j] if j<len(block) else '·',role)]
 ns.append(text('cursor',360,415,f"consumed = {s['consumed']} characters",'result',result=True))
 return diagram('Logical stream into physical blocks','A full block flushes; the cursor restarts at the next block without losing a character.',ns,'Concatenating valid output payloads and the pending buffer reconstructs the consumed prefix.')
def frame(i,caption,diag,formula='',data=None): return {'id':f's{i}','caption':caption,'formula':formula,'diagram':diag,'data':data or {}}
def machine_frames(m,listing=None,mode='control'):
 states=[]
 if m.trace:
  initial=m.trace[0]['before']; states.append(frame('initial','Before the first fetched instruction: registers and control retain the input state.',word_diagram([('A before',initial['A']),('X before',initial['X'])]),data=initial))
 for i,t in enumerate(m.trace):
  s=t['after']; cap=f"At address {t['before']['pc']}: opcode {t['opcode']}, F={t['field']}, M={t['effectiveAddress']}. Next PC={s['pc']}; elapsed {s['clock']}u."
  if mode=='words': d=word_diagram([('A',s['A']),('X',s['X'])],'Register result after one executed instruction')
  else:
   d=flow_diagram(['fetch word','decode A I F C','form M','execute handler','save next PC','fetch / halt'],3,'One real instruction executes',f"A={s['A']['value']}   I1={s['I'][0]}   J={s['J']}   PC={s['pc']}")
   d['nodes'] += [text('fetch-address',140,130,f"address {t['before']['pc']}",'active',fontSize=14),text('decode-values',360,130,f"C={t['opcode']}, F={t['field']}",'active',fontSize=14),text('effective',590,130,f"M={t['effectiveAddress']}",'active',fontSize=14)]
  d['nodes'].append(text('machine-flags',360,340,f"overflow={'ON' if s['overflow'] else 'off'}; compare={s['comparison']}",'active',fontSize=15))
  states.append(frame(i,cap,d,rf"t={s['clock']}u,\quad A={s['A']['value']},\quad I_1={s['I'][0]},\quad J={s['J']}",{'pc':s['pc'],'fetchedAddress':t['before']['pc'],'opcode':t['opcode'],'A':s['A'],'X':s['X'],'I':s['I'],'J':s['J'],'overflow':s['overflow'],'comparison':s['comparison'],'clock':s['clock'],'effectiveAddress':t['effectiveAddress'],'memory':s['memory']}))
 return states

# Original authored prose, notation, transfer prompts; no source program is reproduced.
LESSON_TEXT={
65:(
 ('A sign is not a sixth digit','A MIX word has five byte positions and a separate sign. Here b is the number of values a byte can hold, with 64 ≤ b ≤ 100. Byte d₁ is the most significant. Its contribution is d₁b⁴, whereas d₅ contributes only d₅. A MIX byte is not the modern eight-bit byte.\n\nOur main example encodes −130 in base 64. Two full groups of 64 and two remaining units occupy the last two compartments. Changing to b=100 changes the compartments to 1 and 30; the represented integer is still −130. A portable program must not assume that a single byte can contain 80.',r'\operatorname{value}(s,d_1,\ldots,d_5)=s\sum_{j=1}^{5}d_jb^{5-j},\quad s\in\{-1,1\},\quad0\le d_j<b'),
 ('Equal values can have different representations','Positive zero and negative zero have identical byte magnitudes and different signs. Comparison treats them as equal, but a sign-sensitive load, multiplication, or conversion can preserve or reveal the distinction. Therefore storing only a language integer silently loses information.\n\nThe model retains a sign and five digits even when the magnitude is zero. The two-byte index registers are represented with three leading zero bytes; a value too large for their actual width is rejected rather than silently truncated.',r'+0=-0\text{ numerically},\qquad (+,0,0,0,0,0)\ne(-,0,0,0,0,0)\text{ as words}'),
 ('An address identifies a shelf','MIX has 4000 memory words, addressed 0 through 3999. A and X hold full words, I1 through I6 hold signed two-byte values, and J holds a nonnegative two-byte return address. Memory location 130 and the numeric value 130 are different kinds of thing. A load uses an address to find a word; an enter instruction uses an address field as a number.\n\nThe trace demonstrates representation, not a theorem that every Python integer fits in MIX. The width condition is essential: at base 64 a five-byte magnitude must be below 64⁵.',r'0\le\text{memory address}<4000,\qquad |I_i|<b^2,\qquad |A|,|X|<b^5'),
 ('Transfer the representation rule','When a sign is negative and every byte is zero, do not erase the sign. When the base changes, recompute positional digits instead of copying their labels. These two habits prevent different classes of emulator bugs: losing representation and confusing an integer with its encoding.\n\nFor a new example, 193 is 3·64+1, so its final bytes are 3 and 1. The same value in base 100 ends with 1 and 93. The bytes may differ while every integer calculation agrees.',r'193=3\cdot64+1=1\cdot100+93')),
66:(
 ('A field is an inclusive interval','Number the sign position 0 and bytes 1 through 5. A legal field L:R satisfies 0 ≤ L ≤ R ≤ 5. Its encoded F byte is 8L+R. Thus 2:4 is encoded by 20, not by 24. The interval selects adjacent positions, not a mask of unrelated bits.\n\nLoading selects the source field, right-aligns its bytes, and fills the remaining leading bytes with zeros. It takes the source sign only when L=0. A field excluding the sign loads a positive value even from a negative word.',r'F=8L+R,\quad (L,R)=(\lfloor F/8\rfloor,F\bmod8)'),
 ('Store is not load backward','A store selects destination positions. It takes the required number of rightmost bytes from the register and inserts them into that destination interval. All unselected destination bytes survive. The sign changes exactly when position zero belongs to the field.\n\nThe main trace loads bytes 2 through 4 from a negative word, then places a register’s final two bytes into destination positions 1 and 2. The two operations align different objects; treating store as a reversed load would corrupt the untouched memory.',r'\text{destination}[L:R]\gets\text{rightmost register bytes of the required width}'),
 ('Sign-only fields expose the rule','Field 0:0 has no magnitude bytes. Loading it gives signed zero. Storing it changes only the destination sign. Field 1:5 copies all five magnitude bytes but deliberately leaves the sign out.\n\nIndex registers impose a second constraint: loading a field whose value needs more than two bytes is undefined in MIX. The interpreter reports that case before changing any register. A field can be syntactically legal and still be inappropriate for the chosen destination.',r'\operatorname{load}_{0:0}(s,d_1,\ldots,d_5)=(s,0,0,0,0,0)'),
 ('Preservation is part of correctness','To verify a partial store, check every unselected byte, not merely the new field value. The independent tests cover all 21 legal intervals at several byte bases and both signs. Invalid intervals, such as 4:2, are rejected.\n\nA new two-byte register value 5,6 stored into field 2:3 of a word 1,2,3,4,5 produces 1,5,6,4,5. The memory sign remains unchanged because the field starts after zero.',r'j\notin[L,R]\implies \text{new position }j=\text{old position }j')),
67:(
 ('Overflow is a persistent observation','For ADD and SUB, first compute the signed mathematical result. If its magnitude does not fit, retain its magnitude modulo b⁵ and turn overflow on. An ordinary nonoverflowing addition does not turn an already lit overflow indicator off. A result of numerical zero keeps A’s previous sign.\n\nThis makes two kinds of state visible: a register value and a historical flag. The trace uses small, exact signed values before showing a boundary addition at the largest representable magnitude.',r'W=b^5,\qquad |A_{\rm stored}|=|A_{\rm old}+V|\bmod W'),
 ('A and X form a ten-byte magnitude','Multiplication places the high five bytes in A and low five in X. Both signs become the algebraic product sign, including when the product is zero. Division instead treats A:X as one ten-byte magnitude with A’s sign; X’s old sign is irrelevant.\n\nIf V is nonzero and |A|<|V|, the quotient fits in A. Its sign is the quotient sign, while the remainder takes the old sign of A. If these conditions fail, MIX specifies undefined register information and overflow. Our model stops with an explicit undefined-state marker instead of inventing meaningful quotient bits.',r'N=|A|W+|X|=q|V|+r,\quad0\le r<|V|,\quad |A|<|V|'),
 ('Shifts move bytes, comparisons select fields','SLA and SRA shift only A; SLAX and SRAX shift the concatenated ten bytes; SLC and SRC rotate those ten bytes. Signs are never shifted. A shift count is a byte count, so shifting by one is not multiplying by two.\n\nCMP compares the same selected field in the register and memory. It does not compare an entire register to a right-aligned memory field. Its indicator is less, equal, or greater, and negative zero compares equal to positive zero.',r'\operatorname{CMP}_{L:R}(R,M)=\operatorname{sign}\bigl(\operatorname{field}_{L:R}(R)-\operatorname{field}_{L:R}(M)\bigr)'),
 ('Know where the semantics stop','The executable interpreter includes integer arithmetic, all six shifts and all register comparison families. Floating-point modifier 0:6 is excluded. Index-register arithmetic must fit two bytes; unlike A arithmetic, an overflowing index calculation has no specified wrapped result.\n\nA successful finite trace verifies this example, while the division identity explains all legal dividends. For a transfer case, 29 divided by −6 gives quotient −4 and remainder +5 when the dividend sign is positive.',r'29=(-4)(-6)+5')),
68:(
 ('Fetch a word, then decode it','An instruction is a word whose first two bytes and sign encode an address, followed by an index selector I, modifier F, and opcode C. The fetch uses PC to read that word. Only then can execution determine what the fields mean. F is often a field interval, but for jumps and address transfers it selects a variant.\n\nOur trace executes an assembled loop, not a list of prewritten captions. Each next PC, memory access, flag, and clock value comes from decoding the fetched word.',r'\text{instruction}=(\pm AA,I,F,C),\qquad M=\pm AA+\begin{cases}0&I=0\\rI_I&1\le I\le6\end{cases}'),
 ('Default next and taken next differ','Ordinarily the next instruction is at P+1. A taken jump uses M instead, and normally saves P+1 in J. An untaken conditional jump leaves J unchanged. JSJ is the explicit exception: it jumps while preserving J.\n\nThe index selector names a register; it is not itself the amount added. Thus address 120 indexed by register 1 containing −3 accesses location 117. Negative effective addresses can be valid numeric operands for ENTA but are invalid memory locations for LDA.',r'\text{taken ordinary jump}:\quad J\gets P+1,\quad PC\gets M'),
 ('Tests have their own state effects','JOV tests overflow and clears it if it was on; JNOV jumps when overflow is off and clears it if it was on. Consequently either instruction leaves overflow off. Comparison jumps leave the comparison indicator alone. Register-zero jumps treat either signed zero as zero.\n\nA single generic condition function is not enough if it omits these state effects. The test laboratory checks both outcomes of each overflow test and verifies J separately from PC.',r'\operatorname{JOV/JNOV}\implies O_{\rm after}=\mathrm{off}'),
 ('Reject before partially executing','The model validates memory addresses, index selectors, fields and supported modifiers. A diagnostic rolls the machine back to its preinstruction snapshot. This is a teaching guarantee for malformed encodings, not a claim that historical MIX defined every invalid program.\n\nThe difference matters when debugging: a failed load should not quietly advance PC and leave the learner inspecting a machine that never existed in the intended semantics.',r'\text{diagnostic}\implies S_{\rm after}=S_{\rm before}')),
69:(
 ('Issuing input does not finish input','IN starts a block transfer. If the same device is already busy, the instruction first waits for the prior operation. The newly started operation completes later. A program must not read its destination buffer while input is in progress. OUT has the dual obligation: do not modify its source buffer until output completes.\n\nThe executable scheduling model makes these states explicit. Its durations and block capacities are chosen teaching parameters, not measured MIX-device timings. The CPU and device can work simultaneously only on different owned data.',r'\mathrm{EMPTY}\to\mathrm{FILLING}\to\mathrm{READY}\to\mathrm{PROCESSING}\to\mathrm{EMPTY}'),
 ('Readiness tests and control operations','JBUS jumps while a device is busy; JRED jumps when ready. IOC waits for readiness and performs a device-specific operation such as a tape movement or printer page advance. Block sizes and allowed directions depend on the device, so a generic arbitrary-length read is not a complete MIX I/O model.\n\nOur integer instruction interpreter deliberately rejects opcodes 34–38. The separate scheduling model demonstrates readiness, ownership and waiting, without claiming tape positioning, disks, printer errors or a complete peripheral installation.',r'\mathrm{busy}(d,t)\iff t<t_{\rm completion}(d)'),
 ('Digits are characters before they are numbers','MIX character codes 30 through 39 encode decimal digits 0 through 9. CHAR writes ten decimal character bytes across A and X while preserving their signs. NUM reads each byte modulo ten to recover a decimal magnitude, preserves X and A’s sign, and can overflow A.\n\nThe code executes both conversions and tests their round trip for representable magnitudes. It does not pretend that the whole MIX character alphabet is ASCII or Unicode.',r'\operatorname{digit}(c)=c\bmod10,\qquad\operatorname{code}(d)=30+d'),
 ('Model time is not wall-clock time','MIX assigns relative instruction costs: ordinary loads, stores, additions, shifts and comparisons take 2u; multiplication and conversion take 10u; division takes 12u; MOVE takes (1+2F)u. Most other instructions take 1u, with waiting added where applicable.\n\nThe scheduling animation uses a separate chosen time scale. Neither Python execution duration nor animation speed is MIX execution time. A fast replay does not make an algorithm computationally cheaper.',r'T=\sum_i f_i c_i+T_{\rm waiting}')),
70:(
 ('Labels name locations, not line numbers','An assembler tracks a location counter. A machine instruction or CON occupies one word and advances it. ORIG changes it, and EQU binds a symbolic value without reserving storage. A printed source-line number is merely an editing aid.\n\nThe example starts at 100. START therefore names location 100 even though preceding source lines exist. LOOP resolves to the address at which its instruction is emitted. No runtime instruction searches for the text LOOP.',r'\mathrm{symbol}[\mathrm{label}]=\mathrm{location\ counter}'),
 ('Resolve an instruction’s references','The assembler first discovers label locations, then translates instruction operands into numeric fields. A forward instruction reference can therefore point to a definition appearing later. Our restricted assembler accepts these forward A-part references; it does not implement every MIXAL future-reference rule or silently allocate misspelled names.\n\nThe emitted word is the machine program. Its listing keeps both the symbolic operand and numeric address so the learner can inspect the translation, rather than trusting an opaque compile button.',r'\mathrm{LOOP}\longmapsto102\quad\text{in this original program}'),
 ('Local labels are relative to source position','A definition such as 2H introduces a local occurrence. A reference 2B means the nearest preceding 2H; 2F means the nearest following one. Neither refers to the same line. This is a source-order rule, even if ORIG makes numeric addresses run backward.\n\nThe model resolves local references using source-row positions. Multiple definitions of a global name are rejected, while repeated local definitions are meaningful.',r'2B=\text{last earlier }2H,\qquad2F=\text{first later }2H'),
 ('Separate assembly from execution','ORIG 100 does not make the CPU jump to 100 when encountered at runtime: there is no ORIG instruction in the emitted memory. END supplies the starting address. EQU 4 does not load 4 into any register.\n\nFor a new source sequence ORIG 600; A CON 9; B HLT 0, A is 600 and B is 601. Inserting an EQU line between them changes neither address. Moving ORIG instead relocates subsequent emitted words, so every symbolic reference must be resolved against the new locations.',r'\#\text{emitted words}=\#\text{machine instructions}+\#\text{data words}')),
71:(
 ('One word can be built in pieces','CON can construct a word by placing values into specified fields. Each placement behaves like a store into an initially positive-zero word; a later overlapping placement replaces that part. This is useful for packed data and instruction-like records.\n\nThe main trace constructs a word with a signed address field and small control bytes. The result is calculated by the same field operations tested for machine stores, so the diagram and the numeric encoding agree.',r'W_0=+0,\quad W_{k+1}=\operatorname{store}(W_k,V_k,F_k)'),
 ('Expressions have a declared grammar','MIXAL expressions evaluate binary operations from left to right, rather than following ordinary multiplication precedence. For example, 2+3*4 means 20. Colon combines field endpoints as 8L+R. An asterisk used as an atom denotes the current location.\n\nOur teaching assembler supports +, −, multiplication and colon, with explicit diagnostics for unsupported syntax. Full MIXAL also has division and scaled division; those operators and their signed-word subtleties are not implemented here.',r'(2+3)*4=20,\qquad 2:4=8\cdot2+4=20'),
 ('Literals create stored data','An operand such as =7= requests a constant word and uses its address. It is not an immediate add of seven. The restricted assembler puts literal words after the emitted source and includes them in memory. The program then fetches that constant exactly like any other data.\n\nEQU, ORIG, CON and END are supported. ALF and the full character alphabet, punched-card formats, general W-value expressions and automatic allocation of undefined symbols are outside this assembler’s declared coverage.',r'\mathrm{ADD}\ =7=\quad\rightsquigarrow\quad\mathrm{ADD}\ L,\ \mathrm{memory}[L]=7'),
 ('Inspect before running','Look at the location, sign, address bytes, index selector, F and C before treating the result as executable. An instruction word is data until fetched at PC; a data word may accidentally decode as an instruction if control falls into it. END and a terminating HLT keep the worked program’s control out of its data region.\n\nA new field assignment 12(4:5) stores 12 in the least significant two-byte field. It does not mean decimal concatenation with the existing word.',r'\mathrm{address\ bytes}\ne\mathrm{source\ text}')),
72:(
 ('A complete original summation program','This program sums four signed words 7, −2, 9 and 4. A is the running total. I1 begins at −4, and the effective data address is DATA+4+I1. Each loop adds exactly one element, increments I1, and repeats while it is negative. TOTAL receives 18, then HLT stops before the data words.\n\nThe example is assembled and executed in the included model at byte bases 64, 73 and 100. These values and this program are original to the companion; no textbook program has been copied.',r'A_k=\sum_{j=0}^{k-1}x_j,\qquad I1_k=k-4,\quad0\le k\le4'),
 ('The invariant connects code to mathematics','Number additions from k=0. Before addition k, the first k elements have been summed and the next address is DATA+k. The ADD extends that prefix by one; INC1 makes the next index k+1−4. The branch repeats exactly when another element remains.\n\nAt exit I1=0, so four additions have occurred and A is the full sum. This argument assumes every partial sum fits a word. A different input can overflow even if its final mathematical sum is small.',r'(\mathrm{DATA}+4)+(k-4)=\mathrm{DATA}+k'),
 ('Count actual executions','The trace has two initialization instructions, four iterations of three instructions, a store and a halt: 16 executed instructions. With the declared MIX costs, the elapsed time is 1+1+4(2+1+1)+2+1=21u. Instruction count and elapsed MIX units are different measurements.\n\nThe final conditional branch is executed but not taken. Omitting it from a frequency count gives the wrong cost even though the final memory value remains right.',r'N_{\rm instructions}=2+3n+2,\qquad T(n)=4n+5\quad(n\ge1)'),
 ('A boundary case changes the program','This particular program specializes to four data words. Merely changing its counter to zero does not make it handle an empty input: it would still enter the body once. A generalized routine needs a pretest or a specified positive-length contract.\n\nA new three-element input 5, −8, 6 has partial totals 5, −3, 3. Use the invariant to predict both A and I1, not only the final answer. The smaller help run actually assembles a two-element version.',r'\text{precondition: }n\ge1\text{ and every partial sum fits}')),
73:(
 ('A permutation is a bijective renaming','A permutation p of {1,…,n} gives every object one image and every destination one preimage. Following images from an unvisited object must return to that starting object. It cannot first enter the middle of its path, because that would give one vertex two distinct preimages.\n\nThe model follows the arrows of an original six-element permutation and separates its disjoint cycles. Fixed points are cycles of length one and are retained when counting cycles.',r'p:\{1,\ldots,n\}\to\{1,\ldots,n\}\text{ is bijective}'),
 ('Declare composition order','We write p followed by q as p·q, following the source’s left-to-right convention. Thus (p·q)(i)=q(p(i)). Other texts use the opposite written order. The arrows remove the ambiguity: first follow p from i, then q from the intermediate object.\n\nComposition is generally noncommutative. Testing one object whose images differ is enough to disprove equality of the two composed mappings.',r'(p\cdot q)(i)=q(p(i))'),
 ('Cycles describe safe rearrangement','For a cycle (a b c), renaming sends a to b, b to c and c to a. If array contents are to move under that mapping, specify whether contents follow arrows or whether destination a reads old b. These conventions are inverses.\n\nA temporary cell preserves the value that would otherwise be destroyed during a rotation. The directed graph explains why one temporary cell suffices per cycle and why separate cycles can be processed independently.',r'p^k(a)=a\text{ for the cycle length }k'),
 ('Test the domain before the algorithm','An array with repeated destination 2 is not a permutation and invalidates the unique-predecessor proof. Our cycle routine rejects duplicates and missing labels. Empty and singleton permutations are valid boundaries.\n\nFor transfer, if p exchanges 1 and 2 and q exchanges 2 and 3, then applying p and then q sends 1 to 3. Reversing the order sends 1 to 2.',r'q(p(1))=3\ne2=p(q(1))')),
74:(
 ('An inverse reverses every arrow','If p(i)=j, its inverse must satisfy p⁻¹(j)=i. A separate destination array makes this easy: write the index i at destination p(i). Doing the same writes into the original array is unsafe because a future successor may be overwritten before it is read.\n\nOur original in-place variant follows one cycle, saves its next pointer in a temporary variable, then writes the predecessor with a negative tag. It is related to the source’s cycle-tagging idea but is not a copied implementation of either book algorithm.',r'p^{-1}(p(i))=i\quad(1\le i\le n)'),
 ('The saved successor justifies overwrite','During a cycle, current identifies the cell to replace, previous is its inverse image, and next is read from that cell before the write. Writing −previous cannot lose the onward path because next has already been saved. Cells tagged negative belong to completed reversed edges; untouched positive cells retain original successors.\n\nClosing the cycle writes the final predecessor into the start cell. Only after all cycles are finished does a final pass remove negative tags.',r'\mathrm{next}\gets a[\mathrm{current}];\quad a[\mathrm{current}]\gets-\mathrm{previous}'),
 ('Tags need spare representation','Negative tags are safe because the input consists only of positive labels 1 through n. If arbitrary signed payloads were allowed, sign would no longer distinguish processed cells. This is an extra representation precondition, not a magic property of all arrays.\n\nThere are O(n) reads and writes and O(1) working scalars beyond the input. The displayed history uses extra storage for teaching replay, but that history is not workspace used by the inversion algorithm.',r'a[j]<0\implies j\text{ has been assigned a tagged inverse edge}'),
 ('Prove and test different things','The cycle invariant proves why every original edge is reversed without loss. Exhaustive tests through n=7 compare the output to the separate-array inverse, including fixed points and multiple cycles. Those tests detect implementation mistakes; they do not replace the invariant for arbitrary n.\n\nA three-cycle 1→2→3→1 must become 1→3→2→1. Simply applying a[a[k]]=k from left to right can destroy this cycle’s information.',r'\forall i,\quad\mathrm{inverse}[\mathrm{original}[i]]=i')),
75:(
 ('Choose one cycle notation','Cycle notation can rotate each cycle and reorder different cycles without changing the permutation. To make it canonical, put the smallest element first in each cycle and order cycles by decreasing first element. Keep singleton cycles.\n\nNow erase parentheses. The first item of every cycle is smaller than all earlier items, while no later item inside that cycle can be a new minimum. Thus cycle starts are precisely left-to-right minimum records.',r'i\text{ is a record}\iff i=1\text{ or }a_i<\min(a_1,\ldots,a_{i-1})'),
 ('The missing parentheses are recoverable','Scan the linear sequence and insert a left parenthesis before each new minimum. Close the preceding cycle there. This exactly reconstructs the canonical cycles, proving the transformation is reversible. The output linear sequence is generally a different one-line permutation from the original mapping.\n\nThe model shows original cycles, their canonical order, the erased sequence and the recovered breaks. It does not confuse a notation change with equality of the two one-line arrays.',r'\#\text{cycles of }p=\#\text{record minima of its transformed sequence}'),
 ('A bijection transfers a distribution','For a uniformly random permutation, the transformed linear sequence is also uniform because the transformation is one-to-one and onto. At position j, each of the first j elements is equally likely to be their minimum; hence that position is a record with probability 1/j. Linearity of expectation then gives expected cycle count Hₙ.\n\nIndependence is unnecessary for this expectation calculation. The displayed finite example illustrates record positions, while symmetry and bijectivity establish the general statement.',r'\mathbb E[C_n]=\sum_{j=1}^{n}\frac1j=H_n'),
 ('Conventions change the kind of record','Using largest-first cycles ordered increasingly gives an equally valid maximum-record variant, but switching halfway through breaks reconstruction. This lesson consistently uses smallest-first and decreasing cycle starts.\n\nFor the sequence 4,5,2,3,1, record minima occur at 4,2,1, so the reconstructed cycles are (4 5)(2 3)(1). The maximum-record rule would cut at different positions and would be wrong for this declared convention.',r'(4\ 5)(2\ 3)(1)\longleftrightarrow 4,5,2,3,1')),
76:(
 ('Fixed-point events overlap','Let Eᵢ be the event that a permutation fixes i. Subtracting all |Eᵢ| from n! removes a permutation with two fixed points twice. Inclusion–exclusion repairs such overlap by adding pair intersections, subtracting triple intersections, and continuing.\n\nFixing a chosen set of k labels leaves (n−k)! arrangements of the remaining labels. There are binomial(n,k) such sets. The model computes each signed correction for n=5 and the resulting derangement count 44.',r'D_n=\sum_{k=0}^{n}(-1)^k\binom nk(n-k)!=n!\sum_{k=0}^{n}\frac{(-1)^k}{k!}'),
 ('Check the coefficient of one permutation','A permutation with r fixed points appears in binomial(r,k) of the k-fold intersections. Its net coefficient is the alternating sum of these binomial coefficients. That sum is 1 when r=0 and 0 otherwise, so exactly the derangements survive.\n\nThis coefficient argument proves the formula without assuming that fixed-point events are independent. They are not independent in a finite permutation.',r'\sum_{k=0}^{r}(-1)^k\binom rk=(1-1)^r'),
 ('Zero objects is a meaningful case','The empty permutation has no fixed points and is a derangement of an empty set, so D₀=1. One object cannot move elsewhere, so D₁=0. These cases make recurrences and counting identities work without an artificial exception.\n\nTo count permutations with exactly r fixed points, choose their labels and derange the rest. Choosing fixed points alone is insufficient because the remaining permutation must have no additional fixed points.',r'\#\{p:\text{exactly }r\text{ fixed points}\}=\binom nrD_{n-r}'),
 ('An alternating correction is not a probability yet','Each displayed term is an integer count. Divide the final result by n! to obtain a probability. Intermediate alternating totals may temporarily overcount or undercount; they are not counts of a progressively filtered physical list.\n\nFor a new three-object case the corrections are 6−6+3−1=2. Exhaustive enumeration checks this and all sizes through seven; the coefficient proof covers every finite n.',r'\Pr(\text{no fixed point})=D_n/n!')),
77:(
 ('A call needs a continuation','A call is more than a branch to useful code: the callee must know where to continue the caller. MIX’s ordinary jump saves the following address in J. Our original TWICE routine receives a number in A and returns twice that number in A. Its first instruction stores J into the address field of its return instruction.\n\nThe main program enters 11, calls TWICE, stores 22 and halts. The actual memory word containing the return jump is fetched after it has been changed; the model does not bypass self-modification with a hidden host-language return.',r'\mathrm{call\ at}\ P:\quad J\gets P+1,\quad PC\gets\mathrm{TWICE}'),
 ('Patch only the return address','STJ normally uses field 0:2. It writes J into the sign and two-byte address, preserving the return instruction’s index, modifier and opcode. The routine uses JSJ to return without overwriting J.\n\nThe trace displays the old and new return words. The proof obligation is spatial: only address positions change. If a full-word STJ were used accidentally, the jump opcode would be replaced by zero and the return would fail.',r'\mathrm{RETURN}[0:2]\gets J,\quad\mathrm{RETURN}[3:5]\text{ unchanged}'),
 ('State the entry and exit contract','Entry requires A=x, a valid caller continuation in J, writable TEMP and RETURN cells, and |2x|<b⁵. Exit returns A=2x and control to the caller’s continuation. TEMP and the return address field are clobbered; X and index registers are preserved.\n\nThe same patch cell cannot safely hold two simultaneous activations. Recursion, interrupts or a nested call using the same routine can overwrite an older continuation. A stack of activation records or another per-call storage convention is then required.',r'\{A=x,\ |2x|<b^5\}\ \mathrm{TWICE}\ \{A=2x\}'),
 ('Read the caller after the return','Successful arithmetic alone is not enough. The exit PC must equal the caller’s continuation, and promised preserved registers must still agree with entry. The tests check memory result 22, the preserved return opcode, and J=202.\n\nFor a transfer call with A=−6 the routine should return −12. If the caller needs its original A afterward, it must save it or request a different calling contract.',r'\text{correct call}=\text{correct result}+\text{correct continuation}+\text{contracted preservation}')),
78:(
 ('Reuse trades space for linkage','Suppose a body occupies B words and is used k times. Inlining copies B words at each site. A shared routine stores one body, an L-word linkage section, and C call-site words per use. Sharing saves space only when kB exceeds B+L+kC.\n\nThe computed example varies k while holding B=8, L=2, C=1. The threshold is an algebraic consequence of this declared design, not a universal property of all calling conventions.',r'S_{\rm inline}=kB,\quad S_{\rm shared}=B+L+kC'),
 ('Time includes every entry and exit','If one execution of the useful body costs T and call/return overhead costs H, k inline uses cost kT, while shared execution costs k(T+H). Code size can improve while time worsens. Different hardware or compiler choices can change H.\n\nIn MIX, a simple jump, STJ and return already impose costs distinct from the routine’s arithmetic. Compare whole calling sequences, not only the instructions printed inside the body.',r'T_{\rm shared}-T_{\rm inline}=kH'),
 ('Preservation is a resource decision','Saving registers adds time and temporary storage but can simplify callers. A contract should say which registers carry arguments and results, which are scratch, what memory is modified and which flags survive. An overflow flag can be a meaningful output even when A contains a wrapped value.\n\nThe TWICE example promises X and index preservation but modifies A, TEMP, RETURN and J through the call. The computed preservation check compares entry and exit projections onto the promised state.',r'\pi_{\rm preserved}(S_{\rm exit})=\pi_{\rm preserved}(S_{\rm entry})'),
 ('Do not hide the activation model','A routine with one static return slot is economical for nonoverlapping calls but is not reentrant. A recursive routine needs distinct saved continuations and local storage for each live call. The memory cost is proportional to the number of simultaneous activations, not merely the number of source call sites.\n\nThe transfer check changes the number of call sites and asks when sharing first saves words. It also asks what must change before the same routine can call itself.',r'\text{shared wins when }k(B-C)>B+L')),
79:(
 ('A paused computation keeps its place','A coroutine has a continuation and retained local state. Resuming it continues after its last yield rather than restarting at its entry. Our producer yields successive squares; its retained local counter names the next square to produce. The consumer has its own WAIT and USE locations.\n\nThe executable state machine records both continuation labels at every handoff. This is a semantic coroutine model, not a claim that a Python generator or a hardware thread executed invisibly.',r'\mathrm{coroutine\ state}=(\mathrm{continuation},\mathrm{locals})'),
 ('Save before transferring control','When the producer yields i², it saves ADVANCE as its next location. The consumer receives that one value and resumes USE. When control returns to the producer, it first increments the retained i; restarting at MAKE without advancing would repeat the same output.\n\nMIX can encode continuations in writable jump-address fields. The source’s linkage idea motivates the model, but our square-stream state machine is original and separate from the integer instruction interpreter.',r'(P=\mathrm{MAKE},i)\xrightarrow{\mathrm{yield}\ i^2}(P=\mathrm{ADVANCE},i)'),
 ('Completion is another state','A coroutine may suspend repeatedly and then finish. The explicit END state distinguishes exhaustion from a legitimate yielded value such as zero. Resuming after END must not manufacture another item.\n\nFor n=0 the producer immediately reports completion. The consumer’s total stays zero, and no USE step occurs. Empty input is therefore handled by the same protocol rather than by an invented final payload.',r'i>n\implies P=\mathrm{END},\quad C=\mathrm{END}'),
 ('A coroutine is not automatically parallel','Only one component executes at each step in this model. Coroutines organize control cooperatively; simultaneous processors, data races and preemptive scheduling are different concerns. What survives suspension is precisely what the continuation contract retains.\n\nFor a new n=2 example, yields are 1 and 4. After the first yield, producer i is still 1 and its saved location is ADVANCE. Predicting those values tests continuation state, not just the final sum 5.',r'\text{resume}\ne\text{restart}')),
80:(
 ('Connect two stateful components','The producer emits squares 1² through n². The consumer adds each delivered value to a running total. A one-item handoff slot is either empty or contains a value awaiting consumption. Only the component owning that slot may change it.\n\nThe trace includes yield, consume, resume and end events. Keeping the producer’s counter separate from the consumer’s total lets each component retain exactly the state needed for its own job.',r'T_k=\sum_{i=1}^{k}i^2'),
 ('Exactly once is a protocol invariant','A successful yield fills the slot and moves the consumer to USE. USE adds the value once, empties the slot and moves back to WAIT. The producer cannot yield a second value before the first is consumed.\n\nConsequently the number of consumed items never exceeds produced items, and their difference is zero or one. This makes duplicate consumption and overwritten values visible before a wrong final total appears.',r'0\le N_{\rm produced}-N_{\rm consumed}\le1'),
 ('Exhaustion follows the final consumption','After consuming n², the consumer resumes the producer one more time. ADVANCE moves its counter beyond n, and MAKE then reports END. No extra square is yielded. This final control exchange is real work even though it adds no payload.\n\nThe result is checked against the independent closed form n(n+1)(2n+1)/6. That equality verifies the computed total, while the handoff invariant verifies its exactly-once construction.',r'\sum_{i=1}^{n}i^2=\frac{n(n+1)(2n+1)}6'),
 ('Change the stream without changing the contract','A producer could emit filtered values or decode variable-length records while the consumer kept the same one-item protocol. Both sides must still agree on whether END is separate from data, which side owns a pending item and what cancellation means.\n\nThis lesson models normal finite completion only; it does not implement asynchronous exceptions or cancellation. For n=3, the final total is 14 and exactly three USE events occur.',r'\#\mathrm{USE}=n\quad\text{on normal completion}')),
81:(
 ('The object program is data to the host','An interpreter keeps an object-language PC and dispatches object opcodes. The host program’s own control flow implements those operations. Our tiny stack language has PUSH, DUP, ADD and HALT. PUSH appends an integer; ADD removes two integers and pushes their sum.\n\nThe original object program pushes 4, duplicates it, adds the pair, pushes 3, adds again and halts. The result 11 arises from actual dispatch, with the object stack recorded after each instruction.',r'(pc,\sigma)\xrightarrow{\mathrm{PUSH}\ v}(pc+1,\sigma\mathbin{\|}[v])'),
 ('One object step can require many host steps','Fetching an opcode, validating its operands, checking stack depth and updating the stack are host actions. They collectively implement one object instruction. Counting host statements as object instructions mixes two levels of explanation.\n\nEach computed frame identifies fetch, dispatch and update as distinct host responsibilities and records the resulting object state after one object step. It does not claim to show a separate executed host instruction for each diagram box. The object PC advances once, and the displayed stack contains no accidental host temporaries.',r'(pc,\sigma\mathbin{\|}[a,b])\xrightarrow{\mathrm{ADD}}(pc+1,\sigma\mathbin{\|}[a+b])'),
 ('A language needs failure rules','ADD requires at least two stack entries, DUP at least one, and every fetched opcode must be supported. An invalid program produces a diagnostic. The model does not silently treat unknown instructions as no-ops.\n\nHALT is an explicit instruction. Reaching beyond the code array is not implicitly successful termination; that would hide missing branches or forgotten halts.',r'\mathrm{ADD\ precondition}:\quad |\sigma|\ge2'),
 ('Compact representation is a design choice','An object language can package repeated complex host behavior into short codes. Porting then requires another implementation of the object semantics, not a rewrite of every object program. The advantage depends on instruction design and dispatch overhead; interpretation is not inherently slower or faster in every setting.\n\nFor transfer, PUSH 6; DUP; ADD leaves 12. Removing DUP causes stack underflow, demonstrating that the intermediate state matters as much as the intended arithmetic.',r'\text{object semantics is the contract between code and interpreter}')),
82:(
 ('A faithful subset starts with explicit state','The integer MIX model stores 4000 addressable words, A and X, six narrow index registers, J, PC, overflow, comparison and simulated time. Words retain sign separately from magnitude. One step fetches the memory word currently at PC, including any self-modification by earlier stores.\n\nThe title’s goal is fidelity to the supported subset, not a claim of a complete MIX installation. The executed examples and the declared diagnostics define what this implementation can demonstrate.',r'S=(M,A,X,I_1,\ldots,I_6,J,PC,O,C,t)'),
 ('The implemented instruction families','The interpreter implements NOP and HLT; integer ADD, SUB, MUL and DIV; all positive/negative loads; stores including STJ and STZ; address transfers; comparisons; comparison, overflow and register jumps; six shifts; sequential MOVE; NUM and CHAR. Each family decodes its own F meaning.\n\nFloating-point operations and I/O opcodes 34–38 are excluded from this interpreter. I/O readiness and buffering are implemented in a separate parameterized scheduling model. The assembler is also a stated MIXAL subset, not a full language implementation.',r'\mathrm{step}:S\times\mathrm{supported\ instruction}\to S\cup\{\mathrm{diagnostic},\mathrm{undefined}\}'),
 ('Undefined behavior is not a guessed value','An invalid address, malformed field, unsupported instruction or index overflow produces a transactional diagnostic. Division by zero or an oversized quotient instead sets overflow and reaches an explicit undefined-result stop, matching the fact that MIX does not specify meaningful A and X bits afterward.\n\nThe preserved predivision register bits are available only as diagnostic context; they must not be read as the division result. Distinguishing these cases is more honest than inventing a wrapped quotient.',r'V=0\ \lor\ |A|\ge|V|\implies O=\mathrm{on},\ \text{result unspecified}'),
 ('Simulated cost belongs to the guest','The CLOCK field advances by documented MIX units for executed instructions. Browser animation duration, Python runtime and host loop iterations are not included. Device waiting has its own explicit model and cannot be inferred from these CPU-only program timings.\n\nThe trace of the original four-element sum reaches TOTAL=18 in 21u at every tested byte base. That portability check verifies these programs; it does not prove every arbitrary word-level program is base-independent.',r't_{k+1}=t_k+\mathrm{cost}(\mathrm{instruction}_k)')),
83:(
 ('Test representations, not only values','An assertion that A equals zero misses whether its sign is correct. A field test that checks selected bytes but ignores untouched bytes misses corruption. The laboratory therefore compares signed digit arrays, flags, J, PC and changed memory as well as numerical results.\n\nIts independent field oracle uses positional sums and position-wise expected stores, rather than calling the implementation’s field helper again. This gives a genuinely different path to the expected answer.',r'\mathrm{expected\ state}=\mathrm{oracle}(\mathrm{initial\ state},\mathrm{instruction})'),
 ('Boundary cases make hidden rules visible','The tests include all 21 valid fields, both signs, multiple byte bases, ±0, conversion round trips, taken and untaken overflow jumps, division failure, invalid addressing and sequential overlapping MOVE. These cases target places where a superficially plausible emulator can disagree with the specification.\n\nFor example, copying an overlapping MOVE through a temporary slice produces a different result from MIX’s one-word-at-a-time movement. The source word can propagate into several destinations.',r'\mathrm{MOVE\ overlap}:\quad M[a+1]\gets M[a],\ M[a+2]\gets M[a+1]'),
 ('An invalid instruction must not half-run','Our diagnostic contract says that rejected instructions leave the whole state unchanged. Tests snapshot PC, registers, flags and memory before a bad instruction and compare afterward. This catches a common bug: incrementing PC before validation and forgetting to roll it back.\n\nThis extra diagnostic discipline is a model design choice. It is distinguished from legal MIX semantics and from hardware behavior on undefined input.',r'\mathrm{reject}(I)\implies\mathrm{snapshot}_{\rm after}=\mathrm{snapshot}_{\rm before}'),
 ('Finite evidence supports a bounded claim','Exhaustive field combinations cover that finite subdomain completely. Exhaustive permutations through seven cover those inputs, not every possible array length. Generated arithmetic tests sample a much larger domain. Each test’s scope should be visible rather than hidden behind one green badge.\n\nThe source specification, invariants and independent oracles play different roles. A disagreement calls for inspecting the first different field and revisiting the stated rule, not changing the expected answer until the implementation passes.',r'\text{passed tests}\not\implies\text{all possible programs are correct}')),
84:(
 ('Observe snapshots without executing twice','A trace should record what the program did, not repeat its instructions in order to discover their effects. Our observer copies state after each committed step. The unobserved baseline runs the same program without retaining those copies; their guest results must agree.\n\nThe demonstration pairs guest snapshots and a separate event log. Logging a memory store is safe only because the observer copies the resulting state; reissuing the store or output operation would change the program.',r'\pi_{\rm guest}(S_{\rm traced})=\pi_{\rm guest}(S_{\rm baseline})'),
 ('Keep observer storage separate','A guest program may write any permitted guest memory location. Putting trace records into that same address space without a reservation can overwrite code or data. Our logs live in host-side storage and are absent from guest memory.\n\nAn in-machine tracing routine would need a stronger calling contract: save and restore registers and flags, use disjoint memory, and intercept control transfers correctly. That machinery is discussed conceptually here, not falsely claimed as an implemented MIX trace routine.',r'M_{\rm guest}\cap M_{\rm observer}=\varnothing\quad\text{in the host-side design}'),
 ('Decide what equivalence observes','The CPU-only examples compare registers, flags, guest memory, halted status and guest CLOCK. Host elapsed time and log size differ. If guest behavior depended on real-time devices, instrumentation could affect when a readiness test succeeds; semantic equivalence would then need a carefully controlled device-time model.\n\nThus our equality claim is scoped to deterministic CPU programs with the same initial state and documented guest timing.',r'\pi=(A,X,I,J,PC,O,C,M,\mathrm{halted},t_{\rm guest})'),
 ('A trace explains a branch after it happens','The trace records the fetched word, effective address, cost and whether the branch was taken. It does not infer a jump merely from a changed PC, since a jump can target the sequential next address. It also distinguishes a taken JSJ from a jump that updates J.\n\nFor transfer, adding an observer log entry may change host runtime and storage use. It should not change the computed total or execute an output twice.',r'\mathrm{event}=(PC_{\rm before},I,M,\mathrm{taken},S_{\rm after})')),
85:(
 ('Two buffers let different jobs overlap','With one buffer, input fills it, the CPU processes it, and only then may input reuse it. With two buffers, input can fill one while the CPU processes the other. The ownership condition is essential: they cannot safely work on the same data simultaneously.\n\nThe event model uses four input items, input time 3 and processing time 5. It shows startup, simultaneous work, waits and final drain, rather than drawing two idealized bars that omit boundary costs.',r'T_1=n(I+C),\qquad T_2=I+C+(n-1)\max(I,C)\quad(n\ge1)'),
 ('A completion event changes permission','Issuing input changes EMPTY to FILLING. Only its completion changes FILLING to READY. The CPU acquires the oldest READY buffer and changes it to PROCESSING. Its completion returns the buffer to EMPTY.\n\nAt equal timestamps, completed input and computation are recognized before new work is issued. This explicit event ordering makes the zero-wait handoff deterministic without allowing premature reads.',r'\mathrm{CPU\ may\ read}\iff\mathrm{state}=\mathrm{READY\ or\ PROCESSING\ owned\ by\ CPU}'),
 ('Startup and drain cannot be hidden','For four items with I=3 and C=5, serial time is 32 while two-buffer time is 23. The first input still costs 3 before computation begins, and the last computation still needs its full service time after its input arrives.\n\nThe formula assumes one serial input device, one serial processor, constant positive service times, instantaneous handoffs and enough buffers. It is not a prediction for arbitrary disks, operating systems or variable workloads.',r'3+5+3\cdot5=23<32=4(3+5)'),
 ('Know when to stop reading','The model receives a known item count and never issues a read beyond it. Other protocols require an explicit end marker or a short-block convention; speculative read-ahead must respect whichever protocol applies. An empty stream takes no service time.\n\nFor a new two-item case with I=4 and C=2, two-buffer time is 4+2+4=10, not 8. The limiting input rate does not eliminate the final processing drain.',r'T_2(0)=0')),
86:(
 ('Buffers are owned resources','A pool of k buffers is partitioned among EMPTY, FILLING, READY and PROCESSING states. Each buffer has exactly one state and at most one active owner. A READY queue records arrival order. The CPU removes its oldest entry; input chooses only an EMPTY buffer.\n\nThe animation gives each physical buffer a stable identity as its state changes, so reuse cannot be confused with creating a new buffer.',r'E+F+R+P=k'),
 ('Backpressure prevents overwrite','If the producer finishes faster than the consumer, READY buffers accumulate. Eventually no EMPTY buffer remains, and input must wait. This is backpressure, not a bug. If input is slower, the CPU waits because there is no READY item.\n\nThe computed three-buffer example shows both queue membership and explicit busy or waiting status. A state change is justified by completion or acquisition, never by an arbitrary animation timer.',r'\mathrm{issue\ input}\implies E>0,\qquad\mathrm{start\ CPU}\implies R>0'),
 ('More storage does not remove a bottleneck','Extra buffers can absorb short-term variation but cannot make one serial processor consume faster than its service time, or one device produce faster than its service time. For constant service times, two buffers already achieve the steady-state bottleneck rate in this model.\n\nThe demonstration compares one, two and three buffers using the same workload. It reports total completion times including startup and drain, not only an asymptotic rate.',r'\mathrm{throughput}\le\min(1/I,1/C)=1/\max(I,C)'),
 ('FIFO is a separate invariant','Exclusive ownership prevents races but does not itself guarantee data order. The READY queue carries that second responsibility. Tests verify that the output identifiers are exactly 0,1,…,n−1, with no missing, repeated or reordered item.\n\nA multi-device shared pool needs further policies to avoid one device monopolizing every empty buffer. This model has one producer and one consumer; it does not claim a general deadlock-free multi-device allocator.',r'\mathrm{output}=[0,1,\ldots,n-1]')),
87:(
 ('Logical records need not fit physical blocks','Logical records can have different lengths, while a device may require fixed-capacity physical blocks. Packing follows the concatenated payload stream, filling each block and carrying a record’s remaining characters into the next. Record boundaries need separate information if they must later be reconstructed.\n\nOur original records AB, CDEFG and H have lengths 2,5,1. With capacity five, the physical payloads become ABCDE and FGH. The model retains record lengths [2,5,1] as metadata.',r'\mathrm{payload}=r_1\mathbin{\|}\cdots\mathbin{\|}r_m'),
 ('The cursor identifies the next free position','Appending a character increases the fill count. When it reaches capacity, the block is emitted and the cursor returns to zero. A record boundary alone does not force a flush under this policy.\n\nThe invariant is that emitted valid payloads followed by the pending buffer equal exactly the already consumed input prefix. It proves neither duplication nor omission occurs when a record crosses a block boundary.',r'\mathrm{emitted}\mathbin{\|}\mathrm{pending}=\mathrm{input}[0:c]'),
 ('A partial final block needs its valid length','At end of input, a nonempty pending block is flushed with its valid payload length. Any physical padding is outside that length and is not logical data. An exactly full final block has already been emitted and must not produce an extra empty block.\n\nAn empty stream produces no blocks. Empty records still require their zero lengths in the record metadata if record identity matters; they cannot be recovered by examining payload alone.',r'\#\mathrm{blocks}=\left\lceil N/B\right\rceil\quad(N\ge0,B>0)'),
 ('Reconstruction checks the whole contract','Concatenate valid block payloads, then split at the cumulative record lengths. This recovers both payload and original records. A sentinel-based alternative would require escaping the sentinel when it appears in data; this lesson deliberately uses lengths instead.\n\nFor transfer, records XYZ and PQ packed into capacity three produce XYZ and PQ, with final valid length two. Changing capacity changes physical grouping, not the logical stream.',r'\sum_i|r_i|=N=\sum_j\mathrm{validLength}(B_j)')),
}

def mini_program(ops,initial=None,b=64):
 m=Machine(b)
 for k,(op,a,f) in enumerate(ops):
  c,default=OPS[op]; m.mem[k]=instruction(a,c,default if f is None else f,b=b)
 if initial:
  for k,v in initial.items():
   if isinstance(k,int): m.mem[k]=v
   elif k=='A': m.reg[0]=v
   elif k=='X': m.reg[7]=v
   elif k=='I1': m.reg[1]=v
 for _ in ops:
  if m.halted: break
  m.step()
 return m

def computed_cards(sequence,title,labels,formula=''):
 frames=[]
 for i,(vals,cap) in enumerate(sequence):
  ns=[]
  for j,(name,val) in enumerate(zip(labels,vals)):
   x=60+j*min(220,600/max(1,len(labels))); ns += [rect('card-'+str(j),x,115,190,110,'active' if j==i%len(labels) else 'input'),text('name-'+str(j),x+95,150,name),text('val-'+str(j),x+95,195,val,'result',result=True)]
  if len(labels)>1:
   for j in range(len(labels)-1): ns.append(line('causal-'+str(j),245+j*220,265,285+j*220,265))
  frames.append(frame(i,cap,diagram(title,'The quantities are computed from the stated input, not painted into a fixed answer.',ns),formula,{'values':vals}))
 return frames


def coroutine_diagram(s):
 ns=[]; producer=['MAKE','ADVANCE','END']; consumer=['WAIT','USE','END']
 for row,(name,labels,current) in enumerate([('producer',producer,s['producerPC']),('consumer',consumer,s['consumerPC'])]):
  y=70+row*170
  for i,label in enumerate(labels):
   x=45+i*225; role='active' if label==current else 'muted'; ns.extend([rect(f'{name}-{label}',x,y,190,65,role),text(f'{name}-{label}-text',x+95,y+27,name,role),text(f'{name}-{label}-pc',x+95,y+51,label,role)])
 if not s['done']:
  px=140+225*producer.index(s['producerPC']); cx=140+225*consumer.index(s['consumerPC'])
  ns.append(line('handoff',px if s['held'] is not None else cx,140 if s['held'] is not None else 235,cx if s['held'] is not None else px,235 if s['held'] is not None else 140))
  ns.append(text('handoff-label',360,192,'yield one value' if s['held'] is not None else 'resume saved location','active'))
 ns.extend([text('retained',360,360,f"retained i={s['next']}; pending={s['held']}"),text('total',360,398,f"consumer total={s['total']}",'result',result=True)])
 return diagram('Two independently saved continuations','Highlighted locations are saved continuations. The handoff transfers control and at most one payload.',ns,'A resumed coroutine retains its local variables and continues at its saved location.')

def focused(frames,part):
 if len(frames)<=4: return copy.deepcopy(frames)
 # A different contiguous operation window for each passage, with endpoint context.
 width=min(6,len(frames)); start=round(part*(len(frames)-width)/3); return copy.deepcopy(frames[start:start+width])

def instruction_bridge(fs,model,order,part):
 trace=model.get('executedTrace',[])
 addresses=sorted(set(t['before']['pc'] for t in trace))
 for st in fs:
  if order==77 and part==1:
   t=trace[2]; target=t['effectiveAddress']; before=t['before']['memory'][str(target)]; after=t['after']['memory'][str(target)]
   old=before['sign']*(before['bytes'][0]*64+before['bytes'][1]); new=after['sign']*(after['bytes'][0]*64+after['bytes'][1]); done=st['data']==after
   st['diagram']['nodes'] += [text('instruction-identity',360,265,f"STJ {target}(0:2): source J = {t['before']['J']}",'active'),text('instruction-equation',360,305,f'Address {old} → {new}; opcode C={after["bytes"][4]} is preserved' if done else f'Before store: return address field = {old}; opcode C={before["bytes"][4]}', 'result' if done else 'input',result=done),text('store-contract',360,345,'Only sign and address bytes are selected; I, F, C stay intact.','muted',fontSize=15)]
   continue
  if order==68 and part==3:
   if st['data'].get('values') is not None: st['diagram']['nodes'] += [text('rejected-instruction',360,295,'LDA −1: memory address −1 is outside 0 … 3999.','error',fontSize=16),text('rollback-equation',360,330,f"Reject → PC remains {st['data']['values'][0]}; no register is written.",'result',result=True,fontSize=16)]
   continue
  if 'fetchedAddress' not in st['data']: continue
  t=next(t for t in trace if t['before']['pc']==st['data']['fetchedAddress'] and t['after']['clock']==st['data']['clock'])
  before,after=t['before'],t['after']; c,f,M=t['opcode'],t['field'],t['effectiveAddress']; w=t['instruction']; a1,a2,ix,_,_=w['bytes']; aa=w['sign']*(a1*64+a2)
  mnemonic=next((name for name,(oc,mod) in OPS.items() if oc==c and mod==f),'opcode '+str(c))
  indexed=before['I'][ix-1] if ix else 0
  raw=before['memory'].get(str(M),Word().data()); operand=load(Word(raw['sign'],raw['bytes']),f).value if c in (1,2,3,4) or 8<=c<=23 else None
  source=f'M = {aa} + '+(f'I{ix}({indexed})' if ix else '0')+f' = {M}'
  lhs=''; equation=''
  if c in (1,2):
   lhs=f"A before = {before['A']['value']}; memory[{M}] selected field = {operand}"
   equation=f"A ← {before['A']['value']} {'+' if c==1 else '−'} ({operand}) = {after['A']['value']}"
  elif c==3:
   product=abs(before['A']['value'])*abs(operand); lhs=f"A before = {before['A']['value']}; memory[{M}] field = {operand}"
   equation=f"|A| × |V| = {product} = {abs(after['A']['value'])} × 64⁵ + {abs(after['X']['value'])} → A:X"
  elif c==4:
   N=abs(before['A']['value'])*64**5+abs(before['X']['value']);lhs=f"A:X magnitude = {N}; memory[{M}] divisor = {operand}"
   equation='V = 0: quotient and remainder unspecified; overflow ON' if operand==0 else (f"|A| ≥ |V|: quotient overflow; result unspecified" if abs(before['A']['value'])>=abs(operand) else f"{N} = {abs(after['A']['value'])} × {abs(operand)} + {abs(after['X']['value'])}; A={after['A']['value']}, X={after['X']['value']}")
  elif 48<=c<=55:
   k=c-48; name='A' if k==0 else 'X' if k==7 else 'I'+str(k); old=before[name]['value'] if k in (0,7) else before['I'][k-1]; new=after[name]['value'] if k in (0,7) else after['I'][k-1]
   lhs=f'{name} before = {old}; numeric operand M = {M} (no memory read)'
   equation=f'{name} ← '+(f'{old} + ({M})' if f==0 else f'{old} − ({M})' if f==1 else str(M) if f==2 else f'−({M})')+f' = {new}'
  elif 24<=c<=33:
   k=c-24; name='A' if k==0 else 'X' if k==7 else 'J' if c==32 else 'zero' if c==33 else 'I'+str(k)
   value=before['A']['value'] if k==0 else before['X']['value'] if k==7 else before['J'] if c==32 else 0 if c==33 else before['I'][k-1]
   l,r=field(f); new=after['memory'][str(M)]
   lhs=f"{name} before = {value}; memory[{M}] before = {raw['value']}"
   equation=f"Store field {l}:{r} from {name} → memory[{M}] = {new['value']}"
   if c==32:
    oldaddress=raw['sign']*(64*raw['bytes'][0]+raw['bytes'][1]);newaddress=new['sign']*(64*new['bytes'][0]+new['bytes'][1])
    lhs=f'J before = {value}; memory[{M}] return address before = {oldaddress}'
    equation=f'Patch address {oldaddress} → {newaddress}; I, F, C stay unchanged'
  elif c==39 or 40<=c<=47:
   if c==39: condition=f"overflow {'ON' if before['overflow'] else 'off'}" if f in (2,3) else f"comparison {before['comparison']}" if f>=4 else 'unconditional'
   else:
    k=c-40; name='A' if k==0 else 'X' if k==7 else 'I'+str(k); v=before[name]['value'] if k in (0,7) else before['I'][k-1]; condition=f'{name}={v} tested '+['<0','=0','>0','≥0','≠0','≤0'][f]
   lhs=f'{mnemonic}: {condition} → '+('taken' if t['jumpTaken'] else 'not taken')
   equation=f"PC ← {'M' if t['jumpTaken'] else str(before['pc'])+'+1'} = {after['pc']}; "+(f"J ← {before['pc']}+1 = {after['J']}" if t['jumpTaken'] and not(c==39 and f==1) else f"J stays {after['J']}")
   if c==39 and f in (2,3): equation+='; overflow clears'
  elif c==5 and f==2: lhs=f"HLT was fetched at PC={before['pc']}"; equation=f"halted = true; PC = {before['pc']}+1 = {after['pc']}"
  elif 8<=c<=23:
   k=(c-8)%8; name='A' if k==0 else 'X' if k==7 else 'I'+str(k); value=after[name]['value'] if k in (0,7) else after['I'][k-1]; lhs=f'memory[{M}] selected value = {operand}';equation=f'{name} ← '+('negate ' if c>=16 else '')+f'{operand} = {value}'
  else: lhs=f"Fetched opcode {c}, modifier {f}";equation=f"PC {before['pc']} → {after['pc']}; committed once"
  ns=st['diagram']['nodes']; ns += [text('instruction-identity',360,25,f"Fetch @{before['pc']}: {mnemonic} {aa}"+(f',{ix}' if ix else '')+f' ; word '+('−' if w['sign']<0 else '+')+' '+','.join(map(str,w['bytes'])),'active',fontSize=15),text('instruction-address-equation',360,49,source,'active',fontSize=15),rect('instruction-calculation-panel',35,282,650,46,'muted'),text('instruction-operands',360,300,lhs,'input',fontSize=15),text('instruction-equation',360,321,equation,'result',fontSize=15,result=True)]
  spacing=min(78,610/max(1,len(addresses))); start=55
  for j,address in enumerate(addresses):ns.append(text(f'code-address-{address}',start+j*spacing+spacing/2,375,address,'muted',fontSize=13))
  j=addresses.index(before['pc']);ns += [rect('executed-code-cursor',start+j*spacing,357,spacing-4,24,'active',phase='transform')]
 return fs

def teaching_motion(order,part,fs,model):
 """Spatial witnesses of committed operations; never change the computed trace."""
 if order==65:
  maximum=max(1,max(st['data'].get('value',0).__abs__() for st in fs))
  for st in fs:
   w=st['data']; x=110+500*abs(w['value'])/maximum; y=260 if w['sign']>0 else 325
   base=model['base']; supers=['⁴','³','²','¹','⁰']; pieces=[]
   for j,byte in enumerate(w['bytes']):
    st['diagram']['nodes'].append(text(f'place-weight-{j}',312+75*j,160,f'{byte}×{base}{supers[j]}','muted',fontSize=13))
    if byte: pieces.append(str(byte) if j==4 else f'{byte}×{base}{supers[j]}')
   expansion=' + '.join(pieces) or '0'
   st['diagram']['nodes'] += [text('weight-label',105,160,'byte × weight','muted',fontSize=14),text('magnitude-expansion',360,405,f'Magnitude: {expansion} = {abs(w["value"])}','result',fontSize=17,result=True)]
   st['diagram']['nodes'] += [text('magnitude-axis',360,205,'Magnitude → (same scale in both sign lanes)','muted',fontSize=15),line('positive-lane',110,260,635,260,'muted'),line('negative-lane',110,325,635,325,'muted'),text('positive-label',55,265,'+ sign',fontSize=15),text('negative-label',55,330,'− sign',fontSize=15),rect('signed-word-token',x-24,y-19,48,38,'active',phase='transform'),text('signed-word-value',x,y+6,abs(w['value']),'active',fontSize=15,phase='transform'),text('magnitude-limit',610,365,maximum,'muted',fontSize=14)]
 elif order==66:
  f=model['field']; l,r=field(f); isload=model['operation']=='load'; n=max(0,r-max(l,1)+1)
  source=Word(-1,[1,2,3,4,5]); register=Word(1,[0,0,0,6,7]); got=load(source,f) if isload else store(source,register,f)
  for step,st in enumerate(fs):
   # Keep memory and register identities in their physical rows for STORE too.
   rows=[('memory',source.data() if isload or not step else got.data()),('register',register.data() if not step or not isload else got.data())]
   st['diagram']=word_diagram(rows,active=list(range(l,r+1)))
   selected={0:set(range(l,r+1)),1:set(range(6-n,6)) | ({0} if l==0 else set())}
   for obj in st['diagram']['nodes']:
    if obj['id'][0] in ('w','v','p') and re.fullmatch(r'[wvp][01]-[0-5]',obj['id']):
     row,pos=map(int,obj['id'][1:].split('-')); obj['role']='active' if pos in selected[row] else 'muted'
   for pos in range(max(l,1),r+1):
    srcpos=pos if isload else 6-n+pos-max(l,1); dstpos=6-n+pos-max(l,1) if isload else pos
    srcrow=0 if isload else 1; dstrow=1 if isload else 0; byte=(source if isload else register).bs[srcpos-1]
    x=205+75*(dstpos if step else srcpos); y=75+115*(dstrow if step else srcrow)
    st['diagram']['nodes'] += [rect(f'transfer-byte-{pos}',x+3,y+3,59,46,'active',phase='transform'),text(f'transfer-byte-value-{pos}',x+32,y+33,byte,'active',phase='transform')]
   if l==0:
    row=(1 if isload else 0) if step else (0 if isload else 1); y=75+115*row
    st['diagram']['nodes'] += [rect('transfer-sign',208,y+3,59,46,'active',phase='transform'),text('transfer-sign-value',237,y+33,'−' if isload else '+','active',phase='transform')]
   st['diagram']['nodes'] += [text('transfer-rule',360,315,'Selected bytes → right-aligned register' if isload else 'Rightmost register bytes → selected memory field','muted',fontSize=16),text('sign-rule',360,350,'Sign transfers only when L = 0; excluded memory bytes stay put.','muted',fontSize=15)]
 elif order==70:
  rows=[st['data'] for st in fs]
  for i,st in enumerate(fs):
   ns=st['diagram']['nodes']; ns += [text('operand-lane',360,222,'Source operands → emitted instruction addresses','muted',fontSize=15)]
   for j,row in enumerate(rows):
    done=j<=i; x=65+j*120; y=310 if done else 255
    a=row['word']['sign']*(64*row['word']['bytes'][0]+row['word']['bytes'][1])
    ns += [rect(f'resolution-token-{j}',x,y,110,48,'result' if done else 'input',phase='transform'),text(f'resolution-label-{j}',x+55,y+20,f"A={a}" if done else row['operand'],fontSize=14,phase='transform',result=done),text(f'resolution-location-{j}',x+55,y+38,f"@{row['address']}" if done else f"line {row['line']}",fontSize=13,phase='transform')]
   ns += [rect('emitted-address-cursor',65+i*120,365,110,6,'active',phase='transform')]
 elif order==76:
  if part==2:
   for i,st in enumerate(fs): st['diagram']['nodes'] += [rect('boundary-selection-box',60+220*i,235,190,6,'active',phase='transform'),text('boundary-selection',155+220*i,300,'↑ inspect this boundary','active',phase='transform')]
  else:
   terms=model['terms']
   for i,st in enumerate(fs):
    ns=st['diagram']['nodes']; ns += [text('correction-lane',300,260,'Unapplied signed terms','muted',fontSize=15),text('joined-total',585,370,'Joined running total','muted',fontSize=15)]
    size=(len(terms)-1) if part==1 else model['n']
    for label in range(1,size+1):
     fixed=label<=i; x=210+55*(label-1)
     ns += [rect(f'fixed-label-{label}',x,24,40,30,'active' if fixed else 'muted'),text(f'fixed-label-value-{label}',x+20,45,label,'active' if fixed else 'muted',fontSize=14)]
    choices=math.comb(size,i)
    countlabel=f'{choices} '+('subset' if choices==1 else 'subsets')+f' of {i} fixed labels'
    factorlabel=f' × {size-i}! = {abs(terms[i])}' if part!=1 else f' → signed coefficient {terms[i]:+}'
    ns += [text('fixed-subset-label',360,78,countlabel+factorlabel,'result',fontSize=16,result=True),text('representative-subset-label',360,100,(f'Permutation {list(range(1,size+1))+[size+2,size+1]}: counted once per selected fixed-point subset.' if part==1 else 'Highlighted labels: one representative intersection; count every such subset.'),'muted',fontSize=13)]
    for k,v in enumerate(terms):
     x=585 if k<=i else 70+90*k; y=330 if k<=i else 285; opacity=0 if k<i else 1
     ns += [rect(f'signed-term-{k}',x-35,y-18,70,36,'active' if k==i else 'input',opacity=opacity,phase='transform'),text(f'signed-term-value-{k}',x,y+6,f'{v:+}',opacity=opacity,phase='transform')]
 elif order==81:
  if part==2:
   for i,st in enumerate(fs): st['diagram']['nodes'] += [rect('precondition-selection-box',45+225*(1 if i==0 else 2),145,190,6,'active',phase='transform'),text('precondition-cursor',140+225*(1 if i==0 else 2),310,'↑ '+('check depth' if i==0 else 'rejected: no operands'),'active',fontSize=16,phase='transform')]
  else:
   code=model['code']; tokens=[]; stack=[]; snapshots=[]
   for event in model['trace']:
    pc=event['pc']; op=event['op']; born=None
    if op=='PUSH': born={'id':f'operand-{pc}','value':event['argument'],'origin':pc}
    elif op=='DUP': born={'id':f'copy-{pc}','value':tokens[stack[-1]]['value'],'origin':pc}
    elif op=='ADD':
     b=stack.pop(); a=stack.pop(); tokens[a]['consumed']=pc; tokens[b]['consumed']=pc; born={'id':f'sum-{pc}','value':tokens[a]['value']+tokens[b]['value'],'origin':pc}
    if born: born['born']=pc; tokens.append(born); stack.append(len(tokens)-1)
    snapshots.append(stack[:])
   for st in fs:
    pc=st['data']['pc']; active=snapshots[pc]; ns=st['diagram']['nodes']
    for j,(op,arg) in enumerate(code): ns += [text(f'object-code-{j}',65+100*j,215,f'{j}: {op}','muted',fontSize=13)]
    ns += [rect('object-fetch-cursor',30+100*pc,228,70,5,'active',phase='transform'),text('object-stack-label',540,355,'Committed object stack','muted',fontSize=15)]
    for j,t in enumerate(tokens):
     live=j in active; future=t['born']>pc; x=480+90*active.index(j) if live else (65+100*t['origin'] if future else 360); y=300 if live else (260 if future else 165)
     visible=live or (future and t['id'].startswith('operand-'))
     ns += [rect('stack-token-'+t['id'],x-32,y-20,64,40,'active',opacity=1 if visible else 0,phase='transform'),text('stack-value-'+t['id'],x,y+6,t['value'],opacity=1 if visible else 0,phase='transform',result=live and not t['id'].startswith('operand-'))]
 elif order==84:
  trace=model['trace']; columns=8
  for st in fs:
   count=next(i+1 for i,t in enumerate(trace) if t['after']==st['data']['traced']); ns=st['diagram']['nodes']
   ns += [text('log-label',360,195,'Retained snapshots (entry: A)','muted',fontSize=15)]
   for j,t in enumerate(trace):
    done=j<count; x=45+79*(j%columns) if done else 310; y=215+48*(j//columns) if done else 150
    ns += [rect(f'log-entry-{j}',x,y,73,36,'result',opacity=1 if done else 0,phase='transform'),text(f'log-value-{j}',x+36,y+23,f"{j+1}: {t['after']['A']['value']}",fontSize=13,opacity=1 if done else 0,phase='transform',result=True)]
   ns += [rect('log-append-cursor',45+79*((count-1)%columns),253+48*((count-1)//columns),73,4,'active',phase='transform')]
 return fs

def scenario(order,part,small=False):
 model={'kind':'mix-'+str(order),'implementation':'scripts/fullbook-batch-C.py','exact':True,'focus':part,'smallerExample':small}; q=''; answer=0; distractors=[]
 if order==65:
  n=3 if small else 130; b=64 if part!=3 else 100
  vals=[Word.number(n,b),Word.number(-n,b)] if part in (0,3) else ([Word.number(0,b),Word.number(0,b,-1)] if part==1 else [Word.number(15,b),Word.number(3999,b)])
  fs=[frame(i,f"{'Positive' if w.sign>0 else 'Negative'} sign, magnitude {w.mag}, byte base {b}.",word_diagram([('word',w.data())]),rf'|w|={w.mag}',w.data()) for i,w in enumerate(vals)]
  q=f'At byte base 64, what is the final byte of {n+1}?'; answer=(n+1)%64; model.update(base=b,input=n)
 elif order==66:
  w=Word(-1,[1,2,3,4,5]); src=Word(1,[0,0,0,6,7]); f=[20,10,0,19][part] if not small else [45,36,0,27][part]
  got=load(w,f) if part in (0,2) else store(w,src,f)
  fs=[frame(0,'Before selecting the field.',word_diagram([('memory',w.data()),('register',src.data())],active=list(range(field(f)[0],field(f)[1]+1))),data={'field':f}),frame(1,'The selected operation preserves every excluded position.',word_diagram([('source',w.data()),('result',got.data())],active=list(range(field(f)[0],field(f)[1]+1))),rf'F={f}',got.data())]
  q=f'What is the encoded F value for field {field(f)[0]}:{field(f)[1]}?'; answer=f; model.update(field=f,operation='load' if part in (0,2) else 'store')
 elif order==67:
  n=3 if small else 17
  if part==0: m=mini_program([('ADD',20,None),('SUB',21,None),('LDA',22,None),('INCA',1,None),('ADD',23,None)],{'A':Word.number(-n),20:Word.number(n),21:Word.number(2),22:Word.number(64**5-1),23:Word.number(1)}); q='What sign does A retain immediately after −n + n?'; answer='negative'
  elif part==1: m=mini_program([('MUL',20,None),('DIV',20,None)],{'A':Word.number(-n),20:Word.number(3)}); q=f'After multiplying −{n} by 3 and dividing the ten-byte product by 3, what is A?'; answer=-n
  elif part==2: m=mini_program([('SLAX',1,None),('SRC',1,None)],{'A':Word(-1,[0,1,2,3,4]),'X':Word(1,[5,6,7,8,9])}); q='Does either shift move the sign bits?'; answer='No'
  else: m=mini_program([('DIV',20,None)],{'A':Word.number(0),'X':Word.number(11 if small else 29),20:Word.number(-6)}); q=f'What is the positive remainder of {11 if small else 29} divided by −6?'; answer=(11 if small else 29)%6
  fs=machine_frames(m,mode='words'); model['executedTrace']=m.trace
 elif order==68:
  if part==0: m=mini_program([('ENTA',7 if small else 17,None),('INCA',2,None)]); q='Which instruction field is the opcode?'; answer='C'
  elif part==1:
   m=Machine(); m.mem[0]=instruction(2,39,0); m.mem[2]=instruction(3,39,1); m.step(); m.step(); q='After JMP from 0, followed by JSJ, what remains in J?'; answer=1
  elif part==2:
   m=Machine(); m.overflow=True; m.mem[0]=instruction(1,39,3); m.mem[1]=instruction(2,39,2); m.step(); m.step(); q='After testing JNOV with overflow on, is overflow still on?'; answer='No'
  else:
   m=mini_program([('ENTA',2,None)]); before=m.snapshot(); m.mem[1]=instruction(-1,8); before=m.snapshot()
   try: m.step()
   except SemanticError: pass
   fs=computed_cards([([before['pc'],m.pc],'Invalid memory load is rejected before committing a change.')],'Diagnostic rollback',['PC before','PC after']); q='Does a rejected negative-address load advance PC in this model?'; answer='No'; model['stateUnchanged']=m.snapshot()==before
  if part!=3: fs=machine_frames(m); model['executedTrace']=m.trace
 elif order==69:
  if part<2:
   tr=buffers(1 if small else 2,2,3,1 if part==0 else 2); fs=[frame(i,s['caption'],buffer_diagram(s),rf't={s["time"]}',s) for i,s in enumerate(tr)]; q='May the CPU read a buffer that is still FILLING?'; answer='No'; model['schedule']=tr
  elif part==2:
   n=7 if small else 2468; m=mini_program([('CHAR',0,None),('NUM',0,None)],{'A':Word.number(n)}); fs=machine_frames(m,mode='words'); q=f'What magnitude returns after CHAR then NUM starting with {n}?'; answer=n; model['executedTrace']=m.trace
  else:
   n=2 if small else 4; costs=[2,1,2]; fs=computed_cards([([k+1,sum(costs[:k+1])],f'Execute instruction {k+1}; add its documented cost.') for k in range(3)],'Documented guest instruction costs',['instructions','time u']); q='How many u do LDA, INCA and STA take together?'; answer=sum(costs)
 elif order in (70,71):
  if order==70:
   lines=[('','ORIG','500' if small else '100'),('START','ENTA','3'),('2H','DECA','1'),('','JAP','2B'),('','JMP','2F'),('2H','HLT','0'),('','END','START')]; mem,sy,start,listing=assemble(lines)
   selections=listing if part<2 else listing[2:]; fs=[]
   for i,row in enumerate(selections):
    a=row['word']['sign']*(row['word']['bytes'][0]*64+row['word']['bytes'][1]); d=flow_diagram(['source operand','symbol resolution','encoded address'],part%3,'Names become numeric instruction fields',f"line {row['line']} → memory {row['address']}: {row['op']} {row['operand']}"); d['nodes'] += [text('address-val',585,170,a,'result',result=True)]; fs.append(frame(i,f"Source row {row['line']} emits {row['op']} at {row['address']}; its numeric A-part is {a}.",d,data=row))
   q='What address does START name in this assembled example?'; answer=start; model.update(source=lines,listing=listing,symbols=sy)
  elif part==0:
   parts=[('-7',2),('2',27),('5',36),('8',45)] if not small else [('3',2),('8',45)]; w=Word(); fs=[]
   for i,(v,f) in enumerate(parts): w=store(w,Word.number(int(v)),f); fs.append(frame(i,f'Insert {v} into field {field(f)[0]}:{field(f)[1]}.',word_diagram([('built word',w.data())],active=list(range(field(f)[0],field(f)[1]+1))),data=w.data()))
   q='Does writing field 5:5 replace the address bytes?'; answer='No'
  elif part==1:
   a,b,c=(1,2,3) if small else (2,3,4); fs=computed_cards([([a,b,a+b],'First evaluate the left addition.'),([a+b,c,(a+b)*c],'Then multiply the accumulated expression value.')],'Left-to-right MIXAL expression',['left','right','result']); q=f'In MIXAL, what is {a}+{b}*{c}?'; answer=(a+b)*c
  elif part==2:
   n=3 if small else 7; lines=[('','ORIG','80'),('START','ENTA','0'),('','ADD',f'={n}='),('','HLT','0'),('','END','START')]; m,sy,listing=run_program(lines); fs=machine_frames(m); q='What value is added from the emitted literal word?'; answer=n; model.update(source=lines,listing=listing,executedTrace=m.trace)
  else:
   lines=[('','ORIG','80'),('START','HLT','0'),('DATA','CON','12(4:5)'),('','END','START')]; mem,sy,start,li=assemble(lines); fs=[frame(i,f"{r['op']} occupies memory {r['address']}.",word_diagram([(r['op'],r['word'])]),data=r) for i,r in enumerate(li)]; q='Does CON create a CPU instruction that must be executed?'; answer='No'; model['listing']=li
 elif order==72:
  vals=[3,-1] if small else [7,-2,9,4]; n=len(vals); lines=[('','ORIG','100'),('START','ENTA','0'),('','ENT1',str(-n)),('LOOP','ADD',f'DATA+{n},1'),('','INC1','1'),('','J1N','LOOP'),('','STA','TOTAL'),('','HLT','0')]+[('DATA' if i==0 else '','CON',str(v)) for i,v in enumerate(vals)]+[('TOTAL','CON','0'),('','END','START')]; m,sy,li=run_program(lines); allfs=machine_frames(m)
  fs=allfs if part==0 else ([allfs[i+1] for i,t in enumerate(m.trace) if t['opcode']==1] if part==1 else (allfs[-3:] if part==2 else allfs[:5])); q=f'What is the total for the input {vals}?'; answer=sum(vals)
  if part==1:
   fs=[]
   for k,t in enumerate([t for t in m.trace if t['opcode']==1]):
    before=t['before']; assert before['A']['value']==sum(vals[:k]) and before['I'][0]==k-n and t['effectiveAddress']==sy['DATA']+k
    d=array_diagram(vals,k+1,'Computed prefix before the next ADD')
    d['description']='Array cells are input terms. Completed prefix terms lie left of the highlighted next term.'
    d['invariant']='A is the exact sum of the first k input terms; I1=k−n before ADD.'
    for nd in d['nodes']:
     if nd['id'].startswith('cell-') or nd['id'].startswith('value-'):
      j=int(nd['id'].split('-')[1]);nd['role']='result' if j<k else 'active' if j==k else 'muted'
    d['nodes'] += [text('prefix-equation',360,300,f"k={k}: prefix sum={sum(vals[:k])}; A={before['A']['value']}",'result',result=True),text('index-equation',360,345,f"I1={before['I'][0]} = {k}−{n}; next address={t['effectiveAddress']}",'active')]
    fs.append(frame(k,f'Before zero-based addition {k}: exactly {k} inputs contribute to A; the next operand is DATA+{k}.',d,rf"A=\sum_{{j=0}}^{{{k}-1}}x_j={sum(vals[:k])},\quad I_1={k}-{n}",{'k':k,'A':before['A'],'I':before['I'],'prefix':vals[:k],'nextAddress':t['effectiveAddress']}))
   final=next(t['after'] for t in reversed(m.trace) if t['opcode']==41)
   d=array_diagram(vals,0,'Every input is in the completed prefix');d['description']='The complete input prefix has been summed; no next operand remains.';d['invariant']='At loop exit k=n, A is the full sum and I1=0.'
   d['nodes'] += [text('prefix-equation',360,300,f"k={n}: A={final['A']['value']} = full sum",'result',result=True),text('index-equation',360,345,'I1=0; the final J1N is not taken','active')]
   fs.append(frame(n,'After the final increment and untaken branch: I1=0 and every input has contributed exactly once.',d,rf"k=n={n},\quad A={sum(vals)},\quad I_1=0",{'k':n,'A':final['A'],'I':final['I'],'prefix':vals[:],'nextAddress':None}))
   q='What is I1 after the final increment?'; answer=0
  if part==2: q='What is the documented total cost in u?'; answer=4*n+5
  if part==3: q='Would setting the initial count to zero safely handle empty input without a pretest?'; answer='No'
  model.update(source=lines,listing=li,symbols=sy,executedTrace=m.trace)
 elif order==73:
  p=[2,3,1] if small else [3,1,2,5,4,6]; cs=cycles(p); fs=[]
  if part==3:
   invalid=[2,2,1] if small else [2,3,1,5,5,6];fs=[]
   d=array_diagram(invalid,title='Inspect images before following cycles');d['description']='Cells contain proposed permutation images; repeated targets are not yet accepted.';d['invariant']='Images must be exactly the declared labels 1…n.'
   fs.append(frame(0,'Inspect the proposed image array before any inverse or cycle writes.',d,data={'mapping':invalid,'mutated':False}))
   try:cycles(invalid);raise AssertionError('nonbijection accepted')
   except SemanticError as error:message=str(error)
   duplicate=next(v for v in invalid if invalid.count(v)>1);missing=next(v for v in range(1,len(invalid)+1) if v not in invalid)
   d=copy.deepcopy(d);d['nodes'] += [text('domain-failure',360,310,f'duplicate image {duplicate}; missing image {missing}','error'),text('no-mutation',360,360,'reject before traversal or writes','error')]
   fs.append(frame(1,message+': duplicate and missing images violate bijectivity.',d,data={'mapping':invalid[:],'duplicate':duplicate,'missing':missing,'rejected':True,'mutated':False}));q='Is this input a valid bijection?';answer='No';model.update(input=invalid,rejected=True)
  elif part in (0,2):
   seen=[]
   for i,c in enumerate(cs): seen+=c; fs.append(frame(i,f'Follow cycle {c} back to its start.',cycle_diagram(p,seen),data={'cycles':cs[:i+1]}))
   q='How many disjoint cycles, including fixed points, are in this mapping?'; answer=len(cs)
  else:
   p=[2,1,3]; qmap=[1,3,2]; product=[qmap[x-1] for x in p]; reverse=[p[x-1] for x in qmap]; fs=[frame(i,cap,cycle_diagram(v,title=cap),data={'mapping':v}) for i,(v,cap) in enumerate([(p,'First mapping p'),(qmap,'Then mapping q'),(product,'Product: apply p, then q'),(reverse,'Reversed order gives a different mapping')])]; q='Where does 1 go when p is applied and then q?'; answer=product[0]; model.update(p=p,q=qmap,product=product)
 elif order==74:
  p=[2,3,1] if small else [4,3,2,6,5,1]; tr=inverse_trace(p); allfs=[frame(i,s['caption'],array_diagram(s['array'],s['current'],saved=s['savedNext']),data=s) for i,s in enumerate(tr)]; fs=allfs if part==0 else focused(allfs,part); q=f'What is the inverse image of 1 in {p}?'; answer=p.index(1)+1
  if part==1: q='Which value must be saved before replacing the current cell?'; answer='its original successor'
  if part==2: q='Why can a negative value mark a processed cell?'; answer='all input labels are positive'
  if part==3: q='How many array-sized working arrays does this in-place algorithm require beyond its input?'; answer=0
  model.update(original=p,trace=tr)
 elif order==75:
  p=[2,1,3] if small else [3,1,2,5,4,6]; cs,seq,records=canonical(p); fs=[]
  if part==2:
   from fractions import Fraction
   n=3 if small else 5; total=Fraction(0)
   for i in range(1,n+1): total+=Fraction(1,i); fs+=computed_cards([([i,str(Fraction(1,i)),str(total)],f'Position {i} contributes record probability 1/{i}.')],'Expected cycle count',['position','probability','sum'])
   q=f'What is the record probability at position {n}?'; answer=f'1/{n}'
  else:
   for i in range(len(seq)):
    d=array_diagram(seq[:i+1],i+1,'Read the canonical linear sequence'); d['nodes'] += [text('breaks',360,340,'cycle starts: '+', '.join(str(seq[j]) for j in records if j<=i),'result',result=True)]; fs.append(frame(i,f"Read {seq[i]}: {'new minimum, start a cycle' if i in records else 'continue current cycle'}.",d,data={'sequence':seq[:i+1],'records':[j for j in records if j<=i]}))
   q='How many parentheses groups are recovered from this sequence?'; answer=len(cs)
  model.update(mapping=p,canonicalCycles=cs,sequence=seq,records=records)
 elif order==76:
  n=3 if small else 5; terms=[(-1)**k*math.comb(n,k)*math.factorial(n-k) for k in range(n+1)]; fs=[]
  if part==1:
   r=2 if small else 3; terms=[(-1)**k*math.comb(r,k) for k in range(r+1)]; title='Coefficient of one permutation with fixed points'
  else: title='Signed inclusion–exclusion corrections'
  if part==2: terms=[1,0]; fs=computed_cards([([0,1],'The empty permutation is a derangement.'),([1,0],'A single object cannot move elsewhere.')],title,['n','Dₙ']); q='How many derangements are there of zero objects?'; answer=1
  else:
   total=0
   for k,v in enumerate(terms): total+=v; fs+=computed_cards([([k,v,total],f'Apply correction {k}, with signed contribution {v}.')],title,['k','correction','running total'])
   q='What is the final surviving coefficient?' if part==1 else f'How many derangements are there for n={n}?'; answer=total
  model.update(n=n,terms=terms)
 elif order==77:
  lines=copy.deepcopy(CALL); lines[1]=('START','ENTA','3' if small else '11'); m,sy,li=run_program(lines); allfs=machine_frames(m)
  if part==1:
   before=m.trace[2]['before']['memory'][str(sy['RETURN'])]; after=m.trace[2]['after']['memory'][str(sy['RETURN'])]; fs=[frame(0,'Before STJ: return address is a placeholder.',word_diagram([('RETURN',before)]),data=before),frame(1,'After STJ: only the address field is patched.',word_diagram([('RETURN',after)],active=[0,1,2]),data=after)]; q='What opcode remains in the patched return instruction?'; answer=39
  else: fs=allfs if part==0 else focused(allfs,part); q='What value is returned in A?'; answer=6 if small else 22
  if part==2: q='Can one static return slot safely serve two simultaneous activations?'; answer='No'
  if part==3: q='What continuation does this call resume?'; answer=202
  model.update(source=lines,listing=li,executedTrace=m.trace)
 elif order==78:
  B,L,C=4 if small else 8,2,1; ks=range(1,4 if small else 6)
  if part==0: fs=computed_cards([([k,k*B,B+L+k*C],f'{k} use sites: compare copied bodies with one shared body and linkage.') for k in ks],'Code-space crossover',['calls','inline words','shared words']); q=f'With B={B}, L=2, C=1, what is the smallest k that saves space?'; answer=(B+L)//(B-C)+1
  elif part==1: fs=computed_cards([([k,k*5,k*9],f'{k} uses add four MIX units of linkage per call.') for k in ks],'Body cost plus call overhead',['calls','inline time','shared time']); q='What extra time do two calls incur if linkage costs 4 each?'; answer=8
  elif part==3:
   returns=[11,21] if small else [101,201,301];stack=[];static=None;tr=[]
   def activation_frame(action,expected=None):
    tr.append({'stack':stack[:],'static':static,'expectedReturn':expected,'action':action})
   activation_frame('Before any activation: no continuation is saved.')
   for address in returns:static=address;stack.append(address);activation_frame(f'Enter one more activation; save continuation {address}.')
   while stack:
    expected=stack.pop();activation_frame(f'Return from one activation: its continuation must be {expected}.',expected)
   fs=[]
   for i,a in enumerate(tr):
    ns=[text('static-title',180,55,'one static slot'),text('stack-title',500,55,'one slot per live call'),rect('static-slot',90,125,180,60,'error' if a['expectedReturn'] is not None and a['static']!=a['expectedReturn'] else 'active'),text('static-value',180,162,a['static'] if a['static'] is not None else 'empty','active')]
    for depth,address in enumerate(a['stack']):
     y=100+depth*70;ns += [rect('activation-'+str(depth),410,y,180,55,'active'),text('return-'+str(depth),500,y+34,'return '+str(address),'active')]
    if a['expectedReturn'] is not None:ns += [text('expected-return',360,365,f"required return {a['expectedReturn']}; static contains {a['static']}",'error' if a['static']!=a['expectedReturn'] else 'result',result=True)]
    fs.append(frame(i,a['action'],diagram('Nested activation storage counterexample','These are semantic writes to continuation storage, not a claimed execution of a recursive MIX program.',ns,'Every live activation needs its own saved continuation.'),data=a))
   q='May all simultaneously live calls share a static continuation slot?';answer='No';model['activationTrace']=tr

  else:
   m,sy,li=run_program(CALL); fs=computed_cards([([m.trace[1]['before']['X']['value'],m.trace[-1]['after']['X']['value']],'Compare the promised preserved X value at entry and exit.')],'Contract preservation',['X before','X after']); q='Is A promised unchanged by TWICE?'; answer='No'
 elif order in (79,80):
  n=2 if small else (3 if order==79 else 4); tr=coroutine(n); fs=[]
  for i,s in enumerate(tr):
   d=coroutine_diagram(s); fs.append(frame(i,s['caption'],d,data=s))
  fs=fs if part==0 else focused(fs,part); q='What is the completed consumer total?'; answer=sum(i*i for i in range(1,n+1))
  if part==1: q='What producer continuation is saved immediately after a yield?'; answer='ADVANCE'
  if part==2: q='How many USE events occur before END?'; answer=n
  if part==3: q='Can this single-threaded coroutine model have both components executing at once?'; answer='No'
  model.update(n=n,trace=tr)
 elif order==81:
  code=[('PUSH',2 if small else 4),('DUP',None),('ADD',None)]+([] if small else [('PUSH',3),('ADD',None)])+[('HALT',None)]; tr=interpret(code); fs=[]
  for i,s in enumerate(tr):
   d=flow_diagram(['fetch object code','dispatch '+s['op'],'update object stack'],2,'A host implements one object instruction',f"object PC {s['pc']} → {s['next']}; stack {s['stack']}"); fs.append(frame(i,s['caption'],d,data=s))
  if part==2:
   try: interpret([('ADD',None)])
   except SemanticError as e: fs=[frame(0,str(e),flow_diagram(['empty stack','ADD requires two','diagnostic'],2,'An invalid object instruction cannot run'),data={'error':str(e)})]
   q='What minimum stack depth does ADD require?'; answer=2
  else: fs=focused(fs,part); q='What is the final object-stack value?'; answer=tr[-1]['stack'][0]
  model.update(code=code,trace=tr)
 elif order==82:
  if part==0: m=mini_program([('ENTA',2 if small else 5,None),('INCA',3,None),('STA',20,None)])
  elif part==1: m=mini_program([('ENTA',2,None),('MUL',20,None),('DIV',20,None)],{20:Word.number(3)})
  elif part==2: m=mini_program([('DIV',20,None)],{'A':Word.number(0),20:Word.number(0)})
  else: m,sy,li=run_program(SUM)
  fs=machine_frames(m); q='Does this interpreter execute hardware I/O opcodes 34–38?'; answer='No'
  if part==0: q='What value is stored at address 20?'; answer=m.at(20).value
  if part==2: q='Does dividing by zero produce a meaningful quotient in this model?'; answer='No'
  if part==3: q='What is the summation program’s guest time in u?'; answer=m.clock
  model.update(executedTrace=m.trace,supported='Integer non-I/O families; no floating point; explicit invalid/undefined diagnostics')
 elif order==83:
  if part==0:
   w=Word.number(0,zero=-1); got=load(w,0); fs=[frame(0,'Input is negative zero.',word_diagram([('input',w.data())])),frame(1,'Sign-only load retains the negative sign.',word_diagram([('result',got.data())]))]; q='How many distinct sign representations does numerical zero have in MIX?'; answer=2
  elif part==1:
   m=mini_program([('MOVE',20,2 if small else 3)],{'I1':Word.number(21),20:Word.number(7),21:Word.number(2),22:Word.number(9)}); t=m.trace[0]; vals0=[t['before']['memory'].get(str(i),Word().data())['value'] for i in range(20,24)]; vals1=[m.at(i).value for i in range(20,24)]; fs=[frame(0,'Before a sequential overlapping MOVE.',array_diagram(vals0)),frame(1,'Later reads see earlier writes.',array_diagram(vals1))]; q='What value reaches memory 22 in this overlapping MOVE?'; answer=7; model['executedTrace']=m.trace
  elif part==2:
   m=Machine(); m.mem[0]=instruction(-1,8); before=m.snapshot()
   try: m.step()
   except SemanticError as e: msg=str(e)
   fs=computed_cards([([before['pc'],m.pc],msg)],'Transactional invalid-address test',['PC before','PC after']); q='Does rejecting this instruction change the guest state?'; answer='No'; model['unchanged']=before==m.snapshot()
  else:
   counts=[sum(1 for l in range(6) for r in range(l,6)),2,3]; fs=computed_cards([([counts[0],counts[1],counts[0]*counts[1]*counts[2]],'All fields, signs and tested byte bases form a finite covered domain.')],'Declare test-domain coverage',['valid fields','signs','combinations']); q='How many legal L:R fields exist?'; answer=21
 elif order==84:
  lines=SUM if not small else CALL; a,sy,li=run_program(lines); b=Machine(); mem,_,start,_=assemble(lines); b.mem=mem; b.pc=start; events=[]
  while not b.halted:
   b.step(); events.append(copy.deepcopy(b.snapshot())); b.trace.clear()
  assert a.snapshot()==b.snapshot(); fs=[]
  for i,t in enumerate(a.trace):
   d=flow_diagram(['one guest step','copy snapshot','append log'],1 if part<2 else 2,'Observe without re-execution',f"step {i+1}: traced A={t['after']['A']['value']}; baseline A={events[i]['A']['value']}"); fs.append(frame(i,'The observer copies a committed result; guest execution occurs once.',d,data={'traced':t['after'],'baseline':events[i],'equal':t['after']==events[i]}))
  fs=focused(fs,part); q='Are final guest memory and registers equal with and without retained tracing?'; answer='Yes'; model.update(finalEqual=True,trace=a.trace,baselineFinal=b.snapshot())
 elif order in (85,86):
  n=2 if small else 4; io,c=(2,3) if small else (3,5); k=2 if order==85 else 3
  if part==2:
   timings=[buffers(n,io,c,j)[-1]['time'] for j in (1,2,3)]; fs=computed_cards([([j,t],f'{j} buffers finish all {n} items at time {t}.') for j,t in zip((1,2,3),timings)],'Same work, different storage',['buffers','finish time']); q='Does adding a third buffer improve this constant-service model over two?'; answer='No'; model['times']=timings
  else:
   tr=buffers(n,io,c,k); fs=[frame(i,s['caption'],buffer_diagram(s),rf't={s["time"]}',s) for i,s in enumerate(tr)]; fs=fs if part==0 else focused(fs,part); q='How many items are issued and consumed?'; answer=n; model['schedule']=tr
   if part==1: q='Which state must a buffer have before input may acquire it?'; answer='EMPTY'
   if part==3: q='Does the known-count protocol issue one extra input after the final item?'; answer='No'
 elif order==87:
  records=['AB','C'] if small else ['AB','CDEFG','H']; cap=2 if small else 5; tr=pack(records,cap); allfs=[frame(i,s['caption'],packing_diagram(s,cap),rf'c={s["consumed"]}',s) for i,s in enumerate(tr)]; fs=allfs if part==0 else focused(allfs,part); q='What is the number of valid payload characters in the final block?'; answer=len(tr[-1]['blocks'][-1])
  if part==1: q='Does a record boundary automatically flush the current block in this policy?'; answer='No'
  if part==2: q='How many physical payload blocks are emitted?'; answer=len(tr[-1]['blocks'])
  if part==3: q='Which metadata lets the original record boundaries be reconstructed?'; answer='record lengths'
  model.update(records=records,recordLengths=list(map(len,records)),capacity=cap,trace=tr)
 else: raise AssertionError(order)
 if order in (72,77) and part==0:
  model['sourceVisualLinks']=[]
  listing_by_line={row['line']:row for row in model['listing']}
  initial_memory=model['executedTrace'][0]['before']['memory']
  for source_index,(label,op,operand) in enumerate(model['source']):
   row=listing_by_line.get(source_index+1)
   if op=='CON':
    address=row['address']; initial_word=initial_memory[str(address)]
    fs.append(frame('data-'+str(address),f'Assembly inspection: CON initializes address {address} to {initial_word["value"]}; this is data, not an executed instruction.',word_diagram([(f'initial @{address}',initial_word)]),data={'assemblyOnly':True,'sourceLine':source_index+1,'address':address,'word':initial_word}))
    target=len(fs)-1
   elif row:
    target=next(i for i,st in enumerate(fs) if st['data'].get('fetchedAddress')==row['address'])
   else:target=0
   model['sourceVisualLinks'].append({'sourceLine':source_index+1,'op':op,'address':row['address'] if row else None,'frameIndex':target})
 # A one-event boundary test exposes its precondition before its result.
 if len(fs)==1:
  after=fs[0]
  before=frame('before','Inspect the initial operands and precondition before evaluating this boundary case.',flow_diagram(['initial operands','check precondition','compute or reject'],0,'Before this boundary operation'),data={'phase':'before','focus':part})
  fs=[before,after]
 fs=teaching_motion(order,part,fs,model)
 if order in (68,72,77,82): fs=instruction_bridge(fs,model,order,part)
 # Every state ID is unique within its operation-focused sequence.
 for i,s in enumerate(fs): s['id']=f's{i}'
 if isinstance(answer,int): distractors=[answer+1,answer-1 if answer else 2]
 else:
  alternatives={'No':['Yes','Only when the animation is paused'],'Yes':['No','Only for zero inputs'],'negative':['positive','unspecified'],'C':['I','F'],'ADVANCE':['MAKE','END'],'EMPTY':['FILLING','PROCESSING'],'record lengths':['block count only','first character only'],'its original successor':['the final inverse array','the sign alone'],'all input labels are positive':['negative numbers need no storage','every cycle has length two']}; distractors=alternatives.get(answer,['A different state','No retained state'])
 check={'prompt':q,'choices':[str(answer),*map(str,distractors)],'correctIndex':0,'explanation':f'The computed model gives {answer}. Use the stated operation and its preconditions, rather than a remembered frame position.'}
 return fs,model,check

META=[{'id': 'a-word-is-sign-plus-bytes', 'order': 65, 'title': 'A word is sign plus bytes', 'sections': ['1.3', '1.3.1']}, {'id': 'load-and-store-selected-fields', 'order': 66, 'title': 'Load and store selected fields', 'sections': ['1.3.1']}, {'id': 'arithmetic-flags-and-double-width-values', 'order': 67, 'title': 'Arithmetic flags and double-width values', 'sections': ['1.3.1']}, {'id': 'decode-instructions-and-follow-control', 'order': 68, 'title': 'Decode instructions and follow control', 'sections': ['1.3.1']}, {'id': 'connect-a-machine-to-devices-and-characters', 'order': 69, 'title': 'Connect a machine to devices and characters', 'sections': ['1.3.1']}, {'id': 'names-become-addresses', 'order': 70, 'title': 'Names become addresses', 'sections': ['1.3.2']}, {'id': 'build-data-and-instructions-with-mixal', 'order': 71, 'title': 'Build data and instructions with MIXAL', 'sections': ['1.3.2']}, {'id': 'run-an-original-complete-mix-program', 'order': 72, 'title': 'Run an original complete MIX program', 'sections': ['1.3.2']}, {'id': 'compose-permutations-and-discover-cycles', 'order': 73, 'title': 'Compose permutations and discover cycles', 'sections': ['1.3.3']}, {'id': 'invert-a-permutation-without-losing-information', 'order': 74, 'title': 'Invert a permutation without losing information', 'sections': ['1.3.3']}, {'id': 'relate-cycles-to-records', 'order': 75, 'title': 'Relate cycles to records', 'sections': ['1.3.3']}, {'id': 'count-fixed-points-with-inclusion-and-exclusion', 'order': 76, 'title': 'Count fixed points with inclusion and exclusion', 'sections': ['1.3.3']}, {'id': 'call-a-routine-and-return-safely', 'order': 77, 'title': 'Call a routine and return safely', 'sections': ['1.4.1']}, {'id': 'measure-reuse-and-specify-side-effects', 'order': 78, 'title': 'Measure reuse and specify side effects', 'sections': ['1.4.1']}, {'id': 'resume-where-a-coroutine-paused', 'order': 79, 'title': 'Resume where a coroutine paused', 'sections': ['1.4.2']}, {'id': 'join-producer-and-consumer-coroutines', 'order': 80, 'title': 'Join producer and consumer coroutines', 'sections': ['1.4.2']}, {'id': 'programs-can-interpret-other-programs', 'order': 81, 'title': 'Programs can interpret other programs', 'sections': ['1.4.3']}, {'id': 'build-a-faithful-mix-simulator', 'order': 82, 'title': 'Build a faithful MIX simulator', 'sections': ['1.4.3.1']}, {'id': 'test-a-simulator-at-its-semantic-edges', 'order': 83, 'title': 'Test a simulator at its semantic edges', 'sections': ['1.4.3.1']}, {'id': 'trace-without-changing-the-program-s-meaning', 'order': 84, 'title': "Trace without changing the program's meaning", 'sections': ['1.4.3.2']}, {'id': 'overlap-useful-work-with-input', 'order': 85, 'title': 'Overlap useful work with input', 'sections': ['1.4.4']}, {'id': 'manage-multiple-buffers-as-a-queue', 'order': 86, 'title': 'Manage multiple buffers as a queue', 'sections': ['1.4.4']}, {'id': 'format-variable-output-incrementally', 'order': 87, 'title': 'Format variable output incrementally', 'sections': ['1.4.4']}]
PAGE_RANGES={65:'223–227',66:'227–231',67:'231–238',68:'226–227, 235–238',69:'238–243',70:'249–264',71:'255–265',72:'249–265',73:'277–281',74:'295–298',75:'299–301',76:'301–303',77:'309–318',78:'309–318',79:'319–321',80:'320–329',81:'330–332',82:'332–348',83:'223–243, 332–348',84:'349–352',85:'353–359',86:'359–367',87:'353–358'}

def passage_check(order,part,small,model,original):
 """Assessment targets the passage's claim; explanation supplies the actual reason."""
 def q(prompt,answer,wrong,why):
  return dict(prompt=prompt,choices=[str(answer),*map(str,wrong)],correctIndex=0,explanation=why)

 # Each help question applies its own smaller input or diagnostic, rather than renaming the main question.
 help_cases={
 65:[('Write 65 in base 64. What are its final two bytes?','1,1',['0,65','6,5'],'65=1·64+1, so the quotient and remainder occupy the last two bytes.'),('Both words have zero digits, but one sign is minus. Are their numeric comparisons equal?','Yes',['No','Only at base 100'],'Signed-zero representations differ, while MIX numerical comparison treats both as zero.'),('Can index register I1 hold a magnitude of 64² at radix 64?','No',['Yes','Only with a minus sign'],'Two bytes hold magnitudes from zero through 64²−1. The sign does not add another magnitude position.'),('The integer 65 ends in bytes 1,1 at radix 64. How does it end at radix 100?','0,65',['1,1','6,5'],'At radix 100, 65 fits in one byte, so the preceding byte is zero. Recompute the digits from the same integer.')],
 66:[('Which field code selects only byte 5?','45',['5','40'],'L=R=5, so the encoded selector is 8·5+5=45.'),('Store register tail bytes 6,7 into memory field 4:4. Which digit is written?','7',['6','Both 6 and 7'],'A one-byte store takes the single rightmost source byte and writes it to destination byte 4.'),('Store a positive register sign into field 0:0 of a negative word. What changes?','Only the sign becomes plus',['All bytes become zero','Nothing'],'A sign-only store selects no magnitude positions, so every destination byte survives.'),('Memory bytes are 1,2,3,4,5. Store tail byte 7 into field 3:3. What is byte 2 afterward?','2',['7','0'],'Byte 2 lies outside the selected destination interval and must remain unchanged.')],
 67:[('Overflow is on before adding 1 to A=2. What is its setting afterward?','On',['Off','Undefined'],'The nonoverflowing sum 3 does not clear a previously set overflow toggle.'),('A negative value is multiplied by positive zero. What signs do A and X receive?','Both minus',['Both plus','A minus, X plus'],'MUL assigns both output signs by the algebraic input signs even when the product magnitude is zero.'),('After SLA 1, is X changed?','No',['Its first byte becomes zero','Its sign flips'],'SLA shifts only A’s magnitude bytes. AX shifts and rotations are the distinct instructions that also affect X.'),('At radix 64, I1=4095 and INC1 1 is requested. Is zero a specified result?','No; index overflow is undefined',['Yes; it wraps like A','Yes; J receives the carry'],'4096 needs more than two base-64 bytes. MIX does not prescribe ordinary wrapped A arithmetic for index registers.')],
 68:[('An instruction has address 10 and I=1; I1 contains −2. What is M?','8',['11','−2'],'Indexing adds the contents of I1, not the selector number: 10+(−2)=8.'),('An untaken conditional jump starts with J=7. What remains in J?','7',['The next PC','0'],'Only an actually taken ordinary jump writes J. An untaken test preserves the previous continuation.'),('JNOV begins with overflow off. Does it jump and leave overflow off?','Yes',['No; it switches overflow on','No; it never jumps'],'JNOV jumps when overflow is off and leaves the toggle off in either case.'),('A malformed field is rejected at PC=4. Where does the next inspection find PC?','4',['5','The malformed field code'],'The model rolls back the entire rejected step, including the default PC increment.')],
 69:[('An OUT transfer is unfinished. May the program overwrite its source word?','No',['Yes; output already started','Yes; if the value stays positive'],'OUT can read the source later during the transfer. It must remain unchanged until completion.'),('A device has finished its previous operation. Which readiness jump condition is satisfied?','JRED',['JBUS','Both'],'JRED tests ready and JBUS tests busy. Finishing the operation establishes readiness.'),('NUM reads a byte with code 37. Which decimal digit does that byte contribute?','7',['37','3'],'NUM takes each character byte modulo ten; 37 mod 10 is 7.'),('How many documented units do ENTA then STA cost?','3',['2','4'],'ENTA costs 1u and STA costs 2u. Host animation duration is unrelated.')],
 70:[('ORIG sets location 500, then a labeled ENTA is emitted. Which address belongs to that label?','500',['501','The source row number'],'The label names the current location before emitting its word. ORIG itself occupies no memory word.'),('A branch names EXIT before EXIT is defined. Must the program run to resolve the name?','No; assembly resolves it',['Yes; execute until EXIT','Yes; run the branch twice'],'Symbol resolution converts source names into numeric addresses before guest execution.'),('A 2F reference is followed by two 2H definitions. Which one is selected?','The nearest later source definition',['The farthest later definition','The one with the lowest address'],'F means forward from the referencing source row. Repeated local labels are resolved by source order.'),('A source has EQU followed by CON. Which directive emits a memory word?','CON',['EQU','Both'],'EQU records a symbol value without consuming storage. CON constructs a word at the current location.')],
 71:[('A word’s address is 3. Writing opcode byte 5 to 8 changes which field?','Only byte 5',['The two address bytes','The sign and all bytes'],'Fieldwise construction changes its selected destination positions. An opcode-byte write leaves the address intact.'),('Evaluate MIXAL 1+2*3 under left-to-right rules. What comes first?','1+2',['2*3','Both operations simultaneously'],'MIXAL does not apply conventional multiplication precedence here; (1+2)·3 gives 9.'),('The instruction ADD =3= uses what kind of effective operand?','An address of an emitted word containing 3',['The literal as an immediate number','A source line number'],'The assembler places 3 in the literal pool and makes the ADD address point to that memory word.'),('A CON word lies after HLT and no branch reaches it. Is that word executed?','No',['Always','Only when its value is nonzero'],'CON emits data, and guest control determines which words are fetched. Halting first leaves this word unexecuted.')],
 72:[('The smaller input is 3,−1. What value does TOTAL receive?','2',['4','−2'],'The loop adds each signed input once: 3+(−1)=2.'),('For two inputs, I1 starts at −2. After one completed iteration, what remains to process?','One input',['Two inputs','No inputs'],'One increment changes I1 to −1; the accumulated prefix has one element and one remains.'),('Two inputs use two ADD, two INC1 and two J1N instructions. What is their loop-only cost?','8u',['6u','13u'],'Each iteration costs 2+1+1=4u, so the loop costs 8u. Setup and final store/halt are separate.'),('Where must an empty-input test occur to avoid reading the first data word?','Before entering ADD',['After the first ADD','Only after HLT'],'The current loop is post-tested. A pretest is required to bypass all data access for zero length.')],
 73:[('Is [2,1,3] a bijection of 1,2,3 even though 3 is fixed?','Yes',['No; fixed points are forbidden','No; outputs must be sorted'],'Each label occurs exactly once. A fixed point is a valid singleton cycle, not a violation of bijectivity.'),('p sends 1→2 and q sends 2→3. Applying p then q sends 1 where?','3',['2','1'],'Composition uses the output 2 of p as the input to q, whose output is 3.'),('The cycle 1→2→3→1 contains how many fixed points?','0',['1','3'],'Every node changes to a different image. Returning after three steps does not make any one-step image fixed.'),('The proposed domain is 1,2,3, but an image is 4. What should happen first?','Reject the mapping',['Follow the arrow to array slot 4','Treat 4 as a fixed point'],'All images must belong to the declared finite domain before cycle traversal can be safe.')],
 74:[('In [2,3,1], which inverse entry must equal 1?','Entry 2',['Entry 1','Entry 3'],'The original maps 1 to 2, so its inverse must map 2 back to 1.'),('Before changing cell 2 from successor 3 to a tagged predecessor, what must be retained?','The old 3',['Only the new sign','The final array length'],'Saving successor 3 preserves the onward path after cell 2 is overwritten.'),('Could the same negative-tag rule accept arbitrary negative input labels unchanged?','No',['Yes','Only if every cycle is long'],'Negative payloads would be indistinguishable from the processed marker. The positive-label precondition makes tagging meaningful.'),('A three-cycle test passes. What explains why the next overwrite is safe?','Its successor has already been saved',['The final answer looked right once','Three cells never alias'],'The local cycle invariant preserves the unread path before every destructive write; a single successful test does not establish that reason.')],
 75:[('Canonical cycles are (3)(1 2). What erased sequence follows?','3,1,2',['1,2,3','3,2,1'],'Each cycle begins at its minimum and the cycle starts decrease, so singleton (3) precedes (1 2).'),('Read 3,1,2 under the minimum-record rule. Where does the second cycle begin?','At 1',['At 2','There is no second cycle'],'1 is below the earlier minimum 3 and starts a cycle. The following 2 is not a new minimum.'),('In a uniformly ordered pair, how likely is the second item to be a new minimum?','1/2',['1','1/3'],'Either of the two distinct elements is equally likely to be the smaller, giving probability one half.'),('In sequence 3,1,2, is the final 2 a new minimum?','No',['Yes','Only if it is a maximum record'],'The running minimum is already 1. The declared minimum-record convention therefore keeps 2 in the current cycle.')],
 76:[('For three labels, fixing one chosen label leaves how many arrangements?','2',['3','6'],'The remaining two labels can be permuted in 2!=2 ways, regardless of whether they create extra fixed points.'),('A permutation has two fixed points. What is its inclusion–exclusion coefficient?','1−2+1=0',['1−2=−1','1+2+1=4'],'The pair intersection restores the item subtracted twice. The full coefficient is (1−1)²=0.'),('Can the only permutation of one object be a derangement?','No',['Yes','Only if the object is called zero'],'That sole permutation fixes the object, so D1=0 even though D0=1.'),('Three objects have two derangements among six permutations. What is the probability?','1/3',['2','2/3'],'Uniform probability is favorable count divided by total count: 2/6=1/3.')],
 77:[('The smaller call enters TWICE with A=3. What should the result register hold?','6',['3','9'],'The routine copies A to TEMP and adds that copy once, computing 3+3.'),('A return instruction’s modifier is JSJ. Should STJ change that modifier?','No',['Yes; change it to JMP','Yes; clear it to zero'],'Default STJ writes only 0:2; byte 4 holding the modifier lies outside that field.'),('Calling TWICE with x so large that 2x needs six bytes violates which contract?','The no-overflow entry precondition',['The local-label convention','The sign-only field rule'],'The stated contract requires |2x|<b⁵. Without it, a wrapped A would not be the promised exact doubled result.'),('A caller needs its original A after TWICE returns. What must it arrange?','Save A before the call',['Assume all registers are preserved','Replace JSJ by NOP'],'A is explicitly the result register and may change. Preservation must be arranged by the caller or a different callee contract.')],
 78:[('For B=4,L=2,C=1, do two call sites save any words?','No; both use 8 words',['Yes; sharing uses 4','Yes; inlining uses 6'],'Inlining uses 2·4=8; sharing uses 4+2+2·1=8. A tie is not a strict saving.'),('One call has body cost 5u and linkage cost 4u. What is its full cost?','9u',['5u','4u'],'Call cost includes both useful body work and entry/exit overhead: 5+4=9u.'),('TWICE promises to preserve X. Which comparison checks that promise?','X at entry equals X at exit',['A at exit equals X','X equals zero afterward'],'Preservation is an entry-to-exit equality for the named register; it does not require a particular fixed value.'),('Two recursive activations are live at once. May they share one saved return address?','No',['Yes; if they use the same routine','Yes; if their source call sites differ'],'The inner activation needs its own continuation while the outer one still needs its saved address.')],
 79:[('The producer yielded 1 and saved ADVANCE with i=1. On resume, what happens before the next yield?','i increments to 2',['i resets to 1','The consumer discards its total'],'ADVANCE is the saved control point, so retained i increments before MAKE emits the next square.'),('If the producer mistakenly resumes MAKE with unchanged i, what error occurs?','The same square repeats',['The stream ends correctly','The consumer total resets'],'MAKE uses the retained counter. Without the ADVANCE step it produces the previously yielded value again.'),('For n=0, how many USE steps should the consumer execute?','0',['1','2'],'The producer reports END immediately, with no pending payload for USE.'),('While one coroutine runs, what happens to the other in this model?','It is suspended with retained state',['It executes on a second CPU','It loses its locals'],'The model transfers control cooperatively; suspension stores state without simultaneous execution.')],
 80:[('A yield puts 4 in an empty handoff slot. Who may consume that value next?','The consumer at USE',['The producer at MAKE','Either side without coordination'],'Yield moves the consumer to USE and transfers one pending value; the producer must not overwrite it first.'),('One item was produced and none consumed. How many pending items can the slot hold?','1',['0','2'],'The one-slot invariant makes produced minus consumed equal the pending occupancy, either zero or one.'),('After consuming the second square for n=2, must the producer be resumed again?','Yes, to report END',['No; the consumer guesses exhaustion','Yes, to yield a third square'],'The final resume executes ADVANCE then observes i>n. It reports completion without another payload.'),('Would changing squares to decoded records remove the need to define cancellation?','No',['Yes','Only if records are short'],'The payload type can change, but completion, ownership and any cancellation behavior remain protocol decisions.')],
 81:[('Starting with an empty object stack, PUSH 2 then DUP leaves what?','2,2',['2','4'],'PUSH appends 2 and DUP appends a copy of the top value. Addition has not occurred yet.'),('An ADD changes object PC from 2 to 3. Should three internal host checks add three more to object PC?','No',['Yes','Only on a fast host'],'Host checks implement one object transition. The object PC advances once according to object semantics.'),('The object code ends without HALT and PC moves outside its bounds. Is that successful termination?','No; it is a diagnostic',['Yes; end of array means HALT','Only if the stack is nonempty'],'The language declares HALT explicitly. An out-of-range fetch is a failure rather than an implicit halt.'),('PUSH 6; ADD omits the DUP needed by PUSH 6; DUP; ADD. What happens?','Stack underflow',['It returns 12','It returns 6'],'ADD requires two operands but only one was pushed. The object semantics require the intermediate DUP, not merely the intended final arithmetic.')],
 82:[('Why must a fetched MIX word come from current guest memory?','An earlier store may have modified the instruction',['Program words never change','Host code knows the intended opcode'],'Self-modifying return code changes an instruction’s address field. Fetching stale original source would bypass actual guest semantics.'),('A program requests floating-point modifier 0:6. Does the integer subset silently use integer ADD?','No; it rejects unsupported semantics',['Yes','Only if the operands are whole numbers'],'The declared subset excludes floating point. Reinterpreting its modifier as integer arithmetic would falsely claim support.'),('After failed division, may retained A/X bits be used as the quotient and remainder?','No; they are diagnostic context',['Yes; they are unchanged so correct','Only X is valid'],'MIX specifies undefined register information on failure. The model stops and makes no arithmetic-result claim for those bits.'),('If animation is paused for ten seconds, should guest CLOCK gain those seconds?','No',['Yes','Only while a jump is displayed'],'Guest time adds documented instruction costs. Viewer controls and host wall-clock delays are separate quantities.')],
 83:[('A test only checks that A.value is zero. Which distinction can it miss?','The sign of zero',['Whether zero is an integer','The number of decimal zeros printed'],'Both ±0 map to numeric zero, so representation tests must inspect the separate sign.'),('MOVE copies 7 from address 20 to 21, then reads 21 for its next copy. What value is read?','7',['The old value at 21','An arbitrary temporary copy'],'The instruction reads and writes one word at a time; the earlier write is visible to the later read.'),('A rejected load restores A but leaves PC advanced. Does it satisfy this model’s rollback contract?','No',['Yes','Only if memory is unchanged'],'Rollback covers the entire guest snapshot, including control state, not just the destination register.'),('All tests passed at radix 64. Is that alone evidence for every supported radix?','No',['Yes','Only if signs were tested'],'Radix-specific digits and overflow limits differ. Tests at one radix cover that domain and need broader checks for broader claims.')],
 84:[('A traced ADD has already run. Should the logger run ADD again to find its result?','No',['Yes','Only for positive numbers'],'The second ADD would change the guest again. The logger must copy the first committed result.'),('A log stored in guest location 20 collides with a program store to 20. What is missing?','Disjoint storage or an explicit reservation contract',['A faster animation','A second trace entry'],'Without separation, either guest execution or logging can corrupt the other’s data.'),('The host stores more log records but final guest memory and CLOCK agree. Can the declared projection still match?','Yes',['No','Only if the log is empty'],'Host log size is intentionally outside the CPU-only guest-state projection.'),('A JMP at address 0 targets address 1. Was it taken even though PC became 1?','Yes',['No','Only if J is negative'],'A branch may target the sequential next instruction. The decoded jump event, not PC distance, establishes whether it was taken.')],
 85:[('With one buffer still PROCESSING, may input reuse that buffer?','No',['Yes','Only for the final item'],'Processing owns the contents until completion returns the buffer to EMPTY.'),('A buffer is READY and the CPU acquires it. What is its next state?','PROCESSING',['EMPTY','FILLING'],'Acquisition transfers ownership from the ready queue to CPU work; completion later releases it.'),('For two items with I=2,C=3, what two-buffer total includes startup and drain?','8',['6','10'],'The model gives I+C+(n−1)max(I,C)=2+3+3=8. Six would omit boundary work.'),('The known input count is zero. Should the device start an exploratory read?','No',['Yes','Only with two buffers'],'A known empty stream issues no transfers and requires no service time.')],
 86:[('A pool has one EMPTY, one READY and one PROCESSING buffer. How many buffers are owned in total?','3',['2','4'],'The three disjoint states partition the three physical buffers; queue membership does not create a fourth object.'),('All buffers are READY or PROCESSING. What should the input device do next?','Wait for an EMPTY buffer',['Overwrite the oldest READY item','Allocate a new identity invisibly'],'Backpressure preserves unread and active data. The declared fixed-size pool cannot issue input without empty storage.'),('A serial CPU needs 3 time units per item. Can extra buffers make its sustained rate exceed 1/3?','No',['Yes','Only with an empty READY queue'],'Buffers absorb waiting but do not shorten the serial processor’s service time.'),('READY contains identifiers [0,1]. Choosing 1 first respects ownership but violates what?','FIFO ordering',['The byte radix','The number of buffers'],'Both buffers may be ready, yet only selecting the oldest preserves arrival order. Ownership and order are separate invariants.')],
 87:[('Records AB and C are packed into capacity 2. Does the logical record AB have to share a block with C?','No; blocks are AB and C',['Yes; the block must hold all records','Only if a sentinel is inserted'],'The stream fills one block with AB and retains C as the final partial block; record boundaries are tracked separately.'),('Capacity is 2 and the pending buffer contains A. Appending B should do what?','Emit AB and reset the cursor',['Emit only A','Keep a full pending block indefinitely'],'The append reaches capacity exactly, so a full block is emitted and the next free position returns to zero.'),('A two-character stream fills a capacity-two block exactly. Is an extra empty final block emitted?','No',['Yes','Only for an empty record'],'The full block was already flushed; end-of-input flushes only a nonempty pending buffer.'),('Two original records are empty and A. Which lengths preserve that first empty record?','0,1',['1','1,0'],'Payload alone is A in both cases. The ordered length metadata 0,1 identifies the leading empty record.')]
 }
 if small:return q(*help_cases[order][part])
 overrides={
 (65,1):('How does a sign-only load distinguish −0 from +0?','It retains the separate sign',['It changes a magnitude byte','It treats −0 as −1'],'Both magnitudes are zero, but field 0:0 includes the sign. The destination therefore retains the source zero sign.'),
 (65,2):('Which register width is required for a signed five-byte value?','A or X',['Any index register','J'],'A and X have five magnitude bytes. Index registers have only two; J is a nonnegative two-byte continuation address.'),
 (65,3):('Does copying base-64 digits unchanged into base 100 preserve every represented integer?','No',['Yes','Only the sign decides'],'Positional weights change with the radix. For example, digits 2,2 mean 130 in base 64 but 202 in base 100.'),
 (66,1):('Which register bytes supply a store into a two-byte destination field?','The two rightmost bytes',['The first two bytes','The bytes at the destination indices'],'A store aligns the register’s rightmost required bytes with the selected destination interval; it does not select the matching register interval.'),
 (66,2):('What does loading field 0:0 of a negative word produce?','Negative zero',['The full negative integer','Positive zero'],'Field 0:0 contains a sign and no magnitude bytes. Right-alignment fills all five magnitude positions with zero while retaining the minus sign.'),
 (66,3):('A store targets field 2:3. Which positions must remain unchanged?','Sign and bytes 1,4,5',['Only byte 5','No positions'],'A partial store writes only its inclusive destination interval. Position 0 and bytes outside 2:3 are part of its preservation contract.'),
 (67,3):('What is promised when an index-register sum does not fit two bytes?','No defined wrapped result',['A five-byte result','A two-byte remainder with ordinary A overflow'],'MIX leaves index overflow undefined. This teaching interpreter rejects it transactionally rather than pretending it obeys A’s wrapped-arithmetic rule.'),
 (69,1):('What does IOC do if its selected device is busy?','Wait before performing device-specific control',['Cancel the active transfer','Treat the destination as immediately READY'],'IOC first waits for that device to finish; its subsequent control action depends on the device. JBUS and JRED instead test readiness.'),
 (70,1):('How can an instruction refer to a global label defined later?','Resolve the name after collecting locations',['Treat the label as zero','Execute the later instruction first'],'The assembler first records symbol locations, then encodes instruction operands. Source order of a global definition does not require runtime execution.'),
 (70,2):('What does 2B select when several 2H labels occur?','The nearest earlier 2H in source order',['The smallest numeric address','The current or next 2H'],'B means backward relative to the referencing source row. Local-label resolution excludes that row and is not sorted by memory address.'),
 (70,3):('Does an ORIG directive execute when the assembled program runs?','No; it sets the assembly location counter',['Yes; it changes guest PC','Yes; it moves every memory word'],'ORIG influences where later source rows are emitted. It does not emit a CPU instruction or run as part of the guest program.'),
 (73,0):('Which condition makes a mapping on 1…n a permutation?','Every label occurs exactly once as an image',['Every image is positive','Every cycle has length two'],'A permutation is a bijection of the declared finite domain. Positivity alone permits duplicates and missing images.'),
 (73,3):('Why must [2,2,1] be rejected as a permutation of 1,2,3?','Image 2 repeats and image 3 is missing',['It contains a fixed point','Its entries are not sorted'],'Repeated images violate injectivity and a missing label violates surjectivity. The domain check precedes cycle or inverse operations.'),
 (74,3):('Do exhaustive inverse tests through n=7 prove the implementation for every n?','No; the cycle invariant supplies the general argument',['Yes; seven covers every cycle','Only if replay is fast'],'Finite enumeration checks all tested inputs. Saving each original successor before overwrite explains preservation for arbitrary finite cycles.'),
 (75,0):('Under this canonical convention, how are cycles arranged?','Minimum first; cycle minima decrease',['Maximum first; cycle maxima decrease','Minimum first; cycle minima increase'],'Within a cycle no later member beats its minimum. Decreasing minima across cycles make each next cycle start a new left-to-right minimum.'),
 (75,3):('For minimum-first cycles with decreasing starts, which records mark new cycles?','New minima',['New maxima','Every item larger than its predecessor'],'Every cycle starts below all preceding cycle minima. Using maximum records would reconstruct a different convention and can cut inside a cycle.'),
 (76,3):('How is a derangement count converted to a probability under uniform permutations?','Divide by n!',['Divide by n','Use the last alternating correction'],'There are n! equally likely permutations and D_n favorable ones. Signed intermediate corrections are not probabilities or successive surviving lists.'),
 (78,3):('What must change before a one-static-return-slot routine can recurse safely?','Give each live call a distinct continuation and local storage',['Add more source call sites','Use the same return slot more quickly'],'A nested activation would overwrite its caller’s saved continuation. Storage is needed per simultaneously live activation, not just per source call site.'),
 (79,0):('When a suspended coroutine resumes, where does it continue?','At its saved continuation with retained locals',['At its initial entry with cleared locals','At the caller’s first instruction'],'Suspension preserves both control location and selected local values. Restarting would repeat already completed work.'),
 (79,2):('For an empty stream, what distinguishes completion from yielding zero?','A separate END state',['A payload of zero','An arbitrary extra USE event'],'Zero may be valid data. END is a distinct protocol event; n=0 reaches END without any USE or invented payload.'),
 (80,1):('What must USE do after adding the pending value?','Clear the slot and return to WAIT',['Leave the slot full and use it again','Let the producer overwrite the full slot'],'Clearing the one-item slot after exactly one addition prevents duplicate consumption; forbidding a new yield while full prevents loss.'),
 (80,3):('Can zero safely serve as END when a changed producer may yield zero?','No; completion must remain distinct from data',['Yes; the consumer can guess','Yes; if the buffer has one slot'],'A legitimate zero and exhaustion would become indistinguishable. Changing payloads must preserve the explicit completion and ownership contract.'),
 (81,1):('If one ADD handler performs several host operations, how many object instructions executed?','One',['One per host statement','None until the program halts'],'Fetch, validation and stack updates jointly implement one object ADD transition. Host work and object instruction count are separate levels.'),
 (81,3):('What must a new host preserve to run the same object code correctly?','The object instruction semantics',['The original host variable names','The original host execution speed'],'Portability depends on the contract for PUSH, DUP, ADD and HALT. Host representation and dispatch implementation may differ.'),
 (83,3):('What does exhaustive testing of all legal fields establish?','Coverage of that finite field domain',['Correctness of all programs','Proof of every untested arithmetic case'],'Exhaustive field enumeration covers the stated combinations. Other inputs and interactions still need their own specification, tests and invariants.'),
 (84,0):('How should the observer obtain the effect of an executed instruction?','Copy its committed state',['Execute the instruction a second time','Guess it from the final answer'],'Re-execution can duplicate a store or output. Copying the actual committed result observes the guest without repeating its operation.'),
 (84,1):('Why keep trace logs outside writable guest memory?','Guest writes and logging must not corrupt each other',['Host memory makes every program faster','It removes the need to save flags'],'A guest may write any permitted guest location. Disjoint host-side logs prevent unreserved logging from overwriting guest code or data.'),
 (84,2):('Which difference is allowed by this CPU-only tracing equivalence?','Host runtime and log size',['Guest CLOCK','Final guest registers'],'The comparison projects onto guest registers, flags, memory, control and documented guest time. Extra host work is outside that projection.'),
 (84,3):('Can PC advancing to the next address alone prove that no jump occurred?','No; a jump can target that same address',['Yes; all jumps skip a word','Yes; J is always unchanged'],'A taken jump may target the sequential successor. The trace must record the taken decision and opcode, rather than infer it from PC distance.'),
 (85,0):('When can two buffers overlap input and computation safely?','When the device and CPU own different buffers',['Whenever both select buffer 0','Only after all input ends'],'A FILLING buffer belongs to input and must not be read yet. A different READY or CPU-owned PROCESSING buffer allows simultaneous work.'),
 (85,1):('Which event first permits the CPU to acquire an input buffer?','Input completion changes FILLING to READY',['Issuing IN','The CPU requesting the still-busy buffer'],'Starting input does not finish it. READY is reached only at the modeled completion event, after which CPU acquisition is allowed.'),
 (85,2):('Why is n·max(I,C) alone too small for this finite two-buffer schedule?','It omits startup or final drain',['It counts each item twice','It assumes too many buffers'],'The first item cannot be processed before its input arrives, and the final computation must finish. For n≥1 the total is I+C+(n−1)max(I,C).'),
 (86,0):('May one buffer be FILLING and PROCESSING at the same time?','No; each physical buffer has one state and owner',['Yes; if its identifier stays fixed','Yes; with three buffers'],'The state partition is exclusive. More buffers permit work on different objects, not simultaneous device writes and CPU reads of one object.'),
 (86,3):('Does exclusive buffer ownership by itself guarantee FIFO output?','No; oldest-READY selection is also required',['Yes; ownership sorts identifiers','Yes; any READY choice preserves order'],'Ownership prevents conflicting access. The READY queue separately ensures items are selected in arrival order, with no reordering.'),
 }
 if (order,part) in overrides:
  spec=overrides[order,part]
  if small:
   # Help asks the same rule from a concrete smaller setting, not an unrelated final-answer fact.
   stem={65:'Use the smaller word: ',66:'Use one selected field: ',70:'Use the short source listing: ',73:'Use three labels: ',74:'Use a three-cycle: ',75:'Use the short cycle sequence: ',76:'Use three objects: ',78:'Use two nested calls: ',79:'Use the two-item coroutine: ',80:'Use a one-item handoff: ',81:'Use the short stack program: ',83:'Use the small test case: ',84:'Use the short traced call: ',85:'Use two items and two buffers: ',86:'Use the smaller buffer workload: '}.get(order,'Use the smaller example: ')
   spec=(stem+spec[0][0].lower()+spec[0][1:],*spec[1:])
  return q(*spec)
 reasons={
 65:['The final byte is the remainder after division by 64; each complete group of 64 belongs to the preceding byte.','','',''],
 66:['Encode an inclusive field by 8L+R. The factor 8 separates the left endpoint from the right endpoint.','','',''],
 67:['The exact sum is zero, so ADD retains A’s previous negative sign rather than normalizing it to plus.','Multiplication forms the signed ten-byte product. Dividing that exact product by the same nonzero factor recovers the original A value.','Shifts move only byte magnitudes; neither A’s nor X’s separate sign participates.',''],
 68:['The fetched word ends in I, F, C: C identifies the opcode, while F modifies its interpretation and I selects indexing.','JMP from address 0 saves 1. JSJ then changes control without changing that saved J value.','JNOV clears an on overflow toggle without jumping; if it was off it jumps. Either outcome leaves the toggle off.','Transactional rejection restores PC together with registers, flags and memory; a failed load has no committed effect.'],
 69:['Input has not completed while FILLING, so the CPU cannot treat the destination as ready.','','CHAR encodes the magnitude into decimal digit characters; NUM decodes each modulo ten and reconstructs the same representable magnitude.','LDA costs 2u, INCA costs 1u and STA costs 2u. Their sequential cost is 2+1+2=5u, independently of host runtime.'],
 70:['START is assigned the current assembly location immediately after ORIG; directive and source-line numbering do not consume memory words.','','',''],
 71:['Field 5:5 selects only the final destination byte. The sign and first two address bytes lie outside it and survive unchanged.','The supported MIXAL grammar evaluates left to right: perform the addition before multiplying the accumulated value.','The assembler emits the literal value in a separate memory word and encodes that word’s address as the ADD operand.','CON places a word in memory during assembly. It is not itself an opcode, and the guest only executes locations reached by control flow.'],
 72:['Each ADD visits the next input word exactly once; summing the signed inputs gives the stored TOTAL.','I1 starts at minus the input length and increases once per element. After that many increments it reaches zero, making J1N untaken.','Initialization costs 2u; each item costs ADD 2u + INC1 1u + J1N 1u; STA and HLT add 3u. Hence 4n+5u.','The body executes ADD before its branch test. A zero initial count therefore does not skip the body; empty input needs a pretest.'],
 73:['','Apply p first and use that image as the argument to q. Reversing those lookups generally changes the composition.','Following each unvisited image chain returns to its start; fixed points contribute singleton cycles.',''],
 74:['The inverse image of 1 is the unique original index whose stored image equals 1.','Read the original successor before replacing the cell; the saved value is the only onward link after the overwrite.','All valid input labels are positive, so a negative sign is spare representation reserved for processed inverse edges.',''],
 75:['','Each new left-to-right minimum begins exactly one canonical cycle. Count those records, including the first item.','Among the first j uniformly ordered distinct elements, each is equally likely to be smallest. The jth is smallest with probability 1/j.',''],
 76:['The signed sum subtracts single fixed-point events, adds pair intersections, and continues; only permutations with no fixed points retain coefficient one.','For r>0 fixed points, the total coefficient is (1−1)^r=0. Such a permutation cancels completely from the derangement count.','The empty set has one permutation, and it fixes no objects. Thus its derangement count is one.',''],
 77:['TWICE saves the original A in TEMP and adds it once, so its result is twice the supplied entry value.','STJ writes only positions 0:2. Opcode C in byte 5 remains 39, and the JSJ modifier is also preserved.','A second live activation would overwrite the first saved return address. A static slot supports only nonoverlapping activations.','The call is at address 201. Ordinary JMP saves the following address 202, which STJ patches into the eventual JSJ return.'],
 78:['Solve the strict inequality k(B−C)>B+L; the smallest integer above the resulting ratio is the first actual space saving.','Each call incurs 4u beyond useful body work; two calls therefore add 2·4=8u.','A is the result register and changes from x to 2x. Only registers explicitly promised preserved must retain entry values.',''],
 79:['','The yield leaves the counter unchanged and saves ADVANCE. Resuming there increments it before MAKE can emit the next square.','','Only one component executes each semantic transition; cooperative suspension is not simultaneous execution.'],
 80:['The consumer adds every delivered square once, so its completed total equals 1²+…+n².','','There is one USE per yielded square. The final resume advances beyond n and reports END without an extra USE.',''],
 81:['Follow PUSH, DUP and ADD in order; ADD replaces the top two entries by their sum, and HALT preserves the resulting stack.','','ADD must remove two operands before pushing a sum, so fewer than two entries is underflow.',''],
 82:['ENTA establishes A, INCA adds three, and STA copies that resulting value into location 20.','The supported CPU subset excludes opcodes 34–38. Their readiness and ownership concepts use a separate device scheduling model.','Division by zero reaches an undefined-result stop with overflow. Retained predivision bits are diagnostic context, not a quotient.','The guest clock adds source-defined costs for the executed sum instructions: 2u setup + 16u loop + 3u store/halt = 21u.'],
 83:['MIX stores the sign separately, giving +0 and −0 even though numeric comparison treats them equally.','MOVE copies sequentially. The first write replaces the next source, so later copies propagate the original value 7.','The diagnostic contract rolls back the whole preinstruction snapshot, including PC, rather than committing a partial step.',''],
 85:['','','','The input count is known in advance, so issuing stops when that count is reached. Pending processing then drains without another read.'],
 86:['','Input may acquire only EMPTY storage. Choosing FILLING or PROCESSING storage would overwrite an active owner’s data.','Two buffers already overlap one serial device with one serial CPU at the slower service rate. A third cannot reduce constant-service completion time here.',''],
 87:['Read the final emitted block’s valid payload length. Unused capacity is padding, not additional characters.','This policy flushes only on reaching capacity or a final partial block. A logical record boundary alone does not force a flush.','The number of nonempty blocks is ceil(total payload/capacity); an exactly full final block emits no extra empty block.','Concatenate valid block payloads, then split at cumulative record lengths. Block count or first characters cannot recover arbitrary record boundaries.']}
 result=copy.deepcopy(original); result['explanation']=reasons[order][part]
 misconception={
 (67,2):['Yes, on every shift','Only circular shifts move signs'],
 (68,2):['Yes, because the jump was not taken','It becomes the comparison indicator'],
 (68,3):['Yes, by one','Only the destination register rolls back'],
 (69,0):['Yes, immediately after input is issued','Yes, if it uses a second index register'],
 (71,0):['Yes, because every store changes a full word','Only if the new opcode is nonzero'],
 (71,3):['Yes, every source directive executes','Only constants after END execute'],
 (72,3):['Yes, the first ADD is automatically skipped','Only if TOTAL initially equals zero'],
 (75,2):['1/2','1'],
 (77,2):['Yes, each call overwrites it safely','Only if both calls use the same input'],
 (78,2):['Yes, every register is callee-preserved','Only if TEMP is writable'],
 (79,3):['Yes, separate saved PCs imply two CPUs','Only while the handoff slot is full'],
 (82,1):['Yes, including tape positioning','Only IN and OUT are implemented'],
 (82,2):['Yes, it returns zero','Only the old X bits are a valid remainder'],
 (83,2):['Yes, PC advances despite rejection','Only comparison and overflow change'],
 (85,3):['Yes, one speculative read is always required','Only when the last buffer is full'],
 (86,2):['Yes, each buffer adds processing capacity','Only if the CPU service time is unchanged'],
 (87,1):['Yes, every record ends a physical block','Only if the next record is nonempty']}
 if (order,part) in misconception:result['choices']=[original['choices'][original['correctIndex']],*misconception[order,part]];result['correctIndex']=0
 assert result['explanation'],(order,part)
 return result

def rotated_check(check,offset):
 c=copy.deepcopy(check); xs=c['choices']; offset%=len(xs); c['choices']=xs[offset:]+xs[:offset]; c['correctIndex']=(-offset)%len(xs); return c

# Learner-facing symbol readings, intentionally separate from renderer instructions.
LEARNER_NOTATION = {(65, 0): 'In the formula, s is +1 or −1 for the separate sign, d_j is the digit in byte position j, and j '
          'runs from 1 to 5. The sum adds the five place-value contributions; it does not add the position '
          'labels.',
 (66, 0): 'L names the first selected position and R the last, including both endpoints; F is the single '
          'byte that encodes that pair. For example, F=20 decodes to L=2 and R=4.',
 (67, 0): 'V denotes the signed operand value obtained from the instruction’s selected memory field. W is '
          'one more than the largest five-byte magnitude; mod W keeps the remainder after removing '
          'complete groups of W.',
 (67, 1): 'A:X means the magnitude formed by placing A’s five bytes before X’s five bytes. N is that full '
          'magnitude, q the quotient magnitude, and r the nonnegative remainder magnitude.',
 (67, 2): 'In the comparison formula, R means the selected register word and M the memory word; sign of '
          'their field difference returns less, equal, or greater.',
 (68, 0): 'PC is the program counter: the address of the instruction to fetch. The symbol ±AA is its '
          'signed address field, I selects an index register, and rI_I means that selected register’s '
          'contents. M is the resulting effective address or numeric operand, depending on the '
          'instruction.',
 (68, 1): 'Here P is the value of PC before the instruction executes, so P+1 is the caller’s following '
          'instruction. J stores that continuation; M is the jump destination.',
 (68, 2): 'O names the overflow flag, and the subscript after means its value once the instruction has '
          'finished.',
 (68, 3): 'S denotes the complete machine snapshot, including registers, flags, control, and memory; '
          'equality here requires every component to remain unchanged.',
 (69, 1): 'In busy(d,t), d identifies the device, t is the current simulated time, and t_completion(d) is '
          'when its pending operation finishes.',
 (69, 3): 'The letter u is one MIX time unit. In the cost sum, i identifies an instruction kind, f_i '
          'counts how often it executes, c_i is its cost per execution, and T_waiting is additional '
          'waiting time. Thus four additions at 2u each contribute 4×2u=8u.',
 (75, 2): 'C_n is the number of cycles in a permutation of n labels; E[C_n] means its average over all n! '
          'equally likely permutations. H_n is the harmonic sum 1+1/2+⋯+1/n.',
 (76, 0): 'D_n denotes the number of n-label permutations with no fixed point. The index k is the number '
          'of labels required to stay fixed in one correction; (−1)^k alternates addition and subtraction.',
 (78, 2): 'The symbol π_preserved means “read only the fields promised unchanged.” The equation compares '
          'those fields at entry and exit, not the whole state or the changed result register.',
 (79, 2): 'P and C name the producer’s and consumer’s saved control locations. The counter i identifies '
          'the next square candidate, and n is the number of requested squares.',
 (80, 0): 'T_k is the consumer total after k items have been consumed; i is the square’s sequence index. '
          'For k=2, the equation reads T_2=1²+2²=5.',
 (81, 0): 'In the state formula, pc is the object program’s next instruction position and σ is its stack '
          'sequence, written from bottom to top. The symbol ‖ appends a sequence: σ‖[v] adds v at the top. '
          'The labeled arrow denotes one executed object instruction.',
 (81, 1): 'The displayed tail [a,b] has a below b on the stack. ADD removes both, computes a+b, and '
          'appends that one sum to the untouched older stack σ.',
 (82, 0): 'In S, M is memory, O is overflow, C is the comparison indicator, and t is guest elapsed time. '
          'I_1 through I_6 are index-register contents; they are distinct from an instruction’s index '
          'selector.',
 (84, 0): 'The symbol π_guest means “keep only the guest machine fields being compared.” S_traced and '
          'S_baseline are the two complete run snapshots; the observer’s separate log is omitted by that '
          'projection.',
 (84, 2): 'This displayed tuple defines exactly what π reads: registers, control, flags, memory, halt '
          'status and guest time. Equality means equality of these fields individually.',
 (84, 3): 'In the event tuple, I is the fetched instruction word, M its effective address, taken says '
          'whether its branch was followed, and S_after is the committed resulting snapshot.',
 (85, 0): 'In the formula, n is the number of items, I is input time per item, C is processing time per '
          'item, T_1 is total time with one buffer, and T_2 with two. Here n=4, I=3, C=5: T_1=32 and '
          'T_2=3+5+3×5=23.',
 (86, 0): 'E, F, R and P count buffers in the four named states; k counts all buffers. These are counts, '
          'not buffer identities: moving one buffer from FILLING to READY decreases F by one and increases '
          'R by one.',
 (86, 2): 'I is the input service time per item and C the processing service time per item. Throughput '
          'counts completed items per time unit, so its limiting rate is the smaller of 1/I and 1/C.',
 (87, 0): 'Each r_i is one logical record, m is the number of records, and ‖ means concatenate their '
          'characters in order. Record identity is retained separately in the length list.',
 (87, 1): 'The cursor c counts characters already consumed. Input[0:c] means the prefix starting at '
          'position zero and stopping just before c; ‖ joins the emitted and still-pending character '
          'sequences.',
 (87, 2): 'N is the total number of payload characters and B the physical block capacity. The ceiling '
          'brackets round N/B up to the next whole block; for N=8 and B=5, two blocks are needed.'}

HELPER_CONNECTIONS = {65: 'In either example, byte position chooses the power of the base and the digit counts copies of that '
     'place value. The separate sign applies to their whole sum.',
 66: 'The same field rule applies to the larger word: loading moves selected source bytes to the right, '
     'while storing changes only selected destination positions.',
 67: 'Compare the register result and the flag separately. The same arithmetic rule applies to the larger '
     'operands; changing a magnitude does not automatically clear a historical flag.',
 68: 'The next register value comes from this fetched instruction and its old operands. In the larger '
     'trace, read PC, decode the fields, and evaluate the selected operation in the same order.',
 69: 'A filled buffer becomes readable only at completion. The larger schedule repeats that ownership '
     'change for more items; the device and CPU still cannot own the same data together.',
 70: 'The numeric address comes from the label’s emitted location, not its printed line number. Moving the '
     'origin changes addresses but preserves which source definition a label selects.',
 71: 'Each field placement uses the word produced so far. In the larger construction, later placements '
     'likewise replace only their selected positions.',
 72: 'The short input uses the same loop: A totals the consumed prefix and I1 determines which input comes '
     'next. The final branch still executes when the last item has been added.',
 73: 'A two-arrow composition reads the first image before the second. The larger permutation obeys the '
     'same lookup order, and each disjoint cycle closes on its own start.',
 74: 'Saving the successor protects the path before a cell is overwritten. The same local '
     'read-before-write rule reverses each cycle in the larger permutation.',
 75: 'A newly encountered minimum begins a canonical cycle. The larger sequence has more positions, but '
     'the same record test determines exactly where parentheses return.',
 76: 'Follow one permutation through the alternating fixed-point corrections. A permutation with a fixed '
     'point cancels out; one without any fixed point retains coefficient one.',
 77: 'The smaller call must return to its saved following instruction as well as double A. The larger call '
     'changes the input value, not the return-address preservation rule.',
 78: 'Compare all copied body words with one shared body plus linkage and one call-site cost per use. The '
     'larger body uses the same accounting, with different numerical constants.',
 79: 'After a yield, the saved producer location is ADVANCE and its counter has not yet changed. The next '
     'resume advances that retained counter rather than recreating its first value.',
 80: 'Each square fills the handoff slot once and USE empties it once. The larger stream repeats this '
     'exactly-once exchange before its final END message.',
 81: 'The visible stack is the object program’s stack, not the host’s local variables. More instructions '
     'still use the same append, duplicate and two-operand addition rules.',
 82: 'The small trace uses the same signed words, fetched instructions and diagnostic contract as the '
     'larger MIX program. Check both changed fields and promised unchanged fields.',
 83: 'A numerical answer alone misses representation and side effects. Apply the same complete-state '
     'comparison to signs, untouched bytes, flags and control in the larger test.',
 84: 'The paired runs must agree on guest fields after each committed instruction. The extra observer log '
     'may grow, but it does not execute another guest instruction.',
 85: 'The second buffer allows input and processing of different items to overlap. Startup and the last '
     'processing interval remain real time in both examples.',
 86: 'A buffer moves between ownership states while its identity stays fixed. The READY queue separately '
     'preserves item order; adding empty buffers does not create a faster processor.',
 87: 'Logical records remain the same character stream even when their characters cross block boundaries. '
     'Join valid payloads, then use the stored record lengths to recover the original records.'}
HELPER_NOTATION = {(66, 0): 'L and R are inclusive source positions; F=8L+R encodes them. This smaller load uses F=45, so '
          'L=5 and R=5: it selects only the last byte, not the sign.',
 (85, 0): 'Here n=2 items, input time I=2 and processing time C=3. One buffer takes 2 × (2+3)=10; two '
          'buffers take 2 + 3+(2−1)×3=8. Startup and final processing remain included.',
 (87, 2): 'Here the records AB and C contain N=3 characters and each block holds B=2. The ceiling of 3/2 '
          'is 2 blocks; the final block has only one valid character.'}

def helper_context(n,part,model,states):
 data=states[0].get('data',{})
 if n==65:return f"This smaller word has magnitude {model['input']} in base {model['base']}. The numbers 1 through 5 name positions; the digits inside them give the stored value."
 if n==66:
  field=model['field']; return f"This smaller {model['operation']} selects field {field//8}:{field%8}, encoded by F={field}. Position 0 is the sign; positions 1–5 are bytes."
 if n in (67,68,72,77,82) and 'pc' in data:return f"This run starts at PC={data['pc']} with A={data['A']['value']}. PC names the next instruction address; A holds the current signed numeric value."
 if n in (69,85,86) and 'schedule' in model:
  history=model['schedule']; return f"This smaller schedule has {len(history[0]['states'])} buffer(s) and {history[-1]['issued']} input item(s). Buffer numbers identify storage; item numbers identify the data passing through it."
 if n==70:return f"This source begins emitting at address {model['listing'][0]['address']}. Its first source line number is {model['listing'][0]['line']}; those two numbers have different meanings."
 if n in (79,80):return f"This producer requests {model['n']} squares. The counter i chooses a square; the handoff holds that square's value; the consumer total adds only consumed values."
 if n==81:return 'The smaller object code is '+ '; '.join(op+((' '+str(arg)) if arg is not None else '') for op,arg in model['code'])+'. The rightmost stack entry is its top.'
 if n==87:return f"The records are {', '.join(repr(x) for x in model['records'])}, with lengths {model['recordLengths']}; each physical block holds {model['capacity']} characters."
 return states[0]['caption']+' '+HELPER_CONNECTIONS[n]

def author():
 lessons=[]
 for meta in META:
  n=meta['order']; passages=[]
  for part,(title,body,formula) in enumerate(LESSON_TEXT[n]):
   notation=LEARNER_NOTATION.get((n,part),'')
   if notation:
    first,sep,rest=body.partition('\n\n'); body=first+' '+notation+sep+rest
   if n in (72,77) and part==0:
    program=SUM if n==72 else CALL
    body+='\n\nOriginal executable listing (label | operation | operand):\n\n'+ '\n\n'.join(f'{lab or "·"} | {op} | {arg}' for lab,op,arg in program)
   fs,model,check=scenario(n,part); hs,hm,hc=scenario(n,part,True)
   check=passage_check(n,part,False,model,check); hc=passage_check(n,part,True,hm,hc)
   # Smaller help is independently executed, never aliases the main trace.
   if notation: fs[0]['teachingExplanation']=fs[0]['caption']+' '+notation
   helper_note=HELPER_NOTATION.get((n,part),notation)
   if helper_note: hs[0]['teachingExplanation']=hs[0]['caption']+' '+helper_note
   helpobj={'intro':helper_context(n,part,hm,hs),'model':hm,'states':hs,'steps':[{'action':'read-the-current-state','text':state.get('teachingExplanation',state['caption'])} for state in hs],'connection':HELPER_CONNECTIONS[n],'check':rotated_check(hc,part+1)}
   demo={'id':f'{meta["id"]}-p{part+1}-demo','title':title,'model':model,'states':fs,'transitions':[{'from':a['id'],'to':b['id'],'action':f'execute-transition-{i+1}','explanation':b['caption']} for i,(a,b) in enumerate(zip(fs,fs[1:]))],'check':rotated_check(check,part),'simplerHelp':helpobj}
   passage={'id':f'operation-{part+1}','title':title,'text':body,'formula':formula,'demonstration':demo}
   if n in (72,77) and part==0:
    halt=next(i for i,st in enumerate(fs) if st['data'].get('opcode')==5)
    # Text after the definition is: worked summary, listing heading, each source row, formula.
    passage['visualLinks']={'definition':0,'paragraphs':[halt,0,*[x['frameIndex'] for x in model['sourceVisualLinks']],halt],'takeaway':halt}
   passages.append(passage)
  lessons.append({'id':meta['id'],'order':n,'title':('Build a faithful integer MIX subset' if n==82 else meta['title']),'source':{'book':'Donald E. Knuth, The Art of Computer Programming, Volume 1, third edition','section':', '.join('§'+x for x in meta['sections']),'pdfPages':PAGE_RANGES[n],'pagination':'one-based supplied ebook, not printed'},'provenance':'Original explanations, inputs, diagrams, assessments and executable models after the cited concepts. No source programs, textbook prose, page images or private source files are included.','scope':'Four operation-focused demonstrations with separately computed smaller examples. Integer MIX and MIXAL have explicit supported subsets; coroutine, interpreter and device-scheduling models are named abstractions. Finite checks are implementation evidence, not proofs of all inputs.','sections':[{'id':'worked-concepts','title':meta['title'],'passages':passages}]})
 output=ROOT/'content/fullbook/batch-C.json'; output.parent.mkdir(parents=True,exist_ok=True); payload=json.dumps(lessons,ensure_ascii=False,separators=(',',':'))+'\n'
 if '--check' in sys.argv:
  assert output.read_text()==payload, 'Regenerated batch C differs from checked-in content'
 else: output.write_text(payload)
 print(f'Authored {len(lessons)} lessons, {sum(len(l["sections"][0]["passages"]) for l in lessons)} focused demonstrations: {output}')
 return lessons

if __name__=='__main__':
 if '--test' in sys.argv: tests()
 else: tests(); author()
