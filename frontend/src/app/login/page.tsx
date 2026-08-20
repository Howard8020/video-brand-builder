"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login as apiLogin, register as apiRegister } from "@/lib/api";
import { track } from "@vercel/analytics";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await apiRegister(email, password);
        track("signup", { source_asset: "vbb" });
      }
      const data = await apiLogin(email, password);
      localStorage.setItem("vbb_token", data.access_token);
      router.push("/dashboard");
    } catch (e: any) {
      setError(e?.message || (mode === "login" ? "Login failed. Check email/password." : "Registration failed."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="text-2xl font-bold mb-2">
        {mode === "login" ? "Sign in" : "Create your account"}
      </h1>
      <p className="mb-6 text-sm text-gray-500">
        {mode === "login"
          ? "Sign in to Video Brand Builders"
          : "Start your first script in minutes"}
      </p>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-black focus:outline-none"
            required
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={busy} className="min-h-11 w-full rounded bg-black px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-60">
          {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
      <div className="mt-4 text-center text-sm text-gray-500">
        {mode === "login" ? (
          <>
            Don&apos;t have an account?{" "}
            <button onClick={() => { setMode("register"); setError(""); }} className="font-medium text-[#0B1C3E] hover:underline cursor-pointer bg-transparent border-none p-0">
              Create one
            </button>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <button onClick={() => { setMode("login"); setError(""); }} className="font-medium text-[#0B1C3E] hover:underline cursor-pointer bg-transparent border-none p-0">
              Sign in
            </button>
          </>
        )}
      </div>
      <p className="mt-6 text-center text-xs text-gray-400">
        Your data is encrypted in transit and never shared with third parties.
      </p>
    </div>
  );
}
