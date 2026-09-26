import json, re, unicodedata
PAT = [r'^Tiếng (.+) có dấu gì\?$', r'^Tiếng (.+) có vần gì\?$', r'^Bé hãy chọn tiếng (.+) nhé\.$', r'^Bé hãy ghép tiếng (.+) nhé\.$',
       r'^Tiếng (.+) bắt đầu bằng chữ nào\?$', r'^Bé hãy tìm chữ ghi âm (.+) nhé\.$', r'^Bé hãy tìm chữ (.+) nhé\.$', r'^(.+) gồm (.+) và mấy\?$',
       r'^Số liền (?:sau|trước) của (.+) là số nào\?$', r'^(.+) (?:cộng|trừ) (.+) bằng (.+)\.$', r'^(.+) (?:cộng|trừ) (.+) bằng mấy\?$']
nfc = lambda t: unicodedata.normalize('NFC', t)
clean = lambda t: re.sub(r'[^\w\s]', ' ', nfc(t).lower()).split()
def target_ok(p, heard):
    for pat in PAT:
        m = re.match(pat, p)
        if m:
            tw = clean(p); hw = clean(heard)
            if len(hw) != len(tw): return False, m
            idx = [i for i, w in enumerate(tw) if any(w in clean(g) for g in m.groups())]
            return all(tw[i] == hw[i] for i in idx), m
    return None, None
if __name__ == '__main__':
    r = json.load(open('voice_report.json')); ph = json.load(open('phrases.json'))
    bad = []
    for p in ph:
        e = r.get(p, {})
        if e.get('mode') != 'long': continue
        ok, m = target_ok(p, e.get('heard', ''))
        if ok is False: bad.append((p, e.get('heard')))
    print(len(bad)); [print(b) for b in bad[:200]]
