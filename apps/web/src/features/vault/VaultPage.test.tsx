import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { DocumentRecord } from "@/lib/vault";

import { VaultPage } from "./VaultPage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function documentRecord(overrides: Partial<DocumentRecord> = {}): DocumentRecord {
  return {
    id: "d1",
    original_filename: "certificate.txt",
    content_type: "text/plain",
    size_bytes: 42,
    status: "processed",
    classification: "income",
    note: null,
    created_at: "2026-11-12T00:00:00",
    processed_at: "2026-11-12T00:00:01",
    ...overrides,
  };
}

const ACTIVE_GRANT = {
  id: "g1",
  purpose: "documents.processing",
  policy_version: "1.0",
  granted_at: "2026-11-12T00:00:00",
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

describe("VaultPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it("shows the consent gate when document processing is not allowed", async () => {
    mockApi([["/api/v1/consent/grants", () => jsonResponse([])]]);

    render(<VaultPage />);

    expect(await screen.findByTestId("consent-gate")).toBeInTheDocument();
    expect(screen.queryByLabelText("Document file")).not.toBeInTheDocument();
  });

  it("grants consent and reveals an empty vault", async () => {
    mockApi([
      [
        "/api/v1/consent/grants",
        (init) =>
          init?.method === "POST" ? jsonResponse(ACTIVE_GRANT, 201) : jsonResponse([]),
      ],
      ["/api/v1/vault/documents", () => jsonResponse([])],
    ]);

    render(<VaultPage />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Allow document processing" })
    );

    expect(await screen.findByTestId("vault-empty")).toBeInTheDocument();
  });

  it("uploads a file and lists the processed document", async () => {
    const uploaded = documentRecord();
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      [
        "/api/v1/vault/documents",
        (init) =>
          init?.method === "POST" ? jsonResponse(uploaded, 201) : jsonResponse([]),
      ],
    ]);

    render(<VaultPage />);

    const input = await screen.findByLabelText("Document file");
    fireEvent.change(input, {
      target: {
        files: [
          new File(["Name: Asha Devi"], "certificate.txt", { type: "text/plain" }),
        ],
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload document" }));

    const row = await screen.findByTestId("document-row");
    expect(row).toHaveTextContent("certificate.txt");
    expect(row).toHaveTextContent("Ready");
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/vault/documents",
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
    const uploadCall = vi
      .mocked(fetch)
      .mock.calls.find(([, init]) => init?.method === "POST");
    expect(uploadCall?.[1]?.body).toBeInstanceOf(FormData);
    expect(uploadCall?.[1]?.headers).toBeUndefined();
  });

  it("deletes a document and removes it from the list", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      ["/api/v1/vault/documents/d1", () => new Response(null, { status: 204 })],
      ["/api/v1/vault/documents", () => jsonResponse([documentRecord()])],
    ]);

    render(<VaultPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));

    expect(await screen.findByTestId("vault-empty")).toBeInTheDocument();
    expect(confirmSpy).toHaveBeenCalledWith(
      "Delete this document? This cannot be undone."
    );
  });

  it("keeps the document when the delete confirmation is declined", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const deleteHandler = vi.fn(() => new Response(null, { status: 204 }));
    mockApi([
      ["/api/v1/consent/grants", () => jsonResponse([ACTIVE_GRANT])],
      ["/api/v1/vault/documents/d1", deleteHandler],
      ["/api/v1/vault/documents", () => jsonResponse([documentRecord()])],
    ]);

    render(<VaultPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));

    expect(deleteHandler).not.toHaveBeenCalled();
    expect(screen.getByTestId("document-row")).toBeInTheDocument();
  });
});
