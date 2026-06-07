import { describe, it, expect } from "vitest";
import { trimContext, FEYNMAN_CONTEXT_CHAR_BUDGET } from "./FeynmanChat";

describe("trimContext", () => {
  it("caps combined source full_text to the budget", () => {
    const context = {
      sources: [
        { id: "s1", title: "a", full_text: "x".repeat(5000), insights: [{ content: "i" }] },
        { id: "s2", title: "b", full_text: "y".repeat(5000), insights: [{ content: "i" }] },
      ],
      notes: [],
    };

    const trimmed = trimContext(context);
    const total = trimmed.sources.reduce(
      (n, s) => n + ((s.full_text as string) ?? "").length,
      0,
    );
    expect(total).toBe(FEYNMAN_CONTEXT_CHAR_BUDGET);
    // first source keeps its 5000, second is truncated to the remaining 1000
    expect((trimmed.sources[0].full_text as string).length).toBe(5000);
    expect((trimmed.sources[1].full_text as string).length).toBe(1000);
  });

  it("drops insights to save tokens", () => {
    const context = {
      sources: [{ id: "s1", title: "a", full_text: "short", insights: [{ content: "big insight" }] }],
      notes: [],
    };
    const trimmed = trimContext(context);
    expect(trimmed.sources[0].insights).toEqual([]);
    expect(trimmed.sources[0].full_text).toBe("short");
  });

  it("handles empty / missing fields without throwing", () => {
    expect(trimContext({ sources: [], notes: [] }).sources).toEqual([]);
    const trimmed = trimContext({ sources: [{ id: "s1", title: "a", insights: [] }], notes: [] });
    expect(trimmed.sources[0].full_text).toBeUndefined();
  });
});
