# Fantacalcetto — Guida al progetto (handoff)

> Documento di contesto. Se apri una **nuova chat**, leggi prima questo: spiega cos'è l'app, com'è fatta, dove vive e come si aggiorna. L'assistente deve continuare a **rispondere in italiano** e ricordare che l'utente (Teo) lavora **da pc** e non è uno sviluppatore: vanno dati passi guidati, semplici, uno alla volta.

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

---

## 37. RIFINITURE SCHEDE + PAGELLONE ESTESO + PROFILO A TENDINA + REGOLAMENTO + FORMAZIONE DI GIORNATA A PAGINA INTERA

Due sessioni consecutive, **tutte client (solo `index.html`)**: **nessun SQL**, **nessun PNG nuovo**, `notify.ts` invariato. Le chiavi Supabase sono già dentro il file consegnato (non serve re-incollarle).

### 37.1 Scheda giocatore (bch-page) e scheda squadra

- **Avatar header non più schiacciato**: `.stat-av img` riscritto con `width/height:100%!important`, `max-width/height:none!important`, `object-fit:contain`. Prima `max-height:50px` + `max-width:46px` clampavano in modo indipendente e deformavano l'immagine. Vale per avatar giocatore e logo squadra nell'header.
- **Contenuto centrato** in tutte le caselle: aggiunto `text-align:center` a `.stat-box` (usato solo nelle due schede, verificato).
- **Andamento voti**: rimossa la pillola "media X · top Y" (`.vt-avg`) dall'header del grafico — le caselle *Voto medio* e *Miglior voto* sopra dicono già la stessa cosa. La variabile `best` resta calcolata ma inutilizzata (innocua).
- **Scheda squadra**: casella *Punti* (`tg-hero`) resa più compatta e centrata (flex column, padding ridotto); griglia inferiore `tg-rest` passata da `auto-fit minmax(96px)` (4 strette in fila) a **2 colonne fisse** (2×2 bilanciato).

### 37.2 Pagellone — nuove scene e fix

- **Nuova scena `leaders`** ("I migliori di giornata"): **più gol** (⚽ Bomber), **più assist** (🎯 Assist-man), **muro** (🧤, meno gol presi tra chi era schierato in porta, slot `g1`). Calcolata in `loadRecapExtra` come `ex.leaders={bomber,assistman,wall}` deduplicando per `player_id` (gol/assist sono per-player in `match_stats`, uguali a prescindere da chi schiera). Inserita in `buildRecapCards` dopo `topflop`; `PAG_DUR.leaders=5200`. CSS `.lead-row/.lead-cell/.lead-ic/.lead-av/.lead-nm/.lead-val/.lead-lbl` (avatar con `object-fit:contain`).
- **Verdetto (scena `winner`)**: aggiunti **2º e 3º di giornata** (🥈🥉) e l'ultimo rinominato **"Fanalino di coda"** (🪶) — non più "Cucchiaio di legno". Podio/ultimo calcolati in `loadRecapExtra` via `get_standings_md` → `ex.mdPodium` (top3) e `ex.mdLast`. Guardia: non mostrare il fanalino se coincide col vincitore (lega con 1 squadra). CSS `.vd-list/.vd-row/.vd-medal/.vd-nm/.vd-pt`. Aggiornato anche il testo della scena legacy `verdict` per coerenza. **Nota:** il campo dato dalla RPC resta `d.cucchiaio` (non rinominato lato SQL), cambiata solo l'etichetta UI.
- **BUG classifica risolto**: la scena `standings` non era in `PAG_DUR`, quindi `dur=0` → la barra si riempiva in 0,4s ma **non chiamava mai `recapNext()`** e il pagellone si bloccava lì. Fix: aggiunto `standings:5600` (l'animazione `lbAnimate` dura ~1,8s, poi avanza da sola alla scena `share`).

### 37.3 Carta PNG di condivisione (scena `share`)

- **Avatar non più schiacciati**: `drawAvatar` ora disegna con **aspetto mantenuto** (logica *contain*: scala su lato lungo, centra nel box). Prima forzava `drawImage(...,s,s)` quadrato.
- **Layout righe ridisegnato**: **simbolo a sinistra** (🏆 vincitore, ⭐ MVP, 👟 capocannoniere), testo al centro, **immagine a destra**: nella riga squadra il **logo squadra** (`drawLogo` + `logoBlob` che scarica dal bucket `loghi` come blob, niente tainting canvas), nelle righe giocatore l'**avatar**. Logo vincitore risolto con `winnerLogoName(w)` (per `manager_id`, fallback per `team_name` su `standings` → `teamLogoBy`).

### 37.4 Impostazioni → Profilo: avatar e loghi a tendina

Avatar e Logo squadra ora mostrano **solo la scelta attuale** (miniatura `renderAvCur`/`renderLogoCur`) con bottone **"Cambia ▾"**; la griglia (`#setGrid`/`#setLogoGrid`, classe `disc-body`) è nascosta di default e si espande con `toggleDisc('av'|'logo')`. All'apertura della pagina si richiudono sempre (`collapseDisc`). Rimosso il vecchio `#setLogoPreview` (ob-preview grande). CSS `.disc-head/.disc-cur/.disc-act/.disc-chev`. **Attenzione naming:** le funzioni `renderAvCur/renderLogoCur` sono volutamente diverse dagli id `setAvCur/setLogoCur` per evitare il clash funzione↔global-da-id del browser.

### 37.5 Regolamento

- Voce "In porta" **divisa in due righe** uguali alle altre (emoji · nome · numero): **🧤 Clean Sheet +3** e **🔴 Gol subito −1** (il malus portiere è −1 per gol; emoji coerenti con quelle già usate sul campo).
- **Rimosse tutte le descrizioni** `<small>` dalle righe del regolamento (es. "la tua vera squadra di calcetto", "scelto da te", "raddoppia solo il voto"…). Ora ogni riga è solo emoji + nome + punteggio.

### 37.6 Formazione di giornata → pagina intera (non più bottom-sheet)

`openTeamLineup` non usa più il bottom-sheet condiviso `#sheet` (che lasciava vedere/scrollare lo sfondo). Ora scrive in una **pagina overlay dedicata** `#teamLineupPage` (stile `bch-page`: barra con `‹ Indietro`, `#tlpTitle/#tlpHint/#tlpList`) aperta/chiusa da `openTeamLineupPage()/closeTeamLineupPage()`. Lo swipe campo↔punti (`.tl-swipe`, CSS scroll-snap, nessun hook JS) funziona identico. Il bottom-sheet `#sheet` resta per gli altri usi (apri/modifica giornata, scelta giocatore, azioni giocatore, modifica giocatore).

### 37.7 Deploy

Solo `index.html`. Scarica → carica su GitHub come `index.html` → Vercel pubblica. Niente SQL, niente PNG, `notify.ts` invariato.

## 38. Sessione ritocchi estetici (mercato · formazioni · bacheca)

Solo `index.html`. Niente SQL, `notify.ts` invariato. Le RPC `get_player_card`/`get_team_card` sono **intatte**: cambia solo il *render* lato client. (I valori puramente visivi — px avatar, altezza campo, coordinate `MODULES`, padding, posizioni targhette — **non** sono elencati qui: cambiano spesso, si leggono dal sorgente.)

### 38.1 Bacheca — banner headline a due colonne + prossimo traguardo nelle stats
`bachecaHTML` ora usa `card.next` (il **prossimo traguardo**, prima sfruttato **solo in Home**) anche nelle schede stats giocatore/squadra. Il banner `.bch-head` è diviso in due: a sinistra **il simbolo attuale** (`headline`: icona + testo + sub), a destra **"Prossimo"** con icona, etichetta e **barra di progresso** `now/tot`. Nuova funzione **`nextIcon(next)`**: usa `next.icon` se presente, altrimenti mappa per `key`/`label` (cecchino→🎯, profeta→🔮, rifinitore→🅰️, ecc.), fallback 🎯. Se `card.next` è assente → classe `.solo` (simbolo a tutta larghezza). I due occhielli **"Il tuo simbolo" / "Prossimo"** sono **uniformati** (stesso formato) e allineati sulla stessa riga (colonne `justify-content:flex-start`).

### 38.2 "Da manager" tolto dalla scheda giocatore
`openPlayerStats` ora chiama `bachecaHTML(card,{includeManager:false})` (era `true`): i badge manager **non** compaiono più nella scheda **giocatore** (erano un doppione — stanno già nella scheda **squadra**, come titoli/traguardi propri del manager). La RPC continua a restituire `card.manager`, semplicemente non viene reso lì. Il blocco `.bch-mgr`/`.bch-chip` resta in codice ma di fatto **inutilizzato**.

### 38.3 Titoli come righe (niente chip-scatola)
La sezione **Titoli** non usa più i chip `.bch-chip` (pillole con tinta) ma le stesse **righe** dei Traguardi (`.bch-badge`: medaglia + nome + sottotitolo «N° · Stagione N»). Medaglia per posizione: 🥇 titolo, 🥈/🥉 podio. `.bch-titles`/`.bch-chip` restano in CSS ma inutilizzati.

### 38.4 Andamento voti senza riquadro
`.vtrend` de-boxato (`background/border/box-shadow:none`, `padding:0`): restano **titolo + grafico SVG** appoggiati sullo sfondo, come le altre sezioni.

### 38.5 Card infortunato — oscura solo l'illustrazione, targhetta in risalto
Prima `.pcard-fc.absent{opacity:.45}` smorzava **tutta** la card (targhette incluse). Ora si oscura **solo l'SVG** (`.pcard-fc.absent svg{opacity:.5;filter:saturate(.8)}`): le targhette restano in primo piano e la **🚑 Infortunato** (`.fc-tag.red`) risalta (rosso acceso + alone). Vale anche per i non-presenti a giornata aperta (stessa classe `absent`, assegnata da `dim` in `renderMarket`).

### 38.6 Box stats squadra — cifra centrata anche col "°"
In `teamStatsGridHTML` la posizione è resa `N<span class="deg">°</span>`; `.stat-box .v` è `inline-block;position:relative` e `.deg` è in `position:absolute;left:100%` (apice **fuori dal flusso**). Così è la **cifra** a restare centrata e allineata con i numeri degli altri box: il "°" non la sposta più.

### 38.7 Targhette mercato dentro lo scudo (riassunto visivo)
Le targhette (`👑 Capocannoniere`/`🅰️ Assist-man`/`🚑 Infortunato` a sinistra, `Tu` a destra) sono un overlay `.fc-top` **dentro** la sagoma della card (lo scudo è appuntito in cima: la fascia larga inizia ~13–16% dell'altezza). Testo **senza box**. L'avatar nell'SVG è stato **abbassato** (`<image>` a `y=150 h=320`, clip a `y=150`) per liberare spazio in alto; colonna ruolo/logo/crediti ribilanciata. (Valori esatti nel sorgente.)

### 38.8 Deploy
Solo `index.html`. Niente SQL, `notify.ts` invariato, chiavi già dentro.

## 39. Sessione — VICE-ADMIN + redesign login/email + bacheca titoli + notifiche riscritte + rifiniture

Sessione ampia. Consegnati: `vice_admin.sql` (eseguito), `notify.ts` (ri-deploy dalla dashboard Edge Functions) e `index.html`. **Nota di processo:** a metà sessione il file di lavoro aveva perso due modifiche vecchie (redesign welcome + grafico voti da 1 presenza); sono state **re-incluse**. L'`index.html` corrente contiene TUTTO quanto sotto.

### 39.1 VICE-ADMIN ("operatore di giornata") — IMPLEMENTATO
Prima solo progettato, ora attivo. Decisioni: **più vici per lega**; il vice fa **solo partite e giornate** (non le regole); **reset giornata incluso**; **vede la password d'invito**. Nominare/rimuovere un vice è **solo del proprietario**; un vice non può mai scavalcare il proprietario.

**SQL (`vice_admin.sql`, già eseguito):**
- `vice_admins(league_id, user_id, added_by, created_at, PK(league_id,user_id))`, RLS on, policy `va_read` (i membri leggono); scritture solo via funzioni security definer.
- `is_operator()` = proprietario (`leagues.admin_id=auth.uid()`) **OPPURE** vice della propria lega. `is_admin()` resta = solo proprietario (invariata).
- Ri-gate da `is_admin()` a `is_operator()` delle **operazioni di giornata**: policy `match_stats "stats admin"`, `matchday_players "mp write"`, `matchdays "md admin"`, `extra_voters "ev_write"`, e funzione `reset_matchday`. Le **regole** (`set_gk_mode/set_presence_mode/set_league_schedule/set_credit_mode`), la **manutenzione** (`app_state`) e il **listone** (`players`) restano su `is_admin()`.
- `get_league_admin_info()` ora usa `is_operator()` → il vice vede link+password d'invito.
- `set_vice_admin(p_user)` / `remove_vice_admin(p_user)`: **solo proprietario**; valida target membro della lega e non proprietario; `on conflict do nothing`.
- Letture: `get_my_role()` → `(is_owner, is_vice, can_operate)`; `list_league_members()` → membri con flag `is_vice`/`is_owner`.
- `alter table leagues alter column presence_self set default true` (vedi 39.5).

**Client (`index.html`):**
- Global `opRole={is_owner,is_vice,can_operate}` + `canOp()` = `opRole.can_operate || profile.is_admin` (il proprietario è **sempre** operatore, anche se la RPC fallisce). Popolato da `get_my_role()` dentro `loadProfile()` (`loadMyRole()`).
- Azioni/UI di **giornata** gated su `canOp()` (non più `profile.is_admin`): pannello Bonus/Malus (`adminCard`, `openLiveStats`), card Giornata (`mdCard`), Chi gioca (`presCard` + `!presenceSelf`), Voto soli-manager (`voterCard`), pulsante apri giornata (`renderLiveOpenBtn`), auto-chiusura client, riga "Area amministratore" (`adminRow`), voto sempre concesso.
- UI **solo proprietario** su `profile.is_admin`: Modalità portiere (`gkCard`), Presenze modalità (`presModeCard`), Stagione (`seasonCard`), Gestione giocatori (`manageCard`), Sondaggio valori (`creditCard`), Manutenzione (`maintCard`), + nuova card **Vice-admin** (`viceCard`). `gkCard`/`presModeCard`/`seasonCard` hanno ora un id e sono **nascosti ai non-proprietari**.
- Card **Vice-admin** (pagina Lega, solo proprietario): `renderVices()` usa `list_league_members()` e mostra i membri come chip; `toggleVice(uid,isVice)` chiama `set_vice_admin`/`remove_vice_admin`.

**`notify.ts`:** l'invio push immediato (ex "solo admin") accetta anche il **vice**: dopo il check `prof.is_admin`, se falso controlla `vice_admins` per `(league_id,user_id)`. Così l'apertura/chiusura **manuale** di un vice manda comunque la push (con apertura/chiusura **automatica** le push partono già lato server).

### 39.2 Notifiche push — testi riscritti (`notify.ts`)
`{Giornata}` = label dinamica.
1. Apertura mod. presenze → `{Giornata}: Sondaggio aperto! Vota la presenza ⚽` / "Fai sapere se sarai presente nella prossima giornata."
2. Apertura mod. admin → `{Giornata} aperta! ⚽` / "Schiera la tua formazione prima del fischio d'inizio." (invariata)
3. Presenze chiuse → `{Giornata}: Presenze chiuse. Schiera ora la tua formazione! 📋` / "Scegli i tuoi 5 campioni!"
4. Promemoria presenze 2h → `{Giornata}: Vota la presenza! ⚽` / "Il sondaggio presenze chiude tra 2h. Segna la presenza!"
5. Promemoria formazioni 8h → `{Giornata}: Schiera la formazione! 📋` / "Mancano 8h alla chiusura delle formazioni. Schiera ora i tuoi campioni!"
6. Ultima ora 1h → `{Giornata}: ⏰ Ultima ora per le formazioni` / "Manca 1h alla chiusura delle formazioni. Schierala subito!"
7. Giornata chiusa → `{Giornata} chiusa 🏁` / "Scopri com'è andata la tua squadra e la classifica." (invariata)
NB: i testi di apertura/chiusura **manuale** vivono anche in `index.html` (pushNotify) e vanno tenuti allineati.

### 39.3 Welcome (`#welcome`) e pagina email (`#gate`) — redesign
- **Welcome:** tre blocchi — `.wc-top` (logo + FantaCalcetto + "IL TUO CAMPIONATO"), `.wc-mid` (h1 + sottotitolo), `.wc-actions` (pulsanti + Accedi). `#welcome{display:flex;flex-direction:column}` e `.wc-center{flex:1;min-height:0;justify-content:flex-start}` → riempie lo schermo in modo affidabile (le altezze in `%`/`dvh` non si calcolano bene su iPhone; `min-height:0` toglie l'overshoot che rendeva la pagina scrollabile). `.wc-mid{margin-top:36px}` avvicina il claim al brand; `.wc-actions{margin-top:auto}` spinge i pulsanti in fondo. Titolo e sottotitolo su **una riga** ciascuno (h1 24px, sub 13.5px, niente `<br>`).
- **Email (`#gate`):** due zone — `.gate-top` (brand; riga `.gate-bar` con "‹ Indietro" a sx e **pillola** a dx sulla stessa riga; occhiello "Accedi" + h1 "Entra con la tua email" + descrizione) e `.gate-bottom` (input email + "Inviami il codice →"). `#gate{display:flex;flex-direction:column}` + `.gate-center{flex:1;min-height:0;justify-content:space-between}`. **Crea e Entra sono la STESSA pagina**: cambia solo la pillola (testo in `showGate`).
- **Pillola** (`.wc-ctx`): più visibile (bg `rgba(63,139,255,.22)`, bordo `rgba(127,176,255,.55)`, testo `#dbe8ff`, ombra tenue). Testo create: **"➕ Stai creando una nuova lega"**; join: "🔑 Stai entrando in una lega".
- **Descrizione** email: "Inserisci la tua email per accedere." + a capo "Nessuna password richiesta." (`.gate-desc`).

### 39.4 Bacheca — Titoli: indice stagione sopra + spiegazione sotto
Righe Titoli (`.bch-badge`) con **occhiello stagione** (`.bb-eye`, es. "Stagione 1", con eventuale posizione podio) **sopra** il nome, e come sottotitolo una **spiegazione**. Nuova `titleDesc(key)` (per **chiave**), coi criteri reali di `get_player_card`:
- `pallone` "Pallone d'oro" → "Miglior media voto della stagione" (1° per **voto medio** assoluto; gate presenze ≥30% giornate chiuse / min 4)
- `re_att` "Re dell'attacco" → "…tra gli attaccanti"; `diga` "Diga" (DIF) → "…tra i difensori"; `saracinesca` (POR, solo gk fisso) → "…tra i portieri"
- `podio_att/dif/por` "Sul podio · …" → "Tra i migliori attaccanti/difensori/portieri della stagione"
- `capocannoniere` → "Più gol nella stagione"; `mago_assist` "Mago degli assist" → "Più assist nella stagione"
I **Traguardi** (player e manager) restano coperti da `badgeDesc`.

### 39.5 Default nuove leghe + grafico voti + tendine impostazioni + conferme
- **Default wizard** (`setupRules`): apertura = **automatica** (`open:'auto'`; il proprietario sceglie giorno/ora) e presenze = **giocatori** (`pres:'players'`). Lato DB `leagues.presence_self` default **true**.
- **Grafico andamento voti:** visibile **da 1 presenza** (gate `if(!pts.length)return`; con 1 punto `X=padL`, a sinistra come primo voto, la media tratteggiata ci passa).
- **Impostazioni admin a tendina SENZA riquadro interno:** gli accordion restano (tap per aprire) ma tolto il `.set-card` dentro `.acc-body` (contenuto diretto, `.acc.open>.acc-body{padding:12px 6px 2px}`).
- **"Esci dall'account"** in **fondo** al menu Impostazioni (`#setMenu.on` flex column + logout `margin-top:auto`) e ora **chiede conferma**. Le altre azioni distruttive (chiudi giornata/stagione, elimina giocatore, cambio modulo, salva dati partita, chiudi sondaggio) avevano già conferma.

### 39.6 Rifiniture pagellone
- Fanalino di coda: emoji **🪶 → 🙅🏻‍♂️** (entrambe le occorrenze `pag-spoon`).
- Titolo "**Pagellone di giornata**" (g minuscola); sottotitolo "**Voti**, bonus e pagelle di tutti" (V maiuscola).

### 39.7 Deploy
`vice_admin.sql` PRIMA (fatto), poi `notify.ts` dalla dashboard Edge Functions, poi `index.html` su GitHub. Chiavi già dentro `index.html` (nessun re-incolla se si parte dai file consegnati).

---

## 40. «Apri subito la giornata» (skip_poll) + fix schermo iPhone non riempito al lancio

> Dove in conflitto con sezioni precedenti, **vale questa**. File: `apri_subito.sql` (nuovo) + `index.html`.
> **Ordine di deploy:** `apri_subito.sql` **PRIMA**, poi `index.html`. Chiavi già dentro `index.html` (nessun re-incolla partendo dal file consegnato). `notify.ts` **non** si tocca.

### 40.1 Perché
Caso reale: si gioca **stasera** ma la certezza arriva **stamattina**. L'apertura automatica (72h prima) non fa in tempo, e comunque il ciclo presenze (sondaggio fino a K−36h, formazioni bloccate fino ad allora) non ci sta dentro. Serve: **apro adesso, si schiera adesso, le presenze le metto io a mano.**

### 40.2 `apri_subito.sql` — una sola colonna
```sql
alter table public.matchdays
  add column if not exists skip_poll boolean not null default false;
```
Additiva e idempotente. **Nessuna policy da toccare**: la write su `matchdays` è la `"md admin"` (`is_operator()`) già esistente e vale per tutte le colonne.
- `skip_poll=false` (default) → ciclo normale: apertura auto a K−72h, sondaggio presenze fino a K−36h, poi formazioni.
- `skip_poll=true` → giornata aperta col pulsante: **niente sondaggio presenze**, **formazioni aperte da subito**, presenze inserite a mano dall'admin.

### 40.3 Client — il pulsante
Card admin **Partita → Giornata** (`renderMatchday` → `#mdActions`), riscritta:
- **Nessuna giornata aperta** (`!currentMd || status==='closed'`) → **`⚡ Apri subito la giornata`** (`openNowMatchday()`) + riga di hint (`#openNowHint`, `openNowHintText()`/`refreshOpenNowHint()`) che dice quale kickoff userà.
- **Giornata in corso** → resta solo `🕑 Modifica orario partita`.
- `🗑️ Annulla questa giornata` invariato (se esiste una giornata).
- **RIMOSSO** il pulsante *«Chiudi la giornata adesso»*: la chiusura è automatica (fine finestra voti / tutti hanno votato), altrimenti si annulla. La funzione `closeMatchday()` resta nel file **inutilizzata** (innocua); `doCloseMatchday(true)` continua a servire l'auto-chiusura.

`openNowMatchday()`: kickoff = `nextWeeklyKickoffLocal(schedDraft.weekday, schedDraft.time)` (il **prossimo** giorno/ora della programmazione: se oggi è lunedì e la programmazione è Lun 22:00 → stasera 22:00). Conferma con kickoff + "presenze a mano" + "formazioni subito". Se la programmazione non c'è ancora, ripiega su `openMatchdaySheet(true)` (data/ora a mano, **sempre** senza sondaggio).

### 40.4 Client — come si spegne il sondaggio
Tutto passa da **un solo punto**, `mdTimes()`:
```js
const pc = md.skip_poll ? 0 : (k - PRESENCE_CLOSE_BEFORE);
```
`presenceClose` nel passato (0, **non** `null`: `null` significa "sondaggio sempre aperto" nel fallback senza kickoff!) → a cascata si comportano bene `presencePollOpen()`, `computeLock()` (niente `presPhase` → formazioni aperte), `phaseLabel()`, il countdown e `renderHomePresence()` (nessuna card "Ci sei?" ai giocatori).
La card admin **«Chi gioca questa giornata»** compare comunque (override admin a giornata aperta anche in modalità giocatori) → è lì che si segnano i presenti.

### 40.5 Client — creazione della giornata
`createMatchday(kickoffISO, skipPoll)` (ri-vivo: **non** è più "morto" come diceva §27.5; la label resta comunque del trigger `stamp_season`) e `confirmMatchday(skipPoll)` / `openMatchdaySheet(now)`.
Con `skipPoll` la riga inserita porta anche `presence_remind_sent:true` e `lineup_open_sent:true` → il cron **non** manda fuori tempo le due push del ciclo presenze ("vota la presenza", "presenze chiuse, schiera"). Restano il push di apertura (client `pushNotify`) e il promemoria formazioni a chi non ha schierato.
**Degrado sicuro:** se `apri_subito.sql` non è stato eseguito, l'insert fallisce sulla colonna mancante → si ritenta **senza** `skip_poll` e appare il toast «Aperta, ma manca skip_poll: esegui apri_subito.sql» (giornata comunque aperta, ma col sondaggio normale). In lettura `md.skip_poll` `undefined` = falsy = comportamento normale.

### 40.6 Fix — schermo non riempito al lancio (iPhone/PWA)
**Sintomo:** all'avvio la barra in basso stava **troppo in alto**, con una fascia vuota sotto; scrollando una volta si assestava e restava a posto.
**Causa:** il guscio `.app`/`.overlay` aveva un'**altezza calcolata** (`height:var(--app-h)`, con `--app-h` scritta da JS leggendo `visualViewport.height`). Su iOS PWA quel valore al lancio è **sottostimato** (~793 invece di 852: gli stessi numeri già misurati in §—LAYOUT_FULLSCREEN) e si assesta solo dopo uno scroll.
**Soluzione:** **niente altezza**, ancoraggio ai bordi veri del viewport:
```css
.app{position:fixed;top:0;bottom:0;left:0;right:0;margin:0 auto;max-width:var(--maxw);display:flex;flex-direction:column}
.overlay{position:fixed;top:0;bottom:0;left:0;right:0;...}
```
Rimosso **tutto** lo script che misurava il viewport (`--app-h`, `settle()`, il "freeze" sul focus dei campi). `max-width` + `margin:0 auto` con `left:0;right:0` continua a centrare il guscio.
**Regola:** su iOS-PWA `position:fixed` con **top+bottom** è affidabile (è lo stesso ancoraggio della vecchia `.nav{bottom:0}` che funzionava); `height:100dvh`, `innerHeight` e `visualViewport.height` **no**. Non misurare mai l'altezza in JS.

### 40.7 Deploy
1. `apri_subito.sql` in Supabase → SQL Editor.
2. `index.html` su GitHub (Vercel deploya da solo).
3. Test su iPhone: avvio da app chiusa (barra subito in fondo), rientro da background, rotazione, tastiera aperta; poi **Apri subito** → segna i presenti → schiera.

---

## 41. Link d'invito diretto, riquadro «crea» rosso, avatar interi nel Pagellone, RECAP DI FINE STAGIONE

> Dove in conflitto con sezioni precedenti, **vale questa**. File: `stagione_recap.sql` (nuovo) + `notify.ts` + `index.html`.
> **Ordine di deploy obbligatorio:** `stagione_recap.sql` **PRIMA** → `notify.ts` (dashboard Edge Functions) → `index.html` su GitHub. Invertendo 1 e 3 il client chiama RPC che non esistono ancora. Chiavi già dentro `index.html`. `sw.js` e `admin.html` **non** toccati.

### 41.1 Riquadro «Stai creando una nuova lega» → ROSSO

Il `.ctx-box` del gate era **blu** per «crea» e verde per «entra»: due percorsi opposti col blu che è anche l'accento generale dell'app, quindi poco distinguibile. Ora «crea» usa `var(--red)` (#ff5d6b) con lo **stesso identico trattamento** del verde (sfondo sfumato, bordo, alone, iconcina). «Entra» resta verde.

### 41.2 Link d'invito → dritto alla password

Prima: `?lega=slug` veniva letto **solo** in `showLeague()`, cioè dopo il login; l'utente passava comunque dalla welcome e sceglieva a mano «crea o entra».

Adesso:

- **`boot()`** — niente sessione + slug presente → `resolveInvite()` risolve il nome via `league_by_slug`, poi `authIntent='join'` e `showGate('join')`: la **welcome viene saltata**.
- **`showGate('join')`** — il riquadro verde scrive il nome vero: «Stai entrando in **La Fossa di Lissone**» invece del generico «una lega esistente».
- **Dopo il login** — `showLeague()` va in join con il nome **già compilato e bloccato**: `lgLockInvite()` mette `lgSearch.readOnly`, cambia `#lgSearchLab` in «Lega dell'invito», riscrive `#lgDesc` («Sei stato invitato in «X»…») e trasforma `#lgBack` in «← Entra in un'altra lega» (`lgInviteBack()` → azzera `inviteLeague`, `lgUnlockInvite()`, `lgMode('choose')`). Resta **solo la password** da scrivere; `lgSelect` focalizza già `#lgPwd`.
- **Via di fuga** — `showLeague(forceMode)`: se `forceMode==='create'` l'invito **non** forza il join. Prima lo slug vinceva sempre e chi voleva creare restava intrappolato.
- **Senza link** — flusso invariato: si scrive il nome e `find_leagues` suggerisce le leghe mentre si digita.

**Stato:** globale `inviteLeague` + `async resolveInvite()` (risolve **una volta** e tiene il risultato). Sostituisce `resolveLeagueSlug(slug)`, **rimossa** (nessun riferimento residuo).

**Nota:** `emailRedirectTo` è `origin+pathname` (senza query), ma non serve: il codice OTP si inserisce in pagina, la URL non cambia mai e `?lega=` sopravvive.

### 41.3 Pagellone — avatar mai tagliati

**Sintomo:** nelle storie gli avatar venivano rifilati sopra e sotto.
**Causa:** `.pag-av img{width:88%;height:auto}` dentro un riquadro **quadrato** con `overflow:hidden`: gli avatar più alti che larghi sfondavano.
**Fix:**

```css
.pag-av img{width:88%!important;height:auto!important;
  max-width:88%!important;max-height:88%!important;object-fit:contain!important}
```

L'immagine si **rimpicciolisce** per stare intera. Vale per tutte le misure (`.pag-av`, `.huge`, `.sm`). La card PNG non era interessata: `drawAvatar`/`drawLogo` facevano già il *contain* a mano.

**Regola di progetto:** gli avatar si mostrano **sempre interi** (contain), mai ritagliati (cover).

### 41.4 RECAP DI FINE STAGIONE — cos'è

Un secondo «pagellone», ma dell'**annata**: ~22 scene a storie che partono da sole alla prima apertura dopo la chiusura della stagione, più una push a tutta la lega.

**Non è un motore nuovo.** Riusa per intero quello del Pagellone (overlay `#pag`, `buildProgress`, `showRecapCard`, tap/hold/swipe, coriandoli, `countUp`, `skeletonRows`, `lbRowHTML`). L'interruttore è la globale **`recapMode`** (`'md'` | `'season'`): `showRecapCard` sceglie `renderSeasonHTML(card)` invece di `renderRecapHTML(card, recapData)`. `closeRecap()` e `openRecap()` rimettono `recapMode='md'`.

**Design (skill `mobile-app-ui-design`):** il Pagellone di giornata resta **blu**, la stagione è **oro** — due eventi diversi, due accenti diversi. Un solo picco emotivo: la scena **Campione** (oro + logo + coriandoli + vibrazione lunga). La chiusura è la card PNG condivisibile. Griglia da 8px, ombre tinte, avatar interi.

### 41.5 Il recap è CONGELATO (e perché)

Si calcola **una volta sola** e si salva in `season_recaps(season_id pk, league_id, data jsonb, created_at)`.

- Ricalcolare fino a 38 giornate a ogni apertura sarebbe lento.
- A stagione chiusa i numeri **non cambiano più**.
- Diventa un **albo d'oro** consultabile per sempre.

Se si correggono voti/bonus a stagione già chiusa serve `rebuild_season_recap` (bottone admin in Impostazioni → stagione).

**Niente trigger sulla chiusura**: build **lazy** alla prima `get_season_recap`. Motivo: `get_standings_md` filtra per `my_league()` (quindi `auth.uid()`), va chiamata nel contesto di un membro della lega; un trigger dentro `close_season` funzionerebbe solo per l'admin e, in caso di errore, farebbe fallire la chiusura stessa.

### 41.6 `stagione_recap.sql` — struttura

Additivo e idempotente, non tocca tabelle/trigger/funzioni esistenti.

**Temp table** (tutte `on commit drop`):

- `_sr_md` — classifica di **ogni** giornata chiusa via `lateral get_standings_md(m.id)`, più il flag `played` (= quel manager ha schierato).
- `_sr_mvp` — MVP effettivo di ogni giornata, **stessa regola** di `get_standings_md` (più nomination, tie-break per id).
- `_sr_hist` — classifica **cumulativa progressiva** → `leader_days`, `best_pos`, sorpassi.
- `_sr_pl` — statistiche stagionali per giocatore (presenze, gol, assist, autogol, media voto, MVP, volte schierato, giornate da portiere e gol subiti).

**SQL DINAMICO — non toglierlo.** Ogni query che tocca una temp table gira dentro `execute $q$…$q$` con parametri `USING`. In plpgsql statico il piano cachato punta alla **vecchia** temp table e dalla seconda chiamata nella stessa sessione arriva `relation ... does not exist`. Dollar-quote annidati: `$fn$` per il corpo funzione, `$q$` per le query interne.

**Scoping lega.** `v_league` si prende da `seasons.league_id`; `_sr_pl` filtra `players` per `league_id`. Le funzioni sono `security definer` (girano da proprietario → **RLS bypassata**), quindi il filtro lega va messo **a mano**. `get_standings_md` invece si filtra da sola con `my_league()`.

**Punteggio: NON duplicato.** La formula di `scoreOf`/`get_standings_md` non è stata replicata. Il «fedelissimo» riporta **volte schierato + gol/assist**, non «punti portati», proprio per non rischiare una divergenza. Unica eccezione consapevole: *Mister Fortuna* somma l'esito (V=+2/S=−1), pezzo isolato e stabile.

### 41.7 RPC nuove

| funzione | cosa fa |
|---|---|
| `build_season_recap(p_season)` | **interna** (`revoke` da public/anon). Ritorna il jsonb completo: globale + `managers` + `players`. |
| `get_season_recap(p_season default null)` | pubblica. `null` = ultima stagione **chiusa** della propria lega. Legge la cache; se manca chiama build e la scrive. Ritorna il globale **senza** `managers`/`players` + `me_manager_id`, `me_player_id`, `mine`, `me_player`: così non si scarica la stagione altrui. |
| `get_last_closed_season()` | leggera: `(id, number, name, ended_at)`. Chiamata a ogni `loadSeason()` → `lastClosedSeason`. |
| `rebuild_season_recap(p_season)` | (admin) ricalcola e sovrascrive la cache. |

### 41.8 Notifica di fine stagione

Nuova colonna **`seasons.recap_notified`** (bool, default false).

`notify.ts` → **`runSeasonRecap()`** nel blocco cron: prende le `seasons` con `status='closed'` e `recap_notified=false`, manda `sendAll('Stagione N archiviata 🏆', url '/?srecap=<id>')` alla lega, poi alza il flag. Copre **sia** la chiusura a mano **sia** l'auto-chiusura alle 38 giornate. Ritardo massimo 10 minuti (cron `*/10`).

**Niente push retroattive:** l'SQL fa `update seasons set recap_notified=true where status='closed'` in installazione. Lato client stessa idea col flag `fc_srecap_init`: alla prima apertura dopo il deploy le stagioni già chiuse vengono marcate come viste (il recap resta comunque raggiungibile dall'Albo d'oro).

### 41.9 Client — dove si vede

- **Automatico**: `maybeShowSeasonRecap()`, una volta sola (`localStorage fc_srecap_seen_<season_id>`, stesso schema del Pagellone).
- **Precedenza**: in `afterLogin` `?srecap` batte `?recap`; senza deep-link `maybeShowSeasonRecap().then(shown => if(!shown) maybeShowRecap())` → **la fine stagione batte la fine giornata**.
- **`lastClosedSeason`**: globale nuova, caricata in `loadSeason()`. **Separata da `currentSeason`**: appena l'admin apre la stagione nuova `currentSeason` torna «aperta», ma il recap della precedente deve restare raggiungibile.
- **Albo d'oro**: nuova riga in Home sotto il Pagellone (`#homeSeasonWrap`, `.pag-open-btn.season`, «Rivivi la Stagione N»), da `renderSeasonRecapButton()` chiamata da `loadSeason` e `renderAll`. Visibile solo se esiste una stagione chiusa.
- **Admin**: in `renderSeasonAdmin` bottone «🔄 Ricalcola il recap della Stagione N» → `rebuildSeasonRecap()`.

### 41.10 Le scene

`scover, snumbers, srecords, syou, spath, sloyal, scaptain, smodule, splayer, stwin, schamp, spodium, sawards1, sawards2, swanted, sjump, sduel, striples, sfun, spalmares, sfinal, sshare`.

`buildSeasonCards(d)` le include **solo se il dato c'è**: una lega con 1 sola squadra + un solo-manager senza personaggio degrada a **6 scene** senza rompere niente (testato con dati finti su tutte le scene).

**Pezzi notevoli:**

- **`spath` — la parabola**: `seasonPathSVG(path, teams)`, SVG puro, nessuna libreria. Asse Y **invertito** (1º in alto, è così che si legge una classifica), area sfumata + linea + pallini, ultimo pallino oro. `path` arriva già pronto dall'SQL (una voce per giornata: `label`, `rank`, `pts`).
- **`spalmares` — il tuo palmarès**: `seasonPalmares(d)` raccoglie i premi vinti da chi guarda. `sIsMe(who)` confronta `who.player_id` con `seasonData.me_player_id` e tinge di blu (`.pag-awd-row.me`) la riga del premio vinto dall'utente anche nelle scene dei premi.
- **`sshare` — la card PNG**: `buildSeasonShareCard()`/`prepSeasonShare()`/`shareSeason()`, stessa impalcatura di `buildShareCard` ma 3 blocchi (La mia squadra col logo, Le mie cifre con avatar, Campione col logo), file `stagione-N.png`. **NB:** `mine` non contiene `manager_id` (tolto dall'SQL con `- 'manager_id'`) → si usa `d.me_manager_id`.

### 41.11 Premi e soglie

Rinominato su richiesta: **«Pallone di piombo» → «Il migliore (degli scarsi)» 🫠**. Sta nella scena `sfun` insieme ad **Autogol d'autore** e **Mister Fortuna** (chi ha raccolto più punti dall'esito della squadra vera invece che dalle prestazioni). Per toglierli: cancellare la riga `{t:'sfun'}` in `buildSeasonCards`.

**Gate presenze** (stessa filosofia dei Titoli della Bacheca, così nessuno vince per caso):

- Pallone d'oro e Il migliore (degli scarsi): `pres >= greatest(4, ceil(md_count*0.30))`.
- Saracinesca: `gk_mds >= greatest(2, ceil(md_count*0.20))`.

La card lo dice esplicitamente all'utente.

### 41.12 Casi limite gestiti

0 giornate chiuse → `{empty:true}`, il client non apre nulla. 1 sola squadra → niente gap/duello/podio/cucchiaio. Solo-manager senza personaggio → `me_player` null, scene giocatore saltate. Nessun voto → `vm` null, premi da media assenti.

### 41.13 Deploy e collaudo

1. `stagione_recap.sql` in Supabase → SQL Editor.
2. `notify.ts` dalla dashboard Edge Functions. **Mai su GitHub** (contiene `VAPID_PRIVATE` e `CRON_SECRET`); «Verify JWT» resta **disattivato**.
3. `index.html` su GitHub (Vercel auto-deploy).

**Test:** chiudere la stagione → ricaricare (il recap parte da solo) → entro 10 minuti arriva la push → riaprirlo dalla riga **Albo d'oro** in Home. La **prima** apertura è più lenta (build), le successive istantanee. Controllare la parabola (1º in alto, ultimo pallino oro) e che nella card PNG i loghi escano interi.

---

## 42. SESSIONE 42 — Icone PWA, chiusura giornata, fix recap, restyling storie, SELETTORE STAGIONE

Sessione lunga, cinque filoni: due bug bloccanti, un blocco di fix estetici sul recap di stagione, il selettore di stagione (la novità funzionale vera) e le gesture native.

### 42.1 Icona PWA — perché sulla Home usciva una «F»

Due cause sommate:

1. `apple-touch-icon` puntava a `icon-180.png`, file **assente/404** sul dominio. iOS ripiega su una lettera generata dal nome del sito.
2. Il manifest era un **`data:` URI**. Dentro un data URI gli URL relativi (`icon-512.png`) **non si risolvono**: la base è il data URI stesso, non il sito. Per il browser il manifest era quindi senza icone valide.

**Fix:** `apple-touch-icon` → `icon-512.png?v=4` (file che esiste di sicuro, iOS la riscala da sé) e manifest spostato in un **file vero**, `manifest.webmanifest`, con percorsi assoluti (`/icon-512.png?v=4`), `scope`, `start_url` e la variante `purpose:"maskable"` per Android.

**Regola di progetto:** mai un manifest come data URI. Dopo il deploy iOS tiene in cache l'icona: va **rimossa e ri-aggiunta** l'app alla schermata Home per vederla cambiare.

### 42.2 Manca(va) il tasto «Chiudi la giornata»

`closeMatchday()` esisteva nel sorgente ma **non era agganciata a nessun bottone**: funzione orfana. Una giornata si chiudeva solo in automatico (fine finestra voti, `kickoff+25h`) o dal cron. Conseguenza: chiudendo la stagione con una giornata ancora aperta, quella restava **orfana** — fuori dal recap (congelato) e senza modo di sbloccarla.

**Fix in `renderMatchday`:** nel ramo `live` c'è ora `🏁 Chiudi la giornata adesso`, con `closeMdHintText()` che cambia il testo secondo la fase (avvisa esplicitamente se i voti sono ancora aperti). Il `confirm` distingue **chiudere** da **annullare**, che erano confondibili.

**`closeSeasonNow()` non lascia più orfani:** se c'è una giornata aperta propone di chiuderla e poi archiviare, in un colpo solo; se la chiusura fallisce, non archivia. E se si chiude una giornata a stagione già archiviata, l'app **propone di ricalcolare il recap** (altrimenti resterebbe congelato senza quella giornata per sempre).

### 42.3 `fix_recap_mvp.sql` — «missing FROM-clause entry for table "mvp"»

In `build_season_recap`, temp table `_sr_pl`: la CTE `mvp` (conteggio MVP per giocatore) era **definita ma mai unita**. La select usava `coalesce(mvp.n,0)` mentre nella FROM c'erano solo `st/vt/pr/fld/gk`.

**Fix:** una riga, `left join mvp on mvp.player_id = p.id`. Controllate tutte le altre CTE della funzione: era l'unica scollegata.

**Nota di metodo:** il bug ha resistito settimane perché il recap è **lazy** — si costruisce alla prima `get_season_recap`, cioè molto dopo l'esecuzione dell'SQL. Prima di dare l'app a gruppi esterni, chiudere una stagione finta di 2-3 giornate su una lega di prova.

**Diagnostica aggiunta:** `openSeasonRecap` non dice più «Recap non disponibile» per tutto; mostra il messaggio SQL vero, oppure «recap vuoto: nessuna giornata chiusa». In `renderSeasonAdmin` compare un avviso rosso se la stagione risulta chiusa ma `get_last_closed_season()` non la vede, più un tasto «🏆 Apri il recap».

### 42.4 Recap di stagione — fix estetici

**Righe premio sovrapposte.** `.pag-awd-k` e `.pag-awd-n` erano `<span>` **inline**: etichetta e nome finivano attaccati («CAPOCANNONIEREBenzo») e `text-overflow:ellipsis` non può funzionare su un inline, quindi il nome sfondava sopra il valore. Ora sono `display:block`, `.pag-awd-v` ha `margin-left:auto` + `white-space:nowrap`, icona e padding ridotti per fare spazio.

**«Giornata 5» spezzata a metà.** In `srecords` il label va in `<span class="nb">` (`white-space:nowrap`).

**Avatar tagliati sui piedi.** `.pag-av img` usava `max-height:88%`. Una **max-height percentuale su un grid item** non si risolve in modo affidabile su Safari iOS (l'altezza dell'area viene trattata come indefinita → la percentuale diventa `none`), l'immagine sfondava e `overflow:hidden` la tagliava.
**Regola di progetto:** in questi riquadri le soglie vanno in **px**, mai in %. Valori attuali: `.pag-av` 132 · `.huge` 154 · `.sm` 79 · `.pag-duo` 69 · `.pag-awd-av` 38.

**Coriandoli rimossi.** Coprivano barra di stato e barra di avanzamento. `startConfetti()` non viene più chiamata (funzione e canvas restano inerti). Al suo posto `.pag-trophy.pulse` → keyframe `trophyIn`: il trofeo entra ruotando con bagliore oro e si posa. Rispetta `prefers-reduced-motion`.

**Parabola riscritta (`seasonPathSVG`).** Prima era solo una curva: non diceva a che **posto** fossi. Ora ha corsia sinistra con le posizioni (`1º` in alto, ultimo in basso), linee guida, il numero di posizione **su ogni pallino** (fino a 8 giornate; oltre, solo primo e ultimo) e le etichette X che usano il **label vero** della giornata (`Giornata 1` / `Giornata 5`), non più «1ª giornata». Geometria: `W=320 H=176 L=30 R=12 T=18 B=30`. Con più di 6 squadre mostra solo prima/metà/ultima posizione, altrimenti tutte.

### 42.5 Gesture native

- **Storie (`initRecap`)**: aggiunto lo **swipe orizzontale** (soglia 64px, direzione dominante ×1.4) → scena precedente/successiva, con vibrazione da 8ms. Convive con lo swipe giù che chiude e col tap. Flag `swiped` per non far scattare anche il tap al rilascio.
- **Classifica (`bindSeasonSwipe`)** e **schede (`bindCardSeasonSwipe`)**: swipe orizzontale = stagione precedente/successiva.

### 42.6 SELETTORE DI STAGIONE — il concetto

Prima si vedeva solo la stagione in corso: chiusa la 1 e aperta la 2, la 1 spariva ovunque tranne che nel recap.

**Chiave dell'architettura: `viewSeasonId` è SEPARATO da `currentSeasonId`.**
`currentSeasonId` è la stagione **in corso** e continua a governare Home, campo, voti, crediti, apertura giornate. `viewSeasonId` è solo «quale stagione sto guardando» in Classifica e nelle schede. Tenendole distinte, sfogliare un'annata archiviata **non può alterare niente del gioco attivo**.

Stesso principio per i dati: `standings` resta la classifica corrente (la usa la Home), `lbStandings` è quella della stagione consultata. `lbRows()` sceglie quale mostrare.

### 42.7 `stagioni_selettore.sql`

| funzione | cosa fa |
|---|---|
| `get_seasons()` | **nuova**. `(id, number, status, ended_at, mds_closed)` della propria lega, dalla più recente. Alimenta `allSeasons`. |
| `get_standings_season(p_season bigint default null)` | la precedente + parametro. `null` = stagione corrente (comportamento storico invariato, inclusa la chiamata dentro `get_team_card`). |

**Qui il `drop` è servito:** un parametro con `default` accanto alla versione a zero argomenti rende **ambigua** `get_standings_season()` (due candidati validi → errore). Quindi `drop function get_standings_season()` prima del `create`.

**Sicurezza:** `p_season` arriva dal client e non è fidato. Il filtro resta dentro la CTE:
```sql
select s.id from seasons s
 where s.league_id = my_league()
   and (p_season is null or s.id = p_season)
 order by (s.status='open') desc, s.number desc limit 1
```
Chiedere la stagione di un'altra lega non trova la riga → classifica vuota, mai dati altrui.

### 42.8 `schede_per_stagione.sql` — il pattern «guscio», NIENTE drop

Quattro funzioni, ognuna in **due versioni**:

- la **nuova** con `p_season` **obbligatorio** → contiene la logica
- la **vecchia**, firma invariata → guscio di una riga che chiama la nuova con `null`

```sql
create or replace function get_player_card(p_player_id bigint)
returns jsonb language sql stable security definer set search_path to 'public'
as $fn$ select public.get_player_card(p_player_id, null::bigint) $fn$;
```

**Perché obbligatorio e non `default`:** con `p_season ... default null` una chiamata a un argomento troverebbe due candidati (`(bigint)` e `(bigint,bigint)`) → `function is not unique`. Per evitarlo bisognerebbe **cancellare** le funzioni esistenti. Con il parametro obbligatorio le firme sono distinte, `get_player_card(5)` continua a risolversi sulla vecchia, **non si cancella niente** e in caso di problemi il vecchio comportamento è ancora lì.
PostgREST risolve per **nomi dei parametri** nel payload: `{p_player_id}` → 1 arg, `{p_player_id, p_season}` → 2 arg.

Funzioni toccate: `_player_facts(p_season)`, `_manager_season_facts(p_season)`, `get_team_card(uuid, bigint)`, `get_player_card(bigint, bigint)`.

**Cosa resta all-time e cosa diventa per stagione — distinzione voluta:**

- **Traguardi (all-time)**: gol, assist, MVP, presenze in carriera, Manita/Poker/Tripletta. Sono traguardi di **carriera**: azzerarli per stagione svuoterebbe la Bacheca.
- **Titoli (di stagione)**: Pallone d'oro, Re dell'attacco, Diga, Saracinesca, Capocannoniere, Mago degli assist — gate presenze incluso (`pres_season`, `voto_season` da `_player_facts(v_season)`).
- **Lato manager**: punti, posizione, `best_pos`, Re della giornata, Al comando, Scalatore, Profeta, Capitano coraggioso — tutti sulla stagione scelta.

Aprendo la scheda di un giocatore che è anche manager, il blocco 👔 eredita la **stessa** stagione: `get_team_card(v_owner, v_season)`.

**Guardia esplicita:** se `p_season` non è null e non trova una stagione della propria lega, le due schede tornano `{'error':'season_not_found'}` invece di ripiegare in silenzio sulla corrente mostrando dati con l'etichetta sbagliata.

**`_season_rank_history(v_season)`** accettava già l'id di stagione: nessuna modifica.

### 42.9 `grafico_voti_stagione.sql`

`get_player_vote_trend(p_player)` mostrava **tutte** le giornate chiuse della lega, mescolando le stagioni. Aggiunta `get_player_vote_trend(p_player bigint, p_season bigint)` — stesso pattern del guscio, ma qui la vecchia **non è nemmeno toccata**: la nuova ha firma distinta e basta.

Client: `loadVoteTrend(id, seasonId)` prova la due-argomenti, ricade sulla storica, e **non sparisce più in silenzio** — senza dati scrive «Nessun voto nella Stagione N». Viene richiamata da `refreshPlayerCard`, quindi il grafico **segue il selettore**.

### 42.10 Client — pezzi nuovi

| simbolo | ruolo |
|---|---|
| `allSeasons`, `viewSeasonId`, `lbStandings`, `lbBusy` | stato del browsing per stagione |
| `cardSeasonAware`, `voteTrendSeasonAware` | `null` = da verificare, `false` = SQL non applicata → il selettore resta **nascosto** invece di mostrare un controllo inerte |
| `loadSeasonsList()` | `get_seasons()`, con fallback che ricostruisce da `currentSeason` + `lastClosedSeason` |
| `seasonById`, `viewingCurrentSeason`, `lbRows` | helper |
| `loadSeasonStandingsFor(id)`, `setViewSeason(id)` | caricamento + cambio stagione (skeleton + vibrazione prima della rete) |
| `renderSeasonBar()` | segmented control in Classifica (`#lbSeasonBar`), nascosto se `allSeasons.length < 2` |
| `cardSeasonBarHTML()`, `setCardSeason()` | stesso controllo dentro le schede; tiene allineata anche la Classifica |
| `refreshPlayerCard()`, `refreshTeamCard()` | ricarica scheda (+ grafico voti) per la stagione scelta |
| `_noSeasonArg(err)` | riconosce «RPC senza p_season» (match su `p_season` / `does not exist` / `PGRST202`) |

CSS: `.seasonbar` — segmented control iOS, scroll orizzontale con `scroll-snap`, `.on` / `.on.past` (oro per le archiviate), `.sb-dot` verde sulla stagione aperta.

Sulle stagioni archiviate le frecce ▲▼ sono disattivate (non hanno senso su una classifica congelata) e `#lbHint` scrive «Classifica finale della Stagione N · archiviata».

### 42.11 Ordine di esecuzione

1. `fix_recap_mvp.sql`
2. `stagioni_selettore.sql`
3. `schede_per_stagione.sql` (richiede il 2)
4. `grafico_voti_stagione.sql`
5. `manifest.webmanifest` nella root del repo
6. `index.html` (chiavi Supabase da re-incollare)

`notify.ts`, `sw.js` e `admin.html` **non toccati**. Dopo un DDL, PostgREST impiega qualche secondo a rigenerare la cache dello schema.

**Collaudo:** aprire la scheda di un giocatore che ha vinto titoli nella Stagione 1 e passare da 2 a 1 — Capocannoniere e Pallone d'oro devono comparire sulla 1 e sparire sulla 2, mentre Cecchino e Uomo copertina (carriera) restano fermi. Il grafico voti deve cambiare con la stagione.

---

## 43. SESSIONE 43 — Stagione di riferimento, selettore stagione a foglio, Centro giornata, Impostazioni riorganizzate, Home compattata

> Dove in conflitto con sezioni precedenti, **vale questa** (in particolare sostituisce
> parti della §42 sul selettore stagione e della §40.x/§39.x sul menu Impostazioni).
> File: `index.html` + `stagioni_stato.sql` (nuovo) + `sw.js` (solo bump versione).
> `notify.ts`, `admin.html`, `manifest.webmanifest` **non toccati**.

### 43.1 Il bug: «Stagione 2» in testata sopra i dati della Stagione 1

Chiusa la Stagione 1, l'admin ha premuto «Apri una nuova stagione». Da quel momento la
testata diceva **Stagione 2** mentre classifica, statistiche e bacheca erano ancora quelle
della **Stagione 1** — e la mini-classifica in Home mostrava tutti a **0 punti** (erano i
punti, inesistenti, della Stagione 2).

Causa: `seasonLabel()` e `viewSeasonId` leggevano **sempre** `currentSeason`, cioè la
stagione aperta più recente. Bastava l'esistenza di una stagione aperta e vuota per
spostare tutte le etichette senza spostare i dati. Verificato con SQL che **nessuno**
crea stagioni in automatico alla chiusura (`ended_at` S1 e `started_at` S2 distavano
1'38"): `close_season` è a posto, il problema era solo di presentazione.

### 43.2 `displaySeason` — la stagione di riferimento

Tre concetti distinti, da non confondere mai più:

| globale | significato |
|---|---|
| `currentSeason` / `currentSeasonId` | dove finiscono le giornate **nuove** (logica di scrittura) |
| `displaySeason` / `displaySeasonId` | la stagione di cui l'app **parla** (etichette, classifica, statistiche, bacheca) |
| `viewSeasonId` | quale stagione sto **sfogliando** in Classifica / schede |

`computeDisplaySeason()` (chiamata in `loadSeason()`, **prima** di `loadSeasonsList()`):
se la stagione corrente è aperta **e ha zero giornate** e ne esiste una archiviata, allora
`displaySeason` = l'archiviata; altrimenti = `currentSeason`.

- `seasonIsEmptyOpen(s)` — vero solo se `status==='open' && s.mds_total!=null && mds_total===0`.
  Il controllo su `!=null` è voluto: se la RPC non riportasse `mds_total`, si ricade sul
  comportamento storico invece di mostrare la stagione sbagliata.
- `seasonBreak()` — vero quando `displaySeason.status!=='open'`, cioè **siamo in pausa fra
  due stagioni**.
- `nextSeasonNumber()` — se esiste già una stagione aperta e vuota è il suo numero,
  altrimenti `displaySeason.number + 1`.

**Regola di prodotto:** la stagione nuova prende il posto della vecchia **quando nasce la
sua prima giornata**, non quando viene aperta. Una stagione vuota non ha niente da
raccontare.

Conseguenze applicate:
- `seasonLabel()` legge `displaySeason`.
- `loadStandings()` passa **esplicitamente** `{p_season: displaySeasonId}` a
  `get_standings_season` (con fallback alla chiamata senza argomenti e poi a
  `get_standings`). Senza parametro la SQL prende la stagione aperta = quella vuota.
- `loadSeasonsList()` **esclude** dall'elenco la stagione aperta e vuota, e il default di
  `viewSeasonId` è `displaySeasonId` (non più `currentSeasonId`).
- `viewingCurrentSeason()` → **rinominata `viewingMainSeason()`**, confronta con `displaySeasonId`.
- `renderLB()`: `seasonForList` ripiega su `displaySeasonId`.
- Home: `loadPlayerCard`/`loadTeamCard` ricevono `displaySeasonId`.

### 43.3 Home in pausa fra due stagioni

Hero dinamico (`renderHero()`, chiamata da `renderAll` e `renderSeasonUI`). Nuovi id nel
markup: `#heroTitle`, `#heroCta`, `#heroExtra`.

- Stagione in corso: «Pronto a **schierare?**» + «Schiera la formazione →» (come prima).
- In pausa: «Stagione N **conclusa**» + «🏆 Rivivi la Stagione N», più una nota che spiega
  perché tutto è fermo lì, e (solo proprietario) «▶︎ Inizia la Stagione N+1».

Senza questo l'app invitava a schierare una formazione per una giornata inesistente.

### 43.4 Card admin Stagione riscritta + `cancel_empty_season()`

`renderSeasonAdmin()` ora ha **tre stati**: in corso / archiviata / archiviata con la
prossima già aperta e vuota. `closeSeasonNow()` e `openSeasonNow()` chiedono conferma e
dicono la verità: chiudere **non** apre niente, aprire non cambia nulla finché non c'è la
prima giornata.

`stagioni_stato.sql` (nuovo) aggiunge **`cancel_empty_season()`** — `security definer`,
solo `profiles.is_admin`, cancella la stagione aperta della propria lega **solo se ha zero
giornate** (ritorna `false` altrimenti), con `delete from season_recaps` protetto da
`exception when undefined_table`. Serve a rimediare a un'apertura per sbaglio.

### 43.5 Selettore stagione — via la barra, dentro il foglio

`.seasonbar` (segmented control della §42) **rimossa dall'uso**: non regge oltre 3-4
stagioni. Sostituita da:

- `#legaSeason` che da `<span>` diventa **`<button class="hh-season pick">`**: il titolo
  **è** il selettore, con `⌄` via `::after`. Con una sola stagione è `disabled` e resta
  un'etichetta muta.
- `openSeasonPicker(ctx, kind, ref)` — riusa il foglio generico (`#sheet`) con righe `.opt`:
  ⚽ per la stagione in corso, 🏆 per le archiviate, spunta su quella attiva. Scala a 20 stagioni.
- `renderLegaSeasonHead()` sostituisce `renderSeasonBar()`; disegna anche `#lbBack`, la
  fascia oro «📁 Stai guardando la Stagione N, archiviata» + tasto di ritorno.
- `cardSeasonBarHTML()` nelle schede bacheca usa lo stesso bottone-pillola.
- Lo **swipe** orizzontale (`bindSeasonSwipe`, `bindCardSeasonSwipe`) resta invariato.
- `#lbHint` ora dice «Classifica finale della Stagione N» anche quando si è in pausa sulla
  stagione di riferimento (prima sembrava ancora in gioco).

Il CSS `.seasonbar` resta nel file ma **non è più usato da nessuno**.

### 43.6 Home — mini-classifica e caroselli

**Mini-classifica**: sempre i primi tre; se la propria squadra è fuori dal podio si
**aggancia in fondo** con la posizione reale e un divisore tratteggiato (`.mini-row.split`).
Ovunque compaia, la propria squadra ha `(tu)` (`.youtag`). Nuovi helper `isMyRow(t)` e
`miniRowHTML(t,i,split)`. `isMyRow` confronta il **`manager_id`** (prima confrontava il nome
squadra: due squadre omonime si confondevano).

**Caroselli**: meccanica unica per statistiche e «Rivivi».
- CSS `.bctrack` (flex + `scroll-snap-type:x mandatory`, `overscroll-behavior-x:contain`,
  scrollbar nascosta), `.bctrack>*{flex:0 0 100%}`, `.bcdots` con il pallino attivo che si
  allunga in trattino.
- JS `renderTrackDots(trackId, dotsId)` e `bindTrack(trackId, dotsId)`, generici, con
  `_dotAt[trackId]` per **non riscrivere il DOM a ogni pixel di scroll**. `renderBcDots()`
  e `bindBcTrack()` restano come alias per le statistiche.
- Con meno di 2 schede visibili i pallini spariscono e `overflow-x` va a `hidden`.

**«Rivivi»**: le due sezioni «Pagellone di giornata» e «Albo d'oro» (due intestazioni per
un bottone ciascuna, ~200px) diventano **una sola fascia** `#homeRvWrap` con la pista
`#homeRvGrid` + `#homeRvDots` e due riquadri `.rvtile` (blu il pagellone, `.gold` la
stagione). Disegnati da `renderRecapButton()`; `renderSeasonRecapButton()` ora la richiama
e si occupa solo della riga «Albo d'oro» in Impostazioni.
Id rimossi: `homeRecapWrap`, `homeSeasonWrap`, `homeRecapBtn`, `homeSeasonBtn`,
`homeSeasonTtl`, `homeSeasonSub`.

### 43.7 Impostazioni riorganizzate

Il livello intermedio **`page-admin`** («Area amministratore» → Partita / Lega) è
**eliminato**: erano due tap per arrivare ovunque. Anche **`page-partita`** non esiste più.

Menu (`#setMenu`) diviso in gruppi con intestazione `.setgrp`:

```
IL MIO ACCOUNT   Profilo · Notifiche
LA LEGA          Regolamento · Albo d'oro (#alboRow, solo a stagione archiviata)
GESTIONE         Centro giornata · Stagione · Regole della partita · Gestione lega
                 (#admGrp + .navrow.adminRow, visibili se canOp())
```

- L'id singolo `adminRow` è sostituito dalla **classe** `.navrow.adminRow` (4 righe);
  `applyProfile` cicla su `document.querySelectorAll('.navrow.adminRow')` e mostra `#admGrp`.
- Sottotitoli **vivi**: `#admMdSub` = «Giornata 6 · Voti aperti», `#admSeaSub` =
  «Stagione 1 · 5/38» oppure «Stagione 1 archiviata». Aggiornati in `renderMatchday()`.
- `openAlboSheet()`: con più stagioni archiviate apre l'elenco nel foglio e riapre il
  recap di **qualsiasi** annata; con una sola va dritto al recap.
- Il piede del menu è ora `.setfoot` (logout + versione) con `margin-top:auto` **e**
  `padding-top:26px`. Senza il padding, a menu pieno `margin-top:auto` collassa a zero e
  «Esci» si incolla alla riga sopra.

Nuove pagine (`.setpage`): **`page-giornata`**, **`page-stagione`**, **`page-regole`**.
`page-lega` invariata nel contenuto, cambia solo il `subback` (→ `setMenu`) e il titolo
(«Gestione lega»).

**Vincolo confermato:** gli id che il JS usa per show/hide (`mdCard`, `presCard`,
`seasonCard`, `gkCard`, `presModeCard`, `voterCard`, `inviteCard`, `manageCard`,
`creditCard`) restano sull'elemento **esterno**, anche dopo lo spostamento fra pagine.
`seasonCard` non è più un `.acc` ma un `.set-card` (contiene solo `#seasonBox`).
`mdCard` non è più un `.acc` ma un `<div>` semplice.
`maintCard` è referenziato in `applyProfile` ma **non esiste nel markup** da tempo: la
riga è innocua (guardia `if(mtc)`).

### 43.8 Centro giornata

Il pezzo che risolve il «bordello»: prima tutti i tasti erano visibili insieme e capire
quale servisse adesso era a carico dell'admin.

- `mdcPhaseIdx()` → 0 Programmata · 1 Sondaggio presenze · 2 Formazioni · 3 Partita ·
  4 Voti · 5 Conclusa (−1 = nessuna giornata). Stessa logica di `phaseLabel()`/`computeLock()`.
- `mdcPhaseShort()` → etichetta breve per il sottotitolo nel menu.
- `renderMdCenter()` disegna in `#mdcSteps` la **sequenza verticale** (`.mdc-step` con
  `.dot`, stati `.done` / `.now`, filo di collegamento via `::before`). Il passo
  «Sondaggio presenze» compare **solo** se quella giornata lo prevede
  (`presenceSelf && t.presenceClose`).
- In `#mdcPrimary` **una sola azione**, quella pertinente:
  nessuna giornata → `openNowMatchday()` · presenze/formazioni → `openEditKickoffSheet()` ·
  partita → `openLiveStats()` · voti → `closeMatchday()` (con `closeMdHintText()` sotto) ·
  conclusa → `openRecap(md.id,false)`.
- Tutto il resto (programmazione automatica `#mdOpenBox`, i vecchi `#mdActions` con
  modifica orario / chiudi / **annulla giornata**) sta sotto l'accordion **«Azioni
  avanzate»** (`#mdAdvCard`), chiuso. I tasti distruttivi non sono più a portata di pollice.
- `renderMatchday()` chiama `renderMdCenter()` dopo `renderOpenMode()` e aggiorna i due
  sottotitoli del menu.

Modalità portiere e presenze sono passate in **Regole della partita**: sono configurazioni
di lega, non operazioni di giornata, e stavano in mezzo ai comandi. Le tendine partono
**chiuse** come ovunque nell'app.

### 43.9 Ordine di esecuzione

1. `stagioni_stato.sql` (Supabase SQL Editor)
2. `index.html` (chiavi Supabase da re-incollare)
3. `sw.js` (solo `SW_VERSION` bumpata)

**Collaudo:** con una stagione archiviata e nessuna nuova, la Home deve dire «Stagione N
conclusa» e la classifica deve mostrare i punti **veri** dell'ultima stagione giocata, non
zeri. Aprire una stagione nuova non deve cambiare niente finché non si programma la prima
giornata. Nel Centro giornata, a giornata conclusa, la sequenza è tutta spenta con
l'ultimo passo acceso e «Vedi il pagellone» come azione.

### 43.10 In sospeso

- Multi-lega per `sondaggio.html` (aperto da tempo).
- Split del sito: `/` landing pubblica + `/app/` gioco — vedi `PROSSIMI_PASSI.md`.
  Quando si farà, in `notify.ts` vanno cambiati **tutti** gli `url` delle push
  (`"/"` → `"/app/"`, `"/?srecap="` → `"/app/?srecap="`).

---

## 44. SESSIONE 44 — Card unificate in Home, schede giocatore/manager ridisegnate, frasi nello splash, fase di giornata unificata e doppioni admin rimossi

Sessione mista: prima estetica (Home e schede), poi il primo dei tre interventi di
riordino sulla logica admin. Un solo `index.html`, nessuna SQL, `notify.ts` non toccato.

### 44.1 Riquadro «Stai creando una nuova lega» — via il rosso

Il riquadro di contesto della schermata email (`.ctx-box.create`) era rosso: in una
schermata di accesso il rosso si legge come **errore**, non come «hai scelto questa
strada». Ora è **viola** (`rgba(139,124,255,…)`), colore non usato altrove nell'app,
quindi non si confonde né col verde di `.ctx-box.join` né con l'azzurro del pulsante
d'azione sotto.

Il `+` era l'emoji **➕**, che iOS disegna quasi nera: sul fondo scuro spariva. Sostituita
da un carattere vero con classe dedicata `.ctx-box .ci.plus` (Bricolage 800, bianco,
`text-shadow` leggero). **Regola generale:** le emoji-simbolo monocromatiche (➕ ➖ ✖️)
su fondo scuro in iOS sono da evitare — servono caratteri o SVG.

### 44.2 «Rivivi»: da targhette vuote a locandine con i dati

Prima: due `.rvtile` con emoji + due righe di testo, dentro un riquadro largo tutto lo
schermo. Tanto vuoto, e nessun motivo per aprirle.

Ora `.rvcard` anticipa il contenuto:

- **Card giornata** (`rvMdCardHTML`) — occhiello «Ultima giornata», titolo = label,
  sottotitolo con la data di gioco, e due riquadri-dato riempiti **in differita** da
  `rvFillMd(mdId)`: *Re della giornata* (logo squadra + punti) e *La tua giornata*
  (posizione + punti). Una sola RPC `get_standings_md`, con cache in `_rvMdCache`
  (`{id, rows}`), righe ordinate per punti decrescenti.
  Guardia: se `!rows.length || !(rows[0].pts>0)` non si inventa un vincitore (con nessuna
  formazione schierata il primo sarebbe una squadra a caso a 0 punti) e si mostra un
  riquadro neutro.
  Guardia anti-race: `rvFillMd` rilegge `#rvMdFacts` e confronta col nodo di partenza; se
  la Home si è ridisegnata nel frattempo, esce.
- **Card stagione** (`rvSeasonCardHTML`) — *Campione* e *Giornate giocate*. Il campione si
  ricava da `standings[0]` **senza query extra**, ma solo se
  `Number(displaySeasonId)===Number(s.id)`: altrimenti `standings` è la classifica di
  un'altra stagione e mostrerebbe il vincitore sbagliato. Le giornate arrivano da
  `seasonById(s.id).mds_closed`.

**Peek provato e scartato.** Le card erano state portate a `flex:0 0 88%` per far
intravedere la successiva sul bordo; Teo ha preferito la larghezza piena («più
professionale, i pallini bastano»). Rimosso `.bctrack.rvtrack`.
**Tenuta invece la generalizzazione di `renderTrackDots`**: il passo ora è
`cards[0].getBoundingClientRect().width + 10` invece di `tr.clientWidth + 10`. È corretto
in entrambi i casi e serve se un domani si riprova il peek.

### 44.3 Un solo componente per tutte le card della Home

Le classi `.bcard`, `.bcard-top`, `.bc-ic`, `.bc-eyebrow`, `.bc-title`, `.bc-sub`,
`.bc-arr`, `.bc-meta`, `.bc-pill`, `.bc-next`, `.bc-bar` sono state **eliminate**
(entrambi i blocchi CSS, base e override). Statistiche e Rivivi usano lo stesso `.rvcard`.

Nuovo builder unico:

```js
hcardHTML({wm, eye, ttl, sub, facts, factsId, prog, go})
```

- `wm` filigrana (emoji grande sfumata in alto a destra), `eye` occhiello maiuscolo,
  `ttl` titolo, `sub` sottotitolo, `facts` array di `rvFactHTML(icon,val,key,cls)`,
  `prog` barra opzionale, `go` riga d'apertura con la freccia.
- Lo usano `rvMdCardHTML`, `rvSeasonCardHTML` e le due card di `renderHomeBcards`.

Nel markup `#homeBcardPlayer` è `class="rvcard"` e `#homeBcardMgr` è `class="rvcard gold"`
(gli **id restano invariati**: `updateStatsWrap` continua a leggere `style.display`).
`nextBarHTML` ora emette `.rv-prog > .pt / .pb` invece di `.bc-next`.

Le vecchie pillole sono diventate riquadri-dato allineati. Sulla card manager, se i record
sono ancora a zero **non** si mostra «×0» (non è un traguardo): si ripiega sui punti
stagione.

### 44.4 Scheda giocatore — gerarchia invece di sei box uguali

`playerStatsGridHTML(s)` sostituisce `.sg-core` / `.sg-vote` (rimosse):

- **Anello del voto medio** (`pgRingHTML(val,label,pct,color)`): due `<circle>` in un
  `viewBox 0 0 82 82` ruotato di −90°, arco via `stroke-dasharray`.
  ⚠️ Il colore va nello **`style`**, non nell'attributo `stroke`: Safari non risolve le
  variabili CSS negli attributi di presentazione SVG.
  ⚠️ L'etichetta sta **fuori** dal cerchio (`.pg-rlab` sotto): dentro, in maiuscoletto
  spaziato, finiva a cavallo del bordo — bug estetico segnalato da Teo.
- **Presenze come tacche** (`.pg-ticks`): una per giornata se `maxP<=10`, altrimenti una
  barra unica con due `flex` proporzionali (a 38 giornate sarebbero trattini da 3px).
- **Gol e assist come barre rapportate al MIGLIORE della lega**, non a un massimo teorico:
  i massimi si ricavano ciclando `playerStats` (già caricato per tutti). È l'unico
  paragone che significhi qualcosa in un gruppo di 15 amici. Sotto, una riga di nota
  spiega la scala una volta sola.
- `#bestVoteBox` è stato mantenuto come **id**, con dentro un `.v`: `loadVoteTrend`
  continua a riempirlo senza modifiche. Il valore ora usa la **virgola**.

**Cambio di visibilità consapevole:** «Voto medio» e «Miglior voto» erano gated da
`canOp()` (solo admin/vice). Ora li vedono tutti: l'anello è il perno della scheda, e il
grafico `#statChart` subito sotto era già pubblico e mostrava la media nell'intestazione —
il gate era rimasto per inerzia. Se si volesse tornare indietro, il punto è
`playerStatsGridHTML`.

### 44.5 Scheda manager — posizione grande e record allineati

`teamStatsGridHTML(card)` riscritta; rimosse `.tg-hero`, `.tg-rank`, `.tg-rest`.

- `.tm-hero`: **posizione** in 38px oro con «su N squadre» (N da `standings.length`),
  punti a destra con la stagione, e `.tm-track` = barra `((tot-pos)/(tot-1))*100`, cioè
  «quanto sei in alto» senza dover contare le squadre.
- `.tm-chips` è una **griglia 2 colonne** di `.tm-rec` di uguale misura; l'ultimo elemento
  si allarga su tutta la riga se sono dispari
  (`.tm-chips>.tm-rec:last-child:nth-child(odd){grid-column:1/-1}`).
  Prima erano chip a larghezza variabile che andavano a capo in modo casuale: sembravano
  sbilenche (screenshot di Teo).
- I record a zero restano visibili ma **spenti** (`.tm-rec.z`): sono obiettivi, non
  risultati, e vederli grigi dà una ragione per rincorrerli.
- «Miglior giornata» ha l'unità `pts` in `<small>` grigio, così si legge come unità e non
  come parte del numero.

> **Bug imparato (vale ovunque):** valore ed etichetta erano due `<span>` — elementi in
> **linea**, quindi si affiancano invece di impilarsi, e si leggeva «×0Re della giornata».
> Servono `display:block`. Il `margin-top` su uno `<span>` inline non ha effetto.

### 44.6 Splash — frasi di caricamento

`SPLASH_TIPS`: array di 15 frasi, una a caso a ogni avvio, scelta nello stesso blocco
`try` che copia la `src` da `#wcHero`. Metà spiegano una regola («Il capitano vale
doppio»), metà prendono in giro il calcetto vero («Nessuno vuole fare il portiere. Come
sempre.»).

Markup: `<div class="sp-tip" id="spTip">` fra `.sp-hero` e `.sp-load`.
CSS: posizionata a `bottom: calc(80px + safe-area)`, fade a 1,72s (subito dopo i pallini,
che sono scesi a 40px). Il padding inferiore di `.sp-hero` è passato da **78 a 116px** per
fare spazio: l'illustrazione si ridimensiona invece di finirci sopra.
Aggiunta a `.sp-tip` anche la regola `prefers-reduced-motion`.

Per aggiungere frasi basta allungare l'array: nessun'altra modifica.

### 44.7 Fase della giornata — una sola fonte di verità

**Il problema.** Esistevano due funzioni che calcolavano la stessa cosa con due elenchi
diversi di stati: `phaseLabel()` per l'intestazione del Centro giornata e `mdcPhaseIdx()`
per la timeline. La prima conosceva «Voti chiusi», la seconda no (ritornava `4` sia con
voti aperti sia con voti scaduti) → **a finestra voti scaduta la testata e i pallini
raccontavano due storie diverse**.

**La soluzione.** Un solo elenco e un solo indice:

```js
const MD_PHASES=[ {n,short,desc} × 7 ];   // n=timeline, short=sottotitolo menu, desc=riga sotto al titolo
function mdPhaseIdx(){ … }                // -1 nessuna giornata
function mdPhaseShort(){ … }
function phaseLabel(){ … }                // short · desc
```

Indici: `-1` nessuna giornata · **0** Programmata · **1** Sondaggio presenze ·
**2** Formazioni · **3** Partita · **4** Voti · **5 Voti chiusi (NUOVO)** · **6** Conclusa.

⚠️ **Gli indici sono cambiati rispetto a §43.8**: «Conclusa» era `5`, ora è `6`.
`mdcPhaseIdx()` e `mdcPhaseShort()` **non esistono più**.

Nella timeline le tappe si generano da `MD_PHASES` invece che da un array parallelo. Due
filtri: il passo «Sondaggio presenze» solo se `presenceSelf && t.presenceClose` (come
prima), e il passo «Voti chiusi» **solo quando `i===5`** — altrimenti sarebbe una riga
sempre presente che non dice niente.

### 44.8 Doppioni admin rimossi

**Il problema.** `renderMatchday` compilava a mano `#mdActions` (le «Azioni avanzate») e
`renderMdCenter` compilava a mano `#mdcPrimary` (l'azione principale): gli **stessi**
pulsanti, scritti due volte, con la stessa grafica. A voti aperti «🏁 Chiudi la giornata
adesso» compariva **due volte nella stessa schermata**, una come primaria e una dentro la
fisarmonica. L'idea di «una sola azione per volta» era vera solo a metà, e un'azione
distruttiva era duplicata.

**La soluzione.**

```js
const MD_ACTIONS={ open, kick, panel, close, recap };  // {cls, ic, lab, fn}
function mdActionHTML(k, marginTop){ … }
function mdcPrimaryKey(){ … }        // quale azione è LA azione, dalla fase
function renderMdActions(primary){ … } // le avanzate = tutto TRANNE la primaria
function openRecapCurrent(){ … }     // così MD_ACTIONS non interpola l'id in una stringa onclick
```

- Il blocco `#mdActions` dentro `renderMatchday` è stato **cancellato**: ora
  `renderMdCenter()` chiama `renderMdActions(key)` in coda.
- Le avanzate contengono `kick` e/o `close` **solo se non sono già la primaria**, più
  «Annulla questa giornata» quando esiste una giornata.
- Gli hint (`openNowHintText()`, `closeMdHintText()`) seguono il pulsante primario.
  `#openNowHint` esiste solo quando la primaria è `open`; `refreshOpenNowHint` ha già la
  guardia `if(h)`.

**Regola da mantenere:** una nuova azione di giornata si aggiunge in `MD_ACTIONS` e si cita
in `mdcPrimaryKey()` o in `renderMdActions()` — **mai** scrivendo un `<button>` a mano nei
render. Stessa logica di `hcardHTML` per le card e di `MD_PHASES` per le fasi: un concetto,
un posto.

### 44.9 Revisione dell'organizzazione admin (analisi, non ancora implementata)

Fatta una lettura completa del percorso admin. Sintesi: **fondamenta giuste, organizzazione
no**.

Quello che funziona e non va toccato: l'**automazione** (`open_due_matchdays` +
`close_due_matchdays` + cron ogni 10 min) — una lega gira anche se l'admin non apre mai
l'app, ed è la decisione di design che tiene in vita il progetto; e il **principio di una
sola azione primaria**, che va esteso, non ridiscusso.

Problemi rimasti (dettaglio e piano in `PROSSIMI_PASSI.md` §1-§2):

1. `renderOpenMode()` (programmazione ricorrente: automatico on/off, giorno fisso, ora) sta
   dentro le Azioni avanzate del **Centro giornata**, che è la schermata della giornata
   *in corso*. È una regola permanente: va in **Regole della partita**.
2. **«Modifica orario partita»** (una tantum) e **«Ora del fischio d'inizio»** (ricorrente)
   sono due cose diverse con quasi lo stesso nome in due posti diversi.
3. `page-lega` usa ancora **cinque fisarmoniche** mentre il resto delle Impostazioni usa le
   drill-in page.
4. I **nomi** delle sezioni non aiutano: «chi può votare» (una regola) sta in Gestione
   lega, «chi segna le presenze» sta in Regole.
5. La pagina **Stagione** fa cinque mestieri, inclusi ricalcolo recap e diagnostica SQL,
   che sono manutenzione.
6. **Nessuna scorciatoia dalla Home**: inserire i gol costa Home → ⚙️ → Centro giornata →
   scroll → pannello. Quattro tap per l'azione più frequente. La hero dovrebbe usare
   `mdcPrimaryKey()` per proporre l'azione admin del momento.
7. **Metodo dei crediti: interruttore orfano.** La scelta Manuale/Sondaggio esiste solo nel
   wizard di creazione lega (`#suStep3`), che promette «Potrai cambiare tutto dalle
   Impostazioni» — ma `setCreditMode(mode)` **non è chiamata da nessun pulsante**. Il
   riquadro `#creditCard` («💰 Sondaggio valori», in Gestione lega) si mostra solo con
   `creditMode==='poll' && valuePollOpen`: chiuso il sondaggio sparisce e non si riapre.
   Resta solo la modifica a mano per giocatore (`renderEditForm`, campo Crediti 1-100).
   Da aggiungere una riga in *Regole della partita* con l'interruttore + «Riapri il
   sondaggio». Prima verificare in SQL cosa fa `set_credit_mode('poll')` su una lega dove
   il sondaggio è già stato chiuso: riapre `poll_open` o va aperto a parte?

### 44.10 Ordine di esecuzione

1. `index.html` (**nessuna SQL**)
2. `sw.js` (solo `SW_VERSION`)

Le chiavi Supabase sono **dentro** il file consegnato (la `sb_publishable_…` è pubblica per
design): non serve più re-incollarle, va solo verificato che ci siano.
⚠️ `APP_VERSION` è ancora `'v9'`: da bumpare al prossimo deploy.

**Collaudo:** nel Centro giornata, in qualunque fase, dentro «Azioni avanzate» **non** deve
comparire il gemello del pulsante grande sopra; il sottotitolo della riga «Centro giornata»
nel menu deve coincidere con la fase accesa nella timeline. In Home, le due card
Statistiche devono avere esattamente la stessa forma delle due di Rivivi. Nella scheda
giocatore l'etichetta «Voto medio» deve stare sotto l'anello, non sopra il cerchio.

### 44.11 Decisioni non tecniche prese in questa sessione

- **Partita IVA**: non serve finché è tutto gratis; serve dal primo incasso, perché il
  criterio è l'**abitualità** dell'attività, non la forma del pagamento — la transazione
  singola per stagione **non** è una scappatoia fiscale (ma resta la scelta giusta per
  altri motivi: niente obblighi sul rinnovo automatico, contabilità più semplice).
  Non esiste alcuna soglia di 5.000 € come esenzione.
- **Privacy policy**: obbligatoria a prescindere dalla PWA. Nessun banner cookie finché si
  usa solo storage tecnico.
- **Pubblicità**: scartata. Tecnicamente possibile (AdSense su PWA funziona, non serve
  AdMob), ma a questa scala vale qualche euro al mese e imporrebbe un banner di consenso
  con CMP certificata su un'app che oggi non ne ha bisogno — oltre a contraddire il piano
  di far pagare l'admin. Alternative: sponsor locale statico, o pubblicità sulla sola
  landing dopo lo split.

Dettagli in `PROSSIMI_PASSI.md` §5-§6.

### 44.12 In sospeso

- Admin 2/3 e 3/3 (vedi sopra e `PROSSIMI_PASSI.md`), incluso l'interruttore orfano del
  metodo crediti.
- Sparkline della posizione nella scheda manager: serve una RPC che esponga
  `_season_rank_history` (oggi è solo interna).
- Multi-lega per `sondaggio.html` (aperto da tempo).
- Split `/` landing + `/app/` gioco, con i relativi `url` da cambiare in `notify.ts`.
- Privacy policy e termini, da scrivere insieme alla landing.

---

## 45. SESSIONE 45 — Admin 2/3 e 3/3: configurazione fuori dall'operatività, impostazioni a drill-in, hero della Home admin-aware

Chiusi in una sola sessione i due interventi che restavano del riordino admin, più due
interruttori orfani ritrovati per strada e l'ingrandimento delle frasi dello splash.
Un solo `index.html`, nessuna SQL, `notify.ts` e `sw.js` non toccati. `APP_VERSION` → `v10`.

Il criterio che ha guidato tutto: **in ogni momento c'è una sola cosa che l'admin deve
fare; tutto il resto è configurazione, e la configurazione si tocca due volte l'anno.**

### 45.1 Il nuovo criterio di collocazione (da rispettare d'ora in poi)

Tre contenitori, tre domande:

| Se una voce… | va in… |
|---|---|
| riguarda **la giornata in corso** | **Centro giornata** (`page-giornata`) |
| è un **interruttore permanente** | **Regole della lega** (`page-regole`) |
| chiede di scegliere delle **persone** | **Gestione lega** (`page-lega`) |
| serve **una volta ogni tanto** (ricalcoli, diagnostica, offline) | **Aiuto e manutenzione** (`page-manutenzione`) |

La regola pratica da ricordare è la terza: *se devi scegliere delle persone, è in Gestione
lega*. Risolve la domanda che prima faceva pensare («dove cambio chi segna le presenze?»
→ è un interruttore → Regole della lega).

### 45.2 «Quando giocate di solito» (Admin 2/3, §1.1)

`renderOpenMode()` viveva dentro **Azioni avanzate del Centro giornata**, cioè nella
schermata della giornata *in corso*, pur essendo una regola permanente della lega. Ora sta
in **Regole della lega → Quando giocate di solito** (`page-quando`).

- Contenitore rinominato: `#mdOpenBox` → **`#schedBox`**. È l'unico punto dove `renderOpenMode`
  scrive: se un domani sparisce di nuovo, è quello l'id da cercare.
- `renderOpenMode()` è uscita dal blocco `if(mc){…}` di `renderMatchday`: non dipende più
  dall'esistenza di `#mdCard`, che sta in un'altra pagina.
- **Conflitto di nomi risolto:** «Modifica orario partita» (una tantum) è diventata
  «**Modifica orario di questa giornata**» (`MD_ACTIONS.kick` + titolo del foglio), e «Ora
  del fischio d'inizio» (ricorrente) è diventata «**Ora abituale** del fischio d'inizio»
  (in due posti: `renderOpenMode` e lo step 0 del wizard `#suStep0`). Prima o poi qualcuno
  avrebbe cambiato quella sbagliata.
- Nel Centro giornata, quando non c'è nessuna giornata, sotto l'azione primaria compare una
  scorciatoia `setNav('page-quando')`.
- Il messaggio «⚠️ «X» è ancora aperta: puoi annullarla o chiuderla **qui sotto**» diceva
  il falso dopo lo spostamento → ora rimanda al Centro giornata.

Le «Azioni avanzate» contengono adesso solo cose davvero avanzate: modifica orario, chiudi
(quella non primaria) e annulla giornata.

### 45.3 Fisarmoniche → drill-in (Admin 2/3, §1.2)

Le cinque `.acc gold` di `page-lega` e le due di `page-regole` sono diventate `.navrow` con
pagina dedicata. Su iPhone la fisarmonica costava un tap per aprire, uno scroll, uno per
richiudere; il drill-in è il pattern già usato dal resto delle Impostazioni.

Nuove `.setpage`: `page-quando`, `page-presenze`, `page-portiere`, `page-crediti`,
`page-invita`, `page-giocatori`, `page-vice`, `page-votanti`, `page-manutenzione`.
Da 8 a **17** pagine di impostazioni.

⚠️ **Vincolo rispettato:** gli id usati dal JS per show/hide (`gkCard`, `presModeCard`,
`voterCard`, `inviteCard`, `manageCard`, `creditCard`, `seasonCard`) sono rimasti
**sull'elemento esterno**, che ora è la riga `.navrow` e non più la fisarmonica.

> **Bug conseguente, da ricordare:** `applyProfile` faceva `style.display='block'`. Una
> `.navrow` è `display:flex`: forzarla a `block` la spezza (icona, etichetta e chevron si
> impilano). Ora usa **`display=''`**, che rimette il valore del foglio di stile — `block`
> per un `div`, `flex` per una `.navrow`. Stessa correzione in `loadInvite()`.
> **Regola generale:** mai scrivere `display:'block'` per riaccendere un elemento di cui
> non conosci il display nativo; `''` è sempre corretto.

**Sottotitoli vivi.** Ogni riga dice già com'è impostata la regola («Ogni Mer alle 20:30 ·
apertura automatica», «Le segnano i giocatori», «12 giocatori in rosa»), così non serve
entrare per controllare. Li scrive **`renderRuleRows()`**, unico punto, chiamato da
`renderOpenMode`, `renderGkMode`, `renderPresenceMode`, `loadCreditConfig`, `renderManage`
e `applyProfile`. **Se aggiungi una regola, aggiungi la sua riga lì.**

**Vice-admin.** Le righe che aprono pagine da solo-proprietario hanno ora la classe
**`.ownerRow`** (gestita in `applyProfile` con `is_admin`), separata da `.adminRow`
(gestita con `canOp()`). Prima il vice vedeva «Regole della partita» e ci trovava una
pagina vuota, perché il contenuto era nascosto ma la riga no.

### 45.4 Metodo dei crediti: interruttore orfano richiuso (Admin 2/3, §1.5)

`setCreditMode(mode)` esisteva nel codice ma **nessun pulsante la chiamava più** dalla
sessione 31.5: la scelta Manuale/Sondaggio viveva solo nel wizard di creazione lega, che
compare una volta sola e prometteva «potrai cambiare tutto dalle Impostazioni». Per questa
regola non era vero, e da Stagione 2 in poi non c'era modo di rifare i valori.

Ora **Regole della lega → Crediti dei giocatori** (`page-crediti`):

- interruttore `#creditModeSw` (Manuale / Sondaggio) → `askCreditManual()` / `askCreditPoll()`,
  entrambe con conferma esplicita perché sovrascrivono uno stato di lega;
- «🔁 **Riapri il sondaggio**» quando `credit_mode='poll'` e il sondaggio è chiuso;
- `#creditCard` (avanzamento + «Chiudi e calcola i crediti») **si è spostata qui** da
  `page-lega`: era una regola finita fra le persone.

⚠️ **Il dubbio SQL della sessione 44 è risolto:** `set_credit_mode('poll')` imposta
`value_poll_open=true`, quindi **è anche il «riapri»** — nessuna RPC nuova, nessuna
migrazione. Verificato su `fantacalcetto_context.py` §RPC e coerente con la 31.5, dove un
pulsante «Riapri il sondaggio» esisteva e funzionava. `askCreditPoll()` ricontrolla
comunque `valuePollOpen` dopo la chiamata e avvisa se non risulta aperto: se un domani
l'RPC cambia comportamento, l'app non racconta bugie.

Nota onesta scritta nell'interfaccia: riaprendo, **i voti vecchi restano** (`submit_value_poll`
fa upsert per `voter_id`), quindi chi non rivota tiene il voto della volta scorsa.

### 45.5 Pagina Stagione snellita e «Aiuto e manutenzione» (Admin 2/3, §1.4)

La pagina Stagione faceva cinque mestieri. Ricalcolo del recap e avviso diagnostico su
`stagione_recap.sql` sono **manutenzione**, non gestione: spostati in `page-manutenzione`
(`renderMaintBox()`). In Stagione restano stato, chiusura, apertura della prossima e
«Apri il recap».

**Interruttore orfano n° 2.** Il markup di `#maintCard` / `#maintBtn` era **sparito
dall'HTML** in qualche sessione passata, mentre `applyProfile` e `renderMaintBtn()`
continuavano a cercarlo e `setMaintenance()` non era più raggiungibile da nessun pulsante.
Rimesso — ma con una correzione di rotta (vedi sotto).

### 45.6 «App offline» riservato al super-admin + canale di segnalazione

Rimettere «Metti in manutenzione» per tutti gli admin era sbagliato in prospettiva
multi-lega. **Precisazione tecnica importante:** `setMaintenance()` fa
`.eq('league_id', profile.league_id)`, quindi agisce **solo sulla propria lega** — un altro
admin non avrebbe potuto spegnere l'app a tutti, solo ai suoi. La manutenzione **globale**
sta su `app_global`, è riservata al super-admin e **non ha alcun pulsante** in tutta l'app.

Resta però un pulsante che a un admin che non siamo noi può solo fare danno: serve a chi
pubblica gli aggiornamenti. Quindi `#maintCard` è ora gated su **`isSuperAdmin()`**, non su
`is_admin`. Stessa scelta per l'avviso diagnostico su `stagione_recap.sql`: dice di
eseguire un file SQL che solo noi possiamo eseguire.

Al suo posto, per tutti gli altri admin, la pagina «**Aiuto e manutenzione**» offre
«**Qualcosa non va?**» → `helpMailto()` costruisce un `mailto:` a `accesso@fantacalcettoitalia.it`
con oggetto e corpo precompilati: **lega, `APP_VERSION`, giornata in corso**. Sono le tre
cose che servono sempre per capire un bug e che altrimenti bisogna chiedere. C'è anche
«Copia l'indirizzo» come ripiego se il `mailto:` non parte (succede in certe webview).

### 45.7 Hero della Home admin-aware (Admin 3/3)

Il 90% del lavoro settimanale dell'admin è inserire gol/assist/esito e chiudere. Prima
servivano **Home → ⚙️ → Centro giornata → scroll → «Apri pannello partita»**: quattro tap
e uno scroll ogni settimana per l'azione più frequente che esista. Intanto la hero diceva
all'admin «Schiera la formazione» come a chiunque altro. Ora è **un tap**.

- **`mdcPrimaryKey()` è più sveglia.** A voti aperti (fase 4), se l'esito non è ancora
  stato salvato l'azione primaria è **`panel`** (inserisci i risultati), non `close`.
  Chiudere senza esiti manda in classifica una giornata a metà, ed è l'errore più facile da
  fare in quella fase.
- **`mdResultsSaved`** — nuovo flag calcolato in `loadMatchStats()` **dalle righe del
  database**, non da `adminStats`: quest'ultimo viene mescolato con la bozza locale
  (`loadLiveDraft`, `localStorage`) e direbbe «risultati inseriti» anche senza aver
  salvato. Il segnale è l'`esito` V/S: gol e assist possono legittimamente essere zero,
  «chi ha vinto» no.
- **`HERO_TODO` + `heroTodoKey()` + `heroAdminTodo()`** — la hero legge `mdcPrimaryKey()`,
  la *stessa* funzione che comanda il Centro giornata: le due schermate non possono
  divergere. `kick` e `recap` non compaiono in Home (spostare un orario o rileggere il
  pagellone non sono compiti).
- **`solo`** decide se il compito admin prende il pulsante *principale* o resta un secondo
  pulsante `.hero-2nd` sotto «Schiera la formazione»: prende il principale solo quando il
  giocatore non ha niente da fare.

| Fase | Primaria Centro giornata | Hero |
|---|---|---|
| nessuna giornata | `open` | **principale** → 📅 Programma la prossima |
| sondaggio / formazioni | `kick` | — |
| partita | `panel` | **principale** → 📊 Inserisci i risultati |
| voti aperti, risultati mancanti | `panel` | secondario → 📊 Inserisci i risultati |
| voti aperti, risultati inseriti | `close` | — (ci pensa la chiusura automatica) |
| da archiviare | `close` | **principale** → 🏁 Chiudi la Giornata N |
| conclusa | `recap` | — |

Il ramo `seasonBreak()` di `renderHero` è intatto: nella pausa fra due stagioni resta
«Rivivi la Stagione N».

> **Attenzione al `tick`.** La hero si riadegua dentro `startCountdown()`, confrontando
> `heroTodoKey()` con `lastHeroTodo`. Da lì si chiamano `renderHero()` e `renderMdCenter()`,
> **mai `renderMatchday()`**: quella rifà partire `startCountdown()` → ricorsione.

### 45.8 Frasi dello splash più leggibili

`.sp-tip` da 13px `var(--muted)` a **15.5px, peso 600, colore `#dce8fb`**, con
`text-shadow` leggero e `letter-spacing` negativo. Il padding-bottom di `.sp-hero` da 116 a
**138px**, perché a quella dimensione la frase può andare a due righe.

### 45.9 Cose imparate

- **`display=''` invece di `'block'`** quando si riaccende un elemento (vedi 45.3).
- **Gli interruttori orfani si accumulano in silenzio**: in questa sessione ne sono saltati
  fuori **due** (`setCreditMode`, `setMaintenance`), entrambi con la funzione viva e il
  pulsante sparito, entrambi senza errori a runtime perché le `getElementById` restituivano
  `null` e il codice era difensivo. Vale la pena rifare ogni tanto il controllo «funzioni
  definite e mai richiamate».
- **Scrivere i patch script con scrittura atomica.** Uno script Python è morto su
  `UnicodeEncodeError` (surrogati `\ud83d\udcc5` scritti come stringa Python invece che
  come escape JS) *dopo* aver aperto il file in `'w'`: file troncato a 0 byte. Ricostruito
  rilanciando le patch dall'originale. Da allora: `write` su `.tmp` + `os.replace`.
- **Le emoji nei patch script** vanno scritte come escape JS (`\\ud83d\\udcca` in Python) o
  come carattere vero, mai come surrogato Python isolato.
- Il **validatore casereccio di parentesi** fallisce sui letterali regex: fallisce anche
  sull'`index.html` originale, quindi **l'autorità è `node --check`**, non lo scanner.

### 45.10 File toccati e collaudo

1. `index.html` (**nessuna SQL**, `sw.js` non toccato)

Verifiche fatte: `node --check` OK · 566 backtick pari · graffe e quadre bilanciate ·
annidamento di `v-settings` pulito · 893 `div` e 151 `button` bilanciati · id duplicati solo
i due preesistenti (`pagLb`, `pagShareWrap`) · chiavi Supabase al loro posto · 7040 → 7298
righe · logica della hero provata fase per fase in jsdom.

**Collaudo su iPhone:** le quattro righe di Regole della lega devono mostrare lo stato
giusto senza entrare; cambiando giorno/ora e tornando indietro il sottotitolo si aggiorna
da solo; «Riapri il sondaggio» deve far ricomparire la card del sondaggio in Home; nelle
Azioni avanzate non deve più esserci la programmazione; in Aiuto e manutenzione solo il
super-admin vede «App offline»; a partita giocata la Home dice «Partita in corso · Inserisci
i risultati».

### 45.11 In sospeso

- **Revisione del login** (nuovo, vedi `PROSSIMI_PASSI.md` §1): email+password con OTP come
  ripiego, valutazione di Google Sign-In.
- **Cookie e analytics** (nuovo, `PROSSIMI_PASSI.md` §2): nessun banner finché lo storage è
  solo tecnico; se si aggiungono statistiche, banner **solo sulla landing**.
- Sparkline della posizione nella scheda manager: serve una RPC che esponga
  `_season_rank_history`.
- Split `/` landing + `/app/` gioco, con gli `url` delle push da cambiare in `notify.ts`.
- Privacy policy e termini, da scrivere insieme alla landing.
- Multi-lega per `sondaggio.html` (aperto da tempo).

---

## 46. SESSIONE 46 — LOGIN A PASSWORD: una sola strada per entrare, codice OTP solo per verificare l'email

Il login passa da **Email OTP a ogni accesso** a **email + password**. Un solo `index.html`,
**nessuna SQL**, `notify.ts` / `sw.js` / `admin.html` / `manifest.webmanifest` non toccati.
`APP_VERSION` → `v11`.

Il criterio: **una sola porta d'ingresso**. Due strade parallele significano due cose da
spiegare, due che si rompono, e nessuno che impara bene la strada. Il codice via email non
è più un modo per entrare: serve solo a dimostrare che l'email è tua, e succede due volte
in tutta la vita di un account (registrazione e recupero).

### 46.1 Come si entra adesso

| Chi | Cosa fa |
|---|---|
| Utente nuovo | Registrati → email + password → codice a 6 cifre (conferma l'email) → dentro |
| Chi c'era già, loggato | Apre l'app → schermata «Scegli la tua password» → dentro. **Nessuna email** |
| Tutti, dalla volta dopo | Email + password |
| Password dimenticata | Email → codice → nuova password → dentro |

Restare loggati funzionava già e continua a funzionare: `supabase-js` tiene la sessione in
`localStorage` e rinnova il token da solo. Chi viene buttato fuori è quasi sempre iOS, che
cancella lo storage dopo 7 giorni di inattività **sui siti non installati** (la PWA aggiunta
alla Home è esente): un motivo in più per spingere l'installazione.

### 46.2 Niente link nelle email — solo codici

Il magic-link era già stato abbandonato perché si rompe nella PWA in standalone su iOS. La
stessa trappola si ripresenta identica col recupero password: `resetPasswordForEmail` +
`redirectTo` è esattamente quel punto. Perciò **registrazione e recupero passano dal codice**
(`{{ .Token }}`) e da `verifyOtp`, con `type:'signup'` e `type:'recovery'`.

**Trappola trovata in collaudo (importante).** Il link di recupero non è solo "un'altra
strada": porta un token che Supabase **consuma da solo aprendo la sessione**. L'app, vedendo
un utente valido, mandava dritti in home — dentro l'account, con la vecchia password ancora
buona e nessuna schermata per cambiarla. Ora è intercettato in **due punti**, perché uno
solo non basta:

1. **all'avvio**, leggendo `type=recovery` dall'indirizzo *prima* di creare il client (dopo
   sarebbe tardi: il listener fa in tempo a portare dentro);
2. **sull'evento `PASSWORD_RECOVERY`** del listener, che è la rete più affidabile perché con
   certi tipi di link il token nell'indirizzo non si vede.

In entrambi i casi si finisce su `gateEnterRecovery()` → schermata della nuova password, e
l'indirizzo viene ripulito così un refresh non rimette in moto niente. Il template
«Reset Password» **non contiene più link**: la rete resta accesa solo per le email vecchie,
valide finché non scadono.

### 46.3 Il ponte per chi c'era già (niente SQL)

Chi usava l'app prima di questa versione non ha una password ma **è già dentro con una
sessione valida**: `updateUser({password})` funziona senza email e senza codice. Alla prima
apertura compare `#pwsetup` — 🔑 *Scegli la tua password*, email in vista, un campo, tre
motivi, un pulsante.

Per sapere chi l'ha già fatta si usano i **metadati dell'utente in Supabase Auth**
(`user_metadata.has_pw`), scritti dallo stesso `updateUser` e letti dalla sessione: **nessuna
colonna nuova, nessuna migrazione**. Chi si registra da oggi nasce con `has_pw:true` e quella
schermata non la vede mai.

`«Lo faccio dopo»` non salva niente: alla riapertura la schermata torna. Scelta voluta —
insistere sì, chiudere un amico fuori dalla sua app no.

### 46.4 Errori: rossi, e distinti fra loro

`gateStatus(msg, bad)` separa avviso e informazione: gli errori sono `var(--red)`, grassetto,
dentro un riquadro che compare solo se c'è testo (`:not(:empty)`); le informazioni restano
azzurre. Il rosso sparisce da solo quando l'operazione riesce.

`authErrIt()` traduce i messaggi di Supabase in italiano **distinguendo casi con rimedi
diversi**: credenziali sbagliate ≠ email non confermata ≠ password già usata ≠ troppi
tentativi. Due casi meritano attenzione:

- **email già registrata:** con la conferma attiva Supabase **non dà errore**, restituisce un
  utente finto con `identities: []` (per non far scoprire a un estraneo chi è iscritto). Se
  non lo si intercetta a mano, la persona resta ad aspettare un codice che non arriverà mai.
- **email mai confermata:** invece di lasciare su «credenziali sbagliate», l'app rimanda da
  sola il codice (`auth.resend`, con ripiego su `signInWithOtp` se il metodo manca) e porta
  al passo successivo.

### 46.5 Cosa c'è nel file

- `#gate` a tre schermate + tre passi: `gateMode` = login | signup | reset, `gateStage` =
  form | code | newpw. `gateSet()` / `gateGo()` / `gateBack()` / `gateShowCode()` /
  `gateShowNewPw()` / `gateEnterRecovery()`.
- Campo password con **Mostra/Nascondi testuale**, non emoji: iOS le disegna quasi nere e sul
  fondo blu sparirebbero (stessa ragione del «+» nella `ctx-box`).
- Da «Crea la tua lega» / «Entra in una lega» il gate apre su **Registrati**; da «Accedi» su
  **Accedi**. La `ctx-box` viola/verde è rimasta dov'era.
- In Accedi c'è **«Non ne hai mai avuta una? Impostala qui»** → porta al recupero: è lo stesso
  percorso, chiamato con le parole giuste.
- Impostazioni → Profilo: card **Password** (cambio password, e ripiego per chi ha rimandato).
- Codice OTP a **6 cifre** (impostato lato Supabase): campo `maxlength="6"`, placeholder
  `123456`.

### 46.6 Configurazione Supabase richiesta

1. **Authentication → Emails → «Reset Password»**: template riscritto con `{{ .Token }}` e
   **senza** `{{ .ConfirmationURL }}` → nessun link nell'email.
2. **«Confirm signup»**: deve contenere `{{ .Token }}` (c'era già).
3. **Sign In / Providers → Email**: *Minimum password length* = 8, *Confirm email* acceso.
   Spegnerlo permetterebbe di registrarsi con l'email di un altro e prendersi il recupero.
4. Lunghezza OTP portata a **6 cifre**.

### 46.7 Verifiche fatte

`node --check` OK su entrambi gli script inline, 566 backtick pari, 912 div e 158 button
bilanciati, id duplicati solo i due preesistenti (`pagLb`, `pagShareWrap`), 7298 → 7697 righe.
Le tre schermate sono state fatte girare in **jsdom con un finto Supabase**: 86 prove su 17
gruppi (registrazione, accesso, recupero col codice, recupero col link, `#pwsetup`,
navigazione, errori in rosso, traduzioni). Il collaudo ha trovato **un errore vero**:
`«New password should be different»` finiva nel controllo della lunghezza (contiene «Password
should be») e avrebbe detto «password troppo corta» a chi riusava la vecchia password —
corretto invertendo l'ordine dei controlli.

### 46.8 In sospeso

- Cookie e analytics (`PROSSIMI_PASSI.md` §1): banner **solo sulla landing**.
- Sparkline della posizione nella scheda manager: serve una RPC che esponga
  `_season_rank_history`.
- Split `/` landing + `/app/` gioco, con gli `url` delle push da cambiare in `notify.ts`.
- Privacy policy e termini, da scrivere insieme alla landing.
- Multi-lega per `sondaggio.html` (aperto da tempo).
- Google Sign-In: rimandato, non urgente ora che la password rende l'accesso immediato.
  «Sign in with Apple» richiede l'Apple Developer Program (99 $/anno).

## 47. SESSIONI 47-48 — VETRINA PUBBLICA: prima stesura e restyle

> File: `sito.html`, `sito.css`, `regolamento.html`, cartella `sito/`. **L'app non è toccata**:
> `index.html`, `sw.js`, `manifest.webmanifest` e le icone sono rimasti identici.
> Dove in conflitto con la §6 di `PROSSIMI_PASSI.md`, **vale questa**.

### 47.1 Cos'è

Vetrina pubblica in prova su `/sito.html` (ancora `noindex`), che allo spostamento della §3
diventerà `/index.html` con il gioco in `/app/`. Stessi colori e caratteri dell'app, ma con
regole da sito: testo selezionabile, scroll normale, niente `position:fixed`.
`regolamento.html` è la pagina di dettaglio dei punteggi e condivide `sito.css`.

### 47.2 Struttura (dopo il restyle)

Barra in alto (marchio · voci · «Gioca ora» · tre righe) → apertura → **Anteprima**
(`#anteprima`) → **Come funziona** (`#come-funziona`) → **Funzioni** (`#funzioni`) →
**Installazione** (`#installa`) → **Punteggi** (`#punteggi`) → **Domande** (`#domande`) →
chiusura. Sei sezioni, circa metà dello scroll della prima stesura.

Sparite nel restyle: il campo interattivo che cambiava modulo in apertura, il blocco «Cos'è»
a due colonne, la galleria in fondo (diventata l'apertura), i riquadri statistici
(5 in campo / 100 crediti / 38 giornate / 0 €) e **il calcolatore dei punti**. Quest'ultimo
è una buona notizia per l'invariante del punteggio: la formula non vive più in tre posti,
solo in `scoreOf()` e `get_standings_md`. Al suo posto una griglia statica di dieci riquadri.

### 47.3 Il carosello — un solo componente

`.crsl` > `.crsl-track` > `.crsl-item`, usato in **quattro** punti: schermate dell'anteprima,
gli otto passaggi, installazione iPhone, installazione Android. Scorrimento a scatti
(`scroll-snap`), **puntini e frecce li crea lo script** (`initCrsl`) così l'HTML resta pulito;
senza JS resta comunque una fila che si scorre col dito. `paint()` nasconde tutta la
navigazione quando le schede ci stanno già in larghezza.

⚠️ **Il pannello nascosto ha larghezza zero.** `setTab()` deve richiamare `sync()` sul
carosello che torna visibile, altrimenti i puntini restano fermi sul primo.

### 47.4 La scocca del telefono — la lezione

Le proporzioni vanno su **`.phone-screen`**, non su `.phone`:

```css
.phone{padding:8px}                                   /* niente aspect-ratio qui */
.phone-screen{width:100%;aspect-ratio:var(--ar, 640/1306)}
```

Mettendole sulla scocca, la cornice da 8 px falsa il rapporto di un paio di punti percentuali
e `object-fit:cover` mangia i lati dello screenshot. Con `--ar` sullo schermo il ritaglio è
esatto: nessun bordo vuoto, niente tagliato. Le schermate dell'app sono **640×1306**, quelle
dell'installazione **640×1387**, e `--ar` si passa in linea (`style="--ar:640/1387"`).

Il notch nero (`.phone::after`) è stato **rimosso**: copriva la prima riga degli screenshot
dell'installazione. Variante **`.phone.and`** per Android: angoli a 22 px invece di 40,
cornice più sottile e grigia invece che blu.

### 47.5 Il cerchio rosso delle istruzioni

`<span class="hot" style="--x:..%;--y:..%;--w:..%;--h:..%">` dentro `.phone-screen`: anello
rosso pulsante con il puntatore del mouse (SVG in `background`, data-URI) in basso a destra.
Non è un cerchio fisso ma un rettangolo arrotondato: sulle voci di menu diventa una pillola
che avvolge la riga intera. Le percentuali sono relative allo screenshot, e valgono **solo**
perché `.phone-screen` ha lo stesso rapporto dell'immagine (§47.4).

Valori attuali — se si rifà uno screenshot vanno rimisurati:

| file | --x | --y | --w | --h | cosa indica |
|---|---|---|---|---|---|
| ios-1 | 85% | 93.2% | 13% | 6% | il `•••` di Safari |
| ios-2 | 49% | 61% | 26% | 3.6% | voce «Share / Condividi» |
| ios-3 | 35.5% | 95% | 56% | 3.4% | «Add to Home Screen» |
| ios-4 | 87.8% | 12.5% | 18% | 4.2% | pulsante «Add» |
| ios-5 | 15.3% | 48.5% | 19% | 8.5% | icona sulla Home |
| and-1 | 90% | 7.4% | 10% | 4.4% | menu `⋮` di Chrome |
| and-2 | 56.5% | 56.8% | 54% | 4% | «Installa e crea scorciatoia» |
| and-3 | 81.9% | 60.3% | 17% | 3.4% | pulsante «Installa» |
| and-4 | 15.2% | 73.4% | 19% | 9% | icona sulla Home |

**Metodo:** disegnare il rettangolo sull'immagine con PIL e guardarlo, non stimare a occhio.
Per gli ultimi due sono state trovate le coordinate esatte per colore (il blu del testo
«Installa», il blu scuro dell'icona sul verde acqua dello sfondo).

### 47.6 Le immagini

Convenzione: **larghezza 640, WebP qualità 82**, nella cartella `sito/`.

- **Schermate dell'app** (`01`…`14`): barra di stato tagliata (primi 150 px), risultato 640×1306.
- **Schermate dell'installazione** (`ios-*`, `and-*`): **niente ritaglio**, 640×1387. Sembrava
  più pulito tagliare la barra di stato, ma il `⋮` di Chrome finiva così vicino al bordo che
  il cerchio rosso usciva dallo schermo.
- **Sfocature** (privacy): contatti WhatsApp in `ios-3`, tutte le app tranne FantaCalcetto in
  `ios-5` (dock compreso) e in `and-4`. Fatte con `ImageFilter.GaussianBlur(15)` su rettangoli
  espliciti: se si rifanno gli screenshot vanno rifatte.

**Mancano ancora:** `02-campo`, `06-voti`, `07-presenze`, `12-bonus` (inserimento gol/assist/
risultato), `13-lega` (creazione lega), `14-profilo` (creazione squadra e giocatore) e
`sito/anteprima.png` 1200×630 per i link su WhatsApp. Finché mancano si vede un segnaposto
tratteggiato col nome del file: la pagina non si rompe. Nel carosello dell'anteprima i due
mancanti sono **commentati** apposta, perché in cima alla pagina un riquadro tratteggiato
sarebbe la prima cosa che si vede.

### 47.7 Menu e navigazione

Sopra i **1120 px** le sei sezioni stanno in fila nella barra in alto, con la sottolineatura
blu su quella corrente. Sotto, compaiono le tre righe (`.burger`) e le stesse voci si aprono
in una tendina da destra (`.drawer` + `.scrim`), che si chiude toccando una voce, lo sfondo o
Esc. Lo scroll-spy evidenzia la sezione in tutti e due i menu (`[data-nav]`).

Prima del restyle c'era una barra di pastiglie appiccicata sotto il titolo: si vedeva poco ed
è stata buttata.

### 47.8 Regole di scrittura decise in sessione

- Testi asciutti, non romanzati. La prima stesura è stata accorciata di circa un terzo, il
  restyle di un altro terzo.
- **Imperativo, non seconda persona indicativa**: «Schiera», non «Schieri»; «Vota», non
  «Vi votate».
- Un solo pulsante d'azione, ovunque: **«Gioca ora»**.
- Titoli seri e descrittivi: *Uno sguardo all'app*, *Come funziona*, *Cosa contiene l'app*,
  *Come installarla sulla Home*, *Bonus, malus e moltiplicatori*, *Domande frequenti*,
  *Inizia dalla prossima partita*.
- «Come funziona» copre **tutto il percorso**, non solo la giornata: crea la lega → crea
  squadra e giocatore → apertura → presenze → formazione → bonus e malus → voti → classifica.
- I **soli manager** (`profiles.is_player=false`) sono detti sia nel secondo passaggio sia
  nelle domande frequenti: chi non gioca a calcetto ha la squadra, non prende voti, non
  compare nel sondaggio presenze, e vota solo se l'organizzatore glielo concede.

### 47.9 Invarianti nuove

- **La vetrina non deve essere installabile**: mai `<link rel="manifest">` né service worker
  in `sito.html`, altrimenti sulla Home finisce la vetrina invece del gioco.
- `APP_URL` in fondo a `sito.html` e `regolamento.html` è **l'unico punto** da cambiare allo
  spostamento (`'/'` → `'/app/'`).
- La versione di `sito.css` (`?v=N`) va alzata **in tutte e due le pagine** a ogni modifica
  del foglio, altrimenti `regolamento.html` carica dalla cache un CSS che non esiste più.
- Gli `id` delle sezioni sono citati da `regolamento.html`: cambiandoli si rompono i link
  della sua barra in alto (è già successo con `#dentro` → `#funzioni`).

## 48. NOTA — apertura della giornata: i casi limite

Chiarimento nato da una domanda in sessione 48. Nessun codice cambiato, solo messo per
iscritto come si comporta l'app oggi.

### 48.1 Le due strade non sono equivalenti

- **Automatica.** Giorno e ora salvati in Regole della lega; il cron (ogni 10 min) chiama
  `open_due_matchdays()`, che apre quando *adesso* cade nella finestra **[K−72h, K)**.
  Ciclo intero: sondaggio presenze fino a K−36h, promemoria, chiusura automatica.
- **«Apri subito».** Mette **sempre** `skip_poll=true`: niente sondaggio, formazioni aperte
  all'istante, presenti segnati a mano dall'admin. Non esiste, nell'interfaccia, un modo di
  aprire a mano una giornata **con** il sondaggio: la vecchia modalità Manuale è stata tolta
  in §27.5 e il pulsante è tornato in §40 solo in questa forma.

### 48.2 Presenze a mano

Due casi diversi che finiscono uguali. Lega in **modalità admin** (`presence_self=false`): il
sondaggio non esiste mai, le presenze si segnano in «Chi gioca questa giornata», e con la
**rosa prevista** (`planned_presences` + trigger `seed_presences`) si possono impostare
*prima* dell'apertura. Giornata con **`skip_poll=true`**: il sondaggio è spento solo per
quella giornata. In entrambi i casi `mdTimes()` mette `presenceClose=0`, quindi le formazioni
risultano aperte da subito e le due push del ciclo presenze non partono.

### 48.3 Apertura in ritardo

`open_due_matchdays()` **non aspetta**: se la programmazione viene salvata quando si è già
dentro le 72h, la giornata si apre al primo giro di cron utile, con il ciclo compresso.

- Fra K−72h e K−36h: normale, il sondaggio resta aperto per il tempo che avanza.
- **Già dentro le 36h**: il sondaggio nasce chiuso (`presenceClose` nel passato) → formazioni
  subito aperte. Il promemoria presenze (K−38h) non parte più, la push «presenze chiuse,
  schiera» parte al primo giro. ⚠️ **Rischio vero:** in modalità giocatori nessuno ha votato
  la presenza, quindi `matchday_players` è vuoto e **non c'è nessuno da schierare**. La via
  d'uscita è la card admin «Chi gioca questa giornata», che a giornata aperta compare anche
  in modalità giocatori. Vale la pena ricordarselo prima di aprire tardi.
- **Kickoff già passato**: la finestra è chiusa, non apre niente e aspetta la settimana dopo.
  Non è un guasto — è quello che è successo nella lega di prova. Per giocare oggi serve
  «Apri subito».

I promemoria a scadenza (formazioni −8h, ultima ora −1h) partono comunque al primo giro utile
se il loro momento è già passato ma il blocco non è ancora scattato.

### 48.4 Chi può fare cosa

- **Operazioni di giornata** (Centro giornata, pannello partita, «Chi gioca», annulla
  giornata): proprietario **e vice** — `is_operator()` nel database, `canOp()` nel client.
- **Regole della lega, Stagione, Gestione giocatori, Sondaggio valori, Manutenzione,
  Vice-admin**: **solo il proprietario** — `is_admin()` / `profile.is_admin`.
- Un giocatore normale non vede né l'una né l'altra cosa.

⚠️ **Fragilità nota.** Il client controlla `canOp() = opRole.can_operate || profile.is_admin`,
cioè gli basta la **colonna** `profiles.is_admin`; il database controlla `is_operator()`, che
guarda **`leagues.admin_id`**. Sono allineate da un trigger, ma se per qualsiasi motivo
divergono il sintomo è: pannello admin aperto, scrittura rifiutata con
`new row violates row-level security policy for table "matchdays"`. Diagnosi:

```sql
select l.id as lega, l.name, l.admin_id,
       p.id as profilo, p.team_name, p.player_name, p.is_admin
from leagues l left join profiles p on p.league_id = l.id
order by l.id, p.team_name;

select proname, prosecdef from pg_proc
where proname in ('is_operator','is_admin','my_league');
```

Se per una lega `admin_id` non è l'`id` del profilo che dovrebbe comandarla, il colpevole è
quello. Se `prosecdef` di `is_operator` è `false` il problema è più grosso: `leagues` ha RLS
senza policy, quindi una funzione non-definer non riesce a leggerla e `is_operator()` torna
falso per tutti.
