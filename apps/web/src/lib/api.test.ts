import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch, apiUpload } from "./api";

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

  it("surfaces the API's detail string instead of a bare status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Draft has unresolved issues" }), {
          status: 409,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(apiFetch("/applications/drafts/1/export")).rejects.toMatchObject({
      name: "ApiError",
      status: 409,
      message: "Draft has unresolved issues",
    });
  });

  it("joins FastAPI validation messages", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: [{ msg: "Field required" }, { msg: "String too long" }],
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(apiFetch("/consent/grants", { method: "POST" })).rejects.toMatchObject(
      { status: 422, message: "Field required; String too long" },
    );
  });

  it("falls back to the status when the error body is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("<html>gateway</html>", { status: 502 })),
    );

    await expect(apiFetch("/health")).rejects.toMatchObject({
      status: 502,
      message: "API request failed: 502",
    });
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

describe("apiUpload", () => {
  it("aborts the upload after 120 seconds", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", abortableFetchMock());

    const request = apiUpload("/vault/documents", new FormData());
    const rejection = expect(request).rejects.toMatchObject({
      name: "AbortError",
    });
    await vi.advanceTimersByTimeAsync(120_000);
    await rejection;
  });

  it("clears the upload timeout timer once the request settles", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("{}", { status: 200 })),
    );

    await apiUpload("/vault/documents", new FormData());

    expect(vi.getTimerCount()).toBe(0);
  });
});
