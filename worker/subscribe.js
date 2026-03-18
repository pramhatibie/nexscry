/**
 * NexScry Subscribe Worker — deploy to Cloudflare Workers (free tier)
 *
 * Setup:
 * 1. Go to workers.cloudflare.com → Create Worker → paste this file
 * 2. Settings → Variables → add:
 *    RESEND_API_KEY   = re_xxxxxxxxxxxx  (from resend.com/api-keys)
 *    RESEND_AUDIENCE_ID = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
 *       (from resend.com/audiences → click your audience → copy ID)
 * 3. Deploy → copy the worker URL
 * 4. Add RESEND_WORKER_URL = <your worker url> as a GitHub Secret
 * 5. Re-run the GitHub Actions pipeline to rebuild the site
 */

const ALLOWED_ORIGIN = "https://nexscry.xyz";

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const isAllowed = origin === ALLOWED_ORIGIN || origin.endsWith(".nexscry.xyz");

    const corsHeaders = {
      "Access-Control-Allow-Origin": isAllowed ? origin : ALLOWED_ORIGIN,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    if (request.method !== "POST") {
      return json({ error: "method_not_allowed" }, 405, corsHeaders);
    }

    // Parse body
    let email;
    try {
      const body = await request.json();
      email = (body.email || "").trim().toLowerCase();
    } catch {
      return json({ error: "invalid_body" }, 400, corsHeaders);
    }

    // Basic email validation
    if (!email || !email.includes("@") || !email.includes(".")) {
      return json({ error: "invalid_email" }, 400, corsHeaders);
    }

    // Validate env vars
    if (!env.RESEND_API_KEY || !env.RESEND_AUDIENCE_ID) {
      console.error("Missing RESEND_API_KEY or RESEND_AUDIENCE_ID env vars");
      return json({ error: "server_misconfigured" }, 500, corsHeaders);
    }

    // Add contact to Resend Audience
    const resendRes = await fetch(
      `https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.RESEND_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, subscribed: true }),
      }
    );

    if (!resendRes.ok) {
      const errText = await resendRes.text();
      // 422 = contact already exists — treat as success
      if (resendRes.status === 422) {
        return json({ success: true, already_subscribed: true }, 200, corsHeaders);
      }
      console.error(`Resend ${resendRes.status}:`, errText);
      return json({ error: "resend_error", status: resendRes.status }, 500, corsHeaders);
    }

    return json({ success: true }, 200, corsHeaders);
  },
};

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...headers, "Content-Type": "application/json" },
  });
}
