import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { caseRecord } from "./caseFixtures";
import { PacketPage } from "./PacketPage";

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

describe("PacketPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("renders the frozen packet with the fixed copy", async () => {
    mockApi([["/api/v1/locker/cases/case-1", () => jsonResponse(caseRecord())]]);

    render(<PacketPage caseId="case-1" />);

    expect(await screen.findByText(/Asha Devi/)).toBeInTheDocument();
    expect(screen.getByText(/income.txt/)).toBeInTheDocument();
    expect(screen.getByText(/I declare the information is true/)).toBeInTheDocument();
    expect(screen.getByText(/Review only/)).toBeInTheDocument();
    expect(screen.getByText(/If the portal is unavailable/)).toBeInTheDocument();
  });

  it("prints from the print button", async () => {
    const printSpy = vi.spyOn(window, "print").mockImplementation(() => {});
    mockApi([["/api/v1/locker/cases/case-1", () => jsonResponse(caseRecord())]]);

    render(<PacketPage caseId="case-1" />);

    fireEvent.click(await screen.findByTestId("packet-print"));

    expect(printSpy).toHaveBeenCalled();
    printSpy.mockRestore();
  });
});
