import { apiFetch } from "./api";

export type ServiceSummary = {
  slug: string;
  name: string;
  geography: string;
  department: string;
  latest_version: string;
  summary: string;
  fee: string;
  processing_time: string;
};

export type CatalogField = {
  id: string;
  label: string;
  binding: string | null;
  required: boolean;
  format: string;
};

export type CatalogChecklistGroup = {
  id: string;
  label: string;
  requirement: string;
  accepted_classifications: string[];
};

export type ServiceDetail = ServiceSummary & {
  tags: string[];
  sources: { title: string; url: string }[];
  guidance: {
    what_it_is: string;
    official_channel_steps: string[];
    not_a_submission_notice: string;
  };
  checklist_groups: CatalogChecklistGroup[];
  fields: CatalogField[];
  declaration: { required: boolean; text: string };
};

export function listServices(): Promise<ServiceSummary[]> {
  return apiFetch<ServiceSummary[]>("/api/v1/catalog/services");
}

export function getService(slug: string): Promise<ServiceDetail> {
  return apiFetch<ServiceDetail>(`/api/v1/catalog/services/${slug}`);
}
