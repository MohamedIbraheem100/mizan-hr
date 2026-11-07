"use client";

import { AlertTriangle, Check, Link2 } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { useLang } from "@/components/language-provider";
import { ScoreRing } from "@/components/score-ring";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { CvLine, Judgment, Rubric, ScreeningResult, Verdict } from "@/lib/api";
import { download, toCsv } from "@/lib/export";
import { cn } from "@/lib/utils";

export type ResultItem = { result: ScreeningResult; lines?: CvLine[]; fileName?: string };

export function ResultsView({
  screeningId,
  rubric,
  blind,
  expiresAt,
  items,
  onNew,
}: {
  screeningId: string;
  rubric: Rubric;
  blind: boolean;
  expiresAt?: string;
  items: ResultItem[]; // already ranked
  onNew?: () => void;
}) {
  const { t, lang } = useLang();
  const [selected, setSelected] = useState(0);
  const detailRef = useRef<HTMLDivElement>(null);
  const current = items[selected];

  const share = async () => {
    const url = `${window.location.origin}/results/${screeningId}`;
    try {
      await navigator.clipboard.writeText(url);
      toast.success(t.wizard.results.copied);
    } catch {
      toast(url);
    }
  };
  const exportJson = () =>
    download(
      `mizan-${screeningId.slice(0, 8)}.json`,
      JSON.stringify({ screening_id: screeningId, rubric, blind, results: items.map((i) => i.result) }, null, 2),
      "application/json",
    );
  const exportCsv = () =>
    download(
      `mizan-${screeningId.slice(0, 8)}.csv`,
      toCsv(rubric, items.map((i, idx) => ({ rank: idx + 1, result: i.result }))),
      "text/csv;charset=utf-8",
    );

  if (items.length === 0) {
    return <p className="text-muted-foreground">{t.wizard.results.empty}</p>;
  }

  return (
    <section className="animate-rise">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">{t.wizard.results.title}</h2>
          <p className="mt-1 text-muted-foreground">{t.wizard.results.hint}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            {rubric.job_title} · {rubric.criteria.length} {t.wizard.results.criteria} ·{" "}
            {blind ? t.wizard.results.blindOn : t.wizard.results.blindOff}
            {expiresAt && (
              <>
                {" "}· {t.wizard.results.expires}{" "}
                {new Date(expiresAt).toLocaleString(lang === "ar" ? "ar-EG" : "en-GB", {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={share}>
            <Link2 data-icon="inline-start" />
            {t.wizard.results.share}
          </Button>
          <Button variant="outline" size="sm" onClick={exportCsv}>
            {t.wizard.results.export} {t.wizard.results.csv}
          </Button>
          <Button variant="outline" size="sm" onClick={exportJson}>
            {t.wizard.results.export} {t.wizard.results.json}
          </Button>
          {onNew && (
            <Button size="sm" onClick={onNew}>
              {t.wizard.results.newScreening}
            </Button>
          )}
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(280px,1fr)_minmax(0,1.7fr)]">
        {/* ---------- Ranking ---------- */}
        <ol className="space-y-2">
          {items.map((item, i) => {
            const r = item.result;
            const active = i === selected;
            return (
              <motion.li
                key={r.candidate_ref + i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.45, ease: [0.2, 0.8, 0.2, 1] }}
              >
                <button
                  type="button"
                  onClick={() => {
                    setSelected(i);
                    if (window.innerWidth < 1024) detailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                  }}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-xl border bg-card p-3 text-start transition-colors",
                    active ? "border-ink shadow-sm" : "hover:border-ink/40",
                  )}
                >
                  <span className="num w-5 text-sm text-muted-foreground">{i + 1}</span>
                  <ScoreRing score={r.score} flagged={!r.must_haves_met} size={48} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">{r.candidate_ref}</div>
                    <div className="mt-0.5 flex items-center gap-1.5 text-xs">
                      {r.must_haves_met ? (
                        <span className="inline-flex items-center gap-1 text-met">
                          <Check className="size-3" /> {t.wizard.results.mustHaves} {t.wizard.results.met}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-partial">
                          <AlertTriangle className="size-3" /> {r.missing_must_haves.length}{" "}
                          {t.wizard.results.flagged}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              </motion.li>
            );
          })}
        </ol>

        {/* ---------- Detail ---------- */}
        <div ref={detailRef} className="scroll-mt-20">
          <AnimatePresence mode="wait">
            {current && (
              <motion.div
                key={current.result.candidate_ref + selected}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
              >
                <CandidateDetail item={current} rubric={rubric} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */

function CandidateDetail({ item, rubric }: { item: ResultItem; rubric: Rubric }) {
  const { t } = useLang();
  const r = item.result;
  const [activeLine, setActiveLine] = useState<string | null>(null);
  const citedIds = useMemo(
    () => new Set(r.judgments.flatMap((j) => j.evidence.map((e) => e.line_id))),
    [r.judgments],
  );

  useEffect(() => {
    if (!activeLine) return;
    const el = document.getElementById(`cvline-${activeLine}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
    const id = setTimeout(() => setActiveLine(null), 1800);
    return () => clearTimeout(id);
  }, [activeLine]);

  return (
    <div className="rounded-xl border bg-card">
      <header className="grid gap-4 border-b p-5 sm:grid-cols-[auto_1fr] xl:grid-cols-[auto_1fr_auto]">
        <ScoreRing score={r.score} flagged={!r.must_haves_met} size={72} />
        <div className="min-w-0">
          <h3 className="text-xl font-semibold">{r.candidate_ref}</h3>
          {item.fileName && (
            <p className="truncate text-xs text-muted-foreground" dir="auto">
              {t.wizard.results.file}: {item.fileName}
            </p>
          )}
          <p className="mt-2 text-sm leading-relaxed" dir="auto">
            {r.summary}
          </p>
          {!r.must_haves_met && (
            <p className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-partial/15 px-2 py-1 text-xs text-ink">
              <AlertTriangle className="size-3.5 text-partial" />
              {t.wizard.results.missing}: {r.missing_must_haves.join(" · ")}
            </p>
          )}
        </div>
        <dl className="num grid grid-cols-3 gap-3 self-start text-center text-xs sm:col-span-2 xl:col-span-1">
          <Stat n={r.verify.quotes_verified} label={t.wizard.results.verified} />
          <Stat n={r.verify.quotes_dropped} label={t.wizard.results.dropped} warn={r.verify.quotes_dropped > 0} />
          <Stat n={r.verify.quotes_checked} label={t.wizard.results.checked} />
        </dl>
      </header>

      <Tabs defaultValue="evidence" className="p-5">
        <TabsList>
          <TabsTrigger value="evidence">{t.wizard.results.evidence}</TabsTrigger>
          {item.lines && <TabsTrigger value="cv">{t.wizard.results.cv}</TabsTrigger>}
          <TabsTrigger value="summary">{t.wizard.results.summary}</TabsTrigger>
        </TabsList>

        <TabsContent value="evidence" className="mt-4 space-y-3">
          {rubric.criteria.map((c) => {
            const j = r.judgments.find((x) => x.criterion_id === c.id);
            if (!j) return null;
            return <JudgmentCard key={c.id} j={j} onJump={item.lines ? setActiveLine : undefined} />;
          })}
        </TabsContent>

        {item.lines && (
          <TabsContent value="cv" className="mt-4">
            <p className="mb-3 text-xs text-muted-foreground">{t.wizard.results.linesHint}</p>
            <ol className="max-h-[520px] overflow-auto rounded-lg border bg-paper p-3 font-mono text-[13px] leading-relaxed">
              {item.lines.map((ln) => {
                const cited = citedIds.has(ln.id);
                return (
                  <li
                    key={ln.id}
                    id={`cvline-${ln.id}`}
                    dir="auto"
                    className={cn(
                      "flex gap-3 rounded px-2 py-0.5 transition-colors",
                      cited && "bg-brass-soft",
                      activeLine === ln.id && "ring-2 ring-brass",
                    )}
                  >
                    <span className="num w-9 shrink-0 select-none text-muted-foreground">{ln.id}</span>
                    <span className="font-sans">{ln.text}</span>
                  </li>
                );
              })}
            </ol>
          </TabsContent>
        )}

        <TabsContent value="summary" className="mt-4 grid gap-5 md:grid-cols-2">
          <ListBlock title={t.wizard.results.strengths} items={r.strengths} tone="met" />
          <ListBlock title={t.wizard.results.gaps} items={r.gaps} tone="partial" />
          <ListBlock title={t.wizard.results.questions} items={r.interview_questions} tone="ink" className="md:col-span-2" />
          <div className="md:col-span-2 rounded-lg border bg-paper-2 p-4 text-sm">
            <div className="eyebrow mb-2">{t.wizard.results.profile}</div>
            <div className="flex flex-wrap gap-x-4 gap-y-1" dir="auto">
              {r.profile.headline && <span className="font-medium">{r.profile.headline}</span>}
              {r.profile.total_years_experience != null && (
                <span className="num text-muted-foreground">
                  {r.profile.total_years_experience} {t.wizard.results.years}
                </span>
              )}
            </div>
            {r.profile.skills.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {r.profile.skills.slice(0, 18).map((s) => (
                  <span key={s} className="rounded border bg-card px-1.5 py-0.5 text-xs" dir="auto">
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Stat({ n, label, warn }: { n: number; label: string; warn?: boolean }) {
  return (
    <div className="rounded-md border px-2 py-1.5">
      <div className={cn("text-lg font-semibold leading-none", warn && "text-not-met")}>{n}</div>
      <div className="mt-1 text-[10px] text-muted-foreground">{label}</div>
    </div>
  );
}

const VERDICT_STYLE: Record<Verdict, string> = {
  met: "bg-met/15 text-met",
  partial: "bg-partial/20 text-ink",
  not_met: "bg-not-met/15 text-not-met",
  no_evidence: "bg-muted text-muted-foreground",
};

function JudgmentCard({ j, onJump }: { j: Judgment; onJump?: (lineId: string) => void }) {
  const { t } = useLang();
  return (
    <article className="rounded-lg border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-medium" dir="auto">
            {j.criterion_name}
          </span>
          <span className="rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-muted-foreground ring-1 ring-border">
            {j.criterion_type === "must_have" ? t.wizard.rubric.mustHave : t.wizard.rubric.niceToHave} ·{" "}
            <span className="num">{Math.round(j.weight * 100)}%</span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          {j.verdict_before_verify && (
            <span className="text-[10px] text-muted-foreground">
              {t.wizard.results.downgraded} {t.wizard.verdict[j.verdict_before_verify]}
            </span>
          )}
          <span className={cn("rounded px-2 py-0.5 text-xs font-medium", VERDICT_STYLE[j.verdict])}>
            {t.wizard.verdict[j.verdict]}
          </span>
        </div>
      </div>
      {j.reasoning && (
        <p className="mt-2 text-sm text-muted-foreground" dir="auto">
          {j.reasoning}
        </p>
      )}
      {j.evidence.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {j.evidence.map((e, i) => (
            <li key={i}>
              <button
                type="button"
                onClick={() => onJump?.(e.line_id)}
                disabled={!onJump}
                className={cn(
                  "flex w-full items-start gap-2 rounded-md border-s-2 border-brass bg-brass-soft/50 px-3 py-2 text-start text-sm",
                  onJump && "hover:bg-brass-soft",
                )}
              >
                <span className="num shrink-0 text-xs text-muted-foreground">{e.line_id}</span>
                <span dir="auto">“{e.quote}”</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {j.dropped_evidence.length > 0 && (
        <ul className="mt-2 space-y-1.5">
          {j.dropped_evidence.map((e, i) => (
            <li
              key={i}
              className="flex items-start gap-2 rounded-md border border-dashed border-not-met/40 px-3 py-2 text-sm text-muted-foreground"
              title={t.wizard.results.droppedHint}
            >
              <span className="shrink-0 text-xs text-not-met">{t.wizard.results.dropped}</span>
              <span className="line-through" dir="auto">
                {e.quote}
              </span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function ListBlock({
  title,
  items,
  tone,
  className,
}: {
  title: string;
  items: string[];
  tone: "met" | "partial" | "ink";
  className?: string;
}) {
  if (!items.length) return null;
  return (
    <div className={className}>
      <div className="eyebrow mb-2">{title}</div>
      <ul className="space-y-1.5">
        {items.map((s, i) => (
          <li key={i} className="flex gap-2 text-sm" dir="auto">
            <span
              className={cn(
                "mt-2 size-1.5 shrink-0 rounded-full",
                tone === "met" && "bg-met",
                tone === "partial" && "bg-partial",
                tone === "ink" && "bg-ink",
              )}
            />
            <span>{s}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
