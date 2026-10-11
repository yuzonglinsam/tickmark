# Notes for coding agents

Tickmark = Python credit engine (`engine/`) + Next.js terminal (repo root) + Flask API (`api/index.py`).
Owner: Sam Yu. Portfolio project; visual quality and financial correctness both matter.

## Layout
- `engine/credit_workbench/` — SEC transport (`sec.py`), period normalisation (`normalize.py`), reported-borrowings
  debt build-up (`debt.py`), metrics, risk bands/headroom/Altman (`scorecard.py`), memo generation + validators
  (`memo.py`), issuer JSON contract (`export.py`).
- `engine/pipeline/` — `universe.py` (choose issuers), `fetch.py` (throttled, gzip-cached SEC downloads in `.rawdata/`),
  `build.py` (issuer JSON + `public/data/universe.json` + `tickers.json`), `ai.py` (DeepSeek memos, fingerprinted).
- `api/index.py` — `/api/py/analyze`, `/api/py/memo`, `/api/py/ask`; dev server on :5328 (Next rewrites in dev).
- `app/`, `components/`, `lib/` — Next.js 16 App Router. Read `node_modules/next/dist/docs/` before using new APIs.

## Contracts (do not break)
- Missing values are N/A with a reason; never zero-fill. Every displayed figure must keep its `sources`.
- AI text contains no digits (memo validator). Q&A numbers are verified in `verify_numbers`.
- Debt never adds lease liabilities on top; components only from one filing; untagged parts listed in `debt_scope.not_tagged`.
- Front end is frozen — see AGENTS.md and docs/HANDOVER_CODEX.md (local only, not in the public repo) §5.
- Risk band = weaker of net debt/EBITDA and CFO/net debt on S&P's standard-volatility ranges; not a rating.
- Frontend `lib/issuer.ts#runScenario` must mirror `stress.py` + `scorecard.py`.

## Commands
- Tests: `cd engine && ../.venv/bin/python -m unittest discover -s tests`
- Web: `npm run dev` / `npx tsc --noEmit` / `npm run build`
- Data: see README "Rebuild the dataset". Secrets live in `.env` (gitignored).
