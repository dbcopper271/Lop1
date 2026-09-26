"""Tạo lại âm của chữ cái cho rõ hơn: đọc chậm trong câu mang 'Bây giờ cô đọc âm … nhé.', máy nghe lại phải đúng,
chọn bản dài, rõ nhất trong các bản đạt."""
import json, os, sys, time
ITEMS = json.loads(sys.argv[1]); CARRIERS = json.loads(sys.argv[2]) if len(sys.argv) > 2 else ['Bây giờ cô đọc âm {} nhé.', 'Cô đọc chữ {} nhé.']; sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen.py'), encoding='utf-8').read().split("phr = json.load")[0])
def refine_end(x, t):
    e, f = env(x); k = np.convolve(e, np.ones(3) / 3, 'same')
    lo, hi = max(0, int((t - 0.12) / 0.005)), min(len(k) - 1, int((t + 0.04) / 0.005))
    if hi <= lo: return int(t * SR)
    return (lo + int(np.argmin(k[lo:hi]))) * f
out = json.load(open(OUT, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
res = {}
for text in ITEMS:
    tg = clean(text).split(); n = len(tg); cands = []
    for att, sp in enumerate([0.72, 0.64, 0.8, 0.68, 0.76, 0.6, 0.72, 0.66, 0.84, 0.7, 0.62, 0.78]):
        for carrier in CARRIERS:
            x = gen(carrier.format(text), sp); h, toks, ts = hear(x); w = clean(h).split()
            pre, post = carrier.split('{}'); key = clean(pre).split()[-1:]; nxt = clean(post).split()[:1]
            want = key + tg + nxt
            for i in range(len(w) - len(want) + 1):
                if w[i:i + len(want)] == want and len(ts) == len(w):
                    st = max(0, refine_start(x, ts[i + 1]) - int(SR * 0.015)); en = refine_end(x, ts[i + 1 + n])
                    if en - st > int(SR * 0.2): cands.append((en - st, x[st:en], h, sp))
                    break
        if len(cands) >= 3: break
    if cands:
        cands.sort(key=lambda c: -c[0]); d, y, h, sp = cands[min(1, len(cands) - 1)] if len(cands) >= 3 else cands[0]
        out[text] = mp3(tidy(y, tail=0.12)); rep[text] = {'mode': 'short', 'ok': True, 'heard': h, 'v': 3, 'dur': round(len(y) / SR, 2), 'speed': sp}
        res[text] = (True, round(d / SR, 2), h)
    else: res[text] = (False, 0, '')
    print(text, res[text], flush=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('done', sum(1 for v in res.values() if v[0]), '/', len(res))
