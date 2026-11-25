"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { SiteNav } from "@/components/SiteNav";
import {
  deleteAccount,
  downloadJson,
  exportAccount,
  fetchAccount,
  type AccountUser,
} from "@/lib/account";
import { ApiError } from "@/lib/api";

const EXPORT_FILENAME = "rinavi-account-export.json";

function isoDate(value: string): string {
  return value.slice(0, 10);
}

export function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<AccountUser | null>(null);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState<"export" | "delete" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchAccount()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setReady(true));
  }, []);

  async function handleExport() {
    setBusy("export");
    setError(null);
    setMessage(null);
    try {
      downloadJson(await exportAccount(), EXPORT_FILENAME);
      setMessage("Downloaded. It holds your account details and permission history.");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "Could not prepare your export. Sign in and try again."
      );
    } finally {
      setBusy(null);
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm(
      "Delete your RINAVI account? This erases your documents, profile values, " +
        "drafts and cases, and ends your session. It cannot be undone."
    );
    if (!confirmed) {
      return;
    }
    setBusy("delete");
    setError(null);
    try {
      await deleteAccount();
      // The session cookie is gone with the account; leaving the page keeps a
      // deleted account on screen, which reads like the deletion failed.
      router.push("/");
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "Could not delete your account. Try again."
      );
      setBusy(null);
    }
  }

  if (!ready) {
    return <p data-testid="account-loading">Loading…</p>;
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <SiteNav />
      {user ? (
        <p data-testid="account-user" className="text-sm text-neutral-600">
          Signed in as <span className="font-medium">{user.email}</span>, since 
          {isoDate(user.created_at)}.
        </p>
      ) : (
        <p data-testid="account-signed-out" className="text-sm text-neutral-600">
          You are not signed in, so there is nothing to export or delete here.
        </p>
      )}

      <section
        data-testid="account-export"
        className="flex flex-col gap-2 rounded border border-neutral-200 px-4 py-3"
      >
        <p className="font-medium">Download your account record</p>
        <p className="text-sm text-neutral-600">
          This file holds your account details and your permission history —
          every grant and withdrawal, with dates. It does not include your
          documents or your profile values: you can read those in the app, but
          they are not part of this download yet.
        </p>
        <button
          type="button"
          onClick={() => void handleExport()}
          disabled={!user || busy !== null}
          className="self-start rounded border border-neutral-300 px-3 py-1"
        >
          Download account record and permissions
        </button>
      </section>

      <section
        data-testid="account-delete"
        className="flex flex-col gap-2 rounded border border-neutral-200 px-4 py-3"
      >
        <p className="font-medium">Delete your account</p>
        <p className="text-sm text-neutral-600">
          This erases your documents, profile values, drafts and cases, and ends
          your session. It cannot be undone, and it is the same whether or not
          you have allowed any permission.
        </p>
        <button
          type="button"
          onClick={() => void handleDelete()}
          disabled={!user || busy !== null}
          className="self-start rounded border border-red-300 px-3 py-1 text-red-700"
        >
          Delete my account
        </button>
      </section>

      {message ? <p data-testid="account-message">{message}</p> : null}
      {error ? <p data-testid="account-error">{error}</p> : null}

      <p className="text-sm text-neutral-600">
        Every screen is limited to your own account. You can also read your
        documents, correct your profile values, or withdraw a permission before
        you delete anything.
      </p>
    </div>
  );
}
