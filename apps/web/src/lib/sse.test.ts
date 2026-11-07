import { describe, expect, it } from "vitest";

import { parseSseChunk } from "./sse";

describe("parseSseChunk", () => {
  it("parses complete events and keeps the incomplete tail", () => {
    const buf =
      'event: progress\ndata: {"node":"parse"}\n\nevent: result\ndata: {"score":90}\n\nevent: prog';
    const { events, rest } = parseSseChunk(buf);
    expect(events).toEqual([
      { event: "progress", data: '{"node":"parse"}' },
      { event: "result", data: '{"score":90}' },
    ]);
    expect(rest).toBe("event: prog");
  });

  it("defaults the event name to message and joins multi-line data", () => {
    const { events } = parseSseChunk("data: a\ndata: b\n\n");
    expect(events).toEqual([{ event: "message", data: "a\nb" }]);
  });

  it("ignores blocks without data (comments, keep-alives)", () => {
    const { events } = parseSseChunk(": keep-alive\n\nevent: x\n\n");
    expect(events).toEqual([]);
  });
});
