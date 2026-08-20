export const metadata = {
  title: "Terms of Service | Video Brand Builders",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900">Terms of Service</h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: August 4, 2026</p>

      <div className="mt-8 space-y-6 text-sm leading-6 text-gray-700">
        <p>
          These Terms of Service (&ldquo;Terms&rdquo;) govern your use of Video Brand Builders
          (&ldquo;the Service&rdquo;), operated by Agentic Solutions at{" "}
          <strong>videobrandbuilders.ai</strong>. By creating an account or using the Service, you
          agree to these Terms.
        </p>

        <section>
          <h2 className="text-base font-semibold text-gray-900">The service</h2>
          <p className="mt-2">
            Video Brand Builders helps you draft video ad scripts, review and lock them, approve
            scene treatments, and generate prompt packages or video renders for use with
            third-party video tools. The Service provides tools and AI-assisted drafts; it does
            not guarantee publishing, distribution, or performance of any advertisement.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Accounts &amp; eligibility</h2>
          <p className="mt-2">
            You must be at least 18 years old and capable of entering into a binding agreement to
            use the Service. You are responsible for maintaining the confidentiality of your
            credentials and for all activity under your account. Notify us immediately if you
            suspect unauthorized access.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Credits &amp; billing</h2>
          <p className="mt-2">
            The Service operates on a prepaid credit model. Credits are purchased through Stripe
            and are non-transferable. Credits never expire. Unused credits are refundable on
            request, as described in our{" "}
            <a href="/refund" className="text-[#0B1C3E] underline">
              Refund Policy
            </a>
            . Prices do not include applicable taxes unless stated at checkout.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">AI-generated content</h2>
          <p className="mt-2">
            Scripts, scene descriptions, and video prompts are generated with AI assistance and
            require your review and approval before use. You are responsible for verifying all
            claims — pricing, guarantees, credentials, and offers — before publishing any ad.
            Generated content is provided as a draft and may contain errors.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Your content</h2>
          <p className="mt-2">
            You retain ownership of the briefs, scripts, and prompts you create. You grant us a
            limited license to process your content solely to provide the Service. You are
            responsible for ensuring you have the rights to any brand assets, logos, or claims
            you submit, and that your content does not infringe the rights of others.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Acceptable use</h2>
          <p className="mt-2">You agree not to:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>Use the Service to create deceptive, fraudulent, or illegal advertising.</li>
            <li>Attempt to access another user&apos;s account or data.</li>
            <li>Reverse engineer, scrape, or abuse the Service or its APIs.</li>
            <li>Use the Service in a way that violates applicable law.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Disclaimers &amp; limitation of liability</h2>
          <p className="mt-2">
            The Service is provided on an &ldquo;as-is&rdquo; and &ldquo;as-available&rdquo; basis
            without warranties of any kind, express or implied, including accuracy, uptime, or
            fitness for a particular purpose. To the maximum extent permitted by law, our total
            liability arising out of or related to the Service is limited to the amount you paid
            for credits in the 90 days preceding the claim. We are not liable for indirect,
            incidental, or consequential damages, including lost profits or ad performance.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Termination</h2>
          <p className="mt-2">
            You may stop using the Service and delete your account at any time. We may suspend or
            terminate access for violations of these Terms or activity that harms the Service or
            other users. Upon termination, your right to use the Service ends; unused credits are
            refundable per our Refund Policy unless termination results from a Terms violation.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Changes to these Terms</h2>
          <p className="mt-2">
            We may update these Terms from time to time. Material changes will be posted on this
            page with an updated &ldquo;Last updated&rdquo; date. Continued use of the Service
            after changes constitutes acceptance.
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold text-gray-900">Contact</h2>
          <p className="mt-2">
            Questions about these Terms? Email{" "}
            <a href="mailto:support@videobrandbuilders.ai" className="text-[#0B1C3E] underline">
              support@videobrandbuilders.ai
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
