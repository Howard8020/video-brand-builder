import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "How to Use Video Brand Builder",
  description: "Step-by-step guide to creating professional video ads — from client setup to export.",
};

const STEPS = [
  {
    num: 1,
    title: "Create a Client",
    detail:
      "Every ad starts with a client. Add their business name, category (e.g., Apparel, Contractor, Fitness), and brand notes — tone, colors, style cues the AI should stay consistent with. This is where you also set Continuity (spokesperson, setting, lighting, brand elements), which gets stamped into every scene automatically.",
    tip: "Fill in continuity fields now — it saves you from fixing mismatched clips later.",
  },
  {
    num: 2,
    title: "Start a New Project",
    detail:
      "Pick your client, describe your ad's goal (awareness, leads, appointments), target audience, tone, platform (Instagram, TikTok), aspect ratio, runtime, and CTA. You can paste your own script or let the AI draft one from scratch. Each project goes through a structured pipeline — you can't skip steps or accidentally publish unfinished work.",
    tip: "Use the seed quick-fill buttons (Apple Blossom, Spotlight, MVP Transformation) to pre-populate a real-world example.",
  },
  {
    num: 3,
    title: "Review & Lock the Script — Gate 1",
    detail:
      "Read the AI-generated script. You can revise the full script with a single instruction or target a specific segment. Switch to the Hooks tab to generate alternate opening lines. Run the Claims Lint to catch any invented prices, guarantees, or credentials before they reach a real ad. When the script is right, click Approve Script — this locks the dialogue so nothing changes silently.",
    tip: "Write your instruction like 'Make this more urgent' or 'Shorten the first segment to 4 seconds' — the AI follows plain English direction.",
  },
  {
    num: 4,
    title: "Review Scenes — Gate 2",
    detail:
      "After script lock, the AI drafts one scene treatment per segment: camera direction, action description, and on-screen text. Each scene is stamped with your client's continuity profile (same spokesperson, setting, lighting, brand). You can revise individual scenes without touching the locked dialogue. When everything looks right, click Approve Scenes.",
    tip: "The continuity stamp is what makes your final ad look like one coherent shoot — not five random clips jammed together.",
  },
  {
    num: 5,
    title: "Export Prompts",
    detail:
      "Approve scenes to unlock the Export tab. You'll get one copyable prompt per segment in Flow-ready format (duration, aspect ratio, camera direction, exact dialogue, continuity block), plus a social caption. Paste each prompt into your video generation tool one at a time, then stitch the clips together. That's a complete, on-brand ad ready to publish.",
    tip: "Each prompt is self-contained — you can paste them in any order, but the continuity ensures they'll match.",
  },
  {
    num: 6,
    title: "Render with Veo AI (Premium)",
    detail:
      "If you've purchased render credits, you can generate actual video clips directly from your approved prompts — no manual pasting required. Select Standard ($9.99, 720p) or Pro ($29.99, 1080p), click Render All Segments, and watch the status update as each clip is generated. Buy credits in packs of $20, $50, or $150; credits never expire.",
    tip: "Standard tier (Veo 3.1 Fast) is ideal for social media ads — good quality at a fraction of the cost.",
  },
];

export default function HowToUsePage() {
  return (
    <div className="bg-white">
      {/* Hero */}
      <section className="mx-auto max-w-3xl px-4 pt-16 pb-12 text-center sm:pt-24 sm:pb-16">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          How to use Video Brand Builder
        </h1>
        <p className="mt-4 text-base text-gray-600">
          Six steps from blank slate to a finished ad. Each gate is a checkpoint that keeps your
          message consistent and your brand on track.
        </p>
      </section>

      {/* Steps */}
      <section className="mx-auto max-w-4xl px-4 pb-20 sm:px-6">
        <div className="space-y-10">
          {STEPS.map((step) => (
            <div key={step.num} className="flex gap-5 sm:gap-8">
              <div className="flex flex-col items-center">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-[#0B1C3E] text-sm font-bold text-white">
                  {step.num}
                </div>
                {step.num < STEPS.length && <div className="mt-2 w-px flex-1 bg-gray-200" />}
              </div>
              <div className="flex-1 pb-6">
                <h2 className="text-lg font-semibold text-gray-900">{step.title}</h2>
                <p className="mt-2 text-sm leading-6 text-gray-600">{step.detail}</p>
                <p className="mt-2 text-xs text-[#2DD4BF]">💡 {step.tip}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Link
            href="/dashboard"
            className="min-h-11 inline-flex items-center justify-center rounded bg-[#0B1C3E] px-6 py-3 text-sm font-semibold text-white hover:opacity-90"
          >
            Start your first project
          </Link>
        </div>
      </section>
    </div>
  );
}
