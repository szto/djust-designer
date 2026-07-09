/* zdesign overlay — vanilla JS + Shadow DOM. Hover to highlight any
 * element carrying data-zd-id; click to open the edit panel; edit its
 * class attribute and POST the change back to the source. */
(() => {
  if (window.__zdesign_loaded) return;
  window.__zdesign_loaded = true;

  const host = document.createElement("div");
  host.id = "zdesign-root";
  host.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:2147483647";
  document.documentElement.appendChild(host);
  const root = host.attachShadow({ mode: "open" });

  root.innerHTML = `
    <style>
      :host { all: initial; font: 13px/1.4 system-ui, sans-serif; color: #0f172a; }
      .hi { position:absolute; outline:2px solid #6366f1; background:rgba(99,102,241,.08); pointer-events:none; transition:all .05s ease-out; }
      .badge { position:absolute; background:#4338ca; color:#fff; padding:2px 6px; border-radius:4px; font-size:11px; pointer-events:none; }
      .panel { position:fixed; right:16px; bottom:16px; width:340px; background:#fff; border:1px solid #cbd5e1; border-radius:10px; box-shadow:0 10px 30px rgba(15,23,42,.2); pointer-events:auto; overflow:hidden; }
      .panel header { padding:10px 12px; background:#0f172a; color:#fff; display:flex; justify-content:space-between; align-items:center; }
      .panel header .close { cursor:pointer; opacity:.7; }
      .panel .body { padding:12px; }
      .panel label { display:block; font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:#64748b; margin-bottom:4px; }
      .panel input { width:100%; box-sizing:border-box; padding:8px; border:1px solid #cbd5e1; border-radius:6px; font-family:ui-monospace,monospace; font-size:12px; }
      .panel .src { font-family:ui-monospace,monospace; font-size:11px; color:#334155; margin-top:8px; }
      .panel .actions { display:flex; gap:8px; margin-top:10px; }
      .panel button { flex:1; padding:8px; border:0; border-radius:6px; background:#6366f1; color:#fff; cursor:pointer; }
      .panel button.secondary { background:#e2e8f0; color:#0f172a; }
    </style>
    <div class="hi" hidden></div>
    <div class="badge" hidden></div>
    <div class="panel" hidden>
      <header>
        <span>zdesign</span>
        <span class="close">×</span>
      </header>
      <div class="body">
        <label>class</label>
        <input type="text" class="cls" />
        <div class="src"></div>
        <div class="actions">
          <button class="apply">Apply</button>
          <button class="undo secondary">Undo last</button>
        </div>
      </div>
    </div>
  `;

  const hi = root.querySelector(".hi");
  const badge = root.querySelector(".badge");
  const panel = root.querySelector(".panel");
  const clsInput = root.querySelector(".cls");
  const srcEl = root.querySelector(".src");
  const applyBtn = root.querySelector(".apply");
  const undoBtn = root.querySelector(".undo");
  const closeBtn = root.querySelector(".close");

  let selected = null;
  let hoverPinned = false;

  const findZ = (el) => {
    while (el && el.nodeType === 1) {
      if (el.dataset && el.dataset.zdId) return el;
      el = el.parentElement;
    }
    return null;
  };

  const showHighlight = (el) => {
    const r = el.getBoundingClientRect();
    hi.hidden = false;
    hi.style.left = r.left + "px";
    hi.style.top = r.top + "px";
    hi.style.width = r.width + "px";
    hi.style.height = r.height + "px";
    badge.hidden = false;
    badge.textContent = `${el.tagName.toLowerCase()} · ${el.dataset.zdId}`;
    badge.style.left = r.left + "px";
    badge.style.top = Math.max(0, r.top - 22) + "px";
  };

  const hideHighlight = () => { hi.hidden = true; badge.hidden = true; };

  document.addEventListener("mousemove", (e) => {
    if (hoverPinned) return;
    const el = findZ(e.target);
    if (el) showHighlight(el); else hideHighlight();
  }, true);

  document.addEventListener("click", async (e) => {
    if (root.contains(e.target) || e.composedPath().includes(host)) return;
    const el = findZ(e.target);
    if (!el) return;
    e.preventDefault(); e.stopPropagation();
    selected = el;
    hoverPinned = true;
    showHighlight(el);

    const zdId = el.dataset.zdId;
    const res = await fetch("/__zdesign__/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zd_id: zdId }),
    });
    const entry = res.ok ? await res.json() : { error: true };
    clsInput.value = el.getAttribute("class") || "";
    srcEl.textContent = entry.error ? "(source unknown)" : `${entry.file}:${entry.line}`;
    panel.hidden = false;
  }, true);

  applyBtn.addEventListener("click", async () => {
    if (!selected) return;
    const zdId = selected.dataset.zdId;
    const cls = clsInput.value;
    const res = await fetch("/__zdesign__/edit/class", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zd_id: zdId, class: cls }),
    });
    if (res.ok) {
      selected.setAttribute("class", cls);
    }
  });

  undoBtn.addEventListener("click", async () => {
    await fetch("/__zdesign__/undo", { method: "POST" });
  });

  closeBtn.addEventListener("click", () => {
    panel.hidden = true;
    hoverPinned = false;
    hideHighlight();
    selected = null;
  });
})();
