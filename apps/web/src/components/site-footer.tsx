"use client";

import Link from "next/link";

import { useLang } from "@/components/language-provider";
import { Logo } from "@/components/site-header";

export function SiteFooter() {
  const { t } = useLang();
  return (
    <footer className="border-t bg-paper-2">
      <div className="mx-auto grid w-full max-w-7xl gap-8 px-5 py-12 sm:px-8 md:grid-cols-[1fr_2fr]">
        <div className="flex items-start gap-3">
          <Logo className="mt-0.5 text-ink" />
          <div>
            <div className="font-semibold">{t.brand}</div>
            <div className="text-sm text-muted-foreground">{t.tagline}</div>
          </div>
        </div>
        <div className="grid gap-3 text-sm text-muted-foreground md:grid-cols-3">
          <p>{t.footer.decision}</p>
          <p>
            {t.footer.privacy}{" "}
            <Link href="/privacy" className="underline">
              {t.nav.privacy}
            </Link>
          </p>
          <p>{t.footer.demo}</p>
        </div>
      </div>
    </footer>
  );
}
