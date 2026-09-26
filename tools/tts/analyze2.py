"""So sánh clip đang dùng với bản dựng lại tươi (cùng pipeline) để tách 'clip lỗi' khỏi 'máy nhận dạng không chấm được âm lẻ'.
Đo cả độ dài lõi tiếng và khoảng cách phổ (MFCC) giữa clip và cụm bản tươi."""
import json, os, sys, subprocess, base64
sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen.py'), encoding='utf-8').read().split("phr = json.load")[0])
V = json.load(open(os.path.join(D, 'voice_latest.json'), encoding='utf-8'))
import re
app = open('/home/claude/lop1/src/app.html', encoding='utf-8').read()
lets = re.findall(r"\{ c: '([^']+)', s: '([^']+)', w:", app)[:29]

def dec(b):
    raw = subprocess.run(['ffmpeg','-loglevel','error','-i','-','-f','f32le','-ac','1','-ar',str(SR),'-'],
                         input=base64.b64decode(b), capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()
def core_ms(y):
    e,f = env(y); db = 20*np.log10(e/(e.max()+1e-9)); on = np.where(db>-30)[0]
    return round((on[-1]-on[0]+1)*f/SR*1000) if len(on) else 0
def mfcc(y):
    # 13 hệ số MFCC đơn giản qua FFT + mel + DCT
    import numpy.fft as fft
    y = y/(np.abs(y).max()+1e-9); win=int(SR*0.025); hop=int(SR*0.010); n=1024
    mel_f = 2595*np.log10(1+ (np.linspace(0,SR/2,n//2+1))/700)
    frames=[]
    for st in range(0, max(1,len(y)-win), hop):
        seg = y[st:st+win]*np.hanning(win)
        sp = np.abs(fft.rfft(seg, n))**2
        # 26 bộ lọc mel
        edges = np.linspace(mel_f.min(), mel_f.max(), 28)
        fb=np.zeros((26,n//2+1))
        for i in range(26):
            lo,ce,hi=edges[i],edges[i+1],edges[i+2]
            fb[i]=np.clip((mel_f-lo)/(ce-lo+1e-9),0,None)*np.clip((hi-mel_f)/(hi-ce+1e-9),0,None)
        e=np.log(fb@sp+1e-9)
        c=np.real(fft.rfft(e))[:13]
        frames.append(c)
    return np.array(frames) if frames else np.zeros((1,13))
def dtw(A,B):
    if len(A)<2 or len(B)<2: return 9.9
    D=np.full((len(A)+1,len(B)+1),1e9); D[0,0]=0
    for i in range(1,len(A)+1):
        for j in range(1,len(B)+1):
            c=np.linalg.norm(A[i-1]-B[j-1]); D[i,j]=c+min(D[i-1,j],D[i,j-1],D[i-1,j-1])
    return D[-1,-1]/(len(A)+len(B))

rows=[]
for c,s in lets:
    if s not in V: continue
    clip=dec(V[s]); ms=core_ms(clip)
    # 3 bản dựng lại tươi qua short_clip
    fresh=[]
    for _ in range(3):
        try: y,ok,h=short_clip(s); fresh.append(y)
        except: pass
    fm=[mfcc(f) for f in fresh]; cm=mfcc(clip)
    d_fresh=np.mean([dtw(a,b) for i,a in enumerate(fm) for b in fm[i+1:]]) if len(fm)>1 else 9.9
    d_clip=np.mean([dtw(cm,f) for f in fm]) if fm else 9.9
    fresh_ms=round(np.mean([core_ms(f) for f in fresh])) if fresh else 0
    # cờ: clip lệch xa cụm tươi so với độ tản của cụm → nghi ngờ
    ratio = d_clip/(d_fresh+1e-6)
    rows.append((c,s,ms,fresh_ms,round(d_clip,2),round(d_fresh,2),round(ratio,2)))
rows.sort(key=lambda r:-r[6])
print(f"{'chữ':4}{'âm':7}{'dài(ms)':>8}{'tươi(ms)':>9}{'lệch cụm':>10}{'tản cụm':>9}{'tỉ lệ':>7}")
for r in rows: print(f"{r[0]:4}{r[1]:7}{r[2]:>8}{r[3]:>9}{r[4]:>10}{r[5]:>9}{r[6]:>7}")
susp=[r for r in rows if r[6]>2.0 or r[2]<170]
print("\nNghi ngờ (lệch xa bản tươi >2x, hoặc quá ngắn <170ms):")
for r in susp: print(f"  {r[0]} '{r[1]}': dài {r[2]}ms, lệch {r[4]} vs tản {r[5]} (tỉ lệ {r[6]})")
json.dump([dict(zip(['chu','am','ms','fresh_ms','d_clip','d_fresh','ratio'],r)) for r in rows], open('letter_mfcc.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
