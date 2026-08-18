# Fantacalcetto — Prossimi passi (handoff)

> File di passaggio di consegne. Allegalo a una nuova chat insieme a `index.html`,
> `FANTACALCETTO.md` e `fantacalcetto_context.py` per ripartire senza rispiegare niente.
> Aggiornato: **agosto 2026 — fine sessione 46**.
>
> Questo file guarda **avanti**. Lo storico di ogni sessione sta in `FANTACALCETTO.md`:
> quando un intervento è fatto, qui sparisce e resta solo lì.

---

## 0. Stato dei lavori

| # | Intervento | Stato |
|---|---|---|
| — | Riordino admin 1/3, 2/3, 3/3 | ✅ chiuso (sessioni 44-45) |
| — | **Revisione del login** — email+password | ✅ chiuso (sessione 46) — vedi `FANTACALCETTO.md` §46 |
| 1 | **Cookie e statistiche** — solo sulla landing | ⬜ da fare — §1 |
| 2 | Sparkline posizione nella scheda manager (serve SQL) | ⬜ da fare — §2 |
| 3 | Split `/app/` + landing pubblica | ⬜ da fare — §3 |
| 4 | Screenshot e contenuti del sito pubblico | ⬜ da fare — §3 |
| 5 | Privacy policy + termini di servizio | ⬜ da fare — §4 |
| 6 | Multi-lega per `sondaggio.html` | ⬜ aperto da tempo |

**Ordine consigliato:** §3 e §1 insieme — la landing e le statistiche sono la stessa passata
di lavoro — e §4 di seguito, perché privacy policy e landing sono due pagine dello stesso
sito. La §2 è una sessione corta e indipendente, buona per quando c'è poco tempo.

Regola di sempre: **una sessione = un intervento**, e **un solo upload di `index.html`**
per sessione.

---

## Fatto in sessione 46 (sintesi; dettagli in `FANTACALCETTO.md` §46)

Il login è passato da **codice via email a ogni accesso** a **email + password**, con una
sola porta d'ingresso: il codice a 6 cifre non fa più entrare, serve solo a verificare
l'email (registrazione e recupero). Chi c'era già se la imposta da dentro l'app, senza
nessuna email, perché è già autenticato — il segnalibro è `user_metadata.has_pw`, quindi
**zero SQL e zero migrazioni**. Errori in rosso, tradotti in italiano caso per caso.

Nessuna email contiene link: registrazione e recupero passano dal codice, per la stessa
ragione per cui il magic-link era stato abbandonato (si rompe nella PWA in standalone su
iOS). Il link di recupero, quando ancora esisteva, **apriva la sessione da solo** e portava
dentro l'app invece che al cambio password: ora è intercettato in due punti, e la rete resta
accesa per le email vecchie ancora in circolazione.

**Configurazione Supabase fatta in questa sessione:** template «Reset Password» riscritto
con `{{ .Token }}` e senza link, lunghezza OTP portata a **6 cifre**, lunghezza minima
password a 8.

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
- [ ] Spostare in `/app/`: `index.html`, `sw.js`, `manifest.webmanifest`, `sondaggio.html`, icone.
- [ ] `manifest.webmanifest`: `"start_url": "/app/"` e `"scope": "/app/"`.
- [ ] `<link rel="manifest">` **solo** in `/app/index.html`. Mai nella landing, altrimenti la
      landing diventa installabile e si torna al problema di partenza.
- [ ] Registrazione service worker → `/app/sw.js` (il SW controlla solo la propria cartella in giù).
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
- [ ] Avvisare il gruppo: chi ha l'app installata la reinstalli dal nuovo indirizzo.

### Landing — contenuti
Cos'è · Come funziona (i 4 passaggi: presenze → formazione → partita → voti e pagellone) ·
Screenshot · Regolamento e punteggi · FAQ · CTA **«Entra e gioca»** → `/app/` ·
Guida all'installazione **dentro** `/app/`, non prima.

SEO: «fantacalcetto» da solo è conteso dallo sport in sé. Puntare su code lunghe —
*app fantacalcio calcetto tra amici*, *come organizzare un fantacalcio a 5*, *regolamento
fantacalcio calcio a 5* — e su una pagina regolamento fatta bene, che è ciò che cercano
gli admin di altri gruppi.

### Screenshot da preparare (iPhone, app installata, senza barra Safari)
1. Home con classifica ← schermata simbolo
2. Campo con formazione schierata ← **la più importante**
3. Pagellone (una slide con numeri interessanti)
4. Bacheca con trofei sbloccati
5. Mercato con card giocatore aperta
6. Votazioni + MVP
7. Sondaggio presenze
8. **Scheda giocatore con l'anello del voto**
9. *(opzionale)* Notifica push sulla lockscreen

Usare una giornata con dati realistici, non tutti zeri. Valutare se i nomi degli amici
possono stare online: in caso di dubbio, soprannomi neutri per la vetrina.

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
- **Emoji su iOS:** dove serve un simbolo su fondo scuro, usare testo o caratteri veri, non
  emoji — iOS le disegna quasi nere e spariscono (è successo col «+» della `ctx-box`, per
  questo il mostra/nascondi della password è testuale).
