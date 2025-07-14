/**
 * HydraX Mobile Navigation Service Worker
 * Provides offline functionality, caching, and performance optimization
 */

const CACHE_NAME = 'hydrax-mobile-v1.0.0';
const STATIC_CACHE_NAME = 'hydrax-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'hydrax-dynamic-v1.0.0';

// Files to cache for offline functionality
const STATIC_FILES = [
  '/templates/mobile_navigation.html',
  '/src/ui/mobile/navigation.js',
  '/src/ui/mobile/mobile_optimized.css',
  '/webapp/static/manifest.json',
  '/assets/icons/favicon.svg',
  '/assets/icons/apple-touch-icon.png',
  // Core fonts and libraries
  'https://telegram.org/js/telegram-web-app.js'
];

// API endpoints to cache with network-first strategy
const API_ENDPOINTS = [
  '/api/signals',
  '/api/portfolio',
  '/api/positions',
  '/api/education'
];

// Files that should always be fetched from network
const NETWORK_ONLY = [
  '/api/live-data',
  '/api/real-time',
  '/api/auth'
];

/**
 * Install event - cache static resources
 */
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('Service Worker: Static files cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Error caching static files', error);
      })
  );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

/**
 * Fetch event - handle network requests with caching strategies
 */
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip cross-origin requests that we don't control
  if (url.origin !== location.origin && !url.href.includes('telegram.org')) {
    return;
  }
  
  // Network-only resources
  if (NETWORK_ONLY.some(endpoint => url.pathname.startsWith(endpoint))) {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          // Return offline fallback for critical endpoints
          return new Response(
            JSON.stringify({ 
              error: 'Offline', 
              message: 'This feature requires an internet connection' 
            }),
            { 
              status: 503,
              headers: { 'Content-Type': 'application/json' }
            }
          );
        })
    );
    return;
  }
  
  // API endpoints - network first, cache fallback
  if (API_ENDPOINTS.some(endpoint => url.pathname.startsWith(endpoint))) {
    event.respondWith(networkFirstStrategy(event.request));
    return;
  }
  
  // Static files - cache first, network fallback
  if (STATIC_FILES.some(file => url.pathname === file || event.request.url.includes(file))) {
    event.respondWith(cacheFirstStrategy(event.request));
    return;
  }
  
  // Navigation requests - network first with offline fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(navigationStrategy(event.request));
    return;
  }
  
  // Default strategy for other requests
  event.respondWith(staleWhileRevalidateStrategy(event.request));
});

/**
 * Cache-first strategy for static resources
 */
async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Cache-first strategy failed:', error);
    return new Response('Resource unavailable offline', { status: 503 });
  }
}

/**
 * Network-first strategy for API endpoints
 */
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
    
    throw new Error('Network response not ok');
  } catch (error) {
    console.log('Network failed, trying cache:', error);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      // Add offline indicator to cached responses
      const modifiedResponse = new Response(cachedResponse.body, {
        status: cachedResponse.status,
        statusText: cachedResponse.statusText,
        headers: {
          ...cachedResponse.headers,
          'X-Served-By': 'ServiceWorker-Cache',
          'X-Cache-Date': new Date().toISOString()
        }
      });
      return modifiedResponse;
    }
    
    return new Response(
      JSON.stringify({ 
        error: 'Offline', 
        message: 'Data unavailable offline' 
      }),
      { 
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

/**
 * Navigation strategy for page requests
 */
async function navigationStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      return networkResponse;
    }
    throw new Error('Network response not ok');
  } catch (error) {
    console.log('Navigation network failed, serving offline page');
    
    // Try to serve cached version of the mobile navigation
    const cachedResponse = await caches.match('/templates/mobile_navigation.html');
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback offline page
    return new Response(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HydraX - Offline</title>
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            text-align: center; 
            padding: 50px;
            background: #f5f5f5;
          }
          .offline-message {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
          }
          .offline-icon { font-size: 48px; margin-bottom: 20px; }
          h1 { color: #333; margin-bottom: 10px; }
          p { color: #666; margin-bottom: 20px; }
          button {
            background: #2481cc;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
          }
          button:hover { background: #1a5d8a; }
        </style>
      </head>
      <body>
        <div class="offline-message">
          <div class="offline-icon">📱</div>
          <h1>You're Offline</h1>
          <p>HydraX is currently unavailable. Please check your internet connection and try again.</p>
          <button onclick="window.location.reload()">Try Again</button>
        </div>
      </body>
      </html>
    `, {
      status: 200,
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

/**
 * Stale-while-revalidate strategy
 */
async function staleWhileRevalidateStrategy(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  // Fetch in background to update cache
  const fetchPromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(() => null);
  
  // Return cached version immediately if available
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Otherwise wait for network
  return fetchPromise || new Response('Service unavailable', { status: 503 });
}

/**
 * Background sync for offline actions
 */
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync triggered', event.tag);
  
  if (event.tag === 'offline-actions') {
    event.waitUntil(processOfflineActions());
  }
});

/**
 * Process offline actions when connection is restored
 */
async function processOfflineActions() {
  try {
    // Get offline actions from IndexedDB or localStorage
    const offlineActions = await getOfflineActions();
    
    for (const action of offlineActions) {
      try {
        await fetch(action.url, action.options);
        await removeOfflineAction(action.id);
        console.log('Offline action processed:', action.id);
      } catch (error) {
        console.error('Failed to process offline action:', action.id, error);
      }
    }
  } catch (error) {
    console.error('Error processing offline actions:', error);
  }
}

/**
 * Push notification handling
 */
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push notification received');
  
  const options = {
    body: 'New trading signal available',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    tag: 'trading-signal',
    requireInteraction: true,
    actions: [
      {
        action: 'view',
        title: 'View Signal',
        icon: '/assets/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/assets/icons/action-dismiss.png'
      }
    ],
    data: {
      url: '/templates/mobile_navigation.html#signals',
      timestamp: Date.now()
    }
  };
  
  if (event.data) {
    try {
      const pushData = event.data.json();
      options.body = pushData.message || options.body;
      options.data = { ...options.data, ...pushData };
    } catch (error) {
      console.error('Error parsing push data:', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification('HydraX Trading Alert', options)
  );
});

/**
 * Notification click handling
 */
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked', event.action);
  
  event.notification.close();
  
  if (event.action === 'view') {
    const url = event.notification.data?.url || '/templates/mobile_navigation.html';
    
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          // Check if app is already open
          for (const client of clientList) {
            if (client.url.includes('mobile_navigation.html') && 'focus' in client) {
              client.postMessage({ action: 'navigate', url });
              return client.focus();
            }
          }
          
          // Open new window
          if (clients.openWindow) {
            return clients.openWindow(url);
          }
        })
    );
  }
});

/**
 * Message handling from main thread
 */
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
      case 'CACHE_SIGNAL_DATA':
        cacheSignalData(event.data.payload);
        break;
      case 'STORE_OFFLINE_ACTION':
        storeOfflineAction(event.data.payload);
        break;
      case 'GET_CACHE_STATUS':
        getCacheStatus().then(status => {
          event.ports[0].postMessage(status);
        });
        break;
    }
  }
});

/**
 * Cache signal data for offline access
 */
async function cacheSignalData(signalData) {
  try {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    const response = new Response(JSON.stringify(signalData), {
      headers: { 'Content-Type': 'application/json' }
    });
    await cache.put('/api/signals/cached', response);
    console.log('Signal data cached for offline access');
  } catch (error) {
    console.error('Error caching signal data:', error);
  }
}

/**
 * Store offline action for later processing
 */
async function storeOfflineAction(actionData) {
  try {
    // In a real implementation, use IndexedDB for better storage
    const actions = JSON.parse(localStorage.getItem('hydraX_offlineActions') || '[]');
    actions.push({
      id: Date.now() + Math.random(),
      timestamp: Date.now(),
      ...actionData
    });
    localStorage.setItem('hydraX_offlineActions', JSON.stringify(actions));
    
    // Register for background sync
    if ('sync' in self.registration) {
      await self.registration.sync.register('offline-actions');
    }
  } catch (error) {
    console.error('Error storing offline action:', error);
  }
}

/**
 * Get offline actions
 */
async function getOfflineActions() {
  try {
    return JSON.parse(localStorage.getItem('hydraX_offlineActions') || '[]');
  } catch (error) {
    console.error('Error getting offline actions:', error);
    return [];
  }
}

/**
 * Remove processed offline action
 */
async function removeOfflineAction(actionId) {
  try {
    const actions = JSON.parse(localStorage.getItem('hydraX_offlineActions') || '[]');
    const filteredActions = actions.filter(action => action.id !== actionId);
    localStorage.setItem('hydraX_offlineActions', JSON.stringify(filteredActions));
  } catch (error) {
    console.error('Error removing offline action:', error);
  }
}

/**
 * Get cache status for debugging
 */
async function getCacheStatus() {
  const cacheNames = await caches.keys();
  const status = {};
  
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    status[cacheName] = {
      size: keys.length,
      keys: keys.map(request => request.url)
    };
  }
  
  return status;
}

/**
 * Periodic cache cleanup
 */
setInterval(async () => {
  try {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    const keys = await cache.keys();
    
    // Remove old cached responses (older than 24 hours)
    const cutoff = Date.now() - (24 * 60 * 60 * 1000);
    
    for (const key of keys) {
      const response = await cache.match(key);
      const cacheDate = response.headers.get('X-Cache-Date');
      
      if (cacheDate && new Date(cacheDate).getTime() < cutoff) {
        await cache.delete(key);
        console.log('Removed old cache entry:', key.url);
      }
    }
  } catch (error) {
    console.error('Error during cache cleanup:', error);
  }
}, 60 * 60 * 1000); // Run every hour