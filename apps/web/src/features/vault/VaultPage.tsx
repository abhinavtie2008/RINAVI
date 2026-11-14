"use client";

import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";

import { ApiError } from "@/lib/api";
import {
  DOCUMENTS_PURPOSE,
  deleteDocument,
  grantConsent,
  hasActiveGrant,
  listDocuments,
  listGrants,
  uploadDocument,
  type DocumentRecord,
} from "@/lib/vault";

const STATUS_LABELS: Record<string, string> = {
  quarantined: "Queued",
  processing: "Processing",
  processed: "Ready",
  needs_attention: "Needs attention",
  rejected: "Rejected",
};

export function VaultPage() {
  const [ready, setReady] = useState(false);
  const [consentGranted, setConsentGranted] = useState(false);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const grants = await listGrants();
        const granted = hasActiveGrant(grants, DOCUMENTS_PURPOSE);
        setConsentGranted(granted);
        if (granted) {
          setDocuments(await listDocuments());
        }
      } catch {
        setError("Could not load your vault. Sign in and try again.");
      } finally {
        setReady(true);
      }
    }
    void load();
  }, []);

  async function handleGrant() {
    setBusy(true);
    setError(null);
    try {
      await grantConsent(DOCUMENTS_PURPOSE);
      setConsentGranted(true);
      setDocuments(await listDocuments());
    } catch {
      setError("Could not record consent.");
    } finally {
      setBusy(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (file === null) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const document = await uploadDocument(file);
      setDocuments((current) => [document, ...current]);
      setFile(null);
    } catch (uploadError) {
      if (uploadError instanceof ApiError && uploadError.status === 403) {
        setConsentGranted(false);
      } else if (uploadError instanceof ApiError && uploadError.status === 413) {
        setError("That file is larger than 10 MB.");
      } else if (uploadError instanceof ApiError && uploadError.status === 415) {
        setError("Supported types: PDF, PNG, JPEG, TXT.");
      } else {
        setError("Upload failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this document? This cannot be undone.")) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await deleteDocument(id);
      setDocuments((current) => current.filter((d) => d.id !== id));
    } catch {
      setError("Could not delete the document.");
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p data-testid="vault-loading">Loading…</p>;
  }

  if (!consentGranted) {
    return (
      <section
        data-testid="consent-gate"
        className="flex w-full max-w-md flex-col gap-3 rounded border border-neutral-200 px-4 py-6"
      >
        <p className="text-sm">
          RINAVI processes your documents only after you allow it. Nothing is
          uploaded until then, and you can delete anything at any time.
        </p>
        <button
          type="button"
          onClick={() => void handleGrant()}
          disabled={busy}
          className="rounded border border-neutral-300 px-3 py-1"
        >
          Allow document processing
        </button>
        {error ? <p data-testid="vault-error">{error}</p> : null}
      </section>
    );
  }

  return (
    <div className="flex w-full max-w-md flex-col gap-6">
      <form onSubmit={handleUpload} className="flex flex-col gap-2">
        <label htmlFor="document-file" className="text-sm">
          Document file
        </label>
        <input
          id="document-file"
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.txt"
          onChange={handleFileChange}
          className="text-sm"
        />
        <button
          type="submit"
          disabled={busy || file === null}
          className="rounded border border-neutral-300 px-3 py-1"
        >
          Upload document
        </button>
      </form>

      {documents.length === 0 ? (
        <p data-testid="vault-empty" className="text-sm text-neutral-600">
          No documents yet.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {documents.map((document) => (
            <li
              key={document.id}
              data-testid="document-row"
              className="flex items-center justify-between gap-4 rounded border border-neutral-200 px-4 py-2"
            >
              <div>
                <p className="font-medium">{document.original_filename}</p>
                <p className="text-xs text-neutral-500">
                  {STATUS_LABELS[document.status] ?? document.status}
                  {document.note ? ` — ${document.note}` : ""}
                </p>
              </div>
              <button
                type="button"
                onClick={() => void handleDelete(document.id)}
                disabled={busy}
                className="rounded border border-neutral-300 px-3 py-1"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}

      {error ? <p data-testid="vault-error">{error}</p> : null}
    </div>
  );
}
