const CACHE = 'reino-sombrio-v3';

self.addEventListener('install', e => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // Para HTML, sempre busca da rede (sem cache)
  if (e.request.destination === 'document' || e.request.url.includes('/api/')) {
    e.respondWith(fetch(e.request));
    return;
  }
  // Para imagens/css/js, tenta rede primeiro, fallback no cache
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
