"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import {
  APPLICATIONS_PURPOSE,
  createDraft,
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
        {error ? <p data-testid="applications-error">{error}</p> : null}
      </section>
    );
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
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
