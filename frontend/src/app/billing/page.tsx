"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getCreditBalance, getPricing, createCheckout } from "@/lib/api";
import { track } from "@vercel/analytics";

function ConversionTracker() {
  const searchParams = useSearchParams();
  useEffect(() => {
    if (searchParams?.get("checkout") === "success") {
      track("conversion", { source_asset: "vbb" });
    }
  }, [searchParams]);
  return null;
}

interface PricingTier {
  label: string;
  credits: number;
  amount_cents: number;
  description: string;
  popular: boolean;
}

export default function BillingPage() {
  const [token, setToken] = useState<string | null>(null);
  const [balance, setBalance] = useState<{ balance_cents: number; lifetime_purchased_cents: number } | null>(null);
  const [tiers, setTiers] = useState<Record<string, PricingTier> | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const t = localStorage.getItem("vbb_token");
    if (!t) return;
    setToken(t);
    getCreditBalance(t).then(setBalance).catch(() => {});
    getPricing(t).then((d) => setTiers(d.tiers)).catch(() => {});
  }, []);

  async function handleBuy(tier: PricingTier) {
    if (!token) return;
    setBusy(true);
    try {
      const result = await createCheckout(token, tier.amount_cents);
      window.location.href = result.checkout_url;
    } catch (e) {
      alert(e instanceof Error ? e.message : "Checkout failed");
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-sm px-4 py-16 text-center">
        <h1 className="text-2xl font-bold">Sign in to manage billing</h1>
        <a href="/login" className="mt-4 inline-block rounded bg-[#0B1C3E] px-4 py-2 text-sm font-medium text-white">Go to sign in</a>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Suspense fallback={null}>
        <ConversionTracker />
      </Suspense>
      <h1 className="text-2xl font-bold">Billing &amp; Credits</h1>

      {balance !== null && (
        <div className="mt-6 rounded-lg border border-gray-200 bg-white p-6">
          <p className="text-sm text-gray-600">Your balance</p>
          <p className="text-3xl font-bold text-[#0B1C3E]">${(balance.balance_cents / 100).toFixed(2)}</p>
          <p className="mt-1 text-xs text-gray-400">
            Lifetime purchased: ${(balance.lifetime_purchased_cents / 100).toFixed(2)}
          </p>
          <p className="mt-2 text-xs text-gray-500">
            A Standard render costs $9.99. A Pro render costs $29.99.
          </p>
        </div>
      )}

      <h2 className="mt-10 text-lg font-semibold">Buy credits</h2>
      <p className="mt-1 text-sm text-gray-500">
        Credits are used for video rendering. No subscription required — buy only what you need.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {tiers &&
          Object.entries(tiers).map(([key, tier]) => (
            <div
              key={key}
              className={`rounded-lg border p-6 ${
                tier.popular ? "border-[#0B1C3E] ring-1 ring-[#0B1C3E]" : "border-gray-200"
              }`}
            >
              {tier.popular && (
                <span className="inline-block rounded bg-[#0B1C3E] px-2 py-0.5 text-xs font-medium text-white mb-3">
                  Most popular
                </span>
              )}
              <h3 className="text-lg font-bold text-gray-900">{tier.label}</h3>
              <p className="mt-1 text-2xl font-bold text-[#0B1C3E]">${(tier.amount_cents / 100).toFixed(0)}</p>
              <p className="mt-1 text-sm text-gray-500">{tier.description}</p>
              <button
                onClick={() => handleBuy(tier)}
                disabled={busy}
                className="mt-4 min-h-11 w-full rounded bg-[#0B1C3E] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
              >
                {busy ? "Opening checkout…" : `Buy $${(tier.amount_cents / 100).toFixed(0)}`}
              </button>
            </div>
          ))}
      </div>

      <p className="mt-6 text-xs text-gray-400">
        Credits never expire. Unused credits are refundable on request. Prices do not include applicable taxes.
      </p>
    </div>
  );
}
