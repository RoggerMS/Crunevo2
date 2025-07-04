const STATIC_ASSETS = [
  '/',
  '/static/css/feed.css',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(version).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') {
    return;
  }
  event.respondWith(
    caches.match(req).then(cachedResponse => {
      return (
        cachedResponse ||
        fetch(req)
          .then(networkResponse => {
            if (req.url.includes('.js')) {
              return networkResponse;
            }
            return caches.open(version).then(cache => {
              cache.put(req, networkResponse.clone());
              return networkResponse;
            });
          })
      );
    })
  );
});
