# Working local application — 2026-10-11

## Claude Code handover — later checkpoint, 2026-10-11

The client requested an implementation handover after reviewing the proposed upgrade.
Read `CLAUDE.md` and **`HANDOVER_CLAUDE.md`** for the determined next scope, 12-dimension
product assessment, source-port locations, implementation order and acceptance gates.
`docs/OPEN_SOURCE_AUDIT.md` records the expanded source review. Continue this project;
do not restart discovery or rewrite the PRD.

The new direction is a professional **dark** Streamlit credit workspace, full annual
filing comparison using Disclosure Alpha, attributed FinRobot FCFF/DCF and sensitivity,
and an improved stress/report experience. It supersedes the earlier light UI/60-second
demo direction below. The financial contracts and historical acceptance remain valid.
The original app still has its light UI; no upgraded UI or filing comparison has shipped.

FinRobot source and license/provenance files now exist under
`credit_workbench/vendor/finrobot/`, with `credit_workbench/valuation.py` as an original
adapter. They are **unintegrated drafts**. A prior KO saved-Snapshot preview is neither
new live-data acceptance nor independent valuation validation. Preserve and verify it
before integration. `55a8d48` remains the verified foundation baseline; this handover
is a separate local checkpoint, not a completed-feature release.

At this handover, 54 existing local tests passed again (0.692s), and `pip check` passed.
Compileall and `git diff --check` passed. Three FinRobot upstream file hashes and two
verbatim kernels were checked against the pinned local upstream clone. The handover's
12 short product answers and local Markdown links were checked. These checks establish
handover/provenance integrity, not independent model arithmetic or upgraded UI acceptance.
Git remote is empty. Public app, hosted PostgreSQL, CI and upgraded browser acceptance
remain pending. GitHub synchronization still requires explicit client authorization.
This turn creates the handover and preserves drafts; it does not implement the upgrade.

## Start here

Continue the working application in this repository; do not rebuild the foundation or PRD.
The client requested a **local preview before hosting/database account setup**; Claude Code
will continue the researched upgrade. Local SEC → financials → stress → real DeepSeek → PDF is now
implemented and inspected. Public deployment and its acceptance remain outstanding.

Use `.venv311/bin/python` (Python 3.11.17). The original `.venv` is preserved. The app runs at
`http://127.0.0.1:8501`; start it with `.venv311/bin/python -m streamlit run app.py` if stopped.
Server secrets are present in ignored, mode-600 `.env`; never print or copy their values.
No PostgreSQL connection is configured. No GitHub remote or authenticated GitHub account
exists at this checkpoint. Ask for GitHub synchronization authorization before any push.

Use Python 3.11, Streamlit, EdgarTools/SEC, Pandas/NumPy, Plotly, DeepSeek, ReportLab,
GitHub and Streamlit Community Cloud. Keep one Python application with small modules.
Pin actual installed, tested versions. There is no need for microservices, agent orchestration,
registration, billing, React, a separate API server or a vector database.

## Existing code and verified boundary

| Module | Implemented and locally checked | Remaining boundary |
|---|---|---|
| `models.py`, `metrics.py` | Source invariants, lineage, deterministic metrics and YoY | Wider cross-issuer accounting review |
| `normalize.py`, `xbrl_fallback.py` | Exact contexts, three FYs, quarter differencing, TTM, consolidated filing facts, reviewed KO extensions | Many custom/lease/borrowing scopes remain N/A; no universal coverage |
| `scoring.py`, `stress.py` | Uncalibrated score, missing-factor intervals, immutable sensitivities | Confirmed debt-free real-issuer conventions still need end-to-end validation |
| `sec.py` | Live search/data/filings, atomic raw cache, TTL, stale fallback, shared limiter | Combined deployed-worker traffic not checked |
| `disclosures.py`, `memo.py` | Bounded annual passages, real DeepSeek JSON, known-reference and numeric-prose guards | Semantic support requires editorial review; no automatic claim-proof guarantee |
| `research.py`, `memo_cache.py` | JSON research persistence, versioned identities, SQLite locks/rolling limits and PostgreSQL implementation | Managed PostgreSQL and hosted restart unverified |
| `app.py`, `pdf_export.py` | Streamlit search, chart, Learn Mode, stress/reset, cited memos and real one-page downloads | Public-host and user-selected final ticker acceptance pending |
| `tests/` | 54 passing local tests on Python 3.11 | GitHub/Linux CI has not run |

PyPI and GitHub terminal access returned HTTP 200. The initial SEC 403 was resolved after
using a genuine SEC contact identity; actual SEC index, submissions, companyfacts and filing
requests succeeded. This does not guarantee that another hosting IP will be accepted.
Real AI calls have been made. Local unit tests establish contracts, not universal extraction
accuracy. Live evidence and acceptance screenshots are under ignored `artifacts/`; curated
reviewed exports are documentation examples, never production data fixtures.

## Financial and source contracts

1. **One fact, one meaning.** Every amount retains original concept, accession, filing date,
   source URL, actual period start/end, currency and derivation note. Store base currency units;
   scale only in the UI. `None` means missing, never zero. Distinguish reported/derived/scenario.
   Evidence IDs must uniquely identify a fact or a bounded disclosure passage, not just a company.
2. **Fiscal periods.** Select exact duration/instant contexts and consolidated totals. Never
   select a number merely because its `fy`, `fp`, row label or dataframe column is first. Fiscal
   year differs from calendar year. Handle 52/53-week years and restatements. Choose the latest
   valid filing known at `as_of` for the exact observation; preserve the earlier version's lineage.
   A non-financial amendment must not erase a valid financial statement.
3. **Quarter and TTM.** Income statements may contain discrete quarters and YTD together;
   cash-flow statements commonly require YTD differencing. Q2 = H1−Q1; Q3 = 9M−H1;
   Q4 = FY−9M, only with comparable currency, scope and accounting basis. For TTM use
   FY + current YTD − prior comparable YTD, or four consecutive compatible discrete quarters.
   Retain every input source and check continuity; do not multiply one quarter by four.
   Align balance-sheet date with flow-period end. Show FY and latest quarter separately when
   TTM cannot be supported; do not feed a stale balance sheet into a fresh TTM score.
4. **EBIT/EBITDA.** Core `operating_income` is the operating EBIT proxy. Label it accordingly.
   EBITDA proxy = operating income + compatible D&A. Do not relabel it issuer-adjusted EBITDA.
   Cash-flow D&A can differ in scope from income-statement D&A: disclose the approximation,
   avoid double-counting amortization, and do not add impairment/SBC as D&A. Missing D&A
   means missing EBITDA. Gross interest expense must not be replaced with net interest or
   cash interest paid without a separately named metric and method.
5. **Cash/debt/FCF.** FCF = CFO−cash capex, with capex stored as a positive validated outflow.
   Debt is interest-bearing borrowing, including current maturities once, commercial paper
   once and finance leases once; operating-lease liabilities are separately disclosed.
   Never add a total to its components. Do not substitute total liabilities for debt.
   Cash means unrestricted cash and equivalents, excluding restricted cash and marketable
   securities by default. Net debt may be negative. Keep liquidity facilities and maturity
   schedules separate until backed by specific disclosure evidence.
6. **Source fallback.** SEC companyfacts is a fast path for standard entity-wide facts.
   EdgarTools filing XBRL statements, calculation relationships and footnotes handle custom
   concepts or missing fields. Do not assume label regexes or convenience getters establish
   provenance. If a mapping cannot be verified, show N/A with a reason, not a guessed figure.
   The LLM must not silently fill numeric gaps in the deterministic dataset.
7. **Universe.** Search the live issuer index, resolve ticker/share-class/CIK, then inspect
   issuer metadata and business classification. Reject financial institutions, funds and
   special vehicles for this corporate methodology with a clear explanation. Review mixed
   businesses and REITs explicitly; a blanket sector guess is insufficient. US-listed foreign
   issuers may file 20-F/40-F/6-K and use IFRS: do not silently redefine “US-listed” as domestic
   10-K filers. Support annual analysis where justified; make unavailable quarterly coverage
   explicit. Any genuine technical exclusion must remain visible and documented.

## Score and stress decisions

The core implements a deliberately simple, **uncalibrated screening score**, not a default
probability, investment recommendation or agency credit rating. No invented AAA/BBB mapping.
Keep methodology visible and versioned. Sector-neutral thresholds have material limitations;
sector context belongs in the memo and methodology, not fabricated precision.

| Factor | Weight | 0 points → 100 points (linear, clamped) |
|---|---:|---|
| Gross debt / EBITDA proxy | 30 | 5x or higher → 1x or lower |
| Operating EBIT / gross interest | 25 | 1x or lower → 8x or higher |
| Annual/TTM FCF / debt | 20 | 0% or lower → 40% or higher |
| Current ratio | 15 | 0.5x or lower → 2x or higher |
| Operating margin | 10 | 0% or lower → 20% or higher |

Bands: Strong ≥80; Stable ≥60; Watch ≥40; Weak <40. Present as heuristic credit-health bands,
not calibrated default-risk categories. Positive debt with nonpositive EBITDA gets 0 leverage
points while the ratio displays NM. Confirmed zero debt is distinct from missing debt; zero
interest with outstanding debt remains unresolved. Zero debt/zero interest receives coverage
points only with positive operating income. Nonnegative FCF with confirmed zero debt receives
the cash-flow factor's full points. These explicit conventions require review with real issuers.

Missing factors suppress the single score and instead show data coverage and the mathematically
possible range; the range is **not a statistical confidence interval**. Never reweight missing
factors upward or present an incomplete dataset as a verified score. Missing liquidity does
not imply weak liquidity. No score is produced from quarterly/YTD-only flows.

Stress is a static sensitivity of operating EBIT, gross interest expense and operating cash
flow. Positive changes add a percentage of the absolute base; negative changes subtract it.
This ensures negative EBIT/CFO deteriorate under negative shocks. Explain the sign and show
the actual stressed amount. D&A, capex, cash and debt stay fixed; no unsupported balance-sheet
forecast. Zero bases cannot move with percentage-only sliders: disable those controls with a
reason or add clearly labelled absolute inputs. Always recompute from the immutable base.
Moving/resetting sliders makes **zero AI requests**. The base memo stays explicitly base-case;
the stress view shows local metrics and score changes without pretending the narrative updated.

## AI, evidence, caching and access

- DeepSeek receives the deterministic metric bundle and bounded, cited excerpts from MD&A,
  risk factors and debt notes. Handle quarterly references back to annual disclosures. Include
  source freshness and missing inputs; distinguish factual statements from analyst inferences.
- Use an explicit generate action after financials load. Reuse completed public memos by cache
  key; neither a Streamlit rerun nor a slider should trigger paid generation. Return structured
  JSON with Credit Strengths, Key Risks, Debt Servicing Capacity and Overall Credit View.
  Each material claim carries known evidence IDs and, where relevant, metric IDs.
- Validate JSON shape, length, required sections and references; check quantitative statements
  against the metric bundle. A valid citation ID alone does not prove support. Fact-check a
  real memo against its linked passages during acceptance. Show failed generation honestly.
  Keep financial tables, score and calculations deterministic. Treat filing text as quoted
  untrusted evidence, never instructions. Do not let text choose endpoints, tools or credentials.
- One-page English memo: issuer/ticker, period/as-of, compact financial table, heuristic score
  with coverage, four short research sections and source footnotes. Aim for 350–450 narrative
  words and readable typography; shorten content rather than shrinking it until unreadable.
  Use ReportLab, then render/check the actual PDF. Embed working filing links and methodology
  version. No blank memo or mock PDF counts as delivery.
- Cache raw requests locally during development. Production analyzed results/memos should use
  one small managed PostgreSQL store (e.g. Supabase) with a server-only connection. This is the
  only additional persistence service, not a new application tier. Select/provision securely
  when needed. Local SQLite/files are a development fallback and are not a durable hosted cache.
- Cache identity is CIK + relevant accession set + normalized data and disclosure content hashes
  + extractor/scoring/prompt/model versions. Check latest submissions with a short TTL, invalidate
  on new relevant filings/amendments, and show generated/as-of/last-checked dates. A stale result
  can remain available while refresh is attempted, with a visible stale status.
- Prevent duplicate paid generation with an in-flight lock keyed by analysis identity. Bound
  prompts/output, concurrency and retries. Add a per-session cooldown and a process/global
  rolling request limit; session state alone is not abuse protection. No fixed daily spend cap.
  Keep costs/latency/token counts measurable without logging keys or full user session data.
- SEC transport currently starts at most 4 requests/sec per process. Share the client/limiter
  across Streamlit sessions; combined traffic from all deployment workers must remain compliant.
  No proxy-based bypass for blocks. Surface upstream failure and retain the last valid analysis.
- All credentials belong in server environment variables or Streamlit secrets, never a public
  widget. End users have no account, key or payment requirement. Request account access/keys only
  when necessary, after completing the unblocked work. Do not collect API secrets in chat.

## Earlier interface and 60-second demonstration (superseded)

This section records the implemented foundation presentation. Use the dark workspace
and 2–3 minute demonstration in `HANDOVER_CLAUDE.md` for the next iteration.

English-first research interface. Use a restrained off-white background (#F5F7FA), ink/navy
(#142C4B), teal (#167C80) and muted warning colors; generous spacing, readable tabular numbers,
thin separators and clear hierarchy. Reference the calm density of Quartr/Fiscal.ai without
copying logos/assets. Avoid an emoji dashboard or leaving every Streamlit default on screen.

Top: company/ticker search, AAPL/KO/BA quick starts, visible filing period and refresh status.
Main: overview metrics and readable Plotly financial history; explicit currency/basis labels.
Research area: Overview, Stress Test and Credit Memo with sources accessible from each result.
Learn Mode opens the formula, financial meaning and the current issuer's substitution directly
from the metric card. Keep missing/unsupported/loading/stale/error states first-class and useful.

Render financials before waiting for AI. On a warm, real cached example: 0–10s select issuer;
10–25s explain financials and sources; 25–40s move a stress slider; 40–60s inspect/download memo.
This demonstration is separate from cold-ticker acceptance. Measure warm and cold latency;
do not promise that a first-time full filing parse and AI call always finishes in 60 seconds.

## Release evidence — local checkpoint

| Check | Actual evidence / outstanding work |
|---|---|
| Arbitrary issuer | TXN and TSM, neither a quick start, passed real SEC normalization, actual DeepSeek output and reviewed PDF export. KO also checked. User-selected final ticker pending. TSM required editorial repair after raw AI validation failed. |
| Accounting | KO/TXN have FY 2025/2024/2023, latest quarter and compatible TTM. Reconciliations below. TSM has three IFRS FYs in TWD; no supported quarter. |
| Hard cases | BA historical negative EBIT/CFO; AAPL non-calendar FY; TXN missing interest/D&A; TSM IFRS; JPM SIC 6021 excluded in browser. MNST debt-note facilities are explicitly undrawn at year-end, but complete debt/lease scope remains unverified; full debt-free acceptance is pending. |
| Interactions | Real browser: Alphabet multiple share classes, TXN/TSM arbitrary search, JPM rejection, KO refresh, FY/TTM selection, Learn Mode, chart and all three sliders/reset. |
| Zero AI on stress | At 08:42:01 UTC, shared SQLite `api_calls` count stayed **10 → 10** while KO EBIT −5%, interest +5%, CFO −5% moved score **64.1 → 60.9**; reset returned all controls to zero and score 64.1. `artifacts/browser/stress-acceptance.json`. |
| Real AI | `deepseek-flash`, `memo-v1.0`. KO/TXN real responses passed structural/reference checks; claims reviewed against SEC passages. TSM's two raw responses failed the digit guard; a captured real draft was edited, then validated and marked editorially reviewed. |
| PDF | KO 436 words, TXN 413 words, TSM 430 words; one Letter page each. Rendered/visually inspected, no overlap/clipping. KO actual browser download verified against 47.94/13.76/14.81/46.74 and score 64.1. All three browser downloads verified as one page with actual filing hyperlinks. |
| Caching | KO repeat reused memo, no AI. TXN empty raw-cache run: 3.34s financials, saved memo reused. TSM empty raw-cache repeat: 4.57s financials, reviewed memo reused. These are raw-cache cold timings, not cold AI latency promises. Eight concurrent local claimers produced one owner in a synthetic test; local reopen preserved memo. Managed PG/restart pending. |
| Failures | Original SEC 403 observed; later access succeeded. Synthetic 403/timeout checks retain valid stale data and fail honestly without cache. Missing configuration browser/AppTest state checked. Actual TSM invalid numeric narrative was rejected and not cached. Hosted 429 and full failure matrix still need release verification. |
| Public access | **Pending:** hosting login, managed PostgreSQL, public URL, unauthenticated cold-ticker/memo/PDF and hosted restart checks. |
| Delivery | Pinned requirements, `pip check`, compileall and 54 tests passed locally. Configured secret absent from current source/docs/PDFs and historical Git blobs; `.env` ignored/mode 600. CI workflow prepared, no GitHub CI claim. Local branch `codex/sec-streamlit-workbench`; no GitHub synchronization authorized yet. |

### Hand reconciliations (base units; billion figures below)

**KO FY 2025, USD**, accession `0001628280-26-010047`:

- Revenue 47.941; operating EBIT 13.762; D&A 1.050; EBITDA proxy = **14.812**.
- CFO 7.408 − cash capex 2.112 = FCF **5.296**. Gross interest 1.654; coverage **8.3204x**.
- Debt = LT debt/capital leases incl. current 43.941 + commercial paper 1.495 + other ST
  borrowing 0.056 + disposal-group current borrowing 0.398 + disposal-group LT borrowing
  0.850 = **46.740**. The earlier 45.492 partial sum was corrected before acceptance.
- The two disposal-group concepts are an explicitly reviewed KO extension registry, not
  inferred from labels or fixed values. Exact filing anchors `#f-664` and `#f-668` retained.
- Cash 10.270; current assets 31.044; current liabilities 21.281; gross leverage **3.1555x**;
  complete heuristic score **64.1 Stable**. This is not a credit rating.
- Latest quarter: 2026-04-04–2026-07-03. TTM: 2025-06-28–2026-07-03; revenue 50.129,
  operating EBIT 14.854, CFO 16.342, capex 2.045. Latest debt completeness remains N/A,
  so the FY score is not silently reused for the TTM.
- Actual AI response: 4,969 input / 1,001 output tokens, 5.92s. Edited unsupported
  investment-grade access and exaggerated commercial-paper characterization; original
  response retained locally. The reviewed memo is distinct from a newly generated draft.
- [Actual annual filing](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm).

**TXN FY 2025, USD**, accession `0000097476-26-000059`:

- Revenue 17.682; operating EBIT 6.023; CFO 7.153 − capex 4.550 = FCF **2.603**.
- Cash 3.225; current assets 13.750 / current liabilities 3.159 = current ratio **4.3526x**.
- D&A, gross interest and complete borrowing scope remain **N/A** under the current
  supported mappings. No full score: coverage 25%, possible range 25–100. This is an
  extractor information gap, not evidence that the issuer has no debt or weak credit.
- Latest quarter: 2026-04-01–2026-06-30. TTM: 2025-07-01–2026-06-30;
  revenue 19.453, operating EBIT 7.254, CFO 8.667, capex 3.312.
- Actual AI response: 3,399 input / 942 output tokens, 5.00s. Risk discussion checked
  against the annual risk-factor excerpt, including China exposure/trade restrictions.
- [Actual annual filing](https://www.sec.gov/Archives/edgar/data/97476/000009747626000059/txn-20251231.htm).

**TSM FY 2025, TWD**, accession `0001628280-26-025362`: revenue 3,809.0543,
operating EBIT 1,936.0917, D&A 688.0964, CFO 2,274.9756 and capex 1,272.4105.
No guessed USD conversion. Debt/interest remain N/A; score suppressed. The raw AI digit
guard failures and editorial repair are recorded in the reviewed memo's notes.
[Actual annual filing](https://www.sec.gov/Archives/edgar/data/1046179/000162828026025362/tsm-20251231.htm).

**Other real checks:** AAPL FY ends 2025-09-27/2024-09-28/2023-09-30. BA FY 2024
operating EBIT −10.707 and CFO −12.080 billion; −20% sensitivity worsens them to
−12.8484 and −14.496 billion. TSM reporting currency remains TWD. CAT is flagged for
mixed industrial/financing business. MNST FY 2025 notes state no Credit Facilities or
China line-of-credit borrowings outstanding, but this alone does not prove complete
finance-lease/other-borrowing scope or zero FY interest (its loan was repaid during FY).

### Foundation release work (continue under the new handover)

Implement the local upgrade and its acceptance gates from `HANDOVER_CLAUDE.md` first.
The outstanding accounting and public-release work below still applies.

1. Let the client inspect the local app and reviewed PDFs; optionally use a client-selected
   issuer for the final accounting/UX check. UI improvement may follow separately.
2. Broaden reviewed debt, gross-interest and D&A extraction; verify a complete debt-free
   issuer and remaining real-issuer edge cases. Keep unresolved values N/A.
3. After explicit authorization, authenticate GitHub, synchronize the verified local branch
   and inspect actual CI. Set up Streamlit Community Cloud and managed PostgreSQL with
   server-only secrets; the client handles login/account terms/access approval.
4. Finish cold public-session, database locks/rolling limits, hosted restart, source refresh
   and combined traffic checks. Only then claim a public, persistent release.

See `docs/DEMO.md`, `docs/DEPLOYMENT.md` and `docs/REFERENCE_PROJECTS.md`. The reference
apps' README/license pages were checked at the foundation milestone; they were not
independently installed. EdgarTools is the actually reused parser. The foundation
milestone copied no reference application source. Later unintegrated FinRobot drafts
and the wider source audit are documented in the Claude Code handover above.

## Official references checked during foundation work

- [SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces): endpoint formats, taxonomy/context coverage, periods and server-side access.
- [SEC developer resources](https://www.sec.gov/about/developer-resources): fair-access constraints.
- [EdgarTools financial data](https://edgartools.readthedocs.io/en/latest/guides/financial-data/): convenience APIs, XBRL, multiple periods and statement views.
- [DeepSeek JSON output](https://api-docs.deepseek.com/guides/json_mode/): JSON mode setup and empty/truncated output handling.
- [DeepSeek models](https://api-docs.deepseek.com/quick_start/pricing/): current configurable model identifier; recheck at integration.
- [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app): repository, dependencies and deployment setup.
- [Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management): server configuration.

No third-party application source was copied into the `55a8d48` foundation. Later
draft ports retain their own licenses and are not yet connected to the application.
