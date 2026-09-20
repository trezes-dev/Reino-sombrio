const CACHE_NAME = 'reino-sombrio-v2';
self.addEventListener('install', (e) => {
    self.skipWaiting();
});
self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.map(k => caches.delete(k))
        )).then(() => self.clients.claim())
    );
});
self.addEventListener('fetch', (e) => {
    // Não cachear nada — sempre pega do servidor
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
