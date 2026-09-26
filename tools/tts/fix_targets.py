"""Tạo lại các câu hỏi mà từ quan trọng (tiếng bé phải nghe để chọn) chưa được máy nghe ra đúng.
Chấp nhận bản mà mọi từ quan trọng được nghe đúng, đúng thứ tự, đúng dấu."""
import json, os, sys, re, time
sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen.py'), encoding='utf-8').read().split("phr = json.load")[0])
from targets import PAT
def req_words(p):
    for pat in PAT:
        m = re.match(pat, p)
        if m: return [w for g in m.groups() for w in clean(g).split()]
    return None
def ok_heard(p, h):
    req, hw = req_words(p), clean(h).split()
    if req is None: return None
    if len(hw) < len(clean(p).split()) - 1: return False
    i = 0
    for w in hw:
        if i < len(req) and w == req[i]: i += 1
    return i == len(req)
out = json.load(open(OUT, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
todo = [p for p in json.load(open(os.path.join(D, 'phrases.json'), encoding='utf-8')) if rep.get(p, {}).get('mode') == 'long' and ok_heard(p, rep[p].get('heard', '')) is False]
print('todo', len(todo), flush=True); fixed = 0; t0 = time.time()
for k, p in enumerate(todo):
    for att in range(12):
        x = gen(LEAD + p, [0.9, 0.85, 0.95, 0.8][att % 4])
        h, toks, ts = hear(x); w = clean(h).split(); body = ' '.join(w[NL:]) if len(w) > NL else clean(h)
        if ok_heard(p, body) and len(ts) > NL:
            y = x[max(0, refine_start(x, ts[NL]) - int(SR * 0.02)):]
            out[p] = mp3(tidy(y)); rep[p].update({'heard': body, 'target_ok': True, 'dur': round(len(y) / SR, 2)}); fixed += 1; break
    else: rep[p]['target_ok'] = False
    if k % 5 == 0:
        json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(f'{k}/{len(todo)} fixed {fixed} {time.time() - t0:.0f}s', flush=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('done fixed', fixed, 'of', len(todo), [p for p in todo if rep[p].get('target_ok') is False])
