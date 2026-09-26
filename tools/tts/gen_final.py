"""Final strict pass.
- Short items (≤3 words): try carrier 'Bây giờ cô đọc X.' and 'Bây giờ cô đọc X nhé.' alternately; keep the first
  attempt the recognizer returns word-for-word (tones included); cut between word timestamps.
- Long sentences: lead-in 'Rồi, cô đọc: ' and up to 8 attempts until word-for-word.
Only regenerates items that are new or not yet confirmed exact."""
import json, os, sys, time, difflib
FLAGS = sys.argv[1:]
sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen.py'), encoding='utf-8').read().split("phr = json.load")[0])

def refine_end(x, t):
    e, f = env(x); k = np.convolve(e, np.ones(3) / 3, 'same')
    lo, hi = max(0, int((t - 0.12) / 0.005)), min(len(k) - 1, int((t + 0.04) / 0.005))
    if hi <= lo: return int(t * SR)
    return (lo + int(np.argmin(k[lo:hi]))) * f

def short_strict(text, tries=12):
    target = clean(text).split(); n = len(target); fallback = None
    for att in range(tries):
        nhe = att % 2 == 1
        x = gen(('Bây giờ cô đọc {} nhé.' if nhe else 'Bây giờ cô đọc {}.').format(text), 0.85 if att < 8 else 0.78)
        h, toks, ts = hear(x); w = clean(h).split()
        if nhe:
            ok = len(w) >= n + 1 and w[-(n + 1):-1] == target and w[-1] == 'nhé' and len(ts) >= n + 1
            if ok:
                st = max(0, refine_start(x, ts[len(ts) - n - 1]) - int(SR * 0.015)); en = refine_end(x, ts[-1])
                if en - st > int(SR * 0.15): return tidy(x[st:en]), True, h
        else:
            ok = len(w) >= n and w[-n:] == target and len(ts) >= n
            if ok:
                st = max(0, refine_start(x, ts[len(ts) - n]) - int(SR * 0.015)); return tidy(x[st:]), True, h
        if fallback is None and not nhe and len(w) > 4 and w[:4] == ['bây', 'giờ', 'cô', 'đọc'] and len(ts) > 4:
            fallback = (x, ts[4], h)
    if fallback:
        x, t, h = fallback; st = max(0, refine_start(x, t) - int(SR * 0.015)); return tidy(x[st:]), 'carrier', h
    x = gen('Bây giờ cô đọc {}.'.format(text), 0.85); st = refine_start(x, pre_dur); return tidy(x[st:]), False, ''

def long_strict(text, tries=8):
    target = clean(text); best = None
    for att in range(tries):
        x = gen(LEAD + text, 0.9 if att < 5 else 0.82)
        h, toks, ts = hear(x); w = clean(h).split()
        body = ' '.join(w[NL:]) if len(w) > NL else clean(h)
        t, b = target.split(), body.split()
        sc = sum(m.size for m in difflib.SequenceMatcher(None, t, b).get_matching_blocks()) / max(len(t), 1)
        y = x[max(0, refine_start(x, ts[NL]) - int(SR * 0.02)):] if len(ts) > NL else x
        if best is None or sc > best[0]: best = (sc, y, body)
        if b == t: break
    return tidy(best[1]), round(best[0], 3), best[2]

phr = [nfc(p) for p in json.load(open(os.path.join(D, 'phrases.json'), encoding='utf-8'))]
out = json.load(open(OUT, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
keep = set(phr)
for k in list(out):
    if k not in keep: out.pop(k); rep.pop(k, None)
todo = []
for p in phr:
    short = len(p.split()) <= 3 and not p.endswith(('.', '?', '!'))
    r = rep.get(p) or {}
    if p not in out: todo.append((p, short))
    elif '--newonly' in FLAGS: continue
    elif short and (r.get('ok') is not True or r.get('v') != 2): todo.append((p, short))
    elif not short and r.get('heard') != clean(p) and '--long' in FLAGS: todo.append((p, short))
print('todo', len(todo), flush=True)
t0 = time.time()
for i, (p, short) in enumerate(todo):
    if short:
        y, ok, h = short_strict(p); rep[p] = {'mode': 'short', 'ok': ok, 'heard': h, 'v': 2}
    else:
        y, sc, h = long_strict(p); rep[p] = {'mode': 'long', 'score': sc, 'heard': h}
    rep[p]['dur'] = round(len(y) / SR, 2); out[p] = mp3(y)
    if i % 10 == 0:
        json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(f'{i}/{len(todo)} {time.time() - t0:.0f}s', flush=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('done', len(out), f'{time.time() - t0:.0f}s')
