import { describe, expect, it } from "vitest";

import { formatProfileValue, type ProfileValue } from "./profile";

const STORED_GENDER: ProfileValue = {
  id: "v1",
  field_key: "gender",
  value: "female",
  status: "confirmed",
  source_document_id: "d1",
  source_locator: "line 3",
  confidence: "high",
  stale_reason: null,
  correction_history: [],
  updated_at: "2026-11-12T00:00:00",
};

describe("formatProfileValue", () => {
  it("capitalises the stored gender for display", () => {
    expect(formatProfileValue("gender", "female")).toBe("Female");
    expect(formatProfileValue("gender", "male")).toBe("Male");
    expect(formatProfileValue("gender", "non-binary")).toBe("Non-binary");
  });

  it("leaves prose fields exactly as stored", () => {
    expect(formatProfileValue("full_name", "asha devi")).toBe("asha devi");
    expect(formatProfileValue("address", "12 Janpath, New Delhi")).toBe(
      "12 Janpath, New Delhi",
    );
  });

  it("does not change the stored value", () => {
    expect(formatProfileValue(STORED_GENDER.field_key, STORED_GENDER.value)).toBe(
      "Female",
    );
    expect(STORED_GENDER.value).toBe("female");
  });
});
