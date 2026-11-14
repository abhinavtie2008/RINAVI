"use client";

import { useEffect, useState } from "react";

import { SiteNav } from "@/components/SiteNav";
import { getCase, type CaseRecord } from "@/lib/locker";

export function PacketPage({ caseId }: { caseId: string }) {
  const [record, setRecord] = useState<CaseRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setRecord(await getCase(caseId));
      } catch {
        setError("Could not load the packet.");
      }
    }
    void load();
  }, [caseId]);

  if (record === null) {
    return error ? (
      <p data-testid="packet-error">{error}</p>
    ) : (
      <p data-testid="packet-loading">Loading…</p>
    );
  }

  const snapshot = record.packet_snapshot;

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <div className="print:hidden">
        <SiteNav />
      </div>
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold">{record.service_name}</h1>
        <p className="text-xs text-neutral-500">
          Pack {record.pack_version} · Prepared{" "}
          {new Date(record.created_at).toLocaleDateString()}
        </p>
      </header>

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Application fields</h2>
        <ul className="flex flex-col gap-1 text-sm">
          {snapshot.fields.map((field) => (
            <li key={field.id}>
              <span className="font-medium">{field.label}:</span> {field.value}{" "}
              <span className="text-neutral-500">
                ({field.origin === "profile" ? "from your profile" : "entered by you"})
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Evidence</h2>
        {snapshot.evidence.map((group) => (
          <div key={group.group_id} className="text-sm">
            <p className="font-medium">{group.group_label}</p>
            {group.documents.length === 0 ? (
              <p className="text-neutral-500">No documents attached.</p>
            ) : (
              <ul className="list-disc pl-5">
                {group.documents.map((document) => (
                  <li key={document.document_id}>{document.filename}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Declaration</h2>
        <p className="text-sm">{snapshot.declaration.text}</p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Official channel steps</h2>
        <ol className="list-decimal pl-5 text-sm">
          {snapshot.official_channel_steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>

      {snapshot.processing_time ? (
        <p className="text-sm text-neutral-600">{snapshot.processing_time}</p>
      ) : null}

      <p className="rounded border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950">
        {snapshot.not_a_submission_notice}
      </p>
      <p className="text-sm text-neutral-600">{snapshot.portal_down_guidance}</p>
      <p className="text-sm text-neutral-600">
        {snapshot.acknowledgement_guidance}
      </p>

      <button
        type="button"
        data-testid="packet-print"
        onClick={() => window.print()}
        className="self-start rounded border border-neutral-300 px-3 py-1 print:hidden"
      >
        Print packet
      </button>
    </div>
  );
}
