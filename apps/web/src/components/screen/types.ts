import type { NodeStatuses } from "@/components/pipeline-rail";
import type { CvLine, ScreeningResult } from "@/lib/api";

export type CandidateStatus = "queued" | "running" | "done" | "error";

export type Candidate = {
  id: string;
  file: File;
  ref: string;
  status: CandidateStatus;
  statuses: NodeStatuses;
  lines?: CvLine[];
  result?: ScreeningResult;
  error?: string;
};

export function rankResults<T extends { result?: ScreeningResult }>(items: T[]): T[] {
  return [...items]
    .filter((c) => c.result)
    .sort((a, b) => {
      const ra = a.result!;
      const rb = b.result!;
      if (ra.must_haves_met !== rb.must_haves_met) return ra.must_haves_met ? -1 : 1;
      return rb.score - ra.score;
    });
}
