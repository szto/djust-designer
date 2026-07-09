# Development Handoff — READ BEFORE STARTING NEW WORK

_Last update: 2026-07-09_

## 🚧 Scope reconsideration in progress

The current `main` branch ships a **class/style editor** — hover any element,
edit its Tailwind classes with autocomplete + Tailwind docs links, undo, and
Claude Code (MCP) integration. It is deployed as `djust-designer` on
`main` and works end-to-end (demo → tailscale).

We started expanding toward a **Framer-style no-code builder** but paused
after realizing the scope needs a proper spec first. Do **not** start new
feature work without answering the three questions below.

## ⚠️ Local branch not merged / not pushed

Branch **`feat/regions`** exists **local only**. It is fully implemented
and passes 64/64 tests + ruff/ty, and adds:

- `RegionStore` + `page_slug` (`.djust_designer/regions/<slug>.json`)
- `/__djust_designer__/regions/{list,save,delete}` HTTP JSON views
- Overlay `[Edit] [Regions]` mode toggle + `R` hotkey
- Drag-to-draw regions with scroll-stable document-absolute bbox
- Non-destructive per-mutation bulk chip broadcast (add/remove class to
  every child that lacks/has it, preserving other per-child classes)
- 5-step onboarding hint when entering Regions mode

**Before starting new work, decide what to do with this branch:**
- Merge to `main` if regions stays part of the product.
- Push as a topic branch if we want to revisit as a PR.
- Delete if the final no-code direction absorbs / supersedes it.

There is also a **stash** on `feat/regions`:
`git stash list` → "demo regions session state (temporary)" — this holds
`demo/.djust_designer/regions/_root.json`, transient dev testing data.

## Three questions to answer BEFORE writing spec

The no-code builder direction is many months of focused work. Before
brainstorming the next spec, lock these down:

1. **What are the 3 tasks the designer (wife) actually does most?**
   Ex: text edit / image swap / color+spacing / add new section /
   duplicate card / …
2. **Scope**:
   - a) personal (Django developer sits next to designer)
   - b) team / client-work (designer must be self-sufficient)
   - c) public product (Framer / Webflow competitor)
3. **djust-specific depth**:
   - Does the tool need to edit `LiveComponent` state / props, or
   - is static HTML + Tailwind + Alpine enough for MVP?

## What already exists to reuse

- **Instrumenter** (`djust_designer/instrument/`) — template loader wraps
  `get_contents(origin)` and injects `data-zd-id` + fills a global
  `SourceMapRegistry`. Reusable for any future edit type.
- **Editor** (`djust_designer/edit/`) — `apply_class_change` is the
  narrow current write-back. `paths.resolve_within` + `snapshot.Backups`
  are general-purpose and reusable for text/attr/insert/delete.
- **Bridge** (`djust_designer/bridge/`) — DEBUG-only + loopback-only
  guards + JSON POST endpoints. Add new endpoints here.
- **Overlay** (`djust_designer/static/djust_designer/overlay.js`) —
  Shadow DOM host, hover/highlight, chip UI, mode toggle. Add new
  interactions inside this single file for now.
- **MCP** (`djust_designer/mcp.py`) — Claude Code integration. Add new
  tools (edit_text, upload_image, insert_element, …) here.

## Where the story is written

- **Design spec (P1)**: `docs/superpowers/specs/2026-07-09-djust-designer-design.md`
- **Plan (P1 MVP)**: `docs/superpowers/plans/2026-07-09-djust-designer-p1-mvp.md`
- **Regions spec (P2 stub)**: `docs/superpowers/specs/2026-07-09-djust-designer-regions-design.md` — on `feat/regions` only
- **Regions plan (P2a)**: `docs/superpowers/plans/2026-07-09-djust-designer-regions-p2a.md` — on `feat/regions` only

## Suggested next-session opening

1. Read this file end-to-end.
2. Answer the three questions above.
3. Run `git branch -a` and decide: merge / push / discard `feat/regions`.
4. Only then invoke `superpowers:brainstorming` for the next scope.
