import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ProfileValue } from "@/lib/profile";
import type { DocumentRecord } from "@/lib/vault";

import { ProfilePage } from "./ProfilePage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const ACTIVE_GRANT = {
  id: "g1",
  purpose: "profile.storage",
  policy_version: "1.0",
  granted_at: "2026-11-12T00:00:00",
  withdrawn_at: null,
};

function value(overrides: Partial<ProfileValue> = {}): ProfileValue {
  return {
    id: "v1",
    field_key: "full_name",
    value: "Asha Devi",
    status: "unconfirmed",
    source_document_id: "d1",
    source_locator: "line 1",
    confidence: "high",
    stale_reason: null,
    correction_history: [],
    updated_at: "2026-11-12T00:00:00",
    ...overrides,
  };
}

const PROCESSED_DOCUMENT: DocumentRecord = {
  id: "d1",
  original_filename: "income.txt",
  content_type: "text/plain",
  size_bytes: 42,
  status: "processed",
  classification: "income",
  note: null,
  created_at: "2026-11-12T00:00:00",
  processed_at: "2026-11-12T00:00:01",
};

function mockApi(
  handlers: Array<[suffix: string, handler: (init?: RequestInit) => Response]>
) {
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    const url = String(input);
    const match = handlers.find(([suffix]) => url.endsWith(suffix));
    if (!match) {
      return jsonResponse({}, 404);
    }
    return match[1](init);
  });
}

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("shows the consent gate when profile storage is not allowed", async () => {
    mockApi([["/api/v1/consent/grants", () => jsonResponse([])]]);

    render(<ProfilePage />);

    expect(await screen.findByTestId("profile-consent-gate")).toBeInTheDocument();
  });

  it("confirms an unconfirmed value", async () => {
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      [
        "/api/v1/profile/values/v1/confirm",
        () => jsonResponse(value({ status: "confirmed" })),
      ],
      ["/api/v1/profile/values", () => jsonResponse([value()])],
      ["/api/v1/vault/documents", () => jsonResponse([])],
    ]);

    render(<ProfilePage />);

    fireEvent.click(await screen.findByRole("button", { name: "Confirm" }));

    expect(await screen.findByText(/Confirmed/)).toBeInTheDocument();
    expect(screen.queryByText(/Needs review/)).not.toBeInTheDocument();
  });

  it("corrects a value and shows the corrected text", async () => {
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      [
        "/api/v1/profile/values/v1/correct",
        () =>
          jsonResponse(
            value({
              value: "Asha Devi Sharma",
              status: "confirmed",
              correction_history: [
                { old_value: "Asha Devi", corrected_at: "2026-11-12T01:00:00" },
              ],
            })
          ),
      ],
      ["/api/v1/profile/values", () => jsonResponse([value()])],
      ["/api/v1/vault/documents", () => jsonResponse([])],
    ]);

    render(<ProfilePage />);

    fireEvent.click(await screen.findByRole("button", { name: "Correct" }));
    const input = await screen.findByLabelText("Correct Full name");
    fireEvent.change(input, { target: { value: "Asha Devi Sharma" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Asha Devi Sharma")).toBeInTheDocument();
  });

  it("shows stale values with their reason and source context", async () => {
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      [
        "/api/v1/profile/values",
        () =>
          jsonResponse([
            value({
              status: "stale",
              stale_reason: "source_document_deleted",
              source_document_id: null,
              source_locator: null,
            }),
          ]),
      ],
      ["/api/v1/vault/documents", () => jsonResponse([])],
    ]);

    render(<ProfilePage />);

    expect(await screen.findByText(/Needs re-check/)).toBeInTheDocument();
    expect(screen.getByText(/source_document_deleted/)).toBeInTheDocument();
  });

  it("promotes values from a processed document", async () => {
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      ["/api/v1/profile/values/promote", () => jsonResponse([value()])],
      ["/api/v1/profile/values", () => jsonResponse([])],
      ["/api/v1/vault/documents", () => jsonResponse([PROCESSED_DOCUMENT])],
    ]);

    render(<ProfilePage />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Use this document" })
    );

    expect(await screen.findByText("Asha Devi")).toBeInTheDocument();
    expect(screen.getByText(/Needs review/)).toBeInTheDocument();
  });
});
