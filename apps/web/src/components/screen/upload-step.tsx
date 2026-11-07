"use client";

import { FileText, Upload, X } from "lucide-react";
import { useRef, useState } from "react";

import { useLang } from "@/components/language-provider";
import { PipelineRail } from "@/components/pipeline-rail";
import { Button } from "@/components/ui/button";
import type { Candidate } from "@/components/screen/types";
import { cn } from "@/lib/utils";

const ACCEPT = ".pdf,.docx,.txt";
export const MAX_FILES = 10;

export function UploadStep({
  candidates,
  onAdd,
  onRemove,
  onLoadSamples,
  onStart,
  onViewResults,
  running,
  loadingSamples,
}: {
  candidates: Candidate[];
  onAdd: (files: File[]) => void;
  onRemove: (id: string) => void;
  onLoadSamples: () => void;
  onStart: () => void;
  onViewResults: () => void;
  running: boolean;
  loadingSamples: boolean;
}) {
  const { t } = useLang();
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const doneCount = candidates.filter((c) => c.status === "done").length;
  const allDone = candidates.length > 0 && candidates.every((c) => c.status === "done" || c.status === "error");
  const canStart = candidates.length > 0 && !running && candidates.some((c) => c.status === "queued");

  return (
    <section className="animate-rise">
      <h2 className="text-2xl font-semibold tracking-tight">{t.wizard.upload.title}</h2>
      <p className="mt-1 text-muted-foreground">{t.wizard.upload.hint}</p>

      {!running && !allDone && (
        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setOver(true);
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setOver(false);
            onAdd(Array.from(e.dataTransfer.files));
          }}
          className={cn(
            "mt-6 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed bg-card px-6 py-12 text-center transition-colors",
            over ? "border-brass bg-brass-soft/40" : "border-border hover:border-ink/40",
          )}
        >
          <Upload className="size-6 text-muted-foreground" />
          <p className="mt-3 font-medium">{t.wizard.upload.drop}</p>
          <p className="mt-1 text-xs text-muted-foreground">PDF · DOCX · TXT</p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            multiple
            className="hidden"
            onChange={(e) => {
              onAdd(Array.from(e.target.files ?? []));
              e.target.value = "";
            }}
          />
          <Button
            variant="outline"
            size="sm"
            className="mt-5"
            disabled={loadingSamples}
            onClick={(e) => {
              e.stopPropagation();
              onLoadSamples();
            }}
          >
            {t.wizard.upload.samples}
          </Button>
        </div>
      )}

      {candidates.length > 0 && (
        <ul className="mt-6 space-y-3">
          {candidates.map((c) => (
            <li key={c.id} className="rounded-xl border bg-card p-4">
              <div className="flex items-center gap-3">
                <FileText className="size-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium">{c.ref}</span>
                    <StatusPill status={c.status} />
                  </div>
                  <div className="truncate text-xs text-muted-foreground" dir="auto">
                    {c.file.name}
                  </div>
                </div>
                {c.status === "done" && c.result && (
                  <div className="num text-end">
                    <div className="text-xl font-semibold leading-none">{c.result.score}</div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                      {t.wizard.results.score}
                    </div>
                  </div>
                )}
                {c.status === "queued" && !running && (
                  <Button variant="ghost" size="icon-sm" onClick={() => onRemove(c.id)} aria-label={t.wizard.rubric.remove}>
                    <X />
                  </Button>
                )}
              </div>
              {(c.status === "running" || c.status === "done" || c.status === "error") && (
                <PipelineRail compact statuses={c.statuses} className="mt-3" />
              )}
              {c.status === "error" && c.error && (
                <p className="mt-2 text-xs text-not-met">{c.error}</p>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <span className="text-sm text-muted-foreground">
          {candidates.length} / {MAX_FILES} {t.wizard.upload.files}
          {running || allDone ? ` · ${doneCount} ${t.wizard.upload.done}` : ""}
        </span>
        <div className="flex gap-2">
          {canStart && (
            <Button size="lg" onClick={onStart} className="h-11 px-6">
              {t.wizard.upload.start}
            </Button>
          )}
          {running && (
            <Button size="lg" disabled className="h-11 px-6">
              {t.wizard.upload.screening}
            </Button>
          )}
          {allDone && !running && doneCount > 0 && (
            <Button size="lg" onClick={onViewResults} className="h-11 bg-brass px-6 text-ink hover:bg-brass-strong">
              {t.wizard.upload.viewResults}
            </Button>
          )}
        </div>
      </div>
    </section>
  );
}

function StatusPill({ status }: { status: Candidate["status"] }) {
  const { t } = useLang();
  const label = {
    queued: t.wizard.upload.queued,
    running: t.wizard.upload.screening,
    done: t.wizard.upload.done,
    error: t.wizard.upload.error,
  }[status];
  return (
    <span
      className={cn(
        "rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider",
        status === "queued" && "bg-muted text-muted-foreground",
        status === "running" && "bg-brass-soft text-ink",
        status === "done" && "bg-met/15 text-met",
        status === "error" && "bg-not-met/15 text-not-met",
      )}
    >
      {label}
    </span>
  );
}
