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
2. **bonus/malus** (sommati, mai moltiplicati): gol **+3** · assist **+2** · autogol **−3** · se nello slot **POR** `+3` (imbattuto) o `−gol_subiti` · **risultato squadra reale** `+2` se la sua squadra di calcetto ha vinto, `−2` se ha perso (`match_stats.esito` = `V`/`S`/null).

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
- **Risultato squadra reale**: +2 se la sua squadra di calcetto vince, −2 se perde (`match_stats.esito` = `V`/`S`/null). L'admin lo imposta nella sezione Voti, bottoni Vittoria/Sconfitta (ritocco = togli).
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
