export const metadata = {
  title: "Refund Policy | Video Brand Builders",
};

export default function RefundPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900">Refund Policy</h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: August 4, 2026</p>

      <div className="mt-8 space-y-6 text-sm leading-6 text-gray-700">
        <p>
          Video Brand Builders operates on a prepaid credit model. This policy explains when
          credits are refundable and how to request a refund.
        </p>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Quick summary</h2>
          <p className="mt-2">
            Unused credits never expire and are <strong>refundable on request</strong>. Credits
            that have already been used to generate scripts, prompts, or video renders are
            non-refundable, because the work has been performed.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">What is refundable</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>
              <strong>Unused credit balance</strong> — the full remaining balance is refundable at
              any time.
            </li>
            <li>
              <strong>Duplicate or erroneous charges</strong> — we will refund any charge you did
              not authorize.
            </li>
            <li>
              <strong>Service failure</strong> — if a generation fails and credits are deducted
              without delivering output, we will restore or refund those credits.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">What is not refundable</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>Credits consumed by completed script, prompt, or video generations.</li>
            <li>Results that did not meet creative expectations (AI output is inherently variable).</li>
            <li>Credits purchased with promotional or gifted balances, unless required by law.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">How to request a refund</h2>
          <ol className="mt-2 list-decimal space-y-1 pl-5">
            <li>
              Email{" "}
              <a href="mailto:support@videobrandbuilders.ai" className="text-[#0B1C3E] underline">
                support@videobrandbuilders.ai
              </a>{" "}
              with the subject &ldquo;Refund Request.&rdquo;
            </li>
            <li>Include the email address on your account and your current credit balance.</li>
            <li>
              We&rsquo;ll confirm your unused balance and process the refund to the original
              payment method.
            </li>
          </ol>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Timeline</h2>
          <p className="mt-2">
            Refund requests are processed within <strong>5–10 business days</strong> of approval.
            After we submit the refund, your bank or card issuer may take additional time to show
            it on your statement.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Questions?</h2>
          <p className="mt-2">
            If you have questions about your balance or this policy, contact{" "}
            <a href="mailto:support@videobrandbuilders.ai" className="text-[#0B1C3E] underline">
              support@videobrandbuilders.ai
            </a>{" "}
            before purchasing — we&rsquo;re happy to help.
          </p>
        </section>
      </div>
    </div>
  );
}
