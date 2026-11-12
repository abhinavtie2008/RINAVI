import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ServicesPage } from "./ServicesPage";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

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

const DETAIL = {
  ...SERVICE,
  tags: ["income certificate"],
  sources: [
    { title: "e-District Delhi", url: "https://edistrict.delhigovt.nic.in/" },
  ],
  guidance: {
    what_it_is: "An income certificate.",
    official_channel_steps: ["Register on the official portal."],
    not_a_submission_notice: "RINAVI prepares this draft for your review only.",
  },
  checklist_groups: [
    {
      id: "identity_proof",
      label: "Identity proof",
      requirement: "at_least_one",
      accepted_classifications: ["identity"],
    },
  ],
  fields: [
    {
      id: "applicant_name",
      label: "Applicant name",
      binding: "full_name",
      required: true,
      format: "text",
    },
  ],
  declaration: { required: true, text: "I declare the information is true." },
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

describe("ServicesPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("lists available services", async () => {
    mockApi([["/api/v1/catalog/services", () => jsonResponse([SERVICE])]]);
    render(<ServicesPage />);
    expect(
      await screen.findByRole("button", { name: SERVICE.name }),
    ).toBeInTheDocument();
  });

  it("shows source-linked fields, checklist, and submission notice", async () => {
    mockApi([
      ["/api/v1/catalog/services", () => jsonResponse([SERVICE])],
      [
        "/api/v1/catalog/services/delhi-income-certificate",
        () => jsonResponse(DETAIL),
      ],
    ]);
    render(<ServicesPage />);
    fireEvent.click(await screen.findByRole("button", { name: SERVICE.name }));
    const detail = await screen.findByTestId("service-detail");
    expect(detail).toHaveTextContent("Applicant name");
    expect(detail).toHaveTextContent("Identity proof");
    expect(detail).toHaveTextContent("Register on the official portal.");
    expect(screen.getByTestId("submission-notice")).toHaveTextContent(
      "review only",
    );
  });

  it("starts an application and navigates to its draft", async () => {
    mockApi([
      ["/api/v1/catalog/services", () => jsonResponse([SERVICE])],
      [
        "/api/v1/catalog/services/delhi-income-certificate",
        () => jsonResponse(DETAIL),
      ],
      [
        "/api/v1/applications/drafts",
        () => jsonResponse({ id: "draft-1" }, 201),
      ],
    ]);
    render(<ServicesPage />);
    fireEvent.click(await screen.findByRole("button", { name: SERVICE.name }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Start application" }),
    );
    await waitFor(() =>
      expect(push).toHaveBeenCalledWith("/applications/draft-1"),
    );
  });
});
