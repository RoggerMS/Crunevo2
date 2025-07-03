importScripts('/static/js/sw-utils.js');
importScripts('/static/js/sw-cache.js');
importScripts('/static/js/sw-feed.js');
importScripts('/static/js/sw-store.js');

self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  self.clients.claim();
});
