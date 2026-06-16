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
    "g1 (POR)": "ROTAZIONE (default): accetta chiunque presente. FISSO (gk_fixed): accetta solo presenti con role=POR. In ENTRAMBI i casi bonus/malus portiere applicati solo in questo slot (posizionale, non per ruolo).",
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
    "apri": "MANUALE (default): scegli kickoff. AUTOMATICA (leagues.auto_open): la giornata si apre da sola 48h prima di un fischio settimanale ricorrente (auto_weekday+auto_time, Europe/Rome) via open_due_matchdays() nel cron. blocco formazioni=kickoff-1h, voti aperti=kickoff+1h, voti chiusi=+24h. ALL'APERTURA NESSUNO E' PRESENTE (mdPresent vuoto).",
    "moduli": "il manager sceglie 1-2-2 / 1-3-1 / 1-1-3 prima del kickoff (salvato in lineup_modules); cambiare modulo svuota la formazione.",
    "presenti": "DUE MODALITA' (leagues.presence_self). ADMIN (default): card 'Chi gioca questa giornata' -> matchday_players. GIOCATORI: la card admin sparisce e in HOME esce '.hpcard' (Giornata X aperta! Ci sei?) ai SOLI giocatori (non soli-manager), solo a giornata open e prima di kickoff-1h; ogni giocatore segna la PROPRIA presenza via set_my_presence. In entrambi i casi: solo presenti schierabili/votabili; assenti opachi nel mercato.",
    "bonus_malus": "PANNELLO PARTITA LIVE (non piu' tendina per giocatore). Impostazioni admin -> '📊 Apri pannello partita' (#liveOpenBtn) -> overlay full-screen #liveStats: blocchi grandi GOL/ASSIST/PORTIERE + AUTOGOL, tap giocatore = +1 (vibra), '-' per annullare; bozza salvata in localStorage (fc_live_<mdId>) cosi' sopravvive alla chiusura app; step finale 'Chi ha vinto?' (seleziona vincitori = +1, presenti non scelti = -1, nessuno = pari) -> esito V/S/'' per tutti i presenti; 'Conferma e salva' upserta tutto in match_stats. Apribile da kickoff-30min finche' la giornata non e' chiusa (matchWindow/matchOpenable).",
    "chi_vota": "solo chi ha giocato (suo personaggio presente) + admin + manager abilitati (extra_voters). canIVote() lato app.",
    "genera_squadre": "RIMOSSO DALL'APP (giu 2026): non adatto all'uso diffuso (altre leghe fanno le squadre da se' o hanno giocatori non del fanta). Spostato in TOOL SEPARATO OFFLINE 'crea_squadre.html' (rosa manuale salvata in localStorage, bilanciamento per forza+ruolo, tap-to-move, niente backend/chiavi). Tool privato di Teo. In-app non c'e' piu' ne' la card ne' POLL_ALIAS ne' il campo Valore nella scheda giocatore.",
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
    "leagues": "NUOVA. id bigserial, name, slug unique, password text(in chiaro), admin_id uuid(=creatore), created_at. + CONFIG: auto_open bool, auto_weekday smallint(0=Dom..6=Sab), auto_time time, gk_fixed bool, presence_self bool, credit_mode text('manual'|'poll'), value_poll_open bool. RLS attiva SENZA policy dirette: si legge/scrive SOLO via funzioni security definer (la password non e' mai esposta ai client).",
    "league_id (OVUNQUE)": "Tutte le tabelle dati hanno league_id bigint default 1 references leagues(id). La lega #1 e' 'La Fossa di Lissone' (il gruppo originale). Le scritture vengono 'timbrate' da un trigger (stamp_league) con coalesce(my_league(),1).",
    "profiles": "id uuid(=auth.uid()), team_name, player_name, role, avatar, is_admin bool(DERIVATO dal trigger: true se sei admin_id della tua lega), is_player bool(def true), league_id",
    "players": "id bigint, name, role(ATT/DIF/POR), avatar, present bool, forma int(legacy), trend smallint(1/-1/0 -> forma), owner_id uuid, injured bool, cost int(def20), valore numeric(LEGACY: serviva al vecchio generatore squadre in-app, ora RIMOSSO; colonna lasciata ma non usata/non editabile in-app), league_id. NB: POR usato solo se la lega e' in modalita' portiere FISSO (gk_fixed).",
    "matchdays": "id bigint, label, kickoff timestamptz, status(open/voting/locked/closed), closed_at timestamptz, reminder_sent bool, cost_applied bool, league_id",
    "lineups": "matchday_id, manager_id uuid, slot(a1,a2,a3,d1,d2,d3,g1), player_id, is_captain bool, league_id. CHECK lineups_slot_check su quei 7 slot",
    "lineup_modules": "matchday_id, manager_id uuid, module(1-2-2/1-3-1/1-1-3), league_id  (PK composta)",
    "votes": "matchday_id, voter_id uuid, player_id, score numeric(1-10, anche mezzi), league_id",
    "match_stats": "matchday_id, player_id, gol, assist, autogol, gol_subiti, esito(V/S/null = risultato squadra reale), league_id",
    "nominations": "matchday_id, voter_id uuid, mvp_player_id, sega_player_id(legacy, sempre null), league_id",
    "matchday_players": "matchday_id, player_id (PK), league_id. NB: presenza statistica solo da blocco formazioni",
    "extra_voters": "profile_id uuid PK, league_id  (manager-solo abilitati al voto)",
    "credit_poll": "LEGACY (sondaggio ESTERNO sondaggio.html, per nome). I dati della lega 1 sono stati MIGRATI in value_poll (migrazione_lega1_sondaggio.sql); sondaggio.html e' rimovibile da GitHub. Tabella/funzioni lasciate (innocue).",
    "value_poll": "NUOVA. league_id bigint + voter_id uuid (PK composta), ratings jsonb({player_id: voto 1-10}), created_at. Sondaggio valori INTERNO e PER-LEGA. RLS attiva SENZA policy dirette: accesso solo via funzioni security definer.",
    "push_subscriptions": "endpoint pk, user_id uuid, sub jsonb, created_at, league_id (notifiche inviate solo alla propria lega)",
    "app_state": "id, maintenance bool, league_id. UNA RIGA PER LEGA (la #1 ha id=1). Manutenzione ora per-lega.",
    "storage_bucket": "avatars (pubblico): PNG degli avatar, listati e usati via URL pubblico (condiviso tra tutte le leghe)",
}

RPC = {
    "is_admin()": "bool, helper RLS (legge profiles.is_admin, ora derivato dalla proprieta' lega)",
    "my_league()": "NUOVA. bigint: la lega dell'utente corrente (profiles.league_id). Usata da RLS e dalle funzioni per isolare i dati.",
    "get_averages(md)": "media voti per player nella giornata",
    "get_mvp_sega(md)": "id MVP (e SEGA, ormai ignorato)",
    "get_standings()": "classifica SOLO giornate closed della propria lega + delta posizione (frecce 24h). Ritorna anche manager_id (usato come data-id per il FLIP della classifica animata).",
    "get_standings_md(md)": "classifica di giornata (filtra i manager della lega della giornata): voto*mult(solo voto)+bonus+esito(+/-1)+bonus modulo.",
    "get_player_stats()": "presenze, gol, assist, voto_medio, forma(da trend) della propria lega.",
    "list_solo_managers()": "(admin) profili solo-manager della lega con flag voto.",
    "apply_credit_changes(md)/_apply_credits_core(md)": "crediti alla chiusura col NUOVO metodo a ranking (vedi MATCHDAY_LIFECYCLE.crediti_chiusura).",
    "close_due_matchdays()": "NUOVA (service_role). Chiude TUTTE le leghe con giornate scadute (kickoff+25h), applica crediti, restituisce (closed_id,closed_label,closed_league). Chiamata dal cron in notify.ts.",
    "get_poll_results()": "(admin) medie del VECCHIO sondaggio esterno (credit_poll). Legacy: la card 'Risultati sondaggio valori' e' stata RIMOSSA, la funzione resta in DB ma non e' piu' chiamata in-app.",
    "--- CREDITI / SONDAGGIO VALORI INTERNO ---": "",
    "set_credit_mode(p_mode)": "(admin) imposta leagues.credit_mode 'manual'|'poll'; 'poll' apre il sondaggio (value_poll_open=true), 'manual' lo chiude.",
    "submit_value_poll(p_ratings jsonb)": "qualsiasi membro: upsert dei propri voti {player_id:voto} in value_poll (richiede value_poll_open=true).",
    "get_my_value_poll()": "i propri voti (per pre-compilare il sondaggio).",
    "get_credit_config()": "(tutti) credit_mode, poll_open, i_voted, voters(distinti), members(profili lega). Letta all'avvio da loadCreditConfig().",
    "close_value_poll_and_apply()": "(admin) calcola la media voti per giocatore (default 6 se nessun voto) e applica i crediti: cost=clamp(round(20*v^2.4/media(v^2.4)),5,55); poi value_poll_open=false. Stessa formula di migrazione_lega1_sondaggio.sql.",
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
    "--- CONFIG LEGA (sessione recente, file config_lega.sql) ---": "",
    "get_league_schedule()": "config della propria lega: (auto_open, auto_weekday, auto_time, gk_fixed, presence_self). Letta da TUTTI all'avvio (loadSchedule). Grant authenticated. NB: ritorno cambiato -> droppare prima di ricreare.",
    "set_league_schedule(p_auto,p_weekday,p_time)": "(admin) apertura automatica ricorrente (giorno+ora) o manuale.",
    "set_gk_mode(p_fixed)": "(admin) portiere fisso (true) o rotazione (false).",
    "set_presence_mode(p_self)": "(admin) presenze segnate dai giocatori (true) o dall'admin (false).",
    "set_my_presence(p_present)": "il GIOCATORE segna la PROPRIA presenza (modalita' presence_self). Richiede: presence_self=true, giornata open, prima di kickoff-1h, card con owner_id=auth.uid(). Scrive matchday_players (bypassa la policy is_admin-only).",
    "next_weekly_kickoff(wd,tm)": "prossimo fischio settimanale (giorno 0=Dom..6=Sab + ora) nel fuso Europe/Rome.",
    "open_due_matchdays()": "(service_role) apre le giornate programmate 48h prima del kickoff; idempotente; ritorna (opened_id,opened_label,opened_league,opened_kickoff). Chiamata dal cron in notify.ts.",
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
    "navbar": "Home, Mercato, Campo, Voti, Lega. RESTYLE (giu 2026): barra PIATTA, niente riquadro/pillola ne' pulsante centrale blu rialzato; icone tutte uguali (un po' piu' grandi), attivo evidenziato solo dal colore; sfondo blu pieno (var(--bg)), niente trasparenza/blur, sottile riga di separazione sopra; barra in basso piu' bassa. Topbar ora FISSA (position:fixed, non piu' sticky -> non rimbalza), sfondo blu pieno + hairline sotto; lo scrollwrap ha padding-top per non finirci sotto. Feedback al tocco.",
    "home": "hero 'Pronto a schierare?' con badge lega; (se credit_mode=poll e value_poll_open) card '.hpcard' #homeValuePoll 'Sondaggio valori aperto' -> apre la pagina sondaggio (openValuePoll); (se presence_self) card '.hpcard' Presenze ai giocatori; poi Classifica (mini); Regolamento ora dentro Impostazioni.",
    "mercato": "card con avatar intero (object-fit:contain), ruolo accanto al nome, stato forma (In forma/In calo/Costante), prezzo. Badge Capocannoniere (top scorer) e Infortunato (avatar grigio). 'Tu' solo sul proprio personaggio. Tap -> finestrella stats (Presenze/Gol/Assist/Voto medio, default 0/0/0/6).",
    "campo": "scelta modulo (1-2-2/1-3-1/1-1-3), 5 slot, capitano, doppio countdown.",
    "voti": "voto 1-10 ANCHE MEZZI (es. 7.5) via tastierino numerico (.voteinp, inputmode decimal, arrotonda a 0.5). NON si salvano da soli: tasto 'Invia voti' (#submitVotesBtn) -> submitVotes() upserta tutti i presenti. + nomination MVP (niente SEGA). Vota solo chi ha giocato.",
    "lega": "tendina: Classifica generale (solo giornate chiuse, frecce posizione 24h) / Classifica marcatori / ogni giornata (tap squadra -> formazione). Le giornate non iniziate non compaiono. ALLA PRIMA APERTURA dopo una chiusura fresca (<=24h) la classifica si ANIMA (vedi CLASSIFICA_ANIMATA).",
    "impostazioni": "A PAGINE (drill-in iOS): lista #setMenu con .navrow Profilo / Notifiche / Regolamento / 🔒 Area amministratore; setNav(id) mostra una .setpage alla volta (.subback per tornare). La riga admin (#adminRow) solo all'admin.",
    "impostazioni_admin": "Area amministratore a 2 livelli: ⚽ PARTITA (Modalita' portiere rotazione/fisso, Presenze admin/giocatori, Giornata con apertura auto/manuale + apri/chiudi/reset; NON c'e' piu' 'Crea le squadre') e 🏆 LEGA (Invita, Gestione giocatori, 💰 Crediti giocatori [Manuale/Sondaggio + avanzamento + 'Chiudi e calcola'], Voto soli-manager, Manutenzione). Bonus/malus = pannello partita live.",
    "wizard_creazione": "Chi CREA una lega, dopo l'onboarding, vede #rulesSetup (Le regole della tua lega): Apertura (man/auto+giorno/ora), Portiere (rot/fisso), Presenze (admin/giocatori), 💰 Crediti giocatori (Manuale/Sondaggio) con spiegazioni. saveRulesSetup -> set_league_schedule/set_gk_mode/set_presence_mode/set_credit_mode. Solo al creatore (flag justCreatedLeague). Tutto poi modificabile in Impostazioni.",
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
    "generatore squadre: RIMOSSO dall'app (giu 2026). Ora e' un tool separato offline 'crea_squadre.html' (rosa in localStorage, bilanciamento forza+ruolo, tap-to-move). POLL_ALIAS non e' piu' nell'app.",
    "valore (players.valore): LEGACY. Serviva al vecchio generatore in-app; il campo e' stato tolto dalla scheda giocatore. Colonna lasciata in DB (innocua), preservata sugli edit.",
    "CREDITI giocatori = 2 metodi (leagues.credit_mode): 'manual' (admin imposta cost nella scheda) o 'poll' (sondaggio interno value_poll -> close_value_poll_and_apply calcola i cost). Anche con 'poll' i cost restano modificabili a mano. Vedi VALUE_POLL.",
    "funzioni aggregate sui voti = security definer (voti anonimi, solo i propri leggibili).",
    "crediti per giocatore: players.cost (default 20); budget 100, somma dei 5 entro 100.",
    "auto-update PWA: al rientro confronta il file servito con quello caricato e ricarica se cambiato.",
    "notifiche: ensurePush() ri-aggancia la subscription scaduta a ogni apertura/focus; maybeAskPush() invita alla PRIMA apertura (1 volta per dispositivo, localStorage fc_push_asked).",
    "CONFIG LEGA: 3 modalita' su leagues (auto_open, gk_fixed, presence_self), lette da TUTTI all'avvio via get_league_schedule()/loadSchedule(). Scritte solo dall'admin (set_*). Il wizard #rulesSetup le imposta alla creazione (solo creatore, flag justCreatedLeague).",
    "PORTIERE FISSO: cambia solo CHI puo' stare in g1 (role=POR), NON il punteggio (bonus portiere resta posizionale su slot g1). Onboarding self-signup resta ATT/DIF; POR lo assegna l'admin in Gestione giocatori.",
    "PRESENZE GIOCATORI: set_my_presence (security definer) consente al solo proprietario della propria card di scrivere matchday_players (la policy diretta e' is_admin-only). Card Home solo a giocatori (non soli-manager), giornata open, prima di kickoff-1h.",
    "IMPOSTAZIONI A PAGINE: setNav(id) + .setpage/.navrow/.subback. Niente piu' lista unica. Entrando da go('settings') si riparte da setMenu.",
    "SICUREZZA chiavi: su GitHub vanno SOLO index.html, sw.js, icone (sondaggio.html ora RIMOVIBILE: migrato in value_poll). 'crea_squadre.html' e' un tool PRIVATO offline (nessuna chiave, non serve su GitHub). MAI notify.ts ne' chiavi/secret (repo pubblico = chiave bruciata, va ruotata). Le chiavi VAPID e CRON_SECRET stanno solo nei Secret della Edge Function. Chiavi ruotate il 2026-06-14 dopo un commit accidentale di notify.ts (GitGuardian). VAPID_PUBLIC corrente in index.html inizia con 'BIVh1NLu...'.",
]

# ---------------------------------------------------------------------------
# SONDAGGIO VALORI ESTERNO (sondaggio.html) — LEGACY / MIGRATO
# ---------------------------------------------------------------------------
POLL = {
    "stato": "LEGACY. Era la pagina esterna inviata al gruppo. I voti della lega 1 sono stati MIGRATI in value_poll (migrazione_lega1_sondaggio.sql), quindi sondaggio.html e' RIMOVIBILE da GitHub. Sostituito dal sondaggio INTERNO e per-lega (vedi VALUE_POLL). Tabella credit_poll + get_poll_results restano in DB (innocue); la card 'Risultati sondaggio valori' e' stata RIMOSSA dall'app.",
    "scopo": "Pagina separata: vota ogni giocatore 1-10. SOLO voto.",
    "privacy": "Chi ha il link puo' solo votare; voti non leggibili (RLS senza policy dirette). Medie viste SOLO dall'admin via get_poll_results().",
    "file": "sondaggio.html (su Vercel). Stesse chiavi Supabase. Un voto per dispositivo.",
    "rpc": "submit_poll(p_voter,p_ratings), get_my_poll(p_voter) [anon]; get_poll_results() [admin].",
    "tabella": "credit_poll(voter text pk, ratings jsonb, created_at, league_id).",
    "giocatori_iniziali": ["Teo","Dario","Benzo","Simo","Tave","Tia","Fra","Gabri","Luchino","Previ","Pivo","Lore Chiesa","Davi Kakà","Davi Rouge","Dani","Marco Writer"],
    "alias_nomi": "Nomi sondaggio esterno != nomi in partita -> usati nella MIGRAZIONE (migrazione_lega1_sondaggio.sql): Davide D->Davi Kakà, Rouge->Davi Rouge, Francesco Pio->Fra, Lorenzo->Lore Chiesa, Luca->Luchino, Gabry->Gabri.",
}

# ---------------------------------------------------------------------------
# SONDAGGIO VALORI INTERNO E PER-LEGA (giu 2026) — metodo crediti 'poll'
# ---------------------------------------------------------------------------
VALUE_POLL = {
    "scopo": "Modo GENERALE (per qualsiasi lega) di assegnare i crediti dei giocatori. Sostituisce il sondaggio esterno. Tutto dentro l'app.",
    "scelta_metodo": "leagues.credit_mode: 'manual' (admin imposta cost a mano nella scheda giocatore) o 'poll' (sondaggio). Scelto nel wizard #rulesSetup alla creazione e modificabile in Impostazioni admin -> Lega -> 'Crediti giocatori' (set_credit_mode).",
    "chi_vota": "TUTTI i membri della lega (anche i soli-manager).",
    "cosa_si_vota": "tutte le card giocatori della lega (no manager), ESCLUSO il proprio personaggio (auto-esclusione). Voto 1-10 con mezzi voti.",
    "home": "se credit_mode=poll e value_poll_open: card #homeValuePoll sotto l'hero -> openValuePoll() apre l'overlay full-screen #valuePoll (riusa lo stile .ls-open). select 1..10 per ogni giocatore, 'Invia i voti' -> submit_value_poll. Niente listone in home.",
    "chiusura": "LA FA L'ADMIN (con contatore 'X di Y membri hanno votato', '✓ tutti!' se completo): Impostazioni -> Lega -> Crediti -> 'Chiudi e calcola i crediti' -> close_value_poll_and_apply(). Niente timer, niente attesa rigida di tutti.",
    "formula": "per ogni giocatore media dei voti ricevuti (default 6 se nessun voto), poi cost=clamp(round(20 * v^2.4 / media(v^2.4)), 5, 55). Calibrata su 100cr/5: medio ~20, i 5 piu' forti insieme >100 (non comprabili), gia' 3 forti sfondano. I cost restano modificabili a mano dall'admin.",
    "tabella": "value_poll(league_id+voter_id PK, ratings jsonb {player_id:voto}). RLS senza policy dirette.",
    "rpc": "set_credit_mode, submit_value_poll, get_my_value_poll, get_credit_config, close_value_poll_and_apply. Stato letto all'avvio per tutti via loadCreditConfig()/get_credit_config.",
    "sql": "sondaggio_valori.sql (additivo, colonne+tabella+5 funzioni). Migrazione lega 1: migrazione_lega1_sondaggio.sql (credit_poll -> value_poll + applica i cost).",
}


# ---------------------------------------------------------------------------
# NOTIFICHE PUSH (PWA)
# ---------------------------------------------------------------------------
NOTIFICATIONS = {
    "quando": "Apertura e chiusura giornata + promemoria 1h prima della chiusura formazioni. Poche, niente spam. TUTTE inviate SOLO agli utenti della stessa lega.",
    "self_heal": "ensurePush() ricrea in silenzio la subscription scaduta/persa a ogni apertura app e su focus/visibilitychange (la finestra non gira ad app chiusa).",
    "primo_invito": "maybeAskPush() mostra il prompt gentile alla PRIMA apertura (una volta per dispositivo, localStorage fc_push_asked), solo se supportate e permesso ancora 'default'.",
    "banner_mensile": "maybeShowNotifBanner(): banner #notifBanner in cima all'app, SOLO a chi NON ha le notifiche attive (permission 'default'), max 1 volta ogni 30 giorni (localStorage fc_notif_banner). Esclude i bloccati a livello iOS. Tasti Attiva/✕.",
    "auto_apertura": "notify.ts (cron 10min) chiama open_due_matchdays(): apre le giornate programmate 48h prima (leagues.auto_open) e manda la push '<Giornata> aperta! ⚽' alla lega giusta (runAutoOpen).",
    "auto_chiusura": "notify.ts (cron ogni 10min) chiama close_due_matchdays(): chiude le giornate scadute di tutte le leghe e manda la push 'chiusa' alla lega giusta (closed_league).",
    "testi": [
        "Promemoria: 'manca 1h alla scadenza delle formazioni. Schierala subito!'",
        "Chiusura: '<Giornata> chiusa. Scopri com'e' andata la tua squadra.'",
    ],
    "pezzi": {
        "sw.js": "service worker (root del repo): riceve push + gestisce click.",
        "index.html": "registra SW, ensurePush + maybeAskPush, toggle in Impostazioni, salva subscription (con league_id via trigger), chiama Edge Function su open/close (pushNotify).",
        "notify.ts": "Edge Function: sendAll(title,body,url,leagueId?) filtra push_subscriptions per lega. Immediato (admin) -> lega dell'admin; reminder -> md.league_id; auto-close -> closed_league; auto-OPEN -> open_due_matchdays (runAutoOpen). Risposta cron {opened,reminders,closed}. Pulisce le scadute.",
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
    "limite_noto": "Un utente = una lega (no multi-lega per ora). Il sondaggio valori ora e' INTERNO e PER-LEGA (value_poll); quello esterno (sondaggio.html) e' stato migrato sulla lega 1 ed e' dismesso.",
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


# ---------------------------------------------------------------------------
# CONFIG LEGA (sessione recente): apertura / portiere / presenze + UX
# ---------------------------------------------------------------------------
LEAGUE_CONFIG = {
    "dove": "Tutto su leagues (auto_open, auto_weekday, auto_time, gk_fixed, presence_self). Letto da TUTTI all'avvio via get_league_schedule()/loadSchedule(); scritto solo dall'admin (set_league_schedule/set_gk_mode/set_presence_mode). File SQL: config_lega.sql (idempotente, sostituisce apertura_automatica.sql).",
    "apertura": "MANUALE (apri tu, data/ora) o AUTOMATICA (giorno settimanale + ora -> si apre da sola 48h prima, ricorrente). Calcolo Europe/Rome. Cron notify.ts -> open_due_matchdays() apre e manda la push 'aperta'. UI: Partita -> Giornata (renderOpenMode).",
    "portiere": "ROTAZIONE (default, chiunque in g1) o FISSO (in g1 solo role=POR; il ruolo POR appare nella scheda giocatore). Punteggi INVARIATI (bonus portiere = slot g1). UI: Partita -> Modalita' portiere (renderGkMode). Stato gkFixed; helper roleLabel.",
    "presenze": "ADMIN (default, riquadro 'Chi gioca') o GIOCATORI (card .hpcard in Home, set_my_presence). Card solo ai giocatori, giornata open, prima di kickoff-1h, modificabile finche' aperto. UI: Partita -> Presenze (renderPresenceMode/renderHomePresence). Stato presenceSelf.",
    "impostazioni_pagine": "Drill-in iOS: setNav(id) mostra una .setpage alla volta; lista #setMenu (.navrow). Area amministratore a 2 livelli: Partita / Lega. Riga admin #adminRow solo all'admin.",
    "banner_notifiche": "maybeShowNotifBanner(): #notifBanner mensile (1/30gg) solo a chi non ha le notifiche attive (permission 'default'). localStorage fc_notif_banner.",
    "wizard_creazione": "Alla CREAZIONE lega (solo creatore, flag justCreatedLeague): overlay #rulesSetup con le 3 scelte (apertura/portiere/presenze) + spiegazioni -> saveRulesSetup(). Per la lega #1 gia' esistente non appare: solo campi in Impostazioni.",
    "file": "index.html, config_lega.sql, notify.ts (runAutoOpen), elimina_lega_test.sql (utility cancella lega di test, guardia su lega #1).",
}


# ---------------------------------------------------------------------------
# PAGELLONE (storie) + CLASSIFICA ANIMATA + LAYOUT FULL-SCREEN (sessione recente)
# Tutto in index.html. NIENTE SQL, NIENTE PNG: usa dati gia' forniti dalle RPC.
# ---------------------------------------------------------------------------
RECAP_PAGELLONE = {
    "cos_e": "Visore 'a storie' #pag (full-screen) di fine giornata. openRecap(mdId, auto) carica get_matchday_recap(md); buildRecapCards(d) costruisce le scene; showRecapCard(i) ne mostra una alla volta.",
    "scene": "cover -> numbers/capo/topflop/movers/modules/winner/mvp (se presenti) -> [NUOVA] standings -> share. countUp() anima i numeri delle singole scene.",
    "navigazione": "tap dx avanti / sx indietro / swipe giu' chiude. Auto-apertura 1 volta per giornata: maybeShowRecap() con flag localStorage fc_recap_seen_<mdId> (init fc_recap_init). Riapribile a mano dalla Home ('Rivivi l'ultima giornata').",
    "scena_classifica": "buildRecapCards aggiunge {t:'standings'} ('La classifica adesso') PRIMA di share (solo se standings.length). renderRecapStandings() la riempie: anima la prima volta (flag fc_lb_anim_pag_<mdId>), poi statica. NB: la scena standings NON conta come 'contenuto interessante' -> l'auto-apertura resta come prima.",
}

CLASSIFICA_ANIMATA = {
    "cosa_fa": "Alla chiusura la classifica non si riordina di colpo: si anima in 3 momenti -> (1) RIORDINO righe FLIP (transform/GPU), (2) COUNT-UP punti dal totale precedente al nuovo, (3) FRECCE ▲+n verde / ▼−n rossa che compaiono ad assestamento e RESTANO (come moveArrow, finestra 24h). Niente fade-out.",
    "dove": "Due posti INDIPENDENTI: (a) scena finale del Pagellone; (b) prima apertura della scheda Lega dopo la chiusura. L'effetto avviene in entrambi.",
    "flag_anti_ripetizione": "Due flag localStorage separati: fc_lb_anim_pag_<mdId> (Pagellone) e fc_lb_anim_lega_<mdId> (Lega). Ogni schermata controlla il suo, anima 1 volta, poi lo segna. Scollegati tra loro.",
    "trigger_lega": "go('classifica') -> maybeAnimateLega(): solo vista 'Classifica generale' (selStandingsMd==''), solo se chiusura fresca <=24h (lbFresh via matchdays.closed_at) e flag non segnato. Poi anima #lbList.",
    "trigger_pagellone": "showRecapCard scena 'standings' -> renderRecapStandings(): anima solo se e' l'ultima giornata chiusa ed e' fresca e flag non segnato; altrimenti statica (anche sui Pagelloni vecchi: chiusura elegante ma senza frecce/riordino).",
    "prima_e_dopo_senza_query_extra": "DOPO = standings correnti (get_standings, gia' ordinate, con delta). POSIZIONE precedente = pos_attuale + delta. TOTALE precedente (count-up) = totale - punti_giornata, dove i punti vengono da get_standings_md(md) (mappa manager_id->punti). 'Fresca' (<=24h) si legge da matchdays.closed_at (aggiunto al select di loadMatchdaysList).",
    "FLIP": "Ogni riga ha data-id=manager_id (le righe si rifanno con innerHTML). Schema: misura posizioni attuali per id -> ridisegna nuovo ordine -> spostamento inverso istantaneo -> rilascio con transizione su transform. A fine animazione i transform inline si PULISCONO (nessun conflitto con .tapd). loadStandings() ora mappa anche manager_id (prima assente).",
    "dettagli_pro": "Numeri tabulari (font-variant-numeric:tabular-nums) cosi' le cifre non ballano. prefers-reduced-motion: risultato finale diretto (frecce gia' visibili) ma flag comunque segnati. Skeleton loader (righe grigie pulsanti) in renderLB e renderMini mentre i dati caricano (flag standingsLoaded).",
    "casi_limite": "1a giornata chiusa in assoluto (delta tutti 0): niente riordino, solo count-up 0->totale, nessuna freccia. Lega oltre le 24h: niente animazione (coerente con frecce assenti), statica. Parita'/solo-manager/tante squadre(scroll): ok. Mai righe rotte/vuote (l'ordine vecchio si misura e sostituisce in modo sincrono, mai dipinto).",
    "mini_home": "La mini-classifica in Home resta STATICA: solo data-id + numeri tabulari + skeleton, niente scorrimento (top-3, l'effetto entra/esce-dal-podio sarebbe sporco).",
    "funzioni_nuove": "lbRowHTML(t,i,pts,withArrow), moveArrowR(d) (freccia con classe .rv per il reveal), skeletonRows(kind,n), prefersReduce(), lbFresh(), mdPointsMap(mdId), lbBuildAnimRows(), countUpFromTo(el,from,to,dur), lbAnimate(container,rows,mdPts) (motore), maybeAnimateLega(), renderRecapStandings(). Var standingsLoaded.",
    "non_rotto": "doCloseMatchday ora ricarica anche loadStandings()+loadMatchdaysList() (dati freschi per latestClosedMd/standings/closed_at). Flusso di chiusura, clearRoundLocal() e moveArrow() INVARIATI. renderLB(generale) e renderMini emettono data-id + numero in .num (struttura identica statica/animata).",
}

LAYOUT_FULLSCREEN = {
    "problema": "Una redesign aveva reso .app un GUSCIO position:fixed con scroller interno (.scrollwrap). Su iOS PWA questo manda in tilt il bottom:0 dei position:fixed -> barra in fondo 'galleggiante' (innerHeight/dvh sottostimano l'altezza). Forzando screen.height la barra veniva TAGLIATA. Numeri reali misurati su iPhone: innerHeight~793, screen.height~852.",
    "soluzione": "Tornare all'impianto SCROLL-PAGINA (quello che sul telefono andava bene): il body scrolla; .app blocco normale min-height:100dvh con padding-bottom per la barra; .topbar position:sticky;top:0; .nav position:fixed;bottom:0;left:50%;translateX(-50%). Rimosso ogni tentativo JS di misurare l'altezza (--app-h) e il debug.",
    "regola": "Per le full-screen su iOS-PWA, lo SCROLL del body e' piu' affidabile del guscio fisso a tutto schermo. Evitare .app fixed + scrollwrap interno.",
    "tap_fix_invariato": "Resta valida la regola .tapd: ogni elemento posizionato con transform ripete quel transform anche in .tapd (vedi TAP_FIX). Le righe animate puliscono i transform inline a fine animazione, quindi non serve variante .tapd su di esse.",
}
