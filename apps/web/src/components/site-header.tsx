"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";

import { useLang } from "@/components/language-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const GITHUB_URL = "https://github.com/MohamedIbraheem100/mizan-hr";

export function Logo({ className }: { className?: string }) {
  /* A balance beam: pivot, beam, two pans. Pure SVG, scales with text. */
  return (
    <svg viewBox="0 0 40 40" aria-hidden className={cn("size-7", className)} fill="none">
      <path d="M20 6v26" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M6 12h28" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M6 12l-4 10h8l-4-10Zm28 0l-4 10h8l-4-10Z" fill="currentColor" opacity=".9" />
      <path d="M13 34h14" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

/* usePathname() is runtime-only data; under Cache Components it must sit inside a
   Suspense boundary or it blocks prerendering of every route that shows the header. */
export function SiteHeader() {
  return (
    <Suspense fallback={<HeaderShell onDark={false} />}>
      <HeaderWithPath />
    </Suspense>
  );
}

function HeaderWithPath() {
  const pathname = usePathname();
  return <HeaderShell onDark={pathname === "/"} />;
}

function HeaderShell({ onDark }: { onDark: boolean }) {
  const { t, lang, setLang } = useLang();
  return (
    <header
      className={cn(
        "sticky top-0 z-40 border-b backdrop-blur-md",
        onDark ? "border-white/10 bg-ink/70 text-paper" : "border-border bg-background/80",
      )}
    >
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-5 sm:px-8">
        <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
          <Logo className={onDark ? "text-brass" : "text-ink"} />
          <span className="text-lg">{t.brand}</span>
          <span
            className={cn(
              "hidden text-sm font-normal sm:inline",
              onDark ? "text-paper/55" : "text-muted-foreground",
            )}
          >
            {t.tagline}
          </span>
        </Link>
        <nav className="flex items-center gap-1.5 sm:gap-3">
          <Link
            href="/#how"
            className={cn(
              "hidden rounded-md px-3 py-2 text-sm hover:underline sm:inline",
              onDark ? "text-paper/80" : "text-muted-foreground",
            )}
          >
            {t.nav.how}
          </Link>
          <Link
            href="/demo"
            className={cn(
              "hidden rounded-md px-3 py-2 text-sm hover:underline sm:inline",
              onDark ? "text-paper/80" : "text-muted-foreground",
            )}
          >
            {t.nav.demo}
          </Link>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className={cn(
              "hidden rounded-md px-3 py-2 text-sm hover:underline md:inline",
              onDark ? "text-paper/80" : "text-muted-foreground",
            )}
          >
            {t.nav.github}
          </a>
          <Button
            variant={onDark ? "outline" : "ghost"}
            size="sm"
            onClick={() => setLang(lang === "ar" ? "en" : "ar")}
            className={cn(onDark && "border-white/20 bg-transparent text-paper hover:bg-white/10")}
            aria-label={t.lang.switch}
          >
            {t.lang.switch}
          </Button>
          <Button
            size="sm"
            nativeButton={false}
            render={<Link href="/screen" />}
            className={cn(onDark && "bg-brass text-ink hover:bg-brass-strong")}
          >
            {t.nav.screen}
          </Button>
        </nav>
      </div>
    </header>
  );
}
