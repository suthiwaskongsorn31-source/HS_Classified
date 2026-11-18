/* Service worker: lets the app open and search with no internet (offline mode).
   Bump VERSION whenever index.html or data/*.json change. */
const VERSION = 'v2026-11-18c';
const CORE = ['./', './index.html', './claude.html', './icons/claude-touch-icon.png', './manifest.webmanifest', './icons/apple-touch-icon.png', './icons/icon-192.png',
  './data/tariff.json', './data/rates.json', './data/hs_en.json', './data/permits.json', './data/dict.json'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION && k !== 'cdn').map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('message', e => { if (e.data === 'skip') self.skipWaiting(); });
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET') return;
  // never cache AI or GitHub API calls
  if (/api\.anthropic\.com|api\.github\.com/.test(url.host)) return;
  // team library: network first, fall back to cache
  if (url.pathname.endsWith('/data/library.json')) {
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(VERSION).then(x => x.put(req, c)); return r; }).catch(() => caches.match(req)));
    return;
  }
  // CDN libraries and fonts: cache after first use
  if (/cdnjs\.cloudflare\.com|fonts\.(googleapis|gstatic)\.com/.test(url.host)) {
    e.respondWith(caches.open('cdn').then(c => c.match(req).then(hit => hit || fetch(req).then(r => { if (r.ok || r.type === 'opaque') c.put(req, r.clone()); return r; }))));
    return;
  }
  if (url.origin !== location.origin) return;
  // app files: cache first (fast, offline), refresh in background
  e.respondWith(caches.match(req, {ignoreSearch: true}).then(hit => {
    const net = fetch(req).then(r => { if (r.ok) { const c = r.clone(); caches.open(VERSION).then(x => x.put(req, c)); } return r; });
    return hit || net.catch(() => caches.match('./index.html'));
  }));
});
