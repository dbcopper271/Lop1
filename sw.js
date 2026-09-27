// Service worker: lưu app vào máy để mở được cả khi mất mạng. Không đụng tới các yêu cầu gửi lên Supabase.
const VERSION = '63719f3de5';
const CACHE = 'bvl1-' + VERSION;
const CORE = ['./', './index.html', './voice.json', './config.js', './vendor/supabase.js', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png'];
const FONTS = /^https:\/\/fonts\.(googleapis|gstatic)\.com\//;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('bvl1-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (FONTS.test(req.url)) {            // phông chữ: dùng bản đã lưu, cập nhật ngầm
    e.respondWith(caches.open(CACHE).then(async c => {
      const hit = await c.match(req);
      const net = fetch(req).then(r => { if (r.ok || r.type === 'opaque') c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    }));
    return;
  }
  if (url.origin !== location.origin) return;          // Supabase và trang khác: để trình duyệt tự xử lý
  const fresh = req.mode === 'navigate' || /\/(index\.html|config\.js)?$/.test(url.pathname);
  if (fresh) {                          // trang chính, cấu hình: ưu tiên bản mới trên mạng
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); return r; })
      .catch(() => caches.match(req).then(r => r || caches.match('./index.html'))));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); }
    return r;
  })));
});
