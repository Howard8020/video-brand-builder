export const metadata = {
  title: "Privacy Policy | Video Brand Builders",
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900">Privacy Policy</h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: August 4, 2026</p>

      <div className="mt-8 space-y-6 text-sm leading-6 text-gray-700">
        <p>
          Video Brand Builders (&ldquo;we,&rdquo; &ldquo;us,&rdquo; or &ldquo;our&rdquo;) respects your privacy. This policy
          explains what we collect, why we collect it, and how you can control your data when you
          use our service at <strong>videobrandbuilders.ai</strong>.
        </p>

        <section>
          <h2 className="text-base font-semibold text-gray-900">What we collect</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>
              <strong>Account information:</strong> your email address and a hashed password when
              you create an account.
            </li>
            <li>
              <strong>Brand &amp; project data:</strong> client profile notes, brand voice details,
              creative briefs, scripts, scene descriptions, and the video prompts you generate.
            </li>
            <li>
              <strong>Payment data:</strong> we use Stripe to process credit purchases. Card
              numbers are handled by Stripe and never stored on our servers. We store your credit
              balance and transaction history to operate billing.
            </li>
            <li>
              <strong>Usage data:</strong> pages visited and features used, IP address, browser
              type, and device information, used to operate and improve the service.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">How we use it</h2>
          <p className="mt-2">
            Solely to operate the service: authenticating you, storing your projects, processing
            billing, and sending your brief to AI providers to generate scripts, scene prompts,
            and (when you request it) video renders on your behalf. We do not sell or rent your
            personal data to anyone.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Third-party services</h2>
          <p className="mt-2">To deliver the service, we share necessary data with these providers:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>
              <strong>Stripe</strong> — payment processing. Handles card data under their own
              privacy policy.
            </li>
            <li>
              <strong>AI providers</strong> (e.g. OpenRouter, Google Veo) — script generation,
              scene prompts, and video rendering. We send only the content needed to fulfill your
              request; prompts are processed to generate your output.
            </li>
            <li>
              <strong>Vercel &amp; Railway</strong> — web hosting, backend API, and database
              infrastructure.
            </li>
          </ul>
          <p className="mt-2 text-xs text-gray-400">
            Each provider processes data under its own privacy policy and applicable data
            protection agreements.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Data retention</h2>
          <p className="mt-2">
            We retain your account and project data while your account is active. If you delete
            your account, we delete your projects and personal data from our systems, subject to
            legal obligations (such as tax records for billing history).
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Your rights</h2>
          <p className="mt-2">You may:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>Request a copy of the personal data we hold about you.</li>
            <li>Correct inaccurate data.</li>
            <li>Request deletion of your account and associated data at any time.</li>
            <li>Export or remove your projects.</li>
          </ul>
          <p className="mt-2">
            To exercise any of these rights, contact us at{" "}
            <a href="mailto:support@videobrandbuilders.ai" className="text-[#0B1C3E] underline">
              support@videobrandbuilders.ai
            </a>
            . We respond to verified requests within 30 days.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Cookies</h2>
          <p className="mt-2">
            We use only essential cookies and local storage required for the service to function
            (session and authentication). We do not use advertising cookies or third-party
            behavioral tracking.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Changes to this policy</h2>
          <p className="mt-2">
            We may update this policy from time to time. Material changes will be posted on this
            page with an updated &ldquo;Last updated&rdquo; date. Continued use of the service
            after changes constitutes acceptance of the updated policy.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Contact</h2>
          <p className="mt-2">
            Email:{" "}
            <a href="mailto:support@videobrandbuilders.ai" className="text-[#0B1C3E] underline">
              support@videobrandbuilders.ai
            </a>
          </p>
        </section>
      </div>
    </div>
  );
}
