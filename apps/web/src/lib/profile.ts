import { apiFetch } from "./api";

export type ProfileValue = {
  id: string;
  field_key: string;
  value: string;
  status: "unconfirmed" | "confirmed" | "stale";
  source_document_id: string | null;
  source_locator: string | null;
  confidence: string | null;
  stale_reason: string | null;
  correction_history: Array<{ old_value: string; corrected_at: string }>;
  updated_at: string;
};

export const PROFILE_PURPOSE = "profile.storage";

/**
 * Formatting for the profile fields whose stored value is normalised rather
 * than prose. Gender is stored lowercase by extraction and the backend tests
 * assert that, so only the rendered text is capitalised here.
 */
export function formatProfileValue(fieldKey: string, value: string): string {
  if (fieldKey !== "gender") {
    return value;
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function listProfileValues(): Promise<ProfileValue[]> {
  return apiFetch<ProfileValue[]>("/api/v1/profile/values");
}

export function promoteDocument(documentId: string): Promise<ProfileValue[]> {
  return apiFetch<ProfileValue[]>("/api/v1/profile/values/promote", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId }),
  });
}

export function confirmValue(id: string): Promise<ProfileValue> {
  return apiFetch<ProfileValue>(`/api/v1/profile/values/${id}/confirm`, {
    method: "POST",
  });
}

export function correctValue(id: string, value: string): Promise<ProfileValue> {
  return apiFetch<ProfileValue>(`/api/v1/profile/values/${id}/correct`, {
    method: "POST",
    body: JSON.stringify({ value }),
  });
}

export function rejectValue(id: string): Promise<void> {
  return apiFetch<void>(`/api/v1/profile/values/${id}/reject`, {
    method: "POST",
  });
}
