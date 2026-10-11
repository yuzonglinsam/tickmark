# Agent instructions — Tickmark

Read **`docs/HANDOVER_CODEX.md`** (local only, not in the public repo) in full before changing anything. Summary of the rules that matter most:

1. **Front end is frozen.** Do not change colours, tokens, fonts, spacing, layout, components, libraries or copy tone
   in `app/`, `components/`, `lib/format.ts`, `app/globals.css`, `components/ui/*` unless Sam explicitly approves that
   specific change. Bug fixes and surfacing new back-end fields with existing building blocks (`Panel`, `Tick`,
   `TierChip`, `EChart`) are allowed with minimal diffs and before/after screenshots at 1440 px and 390 px.
2. **Your focus is the back end** (`engine/`, `api/`, `.github/workflows/`): see the prioritised list in §6 of the handover.
3. **Financial contracts:** missing ≠ zero; every number keeps its SEC sources; AI text contains no digits and Q&A
   numbers are verified; debt definition and "indicative risk band, not a rating" wording stay as documented;
   Python stress/band logic and `lib/issuer.ts#runScenario` stay in sync; bump version constants when logic changes.
4. **Never** commit or print secrets (`.env`), never commit `.rawdata/`, `node_modules/`, `.next/`.
5. Before finishing: `cd engine && ../.venv/bin/python -m unittest discover -s tests`, then `npx tsc --noEmit`,
   `npm run lint`, `npm run build` — all green.
6. Ask Sam before changing financial definitions, regenerating all memos (API cost) or touching the UI.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
