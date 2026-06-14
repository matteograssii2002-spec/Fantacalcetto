// Supabase Edge Function: "notify"
// Due usi:
//  1) Invio immediato (chiamato dall'app, solo admin): body {title, body, url}
//  2) Promemoria a tempo (chiamato dallo scheduler pg_cron): header x-cron-secret + body {mode:'reminder'}
//
// Secrets da impostare (Dashboard -> Edge Functions -> notify -> Secrets):
//   VAPID_PUBLIC   = BD39pFvBUZEGfS3D7Olx9MuJqjULAOXa0Aq0MhTkLNqX_lKTNWBucQ9Msn96VUIRRuR0IuWNFNHOFmm-LztRpgg
//   VAPID_PRIVATE  = i0HO0_9E5eByf1mForHgwrBuEcBHicgmqNohetKpB1w
//   CRON_SECRET    = tYSwWb0TSXS8pIbovLxtoOZPaPWgZqCU
// (SUPABASE_URL, SUPABASE_ANON_KEY e SUPABASE_SERVICE_ROLE_KEY sono gia' forniti da Supabase.)

import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-cron-secret",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const URL = Deno.env.get("SUPABASE_URL")!;
const ANON = Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const VAPID_PUBLIC = Deno.env.get("VAPID_PUBLIC")!;
const VAPID_PRIVATE = Deno.env.get("VAPID_PRIVATE")!;
const CRON_SECRET = Deno.env.get("CRON_SECRET") ?? "";

webpush.setVapidDetails("mailto:accesso@fantacalcettoitalia.it", VAPID_PUBLIC, VAPID_PRIVATE);
const admin = createClient(URL, SERVICE);

const HOUR = 3600 * 1000;

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    const body = await req.json().catch(() => ({}));

    // --- MODALITA' SCHEDULER (cron): promemoria + auto-chiusura giornate ---
    const cronHeader = req.headers.get("x-cron-secret") ?? "";
    if (body?.mode === "reminder" || cronHeader) {
      if (!CRON_SECRET || cronHeader !== CRON_SECRET) return json({ error: "bad cron secret" }, 401);
      const reminders = await runReminder();
      const closed = await runAutoClose();
      return json({ ok: true, reminders, closed }, 200);
    }

    // --- MODALITA' INVIO IMMEDIATO (solo admin) ---
    const authHeader = req.headers.get("Authorization") ?? "";
    const userClient = createClient(URL, ANON, { global: { headers: { Authorization: authHeader } } });
    const { data: { user } } = await userClient.auth.getUser();
    if (!user) return json({ error: "unauthorized" }, 401);
    const { data: prof } = await admin.from("profiles").select("is_admin, league_id").eq("id", user.id).single();
    if (!prof?.is_admin) return json({ error: "forbidden" }, 403);

    const sent = await sendAll(body.title ?? "Fantacalcetto", body.body ?? "", body.url ?? "/", prof.league_id);
    return json({ ok: true, sent }, 200);
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});

// Promemoria: 1h prima della chiusura formazioni (= kickoff - 2h), una volta sola per giornata.
async function runReminder() {
  const now = Date.now();
  const { data: mds } = await admin
    .from("matchdays")
    .select("id,label,kickoff,status,reminder_sent,league_id")
    .eq("status", "open")
    .eq("reminder_sent", false)
    .not("kickoff", "is", null);

  let fired = 0;
  for (const md of mds ?? []) {
    const kickoff = new Date(md.kickoff).getTime();
    const lock = kickoff - HOUR;        // chiusura formazioni = kickoff - 1h
    const remindAt = lock - HOUR;       // promemoria = 1h prima della chiusura
    if (now >= remindAt && now < lock) {
      await sendAll(
        "⏰ Ultima ora per le formazioni",
        `${md.label}: manca 1h alla scadenza delle formazioni. Schierala subito!`,
        "/",
        md.league_id
      );
      await admin.from("matchdays").update({ reminder_sent: true }).eq("id", md.id);
      fired++;
    }
  }
  return fired;
}

// Auto-chiusura: chiude le giornate con i voti scaduti (kickoff + 25h) e applica i crediti dinamici, lato server.
// Non dipende dall'admin: gira col cron ogni 10 min. Idempotente (il DB salta quelle gia' chiuse / gia' applicate).
async function runAutoClose() {
  const { data, error } = await admin.rpc("close_due_matchdays");
  if (error) return 0;
  let closed = 0;
  for (const md of data ?? []) {
    await sendAll(
      `${md.closed_label} chiusa 🏁`,
      "Scopri com'è andata la tua squadra e la classifica.",
      "/",
      md.closed_league
    );
    closed++;
  }
  return closed;
}

async function sendAll(title: string, body: string, url: string, leagueId?: number) {
  const payload = JSON.stringify({ title, body, url });
  let q = admin.from("push_subscriptions").select("endpoint, sub");
  if (leagueId != null) q = q.eq("league_id", leagueId);
  const { data: subs } = await q;
  let sent = 0;
  await Promise.all((subs ?? []).map(async (s: any) => {
    try { await webpush.sendNotification(s.sub, payload); sent++; }
    catch (e: any) {
      if (e?.statusCode === 404 || e?.statusCode === 410) {
        await admin.from("push_subscriptions").delete().eq("endpoint", s.endpoint);
      }
    }
  }));
  return sent;
}

function json(obj: unknown, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers: { ...cors, "Content-Type": "application/json" } });
}
