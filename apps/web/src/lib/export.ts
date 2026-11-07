import type { Rubric, ScreeningResult } from "@/lib/api";

export type ExportRow = { rank: number; result: ScreeningResult };

function csvCell(v: unknown): string {
  const s = String(v ?? "");
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function toCsv(rubric: Rubric, rows: ExportRow[]): string {
  const header = [
    "rank",
    "candidate",
    "score",
    "must_haves_met",
    "missing_must_haves",
    ...rubric.criteria.map((c) => `${c.name} (${c.type}, ${Math.round(c.weight * 100)}%)`),
    "summary",
  ];
  const lines = rows.map(({ rank, result }) => {
    const byId = new Map(result.judgments.map((j) => [j.criterion_id, j]));
    return [
      rank,
      result.candidate_ref,
      result.score,
      result.must_haves_met ? "yes" : "no",
      result.missing_must_haves.join("; "),
      ...rubric.criteria.map((c) => byId.get(c.id)?.verdict ?? ""),
      result.summary,
    ]
      .map(csvCell)
      .join(",");
  });
  // BOM so Excel opens Arabic correctly.
  return "﻿" + [header.map(csvCell).join(","), ...lines].join("\n");
}

export function download(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
