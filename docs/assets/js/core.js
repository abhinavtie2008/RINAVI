/* The demo's data layer.
   GitHub Pages is static, so there is no server: this module plays the part of the RINAVI API
   and keeps everything in this browser's localStorage. It follows the rules of the real backend:
   deny-by-default consent, source-linked profile values, deterministic validation,
   frozen packets, a redacted audit trail, and erasure that always works. */
(function () {
  "use strict";
  const R = (globalThis.RINAVI = globalThis.RINAVI || {});
  const KEY = "rinavi.demo.v1";
  const MAX_UPLOAD = 10 * 1024 * 1024;
  const MAX_TEXT_STORED = 60 * 1024;
  const MAX_VALUE = 500;
  const POLICY_VERSION = "demo-1";

  const PURPOSE = {
    documents: "documents.processing",
    profile: "profile.storage",
    applications: "applications.preparation",
    locker: "locker.tracking",
  };
  const PURPOSE_LIST = Object.values(PURPOSE);

  class ApiError extends Error {
    constructor(status, message, code) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.code = code || "";
    }
  }

  let mem = null;
  let storageFailed = false;

  const blank = () => ({ v: 1, user: null, consents: [], documents: [], profile: [], drafts: [], cases: [], audit: [] });
  const uid = (p) => p + "_" + Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-4);
  const now = () => new Date().toISOString();
  const clone = (x) => JSON.parse(JSON.stringify(x));
  const short = (id) => String(id).slice(-6);

  function state() {
    if (mem) return mem;
    try {
      const raw = globalThis.localStorage && globalThis.localStorage.getItem(KEY);
      mem = raw ? Object.assign(blank(), JSON.parse(raw)) : blank();
    } catch (e) {
      mem = blank();
    }
    return mem;
  }
  function save() {
    try {
      globalThis.localStorage.setItem(KEY, JSON.stringify(mem));
      storageFailed = false;
    } catch (e) {
      storageFailed = true;
    }
  }
  if (globalThis.addEventListener) {
    globalThis.addEventListener("storage", (e) => {
      if (e.key === KEY) mem = null;
    });
  }

  function audit(action, detail) {
    const s = state();
    s.audit.unshift({ id: uid("evt"), at: now(), action, detail: detail || "" });
    if (s.audit.length > 300) s.audit.length = 300;
  }

  const S = {};
  R.store = S;
  S.ApiError = ApiError;
  S.PURPOSE = PURPOSE;
  S.PURPOSE_LIST = PURPOSE_LIST;
  S.MAX_UPLOAD = MAX_UPLOAD;
  S.storageFailed = () => storageFailed;
  S._reset = () => { mem = null; };

  /* ---------- identity ---------- */
  S.user = () => state().user;
  S.signIn = (name) => {
    const s = state();
    const clean = String(name || "").trim().slice(0, 60) || "Demo citizen";
    s.user = { id: s.user ? s.user.id : uid("usr"), name: clean, signed_in_at: now() };
    audit("auth.sign_in");
    save();
    return s.user;
  };
  S.signOut = () => {
    const s = state();
    audit("auth.sign_out");
    s.user = null;
    save();
  };

  /* ---------- consent ---------- */
  S.listGrants = () => clone(state().consents);
  S.activeGrant = (purpose) => state().consents.find((c) => c.purpose === purpose && c.withdrawn_at === null) || null;
  S.hasConsent = (purpose) => !!S.activeGrant(purpose);
  S.grant = (purpose) => {
    if (!PURPOSE_LIST.includes(purpose)) throw new ApiError(422, "Unknown purpose.");
    const s = state();
    s.consents.forEach((c) => {
      if (c.purpose === purpose && c.withdrawn_at === null) c.withdrawn_at = now();
    });
    const record = { id: uid("con"), purpose, granted_at: now(), withdrawn_at: null, policy_version: POLICY_VERSION };
    s.consents.unshift(record);
    audit("consent.granted", purpose);
    save();
    return clone(record);
  };
  S.withdraw = (id) => {
    const s = state();
    const record = s.consents.find((c) => c.id === id);
    if (!record) throw new ApiError(404, "Permission not found.");
    if (record.withdrawn_at === null) record.withdrawn_at = now();
    audit("consent.withdrawn", record.purpose);
    save();
    return clone(record);
  };
  function need(purpose) {
    if (!S.hasConsent(purpose)) throw new ApiError(403, "Permission needed.", "consent_required");
  }

  /* ---------- vault and documents ---------- */
  const view = (d) => {
    const { text, ...rest } = d;
    return clone(rest);
  };
  function process(doc, text) {
    doc.fields = [];
    doc.classification = "unsupported";
    if (text === null) {
      doc.status = "needs_attention";
      doc.note = doc.mime === "application/pdf" ? "pdf_not_read_in_demo" : "ocr_not_configured";
      return;
    }
    if (!text.trim()) {
      doc.status = "needs_attention";
      doc.note = "empty_file";
      return;
    }
    const result = R.extract(text);
    doc.fields = result.fields;
    doc.classification = result.classification;
    if (!result.fields.length && result.classification === "unsupported") {
      doc.status = "needs_attention";
      doc.note = "no_fields_detected";
    } else {
      doc.status = "processed";
      doc.note = "";
    }
  }
  S.addDocument = (meta, text) => {
    need(PURPOSE.documents);
    const name = String(meta.name || "document").slice(0, 120);
    const ext = (name.split(".").pop() || "").toLowerCase();
    if (meta.size > MAX_UPLOAD) throw new ApiError(413, "That file is larger than 10 MB.");
    if (!["pdf", "png", "jpg", "jpeg", "txt"].includes(ext)) throw new ApiError(415, "Supported types: PDF, PNG, JPEG, TXT.");
    const mime = ext === "pdf" ? "application/pdf" : ext === "txt" ? "text/plain" : "image/" + (ext === "png" ? "png" : "jpeg");
    const doc = { id: uid("doc"), original_filename: name, size: meta.size || 0, mime, created_at: now(), text: null };
    // Aadhaar stays on the portal: the number is dropped before anything is stored or shown.
    if (ext === "txt") {
      doc.text = String(text || "")
        .slice(0, MAX_TEXT_STORED)
        .replace(/^(\s*aadhaar(?:\s+number)?\s*:\s*).*$/gim, "$1[not kept by RINAVI]");
    }
    process(doc, ext === "txt" ? doc.text : null);
    const s = state();
    s.documents.unshift(doc);
    audit("document.uploaded", `${short(doc.id)} ${doc.status}`);
    save();
    return view(doc);
  };
  S.listDocuments = () => state().documents.map(view);
  S.getDocument = (id) => {
    const d = state().documents.find((x) => x.id === id);
    if (!d) throw new ApiError(404, "Document not found.");
    return view(d);
  };
  S.getDocumentText = (id) => {
    const d = state().documents.find((x) => x.id === id);
    return d && d.text !== null ? d.text : null;
  };
  S.retryDocument = (id) => {
    need(PURPOSE.documents);
    const d = state().documents.find((x) => x.id === id);
    if (!d) throw new ApiError(404, "Document not found.");
    process(d, d.text);
    audit("document.retried", `${short(d.id)} ${d.status}`);
    save();
    return view(d);
  };
  // Erasure always works, even after consent is withdrawn.
  S.deleteDocument = (id) => {
    const s = state();
    const i = s.documents.findIndex((x) => x.id === id);
    if (i < 0) throw new ApiError(404, "Document not found.");
    s.documents.splice(i, 1);
    s.profile.forEach((v) => {
      if (v.source_document_id === id && v.status !== "stale") {
        v.status = "stale";
        v.stale_reason = "source document deleted";
      }
    });
    audit("document.deleted", short(id));
    save();
  };

  /* ---------- profile ---------- */
  S.listProfile = () => {
    need(PURPOSE.profile);
    return clone(state().profile);
  };
  S.promote = (docId) => {
    need(PURPOSE.profile);
    const s = state();
    const doc = s.documents.find((d) => d.id === docId);
    if (!doc || doc.status !== "processed") throw new ApiError(422, "That document has no values to add.");
    let added = 0, kept = 0;
    doc.fields.forEach((f) => {
      const existing = s.profile.find((v) => v.field_key === f.field_key);
      if (existing && existing.status === "confirmed") { kept++; return; }
      const next = {
        id: existing ? existing.id : uid("val"),
        field_key: f.field_key,
        value: f.value,
        status: "unconfirmed",
        confidence: f.confidence,
        source_document_id: doc.id,
        source_filename: doc.original_filename,
        source_locator: `${doc.original_filename}, ${f.locator}`,
        stale_reason: null,
        corrected: false,
      };
      if (existing) Object.assign(existing, next); else s.profile.push(next);
      added++;
    });
    audit("profile.promoted", `${short(doc.id)} +${added}`);
    save();
    return { added, kept, values: clone(s.profile) };
  };
  function profileValue(id) {
    const v = state().profile.find((x) => x.id === id);
    if (!v) throw new ApiError(404, "Value not found.");
    return v;
  }
  S.confirmValue = (id) => {
    need(PURPOSE.profile);
    const v = profileValue(id);
    v.status = "confirmed";
    v.stale_reason = null;
    audit("profile.confirmed", v.field_key);
    save();
    return clone(v);
  };
  S.correctValue = (id, value) => {
    need(PURPOSE.profile);
    const v = profileValue(id);
    const clean = String(value || "").trim();
    if (!clean) throw new ApiError(422, "Enter a value.");
    if (clean.length > MAX_VALUE) throw new ApiError(422, "That value is too long.");
    v.value = clean;
    v.status = "confirmed";
    // The confirmed value is the citizen's now, not the document's. Mirrors
    // profile service correct_value: drop the source pointer so deleting the
    // document cannot mark a value they typed themselves as stale.
    v.source_document_id = null;
    v.source_locator = null;
    v.confidence = null;
    v.corrected = true;
    v.stale_reason = null;
    audit("profile.corrected", v.field_key);
    save();
    return clone(v);
  };
  S.rejectValue = (id) => {
    need(PURPOSE.profile);
    const s = state();
    const v = profileValue(id);
    if (v.status === "confirmed") throw new ApiError(422, "Correct a confirmed value instead of removing it.");
    s.profile = s.profile.filter((x) => x.id !== id);
    audit("profile.removed", v.field_key);
    save();
  };

  /* ---------- applications ---------- */
  const getPack = (slug) => {
    const pack = R.catalog.packs[slug];
    const service = R.catalog.services.find((x) => x.slug === slug);
    if (!pack || !service) throw new ApiError(404, "Service not found.");
    return { pack, service };
  };
  function seedFromProfile(draft) {
    const s = state();
    draft.template_snapshot.fields.forEach((f) => {
      if (!f.binding) return;
      const pv = s.profile.find((v) => v.field_key === f.binding && v.status === "confirmed");
      const cur = draft.values[f.id];
      if (pv) {
        if (!cur || cur.origin === "profile") {
          draft.values[f.id] = { value: pv.value, origin: "profile", source: pv.source_locator, corrected: !!pv.corrected };
        }
      } else if (cur && cur.origin === "profile") {
        delete draft.values[f.id];
      }
    });
  }
  S.createDraft = (slug) => {
    need(PURPOSE.applications);
    const { pack, service } = getPack(slug);
    const draft = {
      id: uid("drf"),
      service_slug: slug,
      service_name: service.name,
      pack_version: pack.pack_version,
      template_snapshot: {
        fields: clone(pack.form_template.fields),
        declaration: clone(pack.form_template.declaration),
        checklist_groups: clone(pack.checklist_groups),
        guidance: clone(pack.guidance),
        processing_time: service.processing_time,
        fee: service.fee,
        sources: clone(service.sources),
      },
      values: {},
      document_links: {},
      declaration_confirmed: false,
      case_id: null,
      created_at: now(),
      updated_at: now(),
    };
    seedFromProfile(draft);
    state().drafts.unshift(draft);
    audit("draft.created", short(draft.id));
    save();
    return withValidation(draft);
  };
  function validate(draft) {
    const s = state();
    const issues = [];
    draft.template_snapshot.fields.forEach((f) => {
      const entry = draft.values[f.id];
      const value = entry ? String(entry.value).trim() : "";
      if (!value) {
        if (f.required) issues.push({ code: "required_field", field_id: f.id, group_id: null, message: `${f.label} is required.` });
        return;
      }
      if (f.format === "numeric" && !/^\d+$/.test(value)) {
        issues.push({ code: "bad_format", field_id: f.id, group_id: null, message: `${f.label} must be a whole number, like 240000.` });
      }
      if (f.format === "date" && !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        issues.push({ code: "bad_format", field_id: f.id, group_id: null, message: `${f.label} must look like 1994-03-12.` });
      }
    });
    draft.template_snapshot.checklist_groups.forEach((g) => {
      const ids = draft.document_links[g.id] || [];
      let usable = 0;
      ids.forEach((id) => {
        const d = s.documents.find((x) => x.id === id);
        if (!d || d.status !== "processed") {
          issues.push({ code: "document_unavailable", field_id: null, group_id: g.id, document_id: id, message: "A linked document is no longer available. Remove it and attach another." });
        } else usable++;
      });
      if (g.requirement === "at_least_one" && usable === 0) {
        issues.push({ code: "missing_evidence", field_id: null, group_id: g.id, message: `Attach at least one document for ${g.label}.` });
      }
    });
    if (draft.template_snapshot.declaration.required && !draft.declaration_confirmed) {
      issues.push({ code: "declaration_required", field_id: null, group_id: null, message: "Read and confirm the declaration before you finish." });
    }
    return issues;
  }
  function withValidation(draft) {
    const out = clone(draft);
    out.validation = validate(draft);
    return out;
  }
  function draftRef(id) {
    const d = state().drafts.find((x) => x.id === id);
    if (!d) throw new ApiError(404, "Draft not found.");
    return d;
  }
  const touch = (d) => { d.updated_at = now(); save(); };
  S.listDrafts = () => {
    need(PURPOSE.applications);
    return state().drafts.map(withValidation);
  };
  // Listing without consent is not allowed, but the citizen can still see ids to delete.
  S.listDraftStubs = () => state().drafts.map((d) => ({ id: d.id, service_name: d.service_name, created_at: d.created_at }));
  S.getDraft = (id) => {
    need(PURPOSE.applications);
    return withValidation(draftRef(id));
  };
  S.setField = (id, fieldId, value) => {
    need(PURPOSE.applications);
    const d = draftRef(id);
    const field = d.template_snapshot.fields.find((f) => f.id === fieldId);
    if (!field) throw new ApiError(422, "Unknown field.");
    const clean = String(value || "").trim();
    if (clean.length > MAX_VALUE) throw new ApiError(422, "That value is too long.");
    if (clean) d.values[fieldId] = { value: clean, origin: "citizen" };
    else delete d.values[fieldId];
    audit("draft.field_set", `${short(d.id)} ${fieldId}`);
    touch(d);
    return withValidation(d);
  };
  S.refreshDraft = (id) => {
    need(PURPOSE.applications);
    const d = draftRef(id);
    seedFromProfile(d);
    audit("draft.refreshed", short(d.id));
    touch(d);
    return withValidation(d);
  };
  S.linkDocument = (id, docId, groupId) => {
    need(PURPOSE.applications);
    const d = draftRef(id);
    const doc = state().documents.find((x) => x.id === docId);
    const group = d.template_snapshot.checklist_groups.find((g) => g.id === groupId);
    if (!doc || doc.status !== "processed" || !group) throw new ApiError(422, "That document cannot be attached to this group.");
    if (group.accepted_classifications.length && !group.accepted_classifications.includes(doc.classification)) {
      throw new ApiError(422, "That document cannot be attached to this group.");
    }
    const list = d.document_links[groupId] || (d.document_links[groupId] = []);
    if (!list.includes(docId)) list.push(docId);
    audit("draft.document_linked", `${short(d.id)} ${groupId}`);
    touch(d);
    return withValidation(d);
  };
  S.unlinkDocument = (id, docId) => {
    need(PURPOSE.applications);
    const d = draftRef(id);
    Object.keys(d.document_links).forEach((g) => {
      d.document_links[g] = d.document_links[g].filter((x) => x !== docId);
    });
    audit("draft.document_unlinked", short(d.id));
    touch(d);
    return withValidation(d);
  };
  S.setDeclaration = (id, confirmed) => {
    need(PURPOSE.applications);
    const d = draftRef(id);
    d.declaration_confirmed = !!confirmed;
    audit("draft.declaration", `${short(d.id)} ${confirmed ? "confirmed" : "cleared"}`);
    touch(d);
    return withValidation(d);
  };
  // Draft deletion is not consent-gated: erasure always works.
  S.deleteDraft = (id) => {
    const s = state();
    const i = s.drafts.findIndex((x) => x.id === id);
    if (i < 0) throw new ApiError(404, "Draft not found.");
    s.drafts.splice(i, 1);
    audit("draft.deleted", short(id));
    save();
  };

  function exportText(d) {
    const t = d.template_snapshot;
    const lines = [];
    lines.push(`${d.service_name} (pack ${d.pack_version})`);
    lines.push("");
    lines.push(`NOT a submission. ${t.guidance.not_a_submission_notice}`);
    lines.push("");
    lines.push("Application details");
    t.fields.forEach((f) => {
      const e = d.values[f.id];
      lines.push(`- ${f.label}: ${e ? e.value : "(not provided)"}`);
    });
    lines.push("");
    lines.push("Evidence to upload");
    const s = state();
    t.checklist_groups.forEach((g) => {
      const names = (d.document_links[g.id] || []).map((id) => (s.documents.find((x) => x.id === id) || {}).original_filename).filter(Boolean);
      lines.push(`- ${g.label}: ${names.length ? names.join(", ") : "(none)"}`);
    });
    lines.push("");
    lines.push("Declaration (you confirm this yourself on the portal)");
    lines.push(t.declaration.text);
    lines.push("");
    lines.push("Official steps");
    t.guidance.official_channel_steps.forEach((step, i) => lines.push(`${i + 1}. ${step}`));
    return lines.join("\n");
  }
  S.exportDraft = (id) => {
    need(PURPOSE.applications);
    const d = draftRef(id);
    if (validate(d).length) throw new ApiError(409, "Resolve the highlighted issues first.");
    audit("draft.exported", short(d.id));
    save();
    return { text: exportText(d) };
  };
  S.completeDraft = (id) => {
    // Gated on applications.preparation alone, exactly like POST /applications/drafts/{id}/complete.
    // Whether case creation should also need locker.tracking is open review question 1 in
    // docs/compliance/data-map.md, so the demo mirrors the API instead of answering it.
    need(PURPOSE.applications);
    const s = state();
    const d = draftRef(id);
    if (validate(d).length) throw new ApiError(409, "Resolve the highlighted issues first.");
    if (d.case_id && s.cases.some((c) => c.id === d.case_id)) return clone(s.cases.find((c) => c.id === d.case_id));
    const t = d.template_snapshot;
    const snapshot = {
      service_name: d.service_name,
      pack_version: d.pack_version,
      fields: t.fields.map((f) => ({ id: f.id, label: f.label, value: d.values[f.id] ? d.values[f.id].value : "", source: d.values[f.id] && d.values[f.id].origin === "profile" ? d.values[f.id].source : "Entered by you" })),
      evidence: t.checklist_groups.map((g) => ({
        group_id: g.id,
        label: g.label,
        documents: (d.document_links[g.id] || []).map((id) => {
          const doc = s.documents.find((x) => x.id === id);
          return { id, filename: doc ? doc.original_filename : "Unavailable document" };
        }),
      })),
      declaration: { text: t.declaration.text, confirmed: true },
      official_channel_steps: clone(t.guidance.official_channel_steps),
      processing_time: t.processing_time,
      fee: t.fee,
      sources: clone(t.sources),
      not_a_submission_notice: t.guidance.not_a_submission_notice,
      portal_down_guidance: R.catalog.PORTAL_DOWN_GUIDANCE,
      acknowledgement_guidance: R.catalog.ACKNOWLEDGEMENT_GUIDANCE,
    };
    const c = {
      id: uid("cas"),
      draft_id: d.id,
      service_slug: d.service_slug,
      service_name: d.service_name,
      pack_version: d.pack_version,
      status: "prepared",
      reference_number: null,
      acknowledgement_number: null,
      deadline_at: null,
      outcome_notes: null,
      packet_snapshot: snapshot,
      events: [{ id: uid("ev"), type: "created", payload: {}, created_at: now() }],
      created_at: now(),
    };
    s.cases.unshift(c);
    d.case_id = c.id;
    audit("case.created", short(c.id));
    touch(d);
    return clone(c);
  };

  /* ---------- locker ---------- */
  S.listCases = () => {
    need(PURPOSE.locker);
    return clone(state().cases);
  };
  S.getCase = (id) => {
    need(PURPOSE.locker);
    const c = state().cases.find((x) => x.id === id);
    if (!c) throw new ApiError(404, "Case not found.");
    return clone(c);
  };
  const clean = (v) => { const t = String(v == null ? "" : v).trim().slice(0, 200); return t || null; };
  S.recordEvent = (id, input) => {
    need(PURPOSE.locker);
    const c = state().cases.find((x) => x.id === id);
    if (!c) throw new ApiError(404, "Case not found.");
    const ev = { id: uid("ev"), type: input.type, payload: {}, created_at: now() };
    switch (input.type) {
      case "submitted":
        ev.payload.reference_number = clean(input.reference_number);
        if (ev.payload.reference_number) c.reference_number = ev.payload.reference_number;
        c.status = "submitted";
        break;
      case "acknowledged":
        ev.payload.acknowledgement_number = clean(input.acknowledgement_number);
        if (ev.payload.acknowledgement_number) c.acknowledgement_number = ev.payload.acknowledgement_number;
        c.status = "acknowledged";
        break;
      case "outcome_received":
        ev.payload.outcome_notes = clean(input.outcome_notes);
        c.outcome_notes = ev.payload.outcome_notes;
        c.status = "outcome_received";
        break;
      case "deadline_updated":
        ev.payload.deadline_at = input.deadline_at || null;
        c.deadline_at = ev.payload.deadline_at;
        break;
      case "abandoned":
      case "uncertain":
        c.status = input.type;
        break;
      default:
        throw new ApiError(422, "Unknown update.");
    }
    c.events.push(ev);
    audit("case.event", `${short(c.id)} ${input.type}`);
    save();
    return clone(c);
  };
  S.applyAgain = (id) => {
    need(PURPOSE.locker);
    need(PURPOSE.applications);
    const s = state();
    const c = s.cases.find((x) => x.id === id);
    if (!c) throw new ApiError(404, "Case not found.");
    const draft = S.createDraft(c.service_slug);
    const suggested = [];
    c.packet_snapshot.evidence.forEach((g) => {
      g.documents.forEach((doc) => {
        const live = s.documents.find((x) => x.id === doc.id && x.status === "processed");
        if (live) suggested.push({ document_id: doc.id, group_id: g.group_id });
      });
    });
    audit("case.apply_again", short(c.id));
    save();
    return { draft, suggested_links: suggested };
  };

  /* ---------- account ---------- */
  S.listAudit = () => clone(state().audit);
  S.stats = () => {
    const s = state();
    return {
      consents: s.consents.filter((c) => c.withdrawn_at === null).length,
      documents: s.documents.length,
      processed: s.documents.filter((d) => d.status === "processed").length,
      attention: s.documents.filter((d) => d.status === "needs_attention").length,
      profile: s.profile.length,
      confirmed: s.profile.filter((v) => v.status === "confirmed").length,
      drafts: s.drafts.length,
      cases: s.cases.length,
    };
  };
  S.exportAll = () => {
    const s = clone(state());
    s.documents.forEach((d) => { if (d.text !== null) d.text = "(text kept in your browser)"; });
    return {
      exported_at: now(),
      // Document text is deliberately left out of the download, so the note
      // must not promise it: the records and metadata are complete, the file
      // contents are not.
      note: "This demo's records and metadata. Document text is kept in your browser and is not included in this export.",
      data: s,
    };
  };
  S.eraseAll = () => {
    mem = blank();
    try { globalThis.localStorage.removeItem(KEY); } catch (e) { /* nothing to do */ }
    try {
      const sess = globalThis.sessionStorage;
      Object.keys(sess).filter((k) => k.indexOf("rinavi:") === 0).forEach((k) => sess.removeItem(k));
    } catch (e) { /* nothing to do */ }
  };
})();
