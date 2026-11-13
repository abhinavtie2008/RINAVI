"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import {
  deleteDraft,
  exportDraft,
  getDraft,
  linkDocument,
  refreshDraft,
  setDeclaration,
  unlinkDocument,
  updateField,
  type Draft,
} from "@/lib/applications";
import { listDocuments, type DocumentRecord } from "@/lib/vault";

export function DraftDetail({ draftId }: { draftId: string }) {
  const router = useRouter();
  const [draft, setDraft] = useState<Draft | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [drafting, setDrafting] = useState<Record<string, string>>({});
  const [linkPicks, setLinkPicks] = useState<Record<string, string>>({});
  const [exportText, setExportText] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [loadedDraft, loadedDocuments] = await Promise.all([
          getDraft(draftId),
          listDocuments(),
        ]);
        setDraft(loadedDraft);
        setDocuments(loadedDocuments);
      } catch {
        setError("Could not load the draft.");
      }
    }
    void load();
  }, [draftId]);

  function applyDraft(updated: Draft) {
    setDraft(updated);
    setExportText(null);
  }

  async function handleSave(fieldId: string) {
    if (draft === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const value = drafting[fieldId] ?? draft.values[fieldId]?.value ?? "";
      applyDraft(await updateField(draft.id, fieldId, value));
      setDrafting((current) => {
        const next = { ...current };
        delete next[fieldId];
        return next;
      });
    } catch {
      setError("Could not save the field.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRefresh() {
    if (draft === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      applyDraft(await refreshDraft(draft.id));
      setDrafting({});
    } catch {
      setError("Could not refresh profile values.");
    } finally {
      setBusy(false);
    }
  }

  async function handleLink(groupId: string) {
    const documentId = linkPicks[groupId];
    if (draft === null || !documentId) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      applyDraft(await linkDocument(draft.id, documentId, groupId));
      setLinkPicks((current) => ({ ...current, [groupId]: "" }));
    } catch (linkError) {
      if (linkError instanceof ApiError && linkError.status === 422) {
        setError("That document cannot be attached to this group.");
      } else {
        setError("Could not attach the document.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleUnlink(documentId: string) {
    if (draft === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      applyDraft(await unlinkDocument(draft.id, documentId));
    } catch {
      setError("Could not remove the document.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDeclaration(confirmed: boolean) {
    if (draft === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      applyDraft(await setDeclaration(draft.id, confirmed));
    } catch {
      setError("Could not update the declaration.");
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    if (draft === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await exportDraft(draft.id);
      setExportText(result.text);
    } catch (exportError) {
      if (exportError instanceof ApiError && exportError.status === 409) {
        setError("Resolve the highlighted issues first.");
      } else {
        setError("Could not preview the draft.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (draft === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await deleteDraft(draft.id);
      router.push("/applications");
    } catch {
      setError("Could not delete the draft.");
      setBusy(false);
    }
  }

  if (draft === null) {
    return error ? (
      <p data-testid="draft-error">{error}</p>
    ) : (
      <p data-testid="draft-loading">Loading…</p>
    );
  }

  const globalIssues = draft.validation.filter(
    (issue) => issue.field_id === null && issue.group_id === null,
  );
  const processedDocuments = documents.filter(
    (document) => document.status === "processed",
  );

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <header className="flex flex-col gap-2">
        <div>
          <h1 className="text-xl font-semibold">{draft.service_name}</h1>
          <p className="text-xs text-neutral-500">Pack {draft.pack_version}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void handleRefresh()}
            disabled={busy}
            className="rounded border border-neutral-300 px-3 py-1"
          >
            Refresh from profile
          </button>
          <button
            type="button"
            onClick={() => void handleDelete()}
            disabled={busy}
            className="rounded border border-neutral-300 px-3 py-1"
          >
            Delete draft
          </button>
        </div>
      </header>

      <p
        data-testid="submission-notice"
        className="rounded border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950"
      >
        {draft.template_snapshot.guidance.not_a_submission_notice}
      </p>

      <section className="flex flex-col gap-4" aria-label="Application fields">
        {draft.template_snapshot.fields.map((field) => {
          const entry = draft.values[field.id];
          const fromProfile = entry?.origin === "profile";
          const value = drafting[field.id] ?? entry?.value ?? "";
          const fieldIssues = draft.validation.filter(
            (issue) => issue.field_id === field.id,
          );
          return (
            <div key={field.id} className="flex flex-col gap-1">
              <label htmlFor={`field-${field.id}`} className="text-sm">
                {field.label}
                {field.required ? " *" : ""}
              </label>
              <div className="flex gap-2">
                <input
                  id={`field-${field.id}`}
                  value={value}
                  disabled={fromProfile || busy}
                  onChange={(event) =>
                    setDrafting((current) => ({
                      ...current,
                      [field.id]: event.target.value,
                    }))
                  }
                  className="min-w-0 flex-1 rounded border border-neutral-300 px-2 py-1"
                />
                {fromProfile ? (
                  <span className="self-center text-xs text-neutral-500">
                    From your profile
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => void handleSave(field.id)}
                    disabled={busy}
                    className="rounded border border-neutral-300 px-3 py-1"
                  >
                    Save
                  </button>
                )}
              </div>
              {fieldIssues.map((issue, index) => (
                <p
                  key={`${issue.code}-${index}`}
                  className="text-sm text-red-700"
                >
                  {issue.message}
                </p>
              ))}
            </div>
          );
        })}
      </section>

      <section className="flex flex-col gap-4" aria-label="Evidence checklist">
        <h2 className="font-medium">Evidence checklist</h2>
        {draft.template_snapshot.checklist_groups.map((group) => {
          const linkedIds = draft.document_links[group.id] ?? [];
          const groupIssues = draft.validation.filter(
            (issue) => issue.group_id === group.id,
          );
          return (
            <section
              key={group.id}
              className="flex flex-col gap-2 rounded border border-neutral-200 p-4"
            >
              <h3 className="text-sm font-medium">{group.label}</h3>
              {linkedIds.length > 0 ? (
                <ul className="flex flex-col gap-1">
                  {linkedIds.map((documentId) => {
                    const document = documents.find(
                      (candidate) => candidate.id === documentId,
                    );
                    return (
                      <li key={documentId} className="flex items-center gap-2">
                        <span className="flex-1 text-sm">
                          {document?.original_filename ?? "Unavailable document"}
                        </span>
                        <button
                          type="button"
                          onClick={() => void handleUnlink(documentId)}
                          disabled={busy}
                          className="rounded border border-neutral-300 px-3 py-1"
                        >
                          Remove
                        </button>
                      </li>
                    );
                  })}
                </ul>
              ) : null}
              <label htmlFor={`attach-${group.id}`} className="text-sm">
                Attach document to {group.label}
              </label>
              <div className="flex gap-2">
                <select
                  id={`attach-${group.id}`}
                  value={linkPicks[group.id] ?? ""}
                  onChange={(event) =>
                    setLinkPicks((current) => ({
                      ...current,
                      [group.id]: event.target.value,
                    }))
                  }
                  className="min-w-0 flex-1 rounded border border-neutral-300 px-2 py-1 text-sm"
                >
                  <option value="">Choose a document…</option>
                  {processedDocuments.map((document) => (
                    <option key={document.id} value={document.id}>
                      {document.original_filename}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => void handleLink(group.id)}
                  disabled={busy || !linkPicks[group.id]}
                  className="rounded border border-neutral-300 px-3 py-1"
                >
                  Attach
                </button>
              </div>
              {groupIssues.map((issue, index) => (
                <p
                  key={`${issue.code}-${issue.document_id ?? "group"}-${index}`}
                  className="text-sm text-red-700"
                >
                  {issue.message}
                </p>
              ))}
            </section>
          );
        })}
      </section>

      <div className="flex items-start gap-2">
        <input
          id="declaration"
          type="checkbox"
          checked={draft.declaration_confirmed}
          disabled={busy}
          onChange={(event) => void handleDeclaration(event.target.checked)}
        />
        <label htmlFor="declaration" className="text-sm">
          {draft.template_snapshot.declaration.text}
        </label>
      </div>

      <div data-testid="validation-issues" className="flex flex-col gap-1">
        {globalIssues.map((issue, index) => (
          <p key={`${issue.code}-${index}`} className="text-sm text-red-700">
            {issue.message}
          </p>
        ))}
      </div>

      {error ? <p data-testid="draft-error">{error}</p> : null}

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Official submission steps</h2>
        <ol className="list-decimal pl-5 text-sm">
          {draft.template_snapshot.guidance.official_channel_steps.map(
            (step) => (
              <li key={step}>{step}</li>
            ),
          )}
        </ol>
      </section>

      <button
        type="button"
        onClick={() => void handleExport()}
        disabled={busy}
        className="self-start rounded border border-neutral-300 px-3 py-1"
      >
        Preview final draft
      </button>
      {exportText !== null ? (
        <pre
          data-testid="export-text"
          className="overflow-x-auto whitespace-pre-wrap rounded border border-neutral-200 p-4 text-sm"
        >
          {exportText}
        </pre>
      ) : null}
    </div>
  );
}
