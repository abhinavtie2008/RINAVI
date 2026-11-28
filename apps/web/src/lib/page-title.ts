"use client";

import { useEffect } from "react";

export const APP_NAME = "RINAVI";

/**
 * Builds the same "subject · section · RINAVI" shape that the root layout's
 * title template produces for server-rendered pages, so a page does not change
 * shape depending on whether its data loads on the server or in the browser.
 */
export function pageTitle(
  subject: string | null | undefined,
  section?: string | null,
): string {
  const parts = [subject, section]
    .map((part) => part?.trim() ?? "")
    .filter((part) => part.length > 0);
  return [...parts, APP_NAME].join(" · ");
}

/**
 * Sets the document title for pages whose subject (a service name, a case
 * reference) is only known after the browser fetches it.
 */
export function usePageTitle(
  subject: string | null | undefined,
  section?: string | null,
): void {
  const title = pageTitle(subject, section);
  useEffect(() => {
    document.title = title;
  }, [title]);
}
