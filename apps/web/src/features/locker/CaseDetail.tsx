"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { SiteNav } from "@/components/SiteNav";
import {
  applyAgain,
  getCase,
  recordCaseEvent,
  type CaseEvent,
  type CaseEventInput,
  type CaseRecord,
} from "@/lib/locker";

import { STATUS_META } from "./statusMeta";

const SUGGESTED_LINKS_PREFIX = "rinavi:suggested-links:";

const UNCERTAIN_NOTICE =
  "Not sure whether it went through? Check the portal for your reference number before trying again — RINAVI cannot tell what happened on the portal.";

function eventLabel(event: CaseEvent): string {
  switch (event.type) {
    case "created":
      return "Application prepared";
    case "submitted": {
      const reference = (event.payload.reference_number as string | null) ?? null;
      return reference
        ? `Marked as submitted — reference ${reference}`
        : "Marked as submitted";
    }
    case "acknowledged": {
      const number =
        (event.payload.acknowledgement_number as string | null) ?? null;
      return number
        ? `Acknowledgement recorded — ${number}`
        : "Acknowledgement recorded";
    }
    case "outcome_received": {
      const notes = (event.payload.outcome_notes as string | null) ?? null;
      return notes ? `Outcome recorded — ${notes}` : "Outcome recorded";
    }
    case "deadline_updated": {
      const deadline = (event.payload.deadline_at as string | null) ?? null;
      return deadline ? `Deadline updated — ${deadline}` : "Deadline cleared";
    }
    case "abandoned":
      return "Marked as abandoned";
    case "uncertain":
      return "Marked as uncertain";
    default:
      return event.type;
  }
}

export function CaseDetail({ caseId }: { caseId: string }) {
  const router = useRouter();
  const [record, setRecord] = useState<CaseRecord | null>(null);
  const [reference, setReference] = useState("");
  const [acknowledgement, setAcknowledgement] = useState("");
  const [outcomeNotes, setOutcomeNotes] = useState("");
  const [deadline, setDeadline] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setRecord(await getCase(caseId));
      } catch {
        setError("Could not load the case.");
      }
    }
    void load();
  }, [caseId]);

  async function handleRecord(event: CaseEventInput) {
    if (record === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setRecord(await recordCaseEvent(record.id, event));
    } catch {
      setError("Could not record the update.");
    } finally {
      setBusy(false);
    }
  }

  async function handleApplyAgain() {
    if (record === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await applyAgain(record.id);
      window.sessionStorage.setItem(
        `${SUGGESTED_LINKS_PREFIX}${result.draft.id}`,
        JSON.stringify(result.suggested_links),
      );
      router.push(`/applications/${result.draft.id}`);
    } catch {
      setError("Could not start a new application.");
      setBusy(false);
    }
  }

  if (record === null) {
    return error ? (
      <p data-testid="case-error">{error}</p>
    ) : (
      <p data-testid="case-loading">Loading…</p>
    );
  }

  const meta = STATUS_META[record.status];
  const snapshot = record.packet_snapshot;
  const journal = [...record.events].reverse();

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <SiteNav />
      <header className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold">{record.service_name}</h1>
          <span
            data-testid="case-status-chip"
            className={`rounded-full px-3 py-1 text-xs ${meta.className}`}
          >
            {meta.label}
          </span>
        </div>
        <p className="text-xs text-neutral-500">
          Pack {record.pack_version} · Prepared{" "}
          {new Date(record.created_at).toLocaleDateString()}
        </p>
      </header>

      <section className="flex flex-col gap-2 rounded border border-neutral-200 p-4 text-sm">
        <p>
          <span className="font-medium">Reference number:</span>{" "}
          {record.reference_number ?? "Not recorded"}
        </p>
        <p>
          <span className="font-medium">Acknowledgement number:</span>{" "}
          {record.acknowledgement_number ?? "Not recorded"}
        </p>
        {record.status === "submitted" &&
        record.acknowledgement_number === null ? (
          <p data-testid="acknowledgement-note" className="text-neutral-600">
            {snapshot.acknowledgement_guidance}
          </p>
        ) : null}
        <p>
          <span className="font-medium">Deadline:</span>{" "}
          {record.deadline_at ?? "No deadline recorded"}
        </p>
        {record.outcome_notes ? (
          <p>
            <span className="font-medium">Outcome:</span> {record.outcome_notes}
          </p>
        ) : null}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Journal</h2>
        <ul data-testid="case-journal" className="flex flex-col gap-2">
          {journal.map((event) => (
            <li
              key={event.id}
              data-testid="case-event"
              className="rounded border border-neutral-200 p-3 text-sm"
            >
              <p>{eventLabel(event)}</p>
              <p className="text-xs text-neutral-500">
                {new Date(event.created_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="font-medium">Record an update</h2>

        <div className="flex flex-col gap-2 rounded border border-neutral-200 p-4">
          <label htmlFor="reference-input" className="text-sm">
            Reference number (optional)
          </label>
          <div className="flex gap-2">
            <input
              id="reference-input"
              value={reference}
              onChange={(event) => setReference(event.target.value)}
              className="min-w-0 flex-1 rounded border border-neutral-300 px-2 py-1 text-sm"
            />
            <button
              type="button"
              onClick={() =>
                void handleRecord({
                  type: "submitted",
                  reference_number: reference === "" ? null : reference,
                })
              }
              disabled={busy}
              className="rounded border border-neutral-300 px-3 py-1"
            >
              Mark as submitted
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-2 rounded border border-neutral-200 p-4">
          <label htmlFor="ack-input" className="text-sm">
            Acknowledgement number (optional)
          </label>
          <div className="flex gap-2">
            <input
              id="ack-input"
              value={acknowledgement}
              onChange={(event) => setAcknowledgement(event.target.value)}
              className="min-w-0 flex-1 rounded border border-neutral-300 px-2 py-1 text-sm"
            />
            <button
              type="button"
              onClick={() =>
                void handleRecord({
                  type: "acknowledged",
                  acknowledgement_number:
                    acknowledgement === "" ? null : acknowledgement,
                })
              }
              disabled={busy}
              className="rounded border border-neutral-300 px-3 py-1"
            >
              Mark as acknowledged
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-2 rounded border border-neutral-200 p-4">
          <label htmlFor="outcome-input" className="text-sm">
            Outcome notes
          </label>
          <textarea
            id="outcome-input"
            value={outcomeNotes}
            onChange={(event) => setOutcomeNotes(event.target.value)}
            rows={3}
            className="rounded border border-neutral-300 px-2 py-1 text-sm"
          />
          <button
            type="button"
            onClick={() =>
              void handleRecord({
                type: "outcome_received",
                outcome_notes: outcomeNotes === "" ? null : outcomeNotes,
              })
            }
            disabled={busy}
            className="self-start rounded border border-neutral-300 px-3 py-1"
          >
            Mark as outcome received
          </button>
        </div>

        <div className="flex flex-col gap-2 rounded border border-neutral-200 p-4">
          <label htmlFor="deadline-input" className="text-sm">
            Deadline
          </label>
          <div className="flex gap-2">
            <input
              id="deadline-input"
              type="date"
              value={deadline}
              onChange={(event) => setDeadline(event.target.value)}
              className="rounded border border-neutral-300 px-2 py-1 text-sm"
            />
            <button
              type="button"
              onClick={() =>
                void handleRecord({
                  type: "deadline_updated",
                  deadline_at: deadline === "" ? null : deadline,
                })
              }
              disabled={busy || deadline === ""}
              className="rounded border border-neutral-300 px-3 py-1"
            >
              Set deadline
            </button>
            <button
              type="button"
              onClick={() =>
                void handleRecord({ type: "deadline_updated", deadline_at: null })
              }
              disabled={busy}
              className="rounded border border-neutral-300 px-3 py-1"
            >
              Clear deadline
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-2 rounded border border-neutral-200 p-4">
          <p className="text-sm text-neutral-600">{UNCERTAIN_NOTICE}</p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void handleRecord({ type: "uncertain" })}
              disabled={busy}
              className="rounded border border-neutral-300 px-3 py-1"
            >
              Mark as uncertain
            </button>
            <button
              type="button"
              onClick={() => void handleRecord({ type: "abandoned" })}
              disabled={busy}
              className="rounded border border-neutral-300 px-3 py-1"
            >
              Mark as abandoned
            </button>
          </div>
        </div>

        {record.status === "submitted" ? (
          <p
            data-testid="portal-down-guidance"
            className="text-sm text-neutral-600"
          >
            {snapshot.portal_down_guidance}
          </p>
        ) : null}
      </section>

      {error ? <p data-testid="case-error">{error}</p> : null}

      <div className="flex gap-2">
        <Link
          data-testid="packet-link"
          href={`/locker/${record.id}/packet`}
          className="rounded border border-neutral-300 px-3 py-1 text-sm underline"
        >
          View packet
        </Link>
        <button
          type="button"
          data-testid="apply-again"
          onClick={() => void handleApplyAgain()}
          disabled={busy}
          className="rounded border border-neutral-300 px-3 py-1 text-sm"
        >
          Apply again
        </button>
      </div>

      <p className="text-sm text-neutral-600">{snapshot.not_a_submission_notice}</p>
    </div>
  );
}
