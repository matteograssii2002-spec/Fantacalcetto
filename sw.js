/* Fantacalcetto — service worker
   - Notifiche push (invariate)
   - HTML SEMPRE fresca: ogni navigazione va in rete bypassando la cache HTTP,
     così dopo un deploy si vede subito la versione nuova (niente pagina "vecchia" in cache).
*/
const SW_VERSION = '2026-08-16-1';   // cambia questa stringa a OGNI deploy per forzare l'aggiornamento

self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

// Navigazioni (apertura pagina / PWA): prendi SEMPRE la versione fresca dalla rete.
// Se offline, ripiega su qualunque risposta il browser abbia (nessuna cache gestita qui).
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req, { cache: 'reload' }).catch(() => fetch(req).catch(() => Response.error()))
    );
  }
  // tutte le altre richieste: comportamento di default del browser (nessuna intercettazione)
});

self.addEventListener('push', event => {
  let d = { title: 'Fantacalcetto', body: '', url: '/' };
  try { d = Object.assign(d, event.data.json()); }
  catch (_) { if (event.data) d.body = event.data.text(); }
  event.waitUntil(
    self.registration.showNotification(d.title, {
      body: d.body,
      icon: 'icon-512.png',
      badge: 'icon-180.png',
      data: { url: d.url || '/' }
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) { if ('focus' in c) return c.focus(); }
      if (self.clients.openWindow) return self.clients.openWindow(url);
    })
  );
});
