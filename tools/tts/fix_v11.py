"""v11: tách vần, chữ cái, phụ âm, tiếng đánh vần và số đếm từ tiếng nằm giữa câu mang; chọn bản có cao độ đúng thanh
(ngang phẳng, sắc đi lên, huyền đi xuống); đuôi nhả hơi tự nhiên (ngưỡng -48dB, đệm 0.09s).
Chạy từ thư mục gốc: python3 tools/tts/fix_v11.py"""
import json, os, sys, subprocess, unicodedata
import numpy as np

ONLY = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen.py'), encoding='utf-8').read().split("phr = json.load")[0])
ROOT = os.path.join(D, '..', '..')

def words_ts(x):
    s = asr.create_stream(); s.accept_waveform(16000, resample(x)); asr.decode_stream(s)
    W, T = [], []
    for tok, t in zip(s.result.tokens, s.result.timestamps):
        if tok.startswith(' ') or not W: W.append(tok.strip().lower()); T.append(t)
        else: W[-1] += tok.strip().lower()
    return [clean(w) for w in W], T, clean(s.result.text)

def f0(y, lo=110, hi=450, win=0.03, hop=0.01):
    w, h = int(SR * win), int(SR * hop); idx = range(0, max(0, len(y) - w), h)
    en = np.array([np.sqrt(np.mean(y[i:i + w] ** 2)) for i in idx]); mx = en.max() + 1e-9 if len(en) else 1
    out = []
    for k, i in enumerate(idx):
        if en[k] < mx * 0.1: out.append(np.nan); continue
        fr = y[i:i + w] - np.mean(y[i:i + w]); ac = np.correlate(fr, fr, 'full')[w - 1:]; ac /= ac[0] + 1e-9
        a, b = int(SR / hi), int(SR / lo); j = a + int(np.argmax(ac[a:b]))
        out.append(SR / j if ac[j] > 0.5 else np.nan)
    return np.array(out)

def contour(y):
    v = f0(y); v = v[~np.isnan(v)]
    if len(v) < 4: return None
    q = max(1, len(v) // 4); st = 12 * np.log2(v / np.median(v))
    return {'drop': round(float(12 * np.log2(np.median(v[-q:]) / np.median(v[:q]))), 1), 'rng': round(float(st.max() - st.min()), 1)}

def tone(word):
    marks = {'̀': 'huyen', '́': 'sac', '̉': 'hoi', '̃': 'nga', '̣': 'nang'}
    for ch in unicodedata.normalize('NFD', word):
        if ch in marks: return marks[ch]
    return 'ngang'

def tone_bad(y, cls):
    c = contour(y)
    if c is None: return 6.0, c
    if cls == 'ngang': return abs(c['drop']) + 0.5 * max(0, c['rng'] - 2), c
    if cls == 'sac': return max(0.0, 4 - c['drop']) + 0.5 * max(0.0, c['drop'] - 9), c
    if cls == 'huyen': return max(0.0, c['drop'] + 1), c
    return 0.0, c

def core(y, thr=-32):
    if len(y) < 2: return 0, len(y)
    e, f = env(y); db = 20 * np.log10(e / (e.max() + 1e-9)); on = np.where(db > thr)[0]
    return (on[0] * f, (on[-1] + 1) * f) if len(on) else (0, len(y))

def tidy_smooth(y, lead=0.015, tail=0.09):
    e, f = env(y); db = 20 * np.log10(e / (e.max() + 1e-9))
    on = np.where(db > -48)[0]
    if len(on):
        st = max(0, on[0] * f - int(SR * 0.015)); en = min(len(y), (on[-1] + 1) * f + int(SR * 0.035)); y = y[st:en]
    y = y / (np.abs(y).max() + 1e-9) * 0.96
    fi = min(len(y), int(SR * 0.004)); y[:fi] *= np.linspace(0, 1, fi)
    fo = min(len(y), int(SR * 0.012)); y[-fo:] *= np.linspace(1, 0, fo)
    return np.concatenate([np.zeros(int(SR * lead), np.float32), y, np.zeros(int(SR * tail), np.float32)])

def stretch(y, target=0.33, floor=0.72):
    s, e = core(y); ms = (e - s) / SR
    if ms <= 0: return y
    tempo = max(floor, min(1.0, ms / target))
    if tempo >= 0.98: return y
    z = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-filter:a', f'atempo={tempo:.3f}', '-f', 'f32le', '-'],
                       input=y.astype(np.float32).tobytes(), capture_output=True).stdout
    return np.frombuffer(z, dtype=np.float32).copy()

def dip(x, a, b):
    e, f = env(x); k = np.convolve(e, np.ones(3) / 3, 'same')
    lo, hi = max(0, int(a / 0.005)), min(len(k) - 1, int(b / 0.005))
    return (lo + int(np.argmin(k[lo:hi]))) * f if hi > lo else None

def word_seg(x, carrier, target):
    """Cắt tiếng đích khỏi câu mang theo mốc của từ đứng trước và sau; máy nghe bỏ sót tiếng đích thì lấy chỗ lặng giữa hai từ."""
    tg = clean(target).split(); cw = clean(carrier.format(target)).split(); p = cw.index(tg[0]); n = len(tg); suf = cw[p + n:]
    W, T, h = words_ts(x)
    if len(W) == len(cw) and W[p + n] == suf[0] and W[p - 1] == cw[p - 1]:
        st = max(0, refine_start(x, T[p]) - int(SR * 0.020)); en = refine_start(x, T[p + n]); how = 'heard' if W[p:p + n] == tg else 'pos'
    elif len(W) == len(cw) - n and W[p] == suf[0] and W[p - 1] == cw[p - 1]:
        en = refine_start(x, T[p]); st = dip(x, T[p - 1] + 0.12, T[p] - 0.10); how = 'dip'
        if st is None: return None
    else:
        return None
    if not (int(SR * 0.12) <= en - st <= int(SR * 0.8)): return None
    return x[st:en], how, h

VOICELESS = ('th', 'ch', 'kh', 'ph', 't', 'c', 'k', 's', 'x', 'p', 'h')

def cut_initial(seg, word, frac):
    seg = seg[slice(*core(seg, thr=-35))]
    if frac == 0: return seg
    if word.startswith(VOICELESS):
        v = f0(seg); hop = int(SR * 0.01); half = len(v) // 2
        un = [i for i in range(half) if np.isnan(v[i])]
        if un and un[-1] + 1 < len(v): return seg[(un[-1] + 1) * hop:]
    return seg[int(len(seg) * frac):]

# Hai bên tiếng đích là tiếng thanh ngang; đứng sau "tiếng" (thanh sắc) thì tiếng thanh ngang bị kéo tụt 4-8 nửa cung
CARRIERS = ['Bây giờ cô {} cho em nghe.', 'Em nghe cô {} cho vui nhé.', 'Cô đọc to {} cho em nghe.', 'Em ơi {} ơi.']
FALLBACK = ['Bé hãy đọc tiếng {} cùng cô nào.', 'Nào, tiếng {} đây rồi.']

def best_take(target, speeds, cls, post):
    best = None
    rounds = [(CARRIERS, speeds), (CARRIERS, [0.84, 0.68, 0.78]), (FALLBACK, speeds)] + ([(CARRIERS, [0.74, 0.82, 0.70, 0.86])] * 3 if ONLY else [])
    for carriers, sps in rounds:
        if best is not None and best[0] <= 1.5: break
        for carrier, sp in [(c, v) for c in carriers for v in sps]:
            r = word_seg(gen(carrier.format(target), sp), carrier, target)
            if r is None: continue
            seg, how, h = r; y = post(seg)
            if len(y) < int(SR * 0.19): continue
            bad, c = tone_bad(y, cls); bad += {'heard': 0, 'pos': 0.3, 'dip': 0.6}[how]
            if best is None or bad < best[0]: best = (bad, y, how, h, c, sp)
    return best

VOICE = os.path.join(ROOT, 'voice.json')
V = json.load(open(VOICE, encoding='utf-8'))
rep = json.load(open(REP, encoding='utf-8'))
fails = []

def put(key, y, note, ok=True):
    V[key] = mp3(y); rep[key] = {'mode': 'short', 'ok': ok, 'heard': note, 'v': 11, 'dur': round(len(y) / SR, 2)}

def do_extract(key, words, frac, target_dur):
    best = None
    for w in words:
        b = best_take(w, [0.80, 0.76, 0.84], tone(w), lambda s, w=w: tidy_smooth(stretch(cut_initial(s, w, frac), target=target_dur)))
        if b and (best is None or b[0] < best[0][0]): best = (b, w)
        if best and best[0][0] < 1.0: break
    if best is None:
        fails.append(key); print(f'  !! {key}: không cắt được từ {words}', flush=True); return
    (bad, y, how, h, c, sp), w = best
    put(key, y, f'(trích từ {w}, {how})'); rep[key]['f0'] = c
    print(f'  {key} ← {w} [{how} sp={sp}] F0 {c} lệch={bad:.1f} {rep[key]["dur"]}s', flush=True)

# 1. Vần: vần mở, vần mũi lấy từ tiếng thanh ngang; vần khép lấy từ tiếng thanh sắc
VAN_MAP = {
    'ai': (['tai', 'mai'], 0.32), 'ay': (['tay', 'bay'], 0.32), 'ây': (['mây', 'cây'], 0.32), 'oi': (['voi', 'coi'], 0.32),
    'ôi': (['tôi', 'đôi'], 0.32), 'ơi': (['bơi', 'chơi'], 0.32), 'ui': (['vui', 'túi'], 0.30), 'ao': (['sao', 'cao'], 0.35),
    'au': (['cau', 'rau'], 0.32), 'âu': (['câu', 'sâu'], 0.32), 'eo': (['keo', 'meo'], 0.32), 'êu': (['kêu', 'nêu'], 0.30),
    'iu': (['hiu', 'xiu'], 0.30), 'ưu': (['hưu', 'mưu'], 0.32), 'ua': (['cua', 'vua'], 0.32), 'ưa': (['mưa', 'cưa'], 0.32), 'oa': (['hoa', 'loa'], 0.32),
    'am': (['cam', 'tam'], 0.32), 'ăm': (['chăm', 'tăm'], 0.32), 'âm': (['mâm', 'tâm'], 0.32), 'em': (['kem', 'tem'], 0.32),
    'êm': (['đêm', 'thêm'], 0.32), 'im': (['chim', 'tim'], 0.35), 'ôm': (['tôm', 'chôm'], 0.32), 'ơm': (['cơm', 'thơm'], 0.32), 'um': (['chum', 'tum'], 0.35),
    'an': (['ban', 'can'], 0.32), 'ăn': (['khăn', 'chăn'], 0.32), 'ân': (['sân', 'cân'], 0.32), 'en': (['sen', 'khen'], 0.32),
    'ên': (['tên', 'lên'], 0.32), 'in': (['pin', 'xin'], 0.32), 'on': (['con', 'non'], 0.32), 'ơn': (['sơn', 'cơn'], 0.32), 'un': (['giun', 'run'], 0.32),
    'ang': (['sang', 'vang'], 0.32), 'ăng': (['măng', 'trăng'], 0.32), 'ong': (['song', 'bong'], 0.32), 'ông': (['sông', 'công'], 0.32),
    'ung': (['sung', 'cung'], 0.32), 'ưng': (['lưng', 'bưng'], 0.32), 'anh': (['chanh', 'xanh'], 0.35), 'inh': (['xinh', 'tinh'], 0.32),
    'ac': (['bác', 'các'], 0.32), 'oc': (['sóc', 'cóc'], 0.32), 'ôc': (['cốc', 'tốc'], 0.32), 'uc': (['cúc', 'súc'], 0.32),
    'ưc': (['đức', 'sức'], 0.32), 'ach': (['sách', 'khách'], 0.35), 'êch': (['ếch'], 0.00), 'ich': (['thích', 'xích'], 0.35),
    'at': (['hát', 'cát'], 0.32), 'ăt': (['bắt', 'cắt'], 0.32), 'ât': (['tất', 'cất'], 0.32), 'et': (['két', 'hét'], 0.32),
    'it': (['mít', 'thít'], 0.32), 'ôt': (['tốt', 'cốt'], 0.32), 'ơt': (['ớt'], 0.00), 'ut': (['bút', 'hút'], 0.32),
    'ap': (['tháp', 'cáp'], 0.35), 'ăp': (['bắp', 'sắp'], 0.32), 'âp': (['gấp', 'cấp'], 0.32), 'ep': (['dép', 'kép'], 0.32),
    'êp': (['bếp', 'xếp'], 0.32), 'op': (['góp', 'cóp'], 0.32), 'ôp': (['cốp', 'tốp'], 0.32), 'ơp': (['lớp', 'chớp'], 0.32),
}
print('=== 1. VẦN ===', flush=True)
for van, (words, frac) in VAN_MAP.items():
    if ONLY is None or van in ONLY: do_extract(van, words, frac, 0.33)

# 2. Chữ cái nguyên âm; ă đọc "á", â đọc "ớ" (tên chữ theo sách, khóa 'á' và 'ớ' trong app)
LETTER_MAP = {
    'a': (['ma', 'ca'], 0.33), 'o': (['bo', 'co', 'to'], 0.35), 'ô': (['cô', 'tô', 'bô'], 0.33), 'ơ': (['bơ', 'cơ', 'tơ'], 0.33),
    'u': (['thu', 'cu', 'tu'], 0.35), 'ư': (['thư', 'tư', 'sư'], 0.35), 'e': (['xe', 'me'], 0.33), 'ê': (['lê', 'tê'], 0.33),
    'i': (['bi', 'ti'], 0.32), 'á': (['lá', 'cá'], 0.33), 'ớ': (['mớ', 'vớ'], 0.33),
}
print('=== 2. NGUYÊN ÂM ===', flush=True)
for key, (words, frac) in LETTER_MAP.items():
    if ONLY is None or key in ONLY: do_extract(key, words, frac, 0.33)

# 3. Phụ âm và tiếng cơ sở, số đếm: lấy nguyên tiếng giữa câu, giữ đúng thanh, không dính từ sau
CONSONANTS = ['bờ', 'cờ', 'dờ', 'đờ', 'gờ', 'hờ', 'ca', 'lờ', 'mờ', 'nờ', 'pờ', 'quờ', 'rờ', 'sờ', 'tờ', 'vờ', 'xờ',
              'i ngắn', 'i dài', 'chờ', 'di', 'khờ', 'ngờ', 'nhờ', 'phờ', 'thờ', 'trờ']
BASES = ['bô', 'me', 'be', 'ga', 'gà', 'bo', 'bò', 'dê', 'hô', 'la', 'mu', 'du', 'cơ', 'rô', 'đa', 've', 'cu', 'bơ', 'bi',
         'so', 'xô', 'co', 'he', 'gô', 'vi', 'meo', 'voi', 'sao', 'tao', 'hoa', 'keo', 'toi', 'tau', 'rua',
         'rau', 'cáo', 'đan', 'cún', 'hươu', 'tai', 'rổ', 'tôm', 'kem']
NUMS = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười']
print('=== 3. PHỤ ÂM, TIẾNG CƠ SỞ, SỐ ===', flush=True)
for key in [k for k in CONSONANTS + BASES + NUMS if ONLY is None or k in ONLY]:
    cls = tone(key) if ' ' not in key else 'any'
    b = best_take(key, [0.76, 0.80, 0.72], cls, tidy_smooth)
    if b is None:
        fails.append(key); print(f'  !! {key}: không cắt được', flush=True); continue
    bad, y, how, h, c, sp = b
    put(key, y, f'{h} ({how})', True if how == 'heard' else 'carrier'); rep[key]['f0'] = c
    print(f'  {key} [{how} sp={sp}] nghe="{h}" F0 {c} lệch={bad:.1f} {rep[key]["dur"]}s', flush=True)

json.dump(V, open(VOICE, 'w', encoding='utf-8'), ensure_ascii=False)
json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('Lỗi:', fails)
subprocess.run(['python3', os.path.join(ROOT, 'tools', 'build.py')], check=True)
