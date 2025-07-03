self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/store')) {
    event.respondWith(
      fetch(event.request).catch(() => new Response(JSON.stringify({ error: "offline" })))
    );
  }
});
