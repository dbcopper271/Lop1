"""Câu dài score<0.7: dựng lại với lead-in 'Rồi, cô đọc: ' chậm, thử nhiều lần, giữ bản điểm cao nhất.
Câu kết bằng từ dễ rớt thanh: đọc thêm 'nhé' rồi cắt bỏ để giữ thanh cuối."""
import json, os, sys, re, difflib
sys.argv=[sys.argv[0]]
D=os.path.dirname(os.path.abspath(__file__))
exec(open('gen.py',encoding='utf-8').read().split("phr = json.load")[0])
def refine_end(x,t):
    e,f=env(x); k=np.convolve(e,np.ones(3)/3,'same')
    lo,hi=max(0,int((t-0.12)/0.005)),min(len(k)-1,int((t+0.05)/0.005))
    if hi<=lo: return int(t*SR)
    return (lo+int(np.argmin(k[lo:hi])))*f
def score(target,body):
    t,b=target.split(),body.split(); sm=difflib.SequenceMatcher(None,t,b)
    return sum(m.size for m in sm.get_matching_blocks())/max(len(t),1), b==t
def make(text,tries=14):
    target=clean(text); best=(-1,None,'')
    body_txt=re.sub(r'[.!?]+$','',text.strip())
    for att in range(tries):
        sp=[0.82,0.78,0.86,0.8,0.84][att%5]
        tail = att%3==2   # thỉnh thoảng thêm 'nhé' để giữ thanh cuối
        src=LEAD+(body_txt+' nhé.' if tail else text)
        x=gen(src,sp); h,toks,ts=hear(x); w=clean(h).split()
        body=' '.join(w[NL:]) if len(w)>NL else clean(h)
        tn=clean(text).split()
        if tail and w and w[-1]=='nhé': body=' '.join(w[NL:-1])
        sc,exact=score(target,body)
        if len(ts)>NL:
            st=max(0,refine_start(x,ts[NL])-int(SR*0.02))
            en = refine_end(x, ts[NL+len(tn)]) if (tail and len(ts)>NL+len(tn)) else len(x)
            y=tidy(x[st:en],tail=0.11)
        else: y=tidy(x)
        if sc>best[0]: best=(sc,y,body)
        if exact and not tail: break
    return best
V=json.load(open('work_voice.json',encoding='utf-8')); rep=json.load(open(REP,encoding='utf-8'))
todo=[k for k,e in rep.items() if e.get('mode')=='long' and (e.get('score') or 1)<0.7]
print('todo',len(todo)); up=0
for p in todo:
    sc,y,body=make(p)
    if y is not None and sc>=rep[p].get('score',0):
        V[p]=mp3(y); rep[p]['score']=round(sc,3); rep[p]['heard']=body; rep[p]['dur']=round(len(y)/SR,2)
        if sc>rep[p].get('score',0)-1: up+=1
    print(f"{sc:.2f}  {p}  → {body}",flush=True)
json.dump(V,open('work_voice.json','w',encoding='utf-8'),ensure_ascii=False); json.dump(rep,open(REP,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print('processed',len(todo))
