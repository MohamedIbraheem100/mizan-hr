"use client";

import { motion } from "motion/react";

import { useLang } from "@/components/language-provider";
import { cn } from "@/lib/utils";

export function Stepper({ step, onStep }: { step: number; onStep?: (i: number) => void }) {
  const { t } = useLang();
  return (
    <ol className="grid grid-cols-4 gap-2">
      {t.wizard.steps.map((label, i) => {
        const state = i < step ? "done" : i === step ? "current" : "todo";
        const clickable = i < step && onStep;
        return (
          <li key={label} className="relative">
            <button
              type="button"
              disabled={!clickable}
              onClick={() => clickable && onStep(i)}
              className={cn(
                "flex w-full items-center gap-2 rounded-md px-1 py-2 text-start",
                clickable && "hover:bg-muted",
              )}
            >
              <span
                className={cn(
                  "num flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-colors",
                  state === "done" && "bg-ink text-paper",
                  state === "current" && "bg-brass text-ink",
                  state === "todo" && "bg-muted text-muted-foreground",
                )}
              >
                {i + 1}
              </span>
              <span
                className={cn(
                  "truncate text-sm",
                  state === "todo" ? "text-muted-foreground" : "font-medium",
                )}
              >
                {label}
              </span>
            </button>
            <div className="mt-1 h-0.5 w-full rounded bg-muted">
              <motion.div
                className="h-full rounded bg-ink"
                initial={false}
                animate={{ width: state === "todo" ? "0%" : "100%" }}
                transition={{ duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
              />
            </div>
          </li>
        );
      })}
    </ol>
  );
}
