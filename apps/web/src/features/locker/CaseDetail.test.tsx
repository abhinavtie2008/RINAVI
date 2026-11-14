import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { draftRecord } from "@/features/applications/draftFixtures";

import { CaseDetail } from "./CaseDetail";
import { caseEvent, caseRecord } from "./caseFixtures";

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

describe("CaseDetail", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    window.sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("renders the status chip, numbers, and journal newest first", async () => {
    const record = caseRecord({
      status: "acknowledged",
      reference_number: "REF-1",
      acknowledgement_number: "ACK-9",
      events: [
        caseEvent({ id: "e1", type: "created" }),
        caseEvent({
          id: "e2",
          type: "submitted",
          payload: { reference_number: "REF-1" },
        }),
        caseEvent({
          id: "e3",
          type: "acknowledged",
          payload: { acknowledgement_number: "ACK-9" },
        }),
      ],
    });
    mockApi([["/api/v1/locker/cases/case-1", () => jsonResponse(record)]]);

    render(<CaseDetail caseId="case-1" />);

    expect(await screen.findByTestId("case-status-chip")).toHaveTextContent(
      "Acknowledged",
    );
    expect(
      screen.getByText(
        (_content, element) =>
          element?.tagName === "P" &&
          element.textContent === "Reference number: REF-1",
      ),
    ).toBeInTheDocument();
    const events = screen.getAllByTestId("case-event");
    expect(events[0]).toHaveTextContent("Acknowledgement recorded");
    expect(events[2]).toHaveTextContent("Application prepared");
  });

  it("shows acknowledgement guidance for a submitted case without one", async () => {
    mockApi([
      [
        "/api/v1/locker/cases/case-1",
        () =>
          jsonResponse(
            caseRecord({ status: "submitted", reference_number: "REF-1" }),
          ),
      ],
    ]);

    render(<CaseDetail caseId="case-1" />);

    expect(
      await screen.findByTestId("acknowledgement-note"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("portal-down-guidance")).toBeInTheDocument();
  });

  it("records a submission and refreshes the case", async () => {
    mockApi([
      [
        "/api/v1/locker/cases/case-1/events",
        () =>
          jsonResponse(
            caseRecord({ status: "submitted", reference_number: "REF-7" }),
          ),
      ],
      ["/api/v1/locker/cases/case-1", () => jsonResponse(caseRecord())],
    ]);

    render(<CaseDetail caseId="case-1" />);

    fireEvent.change(
      await screen.findByLabelText("Reference number (optional)"),
      { target: { value: "REF-7" } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Mark as submitted" }));

    expect(await screen.findByText("Submitted")).toBeInTheDocument();
  });

  it("records an uncertain submission with the right event payload", async () => {
    const bodies: unknown[] = [];
    mockApi([
      [
        "/api/v1/locker/cases/case-1/events",
        (init) => {
          bodies.push(JSON.parse(String(init?.body)));
          return jsonResponse(caseRecord({ status: "uncertain" }));
        },
      ],
      ["/api/v1/locker/cases/case-1", () => jsonResponse(caseRecord())],
    ]);

    render(<CaseDetail caseId="case-1" />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Mark as uncertain" }),
    );

    expect(await screen.findByText("Uncertain")).toBeInTheDocument();
    expect(bodies).toEqual([{ type: "uncertain" }]);
  });

  it("applies again, stores suggestions, and opens the new draft", async () => {
    mockApi([
      [
        "/api/v1/locker/cases/case-1/apply-again",
        () =>
          jsonResponse(
            {
              draft: draftRecord(),
              suggested_links: [
                { document_id: "doc-1", group_id: "income_evidence" },
              ],
            },
            201,
          ),
      ],
      ["/api/v1/locker/cases/case-1", () => jsonResponse(caseRecord())],
    ]);

    render(<CaseDetail caseId="case-1" />);

    fireEvent.click(await screen.findByTestId("apply-again"));

    await waitFor(() =>
      expect(push).toHaveBeenCalledWith("/applications/draft-1"),
    );
    expect(
      window.sessionStorage.getItem("rinavi:suggested-links:draft-1"),
    ).toBe(JSON.stringify([{ document_id: "doc-1", group_id: "income_evidence" }]));
  });
});
