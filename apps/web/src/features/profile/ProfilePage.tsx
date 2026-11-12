"use client";

import { useEffect, useState, type FormEvent } from "react";

import {
  PROFILE_PURPOSE,
  confirmValue,
  correctValue,
  listProfileValues,
  promoteDocument,
  rejectValue,
  type ProfileValue,
} from "@/lib/profile";
import {
  grantConsent,
  hasActiveGrant,
  listDocuments,
  listGrants,
  type DocumentRecord,
} from "@/lib/vault";

const FIELD_LABELS: Record<string, string> = {
  full_name: "Full name",
  father_name: "Father's name",
  date_of_birth: "Date of birth",
  gender: "Gender",
  address: "Address",
  annual_income: "Annual income",
  aadhaar_number: "Aadhaar number",
};

function fieldLabel(fieldKey: string): string {
  return FIELD_LABELS[fieldKey] ?? fieldKey;
}

export function ProfilePage() {
  const [ready, setReady] = useState(false);
  const [consentGranted, setConsentGranted] = useState(false);
  const [values, setValues] = useState<ProfileValue[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [correctingId, setCorrectingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const grants = await listGrants();
        const granted = hasActiveGrant(grants, PROFILE_PURPOSE);
        setConsentGranted(granted);
        if (granted) {
          const [loadedValues, loadedDocuments] = await Promise.all([
            listProfileValues(),
            listDocuments(),
          ]);
          setValues(loadedValues);
          setDocuments(loadedDocuments.filter((d) => d.status === "processed"));
        }
      } catch {
        setError("Could not load your profile. Sign in and try again.");
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
      await grantConsent(PROFILE_PURPOSE);
      setConsentGranted(true);
      const [loadedValues, loadedDocuments] = await Promise.all([
        listProfileValues(),
        listDocuments(),
      ]);
      setValues(loadedValues);
      setDocuments(loadedDocuments.filter((d) => d.status === "processed"));
    } catch {
      setError("Could not record consent.");
    } finally {
      setBusy(false);
    }
  }

  function replaceValue(updated: ProfileValue) {
    setValues((current) =>
      current.map((value) => (value.id === updated.id ? updated : value))
    );
  }

  async function handlePromote(documentId: string) {
    setBusy(true);
    setError(null);
    try {
      setValues(await promoteDocument(documentId));
    } catch {
      setError("Could not add values from that document.");
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm(id: string) {
    setBusy(true);
    setError(null);
    try {
      replaceValue(await confirmValue(id));
    } catch {
      setError("Could not confirm the value.");
    } finally {
      setBusy(false);
    }
  }

  function startCorrection(value: ProfileValue) {
    setCorrectingId(value.id);
    setDraft(value.value);
  }

  async function handleCorrect(event: FormEvent, id: string) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      replaceValue(await correctValue(id, draft));
      setCorrectingId(null);
    } catch {
      setError("Could not save the correction.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReject(id: string) {
    setBusy(true);
    setError(null);
    try {
      await rejectValue(id);
      setValues((current) => current.filter((value) => value.id !== id));
    } catch {
      setError("Could not remove the value.");
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p data-testid="profile-loading">Loading…</p>;
  }

  if (!consentGranted) {
    return (
      <section
        data-testid="profile-consent-gate"
        className="flex w-full max-w-md flex-col gap-3 rounded border border-neutral-200 px-4 py-6"
      >
        <p className="text-sm">
          Your profile is stored only after you allow it. Values stay marked as
          under review until you confirm or correct them.
        </p>
        <button
          type="button"
          onClick={() => void handleGrant()}
          disabled={busy}
          className="rounded border border-neutral-300 px-3 py-1"
        >
          Allow profile storage
        </button>
        {error ? <p data-testid="profile-error">{error}</p> : null}
      </section>
    );
  }

  return (
    <div className="flex w-full max-w-md flex-col gap-6">
      {documents.length > 0 ? (
        <section data-testid="promote-section" className="flex flex-col gap-2">
          <h2 className="text-sm font-medium">Add values from a document</h2>
          <ul className="flex flex-col gap-1">
            {documents.map((document) => (
              <li
                key={document.id}
                className="flex items-center justify-between gap-4 rounded border border-neutral-200 px-4 py-2"
              >
                <span className="text-sm">{document.original_filename}</span>
                <button
                  type="button"
                  onClick={() => void handlePromote(document.id)}
                  disabled={busy}
                  className="rounded border border-neutral-300 px-3 py-1"
                >
                  Use this document
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {values.length === 0 ? (
        <p data-testid="profile-empty" className="text-sm text-neutral-600">
          No profile values yet.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {values.map((value) => (
            <li
              key={value.id}
              data-testid="profile-value"
              className="flex flex-col gap-2 rounded border border-neutral-200 px-4 py-3"
            >
              <p className="text-xs uppercase tracking-wide text-neutral-500">
                {fieldLabel(value.field_key)}
              </p>
              <p className="font-medium">{value.value}</p>
              <p className="text-xs text-neutral-500">
                {value.status === "unconfirmed"
                  ? `Needs review${value.confidence === "low" ? " (low confidence)" : ""}`
                  : null}
                {value.status === "confirmed" ? "Confirmed" : null}
                {value.status === "stale"
                  ? `Needs re-check — ${value.stale_reason ?? "source changed"}`
                  : null}
                {value.source_locator ? ` · from ${value.source_locator}` : null}
              </p>
              <div className="flex gap-2">
                {value.status === "unconfirmed" ? (
                  <button
                    type="button"
                    onClick={() => void handleConfirm(value.id)}
                    disabled={busy}
                    className="rounded border border-neutral-300 px-3 py-1"
                  >
                    Confirm
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => startCorrection(value)}
                  disabled={busy}
                  className="rounded border border-neutral-300 px-3 py-1"
                >
                  Correct
                </button>
                {value.status !== "confirmed" ? (
                  <button
                    type="button"
                    onClick={() => void handleReject(value.id)}
                    disabled={busy}
                    className="rounded border border-neutral-300 px-3 py-1"
                  >
                    Remove
                  </button>
                ) : null}
              </div>
              {correctingId === value.id ? (
                <form
                  onSubmit={(event) => void handleCorrect(event, value.id)}
                  className="flex gap-2"
                >
                  <input
                    aria-label={`Correct ${fieldLabel(value.field_key)}`}
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    className="rounded border border-neutral-300 px-3 py-1"
                  />
                  <button
                    type="submit"
                    disabled={busy || draft.trim().length === 0}
                    className="rounded border border-neutral-300 px-3 py-1"
                  >
                    Save
                  </button>
                </form>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      {error ? <p data-testid="profile-error">{error}</p> : null}
    </div>
  );
}
