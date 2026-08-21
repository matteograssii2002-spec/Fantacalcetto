# Fantacalcetto — Prossimi passi (handoff)

> File di passaggio di consegne. Allegalo a una nuova chat insieme a `index.html`,
> `FANTACALCETTO.md` e `fantacalcetto_context.py` per ripartire senza rispiegare niente.
> Aggiornato: **agosto 2026 — sessione 49 (multi-lega: il gioco funziona in ogni lega)**.
>
> Questo file guarda **avanti**. Lo storico di ogni sessione sta in `FANTACALCETTO.md`:
> quando un intervento è fatto, qui sparisce e resta solo lì.

---

## 0. Stato dei lavori

| # | Intervento | Stato |
|---|---|---|
| — | Riordino admin 1/3, 2/3, 3/3 | ✅ chiuso (sessioni 44-45) |
| — | **Revisione del login** — email+password | ✅ chiuso (sessione 46) — `FANTACALCETTO.md` §46 |
| — | **Vetrina: struttura, testi, grafica, tutorial installazione** | ✅ chiuso (sessioni 47-48) — `FANTACALCETTO.md` §47 |
| — | **Multi-lega: il `league_id` finiva sempre a 1** | ✅ chiuso (sessione 49) — `FANTACALCETTO.md` §49 |
| — | Multi-lega per `sondaggio.html` | ✅ chiuso (sessione 49): file cancellato, `value_poll` è già per-lega |
| 1 | **Screenshot: restano `07-presenze`, `14-profilo`, `anteprima.png`** | 🟡 **è il prossimo passo** — §6 |
| 2 | Split `/app/` + landing pubblica | ⬜ da fare — §3 |
| 3 | Cookie e statistiche — solo sulla landing | ⬜ da fare — §1 |
| 4 | Privacy policy + termini di servizio | ⬜ da fare — §4 |
| 5 | Sparkline posizione nella scheda manager (serve SQL) | ⬜ da fare — §2 |

**Dove siamo:** la sessione 49 ha tolto di mezzo il guasto che rendeva il gioco utilizzabile
**solo nella lega 1** — era la vecchia §7, e si è rivelata molto più grossa di come era stata
archiviata (`FANTACALCETTO.md` §49). Da adesso una lega creata da uno sconosciuto funziona
come la nostra: verificato con la query di controllo, nessun `1` scritto a mano rimasto in
nessuna funzione e in nessuna policy.

La vetrina è finita come struttura, testi e grafica; mancano **tre screenshot e l'immagine
social** (§6), che sono l'unica cosa che la tiene ferma. Poi lo spostamento `/sito.html` → `/`,
app in `/app/` (§3, checklist già corretta con quello che si è scoperto strada facendo). Poi §1
e §4, che sono altre pagine dello stesso sito. La §2 è corta e indipendente.

Regola di sempre: **una sessione = un intervento**, e **un solo upload di `index.html`**
per sessione.

---

---

## 1. Cookie e statistiche

**La risposta breve: oggi non serve nessun banner, e sull'app non servirà mai** — a patto
di non metterci dentro statistiche o terze parti.

Il motivo è che l'app usa solo **storage tecnico**: token di sessione, preferenze, service
worker. Quella roba è esente da consenso; va soltanto dichiarata nell'informativa. Il
banner scatta quando compare qualcosa di **non necessario al servizio**, e le statistiche
di uso lo sono.

Quindi il piano è: **statistiche solo sulla landing pubblica, `/app/` resta pulita.** È un
altro motivo per cui lo split di §3 ha senso. Sulla landing il banner ci vuole, con tre
accortezze:

- il consenso va raccolto **prima** di caricare lo script di analytics, non dopo;
- uno strumento in modalità **cookieless** (persistenza in memoria) rafforza l'esenzione ma
  non la garantisce: il Garante italiano è prudente, meglio il banner;
- ⚠️ **niente dark pattern**: «Accetta tutti» e «Solo essenziali» devono avere la **stessa
  evidenza grafica**. Il Garante ha sanzionato banner in cui il rifiuto era meno visibile.

Da fare insieme alla landing, non prima.

---

## 2. Sparkline della posizione (scheda manager)

Nella proposta grafica c'era, nell'implementazione no: il dato esiste in SQL
(`_season_rank_history`, usato per «Al comando» e «Scalatore») ma **non è esposto da
nessuna RPC**, e ricostruirlo lato client vorrebbe dire una chiamata per ogni giornata
chiusa. Serve una RPC leggera tipo `get_team_rank_history(p_manager, p_season)` →
`(giornata, pos)`. Piccola migrazione a sé, da fare in una sessione dedicata.

---

## 3. Split sito pubblico / app

### Struttura
```
fantacalcettoitalia.it/          → sito pubblico (cos'è, come funziona, regolamento, FAQ)
fantacalcettoitalia.it/app/      → il gioco (index.html attuale)
```

### Checklist tecnica
- [ ] Spostare in `/app/`: `index.html`, `manifest.webmanifest`, `sondaggio.html`.
- [ ] ⚠️ **CORREZIONE (sessione 47) — `sw.js` NON si sposta, e nemmeno le icone.**
      Le iscrizioni push in `push_subscriptions` sono legate alla *registrazione* del service
      worker, che oggi è `/sw.js` con scope `/`. Registrarne uno nuovo in `/app/sw.js` è una
      registrazione **diversa**: tutti perderebbero le notifiche e dovrebbero riattivarle a mano.
      Quindi `sw.js` resta alla radice e in `index.html` si cambia una riga sola:
      `navigator.serviceWorker.register('sw.js')` → `register('/sw.js')`.
      Nessun header `Service-Worker-Allowed` da configurare: uno script servito da `/` può già
      prendere scope `/`, da qualunque pagina venga registrato. Registrazione identica a prima
      → notifiche intatte, zero righe da toccare nel database.
- [ ] `manifest.webmanifest`: `"start_url": "/app/"`, `"scope": "/app/"` e **in più `"id": "/"`**.
      L'`id` serve a non duplicare l'icona su Android: l'identità della PWA installata è oggi
      `/` (il vecchio start_url), e tenendola ferma l'installazione esistente viene *aggiornata*
      invece di comparire una seconda volta. Le icone restano alla radice: nel manifest i loro
      percorsi sono già assoluti (`/icon-512.png?v=4`), quindi non serve toccarli.
- [ ] iOS ignora il manifest dopo l'installazione: chi ha già l'app sull'iPhone resterà con
      `start_url = /` per sempre. Per loro serve **solo** il redirect in standalone (riga sotto).
- [ ] `notify.ts`: tutti gli `url` delle push da `"/"` a `"/app/"`, e `"/?srecap="` → `"/app/?srecap="`.
      Sono in `runAutoOpen`, `runLineupOpen`, `runReminder`, `runAutoClose`, `runPresenceReminder`,
      `runLineupReminder`, `runSeasonRecap`.
- [ ] ⚠️ **Nuovo da sessione 46:** il `redirectTo` di `resetPasswordForEmail` usa
      `location.origin+location.pathname`, quindi da `/app/` punterà da solo alla cartella
      giusta — ma va verificato che l'indirizzo sia nella **allow-list dei redirect** di
      Supabase (Authentication → URL Configuration), altrimenti Supabase ripiega sul Site URL.
- [ ] Deep link `?recap=` e `?srecap=` verificati sul nuovo percorso.
- [ ] In `/index.html` (landing) uno script: se `display-mode: standalone` → redirect a `/app/`.
      Serve a non rompere le installazioni già presenti sui telefoni degli amici, che puntano a `/`.
- [ ] **Nessun** redirect `/` → `/app/` per i browser normali: ucciderebbe la landing.
- [ ] Bump di `SW_VERSION` in `sw.js` **e** di `APP_VERSION` in `index.html`.
- [ ] In `sito.html` e `regolamento.html`: `var APP_URL = '/'` → `'/app/'` (una riga per file),
      togliere `<meta name="robots" content="noindex,nofollow">`, correggere i `canonical`,
      rinominare `sito.html` in `index.html`. ⚠️ Il gioco oggi è alla radice, quindi `/index.html`
      dell'app e `sito.html` rinominato **collidono**: l'app va spostata in `/app/` nello stesso
      commit, non prima e non dopo.
- [ ] Aggiungere `robots.txt` e `sitemap.xml` (non esistono ancora).
- [ ] Avvisare il gruppo: chi ha l'app installata la reinstalli dal nuovo indirizzo.

### Landing — contenuti

> **Chiuso in sessioni 47-48.** Struttura, testi e grafica stanno in `FANTACALCETTO.md` §47;
> gli screenshot che restano da fare sono nella §6 qui sotto.

SEO: «fantacalcetto» da solo è conteso dallo sport in sé. Puntare su code lunghe —
*app fantacalcio calcetto tra amici*, *come organizzare un fantacalcio a 5*, *regolamento
fantacalcio calcio a 5* — e su una pagina regolamento fatta bene, che è ciò che cercano
gli admin di altri gruppi.

---

## 4. Privacy policy e termini (obbligatori, PWA o no)

Il GDPR guarda al trattamento dei dati, non al canale di distribuzione: **la PWA non
esenta da niente**. L'app tratta email, nome, soprannome, avatar, nome squadra, presenze
ed endpoint delle push → serve un'**informativa ex art. 13**, mostrata nel punto in cui i
dati si raccolgono (schermata di accesso) e linkata dalle Impostazioni.

- Titolare del trattamento: Giulio. Responsabili esterni da nominare: **Supabase, Vercel,
  Resend**. Verificare i loro DPA e, dove i server sono fuori UE, le clausole contrattuali
  standard. Se possibile tenere Supabase su region europea.
- ⚠️ **Aggiornamento sessione 46:** ora si trattano anche **password** — custodite da
  Supabase Auth, mai viste né conservate dall'app. Va detto nell'informativa.
- Push: il permesso del browser è già il consenso; nell'informativa va scritto a cosa
  servono.
- Età minima nei termini: sotto i 14 anni servirebbe il consenso dei genitori.
- Quando si comincerà a incassare, all'informativa vanno affiancati i **Termini di
  servizio**.
- Se si aggiungono le statistiche sulla landing (§1), vanno dichiarate qui.

Da scrivere insieme alla landing (§3): sono due pagine dello stesso sito.

---

## 5. Strategia — sintesi

**Ora: PWA, gratis, misurare.** Costo di distribuzione zero, deploy immediato, nessuna
review. E se un domani si monetizza, sul web Stripe costa ~2% contro il 15-30%
dell'in-app purchase obbligatorio su iOS.

**Il limite vero:** su iPhone le push funzionano **solo** se l'app è stata aggiunta alla
Home. Il restare loggati invece pesa meno di prima: con la password chi viene buttato fuori
rientra in due secondi invece di aspettare un'email. Resta comunque vero che iOS cancella lo
storage dopo 7 giorni di inattività sui siti **non installati**. La metrica di sopravvivenza
è il **tasso di installazione**, non i download.

**Segnale per il passo successivo:** una lega non tua, con un admin che non conosci, che
sopravvive a 4+ giornate consecutive. Soglia pratica: **3-5 leghe attive non tue per un
mese**. Sotto quella soglia non toccare né store né pagamenti.

### Partita IVA — quello che è emerso

- **Gratis con tutte le leghe pro: non serve niente.** Nessun incasso, nessun obbligo.
- **Appena si incassa, serve**, e la forma del pagamento non cambia nulla: il criterio
  italiano è l'**abitualità**, che si valuta dal lato di chi vende, non del cliente.
  Vendere «Stagione pro» a dieci leghe una volta l'anno è abituale esattamente come dieci
  abbonamenti mensili. **Non esiste** la soglia dei 5.000 € come esenzione: quella
  riguarda i contributi INPS sul lavoro autonomo occasionale.
- **La transazione singola resta comunque la scelta giusta**, ma per altri motivi: niente
  obblighi sul rinnovo automatico (dal 19 giugno 2026 c'è anche il pulsante di recesso
  obbligatorio), contabilità più semplice, nessuno che si arrabbia per un addebito
  inatteso.
- Inquadramento probabile: **forfettario**, tetto 85.000 €, imposta sostitutiva al **5%**
  per i primi 5 anni se non hai esercitato attività d'impresa nei 3 anni precedenti,
  contributi in **Gestione Separata INPS ~26%** sul reddito imponibile **senza minimi
  fissi**. Fattura elettronica obbligatoria.
- ⚠️ Da verificare con un commercialista prima di aprire qualsiasi cosa.

### Pubblicità — decisione presa: no (per ora)

Tecnicamente si può (una PWA è un sito, AdSense funziona), ma con 15-20 persone parliamo di
qualche euro al mese, imporrebbe un banner di consenso con CMP certificata su un'app che
oggi non ne ha bisogno, e contraddice il piano di far pagare l'admin. Alternative sensate:
**uno sponsor locale** (il centro sportivo, il bar) con logo statico e zero tracciamento,
oppure pubblicità **solo sulla landing** se farà traffico da SEO.

---

## Invarianti da non rompere (promemoria)

- `esito`: **+2 vittoria / −1 sconfitta**, identico in `scoreOf()` (client) e `get_standings_md` (SQL).
- **Il `league_id` lo mette il DEFAULT della colonna**, non un trigger. Una tabella dati nuova
  va creata con `league_id bigint default league_default() references leagues(id)`. Non esiste
  più nessun `default 1`: se ricompare, è un guasto silenzioso che colpirà la prima lega
  diversa dalla 1. `stamp_league` è **morta** (resta in DB con un commento che lo dice).
- I default dipendono da `my_league()` / `league_default()`: un `drop function my_league()`
  fallirà con un errore di dipendenza. È **voluto**; `create or replace` funziona.
- **Prima di dire che un trigger esiste, guardare `pg_trigger`.** Vedi §7.
- `notify.ts` **non entra mai** in GitHub: contiene i segreti.
- `league_id` è **BIGINT**, non UUID.
- SQL sempre idempotente e in ordine di dipendenza (Supabase fa rollback totale sull'errore).
- iOS: `position:fixed` con `top`/`bottom` espliciti, mai altezze in unità viewport.
- Validare JS/HTML prima di consegnare. **L'autorità è `node --check`**, non lo scanner di
  parentesi casereccio (che fallisce sui letterali regex, anche sul file originale).
- **Una card della Home = `hcardHTML`**. Non scrivere markup di card a mano.
- **Un'azione di giornata = `MD_ACTIONS`**. Non scrivere `<button>` a mano nei render.
- **Una fase di giornata = `MD_PHASES` + `mdPhaseIdx()`**. Non reintrodurre calcoli paralleli.
- **Un sottotitolo di riga nelle Impostazioni = `renderRuleRows()`**. Unico punto.
- **Riaccendere un elemento = `display=''`**, mai `'block'`: le `.navrow` sono `flex`.
- Collocazione: giornata in corso → Centro giornata · interruttore → Regole della lega ·
  scelta di persone → Gestione lega · roba rara → Aiuto e manutenzione.
- Le chiavi Supabase sono **dentro** il file consegnato (`sb_publishable_…` è pubblica per
  design): non serve re-incollarle, ma va verificato che ci siano.
- Patch script: scrivere su `.tmp` + `os.replace`, mai direttamente in `'w'`.
- **Da sessione 46 — accesso:** una sola porta (email + password). Il codice a 6 cifre
  verifica l'email, non fa entrare. **Nessuna email contiene link.** Chi non ha ancora una
  password si riconosce da `user_metadata.has_pw` mancante. Se un giorno si vorrà aggiungere
  un altro modo per entrare, prima chiedersi se vale il doppio costo di manutenzione.
- **Vetrina ≠ app.** Nel sito pubblico non deve MAI comparire `<link rel="manifest">` né la
  registrazione del service worker: renderebbe installabile la vetrina, che è esattamente il
  problema che lo split vuole risolvere. E non copiare il CSS dell'app senza pulirlo:
  `user-select:none`, barre di scorrimento nascoste e altezze fisse sono regole da app, su un
  sito rendono il testo non copiabile e lo scroll strano.
- **Le iscrizioni push seguono la registrazione del service worker, non il file.** Spostare
  `sw.js` = perdere tutte le notifiche del gruppo. Vedi §3.
- **Emoji su iOS:** dove serve un simbolo su fondo scuro, usare testo o caratteri veri, non
  emoji — iOS le disegna quasi nere e spariscono (è successo col «+» della `ctx-box`, per
  questo il mostra/nascondi della password è testuale).
- **Vetrina — la scocca del telefono:** `aspect-ratio` va su `.phone-screen`, mai su `.phone`
  (la cornice falsa il rapporto e lo screenshot esce). `--ar` = le proporzioni vere
  dell'immagine: 640/1306 le schermate dell'app, 640/1387 quelle dell'installazione.
- **Vetrina — i cerchi rossi:** le percentuali di `.hot` valgono solo perché lo schermo ha lo
  stesso rapporto dell'immagine. Rifatto uno screenshot, vanno rimisurate (tabella in
  `FANTACALCETTO.md` §47.5) e vanno rifatte le sfocature privacy.
- **Vetrina — `sito.css?v=N`:** alzare la versione in `sito.html` **e** in `regolamento.html`,
  sempre insieme.
- **Un solo pulsante d'azione sulla vetrina: «Gioca ora».** E testi all'imperativo, mai
  «schieri / vi votate».

---

## 6. Vetrina — quello che manca (il prossimo passo)

Struttura, testi, grafica e tutorial d'installazione sono **chiusi**: com'è fatta sta in
`FANTACALCETTO.md` §47, che è la fonte da leggere prima di toccarla.

### Screenshot mancanti

Tutti larghi **640 px**, WebP qualità 82, nella cartella `sito/`. Le schermate dell'app vanno
tagliate dei primi **150 px** (barra di stato) → 640×1306. Basta mandarle grezze: il ritaglio,
il ridimensionamento e la conversione si fanno in sessione.

| file | cosa | dove serve |
|---|---|---|
| `07-presenze.webp` | sondaggio presenze | passaggio 4 |
| `14-profilo.webp` | creazione squadra e giocatore | passaggio 2 |
| `anteprima.png` | 1200×630 per WhatsApp e social | meta `og:image` |

Fatti in sessione 49: `02-campo`, `06-voti`, `12-bonus`, `13-lega`.

⚠️ Per fotografare il **sondaggio presenze** serve una giornata aperta col ciclo normale, e
«Apri subito» non va bene perché salta sempre il sondaggio (vedi `FANTACALCETTO.md` §48).
Scorciatoia dall'SQL Editor, dove RLS non blocca — il `league_id` va **esplicito**, altrimenti
il trigger timbra la lega 1:

```sql
insert into matchdays (league_id, status, kickoff, vote_deadline)
values (<id della lega di prova>, 'open',
        now() + interval '48 hours',
        now() + interval '73 hours');
```

Con il fischio d'inizio a 48h il sondaggio è aperto (chiude a −36h). La label la mette il
trigger `stamp_season`.

### Quando arrivano

Le due schermate dell'anteprima (`02-campo`, `06-voti`) erano commentate nel carosello in cima
a `sito.html`: **il commento è già stato tolto in sessione 49**, le immagini ci sono. Le due
che restano hanno già il loro segnaposto tratteggiato al posto giusto.

### Poi

Rileggere i testi sul telefono e passare alla §3. Decisione già presa e confermata: **«Suca
FC» resta**, non si rinominano gli screenshot.

---

## 7. ✅ CHIUSA — RLS, «Apri subito» in una lega nuova

Risolta in sessione 49, ma **non era quello che c'era scritto qui**. Il racconto completo sta
in `FANTACALCETTO.md` §49; in breve, per non ripetere l'errore:

- La diagnosi archiviata (disallineamento `profiles.is_admin` vs `leagues.admin_id`) era
  **sbagliata**: i due valori coincidevano.
- La causa vera: **il trigger `stamp_league` non è mai esistito**. C'era la funzione, la
  documentazione la dava per attiva, ma nessuna tabella la richiamava — e il `league_id`
  arrivava dal `default 1` della colonna. Nella lega 1 il default sbagliato coincideva con la
  risposta giusta, quindi per due anni non si è visto niente.
- Non era un fastidio della lega di prova: **nessuna lega diversa dalla 1 poteva funzionare**.
- Cura: `multilega.sql` (default → `league_default()` su 17 tabelle + riparazione delle righe
  storte), `verifica_multilega.sql`, `profili_default.sql`.

**La lezione da portarsi dietro:** prima di dare per buono un pezzo di infrastruttura descritto
nella documentazione, guardarlo nel catalogo (`pg_trigger`, `pg_policies`, `pg_proc`). E quando
un guasto si vede solo in un caso nuovo, sospettare che il caso vecchio funzionasse **per
coincidenza**.

---

## Come ripartire

Allegare a una nuova chat: **`PROSSIMI_PASSI.md`** (questo file), **`FANTACALCETTO.md`**,
**`fantacalcetto_context.py`**, **`index.html`** e i tre file della vetrina (**`sito.html`**,
**`sito.css`**, **`regolamento.html`**). Le immagini già fatte non servono: basta sapere che
ci sono. Poi, in ordine: finire la §6 (mancano `07-presenze`, `14-profilo`, `anteprima.png`),
poi la §3 (spostamento).

Per gli screenshot che restano serve una **giornata aperta col ciclo normale** (`07-presenze`):
«Apri subito» non va bene perché salta sempre il sondaggio. La scorciatoia dall'SQL Editor è
sempre quella in §6 — e ora che i default sono a posto il `league_id` esplicito **non è più
obbligatorio**, ma conviene metterlo lo stesso: nell'SQL Editor `auth.uid()` è NULL, quindi
`league_default()` ripiega comunque sulla lega 1.
