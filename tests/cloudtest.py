"""Two 'devices' sharing one mock Supabase: sign up, train, sync; new device signs in and continues; delete propagates."""
import json
from playwright.sync_api import sync_playwright
import os
URL = os.environ.get('BVL1_URL', 'http://127.0.0.1:8686/index.html')
os.makedirs('tests/out', exist_ok=True)
MOCK = open('tests/mock_supabase.js', encoding='utf-8').read()
notes, errs = [], []

def clickall(pg, rounds=12):
    for _ in range(rounds):
        if pg.query_selector('.ov:not([hidden])'): return True
        for bt in pg.query_selector_all('.choice:not(.tried):not(.ok)'):
            try:
                if pg.query_selector('.ov:not([hidden])'): return True
                bt.click(timeout=300); pg.wait_for_timeout(120)
            except Exception: pass
        pg.wait_for_timeout(1500)
    return bool(pg.query_selector('.ov:not([hidden])'))

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 390, 'height': 844})
    ctx.add_init_script(MOCK)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: errs.append('console: ' + m.text) if m.type in ('error', 'warning') and 'fonts.g' not in m.text and 'Failed to load' not in m.text else None)
    pg.goto(URL); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(600)
    notes.append('A cloud label: ' + pg.inner_text('#pCloud'))
    # Device A: create a child, sign up
    pg.click('#pAdd'); pg.wait_for_timeout(300); pg.fill('#fName', 'Bin'); pg.click('.av[data-a="🐼"]'); pg.click('#fOk'); pg.wait_for_timeout(600)
    pg.click('#sGo'); pg.wait_for_timeout(300)
    pg.click('#back') if pg.is_visible('#back') else None
    pg.evaluate("() => { document.querySelector('#title').click(); }"); pg.wait_for_timeout(500)   # về màn chọn bé
    pg.click('#pCloud'); pg.wait_for_timeout(300)
    pg.fill('#cMail', 'ba@example.com'); pg.fill('#cPass', 'matkhau1'); pg.click('#cUp'); pg.wait_for_timeout(1500)
    pg.screenshot(path='tests/out/' + 'cl_A_account.png')
    notes.append('A after signup: ' + (pg.inner_text('.ov-card') or '')[:120].replace('\n', ' | '))
    pg.click('#cNo'); pg.wait_for_timeout(300)
    # Train: chữ cái round (quiz only)
    pg.click('.pmain[data-id]'); pg.wait_for_timeout(500)
    pg.click('#mTrain'); pg.wait_for_timeout(300); pg.click('[data-k="chu"]'); pg.wait_for_timeout(800)
    notes.append('A training finished: ' + str(clickall(pg)))
    pg.wait_for_timeout(4000)   # sync debounce
    db = pg.evaluate("JSON.parse(localStorage.getItem('mockdb'))")
    power_A = pg.evaluate("JSON.parse(localStorage.getItem('bvl1-state-' + JSON.parse(localStorage.getItem('bvl1-profiles')).list[0].id)).power")
    notes.append(f"mockdb after A: children={len(db['children'])} progress={len(db['progress'])} power_remote={db['progress'][0]['state'].get('power') if db['progress'] else None} power_local={power_A} sessions={len(db['sessions'])} items={len(db['item_stats'])}")
    snapA = pg.evaluate("JSON.stringify(Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)])))")
    # Device B: fresh storage except the shared mock DB + users
    pg.evaluate("() => { const db = localStorage.getItem('mockdb'), u = localStorage.getItem('mock-users'); localStorage.clear(); localStorage.setItem('mockdb', db); localStorage.setItem('mock-users', u); }")
    pg.reload(); pg.wait_for_timeout(700)
    notes.append('B before login, profiles: ' + str(len(pg.query_selector_all('.pmain[data-id]'))))
    pg.click('#pCloud'); pg.wait_for_timeout(300)
    pg.fill('#cMail', 'ba@example.com'); pg.fill('#cPass', 'sai-mat-khau'); pg.click('#cIn'); pg.wait_for_timeout(600)
    notes.append('B wrong password msg: ' + pg.inner_text('#cMsg'))
    pg.fill('#cPass', 'matkhau1'); pg.click('#cIn'); pg.wait_for_timeout(2500)
    pg.click('#cNo'); pg.wait_for_timeout(800)
    notes.append('B after login, profiles: ' + str([e.inner_text().replace('\n', ' ') for e in pg.query_selector_all('.pmain[data-id]')]))
    pg.screenshot(path='tests/out/' + 'cl_B_who.png')
    if pg.query_selector('.pmain[data-id]'):
        pg.click('.pmain[data-id]'); pg.wait_for_timeout(500)
        notes.append('B power pill: ' + pg.inner_text('#powN') + f' (A had {power_A})')
        hist = pg.evaluate("() => { const id = JSON.parse(localStorage.getItem('bvl1-profiles')).current; return JSON.parse(localStorage.getItem('bvl1-hist-' + id) || '[]').map(e => e.title); }")
        notes.append('B history: ' + str(hist))
        # B also trains once -> sessions from 2 devices
        pg.click('#mTrain'); pg.wait_for_timeout(300); pg.click('[data-k="chu"]'); pg.wait_for_timeout(800); clickall(pg); pg.wait_for_timeout(4000)
        db = pg.evaluate("JSON.parse(localStorage.getItem('mockdb'))")
        notes.append(f"mockdb after B: sessions={len(db['sessions'])} item devices={sorted(set(r['device_id'] for r in db['item_stats']))} power_remote={db['progress'][0]['state'].get('power')}")
        # B deletes the child
        pg.click('#ovGo') if pg.is_visible('#ovGo') else None; pg.wait_for_timeout(300)
        pg.evaluate("() => { document.querySelector('#title').click(); }"); pg.wait_for_timeout(500)
        pg.click('#pManage'); pg.wait_for_timeout(400); pg.click('.p-del'); pg.wait_for_timeout(200); pg.click('.p-del'); pg.wait_for_timeout(4500)
        db = pg.evaluate("JSON.parse(localStorage.getItem('mockdb'))")
        notes.append(f"after B delete: children={[(c['name'], c['deleted']) for c in db['children']]} sessions={len(db['sessions'])} progress={len(db['progress'])} items={len(db['item_stats'])}")
    # Back to device A: its local copy should drop the deleted child after sync
    dbnow = pg.evaluate("localStorage.getItem('mockdb')")
    pg.evaluate("s => { const o = JSON.parse(s); localStorage.clear(); Object.entries(o).forEach(([k, v]) => localStorage.setItem(k, v)); }", snapA)
    pg.evaluate("s => localStorage.setItem('mockdb', s)", dbnow)
    pg.reload(); pg.wait_for_timeout(2500)
    notes.append('A after B deleted, profiles: ' + str(len(pg.query_selector_all('.pmain[data-id]'))) + ' · label: ' + pg.inner_text('#pCloud'))
    calls = pg.evaluate('window.__mockCalls')
    b.close()
print('\n'.join(notes)); print('\n'.join(errs) or 'no errors')
