import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Analytics } from "@vercel/analytics/react";
import { AppNav } from "@/components/AppNav";
import { Footer } from "@/components/Footer";
import { Albert } from "@/components/Albert";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "Video Brand Builders | Video Ads That Actually Sound Like You",
  description:
    "Tell us about your business. We'll build a script that fits your voice. Lock it, approve the scenes, and get cohesive video prompts that actually go together.",
  openGraph: {
    title: "Video Brand Builders",
    description:
      "Turn a brand brief into an approved script and ready-to-use video prompts in minutes.",
    url: SITE_URL,
    siteName: "Video Brand Builders",
    images: [{ url: "/logo.png", width: 1022, height: 258, alt: "Video Brand Builders" }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Video Brand Builders",
    description:
      "Turn a brand brief into an approved script and ready-to-use video prompts in minutes.",
    images: ["/logo.png"],
  },
  icons: {
    icon: [
      { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: "/favicon-180.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased bg-white text-gray-900 flex min-h-screen flex-col`}>
        <AppNav />
        <main className="flex-1">{children}</main>
        <Footer />
        <Albert />
        <Analytics />
      </body>
    </html>
  );
}
