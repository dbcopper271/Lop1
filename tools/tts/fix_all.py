"""Sửa dứt điểm: (1) từ hỏng ASR, (2) lệch thanh — bằng cách đặt từ ở GIỮA câu mang rồi cắt, giữ nguyên thanh."""
import json, os, sys
sys.argv=[sys.argv[0]]
D=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D,'gen.py'),encoding='utf-8').read().split("phr = json.load")[0])
def refine_end(x,t):
    e,f=env(x); k=np.convolve(e,np.ones(3)/3,'same')
    lo,hi=max(0,int((t-0.12)/0.005)),min(len(k)-1,int((t+0.05)/0.005))
    if hi<=lo: return int(t*SR)
    return (lo+int(np.argmin(k[lo:hi])))*f
def core_ms(y):
    e,f=env(y); db=20*np.log10(e/(e.max()+1e-9)); on=np.where(db>-30)[0]
    return round((on[-1]-on[0]+1)*f/SR*1000) if len(on) else 0
# câu mang có từ đứng GIỮA (theo sau bởi một từ khác) để giữ thanh ngang
CARR=["Cô đọc {} rồi nghỉ nhé.","Nào, {} đây rồi.","Tiếng {} nghe rõ chưa.","Cô phát âm {} thật rõ nhé.","Bé đọc {} theo cô nào."]
def mid_word(target, tries_each=3):
    tg=clean(target).split(); n=len(tg); best=None
    for carrier in CARR:
        for att in range(tries_each):
            sp=[0.74,0.8,0.7,0.78,0.82][att%5]
            x=gen(carrier.format(target),sp); h,toks,ts=hear(x); w=clean(h).split()
            # tìm span khớp đúng (kể cả thanh) và KHÔNG ở cuối câu
            for i in range(len(w)-n):     # -n (không lấy tới hết) để chắc chắn có từ theo sau
                if w[i:i+n]==tg and len(ts)>i+n:
                    st=max(0,refine_start(x,ts[i])-int(SR*0.015)); en=refine_end(x,ts[i+n-1] if n==1 else ts[i+n]-0.001 if False else refine_end(x,ts[i+n]) if len(ts)>i+n else len(x))
                    en=refine_end(x, ts[i+n]) if len(ts)>i+n else len(x)
                    y=tidy(x[st:en],tail=0.11); ms=core_ms(y)
                    if ms>=300 and (best is None or abs(ms-360)<abs(best[1]-360)): best=(y,ms,'exact')
            if best and best[2]=='exact' and best[1]>=320: return best
    return best
V=json.load(open('work_voice.json',encoding='utf-8')); rep=json.load(open(REP,encoding='utf-8'))
TARGETS=['đa','hoa','cáo','rau','đan','on','hat','ăp','răn','hươu','cún',   # hỏng ASR
         'ba','tau','tra','cua','an','thang','bô','bão','rổ','ngờ','tai']    # lệch thanh
done=0
for t in TARGETS:
    b=mid_word(t)
    if b:
        y,ms,mode=b; V[t]=mp3(y); rep[t]={'mode':'short','ok':True,'heard':'(giữa câu) '+t,'v':6,'dur':round(len(y)/SR,2),'ms':ms}; done+=1
        print(f"OK  {t:8} {ms}ms",flush=True)
    else: print(f"--  {t:8} chưa khớp",flush=True)
json.dump(V,open('work_voice.json','w',encoding='utf-8'),ensure_ascii=False); json.dump(rep,open(REP,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print('fixed',done,'/',len(TARGETS))
