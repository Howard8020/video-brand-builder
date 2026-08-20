import Link from "next/link";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-gray-100 bg-white">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <p className="text-xs text-gray-500">
            &copy; {year} Video Brand Builders. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <Link href="/privacy" className="text-xs text-gray-500 hover:text-[#0B1C3E]">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-xs text-gray-500 hover:text-[#0B1C3E]">
              Terms of Service
            </Link>
            <Link href="/refund" className="text-xs text-gray-500 hover:text-[#0B1C3E]">
              Refund Policy
            </Link>
          </div>
        </div>
        <p className="mt-4 text-center text-xs text-gray-400 sm:text-left">
          Your scripts and brand data are encrypted in transit and never shared with third parties.
        </p>
      </div>
    </footer>
  );
}
