/* Typed client for the Mizan API. Mirrors apps/api/mizan/schemas. */

import { readSse } from "@/lib/sse";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

export type CriterionType = "must_have" | "nice_to_have";
export type Verdict = "met" | "partial" | "not_met" | "no_evidence";
export type NodeName = "parse" | "redact" | "extract" | "judge" | "verify" | "score" | "explain";
export type NodeStatus = "running" | "done" | "skipped" | "error";

export type Criterion = {
  id: string;
  name: string;
  type: CriterionType;
  weight: number;
  min_years: number | null;
  description: string;
};
export type Rubric = { job_title: string; language: "ar" | "en"; criteria: Criterion[] };

export type Evidence = { line_id: string; quote: string };
export type Judgment = {
  criterion_id: string;
  criterion_name: string;
  criterion_type: CriterionType;
  weight: number;
  verdict: Verdict;
  evidence: Evidence[];
  dropped_evidence: Evidence[];
  reasoning: string;
  verdict_before_verify: Verdict | null;
};
export type Profile = {
  headline: string;
  total_years_experience: number | null;
  skills: string[];
  experiences: { title: string; organization: string; period: string; years: number | null; line_ids: string[] }[];
  education: string[];
  languages: string[];
  certifications: string[];
};
export type VerifyStats = {
  quotes_checked: number;
  quotes_verified: number;
  quotes_dropped: number;
  verdicts_downgraded: number;
};
export type ScreeningResult = {
  candidate_ref: string;
  language: "ar" | "en";
  blind: boolean;
  score: number;
  must_haves_met: boolean;
  missing_must_haves: string[];
  judgments: Judgment[];
  strengths: string[];
  gaps: string[];
  summary: string;
  interview_questions: string[];
  profile: Profile;
  verify: VerifyStats;
  line_count: number;
  llm_calls: number;
  duration_ms: number;
};
export type CvLine = { id: string; text: string };
export type ProgressEvent = {
  node: NodeName;
  status: NodeStatus;
  detail: Record<string, unknown> & { lines?: CvLine[] | number };
};
export type ScreeningView = {
  screening_id: string;
  rubric: Rubric;
  blind: boolean;
  created_at: string;
  expires_at: string;
  results: ScreeningResult[];
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function readError(res: Response): Promise<ApiError> {
  let detail = res.statusText;
  try {
    const body = await res.json();
    detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
  } catch {
    /* non-JSON body */
  }
  return new ApiError(res.status, detail);
}

export async function createRubric(jd_text: string): Promise<Rubric> {
  const res = await fetch(`${API_URL}/rubric`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jd_text }),
  });
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function createScreening(
  rubric: Rubric,
  blind: boolean,
): Promise<{ screening_id: string; blind: boolean; expires_at: string }> {
  const res = await fetch(`${API_URL}/screenings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rubric, blind }),
  });
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function getScreening(id: string): Promise<ScreeningView> {
  const res = await fetch(`${API_URL}/screenings/${encodeURIComponent(id)}`, { cache: "no-store" });
  if (!res.ok) throw await readError(res);
  return res.json();
}

export type ScreenCallbacks = {
  onProgress: (e: ProgressEvent) => void;
  onResult: (r: ScreeningResult) => void;
  onError: (message: string) => void;
};

/** POST /screen and stream its SSE events. Resolves when the stream ends. */
export async function screenCv(
  file: File,
  screeningId: string,
  candidateRef: string,
  cb: ScreenCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const form = new FormData();
  form.append("file", file, file.name);
  form.append("screening_id", screeningId);
  form.append("candidate_ref", candidateRef);
  const res = await fetch(`${API_URL}/screen`, { method: "POST", body: form, signal });
  if (!res.ok) throw await readError(res);
  await readSse(
    res,
    (e) => {
      if (e.event === "progress") cb.onProgress(JSON.parse(e.data));
      else if (e.event === "result") cb.onResult(JSON.parse(e.data));
      else if (e.event === "error") cb.onError(JSON.parse(e.data).detail ?? "error");
    },
    signal,
  );
}
