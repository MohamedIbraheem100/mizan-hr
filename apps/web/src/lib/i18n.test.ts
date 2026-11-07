import { describe, expect, it } from "vitest";

import { dictionaries } from "./i18n";

function keys(obj: unknown, prefix = ""): string[] {
  if (Array.isArray(obj)) return [prefix];
  if (obj && typeof obj === "object") {
    return Object.entries(obj as Record<string, unknown>).flatMap(([k, v]) =>
      keys(v, prefix ? `${prefix}.${k}` : k),
    );
  }
  return [prefix];
}

describe("dictionaries", () => {
  it("have identical key sets in Arabic and English", () => {
    expect(keys(dictionaries.ar).sort()).toEqual(keys(dictionaries.en).sort());
  });

  it("contain no emoji", () => {
    const text = JSON.stringify(dictionaries);
    expect(/\p{Extended_Pictographic}/u.test(text)).toBe(false);
  });
});
