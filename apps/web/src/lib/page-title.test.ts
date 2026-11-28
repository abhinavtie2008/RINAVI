import { describe, expect, it } from "vitest";

import { pageTitle } from "./page-title";

describe("pageTitle", () => {
  it("names the subject and the app", () => {
    expect(pageTitle("Income Certificate (Delhi)")).toBe(
      "Income Certificate (Delhi) · RINAVI",
    );
  });

  it("puts the section between the subject and the app", () => {
    expect(pageTitle("REF-1", "Case")).toBe("REF-1 · Case · RINAVI");
    expect(pageTitle("REF-1", "Packet")).toBe("REF-1 · Packet · RINAVI");
  });

  it("falls back to the app name while the subject is unknown", () => {
    expect(pageTitle(null)).toBe("RINAVI");
    expect(pageTitle("   ")).toBe("RINAVI");
    expect(pageTitle(null, "Case")).toBe("Case · RINAVI");
  });
});
