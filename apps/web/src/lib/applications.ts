import { apiFetch } from "./api";

export const APPLICATIONS_PURPOSE = "applications.preparation";

export type DraftValue = { value: string; origin: "profile" | "citizen" };
export type ValidationIssue = {
  code: string;
  field_id: string | null;
  group_id: string | null;
  document_id: string | null;
  message: string;
};
export type Draft = {
  id: string;
  service_slug: string;
  service_name: string;
  pack_version: string;
  template_snapshot: {
    fields: {
      id: string;
      label: string;
      binding: string | null;
      required: boolean;
      format: string;
    }[];
    declaration: { required: boolean; text: string };
    checklist_groups: {
      id: string;
      label: string;
      requirement: string;
      accepted_classifications: string[];
    }[];
    guidance: {
      official_channel_steps: string[];
      not_a_submission_notice: string;
    };
  };
  values: Record<string, DraftValue>;
  document_links: Record<string, string[]>;
  declaration_confirmed: boolean;
  validation: ValidationIssue[];
  created_at: string;
  updated_at: string;
};

export function listDrafts(): Promise<Draft[]> {
  return apiFetch<Draft[]>("/api/v1/applications/drafts");
}

export function createDraft(serviceSlug: string): Promise<Draft> {
  return apiFetch<Draft>("/api/v1/applications/drafts", {
    method: "POST",
    body: JSON.stringify({ service_slug: serviceSlug }),
  });
}

export function getDraft(id: string): Promise<Draft> {
  return apiFetch<Draft>(`/api/v1/applications/drafts/${id}`);
}

export function updateField(
  id: string,
  fieldId: string,
  value: string,
): Promise<Draft> {
  return apiFetch<Draft>(
    `/api/v1/applications/drafts/${id}/fields/${fieldId}`,
    { method: "PUT", body: JSON.stringify({ value }) },
  );
}

export function refreshDraft(id: string): Promise<Draft> {
  return apiFetch<Draft>(`/api/v1/applications/drafts/${id}/refresh`, {
    method: "POST",
  });
}

export function linkDocument(
  id: string,
  documentId: string,
  groupId: string,
): Promise<Draft> {
  return apiFetch<Draft>(
    `/api/v1/applications/drafts/${id}/documents/${documentId}`,
    { method: "PUT", body: JSON.stringify({ group_id: groupId }) },
  );
}

export function unlinkDocument(id: string, documentId: string): Promise<Draft> {
  return apiFetch<Draft>(
    `/api/v1/applications/drafts/${id}/documents/${documentId}`,
    { method: "DELETE" },
  );
}

export function setDeclaration(id: string, confirmed: boolean): Promise<Draft> {
  return apiFetch<Draft>(`/api/v1/applications/drafts/${id}/declaration`, {
    method: "PUT",
    body: JSON.stringify({ confirmed }),
  });
}

export function exportDraft(id: string): Promise<{ text: string }> {
  return apiFetch<{ text: string }>(`/api/v1/applications/drafts/${id}/export`);
}

export function deleteDraft(id: string): Promise<void> {
  return apiFetch<void>(`/api/v1/applications/drafts/${id}`, {
    method: "DELETE",
  });
}
