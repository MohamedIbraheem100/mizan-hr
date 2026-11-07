import type { Metadata, Viewport } from "next";
import { Geist_Mono, IBM_Plex_Sans_Arabic, Manrope } from "next/font/google";

import "./globals.css";

import { LanguageProvider } from "@/components/language-provider";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Toaster } from "@/components/ui/sonner";

const latin = Manrope({
  variable: "--font-latin",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const arabic = IBM_Plex_Sans_Arabic({
  variable: "--font-arabic",
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
});

const mono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Mizan - Evidence-based CV screening",
    template: "%s - Mizan",
  },
  description:
    "Mizan turns a job description into a weighted rubric, screens CVs against it, and shows the exact CV line behind every score. Decision support for recruiters. Arabic and English.",
  metadataBase: new URL("https://mizan-hr.vercel.app"),
  openGraph: {
    title: "Mizan - Evidence-based CV screening",
    description: "Every score, backed by a line from the CV.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0f1422",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${latin.variable} ${arabic.variable} ${mono.variable} h-full`}
    >
      <body className="flex min-h-full flex-col">
        <LanguageProvider>
          <SiteHeader />
          <div className="flex flex-1 flex-col">{children}</div>
          <SiteFooter />
          <Toaster position="bottom-center" />
        </LanguageProvider>
      </body>
    </html>
  );
}
