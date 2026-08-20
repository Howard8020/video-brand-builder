import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Video Brand Builders | Video Ads That Actually Sound Like You",
  description:
    "Tell us about your business. We'll build a script that fits your voice. Lock it, approve the scenes, and get cohesive video prompts that actually go together.",
};

const EXAMPLES = [
  { slug: "apple-blossom", name: "Apple Blossom", category: "Custom Apparel", video: "/examples/apple-blossom.mp4", poster: "/examples/apple-blossom-poster.jpg", blurb: "Warm, upbeat spokesperson ad.", available: true },
  { slug: "spotlight", name: "Spotlight Contractor", category: "Contracting", video: "/examples/spotlight.mp4", poster: "/examples/spotlight-poster.jpg", blurb: "Confident, direct ad for a local contracting business.", available: true },
  { slug: "mvp-video", name: "MVP Transformation", category: "Fitness", video: "/examples/mvp-video.mp4", poster: "/examples/mvp-video-poster.jpg", blurb: "High-energy fitness ad for personal training.", available: true },
];

const FEATURES = [
  { icon: "Lock", title: "Lock the script first", desc: "Approve every word before any clip is generated. Once locked, nothing changes silently." },
  { icon: "Film", title: "One look, every clip", desc: "Continuity profile — spokesperson, setting, lighting, brand — stamped into every segment automatically." },
  { icon: "Check", title: "Claims check built in", desc: "Catches invented prices and guarantees before they reach your ad. Your business, your actual claims." },
];

const STEPS = [
  { num: 1, title: "Tell us about your business", detail: "Client profile with brand voice, continuity preferences, and creative brief. Captured once, used for every ad." },
  { num: 2, title: "Set your ad goal", detail: "Platform, runtime, tone, and CTA. Paste an existing script or let AI draft one from your brief." },
  { num: 3, title: "Review and lock the script", detail: "Revise specific segments or the whole thing. Run claims lint. When it's right, lock it — nothing changes after this." },
  { num: 4, title: "Approve cohesive scenes", detail: "Every segment gets a scene treatment with your continuity profile. Same spokesperson, same setting, same feel." },
  { num: 5, title: "Export or render", detail: "Copyable prompts per clip. Or generate actual video with Veo AI. One ad, done right." },
];

function IconLock() { return <svg className="h-5 w-5 text-[#2DD4BF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0110 0v4" /></svg>; }
function IconFilm() { return <svg className="h-5 w-5 text-[#2DD4BF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><rect x="2" y="2" width="20" height="20" rx="2" /><path d="M2 8h20M2 16h20M8 2v20M16 2v20" /></svg>; }
function IconCheck() { return <svg className="h-5 w-5 text-[#2DD4BF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="10" /></svg>; }
const FEATURE_ICONS: Record<string, React.FC> = { Lock: IconLock, Film: IconFilm, Check: IconCheck };

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-center">
      <h2 className="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">{children}</h2>
      <div className="mx-auto mt-3 h-0.5 w-12 rounded-full bg-[#2DD4BF]" />
    </div>
  );
}

export default function MarketingHome() {
  return (
    <div className="bg-white">
      {/* ── Hero with background image ── */}
      <section className="relative overflow-hidden bg-[#0B1C3E]">
        <div className="absolute inset-0 bg-gradient-to-r from-[#0B1C3E]/95 via-[#0B1C3E]/85 to-[#0B1C3E]/70" />
        <img src="/hero-small-business.jpg" alt="" className="absolute inset-0 h-full w-full object-cover opacity-30" />
        <div className="relative mx-auto max-w-6xl px-6 pt-20 pb-16 sm:pt-28 sm:pb-20 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-xs font-medium text-white/80 backdrop-blur">
              <span className="h-1.5 w-1.5 rounded-full bg-[#2DD4BF]" />
              Human-in-the-loop AI video ads
            </div>
            <h1 className="mt-6 text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Your video ads shouldn&apos;t look like{" "}
              <span className="text-[#2DD4BF]">everyone else&apos;s</span>.
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-base leading-7 text-white/70">
              Tell us about your business. We build a script that fits your voice. You approve it. Every clip comes out consistent — same brand, same message, no invented claims.
            </p>
            <div className="mt-8 flex items-center justify-center gap-4">
              <Link href="/dashboard" className="inline-flex items-center justify-center rounded-lg bg-[#2DD4BF] px-6 py-3 text-sm font-semibold text-[#0B1C3E] shadow-sm hover:bg-[#2DD4BF]/90 transition-all">
                Start your first script — free
              </Link>
              <Link href="/how-to-use" className="inline-flex items-center justify-center rounded-lg border border-white/30 bg-white/10 px-6 py-3 text-sm font-medium text-white hover:bg-white/20 transition-all backdrop-blur">
                How it works →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="border-b border-gray-100 bg-white">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <div className="grid grid-cols-2 gap-6 text-center sm:grid-cols-4">
            {[
              { n: "2", l: "Approval gates" },
              { n: "1", l: "Continuity profile" },
              { n: "4 / 6 / 8", l: "Second clips" },
              { n: "Veo AI", l: "Optional render" },
            ].map((s) => (
              <div key={s.l}>
                <div className="text-lg font-bold text-[#0B1C3E]">{s.n}</div>
                <div className="mt-0.5 text-xs text-gray-500">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Intro video placeholder ── */}
      <section className="mx-auto max-w-4xl px-6 py-16 sm:py-20">
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md">
          <div className="aspect-video flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-white shadow-md">
                <svg className="h-6 w-6 text-[#2DD4BF]" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              </div>
              <p className="mt-3 text-sm font-medium text-gray-700">Watch the intro video</p>
              <p className="mt-1 text-xs text-gray-400">Coming soon — built with Video Brand Builders</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Feature cards ── */}
      <section className="border-t border-gray-100 bg-gray-50/50">
        <div className="mx-auto max-w-6xl px-6 py-16 sm:py-20 lg:px-8">
          <SectionHeading>Built different</SectionHeading>
          <p className="mx-auto mt-4 max-w-2xl text-center text-base text-gray-500">Most AI tools optimize for speed. We optimize for coherence — one ad that sounds like you, every time.</p>
          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-3">
            {FEATURES.map((f) => {
              const Icon = FEATURE_ICONS[f.icon];
              return (
                <div key={f.title} className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md hover:border-[#2DD4BF]/30">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#2DD4BF]/10"><Icon /></div>
                  <h3 className="mt-4 font-semibold text-gray-900">{f.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-gray-500">{f.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Workflow ── */}
      <section className="mx-auto max-w-4xl px-6 py-16 sm:py-20">
        <SectionHeading>How it works</SectionHeading>
        <p className="mx-auto mt-4 max-w-2xl text-center text-base text-gray-500">You describe what you need. The tool builds the ad around it.</p>
        <div className="mt-12 space-y-0">
          {STEPS.map((step, i) => (
            <div key={step.num} className="flex gap-5 border-t border-gray-100 py-6 first:border-t-0 sm:gap-8">
              <div className="flex flex-col items-center">
                <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-[#0B1C3E] text-xs font-bold text-white">{step.num}</div>
                {i < STEPS.length - 1 && <div className="mt-1 w-px flex-1 bg-gray-100" />}
              </div>
              <div className="flex-1 pb-2">
                <h3 className="text-sm font-semibold text-gray-900">{step.title}</h3>
                <p className="mt-1 text-sm leading-6 text-gray-500">{step.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Use cases ── */}
      <section className="border-t border-gray-100 bg-gray-50/50">
        <div className="mx-auto max-w-6xl px-6 py-16 sm:py-20 lg:px-8">
          <SectionHeading>Built for real businesses</SectionHeading>
          <p className="mx-auto mt-4 max-w-2xl text-center text-base text-gray-500">Each client creates a continuity profile that follows every ad — consistent whether they make one video or fifty.</p>
          <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[
              { title: "Contractor", body: "A roofing company needed a quick Instagram ad. Brief in 10 minutes, script approved in one pass, 4 prompts exported in under an hour." },
              { title: "Apparel Brand", body: "An independent boutique wanted consistent brand voice across social. Using continuity, every clip featured the same founder, setting, and brand feel." },
              { title: "Fitness Coach", body: "A personal trainer tested multiple ad angles without rewriting dialogue. Locked the script first, then generated scene variations." },
            ].map((uc) => (
              <div key={uc.title} className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md">
                <div className="text-sm font-semibold text-[#0B1C3E]">{uc.title}</div>
                <p className="mt-2 text-sm leading-6 text-gray-500">{uc.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Gallery ── */}
      <section className="mx-auto max-w-6xl px-6 py-16 sm:py-20 lg:px-8">
        <SectionHeading>See it in action</SectionHeading>
        <p className="mx-auto mt-4 max-w-2xl text-center text-base text-gray-500">Real ads built with Video Brand Builders&apos; script-to-prompt workflow.</p>
        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {EXAMPLES.map((ex) =>
            ex.available ? (
              <div key={ex.slug} className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-all hover:shadow-md">
                <video controls preload="metadata" poster={ex.poster} className="aspect-video w-full bg-black">
                  <source src={ex.video} type="video/mp4" />
                </video>
                <div className="p-4">
                  <div className="text-xs font-medium uppercase tracking-wide text-[#2DD4BF]">{ex.category}</div>
                  <h3 className="mt-1 font-semibold text-gray-900">{ex.name}</h3>
                  <p className="mt-1 text-sm text-gray-500">{ex.blurb}</p>
                </div>
              </div>
            ) : (
              <div key={ex.slug} className="flex aspect-video items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 shadow-sm">
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-400">{ex.name}</p>
                  <p className="mt-1 text-xs text-gray-400">{ex.category}</p>
                </div>
              </div>
            )
          )}
        </div>
      </section>

      {/* ── Quote ── */}
      <section className="border-t border-gray-100 bg-[#0B1C3E]">
        <div className="mx-auto max-w-3xl px-6 py-20 text-center sm:py-24">
          <svg className="mx-auto h-8 w-8 text-[#2DD4BF]/40" fill="currentColor" viewBox="0 0 24 24"><path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/></svg>
          <blockquote className="mt-6 text-xl font-medium leading-8 text-white/90 sm:text-2xl">
            &ldquo;The two-gate workflow means I don&apos;t have to check every clip for consistency. It&apos;s baked in.&rdquo;
          </blockquote>
          <div className="mt-6">
            <div className="mx-auto h-10 w-10 rounded-full bg-white/10 flex items-center justify-center text-sm font-bold text-white/60">JD</div>
            <p className="mt-2 text-sm font-medium text-white/70">Early user</p>
            <p className="text-xs text-white/40">Home services marketing</p>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="mx-auto max-w-3xl px-6 py-20 text-center sm:py-24">
        <h2 className="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">Stop generating video ads that don&apos;t sound like you.</h2>
        <div className="mx-auto mt-4 h-0.5 w-12 rounded-full bg-[#2DD4BF]" />
        <p className="mx-auto mt-4 max-w-lg text-base text-gray-500">Tell us about your business. Get a script that matches your voice. Approve it. Export cohesive prompts.</p>
        <div className="mt-8 flex items-center justify-center gap-4">
          <Link href="/dashboard" className="inline-flex items-center justify-center rounded-lg bg-[#0B1C3E] px-6 py-3 text-sm font-semibold text-white shadow-sm hover:opacity-90 transition-all">
            Start your first script — free
          </Link>
        </div>
        <p className="mt-4 text-xs text-gray-400">No credit card. No 50 disposable variants.</p>
      </section>
    </div>
  );
}
