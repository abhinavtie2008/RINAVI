"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { SiteNav } from "@/components/SiteNav";
import { LOCKER_PURPOSE, listCases, type CaseSummary } from "@/lib/locker";
import { grantConsent, hasActiveGrant, listGrants } from "@/lib/vault";

import { STATUS_META } from "./statusMeta";

export function CasesPage() {
  const [ready, setReady] = useState(false);
  const [consentGranted, setConsentGranted] = useState(false);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const grants = await listGrants();
        const granted = hasActiveGrant(grants, LOCKER_PURPOSE);
        setConsentGranted(granted);
        if (granted) {
          setCases(await listCases());
        }
      } catch {
        setError("Could not load your locker. Sign in and try again.");
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
      await grantConsent(LOCKER_PURPOSE);
      setConsentGranted(true);
      setCases(await listCases());
    } catch {
      setError("Could not record consent.");
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p data-testid="locker-loading">Loading…</p>;
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
            RINAVI keeps your application packets here only after you allow
            it. You record every status change yourself; RINAVI never submits
            anything.
          </p>
          <button
            type="button"
            onClick={() => void handleGrant()}
            disabled={busy}
            className="rounded border border-neutral-300 px-3 py-1"
          >
            Allow application tracking
          </button>
          {error ? <p data-testid="locker-error">{error}</p> : null}
        </section>
      </div>
    );
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <SiteNav />
      {cases.length === 0 ? (
        <p data-testid="locker-empty" className="text-sm text-neutral-600">
          No applications in your locker yet. Finish a draft from Applications
          to start tracking it here.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {cases.map((caseRecord) => (
            <li
              key={caseRecord.id}
              data-testid="case-row"
              className="rounded border border-neutral-200 p-4"
            >
              <div className="flex items-center gap-3">
                <Link
                  href={`/locker/${caseRecord.id}`}
                  className="font-medium underline"
                >
                  {caseRecord.service_name}
                </Link>
                <span
                  className={`rounded-full px-3 py-1 text-xs ${STATUS_META[caseRecord.status].className}`}
                >
                  {STATUS_META[caseRecord.status].label}
                </span>
              </div>
              <p className="text-xs text-neutral-500">
                Started {new Date(caseRecord.created_at).toLocaleDateString()}
                {caseRecord.reference_number
                  ? ` · Reference ${caseRecord.reference_number}`
                  : ""}
              </p>
            </li>
          ))}
        </ul>
      )}
      {error !== null ? <p data-testid="locker-error">{error}</p> : null}
    </div>
  );
}
