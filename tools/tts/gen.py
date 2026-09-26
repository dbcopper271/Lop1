import sherpa_onnx, numpy as np, os, sys, json, re, subprocess, base64, difflib, unicodedata, time
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, '..', '..', 'voice.json'); REP = os.path.join(D, 'voice_report.json')  # voice.json ở thư mục gốc của app

m = os.path.join(D, 'vits-piper-vi_VN-vais1000-medium')
tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=os.path.join(m, 'vi_VN-vais1000-medium.onnx'), tokens=os.path.join(m, 'tokens.txt'), data_dir=os.path.join(m, 'espeak-ng-data')),
    num_threads=int(os.environ.get('TTS_THREADS', 4)))))
SR = tts.sample_rate
a = os.path.join(D, 'sherpa-onnx-zipformer-vi-int8-2025-04-20')
asr = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=os.path.join(a, 'encoder-epoch-12-avg-8.int8.onnx'), decoder=os.path.join(a, 'decoder-epoch-12-avg-8.onnx'),
    joiner=os.path.join(a, 'joiner-epoch-12-avg-8.int8.onnx'), tokens=os.path.join(a, 'tokens.txt'), num_threads=int(os.environ.get('TTS_THREADS', 4)), decoding_method='greedy_search')

def nfc(s): return unicodedata.normalize('NFC', s).strip()
def clean(s): return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', nfc(s).lower())).strip()
def gen(text, speed): return np.array(tts.generate(text, sid=0, speed=speed).samples, dtype=np.float32)
def resample(x, to=16000):
    n = int(len(x) * to / SR); return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
def hear(x):
    s = asr.create_stream(); s.accept_waveform(16000, resample(x)); asr.decode_stream(s)
    r = s.result
    return r.text.lower().strip(), [t.strip().lower() for t in r.tokens], list(r.timestamps)
def env(x, hop=0.005):
    f = int(SR * hop); n = len(x) // f
    return np.array([np.sqrt(np.mean(x[i * f:(i + 1) * f] ** 2) + 1e-12) for i in range(n)]), f
def refine_start(x, t):
    e, f = env(x); k = np.convolve(e, np.ones(3) / 3, 'same')
    lo, hi = max(0, int((t - 0.14) / 0.005)), min(len(k) - 1, int((t + 0.03) / 0.005))
    if hi <= lo: return int(t * SR)
    return (lo + int(np.argmin(k[lo:hi]))) * f
def tidy(y, lead=0.03, tail=0.09):
    e, f = env(y); db = 20 * np.log10(e / (e.max() + 1e-9))
    on = np.where(db > -38)[0]
    if len(on): y = y[max(0, on[0] * f - int(SR * 0.01)):min(len(y), (on[-1] + 1) * f + int(SR * 0.02))]
    y = y / (np.abs(y).max() + 1e-9) * 0.9
    fi = min(len(y), int(SR * 0.012)); y[:fi] *= np.linspace(0, 1, fi)
    fo = min(len(y), int(SR * 0.025)); y[-fo:] *= np.linspace(1, 0, fo)
    return np.concatenate([np.zeros(int(SR * lead), np.float32), y, np.zeros(int(SR * tail), np.float32)])
def mp3(y):
    p = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-codec:a', 'libmp3lame', '-b:a', '32k', '-ar', '22050', '-f', 'mp3', '-'], input=y.astype(np.float32).tobytes(), capture_output=True)
    return base64.b64encode(p.stdout).decode()

CARRIER = 'Bây giờ cô đọc {}.'
pre_dur = len(gen('Bây giờ cô đọc', 0.85)) / SR

def short_clip(text):
    target = clean(text).split(); n = len(target); best = None; best_ts = None; best_h = ''
    for att in range(7):
        x = gen(CARRIER.format(text), 0.85 if att < 4 else 0.78)
        h, toks, ts = hear(x)
        words = clean(h).split()
        ok = len(words) >= n and words[-n:] == target and len(ts) >= n
        if ok:
            st = max(0, refine_start(x, ts[len(ts) - n]) - int(SR * 0.015))
            return tidy(x[st:]), True, h
        if len(words) > 4 and words[:4] == ['bây', 'giờ', 'cô', 'đọc'] and len(ts) > 4 and best_ts is None:
            best, best_ts, best_h = x, ts[4], h
        if best is None: best = x
    if best_ts is not None:
        st = max(0, refine_start(best, best_ts) - int(SR * 0.015))
        return tidy(best[st:]), 'carrier', best_h
    st = refine_start(best, pre_dur)
    return tidy(best[st:]), False, h

LEAD = 'Rồi, cô đọc: '
NL = 3
def long_clip(text):
    target = clean(text); best, bs, bh = None, -1, ''
    for att in range(4):
        x = gen(LEAD + text, 0.9)
        h, toks, ts = hear(x)
        words = clean(h).split()
        body = ' '.join(words[NL:]) if len(words) > NL else clean(h)
        sc = difflib.SequenceMatcher(None, target, body).ratio()
        if len(ts) > NL:
            st = max(0, refine_start(x, ts[NL]) - int(SR * 0.02)); y = x[st:]
        else:
            y = x
        if sc > bs: best, bs, bh = y, sc, body
        if sc >= 0.95: break
    return tidy(best), bs, bh

phr = json.load(open(os.path.join(D, 'phrases.json'), encoding='utf-8'))
out = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) and '--fresh' not in sys.argv else {}
rep = json.load(open(REP, encoding='utf-8')) if os.path.exists(REP) and '--fresh' not in sys.argv else {}
if '--redo-short-bad' in sys.argv:
    for k in [k for k, v in rep.items() if v.get('mode') == 'short' and v.get('ok') is not True]: out.pop(k, None); rep.pop(k, None)
if '--redo-long' in sys.argv:
    for k in [k for k, v in rep.items() if v.get('mode') == 'long']: out.pop(k, None); rep.pop(k, None)
t0 = time.time()
for i, p in enumerate(phr):
    p = nfc(p)
    if p in out: continue
    short = len(p.split()) <= 3 and not p.endswith(('.', '?', '!'))
    if short:
        y, ok, h = short_clip(p); rep[p] = {'mode': 'short', 'ok': ok, 'heard': h}
    else:
        y, sc, h = long_clip(p); rep[p] = {'mode': 'long', 'score': round(sc, 3), 'heard': h}
    rep[p]['dur'] = round(len(y) / SR, 2)
    out[p] = mp3(y)
    if i % 25 == 0:
        json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(f'{i}/{len(phr)} {time.time() - t0:.0f}s', flush=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False); json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('done', len(out), f'{time.time() - t0:.0f}s')
