"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { createDraft } from "@/lib/applications";
import {
  getService,
  listServices,
  type ServiceDetail,
  type ServiceSummary,
} from "@/lib/catalog";

export function ServicesPage() {
  const router = useRouter();
  const [services, setServices] = useState<ServiceSummary[]>([]);
  const [selected, setSelected] = useState<ServiceDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setServices(await listServices());
      } catch {
        setError("Could not load services. Sign in and try again.");
      }
    }
    void load();
  }, []);

  async function openService(slug: string) {
    setBusy(true);
    setError(null);
    try {
      setSelected(await getService(slug));
    } catch {
      setError("Could not load this service.");
    } finally {
      setBusy(false);
    }
  }

  async function startApplication(slug: string) {
    setBusy(true);
    setError(null);
    try {
      const draft = await createDraft(slug);
      router.push(`/applications/${draft.id}`);
    } catch {
      setError("Could not start an application. Allow application preparation first.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      {services.length === 0 && error === null ? (
        <p data-testid="catalog-loading">Loading…</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {services.map((service) => (
            <li
              key={service.slug}
              className="rounded border border-neutral-200 p-4"
            >
              <button
                type="button"
                onClick={() => void openService(service.slug)}
                disabled={busy}
                className="font-medium underline"
              >
                {service.name}
              </button>
              <p className="text-sm">{service.summary}</p>
              <p className="text-xs text-neutral-500">
                {service.geography} · {service.fee} · {service.processing_time}
              </p>
            </li>
          ))}
        </ul>
      )}
      {selected !== null ? (
        <section
          data-testid="service-detail"
          className="flex flex-col gap-3 rounded border border-neutral-200 p-4"
        >
          <h2 className="text-lg font-semibold">{selected.name}</h2>
          <p className="text-sm">{selected.guidance.what_it_is}</p>
          <div>
            <h3 className="text-sm font-medium">Fields</h3>
            <ul className="text-sm">
              {selected.fields.map((field) => (
                <li key={field.id}>
                  {field.label}
                  {field.required ? " *" : ""}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-medium">Evidence checklist</h3>
            <ul className="text-sm">
              {selected.checklist_groups.map((group) => (
                <li key={group.id}>{group.label}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-medium">Official channel</h3>
            <ol className="list-decimal pl-5 text-sm">
              {selected.guidance.official_channel_steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
          <p data-testid="submission-notice" className="text-sm text-neutral-600">
            {selected.guidance.not_a_submission_notice}
          </p>
          <button
            type="button"
            onClick={() => void startApplication(selected.slug)}
            disabled={busy}
            className="self-start rounded border border-neutral-300 px-3 py-1"
          >
            Start application
          </button>
        </section>
      ) : null}
      {error !== null ? <p data-testid="catalog-error">{error}</p> : null}
    </div>
  );
}
