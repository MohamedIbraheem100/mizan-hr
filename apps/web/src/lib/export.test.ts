import { describe, expect, it } from "vitest";

import type { Rubric, ScreeningResult } from "./api";
import { toCsv } from "./export";

const rubric: Rubric = {
  job_title: "Backend",
  language: "en",
  criteria: [
    { id: "c1", name: "Python", type: "must_have", weight: 0.6, min_years: 3, description: "" },
    { id: "c2", name: "SQL, advanced", type: "nice_to_have", weight: 0.4, min_years: null, description: "" },
  ],
};

const result = {
  candidate_ref: "Candidate 01",
  score: 80,
  must_haves_met: true,
  missing_must_haves: [],
  summary: 'Strong "backend" profile, meets all must-haves',
  judgments: [
    { criterion_id: "c1", verdict: "met" },
    { criterion_id: "c2", verdict: "partial" },
  ],
} as unknown as ScreeningResult;

describe("toCsv", () => {
  it("writes a BOM, one column per criterion, and escapes quotes and commas", () => {
    const csv = toCsv(rubric, [{ rank: 1, result }]);
    const [header, row] = csv.split("\n");
    expect(header.startsWith("﻿")).toBe(true);
    expect(header).toContain('"SQL, advanced (nice_to_have, 40%)"');
    expect(row).toBe(
      '1,Candidate 01,80,yes,,met,partial,"Strong ""backend"" profile, meets all must-haves"',
    );
  });
});
