import { describe, expect, it } from "vitest";

import nextConfig, { buildCspPolicy } from "../../next.config";

const DEFAULT_POLICY =
  "default-src 'self'; script-src 'self' 'unsafe-inline'; " +
  "style-src 'self' 'unsafe-inline'; img-src 'self' data:; " +
  "connect-src 'self' http://localhost:8000; frame-ancestors 'none'; " +
  "base-uri 'self'; form-action 'self'";

describe("buildCspPolicy", () => {
  it("assembles the static policy", () => {
    expect(buildCspPolicy("http://localhost:8000")).toBe(DEFAULT_POLICY);
  });

  it("puts the configured API origin in connect-src", () => {
    const policy = buildCspPolicy("https://api.example.in");

    expect(policy).toContain("connect-src 'self' https://api.example.in");
    expect(policy).not.toContain("http://localhost:8000");
  });
});

describe("next.config headers", () => {
  it("attaches the CSP header to every route", async () => {
    const entries = await nextConfig.headers?.();
    const headers = (entries ?? []).flatMap((entry) => entry.headers);
    const csp = headers.find(
      (header) => header.key === "Content-Security-Policy",
    );

    expect(csp?.value).toBe(DEFAULT_POLICY);
  });
});
