"""Quét toàn bộ voice.json, gắn cờ clip lỗi. Chạy từ thư mục gốc:
  python3 tools/tts/scan_voice.py [--keys k.json] [--out scan.json]
Kiểm tra: hỏng (câm, quá ngắn, vượt đỉnh); cụt đầu/cuối (âm chưa tắt đã bị cắt); dính tiếng của câu mang (cô, cho, đọc, rồi, nhé);
máy nhận dạng nghe lại lệch chữ, thiếu/thừa chữ (bỏ qua các cặp máy vốn hay nhầm: s/x, tr/ch, d/gi/r, v/ph, g/k, l/n, dấu hỏi/ngã);
vần đôi có đúng hướng lướt; độ to."""
import os, sys, json, re, difflib, unicodedata
_ARGS = sys.argv[1:]
_D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(_D, 'fix_v15.py'), encoding='utf-8').read().rsplit("if __name__ == '__main__':", 1)[0]
     .replace('_ARGS = sys.argv[1:]', ''))
ARGS = _ARGS

CARRIER_W = {'cô', 'cho', 'đọc', 'rồi', 'nhé', 'em', 'nghe', 'bây', 'giờ', 'nào', 'sẽ'}
PHONICS = set(GLIDE) | set(NUC) | {'bờ', 'cờ', 'dờ', 'đờ', 'gờ', 'hờ', 'ca', 'lờ', 'mờ', 'nờ', 'pờ', 'quờ', 'rờ', 'sờ', 'tờ', 'vờ', 'xờ',
                                   'i ngắn', 'i dài', 'chờ', 'gờ kép', 'di', 'khờ', 'ngờ', 'ngờ kép', 'nhờ', 'phờ', 'thờ', 'trờ'}

def fold(t):
    """Gộp các cặp máy nhận dạng hay nhầm để không báo lỗi nhầm."""
    t = clean(t)
    t = unicodedata.normalize('NFD', t).replace('̃', '̉')        # ngã ≈ hỏi
    t = unicodedata.normalize('NFC', t)
    for a, b in (('gi', 'd'), ('tr', 'ch'), ('ph', 'v'), ('ngh', 'ng'), ('gh', 'g'), ('x', 's'), ('r', 'd'), ('k', 'c'), ('q', 'c'), ('l', 'n')):
        t = re.sub(r'\b' + a, b, t)
    return t

def edge_db(y):
    """Mức năng lượng (dB so với đỉnh) ở 15ms đầu và 15ms cuối phần không lặng (bỏ khoảng đệm): cao nghĩa là bị cắt ngang."""
    db, f = db_env(y); on = np.where(db > -50)[0]
    if not len(on): return 0, 0
    k = 3
    return float(db[on[0]:on[0] + k].max()), float(db[on[-1] - k + 1:on[-1] + 1].max())

def rms_db(y):
    f = int(SR * 0.02); e = np.array([np.sqrt(np.mean(y[i:i + f] ** 2)) for i in range(0, len(y) - f, f)])
    act = e[e > e.max() * 0.1]; return float(20 * np.log10(np.sqrt(np.mean(act ** 2)) + 1e-9))

def scan_one(k, b, mode):
    y = dec(b); r = {'k': k, 'flags': []}
    dur = len(y) / SR; r['dur'] = round(dur, 2)
    if dur < 0.15 or np.abs(y).max() < 0.05: r['flags'].append('hỏng'); return r
    if np.abs(y).max() > 0.999: r['flags'].append('vượt đỉnh')
    s, e = edge_db(y); r['edge'] = [round(s, 1), round(e, 1)]
    if e > -18: r['flags'].append('cụt cuối')
    if s > -12: r['flags'].append('cụt đầu')
    r['rms'] = round(rms_db(y), 1)
    if k in PHONICS:
        if k in MOVE:
            ok, _, desc = check(k, y); r['lướt'] = desc
            if not ok: r['flags'].append('vần đôi không lướt đúng')
        return r
    h = hear_alone(y); r['nghe'] = h
    tw, hw = clean(k).split(), h.split()
    if hw and hw[0] in CARRIER_W and (not tw or hw[0] != tw[0]) and len(hw) > len(tw): r['flags'].append('dính tiếng đầu: ' + hw[0])
    if hw and hw[-1] in CARRIER_W and (not tw or hw[-1] != tw[-1]) and len(hw) > len(tw): r['flags'].append('dính tiếng cuối: ' + hw[-1])
    sc = difflib.SequenceMatcher(None, fold(k), fold(h)).ratio(); r['khớp'] = round(sc, 3)
    n = len(tw)
    if n >= 2 and len(hw) < n - max(1, n // 5): r['flags'].append(f'thiếu chữ ({len(hw)}/{n})')
    if n >= 1 and len(hw) > n + max(1, n // 5): r['flags'].append(f'thừa chữ ({len(hw)}/{n})')
    if n >= 3 and sc < 0.8: r['flags'].append(f'lệch chữ ({sc:.2f})')
    return r

if __name__ == '__main__':
    V = json.load(open(os.path.join(ROOT, 'voice.json'), encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
    keys = json.load(open(ARGS[ARGS.index('--keys') + 1], encoding='utf-8')) if '--keys' in ARGS else [k for k in V if not k.startswith('__')]
    build_ref()
    out = []
    for i, k in enumerate(keys):
        out.append(scan_one(k, V[k], rep.get(k, {}).get('mode')))
        if i % 100 == 0: print(i, len(keys), flush=True)
    pth = ARGS[ARGS.index('--out') + 1] if '--out' in ARGS else os.path.join(_D, 'scan.json')
    json.dump(out, open(pth, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
