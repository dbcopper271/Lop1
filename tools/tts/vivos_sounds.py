"""Âm chữ cái, chữ ghép, vần bằng giọng nữ số 1 của mô hình vits-piper-vi_VN-vivos-x_low.
Giọng vais1000 (giọng chính) không đọc được âm đứng riêng: âm dài 0,1-0,2 giây, đo formant chỉ đúng 3/9 nguyên âm
(u ra ê, ư ra ô, o ra a). Giọng vivos số 1 đọc âm đứng riêng dài khoảng 0,5 giây, tách rõ ô/o, u/ư.
Mỗi âm đọc nhiều lần ("X." và "X!", hai tốc độ); nguyên âm chọn theo formant F1/F2 (gần đúng nguyên âm của nó,
xa các nguyên âm dễ lẫn), vần và tên phụ âm chọn theo độ dài và cao độ đúng thanh.
Tải mô hình: https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-vi_VN-vivos-x_low.tar.bz2
Chạy từ thư mục gốc: python3 tools/tts/vivos_sounds.py [--only a,ô,ai] [--words] [--dry]
  --words: mọi tiếng, từ ngắn (≤3 tiếng) còn lại, dùng trong đánh vần, luyện tập; cần thêm mô hình nhận dạng sherpa-onnx-zipformer-vi-int8-2025-04-20"""
import base64, json, os, subprocess, sys, unicodedata
import numpy as np, sherpa_onnx

D = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(D, '..', '..')
VOICE, REP = os.path.join(ROOT, 'voice.json'), os.path.join(D, 'voice_report.json')
M = os.path.join(D, 'vits-piper-vi_VN-vivos-x_low'); SID = 1
tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=os.path.join(M, 'vi_VN-vivos-x_low.onnx'), tokens=os.path.join(M, 'tokens.txt'),
                                               data_dir=os.path.join(M, 'espeak-ng-data')), num_threads=int(os.environ.get('TTS_THREADS', 4)))))
SR = tts.sample_rate

VOWELS = ['a', 'e', 'ê', 'i', 'o', 'ô', 'ơ', 'u', 'ư']
LETTERS = VOWELS + ['á', 'ớ', 'bờ', 'cờ', 'dờ', 'đờ', 'gờ', 'hờ', 'i ngắn', 'ca', 'lờ', 'mờ', 'nờ', 'pờ', 'quờ', 'rờ', 'sờ', 'tờ', 'vờ', 'xờ', 'i dài']
DIGRAPHS = ['chờ', 'gờ kép', 'di', 'khờ', 'ngờ', 'ngờ kép', 'nhờ', 'phờ', 'thờ', 'trờ']
OPEN = ['ai', 'ay', 'ây', 'oi', 'ôi', 'ơi', 'ui', 'ao', 'au', 'âu', 'eo', 'êu', 'iu', 'ưu', 'ua', 'ưa', 'oa',
        'am', 'ăm', 'âm', 'em', 'êm', 'im', 'ôm', 'ơm', 'um', 'an', 'ăn', 'ân', 'en', 'ên', 'in', 'on', 'ơn', 'un',
        'ang', 'ăng', 'ong', 'ông', 'ung', 'ưng', 'anh', 'inh']
# Vần khép (tận cùng c, ch, t, p) không có thanh ngang; khi đọc vần, cô đọc lên giọng như thanh sắc
CLOSED = {'ac': 'ác', 'oc': 'óc', 'ôc': 'ốc', 'uc': 'úc', 'ưc': 'ức', 'ach': 'ách', 'êch': 'ếch', 'ich': 'ích',
          'at': 'át', 'ăt': 'ắt', 'ât': 'ất', 'et': 'ét', 'it': 'ít', 'ôt': 'ốt', 'ơt': 'ớt', 'ut': 'út',
          'ap': 'áp', 'ăp': 'ắp', 'âp': 'ấp', 'ep': 'ép', 'êp': 'ếp', 'op': 'óp', 'ôp': 'ốp', 'ơp': 'ớp'}
SOUNDS = LETTERS + DIGRAPHS + OPEN + list(CLOSED)

def gen(text, speed):
    return np.array(tts.generate(text, sid=SID, speed=speed).samples, dtype=np.float32)

def db_env(y, hop=0.005):
    f = int(SR * hop); n = len(y) // f
    e = np.array([np.sqrt(np.mean(y[i * f:(i + 1) * f] ** 2) + 1e-12) for i in range(n)])
    return 20 * np.log10(e / (e.max() + 1e-9)), f

def core_dur(y):
    db, f = db_env(y); on = np.where(db > -30)[0]
    return (on[-1] - on[0] + 1) * f / SR if len(on) else 0.0

def tidy(y, lead=0.015, tail=0.12):
    """Bỏ khoảng lặng hai đầu (ngưỡng -48dB, chừa 35ms nhả hơi), đệm đuôi để không nghe cụt."""
    db, f = db_env(y); on = np.where(db > -48)[0]
    if len(on): y = y[max(0, on[0] * f - int(SR * 0.015)):min(len(y), (on[-1] + 1) * f + int(SR * 0.035))]
    y = y / (np.abs(y).max() + 1e-9) * 0.93
    fi = min(len(y), int(SR * 0.004)); y[:fi] *= np.linspace(0, 1, fi)
    fo = min(len(y), int(SR * 0.015)); y[-fo:] *= np.linspace(1, 0, fo)
    return np.concatenate([np.zeros(int(SR * lead), np.float32), y, np.zeros(int(SR * tail), np.float32)])

def mp3(y):
    p = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-codec:a', 'libmp3lame',
                        '-b:a', '32k', '-ar', '22050', '-f', 'mp3', '-'], input=y.astype(np.float32).tobytes(), capture_output=True, check=True)
    return base64.b64encode(p.stdout).decode()

def formants(y):
    """F1, F2 ở giữa phần có tiếng (LPC bậc 18 trên tín hiệu 16kHz)."""
    e = np.convolve(y.astype(np.float64) ** 2, np.ones(int(SR * 0.02)) / int(SR * 0.02), 'same'); on = np.where(e > e.max() * 0.1)[0]
    if len(on) < int(SR * 0.06): return None
    m = (on[0] + on[-1]) // 2; half = max(int(SR * 0.015), int((on[-1] - on[0]) * 0.25))
    seg = y[m - half:m + half].astype(np.float64)
    seg = np.append(seg[0], seg[1:] - 0.97 * seg[:-1]) * np.hamming(len(seg))
    p = 18; r = np.correlate(seg, seg, 'full')[len(seg) - 1:len(seg) + p]
    R = np.array([[r[abs(i - j)] for j in range(p)] for i in range(p)]) + np.eye(p) * 1e-6 * r[0]
    a = np.linalg.solve(R, r[1:p + 1]); roots = np.roots(np.r_[1, -a]); roots = roots[np.imag(roots) > 0]
    fr = np.angle(roots) * SR / (2 * np.pi); bw = -np.log(np.abs(roots)) * SR / np.pi
    f = sorted(x for x, w in zip(fr, bw) if 200 < x < 3500 and w < 500)
    return (f[0], f[1]) if len(f) >= 2 else None

def f0(y, lo=120, hi=450):
    w, h = int(SR * 0.03), int(SR * 0.01); out = []; mx = np.abs(y).max()
    for i in range(0, len(y) - w, h):
        fr = y[i:i + w] - y[i:i + w].mean()
        if np.sqrt((fr ** 2).mean()) < mx * 0.08: continue
        ac = np.correlate(fr, fr, 'full')[w - 1:]; ac /= ac[0] + 1e-9; a, b = int(SR / hi), int(SR / lo); j = a + int(np.argmax(ac[a:b]))
        if ac[j] > 0.5: out.append(SR / j)
    return np.array(out)

def tone(word):
    marks = {'̀': 'huyen', '́': 'sac', '̉': 'hoi', '̃': 'nga', '̣': 'nang'}
    for ch in unicodedata.normalize('NFD', word.split()[-1]):
        if ch in marks: return marks[ch]
    return 'ngang'

def tone_bad(y, cls):
    v = f0(y)
    if len(v) < 4: return 5.0
    q = max(1, len(v) // 4); drop = 12 * np.log2(np.median(v[-q:]) / np.median(v[:q])); rng = float(np.ptp(12 * np.log2(v / np.median(v))))
    if cls == 'ngang': return abs(drop) + 0.5 * max(0, rng - 2.5)
    if cls == 'sac': return max(0.0, 3 - drop)
    if cls == 'huyen': return max(0.0, drop + 1)
    return 0.0

def takes(text, speeds=(0.65, 0.75)):
    for suffix in ['.', '!']:
        for sp in speeds:
            for _ in range(3):
                yield tidy(gen(text + suffix, sp)), suffix, sp

def vowel_space():
    """Formant trung vị của 9 nguyên âm theo chính giọng này; e lấy bản đọc "e!" (bản "e." đọc gần như ê)."""
    ref = {}
    for v in VOWELS:
        fs = [formants(gen(v + ('!' if v == 'e' else '.'), 0.65)) for _ in range(5)]
        fs = [f for f in fs if f]; ref[v] = np.log(np.median(np.array(fs), 0))
    return ref

def pick_vowel(v, ref):
    """Bản đọc có formant gần nguyên âm v nhất so với nguyên âm gần kề dễ lẫn; phải dài ít nhất 0,35 giây."""
    best = None
    for y, suf, sp in takes(v):
        F = formants(y)
        if F is None or core_dur(y) < 0.35: continue
        x = np.log(np.array(F)); own = np.linalg.norm(x - ref[v]); other = min(np.linalg.norm(x - ref[k]) for k in ref if k != v)
        if other <= own: continue                      # gần nguyên âm khác hơn: loại
        score = (other - own) / (other + own) - 0.05 * tone_bad(y, 'ngang')
        if best is None or score > best[0]: best = (score, y, suf, sp, [round(z) for z in F])
    return best

def pick_other(key):
    text = CLOSED.get(key, key); cls = tone(text) if ' ' not in key else 'any'; best = None
    need = 0.28 if key in CLOSED else 0.38                      # vần khép tận cùng bằng âm tắc nên vốn ngắn hơn
    for y, suf, sp in takes(text, (0.5, 0.6, 0.7) if key in CLOSED else (0.65, 0.75)):
        d = core_dur(y); score = -tone_bad(y, cls) - 5 * max(0.0, need - d)
        if best is None or score > best[0]: best = (score, y, suf, sp, round(d, 2))
    return best

ASR = None
def hear(y):
    """Máy nhận dạng (sherpa-onnx zipformer tiếng Việt, cùng thư mục) nghe một clip đứng riêng."""
    global ASR
    if ASR is None:
        a = os.path.join(D, 'sherpa-onnx-zipformer-vi-int8-2025-04-20')
        ASR = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=os.path.join(a, 'encoder-epoch-12-avg-8.int8.onnx'), decoder=os.path.join(a, 'decoder-epoch-12-avg-8.onnx'),
            joiner=os.path.join(a, 'joiner-epoch-12-avg-8.int8.onnx'), tokens=os.path.join(a, 'tokens.txt'), num_threads=int(os.environ.get('TTS_THREADS', 4)), decoding_method='greedy_search')
    st = ASR.create_stream(); x = np.concatenate([np.zeros(int(SR * 0.2), np.float32), y, np.zeros(int(SR * 0.3), np.float32)])
    if SR != 16000: x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * 16000 / SR)), np.arange(len(x)), x).astype(np.float32)
    st.accept_waveform(16000, x); ASR.decode_stream(st)
    return clean(st.result.text)

def clean(t):
    import re
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFC', t).lower())).strip()

def dec(b):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', '-', '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], input=base64.b64decode(b), capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def pick_word(key, cur):
    """Tiếng, từ ngắn: ưu tiên bản máy nghe đúng chữ, rồi đúng thanh, đủ dài. Bản đang dùng nghe đúng mà bản mới không thì giữ."""
    n = len(key.split()); cls = tone(key) if n == 1 else 'any'; best = None
    for y, suf, sp in takes(key, (0.7, 0.8)):
        h = hear(y); ok = h == clean(key); d = core_dur(y)
        score = (3 if ok else 0) - tone_bad(y, cls) - 5 * max(0.0, 0.3 * n - d)
        if best is None or score > best[0]: best = (score, y, suf, sp, h)
        if ok and score > 2.5: break
    cur_ok = hear(dec(cur)) == clean(key)
    if best is None or (cur_ok and best[4] != clean(key)): return None
    return best

if __name__ == '__main__':
    V = json.load(open(VOICE, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
    if '--words' in sys.argv:
        only = [k for k, v in rep.items() if v.get('mode') == 'short' and k in V and k not in SOUNDS]
    else:
        only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else SOUNDS
    ref = vowel_space() if any(k in VOWELS for k in only) else None; out = {}
    for i, k in enumerate(only):
        if k not in V: print('bỏ qua (app không dùng):', k); continue
        b = pick_vowel(k, ref) if k in VOWELS else pick_other(k) if k in SOUNDS else pick_word(k, V[k])
        if b is None: print(f'[{i + 1}/{len(only)}] {k}: không có bản đạt, giữ cũ', flush=True); continue
        score, y, suf, sp, info = b
        out[k] = [mp3(y), {'mode': 'short', 'ok': 'vivos', 'heard': '', 'v': 'vivos1', 'src': f'vivos sid{SID} "{CLOSED.get(k, k)}{suf}" sp={sp}',
                          'core': round(core_dur(y), 2), 'dur': round(len(y) / SR, 2)}]
        print(f'[{i + 1}/{len(only)}] {k} "{CLOSED.get(k, k)}{suf}" sp={sp} điểm={score:.2f} {info} dài {out[k][1]["core"]}s', flush=True)
    if '--dry' in sys.argv:
        json.dump(out, open(os.path.join(D, 'vivos_preview.json'), 'w', encoding='utf-8'), ensure_ascii=False); sys.exit(0)
    for k, (b, info) in out.items(): V[k] = b; rep[k] = info
    json.dump(V, open(VOICE, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    subprocess.run(['python3', os.path.join(ROOT, 'tools', 'build.py')], check=True)
