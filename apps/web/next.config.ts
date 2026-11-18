import type { NextConfig } from "next";

// Mirrors the client default in src/lib/api.ts.
export const DEFAULT_API_URL = "http://localhost:8000";

export function buildCspPolicy(
  apiUrl: string,
  isDev = process.env.NODE_ENV === "development",
): string {
  return [
    "default-src 'self'",
    // The Next runtime hydrates with inline scripts and styles; without a
    // nonce middleware these sources must stay open. React also uses eval in
    // development to reconstruct server-side error stacks in the browser.
    `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    `connect-src 'self' ${apiUrl}`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
}

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "no-referrer" },
  {
    key: "Permissions-Policy",
    value: "geolocation=(), microphone=(), camera=()",
  },
  {
    key: "Content-Security-Policy",
    value: buildCspPolicy(
      process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL,
      process.env.NODE_ENV === "development",
    ),
  },
];

// HSTS only means something over https, so production gets it and local
// development does not.
if (process.env.NODE_ENV === "production") {
  securityHeaders.push({
    key: "Strict-Transport-Security",
    value: "max-age=31536000; includeSubDomains",
  });
}

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
