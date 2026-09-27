"""Làm giọng dễ nghe hơn cho mọi clip trong voice.json, không đổi cách đọc.
- Bớt chói: lọc bỏ tiếng ù dưới 70Hz, thêm ấm quanh 250Hz, giảm vùng gắt 3-4kHz và vùng xì trên 6kHz, giảm tiếng "s", "x".
- Độ to đều: chuẩn hóa theo năng lượng phần có tiếng về -20dBFS, đỉnh không quá -3dB (trước đây chuẩn theo đỉnh 0,93 nên clip to nhỏ không đều, dễ chói).
- Cảm xúc (--expressive): với câu dài và cụm từ, dùng bộ phân tích-tổng hợp WORLD nới biên độ ngữ điệu (mặc định 1,2 lần quanh cao độ trung vị,
  giữ hướng lên xuống của từng dấu thanh) và nâng cao độ chung 0,5 nửa cung cho giọng tươi hơn. Âm, tiếng đứng riêng giữ nguyên ngữ điệu.
  --guard: câu nào nới ngữ điệu xong máy nhận dạng nghe kém đi thì giữ ngữ điệu gốc (cần mô hình sherpa-onnx-zipformer-vi-int8-2025-04-20).
Chạy từ thư mục gốc: python3 tools/tts/polish.py [--expressive [--guard]] [--keys k.json --part out.json] [--merge a.json ...]"""
import base64, json, os, subprocess, sys
import numpy as np

D = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(D, '..', '..')
VOICE, REP = os.path.join(ROOT, 'voice.json'), os.path.join(D, 'voice_report.json')
SR = 22050
EQ = 'highpass=f=70,equalizer=f=250:t=q:w=1.0:g=2,equalizer=f=3500:t=q:w=1.2:g=-3.5,treble=g=-4:f=6500,deesser=i=0.4'

def dec(b):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', '-', '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], input=base64.b64decode(b), capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def ff(y, filt):
    z = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-af', filt, '-f', 'f32le', '-'],
                       input=y.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(z, dtype=np.float32).copy()

def mp3(y, kbps=48):
    p = subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-codec:a', 'libmp3lame',
                        '-b:a', f'{kbps}k', '-f', 'mp3', '-'], input=y.astype(np.float32).tobytes(), capture_output=True, check=True)
    return base64.b64encode(p.stdout).decode()

def loudness(y, target_db=-20.0, peak_db=-3.0):
    f = int(SR * 0.02); fr = [y[i:i + f] for i in range(0, len(y) - f, f)]
    e = np.array([np.sqrt(np.mean(x ** 2)) for x in fr]) if fr else np.array([np.sqrt(np.mean(y ** 2))])
    act = e[e > e.max() * 0.1] if e.max() > 0 else e
    rms = np.sqrt(np.mean(act ** 2)) + 1e-9
    g = 10 ** (target_db / 20) / rms
    pk = np.abs(y).max() * g; lim = 10 ** (peak_db / 20)
    if pk > lim: g *= lim / pk
    return (y * g).astype(np.float32)

def expressive(y, stretch=1.2, lift=0.5):
    import pyworld as pw
    x = y.astype(np.float64)
    f0, t = pw.dio(x, SR, f0_floor=100, f0_ceil=500, frame_period=5.0); f0 = pw.stonemask(x, f0, t, SR)
    v = f0 > 0
    if v.sum() < 10: return y
    sp = pw.cheaptrick(x, f0, t, SR); ap = pw.d4c(x, f0, t, SR)
    lf = np.log2(f0[v]); med = np.median(lf)
    f1 = f0.copy(); f1[v] = 2 ** (med + (lf - med) * stretch + lift / 12)
    z = pw.synthesize(f1, sp, ap, SR, frame_period=5.0).astype(np.float32)
    return z[:len(y)] if len(z) >= len(y) else np.concatenate([z, np.zeros(len(y) - len(z), np.float32)])

ASR = None
def hear(y):
    global ASR
    import re, unicodedata, sherpa_onnx
    if ASR is None:
        a = os.path.join(D, 'sherpa-onnx-zipformer-vi-int8-2025-04-20')
        ASR = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=os.path.join(a, 'encoder-epoch-12-avg-8.int8.onnx'), decoder=os.path.join(a, 'decoder-epoch-12-avg-8.onnx'),
            joiner=os.path.join(a, 'joiner-epoch-12-avg-8.int8.onnx'), tokens=os.path.join(a, 'tokens.txt'), num_threads=1, decoding_method='greedy_search')
    x = np.concatenate([np.zeros(int(SR * 0.2), np.float32), y, np.zeros(int(SR * 0.3), np.float32)])
    x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * 16000 / SR)), np.arange(len(x)), x).astype(np.float32)
    st = ASR.create_stream(); st.accept_waveform(16000, x); ASR.decode_stream(st)
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFC', st.result.text).lower())).strip()

def match(text, y):
    import difflib, re, unicodedata
    t = re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFC', text).lower())).strip()
    return difflib.SequenceMatcher(None, t, hear(y)).ratio()

def polish(b, long, expr, text=None):
    """text (chốt an toàn): nới ngữ điệu làm máy nghe kém đi quá 0,05 thì bỏ bước nới ngữ điệu cho câu này."""
    y = dec(b)
    if expr and long:
        z = expressive(y)
        if text is None or match(text, z) >= match(text, y) - 0.05: y = z
    y = ff(y, EQ)
    y = loudness(y)
    fi = min(len(y), int(SR * 0.004)); y[:fi] *= np.linspace(0, 1, fi)
    fo = min(len(y), int(SR * 0.012)); y[-fo:] *= np.linspace(1, 0, fo)
    return mp3(y)

if __name__ == '__main__':
    A = sys.argv[1:]
    V = json.load(open(VOICE, encoding='utf-8')); rep = json.load(open(REP, encoding='utf-8'))
    if '--merge' in A:
        for pth in A[A.index('--merge') + 1:]:
            for k, b in json.load(open(pth, encoding='utf-8')).items(): V[k] = b; rep.setdefault(k, {})['polish'] = 2
        json.dump(V, open(VOICE, 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        subprocess.run(['python3', os.path.join(ROOT, 'tools', 'build.py')], check=True); sys.exit(0)
    keys = json.load(open(A[A.index('--keys') + 1], encoding='utf-8')) if '--keys' in A else [k for k in V if not k.startswith('__')]
    expr = '--expressive' in A; out = {}
    for i, k in enumerate(keys):
        if rep.get(k, {}).get('polish'): continue
        long = rep.get(k, {}).get('mode') == 'long' or len(k.split()) > 1
        out[k] = polish(V[k], long, expr, k if '--guard' in A else None)
        if i % 50 == 0: print(f'{i}/{len(keys)}', flush=True)
    if '--part' in A:
        json.dump(out, open(A[A.index('--part') + 1], 'w', encoding='utf-8'), ensure_ascii=False); sys.exit(0)
    for k, b in out.items(): V[k] = b; rep.setdefault(k, {})['polish'] = 2
    json.dump(V, open(VOICE, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(rep, open(REP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    subprocess.run(['python3', os.path.join(ROOT, 'tools', 'build.py')], check=True)
