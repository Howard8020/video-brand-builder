"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const APP_NAV = [
  { href: "/dashboard", label: "Projects" },
  { href: "/billing", label: "Billing" },
  { href: "/profile", label: "My Brand" },
];

const MARKETING_ROUTES = ["/", "/privacy", "/terms", "/how-to-use"];

export function AppNav() {
  const pathname = usePathname();
  const isMarketing = MARKETING_ROUTES.includes(pathname || "/");

  return (
    <nav className="border-b border-gray-100 bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex min-h-[6.5rem] sm:min-h-[7.5rem] items-center justify-between gap-4 py-3 sm:py-4">
          <div className="flex items-center gap-6 flex-shrink-0">
            <Link href="/" className="flex items-center flex-shrink-0">
              <Image
                src="/logo.png"
                alt="Video Brand Builders"
                width={1022}
                height={258}
                priority
                className="h-16 w-auto sm:h-20"
              />
            </Link>
            {!isMarketing && (
              <div className="hidden md:flex items-center gap-4 flex-shrink-0">
                {APP_NAV.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`text-sm font-medium whitespace-nowrap transition-colors ${
                      pathname?.startsWith(item.href) ? "text-[#0B1C3E]" : "text-gray-500 hover:text-[#0B1C3E]"
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            )}
          </div>
          {isMarketing && (
            <div className="flex items-center gap-4">
              <Link href="/how-to-use" className="text-sm font-medium text-gray-500 hover:text-[#0B1C3E]">
                How to Use
              </Link>
              <Link
                href="/dashboard"
                className="min-h-11 flex items-center rounded bg-[#0B1C3E] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
              >
                Sign in
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
