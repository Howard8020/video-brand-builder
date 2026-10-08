"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { generateProject, reviseProject, approveScript, approveScenes, getProjectPrompts, refreshCaption, refreshHooks, lintProject, startRender, getRenderStatus, API_BASE, assembleProject, getAssembledVideo, assembledPlaybackUrl, downloadAssembled } from "@/lib/api";

interface Segment {
  name?: string;
  purpose?: string;
  duration?: number;
  spoken?: string;
  on_screen_text?: string;
}

interface Script {
  title?: string;
  segments?: Segment[];
}

interface Scene {
  action?: string;
  camera?: string;
  on_screen_text?: string;
}

interface ProjectData {
  id: string;
  user_id: string;
  client_id?: string;
  status: string;
  brief: Record<string, any>;
  continuity: Record<string, any>;
  script?: Script;
  scenes?: { scenes?: Scene[] };
  prompts?: any;
  versions?: any[];
  source_script?: string;
  adaptation_note?: string;
  settings?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export default function ProjectReview() {
  const params = useParams();
  const router = useRouter();
  const projectId = Array.isArray(params?.id) ? params.id[0] : (params?.id as string);
  const token = typeof window !== "undefined" ? localStorage.getItem("vbb_token") : null;

  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [generating, setGenerating] = useState(false);
  const [revising, setRevising] = useState(false);
  const [approvingScript, setApprovingScript] = useState(false);
  const [approvingScenes, setApprovingScenes] = useState(false);
  const [refreshingCaption, setRefreshingCaption] = useState(false);
  const [refreshingHooks, setRefreshingHooks] = useState(false);
  const [hooksResult, setHooksResult] = useState<string | null>(null);

  const [instruction, setInstruction] = useState("");
  const [segmentIndex, setSegmentIndex] = useState<number | null>(null);
  const [draftScenes, setDraftScenes] = useState(true);
  const [lintResult, setLintResult] = useState<{ flags: any[] } | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem("vbb_token")) {
      router.replace("/login");
    }
  }, [router]);

  const [promptsReady, setPromptsReady] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<"script" | "hooks" | "scenes" | "export">("script");
  const [segmentRevising, setSegmentRevising] = useState<{ [key: number]: { instruction: string; busy: boolean } }>({});

  const [continuity, setContinuity] = useState<Record<string, string>>({});
  const [renderTier, setRenderTier] = useState<"standard" | "pro">("pro");
  const [renderRunning, setRenderRunning] = useState(false);
  const [renderJobs, setRenderJobs] = useState<any[] | null>(null);
  const [renderStatus, setRenderStatus] = useState<any[] | null>(null);
  const [pollInterval, setPollInterval] = useState<ReturnType<typeof setInterval> | null>(null);

  // ── Assembly: join the segments into one postable video ──
  const [assembling, setAssembling] = useState(false);
  const [assembled, setAssembled] = useState<any | null>(null);
  const [assembleError, setAssembleError] = useState("");
  const [downloading, setDownloading] = useState(false);

  async function load() {
    if (!token || !projectId) return;
    setLoading(true);
    try {
      const data = await (await fetch(`${API_BASE ?? ""}/api/projects/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })).json();
      setProject(data);
      setContinuity((data.continuity || {}) as any);
      if (data.status === "approved" && data.prompts) {
        setPromptsReady(data.prompts);
      }
      // Surface an already-assembled video so the final file survives a reload
      // instead of appearing to vanish.
      try {
        const asm = await getAssembledVideo(token, projectId);
        if (asm?.assembled) setAssembled(asm);
      } catch {
        /* nothing assembled yet */
      }
    } catch {
      setError("Failed to load project");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [token, projectId]);

  function updateContinuity(key: string, value: string) {
    setContinuity((s) => ({ ...s, [key]: value }));
  }

  async function onGenerate() {
    if (!project || !token) return;
    setGenerating(true);
    try {
      const data = await generateProject(token, project.id);
      setProject({ ...project, status: "script_review", script: data.script, brief: { ...project.brief, ...(data.brief || {}) }, adaptation_note: data.adaptation_note } as any);
      setActiveTab("script");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function onRevise() {
    if (!project || !token || !instruction.trim()) return;
    setRevising(true);
    try {
      const data = await reviseProject(token, project.id, { instruction, segment_index: segmentIndex ?? undefined });
      setProject({ ...project, script: data.script } as any);
      setInstruction("");
      setSegmentIndex(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Revision failed");
    } finally {
      setRevising(false);
    }
  }

  async function onSegmentRevise(idx: number) {
    if (!project || !token) return;
    const instr = segmentRevising[idx]?.instruction || "";
    if (!instr.trim()) return;
    setSegmentRevising((s) => ({ ...s, [idx]: { instruction: s[idx]?.instruction || "", busy: true } }));
    try {
      const data = await reviseProject(token, project.id, { instruction: instr, segment_index: idx });
      setProject({ ...project, script: data.script } as any);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Revision failed");
    } finally {
      setSegmentRevising((s) => ({ ...s, [idx]: { instruction: s[idx]?.instruction || "", busy: false } }));
    }
  }

  async function onApproveScript() {
    if (!project || !token) return;
    setApprovingScript(true);
    try {
      const data = await approveScript(token, project.id, draftScenes);
      setProject({ ...project, status: data.status, scenes: data.scenes } as any);
      setActiveTab("scenes");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approve failed");
    } finally {
      setApprovingScript(false);
    }
  }

  async function onApproveScenes() {
    if (!project || !token) return;
    setApprovingScenes(true);
    try {
      const prompts = await approveScenes(token, project.id);
      setPromptsReady(prompts);
      setProject({ ...project, status: "approved", prompts } as any);
      setActiveTab("export");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approve scenes failed");
    } finally {
      setApprovingScenes(false);
    }
  }

  async function onRefreshCaption() {
    if (!project || !token) return;
    setRefreshingCaption(true);
    try {
      const data = await refreshCaption(token, project.id);
      setProject({ ...project, prompts: { ...project.prompts, social: data } } as any);
      setPromptsReady({ ...promptsReady, social: data } as any);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Caption refresh failed");
    } finally {
      setRefreshingCaption(false);
    }
  }

  async function onRefreshHooks() {
    if (!project || !token) return;
    setRefreshingHooks(true);
    setHooksResult(null);
    try {
      const data = await refreshHooks(token, project.id);
      setProject({ ...project, script: data.script } as any);
      setHooksResult("Alternate hooks loaded into the first segment.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hooks refresh failed");
    } finally {
      setRefreshingHooks(false);
    }
  }

  async function onLint() {
    if (!project || !token) return;
    try {
      const data = await lintProject(token, project.id);
      setLintResult(data);
    } catch {
      setError("Lint failed");
    }
  }

  function copyBlock(text: string) {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
    }
  }

  async function onStartRender() {
    if (!project || !token) return;
    setRenderRunning(true);
    setRenderJobs(null);
    try {
      const result = await startRender(token, project.id, renderTier);
      setRenderJobs(result.jobs);
      // Start polling
      const interval = setInterval(async () => {
        try {
          const status = await getRenderStatus(token, project.id);
          setRenderStatus(status.jobs);
          const allDone = status.jobs.every((j: any) => j.status === "succeeded" || j.status === "failed");
          if (allDone) {
            clearInterval(interval);
            setRenderRunning(false);
            setPollInterval(null);
          }
        } catch {
          clearInterval(interval);
          setRenderRunning(false);
          setPollInterval(null);
        }
      }, 5000);
      setPollInterval(interval);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Render failed");
      setRenderRunning(false);
    }
  }

  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [pollInterval]);

  // Join the rendered segments into one platform-ready video.
  async function onAssemble() {
    if (!project || !token) return;
    setAssembling(true);
    setAssembleError("");
    try {
      const result = await assembleProject(token, project.id);
      setAssembled(result);
    } catch (e) {
      setAssembleError(e instanceof Error ? e.message : "Assembly failed");
    } finally {
      setAssembling(false);
    }
  }

  async function onDownload() {
    if (!project || !token || !assembled) return;
    setDownloading(true);
    setAssembleError("");
    try {
      await downloadAssembled(token, project.id, assembled.filename);
    } catch (e) {
      setAssembleError(e instanceof Error ? e.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  }

  if (loading) {
    return <div className="mx-auto max-w-5xl px-4 py-10 text-sm text-gray-500">Loading project…</div>;
  }

  if (!project) {
    return <div className="mx-auto max-w-3xl px-4 py-10 text-sm text-red-600">{error || "Project not found"}</div>;
  }

  const status = project.status;
  const script = project.script || { segments: [] };
  const segs = script.segments || [];
  const scenesList = (project.scenes && project.scenes.scenes) || [];
  const brief = project.brief || {};
  const renderList = renderStatus || renderJobs || [];
  const allSegmentsSucceeded =
    renderList.length > 0 && renderList.every((j: any) => j.status === "succeeded");

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 space-y-6">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{brief.clientName || "Untitled project"}</h1>
          <div className="mt-1 text-xs text-gray-500">
            {brief.serviceLine} · {brief.platform} · {brief.runtime}s · {status}
          </div>
          {project.adaptation_note && <p className="mt-1 text-xs text-gray-600">Adapted: {project.adaptation_note}</p>}
          {project.source_script && <p className="mt-1 text-xs text-gray-500">Has source script</p>}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => router.push("/dashboard")} className="rounded border border-gray-200 px-3 py-1 text-xs hover:border-gray-400">
            Back to projects
          </button>
        </div>
      </header>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Continuity sidebar */}
      {(status === "script_review" || status === "scene_review") && (
        <aside className="rounded border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Continuity</h2>
            <span className="text-xs text-gray-500">Fixed across all segments</span>
          </div>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
            <ContinuityField label="Spokesperson / mode" value={continuity.spokesperson || continuity.mode || ""} onChange={(v) => updateContinuity("spokesperson", v)} />
            <ContinuityField label="Vocal delivery" value={continuity.delivery || ""} onChange={(v) => updateContinuity("delivery", v)} />
            <ContinuityField label="Setting" value={continuity.setting || ""} onChange={(v) => updateContinuity("setting", v)} />
            <ContinuityField label="Lighting" value={continuity.lighting || ""} onChange={(v) => updateContinuity("lighting", v)} />
            <ContinuityField label="Brand elements" value={continuity.brand || ""} onChange={(v) => updateContinuity("brand", v)} />
          </div>
        </aside>
      )}

      {status === "draft" && (
        <section className="space-y-4">
          <div className="rounded border border-gray-200 p-4 text-sm">
            <p className="font-medium">Brief ready</p>
            <ul className="mt-2 list-disc pl-5 text-gray-600 space-y-1">
              <li>Audience: {brief.audience}</li>
              <li>Tone: {(brief.tones || []).join(", ")}</li>
              <li>CTA: {brief.cta}</li>
              <li>Aspect: {brief.aspect}</li>
            </ul>
          </div>
          <button disabled={generating} onClick={onGenerate} className="rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
            {generating ? "Generating…" : "Generate script"}
          </button>
        </section>
      )}

      {status === "script_review" && (
        <>
          <div className="flex items-center gap-2">
            <button onClick={() => setActiveTab("script")} className={`rounded px-3 py-1 text-xs ${activeTab === "script" ? "bg-black text-white" : "border border-gray-200"}`}>Script</button>
            <button onClick={() => setActiveTab("hooks")} className={`rounded px-3 py-1 text-xs ${activeTab === "hooks" ? "bg-black text-white" : "border border-gray-200"}`}>Hooks</button>
            <button onClick={onLint} className="rounded border border-gray-200 px-3 py-1 text-xs hover:border-gray-400">Run claim lint</button>
          </div>

          {activeTab === "script" && (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Gate 1 — script</h2>
              {segs.map((seg, idx) => (
                <div key={idx} className="rounded border border-gray-200 p-4">
                  <div className="text-sm font-medium">#{idx + 1} — {seg.name} ({seg.purpose}, {seg.duration}s)</div>
                  <p className="mt-1 text-sm text-gray-800">{seg.spoken}</p>
                  {seg.on_screen_text && <p className="mt-1 text-xs text-gray-500">On-screen: {seg.on_screen_text}</p>}
                  <div className="mt-3 flex items-center gap-2">
                    <input
                      type="text"
                      placeholder="Revise this segment"
                      className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs focus:border-black focus:outline-none"
                      onChange={(e) => setSegmentRevising((s) => ({ ...s, [idx]: { ...s[idx], instruction: e.target.value } }))}
                    />
                    <button disabled={segmentRevising[idx]?.busy} onClick={() => onSegmentRevise(idx)} className="rounded bg-black px-3 py-1 text-xs font-medium text-white disabled:opacity-60">
                      {segmentRevising[idx]?.busy ? "Saving…" : "Revise"}
                    </button>
                  </div>
                </div>
              ))}

              <div className="rounded border border-gray-200 p-3 text-xs text-gray-600">
                <label className="font-medium text-gray-700">Revise full script</label>
                <div className="mt-1 flex items-center gap-2">
                  <input value={instruction} onChange={(e) => setInstruction(e.target.value)} placeholder="Make it punchier / shorter / fix hook…" className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs focus:border-black focus:outline-none" />
                  <button disabled={revising} onClick={onRevise} className="rounded bg-black px-3 py-1 text-xs font-medium text-white disabled:opacity-60">{revising ? "Saving…" : "Apply"}</button>
                </div>
              </div>

              {lintResult && (
                <div className="rounded border border-gray-200 p-3 text-xs">
                  <div className="font-medium">Claim lint</div>
                  {lintResult.flags.length === 0 && <p className="mt-1 text-green-700">No flagged claims.</p>}
                  {lintResult.flags.length > 0 && (
                    <ul className="mt-1 list-disc pl-5 text-red-700">
                      {lintResult.flags.map((f, i) => (
                        <li key={i}>seg {f.seg + 1}: {f.text} ({f.kind})</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              <div className="flex items-center gap-4">
                <button disabled={approvingScript} onClick={onApproveScript} className="rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
                  {approvingScript ? "Approving…" : "Approve script + draft scenes"}
                </button>
                <label className="flex items-center gap-2 text-xs text-gray-700">
                  <input type="checkbox" checked={draftScenes} onChange={(e) => setDraftScenes(e.target.checked)} />
                  Draft scenes with LLM
                </label>
              </div>
            </section>
          )}

          {activeTab === "hooks" && (
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Alternate hooks</h2>
                <button disabled={refreshingHooks} onClick={onRefreshHooks} className="rounded bg-black px-3 py-1 text-xs font-medium text-white disabled:opacity-60">
                  {refreshingHooks ? "Generating…" : "Regenerate alternates"}
                </button>
              </div>
              <p className="text-xs text-gray-500">This replaces the first segment with alternate hook options from the LLM. Use it when you want a stronger opening.</p>
              {hooksResult && <p className="text-xs text-gray-700">{hooksResult}</p>}
              <div className="rounded border border-gray-200 p-4">
                <div className="text-sm font-medium">#{1} — {segs[0]?.name} (hook, {segs[0]?.duration}s)</div>
                <p className="mt-1 text-sm text-gray-800">{segs[0]?.spoken}</p>
              </div>
            </section>
          )}
        </>
      )}

      {status === "scene_review" && (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Gate 2 — scenes</h2>
          </div>
          {scenesList.map((scene, idx) => (
            <div key={idx} className="rounded border border-gray-200 p-4">
              <div className="text-sm font-medium">#{idx + 1}</div>
              <p className="mt-1 text-sm text-gray-800">{scene.action}</p>
              <p className="text-xs text-gray-600">Camera: {scene.camera}</p>
              {scene.on_screen_text && <p className="text-xs text-gray-600">On-screen: {scene.on_screen_text}</p>}
            </div>
          ))}
          <div className="flex items-center gap-3">
            <button disabled={approvingScenes} onClick={onApproveScenes} className="rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
              {approvingScenes ? "Approving…" : "Approve scenes"}
            </button>
          </div>
        </section>
      )}

      {status === "approved" && (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Export</h2>
            <button disabled={refreshingCaption} onClick={onRefreshCaption} className="rounded border border-gray-200 px-3 py-1 text-xs hover:border-gray-400">
              Refresh caption
            </button>
          </div>
          {(promptsReady?.segments || []).map((seg: any) => (
            <div key={seg.segment} className="rounded border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Segment {seg.segment} — {seg.name}</div>
                <button onClick={() => copyBlock(seg.prompt)} className="rounded border border-gray-200 px-2 py-1 text-xs hover:border-gray-400">Copy prompt</button>
              </div>
              <pre className="mt-2 whitespace-pre-wrap rounded bg-gray-50 p-3 text-xs text-gray-700">{seg.prompt}</pre>
            </div>
          ))}
          {promptsReady?.social && (
            <div className="rounded border border-gray-200 p-4">
              <div className="text-sm font-medium">Social caption</div>
              <pre className="mt-2 whitespace-pre-wrap rounded bg-gray-50 p-3 text-xs text-gray-700">{promptsReady.social.caption || promptsReady.social}</pre>
            </div>
          )}

          {/* Render tier */}
          <div className="rounded border border-[#0B1C3E] p-4">
            <h3 className="text-sm font-semibold">Render with Veo AI</h3>
            <p className="mt-1 text-xs text-gray-500">Generate actual video clips from your approved prompts. 1-3 minutes per clip.</p>
            <div className="mt-3 flex items-center gap-3">
              <select
                value={renderTier}
                onChange={(e) => setRenderTier(e.target.value as "standard" | "pro")}
                disabled={renderRunning}
                className="rounded border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="pro">1080×1920 — Veo 3.1 (recommended: TikTok / Facebook Reels)</option>
                <option value="standard">720×1280 — Veo 3.1 Fast (faster, cheaper drafts)</option>
              </select>
              <button
                disabled={renderRunning}
                onClick={onStartRender}
                className="min-h-11 rounded bg-[#0B1C3E] px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
              >
                {renderRunning ? "Rendering…" : "Render all segments"}
              </button>
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Rendered vertical 9:16 automatically — the format TikTok and Facebook Reels expect. The two options differ only in resolution.
            </p>

            {/* Render status list */}
            {renderJobs && (
              <div className="mt-4 space-y-2">
                <p className="text-xs font-medium text-gray-600">Render status</p>
                {(renderStatus || renderJobs).map((job: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded bg-gray-50 px-3 py-2 text-xs">
                    <span>Segment {job.segment_index + 1}</span>
                    <span className={`font-medium ${
                      job.status === "succeeded" ? "text-green-700" :
                      job.status === "failed" ? "text-red-700" :
                      job.status === "running" ? "text-blue-700" : "text-gray-500"
                    }`}>
                      {job.status === "succeeded" ? "✅ Done" :
                       job.status === "failed" ? `❌ Failed${job.error_message ? ": " + job.error_message : ""}` :
                       job.status === "running" ? "⏳ Generating…" : "⏳ Pending"}
                    </span>
                    {job.video_url && (
                      <a href={`${API_BASE}${job.video_url}`} target="_blank" rel="noopener noreferrer" className="text-[#0B1C3E] underline">View</a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Assemble → one postable video */}
          {(allSegmentsSucceeded || assembled) && (
            <div className="rounded border border-[#0B1C3E] p-4">
              <h3 className="text-sm font-semibold">Finish the ad</h3>
              <p className="mt-1 text-xs text-gray-500">
                Joins every segment into a single video, in order, and levels the audio so the
                volume doesn&apos;t jump between cuts. Output is MP4 / H.264 / AAC at 9:16 —
                ready to upload to TikTok and Facebook Reels.
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-3">
                <button
                  disabled={assembling}
                  onClick={onAssemble}
                  className="min-h-11 rounded bg-[#0B1C3E] px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
                >
                  {assembling ? "Joining clips…" : assembled ? "Rebuild final video" : "Assemble final video"}
                </button>
                {assembled && (
                  <button
                    disabled={downloading}
                    onClick={onDownload}
                    className="min-h-11 rounded border border-[#0B1C3E] px-4 py-2 text-sm font-medium text-[#0B1C3E] disabled:opacity-60"
                  >
                    {downloading ? "Preparing…" : "Download MP4"}
                  </button>
                )}
              </div>

              {assembleError && <p className="mt-2 text-xs text-red-600">{assembleError}</p>}

              {assembled && (
                <div className="mt-4 space-y-2">
                  <video
                    controls
                    playsInline
                    className="w-full max-w-xs rounded border border-gray-200 bg-black"
                    src={assembledPlaybackUrl(assembled.url)}
                  />
                  <p className="text-xs text-gray-500">
                    {assembled.filename} · {assembled.segment_count} segments ·{" "}
                    {assembled.duration}s · {assembled.width}×{assembled.height}
                    {assembled.has_audio ? " · with audio" : " · no audio track"}
                  </p>
                </div>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function ContinuityField({ label, value, onChange }: { label: string; value?: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-700">{label}</label>
      <input value={value || ""} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded border border-gray-300 px-2 py-1 text-xs focus:border-black focus:outline-none" />
    </div>
  );
}
