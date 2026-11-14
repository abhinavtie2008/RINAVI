import { apiFetch } from "./api";
import type { Draft } from "./applications";

export const LOCKER_PURPOSE = "locker.tracking";

export type CaseStatus =
  | "prepared"
  | "submitted"
  | "acknowledged"
  | "outcome_received"
  | "abandoned"
  | "uncertain";

export type CaseEvent = {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type PacketSnapshot = {
  fields: { id: string; label: string; value: string; origin: string }[];
  evidence: {
    group_id: string;
    group_label: string;
    documents: { document_id: string; filename: string }[];
  }[];
  declaration: { required: boolean; text: string };
  official_channel_steps: string[];
  processing_time: string | null;
  not_a_submission_notice: string;
  portal_down_guidance: string;
  acknowledgement_guidance: string;
};

export type CaseSummary = {
  id: string;
  service_slug: string;
  service_name: string;
  status: CaseStatus;
  reference_number: string | null;
  created_at: string;
};

export type CaseRecord = CaseSummary & {
  draft_id: string | null;
  pack_version: string;
  acknowledgement_number: string | null;
  deadline_at: string | null;
  outcome_notes: string | null;
  updated_at: string;
  events: CaseEvent[];
  packet_snapshot: PacketSnapshot;
};

export type CaseEventInput =
  | { type: "submitted"; reference_number: string | null }
  | { type: "acknowledged"; acknowledgement_number: string | null }
  | { type: "outcome_received"; outcome_notes: string | null }
  | { type: "abandoned" }
  | { type: "uncertain" }
  | { type: "deadline_updated"; deadline_at: string | null };

export type SuggestedLink = { document_id: string; group_id: string };

export type ApplyAgainResult = { draft: Draft; suggested_links: SuggestedLink[] };

export function listCases(): Promise<CaseSummary[]> {
  return apiFetch<CaseSummary[]>("/api/v1/locker/cases");
}

export function getCase(id: string): Promise<CaseRecord> {
  return apiFetch<CaseRecord>(`/api/v1/locker/cases/${id}`);
}

export function recordCaseEvent(
  id: string,
  event: CaseEventInput,
): Promise<CaseRecord> {
  return apiFetch<CaseRecord>(`/api/v1/locker/cases/${id}/events`, {
    method: "POST",
    body: JSON.stringify(event),
  });
}

export function applyAgain(id: string): Promise<ApplyAgainResult> {
  return apiFetch<ApplyAgainResult>(`/api/v1/locker/cases/${id}/apply-again`, {
    method: "POST",
  });
}

export function completeDraft(id: string): Promise<CaseRecord> {
  return apiFetch<CaseRecord>(`/api/v1/applications/drafts/${id}/complete`, {
    method: "POST",
  });
}
