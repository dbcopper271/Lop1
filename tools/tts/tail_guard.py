"""Câu có tiếng cuối bị hạ giọng (hoa → hòa): đọc kèm 'nhé' ở cuối rồi cắt bỏ 'nhé', giữ đúng dấu của tiếng cuối."""
import json, os, sys, re
sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen_final.py'), encoding='utf-8').read().split("phr = [nfc(p)")[0])
out = json.load(open(OUT, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
ph = json.load(open(os.path.join(D, 'phrases.json'), encoding='utf-8'))
todo = []
for p in ph:
    r = rep.get(p, {})
    if r.get('mode') != 'long' or r.get('tail'): continue
    t, h = clean(p).split(), clean(r.get('heard', '')).split()
    if t and h and t[-1] != h[-1]: todo.append(p)
print('todo', len(todo), flush=True); fixed = 0
for p in todo:
    body = re.sub(r'[.!?]+$', '', p.strip()); t = clean(p).split(); n = len(t)
    for att in range(10):
        x = gen(LEAD + body + ' nhé.', [0.9, 0.85, 0.95, 0.8][att % 4]); h, toks, ts = hear(x); w = clean(h).split()
        if len(w) == NL + n + 1 and w[NL:NL + n][-1] == t[-1] and w[-1] == 'nhé' and len(ts) == len(w):
            st = max(0, refine_start(x, ts[NL]) - int(SR * 0.02)); en = refine_end(x, ts[-1])
            sc = sum(a == b for a, b in zip(w[NL:NL + n], t)) / n
            if sc >= rep[p].get('score', 0) - 0.01:
                out[p] = mp3(tidy(x[st:en], tail=0.12)); rep[p].update({'score': round(sc, 3), 'heard': ' '.join(w[NL:NL + n]), 'tail': 1}); fixed += 1
                break
    print(p, '→', rep[p]['heard'], flush=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('fixed', fixed, 'of', len(todo))
