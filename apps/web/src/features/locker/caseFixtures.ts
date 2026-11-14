import type {
  CaseEvent,
  CaseRecord,
  CaseSummary,
  PacketSnapshot,
} from "@/lib/locker";

export function packetSnapshot(
  overrides: Partial<PacketSnapshot> = {},
): PacketSnapshot {
  return {
    fields: [
      {
        id: "applicant_name",
        label: "Applicant name",
        value: "Asha Devi",
        origin: "profile",
      },
    ],
    evidence: [
      {
        group_id: "income_evidence",
        group_label: "Income evidence",
        documents: [{ document_id: "doc-1", filename: "income.txt" }],
      },
    ],
    declaration: { required: true, text: "I declare the information is true." },
    official_channel_steps: ["Register on the official portal."],
    processing_time: "Indicative only: around 14 days; not a guarantee",
    not_a_submission_notice: "Review only. RINAVI does not submit.",
    portal_down_guidance:
      "If the portal is unavailable, nothing here changes. Your packet stays in the locker.",
    acknowledgement_guidance:
      "No acknowledgement yet? Some portals send receipts later.",
    ...overrides,
  };
}

export function caseEvent(overrides: Partial<CaseEvent> = {}): CaseEvent {
  return {
    id: "event-1",
    type: "created",
    payload: {},
    created_at: "2026-11-13T00:00:00",
    ...overrides,
  };
}

export function caseRecord(overrides: Partial<CaseRecord> = {}): CaseRecord {
  return {
    id: "case-1",
    service_slug: "delhi-income-certificate",
    service_name: "Income Certificate (Delhi)",
    status: "prepared",
    reference_number: null,
    created_at: "2026-11-13T00:00:00",
    draft_id: "draft-1",
    pack_version: "1.0.0",
    acknowledgement_number: null,
    deadline_at: null,
    outcome_notes: null,
    updated_at: "2026-11-13T00:00:00",
    events: [caseEvent()],
    packet_snapshot: packetSnapshot(),
    ...overrides,
  };
}

export function caseSummary(overrides: Partial<CaseSummary> = {}): CaseSummary {
  return {
    id: "case-1",
    service_slug: "delhi-income-certificate",
    service_name: "Income Certificate (Delhi)",
    status: "prepared",
    reference_number: null,
    created_at: "2026-11-13T00:00:00",
    ...overrides,
  };
}
