"use client";

import { useState } from "react";

import { useLang } from "@/components/language-provider";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const MIN = 30;
const MAX = 10_000;

export function JdStep({
  value,
  onChange,
  onSubmit,
  busy,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  busy: boolean;
}) {
  const { t } = useLang();
  const [active, setActive] = useState<string | null>(null);
  const templates = Object.entries(t.templates) as [string, { name: string; body: string }][];
  const ok = value.trim().length >= MIN && value.length <= MAX;

  return (
    <section className="animate-rise">
      <h2 className="text-2xl font-semibold tracking-tight">{t.wizard.jd.title}</h2>
      <p className="mt-1 text-muted-foreground">{t.wizard.jd.hint}</p>

      <div className="mt-6">
        <p className="eyebrow mb-2">{t.wizard.jd.templates}</p>
        <div className="flex flex-wrap gap-2">
          {templates.map(([key, tpl]) => (
            <button
              key={key}
              type="button"
              onClick={() => {
                onChange(tpl.body);
                setActive(key);
              }}
              className={cn(
                "rounded-full border px-3.5 py-1.5 text-sm transition-colors hover:border-ink",
                active === key && value === tpl.body ? "border-ink bg-ink text-paper" : "bg-card",
              )}
            >
              {tpl.name}
            </button>
          ))}
        </div>
      </div>

      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={t.wizard.jd.placeholder}
        dir="auto"
        className="mt-5 min-h-[260px] resize-y bg-card text-base leading-relaxed"
        maxLength={MAX}
      />
      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
        <span className={cn(!ok && value.length > 0 && "text-not-met")}>
          {value.trim().length < MIN ? t.wizard.jd.min : ""}
        </span>
        <span className="num">
          {value.length.toLocaleString()} / {MAX.toLocaleString()} {t.wizard.jd.chars}
        </span>
      </div>

      <div className="mt-6 flex justify-end">
        <Button size="lg" disabled={!ok || busy} onClick={onSubmit} className="h-11 px-6">
          {busy ? t.wizard.jd.generating : t.wizard.jd.generate}
        </Button>
      </div>
    </section>
  );
}
