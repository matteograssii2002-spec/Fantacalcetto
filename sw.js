/* Fantacalcetto — service worker
   - Notifiche push (INVARIATE: stesso file, stessa posizione, stessa registrazione,
     quindi nessuna iscrizione si perde)
   - HTML SEMPRE fresca: ogni navigazione va in rete bypassando la cache HTTP,
     così dopo un deploy si vede subito la versione nuova.
   - NOVITÀ 3.5 — avvio offline: dell'ultima navigazione andata a buon fine si
     tiene una copia. Se la rete non risponde si serve quella, l'app parte, non
     trova Supabase e mostra la sua schermata offline. Prima, senza rete e senza
     app già aperta, restava una pagina bianca.
     La copia si usa SOLO quando la rete fallisce: la regola dell'HTML fresca
     non cambia.
*/
const SW_VERSION = '2026-09-13-offline-a';   // cambia questa stringa a OGNI deploy
const CACHE      = 'fc-shell-' + SW_VERSION;

/* Il minimo per far partire l'app senza rete. La libreria di Supabase sta in un
   CDN: senza di lei lo script muore prima di poter mostrare qualunque cosa. */
const SHELL = [
  '/app/',
  '/app/index.html',
  'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2',
  '/icon-192.png',
  '/icon-512.png'
];

/* Una risposta che arriva da un reindirizzamento non si può rimettere in cache
   così com'è: si ricostruisce. */
async function putSafe(cache, key, res){
  try{
    if(!res || !res.ok) return;
    if(res.redirected){
      const body = await res.clone().blob();
      await cache.put(key, new Response(body, { status:200, headers:res.headers }));
    } else {
      await cache.put(key, res.clone());
    }
  }catch(_){ }
}

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // uno per uno: se un file non si scarica, gli altri si salvano lo stesso
    await Promise.all(SHELL.map(async url => {
      try{
        const res = await fetch(url, { cache:'reload' });
        await putSafe(cache, url, res);
      }catch(_){ }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const nomi = await caches.keys();
    await Promise.all(nomi.map(n => (n.startsWith('fc-shell-') && n !== CACHE) ? caches.delete(n) : null));
    await self.clients.claim();
  })());
});

/* Pagina di scorta per tutto ciò che non è l'app (per esempio la vetrina). */
const OFFLINE_HTML = `<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Senza connessione</title>
<style>
 html,body{margin:0;height:100%;background:#0a1a2f;color:#eaf1fb;
   font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
 .w{position:fixed;top:0;bottom:0;left:0;right:0;display:flex;flex-direction:column;
   align-items:center;justify-content:center;text-align:center;padding:28px}
 .i{width:74px;height:74px;border-radius:20px;background:rgba(63,151,255,.14);
   border:1px solid rgba(120,170,255,.3);display:flex;align-items:center;justify-content:center;
   font-size:34px;margin-bottom:18px}
 h1{font-size:20px;margin:0 0 8px} p{color:#9fb8d8;font-size:14px;line-height:1.5;margin:0 0 22px;max-width:300px}
 button{background:linear-gradient(135deg,#4ea0ff,#1c6ff2);color:#fff;border:none;
   font-size:15px;font-weight:800;padding:13px 26px;border-radius:12px}
</style></head><body><div class="w">
 <div class="i">&#9917;</div>
 <h1>Nessuna connessione</h1>
 <p>Controlla la rete o la modalit&agrave; aereo: appena torna, la pagina si ricarica da sola.</p>
 <button onclick="location.reload()">Riprova</button>
 <script>addEventListener('online',()=>location.reload());<\/script>
</div></body></html>`;

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const isApp = url.origin === self.location.origin && url.pathname.startsWith('/app');

  // NAVIGAZIONI: prima la rete (HTML sempre fresca), la copia solo se la rete manca.
  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      try{
        const res = await fetch(req, { cache:'reload' });
        if (isApp) { const c = await caches.open(CACHE); await putSafe(c, '/app/index.html', res); }
        return res;
      }catch(_){
        if (isApp) {
          const hit = await caches.match('/app/index.html');
          if (hit) return hit;
        }
        const any = await caches.match(req);
        if (any) return any;
        return new Response(OFFLINE_HTML, { headers:{ 'Content-Type':'text/html; charset=utf-8' } });
      }
    })());
    return;
  }

  // I pochi file dell'ossatura: prima la cache (istantanei), poi si aggiornano di
  // nascosto per la volta dopo. Tutto il resto passa liscio come prima.
  const chiave = SHELL.find(u => u === url.href || u === url.pathname);
  if (!chiave) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(chiave);
    const rete = fetch(req).then(res => { putSafe(cache, chiave, res); return res; }).catch(() => null);
    return hit || (await rete) || Response.error();
  })());
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
