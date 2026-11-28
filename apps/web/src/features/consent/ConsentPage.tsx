"use client";

import { useEffect, useState } from "react";

import { SiteNav } from "@/components/SiteNav";
import { listGrants, withdrawConsent, type ConsentRecord } from "@/lib/vault";

export type PurposeInfo = {
  purpose: string;
  label: string;
  description: string;
};

// Must stay equal to backend/app/modules/consent/purposes.py and
// docs/compliance/data-map.md §4; the test below pins the four strings.
export const PURPOSES: PurposeInfo[] = [
  {
    purpose: "documents.processing",
    label: "Document processing",
    description: "Reading a document you upload so its fields can be extracted.",
  },
  {
    purpose: "profile.storage",
    label: "Profile storage",
    description: "Keeping those values in your profile so you can review them.",
  },
  {
    purpose: "applications.preparation",
    label: "Application preparation",
    description: "Filling an application draft from your profile and documents.",
  },
  {
    purpose: "locker.tracking",
    label: "Application tracking",
    description: "Recording what happened to an application you filed yourself.",
  },
];

function isoDate(value: string): string {
  return value.slice(0, 10);
}

function activeGrant(
  grants: ConsentRecord[],
  purpose: string
): ConsentRecord | undefined {
  return grants.find(
    (grant) => grant.purpose === purpose && grant.withdrawn_at === null
  );
}

// listGrants() is newest first, so the first record for a purpose is its latest.
function latestGrant(
  grants: ConsentRecord[],
  purpose: string
): ConsentRecord | undefined {
  return grants.find((grant) => grant.purpose === purpose);
}

export function ConsentPage() {
  const [ready, setReady] = useState(false);
  const [grants, setGrants] = useState<ConsentRecord[]>([]);
  const [busyPurpose, setBusyPurpose] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setGrants(await listGrants());
      } catch {
        setError("Could not load your permissions. Sign in and try again.");
      } finally {
        setReady(true);
      }
    }
    void load();
  }, []);

  async function handleWithdraw(info: PurposeInfo, grantId: string) {
    const confirmed = window.confirm(
      `Withdraw permission to ${info.label.toLowerCase()}? RINAVI will ask again before using your data for this.`
    );
    if (!confirmed) {
      return;
    }
    setBusyPurpose(info.purpose);
    setError(null);
    try {
      const withdrawn = await withdrawConsent(grantId);
      setGrants((current) => [
        withdrawn,
        ...current.filter((grant) => grant.id !== withdrawn.id),
      ]);
    } catch {
      setError("Could not withdraw that permission.");
    } finally {
      setBusyPurpose(null);
    }
  }

  if (!ready) {
    return <p data-testid="consent-loading">Loading…</p>;
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <SiteNav />
      <p className="text-sm text-neutral-600">
        RINAVI only touches your data while the matching permission is allowed.
        Withdrawing one takes effect immediately, and nothing already saved is
        deleted for you — delete documents and drafts yourself if you want them
        gone.
      </p>
      <ul className="flex flex-col gap-2">
        {PURPOSES.map((info) => {
          const active = activeGrant(grants, info.purpose);
          const latest = active ?? latestGrant(grants, info.purpose);
          return (
            <li
              key={info.purpose}
              data-testid={`consent-${info.purpose}`}
              className="flex flex-col gap-2 rounded border border-neutral-200 px-4 py-3"
            >
              <p className="font-medium">{info.label}</p>
              <p className="text-xs text-neutral-500">{info.description}</p>
              <p className="text-sm">
                {active
                  ? `Allowed on ${isoDate(active.granted_at)} (policy ${active.policy_version})`
                  : latest?.withdrawn_at
                    ? `Withdrawn on ${isoDate(latest.withdrawn_at)}`
                    : "Not allowed"}
              </p>
              {active ? (
                <button
                  type="button"
                  onClick={() => void handleWithdraw(info, active.id)}
                  disabled={busyPurpose !== null}
                  className="self-start rounded border border-neutral-300 px-3 py-1"
                >
                  Withdraw
                </button>
              ) : null}
            </li>
          );
        })}
      </ul>
      {error ? <p data-testid="consent-error">{error}</p> : null}
    </div>
  );
}
