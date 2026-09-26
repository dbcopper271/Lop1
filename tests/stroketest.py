import json
from playwright.sync_api import sync_playwright
exec(open('tests/tracetest.py', encoding='utf-8').read().split('with sync_playwright() as p:')[0])
res = {}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844})
    pg.goto(URL)
    pg.evaluate("""() => { const id='ptest'; localStorage.setItem('bvl1-profiles', JSON.stringify({list:[{id, name:'Bin', avatar:'🐯'}], current:id, pin:''})); localStorage.setItem('bvl1-state-'+id, JSON.stringify({intro:true, sound:false})); }""")
    pg.reload(); pg.wait_for_timeout(500); pg.click('.pmain[data-id="ptest"]'); pg.wait_for_timeout(300)
    pg.click('#mBook'); pg.wait_for_timeout(300); pg.click('[data-s="to"]'); pg.wait_for_timeout(500); pg.click('.tseg [data-k="net"]'); pg.wait_for_timeout(600)
    for want in ['móc ngược', 'khuyết ngược', 'cong kín']:
        while pg.eval_on_selector('.tcur', 'e => e.textContent') != want: pg.click('.tnext'); pg.wait_for_timeout(150)
        pg.wait_for_timeout(500); pts = guide_pixels(pg)
        ys = [q[1] for q in pts]; y0, y1 = min(ys), max(ys)
        scan_strokes(pg, pts, lambda q: q[1] < y0 + .5 * (y1 - y0)); pg.click('.tdone'); pg.wait_for_timeout(300)
        res[want + ' nửa trên → qua?'] = bool(pg.query_selector('.twrap .stamp'))
        pg.screenshot(path='tests/out/' + f'st_{want}.png'); pg.wait_for_timeout(1900); pg.click('.tclr'); pg.wait_for_timeout(200)
        scan_strokes(pg, pts, lambda q: True); pg.wait_for_timeout(300)
        res[want + ' tô đủ → qua?'] = bool(pg.query_selector('.twrap .stamp')); res[want + ' cao (px)'] = round(y1 - y0)
        pg.wait_for_timeout(2600)
    b.close()
print(json.dumps(res, ensure_ascii=False, indent=1))
