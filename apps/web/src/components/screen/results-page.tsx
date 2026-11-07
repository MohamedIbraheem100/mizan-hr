"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useLang } from "@/components/language-provider";
import { ResultsView } from "@/components/screen/results-view";
import { rankResults } from "@/components/screen/types";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, type ScreeningView, getScreening } from "@/lib/api";

/* Shareable results: read from the API (24 h retention). No CV text here, so the
   evidence tab shows quotes without the line view. */
export function ResultsPage({ id }: { id: string }) {
  const { t } = useLang();
  const [view, setView] = useState<ScreeningView | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getScreening(id)
      .then((v) => !cancelled && setView(v))
      .catch((e: unknown) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 410) setError(t.wizard.errors.expired);
        else if (e instanceof ApiError && e.status === 404) setError(t.wizard.errors.notFound);
        else setError(t.wizard.errors.api);
      });
    return () => {
      cancelled = true;
    };
  }, [id, t]);

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8 sm:px-8 sm:py-12">
      {error ? (
        <div className="rounded-xl border bg-card p-8 text-center">
          <p className="text-lg font-medium">{error}</p>
          <Button className="mt-5" nativeButton={false} render={<Link href="/screen" />}>
            {t.wizard.results.newScreening}
          </Button>
        </div>
      ) : !view ? (
        <div className="space-y-4" aria-busy>
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
          <div className="grid gap-6 lg:grid-cols-[1fr_1.7fr]">
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
            <Skeleton className="h-96 w-full" />
          </div>
          <p className="text-sm text-muted-foreground">{t.wizard.results.loading}</p>
        </div>
      ) : (
        <ResultsView
          screeningId={view.screening_id}
          rubric={view.rubric}
          blind={view.blind}
          expiresAt={view.expires_at}
          items={rankResults(view.results.map((r) => ({ result: r }))).map((x) => ({ result: x.result! }))}
        />
      )}
    </main>
  );
}
