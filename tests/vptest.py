"""Screenshot main screens across device sizes; report horizontal overflow and clipped content."""
import sys
from playwright.sync_api import sync_playwright
import os
URL = os.environ.get('BVL1_URL', 'http://127.0.0.1:8686/index.html')
os.makedirs('tests/out', exist_ok=True)
VPS = [(390, 844, 'phone'), (844, 390, 'phoneL'), (820, 1180, 'ipad'), (1180, 820, 'ipadL'), (1366, 768, 'laptop'), (1920, 1080, 'desktop')]
if len(sys.argv) > 1: VPS = [v for v in VPS if v[2] in sys.argv[1].split(',')]
SCREENS = sys.argv[2].split(',') if len(sys.argv) > 2 else ['who', 'map', 'level', 'train', 'book', 'bookspell', 'history']
issues = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for w, h, nm in VPS:
        pg = b.new_page(viewport={'width': w, 'height': h}, has_touch=nm.startswith(('phone', 'ipad')), is_mobile=nm.startswith('phone'))
        pg.on('pageerror', lambda e: issues.append('pageerror: ' + str(e)))
        pg.goto(URL)
        pg.evaluate("""() => { const id='ptest'; localStorage.setItem('bvl1-profiles', JSON.stringify({list:[{id, name:'Bin', avatar:'🐯'},{id:'p2', name:'Na', avatar:'🐰'}], current:id, pin:''}));
          localStorage.setItem('bvl1-state-'+id, JSON.stringify({intro:true, unlockAll:false, rec:false, sound:false, power:40, stars:23, levels:{1:3,2:2,3:3,4:1,5:3,6:2,7:3,8:3,9:2}})); }""")
        pg.reload(); pg.wait_for_timeout(500)
        def shot(n):
            pg.wait_for_timeout(450)
            sw = pg.evaluate('[document.documentElement.scrollWidth, innerWidth, document.querySelector("main") ? document.querySelector("main").scrollWidth - document.querySelector("main").clientWidth : 0]')
            if sw[0] > sw[1] + 1 or sw[2] > 1: issues.append(f'{nm} {n}: horizontal overflow {sw}')
            pg.screenshot(path='tests/out/' + f'vp_{nm}_{n}.png')
        for s in SCREENS:
            if s == 'who': shot('who'); pg.click('.pmain[data-id="ptest"]'); pg.wait_for_timeout(400)
            elif s == 'map': pg.evaluate("() => document.querySelector('.welcome')?.remove()"); shot('map')
            elif s == 'level':
                pg.evaluate("() => { const B = window.__bvl; B.runRound('Màn 2', 'river', [B.T.findLetter(B.L), B.T.count(8)], () => 300, () => {}, null); }")
                shot('level')
                pg.evaluate("() => { const B = window.__bvl; B.runRound('Màn 3', 'gate', [B.T.spell(2)], () => 300, () => {}, null); }"); shot('spell')
                pg.evaluate("() => { const B = window.__bvl; B.runRound('Màn 4', 'bridge', [B.T.addsub(10)], () => 300, () => {}, null); }"); shot('math')
                pg.evaluate("() => { const B = window.__bvl; B.runRound('Màn 5', 'door', [B.T.traceLetter(B.DG)], () => 300, () => {}, null); }"); shot('trace')
                pg.click('#back'); pg.wait_for_timeout(300)
            elif s == 'train': pg.click('#mTrain'); shot('train'); pg.click('#back'); pg.wait_for_timeout(300)
            elif s == 'book': pg.click('#mBook'); shot('book')
            elif s == 'bookspell':
                if pg.query_selector('#btabs [data-t="spell"]'): pg.click('#btabs [data-t="spell"]')
                shot('bookspell'); pg.click('#back'); pg.wait_for_timeout(300)
            elif s == 'history': pg.evaluate("() => { location.hash=''; }"); pg.goto(URL); pg.wait_for_timeout(400); pg.click('.pmain[data-id="ptest"]'); pg.wait_for_timeout(300)
        pg.close()
    b.close()
print('\n'.join(issues) or 'no issues')
