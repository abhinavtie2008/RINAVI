/* Page controllers. Each one renders into #view and wires its own events. */
(function () {
  "use strict";
  const R = globalThis.RINAVI;
  const S = R.store;
  const U = R.ui;
  const L = R.LABELS;
  const H = R.HUE;
  const esc = U.esc;
  const PURPOSE = S.PURPOSE;
  const P = (R.pages = {});

  const FIELD_HUE = {
    full_name: "h-lav", father_name: "h-lav", date_of_birth: "h-lav", gender: "h-lav",
    address: "h-peach", annual_income: "h-mint",
  };
  const SERVICE_SLUG = "delhi-income-certificate";
  const serviceHref = (slug) => "service.html?slug=" + encodeURIComponent(slug);

  async function ensureConsent(purpose, confirmLabel) {
    if (S.hasConsent(purpose)) return true;
    const info = L.purpose[purpose];
    const ok = await U.confirm({
      title: `Allow ${info.label.toLowerCase()}?`,
      body: `${info.description} You can withdraw this at any time.`,
      confirmLabel: confirmLabel || "Allow",
    });
    if (ok) S.grant(purpose);
    return ok;
  }

  const backLink = (href, label) => `<a class="back" href="${href}">${esc(label)}</a>`;
  const head = (title, lead, extra) =>
    `<div class="page-head"><h1>${esc(title)}</h1>${lead ? `<p class="lead">${esc(lead)}</p>` : ""}${extra || ""}</div>`;
  const notFound = (view, href, label, what) => {
    view.innerHTML = backLink(href, label) + U.empty(`We couldn't find that ${what}`, "It may have been deleted, or it was never saved in this browser.", `<a class="btn" href="${href}">${esc(label)}</a>`);
  };

  /* ================= landing ================= */
  P.landing = (view) => {
    const user = S.user();
    const next = U.safeNext(U.params().get("next"));
    const start = user
      ? `<div id="start" class="panel tint h-lav stack">
           <h2 style="font-size:1.4rem">Welcome back, ${esc(user.name)}</h2>
           <div class="cluster"><a class="btn" href="${next || "dashboard.html"}">Continue</a><button class="btn btn-ghost" data-act="signout">Sign out</button></div>
         </div>`
      : `<form id="start" class="panel tint h-lav stack" novalidate>
           <div class="field"><label for="name">What should we call you?</label>
           <input id="name" type="text" autocomplete="given-name" placeholder="Your first name" maxlength="60"></div>
           <div class="cluster"><button class="btn" type="submit">Start the demo</button>
           <span class="small muted">No account or password. Your demo data stays in this browser.</span></div>
         </form>`;

    view.innerHTML = `
    <section class="wrap hero">
      <div class="hero-copy">
        <h1>Not another government portal. Your companion across all of them.</h1>
        <p class="lead">RINAVI helps you prepare and track applications for Indian government services. It explains, organises and checks. You review everything and submit on the official portal yourself.</p>
        ${start}
      </div>
      <aside class="slip" aria-label="Example of a prepared application draft">
        <div class="slip-head"><strong>Income certificate (Delhi)</strong>${U.chip("Draft for your review", "h-butter", true)}</div>
        <dl class="slip-fields">
          <div><dt>Applicant name</dt><dd>Asha Verma ${U.chip("identity-card-sample.txt, line 2", "h-lav")}</dd></div>
          <div><dt>Date of birth</dt><dd>1994-03-12 ${U.chip("identity-card-sample.txt, line 4", "h-lav")}</dd></div>
          <div><dt>Residence address</dt><dd>14 Sample Lane, Rohini, Delhi 110085 ${U.chip("address-proof-sample.txt, line 3", "h-peach")}</dd></div>
          <div><dt>Annual income (INR)</dt><dd>240000 ${U.chip("income-statement-sample.txt, line 5", "h-mint")}</dd></div>
          <div class="missing"><dt>Purpose of certificate</dt><dd>Still needed from you</dd></div>
        </dl>
        <p class="slip-foot">Every value shows where it came from. You make the declaration and submit it yourself.</p>
      </aside>
    </section>

    <section class="wrap section" style="padding-top:8px">
      <div class="section-head"><h2>Three things RINAVI will not do</h2></div>
      <div class="grid-3">
        <div class="principle h-lav"><h3>Submit for you</h3><p class="muted">RINAVI prepares a copy-ready packet. You review it, make the declaration and submit on the official portal.</p></div>
        <div class="principle h-mint"><h3>Keep your portal passwords</h3><p class="muted">You sign in to government portals yourself, so there is no password for RINAVI to store or lose.</p></div>
        <div class="principle h-peach"><h3>Get around OTP or CAPTCHA</h3><p class="muted">Those checks protect you. RINAVI leaves them exactly as the portal built them.</p></div>
      </div>
    </section>

    <section class="wrap section">
      <div class="section-head"><h2>From a pile of papers to a packet you can trust</h2>
        <p class="muted">The same path every time, and you decide how far to go.</p></div>
      <ol class="steps-list">
        <li class="h-butter"><span class="step-no">1</span><div><a class="t" href="consent.html">Choose your permissions</a><p class="muted">Everything is off until you allow it. Withdraw any permission whenever you like.</p></div><a class="btn btn-ghost btn-sm" href="consent.html">Open permissions</a></li>
        <li class="h-lav"><span class="step-no">2</span><div><a class="t" href="vault.html">Add documents to your vault</a><p class="muted">RINAVI reads them with plain rules and shows which line each value came from.</p></div><a class="btn btn-ghost btn-sm" href="vault.html">Open the vault</a></li>
        <li class="h-mint"><span class="step-no">3</span><div><a class="t" href="profile.html">Review your profile</a><p class="muted">Confirm, correct or remove each value. Nothing is used until you confirm it.</p></div><a class="btn btn-ghost btn-sm" href="profile.html">Open your profile</a></li>
        <li class="h-peach"><span class="step-no">4</span><div><a class="t" href="applications.html">Prepare an application</a><p class="muted">Drafts fill from confirmed values, check your evidence, and list what is still missing.</p></div><a class="btn btn-ghost btn-sm" href="applications.html">Open applications</a></li>
        <li class="h-sky"><span class="step-no">5</span><div><a class="t" href="locker.html">Track it in your locker</a><p class="muted">Keep the frozen packet, your reference numbers, deadlines and notes in one place.</p></div><a class="btn btn-ghost btn-sm" href="locker.html">Open the locker</a></li>
      </ol>
    </section>

    <section class="wrap section">
      <div class="section-head"><h2>Available in this demo</h2></div>
      <div class="list-panel"><ul class="list"><li class="row">
        <div class="row-main"><a class="row-title" href="${serviceHref(SERVICE_SLUG)}">Income Certificate (Delhi)</a>
          <span class="muted small">Revenue Department, Government of NCT of Delhi, through e-District.</span></div>
        <div class="cluster">${U.chip("Delhi", "h-sky")}${U.chip("e-District", "h-neutral")}<a class="btn btn-soft btn-sm" href="${serviceHref(SERVICE_SLUG)}">See the service</a></div>
      </li></ul></div>
    </section>

    <section class="wrap section" style="padding-top:8px">
      <div class="notice"><strong>This is a demo.</strong> It runs entirely in your browser: nothing you enter is sent anywhere, and it is only meant for synthetic data. Use the sample documents in the vault to try the whole journey. Read how the real system treats your data on the <a href="trust.html">trust and privacy page</a>.</div>
    </section>`;

    const form = U.$("form#start", view);
    if (form) {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        S.signIn(U.$("#name", view).value);
        U.go(next || "dashboard.html");
      });
    }
    U.on(view, "click", '[data-act="signout"]', () => {
      S.signOut();
      location.reload();
    });
    if (location.hash === "#start") {
      const input = U.$("#name", view);
      if (input) setTimeout(() => input.focus(), 0);
    }
  };

  /* ================= dashboard ================= */
  P.dashboard = (view) => {
    const user = S.user();
    const st = S.stats();
    const drafts = S.hasConsent(PURPOSE.applications) ? S.listDrafts() : [];
    const cases = S.hasConsent(PURPOSE.locker) ? S.listCases() : [];

    const steps = [
      { key: "consent", label: "Permissions", href: "consent.html", done: st.consents > 0, note: st.consents + " allowed" },
      { key: "docs", label: "Documents", href: "vault.html", done: st.processed > 0, note: st.processed + " ready" },
      { key: "profile", label: "Profile", href: "profile.html", done: st.confirmed > 0, note: st.confirmed + " confirmed" },
      { key: "draft", label: "Application", href: "applications.html", done: st.drafts > 0, note: st.drafts + " in progress" },
      { key: "locker", label: "Locker", href: "locker.html", done: st.cases > 0, note: st.cases + " tracked" },
    ];
    const nowIndex = steps.findIndex((s) => !s.done);

    let next;
    const openDraft = drafts.find((d) => d.validation.length && !d.case_id);
    const readyDraft = drafts.find((d) => !d.validation.length && !d.case_id);
    if (!st.consents) next = { hue: "h-butter", title: "Choose what RINAVI may do", text: "RINAVI asks before it touches your data. Start by looking at the four permissions.", href: "consent.html", label: "Review permissions" };
    else if (!st.processed) next = { hue: "h-lav", title: "Add your first document", text: "Upload a text file, or add the sample documents to see how extraction works.", href: "vault.html", label: "Open the vault" };
    else if (!st.confirmed) next = { hue: "h-mint", title: "Review the values RINAVI found", text: "Add values from a document to your profile, then confirm or correct each one.", href: "profile.html", label: "Review your profile" };
    else if (!st.drafts) next = { hue: "h-peach", title: "Start an application", text: "Your confirmed values can fill an income certificate draft for you to review.", href: serviceHref(SERVICE_SLUG), label: "See the income certificate" };
    else if (openDraft) next = { hue: "h-peach", title: "Finish your draft", text: `${openDraft.validation.length} ${openDraft.validation.length === 1 ? "thing is" : "things are"} still missing from your ${openDraft.service_name} draft.`, href: "draft.html?id=" + encodeURIComponent(openDraft.id), label: "Continue the draft" };
    else if (readyDraft) next = { hue: "h-mint", title: "Your draft is complete", text: "Finish it to freeze a packet and start tracking what happens on the official portal.", href: "draft.html?id=" + encodeURIComponent(readyDraft.id), label: "Review and finish" };
    else next = { hue: "h-sky", title: "Keep your locker up to date", text: "Record your reference number, acknowledgement and outcome as they arrive.", href: "locker.html", label: "Open the locker" };

    const attention = [];
    if (st.attention) attention.push(`<a href="vault.html">${st.attention} ${st.attention === 1 ? "document needs" : "documents need"} attention</a>`);
    if (S.hasConsent(PURPOSE.profile)) {
      const stale = S.listProfile().filter((v) => v.status === "stale").length;
      if (stale) attention.push(`<a href="profile.html">${stale} profile ${stale === 1 ? "value needs" : "values need"} a re-check</a>`);
    }
    const dueSoon = cases.filter((c) => c.deadline_at && !["outcome_received", "abandoned"].includes(c.status));
    dueSoon.forEach((c) => attention.push(`<a href="case.html?id=${encodeURIComponent(c.id)}">${esc(c.service_name)} has a deadline on ${esc(U.fmtDate(c.deadline_at))}</a>`));

    view.innerHTML = `
      ${head(`Hello, ${user.name}`, "Here is where your preparation stands.")}
      <div class="stack-l">
        <section class="panel panel-big tint ${next.hue} stack">
          <h2>${esc(next.title)}</h2><p>${esc(next.text)}</p>
          <div><a class="btn" href="${next.href}">${esc(next.label)}</a></div>
        </section>
        <section aria-label="Your preparation path"><ol class="path">
          ${steps.map((s, i) => `<li class="${s.done ? "done" : i === nowIndex ? "now" : ""}"><a href="${s.href}">${s.label}</a><small>${esc(s.note)}</small></li>`).join("")}
        </ol></section>
        ${attention.length ? `<section class="notice rose stack-s"><strong>Needs your attention</strong><ul class="plain">${attention.map((a) => `<li>${a}</li>`).join("")}</ul></section>` : ""}
        <section><h2 style="font-size:1.4rem;margin-bottom:12px">At a glance</h2>
          <div class="list-panel"><ul class="list">
            <li class="row"><span>Documents in your vault</span><a href="vault.html"><strong>${st.documents}</strong></a></li>
            <li class="row"><span>Profile values, confirmed or waiting for review</span><a href="profile.html"><strong>${st.confirmed} of ${st.profile}</strong></a></li>
            <li class="row"><span>Application drafts</span><a href="applications.html"><strong>${st.drafts}</strong></a></li>
            <li class="row"><span>Cases in your locker</span><a href="locker.html"><strong>${st.cases}</strong></a></li>
          </ul></div></section>
      </div>`;
  };

  /* ================= catalog ================= */
  P.catalog = (view) => {
    const services = R.catalog.services;
    view.innerHTML = `${head("Services", "Each service comes with official sources, guidance, an evidence checklist and a form template.")}
      <div class="stack-l">
        <div class="field"><label for="q">Search services</label><input id="q" type="search" placeholder="Try “income” or “Delhi”" autocomplete="off"></div>
        <div id="results" class="list-panel"></div>
        <p class="muted small">More services are planned, starting with the domicile certificate. Each one is added only after its official sources are checked.</p>
      </div>`;
    const results = U.$("#results", view);
    const draw = () => {
      const q = U.$("#q", view).value.trim().toLowerCase();
      const hits = services.filter((s) => !q || [s.name, s.geography, s.department, s.summary, s.tags.join(" ")].join(" ").toLowerCase().includes(q));
      results.innerHTML = hits.length
        ? `<ul class="list">${hits.map((s) => `<li class="row">
            <div class="row-main"><a class="row-title" href="${serviceHref(s.slug)}">${esc(s.name)}</a>
              <span class="muted">${esc(s.summary)}</span><span class="muted small">${esc(s.department)}</span></div>
            <div class="cluster">${U.chip(s.geography, "h-sky")}${U.chip("Pack " + s.latest_version, "h-neutral")}<a class="btn btn-soft btn-sm" href="${serviceHref(s.slug)}">See the service</a></div></li>`).join("")}</ul>`
        : `<div style="padding:24px" class="muted">No services match “${esc(q)}”.</div>`;
    };
    U.$("#q", view).addEventListener("input", draw);
    draw();
  };

  /* ================= service ================= */
  P.service = (view) => {
    const slug = U.params().get("slug") || SERVICE_SLUG;
    const service = R.catalog.services.find((s) => s.slug === slug);
    const pack = R.catalog.packs[slug];
    if (!service || !pack) return notFound(view, "catalog.html", "Back to services", "service");
    const g = pack.guidance;
    const user = S.user();
    const signInHref = "index.html?next=" + encodeURIComponent(serviceHref(slug)) + "#start";

    view.innerHTML = `${backLink("catalog.html", "All services")}
      ${head(service.name, service.summary, `<div class="cluster">${U.chip(service.geography, "h-sky")}${U.chip("Pack " + pack.pack_version, "h-neutral")}</div>`)}
      <div class="split"><div class="stack-l">
        <section class="stack-s"><h2 style="font-size:1.4rem">What it is</h2><p>${esc(g.what_it_is)}</p>
          <ul class="plain muted">${g.eligibility_notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></section>
        <section class="stack-s"><h2 style="font-size:1.4rem">Evidence you will need</h2>
          <div class="list-panel"><ul class="list">${pack.checklist_groups.map((grp) => `<li class="row">
            <div class="row-main"><span class="row-title">${esc(grp.label)}</span>
            <span class="muted small">${grp.accepted_classifications.length ? "Accepts " + esc(grp.accepted_classifications.map((c) => L.classification[c].toLowerCase()).join(", ")) + " documents" : "Any document you have added"}</span></div>
            ${U.chip(L.requirement[grp.requirement], H.group[grp.id], true)}</li>`).join("")}</ul></div></section>
        <section class="stack-s"><h2 style="font-size:1.4rem">What the form asks</h2>
          <div class="list-panel"><ul class="list">${pack.form_template.fields.map((f) => `<li class="row">
            <div class="row-main"><span class="row-title">${esc(f.label)}</span>
            <span class="muted small">${f.binding ? "Filled from your confirmed profile when available" : "You write this one yourself"}</span></div>
            ${U.chip(f.required ? "Required" : "Optional", f.required ? "h-rose" : "h-neutral")}</li>`).join("")}</ul></div></section>
        <section class="stack-s"><h2 style="font-size:1.4rem">How you apply on the official portal</h2>
          <ol class="plain">${g.official_channel_steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol></section>
      </div>
      <aside class="stack sticky">
        <div class="panel stack" id="cta">
          <h3>Prepare an application</h3>
          <p class="muted small">A draft fills from your confirmed profile values and lists whatever is still missing.</p>
          ${user ? `<button class="btn" data-act="start">Start a draft</button>` : `<a class="btn" href="${signInHref}">Try the demo to start</a>`}
        </div>
        <div class="panel stack-s"><dl class="kv"><dt>Fee</dt><dd>${esc(service.fee)}</dd><dt>Time</dt><dd>${esc(service.processing_time)}</dd><dt>Department</dt><dd>${esc(service.department)}</dd></dl></div>
        <div class="panel stack-s"><h3>Official sources</h3><ul class="plain">${service.sources.map((s) => `<li><a href="${esc(s.url)}" rel="noopener" target="_blank">${esc(s.title)}</a></li>`).join("")}</ul></div>
        <div class="notice">${esc(g.not_a_submission_notice)}</div>
      </aside></div>`;

    U.on(view, "click", '[data-act="start"]', async () => {
      try {
        if (!(await ensureConsent(PURPOSE.applications, "Allow and start"))) return;
        const draft = S.createDraft(slug);
        U.go("draft.html?id=" + encodeURIComponent(draft.id));
      } catch (e) {
        U.toast(U.errMsg(e, "Could not start the draft."), "error");
      }
    });
  };

  /* ================= consent ================= */
  P.consent = (view) => {
    const render = () => {
      const grants = S.listGrants();
      view.innerHTML = `${head("Permissions", "RINAVI only touches your data while the matching permission is allowed. Withdrawing one takes effect immediately. Nothing already saved is deleted for you, so delete documents and drafts yourself if you want them gone.")}
        <div class="list-panel"><ul class="list">${S.PURPOSE_LIST.map((p) => {
          const info = L.purpose[p];
          const active = grants.find((g) => g.purpose === p && g.withdrawn_at === null);
          const latest = grants.find((g) => g.purpose === p);
          const status = active ? `Allowed on ${U.fmtDate(active.granted_at)} (policy ${active.policy_version})` : latest && latest.withdrawn_at ? `Withdrawn on ${U.fmtDate(latest.withdrawn_at)}` : "Not allowed yet";
          return `<li class="row" data-purpose="${p}">
            <div class="row-main"><span class="cluster"><span class="row-title">${esc(info.label)}</span>${U.chip(active ? "Allowed" : "Off", active ? H.purpose[p] : "h-neutral", true)}</span>
              <span class="muted">${esc(info.description)}</span><span class="muted small">${esc(status)}</span></div>
            <div class="row-actions">${active ? `<button class="btn btn-ghost btn-sm" data-act="withdraw" data-id="${esc(active.id)}" data-p="${p}">Withdraw</button>` : `<button class="btn btn-soft btn-sm" data-act="allow" data-p="${p}">Allow</button>`}</div></li>`;
        }).join("")}</ul></div>
        <p class="muted small" style="margin-top:16px">Erasure never depends on permissions. You can delete documents, drafts or your whole account even after you withdraw everything.</p>`;
    };
    render();
    U.on(view, "click", "[data-act]", async (ev, el) => {
      try {
        if (el.dataset.act === "allow") {
          S.grant(el.dataset.p);
          U.toast(`${L.purpose[el.dataset.p].label} is allowed.`, "ok");
        } else {
          const info = L.purpose[el.dataset.p];
          const ok = await U.confirm({ title: `Withdraw ${info.label.toLowerCase()}?`, body: "RINAVI will ask again before using your data for this.", confirmLabel: "Withdraw" });
          if (!ok) return;
          S.withdraw(el.dataset.id);
          U.toast(`${info.label} is withdrawn.`);
        }
        render();
      } catch (e) {
        U.toast(U.errMsg(e, "Could not update that permission."), "error");
      }
    });
  };

  /* ================= vault ================= */
  P.vault = (view) => {
    const rowFor = (d, full) => {
      const note = d.note ? L.note[d.note] || d.note : "";
      return `<li class="row" data-id="${esc(d.id)}">
        <div class="row-main">
          ${full ? `<a class="row-title" href="document.html?id=${encodeURIComponent(d.id)}">${esc(d.original_filename)}</a>` : `<span class="row-title">${esc(d.original_filename)}</span>`}
          <span class="cluster">${U.chip(L.docStatus[d.status] || d.status, H.docStatus[d.status], true)}${d.status === "processed" ? U.chip(L.classification[d.classification], H.classification[d.classification]) : ""}<span class="muted small">${esc(U.fmtSize(d.size))}, added ${esc(U.fmtDate(d.created_at))}</span></span>
          ${note ? `<span class="muted small">${esc(note)}</span>` : ""}</div>
        <div class="row-actions">
          ${full ? `<a class="btn btn-ghost btn-sm" href="document.html?id=${encodeURIComponent(d.id)}">View values</a>` : ""}
          ${full && d.status === "needs_attention" && d.mime === "text/plain" ? `<button class="btn btn-ghost btn-sm" data-act="retry" data-id="${esc(d.id)}">Retry</button>` : ""}
          <button class="btn btn-danger btn-sm" data-act="delete" data-id="${esc(d.id)}">Delete</button></div></li>`;
    };

    const render = () => {
      const docs = S.listDocuments();
      if (!S.hasConsent(PURPOSE.documents)) {
        view.innerHTML = head("Vault", "Your documents, read only with your permission.") +
          U.gate(PURPOSE.documents, "RINAVI reads your documents only after you allow it. Nothing is uploaded until then, and you can delete anything at any time.", "Allow document processing") +
          (docs.length ? `<h2 style="font-size:1.3rem;margin:32px 0 12px">Documents already in this browser</h2><div class="list-panel"><ul class="list">${docs.map((d) => rowFor(d, false)).join("")}</ul></div>` : "");
        return;
      }
      view.innerHTML = `${head("Vault", "Add a document and RINAVI reads the lines it recognises. It never guesses: every value shows the line it came from.")}
        <div class="stack-l">
          <div class="drop stack" id="drop">
            <p><strong>Drop a file here</strong> or choose one</p>
            <div class="cluster" style="justify-content:center"><label class="btn btn-soft" for="file">Choose files</label><input id="file" class="sr-only" type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.txt"></div>
            <p class="muted small">PDF, PNG, JPEG or TXT, up to 10 MB. This demo reads text files only.</p>
          </div>
          <section class="stack-s"><h2 style="font-size:1.3rem">No documents handy? Use a sample</h2>
            <p class="muted small">Synthetic documents for a made-up person. They fill the whole income certificate journey.</p>
            <div class="cluster">${R.SAMPLES.map((s) => `<button class="btn btn-ghost btn-sm" data-act="sample" data-key="${s.key}">${U.chip(s.title, s.hue)} Add ${esc(s.title.toLowerCase())}</button>`).join("")}</div></section>
          <section><h2 style="font-size:1.3rem;margin-bottom:12px">Your documents</h2>
            ${docs.length ? `<div class="list-panel"><ul class="list">${docs.map((d) => rowFor(d, true)).join("")}</ul></div>` : U.empty("Nothing here yet", "Choose a file or add a sample document to get started.")}</section>
        </div>`;
    };
    render();
    U.bindGate(view, render);

    async function addFiles(files) {
      for (const file of files) {
        try {
          let text = null;
          if (/\.txt$/i.test(file.name) && file.size <= S.MAX_UPLOAD) text = await file.text();
          const doc = S.addDocument({ name: file.name, size: file.size }, text);
          U.toast(doc.status === "processed" ? `${doc.original_filename} is ready.` : `${doc.original_filename} needs attention.`, doc.status === "processed" ? "ok" : "");
        } catch (e) {
          U.toast(`${file.name}: ${U.errMsg(e, "Upload failed.")}`, "error");
        }
      }
      render();
    }
    view.addEventListener("change", (e) => {
      if (e.target.id === "file") addFiles(Array.from(e.target.files));
    });
    view.addEventListener("dragover", (e) => {
      const z = e.target.closest("#drop");
      if (z) { e.preventDefault(); z.classList.add("over"); }
    });
    view.addEventListener("dragleave", (e) => {
      const z = e.target.closest("#drop");
      if (z) z.classList.remove("over");
    });
    view.addEventListener("drop", (e) => {
      const z = e.target.closest("#drop");
      if (z) { e.preventDefault(); z.classList.remove("over"); addFiles(Array.from(e.dataTransfer.files)); }
    });
    U.on(view, "click", "[data-act]", async (ev, el) => {
      try {
        const act = el.dataset.act;
        if (act === "sample") {
          const s = R.SAMPLES.find((x) => x.key === el.dataset.key);
          S.addDocument({ name: s.filename, size: s.text.length }, s.text);
          U.toast(`${s.title} added.`, "ok");
        } else if (act === "retry") {
          const d = S.retryDocument(el.dataset.id);
          U.toast(d.status === "processed" ? "Document is ready." : "Still needs attention.");
        } else if (act === "delete") {
          const ok = await U.confirm({ title: "Delete this document?", body: "This cannot be undone. Profile values that came from it will need a re-check.", confirmLabel: "Delete", danger: true });
          if (!ok) return;
          S.deleteDocument(el.dataset.id);
          U.toast("Document deleted.");
        }
        render();
      } catch (e) {
        U.toast(U.errMsg(e), "error");
        render();
      }
    });
  };

  /* ================= document ================= */
  P.document = (view) => {
    const id = U.params().get("id");
    const render = () => {
      let d;
      try { d = S.getDocument(id); } catch (e) { return notFound(view, "vault.html", "Back to the vault", "document"); }
      if (!S.hasConsent(PURPOSE.documents)) {
        view.innerHTML = backLink("vault.html", "Back to the vault") + U.gate(PURPOSE.documents, "Reading this document's values needs your permission.", "Allow document processing");
        return;
      }
      const text = S.getDocumentText(id);
      const hit = new Set(d.fields.map((f) => Number(f.locator.replace("line ", ""))));
      const lines = text === null ? [] : text.split(/\r?\n/);
      const note = d.note ? L.note[d.note] || d.note : "";
      view.innerHTML = `${backLink("vault.html", "Back to the vault")}
        ${head(d.original_filename, "", `<div class="cluster">${U.chip(L.docStatus[d.status], H.docStatus[d.status], true)}${d.status === "processed" ? U.chip(L.classification[d.classification] + " document", H.classification[d.classification]) : ""}<span class="muted small">${esc(U.fmtSize(d.size))}, added ${esc(U.fmtDate(d.created_at))}</span></div>`)}
        <div class="split"><div class="stack-l">
          ${note ? `<div class="notice rose">${esc(note)}</div>` : ""}
          <section class="stack-s"><h2 style="font-size:1.4rem">Values RINAVI found</h2>
            ${d.fields.length ? `<div class="list-panel"><ul class="list">${d.fields.map((f) => `<li class="row">
              <div class="row-main"><span class="muted small">${esc(L.field[f.field_key] || f.field_key)}</span><span class="row-title">${esc(f.value)}</span></div>
              <div class="cluster">${U.chip(f.confidence === "high" ? "High confidence" : "Low confidence, check it", f.confidence === "high" ? "h-mint" : "h-butter")}${U.chip(f.locator, "h-neutral")}</div></li>`).join("")}</ul></div>`
              : `<p class="muted">No values were found in this file.</p>`}
            ${d.classification === "identity" ? `<p class="muted small">RINAVI recognised an Aadhaar line but never keeps the number. Enter it yourself on the official portal.</p>` : ""}
          </section>
          ${lines.length ? `<section class="stack-s"><h2 style="font-size:1.4rem">The text, line by line</h2><p class="muted small">Highlighted lines are where the values came from.</p>
            <div class="lines" role="region" aria-label="Document text">${lines.map((t, i) => `<div class="${hit.has(i + 1) ? "hit" : ""}"><span class="n">${i + 1}</span><span class="t">${esc(t) || "&nbsp;"}</span></div>`).join("")}</div></section>` : ""}
        </div>
        <aside class="stack sticky"><div class="panel stack">
          <h3>Use these values</h3><p class="muted small">Add them to your profile as “needs review”. Nothing reaches an application until you confirm it.</p>
          <button class="btn" data-act="promote" ${d.status === "processed" && d.fields.length ? "" : "disabled"}>Add to my profile</button>
          <button class="btn btn-danger btn-sm" data-act="delete">Delete this document</button></div></aside></div>`;
    };
    render();
    U.bindGate(view, render);
    U.on(view, "click", "[data-act]", async (ev, el) => {
      try {
        if (el.dataset.act === "promote") {
          if (!(await ensureConsent(PURPOSE.profile, "Allow and add"))) return;
          const r = S.promote(id);
          U.toast(`Added ${r.added} ${r.added === 1 ? "value" : "values"} for review${r.kept ? `, kept ${r.kept} you already confirmed` : ""}.`, "ok");
          U.go("profile.html");
        } else if (el.dataset.act === "delete") {
          const ok = await U.confirm({ title: "Delete this document?", body: "This cannot be undone. Profile values that came from it will need a re-check.", confirmLabel: "Delete", danger: true });
          if (!ok) return;
          S.deleteDocument(id);
          U.go("vault.html");
        }
      } catch (e) {
        U.toast(U.errMsg(e), "error");
      }
    });
  };

  /* ================= profile ================= */
  P.profile = (view) => {
    let correcting = null;
    const render = () => {
      if (!S.hasConsent(PURPOSE.profile)) {
        view.innerHTML = head("Profile", "The values RINAVI may use to fill your applications.") +
          U.gate(PURPOSE.profile, "Your profile is stored only after you allow it. Values stay marked as needing review until you confirm or correct them.", "Allow profile storage");
        return;
      }
      const values = S.listProfile();
      const docs = S.listDocuments().filter((d) => d.status === "processed" && d.fields.length);
      view.innerHTML = `${head("Profile", "Every value keeps its source. Confirm what is right, correct what is not, and remove what you don't want. Only confirmed values fill a draft.")}
        <div class="stack-l">
          ${docs.length ? `<section class="stack-s"><h2 style="font-size:1.3rem">Add values from a document</h2>
            <div class="list-panel"><ul class="list">${docs.map((d) => `<li class="row"><div class="row-main"><a class="row-title" href="document.html?id=${encodeURIComponent(d.id)}">${esc(d.original_filename)}</a><span>${U.chip(L.classification[d.classification], H.classification[d.classification])}</span></div>
              <button class="btn btn-soft btn-sm" data-act="promote" data-id="${esc(d.id)}">Use this document</button></li>`).join("")}</ul></div></section>` : ""}
          <section class="stack-s"><h2 style="font-size:1.3rem">Your values</h2>
            ${values.length ? `<div class="list-panel"><ul class="list">${values.map((v) => {
              const label = L.field[v.field_key] || v.field_key;
              return `<li class="row" data-id="${esc(v.id)}">
                <div class="row-main"><span class="muted small">${esc(label)}</span><span class="row-title">${esc(v.value)}</span>
                  <span class="cluster">${U.chip(L.profileStatus[v.status], H.profileStatus[v.status], true)}${v.confidence === "low" && v.status === "unconfirmed" ? U.chip("Low confidence", "h-butter") : ""}${v.corrected ? U.chip("Corrected by you", "h-neutral") : ""}
                  <span class="muted small">${v.status === "stale" ? esc("Source changed: " + (v.stale_reason || "source document deleted")) : "From " + esc(v.source_locator)}</span></span>
                  ${correcting === v.id ? `<form class="inline-form" data-form="correct" data-id="${esc(v.id)}" style="margin-top:8px"><input type="text" aria-label="Correct ${esc(label)}" value="${esc(v.value)}" maxlength="500"><button class="btn btn-sm" type="submit">Save</button><button class="btn btn-ghost btn-sm" type="button" data-act="cancel">Cancel</button></form>` : ""}</div>
                <div class="row-actions">${v.status === "unconfirmed" ? `<button class="btn btn-sm" data-act="confirm" data-id="${esc(v.id)}">Confirm</button>` : ""}
                  <button class="btn btn-ghost btn-sm" data-act="correct" data-id="${esc(v.id)}">Correct</button>
                  ${v.status !== "confirmed" ? `<button class="btn btn-danger btn-sm" data-act="remove" data-id="${esc(v.id)}">Remove</button>` : ""}</div></li>`;
            }).join("")}</ul></div>` : U.empty("No profile values yet", "Add a document to your vault, then bring its values here to review.", '<a class="btn" href="vault.html">Open the vault</a>')}
          </section>
          <p class="muted small">Aadhaar numbers are never stored here. You enter them on the official portal yourself.</p>
        </div>`;
      const input = U.$("form[data-form=correct] input", view);
      if (input) input.focus();
    };
    render();
    U.bindGate(view, render);
    U.on(view, "click", "[data-act]", (ev, el) => {
      try {
        const act = el.dataset.act;
        if (act === "promote") {
          const r = S.promote(el.dataset.id);
          U.toast(`Added ${r.added} ${r.added === 1 ? "value" : "values"} for review${r.kept ? `, kept ${r.kept} you already confirmed` : ""}.`, "ok");
        } else if (act === "confirm") {
          S.confirmValue(el.dataset.id);
          U.toast("Confirmed.", "ok");
        } else if (act === "correct") {
          correcting = el.dataset.id;
        } else if (act === "cancel") {
          correcting = null;
        } else if (act === "remove") {
          S.rejectValue(el.dataset.id);
          U.toast("Value removed.");
        }
        render();
      } catch (e) {
        U.toast(U.errMsg(e), "error");
        render();
      }
    });
    view.addEventListener("submit", (e) => {
      const form = e.target.closest("form[data-form=correct]");
      if (!form) return;
      e.preventDefault();
      try {
        S.correctValue(form.dataset.id, form.querySelector("input").value);
        correcting = null;
        U.toast("Saved and confirmed.", "ok");
      } catch (err) {
        U.toast(U.errMsg(err), "error");
      }
      render();
    });
  };

  /* ================= applications ================= */
  P.applications = (view) => {
    const render = () => {
      if (!S.hasConsent(PURPOSE.applications)) {
        const stubs = S.listDraftStubs();
        view.innerHTML = head("Applications", "Drafts you are preparing for official portals.") +
          U.gate(PURPOSE.applications, "RINAVI fills drafts from your profile and documents only after you allow it.", "Allow application preparation") +
          (stubs.length ? `<h2 style="font-size:1.3rem;margin:32px 0 12px">Drafts already in this browser</h2><p class="muted small" style="margin-bottom:12px">You can delete these without allowing anything.</p><div class="list-panel"><ul class="list">${stubs.map((d) => `<li class="row"><div class="row-main"><span class="row-title">${esc(d.service_name)}</span><span class="muted small">Started ${esc(U.fmtDate(d.created_at))}</span></div><button class="btn btn-danger btn-sm" data-act="delete" data-id="${esc(d.id)}">Delete</button></li>`).join("")}</ul></div>` : "");
        return;
      }
      const drafts = S.listDrafts();
      view.innerHTML = `${head("Applications", "Drafts you are preparing for official portals. RINAVI never submits them.", '<div><a class="btn btn-soft" href="catalog.html">Start a new application</a></div>')}
        ${drafts.length ? `<div class="list-panel"><ul class="list">${drafts.map((d) => {
          const n = d.validation.length;
          const chip = d.case_id ? U.chip("In your locker", "h-sky", true) : n ? U.chip(`${n} ${n === 1 ? "thing" : "things"} left`, "h-butter", true) : U.chip("Ready to finish", "h-mint", true);
          return `<li class="row"><div class="row-main"><a class="row-title" href="draft.html?id=${encodeURIComponent(d.id)}">${esc(d.service_name)}</a>
            <span class="cluster">${chip}<span class="muted small">Pack ${esc(d.pack_version)}, updated ${esc(U.fmtDate(d.updated_at))}</span></span></div>
            <div class="row-actions"><a class="btn btn-ghost btn-sm" href="draft.html?id=${encodeURIComponent(d.id)}">Open</a><button class="btn btn-danger btn-sm" data-act="delete" data-id="${esc(d.id)}">Delete</button></div></li>`;
        }).join("")}</ul></div>` : U.empty("No drafts yet", "Pick a service to start. The draft fills from your confirmed profile values.", '<a class="btn" href="catalog.html">Browse services</a>')}`;
    };
    render();
    U.bindGate(view, render);
    U.on(view, "click", '[data-act="delete"]', async (ev, el) => {
      const ok = await U.confirm({ title: "Delete this draft?", body: "This cannot be undone. Packets already in your locker are not affected.", confirmLabel: "Delete", danger: true });
      if (!ok) return;
      try { S.deleteDraft(el.dataset.id); U.toast("Draft deleted."); } catch (e) { U.toast(U.errMsg(e), "error"); }
      render();
    });
  };

  /* ================= draft ================= */
  P.draft = (view) => {
    const id = U.params().get("id");
    const drafting = {};
    const picks = {};
    let exportText = null;
    let suggestions = U.readSuggestions(id);

    const render = () => {
      if (!S.listDraftStubs().some((d) => d.id === id)) return notFound(view, "applications.html", "Back to applications", "draft");
      if (!S.hasConsent(PURPOSE.applications)) {
        view.innerHTML = backLink("applications.html", "All applications") +
          `<div class="stack-l">${U.gate(PURPOSE.applications, "Opening this draft needs your permission to prepare applications.", "Allow application preparation")}
          <div><button class="btn btn-danger btn-sm" data-act="delete">Delete this draft instead</button></div></div>`;
        return;
      }
      const d = S.getDraft(id);
      const t = d.template_snapshot;
      const issues = d.validation;
      const docs = S.listDocuments();
      const processed = docs.filter((x) => x.status === "processed");

      const fieldsHtml = t.fields.map((f) => {
        const entry = d.values[f.id];
        const fromProfile = entry && entry.origin === "profile";
        const value = drafting[f.id] !== undefined ? drafting[f.id] : entry ? entry.value : "";
        const fieldIssues = issues.filter((i) => i.field_id === f.id);
        return `<form class="field" data-form="field" data-id="${esc(f.id)}">
          <label for="f-${esc(f.id)}">${esc(f.label)}${f.required ? ' <span class="hint">(required)</span>' : ""}</label>
          <div class="inline-form"><input id="f-${esc(f.id)}" type="text" data-field="${esc(f.id)}" value="${esc(value)}" maxlength="500" ${fromProfile ? "disabled" : ""} ${fieldIssues.length ? 'aria-invalid="true"' : ""}>
            ${fromProfile ? "" : '<button class="btn btn-soft btn-sm" type="submit">Save</button>'}</div>
          ${fromProfile ? `<div class="cluster">${U.chip("From your profile", FIELD_HUE[f.binding] || "h-lav", true)}<span class="muted small">${esc(entry.source || "")}. To change it, <a href="profile.html">correct it in your profile</a>.</span></div>` : ""}
          ${fieldIssues.map((i) => `<p class="error-text">${esc(i.message)}</p>`).join("")}</form>`;
      }).join("");

      const groupsHtml = t.checklist_groups.map((g) => {
        const linked = d.document_links[g.id] || [];
        const eligible = processed.filter((x) => !g.accepted_classifications.length || g.accepted_classifications.includes(x.classification));
        const gi = issues.filter((i) => i.group_id === g.id);
        return `<section class="panel stack-s" id="g-${esc(g.id)}">
          <div class="between"><h3>${esc(g.label)}</h3>${U.chip(L.requirement[g.requirement], H.group[g.id], true)}</div>
          ${g.accepted_classifications.length ? `<p class="muted small">Accepts ${esc(g.accepted_classifications.map((c) => L.classification[c].toLowerCase()).join(", "))} documents.</p>` : ""}
          ${linked.length ? `<ul class="list">${linked.map((docId) => {
            const doc = docs.find((x) => x.id === docId);
            return `<li class="row" style="padding:8px 0"><span>${esc(doc ? doc.original_filename : "Unavailable document")}</span><button class="btn btn-ghost btn-sm" data-act="unlink" data-doc="${esc(docId)}">Remove</button></li>`;
          }).join("")}</ul>` : ""}
          <div class="inline-form"><select aria-label="Attach a document to ${esc(g.label)}" data-pick="${esc(g.id)}"><option value="">Choose a document…</option>
            ${eligible.map((x) => `<option value="${esc(x.id)}" ${picks[g.id] === x.id ? "selected" : ""}>${esc(x.original_filename)}</option>`).join("")}</select>
            <button class="btn btn-soft btn-sm" data-act="attach" data-group="${esc(g.id)}" ${picks[g.id] ? "" : "disabled"}>Attach</button></div>
          ${!eligible.length ? `<p class="muted small">No matching documents yet. <a href="vault.html">Add one in the vault</a>.</p>` : ""}
          ${gi.map((i) => `<p class="error-text">${esc(i.message)}</p>`).join("")}</section>`;
      }).join("");

      const sugHtml = suggestions.length ? `<section class="panel tint h-sky stack-s"><h3>Suggested from your previous application</h3>
        ${suggestions.map((s, i) => {
          const doc = docs.find((x) => x.id === s.document_id);
          const grp = t.checklist_groups.find((x) => x.id === s.group_id);
          return `<div class="between"><span>${esc(doc ? doc.original_filename : s.document_id)}, for ${esc(grp ? grp.label : s.group_id)}</span><button class="btn btn-sm" data-act="accept" data-i="${i}">Attach</button></div>`;
        }).join("")}</section>` : "";

      const anchor = (i) => (i.field_id ? "#f-" + i.field_id : i.group_id ? "#g-" + i.group_id : "#declaration");
      const aside = d.case_id
        ? `<div class="panel stack"><h3>Already in your locker</h3><p class="muted small">A frozen copy of this draft is being tracked.</p><a class="btn" href="case.html?id=${encodeURIComponent(d.case_id)}">Open in your locker</a></div>`
        : issues.length
          ? `<div class="panel stack"><h3>${issues.length} ${issues.length === 1 ? "thing is" : "things are"} left</h3><ul class="plain small">${issues.map((i) => `<li><a href="${esc(anchor(i))}">${esc(i.message)}</a></li>`).join("")}</ul></div>`
          : `<div class="panel tint h-mint stack"><h3>This draft is complete</h3><p class="small">Finish it to freeze a packet and start tracking.</p><button class="btn" data-act="complete">Finish and start tracking</button></div>`;

      view.innerHTML = `${backLink("applications.html", "All applications")}
        ${head(d.service_name, "", `<div class="cluster">${U.chip("Pack " + d.pack_version, "h-neutral")}<a class="small" href="${serviceHref(d.service_slug)}">About this service</a></div>`)}
        <div class="notice" style="margin-bottom:28px" data-testid="submission-notice">${esc(t.guidance.not_a_submission_notice)}</div>
        <div class="split"><div class="stack-l">
          ${sugHtml}
          <section class="stack"><h2 style="font-size:1.4rem">Application details</h2>${fieldsHtml}</section>
          <section class="stack"><h2 style="font-size:1.4rem">Evidence checklist</h2>${groupsHtml}</section>
          <section class="stack-s"><h2 style="font-size:1.4rem">Declaration</h2>
            <label class="check" for="declaration"><input id="declaration" type="checkbox" ${d.declaration_confirmed ? "checked" : ""}><span>${esc(t.declaration.text)}</span></label>
            <p class="muted small">This only records that you have read it. You make the official declaration on the portal.</p></section>
          <section class="stack-s"><h2 style="font-size:1.4rem">Official submission steps</h2><ol class="plain">${t.guidance.official_channel_steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>
            <p class="muted small">${esc(t.processing_time)}</p></section>
          ${exportText !== null ? `<section class="stack-s"><h2 style="font-size:1.4rem">Final draft preview</h2><pre class="export" data-testid="export-text">${esc(exportText)}</pre></section>` : ""}
        </div>
        <aside class="stack sticky">${aside}
          <div class="panel stack-s"><h3>Tools</h3>
            <button class="btn btn-ghost btn-sm" data-act="refresh">Refresh from profile</button>
            <button class="btn btn-ghost btn-sm" data-act="preview">Preview final draft</button>
            <button class="btn btn-danger btn-sm" data-act="delete">Delete draft</button></div></aside></div>`;
    };

    const run = (fn, onOk) => {
      try { fn(); if (onOk) onOk(); } catch (e) {
        if (e.status === 409) U.toast("Resolve the highlighted issues first.", "error");
        else if (e.status === 403) { /* the gate shows after render */ } else U.toast(U.errMsg(e), "error");
      }
      render();
    };
    render();
    U.bindGate(view, render);

    view.addEventListener("input", (e) => {
      if (e.target.dataset && e.target.dataset.field) drafting[e.target.dataset.field] = e.target.value;
    });
    view.addEventListener("change", (e) => {
      const t = e.target;
      if (t.id === "declaration") run(() => S.setDeclaration(id, t.checked), () => { exportText = null; });
      else if (t.dataset && t.dataset.pick !== undefined) { picks[t.dataset.pick] = t.value; render(); }
    });
    view.addEventListener("submit", (e) => {
      const form = e.target.closest("form[data-form=field]");
      if (!form) return;
      e.preventDefault();
      const fid = form.dataset.id;
      run(() => S.setField(id, fid, form.querySelector("input").value), () => { delete drafting[fid]; exportText = null; U.toast("Saved.", "ok"); });
    });
    U.on(view, "click", "[data-act]", async (ev, el) => {
      const act = el.dataset.act;
      if (act === "attach") {
        const g = el.dataset.group;
        run(() => S.linkDocument(id, picks[g], g), () => { picks[g] = ""; exportText = null; });
      } else if (act === "unlink") run(() => S.unlinkDocument(id, el.dataset.doc), () => { exportText = null; });
      else if (act === "accept") {
        const s = suggestions[Number(el.dataset.i)];
        run(() => S.linkDocument(id, s.document_id, s.group_id), () => {
          suggestions = suggestions.filter((x) => x !== s);
          U.writeSuggestions(id, suggestions);
        });
      } else if (act === "refresh") run(() => S.refreshDraft(id), () => { Object.keys(drafting).forEach((k) => delete drafting[k]); exportText = null; U.toast("Refreshed from your confirmed profile values."); });
      else if (act === "preview") run(() => { exportText = S.exportDraft(id).text; });
      else if (act === "complete") {
        try {
          if (!(await ensureConsent(PURPOSE.locker, "Allow and finish"))) return;
          const c = S.completeDraft(id);
          U.go("case.html?id=" + encodeURIComponent(c.id));
        } catch (e) {
          U.toast(e.status === 409 ? "Resolve the highlighted issues first." : U.errMsg(e, "Could not finish the draft."), "error");
        }
      } else if (act === "delete") {
        const ok = await U.confirm({ title: "Delete this draft?", body: "This cannot be undone. Packets already in your locker are not affected.", confirmLabel: "Delete", danger: true });
        if (!ok) return;
        try { S.deleteDraft(id); U.writeSuggestions(id, []); U.go("applications.html"); } catch (e) { U.toast(U.errMsg(e), "error"); }
      }
    });
  };

  /* ================= locker ================= */
  P.locker = (view) => {
    const render = () => {
      if (!S.hasConsent(PURPOSE.locker)) {
        view.innerHTML = head("Locker", "Your frozen packets and what happened to each application.") +
          U.gate(PURPOSE.locker, "RINAVI records what happens to an application only after you allow it. You file on the official portal; RINAVI just keeps your notes.", "Allow application tracking");
        return;
      }
      const cases = S.listCases();
      view.innerHTML = `${head("Locker", "Frozen packets, reference numbers, deadlines and notes. RINAVI can't see the portal, so you tell it what happened.")}
        ${cases.length ? `<div class="list-panel"><ul class="list">${cases.map((c) => `<li class="row">
          <div class="row-main"><a class="row-title" href="case.html?id=${encodeURIComponent(c.id)}">${esc(c.service_name)}</a>
            <span class="cluster">${U.chip(L.caseStatus[c.status], H.caseStatus[c.status], true)}<span class="muted small">Prepared ${esc(U.fmtDate(c.created_at))}</span>
            ${c.reference_number ? `<span class="muted small">Reference ${esc(c.reference_number)}</span>` : ""}${c.deadline_at ? `<span class="muted small">Deadline ${esc(U.fmtDate(c.deadline_at))}</span>` : ""}</span></div>
          <a class="btn btn-ghost btn-sm" href="case.html?id=${encodeURIComponent(c.id)}">Open</a></li>`).join("")}</ul></div>`
          : U.empty("Nothing in your locker yet", "Finish a complete draft and its packet will be frozen here.", '<a class="btn" href="applications.html">Go to applications</a>')}`;
    };
    render();
    U.bindGate(view, render);
  };

  /* ================= case ================= */
  const UNCERTAIN_NOTICE = "Not sure whether it went through? Check the portal for your reference number before trying again. RINAVI cannot tell what happened on the portal.";
  function eventLabel(ev) {
    const p = ev.payload || {};
    switch (ev.type) {
      case "created": return "Application prepared";
      case "submitted": return p.reference_number ? `Marked as submitted, reference ${p.reference_number}` : "Marked as submitted";
      case "acknowledged": return p.acknowledgement_number ? `Acknowledgement recorded, ${p.acknowledgement_number}` : "Acknowledgement recorded";
      case "outcome_received": return p.outcome_notes ? `Outcome recorded: ${p.outcome_notes}` : "Outcome recorded";
      case "deadline_updated": return p.deadline_at ? `Deadline set to ${U.fmtDate(p.deadline_at)}` : "Deadline cleared";
      case "abandoned": return "Marked as abandoned";
      case "uncertain": return "Marked as uncertain";
      default: return ev.type;
    }
  }
  const EVENT_HUE = { created: "h-lav", submitted: "h-sky", acknowledged: "h-mint", outcome_received: "h-mint", deadline_updated: "h-butter", abandoned: "h-neutral", uncertain: "h-butter" };

  P.case = (view) => {
    const id = U.params().get("id");
    const render = () => {
      if (!S.hasConsent(PURPOSE.locker)) {
        view.innerHTML = backLink("locker.html", "Back to the locker") + U.gate(PURPOSE.locker, "Opening this case needs your permission to track applications.", "Allow application tracking");
        return;
      }
      let c;
      try { c = S.getCase(id); } catch (e) { return notFound(view, "locker.html", "Back to the locker", "case"); }
      const snap = c.packet_snapshot;
      view.innerHTML = `${backLink("locker.html", "Back to the locker")}
        ${head(c.service_name, "", `<div class="cluster">${U.chip(L.caseStatus[c.status], H.caseStatus[c.status], true)}<span class="muted small">Pack ${esc(c.pack_version)}, prepared ${esc(U.fmtDate(c.created_at))}</span></div>`)}
        <div class="split"><div class="stack-l">
          <section class="panel stack"><dl class="kv">
            <dt>Reference number</dt><dd>${esc(c.reference_number || "Not recorded")}</dd>
            <dt>Acknowledgement number</dt><dd>${esc(c.acknowledgement_number || "Not recorded")}</dd>
            <dt>Deadline</dt><dd>${c.deadline_at ? esc(U.fmtDate(c.deadline_at)) : "No deadline recorded"}</dd>
            ${c.outcome_notes ? `<dt>Outcome</dt><dd>${esc(c.outcome_notes)}</dd>` : ""}</dl>
            ${c.status === "submitted" && !c.acknowledgement_number ? `<p class="muted small" data-testid="acknowledgement-note">${esc(snap.acknowledgement_guidance)}</p>` : ""}
            ${c.status === "submitted" ? `<p class="muted small" data-testid="portal-down-guidance">${esc(snap.portal_down_guidance)}</p>` : ""}</section>
          <section class="stack-s"><h2 style="font-size:1.4rem">Journal</h2>
            <ol class="journal" data-testid="case-journal">${c.events.slice().reverse().map((ev) => `<li class="${EVENT_HUE[ev.type] || "h-lav"}"><p>${esc(eventLabel(ev))}</p><p class="muted small">${esc(U.fmtDateTime(ev.created_at))}</p></li>`).join("")}</ol></section>
          <section class="stack-s"><h2 style="font-size:1.4rem">Record an update</h2>
            <div class="list-panel"><ul class="list">
              <li class="row"><form class="inline-form grow" data-form="submitted"><label class="sr-only" for="ref">Reference number</label><input id="ref" type="text" placeholder="Reference number (optional)" maxlength="200"><button class="btn btn-soft btn-sm" type="submit">Mark as submitted</button></form></li>
              <li class="row"><form class="inline-form grow" data-form="acknowledged"><label class="sr-only" for="ack">Acknowledgement number</label><input id="ack" type="text" placeholder="Acknowledgement number (optional)" maxlength="200"><button class="btn btn-soft btn-sm" type="submit">Mark as acknowledged</button></form></li>
              <li class="row"><form class="inline-form grow" data-form="outcome_received"><label class="sr-only" for="out">Outcome notes</label><input id="out" type="text" placeholder="Outcome notes" maxlength="200"><button class="btn btn-soft btn-sm" type="submit">Mark outcome received</button></form></li>
              <li class="row"><form class="inline-form grow" data-form="deadline"><label class="sr-only" for="dl">Deadline</label><input id="dl" type="date" value="${esc(c.deadline_at || "")}"><button class="btn btn-soft btn-sm" type="submit">Set deadline</button><button class="btn btn-ghost btn-sm" type="button" data-act="clear-deadline">Clear</button></form></li>
              <li class="row"><div class="grow stack-s"><p class="muted small">${esc(UNCERTAIN_NOTICE)}</p><div class="cluster"><button class="btn btn-ghost btn-sm" data-act="uncertain">Mark as uncertain</button><button class="btn btn-ghost btn-sm" data-act="abandoned">Mark as abandoned</button></div></div></li>
            </ul></div></section>
        </div>
        <aside class="stack sticky">
          <div class="panel stack"><h3>Your packet</h3><p class="muted small">The copy of your application, frozen when you finished the draft.</p>
            <a class="btn" href="packet.html?id=${encodeURIComponent(c.id)}" data-testid="packet-link">View packet</a>
            <button class="btn btn-soft" data-act="again" data-testid="apply-again">Apply again</button></div>
          <div class="notice">${esc(snap.not_a_submission_notice)}</div></aside></div>`;
    };
    render();
    U.bindGate(view, render);

    const record = (input, msg) => {
      try { S.recordEvent(id, input); if (msg) U.toast(msg, "ok"); } catch (e) { U.toast(U.errMsg(e, "Could not record the update."), "error"); }
      render();
    };
    view.addEventListener("submit", (e) => {
      const form = e.target.closest("form[data-form]");
      if (!form) return;
      e.preventDefault();
      const v = form.querySelector("input").value;
      const kind = form.dataset.form;
      if (kind === "submitted") record({ type: "submitted", reference_number: v }, "Marked as submitted.");
      else if (kind === "acknowledged") record({ type: "acknowledged", acknowledgement_number: v }, "Acknowledgement recorded.");
      else if (kind === "outcome_received") record({ type: "outcome_received", outcome_notes: v }, "Outcome recorded.");
      else if (kind === "deadline") { if (!v) return U.toast("Choose a date first.", "error"); record({ type: "deadline_updated", deadline_at: v }, "Deadline set."); }
    });
    U.on(view, "click", "[data-act]", async (ev, el) => {
      const act = el.dataset.act;
      if (act === "clear-deadline") record({ type: "deadline_updated", deadline_at: null }, "Deadline cleared.");
      else if (act === "uncertain") record({ type: "uncertain" });
      else if (act === "abandoned") record({ type: "abandoned" });
      else if (act === "again") {
        try {
          if (!(await ensureConsent(PURPOSE.applications, "Allow and continue"))) return;
          const r = S.applyAgain(id);
          U.writeSuggestions(r.draft.id, r.suggested_links);
          U.go("draft.html?id=" + encodeURIComponent(r.draft.id));
        } catch (e) {
          U.toast(U.errMsg(e, "Could not start a new application."), "error");
        }
      }
    });
  };

  /* ================= packet ================= */
  function packetText(snap) {
    const out = [snap.service_name + " (pack " + snap.pack_version + ")", "", "NOT a submission. " + snap.not_a_submission_notice, "", "Application details"];
    snap.fields.forEach((f) => out.push(`- ${f.label}: ${f.value || "(not provided)"}`));
    out.push("", "Evidence to upload");
    snap.evidence.forEach((g) => out.push(`- ${g.label}: ${g.documents.length ? g.documents.map((d) => d.filename).join(", ") : "(none)"}`));
    out.push("", "Declaration (you confirm this yourself on the portal)", snap.declaration.text, "", "Official steps");
    snap.official_channel_steps.forEach((s, i) => out.push(`${i + 1}. ${s}`));
    out.push("", snap.processing_time);
    return out.join("\n");
  }

  P.packet = (view) => {
    const id = U.params().get("id");
    const render = () => {
      if (!S.hasConsent(PURPOSE.locker)) {
        view.innerHTML = backLink("locker.html", "Back to the locker") + U.gate(PURPOSE.locker, "Opening this packet needs your permission to track applications.", "Allow application tracking");
        return;
      }
      let c;
      try { c = S.getCase(id); } catch (e) { return notFound(view, "locker.html", "Back to the locker", "packet"); }
      const snap = c.packet_snapshot;
      view.innerHTML = `<div class="no-print">${backLink("case.html?id=" + encodeURIComponent(c.id), "Back to the case")}</div>
        <div class="page-head no-print"><h1>Packet</h1><p class="lead">Copy these details into the official portal. Print it or save it as a PDF from your browser.</p>
          <div class="cluster"><button class="btn" data-act="print">Print or save as PDF</button><button class="btn btn-soft" data-act="copy">Copy as text</button></div></div>
        <article class="packet">
          <div class="notice" data-testid="packet-notice">${esc(snap.not_a_submission_notice)}</div>
          <div class="stack-s"><h2>${esc(snap.service_name)}</h2><p class="muted small">Pack ${esc(snap.pack_version)}. Prepared ${esc(U.fmtDate(c.created_at))}.</p></div>
          <section class="stack-s"><h2>Application details</h2><dl class="packet-fields">${snap.fields.map((f) => `<div><dt>${esc(f.label)}</dt><dd>${esc(f.value || "Not provided")}<br><span class="muted small" style="font-weight:400">${esc(f.source)}</span></dd></div>`).join("")}</dl></section>
          <section class="stack-s"><h2>Evidence to upload</h2><dl class="packet-fields">${snap.evidence.map((g) => `<div><dt>${esc(g.label)}</dt><dd>${g.documents.length ? g.documents.map((d) => esc(d.filename)).join(", ") : "None"}</dd></div>`).join("")}</dl></section>
          <section class="stack-s"><h2>Declaration</h2><p>${esc(snap.declaration.text)}</p><p class="muted small">You make this declaration yourself on the official portal.</p></section>
          <section class="stack-s"><h2>Official steps</h2><ol class="plain">${snap.official_channel_steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>
            <p class="muted small">${esc(snap.processing_time)}. ${esc(snap.fee)}.</p></section>
          <section class="stack-s"><p class="muted small">${esc(snap.portal_down_guidance)}</p><p class="muted small">${esc(snap.acknowledgement_guidance)}</p>
            <p class="muted small">Official sources: ${snap.sources.map((s) => esc(s.title) + " (" + esc(s.url) + ")").join("; ")}</p></section>
        </article>`;
    };
    render();
    U.bindGate(view, render);
    U.on(view, "click", "[data-act]", async (ev, el) => {
      if (el.dataset.act === "print") window.print();
      else if (el.dataset.act === "copy") {
        try {
          await navigator.clipboard.writeText(packetText(S.getCase(id).packet_snapshot));
          U.toast("Copied to your clipboard.", "ok");
        } catch (e) {
          U.toast("Couldn't copy. Select the text on the page instead.", "error");
        }
      }
    });
  };

  /* ================= account ================= */
  const AUDIT_LABEL = {
    "auth.sign_in": "Signed in", "auth.sign_out": "Signed out",
    "consent.granted": "Permission allowed", "consent.withdrawn": "Permission withdrawn",
    "document.uploaded": "Document added", "document.retried": "Document re-read", "document.deleted": "Document deleted",
    "profile.promoted": "Values added to profile", "profile.confirmed": "Value confirmed", "profile.corrected": "Value corrected", "profile.removed": "Value removed",
    "draft.created": "Draft started", "draft.field_set": "Draft field saved", "draft.refreshed": "Draft refreshed from profile",
    "draft.document_linked": "Evidence attached", "draft.document_unlinked": "Evidence removed", "draft.declaration": "Declaration updated",
    "draft.exported": "Draft previewed", "draft.deleted": "Draft deleted",
    "case.created": "Packet frozen in locker", "case.event": "Case updated", "case.apply_again": "New application from a past one",
  };
  P.account = (view) => {
    const user = S.user();
    const events = S.listAudit().slice(0, 40);
    view.innerHTML = `${head("Account", `Signed in as ${user.name}.`, '<div><button class="btn btn-ghost btn-sm" data-act="signout">Sign out</button></div>')}
      <div class="stack-l">
        <section class="stack-s"><h2 style="font-size:1.4rem">Your data</h2>
          <p class="muted">Everything lives in this browser. Export a copy, or erase it all. Erasing works whether or not any permission is allowed.</p>
          <div class="cluster"><button class="btn btn-soft" data-act="export">Download my data (JSON)</button><button class="btn btn-danger" data-act="erase">Erase everything and sign out</button></div></section>
        <section class="stack-s"><h2 style="font-size:1.4rem">Activity log</h2>
          <p class="muted small">A redacted record of what happened. It holds actions and short ids, never document contents or personal details.</p>
          ${events.length ? `<div class="list-panel"><ul class="list">${events.map((e) => `<li class="row" style="padding:10px 0"><span>${esc(AUDIT_LABEL[e.action] || e.action)}${e.detail ? ` <span class="muted small">${esc(e.detail)}</span>` : ""}</span><span class="muted small">${esc(U.fmtDateTime(e.at))}</span></li>`).join("")}</ul></div>` : U.empty("No activity yet", "Actions you take will appear here.")}</section>
      </div>`;
    U.on(view, "click", "[data-act]", async (ev, el) => {
      const act = el.dataset.act;
      if (act === "signout") { S.signOut(); U.go("index.html"); }
      else if (act === "export") {
        const blob = new Blob([JSON.stringify(S.exportAll(), null, 2)], { type: "application/json" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "rinavi-demo-data.json";
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      } else if (act === "erase") {
        const ok = await U.confirm({ title: "Erase everything?", body: "Documents, profile values, drafts, locker cases, permissions and the activity log are deleted from this browser. This cannot be undone.", confirmLabel: "Erase everything", danger: true });
        if (!ok) return;
        S.eraseAll();
        U.go("index.html");
      }
    });
  };

  /* ================= trust ================= */
  P.trust = (view) => {
    const REPO = "https://github.com/abhinavtie2008/RINAVI";
    view.innerHTML = `${head("Trust and privacy", "How RINAVI is built to keep you in control, in plain language.")}
      <div class="stack-l">
        <section class="stack"><h2>What RINAVI does</h2>
          <ul class="plain"><li>Reads documents you choose to add, and shows which line each value came from.</li><li>Keeps your confirmed values in a profile you can correct or erase.</li><li>Fills application drafts, checks your evidence, and tells you what is missing.</li><li>Freezes a copy-ready packet and keeps your notes while you wait on the portal.</li></ul></section>
        <section class="stack"><h2>What RINAVI never does</h2>
          <div class="grid-3">
            <div class="principle h-lav"><h3>Submit for you</h3><p class="muted">The citizen submits on the official portal. RINAVI never does it on their behalf.</p></div>
            <div class="principle h-mint"><h3>Store portal passwords</h3><p class="muted">There is nothing to store because you sign in yourself.</p></div>
            <div class="principle h-peach"><h3>Bypass OTP or CAPTCHA</h3><p class="muted">Those protections stay in place.</p></div></div></section>
        <section class="stack"><h2>How you stay in control</h2>
          <div class="list-panel"><ul class="list">
            <li class="row"><div class="row-main"><span class="row-title">Permissions are off until you allow them</span><span class="muted">Four purposes, each asked for separately, each withdrawable at any time.</span></div>${U.chip("Consent", "h-butter", true)}</li>
            <li class="row"><div class="row-main"><span class="row-title">Every value shows its source</span><span class="muted">If the source document is deleted, the value is marked for a re-check.</span></div>${U.chip("Provenance", "h-lav", true)}</li>
            <li class="row"><div class="row-main"><span class="row-title">Erasure always works</span><span class="muted">Deleting a document or your account works even after permissions are withdrawn.</span></div>${U.chip("Erasure", "h-rose", true)}</li>
            <li class="row"><div class="row-main"><span class="row-title">The activity log is redacted</span><span class="muted">It records what happened, never document contents or personal details.</span></div>${U.chip("Audit", "h-sky", true)}</li>
            <li class="row"><div class="row-main"><span class="row-title">Aadhaar stays on the portal</span><span class="muted">Aadhaar numbers never enter profiles, drafts, packets or logs.</span></div>${U.chip("Restricted", "h-peach", true)}</li>
          </ul></div></section>
        <section class="stack"><h2>About this demo</h2>
          <div class="notice"><strong>Everything here runs in your browser.</strong> This site is static, so there is no server. Your data lives in this browser's local storage and goes nowhere. Use synthetic data only.</div>
          <ul class="plain"><li>The demo reads <strong>.txt</strong> files. The full app also reads PDFs, and images wait for text recognition.</li><li>Sign-in here is a demo name. The full app uses passkeys.</li><li>Extraction follows simple rules, not AI, and the rules are the same ones the project's backend uses.</li><li>The real RINAVI is independent and is not affiliated with any government body.</li></ul></section>
        <section class="stack"><h2>Read more</h2>
          <div class="cluster"><a class="btn btn-soft" href="handbook/rinavi-handbook.html">Handbook</a><a class="btn btn-ghost" href="${REPO}" rel="noopener">Source code</a><a class="btn btn-ghost" href="${REPO}/tree/main/docs/compliance" rel="noopener">Compliance notes</a><a class="btn btn-ghost" href="${REPO}/tree/main/docs/architecture" rel="noopener">Architecture decisions</a></div></section>
      </div>`;
  };

  /* ================= 404 ================= */
  P.notfound = (view) => {
    view.innerHTML = U.empty("That page doesn't exist", "The link may be old or mistyped.", '<a class="btn" href="index.html">Go to the start</a>');
  };
})();
