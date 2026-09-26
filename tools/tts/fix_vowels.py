"""Nguyên âm: dựng lại tự nhiên (không kéo 2x), chọn bản điển hình, rồi kéo giãn VỪA PHẢI (tempo>=0.6) tới ~0.42s.
Có lead 0.04s, tail 0.12s, fade 25ms để êm tai."""
import json, os, sys, subprocess, base64
sys.argv=[sys.argv[0]]
D=os.path.dirname(os.path.abspath(__file__))
exec(open('gen.py',encoding='utf-8').read().split("phr = json.load")[0])
def core_ms(y):
    e,f=env(y); db=20*np.log10(e/(e.max()+1e-9)); on=np.where(db>-30)[0]
    return round((on[-1]-on[0]+1)*f/SR*1000) if len(on) else 0
def mfcc(y):
    import numpy.fft as fft
    y=y/(np.abs(y).max()+1e-9); win=int(SR*0.025); hop=int(SR*0.010); n=1024
    mel_f=2595*np.log10(1+np.linspace(0,SR/2,n//2+1)/700); fr=[]
    for st in range(0,max(1,len(y)-win),hop):
        seg=y[st:st+win]*np.hanning(win); sp=np.abs(fft.rfft(seg,n))**2
        ed=np.linspace(mel_f.min(),mel_f.max(),28); fb=np.zeros((26,n//2+1))
        for i in range(26):
            lo,ce,hi=ed[i],ed[i+1],ed[i+2]; fb[i]=np.clip((mel_f-lo)/(ce-lo+1e-9),0,None)*np.clip((hi-mel_f)/(hi-ce+1e-9),0,None)
        fr.append(np.real(fft.rfft(np.log(fb@sp+1e-9)))[:13])
    return np.array(fr) if fr else np.zeros((1,13))
def dtw(A,B):
    if len(A)<2 or len(B)<2: return 9.9
    Dm=np.full((len(A)+1,len(B)+1),1e9); Dm[0,0]=0
    for i in range(1,len(A)+1):
        for j in range(1,len(B)+1): Dm[i,j]=np.linalg.norm(A[i-1]-B[j-1])+min(Dm[i-1,j],Dm[i,j-1],Dm[i-1,j-1])
    return Dm[-1,-1]/(len(A)+len(B))
def fade(y,lead=0.04,tail=0.12):
    y=y/(np.abs(y).max()+1e-9)*0.9
    fi=int(SR*0.025); y[:fi]*=np.linspace(0,1,fi); fo=int(SR*0.025); y[-fo:]*=np.linspace(1,0,fo)
    return np.concatenate([np.zeros(int(SR*lead),np.float32),y,np.zeros(int(SR*tail),np.float32)])
def stretch(y,target=0.42,floor=0.60):
    ms=core_ms(y)/1000
    if ms<=0: return y
    tempo=max(floor,min(1.0,ms/target))
    if tempo>=0.98: return y
    z=subprocess.run(['ffmpeg','-loglevel','error','-f','f32le','-ar',str(SR),'-ac','1','-i','-','-filter:a',f'atempo={tempo:.3f}','-f','f32le','-'],input=y.astype(np.float32).tobytes(),capture_output=True).stdout
    return np.frombuffer(z,dtype=np.float32).copy()
def natural(s, word='i' if False else None):
    txt = s
    cands=[]
    for att in range(8):
        for carrier in ['Bây giờ cô đọc {}.','Cô đọc âm {} nhé.','Bây giờ cô đọc {} nhé.']:
            x=gen(carrier.format(txt),[0.85,0.9,0.8,0.82][att%4]); h,toks,ts=hear(x); w=clean(h).split(); pre=clean(carrier.split('{}')[0]).split()
            if len(w)>len(pre) and w[:len(pre)]==pre and len(ts)>len(pre):
                i=len(pre); st=max(0,refine_start(x,ts[i])-int(SR*0.012))
                en=len(x) if carrier.endswith('{}.') else (refine_start(x,ts[i+1]) if len(ts)>i+1 else len(x))
                seg=x[st:en]
                # cắt gọn phần có tiếng
                e,f=env(seg); db=20*np.log10(e/(e.max()+1e-9)); on=np.where(db>-32)[0]
                if len(on): seg=seg[max(0,on[0]*f-int(SR*0.01)):min(len(seg),(on[-1]+1)*f+int(SR*0.02))]
                ms=core_ms(seg)
                if 150<=ms<=360: cands.append(seg)
        if len(cands)>=5: break
    if len(cands)<3: return None
    fm=[mfcc(c) for c in cands]
    best=min(range(len(cands)),key=lambda i:sum(dtw(fm[i],fm[j]) for j in range(len(cands)) if j!=i))
    return cands[best]
V=json.load(open('work_voice.json',encoding='utf-8')); rep=json.load(open(REP,encoding='utf-8'))
import re
app=open('/home/claude/lop1/src/app.html',encoding='utf-8').read()
VOWELS=[s for c,s in re.findall(r"\{ c: '([^']+)', s: '([^']+)', w:",app)[:29] if s in ['a','á','ớ','e','ê','o','ô','ơ','u','ư']]
for s in VOWELS:
    y=natural(s)
    if y is None: print('--',s,'chưa dựng được'); continue
    y2=fade(stretch(y)); V[s]=mp3(y2); rep[s]={'mode':'short','ok':True,'heard':'(nguyên âm tự nhiên + giãn nhẹ)','v':7,'dur':round(len(y2)/SR,2),'ms':core_ms(y2)}
    print(f"OK {s}: lõi {core_ms(y)}ms → sau giãn {core_ms(y2)}ms (clip {round(len(y2)/SR,2)}s)",flush=True)
json.dump(V,open('work_voice.json','w',encoding='utf-8'),ensure_ascii=False); json.dump(rep,open(REP,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print('done vowels')
