import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { caseRecord } from "@/features/locker/caseFixtures";

import { DraftDetail } from "./DraftDetail";
import { draftRecord } from "./draftFixtures";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

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

describe("DraftDetail", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    window.sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("locks profile values and shows the submission notice", async () => {
    mockApi([
      ["/api/v1/applications/drafts/draft-1", () => jsonResponse(draftRecord())],
      ["/api/v1/vault/documents", () => jsonResponse([])],
    ]);

    render(<DraftDetail draftId="draft-1" />);

    expect(await screen.findByLabelText("Applicant name *")).toBeDisabled();
    expect(screen.getByTestId("submission-notice")).toHaveTextContent(
      "review only",
    );
  });

  it("shows validation issues returned by the API", async () => {
    const draft = draftRecord({
      validation: [
        {
          code: "field_required",
          field_id: "purpose",
          group_id: null,
          document_id: null,
          message: "This field is required.",
        },
      ],
    });
    mockApi([
      ["/api/v1/applications/drafts/draft-1", () => jsonResponse(draft)],
      ["/api/v1/vault/documents", () => jsonResponse([])],
    ]);

    render(<DraftDetail draftId="draft-1" />);

    expect(await screen.findByText("This field is required.")).toBeInTheDocument();
  });

  it("previews the export text", async () => {
    mockApi([
      ["/api/v1/applications/drafts/draft-1", () => jsonResponse(draftRecord())],
      ["/api/v1/vault/documents", () => jsonResponse([])],
      [
        "/api/v1/applications/drafts/draft-1/export",
        () =>
          jsonResponse({
            text: "RINAVI — application draft (NOT a submission)",
          }),
      ],
    ]);

    render(<DraftDetail draftId="draft-1" />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Preview final draft" }),
    );

    expect(await screen.findByTestId("export-text")).toHaveTextContent(
      "NOT a submission",
    );
  });

  it("updates the declaration from the checkbox", async () => {
    mockApi([
      ["/api/v1/applications/drafts/draft-1", () => jsonResponse(draftRecord())],
      ["/api/v1/vault/documents", () => jsonResponse([])],
      [
        "/api/v1/applications/drafts/draft-1/declaration",
        () => jsonResponse(draftRecord({ declaration_confirmed: true })),
      ],
    ]);

    render(<DraftDetail draftId="draft-1" />);

    fireEvent.click(await screen.findByRole("checkbox"));

    await waitFor(() => expect(screen.getByRole("checkbox")).toBeChecked());
  });

  it("shows the finish button when the draft has no issues", async () => {
    mockApi([
      ["/api/v1/applications/drafts/draft-1", () => jsonResponse(draftRecord())],
      ["/api/v1/vault/documents", () => jsonResponse([])],
    ]);

    render(<DraftDetail draftId="draft-1" />);

    expect(await screen.findByTestId("complete-draft")).toBeInTheDocument();
  });

  it("hides the finish button when issues remain", async () => {
    const draft = draftRecord({
      validation: [
        {
          code: "field_required",
          field_id: "purpose",
          group_id: null,
          document_id: null,
          message: "This field is required.",
        },
      ],
    });
    mockApi([
      ["/api/v1/applications/drafts/draft-1", () => jsonResponse(draft)],
      ["/api/v1/vault/documents", () => jsonResponse([])],
    ]);

    render(<DraftDetail draftId="draft-1" />);

    await screen.findByText("This field is required.");
    expect(screen.queryByTestId("complete-draft")).not.toBeInTheDocument();
  });

  it("completes the draft and opens the locker case", async () => {
    mockApi([
      ["/api/v1/applications/drafts/draft-1", () => jsonResponse(draftRecord())],
      ["/api/v1/vault/documents", () => jsonResponse([])],
      [
        "/api/v1/applications/drafts/draft-1/complete",
        () => jsonResponse(caseRecord()),
      ],
    ]);

    render(<DraftDetail draftId="draft-1" />);

    fireEvent.click(await screen.findByTestId("complete-draft"));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/locker/case-1"));
  });

  it("shows and attaches suggested evidence from a previous application", async () => {
    window.sessionStorage.setItem(
      "rinavi:suggested-links:draft-1",
      JSON.stringify([{ document_id: "doc-1", group_id: "income_evidence" }]),
    );
    mockApi([
      ["/api/v1/applications/drafts/draft-1", () => jsonResponse(draftRecord())],
      [
        "/api/v1/vault/documents",
        () =>
          jsonResponse([
            {
              id: "doc-1",
              original_filename: "income.txt",
              content_type: "text/plain",
              size_bytes: 10,
              status: "processed",
              classification: "income",
              note: null,
              created_at: "2026-11-13T00:00:00",
              processed_at: "2026-11-13T00:00:00",
            },
          ]),
      ],
      [
        "/api/v1/applications/drafts/draft-1/documents/doc-1",
        () =>
          jsonResponse(draftRecord({ document_links: { income_evidence: ["doc-1"] } })),
      ],
    ]);

    render(<DraftDetail draftId="draft-1" />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Attach income.txt" }),
    );

    await waitFor(() =>
      expect(screen.queryByTestId("suggested-evidence")).not.toBeInTheDocument(),
    );
    expect(
      window.sessionStorage.getItem("rinavi:suggested-links:draft-1"),
    ).toBeNull();
  });
});
