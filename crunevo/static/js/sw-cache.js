const STATIC_ASSETS = [
  '/',
  '/feed',
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
  event.respondWith(
    caches.match(req).then(res => res || fetch(req))
  );
});
