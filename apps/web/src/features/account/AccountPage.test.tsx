import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

import { AccountPage } from "./AccountPage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const ME = {
  id: "u1",
  email: "asha@example.test",
  display_name: "Asha",
  created_at: "2026-11-01T09:30:00",
};

const GRANT = {
  id: "g1",
  purpose: "documents.processing",
  policy_version: "1.0",
  granted_at: "2026-11-02T00:00:00",
  withdrawn_at: null,
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

function deleteCalls(): RequestInit[] {
  return vi
    .mocked(fetch)
    .mock.calls.map(([, init]) => init)
    .filter((init): init is RequestInit => init?.method === "DELETE");
}

describe("AccountPage", () => {
  let createObjectURL: ReturnType<typeof vi.fn>;
  let revokeObjectURL: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    createObjectURL = vi.fn(() => "blob:mock");
    revokeObjectURL = vi.fn();
    Object.defineProperty(URL, "createObjectURL", {
      value: createObjectURL,
      configurable: true,
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      value: revokeObjectURL,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it("says which account it is acting on and what the export leaves out", async () => {
    mockApi([["/api/v1/auth/me", () => jsonResponse(ME)]]);

    render(<AccountPage />);

    expect(await screen.findByTestId("account-user")).toHaveTextContent(
      "asha@example.test"
    );
    expect(screen.getByTestId("account-export")).toHaveTextContent(
      "does not include your documents or your profile values"
    );
  });

  it("offers both actions only to a signed-in account", async () => {
    mockApi([["/api/v1/auth/me", () => jsonResponse({ detail: "Not signed in" }, 401)]]);

    render(<AccountPage />);

    expect(await screen.findByTestId("account-signed-out")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Download account record and permissions" })
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Delete my account" })).toBeDisabled();
  });

  it("downloads the account record under a filename the citizen can recognise", async () => {
    mockApi([
      ["/api/v1/auth/export", () => jsonResponse({ user: ME, consent_records: [GRANT] })],
      ["/api/v1/auth/me", () => jsonResponse(ME)],
    ]);
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});

    render(<AccountPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Download account record and permissions",
      })
    );

    expect(await screen.findByTestId("account-message")).toHaveTextContent(
      "Downloaded"
    );
    const anchor = clickSpy.mock.contexts[0] as HTMLAnchorElement;
    expect(anchor.download).toBe("rinavi-account-export.json");
    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock");
  });

  it("reports the server reason when the export is rate-limited", async () => {
    mockApi([
      [
        "/api/v1/auth/export",
        () => jsonResponse({ detail: "Rate limit exceeded" }, 429),
      ],
      ["/api/v1/auth/me", () => jsonResponse(ME)],
    ]);

    render(<AccountPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Download account record and permissions",
      })
    );

    expect(await screen.findByTestId("account-error")).toHaveTextContent(
      "Rate limit exceeded"
    );
    expect(createObjectURL).not.toHaveBeenCalled();
  });

  it("deletes the account only after a confirmation, then leaves the page", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    mockApi([
      ["/api/v1/auth/account", () => new Response(null, { status: 204 })],
      ["/api/v1/auth/me", () => jsonResponse(ME)],
    ]);

    render(<AccountPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Delete my account" }));

    await vi.waitFor(() => expect(pushMock).toHaveBeenCalledWith("/"));
    expect(confirmSpy).toHaveBeenCalled();
    expect(deleteCalls()).toHaveLength(1);
  });

  it("sends nothing when the confirmation is declined", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    mockApi([
      ["/api/v1/auth/account", () => new Response(null, { status: 204 })],
      ["/api/v1/auth/me", () => jsonResponse(ME)],
    ]);

    render(<AccountPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Delete my account" }));

    expect(deleteCalls()).toHaveLength(0);
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("keeps the account on screen when the erasure fails, and says why", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mockApi([
      [
        "/api/v1/auth/account",
        () =>
          jsonResponse(
            { detail: "Account data could not be erased; try again" },
            503
          ),
      ],
      ["/api/v1/auth/me", () => jsonResponse(ME)],
    ]);

    render(<AccountPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Delete my account" }));

    expect(await screen.findByTestId("account-error")).toHaveTextContent(
      "Account data could not be erased; try again"
    );
    expect(pushMock).not.toHaveBeenCalled();
    expect(screen.getByTestId("account-user")).toBeInTheDocument();
  });
});
