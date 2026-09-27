"""v14: vần và nguyên âm chữ cái bằng giọng chính (vais1000), tách từ tiếng chuẩn rồi kéo dài cho đủ nghe.
- Đọc thẳng vần, nguyên âm (sau "đọc", ở đầu câu hay đứng riêng) thì giọng máy nối âm, đọc lệch nguyên âm và chỉ dài 0,1-0,2 giây:
  đo formant chỉ đúng 3/9 nguyên âm (u ra ê, ư ra ô, o ra a).
- Ở đây vần, nguyên âm được tách từ tiếng có phụ âm đầu vô thanh (tai → ai, thu → u, cốc → ôc): cắt tiếng ở khoảng lặng thật
  (cách của fix_v12), bỏ phụ âm đầu tại chỗ dây thanh bắt đầu rung và hết tiếng xì. Đo formant: đúng 8/9 nguyên âm.
- Kéo dài giữ nguyên cao độ (nguyên âm 0,45 giây, vần mở 0,42, vần khép 0,30) và kéo dài tên phụ âm dùng khi đánh vần vần.
- Các âm này nén 64kbps (câu khác 32kbps) cho rõ tiếng.
Chạy từ thư mục gốc: python3 tools/tts/fix_v14.py [--only ai,ô] [--dry]"""
import os, sys, json
_ARGS = sys.argv[1:]
_D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(_D, 'fix_v12.py'), encoding='utf-8').read().split("if __name__ == '__main__' and '--merge'")[0]
     .replace('__file__', repr(os.path.join(_D, 'fix_v12.py'))))
ARGS = _ARGS

SOURCES = {
    'ai': ['tai', 'cai', 'thai'], 'ay': ['tay', 'cay', 'say'], 'ây': ['cây', 'tây', 'thây'], 'oi': ['coi', 'soi', 'thoi'],
    'ôi': ['tôi', 'thôi', 'xôi'], 'ơi': ['chơi', 'khơi', 'tơi'], 'ui': ['tui', 'xui', 'thui'], 'ao': ['cao', 'sao', 'tao'],
    'au': ['cau', 'sau', 'thau'], 'âu': ['câu', 'sâu', 'châu'], 'eo': ['keo', 'theo', 'xeo'], 'êu': ['kêu', 'khêu', 'têu'],
    'iu': ['thiu', 'xiu', 'chiu'], 'ưu': ['sưu', 'cưu', 'khưu'], 'ua': ['cua', 'thua', 'chua'], 'ưa': ['cưa', 'thưa', 'xưa'],
    'oa': ['khoa', 'toa', 'xoa'], 'am': ['cam', 'tam', 'tham'], 'ăm': ['tăm', 'chăm', 'căm'], 'âm': ['tâm', 'câm', 'thâm'],
    'em': ['kem', 'tem', 'xem'], 'êm': ['thêm', 'têm', 'chêm'], 'im': ['tim', 'chim', 'kim'], 'ôm': ['tôm', 'xôm', 'chôm'],
    'ơm': ['thơm', 'cơm', 'sơm'], 'um': ['tum', 'chum', 'khum'], 'an': ['can', 'than', 'tan'], 'ăn': ['khăn', 'chăn', 'săn'],
    'ân': ['cân', 'sân', 'tân'], 'en': ['sen', 'khen', 'chen'], 'ên': ['tên', 'sên', 'kên'], 'in': ['xin', 'tin', 'pin'],
    'on': ['con', 'son', 'thon'], 'ơn': ['sơn', 'cơn', 'chơn'], 'un': ['thun', 'chun', 'xun'], 'ang': ['sang', 'thang', 'tang'],
    'ăng': ['căng', 'tăng', 'xăng'], 'ong': ['song', 'cong', 'chong'], 'ông': ['sông', 'công', 'thông'], 'ung': ['sung', 'cung', 'chung'],
    'ưng': ['sưng', 'chưng', 'tưng'], 'anh': ['chanh', 'xanh', 'tanh'], 'inh': ['xinh', 'tinh', 'kinh'],
    'ac': ['các', 'khác', 'tác'], 'oc': ['sóc', 'cóc', 'tóc'], 'ôc': ['cốc', 'tốc', 'xốc'], 'uc': ['cúc', 'súc', 'chúc'],
    'ưc': ['sức', 'tức', 'chức'], 'ach': ['sách', 'khách', 'cách'], 'êch': ['chếch', 'kếch', 'xếch'], 'ich': ['thích', 'xích', 'tích'],
    'at': ['cát', 'tát', 'sát'], 'ăt': ['cắt', 'sắt', 'tắt'], 'ât': ['tất', 'cất', 'chất'], 'et': ['két', 'tét', 'sét'],
    'it': ['xít', 'thít', 'tít'], 'ôt': ['tốt', 'cốt', 'sốt'], 'ơt': ['thớt', 'sớt', 'chớt'], 'ut': ['sút', 'chút', 'tút'],
    'ap': ['cáp', 'tháp', 'sáp'], 'ăp': ['sắp', 'cắp', 'tắp'], 'âp': ['cấp', 'tấp', 'sấp'], 'ep': ['kép', 'tép', 'xép'],
    'êp': ['xếp', 'kếp', 'tếp'], 'op': ['cóp', 'tóp', 'xóp'], 'ôp': ['cốp', 'tốp', 'xốp'], 'ơp': ['chớp', 'tớp', 'khớp'],
    # Nguyên âm chữ cái; ă đọc "á", â đọc "ớ" (khóa 'á', 'ớ' trong app)
    'a': ['ta', 'ca', 'tha'], 'o': ['to', 'co', 'tho'], 'ô': ['tô', 'thô', 'khô'], 'ơ': ['tơ', 'cơ', 'thơ'],
    'u': ['thu', 'tu', 'khu'], 'ư': ['thư', 'tư', 'sư'], 'e': ['xe', 'che', 'te'], 'ê': ['tê', 'khê', 'chê'],
    'i': ['ti', 'thi', 'chi'], 'á': ['cá', 'tá', 'khá'], 'ớ': ['tớ', 'sớ', 'khớ'],
}
LETTER_KEYS = {'a', 'o', 'ô', 'ơ', 'u', 'ư', 'e', 'ê', 'i', 'á', 'ớ'}
# Tên phụ âm, chữ ghép (bờ, cờ, ngờ…, i ngắn, i dài): chỉ ngân dài bản đang có
FINAL_NAMES = ['bờ', 'cờ', 'dờ', 'đờ', 'gờ', 'hờ', 'ca', 'lờ', 'mờ', 'nờ', 'pờ', 'quờ', 'rờ', 'sờ', 'tờ', 'vờ', 'xờ', 'i ngắn', 'i dài',
               'chờ', 'gờ kép', 'di', 'khờ', 'ngờ', 'ngờ kép', 'nhờ', 'phờ', 'thờ', 'trờ']

def zc(a):
    return float(np.mean(np.abs(np.diff(np.sign(a))) > 0)) if len(a) > 2 else 1.0

def strip_initial(seg):
    """Bỏ phụ âm đầu vô thanh: từ khung đầu có cao độ, dò tiếp từng 5ms tới khi hết tiếng xì/bật."""
    v = f0(seg); hop = int(SR * 0.01)
    k = next((i for i in range(len(v) - 3) if not np.isnan(v[i:i + 3]).any()), None)
    if k is None or k < 3: return None
    fr = int(SR * 0.005); st = k * hop
    ref = zc(seg[st + int(SR * 0.06):st + int(SR * 0.10)])
    lvl = np.sqrt(np.mean(seg[st + int(SR * 0.04):st + int(SR * 0.10)] ** 2)) + 1e-9
    for _ in range(12):
        w = seg[st:st + fr * 2]
        if zc(w) <= max(0.08, 1.6 * ref) and np.sqrt(np.mean(w ** 2)) > lvl * 0.15: break
        st += fr
    else:
        return None
    vow = seg[max(0, st - int(SR * 0.002)):]
    return vow if len(vow) >= int(SR * 0.10) else None

def core_dur(y):
    db, f = db_env(y); on = np.where(db > -30)[0]
    return (on[-1] - on[0] + 1) * f / SR if len(on) else 0.0

def atempo(y, factor):
    """Kéo dài factor lần giữ nguyên cao độ (atempo nối nhiều tầng, mỗi tầng ≥ 0,5)."""
    t, chain = 1.0 / factor, []
    while t < 0.5: chain.append('atempo=0.5'); t /= 0.5
    chain.append(f'atempo={t:.4f}')
    z = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-filter:a', ','.join(chain),
                        '-f', 'f32le', '-'], input=y.astype(np.float32).tobytes(), capture_output=True).stdout
    return np.frombuffer(z, dtype=np.float32).copy()

def lengthen(y, target):
    """Ngân dài nguyên âm: lặp chu kỳ dao động của dây thanh ở giữa phần có tiếng (chồng cửa sổ Hann theo chu kỳ, kiểu PSOLA).
    Giữ nguyên cao độ, màu âm, đoạn đầu và đoạn cuối; như cô giáo kéo dài "aaa"."""
    db, f = db_env(y); on = np.where(db > -30)[0]
    if not len(on): return y
    a, b = on[0] * f, (on[-1] + 1) * f; d = (b - a) / SR
    if d >= target * 0.97: return y
    v = f0(y); hop = int(SR * 0.01); m = a + int((b - a) * 0.4)
    ks = [i for i in range(len(v)) if not np.isnan(v[i])]
    if not ks: return y
    kc = min(ks, key=lambda i: abs(i * hop + int(SR * 0.015) - m)); T = int(round(SR / v[kc]))
    if m - T < 0 or m + T > len(y): return y
    frame = y[m - T:m + T] * np.hanning(2 * T).astype(np.float32)
    extra = int((target - d) * SR); n = extra // T + 3
    ola = np.zeros(n * T + 2 * T, np.float32)
    for k in range(n): ola[k * T:k * T + 2 * T] += frame
    seg = ola[T:T + extra]
    seg *= (np.sqrt(np.mean(y[m - T:m + T] ** 2)) + 1e-9) / (np.sqrt(np.mean(seg ** 2)) + 1e-9)
    x = min(T, int(SR * 0.006)); r = np.linspace(0, 1, x, dtype=np.float32)
    left, right = y[:m].copy(), y[m:].copy()
    seg[:x] = seg[:x] * r + left[-x:] * (1 - r); left = left[:-x]
    seg[-x:] = seg[-x:] * (1 - r) + right[:x] * r; right = right[x:]
    return np.concatenate([left, seg, right]).astype(np.float32)

def mp3hq(y):
    p = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-codec:a', 'libmp3lame',
                        '-b:a', '64k', '-ar', '22050', '-f', 'mp3', '-'], input=y.astype(np.float32).tobytes(), capture_output=True, check=True)
    return base64.b64encode(p.stdout).decode()

def target_of(key):
    return 0.45 if key in LETTER_KEYS else 0.30 if key in CLOSED else 0.42

def rime_take(key):
    cls = 'sac' if key in CLOSED or key in ('á', 'ớ') else 'ngang'
    best = None
    for w in SOURCES[key]:
        for sp in [0.76, 0.80, 0.72, 0.68]:
            for carrier in CARRIERS:
                r = extract(gen(carrier.format(w), sp), carrier, w)
                if r is None or not edges_quiet(r[0]): continue
                vow = strip_initial(r[0])
                if vow is None: continue
                y = tidy_smooth(lengthen(vow, target_of(key)), tail=0.12); bad, c = tone_bad(y, cls); ctx = r[1] == w
                score = bad + (0 if ctx else 0.5)
                if best is None or score < best[0]: best = (score, y, w, sp, c, ctx)
        if best and best[0] <= 0.8: break
    return best

if __name__ == '__main__':
    keys = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else list(SOURCES) + FINAL_NAMES
    V = json.load(open(os.path.join(ROOT, 'voice.json'), encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
    out = {}
    for i, key in enumerate(keys):
        if key not in V: continue
        if key in FINAL_NAMES:
            y = dec(V[key]); db, f = db_env(y); on = np.where(db > -48)[0]; y = y[on[0] * f:(on[-1] + 1) * f]
            y = tidy_smooth(lengthen(y, 0.42), tail=0.12)
            out[key] = [mp3hq(y), dict(rep.get(key, {}), v=14, core=round(core_dur(y), 2), dur=round(len(y) / SR, 2))]
            print(f'[{i + 1}/{len(keys)}] {key} kéo dài {out[key][1]["core"]}s', flush=True); continue
        b = rime_take(key)
        if b is None: print(f'[{i + 1}/{len(keys)}] {key}: không tách được, giữ cũ', flush=True); continue
        score, y, w, sp, c, ctx = b
        out[key] = [mp3hq(y), {'mode': 'short', 'ok': 'ctx' if ctx else 'gate', 'heard': f'(tách từ {w})', 'v': 14, 'src': w, 'f0': c,
                               'core': round(core_dur(y), 2), 'dur': round(len(y) / SR, 2)}]
        print(f'[{i + 1}/{len(keys)}] {key} ← {w} sp={sp} F0 {c} điểm={score:.1f} dài {out[key][1]["core"]}s', flush=True)
    if '--dry' in ARGS or '--part' in ARGS:
        json.dump(out, open(ARGS[ARGS.index('--part') + 1] if '--part' in ARGS else os.path.join(_D, 'v14_preview.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        sys.exit(0)
    for k, (b, info) in out.items(): V[k] = b; rep[k] = info
    json.dump(V, open(os.path.join(ROOT, 'voice.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    build()
