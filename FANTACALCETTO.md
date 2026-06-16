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

**Generatore squadre (admin).** Impostazioni → "Crea le squadre": divide i presenti in due squadre equilibrate per **valore** (`players.valore`, o medie del sondaggio per nome, o 5.5 di default) e per **ruolo**; si spostano i giocatori toccandoli (tap-to-move, affidabile su iOS); verde se le due squadre sono pari, rosso altrimenti. Alcuni nomi del sondaggio ≠ nomi in partita: c'è una mappa di alias `POLL_ALIAS` (Davide D→Davi Kakà, Rouge→Davi Rouge, Francesco Pio→Fra, Lorenzo→Lore Chiesa, Luca→Luchino, Gabry→Gabri).

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
Aggiunta `runAutoOpen()` chiamata nel ramo cron (prima di reminder e auto-close): invoca `open_due_matchdays()` e per ogni giornata aperta manda la push **"<Giornata> aperta! ⚽"** alla lega giusta. Risposta cron ora `{opened, reminders, closed}`. Resto invariato.

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
`migrazione_lega1_sondaggio.sql` (una tantum, dopo `sondaggio_valori.sql`): porta i voti di `credit_poll` (sondaggio.html, per nome) dentro `value_poll` per la **lega 1**, applicando gli alias dei nomi (Davide D→Davi Kakà, Rouge→Davi Rouge, Francesco Pio→Fra, Lorenzo→Lore Chiesa, Luca→Luchino, Gabry→Gabri), poi **calcola e applica i crediti** e imposta `credit_mode='poll'`, `value_poll_open=false`. Rilanciabile (ripulisce prima). **Dopo: `sondaggio.html` è rimovibile da GitHub.** La tabella `credit_poll` e `get_poll_results` restano (innocue, ancora dietro la vecchia card «Risultati sondaggio valori»).

### 24.4 Generatore squadre rimosso dall'app → tool separato
«Crea le squadre» **rimosso dall'app** (non adatto all'uso diffuso: altre leghe fanno le squadre da sé o hanno giocatori non del fanta). Tolti: card in Impostazioni, funzioni (`openTeamMaker`/`tmGenerate`/`tmMove`/`tmCol`/`renderTeamMaker`/`pollValueFor`/`tmStrength`), `POLL_ALIAS`, variabili `tmA/tmB/pollMap`, e il campo **Valore** nella scheda giocatore. La colonna `players.valore` resta in DB (innocua, preservata sugli edit) ma non è più usata/editabile in-app. CSS `.tm-*` lasciato (morto, innocuo).
Nuovo file **`crea_squadre.html`**: tool **personale offline** (nessun backend/chiave) — rosa salvata in `localStorage`, bilanciamento per forza+ruolo, tap-to-move, «Rigenera». Tool privato di Teo (non serve su GitHub).

### 24.5 File toccati
- `index.html` — restyle barre, sondaggio valori interno (wizard/home/overlay/admin), rimozione generatore + campo Valore.
- `sondaggio_valori.sql` — colonne+tabella+funzioni del sondaggio interno.
- `migrazione_lega1_sondaggio.sql` — migrazione una tantum del sondaggio esterno (lega 1).
- `crea_squadre.html` — tool separato (generatore squadre offline).
- (Ricorda: re-incollare le 2 chiavi Supabase a ogni upload di `index.html`.)
