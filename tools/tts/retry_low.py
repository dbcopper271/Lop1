import json, os, sys, time
sys.argv = [sys.argv[0], '--long']
D = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(D, 'gen_final.py'), encoding='utf-8').read()
exec(src.split("phr = [nfc(p)")[0])
out = json.load(open(OUT, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
ph = json.load(open(os.path.join(D, 'phrases.json'), encoding='utf-8'))
todo = [p for p in ph if rep.get(p, {}).get('mode') == 'long' and rep[p].get('score', 1) < 0.75]
print('todo', len(todo), flush=True); better = 0
for p in todo:
    y, sc, h = long_strict(p, tries=10)
    if sc > rep[p].get('score', 0):
        out[p] = mp3(y); rep[p].update({'score': sc, 'heard': h, 'dur': round(len(y) / SR, 2)}); better += 1
    print(p, rep[p]['score'], rep[p]['heard'], flush=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('better', better, 'of', len(todo))
