import type { Metadata } from "next";
import { Suspense } from "react";

import { ResultsPage } from "@/components/screen/results-page";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Results" };

/* Under Cache Components the dynamic `id` is runtime data: it is read inside a
   Suspense boundary so the shell prerenders and the results stream in. */
export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense
      fallback={
        <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8 sm:px-8 sm:py-12">
          <Skeleton className="h-8 w-64" />
        </main>
      }
    >
      <ResultsRoute params={params} />
    </Suspense>
  );
}

async function ResultsRoute({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ResultsPage id={id} />;
}
