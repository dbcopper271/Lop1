"""Lấy âm i từ 'y tá', âm ơ từ 'ơ kìa' (máy nghe lại được), rồi kéo dài các nguyên âm đơn cho bé nghe rõ (giữ nguyên cao độ)."""
import json, os, sys, subprocess, base64
sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen.py'), encoding='utf-8').read().split("phr = json.load")[0])
out = json.load(open(OUT, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
def grab(target, carrier, idx_word, sps=(0.72, 0.66, 0.8, 0.7, 0.62, 0.76, 0.68, 0.84)):
    for sp in sps:
        x = gen(carrier, sp); h, toks, ts = hear(x); w = clean(h).split(); cw = clean(carrier).split()
        if w == cw and len(ts) == len(w):
            i = idx_word; st = max(0, refine_start(x, ts[i]) - int(SR * 0.015)); en = refine_start(x, ts[i + 1])
            if en - st > int(SR * 0.15): return x[st:en], h, sp
    return None, None, None
for text, carrier, i in [('i', 'Bây giờ cô đọc y tá nhé.', 4), ('ơ', 'Bây giờ cô đọc ơ kìa nhé.', 4)]:
    if rep.get(text, {}).get('v') == 4: continue
    y, h, sp = grab(text, carrier, i)
    print(text, carrier, bool(y is not None), h, flush=True)
    if y is not None:
        out[text] = mp3(tidy(y, tail=0.12)); rep[text] = {'mode': 'short', 'ok': True, 'heard': h, 'v': 4, 'src': carrier, 'dur': round(len(y) / SR, 2)}
# Kéo dài nguyên âm đơn (atempo giữ cao độ)
def dur_mp3(b):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', '-', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], input=base64.b64decode(b), capture_output=True).stdout; return len(raw) / 4 / 16000
for v in ['a', 'á', 'ớ', 'e', 'ê', 'i', 'o', 'ô', 'ơ', 'u', 'ư']:
    if rep.get(v, {}).get('stretched'): continue
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', '-', '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], input=base64.b64decode(out[v]), capture_output=True).stdout
    y = np.frombuffer(raw, dtype=np.float32).copy()
    e, f = env(y); db = 20 * np.log10(e / (e.max() + 1e-9)); on = np.where(db > -30)[0]
    core = (on[-1] - on[0] + 1) * f / SR if len(on) else len(y) / SR
    tempo = max(0.5, min(1.0, core / 0.5))
    if tempo < 0.97:
        z = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-filter:a', f'atempo={tempo:.3f}', '-f', 'f32le', '-'], input=y.tobytes(), capture_output=True).stdout
        y = np.frombuffer(z, dtype=np.float32).copy()
    out[v] = mp3(tidy(y, tail=0.12)); rep[v]['stretched'] = round(tempo, 2)
    print(v, 'core', round(core, 2), 'tempo', round(tempo, 2), '→', round(dur_mp3(out[v]), 2), flush=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
