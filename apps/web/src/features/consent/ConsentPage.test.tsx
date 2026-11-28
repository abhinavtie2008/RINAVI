import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ConsentPage, PURPOSES } from "./ConsentPage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const ACTIVE_GRANT = {
  id: "g1",
  purpose: "documents.processing",
  policy_version: "1.0",
  granted_at: "2026-11-12T00:00:00",
  withdrawn_at: null,
};

const WITHDRAWN_GRANT = {
  ...ACTIVE_GRANT,
  withdrawn_at: "2026-11-13T00:00:00",
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

describe("ConsentPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it("offers exactly the four documented purposes", () => {
    // The web copy of the list, pinned so a purpose added here alone fails
    // instead of becoming an action the API would refuse with 422.
    expect(PURPOSES.map((info) => info.purpose)).toEqual([
      "documents.processing",
      "profile.storage",
      "applications.preparation",
      "locker.tracking",
    ]);
  });

  it("lists every purpose with the state of its grant", async () => {
    mockApi([["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])]]);

    render(<ConsentPage />);

    expect(await screen.findByTestId("consent-documents.processing")).toHaveTextContent(
      "Allowed on 2026-11-12"
    );
    expect(screen.getByTestId("consent-profile.storage")).toHaveTextContent(
      "Not allowed"
    );
    expect(screen.getByTestId("consent-applications.preparation")).toHaveTextContent(
      "Not allowed"
    );
    expect(screen.getByTestId("consent-locker.tracking")).toHaveTextContent(
      "Not allowed"
    );
    expect(screen.getAllByRole("button", { name: "Withdraw" })).toHaveLength(1);
  });

  it("withdraws an active grant and shows the withdrawal date", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const withdrawHandler = vi.fn(() => jsonResponse(WITHDRAWN_GRANT));
    mockApi([
      ["/api/v1/consent/grants/g1/withdraw", withdrawHandler],
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
    ]);

    render(<ConsentPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Withdraw" }));

    expect(await screen.findByTestId("consent-documents.processing")).toHaveTextContent(
      "Withdrawn on 2026-11-13"
    );
    expect(withdrawHandler).toHaveBeenCalled();
    expect(confirmSpy).toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Withdraw" })).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/consent/grants/g1/withdraw",
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
  });

  it("keeps the grant when the confirmation is declined", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const withdrawHandler = vi.fn(() => jsonResponse(WITHDRAWN_GRANT));
    mockApi([
      ["/api/v1/consent/grants/g1/withdraw", withdrawHandler],
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
    ]);

    render(<ConsentPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Withdraw" }));

    expect(withdrawHandler).not.toHaveBeenCalled();
    expect(screen.getByTestId("consent-documents.processing")).toHaveTextContent(
      "Allowed on 2026-11-12"
    );
  });

  it("reports a load failure instead of claiming nothing is allowed", async () => {
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse({ detail: "Not authenticated" }, 401)],
    ]);

    render(<ConsentPage />);

    expect(await screen.findByTestId("consent-error")).toHaveTextContent("Sign in");
  });
});
