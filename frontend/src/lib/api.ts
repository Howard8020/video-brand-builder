const API_BASE = process.env.NEXT_PUBLIC_API_URL;
export { API_BASE };
if (!API_BASE && typeof window !== "undefined") {
  console.error(
    "NEXT_PUBLIC_API_URL is not set. API calls will fail. Set it in .env.local (dev) or your hosting platform's environment variables (production)."
  );
}

async function request(path: string, options: RequestInit = {}) {
  const url = `${API_BASE ?? ""}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    let message = text;
    try {
      const data = JSON.parse(text);
      message = data.detail || message;
    } catch {
      // keep raw text
    }
    throw new Error(message || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function login(email: string, password: string) {
  const form = new FormData();
  form.append("username", email);
  form.append("password", password);
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

export async function register(email: string, password: string) {
  return request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function listClients(token: string) {
  return request("/api/clients/", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function loadSeedClient(token: string, name: string) {
  const list = await listClients(token);
  return list.find((c: any) => c.name.toLowerCase() === name.toLowerCase()) || null;
}

export async function createClient(token: string, payload: any) {
  return request("/api/clients/", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function listProjects(token: string) {
  return request("/api/projects/", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function createProject(token: string, payload: any) {
  return request("/api/projects/", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function generateProject(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/generate`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function reviseProject(token: string, projectId: string, payload: { instruction: string; segment_index?: number }) {
  return request(`/api/projects/${projectId}/revise`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
}

export async function approveScript(token: string, projectId: string, draftScenes = true) {
  return request(`/api/projects/${projectId}/approve-script`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ draft_scenes: draftScenes }),
  });
}

export async function approveScenes(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/approve-scenes`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getProjectPrompts(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/prompts`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function refreshHooks(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/hooks`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function refreshCaption(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/caption`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function lintProject(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/lint`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ── Render (Veo) ──────────────────────────────────────────────────

export async function startRender(token: string, projectId: string, tier: "standard" | "pro" = "standard") {
  return request(`/api/projects/${projectId}/render?tier=${tier}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getRenderStatus(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/render/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

// ── Assembly (join segments into one postable video) ──────────────

export async function assembleProject(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/assemble`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getAssembledVideo(token: string, projectId: string) {
  return request(`/api/projects/${projectId}/assemble`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

/** Absolute URL for playback. The /assembled mount is public, so <video src>
 *  does not need to carry the auth header. */
export function assembledPlaybackUrl(relativeUrl: string) {
  return `${API_BASE}${relativeUrl}`;
}

/** Download the assembled video.
 *
 * Fetched with the Authorization header and saved via a blob URL, because a
 * plain <a href> cannot send the bearer token and would 401. */
export async function downloadAssembled(token: string, projectId: string, filename: string) {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/assemble/download`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    let detail = `Download failed (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) detail = data.detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// ── Billing / Credits ─────────────────────────────────────────────

export async function getCreditBalance(token: string) {
  return request("/api/payments/balance", { headers: { Authorization: `Bearer ${token}` } });
}

export async function getPricing(token: string) {
  return request("/api/payments/pricing", { headers: { Authorization: `Bearer ${token}` } });
}

export async function createCheckout(token: string, amountCents: number) {
  return request("/api/payments/create-checkout", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ amount_cents: amountCents }),
  });
}
