import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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
});
