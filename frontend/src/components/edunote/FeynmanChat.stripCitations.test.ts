import { describe, it, expect } from "vitest";
import { stripCitations } from "./FeynmanChat";

describe("stripCitations", () => {
  it("removes a trailing source citation and its leading space", () => {
    expect(stripCitations("如何確保索引仍然有效呢？ [source:dgy4qy4sqp8qs48vtv3b]")).toBe(
      "如何確保索引仍然有效呢？",
    );
  });

  it("removes note and insight citations mid-text", () => {
    expect(stripCitations("see [note:xyz] and [insight:def] now")).toBe("see and now");
  });

  it("removes multiple citations", () => {
    expect(stripCitations("a [source:1] b [source:2]")).toBe("a b");
  });

  it("leaves normal text (and ordinary brackets) untouched", () => {
    expect(stripCitations("這是正常的問題嗎？")).toBe("這是正常的問題嗎？");
    expect(stripCitations("陣列 arr[0] 是什麼？")).toBe("陣列 arr[0] 是什麼？");
  });
});
