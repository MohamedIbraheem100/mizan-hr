"use client";

import { motion } from "motion/react";

import { cn } from "@/lib/utils";

export function ScoreRing({
  score,
  flagged,
  size = 64,
  className,
}: {
  score: number;
  flagged?: boolean;
  size?: number;
  className?: string;
}) {
  const stroke = Math.max(4, Math.round(size / 12));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const color = flagged ? "var(--partial)" : score >= 70 ? "var(--met)" : score >= 40 ? "var(--partial)" : "var(--no-evidence)";
  return (
    <div className={cn("relative shrink-0", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="var(--border)" strokeWidth={stroke} fill="none" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c - (c * score) / 100 }}
          transition={{ duration: 1, ease: [0.2, 0.8, 0.2, 1] }}
        />
      </svg>
      <span
        className="num absolute inset-0 flex items-center justify-center font-semibold"
        style={{ fontSize: size / 3.2 }}
      >
        {score}
      </span>
    </div>
  );
}
