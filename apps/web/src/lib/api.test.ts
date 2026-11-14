import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "./api";

function abortableFetchMock() {
  return vi.fn(
    (_url: string | URL | Request, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => {
          reject(new DOMException("The operation was aborted.", "AbortError"));
        });
      }),
  );
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("apiFetch", () => {
  it("aborts the request after 30 seconds", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", abortableFetchMock());

    const request = apiFetch("/slow");
    const rejection = expect(request).rejects.toMatchObject({
      name: "AbortError",
    });
    await vi.advanceTimersByTimeAsync(30_000);
    await rejection;
  });

  it("clears the timeout timer once the request settles", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("{}", { status: 200 })),
    );

    await apiFetch("/ok");

    expect(vi.getTimerCount()).toBe(0);
  });

  it("respects a caller-supplied abort signal", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", abortableFetchMock());
    const caller = new AbortController();

    const request = apiFetch("/slow", { signal: caller.signal });
    caller.abort();

    await expect(request).rejects.toMatchObject({ name: "AbortError" });
  });
});
