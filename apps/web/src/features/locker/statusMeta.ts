import type { CaseStatus } from "@/lib/locker";

export const STATUS_META: Record<CaseStatus, { label: string; className: string }> = {
  prepared: { label: "Prepared", className: "bg-neutral-100 text-neutral-700" },
  submitted: { label: "Submitted", className: "bg-blue-100 text-blue-800" },
  acknowledged: { label: "Acknowledged", className: "bg-green-100 text-green-800" },
  outcome_received: {
    label: "Outcome received",
    className: "bg-green-100 text-green-900",
  },
  abandoned: { label: "Abandoned", className: "bg-neutral-200 text-neutral-600" },
  uncertain: { label: "Uncertain", className: "bg-amber-100 text-amber-800" },
};
