"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listProjects, createProject, login as apiLogin } from "@/lib/api";

interface Project {
  id: string;
  status: string;
  brief: Record<string, any>;
  updated_at?: string;
  client_id?: string;
}

interface Template {
  id: string;
  title: string;
  trade: string;
  emoji: string;
  description: string;
  prefill: {
    serviceLine: string;
    goal: string;
    audience: string;
    tones: string;
    cta: string;
    platform: string;
    aspect: string;
    runtime: string;
    visualMode: string;
  };
  continuity: {
    mode: string;
    spokesperson: string;
    delivery: string;
    setting: string;
    lighting: string;
    brand: string;
  };
}

const TEMPLATES: Template[] = [
  {
    id: "spring-inspection",
    title: "Spring Roofing Inspection",
    trade: "Roofing / Gutter",
    emoji: "🏠",
    description: "Urgent seasonal ad targeting homeowners before spring storms hit.",
    prefill: {
      serviceLine: "Roofing inspection & repair",
      goal: "drive urgent seasonal calls",
      audience: "homeowners 35-65 within 20 miles",
      tones: "urgent, trustworthy, local",
      cta: "Schedule your free inspection today",
      platform: "Instagram",
      aspect: "9:16",
      runtime: "15",
      visualMode: "spokesperson",
    },
    continuity: {
      mode: "spokesperson",
      spokesperson: "experienced crew leader",
      delivery: "direct, confident, reassuring",
      setting: "residential rooftop with skyline",
      lighting: "bright natural daylight",
      brand: "company logo on hat/vest, truck visible",
    },
  },
  {
    id: "summer-tuneup",
    title: "Summer AC Tune-Up",
    trade: "HVAC",
    emoji: "❄️",
    description: "Helpful seasonal reminder for AC maintenance before peak heat.",
    prefill: {
      serviceLine: "HVAC maintenance & repair",
      goal: "book preventive maintenance appointments",
      audience: "homeowners 30-65",
      tones: "helpful, seasonal, friendly",
      cta: "Book your AC tune-up now",
      platform: "Facebook",
      aspect: "9:16",
      runtime: "24",
      visualMode: "spokesperson",
    },
    continuity: {
      mode: "spokesperson",
      spokesperson: "friendly service technician",
      delivery: "warm, educational",
      setting: "residential driveway with service van",
      lighting: "bright sunny day",
      brand: "logo on van, uniform shirt",
    },
  },
  {
    id: "before-after",
    title: "Before & After Showcase",
    trade: "Any Trade",
    emoji: "✨",
    description: "Visual proof ad — let the transformation speak for itself.",
    prefill: {
      serviceLine: "Home improvement",
      goal: "generate quality leads with visual proof",
      audience: "homeowners considering renovations",
      tones: "proud, visual, aspirational",
      cta: "Get your free quote today",
      platform: "TikTok",
      aspect: "9:16",
      runtime: "30",
      visualMode: "mixed",
    },
    continuity: {
      mode: "mixed",
      spokesperson: "project manager",
      delivery: "enthusiastic, proud",
      setting: "alternating between finished project and job site",
      lighting: "professional — highlight before/after contrast",
      brand: "logo watermark, consistent color grade",
    },
  },
  {
    id: "emergency-service",
    title: "Emergency Service",
    trade: "Plumbing / Electrical",
    emoji: "🔧",
    description: "Direct response ad for urgent service calls — calm, fast, available now.",
    prefill: {
      serviceLine: "Emergency plumbing & electrical",
      goal: "drive immediate emergency calls",
      audience: "homeowners in service area",
      tones: "direct, calm urgency, reliable",
      cta: "Call now — we answer 24/7",
      platform: "Instagram",
      aspect: "9:16",
      runtime: "15",
      visualMode: "spokesperson",
    },
    continuity: {
      mode: "spokesperson",
      spokesperson: "dispatched technician",
      delivery: "calm, direct, reassuring",
      setting: "service van interior or residential driveway",
      lighting: "evening/night setting — on-call readiness",
      brand: "logo visible, phone number on van",
    },
  },
  {
    id: "landscaping-seasonal",
    title: "Spring Clean-Up",
    trade: "Landscaping",
    emoji: "🌿",
    description: "Friendly seasonal invite for yard clean-up and spring prep.",
    prefill: {
      serviceLine: "Landscaping & yard maintenance",
      goal: "book seasonal clean-up jobs",
      audience: "homeowners with yards",
      tones: "friendly, inviting, local",
      cta: "Book your spring clean-up today",
      platform: "Instagram",
      aspect: "9:16",
      runtime: "24",
      visualMode: "spokesperson",
    },
    continuity: {
      mode: "spokesperson",
      spokesperson: "friendly crew lead",
      delivery: "warm, approachable",
      setting: "freshly landscaped front yard",
      lighting: "golden hour / soft afternoon",
      brand: "logo on truck, crew in branded shirts",
    },
  },
  {
    id: "remodel-reveal",
    title: "Remodel Reveal",
    trade: "Contracting / Remodeling",
    emoji: "🏗️",
    description: "Aspirational ad showcasing a completed room transformation.",
    prefill: {
      serviceLine: "Home remodeling & renovation",
      goal: "generate remodel consultation leads",
      audience: "homeowners planning renovations",
      tones: "aspirational, proud, detailed",
      cta: "Start your remodel consultation",
      platform: "Facebook",
      aspect: "9:16",
      runtime: "30",
      visualMode: "mixed",
    },
    continuity: {
      mode: "mixed",
      spokesperson: "lead designer or project manager",
      delivery: "proud, walkthrough style",
      setting: "finished kitchen or bathroom",
      lighting: "interior — warm, inviting",
      brand: "logo watermark, before/after split",
    },
  },
  {
    id: "new-mover-welcome",
    title: "New Homeowner Welcome",
    trade: "Home Services General",
    emoji: "🏡",
    description: "Welcome new neighbors with a helpful introduction to your services.",
    prefill: {
      serviceLine: "Home services",
      goal: "capture new mover leads in service area",
      audience: "new homeowners who just moved in",
      tones: "welcoming, helpful, local",
      cta: "Get your new homeowner welcome kit",
      platform: "Facebook",
      aspect: "9:16",
      runtime: "15",
      visualMode: "spokesperson",
    },
    continuity: {
      mode: "spokesperson",
      spokesperson: "friendly owner or manager",
      delivery: "warm, neighborly",
      setting: "front porch or neighborhood street",
      lighting: "soft natural light",
      brand: "logo on sign or shirt",
    },
  },
];

const DEFAULT_FORM = { clientId: "", serviceLine: "", goal: "", audience: "", tones: "", visualMode: "spokesperson", cta: "", runtime: "24", platform: "Instagram", aspect: "9:16" };

export default function Dashboard() {
  const [token, setToken] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("vbb_token");
    if (!t) return;
    setToken(t);
    listProjects(t).then(setProjects).catch(() => {});
  }, []);

  if (!token) {
    return <LoginInline email={email} setEmail={setEmail} password={password} setPassword={setPassword} error={error} setError={setError} onLogin={(t: string) => { localStorage.setItem("vbb_token", t); setToken(t); }} />;
  }

  function applyTemplate(tpl: Template) {
    setSelectedTemplate(tpl.id);
    setForm((f) => ({ ...f, ...tpl.prefill }));
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const brief = {
        clientName: form.clientId || form.serviceLine,
        serviceLine: form.serviceLine,
        goal: form.goal,
        audience: form.audience,
        tones: form.tones.split(",").map((s) => s.trim()),
        platform: form.platform,
        aspect: form.aspect,
        runtime: parseInt(form.runtime),
        visualMode: form.visualMode,
        cta: form.cta,
      };
      const p = await createProject(token!, { client_id: form.clientId, mode: "ai", source_script: "", brief, settings: { wpm: 125, clipLengths: [4, 6, 8] } });
      window.location.href = `/project/${p.id}/review`;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create project");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Your Projects</h1>
          <p className="mt-1 text-xs text-gray-500">Pick a template or start from scratch.</p>
        </div>
        <button onClick={() => { setShowNew(!showNew); setSelectedTemplate(null); }} className="min-h-11 rounded bg-[#0B1C3E] px-4 py-2 text-sm font-medium text-white hover:opacity-90">
          New Project
        </button>
      </div>

      {showNew && (
        <div className="mb-10">
          <form onSubmit={onCreate} className="space-y-4 rounded border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-900">
                {selectedTemplate ? `New: ${TEMPLATES.find((t) => t.id === selectedTemplate)?.title || "Project"}` : "New Project"}
              </h2>
            </div>
            <div>
              <label className="block text-sm font-medium">Template</label>
              <select
                value={selectedTemplate || ""}
                onChange={(e) => {
                  const val = e.target.value;
                  if (val === "__scratch__") {
                    setSelectedTemplate(null);
                    setForm(DEFAULT_FORM);
                  } else {
                    const tpl = TEMPLATES.find((t) => t.id === val);
                    if (tpl) applyTemplate(tpl);
                  }
                }}
                className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">Start from scratch</option>
                <option disabled>──────────</option>
                {TEMPLATES.map((tpl) => (
                  <option key={tpl.id} value={tpl.id}>
                    {tpl.emoji} {tpl.title} — {tpl.trade}
                  </option>
                ))}
              </select>
            </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium">Company name</label>
              <input value={form.clientId} onChange={(e) => setForm({ ...form, clientId: e.target.value })} placeholder="Your business name" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium">Service line</label>
              <input value={form.serviceLine} onChange={(e) => setForm({ ...form, serviceLine: e.target.value })} className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium">Goal</label>
              <input value={form.goal} onChange={(e) => setForm({ ...form, goal: e.target.value })} className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium">Audience</label>
              <input value={form.audience} onChange={(e) => setForm({ ...form, audience: e.target.value })} className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium">Tones (comma)</label>
              <input value={form.tones} onChange={(e) => setForm({ ...form, tones: e.target.value })} className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium">CTA</label>
              <input value={form.cta} onChange={(e) => setForm({ ...form, cta: e.target.value })} className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium">Runtime (seconds)</label>
              <input type="number" value={form.runtime} onChange={(e) => setForm({ ...form, runtime: e.target.value })} className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium">Platform</label>
              <input value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value })} className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={busy} className="min-h-11 rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
            {busy ? "Creating…" : "Create project"}
          </button>
        </form>
        </div>
      )}

      <div className="space-y-3">
        {projects.length === 0 && (
          <div className="rounded border border-dashed border-gray-300 p-8 text-center">
            <p className="text-sm text-gray-500">No projects yet.</p>
            <button
              onClick={() => { setShowNew(true); }}
              className="mt-3 min-h-11 rounded bg-[#0B1C3E] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
            >
              Create your first project →
            </button>
          </div>
        )}
        {projects.map((p) => (
          <Link key={p.id} href={`/project/${p.id}/review`} className="block rounded border border-gray-200 p-4 hover:border-gray-400">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{p.brief?.clientName || "Untitled"}</div>
                <div className="text-xs text-gray-500">{p.brief?.serviceLine} · {p.status}</div>
              </div>
              <div className="text-xs text-gray-400">{new Date(p.updated_at || "").toLocaleString()}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function LoginInline({ email, setEmail, password, setPassword, error, setError, onLogin }: any) {
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const data = await apiLogin(email, password);
      onLogin(data.access_token);
    } catch {
      setError("Login failed");
    }
  }
  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="text-2xl font-bold mb-6">Sign in to Video Brand Builder</h1>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" required />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" className="min-h-11 w-full rounded bg-black px-4 py-2 text-sm font-medium text-white">Sign in</button>
      </form>
      <p className="mt-4 text-center text-xs text-gray-400">
        Your data is encrypted in transit and never shared with third parties.
      </p>
    </div>
  );
}
