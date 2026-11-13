import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApplicationsPage } from "./ApplicationsPage";
import { draftRecord } from "./draftFixtures";

const ACTIVE_GRANT = {
  id: "g1",
  purpose: "applications.preparation",
  policy_version: "1.0",
  granted_at: "2026-11-12T00:00:00",
  withdrawn_at: null,
};

const SERVICE = {
  slug: "delhi-income-certificate",
  name: "Income Certificate (Delhi)",
  geography: "Delhi",
  department: "Revenue Department, Government of NCT of Delhi",
  latest_version: "1.0.0",
  summary: "Prepare a Delhi income certificate application.",
  fee: "No application fee listed by the official source",
  processing_time:
    "Indicative only: around 14 days after submission; not a guarantee",
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

describe("ApplicationsPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("shows the consent gate when application preparation is not allowed", async () => {
    mockApi([["/api/v1/consent/grants", () => jsonResponse([])]]);

    render(<ApplicationsPage />);

    expect(await screen.findByTestId("consent-gate")).toBeInTheDocument();
  });

  it("grants consent and shows an empty application list", async () => {
    mockApi([
      [
        "/api/v1/consent/grants",
        (init) =>
          init?.method === "POST"
            ? jsonResponse(ACTIVE_GRANT, 201)
            : jsonResponse([]),
      ],
      ["/api/v1/applications/drafts", () => jsonResponse([])],
      ["/api/v1/catalog/services", () => jsonResponse([])],
    ]);

    render(<ApplicationsPage />);

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Allow application preparation",
      }),
    );

    expect(await screen.findByTestId("applications-empty")).toBeInTheDocument();
  });

  it("starts a new application from the service picker", async () => {
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      [
        "/api/v1/applications/drafts",
        (init) =>
          init?.method === "POST"
            ? jsonResponse(draftRecord(), 201)
            : jsonResponse([]),
      ],
      ["/api/v1/catalog/services", () => jsonResponse([SERVICE])],
    ]);

    render(<ApplicationsPage />);

    fireEvent.change(await screen.findByLabelText("Service"), {
      target: { value: "delhi-income-certificate" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Start new application" }),
    );

    expect(await screen.findByTestId("draft-row")).toHaveTextContent(
      "Income Certificate (Delhi)",
    );
  });
});
