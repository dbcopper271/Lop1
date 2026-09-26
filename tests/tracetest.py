import os, json
from playwright.sync_api import sync_playwright
import os
URL = os.environ.get('BVL1_URL', 'http://127.0.0.1:8686/index.html')
os.makedirs('tests/out', exist_ok=True)
res = {}

def guide_pixels(pg):
    return pg.evaluate("""() => {
      const cv = document.querySelector('.twrap canvas'); const c = cv.getContext('2d');
      const d = c.getImageData(0, 0, cv.width, cv.height).data, dpr = cv.width / cv.clientWidth, pts = [];
      for (let y = 0; y < cv.height; y += 2) for (let x = 0; x < cv.width; x += 2) { const i = (y * cv.width + x) * 4;
        if (Math.abs(d[i] - 238) < 6 && Math.abs(d[i+1] - 233) < 6 && Math.abs(d[i+2] - 252) < 6) pts.push([x / dpr, y / dpr]); }
      return pts; }""")

def scan_strokes(pg, pts, keep):
    box = pg.query_selector('.twrap canvas').bounding_box()
    pts = [p for p in pts if keep(p)]
    rows = {}
    for x, y in pts: rows.setdefault(round(y / 7) * 7, []).append(x)
    n = 0
    for y, xs in sorted(rows.items()):
        xs.sort(); runs = []; s = xs[0]; prev = xs[0]
        for x in xs[1:]:
            if x - prev > 4: runs.append((s, prev)); s = x
            prev = x
        runs.append((s, prev))
        for a, b in runs:
            pg.mouse.move(box['x'] + a, box['y'] + y); pg.mouse.down(); pg.mouse.move(box['x'] + b, box['y'] + y, steps=4); pg.mouse.up(); n += 1
    return n

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 390, 'height': 844})
    pg.goto(URL)
    pg.evaluate("""() => { const id='ptest'; localStorage.setItem('bvl1-profiles', JSON.stringify({list:[{id, name:'Bin', avatar:'🐯'}], current:id, pin:''}));
      localStorage.setItem('bvl1-state-'+id, JSON.stringify({intro:true, unlockAll:true})); }""")
    pg.reload(); pg.wait_for_timeout(600)
    pg.click('.pmain[data-id="ptest"]'); pg.wait_for_timeout(500)
    pg.click('#mBook'); pg.wait_for_timeout(300); pg.click('[data-s="to"]'); pg.wait_for_timeout(700)
    for target, idx, name, partial in [('ơ', 18, 'o-horn', lambda bb: (lambda p: not (p[0] > bb[2] - 0.25 * (bb[2] - bb[0]) and p[1] < bb[1] + 0.5 * (bb[3] - bb[1])))),
                                         ('â', 2, 'a-hat', lambda bb: (lambda p: p[1] > bb[1] + 0.33 * (bb[3] - bb[1]))),
                                         ('đ', 6, 'd-bar', lambda bb: (lambda p: not (p[1] < bb[1] + 0.3 * (bb[3] - bb[1]) and p[0] > bb[0] + 0.55 * (bb[2] - bb[0]))))]:
        cur = pg.eval_on_selector('.tcur', 'e => e.textContent')
        while cur != target:
            pg.click('.tnext'); pg.wait_for_timeout(120); cur = pg.eval_on_selector('.tcur', 'e => e.textContent')
        pg.wait_for_timeout(600)
        pts = guide_pixels(pg)
        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]; bb = (min(xs), min(ys), max(xs), max(ys))
        scan_strokes(pg, pts, partial(bb)); pg.click('.tdone'); pg.wait_for_timeout(300)
        res[name + ' partial passed'] = bool(pg.query_selector('.twrap .stamp'))
        if name == 'o-horn': pg.screenshot(path='tests/out/' + 'trace_partial.png')
        pg.wait_for_timeout(1900)
        pg.click('.tclr'); pg.wait_for_timeout(200)
        scan_strokes(pg, pts, lambda q: True); pg.wait_for_timeout(300)
        res[name + ' full passed'] = bool(pg.query_selector('.twrap .stamp'))
        pg.wait_for_timeout(2500)
    b.close()
print(json.dumps(res, indent=1, ensure_ascii=False))
