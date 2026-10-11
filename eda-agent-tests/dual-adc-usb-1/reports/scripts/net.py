import re,sys,collections
def parse(t):
    toks=re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+',t); st=[[]]
    for k in toks:
        if k=='(': st.append([])
        elif k==')': x=st.pop(); st[-1].append(x)
        else: st[-1].append(k.strip('"'))
    return st[0][0]
def get(n,key): return [c for c in n if isinstance(c,list) and c and c[0]==key]
def val(n,key):
    g=get(n,key); return g[0][1] if g and len(g[0])>1 else ''
T=parse(open(sys.argv[1]).read())
comps={val(c,'ref'):(val(c,'value'),val(c,'footprint')) for c in get(get(T,'components')[0],'comp')}
pins=collections.defaultdict(dict)  # ref -> pin -> (net, pinfunction)
nets={}
for n in get(get(T,'nets')[0],'net'):
    name=val(n,'name'); nets[name]=[]
    for nd in get(n,'node'):
        r,p,f=val(nd,'ref'),val(nd,'pin'),val(nd,'pinfunction'); pins[r][p]=(name,f); nets[name].append((r,p,f))
