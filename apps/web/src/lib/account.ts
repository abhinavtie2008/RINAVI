import { apiFetch } from "./api";
import type { ConsentRecord } from "./vault";

export type AccountUser = {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
};

// The server decides what an export contains (identity/schemas.py::AccountExport):
// the account and its permission history, not the documents or profile values.
export type AccountExport = {
  user: AccountUser;
  consent_records: ConsentRecord[];
};

export function fetchAccount(): Promise<AccountUser> {
  return apiFetch<AccountUser>("/api/v1/auth/me");
}

export function exportAccount(): Promise<AccountExport> {
  return apiFetch<AccountExport>("/api/v1/auth/export");
}

export function deleteAccount(): Promise<void> {
  return apiFetch<void>("/api/v1/auth/account", { method: "DELETE" });
}

// The JSON is fetched first and handed to an object URL, rather than linking
// straight at the endpoint: a rate-limited or failed export then surfaces as a
// message in the page instead of rendering the error body as a downloaded file.
export function downloadJson(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
