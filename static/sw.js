// Service Worker for Commander Throne PWA
const CACHE_NAME = 'commander-throne-v1';
const urlsToCache = [
  '/throne',
  '/static/manifest.json',
  // Cache external CDN resources
  'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js',
  'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js'
];

// Install service worker and cache resources
self.addEventListener('install', function(event) {
  console.log('[SW] Install event');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('[SW] Opened cache');
        return cache.addAll(urlsToCache);
      })
      .catch(function(error) {
        console.log('[SW] Cache failed:', error);
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', function(event) {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip API calls for offline functionality
  if (event.request.url.includes('/throne/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Return cached version or fetch from network
        if (response) {
          console.log('[SW] Serving from cache:', event.request.url);
          return response;
        }

        return fetch(event.request).then(function(response) {
          // Don't cache if not successful
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          var responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(function(cache) {
              cache.put(event.request, responseToCache);
            });

          return response;
        });
      })
  );
});

// Activate service worker and clean up old caches
self.addEventListener('activate', function(event) {
  console.log('[SW] Activate event');
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline actions (if needed later)
self.addEventListener('sync', function(event) {
  console.log('[SW] Background sync:', event.tag);
});

// Push notifications (if needed later)
self.addEventListener('push', function(event) {
  console.log('[SW] Push received');
});