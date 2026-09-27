"""v15: vần và nguyên âm chữ cái (giọng chính vais1000), có kiểm tra đường đi formant bằng Praat.
v14 bỏ phụ âm đầu bằng cách dò "hết tiếng xì" nên cắt lấn mất nguyên âm đầu của vần đôi (ai chỉ còn "i", ay còn "ê"),
và phép đo cũ chỉ đo giữa clip nên không bắt được. Ở đây:
- Nguyên âm mẫu (a, i, u, o, ô, ơ, ư, e, ê) đo từ chính giọng này trong các tiếng thật (ta, ti, tu…).
- Mỗi vần có đường đi chuẩn: ai, ay = a → i; ây, ơi = ơ → i; ao, au = a → u; oa = o → a; vần mũi, vần khép có nguyên âm chính đúng.
- Ứng viên tạo bằng nhiều cách (bỏ phụ âm đầu tại chỗ dây thanh bắt đầu rung; cách v14; đọc thẳng vần trong câu);
  chỉ nhận bản có đầu, cuối, nguyên âm chính đúng; ngân dài ở nguyên âm chính rồi đo lại.
Chạy từ thư mục gốc: python3 tools/tts/fix_v15.py [--only ai,ay] [--part out.json]"""
import os, sys, json
_ARGS = sys.argv[1:]
_D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(_D, 'fix_v14.py'), encoding='utf-8').read().split("if __name__ == '__main__':")[0]
     .replace("os.path.join(_D, 'fix_v12.py'), encoding", "os.path.join(_D, 'fix_v12.py'), encoding").replace('_ARGS = sys.argv[1:]', ''))
ARGS = _ARGS
import parselmouth

VOW = ['a', 'i', 'u', 'o', 'ô', 'ơ', 'ư', 'e', 'ê']
REF_WORDS = {'a': ['ta', 'ca'], 'i': ['ti', 'thi'], 'u': ['tu', 'thu'], 'o': ['to', 'co'], 'ô': ['tô', 'cô'], 'ơ': ['tơ', 'cơ'],
             'ư': ['tư', 'thư'], 'e': ['te', 'xe'], 'ê': ['tê', 'khê']}
# (đầu, cuối) của vần đôi; tập hợp nghĩa là chấp nhận một trong các nguyên âm
GLIDE = {'ai': ('a', 'i'), 'ay': ('a', 'iê'), 'ây': ('ơ', 'iê'), 'oi': ('oô', 'iê'), 'ôi': ('ô', 'iê'), 'ơi': ('ơ', 'iê'),
         'ui': ('u', 'iê'), 'ao': ('a', 'uoô'), 'au': ('a', 'uoô'), 'âu': ('ơ', 'uô'), 'eo': ('e', 'uoô'), 'êu': ('ê', 'uô'),
         'iu': ('iê', 'u'), 'ưu': ('ư', 'u'), 'ua': ('uô', 'ơa'), 'ưa': ('ư', 'ơa'), 'oa': ('uoô', 'a')}
NUC = {'am': 'a', 'ăm': 'a', 'âm': 'ơ', 'em': 'e', 'êm': 'ê', 'im': 'i', 'ôm': 'ô', 'ơm': 'ơ', 'um': 'u',
       'an': 'a', 'ăn': 'a', 'ân': 'ơ', 'en': 'e', 'ên': 'ê', 'in': 'i', 'on': 'o', 'ơn': 'ơ', 'un': 'u',
       'ang': 'a', 'ăng': 'a', 'ong': 'oô', 'ông': 'ô', 'ung': 'u', 'ưng': 'ư', 'anh': 'aeê', 'inh': 'i',
       'ac': 'a', 'oc': 'oô', 'ôc': 'ô', 'uc': 'u', 'ưc': 'ư', 'ach': 'aeê', 'êch': 'ê', 'ich': 'i',
       'at': 'a', 'ăt': 'a', 'ât': 'ơ', 'et': 'e', 'it': 'i', 'ôt': 'ô', 'ơt': 'ơ', 'ut': 'u',
       'ap': 'a', 'ăp': 'a', 'âp': 'ơ', 'ep': 'e', 'êp': 'ê', 'op': 'o', 'ôp': 'ô', 'ơp': 'ơ',
       'a': 'a', 'i': 'i', 'u': 'u', 'o': 'o', 'ô': 'ô', 'ơ': 'ơ', 'ư': 'ư', 'e': 'e', 'ê': 'ê', 'á': 'a', 'ớ': 'ơ'}

def fmt(y, t0, t1):
    """F1, F2 trung vị (Praat Burg, trần 5000Hz) trong đoạn [t0, t1] giây."""
    snd = parselmouth.Sound(y.astype(np.float64), SR)
    fo = snd.to_formant_burg(time_step=0.005, max_number_of_formants=5, maximum_formant=5000)
    ts = [t for t in np.arange(t0, t1, 0.005)]
    f1 = [fo.get_value_at_time(1, t) for t in ts]; f2 = [fo.get_value_at_time(2, t) for t in ts]
    p = [(a, b) for a, b in zip(f1, f2) if a == a and b == b]
    return (float(np.median([a for a, _ in p])), float(np.median([b for _, b in p]))) if p else None

def voiced_span(y):
    snd = parselmouth.Sound(y.astype(np.float64), SR); pi = snd.to_pitch(time_step=0.005, pitch_floor=120, pitch_ceiling=500)
    v = [pi.xs()[i] for i in range(pi.n_frames) if pi.selected_array['frequency'][i] > 0]
    return (v[0], v[-1]) if len(v) > 4 else None

REF = {}
def build_ref():
    for v, ws in REF_WORDS.items():
        pts = []
        for w in ws:
            for sp in (0.76, 0.8):
                r = extract(gen(CARRIERS[0].format(w), sp), CARRIERS[0], w)
                if r is None: continue
                vs = voiced_span(r[0])
                if not vs: continue
                a, b = vs; F = fmt(r[0], a + (b - a) * 0.4, a + (b - a) * 0.7)
                if F: pts.append(np.log(F))
        REF[v] = np.median(np.array(pts), 0)

def nearest(F):
    x = np.log(F); d = {v: float(np.linalg.norm(x - REF[v])) for v in REF}
    return sorted(d.items(), key=lambda kv: kv[1])

# Hướng lướt của vần đôi (cuối trừ đầu, Hz): giọng máy đo formant tuyệt đối không ổn định, nhưng hướng lướt thì chắc chắn.
# (dF1 nhỏ nhất, dF1 lớn nhất, dF2 nhỏ nhất, dF2 lớn nhất); None là không ràng buộc
MOVE = {'ai': (None, -80, 250, None), 'ay': (None, -60, 250, None), 'ây': (None, None, 250, None),
        'oi': (None, None, 400, None), 'ôi': (None, None, 400, None), 'ơi': (None, None, 350, None), 'ui': (None, None, 500, None),
        'ao': (None, None, None, -250), 'au': (None, None, None, -250), 'âu': (None, None, None, -250),
        'eo': (None, None, None, -300), 'êu': (None, None, None, -400), 'iu': (None, None, None, -500), 'ưu': (None, None, None, -400),
        'ua': (50, None, 100, None), 'ưa': (50, None, None, None), 'oa': (100, None, None, None)}
OPEN_START = {'ai', 'ay', 'ao', 'au'}      # bắt đầu bằng a: đầu phải mở hơn cuối rõ rệt

def check(key, y):
    """Trả về (đạt?, điểm lệch, mô tả). Vần đôi: đo hướng lướt đầu (8-22%) → cuối (78-92%). Nguyên âm đơn: đo nguyên âm chính (25-60%)."""
    vs = voiced_span(y)
    if not vs: return False, 9, 'không có tiếng'
    a, b = vs; L = b - a
    if key in MOVE:
        s = fmt(y, a + L * 0.08, a + L * 0.22); e = fmt(y, a + L * 0.78, a + L * 0.92)
        if not s or not e: return False, 9, 'không đo được'
        d1, d2 = e[0] - s[0], e[1] - s[1]; lo1, hi1, lo2, hi2 = MOVE[key]
        ok = (lo1 is None or d1 >= lo1) and (hi1 is None or d1 <= hi1) and (lo2 is None or d2 >= lo2) and (hi2 is None or d2 <= hi2)
        if key in OPEN_START: ok = ok and s[0] >= e[0] + 80
        mag = abs(d2) + abs(d1)
        return ok, 1000.0 / (mag + 50), f'F1 {int(s[0])}→{int(e[0])}, F2 {int(s[1])}→{int(e[1])}'
    n = fmt(y, a + L * 0.25, a + L * 0.60)
    if not n: return False, 9, 'không đo được'
    nn = nearest(n); want = NUC[key]
    return nn[0][0] in want, min(d for v, d in nn if v in want), nn[0][0]

def strip_voicing(seg):
    """Bỏ phụ âm đầu vô thanh tại chỗ dây thanh bắt đầu rung (Praat), không dò thêm."""
    vs = voiced_span(seg)
    if not vs: return None
    st = max(0, int((vs[0] + 0.012) * SR))
    return seg[st:] if len(seg) - st > int(SR * 0.08) else None

def lengthen_at(y, target, pos):
    """Ngân dài ở vị trí pos (tỉ lệ trong phần có tiếng): vần "ai" ngân ở "a", vần "oa" ngân ở "a" cuối."""
    global lengthen
    db, f = db_env(y); on = np.where(db > -30)[0]
    if not len(on): return y
    a, b = on[0] * f, (on[-1] + 1) * f
    d = (b - a) / SR
    if d >= target * 0.97: return y
    m = a + int((b - a) * pos)
    v = f0(y); hop = int(SR * 0.01); ks = [i for i in range(len(v)) if not np.isnan(v[i])]
    if not ks: return y
    kc = min(ks, key=lambda i: abs(i * hop + int(SR * 0.015) - m)); T = int(round(SR / v[kc]))
    if m - T < 0 or m + T > len(y): return y
    frame = y[m - T:m + T] * np.hanning(2 * T).astype(np.float32)
    extra = int((target - d) * SR); n = extra // T + 3
    ola = np.zeros(n * T + 2 * T, np.float32)
    for k in range(n): ola[k * T:k * T + 2 * T] += frame
    seg = ola[T:T + extra]; seg *= (np.sqrt(np.mean(y[m - T:m + T] ** 2)) + 1e-9) / (np.sqrt(np.mean(seg ** 2)) + 1e-9)
    x = min(T, int(SR * 0.006)); r = np.linspace(0, 1, x, dtype=np.float32)
    left, right = y[:m].copy(), y[m:].copy()
    seg[:x] = seg[:x] * r + left[-x:] * (1 - r); left = left[:-x]
    seg[-x:] = seg[-x:] * (1 - r) + right[:x] * r; right = right[x:]
    return np.concatenate([left, seg, right]).astype(np.float32)

def clean_onset(y):
    """Đầu clip là nguyên âm ngay: từ lúc có tiếng (-35dB) tới lúc dây thanh rung (Praat) không quá 15ms (không còn tiếng bật, tiếng xì)."""
    vs = voiced_span(y)
    if not vs: return False
    db, f = db_env(y); on = np.where(db > -35)[0]
    return bool(len(on)) and vs[0] - on[0] * f / SR <= 0.015

def pos_of(key):
    if key in ('oa',): return 0.70
    if key in GLIDE: return 0.22
    return 0.35

EXTRA = {'ai': ['sai', 'chai', 'khai', 'xai'], 'iu': ['khiu', 'tiu', 'chiu', 'xiu'], 'ua': ['xua', 'tua', 'khua', 'sua'], 'ưa': ['chưa', 'sưa', 'khưa'],
         'oa': ['thoa', 'xoa', 'toa', 'khoa']}

def candidates(key):
    """(clip thô, cách tạo, tiếng nguồn)"""
    for w in SOURCES.get(key, []) + EXTRA.get(key, []):
        for sp in (0.76, 0.72, 0.80, 0.68):
            for carrier in CARRIERS[:2]:
                r = extract(gen(carrier.format(w), sp), carrier, w)
                if r is None or not edges_quiet(r[0]): continue
                for how, fn in (('rung', strip_voicing), ('v14', strip_initial)):
                    v = fn(r[0])
                    if v is not None: yield v, how, w
    src = CLOSED.get(key, key)
    for sp in (0.76, 0.72):
        for carrier in CARRIERS:
            r = extract(gen(carrier.format(src), sp), carrier, src)
            if r is not None and edges_quiet(r[0]): yield r[0], 'đọc thẳng', src

def take15(key):
    cls = 'sac' if key in CLOSED or key in ('á', 'ớ') else 'ngang'; best = None; n = 0
    for raw, how, w in candidates(key):
        n += 1
        ok, miss, desc = check(key, raw)
        if not ok or not clean_onset(raw): continue
        y = tidy_smooth(lengthen_at(raw, target_of(key), pos_of(key)), tail=0.12)
        ok2, miss2, desc2 = check(key, y)
        if not ok2: continue
        bad, c = tone_bad(y, cls)
        score = miss2 + 0.3 * bad + (5.0 if how == 'đọc thẳng' else 0)   # đọc thẳng sau "đọc" dễ bị nối âm c: chỉ dùng khi không còn cách nào
        if best is None or score < best[0]: best = (score, y, how, w, desc2, c)
    return best, n

if __name__ == '__main__':
    keys = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else list(MOVE)
    build_ref()
    print('nguyên âm mẫu (F1, F2):', {v: [int(x) for x in np.exp(REF[v])] for v in REF}, flush=True)
    V = json.load(open(os.path.join(ROOT, 'voice.json'), encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
    out = {}
    for i, key in enumerate(keys):
        cur = check(key, dec(V[key])) if key in V else (False, 9, '')
        b, n = take15(key)
        if b is None:
            print(f'[{i + 1}/{len(keys)}] {key}: {n} ứng viên, không bản nào đúng đường đi; bản đang chạy {cur[2]} ({"đạt" if cur[0] else "SAI"})', flush=True); continue
        score, y, how, w, desc, c = b
        out[key] = [mp3hq(y), {'mode': 'short', 'ok': 'formant', 'heard': desc, 'v': 15, 'src': f'{w} ({how})', 'f0': c,
                               'core': round(core_dur(y), 2), 'dur': round(len(y) / SR, 2)}]
        print(f'[{i + 1}/{len(keys)}] {key} ← {w} ({how}) {desc} lệch {score:.2f} F0 {c} dài {out[key][1]["core"]}s | đang chạy: {cur[2]} ({"đạt" if cur[0] else "SAI"})', flush=True)
    pth = ARGS[ARGS.index('--part') + 1] if '--part' in ARGS else os.path.join(_D, 'v15_out.json')
    json.dump(out, open(pth, 'w', encoding='utf-8'), ensure_ascii=False)
