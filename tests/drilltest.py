"""Bảng cộng/trừ/tách số/cộng trừ 100: đáp án không hiện sẵn; bé nhập sai bị báo, nhập đúng thì hiện kết quả."""
import re
from playwright.sync_api import sync_playwright
import os
URL = os.environ.get('BVL1_URL', 'http://127.0.0.1:8686/index.html')
os.makedirs('tests/out', exist_ok=True); res = []; errs = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for w, h, nm in [(390, 844, 'phone'), (1366, 768, 'laptop')]:
        pg = b.new_page(viewport={'width': w, 'height': h}); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL); pg.evaluate("""() => { const id='ptest'; localStorage.setItem('bvl1-profiles', JSON.stringify({list:[{id, name:'Bin', avatar:'🐯'}], current:id, pin:''})); localStorage.setItem('bvl1-state-'+id, JSON.stringify({intro:true, sound:false})); }""")
        pg.reload(); pg.wait_for_timeout(500); pg.click('.pmain[data-id="ptest"]'); pg.wait_for_timeout(300)
        for sec in ['cong', 'tru', 'tachso', 'tinh100']:
            pg.click('#mBook') if pg.query_selector('#mBook') else None; pg.wait_for_timeout(300); pg.click(f'[data-s="{sec}"]'); pg.wait_for_timeout(500)
            chips = [c.inner_text() for c in pg.query_selector_all('.cchip')]
            hidden = all(c.strip().endswith('?') for c in chips)
            # đáp án của câu đang chọn
            on = pg.inner_text('.cchip.on')
            m = re.match(r'(\d+) ([+−]) (\d+)', on) or re.match(r'(\d+) gồm (\d+)', on)
            if 'gồm' in on: ans = int(m.group(1)) - int(m.group(2))
            else: a, op, bb = int(m.group(1)), m.group(2), int(m.group(3)); ans = a + bb if op == '+' else a - bb
            wrong = (ans + 1) if ans < 10 else ans - 1
            def enter(v):
                if sec == 'tinh100':
                    for d in str(v): pg.click(f'.npad .nk[data-k="{d}"]'); pg.wait_for_timeout(60)
                    pg.click('.npad .nk[data-k="✓"]')
                else: pg.click(f'.npad .nk[data-k="{v}"]')
                pg.wait_for_timeout(500)
            enter(wrong); after_wrong = pg.inner_text('.dq .ans')
            enter(ans); after_right = pg.inner_text('.dq .ans'); chip = pg.inner_text(f'.cchip.did') if pg.query_selector('.cchip.did') else ''
            sw = pg.evaluate('[document.documentElement.scrollWidth, innerWidth, document.querySelector("main").scrollWidth - document.querySelector("main").clientWidth]')
            res.append(f'{nm} {sec}: {len(chips)} câu, ẩn đáp án={hidden}, câu "{on}" nhập sai → "{after_wrong}", nhập đúng {ans} → "{after_right}", ô đã làm: "{chip}", tràn={sw[0] > sw[1] + 1 or sw[2] > 1}')
            pg.screenshot(path='tests/out/' + f'dr_{nm}_{sec}.png'); pg.wait_for_timeout(1500)
            pg.click('#back'); pg.wait_for_timeout(300)
        pg.click('[data-s="sosanh"]'); pg.wait_for_timeout(500)
        res.append(f'{nm} sosanh: có phần luyện={bool(pg.query_selector(".cmpprac .choice"))}, dấu đang ẩn={pg.inner_text(".cmpprac .ans")}')
        pg.screenshot(path='tests/out/' + f'dr_{nm}_sosanh.png'); pg.close()
    b.close()
print('\n'.join(res)); print(errs or 'no errors')
