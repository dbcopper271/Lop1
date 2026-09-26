// Giả lập tối giản supabase-js v2 (chỉ dùng để kiểm thử tự động). Dữ liệu lưu ở localStorage 'mockdb'.
(function () {
  const PK = { children: ['user_id', 'id'], progress: ['user_id', 'child_id'], sessions: ['user_id', 'id'], item_stats: ['user_id', 'child_id', 'device_id', 'item_key'] };
  const db = () => JSON.parse(localStorage.getItem('mockdb') || '{"children":[],"progress":[],"sessions":[],"item_stats":[]}');
  const put = d => localStorage.setItem('mockdb', JSON.stringify(d));
  const users = () => JSON.parse(localStorage.getItem('mock-users') || '{}');
  window.__mockCalls = [];
  function client() {
    const listeners = [];
    const sess = () => JSON.parse(localStorage.getItem('bvl1-auth') || 'null');
    const emit = (ev, s) => listeners.forEach(cb => setTimeout(() => cb(ev, s), 0));
    const auth = {
      async getSession() { return { data: { session: sess() }, error: null }; },
      onAuthStateChange(cb) { listeners.push(cb); return { data: { subscription: { unsubscribe() {} } } }; },
      async signUp({ email, password }) { const u = users(); if (u[email]) return { data: null, error: { message: 'User already registered' } }; u[email] = { id: 'u-' + Math.random().toString(36).slice(2), password }; localStorage.setItem('mock-users', JSON.stringify(u)); const s = { user: { id: u[email].id, email } }; localStorage.setItem('bvl1-auth', JSON.stringify(s)); emit('SIGNED_IN', s); return { data: { session: s, user: s.user }, error: null }; },
      async signInWithPassword({ email, password }) { const u = users()[email]; if (!u || u.password !== password) return { data: null, error: { message: 'Invalid login credentials' } }; const s = { user: { id: u.id, email } }; localStorage.setItem('bvl1-auth', JSON.stringify(s)); emit('SIGNED_IN', s); return { data: { session: s }, error: null }; },
      async signOut() { localStorage.removeItem('bvl1-auth'); emit('SIGNED_OUT', null); return { error: null }; }
    };
    function from(table) {
      const st = { op: 'select', filters: [], order: null, range: null, rows: null, opts: {} };
      const uid = () => (sess() || {}).user?.id;
      const b = {
        select() { if (st.op !== 'delete') st.op = 'select'; return b; },
        eq(c, v) { st.filters.push(r => r[c] === v); return b; }, neq(c, v) { st.filters.push(r => r[c] !== v); return b; },
        gt(c, v) { st.filters.push(r => r[c] > v); return b; },
        order(c, o) { st.order = [c, !o || o.ascending !== false]; return b; }, range(a, z) { st.range = [a, z]; return b; },
        upsert(rows, opts) { st.op = 'upsert'; st.rows = rows; st.opts = opts || {}; return b; },
        delete() { st.op = 'delete'; return b; },
        then(res, rej) { return Promise.resolve().then(run).then(res, rej); }
      };
      function run() {
        window.__mockCalls.push(table + ':' + st.op);
        const u = uid(); if (!u) return { data: null, error: { message: 'not authenticated' } };
        const d = db(); let T = d[table];
        if (st.op === 'upsert') {
          const keys = new Set(st.rows.flatMap(r => Object.keys(r)));
          if (st.rows.some(r => Object.keys(r).length !== keys.size)) return { data: null, error: { message: 'All object keys must match' } };
          for (const r0 of st.rows) {
            const r = Object.assign({ user_id: u }, r0); if (r.user_id !== u) return { data: null, error: { message: 'new row violates row-level security policy' } };
            if (table !== 'children' && !d.children.some(c => c.user_id === u && c.id === r.child_id)) return { data: null, error: { message: 'violates foreign key constraint' } };
            const i = T.findIndex(x => PK[table].every(k => x[k] === r[k]));
            if (i >= 0) { if (!st.opts.ignoreDuplicates) T[i] = Object.assign(T[i], r); } else T.push(r);
          }
          put(d); return { data: null, error: null };
        }
        let rows = T.filter(r => r.user_id === u && st.filters.every(f => f(r)));
        if (st.op === 'delete') { d[table] = T.filter(r => !rows.includes(r)); put(d); return { data: null, error: null }; }
        if (st.order) { const [c, asc] = st.order; rows.sort((a, z) => (a[c] > z[c] ? 1 : a[c] < z[c] ? -1 : 0) * (asc ? 1 : -1)); }
        if (st.range) rows = rows.slice(st.range[0], st.range[1] + 1);
        return { data: JSON.parse(JSON.stringify(rows)), error: null };
      }
      return b;
    }
    return { auth, from };
  }
  window.supabase = { createClient: () => client() };
  // Cấu hình giả như khi cha mẹ tự nhập trong app (config.js để trống)
  if (!localStorage.getItem('bvl1-cloud-cfg')) localStorage.setItem('bvl1-cloud-cfg', JSON.stringify({ url: 'https://mock.supabase.co', key: 'mock-anon-key-000000000000' }));
})();
