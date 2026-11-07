"use client";

import { useLang } from "@/components/language-provider";

const GITHUB_URL = "https://github.com/MohamedIbraheem100/mizan-hr";

export function PrivacyPage() {
  const { t } = useLang();
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-5 py-12 sm:px-8 sm:py-16">
      <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{t.privacy.title}</h1>
      <p className="mt-4 text-lg leading-relaxed text-muted-foreground">{t.privacy.intro}</p>
      <dl className="mt-10 divide-y rounded-xl border bg-card">
        {t.privacy.sections.map((s, i) => (
          <div key={s.t} className="grid gap-2 p-5 sm:grid-cols-[2rem_1fr] sm:p-6">
            <dt className="num text-xs font-medium text-brass-strong">0{i + 1}</dt>
            <div>
              <dt className="font-semibold">{s.t}</dt>
              <dd className="mt-1.5 leading-relaxed text-muted-foreground">{s.d}</dd>
            </div>
          </div>
        ))}
      </dl>
      <p className="mt-8 text-sm text-muted-foreground">
        {t.privacy.contact}{" "}
        <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="underline">
          GitHub
        </a>
      </p>
    </main>
  );
}
