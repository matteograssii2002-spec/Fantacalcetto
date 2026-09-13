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
  '/app/squadra.webp',
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
<title>Nessuna connessione</title>
<style>
 html,body{margin:0;height:100%;background:#0a1626;color:#eef4fd;
   font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
 .w{position:fixed;top:0;bottom:0;left:0;right:0;display:flex;flex-direction:column;
   align-items:center;justify-content:center;text-align:center;padding:26px 24px 34px;
   background:radial-gradient(120% 62% at 50% 30%, rgba(63,151,255,.20), transparent 64%)}
 .sq{position:relative;flex:0 1 auto;min-height:0;max-height:36vh;display:flex;align-items:flex-end;justify-content:center;width:100%}
 .sq::after{content:'';position:absolute;left:50%;bottom:-4px;transform:translateX(-50%);
   width:80%;height:42px;border-radius:50%;
   background:radial-gradient(50% 50% at 50% 50%, rgba(63,151,255,.38), transparent 72%)}
 .sq img{position:relative;z-index:1;width:100%;max-width:430px;max-height:36vh;object-fit:contain;
   filter:drop-shadow(0 20px 26px rgba(0,0,0,.55))}
 h1{font-size:25px;letter-spacing:-.03em;margin:28px 0 0;font-weight:800}
 p{color:#9bb2d6;font-size:13.5px;line-height:1.45;margin:9px 0 22px}
 button{width:100%;max-width:340px;background:linear-gradient(135deg,#4ea0ff,#1c6ff2);color:#fff;border:none;
   font-size:15.5px;font-weight:800;padding:15px 26px;border-radius:14px}
</style></head><body><div class="w">
 <div class="sq"><img src="/app/squadra.webp" alt="" onerror="this.style.display='none'"></div>
 <h1>Nessuna connessione</h1>
 <p>Per usare l&rsquo;app serve una connessione a internet.<br>Riparte da sola appena la rete torna.</p>
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
