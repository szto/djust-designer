/* zdesign overlay — vanilla JS + Shadow DOM.
 *
 * Hover to highlight any element carrying data-zd-id; click to open the edit
 * panel; edit its class attribute with Tailwind autocomplete and POST the
 * change back to the source. The current selection is also mirrored to the
 * server so a Claude Code MCP client can see what the designer picked.
 */
(() => {
  if (window.__zdesign_loaded) return;
  window.__zdesign_loaded = true;

  // ============================================================
  // Tailwind utility catalogue (built at load, ~1600 classes).
  // Deliberately covers the utility surface most designers reach
  // for without dragging in obscure variants.
  // ============================================================
  const TW_CLASSES = (() => {
    const s = new Set();
    const add = (...xs) => xs.forEach((x) => s.add(x));

    const scale = [
      "0", "0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "5", "6", "7", "8",
      "9", "10", "11", "12", "14", "16", "20", "24", "28", "32", "36", "40",
      "48", "56", "64", "72", "80", "96",
    ];
    for (const p of ["p", "m", "px", "py", "pt", "pr", "pb", "pl",
                     "mx", "my", "mt", "mr", "mb", "ml",
                     "gap", "gap-x", "gap-y", "space-x", "space-y"]) {
      for (const v of scale) add(`${p}-${v}`);
    }
    add("m-auto", "mx-auto", "my-auto");

    const sizes = ["auto", "full", "screen", "fit", "min", "max", ...scale,
      "1/2", "1/3", "2/3", "1/4", "2/4", "3/4", "1/5", "2/5", "3/5", "4/5",
      "1/6", "5/6", "1/12", "11/12"];
    for (const n of sizes) { add(`w-${n}`, `h-${n}`); }
    for (const m of ["xs","sm","md","lg","xl","2xl","3xl","4xl","5xl",
                     "6xl","7xl","full","prose","none"]) add(`max-w-${m}`);
    for (const m of ["xs","sm","md","lg","xl","2xl","3xl","4xl"]) add(`min-w-${m}`);
    for (const m of ["screen","full","min","max","fit"]) add(`min-h-${m}`,`max-h-${m}`);

    for (const t of ["xs","sm","base","lg","xl","2xl","3xl","4xl","5xl",
                     "6xl","7xl","8xl","9xl"]) add(`text-${t}`);
    for (const w of ["thin","extralight","light","normal","medium","semibold",
                     "bold","extrabold","black"]) add(`font-${w}`);
    add("italic","not-italic","underline","line-through","no-underline",
        "uppercase","lowercase","capitalize","normal-case",
        "text-left","text-center","text-right","text-justify",
        "tracking-tight","tracking-normal","tracking-wide","tracking-wider",
        "leading-none","leading-tight","leading-snug","leading-normal",
        "leading-relaxed","leading-loose","whitespace-nowrap","whitespace-normal",
        "break-words","break-all","truncate");

    const colors = ["slate","gray","zinc","neutral","stone","red","orange",
                    "amber","yellow","lime","green","emerald","teal","cyan",
                    "sky","blue","indigo","violet","purple","fuchsia","pink",
                    "rose"];
    const shades = ["50","100","200","300","400","500","600","700","800","900","950"];
    for (const c of colors) for (const sh of shades) {
      add(`text-${c}-${sh}`, `bg-${c}-${sh}`, `border-${c}-${sh}`, `ring-${c}-${sh}`);
    }
    for (const bw of ["text","bg","border","ring"]) {
      add(`${bw}-white`, `${bw}-black`, `${bw}-transparent`, `${bw}-current`);
    }

    add("rounded");
    for (const r of ["none","sm","md","lg","xl","2xl","3xl","full"]) add(`rounded-${r}`);
    for (const side of ["t","r","b","l","tl","tr","br","bl"]) {
      add(`rounded-${side}`);
      for (const r of ["none","sm","md","lg","xl","2xl","3xl","full"]) add(`rounded-${side}-${r}`);
    }

    add("border","border-0","border-2","border-4","border-8");
    for (const side of ["t","r","b","l","x","y"]) {
      add(`border-${side}`, `border-${side}-0`, `border-${side}-2`, `border-${side}-4`, `border-${side}-8`);
    }

    add("shadow","shadow-inner","shadow-none");
    for (const sh of ["sm","md","lg","xl","2xl"]) add(`shadow-${sh}`);

    add("block","inline","inline-block","flex","inline-flex","grid","inline-grid",
        "hidden","table","flow-root",
        "flex-row","flex-col","flex-row-reverse","flex-col-reverse",
        "flex-wrap","flex-nowrap","flex-wrap-reverse",
        "flex-1","flex-auto","flex-initial","flex-none",
        "items-start","items-center","items-end","items-baseline","items-stretch",
        "justify-start","justify-center","justify-end","justify-between",
        "justify-around","justify-evenly",
        "content-start","content-center","content-end","content-between",
        "content-around","content-evenly",
        "self-start","self-center","self-end","self-stretch","self-auto");
    for (const n of ["1","2","3","4","5","6","7","8","9","10","11","12"]) {
      add(`grid-cols-${n}`, `grid-rows-${n}`, `col-span-${n}`, `row-span-${n}`,
          `col-start-${n}`, `col-end-${n}`, `row-start-${n}`, `row-end-${n}`);
    }
    add("col-span-full","row-span-full","col-auto","row-auto");

    add("static","relative","absolute","fixed","sticky");
    for (const t of ["0","0.5","1","2","4","6","8","10","12","16","20","24","auto","full","1/2","1/3","2/3"]) {
      add(`top-${t}`, `right-${t}`, `bottom-${t}`, `left-${t}`, `inset-${t}`, `inset-x-${t}`, `inset-y-${t}`);
    }
    for (const z of ["0","10","20","30","40","50","auto"]) add(`z-${z}`);

    for (const o of ["0","5","10","20","25","30","40","50","60","70","75","80","90","95","100"]) add(`opacity-${o}`);
    add("cursor-pointer","cursor-not-allowed","cursor-default","cursor-wait",
        "cursor-text","cursor-move","cursor-help","cursor-crosshair",
        "select-none","select-all","select-auto","select-text",
        "pointer-events-none","pointer-events-auto",
        "overflow-hidden","overflow-auto","overflow-scroll","overflow-visible",
        "overflow-x-auto","overflow-y-auto","overflow-x-hidden","overflow-y-hidden");

    add("transition","transition-none","transition-all","transition-colors",
        "transition-opacity","transition-transform","transition-shadow",
        "duration-75","duration-100","duration-150","duration-200",
        "duration-300","duration-500","duration-700","duration-1000",
        "ease-in","ease-out","ease-in-out","ease-linear",
        "delay-75","delay-100","delay-150","delay-200","delay-300","delay-500");
    add("transform","transform-none",
        "translate-x-0","translate-x-full","translate-x-1/2","-translate-x-1/2",
        "translate-y-0","translate-y-full","translate-y-1/2","-translate-y-1/2",
        "rotate-0","rotate-45","rotate-90","rotate-180","-rotate-45","-rotate-90",
        "scale-0","scale-50","scale-75","scale-90","scale-95","scale-100",
        "scale-105","scale-110","scale-125","scale-150");

    add("appearance-none","container","antialiased","subpixel-antialiased",
        "outline-none","ring","ring-0","ring-1","ring-2","ring-4","ring-8",
        "ring-inset","ring-offset-0","ring-offset-2","ring-offset-4",
        "backdrop-blur","backdrop-blur-sm","backdrop-blur-md","backdrop-blur-lg",
        "blur","blur-sm","blur-md","blur-lg","blur-none",
        "aspect-square","aspect-video","aspect-auto");

    return [...s].sort();
  })();

  // ============================================================
  // Shadow DOM host — no style leakage into the underlying page.
  // ============================================================
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
      .panel { position:fixed; right:16px; bottom:16px; width:min(560px, calc(100vw - 32px)); background:#fff; border:1px solid #cbd5e1; border-radius:10px; box-shadow:0 10px 30px rgba(15,23,42,.2); pointer-events:auto; overflow:visible; resize:both; min-width:360px; max-width:calc(100vw - 32px); }
      .panel header { padding:10px 12px; background:#0f172a; color:#fff; display:flex; justify-content:space-between; align-items:center; border-radius:10px 10px 0 0; cursor:move; user-select:none; }
      .panel header .tag { font-family:ui-monospace,monospace; font-size:13px; }
      .panel header .tag em { opacity:.55; font-style:normal; margin-left:8px; font-size:11px; }
      .panel header .close { cursor:pointer; opacity:.7; font-size:16px; line-height:1; padding:0 4px; }
      .panel .body { padding:12px; position:relative; }
      .panel label { display:block; font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:#64748b; margin-bottom:4px; }
      .panel .cls-wrap { position:relative; }
      .panel textarea.cls { width:100%; box-sizing:border-box; padding:8px 10px; border:1px solid #cbd5e1; border-radius:6px; font-family:ui-monospace,monospace; font-size:12px; line-height:1.55; min-height:64px; max-height:280px; resize:vertical; overflow-y:auto; white-space:pre-wrap; word-break:break-word; }
      .panel textarea.cls:focus { outline:2px solid #6366f1; outline-offset:-1px; }
      .panel .suggest { position:absolute; left:0; right:0; top:100%; margin-top:2px; background:#fff; border:1px solid #cbd5e1; border-radius:6px; box-shadow:0 6px 16px rgba(15,23,42,.15); max-height:240px; overflow-y:auto; z-index:10; }
      .panel .sug { padding:6px 10px; font-family:ui-monospace,monospace; font-size:12px; cursor:pointer; }
      .panel .sug.active, .panel .sug:hover { background:#eef2ff; color:#4338ca; }
      .panel .src { font-family:ui-monospace,monospace; font-size:11px; color:#334155; margin-top:8px; word-break:break-all; }
      .panel .actions { display:flex; gap:8px; margin-top:10px; }
      .panel button { flex:1; padding:8px; border:0; border-radius:6px; background:#6366f1; color:#fff; cursor:pointer; font-size:13px; }
      .panel button.secondary { background:#e2e8f0; color:#0f172a; }
      .panel .toast { position:absolute; left:12px; right:12px; bottom:-32px; padding:6px 10px; border-radius:6px; font-size:11px; color:#fff; background:#0f172a; opacity:0; transition:opacity .18s; pointer-events:none; }
      .panel .toast.show { opacity:1; }
      .panel .toast.err { background:#dc2626; }
    </style>
    <div class="hi" hidden></div>
    <div class="badge" hidden></div>
    <div class="panel" hidden>
      <header>
        <span class="tag">zdesign</span>
        <span class="close">×</span>
      </header>
      <div class="body">
        <label>class <em style="font-family:ui-monospace,monospace;text-transform:none;letter-spacing:0;opacity:.5;font-style:normal">— Enter to apply · Shift+Enter for newline</em></label>
        <div class="cls-wrap">
          <textarea class="cls" autocomplete="off" spellcheck="false" rows="3"></textarea>
          <div class="suggest" hidden></div>
        </div>
        <div class="src"></div>
        <div class="actions">
          <button class="apply">Apply</button>
          <button class="undo secondary">Undo last</button>
        </div>
        <div class="toast"></div>
      </div>
    </div>
  `;

  const hi = root.querySelector(".hi");
  const badge = root.querySelector(".badge");
  const panel = root.querySelector(".panel");
  const tagLabel = root.querySelector(".tag");
  const clsInput = root.querySelector(".cls");
  const suggestBox = root.querySelector(".suggest");
  const srcEl = root.querySelector(".src");
  const applyBtn = root.querySelector(".apply");
  const undoBtn = root.querySelector(".undo");
  const closeBtn = root.querySelector(".close");
  const toast = root.querySelector(".toast");

  let selected = null;
  let hoverPinned = false;
  let activeSuggestIndex = -1;
  let currentMatches = [];

  const notify = (msg, err = false) => {
    toast.textContent = msg;
    toast.classList.toggle("err", err);
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 1600);
  };

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

  // -- Tailwind suggest ---------------------------------------------------
  const currentWord = () => {
    const val = clsInput.value;
    const pos = clsInput.selectionStart ?? val.length;
    const start = val.lastIndexOf(" ", pos - 1) + 1;
    let end = val.indexOf(" ", pos);
    if (end === -1) end = val.length;
    return { start, end, word: val.slice(start, end) };
  };

  const renderSuggest = () => {
    const { word } = currentWord();
    if (!word || word.length < 1) { suggestBox.hidden = true; return; }
    currentMatches = TW_CLASSES.filter((c) => c.startsWith(word)).slice(0, 30);
    if (!currentMatches.length) { suggestBox.hidden = true; return; }
    activeSuggestIndex = 0;
    suggestBox.innerHTML = currentMatches
      .map((c, i) => `<div class="sug${i === 0 ? " active" : ""}" data-i="${i}">${c}</div>`)
      .join("");
    suggestBox.hidden = false;
  };

  const applySuggest = (idx) => {
    if (idx < 0 || idx >= currentMatches.length) return;
    const chosen = currentMatches[idx];
    const { start, end } = currentWord();
    const before = clsInput.value.slice(0, start);
    const after = clsInput.value.slice(end);
    const joined = `${before}${chosen}${after.startsWith(" ") || after === "" ? after : " " + after}`;
    clsInput.value = joined;
    const caret = (before + chosen).length;
    clsInput.setSelectionRange(caret, caret);
    suggestBox.hidden = true;
    clsInput.focus();
  };

  clsInput.addEventListener("input", renderSuggest);
  clsInput.addEventListener("focus", renderSuggest);
  clsInput.addEventListener("blur", () => setTimeout(() => (suggestBox.hidden = true), 120));
  clsInput.addEventListener("keydown", (e) => {
    if (!suggestBox.hidden) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        const dir = e.key === "ArrowDown" ? 1 : -1;
        activeSuggestIndex =
          (activeSuggestIndex + dir + currentMatches.length) % currentMatches.length;
        for (const el of suggestBox.querySelectorAll(".sug")) el.classList.remove("active");
        const el = suggestBox.querySelector(`.sug[data-i="${activeSuggestIndex}"]`);
        if (el) { el.classList.add("active"); el.scrollIntoView({ block: "nearest" }); }
        return;
      }
      if (e.key === "Tab" || (e.key === "Enter" && !e.shiftKey)) {
        if (activeSuggestIndex >= 0) {
          e.preventDefault();
          applySuggest(activeSuggestIndex);
          return;
        }
      }
      if (e.key === "Escape") {
        e.preventDefault();
        suggestBox.hidden = true;
        return;
      }
    }
    // No open suggestion: Enter (without Shift) submits, Cmd/Ctrl+Enter also submits.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      applyBtn.click();
    } else if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      applyBtn.click();
    }
  });
  suggestBox.addEventListener("mousedown", (e) => {
    const el = e.target.closest(".sug");
    if (!el) return;
    e.preventDefault();
    applySuggest(Number(el.dataset.i));
  });

  // -- Global hover/click -------------------------------------------------
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
    let entry = { error: true };
    try {
      const res = await fetch("/__zdesign__/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ zd_id: zdId }),
      });
      if (res.ok) entry = await res.json();
    } catch (_) {}

    clsInput.value = el.getAttribute("class") || "";
    tagLabel.innerHTML = `&lt;${el.tagName.toLowerCase()}&gt;<em>${zdId}</em>`;
    srcEl.textContent = entry.error ? "(source unknown)" : `${entry.file}:${entry.line}`;
    panel.hidden = false;
    clsInput.focus();
    clsInput.setSelectionRange(clsInput.value.length, clsInput.value.length);

    // Mirror selection to the server so an MCP client can see it.
    fetch("/__zdesign__/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ zd_id: zdId, class: clsInput.value }),
    }).catch(() => {});
  }, true);

  applyBtn.addEventListener("click", async () => {
    if (!selected) return;
    const zdId = selected.dataset.zdId;
    // Collapse whitespace (newlines from Shift+Enter, tabs, doubled spaces) so
    // the file gets a single-line class attribute.
    const cls = clsInput.value.replace(/\s+/g, " ").trim();
    clsInput.value = cls;
    try {
      const res = await fetch("/__zdesign__/edit/class", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ zd_id: zdId, class: cls }),
      });
      if (res.ok) {
        selected.setAttribute("class", cls);
        notify("Applied");
        fetch("/__zdesign__/select", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ zd_id: zdId, class: cls }),
        }).catch(() => {});
      } else {
        const body = await res.text().catch(() => "");
        notify(`Apply failed (${res.status}) ${body}`.trim(), true);
      }
    } catch (err) {
      notify(`Apply error: ${err.message || err}`, true);
    }
  });

  undoBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/__zdesign__/undo", { method: "POST" });
      if (res.ok) notify("Undone — reload to see");
      else notify(`Undo failed (${res.status})`, true);
    } catch (err) {
      notify(`Undo error: ${err.message || err}`, true);
    }
  });

  closeBtn.addEventListener("click", () => {
    panel.hidden = true;
    hoverPinned = false;
    hideHighlight();
    selected = null;
  });

  // Drag the panel by its header.
  (() => {
    const header = root.querySelector(".panel header");
    let dragging = false;
    let dx = 0, dy = 0;
    header.addEventListener("mousedown", (e) => {
      if (e.target === closeBtn) return;
      const rect = panel.getBoundingClientRect();
      dragging = true;
      dx = e.clientX - rect.left;
      dy = e.clientY - rect.top;
      panel.style.right = "auto";
      panel.style.bottom = "auto";
      panel.style.left = rect.left + "px";
      panel.style.top = rect.top + "px";
      e.preventDefault();
    });
    document.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      const w = panel.offsetWidth, h = panel.offsetHeight;
      const x = Math.max(0, Math.min(window.innerWidth - w, e.clientX - dx));
      const y = Math.max(0, Math.min(window.innerHeight - h, e.clientY - dy));
      panel.style.left = x + "px";
      panel.style.top = y + "px";
    });
    document.addEventListener("mouseup", () => { dragging = false; });
  })();
})();
