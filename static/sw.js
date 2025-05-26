// PGG Tour Service Worker for PWA functionality
const CACHE_NAME = 'pgg-tour-v1';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/manifest.json',
  '/scorecard',
  '/leaderboard',
  '/stats',
  '/roster',
  '/awards',
  '/hole-in-one',
  '/schedule',
  // Add other important pages and assets
];

// Install event - cache resources
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('🚀 PGG Tour cache opened');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline score submission
self.addEventListener('sync', function(event) {
  if (event.tag === 'background-sync-scores') {
    event.waitUntil(syncScores());
  }
});

function syncScores() {
  // This would sync any offline-submitted scores when connection returns
  console.log('🔄 Syncing offline scores...');
  // Implementation would depend on your offline storage strategy
}
