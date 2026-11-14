import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CasesPage } from "./CasesPage";
import { caseSummary } from "./caseFixtures";

const ACTIVE_GRANT = {
  id: "g1",
  purpose: "locker.tracking",
  policy_version: "1.0",
  granted_at: "2026-11-13T00:00:00",
  withdrawn_at: null,
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function mockApi(
  handlers: Array<[suffix: string, handler: (init?: RequestInit) => Response]>,
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

describe("CasesPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("shows the consent gate when tracking is not allowed", async () => {
    mockApi([["/api/v1/consent/grants", () => jsonResponse([])]]);

    render(<CasesPage />);

    expect(await screen.findByTestId("consent-gate")).toBeInTheDocument();
  });

  it("grants consent and shows an empty locker", async () => {
    mockApi([
      [
        "/api/v1/consent/grants",
        (init) =>
          init?.method === "POST"
            ? jsonResponse(ACTIVE_GRANT, 201)
            : jsonResponse([]),
      ],
      ["/api/v1/locker/cases", () => jsonResponse([])],
    ]);

    render(<CasesPage />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Allow application tracking" }),
    );

    expect(await screen.findByTestId("locker-empty")).toBeInTheDocument();
  });

  it("lists cases with status chip, date, and reference number", async () => {
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      [
        "/api/v1/locker/cases",
        () =>
          jsonResponse([
            caseSummary({
              id: "case-2",
              service_name: "Income Certificate (Delhi)",
              status: "submitted",
              reference_number: "REF-42",
            }),
          ]),
      ],
    ]);

    render(<CasesPage />);

    expect(
      await screen.findByRole("link", { name: "Income Certificate (Delhi)" }),
    ).toHaveAttribute("href", "/locker/case-2");
    expect(screen.getByText("Submitted")).toBeInTheDocument();
    expect(screen.getByText(/REF-42/)).toBeInTheDocument();
  });
});
