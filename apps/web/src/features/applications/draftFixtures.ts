import type { Draft } from "@/lib/applications";

export function draftRecord(overrides: Partial<Draft> = {}): Draft {
  return {
    id: "draft-1",
    service_slug: "delhi-income-certificate",
    service_name: "Income Certificate (Delhi)",
    pack_version: "1.0.0",
    template_snapshot: {
      fields: [
        {
          id: "applicant_name",
          label: "Applicant name",
          binding: "full_name",
          required: true,
          format: "text",
        },
        {
          id: "purpose",
          label: "Purpose of certificate",
          binding: null,
          required: true,
          format: "text",
        },
      ],
      declaration: {
        required: true,
        text: "I declare the information is true.",
      },
      checklist_groups: [
        {
          id: "income_evidence",
          label: "Income evidence",
          requirement: "at_least_one",
          accepted_classifications: ["income"],
        },
      ],
      guidance: {
        official_channel_steps: ["Register on the official portal."],
        not_a_submission_notice:
          "RINAVI prepares this draft for your review only.",
      },
    },
    values: {
      applicant_name: { value: "Asha Devi", origin: "profile" },
    },
    document_links: {},
    declaration_confirmed: false,
    validation: [],
    created_at: "2026-11-12T00:00:00",
    updated_at: "2026-11-12T00:00:00",
    ...overrides,
  };
}
