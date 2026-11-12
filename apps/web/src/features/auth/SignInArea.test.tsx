import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SignInArea } from "./SignInArea";

vi.mock("@simplewebauthn/browser", () => ({
  startAuthentication: vi.fn(),
  startRegistration: vi.fn(),
}));

import { startAuthentication } from "@simplewebauthn/browser";

const API = "http://localhost:8000";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function meResponse(email: string): Response {
  return jsonResponse({
    id: "00000000-0000-0000-0000-000000000001",
    email,
    display_name: email.split("@")[0],
    created_at: "2026-11-11T00:00:00",
  });
}

describe("SignInArea", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("shows the sign-in form when there is no session", async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse({}, 401));

    render(<SignInArea />);

    expect(await screen.findByTestId("signin-form")).toBeInTheDocument();
  });

  it("shows the signed-in state when a session exists", async () => {
    vi.mocked(fetch).mockResolvedValue(meResponse("citizen@example.com"));

    render(<SignInArea />);

    expect(await screen.findByTestId("signed-in")).toBeInTheDocument();
    expect(screen.getByText("Signed in as citizen@example.com")).toBeInTheDocument();
  });

  it("submits dev sign-in and updates the view", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse({}, 401))
      .mockResolvedValueOnce(meResponse("citizen@example.com"));

    render(<SignInArea />);

    const input = await screen.findByLabelText("Email");
    fireEvent.change(input, { target: { value: "citizen@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    expect(await screen.findByTestId("signed-in")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      `${API}/api/v1/auth/dev-signin`,
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ email: "citizen@example.com" }),
      })
    );
  });

  it("signs out and returns to the form", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(meResponse("citizen@example.com"))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(jsonResponse({}, 401));

    render(<SignInArea />);

    fireEvent.click(await screen.findByRole("button", { name: "Sign out" }));

    expect(await screen.findByTestId("signin-form")).toBeInTheDocument();
  });

  it("logs in with a passkey", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse({}, 401))
      .mockResolvedValueOnce(
        jsonResponse({ challenge_id: "ch-1", options: { challenge: "abc" } })
      )
      .mockResolvedValueOnce(meResponse("citizen@example.com"));
    vi.mocked(startAuthentication).mockResolvedValue({
      id: "cred-1",
      rawId: "cred-1",
      type: "public-key",
      response: {},
    } as never);

    render(<SignInArea />);

    fireEvent.click(await screen.findByRole("button", { name: "Use passkey" }));

    expect(await screen.findByTestId("signed-in")).toBeInTheDocument();
    expect(startAuthentication).toHaveBeenCalledWith({ challenge: "abc" });
    expect(fetch).toHaveBeenCalledWith(
      `${API}/api/v1/auth/passkey/login/finish`,
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
  });
});
