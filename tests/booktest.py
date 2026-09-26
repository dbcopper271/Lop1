"""Open every handbook page on several screen sizes, tap a few things, check errors/overflow, export phrases."""
import json, sys
from playwright.sync_api import sync_playwright
import os
URL = os.environ.get('BVL1_URL', 'http://127.0.0.1:8686/index.html')
os.makedirs('tests/out', exist_ok=True)
VPS = [(390, 844, 'phone'), (820, 1180, 'ipad'), (1366, 768, 'laptop')]
if len(sys.argv) > 1: VPS = [v for v in VPS if v[2] in sys.argv[1].split(',')]
SECS = ['chu', 'ghep', 'thanh', 'van', 'danhvan', 'cau', 'so', 'cong', 'tru', 'sosanh', 'hinh', 'gio', 'to']
TAP = {'chu': '.lk[data-k="12"]', 'ghep': '.lk[data-k="5"]', 'thanh': '.tex[data-k="3"]', 'van': '.vchip[data-v="ông"]', 'danhvan': '.lvseg [data-v="4"]',
       'cau': '.scard[data-k="2"]', 'so': '.lk[data-k="6"]', 'cong': '.cchip[data-a="4"][data-b="3"]', 'tru': '.cchip[data-a="9"][data-b="4"]',
       'sosanh': '.cmprow[data-k="1"]', 'hinh': '.shcard[data-k="4"]', 'gio': '.cnext', 'to': '.tseg [data-k="ghep"]'}
issues = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for w, h, nm in VPS:
        pg = b.new_page(viewport={'width': w, 'height': h})
        pg.on('pageerror', lambda e: issues.append('pageerror: ' + str(e)))
        pg.goto(URL)
        pg.evaluate("""() => { const id='ptest'; localStorage.setItem('bvl1-profiles', JSON.stringify({list:[{id, name:'Bin', avatar:'🐯'}], current:id, pin:''}));
          localStorage.setItem('bvl1-state-'+id, JSON.stringify({intro:true, rec:false, sound:false})); }""")
        pg.reload(); pg.wait_for_timeout(500); pg.click('.pmain[data-id="ptest"]'); pg.wait_for_timeout(400)
        pg.click('#mBook'); pg.wait_for_timeout(400); pg.screenshot(path='tests/out/' + f'bk_{nm}_home.png')
        for sec in SECS:
            pg.click(f'[data-s="{sec}"]'); pg.wait_for_timeout(450)
            try: pg.eval_on_selector(TAP[sec], 'e => e.click()'); pg.wait_for_timeout(700)
            except Exception as e: issues.append(f'{nm} {sec}: tap failed {e}')
            if sec == 'van': pg.click('.vword'); pg.wait_for_timeout(300)
            if sec == 'danhvan': pg.eval_on_selector('.wcard[data-w="chanh"]', 'e => e.click()'); pg.wait_for_timeout(300)
            sw = pg.evaluate('[document.documentElement.scrollWidth, innerWidth, document.querySelector("main").scrollWidth - document.querySelector("main").clientWidth]')
            if sw[0] > sw[1] + 1 or sw[2] > 1: issues.append(f'{nm} {sec}: horizontal overflow {sw}')
            pg.screenshot(path='tests/out/' + f'bk_{nm}_{sec}.png')
            pg.click('#back'); pg.wait_for_timeout(300)
        if nm == 'phone':
            phr = pg.evaluate('window.__phrases()'); json.dump(phr, open('tools/tts/phrases.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
            print('phrases', len(phr))
        # map screen too
        pg.click('#back'); pg.wait_for_timeout(400); pg.screenshot(path='tests/out/' + f'bk_{nm}_map.png')
        pg.close()
    b.close()
print('\n'.join(issues) or 'no issues')
