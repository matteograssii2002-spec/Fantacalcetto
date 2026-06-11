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
  (get_standings / get_standings_md).
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
    "risultato squadra reale": "+2 se la sua squadra di calcetto vince, -2 se perde (match_stats.esito = V/S/null)",
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
        bonus += 2
    elif esito == "S":
        bonus -= 2
    if slot == "g1":  # portiere
        bonus += 3 if gol_subiti == 0 else -gol_subiti
    return media_voti * mult + bonus


# ---------------------------------------------------------------------------
# CICLO GIORNATA (admin)
# ---------------------------------------------------------------------------
MATCHDAY_LIFECYCLE = {
    "apri": "scegli kickoff. blocco formazioni=kickoff-1h, voti aperti=kickoff+1h, voti chiusi=+24h. all'apertura presenti di default (per schierabilita).",
    "moduli": "il manager sceglie 1-2-2 / 1-3-1 / 1-1-3 prima del kickoff (salvato in lineup_modules); cambiare modulo svuota la formazione.",
    "presenti": "card 'Chi gioca questa giornata' -> matchday_players. solo presenti schierabili/votabili; assenti opachi nel mercato.",
    "bonus_malus": "tendina giocatore + gol/assist/autogol/gol presi + Risultato squadra (V/S) -> match_stats. BLOCCATO finche non aprono i voti (statsOpen()).",
    "chi_vota": "solo chi ha giocato (suo personaggio presente) + admin + manager abilitati (extra_voters). canIVote() lato app.",
    "genera_squadre": "admin: divide i presenti in 2 squadre equilibrate per valore (players.valore o medie sondaggio o 5.5) e ruolo; tap-to-move; verde se pari, rosso altrimenti.",
    "chiudi": "status='closed' + closed_at=now(). da qui i punti entrano in classifica e scattano le frecce 24h.",
    "reset": "rpc reset_matchday: cancella giornata e TUTTI i figli (formazioni/voti/nomination/stat/presenze).",
    "presenza_statistica": "conta solo da blocco formazioni (kickoff-1h) o se closed; aprire una giornata non genera piu presenze.",
    "classifica": "somma SOLO le giornate closed: la giornata in corso (e il bonus modulo) compare solo quando l'admin chiude.",
    "formazioni_avversarie": "nascoste finche la partita non inizia (kickoff o closed). selettore Lega nasconde le giornate non ancora iniziate.",
    "status_validi": ["open", "voting", "locked", "closed"],
}

# ---------------------------------------------------------------------------
# MODELLO DATI (colonne come usate dall'app)
# ---------------------------------------------------------------------------
SCHEMA = {
    "profiles": "id uuid(=auth.uid()), team_name, player_name, role, avatar, is_admin bool, is_player bool(def true)",
    "players": "id bigint, name, role(ATT/DIF), avatar, present bool, forma int(legacy), owner_id uuid, injured bool, cost int(def20), valore numeric(forza 1-10, ADMIN-only)",
    "matchdays": "id bigint, label, kickoff timestamptz, status(open/voting/locked/closed), closed_at timestamptz, reminder_sent bool",
    "lineups": "matchday_id, manager_id uuid, slot(a1,a2,a3,d1,d2,d3,g1), player_id, is_captain bool. CHECK lineups_slot_check su quei 7 slot",
    "lineup_modules": "matchday_id, manager_id uuid, module(1-2-2/1-3-1/1-1-3)  (PK composta)",
    "votes": "matchday_id, voter_id uuid, player_id, score int(1-10)",
    "match_stats": "matchday_id, player_id, gol, assist, autogol, gol_subiti, esito(V/S/null = risultato squadra reale)",
    "nominations": "matchday_id, voter_id uuid, mvp_player_id, sega_player_id(legacy, sempre null)",
    "matchday_players": "matchday_id, player_id (PK). NB: presenza statistica solo da blocco formazioni",
    "extra_voters": "profile_id uuid PK  (manager-solo abilitati al voto)",
    "storage_bucket": "avatars (pubblico): PNG degli avatar, listati e usati via URL pubblico",
}

RPC = {
    "is_admin()": "bool, helper RLS",
    "get_averages(md)": "media voti per player nella giornata",
    "get_mvp_sega(md)": "id MVP (e SEGA, ormai ignorato)",
    "get_standings()": "classifica SOLO giornate closed + delta posizione (frecce 24h). FIRMA: +colonna delta int",
    "get_standings_md(md)": "classifica di giornata: voto*mult(solo voto)+bonus+esito+bonus modulo, niente SEGA",
    "get_player_stats()": "presenze(da blocco formazioni), gol, assist, voto_medio, forma",
    "list_solo_managers()": "(admin) profili solo-manager con flag voto (card 'Voto ai soli-manager')",
    "get_poll_results()": "(admin) medie sondaggio valori",
    "reset_matchday(md)": "cancella giornata + tutti i figli (presenze incluse)",
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
    "navbar": "Home, Mercato, Campo (centrale evidenziato), Voti, Lega. Feedback al tocco (anim + vibrazione).",
    "home": "hero 'Pronto a schierare?', poi Classifica (mini), poi Regolamento.",
    "mercato": "card con avatar intero (object-fit:contain), ruolo accanto al nome, stato forma (In forma/In calo/Costante), prezzo. Badge Capocannoniere (top scorer) e Infortunato (avatar grigio). 'Tu' solo sul proprio personaggio. Tap -> finestrella stats (Presenze/Gol/Assist/Voto medio, default 0/0/0/6).",
    "campo": "scelta modulo (1-2-2/1-3-1/1-1-3), 5 slot, capitano, doppio countdown.",
    "voti": "voto 1-10 dei presenti + nomination MVP (niente SEGA), medie live; (admin) bonus/malus + Risultato squadra. Vota solo chi ha giocato.",
    "lega": "tendina: Classifica generale (solo giornate chiuse, frecce posizione 24h) / Classifica marcatori / ogni giornata (tap squadra -> formazione). Le giornate non iniziate non compaiono.",
    "impostazioni_admin": "Apri/chiudi/reset giornata, Chi gioca, Gestione giocatori (con Valore admin-only), Crea le squadre, Voto ai soli-manager, Risultati sondaggio, Manutenzione, Notifiche.",
    "ux": "Campo centrale evidenziato dentro la barra; fix PWA iOS apre in cima; 'Tu' solo personaggio iniziale.",
}

GOTCHAS = [
    "Chiavi placeholder: reincollarle a ogni upload del file intero.",
    "Icona PWA: cambia solo rimuovendo e ri-aggiungendo l'app alla home.",
    "players.forma: legacy, non usata nei punti. Lo 'stato di forma' viene da get_player_stats.",
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
    "quando": "Apertura e chiusura giornata (trigger admin) + promemoria 1h prima della chiusura formazioni (scheduler a tempo). Poche, niente spam.",
    "testi": [
        "Apertura: '<Giornata> aperta! Schiera la tua formazione...'",
        "Promemoria: 'manca 1h alla scadenza delle formazioni. Schierala subito!'",
        "Chiusura: '<Giornata> chiusa. Scopri com'e' andata la tua squadra.'",
    ],
    "pezzi": {
        "sw.js": "service worker (root del repo): riceve push + gestisce click.",
        "index.html": "registra SW, prompt dopo onboarding + toggle in Impostazioni, salva subscription, chiama Edge Function su open/close (pushNotify).",
        "notify.ts": "Edge Function Supabase: invia push a tutte le subscription con web-push; solo admin; pulisce le scadute.",
        "VAPID": "pubblica in index.html (VAPID_PUBLIC); privata = secret della Edge Function.",
    },
    "tabella": "push_subscriptions(endpoint pk, user_id uuid, sub jsonb, created_at) + RLS 'own'. matchdays.reminder_sent bool per il promemoria.",
    "setup": [
        "1. SQL: crea push_subscriptions + matchdays.reminder_sent + cron pg_cron/pg_net (vedi FANTACALCETTO.md §14).",
        "2. Supabase -> Edge Functions -> crea 'notify' -> incolla notify.ts -> Deploy.",
        "3. Secrets della function: VAPID_PUBLIC, VAPID_PRIVATE, CRON_SECRET.",
        "4. Carica sw.js + index.html su GitHub.",
        "5. Ogni utente attiva dal prompt/Impostazioni; app installata sulla home (iOS 16.4+).",
    ],
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

    print("\n" + line)
    print("  Dettagli completi e tutto l'SQL: vedi FANTACALCETTO.md")
    print(line)


if __name__ == "__main__":
    briefing()

# ---------------------------------------------------------------------------
# MANUTENZIONE + FLUIDITA' (aggiunte recenti)
# ---------------------------------------------------------------------------
MAINTENANCE = {
    "scopo": "L'admin mette l'app in stand-by per tutti gli altri (lui continua a usarla). Per fare modifiche senza interferenze.",
    "ui": "Impostazioni -> card Manutenzione -> '🛠️ Metti in manutenzione' / '🟢 Torna live'. Non-admin: overlay full-screen #maint. Admin: banner rosso #maintBanner.",
    "stato": "Tabella app_state(id=1, maintenance bool) + realtime (channel 'appstate'). Bypass admin via profile.is_admin.",
    "rls": "select per tutti; update solo is_admin().",
    "realtime_nota": "Se gli aggiornamenti live non arrivano, abilitare la replica realtime su app_state (Database -> Replication/Publications).",
}

TAP_FIX = {
    "problema": "Schierare richiedeva 3-4 tap: .tapd{transform:scale(.95)} sovrascriveva il transform di centraggio degli slot (.slot usa translate(-50%,-50%)) -> lo slot saltava sotto il dito.",
    "fix": ".slot.tapd{transform:translate(-50%,-50%) scale(.95)} + touch-action:manipulation globale (toglie ritardo ~300ms e doppio-tap-zoom).",
    "regola": "Ogni elemento posizionato con transform deve ripetere quel transform anche nella variante .tapd.",
}

SORTING = "Mercato e selettore di schieramento: card ordinate per crediti decrescenti (piu costoso -> meno)."
