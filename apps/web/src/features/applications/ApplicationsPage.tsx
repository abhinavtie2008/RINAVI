"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { SiteNav } from "@/components/SiteNav";
import { ApiError } from "@/lib/api";
import {
  APPLICATIONS_PURPOSE,
  createDraft,
  deleteAllDrafts,
  listDrafts,
  type Draft,
} from "@/lib/applications";
import { listServices, type ServiceSummary } from "@/lib/catalog";
import {
  grantConsent,
  hasActiveGrant,
  listGrants,
} from "@/lib/vault";

export function ApplicationsPage() {
  const [ready, setReady] = useState(false);
  const [consentGranted, setConsentGranted] = useState(false);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [services, setServices] = useState<ServiceSummary[]>([]);
  const [serviceSlug, setServiceSlug] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draftsDeleted, setDraftsDeleted] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  async function loadApplicationData() {
    const [loadedDrafts, loadedServices] = await Promise.all([
      listDrafts(),
      listServices(),
    ]);
    setDrafts(loadedDrafts);
    setServices(loadedServices);
  }

  useEffect(() => {
    async function load() {
      try {
        const grants = await listGrants();
        const granted = hasActiveGrant(grants, APPLICATIONS_PURPOSE);
        setConsentGranted(granted);
        if (granted) {
          await loadApplicationData();
        }
      } catch {
        setError("Could not load your applications. Sign in and try again.");
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
      await grantConsent(APPLICATIONS_PURPOSE);
      setConsentGranted(true);
      await loadApplicationData();
    } catch {
      setError("Could not record consent.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteSavedDrafts() {
    setBusy(true);
    setError(null);
    try {
      await deleteAllDrafts();
      setDraftsDeleted(true);
      setConfirmingDelete(false);
    } catch {
      setError("Could not delete your drafts.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreate() {
    if (serviceSlug === "") {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const draft = await createDraft(serviceSlug);
      setDrafts((current) => [draft, ...current]);
      setServiceSlug("");
    } catch (createError) {
      if (createError instanceof ApiError && createError.status === 403) {
        setConsentGranted(false);
      } else {
        setError("Could not create the draft.");
      }
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p data-testid="applications-loading">Loading…</p>;
  }

  if (!consentGranted) {
    return (
      <div className="flex w-full max-w-2xl flex-col gap-4">
        <SiteNav />
        <section
          data-testid="consent-gate"
          className="flex w-full max-w-md flex-col gap-3 rounded border border-neutral-200 px-4 py-6"
        >
          <p className="text-sm">
            RINAVI prepares application drafts only after you allow it. You
            control every value, document, declaration, and final submission.
          </p>
          <button
            type="button"
            onClick={() => void handleGrant()}
            disabled={busy}
            className="rounded border border-neutral-300 px-3 py-1"
          >
            Allow application preparation
          </button>
          <div className="flex flex-col gap-2 border-t border-neutral-200 pt-3">
            <p className="text-sm">
              Deleting your drafts is always available, with or without this
              permission.
            </p>
            {confirmingDelete ? (
              <div
                data-testid="delete-drafts-confirm"
                className="flex flex-col gap-2 rounded border border-neutral-300 p-3"
              >
                <p className="text-sm">
                  This deletes every saved application draft. It cannot be
                  undone.
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => void handleDeleteSavedDrafts()}
                    disabled={busy}
                    className="rounded border border-neutral-300 px-3 py-1"
                  >
                    Confirm delete all
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmingDelete(false)}
                    disabled={busy}
                    className="rounded border border-neutral-300 px-3 py-1"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setConfirmingDelete(true)}
                disabled={busy}
                className="rounded border border-neutral-300 px-3 py-1"
              >
                Delete all saved drafts
              </button>
            )}
            {draftsDeleted ? (
              <p data-testid="drafts-deleted" className="text-sm">
                Saved drafts deleted.
              </p>
            ) : null}
          </div>
          {error ? <p data-testid="applications-error">{error}</p> : null}
        </section>
      </div>
    );
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <SiteNav />
      <div className="flex items-end gap-2">
        <label htmlFor="service-picker" className="text-sm">
          Service
        </label>
        <select
          id="service-picker"
          value={serviceSlug}
          onChange={(event) => setServiceSlug(event.target.value)}
          className="min-w-0 flex-1 rounded border border-neutral-300 px-2 py-1 text-sm"
        >
          <option value="">Choose a service…</option>
          {services.map((service) => (
            <option key={service.slug} value={service.slug}>
              {service.name}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => void handleCreate()}
          disabled={busy || serviceSlug === ""}
          className="rounded border border-neutral-300 px-3 py-1"
        >
          Start new application
        </button>
      </div>

      {drafts.length === 0 ? (
        <p data-testid="applications-empty" className="text-sm text-neutral-600">
          No applications yet.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {drafts.map((draft) => (
            <li
              key={draft.id}
              data-testid="draft-row"
              className="rounded border border-neutral-200 p-4"
            >
              <Link
                href={`/applications/${draft.id}`}
                className="font-medium underline"
              >
                {draft.service_name}
              </Link>
              <p className="text-xs text-neutral-500">
                Pack {draft.pack_version} ·{" "}
                {draft.validation.length === 0
                  ? "Ready to export"
                  : `${draft.validation.length} unresolved issues`}
              </p>
            </li>
          ))}
        </ul>
      )}
      {error !== null ? (
        <p data-testid="applications-error">{error}</p>
      ) : null}
    </div>
  );
}
