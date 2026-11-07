"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useLang } from "@/components/language-provider";
import { type ResultItem, ResultsView } from "@/components/screen/results-view";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { Rubric } from "@/lib/api";

type DemoBundle = {
  generated_at: string;
  jd_text: string;
  rubric: Rubric;
  blind: boolean;
  items: ResultItem[];
};

/* Served from /public: no API, no model, no database. Always loads. */
export function DemoPage() {
  const { t, lang } = useLang();
  const [bundle, setBundle] = useState<DemoBundle | null>(null);
  const [showJd, setShowJd] = useState(false);

  useEffect(() => {
    fetch("/demo/backend-engineer.json")
      .then((r) => r.json())
      .then(setBundle)
      .catch(() => setBundle(null));
  }, []);

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8 sm:px-8 sm:py-12">
      <div className="mb-8 rounded-xl border bg-paper-2 p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="eyebrow">{t.demo.title}</p>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{t.demo.body}</p>
            {bundle && (
              <p className="mt-2 text-xs text-muted-foreground">
                {t.demo.generated}:{" "}
                {new Date(bundle.generated_at).toLocaleString(lang === "ar" ? "ar-EG" : "en-GB", {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowJd((v) => !v)}>
              {t.demo.viewJd}
            </Button>
            <Button size="sm" nativeButton={false} render={<Link href="/screen" />}>
              {t.demo.open}
            </Button>
          </div>
        </div>
        {showJd && bundle && (
          <pre className="mt-4 whitespace-pre-wrap rounded-lg border bg-card p-4 font-sans text-sm leading-relaxed">
            {bundle.jd_text}
          </pre>
        )}
      </div>

      {bundle ? (
        <ResultsView
          screeningId="demo"
          rubric={bundle.rubric}
          blind={bundle.blind}
          items={bundle.items}
        />
      ) : (
        <div className="space-y-3" aria-busy>
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}
    </main>
  );
}
