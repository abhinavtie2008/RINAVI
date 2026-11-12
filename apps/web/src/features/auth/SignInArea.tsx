"use client";

import { startAuthentication, startRegistration } from "@simplewebauthn/browser";
import { useEffect, useState, type FormEvent } from "react";

import { apiFetch } from "@/lib/api";

type Me = {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
};

type PasskeyBegin = {
  challenge_id: string;
  options: unknown;
};

export function SignInArea() {
  const [me, setMe] = useState<Me | null>(null);
  const [checked, setChecked] = useState(false);
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiFetch<Me>("/api/v1/auth/me")
      .then(setMe)
      .catch(() => setMe(null))
      .finally(() => setChecked(true));
  }, []);

  async function handleDevSignin(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await apiFetch<Me>("/api/v1/auth/dev-signin", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setMe(user);
    } catch {
      setError("Sign-in failed. Is the backend running?");
    } finally {
      setBusy(false);
    }
  }

  async function handlePasskeyLogin() {
    setBusy(true);
    setError(null);
    try {
      const begin = await apiFetch<PasskeyBegin>("/api/v1/auth/passkey/login/begin", {
        method: "POST",
      });
      const assertion = await startAuthentication(begin.options as never);
      const user = await apiFetch<Me>("/api/v1/auth/passkey/login/finish", {
        method: "POST",
        body: JSON.stringify({
          challenge_id: begin.challenge_id,
          credential: JSON.stringify(assertion),
        }),
      });
      setMe(user);
    } catch {
      setError("Passkey sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleAddPasskey() {
    setBusy(true);
    setError(null);
    try {
      const begin = await apiFetch<PasskeyBegin>("/api/v1/auth/passkey/register/begin", {
        method: "POST",
      });
      const attestation = await startRegistration(begin.options as never);
      await apiFetch("/api/v1/auth/passkey/register/finish", {
        method: "POST",
        body: JSON.stringify({
          challenge_id: begin.challenge_id,
          credential: JSON.stringify(attestation),
        }),
      });
    } catch {
      setError("Passkey registration failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSignOut() {
    await apiFetch<void>("/api/v1/auth/logout", { method: "POST" });
    setMe(null);
  }

  if (!checked) {
    return <p data-testid="auth-loading">Loading…</p>;
  }

  if (me) {
    return (
      <div data-testid="signed-in" className="flex flex-col items-center gap-3">
        <p>Signed in as {me.email}</p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleAddPasskey}
            disabled={busy}
            className="rounded border border-neutral-300 px-3 py-1"
          >
            Add passkey
          </button>
          <button
            type="button"
            onClick={handleSignOut}
            disabled={busy}
            className="rounded border border-neutral-300 px-3 py-1"
          >
            Sign out
          </button>
        </div>
        {error ? <p data-testid="signin-error">{error}</p> : null}
      </div>
    );
  }

  return (
    <form
      onSubmit={handleDevSignin}
      data-testid="signin-form"
      className="flex flex-col items-center gap-3"
    >
      <label htmlFor="email" className="text-sm">
        Email
      </label>
      <input
        id="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        required
        className="rounded border border-neutral-300 px-3 py-1"
      />
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={busy}
          className="rounded border border-neutral-300 px-3 py-1"
        >
          Continue
        </button>
        <button
          type="button"
          onClick={handlePasskeyLogin}
          disabled={busy}
          className="rounded border border-neutral-300 px-3 py-1"
        >
          Use passkey
        </button>
      </div>
      {error ? <p data-testid="signin-error">{error}</p> : null}
    </form>
  );
}
