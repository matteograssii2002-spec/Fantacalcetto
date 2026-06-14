"""
fantacalcetto_context.py
========================

File di CONTESTO del progetto "Fantacalcetto".

Scopo: se apro una nuova chat con un assistente AI, gli do questo file (insieme a
FANTACALCETTO.md) così capisce subito cos'è l'app, com'è fatta e come continuare.

Eseguendolo (`python3 fantacalcetto_context.py`) stampa un briefing sintetico.

NOTE PER L'ASSISTENTE
---------------------
- Rispondere SEMPRE in italiano.
- L'utente (Giulio, display name "Teo") lavora da iPhone e non è uno sviluppatore:
  servono passi guidati, semplici, uno alla volta.
- Tutta l'app è UN UNICO file `index.html` (HTML+CSS+JS vanilla, script non-module).
- Per modificare: applicare le modifiche, VALIDARE i bracket {} () [] e i backtick,
  ripresentare il file intero, ricordare di RE-INCOLLARE le chiavi Supabase,
  e dire chiaro SE serve eseguire SQL e/o caricare nuovi PNG icona.
- Coerenza punteggio OBBLIGATORIA tra client (computeScore/scoreOf) e SQL
  (get_standings / get_standings_md). NB: risultato squadra reale = +/-1 (non +/-2);
  crediti alla chiusura = metodo a ranking (vedi MATCHDAY_LIFECYCLE).
- App multi-lega: ogni gruppo e' una lega (league_id ovunque, isolamento via RLS/my_league()).
  Il gruppo originale e' la lega #1 'La Fossa di Lissone'.
"""

# ---------------------------------------------------------------------------
# OVERVIEW
# ---------------------------------------------------------------------------
APP = {
    "nome": "Fantacalcetto",
    "cos_e": "Fantasy game per un gruppo che gioca a calcetto a 5 una volta a settimana.",
    "doppio_ruolo": "Ogni utente è sia giocatore (nel listone) sia fanta-manager.",
    "giornate": "Budget 100 cr, si schierano 5 giocatori (20 cr l'uno), formazione rifatta ogni giornata.",
    "classifica": "Unica e condivisa, per punti totali stagionali.",
    "solo_manager": "Modalità per chi non gioca a calcetto: ha la squadra ma non entra nel listone (profiles.is_player=false).",
    "lingua": "italiano",
    "utente": "Giulio / 'Teo', su iPhone, non sviluppatore",
}

# ---------------------------------------------------------------------------
# STACK & HOSTING
# ---------------------------------------------------------------------------
STACK = {
    "frontend": "Un unico index.html (HTML+CSS+JS vanilla). supabase-js UMD via CDN, poi <script> non-module.",
    "tema": "Blu scuro; campo verde. Font: Bricolage Grotesque, Hanken Grotesk, JetBrains Mono.",
    "backend": "Supabase (progetto 'Fantacalcetto').",
    "repo_github": "Fantacalcetto (utente matteograssii2002)",
    "vercel_url": "https://fantacalcetto-zeta.vercel.app",
    "dominio": "fantacalcettoitalia.it (principale www; apex 308->www)",
    "dns_aruba": {
        "A @": "216.198.79.1",
        "CNAME www": "5bb2fdcd25437f2d.vercel-dns-017.com.",
        "ATTENZIONE": "Non toccare i record email; non cambiare i nameserver (restano Aruba).",
    },
    "icone": "icon-180.png (apple-touch-icon) e icon-512.png (manifest) nella root del repo.",
}

# ---------------------------------------------------------------------------
# DEPLOY WORKFLOW (come si aggiorna)
# ---------------------------------------------------------------------------
DEPLOY = [
    "1. Scarica l'ultimo index.html (contiene SEMPRE tutte le modifiche precedenti).",
    "2. Incolla le chiavi Supabase in cima allo <script> (il file consegnato ha placeholder).",
    "3. Carica su GitHub rinominando in index.html (Add file -> Upload files).",
    "4. Vercel ridistribuisce in ~1 minuto.",
    "5. Se cambia l'icona: carica i PNG e rimuovi/ri-aggiungi la PWA alla home (iOS).",
]

CONFIG_KEYS = {
    "SUPABASE_URL": "https://<PROGETTO>.supabase.co (Settings -> API / Connect)",
    "SUPABASE_ANON": "Publishable key sb_publishable_... (NON la sb_secret_)",
    "nota": "Le chiavi vanno reincollate ogni volta che si ricarica il file intero.",
}

# ---------------------------------------------------------------------------
# REGOLE DI GIOCO E PUNTEGGIO  (devono coincidere tra client e DB)
# ---------------------------------------------------------------------------
PRICE = 20            # costo di default di ogni giocatore (modificabile per giocatore: players.cost)
BUDGET = 100          # crediti per giornata
FIELD_SIZE = 5        # giocatori in campo
# Tre moduli scelti dal manager (salvati in lineup_modules). Bonus di partenza per il manager:
MODULES = {
    "1-2-2": {"bonus": 0,  "slots": ["a1", "a2", "d1", "d2", "g1"]},   # default (2 ATT, 2 DIF, 1 POR)
    "1-3-1": {"bonus": 5,  "slots": ["a1", "d1", "d2", "d3", "g1"]},   # parti +5 (1 ATT, 3 DIF)
    "1-1-3": {"bonus": -5, "slots": ["a1", "a2", "a3", "d1", "g1"]},   # parti -5 (3 ATT, 1 DIF)
}
SLOTS_ALL = ["a1", "a2", "a3", "d1", "d2", "d3", "g1"]  # vincolo lineups_slot_check ammette questi
SLOT_RULES = {
    "aN (ATT)": "accettano solo giocatori ATT",
    "dN (DIF)": "accettano solo giocatori DIF",
    "g1 (POR)": "accetta chiunque (bonus/malus portiere applicati solo in questo slot)",
}

SCORING = {
    "formula_giocatore": "voto*moltiplicatore + bonus  (i bonus NON sono moltiplicati)",
    "voto": "media dei voti ricevuti; 6 di default se nessun voto",
    "moltiplicatore (solo sul voto)": "x2 se MVP, x2 se Capitano, cumulabili -> x4",
    "bonus": "gol +3, assist +2, autogol -3",
    "portiere (solo slot g1)": "+3 se 0 gol subiti, altrimenti -gol_subiti (e' un bonus, NON moltiplicato)",
    "risultato squadra reale": "+1 se la sua squadra di calcetto vince, -1 se perde (match_stats.esito = V/S/null). NB: cambiato da +/-2 a +/-1.",
    "bonus modulo (una volta per manager)": "1-2-2: 0 | 1-3-1: +5 | 1-1-3: -5",
    "punti_manager_giornata": "bonus_modulo + somma punti dei 5 giocatori",
    "MVP": "il piu nominato dal gruppo (parita: id piu basso), x2 sul voto",
    "SEGA": "RIMOSSA (si vota solo MVP + i voti 1-10). nominations.sega_player_id resta legacy = null",
}


def score_player(slot, is_captain, media_voti=6.0, gol=0, assist=0, autogol=0,
                 gol_subiti=0, is_mvp=False, esito=None):
    """Riferimento Python di scoreOf (client) e get_standings_md (SQL).
    Capitano/MVP raddoppiano SOLO il voto; i bonus restano piatti. esito: 'V'/'S'/None.
    NB: il bonus modulo (+5/-5) si somma una volta a livello di manager, non qui."""
    mult = (2 if is_mvp else 1) * (2 if is_captain else 1)
    bonus = gol * 3 + assist * 2 - autogol * 3
    if esito == "V":
        bonus += 1
    elif esito == "S":
        bonus -= 1
    if slot == "g1":  # portiere
        bonus += 3 if gol_subiti == 0 else -gol_subiti
    return media_voti * mult + bonus


# ---------------------------------------------------------------------------
# CICLO GIORNATA (admin)
# ---------------------------------------------------------------------------
MATCHDAY_LIFECYCLE = {
    "apri": "scegli kickoff. blocco formazioni=kickoff-1h, voti aperti=kickoff+1h, voti chiusi=+24h. ALL'APERTURA NESSUNO E' PRESENTE (mdPresent vuoto): l'admin sceglie i presenti ogni giornata (prima erano tutti presenti di default).",
    "moduli": "il manager sceglie 1-2-2 / 1-3-1 / 1-1-3 prima del kickoff (salvato in lineup_modules); cambiare modulo svuota la formazione.",
    "presenti": "card 'Chi gioca questa giornata' -> matchday_players. solo presenti schierabili/votabili; assenti opachi nel mercato. All'apertura tutti deselezionati.",
    "bonus_malus": "PANNELLO PARTITA LIVE (non piu' tendina per giocatore). Impostazioni admin -> '📊 Apri pannello partita' (#liveOpenBtn) -> overlay full-screen #liveStats: blocchi grandi GOL/ASSIST/PORTIERE + AUTOGOL, tap giocatore = +1 (vibra), '-' per annullare; bozza salvata in localStorage (fc_live_<mdId>) cosi' sopravvive alla chiusura app; step finale 'Chi ha vinto?' (seleziona vincitori = +1, presenti non scelti = -1, nessuno = pari) -> esito V/S/'' per tutti i presenti; 'Conferma e salva' upserta tutto in match_stats. Apribile da kickoff-30min finche' la giornata non e' chiusa (matchWindow/matchOpenable).",
    "chi_vota": "solo chi ha giocato (suo personaggio presente) + admin + manager abilitati (extra_voters). canIVote() lato app.",
    "genera_squadre": "admin: divide i presenti in 2 squadre equilibrate per valore (players.valore o medie sondaggio o 5.5) e ruolo; tap-to-move; verde se pari, rosso altrimenti.",
    "chiudi": "AUTO-CHIUSURA LATO SERVER: close_due_matchdays() (cron ogni 10min via notify.ts) chiude le giornate con now()>=kickoff+25h, applica i crediti e manda la push 'chiusa' della lega. Non dipende dall'admin. L'admin puo' comunque chiudere a mano. Alla chiusura: status='closed'+closed_at=now(), reset locale (clearRoundLocal svuota formazione/capitano/modulo/voti/MVP/medie).",
    "reset": "rpc reset_matchday(md): solo admin della stessa lega; cancella giornata e TUTTI i figli (formazioni/voti/nomination/stat/presenze).",
    "presenza_statistica": "conta solo da blocco formazioni (kickoff-1h) o se closed; aprire una giornata non genera piu presenze.",
    "crediti_chiusura": "NUOVO METODO (non piu' delta-voto). Solo sui presenti: (1) ranking-credito per cost desc (parita=media); (2) ranking-punti per voto+0.5*(gol*3+assist*2-autogol*3-gol_subiti) [voto medio, no clean-sheet, no esito/MVP/cap/modulo]; (3) scarto=rank_credito-rank_punti; (4) ordina per scarto desc, parita=cost asc: top3 +2/+1/+1, bottom3 -2/-1/-1, in mezzo invariati (clamp 1..100); (5) trend smallint 1/-1/0 -> forma (In forma/In calo/Costante). Funzioni: _apply_credits_core(md) + apply_credit_changes(md) [admin].",
    "classifica": "somma SOLO le giornate closed: la giornata in corso (e il bonus modulo) compare solo quando viene chiusa.",
    "formazioni_avversarie": "nascoste finche la partita non inizia (kickoff o closed). selettore Lega nasconde le giornate non ancora iniziate.",
    "status_validi": ["open", "voting", "locked", "closed"],
}

# ---------------------------------------------------------------------------
# MODELLO DATI (colonne come usate dall'app)
# ---------------------------------------------------------------------------
SCHEMA = {
    "leagues": "NUOVA. id bigserial, name, slug unique, password text(in chiaro), admin_id uuid(=creatore), created_at. RLS attiva SENZA policy dirette: si legge/scrive SOLO via funzioni security definer (la password non e' mai esposta ai client).",
    "league_id (OVUNQUE)": "Tutte le tabelle dati hanno league_id bigint default 1 references leagues(id). La lega #1 e' 'La Fossa di Lissone' (il gruppo originale). Le scritture vengono 'timbrate' da un trigger (stamp_league) con coalesce(my_league(),1).",
    "profiles": "id uuid(=auth.uid()), team_name, player_name, role, avatar, is_admin bool(DERIVATO dal trigger: true se sei admin_id della tua lega), is_player bool(def true), league_id",
    "players": "id bigint, name, role(ATT/DIF), avatar, present bool, forma int(legacy), trend smallint(1/-1/0 -> forma), owner_id uuid, injured bool, cost int(def20), valore numeric(forza 1-10, ADMIN-only), league_id",
    "matchdays": "id bigint, label, kickoff timestamptz, status(open/voting/locked/closed), closed_at timestamptz, reminder_sent bool, cost_applied bool, league_id",
    "lineups": "matchday_id, manager_id uuid, slot(a1,a2,a3,d1,d2,d3,g1), player_id, is_captain bool, league_id. CHECK lineups_slot_check su quei 7 slot",
    "lineup_modules": "matchday_id, manager_id uuid, module(1-2-2/1-3-1/1-1-3), league_id  (PK composta)",
    "votes": "matchday_id, voter_id uuid, player_id, score numeric(1-10, anche mezzi), league_id",
    "match_stats": "matchday_id, player_id, gol, assist, autogol, gol_subiti, esito(V/S/null = risultato squadra reale), league_id",
    "nominations": "matchday_id, voter_id uuid, mvp_player_id, sega_player_id(legacy, sempre null), league_id",
    "matchday_players": "matchday_id, player_id (PK), league_id. NB: presenza statistica solo da blocco formazioni",
    "extra_voters": "profile_id uuid PK, league_id  (manager-solo abilitati al voto)",
    "credit_poll": "voter text pk, ratings jsonb, created_at, league_id (sondaggio resta di fatto sulla lega 1 finche' non si rende multi-lega la pagina sondaggio.html)",
    "push_subscriptions": "endpoint pk, user_id uuid, sub jsonb, created_at, league_id (notifiche inviate solo alla propria lega)",
    "app_state": "id, maintenance bool, league_id. UNA RIGA PER LEGA (la #1 ha id=1). Manutenzione ora per-lega.",
    "storage_bucket": "avatars (pubblico): PNG degli avatar, listati e usati via URL pubblico (condiviso tra tutte le leghe)",
}

RPC = {
    "is_admin()": "bool, helper RLS (legge profiles.is_admin, ora derivato dalla proprieta' lega)",
    "my_league()": "NUOVA. bigint: la lega dell'utente corrente (profiles.league_id). Usata da RLS e dalle funzioni per isolare i dati.",
    "get_averages(md)": "media voti per player nella giornata",
    "get_mvp_sega(md)": "id MVP (e SEGA, ormai ignorato)",
    "get_standings()": "classifica SOLO giornate closed della propria lega + delta posizione (frecce 24h).",
    "get_standings_md(md)": "classifica di giornata (filtra i manager della lega della giornata): voto*mult(solo voto)+bonus+esito(+/-1)+bonus modulo.",
    "get_player_stats()": "presenze, gol, assist, voto_medio, forma(da trend) della propria lega.",
    "list_solo_managers()": "(admin) profili solo-manager della lega con flag voto.",
    "apply_credit_changes(md)/_apply_credits_core(md)": "crediti alla chiusura col NUOVO metodo a ranking (vedi MATCHDAY_LIFECYCLE.crediti_chiusura).",
    "close_due_matchdays()": "NUOVA (service_role). Chiude TUTTE le leghe con giornate scadute (kickoff+25h), applica crediti, restituisce (closed_id,closed_label,closed_league). Chiamata dal cron in notify.ts.",
    "get_poll_results()": "(admin) medie sondaggio valori della propria lega",
    "reset_matchday(md)": "(admin stessa lega) cancella giornata + tutti i figli (presenze incluse)",
    "--- LEGHE (per Crea/Entra) ---": "",
    "slugify(text)": "genera lo slug della lega",
    "create_league(name,password)": "crea la lega (admin=creatore) + riga app_state; ritorna id/name/slug",
    "find_leagues(query)": "cerca leghe per nome (NO password)",
    "league_by_slug(slug)": "info lega dal link d'invito ?lega=slug (NO password)",
    "verify_league(id,password)": "verifica password, ritorna la lega se ok",
    "onboard_join(league,password,team,player,role,avatar,is_player)": "crea il profilo nella lega scelta; controlla password e unicita' nome squadra/giocatore nella lega (errori: team_taken/player_taken/'password errata')",
    "get_my_league()": "nome/slug della propria lega (per il badge in Home/Lega)",
    "get_league_admin_info()": "(solo admin della lega) name/slug/password per il pannello invito",
}

# ---------------------------------------------------------------------------
# AUTH & EMAIL
# ---------------------------------------------------------------------------
AUTH = {
    "metodo": "Email OTP: signInWithOtp -> verifyOtp({type:'email'}) con codice 6 cifre.",
    "perche": "il magic-link si rompeva nella PWA iOS (storage separato in standalone).",
    "template": "'Magic Link' e 'Confirm signup' mostrano entrambi {{ .Token }}.",
    "smtp": "Resend (smtp.resend.com:587, user 'resend', pass = API key re_...).",
    "mittente": "accesso@fantacalcettoitalia.it (dominio verificato su Resend, DKIM/SPF/MX su Aruba).",
    "admin": "update profiles set is_admin=true where id='<UID>';",
}

# ---------------------------------------------------------------------------
# FEATURE PRINCIPALI (e dove stanno)
# ---------------------------------------------------------------------------
FEATURES = {
    "leghe": "NUOVO. Al primo accesso (nessun profilo) schermata #league: '🔑 Entra in una lega' (cerca per nome o link d'invito ?lega=slug + password) oppure '➕ Crea una nuova lega' (nome+password). Poi l'onboarding di sempre, che chiama onboard_join nella lega scelta. Il gruppo originale (lega 1) salta del tutto la schermata. Badge '🏆 <nome lega>' in Home e Classifica (renderLeagueName).",
    "invito_admin": "Impostazioni (admin) -> card 'Invita nella lega' (#inviteCard): mostra link (?lega=slug) e password da condividere, con 'Copia' (loadInvite -> get_league_admin_info).",
    "navbar": "Home, Mercato, Campo (centrale evidenziato), Voti, Lega. Feedback al tocco (anim + vibrazione).",
    "home": "hero 'Pronto a schierare?' con badge lega, poi Classifica (mini), poi Regolamento.",
    "mercato": "card con avatar intero (object-fit:contain), ruolo accanto al nome, stato forma (In forma/In calo/Costante), prezzo. Badge Capocannoniere (top scorer) e Infortunato (avatar grigio). 'Tu' solo sul proprio personaggio. Tap -> finestrella stats (Presenze/Gol/Assist/Voto medio, default 0/0/0/6).",
    "campo": "scelta modulo (1-2-2/1-3-1/1-1-3), 5 slot, capitano, doppio countdown.",
    "voti": "voto 1-10 ANCHE MEZZI (es. 7.5) via tastierino numerico (.voteinp, inputmode decimal, arrotonda a 0.5). NON si salvano da soli: tasto 'Invia voti' (#submitVotesBtn) -> submitVotes() upserta tutti i presenti. + nomination MVP (niente SEGA). Vota solo chi ha giocato.",
    "lega": "tendina: Classifica generale (solo giornate chiuse, frecce posizione 24h) / Classifica marcatori / ogni giornata (tap squadra -> formazione). Le giornate non iniziate non compaiono.",
    "impostazioni_admin": "Invita nella lega, Apri/chiudi/reset giornata, Chi gioca, Gestione giocatori (con Valore admin-only), Crea le squadre, Voto ai soli-manager, Risultati sondaggio, Manutenzione (per-lega), Notifiche. Bonus/malus = pannello partita live (vedi MATCHDAY_LIFECYCLE.bonus_malus).",
    "ux": "Campo centrale evidenziato dentro la barra; fix PWA iOS apre in cima; 'Tu' solo personaggio iniziale.",
}

GOTCHAS = [
    "LEGHE: ogni gruppo = una lega privata. league_id su tutte le tabelle (default 1), letture isolate via RLS (league_id=my_league()), scritture timbrate dal trigger stamp_league. Le funzioni aggregate (security definer) filtrano per my_league().",
    "is_admin DERIVATO: il trigger profiles_guard imposta is_admin=true solo se sei admin_id della tua lega; la lega non si cambia da update. Nessuno puo' auto-promuoversi o cambiare lega.",
    "RISULTATO SQUADRA = +/-1 (non piu' +/-2). Tenere allineati scoreOf (client), get_standings_md (SQL) e il Regolamento in Home.",
    "CREDITI alla chiusura = metodo a RANKING (scarto credito vs punti), non piu' delta-voto. Vedi MATCHDAY_LIFECYCLE.crediti_chiusura. forma da players.trend.",
    "BONUS/MALUS via pannello partita LIVE (#liveStats), non piu' tendina per giocatore; bozza in localStorage fc_live_<mdId>.",
    "AUTO-CHIUSURA lato server (close_due_matchdays via cron in notify.ts): chiude a kickoff+25h e applica i crediti, indipendente dall'admin.",
    "PRESENZE: all'apertura di una giornata NESSUNO e' presente; l'admin sceglie. presentId/togglePresence aggiornati.",
    "Chiavi placeholder: reincollarle a ogni upload del file intero.",
    "Icona PWA: cambia solo rimuovendo e ri-aggiungendo l'app alla home.",
    "players.forma: legacy, non usata nei punti. Lo 'stato di forma' viene da get_player_stats (trend).",
    "injured: stato solo visivo (non blocca lo schieramento da solo).",
    "presenze: contate da matchday_players MA solo da blocco formazioni (kickoff-1h) o se closed.",
    "classifica: somma solo le giornate closed -> niente leak del modulo prima del match. Cambiare punteggio = toccare solo get_standings_md.",
    "frecce posizione: ▲ verde / ▼ rossa, attive 24h dopo l'ultima chiusura e solo dalla 2a giornata chiusa (serve closed_at).",
    "moltiplicatore capitano/MVP: SOLO sul voto, i bonus restano piatti.",
    "SEGA rimossa: nessuna UI/calcolo; nominations.sega_player_id resta legacy = null.",
    "generatore squadre: drag&drop nativo iOS inaffidabile -> tap-to-move. Alias nomi sondaggio<->partita in POLL_ALIAS.",
    "valore (players.valore): forza per il generatore, visibile/modificabile SOLO admin.",
    "funzioni aggregate sui voti = security definer (voti anonimi, solo i propri leggibili).",
    "crediti per giocatore: players.cost (default 20); budget 100, somma dei 5 entro 100.",
    "auto-update PWA: al rientro confronta il file servito con quello caricato e ricarica se cambiato.",
    "notifiche: ensurePush() ri-aggancia la subscription scaduta a ogni apertura/focus; maybeAskPush() invita alla PRIMA apertura (1 volta per dispositivo, localStorage fc_push_asked).",
]

# ---------------------------------------------------------------------------
# SONDAGGIO VALORI (sondaggio.html)
# ---------------------------------------------------------------------------
POLL = {
    "scopo": "Pagina separata da mandare al gruppo: vota ogni giocatore 1-10. SOLO voto.",
    "privacy": "Chi ha il link puo' solo votare; i voti non sono leggibili da nessuno (RLS senza policy dirette). I risultati (medie) li vede SOLO l'admin dentro l'app (Impostazioni -> Risultati sondaggio), via get_poll_results() che controlla is_admin().",
    "file": "sondaggio.html (su Vercel, es. /sondaggio.html). Stesse chiavi Supabase. Un voto per dispositivo, modificabile.",
    "rpc": "submit_poll(p_voter,p_ratings) e get_my_poll(p_voter) [anon, security definer]; get_poll_results() [solo admin].",
    "tabella": "credit_poll(voter text pk, ratings jsonb, created_at). RLS attiva, nessuna policy diretta.",
    "giocatori_iniziali": ["Teo","Dario","Benzo","Simo","Tave","Tia","Fra","Gabri","Luchino","Previ","Pivo","Lore Chiesa","Davi Kakà","Davi Rouge","Dani","Marco Writer"],
    "alias_nomi": "Alcuni nomi del sondaggio != nomi in partita. Mappa POLL_ALIAS (partita->sondaggio) nel generatore: Davide D->Davi Kakà, Rouge->Davi Rouge, Francesco Pio->Fra, Lorenzo->Lore Chiesa, Luca->Luchino, Gabry->Gabri.",
}

# ---------------------------------------------------------------------------
# NOTIFICHE PUSH (PWA)
# ---------------------------------------------------------------------------
NOTIFICATIONS = {
    "quando": "Apertura e chiusura giornata + promemoria 1h prima della chiusura formazioni. Poche, niente spam. TUTTE inviate SOLO agli utenti della stessa lega.",
    "self_heal": "ensurePush() ricrea in silenzio la subscription scaduta/persa a ogni apertura app e su focus/visibilitychange (la finestra non gira ad app chiusa).",
    "primo_invito": "maybeAskPush() mostra il prompt gentile alla PRIMA apertura (una volta per dispositivo, localStorage fc_push_asked), solo se supportate e permesso ancora 'default'.",
    "auto_chiusura": "notify.ts (cron ogni 10min) chiama close_due_matchdays(): chiude le giornate scadute di tutte le leghe e manda la push 'chiusa' alla lega giusta (closed_league).",
    "testi": [
        "Promemoria: 'manca 1h alla scadenza delle formazioni. Schierala subito!'",
        "Chiusura: '<Giornata> chiusa. Scopri com'e' andata la tua squadra.'",
    ],
    "pezzi": {
        "sw.js": "service worker (root del repo): riceve push + gestisce click.",
        "index.html": "registra SW, ensurePush + maybeAskPush, toggle in Impostazioni, salva subscription (con league_id via trigger), chiama Edge Function su open/close (pushNotify).",
        "notify.ts": "Edge Function: sendAll(title,body,url,leagueId?) filtra push_subscriptions per lega. Immediato (admin) -> lega dell'admin; reminder -> md.league_id; auto-close -> closed_league. Pulisce le scadute.",
        "VAPID": "pubblica in index.html (VAPID_PUBLIC); privata = secret della Edge Function.",
    },
    "tabella": "push_subscriptions(endpoint pk, user_id uuid, sub jsonb, created_at, league_id) + RLS 'own'. matchdays.reminder_sent bool per il promemoria.",
    "setup": [
        "1. SQL: push_subscriptions + matchdays.reminder_sent + cron pg_cron/pg_net (vedi FANTACALCETTO.md §14). league_id aggiunto dalla migrazione leghe.",
        "2. Supabase -> Edge Functions -> 'notify' -> incolla notify.ts -> Deploy.",
        "3. Secrets della function: VAPID_PUBLIC, VAPID_PRIVATE, CRON_SECRET.",
        "4. Carica sw.js + index.html su GitHub.",
        "5. Ogni utente attiva dal prompt/Impostazioni; app installata sulla home (iOS 16.4+).",
    ],
}

# ---------------------------------------------------------------------------
# LEGHE (multi-tenant) — la grande aggiunta
# ---------------------------------------------------------------------------
LEAGUES = {
    "idea": "L'app e' diffondibile: ogni gruppo = una lega privata (come il fantacalcio). Chi entra crea una lega o ne entra in una con la password dell'admin.",
    "migrazione_seamless": "Il gruppo originale e' confluito nella lega #1 'La Fossa di Lissone' (admin=Teo, password 'SiamoLaPrima!') SENZA perdere dati/utenti: league_id default 1 + backfill. Per loro l'app e' identica, salta la schermata lega, vede solo il badge col nome.",
    "isolamento": "RLS: letture filtrate per league_id=my_league(); scritture timbrate dal trigger stamp_league. Tabella leagues con RLS senza policy dirette (solo funzioni). is_admin derivato (trigger profiles_guard).",
    "flusso_nuovo_utente": "login -> #league (Crea/Entra) -> onboarding -> onboard_join(lega,password,...) crea il profilo (e l'eventuale giocatore). Crea: create_league poi onboard_join. Entra: verify_league poi onboard_join. Link d'invito: ?lega=slug -> league_by_slug.",
    "invito": "Impostazioni admin -> card 'Invita nella lega' (link ?lega=slug + password) via get_league_admin_info (password vista solo dall'admin della lega).",
    "sql": "Due file: leghe_step1.sql (fondamenta retro-compatibili: leagues, colonne, trigger, RLS, funzioni) e leghe_step2.sql (onboard_join con unicita' nomi + get_league_admin_info). Gia' applicati.",
    "limite_noto": "Un utente = una lega (no multi-lega per ora). Il sondaggio (sondaggio.html) resta di fatto sulla lega 1 finche' non lo si rende multi-lega.",
}


def briefing():
    line = "=" * 64
    print(line)
    print("  FANTACALCETTO — briefing di contesto")
    print(line)
    print(f"\n{APP['cos_e']}\n{APP['doppio_ruolo']}\n{APP['giornate']}")
    print(f"\nLingua: {APP['lingua']} | Utente: {APP['utente']}")

    print("\n-- STACK --")
    for k, v in STACK.items():
        print(f"  {k}: {v}")

    print("\n-- DEPLOY --")
    for step in DEPLOY:
        print(f"  {step}")

    print("\n-- CHIAVI --")
    for k, v in CONFIG_KEYS.items():
        print(f"  {k}: {v}")

    print("\n-- REGOLE/PUNTEGGIO --")
    print(f"  prezzo={PRICE} budget={BUDGET} in_campo={FIELD_SIZE}")
    print(f"  moduli={ {m: MODULES[m]['bonus'] for m in MODULES} } slot_ammessi={SLOTS_ALL}")
    for k, v in SCORING.items():
        print(f"  {k}: {v}")
    print(f"  esempio: attaccante 2 gol, capitano, voto 7, squadra vince -> "
          f"{score_player('a1', True, 7, gol=2, esito='V'):.1f} punti (voto x2 + bonus)")

    print("\n-- CICLO GIORNATA --")
    for k, v in MATCHDAY_LIFECYCLE.items():
        print(f"  {k}: {v}")

    print("\n-- SCHEMA --")
    for k, v in SCHEMA.items():
        print(f"  {k}: {v}")

    print("\n-- RPC --")
    for k, v in RPC.items():
        print(f"  {k}: {v}")

    print("\n-- AUTH/EMAIL --")
    for k, v in AUTH.items():
        print(f"  {k}: {v}")

    print("\n-- FEATURE --")
    for k, v in FEATURES.items():
        print(f"  {k}: {v}")

    print("\n-- GOTCHAS --")
    for g in GOTCHAS:
        print(f"  - {g}")

    print("\n-- NOTIFICHE PUSH --")
    print(f"  quando: {NOTIFICATIONS['quando']}")
    for s in NOTIFICATIONS["setup"]:
        print(f"  {s}")

    print("\n-- LEGHE --")
    for k, v in LEAGUES.items():
        print(f"  {k}: {v}")

    print("\n" + line)
    print("  Dettagli completi e tutto l'SQL: vedi FANTACALCETTO.md")
    print(line)


if __name__ == "__main__":
    briefing()

# ---------------------------------------------------------------------------
# MANUTENZIONE + FLUIDITA' (aggiunte recenti)
# ---------------------------------------------------------------------------
MAINTENANCE = {
    "scopo": "L'admin mette l'app in stand-by per gli altri della SUA lega (lui continua a usarla). Per modifiche senza interferenze.",
    "ui": "Impostazioni -> card Manutenzione -> '🛠️ Metti in manutenzione' / '🟢 Torna live'. Non-admin: overlay full-screen #maint. Admin: banner rosso #maintBanner.",
    "stato": "app_state(maintenance bool) UNA RIGA PER LEGA (legge/scrive per league_id = profile.league_id) + realtime (channel 'appstate', isolato per lega dall'RLS). Bypass admin via profile.is_admin.",
    "rls": "select e update solo della propria lega (league_id=my_league()); update solo is_admin().",
    "realtime_nota": "Se gli aggiornamenti live non arrivano, abilitare la replica realtime su app_state (Database -> Replication/Publications).",
}

TAP_FIX = {
    "problema": "Schierare richiedeva 3-4 tap: .tapd{transform:scale(.95)} sovrascriveva il transform di centraggio degli slot (.slot usa translate(-50%,-50%)) -> lo slot saltava sotto il dito.",
    "fix": ".slot.tapd{transform:translate(-50%,-50%) scale(.95)} + touch-action:manipulation globale (toglie ritardo ~300ms e doppio-tap-zoom).",
    "regola": "Ogni elemento posizionato con transform deve ripetere quel transform anche nella variante .tapd.",
}

SORTING = "Mercato e selettore di schieramento: card ordinate per crediti decrescenti (piu costoso -> meno)."

# ---------------------------------------------------------------------------
# UI / REGOLE RECENTI (campo, icone, crediti dinamici, logo)
# ---------------------------------------------------------------------------
UI_RECENT = {
    "input_rotella": "Voti (1-10) e bonus admin (0-10) sono <select> (rotella iOS), non slider/casella. CSS .votesel/.admsel.",
    "medie_nascoste": "Media voto e n. voti SOLO admin (sezione Voti, refreshAvgLabels, box 'Voto medio' nel Mercato). Sul proprio campo l'utente vede il voto medio (bonus esclusi) dei suoi 5.",
    "icone_campo": "statIcons(r): ⚽xgol, 🅰️xassist, 💀xautogol, 🧤 se portiere imbattuto / 🔴xgol_subiti. Ripetute per quantita.",
    "formazione_altrui": "In Lega->giornata->tap squadra: campo (modulo+voti medi+simboli) + swipe orizzontale -> lista punti totali (bonus inclusi). pitchSlotsHTML mostra il voto medio; .tl-swipe/.tl-slide.",
    "crediti_dinamici": "Alla chiusura: +/-1 credito se voto medio (bonus esclusi) varia di +/-0.5 vs giornata prec. Min1/Max100, una volta sola (cost_applied). closeMatchday -> apply_credit_changes(md) -> loadPlayers().",
    "logo": "Brand = <img src=icon-512.png> nei 3 .dot; icone PWA rigenerate dall'immagine. Logo IN-app si auto-aggiorna; icona HOME: iOS richiede rimuovi+riaggiungi, Android col tempo da sola.",
    "valore_mezzi": "Campo Valore (admin) step 0.5 (6.5/7.5...).",
    "avviso_logo_temporaneo": "maybeShowLogoNotice(): popup una-tantum (localStorage fc_logo_notice_v1) che invita a reinstallare per la nuova icona. Si auto-disattiva dopo 2026-07-15; blocco rimovibile.",
    "voti_mezzi_invio": "Voti 1-10 anche mezzi (7.5) via tastierino numerico (.voteinp), parseVote() arrotonda a 0.5. NON auto-save: tasto 'Invia voti' -> submitVotes(). DB: votes.score = numeric.",
    "fix_owner_id": "Card creata da admin = owner_id NULL -> l'utente non vota. Fix dati: collega owner_id=suo profilo + name=player_name + presente. Gli id legano voti/formazioni, ri-collegare non perde dati.",
}

