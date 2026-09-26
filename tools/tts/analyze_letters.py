"""Phân tích độ rõ của từng âm chữ cái/chữ ghép:
- Giải mã clip trong voice.json, ghép vào câu mẫu trung tính rồi cho bộ nhận dạng nghe lại.
- 'clear' = nghe ra đúng âm; 'blur' = nghe ra khác. Kèm độ dài phần có tiếng (ms)."""
import json, os, sys, subprocess, base64
sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen.py'), encoding='utf-8').read().split("phr = json.load")[0])
V = json.load(open(os.path.join(D, 'voice_latest.json'), encoding='utf-8'))

def dec(b):
    raw = subprocess.run(['ffmpeg','-loglevel','error','-i','-','-f','f32le','-ac','1','-ar',str(SR),'-'],
                         input=base64.b64decode(b), capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def core_ms(y):
    e,f = env(y); db = 20*np.log10(e/(e.max()+1e-9)); on = np.where(db>-30)[0]
    return round((on[-1]-on[0]+1)*f/SR*1000) if len(on) else 0

# câu mẫu để nghe lại: đặt âm vào giữa cho ASR có ngữ cảnh
pre = gen('Cô đọc chữ', 0.9); post = gen('nhé.', 0.9)
prN = clean(hear(pre)[0]).split(); poN = clean(hear(post)[0]).split()

def listen(y):
    y = y/(np.abs(y).max()+1e-9)*np.abs(pre).max()
    h = clean(hear(np.concatenate([pre, np.zeros(int(SR*.09),np.float32), y, np.zeros(int(SR*.05),np.float32), post]))[0]).split()
    # bỏ phần câu mẫu ở đầu/cuối
    i=0
    while i<len(h) and i<len(prN) and h[i]==prN[i]: i+=1
    j=len(h)
    while j>i and (len(h)-j)<len(poN) and h[j-1]==poN[len(h)-j]: j-=1
    return ' '.join(h[i:j])

# đọc danh sách âm từ app
app = open('/home/claude/lop1/src/app.html', encoding='utf-8').read()
import re
letters = re.findall(r"\{ c: '([^']+)', s: '([^']+)'", app)
lets = [(c,s) for c,s in letters][:29]
digs = re.findall(r"\{ c: '(ch|gh|gi|kh|ng|ngh|nh|ph|qu|th|tr)', s: '([^']+)'(?:, n: '([^']*)')?", app)

def norm2(t): return clean(t)
rows=[]
for c,s in lets:
    if s not in V: continue
    y=dec(V[s]); heard=listen(y); ok = norm2(heard)==norm2(s)
    rows.append(('chữ '+c, s, heard, ok, core_ms(y)))
for m in digs:
    c,s,n = m[0],m[1],m[2]
    key = n if n else s
    if key not in V: 
        key = s
    y=dec(V[key]); heard=listen(y); exp = n if n else s; ok = norm2(heard)==norm2(exp)
    rows.append(('ghép '+c, exp, heard, ok, core_ms(y)))

clear=[r for r in rows if r[3]]; blur=[r for r in rows if not r[3]]
print(f"RÕ (nghe ra đúng): {len(clear)}/{len(rows)}")
for r in clear: print(f"  {r[0]:10} '{r[1]}'  ({r[4]}ms)")
print(f"\nCHƯA RÕ (nghe ra khác): {len(blur)}")
for r in blur: print(f"  {r[0]:10} đọc '{r[1]}'  →  máy nghe: '{r[2]}'  ({r[4]}ms)")
json.dump([{'muc':r[0],'doc':r[1],'nghe':r[2],'ro':r[3],'ms':r[4]} for r in rows], open('letter_analysis.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
