/* Shared UI helpers: escaping, toasts, dialogs, header, footer, consent gate, page boot. */
(function () {
  "use strict";
  const R = (globalThis.RINAVI = globalThis.RINAVI || {});
  const S = R.store;
  const U = (R.ui = {});

  U.esc = (value) =>
    String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  U.$ = (sel, el) => (el || document).querySelector(sel);
  U.$$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));
  U.params = () => new URLSearchParams(location.search);

  U.fmtDate = (iso) => {
    if (!iso) return "";
    const d = new Date(iso.length === 10 ? iso + "T00:00:00" : iso);
    return isNaN(d) ? String(iso) : d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  };
  U.fmtDateTime = (iso) => {
    const d = new Date(iso);
    return isNaN(d) ? "" : d.toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" });
  };
  U.fmtSize = (n) => (n < 1024 ? n + " B" : n < 1048576 ? Math.round(n / 1024) + " KB" : (n / 1048576).toFixed(1) + " MB");

  U.chip = (label, hue, dot) => `<span class="chip ${hue || "h-neutral"}">${dot ? '<span class="dot"></span>' : ""}${U.esc(label)}</span>`;
  U.errMsg = (e, fallback) => (e && e.status && e.message ? e.message : fallback || "Something went wrong. Try again.");

  /* delegated events */
  U.on = (root, type, selector, handler) => {
    root.addEventListener(type, (ev) => {
      const el = ev.target.closest(selector);
      if (el && root.contains(el)) handler(ev, el);
    });
  };

  /* toasts */
  U.toast = (message, kind) => {
    const host = U.$("#toasts");
    if (!host) return;
    const el = document.createElement("div");
    el.className = "toast " + (kind || "");
    el.textContent = message;
    host.appendChild(el);
    setTimeout(() => el.remove(), kind === "error" ? 6000 : 3500);
  };

  /* confirm dialog */
  U.confirm = ({ title, body, confirmLabel, danger }) =>
    new Promise((resolve) => {
      if (typeof HTMLDialogElement === "undefined") {
        resolve(window.confirm(title + "\n" + (body || "")));
        return;
      }
      const dlg = document.createElement("dialog");
      dlg.innerHTML = `<h3>${U.esc(title)}</h3><p class="muted">${U.esc(body || "")}</p>
        <div class="actions"><button class="btn btn-ghost" value="no">Cancel</button>
        <button class="btn ${danger ? "btn-danger" : ""}" value="yes">${U.esc(confirmLabel || "Confirm")}</button></div>`;
      document.body.appendChild(dlg);
      dlg.addEventListener("click", (e) => {
        const b = e.target.closest("button");
        if (b) dlg.close(b.value);
      });
      dlg.addEventListener("close", () => {
        resolve(dlg.returnValue === "yes");
        dlg.remove();
      });
      dlg.showModal();
    });

  /* navigation */
  const SAFE_NEXT = /^[a-z0-9-]+\.html(\?[A-Za-z0-9=&_%.\-]*)?$/;
  U.safeNext = (value) => (value && SAFE_NEXT.test(value) ? value : null);
  U.go = (url) => location.assign(url);

  const LOGO = `<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="11" cy="12" r="8" fill="#cfc4f5"/><circle cx="21" cy="12" r="8" fill="#bfe8d4" fill-opacity="0.85"/><circle cx="16" cy="21" r="8" fill="#fbd3bd" fill-opacity="0.85"/></svg>`;

  const NAV_IN = [
    ["dashboard", "dashboard.html", "Home"],
    ["catalog", "catalog.html", "Services"],
    ["vault", "vault.html", "Vault"],
    ["profile", "profile.html", "Profile"],
    ["applications", "applications.html", "Applications"],
    ["locker", "locker.html", "Locker"],
    ["consent", "consent.html", "Permissions"],
  ];
  const NAV_OUT = [
    ["catalog", "catalog.html", "Services"],
    ["trust", "trust.html", "Trust and privacy"],
  ];
  // Detail pages highlight their parent in the nav.
  const PARENT = { service: "catalog", document: "vault", draft: "applications", case: "locker", packet: "locker", account: "" };

  U.renderHeader = (page) => {
    const user = S.user();
    const active = PARENT[page] !== undefined ? PARENT[page] : page;
    const items = (user ? NAV_IN : NAV_OUT)
      .map(([key, href, label]) => `<a href="${href}"${key === active ? ' aria-current="page"' : ""}>${label}</a>`)
      .join("");
    const right = user
      ? `<a class="avatar" href="account.html" aria-label="Account for ${U.esc(user.name)}">${U.esc(user.name.charAt(0).toUpperCase())}</a>`
      : `<a class="btn btn-soft btn-sm" href="index.html#start">Try the demo</a>`;
    U.$("#site-header").innerHTML = `<header class="site-header"><div class="wrap bar">
      <a class="brand" href="${user ? "dashboard.html" : "index.html"}" aria-label="RINAVI home">${LOGO}<span>rinavi</span></a>
      <nav class="nav" aria-label="Main">${items}</nav>
      <div class="bar-right">${right}</div></div></header>`;
  };

  U.renderFooter = () => {
    U.$("#site-footer").innerHTML = `<footer class="site-footer"><div class="wrap foot">
      <div class="stack-s"><strong style="font-family:var(--font-display);font-size:1.1rem">rinavi</strong>
        <p class="muted small">RINAVI is independent. It is not affiliated with, endorsed by, or acting for any government body, department, or authority.</p>
        <p class="muted small">This site is a demo. Everything you enter stays in this browser, and only synthetic data should be used.</p></div>
      <nav aria-label="Footer">
        <a href="trust.html">Trust and privacy</a>
        <a href="handbook/rinavi-handbook.html">Handbook</a>
        <a href="https://github.com/abhinavtie2008/RINAVI" rel="noopener">Source on GitHub</a>
        <a href="https://github.com/abhinavtie2008/RINAVI/blob/main/SECURITY.md" rel="noopener">Security policy</a>
        <a href="https://github.com/abhinavtie2008/RINAVI/blob/main/LICENSE" rel="noopener">Apache 2.0 licence</a>
      </nav></div></footer>`;
  };

  /* consent gate panel, used by vault, profile, applications and locker */
  U.gate = (purpose, lead, buttonLabel) => {
    const info = R.LABELS.purpose[purpose];
    return `<section class="panel panel-big tint h-butter stack" data-gate="${purpose}">
      <h2>Allow ${U.esc(info.label.toLowerCase())}?</h2>
      <p>${U.esc(lead)}</p>
      <p class="small">${U.esc(info.description)} You can withdraw this at any time on the <a href="consent.html">permissions page</a>.</p>
      <div><button class="btn" data-grant="${purpose}">${U.esc(buttonLabel)}</button></div></section>`;
  };
  U.bindGate = (root, rerender) => {
    U.on(root, "click", "[data-grant]", (ev, el) => {
      try {
        S.grant(el.dataset.grant);
        rerender();
      } catch (e) {
        U.toast(U.errMsg(e, "Could not record your permission."), "error");
      }
    });
  };

  U.empty = (title, text, actionHtml) =>
    `<div class="empty"><h3>${U.esc(title)}</h3><p>${U.esc(text)}</p>${actionHtml || ""}</div>`;

  /* suggested evidence links live only for this tab, as in the real app */
  U.suggestionsKey = (draftId) => "rinavi:suggested-links:" + draftId;
  U.readSuggestions = (draftId) => {
    try {
      const raw = sessionStorage.getItem(U.suggestionsKey(draftId));
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  };
  U.writeSuggestions = (draftId, list) => {
    try {
      if (list.length) sessionStorage.setItem(U.suggestionsKey(draftId), JSON.stringify(list));
      else sessionStorage.removeItem(U.suggestionsKey(draftId));
    } catch (e) { /* tab storage unavailable */ }
  };

  /* boot: guard, chrome, then the page controller */
  U.boot = () => {
    const body = document.body;
    const page = body.dataset.page;
    if (body.dataset.auth === "required" && !S.user()) {
      const here = location.pathname.split("/").pop() + location.search;
      U.go("index.html?next=" + encodeURIComponent(U.safeNext(here) || "dashboard.html") + "#start");
      return;
    }
    U.renderHeader(page);
    U.renderFooter();
    const view = U.$("#view");
    const controller = R.pages && R.pages[page];
    if (!controller) return;
    try {
      controller(view);
    } catch (e) {
      console.error(e);
      view.innerHTML = U.empty("This page didn't load", "Reload the page. If it keeps happening, your browser may be blocking local storage.", '<a class="btn" href="index.html">Back to the start</a>');
    }
    if (S.storageFailed()) U.toast("Your browser blocked saving. Changes will be lost when you leave.", "error");
  };

  document.addEventListener("DOMContentLoaded", () => {
    if (R.pages) U.boot();
  });
})();
