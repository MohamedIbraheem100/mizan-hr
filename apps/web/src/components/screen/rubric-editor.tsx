"use client";

import { Plus, Trash2 } from "lucide-react";

import { useLang } from "@/components/language-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import type { Criterion, Rubric } from "@/lib/api";
import { cn } from "@/lib/utils";

/* The recruiter edits the proposal; code normalizes weights for display and the
   API normalizes them again on save. Weights here are 1..100 sliders. */

export function RubricEditor({
  rubric,
  onChange,
  blind,
  onBlind,
  onConfirm,
  busy,
}: {
  rubric: Rubric;
  onChange: (r: Rubric) => void;
  blind: boolean;
  onBlind: (b: boolean) => void;
  onConfirm: () => void;
  busy: boolean;
}) {
  const { t } = useLang();
  const total = rubric.criteria.reduce((s, c) => s + c.weight, 0) || 1;

  const update = (i: number, patch: Partial<Criterion>) => {
    const criteria = rubric.criteria.map((c, j) => (j === i ? { ...c, ...patch } : c));
    onChange({ ...rubric, criteria });
  };
  const remove = (i: number) =>
    onChange({ ...rubric, criteria: rubric.criteria.filter((_, j) => j !== i) });
  const add = () =>
    onChange({
      ...rubric,
      criteria: [
        ...rubric.criteria,
        {
          id: `c${rubric.criteria.length + 1}`,
          name: t.wizard.rubric.newCriterion,
          type: "nice_to_have",
          weight: 0.1,
          min_years: null,
          description: "",
        },
      ],
    });

  const valid =
    rubric.criteria.length > 0 &&
    rubric.criteria.every((c) => c.name.trim().length >= 2) &&
    rubric.criteria.some((c) => c.type === "must_have");

  return (
    <section className="animate-rise">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">{t.wizard.rubric.title}</h2>
          <p className="mt-1 max-w-2xl text-muted-foreground">{t.wizard.rubric.hint}</p>
        </div>
        <div className="text-end">
          <Label className="text-xs text-muted-foreground">{t.wizard.rubric.jobTitle}</Label>
          <div className="mt-1 font-medium" dir="auto">{rubric.job_title}</div>
          <div className="text-xs text-muted-foreground">{t.wizard.rubric.language}: {rubric.language.toUpperCase()}</div>
        </div>
      </div>

      <ul className="mt-6 space-y-3">
        {rubric.criteria.map((c, i) => {
          const pct = Math.round((c.weight / total) * 100);
          return (
            <li
              key={c.id + i}
              className="grid gap-4 rounded-xl border bg-card p-4 sm:grid-cols-[1fr_auto] sm:p-5"
            >
              <div className="grid gap-4 md:grid-cols-[1.4fr_1fr]">
                <div>
                  <Label className="text-xs text-muted-foreground">{t.wizard.rubric.name}</Label>
                  <Input
                    value={c.name}
                    onChange={(e) => update(i, { name: e.target.value })}
                    dir="auto"
                    className="mt-1"
                  />
                  {c.description && (
                    <p className="mt-1.5 text-xs text-muted-foreground">{c.description}</p>
                  )}
                </div>
                <div className="grid grid-cols-[1fr_auto] gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">{t.wizard.rubric.type}</Label>
                    <div className="mt-1 inline-flex rounded-md border p-0.5">
                      {(["must_have", "nice_to_have"] as const).map((type) => (
                        <button
                          key={type}
                          type="button"
                          onClick={() => update(i, { type })}
                          className={cn(
                            "rounded px-3 py-1.5 text-xs font-medium transition-colors",
                            c.type === type
                              ? type === "must_have"
                                ? "bg-ink text-paper"
                                : "bg-brass-soft text-ink"
                              : "text-muted-foreground hover:text-foreground",
                          )}
                        >
                          {type === "must_have" ? t.wizard.rubric.mustHave : t.wizard.rubric.niceToHave}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="w-24">
                    <Label className="text-xs text-muted-foreground">{t.wizard.rubric.years}</Label>
                    <Input
                      type="number"
                      min={0}
                      max={40}
                      value={c.min_years ?? ""}
                      onChange={(e) =>
                        update(i, { min_years: e.target.value === "" ? null : Number(e.target.value) })
                      }
                      className="mt-1 num"
                      placeholder="-"
                    />
                  </div>
                </div>
                <div className="md:col-span-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs text-muted-foreground">{t.wizard.rubric.weight}</Label>
                    <span className="num text-sm font-semibold">{pct}%</span>
                  </div>
                  <Slider
                    value={[Math.round(c.weight * 100)]}
                    min={1}
                    max={100}
                    step={1}
                    onValueChange={(v) => {
                      const n = Array.isArray(v) ? v[0] : v;
                      update(i, { weight: (n as number) / 100 });
                    }}
                    className="mt-2"
                  />
                </div>
              </div>
              <div className="flex items-start justify-end">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => remove(i)}
                  aria-label={t.wizard.rubric.remove}
                  className="text-muted-foreground hover:text-not-met"
                >
                  <Trash2 />
                </Button>
              </div>
            </li>
          );
        })}
      </ul>

      <div className="mt-3">
        <Button variant="outline" onClick={add}>
          <Plus data-icon="inline-start" />
          {t.wizard.rubric.add}
        </Button>
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-paper-2 p-4 sm:p-5">
        <div className="flex items-center gap-3">
          <Switch checked={blind} onCheckedChange={onBlind} id="blind" />
          <div>
            <Label htmlFor="blind" className="font-medium">
              {t.wizard.rubric.blind}
            </Label>
            <p className="text-xs text-muted-foreground">{t.wizard.rubric.blindHint}</p>
          </div>
        </div>
        <Button size="lg" disabled={!valid || busy} onClick={onConfirm} className="h-11 px-6">
          {busy ? t.wizard.rubric.confirming : t.wizard.rubric.confirm}
        </Button>
      </div>
    </section>
  );
}
