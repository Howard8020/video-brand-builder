"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const DEFAULT = { company_name: "", website: "", service_category: "", brand_notes: "", logo_path: "", spokesperson: "", delivery: "", setting: "", lighting: "", brand_elements: "" };

export default function ProfilePage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [form, setForm] = useState(DEFAULT);
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const t = localStorage.getItem("vbb_token");
    if (!t) { router.push("/login"); return; }
    setToken(t);
    fetch(`${API_BASE}/api/profile`, { headers: { Authorization: `Bearer ${t}` } })
      .then((r) => r.json())
      .then((data) => { if (data.company_name) setForm(data); })
      .catch(() => {});
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSaving(true);
    setError("");
    try {
      const r = await fetch(`${API_BASE}/api/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(form),
      });
      if (!r.ok) throw new Error("Failed to save");
      setDone(true);
    } catch { setError("Failed to save profile."); }
    finally { setSaving(false); }
  }

  if (done) {
    return (
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <div className="text-4xl mb-4">✅</div>
        <h1 className="text-2xl font-bold">Profile saved</h1>
        <p className="mt-2 text-gray-500">Your brand profile is set. Every project will use these details automatically.</p>
        <button onClick={() => router.push("/dashboard")} className="mt-6 min-h-11 rounded bg-[#0B1C3E] px-6 py-3 text-sm font-semibold text-white hover:opacity-90">
          Go to dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-bold">Your Brand Profile</h1>
      <p className="mt-1 text-sm text-gray-500">Set this up once. Every project you create will use these details for continuity — spokesperson, setting, lighting, and brand voice.</p>

      <form onSubmit={onSubmit} className="mt-8 space-y-6">
        <fieldset className="rounded-lg border border-gray-200 p-5">
          <legend className="text-sm font-semibold text-gray-900 px-1">Company</legend>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700">Company name</label>
              <input value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Website</label>
              <input value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} placeholder="https://" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Service category</label>
              <input value={form.service_category} onChange={(e) => setForm({ ...form, service_category: e.target.value })} placeholder="e.g. Roofing, HVAC, Landscaping" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700">Brand notes</label>
              <textarea value={form.brand_notes} onChange={(e) => setForm({ ...form, brand_notes: e.target.value })} rows={2} placeholder="Tone, colors, style cues the AI should stay consistent with" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
          </div>
        </fieldset>

        <fieldset className="rounded-lg border border-gray-200 p-5">
          <legend className="text-sm font-semibold text-gray-900 px-1">Spokesperson & Continuity</legend>
          <p className="text-xs text-gray-500 mb-3">These details are stamped into every scene prompt so your video clips look like one cohesive shoot.</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Spokesperson</label>
              <input value={form.spokesperson} onChange={(e) => setForm({ ...form, spokesperson: e.target.value })} placeholder="e.g. owner-operator, crew lead" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Delivery style</label>
              <input value={form.delivery} onChange={(e) => setForm({ ...form, delivery: e.target.value })} placeholder="e.g. warm, confident, direct" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Setting</label>
              <input value={form.setting} onChange={(e) => setForm({ ...form, setting: e.target.value })} placeholder="e.g. jobsite, front porch, office" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Lighting</label>
              <input value={form.lighting} onChange={(e) => setForm({ ...form, lighting: e.target.value })} placeholder="e.g. bright daylight, warm interior" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700">Brand elements</label>
              <input value={form.brand_elements} onChange={(e) => setForm({ ...form, brand_elements: e.target.value })} placeholder="e.g. logo on hat, truck wrap, uniform colors" className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
          </div>
        </fieldset>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={saving} className="min-h-11 rounded bg-[#0B1C3E] px-6 py-3 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-60">
          {saving ? "Saving…" : "Save profile"}
        </button>
      </form>
    </div>
  );
}
