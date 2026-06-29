# Fantacalcetto — Guida al progetto (handoff)

> Documento di contesto. Se apri una **nuova chat**, leggi prima questo: spiega cos'è l'app, com'è fatta, dove vive e come si aggiorna. L'assistente deve continuare a **rispondere in italiano** e ricordare che l'utente (Giulio, display name "Teo") lavora **da iPhone** e non è uno sviluppatore: vanno dati passi guidati, semplici, uno alla volta.

---

## 1. Cos'è

Fantacalcetto è un **fantasy game per un gruppo di amici che gioca a calcetto a 5** una volta a settimana. Ogni partecipante è contemporaneamente:

- un **giocatore** (sta nel "listone"/pool e può essere schierato dagli altri),
- un **fanta-manager** (ha una squadra e schiera 5 giocatori presi dal listone).

Si gioca a **giornate**. Ogni giornata: budget **100 crediti**, si schierano **5 giocatori** (ognuno costa 20 cr), e la formazione si **rifà da zero ogni giornata** (stile "F1"). Classifica **unica e condivisa** per punti totali stagionali.

C'è anche la modalità **solo manager** (per amici/fidanzate che non giocano a calcetto ma vogliono fare il fanta): hanno la squadra ma non entrano nel listone.

---

## 2. Stack & dove vive

- **Un unico file** `index.html` autocontenuto: HTML + CSS + JS vanilla in un solo file.
- Carica `supabase-js` UMD via CDN, poi uno `<script>` **non-module** (così gli `onclick` inline funzionano come funzioni globali).
- Tema **blu scuro**; campo verde. Font: Bricolage Grotesque (titoli), Hanken Grotesk (testo), JetBrains Mono (numeri).
- **Backend**: Supabase (progetto "Fantacalcetto").
- **Hosting**: repo GitHub `Fantacalcetto` (utente `matteograssii2002`) → deploy automatico su **Vercel**.
  - URL Vercel: `https://fantacalcetto-zeta.vercel.app`
  - Dominio custom: **`fantacalcettoitalia.it`** (su Aruba). Il principale è `www.fantacalcettoitalia.it`; l'apex fa 308 → www. Record su Aruba: `A @ → 216.198.79.1`, `CNAME www → 5bb2fdcd25437f2d.vercel-dns-017.com.` (NON toccare i record email; NON cambiare i nameserver).
- **Icona app**: `icon-180.png` (apple-touch-icon) e `icon-512.png` (manifest), nella **root del repo**, accanto a `index.html`.

---

## 3. Come si aggiorna (workflow di deploy) — IMPORTANTE

Il file viene modificato dall'assistente e ripresentato. L'utente poi:

1. Scarica l'ultimo `index.html`.
2. **Incolla le chiavi Supabase** in cima allo `<script>` (vedi §4) — il file consegnato ha dei **placeholder**.
3. Lo carica su GitHub (Add file → Upload files) **rinominandolo `index.html`**.
4. Vercel ridistribuisce da solo in ~1 minuto.
5. Se è cambiata l'icona: carica anche i PNG e **rimuove/ri-aggiunge** la PWA alla home (iOS legge l'icona solo alla nuova installazione).

**Regole d'oro per l'assistente:**

- È sempre lo **stesso** `index.html`: ogni versione contiene **tutte** le modifiche precedenti. Si carica solo l'ultima.
- Prima di presentare il file, **validare** sempre il bilanciamento di `{}`, `()`, `[]` e dei backtick nel blocco `<script>`, e controllare che le stringhe chiave esistano.
- Indicare sempre **se serve eseguire SQL** su Supabase e **se servono nuovi PNG**, distinguendo "da fare ora" vs "dopo".
- Ricordare di **re-incollare le chiavi** ogni volta che si ricarica il file intero.

---

## 4. Configurazione chiavi

In cima allo `<script>` ci sono due costanti da compilare:

```js
const SUPABASE_URL  = "https://<PROGETTO>.supabase.co";  // Project URL (Settings → API / Connect)
const SUPABASE_ANON = "sb_publishable_xxx";              // Publishable key (NON la secret!)
```

- Usare la **Publishable key** (`sb_publishable_...`), mai la `sb_secret_...`.
- Sono i nuovi formati chiave Supabase.

---

## 5. Modello dati (Supabase / Postgres)

Tabelle e colonne **come usate dall'app** (la DDL originale di alcune tabelle è stata creata in sessioni precedenti; qui sotto la struttura effettiva):

- **profiles** — un record per account.
  `id` uuid (= `auth.uid()`), `team_name` text, `player_name` text, `role` text, `avatar` text, `is_admin` bool, `is_player` bool (default true; false = solo manager).
- **players** — il listone.
  `id` bigint, `name` text, `role` text (`ATT`/`DIF`), `avatar` text, `present` bool (legacy globale), `forma` int (legacy, non usata nei punti), `owner_id` uuid, `injured` bool (default false), `cost` int (default 20), **`valore` numeric** (forza 1–10 per il generatore squadre; visibile/modificabile solo admin).
- **matchdays** — le giornate.
  `id` bigint, `label` text (es. "Giornata 3"), `kickoff` timestamptz, `status` text in (`open`,`voting`,`locked`,`closed`), **`closed_at` timestamptz** (istante di chiusura, per la finestra 24h delle frecce), `reminder_sent` bool.
- **lineups** — formazioni schierate.
  `matchday_id` bigint, `manager_id` uuid, `slot` text (`a1`,`a2`,`a3`,`d1`,`d2`,`d3`,`g1`), `player_id` bigint, `is_captain` bool. **CHECK `lineups_slot_check`** ammette i 7 slot elencati (ampliato per i moduli).
- **lineup_modules** — modulo scelto da ogni manager per giornata.
  `matchday_id` bigint, `manager_id` uuid, `module` text (`1-2-2`/`1-3-1`/`1-1-3`), PK composta.
- **votes** — voti 1-10 dati dai membri.
  `matchday_id`, `voter_id` uuid, `player_id` bigint, `score` int.
- **match_stats** — bonus/malus oggettivi inseriti dall'admin.
  `matchday_id`, `player_id`, `gol` int, `assist` int, `autogol` int, `gol_subiti` int, **`esito` text** (`V` vittoria / `S` sconfitta / null) = risultato della **vera** squadra di calcetto.
- **nominations** — nomination MVP di ciascun membro.
  `matchday_id`, `voter_id` uuid, `mvp_player_id` bigint, `sega_player_id` bigint (**colonna legacy: la SEGA è stata rimossa, vi si scrive sempre null**).
- **matchday_players** — chi gioca in una data giornata.
  `matchday_id` bigint, `player_id` bigint, PK composta. La **presenza statistica** è però conteggiata solo da quando si bloccano le formazioni (vedi §6/§7).
- **extra_voters** — manager-solo abilitati a votare anche se non giocano.
  `profile_id` uuid PK.

**Storage**: bucket **`avatars`** (pubblico), contiene i PNG degli avatar caricati a mano. L'app li lista e usa l'URL pubblico.

---

## 6. Regole di gioco e punteggio (devono COINCIDERE tra client e DB)

- Ruoli giocatore **fissi**: ATT o DIF.
- **Tre moduli**, scelti dal manager prima del kickoff (slot ATT accettano solo ATT, DIF solo DIF, **POR chiunque**); il modulo si salva in `lineup_modules`, cambiarlo svuota la formazione:
  - **1-2-2** (2 ATT, 2 DIF, 1 POR) — default, **nessun bonus**.
  - **1-3-1** (1 ATT, 3 DIF, 1 POR) — parti da **+5**.
  - **1-1-3** (3 ATT, 1 DIF, 1 POR) — parti da **−5**.
- Ogni giocatore costa i suoi crediti (`players.cost`, default 20), budget **100**, in campo **esattamente 5**.

Punteggio di un giocatore schierato in una giornata = **voto×moltiplicatore + bonus** (i bonus NON vengono moltiplicati):

1. **voto** = media dei voti ricevuti (se nessun voto → **6**). Moltiplicatore: `×2` se **MVP**, `×2` se **Capitano**, cumulabili (→ `×4`). **Il moltiplicatore agisce SOLO sul voto.**
2. **bonus/malus** (sommati, mai moltiplicati): gol **+3** · assist **+2** · autogol **−3** · se nello slot **POR** `+3` (imbattuto) o `−gol_subiti` · **risultato squadra reale** `+1` se la sua squadra di calcetto ha vinto, `−1` se ha perso (`match_stats.esito` = `V`/`S`/null). *(Cambiato da ±2 a ±1.)*

Punti del manager nella giornata = **bonus_modulo** (+5/−5/0) **+ Σ punti dei 5 giocatori**.

MVP: vince **il più nominato** dal gruppo (a parità, id più basso), `×2` sul voto. **La SEGA è stata rimossa** (si vota solo MVP + i voti 1–10).

**Presenza (statistica).** Conta solo dalle giornate in cui si sono **bloccate le formazioni** (kickoff − 1h passato) o che sono `closed`. Aprire una giornata non genera più presenze; un reset le rimuove.

**Classifica.** La classifica generale somma **solo le giornate `closed`**: la giornata in corso (e il suo bonus modulo) compare per tutti **solo quando l'admin la chiude**. Così dal totale non si intuisce il modulo prima del match.

---

## 7. Ciclo di una giornata (admin)

In Impostazioni l'admin può:

- **Aprire una nuova giornata**: sceglie il `kickoff` (datetime-local). Da lì: blocco formazioni = kickoff − 1h; apertura voti = kickoff + 1h; chiusura voti = +24h. All'apertura i giocatori sono segnati presenti di default (per la schierabilità), ma la **presenza statistica** scatta solo al blocco formazioni (vedi §6).
- **Scegliere i presenti** ("Chi gioca questa giornata"): toggle per giocatore → tabella `matchday_players`. Solo i presenti sono schierabili e votabili; gli assenti appaiono opachi nel mercato.
- **Inserire bonus/malus**: tendina giocatore + campi gol/assist/autogol/gol presi **+ Risultato squadra (Vittoria/Sconfitta)** → `match_stats`. Il pannello è **bloccato finché non si aprono i voti** (kickoff + 1h); prima mostra un lucchetto (helper `statsOpen()`).
- **Chiudere la giornata adesso** (`status='closed'`, salva `closed_at`): da qui i punti entrano in classifica e scattano le frecce di posizione per 24h.
- **Resettare la giornata** (rpc: cancella la giornata e TUTTI i figli — formazioni, voti, nomination, stat, presenze; non avanza il numero).

**Chi può votare.** Di default vota **solo chi ha giocato** quella giornata (un suo personaggio è tra i presenti). I "solo-manager" non votano, a meno che l'admin li abiliti da Impostazioni → "Voto ai soli-manager" (tabella `extra_voters`). L'admin può sempre votare. Il blocco è lato app (slider/MVP disattivati + guardia su `onVote`/`onNominate`).

Le **formazioni avversarie** sono nascoste finché la partita non inizia (kickoff o status closed); la propria è sempre visibile; le giornate passate sono sempre visibili (storico). Nel selettore Lega le giornate **non ancora iniziate** non compaiono (per non sbirciarne i punti/modulo).

---

## 8. Funzionalità (e dove stanno nell'UI)

Barra in basso (5 voci): **Home · Mercato · Campo (centrale, evidenziato) · Voti · Lega**.

- **Home**: hero "Pronto a schierare?", poi **Classifica** (mini), poi **Regolamento**.
- **Mercato**: card giocatori con avatar intero (`object-fit:contain`), ruolo accanto al nome, **stato di forma** (▲ In forma / ▼ In calo / ■ Costante), prezzo. Badge **👑 Capocannoniere** sul/i top scorer; badge **🚑 Infortunato** (avatar in grigio) se infortunato. Etichetta **"Tu"** solo sul proprio personaggio iniziale. Tap sulla card → **finestrella stats** (Presenze, Gol, Assist, Voto medio; default 0/0/0/6).
- **Campo**: schieramento 5 slot, scelta capitano, doppio countdown (blocco formazioni / chiusura voti).
- **Voti**: ognuno vota i presenti 1-10 e nomina MVP e SEGA; medie live dal DB; (admin) sezione bonus/malus.
- **Lega**: tendina con **Classifica generale** (punti stagione), **Classifica marcatori** (capocannoniere in cima), e **ogni giornata** (punti di giornata, tap su squadra → formazione di quella giornata).

Extra UX: pulsante **Campo** centrale evidenziato e contenuto nella barra; **feedback al tocco** (micro-animazione + vibrazione leggera dove supportata); fix PWA iOS che riapriva la pagina a metà (ora apre sempre in cima).

---

## 9. Funzioni / RPC su Supabase

Già presenti nel DB (definite in sessioni precedenti — qui solo firma e scopo):

- `is_admin()` → bool. Helper usato nelle policy RLS.
- `get_averages(md bigint)` → media voti per player nella giornata.
- `get_mvp_sega(md bigint)` → id MVP (e SEGA, ormai ignorato lato app).
- `reset_matchday(md bigint)` → cancella giornata + TUTTI i figli (formazioni/voti/nomination/stat/presenze). DDL aggiornata in §18.

Aggiunte/aggiornate nelle sessioni recenti (DDL completa in §10 e soprattutto **§18**):

- `get_standings()` → classifica stagionale **solo giornate `closed`** + `delta` (variazione posizione, attiva 24h dopo l'ultima chiusura). **Firma cambiata** (aggiunta colonna `delta int`).
- `get_standings_md(md bigint)` → classifica della singola giornata (assist×2, esito, moltiplicatore solo-voto, bonus modulo, niente SEGA).
- `get_player_stats()` → presenze (solo da blocco formazioni), gol, assist, voto_medio, forma.
- `list_solo_managers()` → (admin) elenco profili solo-manager con flag voto, per la card "Voto ai soli-manager".
- `get_poll_results()` → (admin) medie del sondaggio valori.

---

## 10. SQL aggiuntivo (eseguito di recente — riferimento)

> ⚠️ `get_standings_md` e `get_player_stats` qui sotto sono la versione **vecchia**: le versioni correnti (assist×2, esito, moltiplicatore solo-voto, bonus modulo, presenze dal blocco formazioni) sono in **§18**. Le tengo qui per storico.

```sql
-- modalità solo-manager
alter table profiles add column if not exists is_player boolean default true;

-- infortuni
alter table players add column if not exists injured boolean default false;

-- formazioni leggibili da tutti (la visibilità "prima del kickoff" è gestita lato client)
drop policy if exists "lineups read" on lineups;
create policy "lineups read" on lineups for select using (true);

-- presenze per giornata
create table if not exists matchday_players(
  matchday_id bigint not null,
  player_id bigint not null,
  primary key (matchday_id, player_id)
);
alter table matchday_players enable row level security;
drop policy if exists "mp read" on matchday_players;
create policy "mp read" on matchday_players for select using (true);
drop policy if exists "mp write" on matchday_players;
create policy "mp write" on matchday_players for all using (is_admin()) with check (is_admin());

-- classifica di singola giornata
create or replace function get_standings_md(md bigint)
returns table(manager_id uuid, team_name text, player_name text, points numeric)
language sql security definer stable set search_path = public as $$
  with av as (select player_id, avg(score)::numeric as v from votes where matchday_id=md group by player_id),
  mv as (select mvp_player_id as pid from nominations where matchday_id=md and mvp_player_id is not null group by mvp_player_id order by count(*) desc, mvp_player_id limit 1),
  sg as (select sega_player_id as pid from nominations where matchday_id=md and sega_player_id is not null group by sega_player_id order by count(*) desc, sega_player_id limit 1),
  scored as (
    select l.manager_id,
      ( case when (exists(select 1 from sg) and (select pid from sg)=l.player_id) then 0
        else ( coalesce(av.v,6) + coalesce(ms.gol,0)*3 + coalesce(ms.assist,0)*1 - coalesce(ms.autogol,0)*3
          + case when l.slot='g1' then (case when coalesce(ms.gol_subiti,0)=0 then 3 else -coalesce(ms.gol_subiti,0) end) else 0 end )
          * (case when (exists(select 1 from mv) and (select pid from mv)=l.player_id) then 2 else 1 end)
          * (case when l.is_captain then 2 else 1 end)
      end ) as pts
    from lineups l
    left join av on av.player_id=l.player_id
    left join match_stats ms on ms.matchday_id=l.matchday_id and ms.player_id=l.player_id
    where l.matchday_id=md )
  select p.id, p.team_name, p.player_name, coalesce(round(sum(s.pts)::numeric,1),0)
  from profiles p left join scored s on s.manager_id=p.id
  group by p.id, p.team_name, p.player_name order by 4 desc, p.team_name;
$$;

-- statistiche giocatore + forma
create or replace function get_player_stats()
returns table(player_id bigint, presences int, gol int, assist int, voto_medio numeric, forma text)
language sql security definer stable set search_path=public as $$
  with pres as (select player_id, count(*)::int n from matchday_players group by player_id),
  st as (select player_id, coalesce(sum(gol),0)::int gol, coalesce(sum(assist),0)::int assist from match_stats group by player_id),
  vall as (select player_id, avg(score)::numeric vm from votes group by player_id),
  vmd as (select player_id, matchday_id, avg(score)::numeric v from votes group by player_id, matchday_id),
  ranked as (select player_id, matchday_id, v, row_number() over (partition by player_id order by matchday_id desc) rn from vmd),
  forma as (
    select r1.player_id,
      case when r2.v is null then 'Costante'
           when r1.v > r2.v then 'In forma'
           when r1.v < r2.v then 'In calo'
           else 'Costante' end ftxt
    from ranked r1 left join ranked r2 on r2.player_id=r1.player_id and r2.rn=2
    where r1.rn=1)
  select p.id, coalesce(pres.n,0), coalesce(st.gol,0), coalesce(st.assist,0),
         round(coalesce(vall.vm,6),2), coalesce(forma.ftxt,'Costante')
  from players p
  left join pres on pres.player_id=p.id
  left join st on st.player_id=p.id
  left join vall on vall.player_id=p.id
  left join forma on forma.player_id=p.id
  order by p.id;
$$;
```

Inoltre, per liste avatar serve la policy di SELECT sullo storage:

```sql
create policy "avatars public list" on storage.objects for select to public using (bucket_id='avatars');
```

---

## 11. Auth & email

- **Login** con **Email OTP**: si invia un codice a 6 cifre (`signInWithOtp`) e si verifica con `verifyOtp({type:'email'})`. Si è passati dal magic-link al codice perché il magic-link si rompeva nella PWA iOS (storage separato in standalone).
- I template email **"Magic Link"** e **"Confirm signup"** mostrano entrambi `{{ .Token }}` (Confirm signup = nuovi utenti, Magic Link = utenti esistenti).
- **Invio email**: SMTP custom = **Resend** (`smtp.resend.com:587`, user `resend`, password = API key `re_...`). Mittente `accesso@fantacalcettoitalia.it`. Dominio `fantacalcettoitalia.it` verificato su Resend con DKIM/SPF/MX impostati su Aruba.
- L'utente è admin: `update profiles set is_admin=true where id='<UID>';`
- Constraint stato giornata già allargato: `status in ('open','voting','locked','closed')`.

---

## 12. Come deve agire l'assistente in una nuova chat

- **Lingua: italiano.** Tono semplice e operativo, passi guidati uno alla volta (utente su iPhone, non dev).
- Tutto vive in **un unico `index.html`**. Per modifiche: chiedere/recuperare l'ultima versione, applicare le modifiche, **validare i bracket**, ripresentare il file intero, ricordare di **re-incollare le chiavi** e dire chiaramente **se serve SQL** o **nuovi PNG**.
- Mantenere **coerenza punteggio** tra client (`computeScore`/`scoreOf`) e funzioni SQL (`get_standings`, `get_standings_md`).
- Non rompere l'auth: non toccare i record email su Aruba, non cambiare i nameserver, usare la publishable key.
- Le funzioni che fanno aggregati sui voti sono **security definer** (i voti restano anonimi: ognuno legge solo i propri, gli aggregati passano dalle funzioni).
- Prima di dichiarare "fatto", ricontrollare che le nuove feature siano riflesse in **tutti** i punti: caricamento dati, render, eventuali RLS/SQL, e refresh dopo le azioni.

---

## 13. Problemi noti / promemoria

- **Chiavi placeholder**: il file consegnato non contiene le chiavi vere → vanno reincollate a ogni upload del file intero.
- **Icona PWA**: cambia solo rimuovendo e ri-aggiungendo l'app alla home.
- **forma (campo legacy in `players`)**: non incide sui punti; lo "stato di forma" mostrato nel mercato è calcolato da `get_player_stats` (confronto media voti ultima vs penultima giornata).
- **Infortunio**: è solo uno stato visivo (🚑). Non blocca da solo lo schieramento; per escludere un infortunato basta non segnarlo presente in giornata. (Se richiesto, si può rendere automatico.)
- **Presenze**: contate da `matchday_players` (giornate in cui il giocatore era segnato presente).

---

## 14. Notifiche push (PWA)

Notifiche web push che arrivano **anche con l'app chiusa** (iOS 16.4+, solo se l'app è installata sulla home). Volutamente **poche**:

1. 📢 Apertura giornata (trigger: admin apre la giornata).
2. ⏰ Promemoria 1h prima della chiusura formazioni (trigger: **scheduler a tempo**, vedi sotto).
3. 🏁 Chiusura giornata (trigger: admin chiude la giornata).

**Pezzi coinvolti:**

- `sw.js` (service worker, nella root del repo accanto a `index.html`): riceve il push e gestisce il click.
- `index.html`: registra il SW, chiede il permesso con un prompt gentile **dopo l'onboarding** (e c'è un toggle in Impostazioni → Notifiche), salva la subscription in `push_subscriptions`, e chiama la Edge Function su apertura/chiusura giornata (`pushNotify`).
- Edge Function **`notify`** su Supabase (`notify.ts`): invia il push a tutte le subscription usando `web-push`. Può chiamarla **solo un admin** (verifica `profiles.is_admin`). Pulisce le subscription scadute (404/410).
- Chiavi **VAPID**: la pubblica è in `index.html` (`VAPID_PUBLIC`), la privata è un **secret** della Edge Function.

**SQL:**

```sql
create table if not exists push_subscriptions(
  endpoint text primary key,
  user_id uuid,
  sub jsonb not null,
  created_at timestamptz default now()
);
alter table push_subscriptions enable row level security;
drop policy if exists "ps own" on push_subscriptions;
create policy "ps own" on push_subscriptions for all using (auth.uid()=user_id) with check (auth.uid()=user_id);

-- promemoria a tempo
alter table matchdays add column if not exists reminder_sent boolean default false;

-- scheduler: ogni 10 min controlla se inviare il promemoria (1h prima della chiusura formazioni)
create extension if not exists pg_cron;
create extension if not exists pg_net;
select cron.schedule('fanta-reminder','*/10 * * * *', $$
  select net.http_post(
    url := 'https://<PROGETTO>.supabase.co/functions/v1/notify',
    headers := jsonb_build_object('Content-Type','application/json','x-cron-secret','<CRON_SECRET>'),
    body := jsonb_build_object('mode','reminder')
  );
$$);
```

**Logica promemoria** (dentro `notify.ts`, modalità `reminder`): trova le giornate `status='open'` con `reminder_sent=false`; per ognuna calcola chiusura formazioni = `kickoff − 1h` e invia il promemoria quando `now` è tra `(chiusura − 1h)` e `chiusura`, poi imposta `reminder_sent=true` (una sola volta).

**Setup una-tantum (dashboard Supabase):**

1. Esegui l'SQL qui sopra (sostituisci `<PROGETTO>` e `<CRON_SECRET>`).
2. Edge Functions → Create function → nome `notify` → incolla `notify.ts` → Deploy.
3. Nei Secrets della function imposta `VAPID_PUBLIC`, `VAPID_PRIVATE` e `CRON_SECRET` (tutte annotate in cima a `notify.ts`). `SUPABASE_URL`/`SUPABASE_ANON_KEY`/`SUPABASE_SERVICE_ROLE_KEY` ci sono già.
4. Carica `sw.js` + `index.html` aggiornato su GitHub.
5. Ogni utente attiva le notifiche dal prompt o da Impostazioni; l'app dev'essere installata sulla home (iOS).

**Chiavi VAPID di questo progetto:** la pubblica è in `index.html`; la privata va nel secret (è annotata in cima a `notify.ts`). Se le rigeneri, aggiornale in entrambi i posti.

---

## 15. Crediti per giocatore, sondaggio, auto-update

**Crediti per giocatore.** Ogni giocatore ha un costo in crediti (`players.cost`, default 20). L'admin lo imposta/modifica dalla scheda del giocatore (Impostazioni → Gestione giocatori → ✏️ → campo "Crediti"). Il budget per giornata resta 100 e si schierano sempre 5 giocatori, ma ora la somma dei costi dei 5 deve stare entro 100: il selettore mostra i costi, disabilita chi non ci si può permettere, e il pulsante "Conferma" si blocca se si sfora. Client: `costOf(pid)`, `lineupSpent()`, budget in `updateBudget`. SQL:

```sql
alter table players add column if not exists cost int default 20;
```

**Sondaggio valori** (`sondaggio.html`). Pagina separata, da hostare su Vercel (es. `fantacalcettoitalia.it/sondaggio.html`) e mandare al gruppo. Ognuno vota i giocatori 1–10. **Privacy:** chiunque ha il link può **solo votare**; i voti NON sono leggibili da nessuno (RLS senza policy dirette), e i **risultati (medie) li vede solo l'admin dentro l'app** (Impostazioni → Risultati sondaggio valori), via funzione `get_poll_results()` che controlla `is_admin()`. Voto e recupero del proprio voto passano da funzioni `security definer`. SQL:

```sql
create table if not exists credit_poll(
  voter text primary key,
  ratings jsonb not null,
  created_at timestamptz default now()
);
alter table credit_poll enable row level security;
-- nessun accesso diretto: solo tramite funzioni
drop policy if exists "poll read" on credit_poll;
drop policy if exists "poll insert" on credit_poll;
drop policy if exists "poll update" on credit_poll;

create or replace function submit_poll(p_voter text, p_ratings jsonb)
returns void language sql security definer set search_path=public as $$
  insert into credit_poll(voter, ratings) values (p_voter, p_ratings)
  on conflict (voter) do update set ratings=excluded.ratings, created_at=now();
$$;

create or replace function get_my_poll(p_voter text)
returns jsonb language sql security definer stable set search_path=public as $$
  select ratings from credit_poll where voter = p_voter;
$$;

create or replace function get_poll_results()
returns table(player text, avg numeric, n int)
language plpgsql security definer stable set search_path=public as $$
begin
  if not is_admin() then raise exception 'forbidden'; end if;
  return query
  select key as player, round(avg(value::numeric),2) as avg, count(*)::int as n
  from credit_poll, jsonb_each_text(ratings)
  group by key order by 2 desc;
end; $$;
```

La lista dei 16 giocatori è hardcodata nel file; per aggiungerne, l'admin li crea direttamente nell'app (non serve il sondaggio).

**Auto-update PWA.** L'app non fa caching dell'HTML (il service worker gestisce solo le push), quindi prende la nuova versione al riavvio. In più, al rientro nell'app (focus/visibilitychange) confronta il file servito da Vercel con quello caricato e, se è cambiato, fa `location.reload()`. Risultato: dopo un deploy gli utenti si aggiornano da soli, senza togliere/rimettere l'app dalla home.

---

## 16. RLS tabella `players` (listone visibile a tutti)

La tabella `players` è il listone condiviso: **tutti** devono vederlo. In una sessione passata le policy erano rimaste troppo restrittive (ognuno vedeva solo i giocatori creati da sé → i giocatori creati da altri utenti non comparivano nel mercato). Regole corrette: lettura per tutti gli autenticati; inserimento/modifica per admin o per il proprietario del proprio record; cancellazione solo admin.

```sql
-- pulisci tutte le policy esistenti su players, poi rimetti quelle giuste
do $$
declare r record;
begin
  for r in select polname from pg_policy where polrelid='public.players'::regclass loop
    execute format('drop policy if exists %I on public.players', r.polname);
  end loop;
end $$;

alter table players enable row level security;

create policy "players_select" on players
  for select to authenticated using (true);
create policy "players_insert" on players
  for insert to authenticated with check (is_admin() or owner_id = auth.uid());
create policy "players_update" on players
  for update to authenticated using (is_admin() or owner_id = auth.uid())
  with check (is_admin() or owner_id = auth.uid());
create policy "players_delete" on players
  for delete to authenticated using (is_admin());
```

Nota: l'insert del proprio giocatore in onboarding ora controlla l'errore e lo mostra (prima falliva in silenzio se le policy lo bloccavano).

**Proprietà dei giocatori (owner_id) — IMPORTANTE.** `owner_id` identifica SOLO il personaggio personale di un utente (quello creato al suo onboarding "in campo"). I giocatori creati dall'admin dalle Impostazioni sono giocatori del listone **senza proprietario** (`owner_id = null`). Motivo: il salvataggio Impostazioni sincronizza nome/avatar del proprio personaggio cercandolo per `owner_id = me`; se i giocatori creati da admin avessero `owner_id = admin`, verrebbero rinominati tutti col nome dell'admin (bug capitato). Ora il salvataggio Impostazioni è ristretto a `owner_id = me AND name = vecchio player_name` e i giocatori admin nascono con `owner_id = null`. Se restano in giro vecchi giocatori con `owner_id` dell'admin, ripulirli (dopo aver rimesso i nomi giusti) con: `update players set owner_id=null where owner_id='<ADMIN_UID>' and name <> '<NOME_PERSONAGGIO_ADMIN>';`

---

## 17. Fluidità tocco + Modalità manutenzione

**Fix tocco schieramento.** Gli slot in campo sono centrati con `transform:translate(-50%,-50%)`; l'animazione al tocco `.tapd{transform:scale(.95)}` sovrascriveva quel transform facendo "saltare" lo slot sotto il dito → il click al rilascio mancava il bersaglio (servivano più tap). Fix: `.slot.tapd{transform:translate(-50%,-50%) scale(.95)}` (mantiene il centraggio). Aggiunto anche `touch-action:manipulation` globale per togliere il ritardo di ~300ms e lo zoom da doppio-tap su iOS. Regola generale: ogni elemento posizionato con `transform` deve includere quel transform anche nella variante `.tapd`.

**Modalità manutenzione (admin).** L'admin può mettere l'app in stand-by per tutti gli altri (lui continua a usarla) da Impostazioni → card "Manutenzione" → "🛠️ Metti in manutenzione" / "🟢 Torna live". I non-admin vedono un overlay a schermo intero (⚙️ "Manutenzione in corso…"); l'admin vede un banner rosso in alto come promemoria. Stato condiviso su Supabase (tabella `app_state`, singola riga id=1) + realtime: appena l'admin cambia, gli altri vengono messi/tolti dallo stand-by senza ricaricare. Bypass admin via `profile.is_admin`. SQL:

```sql
create table if not exists app_state(
  id int primary key,
  maintenance boolean not null default false
);
insert into app_state(id, maintenance) values (1, false) on conflict (id) do nothing;
alter table app_state enable row level security;
drop policy if exists "app_state read" on app_state;
create policy "app_state read" on app_state for select using (true);
drop policy if exists "app_state write" on app_state;
create policy "app_state write" on app_state for update using (is_admin()) with check (is_admin());
```

Inoltre, in Realtime, assicurarsi che la tabella `app_state` sia abilitata alla replica (Database → Replication / Publications) se gli aggiornamenti live non arrivano.

**Ordinamento mercato/selettore.** Card ordinate per crediti decrescenti (più costoso → meno) sia nel Mercato sia nel selettore di schieramento.

---

## 18. Aggiornamenti recenti — moduli, voti condizionati, generatore, classifica a giornate chiuse

Questa sezione raccoglie le modifiche più recenti (hanno precedenza su §6/§10 dove differiscono). Tutte già applicate nel file `index.html`.

### 18.1 Punteggio (riepilogo)

- **Assist = +2** (prima +1).
- **Risultato squadra reale**: +1 se la sua squadra di calcetto vince, −1 se perde (`match_stats.esito` = `V`/`S`/null). *(Cambiato da ±2 a ±1.)* Ora si imposta dal **pannello partita live** (vedi §21), step "Chi ha vinto?".
- **Capitano e MVP raddoppiano SOLO il voto**, non i bonus. Cumulabili (×4 sul voto). Funzione client: `scoreOf` → `voto*mult + bonus`.
- **SEGA rimossa** ovunque (UI, calcolo, hint). `nominations.sega_player_id` resta come colonna legacy, sempre null.
- **Moduli** con bonus di partenza: 1-2-2 (0), 1-3-1 (+5), 1-1-3 (−5). Client: `MODULES`, `formModule`, `SLOTS`, `moduleBonus()`, `setModule()`, salvataggio in `lineup_modules`.

### 18.2 Voti condizionati

- Vota solo chi ha giocato (suo personaggio presente) + admin + manager abilitati in `extra_voters`. Client: `canIVote()`, `loadCanVote()`.

### 18.3 Bonus/malus bloccati

- Il pannello admin bonus/malus si apre solo da kickoff + 1h (`statsOpen()`), bloccato anche su `admSet`/`setEsito`.

### 18.4 Presenze

- Conteggiate solo da blocco formazioni (kickoff − 1h) o se `closed`; reset le rimuove.

### 18.5 Classifica a giornate chiuse + frecce

- `get_standings()` somma solo le giornate `closed`; restituisce anche `delta` (variazione posizione) attivo 24h dopo l'ultima chiusura e solo dalla 2ª giornata chiusa. Client: `moveArrow()`, frecce ▲ verde / ▼ rossa in `renderMini`/`renderLB`. Il selettore Lega nasconde le giornate non ancora iniziate.

### 18.6 Generatore squadre + valore

- `players.valore` (numerico, admin-only). Generatore (admin): `tmGenerate/tmMove/renderTeamMaker`, forza = `valore` → media sondaggio (con alias `POLL_ALIAS`) → 5.5.

### SQL completo da eseguire (idempotente)

```sql
-- colonne nuove
alter table match_stats add column if not exists esito text;             -- V / S / null
alter table players     add column if not exists valore numeric;          -- forza 1-10 (admin)
alter table matchdays   add column if not exists closed_at timestamptz;   -- istante chiusura

-- slot ampliati per i moduli (1-3-1 usa d3, 1-1-3 usa a3)
alter table lineups drop constraint if exists lineups_slot_check;
alter table lineups add constraint lineups_slot_check
  check (slot in ('a1','a2','a3','d1','d2','d3','g1'));

-- modulo per giornata/manager
create table if not exists lineup_modules(
  matchday_id bigint not null,
  manager_id  uuid   not null,
  module      text   not null default '1-2-2',
  primary key (matchday_id, manager_id)
);
alter table lineup_modules enable row level security;
drop policy if exists lm_read  on lineup_modules;
create policy lm_read  on lineup_modules for select using (true);
drop policy if exists lm_write on lineup_modules;
create policy lm_write on lineup_modules for all
  using (manager_id = auth.uid()) with check (manager_id = auth.uid());

-- manager-solo abilitati al voto
create table if not exists extra_voters(profile_id uuid primary key);
alter table extra_voters enable row level security;
drop policy if exists ev_read  on extra_voters;
create policy ev_read  on extra_voters for select using (true);
drop policy if exists ev_write on extra_voters;
create policy ev_write on extra_voters for all using (is_admin()) with check (is_admin());

create or replace function list_solo_managers()
returns table(id uuid, team_name text, player_name text, can_vote bool)
language plpgsql security definer stable set search_path=public as $$
begin
  if not is_admin() then raise exception 'forbidden'; end if;
  return query
  select p.id, p.team_name, p.player_name,
         exists(select 1 from extra_voters e where e.profile_id=p.id)
  from profiles p
  where coalesce(p.is_player,true)=false
  order by p.team_name;
end $$;

-- classifica di giornata: voto×mult (solo voto) + bonus + esito + bonus modulo, niente SEGA
create or replace function get_standings_md(md bigint)
returns table(manager_id uuid, team_name text, player_name text, points numeric)
language sql security definer stable set search_path = public as $$
  with av as (select player_id, avg(score)::numeric as v from votes where matchday_id=md group by player_id),
  mv as (select mvp_player_id as pid from nominations where matchday_id=md and mvp_player_id is not null group by mvp_player_id order by count(*) desc, mvp_player_id limit 1),
  scored as (
    select l.manager_id,
      ( coalesce(av.v,6)
          * (case when (exists(select 1 from mv) and (select pid from mv)=l.player_id) then 2 else 1 end)
          * (case when l.is_captain then 2 else 1 end)
        + coalesce(ms.gol,0)*3 + coalesce(ms.assist,0)*2 - coalesce(ms.autogol,0)*3
        + case when l.slot='g1' then (case when coalesce(ms.gol_subiti,0)=0 then 3 else -coalesce(ms.gol_subiti,0) end) else 0 end
        + case when ms.esito='V' then 2 when ms.esito='S' then -2 else 0 end
      ) as pts
    from lineups l
    left join av on av.player_id=l.player_id
    left join match_stats ms on ms.matchday_id=l.matchday_id and ms.player_id=l.player_id
    where l.matchday_id=md ),
  mods as (
    select manager_id, case module when '1-3-1' then 5 when '1-1-3' then -5 else 0 end as m
    from lineup_modules where matchday_id=md )
  select p.id, p.team_name, p.player_name,
    coalesce(round(sum(s.pts)::numeric,1),0)
    + (case when count(s.manager_id)>0 then coalesce(max(mo.m),0) else 0 end) as points
  from profiles p
  left join scored s on s.manager_id=p.id
  left join mods   mo on mo.manager_id=p.id
  group by p.id, p.team_name, p.player_name
  order by points desc, p.team_name;
$$;

-- presenza solo da blocco formazioni (kickoff - 1h) o se chiusa
create or replace function get_player_stats()
returns table(player_id bigint, presences int, gol int, assist int, voto_medio numeric, forma text)
language sql security definer stable set search_path=public as $$
  with pres as (
    select mp.player_id, count(*)::int n
    from matchday_players mp
    join matchdays m on m.id=mp.matchday_id
    where m.kickoff is not null
      and ((m.kickoff - interval '1 hour') <= now() or m.status='closed')
    group by mp.player_id),
  st as (select player_id, coalesce(sum(gol),0)::int gol, coalesce(sum(assist),0)::int assist from match_stats group by player_id),
  vall as (select player_id, avg(score)::numeric vm from votes group by player_id),
  vmd as (select player_id, matchday_id, avg(score)::numeric v from votes group by player_id, matchday_id),
  ranked as (select player_id, matchday_id, v, row_number() over (partition by player_id order by matchday_id desc) rn from vmd),
  forma as (
    select r1.player_id,
      case when r2.v is null then 'Costante'
           when r1.v > r2.v then 'In forma'
           when r1.v < r2.v then 'In calo'
           else 'Costante' end ftxt
    from ranked r1 left join ranked r2 on r2.player_id=r1.player_id and r2.rn=2
    where r1.rn=1)
  select p.id, coalesce(pres.n,0), coalesce(st.gol,0), coalesce(st.assist,0),
         round(coalesce(vall.vm,6),2), coalesce(forma.ftxt,'Costante')
  from players p
  left join pres on pres.player_id=p.id
  left join st on st.player_id=p.id
  left join vall on vall.player_id=p.id
  left join forma on forma.player_id=p.id
  order by p.id;
$$;

-- reset: cancella la giornata e tutti i figli (presenze incluse)
create or replace function reset_matchday(md bigint)
returns void language sql security definer set search_path=public as $$
  delete from lineups where matchday_id=md;
  delete from votes where matchday_id=md;
  delete from nominations where matchday_id=md;
  delete from match_stats where matchday_id=md;
  delete from matchday_players where matchday_id=md;
  delete from matchdays where id=md;
$$;

-- classifica stagionale: SOLO giornate chiuse + delta posizione (frecce 24h)
drop function if exists get_standings();
create function get_standings()
returns table(manager_id uuid, team_name text, player_name text, points numeric, delta int)
language sql security definer stable set search_path=public as $$
  with closed as (select id, closed_at from matchdays where status='closed'),
  last_md as (select id, closed_at from closed order by closed_at desc nulls last, id desc limit 1),
  cur as (select gs.manager_id, sum(gs.points) pts from closed c, lateral get_standings_md(c.id) gs group by gs.manager_id),
  prev as (select gs.manager_id, sum(gs.points) pts from closed c, lateral get_standings_md(c.id) gs where c.id <> (select id from last_md) group by gs.manager_id),
  cur_rank as (select p.id manager_id, rank() over (order by coalesce(cur.pts,0) desc) r from profiles p left join cur on cur.manager_id=p.id),
  prev_rank as (select p.id manager_id, rank() over (order by coalesce(prev.pts,0) desc) r from profiles p left join prev on prev.manager_id=p.id),
  show_arrows as (select (select count(*) from closed) >= 2
       and (select closed_at from last_md) is not null
       and (select closed_at from last_md) > now() - interval '24 hours' as ok)
  select p.id, p.team_name, p.player_name,
    coalesce(round(cur.pts::numeric,1),0) as points,
    case when (select ok from show_arrows) then (prev_rank.r - cur_rank.r) else 0 end as delta
  from profiles p
  left join cur on cur.manager_id=p.id
  left join cur_rank on cur_rank.manager_id=p.id
  left join prev_rank on prev_rank.manager_id=p.id
  order by points desc, p.team_name;
$$;

-- pulizia una-tantum presenze fantasma (eseguita una volta): azzera i presenti di giornate non aperte
-- delete from matchday_players where matchday_id in (select id from matchdays where status <> 'open');
```

### Promemoria handoff (aggiornato)

- **Coerenza punteggio**: client `scoreOf` ⇄ SQL `get_standings_md`. La stagionale `get_standings` somma le sole giornate chiuse, quindi cambia il punteggio in **un solo posto** (`get_standings_md`).
- **Drag&drop squadre**: su iPhone è "tap-to-move" (il drag nativo iOS è inaffidabile).
- **Blocco voto**: lato app; se serve a prova di manomissione, aggiungere una policy RLS su `votes` (non ancora fatta).

---

## 19. Aggiornamenti recenti — campo, icone, crediti dinamici, logo

Tutto già applicato in `index.html`. Precede §6/§18 dove differisce.

### 19.1 Input a "rotella" (select)

- I **voti** dei giocatori e i **bonus/malus** admin (gol/assist/autogol/gol presi) usano `<select>` (su iPhone = rotella che scorre), non più slider/casella di testo. Classi CSS `.votesel` / `.admsel`. Voti 1–10, bonus 0–10.

### 19.2 Medie nascoste agli utenti

- La **media voto** e il **numero di voti** li vede SOLO l'admin: nella sezione Voti (i non-admin vedono il ruolo), nell'aggiornamento live (`refreshAvgLabels` esce subito se non admin) e nella finestrella stats del Mercato (il box "Voto medio" non viene reso ai non-admin).
- **Sul proprio campo** invece ogni utente vede il **voto medio (bonus esclusi)** dei propri 5 giocatori schierati, con i simboli evento.

### 19.3 Icone evento sul campo

- `statIcons(r)`: ⚽×gol · 🅰️×assist · 💀×autogol · 🧤 se portiere imbattuto / 🔴×gol subiti. Ripetute per quantità. Usate sia sul proprio campo sia nelle formazioni altrui.

### 19.4 Formazione altrui = campo + swipe

- In Lega → giornata → tap su una squadra: si apre la **formazione sul campo** (modulo + voti medi + simboli) e **scorrendo orizzontalmente** si vede il secondo pannello con la **lista dei punti totali (bonus inclusi)** per giocatore + totale squadra. Funzioni: `pitchSlotsHTML(mod,getp)` (mostra il voto medio), `PITCH_MARKS`, contenitore `.tl-swipe`/`.tl-slide`.

### 19.5 Crediti dinamici (±1 a giornata)

- Alla **chiusura** di una giornata, ogni giocatore può variare di **±1 credito**: +1 se il voto medio (bonus esclusi) è ≥ +0,5 rispetto alla giornata precedente, −1 se ≤ −0,5, altrimenti invariato. Min 1, max 100. Applicato una sola volta per giornata (`matchdays.cost_applied`). Client: `closeMatchday` chiama `apply_credit_changes(md)` poi `loadPlayers()`.

### 19.6 Logo

- Nuovo logo immagine al posto del pallino ⚽: i tre `.dot` del brand usano `<img src="icon-512.png">`. Le icone PWA (`icon-180/512/1024.png`) sono rigenerate dall'immagine. Il logo **dentro** l'app si aggiorna da solo (auto-update); l'**icona in Home** su iOS richiede rimuovi+ri-aggiungi (limite Apple), su Android si aggiorna da sola col tempo.

### 19.7 Valore con mezzi punti

- Il campo Valore (admin) accetta i mezzi punti (step 0,5), es. 6.5 / 7.5.

### 19.8 Avviso temporaneo "nuovo logo"

- Blocco autonomo in fondo allo script (`maybeShowLogoNotice`): popup una-tantum per dispositivo (flag `localStorage fc_logo_notice_v1`) che invita a rimuovere/ri-aggiungere l'app per la nuova icona. **Si auto-disattiva dopo il 2026-07-15** ed è pensato per essere rimosso in un deploy futuro (cancellare il blocco + la chiamata in `afterLogin`).

### SQL da eseguire

```sql
-- crediti dinamici
alter table matchdays add column if not exists cost_applied boolean default false;

create or replace function apply_credit_changes(md bigint)
returns void language plpgsql security definer set search_path=public as $$
declare prev bigint; already bool;
begin
  if not is_admin() then raise exception 'forbidden'; end if;
  select cost_applied into already from matchdays where id=md;
  if already then return; end if;
  select id into prev from matchdays where id < md order by id desc limit 1;
  update players p
  set cost = greatest(1, least(100, p.cost + d.delta))
  from (
    select cur.player_id,
      case when (cur.v - coalesce(prv.v, cur.v)) >=  0.5 then  1
           when (cur.v - coalesce(prv.v, cur.v)) <= -0.5 then -1
           else 0 end as delta
    from (select player_id, avg(score)::numeric v from votes where matchday_id=md   group by player_id) cur
    left join (select player_id, avg(score)::numeric v from votes where matchday_id=prev group by player_id) prv
      on prv.player_id=cur.player_id
  ) d
  where d.player_id=p.id and d.delta<>0;
  update matchdays set cost_applied=true where id=md;
end $$;
```

### Nota coerenza

- Sul campo si mostra il **voto medio** (bonus esclusi); i **punti** (con bonus) restano in `scoreOf`/`get_standings_md` e nel pannello "punti totali" della formazione altrui e nella classifica.

---

## 20. Voti: mezzi voti + invio manuale

Applicato in `index.html`.

- **Mezzi voti**: si vota da 1 a 10 anche con la mezza cifra (es. 7.5). Input = **tastierino numerico** (`<input type="text" inputmode="decimal">`, classe `.voteinp`) → esce solo la tastiera con numeri e virgola. `parseVote()` arrotonda al **mezzo voto** più vicino e blocca tra 1 e 10 (7.2→7, 7.7→7.5/8); `fmtVote()` formatta (7 / 7.5). I bonus admin restano su `<select>` 0–10.
- **Invio manuale**: i voti **non si salvano da soli**. C'è un tasto **"Invia voti"** in alto nella card Voti (`#submitVotesBtn`, accanto al titolo). `onVote()` aggiorna solo lo stato locale (`myVotes`) + `voteDirty`; `submitVotes()` fa l'upsert di **tutti** i presenti (i non toccati restano 6 di default) e poi ricarica le medie. Il tasto "pulsa" quando ci sono modifiche non salvate (`.vsend.dirty`).

### SQL da eseguire

```sql
-- i voti ora possono avere la mezza cifra
alter table votes alter column score type numeric using score::numeric;
```

### Collegare una card a un utente (fix "non riesco a votare")

Se un giocatore è stato creato dall'admin, la sua card nasce con `owner_id` NULL e lui non può votare (il voto richiede un personaggio collegato `owner_id = suo account` e presente). Fix dati (no codice):

```sql
-- esempio per "Previ": rendi giocatore, collega la card, mettilo presente
update profiles set is_player=true
 where id=(select id from profiles where player_name ilike '%previ%' or team_name ilike '%previ%' order by id limit 1);
update players set owner_id=(select id from profiles where player_name ilike '%previ%' or team_name ilike '%previ%' order by id limit 1),
                   name=(select player_name from profiles where player_name ilike '%previ%' or team_name ilike '%previ%' order by id limit 1)
 where id=(select id from players where name ilike '%previ%' order by (owner_id is null) desc, id limit 1);
insert into matchday_players(matchday_id,player_id)
 select m.id,p.id from matchdays m join players p on p.owner_id=(select id from profiles where player_name ilike '%previ%' order by id limit 1)
 where m.status='open' on conflict do nothing;
```

Operazioni sicure: gli id numerici legano voti/formazioni/bonus, quindi rinominare o ri-collegare una card non stacca nulla di già inserito.

---

## 21. Aggiornamenti più recenti (sessione corrente) — pannello live, auto-chiusura, nuovi crediti, notifiche, LEGHE

> **Nota di precedenza:** dove questa sezione è in conflitto con quelle precedenti, **vale questa**. Le sezioni 1–20 restano valide per tutto il resto.

### 21.1 Risultato squadra reale: ±1 (non più ±2)

`match_stats.esito` `V`/`S`/null → **+1 / −1 / 0**. Allineato in `scoreOf` (client), `get_standings_md` (SQL) e Regolamento in Home. Se si ritocca il punteggio, tenere i tre punti coerenti.

### 21.2 Bonus/malus = Pannello partita LIVE

Sparita la tendina per-giocatore nella sezione Voti. Ora in **Impostazioni (admin)** c'è **"📊 Apri pannello partita"** (`#liveOpenBtn`) che apre un overlay a tutto schermo (`#liveStats`):

- Blocchi grandi **GOL / ASSIST / PORTIERE** + riquadro **AUTOGOL**. **Tap sul giocatore = +1** (vibrazione), **"−"** per annullare. Mostra solo i presenti (`livePlayers()`).
- La spunta live è in `adminStats` e viene salvata come **bozza in `localStorage`** (`fc_live_<mdId>`): se chiudi l'app, al riapri la ritrovi.
- Ultimo step **"🏈 Chi ha vinto?"**: tocchi i **vincitori** (verde, +1); i presenti non scelti = sconfitti (−1); nessuno scelto = pareggio (0). Deriva `esito` per tutti i presenti.
- **"Conferma e salva"** fa l'upsert di tutto in `match_stats`.
- Finestra di apertura: da **kickoff − 30 min** finché la giornata non è chiusa (`matchWindow()` / `matchOpenable()`).
- Funzioni: `LS()`, `livePlayers()`, `renderLive()`, `liveAdd()`, `liveToggleWin()`, `recomputeEsito()`, `liveConfirmSave()`, `saveLiveDraft/loadLiveDraft/clearLiveDraft`, `renderLiveOpenBtn()`.

### 21.3 Auto-chiusura lato server (indipendente dall'admin)

Funzione SQL **`close_due_matchdays()`** (service_role): chiude **tutte le leghe** con `now() >= kickoff + 25h`, applica i crediti e restituisce `(closed_id, closed_label, closed_league)`. Viene chiamata da **`notify.ts`** col cron pg_cron esistente (ogni 10 min), che poi invia la push "chiusa" alla lega giusta. La chiusura manuale dell'admin resta possibile. Alla chiusura `clearRoundLocal()` svuota formazione/capitano/modulo/voti/MVP/medie.

### 21.4 Crediti alla chiusura: nuovo metodo a RANKING

Non più "±1 se il voto medio varia di ±0,5". Ora, sui **soli presenti** (`_apply_credits_core(md)`):

1. **rank-credito**: per `cost` decrescente (parità = media dei ranghi).
2. **rank-punti**: per `voto + 0.5*(gol*3 + assist*2 − autogol*3 − gol_subiti)` — voto = media (6 di default), **senza** clean-sheet, esito, MVP, capitano, modulo.
3. **scarto** = rank-credito − rank-punti.
4. Ordina per scarto desc (parità = `cost` asc): **top 3 → +2/+1/+1**, **bottom 3 → −2/−1/−1**, gli altri invariati. Clamp **1..100**.
5. `players.trend` (1/−1/0) guida la **forma** (In forma / In calo / Costante) in `get_player_stats`.

`apply_credit_changes(md)` (admin) è il wrapper che chiama il core.

### 21.5 Presenze: all'apertura nessuno è presente

`createMatchday` non inserisce più tutti in `matchday_players`; parte con `mdPresent` **vuoto**. `presentId(id)` = `currentMd ? mdPresent.has(id) : false`. L'admin sceglie i presenti ogni giornata dalla card "Chi gioca questa giornata".

### 21.6 Notifiche: self-heal + invito alla prima apertura + per-lega

- `ensurePush()` ricrea in silenzio la subscription scaduta/persa a ogni apertura e su focus/visibilitychange.
- `maybeAskPush()` mostra il prompt gentile **solo alla prima apertura** (una volta per dispositivo, `localStorage fc_push_asked`).
- `notify.ts`: `sendAll(title, body, url, leagueId?)` invia **solo agli utenti della lega giusta** (immediato → lega dell'admin; reminder → `md.league_id`; auto-close → `closed_league`).

### 21.7 LEGHE (multi-tenant) — la grande aggiunta

L'app è diffondibile: **ogni gruppo = una lega privata**. Chi si registra **crea** una lega o **entra** in una con la password dell'admin.

**Migrazione del gruppo (zero perdite):** tutto il gruppo originale è confluito nella **lega #1 "La Fossa di Lissone"** (admin = Teo, password `SiamoLaPrima!`). Fatto con `league_id default 1` + backfill: per loro l'app è **identica**, salta la schermata lega, vede solo il badge `🏆` col nome in Home e Classifica.

**Isolamento (sicurezza):**

- Colonna `league_id` su tutte le tabelle dati; tabella **`leagues`** (`id, name, slug, password, admin_id`) con RLS **senza policy dirette** (accesso solo via funzioni `security definer`, così la password non è mai esposta).
- **Letture** filtrate da RLS con `league_id = my_league()`; **scritture** timbrate dal trigger `stamp_league` (`coalesce(my_league(),1)`).
- `is_admin` **derivato** dal trigger `profiles_guard`: sei admin solo se sei l'`admin_id` della tua lega; la lega non si cambia via update (anti-elevazione).
- Funzioni aggregate (`get_standings`, `get_standings_md`, `get_player_stats`, `list_solo_managers`, `get_poll_results`) filtrate per `my_league()`; `reset_matchday` con guardia admin+lega.

**Flusso nuovo utente:** login → schermata `#league` (Crea/Entra) → onboarding → **`onboard_join(lega, password, …)`** crea il profilo (e l'eventuale giocatore). *Crea*: `create_league` poi `onboard_join`. *Entra*: `verify_league` poi `onboard_join`. **Link d'invito** `?lega=slug` → `league_by_slug`. `onboard_join` controlla anche l'unicità di nome squadra/giocatore **dentro la lega** (errori `team_taken` / `player_taken` / `password errata`).

**Invito (admin):** Impostazioni → card **"Invita nella lega"** (`#inviteCard`) con link `?lega=slug` + password (tasti Copia), via `get_league_admin_info()` (password vista solo dall'admin di quella lega).

**Manutenzione:** ora **per-lega** (`app_state` una riga per lega; load/set per `league_id`).

**Funzioni nuove:** `my_league`, `slugify`, `create_league`, `find_leagues`, `league_by_slug`, `verify_league`, `onboard_join`, `get_my_league`, `get_league_admin_info`, `close_due_matchdays` (rivista).

**File SQL (già applicati):**

- `leghe_step1.sql` — fondamenta retro-compatibili (tabella leghe + lega 1, colonne `league_id` + backfill, trigger `stamp_league`/`profiles_guard`, RLS isolate, funzioni aggiornate, funzioni Crea/Entra). **Ordine importante:** le colonne `league_id` vanno create **prima** di `my_league()`; `close_due_matchdays` va **droppata** prima di ricrearla (cambia tipo di ritorno).
- `leghe_step2.sql` — `onboard_join` con unicità nomi + `get_league_admin_info`.

**Limiti noti:** un utente = una lega (no multi-lega per ora). Il **sondaggio** (`sondaggio.html`) resta di fatto sulla lega 1 finché non lo si rende multi-lega.

### 21.8 File toccati in questa sessione

- `index.html` — pannello partita live, "Chi ha vinto?", schermata lega + invito + badge nome, onboarding via `onboard_join`, manutenzione per-lega, notifiche self-heal/primo-invito, presenze deselezionate.
- `notify.ts` — auto-chiusura via `close_due_matchdays`, invii per-lega.
- `leghe_step1.sql`, `leghe_step2.sql` — sistema leghe.
- (Ricorda sempre: re-incollare le 2 chiavi Supabase a ogni upload di `index.html`.)

### 21.9 Sicurezza chiavi (nota)

Su GitHub vanno **solo** `index.html`, `sw.js`, le icone e `sondaggio.html`. **Mai** `notify.ts` né chiavi/secret: un repo pubblico rende la chiave "bruciata" anche se la rimuovi (resta nella cronologia e i bot la leggono in secondi) → va **ruotata**. Le chiavi VAPID e il `CRON_SECRET` stanno **solo** nei Secret della Edge Function `notify`. *(Il 2026-06-14 le chiavi sono state ruotate dopo un commit accidentale di `notify.ts` segnalato da GitGuardian: nuove VAPID + nuovo `CRON_SECRET` nel job pg_cron `fanta-reminder`. La `VAPID_PUBLIC` in `index.html` inizia con `BIVh1NLu...`.)*

---

## 22. Aggiornamenti recenti — config lega (apertura auto / portiere / presenze), impostazioni a pagine, banner notifiche, wizard creazione

Sessione di rifinitura UX + tre nuove regole di lega configurabili. **Tutta la config sta in nuove colonne su `leagues`**, letta da tutti gli utenti all'avvio via `get_league_schedule()` (nome storico: ora ritorna anche portiere/presenze) e scritta solo dall'admin via RPC dedicate.

### 22.1 Impostazioni a pagine (drill-in stile iOS)

Le Impostazioni non sono più una lista unica: ora sono **pagine navigabili**. Si entra in `#setMenu` (lista) con righe `.navrow` → **Profilo · Notifiche · Regolamento · 🔒 Area amministratore**; toccando una riga si entra nella sua `.setpage` (con `.subback` "‹ Indietro"). L'Area amministratore è un secondo livello: **⚽ Partita** (Modalità portiere, Presenze, Giornata) e **🏆 Lega** (Invita, Gestione giocatori, Risultati sondaggio, Voto soli-manager, Manutenzione). Funzione `setNav(id)` mostra una `.setpage` alla volta; la riga admin (`#adminRow`) appare solo all'admin (in `applyProfile`). Entrando da `go('settings')` si riparte sempre da `setMenu`.

### 22.2 Apertura giornata: automatica (ricorrente) o manuale

Nuova scelta admin in **Partita → Giornata** (`renderOpenMode`): **✋ Manuale** (come prima, apri tu con data/ora) o **🤖 Automatica**. In automatica scegli **giorno della settimana + ora**: la giornata si apre **da sola 48h prima** del fischio d'inizio, ricorrente ogni settimana. Calcolo lato server nel fuso **Europe/Rome**. Lo scheduler `notify.ts` (cron ogni 10 min) chiama `open_due_matchdays()` che apre e manda la push "aperta". Non al secondo esatto: entro ~10 min dallo scoccare delle 48h. Per una settimana diversa l'admin passa a Manuale e apre a mano (la programmazione resta salvata). Stato client: `leagueSched`/`schedDraft`; colonne `leagues.auto_open`, `auto_weekday` (0=Dom..6=Sab, come `getDay`), `auto_time`.

### 22.3 Modalità portiere: rotazione o fisso (ruolo POR)

Nuova scelta admin in **Partita → Modalità portiere** (`renderGkMode`/`setGkMode`): **🔄 Rotazione** (default, **invariata**: chiunque nello slot `g1`) o **🧤 Fisso**. In modalità **fisso**: nella scheda giocatore (Gestione giocatori) compare il ruolo **Portiere (POR)**; lo slot porta (`g1`) nel picker accetta **solo** i presenti con `role==='POR'` (`openPickerSheet` filtra). **I punteggi NON cambiano**: il bonus/malus portiere resta legato allo **slot g1** (posizionale), quindi `scoreOf`/`get_standings` sono invariati. Helper `roleLabel(r)` (ATT/DIF/POR). Stato `gkFixed`; colonna `leagues.gk_fixed`. Onboarding self-signup resta ATT/DIF: il ruolo POR lo assegna l'admin.

### 22.4 Modalità presenze: admin o giocatori

Nuova scelta admin in **Partita → Presenze** (`renderPresenceMode`/`setPresenceMode`): **🙋 Admin** (default, **invariata**: l'admin segna dal riquadro "Chi gioca questa giornata") o **👥 Giocatori**.
In modalità **giocatori**: la card admin "Chi gioca" si **nasconde** e compare in **Home** (tra l'hero "Pronto a schierare?" e la Classifica) una card `.hpcard` **"Giornata X aperta! · Ci sei?"** con **✓ Ci sono / ✕ Salto** (`renderHomePresence`). La card esce **solo ai giocatori** (chi ha una card giocatore: `myPlayer()`), **non** ai soli-manager; appare solo a giornata **open** e **prima del blocco formazioni** (kickoff−1h, `!lineupLocked`), e **sparisce** allo scadere. Il toggle chiama l'RPC `set_my_presence(present)` che, lato server, consente al **solo proprietario** della propria card di inserirsi/togliersi da `matchday_players` (perché la write su quella tabella è `is_admin()`-only). Conseguenze identiche al solito (schierabile/non, opaco nel mercato). Stato `presenceSelf`; colonna `leagues.presence_self`.

### 22.5 Banner notifiche mensile

Oltre al modale alla primissima apertura (`maybeAskPush`, invariato), c'è un **banner** in cima all'app (`#notifBanner`, `.nbanner`) che invita ad attivare le notifiche **solo a chi non le ha attive** e **al massimo una volta ogni 30 giorni** (`maybeShowNotifBanner`, `localStorage fc_notif_banner`). Mira a `Notification.permission==='default'` (attivabile con un tap); esclude i "bloccati a livello iOS" (non ri-promptabili). Tasti **Attiva** (`bannerEnable`→`enablePush`) e **✕** (`dismissNotifBanner`).

### 22.6 Wizard "regole" alla creazione lega

Chi **crea** una lega, dopo aver fatto il suo giocatore+squadra (onboarding), vede l'overlay **`#rulesSetup`** "Le regole della tua lega" con 3 scelte (ognuna con spiegazione breve): **Apertura** (Manuale/Automatica + giorno/ora se auto), **Portiere** (Rotazione/Fisso), **Presenze** (Admin/Giocatori). `saveRulesSetup()` chiama `set_league_schedule` + `set_gk_mode` + `set_presence_mode`. Mostrato **solo al creatore** (flag `justCreatedLeague`, impostato in `lgCreateBtn`, non nel join). Per la lega #1 già esistente **non appare**: ci sono solo i campi modificabili nelle Impostazioni. Tutte le regole restano sempre modificabili in Impostazioni.

### 22.7 SQL — `config_lega.sql` (idempotente, sostituisce i file SQL config precedenti)

Colonne su `leagues`: `auto_open bool`, `auto_weekday smallint`, `auto_time time`, `gk_fixed bool`, `presence_self bool`.
Funzioni (security definer, `set search_path=public`):

- `get_league_schedule()` → `(auto_open, auto_weekday, auto_time, gk_fixed, presence_self)` per la propria lega (grant `authenticated`). **Ritorno cambiato** → va **droppata** prima di ricrearla.
- `set_league_schedule(p_auto bool, p_weekday int, p_time text)` — admin.
- `set_gk_mode(p_fixed bool)` — admin.
- `set_presence_mode(p_self bool)` — admin.
- `set_my_presence(p_present bool)` — il giocatore segna **la propria** presenza; richiede `presence_self=true`, giornata open, prima di kickoff−1h, e card con `owner_id=auth.uid()`.
- `next_weekly_kickoff(wd int, tm time)` → prossimo fischio settimanale in Europe/Rome.
- `open_due_matchdays()` (service_role) → apre le giornate programmate 48h prima; idempotente (salta se c'è già una giornata non chiusa o lo stesso kickoff); ritorna `(opened_id, opened_label, opened_league, opened_kickoff)`.

### 22.8 `notify.ts` — apertura automatica nello scheduler

Aggiunta `runAutoOpen()` chiamata nel ramo cron (prima di reminder e auto-close): invoca `open_due_matchdays()` e per ogni giornata aperta manda la push **"`<Giornata>` aperta! ⚽"** alla lega giusta. Risposta cron ora `{opened, reminders, closed}`. Resto invariato.

### 22.9 File toccati

- `index.html` — impostazioni a pagine (`setNav`/`.setpage`/`.navrow`), apertura auto/manuale (`renderOpenMode`, `loadSchedule`), modalità portiere (`renderGkMode`, ruolo POR, `roleLabel`, `openPickerSheet`), modalità presenze (`renderPresenceMode`, `renderHomePresence`, `setMyPresence`, card `.hpcard` in Home), banner notifiche (`maybeShowNotifBanner`), wizard creazione (`#rulesSetup`, `saveRulesSetup`, `justCreatedLeague`). `loadSchedule()` ora chiamata all'avvio per **tutti** (serve portiere/presenze a ogni utente).
- `config_lega.sql` — tutta la config lega (sostituisce `apertura_automatica.sql`).
- `notify.ts` — `runAutoOpen`.
- `elimina_lega_test.sql` — utility per cancellare una lega di test (guardia su lega #1), per provare il wizard senza lasciare leghe spazzatura.
- (Ricorda: re-incollare le 2 chiavi Supabase a ogni upload di `index.html`.)

### 22.10 Note di coerenza

- Punteggi **invariati** anche con portiere fisso (bonus portiere = slot `g1`, non ruolo).
- Presenze sempre in `matchday_players`; cambia **chi** può scriverle (admin diretto vs `set_my_presence` per il giocatore).
- `get_league_schedule()` è di fatto il "league config read" usato da tutti; le tre modalità sono lette in `loadSchedule()`.

## 23. Aggiornamenti recenti — Pagellone (storie) + Classifica ANIMATA alla chiusura

> Sessione dedicata a due cose: (1) la **classifica animata** quando una giornata si chiude, (2) il fix del **layout a tutto schermo** (barra in fondo). **Nessun SQL e nessun PNG**: tutto JS/CSS dentro `index.html`, usando dati che le RPC già forniscono.

### 23.1 Pagellone di fine giornata (contesto, già esistente)

Il **Pagellone** è un visore "a storie" (`#pag`, full-screen) aperto da `openRecap(mdId, auto)`:

- carica `get_matchday_recap(md)`; `buildRecapCards(d)` costruisce l'elenco delle scene (numbers, capo, topflop, movers, modules, winner, mvp, …) con **cover** prima e **share** ultima;
- `showRecapCard(i)` mostra una scena alla volta (tap dx = avanti, sx = indietro, swipe giù = chiudi); `countUp()` anima i numeri delle singole scene;
- auto-apertura una volta per giornata via `maybeShowRecap()` (flag `localStorage fc_recap_seen_<mdId>`, init `fc_recap_init`); riapribile a mano dalla Home ("Rivivi l'ultima giornata").

### 23.2 Classifica animata — cosa fa

Quando una giornata si chiude, la classifica non si riordina più "di colpo": si **anima** in 3 momenti.

1. **Riordino righe (FLIP):** le squadre scivolano fluide dalla vecchia alla nuova posizione (`transform`, gira su GPU).
2. **Count-up punti:** il totale di ogni squadra sale animato dal valore *precedente* a quello nuovo.
3. **Frecce:** ad assestamento avvenuto compaiono ▲+n (verde) / ▼−n (rosso); poi **restano** statiche come le mostra oggi `moveArrow()` (finestra 24h). Niente fade-out.

### 23.3 Dove appare (due posti **indipendenti**)

- **Pagellone:** nuova **scena finale** `{t:'standings'}` ("La classifica adesso"), inserita in `buildRecapCards` **prima** di `share` (solo se `standings.length`). Anima la **prima volta** che la scena viene mostrata; poi statica.
- **Scheda Lega:** la **prima apertura** della Lega dopo la chiusura (vista "Classifica generale"), agganciata in `go('classifica')` → `maybeAnimateLega()`.
- I due posti sono **scollegati**: l'effetto avviene in entrambi.

### 23.4 Regola anti-ripetizione — due flag `localStorage` separati

- `fc_lb_anim_pag_<mdId>` → animazione nel **Pagellone** già vista;
- `fc_lb_anim_lega_<mdId>` → animazione in **Lega** già vista.
  Ogni schermata controlla il suo flag, anima una volta, poi lo segna. Stile identico ai flag esistenti (`fc_recap_seen_*`, `fc_push_asked`, …).

### 23.5 "Prima" e "dopo" senza query extra

- **Dopo** = `standings` correnti (da `get_standings()`), già ordinate, con `delta` per riga.
- **Posizione precedente** di ogni squadra = `posizione_attuale + delta`.
- **Totale precedente** (per il count-up) = `totale_attuale − punti_di_giornata`, dove i punti di giornata arrivano da `get_standings_md(md)` (mappa `manager_id → punti`).
- Per sapere se la chiusura è "fresca" (≤24h) si legge `matchdays.closed_at` (aggiunto al `select` di `loadMatchdaysList`).

### 23.6 Requisiti tecnici / dettagli "pro"

- **`data-id = manager_id`** su ogni riga: serve al FLIP per riconoscere la stessa squadra prima/dopo (le righe si ricostruiscono con `innerHTML`). Per questo `loadStandings()` ora mappa anche `manager_id` (era assente).
- Schema FLIP: misura posizioni attuali per id → ridisegna nel nuovo ordine → spostamento inverso istantaneo → rilascio con transizione su `transform`. A fine animazione i `transform` inline vengono **puliti** (nessun conflitto con `.tapd`).
- **Numeri tabulari** (`font-variant-numeric:tabular-nums`) così le cifre non ballano mentre salgono.
- **`prefers-reduced-motion`:** chi ha le animazioni ridotte vede direttamente il risultato finale (frecce già visibili), ma i flag vengono **comunque** segnati come "visto".
- **Skeleton loader** (righe grigie pulsanti) in `renderLB` e `renderMini` mentre i dati caricano (`standingsLoaded`).
- **Mini-classifica Home** = **statica** (solo `data-id`, numeri tabulari, skeleton): niente scorrimento (è top-3, l'effetto entra/esce-dal-podio sarebbe sporco).

### 23.7 Casi limite gestiti

- **Prima giornata chiusa in assoluto** (`delta` tutti 0): niente riordino, solo count-up (da 0 al totale), nessuna freccia → automatico.
- **Pagelloni vecchi:** la scena classifica esce **statica** (il `delta` valido c'è solo per l'ultima chiusura nelle 24h, quindi su giornate vecchie `delta=0` → niente frecce/riordino, ma chiusura comunque elegante).
- **Lega oltre le 24h:** niente animazione (coerente con le frecce che lì non esistono più), classifica statica.
- Parità in classifica, solo-manager, tante squadre (scroll): ok. Mai righe rotte/vuote (l'ordine "vecchio" si misura e si sostituisce in modo sincrono, mai dipinto).

### 23.8 Funzioni nuove (in `index.html`)

`lbRowHTML(t,i,pts,withArrow)` (riga condivisa statica/animata), `moveArrowR(d)` (freccia con classe `.rv` per il reveal), `skeletonRows(kind,n)`, `prefersReduce()`, `lbFresh()` (chiusura ≤24h via `closed_at`), `mdPointsMap(mdId)` (RPC `get_standings_md` → mappa punti), `lbBuildAnimRows()`, `countUpFromTo(el,from,to,dur)`, `lbAnimate(container,rows,mdPts)` (il motore FLIP+count-up+frecce), `maybeAnimateLega()` (trigger Lega), `renderRecapStandings()` (trigger Pagellone). Variabile `standingsLoaded`.

### 23.9 Innesti nel codice esistente (cosa NON ho rotto)

- `doCloseMatchday`: dopo la chiusura ricarica anche `loadStandings()` + `loadMatchdaysList()` (così `latestClosedMd()`/`standings`/`closed_at` sono freschi). Flusso di chiusura, `clearRoundLocal()` e `moveArrow()` **invariati**.
- `buildRecapCards`: la scena `standings` NON conta come "contenuto interessante" → l'auto-apertura del Pagellone resta come prima.
- `renderLB` (vista generale) e `renderMini`: ora emettono `data-id` + numero in `.num` (struttura identica statica/animata) + skeleton.

### 23.10 Layout a tutto schermo (barra in fondo) — nota

Una redesign precedente aveva reso `.app` un **guscio `position:fixed`** con scroller interno (`.scrollwrap`): su **iOS PWA** questo manda in tilt il `bottom:0` dei `position:fixed` (innerHeight/`dvh` sottostimano l'altezza reale → barra "galleggiante"; forzando `screen.height` la barra veniva **tagliata**). Numeri reali misurati su iPhone: `innerHeight≈793`, `screen.height≈852`. **Soluzione:** tornare all'impianto **scroll-pagina** (quello che sul telefono andava bene): `body` scrolla, `.app` blocco normale `min-height:100dvh` con `padding-bottom` per la barra, `.topbar` `position:sticky`, `.nav` `position:fixed;bottom:0` centrata. Rimosso ogni tentativo JS di misurare l'altezza. Lezione: per le full-screen su iOS-PWA, lo **scroll del `body`** è più affidabile del guscio fisso.

### 23.11 File toccati

- `index.html` — tutto qui (motore animazione + scena Pagellone + skeleton + ripristino layout). Nessun altro file.
- (Ricorda: re-incollare le 2 chiavi Supabase a ogni upload; **niente SQL, niente PNG**.)

---

## 24. Aggiornamenti recenti — restyle barre, crediti via sondaggio interno, generatore separato

Sessione di giugno 2026. Tre blocchi: (a) restyle delle barre, (b) metodo crediti con **sondaggio valori interno e per-lega**, (c) **rimozione del generatore squadre** dall'app verso un tool separato.

### 24.1 Restyle barra in alto e in basso

- **Topbar**: da `position:sticky` a **`position:fixed`** (non rimbalza più con lo scroll), **sfondo blu pieno** (`var(--bg)`, niente più gradiente/trasparenza né `backdrop-filter`), sottile `border-bottom`. Per non finire sotto la barra, `.scrollwrap` ha `padding-top: calc(66px + env(safe-area-inset-top))`.
- **Nav in basso**: sfondo blu pieno, niente blur, **più bassa** (ridotte `.nav` padding, `.nav-inner` padding, **`.nav .ic` da 46→32→34px**). Poi resa **piatta come le app di riferimento** (OneFootball/Amazon/Booking): tolto il riquadro/pillola (`.nav-inner` senza background/border/radius), **tolto il pulsante centrale blu** del Campo (ora icona uguale alle altre, attivo solo via colore), icone un po' più grandi (`svg` 21→26px), `border-top` sottile. `.app` padding-bottom adeguato (74px).

### 24.2 Crediti giocatori: Manuale o Sondaggio (interno, per-lega)

Nuova colonna **`leagues.credit_mode`** (`'manual'|'poll'`) + **`leagues.value_poll_open`** bool. Scelta nel **wizard #rulesSetup** (4ª regola «💰 Crediti giocatori») e in **Impostazioni → Lega → Crediti giocatori** (`set_credit_mode`).

- **Manuale**: come prima, l'admin imposta `players.cost` nella scheda giocatore.
- **Sondaggio** (nuovo, sostituisce quello esterno):
  - Tabella **`value_poll`** (`league_id+voter_id` PK, `ratings jsonb {player_id:voto}`), RLS senza policy dirette.
  - **Votano TUTTI i membri** (anche soli-manager); si valutano **tutte le card giocatori** della lega (no manager), **escluso il proprio personaggio**; voto **1–10 con mezzi voti**.
  - **Home**: card `#homeValuePoll` sotto l'hero (se `credit_mode=poll` e `value_poll_open`) → `openValuePoll()` apre l'overlay `#valuePoll` (riusa `.ls-open`); `select` 1..10 per giocatore; «Invia i voti» → `submit_value_poll`.
  - **Chiusura = admin** con contatore «X di Y membri hanno votato» (+ «✓ tutti!»): «Chiudi e calcola i crediti» → `close_value_poll_and_apply()`.
  - **Formula**: media voti per giocatore (default 6 se nessun voto), poi `cost = clamp(round(20 * v^2.4 / media(v^2.4)), 5, 55)`. Calibrata su 100cr/5: medio ~20, i **5 più forti insieme >100** (non comprabili), già 3 forti sfondano. I `cost` restano **modificabili a mano**.
  - Funzioni: `set_credit_mode`, `submit_value_poll`, `get_my_value_poll`, `get_credit_config`, `close_value_poll_and_apply`. Stato letto all'avvio per tutti via `loadCreditConfig()`.
- **SQL**: `sondaggio_valori.sql` (additivo: 2 colonne + tabella + 5 funzioni; non tocca dati esistenti, eseguibile anche a campionato in corso).

### 24.3 Migrazione del sondaggio esterno nella lega 1

`migrazione_lega1_sondaggio.sql` (una tantum, dopo `sondaggio_valori.sql`): porta i voti di `credit_poll` (sondaggio.html, per nome) dentro `value_poll` per la **lega 1**, applicando gli alias dei nomi (Davide D→Davi Kakà, Rouge→Davi Rouge, Francesco Pio→Fra, Lorenzo→Lore Chiesa, Luca→Luchino, Gabry→Gabri), poi **calcola e applica i crediti** e imposta `credit_mode='poll'`, `value_poll_open=false`. Rilanciabile (ripulisce prima). **Dopo: `sondaggio.html` è rimovibile da GitHub.** La card «Risultati sondaggio valori» e la sua funzione `openPollResults` sono state **rimosse** dall'app; la tabella `credit_poll` e l'RPC `get_poll_results` restano in DB (innocue, non più usate in-app).

### 24.4 Generatore squadre rimosso dall'app → tool separato

«Crea le squadre» **rimosso dall'app** (non adatto all'uso diffuso: altre leghe fanno le squadre da sé o hanno giocatori non del fanta). Tolti: card in Impostazioni, funzioni (`openTeamMaker`/`tmGenerate`/`tmMove`/`tmCol`/`renderTeamMaker`/`pollValueFor`/`tmStrength`), `POLL_ALIAS`, variabili `tmA/tmB/pollMap`, e il campo **Valore** nella scheda giocatore. La colonna `players.valore` resta in DB (innocua, preservata sugli edit) ma non è più usata/editabile in-app. CSS `.tm-*` lasciato (morto, innocuo).
Nuovo file **`crea_squadre.html`**: tool **personale offline** (nessun backend/chiave) — rosa salvata in `localStorage`, bilanciamento per forza+ruolo, tap-to-move, «Rigenera». Tool privato di Teo (non serve su GitHub).

### 24.5 File toccati

- `index.html` — restyle barre, sondaggio valori interno (wizard/home/overlay/admin), rimozione generatore + campo Valore.
- `sondaggio_valori.sql` — colonne+tabella+funzioni del sondaggio interno.
- `migrazione_lega1_sondaggio.sql` — migrazione una tantum del sondaggio esterno (lega 1).
- `crea_squadre.html` — tool separato (generatore squadre offline).
- (Ricorda: re-incollare le 2 chiavi Supabase a ogni upload di `index.html`.)

---

## 25. Aggiornamenti recenti — chiusura davvero automatica, frecce in Lega, Pagellone semplificato

> Dove in conflitto con sezioni precedenti, **vale questa**. Tutto in `index.html`, tranne la verifica del timer di chiusura (lato Supabase, 25.1).

### 25.1 Chiusura giornata AUTOMATICA (due livelli)

La giornata si chiude da sola alla **scadenza voti** (kickoff + 25h), aggiornando classifica + crediti e facendo partire il Pagellone, **senza che l'admin prema il tasto**.

- **Lato server (vero "app chiusa"):** `pg_cron` `fanta-reminder` (ogni 10 min) → `notify.ts` `runAutoClose()` → RPC `close_due_matchdays()`. Deve essere attivo su Supabase. File **`timer_chiusura.sql`**: diagnosi (funzione/cron presenti?) + (ri)attivazione idempotente del job + test. Servono `<PROGETTO>` e `<CRON_SECRET>`. *(Verificato funzionante dall'utente.)*
- **Rete di sicurezza lato client (admin):** in `tick()`, se l'admin apre l'app con finestra voti scaduta, chiude via `doCloseMatchday(true)` (guardia `_autoClosing`); sul ramo `auto` chiama `maybeShowRecap()`. Idempotente col server.
- Il tasto "Chiudi adesso" resta solo come chiusura **anticipata** manuale.

### 25.2 Frecce classifica colorate anche in Lega

In Lega le frecce ▲/▼ stavano dentro il nome `<b>` troncato (`overflow:hidden`) → tagliate. Fix in `lbRowHTML`: `<span class="mvw">` ora **sorella** del nome, prima di `.tot`, con `.lb-row>.mvw{flex:none;margin-left:-6px}`. Vale per Classifica generale Lega + scena classifica Pagellone. Home (`renderMini`) invariata. `lbAnimate` trova ancora `.mvw`.

### 25.3 Pagellone — scene più chiare

Tolto «5 vincitori vs 5 sconfitti» e i nomi oscuri «Fascia d'oro/gelata». Scena `captains` riscritta («La fascia da capitano» + sottotitolo «Il capitano vale doppio sul voto…», colonne ✅ Capitano più azzeccato / ❌ Capitano sfortunato, «scelto da {squadra}»). MVP e Vincitore ora scene dedicate (`mvp`, `winner` con cucchiaio). Flusso: cover → you → topflop → captains → mvp → winner → forma → standings → share. Scene `verdict`/vecchia `captains` inerti.

### 25.4 File toccati

- `index.html`, `timer_chiusura.sql`. (Reincollare le 2 chiavi a ogni upload. Niente PNG.)

---

## 26. Aggiornamenti recenti — podio MVP, chiusura "hanno votato tutti", classifica sempre animata nel Pagellone, punti arrotondati

> Dove in conflitto con sezioni precedenti, **vale questa**. `index.html` + **`podio_e_chiusura_voti.sql`** (2 funzioni nuove, additive).

### 26.1 Podio MVP (2º e 3º più votati)

Sotto l'MVP, nella scena `mvp`, compaiono il **2º e 3º più nominati** (🥈/🥉, avatar + nome + n. nomination). Dati da nuova RPC **`get_mvp_podium(md)`** (security definer, top-3 per `count(*)` su `nominations.mvp_player_id`, tie = id più basso; il 1º coincide con l'MVP). Client: `loadRecapExtra` la chiama in parallelo e salva `ex.mvpPodium=[1º,2º,3º]`; la scena usa `slice(1,3)`. CSS `.mvp-podium/.mvp-prow/.mvp-pmedal/.mvp-pav/.mvp-pnm/.mvp-pv`. Se l'RPC non c'è ancora (SQL non eseguito) degrada: nessun podio, nessun errore.

### 26.2 Chiusura anticipata: quando hanno votato TUTTI

Oltre alle 25h, la giornata si chiude **appena tutti gli aventi diritto hanno votato** (es. se alle 16 han votato tutti, si chiude alle 16, non aspetta le 21). Nuova RPC **`close_if_all_voted(p_md)`** (security definer, ritorna bool): chiude + applica crediti via `_apply_credits_core` **solo** se (a) è la propria lega (`my_league()`), (b) c'è ≥1 voto, (c) **nessun** avente-diritto manca all'appello. "Avente diritto" = stessa regola di `canIVote`: **admin** della lega · **extra_voters** · chi ha un **proprio personaggio presente** (`players.owner_id=p.id` in `matchday_players`). "Ha votato" = ≥1 riga in `votes`. Client: chiamata in coda a `submitVotes()`; se torna true → reload giornata/classifica + `clearRoundLocal()` + `maybeShowRecap()` (Pagellone). Idempotente (guardie `status<>'closed'` + `cost_applied`). Backstop 25h lato server invariato. **Nota:** dipende dalla funzione interna `_apply_credits_core(md)` (esistente, usata anche da `close_due_matchdays`/`apply_credit_changes`).

### 26.3 Pagellone: classifica SEMPRE animata (Lega solo la prima volta)

`renderRecapStandings()` ora anima **ogni volta** che si apre la scena classifica del Pagellone (per l'ultima giornata chiusa): rimosso il flag `fc_lb_anim_pag_<md>`. Si anima quando `isLatest && !prefersReduce()`; pagelloni vecchi o reduced-motion = statici. La **Lega** invece resta **solo la prima volta** (`maybeAnimateLega` + flag `fc_lb_anim_lega_<md>`): **invariata**.

### 26.4 Classifica con punti arrotondati (ordine per valore vero)

Nelle **classifiche** i punti si mostrano **interi** (`Math.round`): Home mini, Lega «Classifica generale» (`lbRowHTML`), Lega «di giornata» (`mdStandings`), scena classifica Pagellone, e il count-up animato (`countUpFromTo` ora su interi). L'**ordine** resta per **valore vero** con la virgola (le RPC `get_standings`/`get_standings_md` fanno `ORDER BY points desc` sul valore reale), quindi a pari arrotondato vince chi ha il decimale più alto (es. 79,3 sopra 78,9, entrambi mostrati «79»). `countUp` delle altre scene (data-count con `dec`) invariato.

### 26.5 File toccati

- `index.html` — podio MVP (scena + CSS + fetch), `close_if_all_voted` in `submitVotes`, `renderRecapStandings` sempre animata, arrotondamenti classifica + `countUpFromTo`.
- `podio_e_chiusura_voti.sql` — `get_mvp_podium(md)` + `close_if_all_voted(p_md)` (additive, idempotenti).
- (Reincollare le 2 chiavi Supabase a ogni upload di `index.html`. Niente PNG.)

---

## 27. Aggiornamenti recenti — mezzi punti, STAGIONI, voti+MVP uniti, apertura solo-auto 72h, ciclo presenze (sondaggio 36h)

> Dove in conflitto con sezioni precedenti, **vale questa**. File: `index.html` + **3 SQL nuovi** (`stagioni.sql`, `presenze.sql`, `apertura_72h.sql`) + `notify.ts` aggiornato.
> **Ordine di esecuzione SQL**: `stagioni.sql` → `presenze.sql` → `apertura_72h.sql`. Poi `notify.ts` (Edge Function, MAI su GitHub) e `index.html`. Infine, una volta sola, Admin → Partita → **Salva programmazione**.

### 27.1 Classifica con mezzi punti (0,5) + frecce (SUPERA §26.4)

I punti classifica si mostrano arrotondati **al mezzo punto** con la **virgola** (es. `180,5`). Helper in `index.html`: `roundHalf(n)` e `fmtPts(n)` (`Number.isInteger? "180" : "180,5"`). Applicati a: Home `renderMini`, riga condivisa `lbRowHTML`, `mdStandings`, e al count-up `countUpFromTo`. Ordine sempre per valore vero.
**Frecce ▲/▼**: in **Lega** «Classifica generale» compaiono **solo entro 48h** dall'ultima chiusura (`lbFresh()` ora a 48h; `renderLB` passa `withArrow=lbFresh()`). Nel **Pagellone** restano **sempre** (`lbRowHTML(...,true)` / `lbAnimate`). Il `delta` arriva da `get_standings_season()` ed è **persistente** (richiede ≥2 giornate chiuse nella stagione, niente più gate 24h).

### 27.2 STAGIONI (`stagioni.sql`)

Nuovo concetto: una **stagione** raccoglie max **38 giornate** (come la Serie A). Tabella `seasons(id bigint identity, league_id, number, name, status 'open'|'closed', started_at, ended_at, created_at)` + indice parziale «una sola aperta per lega» + `unique(league_id,number)`. `matchdays.season_id bigint` (FK seasons). RLS `seasons_read` (solo la propria lega).

- **Trigger `stamp_season`** (BEFORE INSERT su matchdays): assegna la stagione aperta (se manca, la crea → «una nuova stagione parte da sé»); se la stagione aperta ha già 38 giornate la chiude e ne apre una nuova; **fissa la label `'Giornata N'` per-stagione (1..38)**. Gira anche per le aperture automatiche (cron) → la numerazione è **lato server** (il `createMatchday` client è ormai morto, vedi §27.5).
- **Trigger `close_full_season`** (AFTER UPDATE): alla 38ª giornata **chiusa**, chiude la stagione.
- RPC: `get_current_season()` (stagione aperta o, se nessuna, l'ultima per numero; con `mds_total`/`mds_closed`), `get_standings_season()` (classifica della **stagione corrente**: somma le sole giornate chiuse della stagione riusando `get_standings_md`, + `delta` frecce), `ensure_open_season()` (admin: apri), `close_season()` (admin: chiudi anticipata).
- Client: `loadSeason()` → `currentSeason`/`currentSeasonId`; `loadStandings()` ora chiama `get_standings_season` con **fallback** a `get_standings` (se la SQL non è ancora stata eseguita). La **classifica è quindi per-stagione** (chiusa una stagione e aperta la nuova, riparte da zero). Il menù a tendina giornate in Lega è filtrato alla stagione corrente (`m.season_id===currentSeasonId`).
- UI: stagione mostrata in Home (`#heroSeason`, in alto a destra) e in Lega (`#legaSeason`, vicino alla classifica). Card admin **«Stagione»** (`#seasonCard`/`#seasonBox`, in Partita) con `closeSeasonNow()` / `openSeasonNow()`.

### 27.3 Voti: MVP unito alla lista + invio unico + medie nascoste

- L'**MVP** non è più un select separato: si sceglie con la **🏆 sulla riga del giocatore** (`pickMvp(id)`, scelta locale in `myNom.mvp`, **salvata insieme ai voti** all'invio). `submitVotes()` fa upsert di `votes` **e** `nominations` insieme.
- **Validazione**: l'invio è bloccato finché non hai dato un voto a **tutti** i presenti **e** scelto l'MVP (`voteStatus()`, `updateSubmitBtn()`, riga `#voteReq`). `ensureStats()` **non** preimposta più il voto a 6 → «non votato» = vuoto/`null`.
- **Medie nascoste a TUTTI** durante la votazione (anche admin): `showAvg=false` in `renderVoti`, `refreshAvgLabels` no-op. Niente conteggio votanti. `renderMvpSegaHint` reso **no-op** (non si mostra più chi il gruppo sta votando come MVP). I voti restano a mezzo punto (`parseVote`/`fmtVote`).

### 27.4 Home: testata lega + stagione

Hero ridisegnato: riga `.hero-head` con **nome lega a sinistra** (`#homeLeague`) e **Stagione N a destra** (`#heroSeason`); sotto il riquadro «pronto a schierare» (`.hero-top`: giornata `#heroKo` + squadra `#heroTeam`). CSS nuovi: `.hero-head/.hh-league/.hh-season`. In Lega: `.lega-head` racchiude `#legaLeague` + `#legaSeason`.

### 27.5 Apertura giornata: SOLO automatica, a **72h** (era 48h)

Tolta la modalità **Manuale**. `renderOpenMode()` mostra solo giorno+ora; `saveSchedule()` salva sempre `p_auto:true`. (`createMatchday`/`confirmMatchday`/`openMatchdaySheet` restano nel file ma **inutilizzati**: la numerazione la fa il trigger.) **`apertura_72h.sql`** riscrive `open_due_matchdays()` per aprire **72h prima** del via (era 48h): si appoggia a `next_weekly_kickoff()` (fuso Europe/Rome, intatta), imposta `league_id` esplicito, label via trigger, idempotente. ⚠️ È l'unica funzione "storica" riscritta — verifica `select next_weekly_kickoff(2,'21:00'::time);` dopo l'esecuzione.

### 27.6 Ciclo presenze + formazioni (modalità giocatori)

Timeline (kickoff = K): **K−72h apertura** (sondaggio presenze aperto, formazioni bloccate) · **K−36h** sondaggio chiuso → formazioni aperte (si schiera solo chi ha votato presente) · **K−1h** formazioni bloccate · K+1h voti · +25h/«tutti votato» chiusura.

- Costante `PRESENCE_CLOSE_BEFORE=36*HOUR`. `mdTimes` aggiunge `presenceClose=k-36h`. `presencePollOpen()` (player mode, giornata aperta, `now<presenceClose`). `computeLock()`: in player mode `lineupLocked` è true anche durante la fase sondaggio. `renderHomePresence` compare durante il sondaggio e **solo ai giocatori** (`is_player`). Messaggi via `lineupBlockReason()`; `phaseLabel`/countdown hanno il ramo «sondaggio presenze».
- **`presenze.sql`**: `set_my_presence` riscritta (guardia `now()<kickoff-36h`, errori `presence_self_off`/`no_open_matchday`/`presence_closed`/`no_player`). ⚠️ **`drop function if exists set_my_presence(boolean);` prima del create** (la vecchia aveva un return type diverso → errore 42P13).
- **Override admin** (player mode): l'admin può correggere le presenze **anche dopo la chiusura del sondaggio**, fino al blocco formazioni. La card admin presenze (`#presCard`) ora compare in player mode quando c'è una giornata aperta; `renderPresence` ne gestisce visibilità + titolo «Presenze — correggi (admin)»; `togglePresence` scrive `matchday_players` diretto (RLS admin, niente guardia tempo).
- **Rosa prevista** (modalità admin, presenze impostabili **prima** dell'apertura): tabella `planned_presences(league_id,player_id)` + RPC `get_planned_presences()`/`set_planned_presence(p_player,p_present)` + **trigger `seed_presences`** (AFTER INSERT su matchdays: in modalità admin precompila `matchday_players` dalla rosa). Client: `plannedPresent` Set, `loadPlannedPresences()`; `renderPresence` instrada: giornata aperta → `matchday_players`; nessuna giornata → rosa prevista.
- **Modifica orario partita** (gestione ritardi/anticipi vs programmato): bottone admin sulla giornata aperta → `openEditKickoffSheet()`/`confirmEditKickoff()` aggiornano `matchdays.kickoff`+`vote_deadline` e **riarmano** `reminder_sent`+`lineup_open_sent`; tutto (presenze/formazioni/voti) si ricalcola dal nuovo kickoff.

### 27.7 Notifiche (`notify.ts`)

> ⚠️ Aggiornato in **§31**: ora sono **4** push (aggiunti promemoria presenze a K−38h e formazioni a 8h dal blocco). Sotto la versione precedente a 2 push.

Colonna `matchdays.lineup_open_sent` (in `presenze.sql`). 2 push in modalità giocatori:

- **1ª, all'apertura** «Vota la presenza»: `runAutoOpen` legge `leagues.presence_self` e, in player mode, invia con **`sendToPlayers()`** (solo `profiles.is_player=true`). In modalità admin invia «schiera» a tutti (`sendAll`).
- **2ª, a K−36h** «schiera la formazione»: nuova `runLineupOpen()` (player mode, una volta sola via `lineup_open_sent`) → `sendAll` (anche i soli-manager schierano). Costante `PRESENCE_CLOSE_BEFORE=36h`.
  Risposta cron ora `{opened, lineup, reminders, closed}`. `sendAll` refattorizzata con `pushList()`; aggiunta `sendToPlayers()`.

### 27.8 Costanti tempi (riepilogo attuale)

Apertura **72h** prima · sondaggio presenze chiude **36h** prima · formazioni bloccate **5 min** prima (era 1h — vedi §31) · voti aperti **+1h** · finestra voti **24h** (chiusi **+25h**). Chiusura anche se hanno votato tutti (§26.2).

### 27.9 File toccati

- `index.html` — mezzi punti+frecce 48h, stagioni (stato/UI/admin), voti+MVP uniti+validazione+medie nascoste, hero testata, apertura solo-auto 72h (testi), ciclo presenze 36h + override admin + rosa prevista + modifica orario.
- `stagioni.sql`, `presenze.sql`, `apertura_72h.sql` (additivi/idempotenti; `presenze.sql` droppa `set_my_presence` prima di ricrearla).
- `notify.ts` — 2 notifiche, `sendToPlayers`, `runLineupOpen`, testi per-modalità.
- (Reincollare le 2 chiavi Supabase a ogni upload di `index.html`. Niente PNG nel repo. `notify.ts` MAI su GitHub.)

---

## 28. Operatività & cose imparate (cron, finestra apertura, fix dati) + data/ora nel sondaggio

> Sessione di messa in produzione del ciclo automatico. Una sola modifica di codice (28.1); il resto è **configurazione/diagnosi** da ricordare.

### 28.1 Sondaggio presenze: mostra giorno e ora del match (codice)

In `renderHomePresence` (`index.html`) la card del sondaggio ora mostra una riga **«📅 Partita: `<giorno ora>`»** presa da `currentMd.kickoff` (via `fmtDayTime`), così la gente sa *quando* si gioca prima di votare presente/assente. Domanda cambiata in «Ci sei a questa partita?». CSS `.hpcard .hp-match` (pill oro). Unico file toccato: `index.html`.

### 28.2 Come funziona DAVVERO l'apertura automatica (catena completa)

`pg_cron` (job **`fanta-reminder`**, `*/10 * * * *`) → fa una **HTTP POST alla Edge Function `notify`** (`net.http_post`, header `x-cron-secret`, body `{mode:'reminder'}`) → `notify` chiama `open_due_matchdays` / `runLineupOpen` / `runReminder` / `close_due_matchdays`. **Importante**: chiamare `select open_due_matchdays();` a mano APRE la giornata ma **NON manda le push** (le push le manda `notify`, non la funzione SQL). Per testare le notifiche bisogna lasciar fare al **cron** (resettare la giornata e aspettare lo scatto), non riaprire a mano.

### 28.3 La finestra 72h è un «da… in poi», non una scadenza

`open_due_matchdays` apre se **`now() >= kickoff-72h` E `now() < kickoff`**. Quindi se il momento «kickoff-72h» è già passato, NON è un problema: sei *dentro* la finestra e la giornata è apribile fino al fischio d'inizio. La scritta in app «Si aprirà sab 20:00» è solo il momento teorico d'inizio finestra. Idempotenza: non apre se esiste già una giornata non chiusa o una con lo stesso kickoff.

### 28.4 TROUBLESHOOTING CRON — il caso «non si apre da sola» (401 → 200)

Sintomo: le giornate non si aprivano/chiudevano da sole e **nessuna push** arrivava, pur con `fanta-reminder` attivo. Diagnosi: `select status_code, content from net._http_response order by created desc limit 5;` → tornava **401 `{"error":"bad cron secret"}`**. Due cause, da sistemare entrambe:

- **Verify JWT** sulla function `notify` deve essere **OFF** (Edge Functions → notify → Settings). Se ON, la chiamata del cron è rifiutata prima di entrare (la function si protegge da sé col `x-cron-secret`).
- **`CRON_SECRET` allineato**: il segreto nel job `cron.schedule` e quello nei **Secrets** della function devono essere **identici** (occhio a spazi/maiuscole; un valore alfanumerico semplice evita problemi). Dopo aver cambiato un Secret può servire **ridistribuire** la function.
  Ricreazione job (template):

```sql
select cron.unschedule('fanta-reminder');
select cron.schedule('fanta-reminder','*/10 * * * *', $$
  select net.http_post(
    url := 'https://lfvpseusbsyzniugczbx.supabase.co/functions/v1/notify',
    headers := jsonb_build_object('Content-Type','application/json','x-cron-secret','SEGRETO'),
    body := jsonb_build_object('mode','reminder')
  );
$$);
```

Verifica OK = `status_code 200` con `{"ok":true,"opened":..,"lineup":..,"reminders":..,"closed":..}`. (Nota: i timestamp di `net._http_response` sono in **UTC**, +2h rispetto all'ora italiana legale. `status_code` **NULL** = risposta non ancora registrata, non è un errore.)

### 28.5 FIX DATI — carta con `owner_id` sbagliato (es. «Benzo»)

Sintomo: un giocatore vota «Ci sono» (e sblocca il proprio personaggio nel mercato), ma rientrando il voto non risulta più e a essere «presente» è un'**altra carta** (una carta del listone senza profilo). Causa: quella carta ha per errore l'`owner_id` di un utente reale (residuo del vecchio bug del rinomino di massa), quindi `set_my_presence` trova **due** carte col tuo `owner_id` e ne salva una "a caso". Diagnosi:

```sql
select p.id, p.name, p.owner_id, pr.player_name
from players p left join profiles pr on pr.id=p.owner_id
where p.owner_id is not null order by p.owner_id, p.id;
```

Regola: **ogni persona possiede ESATTAMENTE una carta** (la propria); le carte del listone non-personali hanno `owner_id=null`. Fix:

```sql
update players set owner_id=null where name='Benzo' and league_id=1;
delete from matchday_players
 where matchday_id=(select id from matchdays where status='open' order by id desc limit 1)
   and player_id=(select id from players where name='Benzo' and league_id=1);
```

(Possibile hardening futuro: rendere `set_my_presence` deterministico nella scelta della carta — non fatto, bastava pulire il dato.)

### 28.6 File toccati

- `index.html` — data/ora nel sondaggio presenze (`renderHomePresence` + CSS `.hp-match`).
- Nessun nuovo SQL applicativo. Le query di 28.4/28.5 sono **operative/diagnostiche**, non migrazioni.

---

## 29. Aggiornamenti recenti — BACHECA (trofei/achievement), card Home giocatore+manager, scheda squadra, pagina full-screen, filtro moduli per reparto

Grande aggiunta: una **Bacheca** di trofei automatici, retroattivi, a **zero lavoro admin** (calcolati dai dati già raccolti). Ogni persona ha **due nature** e la bacheca le mostra entrambe: lato **giocatore** (sta nel listone) e lato **manager 👔** (ha una squadra). Più una rifinitura importante al **campo**: i moduli selezionabili dipendono dai presenti per reparto.

### 29.1 Due tipi di targa

- **Traguardi** 🔒 = milestone **cumulative a gradini**, **all-time** (tutte le stagioni), **sticky** (una volta presi restano).
- **Titoli** 🏅 = di **classifica/reparto**, **uno solo per lega**, **per stagione corrente**, **perdibili**; scattano solo col **gate presenze** (≥30% delle giornate chiuse della stagione, **minimo 4 presenze**) per non essere ridicoli a inizio stagione. I titoli restano **nello storico** etichettati «Stagione N».

### 29.2 Catalogo targhe (soglie finali)

**Giocatore — Traguardi 🔒 (all-time):**

- **Cecchino** — gol totali · 10/25/50/100
- **Rifinitore** — assist totali · 10/25/50
- **Uomo copertina** — MVP di giornata vinti · **1**/3/7/15
- **Tripletta / Poker / Manita** — 3 / 4 / 5+ gol in **una** giornata (targhe distinte, sticky; mostrate col solo nome, senza numero)
- **Presenza** — presenze totali · **5**/10/25
- **Stagione perfetta** — 100% delle giornate di una stagione (min 8)

**Giocatore — Titoli 🏅 (stagione, gate presenze):**

- **Pallone d'oro** — miglior voto medio assoluto
- **Re dell'attacco** / **Diga** / **Saracinesca** — miglior voto medio per reparto ATT/DIF/POR (Saracinesca **solo se `gk_fixed`**)
- **Capocannoniere** — più gol in stagione · **Mago degli assist** — più assist in stagione
- **Sul podio del reparto** — 2º-3º di reparto (versione leggera, chip argento)

**Manager 👔 (traguardi sticky, conteggi stagione corrente):**

- **Profeta** — modulo ≠ default (1-3-1/1-1-3) **e** chiusura in metà alta · 3/8/15
- **Capitano coraggioso** — il capitano schierato è stato MVP o ha segnato ≥1 gol · 3/8/15
- **Re della giornata** — vittorie di giornata (1º in `get_standings_md`) · 1/3/7
- **Al comando** — giornate chiuse da 1º in classifica generale · 1/5/12
- **Scalatore** — balzo massimo di posizioni in una giornata · +3/+5/+8

**Headline (punto di forza)** + **pavimento di dignità**: la card sceglie da sola la dimensione in cui spicchi; se non eccelli in nulla ripiega su **Bandiera** (presenze) o sul miglior piazzamento di reparto. Nessuno resta senza headline.

### 29.3 «Al comando» e «Scalatore» — classifica storica progressiva senza tabelle

Non esiste (né serve) una tabella snapshot delle posizioni. Si **ricostruisce in SQL** la classifica «com'era dopo ogni giornata chiusa» della stagione, scorrendo le chiuse in ordine di `closed_at` e sommando progressivamente i punti via `get_standings_md`. Da lì: **Al comando** = nº giornate chiuse da 1º; **Scalatore** = max balzo (pos. precedente − pos. nuova). Retroattivo, zero lavoro admin, coerente col punteggio. Helper interno `_season_rank_history(p_season)`.

### 29.4 SQL — `bacheca.sql` (additivo, idempotente)

**Già eseguito.** Non tocca tabelle/trigger/funzioni esistenti. Crea funzioni interne + 2 RPC pubbliche:

- `get_player_card(p_player_id bigint)` → jsonb: stats base (riusa `get_player_stats`), traguardi (con gradino), titoli (con gate+stagione), headline, **prossimo traguardo** (per la Home), **lato manager** della stessa persona (risolve `owner_id`).
- `get_team_card(p_manager_id uuid)` → jsonb: stats squadra (punti, posizione, vittorie giornata, **giornate da leader**, **miglior balzo**, miglior giornata), traguardi manager, headline, prossimo traguardo. Funziona anche per i **soli-manager**.
- Helper: `_badge_tier(qty, thresholds[])`, `_season_rank_history(p_season)`, `_manager_season_facts()`, `_player_facts()`, `_next_milestone_player(...)`, `_next_milestone_manager(...)`.
- **Gate titoli**: `pres_season >= greatest(4, ceil(v_closed*0.30))`.
- **Casi limite gestiti**: inizio stagione (titoli sotto soglia → assenti), solo-manager (solo card manager), gk a rotazione (niente Saracinesca), parità medie (ordine per id), nessun MVP, persona senza nulla (pavimento di dignità), `played_md`/`leader_days` contano solo le giornate **effettivamente schierate** (i soli-manager che non schierano non risultano «in metà alta»/«leader»).
- **Note tecniche imparate**: `league_id` è BIGINT; non si può mettere una window function (`lag`) dentro un'aggregata (`max`) → separare in CTE; `_player_facts()` calcola voto_season da `votes`, presenze da `matchday_players` con la stessa guardia di `get_player_stats` (kickoff−1h o closed).

### 29.5 DOVE si vede (client)

Render condiviso `bachecaHTML(card,{includeManager})` + `badgeDesc(key,val)` (frase chiara sotto ogni traguardo, es. «Scalatore» → «Balzo record: +3 posizioni in una giornata»). Medaglie per gradino `MEDALS=['','🥉','🥈','🥇','💎']`.

- **Mercato** → tap sulla card apre la **pagina bacheca** (vedi §29.6): stat esistenti (Presenze/Gol/Assist + Voto medio admin) **invariate**, con la bacheca **aggiunta sotto** (`#statBacheca`). Mostra **solo le targhe conquistate** (niente lucchetti/vuoti). Riga **👔 Da manager** in fondo.
- **Home** → due card separate **sotto la Classifica** (`#homeBcardPlayer`, `#homeBcardMgr`): card **giocatore** (solo se `is_player` e ha un `myPlayer()`) con headline + forma + piazzamento reparto + barra **prossimo traguardo**; card **manager 👔** (per **tutti**, anche soli-manager) con headline + pillole. Tap → pagina bacheca completa (`openMyPlayerBacheca`/`openMyTeamBacheca`). Throttle 20s + refresh forzato dopo chiusura giornata. **Il Pagellone automatico** a schermo intero resta indipendente e parte come prima.
- **Classifica generale (Lega)** → tap sulla riga squadra (`lbRowHTML` → `openTeamCard(manager_id)`) apre la **scheda squadra**. La **vista di giornata** resta invariata (tap → formazione, `openTeamLineup`).

### 29.6 Pagina bacheca full-screen (NON più finestra/modal)

Scelta UX: i vecchi modal `statModal`/`teamModal` con sfondo bloccato facevano «ballare» lo sfondo su iPhone. Sostituiti da **una pagina overlay** a tutto schermo `#bachecaPage` (classe `.overlay .bch-page`, `z-index:90`, stessa tecnica collaudata di gate/onboard/league: `position:fixed; inset:0`, scrolla internamente, niente sfondo dietro). Header con **‹ Indietro** (`closeBacheca()`). Due sotto-blocchi `#pgPlayer` / `#pgTeam`; `openBacheca('player'|'team')` mostra quello giusto. Le funzioni storiche `closeStatModal`/`closeTeamModal` ora rimandano a `closeBacheca`. Il modal `.statmodal` **resta** solo per il push-prompt (`pushModal`). Rimossi gli helper `lockScroll/unlockScroll` (non più necessari).

### 29.7 Filtro moduli per reparto (campo) + 1-2-2 a «ruoli liberi»

I moduli ora si abilitano in base ai **presenti per reparto** (ruolo anagrafico): un modulo è scegliibile solo se `#ATT_presenti ≥ slot_ATT` **e** `#DIF_presenti ≥ slot_DIF`.

- `MODULE_NEED = {'1-3-1':{ATT:1,DIF:3}, '1-2-2':{ATT:2,DIF:2}, '1-1-3':{ATT:3,DIF:1}}`.
- `fieldAvailability()` → `{nATT,nDIF,available:Set,freeRoles}`. Esempi: 1 DIF → solo 1-1-3 · 1 ATT → solo 1-3-1 · 2 DIF → 1-2-2 e 1-1-3 · 2 ATT/2 DIF → solo 1-2-2 · 3/3 → tutti.
- **Manca un reparto** (0 ATT **o** 0 DIF) → `freeRoles=true`: **solo 1-2-2** e **blocco ruoli disattivato** (in `openPickerSheet`, gli slot di movimento accettano chiunque; il portiere resta secondo `gkFixed`). Bonus modulo 1-2-2 = 0 → nessuna distorsione. Banner giallo `#modFreeInfo`.
- I moduli non disponibili restano **visibili ma disabilitati** (`.modbtn.unavail`, con `title` esplicativo). `setModule` rifiuta i non disponibili con toast.
- `ensureValidModule()` (chiamato in `renderPitch`) ripiega su un modulo valido se quello attuale non lo è più (svuota la formazione). **Guardia**: non agisce se `mdPresent.size===0` (evita di svuotare al primo caricamento prima che le presenze siano caricate).
- **Admin corregge le presenze** → riadeguo automatico: `togglePresence` ora chiama anche `renderPitch()`; il **realtime** ascolta pure `matchday_players` (`schedulePresence`/`refreshPresence`: `loadMdPresent` + ridisegno) così il cambio si propaga a tutti senza ricaricare.
- **Ruoli validi per stat/trofei**: il «ruolo libero» vale **solo** per schierare. Il salvataggio (`saveBtn`) scrive `slot`+`player_id`+`module` senza validazione di ruolo (lo slot `g1` = portiere ai fini punteggio; gli slot di movimento non danno bonus di ruolo).

### 29.8 File toccati

- `index.html` — Bacheca completa (CSS+render+2 card Home+pagina full-screen+scheda squadra+tap classifica generale); filtro moduli per reparto + ruoli liberi + refresh presenze realtime. **Reincollare le 2 chiavi Supabase a ogni upload.**
- `bacheca.sql` — **già eseguito** (additivo/idempotente). Nessun PNG.
- Nessuna modifica a `notify.ts`.

---

## 30. Correzione punteggio — risultato squadra reale = +2 / −1 (`fix_esito.sql`)

**Regola corretta e definitiva:** giocatori della squadra (di calcetto) che **vince → +2**; che **perde → −1**; pareggio/null → 0. (Supera le note precedenti §21.1/§18.1 che indicavano «±1»: erano errate. La vittoria è sempre stata +2.)

**Stato trovato nel codice prima del fix:**

- Client `scoreOf` (riga ~2374): `V → +2`, `S → −1` ✅ **già corretto**.
- SQL `get_standings_md`: `V → +2`, `S → −2` ❌ (sconfitta sbagliata).

**Fix:** `fix_esito.sql` ridefinisce **solo** `get_standings_md` portando la sconfitta a **−1**. È l'unica funzione che applica la formula esito ai punti di classifica; la usano anche il **Pagellone** (`mdPointsMap` → `get_standings_md`) e la **Bacheca** (`get_standings_md` dentro `get_player_card`/`get_team_card`/`_season_rank_history`), quindi un solo punto allinea tutto. I **crediti a ranking** (`_apply_credits_core`) usano una formula **senza** esito → non interessati.

**Retroattivo:** ricalcola le classifiche delle giornate già chiuse (i perdenti del passato guadagnano +1 a giornata persa). Voluto: la regola corretta vale per tutti uguale.

**Verifica fatta:** con voto 6 piatto, vincitore 6+2=8 (invariato), perdente passa da 6−2=4 a 6−1=5. Idempotente (`CREATE OR REPLACE`).

**File toccati:** `fix_esito.sql` (additivo/idempotente). `index.html` **non** modificato (client già +2/−1). Nessun PNG, nessuna modifica a `notify.ts`.

---

## 31. Aggiornamenti recenti — blocco a 5 min, +2 promemoria mirati, capitano obbligatorio, crediti semplificati, gestione giocatori a tendina, chiavi nel file

Sessione di rifinitura UX + notifiche. **File toccati:** `index.html`, `notify.ts`, `promemoria.sql` (nuovo), `fix_presenze_5min.sql` (nuovo). Nessun PNG.

### 31.1 Blocco formazioni: kickoff − 5 min (era kickoff − 1h)

- `index.html`: `LINEUP_LOCK_BEFORE=5*MIN` (aggiunta costante `MIN=60000`). Testi UI aggiornati («si bloccano 5 min prima del via») in `lineupBlockReason`, hint apertura/modifica giornata, prompt notifiche.
- `notify.ts`: costante `LINEUP_LOCK_BEFORE = 5 * MIN`; `runReminder` usa `lock = kickoff − LINEUP_LOCK_BEFORE` (il promemoria «ultima ora» resta 1h prima del *blocco*).
- `fix_presenze_5min.sql`: **`get_player_stats`** allineata — soglia presenze statistiche da `interval '1 hour'` a `interval '5 minutes'`. Unica modifica, stessa firma, `CREATE OR REPLACE`. (Mantiene i filtri `my_league()` e la forma da `players.trend`.)
- ⚠️ Invariante: questo valore deve restare identico tra client (`LINEUP_LOCK_BEFORE`), `notify.ts` e la soglia in `get_player_stats`.

### 31.2 Notifiche: ora 4 push (aggiunti 2 promemoria mirati)

Set completo in modalità giocatori, in ordine di tempo:

1. **Apertura** «Vota la presenza» → solo giocatori (`runAutoOpen` + `sendToPlayers`). *(invariata)*
2. **K−38h** «Vota la presenza! Il sondaggio chiude tra 2h» → **solo ai giocatori che NON hanno ancora risposto** al sondaggio (`runPresenceReminder`, una volta sola via `presence_remind_sent`). Solo se `leagues.presence_self=true`. *(NUOVA)*
3. **K−36h** «Presenze chiuse — schiera» → a tutti (`runLineupOpen`). *(invariata)*
4. **8h prima del blocco** «Schiera la formazione» → **solo a chi NON ha ancora schierato** (`runLineupReminder`, una volta sola via `lineup_remind_sent`); vale in entrambe le modalità. *(NUOVA)*
5. **1h prima del blocco** «Ultima ora» → a tutti (`runReminder`). *(invariata, ora relativa al blocco a −5min)*
6. Apertura/chiusura giornata invariate.

Implementazione `notify.ts`: nuove `runPresenceReminder()` e `runLineupReminder()` + helper **`sendToIds(title,body,url,leagueId,ids[])`** (push a un elenco esplicito di `user_id`, filtrato per lega). Targeting:
- non-votanti presenze = `profiles(is_player=true, league)` **meno** chi è in `presence_responses` per quella giornata.
- non-schierati = tutti i `profiles(league)` **meno** i `manager_id` presenti in `lineups` per quella giornata.
Risposta cron ora `{opened, presRem, lineup, lineupRem, reminders, closed}`.

### 31.3 Tracciamento risposte al sondaggio presenze (`promemoria.sql`)

Serviva per il punto 2 («solo chi non ha votato»): il DB prima **non** distingueva «ha votato Salto» da «non ha votato» (entrambi assenti da `matchday_players`). Aggiunto:

- Tabella **`presence_responses(matchday_id, user_id, responded_at, PK(md,user))`** + RLS (`select using(true)`, `insert with check(user_id=auth.uid())`).
- RPC **`mark_presence_responded()`** (security definer): trova la giornata `open` della lega del chiamante e inserisce la riga (idempotente, `on conflict do nothing`). **Non** tocca le presenze vere (restano in `set_my_presence`, lasciata intatta → zero regressioni).
- Client: in `setMyPresence`, dopo il successo, chiama `mark_presence_responded` (sia per «Ci sono» sia per «Salto»).
- Colonne nuove su `matchdays`: **`presence_remind_sent`**, **`lineup_remind_sent`** (bool default false). Resettate (false) in `confirmEditKickoff` insieme a `reminder_sent`/`lineup_open_sent`. Il `promemoria.sql` fa `update matchdays set ...=true where status='open'` così la giornata già aperta al deploy non riceve avvisi fuori tempo.

### 31.4 Capitano obbligatorio

Prima il tasto «Conferma formazione» era cliccabile anche senza capitano. Ora in `updateBudget`: `btn.disabled=!(n===5 && captain)` e testo «👑 Scegli il capitano». Guardia anche in `saveBtn.onclick`: se `!captain` → toast e stop. Solo `index.html`.

### 31.5 Crediti: tolta la sezione dalle impostazioni admin

La scelta **manuale/sondaggio all'apertura lega** (`setupRules.credit` → `set_credit_mode`) resta intatta. Nelle impostazioni admin:
- rimossi la card statica «💰 Crediti giocatori», il toggle `creditModeSw` e il bottone «Riapri il sondaggio».
- la card `#creditCard` ora è `display:none` di default e `renderCreditAdmin` la mostra **solo mentre un sondaggio valori è aperto** (avanzamento + «Chiudi e calcola i crediti»); chiuso il sondaggio, sparisce per sempre.
- dopo, i crediti si modificano **a mano** dalla scheda di ogni giocatore (matita ✏️).
- `setCreditMode()` resta definita ma non più richiamata da bottoni (il setup usa `sb.rpc('set_credit_mode')` direttamente). `renderHomeValuePoll` (card sondaggio per i membri) invariata.

### 31.6 Gestione giocatori → tendina (accordion)

La card «Gestione giocatori» era sempre aperta e occupava troppo. Ora è un accordion `.acc gold` (chiuso di default) col pattern esistente `toggleAcc(this)` / `.acc-head` / `.acc-body`. Mantiene `id="manageCard"` sull'`.acc` esterno (lo show/hide admin in `applyProfile` continua a funzionare). Contenuto invariato (`#manageList` + «＋ Nuovo giocatore»). Solo `index.html`.

### 31.7 Chiavi Supabase incollate nel file (niente più re-paste)

`SUPABASE_URL` e `SUPABASE_ANON` (publishable) sono ora **scritte direttamente** in `index.html` (non più placeholder `INCOLLA_*`). La publishable key è pubblica per design (già visibile nel sito), quindi sicura nel repo; le RLS proteggono i dati. **D'ora in poi NON serve re-incollare le chiavi** a ogni upload. Resta valido: usare la publishable (`sb_publishable_…`), MAI la secret. La guardia `if(SUPABASE_URL.includes('INCOLLA')…)` resta innocua (non scatta).

### 31.8 Ordine di deploy

1. SQL Editor: `promemoria.sql` → poi `fix_presenze_5min.sql`.
2. Edge Function `notify`: incolla `notify.ts` e Deploy (mai su GitHub).
3. GitHub: `index.html` (Vercel ridistribuisce).

Il SQL va per primo (app e `notify` usano le nuove colonne/tabella/RPC).

---

## 32. Impostazioni admin a tendine + DASHBOARD super-admin esterna + manutenzione GLOBALE

Sessione: pulizia impostazioni admin e nuova console del proprietario dell'app. **File toccati:** `index.html`, `superadmin.sql` (nuovo), `admin.html` (nuovo). Nessun PNG. Nessuna modifica a `notify.ts`.

### 32.1 Impostazioni admin tutte a tendina (accordion)

Tutte le sezioni di **Partita** e **Lega** ora sono accordion chiusi di default (pattern esistente `toggleAcc(this)` / `.acc` / `.acc-head` / `.acc-body`), per ridurre l'ingombro.

- **Partita:** Modalità portiere, Presenze, Stagione (`#seasonCard`), Giornata (`#mdCard`), Chi gioca (`#presCard`).
- **Lega:** Invita (`#inviteCard`), Gestione giocatori (già accordion da §31), Voto soli-manager (`#voterCard`), Manutenzione lega (`#maintCard`). `#creditCard` resta NON-accordion (è il pannello a comparsa automatica del sondaggio valori).
- **Vincolo importante:** gli `id` che il JS usa per show/hide via `style.display` (`presCard`, `mdCard`, `voterCard`, `maintCard`, `inviteCard`, `seasonCard`) restano sull'elemento **esterno** `.acc` (così `applyProfile`/`renderPresence`/`renderMatchday`/`loadInvite` continuano a funzionare). Il titolo dinamico `#presTitle` è ora uno `<span>` dentro l'`.acc-head` (l'icona resta).
- Manutenzione per-lega rinominata «**Manutenzione lega**» per distinguerla dalla globale (§32.3).

### 32.2 Dashboard super-admin — `admin.html` (esterna ma collegata)

Pagina **separata** `admin.html` nello **stesso repo** GitHub → pubblicata da Vercel sullo stesso sito → URL **`fantacalcettoitalia.it/admin.html`**. Usa lo **stesso Supabase** (stesse chiavi incollate, login via OTP email identico all'app; riusa la sessione se già loggato sullo stesso dominio). `<meta robots noindex>`.

- **Protezione lato server:** ogni RPC `sa_*` controlla `is_superadmin()`; un non-super-admin vede «Accesso riservato». Il gate client è solo UX.
- **Mostra:** leghe totali/attive/inattive, leghe a pagamento/gratis, utenti totali/attivi/inattivi, costo/ricavo/margine stimati (editabili), elenco leghe con toggle Gratis↔Pagante, e il tasto **Manutenzione globale**.
- **Definizioni «attivo» (ultimi 30 giorni):** lega = ha una giornata con `status='open'` OR `kickoff > now()-30d` OR `closed_at > now()-30d`; utente = `last_seen > now()-30d`.
- **Economia:** `monthly_cost` e `price_per_league` li imposta l'admin dalla dashboard (`sa_set_economics`); `revenue_est = leghe_paganti × price`, `margin_est = revenue_est − monthly_cost`. (Placeholder finché non li compila.)

### 32.3 Manutenzione GLOBALE (super-admin) — `app_global`

Distinta dalla manutenzione per-lega (`app_state`, invariata). Tabella singola **`app_global(id=1, maintenance, monthly_cost, price_per_league, updated_at)`** (RLS: read `true`, scrittura solo via RPC super-admin).

- Toggle dalla dashboard → `sa_set_maintenance(bool)`.
- **Enforcement nell'app (`index.html`):** `loadMaintenance()` ora legge ANCHE `app_global.maintenance` (→ `globalMaint`). `applyMaintenance()`: l'overlay `#maint` esce se `(globalMaint && !isSuperAdmin) || (maintOn && !isAdmin)`. Banner: super-admin vede «🌐 Manutenzione GLOBALE attiva»; admin di lega vede «⚙️ Manutenzione lega attiva». Il super-admin (`profile.is_superadmin`) **non** viene mai bloccato.
- **Buttafuori live:** il canale realtime `maint` ascolta sia `app_state` sia `app_global`; a ogni cambio richiama `loadMaintenance()` → chi è dentro viene messo in stand-by all'istante. ⚠️ Richiede che **`app_global` sia nella publication realtime** (`alter publication supabase_realtime add table app_global;` oppure Database → Replication).

### 32.4 `last_seen` (utenti attivi)

Colonna `profiles.last_seen timestamptz`. RPC `touch_last_seen()` (security definer, aggiorna `last_seen=now()` per `auth.uid()`), chiamata dall'app a ogni avvio (subito dopo `loadMaintenance()`). Alimenta il conteggio «utenti attivi» della dashboard.

### 32.5 `superadmin.sql` (additivo, idempotente) — contenuto

Colonne: `profiles.is_superadmin` (bool def false), `profiles.last_seen`, `leagues.is_paid` (bool def false). Tabella `app_global`. Funzioni: `is_superadmin()`, `touch_last_seen()`, `sa_set_maintenance(bool)`, `sa_set_league_paid(bigint,bool)`, `sa_set_economics(numeric,numeric)`, `sa_overview()→jsonb`, `sa_leagues()→jsonb`. Tutte le `sa_*` guardate da `is_superadmin()`; grant `authenticated`.

**Due passi a mano (una volta):**
1. Renditi super-admin: `update profiles set is_superadmin=true where id=(select id from auth.users where email='LA_TUA_EMAIL');`
2. Realtime: aggiungi `app_global` alla publication (vedi §32.3).

### 32.6 Ordine di deploy

1. SQL Editor: `fix_presenze_5min.sql` (se non già fatto) → `superadmin.sql` → i 2 passi a mano (§32.5).
2. GitHub: `index.html` (aggiornato) + `admin.html` (nuovo).
3. Aprire `fantacalcettoitalia.it/admin.html`.

Chiavi già incluse in entrambi i file: niente re-paste.

### 32.7 Aperti / possibili prossimi passi

Affinare le soglie «attivo» (ora 30g fisse); grafici storici (servirebbe `created_at` su `profiles`/`leagues`, oggi non garantito); dati economici reali (tariffe). La manutenzione globale non logga; la dashboard non ha realtime (basta «↻ Aggiorna»).

---

## 33. Rigori (sbagliato −3 / parato +3), grafico andamento voti per giocatore, rimozione manutenzione lega dall'app (`rigori.sql`)

Sessione su 3 richieste. **File toccati:** `index.html`, `rigori.sql` (nuovo, additivo/idempotente), context (`FANTACALCETTO.md`, `fantacalcetto_context.py`). Nessun PNG, nessuna modifica a `notify.ts` o `admin.html`.

⚠️ **Ordine di deploy:** eseguire **PRIMA** `rigori.sql` (aggiunge le colonne), **POI** caricare `index.html`. Il pannello partita ora invia sempre anche `rigore_sbagliato`/`rigore_parato` nell'upsert: senza le colonne il salvataggio fallirebbe. La SQL Editor fa rollback su errore → dati al sicuro.

### 33.1 Rigore sbagliato (−3) e rigore parato (+3)

Due nuovi eventi bonus/malus nel **pannello partita live**, mostrati in una **riga piccola in basso** insieme all'Autogol (eventi rari). Emoji: 🚫 rig. sbagliato, 🙌 rig. parato, 💀 autogol.

- **DB**: `match_stats` + colonne `rigore_sbagliato int not null default 0`, `rigore_parato int not null default 0` (additive: righe esistenti → 0, dati intatti).
- **Punteggio** (invariante client⇄SQL): aggiunto `− rigore_sbagliato*3 + rigore_parato*3` in **`scoreOf()`** (client) e in **`get_standings_md`** (SQL, unica funzione punti → allinea anche Pagellone e Bacheca). Valori scelti = standard fantacalcio, stessa scala di gol(+3)/autogol(−3). I **crediti** (`_apply_credits_core`) NON toccati (formula proxy, già senza esito/clean-sheet → coerente escludere anche i rigori).
- **Modello dati client**: chiavi `rs`/`rp` aggiunte all'oggetto-stat di default ovunque (`{gol,assist,og,gs,rs,rp,esito}`) e ai lettori da DB (`rs:r.rigore_sbagliato`, `rp:r.rigore_parato`) in `loadMatchStats` + i due lettori Pagellone.
- **UI pannello**: `LIVE_FIELDS` con `og`/`rs`/`rp` (campo `tone:'neg'|'pos'`); `renderLive` home ridisegnata = 3 blocchi grandi (gol/assist/portiere) + `.ls-srow` con 3 `.ls-mini` (CSS nuovo). Picker `+/−` riusa `liveAdd` generico. Upsert in `liveConfirmSave` con le 2 colonne. Icone campo `statIcons` += 🚫×rs, 🙌×rp. Regolamento (Impostazioni) += 2 righe.

### 33.2 Grafico andamento voti nella scheda giocatore

Nella scheda giocatore (overlay `#bachecaPage` → `#pgPlayer`), tra le statistiche e la bacheca, un **grafichino a linea** dell'andamento del **voto medio per giornata** (SOLO voto, niente bonus) nella stagione corrente.

- **SQL**: nuova RPC **`get_player_vote_trend(p_player bigint)`** → `(md_label, voto)`, una riga per ogni **giornata chiusa** con voti per quel player, `avg(votes.score)`, scoping `my_league()`, ordine per `kickoff`. Grant `anon, authenticated`.
- **Client**: container `#statChart` (`.vtrend`, CSS nuovo). `loadVoteTrend(id)` (chiamata in `openPlayerStats`) → fetch RPC → `voteTrendHTML(pts)` disegna un **SVG** fatto a mano (curve Catmull-Rom→Bézier, area sfumata, linea media tratteggiata, pallini verde/rosa sopra/sotto la media, voto sopra ogni punto, label `G1/G2…` ricavata dal numero nella label). Si mostra solo con **≥2 giornate**; se l'RPC non è ancora installata o si è offline → silenziosamente niente grafico (nessun crash). `mdShortLabel` estrae N da "Giornata N".

### 33.3 Rimozione pannello «Manutenzione lega» dall'app

Tolto dall'area admin in-app il blocco `#maintCard` (la manutenzione si gestisce dalla **console esterna** `admin.html`). Aggiornato il sottotitolo del menu Lega (tolta la parola «manutenzione»).

- ⚠️ Rimossa solo la **UI** della manutenzione **per-lega**. La **logica** (`loadMaintenance`/`applyMaintenance`/`subscribeMaintenance`) e l'**overlay/banner** restano intatti: servono ancora a mostrare/bloccare gli utenti quando è attiva la **manutenzione GLOBALE** dalla console. `renderMaintBtn` e il toggle `#maintCard` in `applyProfile` hanno già le guardie `if(!el)` → nessun errore con gli elementi rimossi. `setMaintenance`/`renderMaintBtn` restano nel file (inutilizzati, innocui).

### 33.4 Da sapere / possibili prossimi passi

Se in futuro si volesse che i rigori incidano anche sui **crediti dinamici**, aggiungere i due termini a `_apply_credits_core` (oggi esclusi di proposito). Il grafico usa solo giornate **chiuse**: una giornata con voti ma ancora aperta non compare (scelta voluta, dati stabili).

---

## 34. LOGHI SQUADRA (crest per ogni squadra)

Ogni squadra (= profilo) può avere un **logo/crest** scelto da una raccolta condivisa, esattamente come funzionano gli **avatar** dei giocatori.

**Storage:** nuovo bucket pubblico **`loghi`** (gemello di `avatars`). Contiene i PNG `logo-01.png … logo-25.png` (512×512, angoli arrotondati uniformi, sfondo scuro originale che si sposa col tema). Caricati a mano dal pannello Storage.

**DB (`loghi.sql`, additivo/idempotente):**
- `profiles.logo text` (nome-file del logo scelto; NULL = non ancora scelto).
- `get_team_logos()` → `(manager_id uuid, logo text)` security definer, filtrata `my_league()`, grant `anon, authenticated`. **Non** cambia nessuna RPC esistente (niente DROP a catena): è una funzione nuova.

**Client (`index.html`):**
- Globali `logos=[]` (come `avatars`), `teamLogoBy={}` (manager_id→nome-file). Loader `loadLogos()` (lista bucket) e `loadTeamLogos()` (RPC) chiamati in `afterLogin` (e dopo onboarding/salvataggi).
- Helper `logoImg(name,px)` → box quadrato px×px con `object-fit:contain` (mai tagliato, dimensione uniforme; segnaposto `.tlogo.ph` se manca). `teamLogoHTML(managerId,px)` legge da `teamLogoBy`.
- **Dove compare:** classifica Lega (`lbRowHTML`, tra rank e nome), mini-classifica Home (`renderMini`), classifica di giornata, **pill squadra in Home** (`applyProfile` → `#heroTeam`), **scheda squadra** (`openTeamCard` → `#teamAv`), **striscia sul campo** sopra il verde (`renderCampoTeam` → `#campoTeam`, chiamata in `renderAll`).
- **Scelta logo:** in **Impostazioni → Profilo** (card `#setLogoCard`, griglia `.lggrid`, `renderSetLogo`/`pickSetLogo`, salvato in `setSaveBtn` insieme al resto). In **onboarding** è uno **step del wizard** (vedi sotto). Salvataggio = `update profiles.logo` diretto sul proprio record (RLS lo consente, come per avatar).

**Avviso "novità loghi" (solo lega già esistente):** `maybeShowLogoIntro()` mostra l'overlay `#logoIntro` a chi ha una squadra ma `profile.logo` è NULL: spiega la novità e fa scegliere subito un logo (`saveLogoIntro`). Resta finché non sceglie; "Lo scelgo più tardi" lo rimanda per la sessione (`sessionStorage fc_logo_intro_snooze`). Le **nuove** squadre scelgono il logo in registrazione, quindi non lo vedono mai. Blocco autonomo e rimovibile, accanto all'avviso temporaneo icona.

**Onboarding ora è un wizard a 3 pagine** (prima era un'unica schermata che scrollava): `#obStepMode` (come giochi) → `#obStepChar` (avatar+ruolo+nome, o solo nome per i manager) → `#obStepTeam` (nome squadra + **logo**). Navigazione `obGo(step)`, pallini `#obDots`, `obNextFromChar()` valida lo step 1. Il submit (`#obBtn`) chiama `onboard_join` (invariata) e poi un `update profiles.logo` additivo col logo scelto.

**Immagini:** i 25 crest originali (screenshot 374×348 con sfondo scuro) sono stati uniformati via script Python (`make_logos_final.py`): center-crop quadrato → 512×512 LANCZOS → angoli arrotondati uniformi. **Sfondo NON rimosso**: il cutout automatico rompeva i crest scuri-su-scuro (e il modello ML era irraggiungibile dalla rete sandbox); tenere l'artwork originale dà risultato pulito e coerente sul tema scuro.

### 34.1 Ordine di deploy per i loghi
1. **SQL**: esegui `loghi.sql` nel SQL Editor.
2. **Storage**: crea bucket pubblico `loghi`, carica `logo-01…25.png`.
3. **index.html**: carica la nuova versione (chiavi già dentro).
4. Nessuna modifica a `notify.ts`.

---

## 35. CARD GIOCATORE STILE FUT (mercato)

Le card del mercato (`renderMarket`) non sono più rettangolari ma a **sagoma FUT** (SVG inline).

**Sagoma:** `FC_PATH` (costante JS), viewBox `0 0 200 261`. Estratta da un template immagine, resa simmetrica/centrata, ammorbidita (Chaikin) e allargata, con punta inferiore pulita. **Non è la silhouette EA** (modificata apposta per copyright).

**Layout:** colonna sinistra impilata **ruolo → logo squadra → crediti**; **foto** (avatar) grande spostata a destra, ancorata in basso e sfumata (`xMidYMax meet`, mai schiacciata/tagliata); sotto al centro **nome → forma → "FC"/"CARDS"** (FC grande, CARDS piccolo). Colori app (blu scuro/blu/bianco, accento azzurro).

**Bordo dinamico:** lo stroke (+glow) della card prende il **colore della forma**: `In forma`→verde `#37c98a`, `In calo`→rosso `#ff6b6b`, `Costante`→azzurro `#3d8bff` (`fcFormColor`).

**Logo sulla card (`fcCardLogoUrl`)** — 3 casi: squadra con logo → mostra; **senza squadra** (`owner_id` null, es. benzo) → logo **fisso "a caso"** deterministico (`hashStr(id)%logos.length`); squadra **senza logo scelto** → **vuoto** finché non sceglie.

**Funzioni:** `playerCardSVG(p,s)` costruisce l'SVG (id unici per giocatore); `renderMarket` ora produce `<div class="pcard-fc" onclick="openPlayerStats(id)">` con i badge sovrapposti (👑 capocannoniere, 🚑 infortunato, "Tu"). Dati usati: `p.role`, `p.avatar`, `p.cost` (crediti), `p.owner_id`, `s.forma`. Foto/loghi via `<image href>` (transparenti).

**Verifica render:** generata in locale con `cairosvg` prima dell'implementazione (più iterazioni di forma approvate dall'utente).

### 35.1 Cache-busting immagini (avatar + loghi)
`loadAvatars()` e `loadLogos()` aggiungono `?v=<updated_at>` all'URL pubblico: sostituendo un file con lo **stesso nome** nel bucket, l'app mostra subito la versione nuova (niente cache vecchia di browser/PWA/CDN). Imparato risolvendo "vedo ancora le immagini vecchie dopo l'upload".

### 35.2 DA FARE (prossimo step, richiede il sorgente SQL attuale)
Due statistiche ancora da aggiungere (servono i corpi attuali di `get_team_card`/`get_player_card`):
- squadra → **miglior posizione mai raggiunta** in classifica (oltre all'attuale)
- giocatore → **miglior voto preso in una giornata** (oltre a media + grafico)
Recuperare il sorgente con `select pg_get_functiondef('get_team_card(uuid)'::regprocedure);` (e `get_player_card(bigint)`), poi `CREATE OR REPLACE` additivo.

### 35.3 Stat aggiuntive — FATTE
- **Giocatore · miglior voto in una giornata**: calcolato client-side dal **massimo** dei dati di `get_player_vote_trend` (nessuna modifica SQL). Mostrato nell'header del grafico voti: "media X · **top Y**" (`voteTrendHTML`).
- **Squadra · miglior posizione mai raggiunta**: `best_pos.sql` ridefinisce `get_team_card(uuid)` (CREATE OR REPLACE, stessa firma) aggiungendo `stats.best_pos`, calcolato ricostruendo la classifica cumulativa giornata-per-giornata (`get_standings_md` sommato) e prendendo il rank minimo, in blocco `begin/exception` (fallisce→NULL, scheda intatta). Mostrato in `teamStatsGridHTML` come box "Miglior posizione" (oro), accanto a "Posizione".

---

## 36. Welcome a 3 percorsi + interruttore apertura automatica ON/OFF + fix favicon web + "FantaCalcetto" (C maiuscola)

Sessione tutta **client** (solo `index.html`): **nessun SQL da eseguire**, **nessun PNG nuovo** (`icon-512.png` era già il logo nuovo nel repo). `notify.ts` invariato.

### 36.1 Schermata di benvenuto (`#welcome`) — prima schermata quando NON c'è sessione
Prima del gate email ora c'è una landing "da app vera" con **3 percorsi**: ➕ **Crea la tua lega**, 🔑 **Entra in una lega**, e sotto il link *"Hai già un account in una lega? Accedi"*. Frase principale **"Il fanta del tuo calcetto"** (tutta bianca), sottotitolo *"Crea o entra in una lega. Inizia in un minuto."*. Layout centrato (`.ob-inner.wc-center`), con uno **stacco di 60px** tra il blocco pulsanti e il contenuto sopra (`.wc-center .ob-btn:first-of-type{margin-top:60px}`). Stili `.wc-*` (logo, name, tag, h, sub, login, back, ctx) + `.ob-btn.ghost` (variante chiara).

**Flusso e funzioni (intento → smistamento dopo login):**
- `let authIntent=null;` (`'create' | 'join' | 'login'`).
- `showWelcome()` = entry point quando non c'è sessione (in `boot()` il ramo "no session" ora chiama **showWelcome**, non più `showGate`; idem la rete di sicurezza a 9s). Azzera `authIntent`, nasconde gate/league/onboard, mostra `#welcome`.
- `welcomeGo(intent)` = i 3 bottoni: salva l'intento e va al passo email con `showGate(intent)`.
- `showGate(intent)` ora mostra una **pillola contestuale** `#gateContext` ("Stai creando una lega" / "Stai entrando in una lega" / niente per login) + bottone `‹ Indietro` (`onclick="showWelcome()"`).
- `afterLogin()`: se **profilo assente** chiama `routeNewUser()` invece di `showLeague()` diretto. Nasconde anche `#welcome`.
- `routeNewUser()`: `create`→`showLeague('create')`, `join`→`showLeague('join')`, `login`(o nullo)→`showLeague()` (scelta generica).
- `showLeague(forceMode)`: ora accetta un modo. Lo **slug `?lega=` ha la precedenza** (link invito → join + `resolveLeagueSlug`), altrimenti usa `forceMode || 'choose'`.

**Robustezza (la garanzia anti-bug, chiarita con l'utente):** chi ha la **sessione valida** salta tutta la welcome ed entra **dritto in lega** (la welcome compare SOLO se non c'è sessione: logout, scadenza, dispositivo nuovo, PWA reinstallata). Chi **ha già un profilo**, anche se tocca per sbaglio "Crea" o "Entra", dopo il codice finisce **comunque in lega** (l'intento viene ignorato) → impossibile creare/entrare due volte. Lega #1 invariata.

### 36.2 Apertura automatica: interruttore ON/OFF (sostituisce l'idea "salta giornata")
In Impostazioni → 🤖 **Apertura automatica** ora c'è uno switch **🟢 Attiva / ⏸️ In pausa**. In pausa **nessuna** giornata parte; giorno e ora **restano salvati**.
- **Perché basta lato app (niente SQL):** `open_due_matchdays()` apre solo le leghe con `coalesce(auto_open,false)=true` → in pausa non apre nulla. E `set_league_schedule(p_auto,p_weekday,p_time)` con `p_auto=false` **conserva** `auto_weekday`/`auto_time` (rami `else auto_weekday` / `else auto_time` nel corpo SQL).
- **Funzioni:** `applyAutoOpen(on)` chiama `set_league_schedule` (passa sempre giorno/ora salvati); `saveSchedule()` = `applyAutoOpen(true)`; `setAutoOpen(on)` = lo switch. `renderOpenMode()` riscritta con lo switch in cima + (solo se ON) il selettore giorno/ora.
- **Ordine importante (anti-cron):** spegnendo l'interruttore con una giornata già aperta, l'app **prima** mette in pausa (`auto_open=false`) **poi** offre di annullarla. Se si annulla prima di mettere in pausa, il cron (ogni 10 min) la **riapre** entro pochi minuti perché non esiste più una giornata con quel kickoff.

### 36.3 "Mi dimentico di spegnere e parte una giornata"
Pulsante rinominato **"🗑️ Annulla questa giornata"** (era "Resetta giornata (annulla · per test)") → chiama `reset_matchday(md)` (già esistente: cancella giornata + figli; non avendo `status='closed'`, non ha mai contato in classifica). `resetMatchday()` ora **avvisa**: se `leagueSched.auto_open` è attivo, mettere prima «In pausa», altrimenti il cron riapre entro ~10 min.

### 36.4 Logo/favicon sul web (il tab PC mostrava l'icona vecchia)
Causa = **cache** (verificato: **nessun `favicon.ico`** nel repo). Fix: **cache-busting `?v=3`** su TUTTI i riferimenti icona (link in `<head>`, `manifest`, e gli `<img src="icon-512.png?v=3">` interni all'app) + aggiunto `<link rel="shortcut icon" href="icon-512.png?v=3">`. `icon-512.png` nel repo è **già** il logo nuovo. Dopo deploy: **hard-refresh** (Cmd+Shift+R) o incognito. ⚠️ Nell'anteprima della chat il logo appare **rotto** (percorso relativo, il file non esiste nell'ambiente di anteprima) — è **normale**, sul sito vero si vede.

### 36.5 Capitalizzazione brand
**"FantaCalcetto"** (C maiuscola) ovunque: splash, home/topbar, welcome, gate, onboarding, scelta lega, `<title>`, meta `apple-mobile-web-app-title`, `manifest` (`name`/`short_name`) e fallback JS. Audit nome completato.

### 36.6 File toccati / deploy
Solo `index.html`. Deploy: scarica → (re)incolla chiavi se placeholder → carica su GitHub → hard-refresh per vedere il logo. Niente SQL, niente PNG, `notify.ts` invariato.
