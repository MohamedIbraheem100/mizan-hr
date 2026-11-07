"use client";

import { useCallback, useRef, useState } from "react";
import { toast } from "sonner";

import { useLang } from "@/components/language-provider";
import { JdStep } from "@/components/screen/jd-step";
import { ResultsView } from "@/components/screen/results-view";
import { RubricEditor } from "@/components/screen/rubric-editor";
import { Stepper } from "@/components/screen/stepper";
import { type Candidate, rankResults } from "@/components/screen/types";
import { MAX_FILES, UploadStep } from "@/components/screen/upload-step";
import { ApiError, type Rubric, createRubric, createScreening, screenCv } from "@/lib/api";

const CONCURRENCY = 3;
const MAX_BYTES = 5 * 1024 * 1024;

export function Workspace() {
  const { t } = useLang();
  const [step, setStep] = useState(0);
  const [jd, setJd] = useState("");
  const [rubric, setRubric] = useState<Rubric | null>(null);
  const [blind, setBlind] = useState(true);
  const [screening, setScreening] = useState<{ id: string; expiresAt: string } | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [busy, setBusy] = useState(false);
  const [running, setRunning] = useState(false);
  const [loadingSamples, setLoadingSamples] = useState(false);
  const abort = useRef<AbortController | null>(null);

  const fail = (err: unknown) => {
    const msg = err instanceof ApiError ? err.message : t.wizard.errors.api;
    toast.error(msg);
  };

  /* ---------- step 1: JD -> rubric ---------- */
  const buildRubric = async () => {
    setBusy(true);
    try {
      setRubric(await createRubric(jd));
      setStep(1);
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };

  /* ---------- step 2: confirm rubric -> screening ---------- */
  const confirmRubric = async () => {
    if (!rubric) return;
    setBusy(true);
    try {
      const created = await createScreening(rubric, blind);
      setScreening({ id: created.screening_id, expiresAt: created.expires_at });
      setStep(2);
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };

  /* ---------- step 3: files ---------- */
  const addFiles = useCallback(
    (files: File[]) => {
      setCandidates((prev) => {
        const room = MAX_FILES - prev.length;
        if (room <= 0) {
          toast.error(t.wizard.upload.maxFiles);
          return prev;
        }
        const accepted: Candidate[] = [];
        for (const f of files.slice(0, room)) {
          if (!/\.(pdf|docx|txt)$/i.test(f.name)) {
            toast.error(`${f.name}: ${t.wizard.errors.type}`);
            continue;
          }
          if (f.size > MAX_BYTES) {
            toast.error(`${f.name}: ${t.wizard.errors.tooLarge}`);
            continue;
          }
          const n = prev.length + accepted.length + 1;
          accepted.push({
            id: crypto.randomUUID(),
            file: f,
            ref: blind ? `${t.wizard.results.candidate} ${String(n).padStart(2, "0")}` : f.name.replace(/\.[^.]+$/, ""),
            status: "queued",
            statuses: {},
          });
        }
        return [...prev, ...accepted];
      });
    },
    [blind, t],
  );

  const loadSamples = async () => {
    setLoadingSamples(true);
    try {
      const manifest: { file: string }[] = await (await fetch("/samples/manifest.json")).json();
      const files = await Promise.all(
        manifest.map(async (m) => {
          const blob = await (await fetch(`/samples/${m.file}`)).blob();
          return new File([blob], m.file, {
            type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          });
        }),
      );
      addFiles(files);
    } catch (e) {
      fail(e);
    } finally {
      setLoadingSamples(false);
    }
  };

  const loadScreenMe = async () => {
    setLoadingSamples(true);
    try {
      const res = await fetch("/screen-me/cv.pdf");
      if (!res.ok) throw new ApiError(res.status, t.wizard.errors.notFound);
      const blob = await res.blob();
      const file = new File([blob], "author-cv.pdf", { type: "application/pdf" });
      setCandidates((prev) => [
        ...prev,
        { id: crypto.randomUUID(), file, ref: t.screenMe.ref, status: "queued", statuses: {} },
      ]);
    } catch (e) {
      fail(e);
    } finally {
      setLoadingSamples(false);
    }
  };

  const patch = (id: string, fn: (c: Candidate) => Candidate) =>
    setCandidates((prev) => prev.map((c) => (c.id === id ? fn(c) : c)));

  const runOne = async (c: Candidate, signal: AbortSignal) => {
    if (!screening) return;
    patch(c.id, (x) => ({ ...x, status: "running", statuses: {} }));
    try {
      await screenCv(
        c.file,
        screening.id,
        c.ref,
        {
          onProgress: (e) => {
            patch(c.id, (x) => ({
              ...x,
              statuses: { ...x.statuses, [e.node]: e.status },
              // parse: original lines; redact (blind mode): the redacted lines replace them,
              // so the recruiter reviews the same text the model judged.
              lines:
                (e.node === "parse" || e.node === "redact") && Array.isArray(e.detail.lines)
                  ? e.detail.lines
                  : x.lines,
            }));
          },
          onResult: (r) => patch(c.id, (x) => ({ ...x, status: "done", result: r })),
          onError: (msg) => patch(c.id, (x) => ({ ...x, status: "error", error: msg })),
        },
        signal,
      );
      patch(c.id, (x) => (x.status === "running" ? { ...x, status: "error", error: t.wizard.errors.api } : x));
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.status === 429
            ? t.wizard.errors.rateLimited
            : e.status === 422 && /scanned|text layer/i.test(e.message)
              ? t.wizard.errors.scanned
              : e.message
          : t.wizard.errors.api;
      patch(c.id, (x) => ({ ...x, status: "error", error: msg }));
    }
  };

  const start = async () => {
    const queue = candidates.filter((c) => c.status === "queued");
    if (!queue.length) return;
    setRunning(true);
    abort.current = new AbortController();
    const signal = abort.current.signal;
    let next = 0;
    const worker = async () => {
      while (next < queue.length && !signal.aborted) {
        const c = queue[next++];
        await runOne(c, signal);
      }
    };
    await Promise.all(Array.from({ length: Math.min(CONCURRENCY, queue.length) }, worker));
    setRunning(false);
  };

  const reset = () => {
    abort.current?.abort();
    setStep(0);
    setJd("");
    setRubric(null);
    setScreening(null);
    setCandidates([]);
    setRunning(false);
  };

  const ranked = rankResults(candidates).map((c) => ({
    result: c.result!,
    lines: c.lines,
    fileName: c.file.name,
  }));

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8 sm:px-8 sm:py-12">
      <Stepper step={step} onStep={(i) => !running && setStep(i)} />
      <div className="mt-10">
        {step === 0 && <JdStep value={jd} onChange={setJd} onSubmit={buildRubric} busy={busy} />}
        {step === 1 && rubric && (
          <RubricEditor
            rubric={rubric}
            onChange={setRubric}
            blind={blind}
            onBlind={setBlind}
            onConfirm={confirmRubric}
            busy={busy}
          />
        )}
        {step === 2 && (
          <UploadStep
            candidates={candidates}
            onAdd={addFiles}
            onRemove={(id) => setCandidates((p) => p.filter((c) => c.id !== id))}
            onLoadSamples={loadSamples}
            onScreenMe={loadScreenMe}
            onStart={start}
            onViewResults={() => setStep(3)}
            running={running}
            loadingSamples={loadingSamples}
          />
        )}
        {step === 3 && rubric && screening && (
          <ResultsView
            screeningId={screening.id}
            rubric={rubric}
            blind={blind}
            expiresAt={screening.expiresAt}
            items={ranked}
            onNew={reset}
          />
        )}
      </div>
    </main>
  );
}
