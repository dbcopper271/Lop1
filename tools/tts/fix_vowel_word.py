import json,os,sys,subprocess
sys.argv=[sys.argv[0]]
exec(open('gen.py',encoding='utf-8').read().split("phr = json.load")[0])
def core(y,thr=-30):
    if len(y)<2: return 0,len(y)
    e,f=env(y); m=e.max()+1e-9; db=20*np.log10(e/m); on=np.where(db>thr)[0]
    return (on[0]*f,(on[-1]+1)*f) if len(on) else (0,len(y))
def pitch(y):
    y=y/(np.abs(y).max()+1e-9); win=int(SR*0.04); hop=int(SR*0.008); f0=[]
    for st in range(0,max(1,len(y)-win),hop):
        seg=y[st:st+win]*np.hanning(win)
        if np.sqrt(np.mean(seg**2))<0.05: continue
        ac=np.correlate(seg,seg,'full')[win-1:]; lo,hi=int(SR/350),int(SR/80)
        if hi>=len(ac): continue
        pk=lo+int(np.argmax(ac[lo:hi]))
        if ac[pk]>0.3*ac[0]: f0.append(SR/pk)
    return np.array(f0)
def trend(y):
    f=pitch(y)
    if len(f)<4: return '?',0,0
    h,t=np.mean(f[:max(2,len(f)//3)]),np.mean(f[-max(2,len(f)//3):])
    return ('lên' if t>h*1.05 else 'xuống' if t<h*0.94 else 'phẳng'),round(h),round(t)
def finish(y,lead=0.03,tail=0.11,fin=0.008):
    y=y/(np.abs(y).max()+1e-9)*0.97
    fi=int(SR*fin); y[:fi]*=np.linspace(0,1,fi); fo=int(SR*0.03); y[-fo:]*=np.linspace(1,0,fo)
    return np.concatenate([np.zeros(int(SR*lead),np.float32),y,np.zeros(int(SR*tail),np.float32)])
def stretch(y,target,floor=0.7):
    s,e=core(y); ms=(e-s)/SR
    if ms<=0: return y
    tempo=max(floor,min(1.0,ms/target))
    if tempo>=0.98: return y
    z=subprocess.run(['ffmpeg','-loglevel','error','-f','f32le','-ar',str(SR),'-ac','1','-i','-','-filter:a',f'atempo={tempo:.3f}','-f','f32le','-'],input=y.astype(np.float32).tobytes(),capture_output=True).stdout
    return np.frombuffer(z,dtype=np.float32).copy()
def get_vowel(word,initial_frac):
    cands=[]
    for sp in [0.85,0.8,0.9,0.82,0.88,0.78,0.86]:
        x=gen(f'Cô đọc {word} to nhé.',sp); h,toks,ts=hear(x); w=clean(h).split()
        if word not in w: continue
        i=w.index(word)
        if len(ts)<=i+1: continue
        st=refine_start(x,ts[i]); en=refine_start(x,ts[i+1])
        if en-st<int(SR*0.12): continue
        seg=x[st:en]; cs,ce=core(seg)
        if ce-cs<int(SR*0.1): continue
        seg=seg[cs:ce]; cut=int(len(seg)*initial_frac); vow=seg[cut:]
        if len(vow)>=int(SR*0.12): cands.append(vow)
    return cands

V=json.load(open('work_voice.json',encoding='utf-8')); rep=json.load(open(REP,encoding='utf-8'))
# 'a' phẳng — lấy phần đầu (trước khi cao độ tụt tự nhiên), từ na/ma/ba/la
picks=[]
for wd in ['na','ma','ba','la','va']:
    for vow in get_vowel(wd,0.33):
        front=vow[:int(len(vow)*0.62)]   # phần đầu, phẳng hơn
        tr,h0,t0=trend(front)
        picks.append((abs(t0-h0),front,wd,tr,h0,t0))
picks.sort(key=lambda p:p[0])   # phẳng nhất
if picks:
    front=picks[0][1]; y=finish(stretch(front,0.34))
    V['a']=mp3(y); rep['a']={'mode':'short','ok':True,'heard':f"(tách từ {picks[0][2]}, phẳng)",'v':8,'dur':round(len(y)/SR,2)}
    print(f"a ← {picks[0][2]}: {picks[0][3]} {picks[0][4]}→{picks[0][5]}Hz, {round(len(y)/SR,2)}s | top3:",[(p[2],p[3],p[4],p[5]) for p in picks[:3]])
# 'á' (ă) sắc lên — từ cá/má/lá/tá
pa=[]
for wd in ['cá','má','lá','tá','sá']:
    for vow in get_vowel(wd,0.42):
        tr,h0,t0=trend(vow)
        if tr=='lên': pa.append((abs(len(vow)/SR-0.26),vow,wd,tr,h0,t0))
if pa:
    pa.sort(key=lambda p:p[0]); vow=pa[0][1]; y=finish(stretch(vow,0.30))
    V['á']=mp3(y); rep['á']={'mode':'short','ok':True,'heard':f"(tách từ {pa[0][2]}, sắc)",'v':8,'dur':round(len(y)/SR,2)}
    print(f"á ← {pa[0][2]}: {pa[0][3]} {pa[0][4]}→{pa[0][5]}Hz, {round(len(y)/SR,2)}s")
else: print("á: chưa lấy được thanh lên")
json.dump(V,open('work_voice.json','w',encoding='utf-8'),ensure_ascii=False); json.dump(rep,open(REP,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
