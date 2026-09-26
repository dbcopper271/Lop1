#!/usr/bin/env python3
"""Dựng bản chạy từ mã nguồn.

  src/app.html      → index.html  (trang đầy đủ: PWA, cấu hình Supabase, service worker)
  voice.json        → voice.js    (giọng cô giáo cho trường hợp mở trực tiếp file index.html)
  sw.js             ← đóng dấu phiên bản để máy người dùng tự cập nhật bản mới

Cách dùng:  python3 tools/build.py
"""
import hashlib, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = lambda *a: os.path.join(ROOT, *a)

src = open(p('src', 'app.html'), encoding='utf-8').read()
i = src.index('<style>')
j = src.index('</style>') + len('</style>')
head_extra, style, body = src[:i].strip(), src[i:j], src[j:].strip()

HEAD = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Bé Vào Lớp 1: học chữ cái, đánh vần, làm toán và tập tô qua trò chơi giải cứu công chúa.">
<meta name="theme-color" content="#6B4FD8">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Bé Vào Lớp 1">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/icon-192.png">
{head_extra}
<style>:root{{color-scheme:light}}body{{margin:0}}[hidden]{{display:none!important}}</style>
{style}
<script src="config.js"></script>
<script>
// Mở trực tiếp file index.html (file://) thì trình duyệt không cho tải voice.json, nên nạp voice.js thay thế
if (location.protocol === 'file:') document.write('<script src="voice.js"><\\/script>');
</script>
</head>
<body>
"""
TAIL = """
<script>
if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) navigator.serviceWorker.register('sw.js').catch(() => {});
</script>
</body>
</html>
"""
html = HEAD + body + TAIL
open(p('index.html'), 'w', encoding='utf-8').write(html)

voice = json.load(open(p('voice.json'), encoding='utf-8'))
open(p('voice.js'), 'w', encoding='utf-8').write('window.VOICE_DATA=' + json.dumps(voice, ensure_ascii=False, separators=(',', ':')) + ';\n')

ver = hashlib.sha1((html + json.dumps(voice, sort_keys=True)).encode('utf-8')).hexdigest()[:10]
sw = open(p('sw.js'), encoding='utf-8').read()
sw = re.sub(r"const VERSION = '[^']*';", f"const VERSION = '{ver}';", sw)
open(p('sw.js'), 'w', encoding='utf-8').write(sw)
print(f'index.html {len(html) // 1024} KB · voice.js {len(voice)} câu · sw {ver}')
