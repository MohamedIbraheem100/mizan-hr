"use client";

import { motion } from "motion/react";

import { useLang } from "@/components/language-provider";
import type { NodeName, NodeStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

export const NODE_ORDER: NodeName[] = ["parse", "redact", "extract", "judge", "verify", "score", "explain"];
const CODE_NODES = new Set<NodeName>(["parse", "verify", "score"]);

export type NodeStatuses = Partial<Record<NodeName, NodeStatus>>;

/* One rail, two uses: static explainer on the landing (no statuses) and the
   live "Watch Mizan Think" strip per candidate (statuses from SSE). */
export function PipelineRail({
  statuses,
  compact = false,
  className,
}: {
  statuses?: NodeStatuses;
  compact?: boolean;
  className?: string;
}) {
  const { t } = useLang();
  const live = statuses !== undefined;
  return (
    <ol
      className={cn(
        "grid gap-2",
        compact ? "grid-cols-7" : "grid-cols-2 sm:grid-cols-4 lg:grid-cols-7",
        className,
      )}
    >
      {NODE_ORDER.map((node, i) => {
        const status = statuses?.[node];
        const isCode = CODE_NODES.has(node);
        return (
          <motion.li
            key={node}
            initial={live ? false : { opacity: 0, y: 10 }}
            whileInView={live ? undefined : { opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: i * 0.06, duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
            className={cn(
              "relative overflow-hidden rounded-lg border bg-card transition-colors",
              compact ? "px-2 py-1.5" : "p-4",
              status === "running" && "border-brass",
              status === "done" && "border-met/50",
              status === "skipped" && "opacity-50",
              status === "error" && "border-not-met",
            )}
          >
            {status === "running" && (
              <span className="absolute inset-x-0 bottom-0 h-0.5 bg-brass/30">
                <span className="block h-full w-1/3 animate-sweep bg-brass" />
              </span>
            )}
            <div className="flex items-center justify-between gap-2">
              <span className={cn("font-medium", compact ? "text-[11px]" : "text-sm")}>
                {t.pipeline.steps[node].t}
              </span>
              {!compact && (
                <span
                  className={cn(
                    "rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider",
                    isCode ? "bg-ink text-paper" : "bg-brass-soft text-ink",
                  )}
                >
                  {isCode ? t.pipeline.code : t.pipeline.model}
                </span>
              )}
              {live && (
                <StatusDot status={status} />
              )}
            </div>
            {!compact && (
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                {t.pipeline.steps[node].d}
              </p>
            )}
          </motion.li>
        );
      })}
    </ol>
  );
}

function StatusDot({ status }: { status?: NodeStatus }) {
  return (
    <span
      className={cn(
        "size-2 shrink-0 rounded-full",
        !status && "bg-border",
        status === "running" && "animate-pulse-soft bg-brass",
        status === "done" && "bg-met",
        status === "skipped" && "bg-no-evidence",
        status === "error" && "bg-not-met",
      )}
    />
  );
}
