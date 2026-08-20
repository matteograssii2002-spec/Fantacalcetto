# Fantacalcetto — Prossimi passi (handoff)

> File di passaggio di consegne. Allegalo a una nuova chat insieme a `index.html`,
> `FANTACALCETTO.md` e `fantacalcetto_context.py` per ripartire senza rispiegare niente.
> Aggiornato: **agosto 2026 — sessione 48 (vetrina pubblica, restyle)**.
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
| 1 | **Screenshot mancanti + immagine social** | 🟡 **è il prossimo passo** — §6 |
| 2 | Split `/app/` + landing pubblica | ⬜ da fare — §3 |
| 3 | Cookie e statistiche — solo sulla landing | ⬜ da fare — §1 |
| 4 | Privacy policy + termini di servizio | ⬜ da fare — §4 |
| 5 | RLS: «Apri subito» rifiutato in una lega nuova | ⬜ da capire — §7 |
| 6 | Sparkline posizione nella scheda manager (serve SQL) | ⬜ da fare — §2 |
| 7 | Multi-lega per `sondaggio.html` | ⬜ aperto da tempo |

**Dove siamo:** la vetrina è finita come struttura, testi e grafica; mancano **sei screenshot
e l'immagine social** (§6), che sono l'unica cosa che la tiene ferma. Poi lo spostamento
`/sito.html` → `/`, app in `/app/` (§3, checklist già corretta con quello che si è scoperto
strada facendo). Poi §1 e §4, che sono altre pagine dello stesso sito. La §5 e la §2 sono
corte e indipendenti.

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
| `02-campo.webp` | formazione schierata sul campo | passaggio 5 + anteprima (commentata) |
| `06-voti.webp` | votazioni + MVP | passaggio 7 + anteprima (commentata) |
| `07-presenze.webp` | sondaggio presenze | passaggio 4 |
| `12-bonus.webp` | inserimento gol, assist, risultato | passaggio 6 |
| `13-lega.webp` | schermata di creazione della lega | passaggio 1 |
| `14-profilo.webp` | creazione squadra e giocatore | passaggio 2 |
| `anteprima.png` | 1200×630 per WhatsApp e social | meta `og:image` |

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

Le due schermate dell'anteprima (`02-campo`, `06-voti`) sono **commentate** dentro
`sito.html`, nel carosello in cima: basta togliere le due righe di commento. Le altre hanno
già il loro segnaposto tratteggiato al posto giusto.

### Poi

Rileggere i testi sul telefono e passare alla §3. Decisione già presa e confermata: **«Suca
FC» resta**, non si rinominano gli screenshot.

---

## 7. RLS — «Apri subito» rifiutato in una lega nuova

In una lega di prova appena creata il pulsante fallisce con
`new row violates row-level security policy for table "matchdays"`, pur essendo visibile
tutto il pannello admin. Il perché e le due query di diagnosi stanno in `FANTACALCETTO.md`
§48.4. In breve: il client si fida della colonna `profiles.is_admin`, il database di
`leagues.admin_id`, e nella lega di prova le due cose non coincidono.

Da fare in una sessione dedicata, partendo dal risultato delle query. Probabile fix: un
`update` di una riga su `leagues.admin_id`. Se invece `is_operator()` non è `security
definer`, va rifatta la funzione.

---

## Come ripartire

Allegare a una nuova chat: **`PROSSIMI_PASSI.md`** (questo file), **`FANTACALCETTO.md`**,
**`fantacalcetto_context.py`**, **`index.html`** e i tre file della vetrina (**`sito.html`**,
**`sito.css`**, **`regolamento.html`**). Le immagini già fatte non servono: basta sapere che
ci sono. Poi, in ordine: finire la §6 (screenshot), poi la §3 (spostamento).
