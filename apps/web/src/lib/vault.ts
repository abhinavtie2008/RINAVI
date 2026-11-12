import { apiFetch, apiUpload } from "./api";

export type DocumentStatus =
  | "quarantined"
  | "processing"
  | "processed"
  | "needs_attention"
  | "rejected";

export type DocumentRecord = {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  classification: string | null;
  note: string | null;
  created_at: string;
  processed_at: string | null;
};

export type ConsentRecord = {
  id: string;
  purpose: string;
  policy_version: string;
  granted_at: string;
  withdrawn_at: string | null;
};

export const DOCUMENTS_PURPOSE = "documents.processing";

export function listDocuments(): Promise<DocumentRecord[]> {
  return apiFetch<DocumentRecord[]>("/api/v1/vault/documents");
}

export function uploadDocument(file: File): Promise<DocumentRecord> {
  const form = new FormData();
  form.append("file", file);
  return apiUpload<DocumentRecord>("/api/v1/vault/documents", form);
}

export function deleteDocument(id: string): Promise<void> {
  return apiFetch<void>(`/api/v1/vault/documents/${id}`, { method: "DELETE" });
}

export function listGrants(): Promise<ConsentRecord[]> {
  return apiFetch<ConsentRecord[]>("/api/v1/consent/grants");
}

export function grantConsent(purpose: string): Promise<ConsentRecord> {
  return apiFetch<ConsentRecord>("/api/v1/consent/grants", {
    method: "POST",
    body: JSON.stringify({ purpose }),
  });
}

export function hasActiveGrant(
  grants: ConsentRecord[],
  purpose: string
): boolean {
  return grants.some((g) => g.purpose === purpose && g.withdrawn_at === null);
}
