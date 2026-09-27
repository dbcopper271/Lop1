"""v12: cắt âm từ câu mang mà tiếng đứng trước tận cùng bằng âm tắc và tiếng đứng sau bắt đầu bằng "cho",
nên hai đầu clip nằm trong khoảng lặng thật (không dính tiếng bên cạnh). Mỗi clip phải qua cổng kiểm tra:
hai đầu lặng, độ dài hợp lý, ghép sau "Bây giờ cô đọc chữ" thì máy không nghe ra tiếng của câu mang.
Chọn bản đúng thanh theo cao độ F0. Không qua cổng thì giữ nguyên âm cũ.
Câu dài đọc sau lời dẫn "Rồi, cô đọc:", cắt ở khoảng lặng sau "đọc", giữ trọn đuôi câu.
Bản mới chỉ thay bản cũ khi máy nghe lại không kém bản cũ.
Chạy từ thư mục gốc:
  python3 tools/tts/fix_v12.py                      tạo lại mọi câu, ghi voice.json rồi dựng app
  python3 tools/tts/fix_v12.py --keys k.json --part out.json   chỉ các câu trong k.json, ghi kết quả ra out.json
  python3 tools/tts/fix_v12.py --merge a.json b.json ...        gộp các phần vào voice.json rồi dựng app"""
import json, os, sys, subprocess, unicodedata
import numpy as np

ARGS = sys.argv[1:]
sys.argv = [sys.argv[0]]
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, 'gen.py'), encoding='utf-8').read().split("phr = json.load")[0])
ROOT = os.path.join(D, '..', '..')
HOP = 0.005

def words_ts(x):
    s = asr.create_stream(); s.accept_waveform(16000, resample(x)); asr.decode_stream(s)
    W, T = [], []
    for tok, t in zip(s.result.tokens, s.result.timestamps):
        if tok.startswith(' ') or not W: W.append(tok.strip().lower()); T.append(t)
        else: W[-1] += tok.strip().lower()
    return [clean(w) for w in W], T

def db_env(x):
    e, f = env(x); return 20 * np.log10(e / (e.max() + 1e-9)), f

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
    for ch in unicodedata.normalize('NFD', word.split()[-1]):
        if ch in marks: return marks[ch]
    return 'ngang'

def tone_bad(y, cls):
    c = contour(y)
    if c is None: return 6.0, c
    if cls == 'ngang': return abs(c['drop']) + 0.5 * max(0, c['rng'] - 2), c
    if cls == 'sac': return max(0.0, 4 - c['drop']) + 0.5 * max(0.0, c['drop'] - 9), c
    if cls == 'huyen': return max(0.0, c['drop'] + 1), c
    return 0.0, c

def tidy_smooth(y, lead=0.015, tail=0.09):
    db, f = db_env(y); on = np.where(db > -48)[0]
    if len(on):
        st = max(0, on[0] * f - int(SR * 0.015)); en = min(len(y), (on[-1] + 1) * f + int(SR * 0.035)); y = y[st:en]
    y = y / (np.abs(y).max() + 1e-9) * 0.93
    fi = min(len(y), int(SR * 0.004)); y[:fi] *= np.linspace(0, 1, fi)
    fo = min(len(y), int(SR * 0.012)); y[-fo:] *= np.linspace(1, 0, fo)
    return np.concatenate([np.zeros(int(SR * lead), np.float32), y, np.zeros(int(SR * tail), np.float32)])

def stretch(y, target):
    if target <= 0: return y
    db, f = db_env(y); on = np.where(db > -32)[0]
    ms = (on[-1] - on[0] + 1) * f / SR if len(on) else 0
    if ms <= 0: return y
    tempo = max(0.72, min(1.0, ms / target))
    if tempo >= 0.98: return y
    z = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-filter:a', f'atempo={tempo:.3f}', '-f', 'f32le', '-'],
                       input=y.astype(np.float32).tobytes(), capture_output=True).stdout
    return np.frombuffer(z, dtype=np.float32).copy()

def quiet_runs(db, lo, hi, thr):
    """Các đoạn liên tiếp dưới ngưỡng thr (dB so với đỉnh cả câu) trong [lo, hi) (chỉ số khung)."""
    runs, i = [], lo
    while i < hi:
        if db[i] < thr:
            j = i
            while j < hi and db[j] < thr: j += 1
            runs.append((i, j)); i = j
        else: i += 1
    return runs

def cut_between(x, t_prev, t_next, thr=-30, min_q=3):
    """Tiếng đích nằm giữa khoảng lặng sau tiếng đứng trước (bắt đầu từ t_prev) và khoảng lặng ngay trước tiếng đứng sau (t_next)."""
    db, f = db_env(x); db = np.convolve(db, np.ones(2) / 2, 'same')
    lo, hi = int((t_prev + 0.08) / HOP), min(len(db), int((t_next + 0.06) / HOP))
    runs = quiet_runs(db, lo, hi, thr)
    first = next((r for r in runs if r[1] - r[0] >= min_q), None)
    if first is None: return None
    tail = [r for r in runs if r[0] >= first[1] + int(0.1 / HOP) and r[1] - r[0] >= 2]
    if not tail: return None
    a, b = first, tail[-1]
    # Âm mũi cuối tiếng (n, m, ng, nh) nhỏ, thường dưới -30dB: dò tiếp tới khi thật sự tắt (-40dB) để không cụt đuôi
    e0 = b[0]
    while e0 < b[1] and db[e0] >= -40: e0 += 1
    st = max(a[0], a[1] - int(0.03 / HOP)) * f; en = min(b[1], e0 + int(0.03 / HOP)) * f
    if not (int(SR * 0.12) <= en - st <= int(SR * 0.9)): return None
    return st, en

# Tiếng đứng trước tận cùng bằng âm tắc (khoảng lặng thật), tiếng đứng sau là "cho" (âm tắc xát, có khoảng lặng trước)
CARRIERS = ['Bây giờ cô đọc {} cho em nghe.', 'Nào, cô đọc {} cho em nghe.', 'Cô sẽ đọc {} cho cả lớp nghe.']
BANNED = {'bây', 'giờ', 'cô', 'đọc', 'cho', 'em', 'nghe', 'nào', 'sẽ', 'cả', 'lớp', 'nhé', 'chữ'}

def extract(x, carrier, target):
    tg = clean(target).split(); cw = clean(carrier.format(target)).split(); p = cw.index(tg[0]); n = len(tg)
    W, T = words_ts(x)
    try:
        i_prev = max(i for i in range(min(len(W), p)) if W[i] == cw[p - 1])
        i_next = next(i for i in range(i_prev + 1, len(W)) if W[i] == cw[p + n])
    except (ValueError, StopIteration):
        return None
    r = cut_between(x, T[i_prev], T[i_next])
    if r is None: return None
    return x[r[0]:r[1]], ' '.join(W[i_prev + 1:i_next])

AUDIT_PRE = None
def audit(y, target):
    """Ghép clip sau "Bây giờ cô đọc chữ"; máy nghe ra tiếng của câu mang thì loại."""
    global AUDIT_PRE
    if AUDIT_PRE is None:
        AUDIT_PRE = gen('Bây giờ cô đọc chữ', 0.85); AUDIT_PRE = AUDIT_PRE / np.abs(AUDIT_PRE).max() * 0.9
    x = np.concatenate([AUDIT_PRE, np.zeros(int(SR * 0.06), np.float32), y, np.zeros(int(SR * 0.3), np.float32)])
    h = clean(hear(x)[0]).split()[5:]; tg = set(clean(target).split())
    return not any(w in BANNED and w not in tg for w in h), ' '.join(h)

def edges_quiet(y):
    """Hai đầu clip (trước khi đệm) phải lặng hơn đỉnh 25dB: không có mẩu tiếng bên cạnh."""
    db, f = db_env(y); k = max(1, int(0.015 / HOP))
    return len(db) > 2 * k and db[:k].max() < -25 and db[-k:].max() < -25


def dec(b):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', '-', '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], input=base64.b64decode(b), capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def take(src, stretch_to):
    """Nhiều bản của tiếng src; chỉ nhận bản máy nghe lại đúng đủ từng chữ. Không có bản nào đúng (tiếng chưa dấu khi đánh vần,
    máy không nhận được) thì nhận bản đủ số tiếng, đủ dài. Trong các bản nhận được, chọn bản đúng thanh."""
    n = len(clean(src).split()); cls = tone(src) if n == 1 else 'any'; best = None; tries = 0
    for sp in [0.76, 0.72, 0.80, 0.68]:
        for carrier in CARRIERS:
            tries += 1
            r = extract(gen(carrier.format(src), sp), carrier, src)
            if r is None or not edges_quiet(r[0]): continue
            y = tidy_smooth(stretch(r[0], stretch_to))
            ok, h = audit(y, src)
            if not ok: continue
            exact = h == clean(src)
            if not exact and (len(h.split()) not in (0, n) or core_len(y) < 0.22 * n): continue
            bad, c = tone_bad(y, cls); ctx = r[1] == clean(src)
            score = bad + (0 if exact else 0.7 if ctx else 1.5)
            if best is None or score < best[0]: best = (score, y, h, c, sp, exact, ctx)
        if best and best[5] and best[0] <= 1.0: break
    return best, tries

def core_len(y):
    db, f = db_env(y); on = np.where(db > -30)[0]
    return (on[-1] - on[0] + 1) * f / SR if len(on) else 0.0

LEAD = 'Rồi, cô đọc: '
LEAD_W = {'rồi', 'cô', 'đọc'}

def hear_alone(y):
    x = np.concatenate([np.zeros(int(SR * 0.2), np.float32), y, np.zeros(int(SR * 0.3), np.float32)])
    return clean(hear(x)[0])

def long_score(text, h):
    import difflib
    t = clean(text); hw, tw = h.split(), t.split()
    if hw and tw and hw[0] in LEAD_W and hw[0] != tw[0]: return 0.0
    return difflib.SequenceMatcher(None, t, h).ratio()

def long_take(text):
    best = None
    variants = [text] + ([text.replace(', ', '. ')] if ', ' in text else [])
    for variant in variants:
        for sp in [0.9, 0.86, 0.94, 0.88]:
            x = gen(LEAD + variant, sp); W, T = words_ts(x)
            i = next((j for j in range(min(4, len(W))) if W[j] == 'đọc'), None)
            if i is None: continue
            db, f = db_env(x); db = np.convolve(db, np.ones(2) / 2, 'same')
            lo = int((T[i] + 0.08) / HOP); hi = min(len(db), lo + int(0.35 / HOP))
            run = next((r for r in quiet_runs(db, lo, hi, -30) if r[1] - r[0] >= 3), None)
            if run is None: continue
            seg = x[max(run[0], run[1] - int(0.03 / HOP)) * f:]
            if not edges_quiet(seg): continue
            y = tidy_smooth(seg); h = hear_alone(y); sc = long_score(text, h)
            if best is None or sc > best[0]: best = (sc, y, h, sp)
            if sc >= 0.97: return best
        if best and best[0] >= 0.9: return best
    return best

OPEN = ['ai', 'ay', 'ây', 'oi', 'ôi', 'ơi', 'ui', 'ao', 'au', 'âu', 'eo', 'êu', 'iu', 'ưu', 'ua', 'ưa', 'oa',
        'am', 'ăm', 'âm', 'em', 'êm', 'im', 'ôm', 'ơm', 'um', 'an', 'ăn', 'ân', 'en', 'ên', 'in', 'on', 'ơn', 'un',
        'ang', 'ăng', 'ong', 'ông', 'ung', 'ưng', 'anh', 'inh']
# Vần khép đọc lên giọng như thanh sắc; vần mở, vần mũi đọc thẳng cả tiếng thanh ngang
CLOSED = {'ac': 'ác', 'oc': 'óc', 'ôc': 'ốc', 'uc': 'úc', 'ưc': 'ức', 'ach': 'ách', 'êch': 'ếch', 'ich': 'ích',
          'at': 'át', 'ăt': 'ắt', 'ât': 'ất', 'et': 'ét', 'it': 'ít', 'ôt': 'ốt', 'ơt': 'ớt', 'ut': 'út',
          'ap': 'áp', 'ăp': 'ắp', 'âp': 'ấp', 'ep': 'ép', 'êp': 'ếp', 'op': 'óp', 'ôp': 'ốp', 'ơp': 'ớp'}
LETTERS = ['a', 'á', 'ớ', 'e', 'ê', 'i', 'o', 'ô', 'ơ', 'u', 'ư']   # ă đọc "á", â đọc "ớ" (khóa 'á', 'ớ' trong app)

def job(key):
    if key in CLOSED: return CLOSED[key], 0.34
    if key in OPEN: return key, 0.38
    if key in LETTERS: return key, 0.42
    return key, (0.36 if len(clean(key).split()) == 1 else 0.0)

def run_short(key, V):
    src, st = job(key)
    best, tries = take(src, st)
    old_h = audit(dec(V[key]), src) if key in V else (False, '')
    old_exact = old_h[0] and old_h[1] == clean(src)   # bản cũ nghe thừa/thiếu chữ thì không được giữ
    if best is None: return None, f'không có bản qua cổng ({tries} lần), giữ cũ'
    score, y, h, c, sp, exact, ctx = best
    if old_exact and not exact: return None, f'cũ nghe đúng "{old_h[1]}", mới nghe "{h}": giữ cũ'
    info = {'mode': 'short', 'ok': True if exact else 'ctx' if ctx else 'gate', 'heard': h, 'v': 12, 'src': src, 'f0': c, 'dur': round(len(y) / SR, 2)}
    return (mp3(y), info), f'← {src} sp={sp} nghe="{h}" {"ĐÚNG" if exact else "đúng-trong-câu" if ctx else "khác"} F0 {c} điểm={score:.1f} {info["dur"]}s'

import re
# Giọng máy đọc dồn "e, ê, i" (dấu phẩy không tạo chỗ ngắt) và lướt tên chữ giữa câu: ghép câu từ đoạn chữ và clip tên chữ
SPLICE = [
    (re.compile(r'^(.*?)\be, ê, i\b,?\s*(.*)$'), lambda m: [('t', m[1]), ('k', 'e'), ('k', 'ê'), ('k', 'i'), ('t', m[2])]),
    (re.compile(r'^Bé hãy tìm chữ ghi âm (.+) nhé\.$'), lambda m: [('t', 'Bé hãy tìm chữ ghi âm'), ('k', m[1]), ('t', 'nhé')]),
    (re.compile(r'^Bé hãy tìm chữ (i ngắn|i dài|ca) nhé\.$'), lambda m: [('t', 'Bé hãy tìm chữ'), ('k', m[1]), ('t', 'nhé')]),
]
PIECES = {}

def piece(t):
    if t not in PIECES:
        if t == 'nhé':
            b = take(t, 0.0)[0]; PIECES[t] = b[1] if b else None
        else:
            b = long_take(t); PIECES[t] = b[1] if b else None
    return PIECES[t]

def spliced(key, V):
    for pat, fn in SPLICE:
        m = pat.match(key)
        if not m: continue
        parts = []
        for kind, v in fn(m):
            if kind == 't':
                if not v.strip(): continue
                y = piece(v)
            else:
                if v not in V: return None
                y = np.concatenate([np.zeros(int(SR * 0.06), np.float32), dec(V[v]), np.zeros(int(SR * 0.06), np.float32)])
            if y is None: return None
            parts.append(y / (np.abs(y).max() + 1e-9) * 0.93)
        return np.concatenate(parts)
    return None

def run_long(key, V):
    y = spliced(key, V)
    if y is not None:
        h = hear_alone(y); sc = long_score(key, h); old = long_score(key, hear_alone(dec(V[key])))
        # Câu quy tắc: máy nghe tên chữ kém nên không chấm được; bản cũ đo được là nuốt "ê, i", luôn dùng bản ghép
        if sc < old - 0.05 and 'e, ê, i' not in key: return None, f'ghép {sc:.2f} < cũ {old:.2f}: giữ cũ'
        info = {'mode': 'long', 'score': round(sc, 3), 'heard': h, 'v': 12, 'old': round(old, 3), 'spliced': True, 'dur': round(len(y) / SR, 2)}
        return (mp3(y), info), f'ghép {sc:.2f} (cũ {old:.2f}) "{h}"'
    best = long_take(key)
    old = long_score(key, hear_alone(dec(V[key]))) if key in V else 0.0
    if best is None: return None, f'không cắt được, giữ cũ ({old:.2f})'
    sc, y, h, sp = best
    if sc < old - 0.02: return None, f'mới {sc:.2f} < cũ {old:.2f}: giữ cũ'
    info = {'mode': 'long', 'score': round(sc, 3), 'heard': h, 'v': 12, 'old': round(old, 3), 'dur': round(len(y) / SR, 2)}
    return (mp3(y), info), f'mới {sc:.2f} (cũ {old:.2f}) sp={sp} "{h}"'

VOICE = os.path.join(ROOT, 'voice.json')

def build():
    subprocess.run(['python3', os.path.join(ROOT, 'tools', 'build.py')], check=True)

if __name__ == '__main__' and '--merge' in ARGS:
    V = json.load(open(VOICE, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
    for pth in ARGS[ARGS.index('--merge') + 1:]:
        for k, (b, info) in json.load(open(pth, encoding='utf-8')).items(): V[k] = b; rep[k] = info
    json.dump(V, open(VOICE, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    build(); sys.exit(0)

if __name__ == '__main__':
    V = json.load(open(VOICE, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
    keys = json.load(open(ARGS[ARGS.index('--keys') + 1], encoding='utf-8')) if '--keys' in ARGS else list(rep)
    out = {}; kept = []
    for i, key in enumerate(keys):
        if key not in V: continue
        long = rep.get(key, {}).get('mode') == 'long'
        res, msg = (run_long if long else run_short)(key, V)
        print(f'[{i + 1}/{len(keys)}] {key} {msg}', flush=True)
        if res is None: kept.append(key); continue
        out[key] = res
        if '--part' in ARGS and len(out) % 20 == 0:
            json.dump(out, open(ARGS[ARGS.index('--part') + 1], 'w', encoding='utf-8'), ensure_ascii=False)
    print('Giữ âm cũ:', len(kept), kept[:50])
    if '--part' in ARGS:
        json.dump(out, open(ARGS[ARGS.index('--part') + 1], 'w', encoding='utf-8'), ensure_ascii=False); sys.exit(0)
    for k, (b, info) in out.items(): V[k] = b; rep[k] = info
    json.dump(V, open(VOICE, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    build()
