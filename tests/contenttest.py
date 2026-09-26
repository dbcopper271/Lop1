"""Render every task type in a round, answer each (correct choice), screenshot a few, check errors; export phrases."""
import json, sys
from playwright.sync_api import sync_playwright
import os
URL = os.environ.get('BVL1_URL', 'http://127.0.0.1:8686/index.html')
os.makedirs('tests/out', exist_ok=True)
errs, shots = [], []
TYPES = [
  ('findDigraph', '[]'), ('toneQuiz', '[window.__W1]'), ('vanQuiz', '[window.__W2]'), ('ruleQuiz', '[]'), ('readSentence', '[]'),
  ('compareSign', '[10]'), ('neighbor', '[10]'), ('bond', '[10]'), ('picEq', '[10]'), ('measure', '[]'), ('clock', '[]'), ('solid', '[]'),
  ('addsub', '[10, true]'), ('spell', '[4]'), ('spell', '[3]'), ('traceWord', '[]'), ('traceLetter', '[window.__DG]')]
VIEW = sys.argv[1] if len(sys.argv) > 1 else '390x844'
w, h = map(int, VIEW.split('x'))
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    pg = b.new_page(viewport={'width': w, 'height': h})
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_TUNNEL' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.goto(URL)
    pg.evaluate("""() => { const id='ptest'; localStorage.setItem('bvl1-profiles', JSON.stringify({list:[{id, name:'Bin', avatar:'🐯'}], current:id, pin:''}));
      localStorage.setItem('bvl1-state-'+id, JSON.stringify({intro:true, unlockAll:true, rec:false, sound:false})); }""")
    pg.reload(); pg.wait_for_timeout(500)
    pg.click('.pmain[data-id="ptest"]'); pg.wait_for_timeout(400)
    phr = pg.evaluate('window.__phrases()')
    json.dump(phr, open('tools/tts/phrases.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    for name, args in TYPES:
        pg.evaluate(f"""() => {{ const B = window.__bvl; window.__W1 = undefined; }}""")
        ok = pg.evaluate(f"""() => {{ try {{
            const B = window.__bvl;
            const pools = {{ W1: null }};
            window.__W1 = window.__W1 || null;
            const T = B.T; const mk = () => T['{name}'](...{args.replace('window.__W1', 'B.W1').replace('window.__W2', 'B.W2').replace('window.__DG', 'B.DG')});
            const t = mk(); window.__cur = t;
            B.runRound('Thử', 'thorns', [t], () => 300, () => {{ window.__fin = 1; }}, null);
            return t.kind; }} catch (e) {{ return 'ERR ' + e.message; }} }}""")
        if ok.startswith('ERR'): errs.append(f'{name}: {ok}'); continue
        pg.wait_for_timeout(500)
        shot = f'ct_{name}_{args.strip("[]").replace(", ", "_").replace("window.__", "")}_{VIEW}.png'
        pg.screenshot(path=shot); shots.append(shot)
        if ok == 'quiz':
            idx = pg.evaluate("() => window.__cur.choices.findIndex(c => c.correct)")
            n = pg.evaluate("() => window.__cur.choices.filter(c => c.correct).length")
            if n != 1: errs.append(f'{name}: {n} correct choices')
            pg.eval_on_selector(f'.choice[data-i="{idx}"]', 'e => e.click()'); pg.wait_for_timeout(700)
            if not pg.query_selector('.choice.ok'): errs.append(f'{name}: correct choice not accepted')
            pg.screenshot(path=shot.replace('.png', '_solved.png'))
        # overflow check
        ov = pg.evaluate("() => { const m = document.querySelector('main') || document.body; return [document.documentElement.scrollWidth, innerWidth]; }")
        if ov[0] > ov[1] + 1: errs.append(f'{name}: horizontal overflow {ov}')
        pg.evaluate("() => { document.querySelector('#back').click(); }"); pg.wait_for_timeout(250)
    missing = pg.evaluate('window.__missing || []')
    b.close()
print('phrases', len(phr)); print('\n'.join(errs) or 'no errors'); print('missing voice', len(set(missing)), list(set(missing))[:12])
