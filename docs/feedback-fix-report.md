# Memo and Q&A correctness fixes

Verified locally on 24 October 2026 (Asia/Singapore). Scope: financial-text correctness and necessary labels; existing visual design, financial definitions, scoring, SEC refresh workflow and precomputation logic are unchanged.

## Root causes and resulting behavior

The original memo validator checked shape, citation IDs and the absence of digits. Those checks cannot establish that “below” agrees with the underlying figures. KO's saved English and Traditional Chinese drafts contain reversed net-leverage comparisons and incorrect cash-coverage statements.

`consistency.py` now calculates coverage, comparable annual trends, peer directions and selected liquidity/coverage boundaries before examining text. Missing inputs remain unknown. Lower leverage and higher liquidity/coverage have opposite improvement directions. Prior-year trends require adjacent annual periods with comparable durations. Supported English and Chinese comparison phrases are checked separately from citation resolution; conditional, negated and unsupported phrasing remains unreviewed. No overall semantic-verification claim is made.

The memo page reports conflicts, checked comparisons and unreviewed clauses alongside its existing citation badges. A conflicting claim is withheld from the displayed analysis; its original draft, deterministic comparison and source links remain available in an expandable review. Markdown copy marks and replaces known conflicting claims with their deterministic comparisons. New English generation receives the computed comparisons and rejects recognized contradictions through the existing bounded correction attempt. Translation is checked independently in the returned memo review. Existing stored memos have not been regenerated.

The original Q&A validator searched an issuer-wide number pool, compared absolute magnitudes, and ignored the metric, fiscal period and currency of a sentence. Consequently, a debt value could incorrectly validate a revenue claim, wrong currency or wrong sign.

`answer_checks.py` replaces that matching with explicit `period/metric` operands. It supports values, sums, differences, ratios, percentages and money-unit conversion, including references to earlier calculation results for compound expressions. The server chooses canonical labels, computes signed values, preserves all input sources and prints the equation. Unknown operands, missing/non-finite values, unsupported conversions, mixed units/currencies, inappropriate cross-period operations, forward references and zero denominators fail closed. No FX conversion is implied. Arbitrary model labels or numeric outputs cannot overwrite the bound result. Free numerical prose is withheld rather than receiving a verification badge. Recognized contradictory prose is withheld, with the deterministic comparison shown. Correct arithmetic does not establish that the model selected the best metric or answered every part of a question.

## Reproduced KO evidence

| Check | Inputs in the frozen regression snapshot | Result |
|---|---|---|
| Original handover comparison | Net leverage 2.378x; peer median 2.302x | Above, not below; explicit EN/繁中 regression |
| Current local pending-data comparison | Net leverage 2.377936808x; peer median 2.339786123x | Above; existing draft conflicts in both languages |
| OCF coverage | USD 7.408bn OCF versus USD 2.112bn capex + USD 8.779bn dividends | Insufficient coverage |
| Shareholder distributions | USD 8.779bn dividends + USD 0.746bn buybacks | USD 9.525bn |
| FCF funding gap | USD 5.296bn FCF − USD 9.525bn distributions | USD −4.229bn |
| Distributions / FCF | USD 9.525bn / USD 5.296bn × 100 | 179.853% at three decimals |

The differing peer medians reflect the inherited pending dataset changes. These fixes do not rewrite the source figures. The test snapshot under `engine/tests/fixtures/` is explicitly labelled as regression input and is never served by the app. Tests also exercise BA, BABA and AAPL document shapes, plus synthetic missing-value, liquidity-trend and invalid-answer cases confined to tests.

## Data coverage and risk wording

The overview distinguishes dataset build date, evidence cut-off and the selected financial period's start/end. It lists available standalone quarters; no standalone quarters means none available, even if annual/TTM data exists. Missing quarters are unavailable, not zero. A recent build date is not a claim of recent financial coverage. Review responses expose the same distinction.

Methodology wording explicitly describes the financial-risk band as a simplified mapping using net leverage and CFO as a proxy, with business risk, liquidity assessment and agency adjustments outside scope. It is not a credit rating. No financial definition or stress threshold changed.

## Verification

- Original 66 tests passed before edits; final suite: **90 tests passed**.
- `npx tsc --noEmit`: passed.
- `npm run lint`: passed.
- `npm run build`: passed, 507 pages. The first invocation stopped after compilation with a Next.js security upgrade reminder; the prescribed retry completed successfully, still reporting the existing vulnerability. No dependency upgrade was bundled.
- Browser: KO memo EN/繁中, conflict expansion with source buttons, and Ask response checked. Desktop 1440×900 and mobile 390×844 screenshots retained. Mobile document width and scroll width were both 390px for memo and Ask.
- Local API tests cover cached review, separate citations/consistency, contradictory answers, bound calculations, malformed provider output and generation rejection before caching.
- GitHub CI passed for code revision `06b6d37`: [run 40085311216](https://github.com/yuzonglinsam/tickmark/actions/runs/40085311216), with both Python engine tests and Next.js build successful. [Draft PR #1](https://github.com/yuzonglinsam/tickmark/pull/1) is open and not merged. A subsequent documentation-only commit records this result; final-head checks are also verified before delivery.

Reproduce:

```bash
(cd engine && ../.venv/bin/python -m unittest discover -s tests)
npx tsc --noEmit
npm run lint
npm run build
```

Browser evidence: [memo before, desktop](screenshots/feedback/memo-before-1440.png), [memo after, desktop](screenshots/feedback/memo-after-1440.png), [memo before, mobile](screenshots/feedback/memo-before-390.png), [memo after, mobile](screenshots/feedback/memo-after-390.png), [real Ask result, mobile](screenshots/feedback/ask-result-390.png). No color, typography, spacing token, library or navigation redesign was made.

## Actual LLM calls

Four real DeepSeek Q&A requests were made during this work: KO arithmetic/direction, BABA Traditional Chinese period comparison/unit conversion, KO compound arithmetic, and a KO request through the browser. All returned HTTP 200. The responses exposed genuine model mistakes: a direction contradiction, a difference using dividends alone instead of total distributions, and unbound Chinese/numerical prose. These were used to repair the guards and compound-expression support. The final compound request and browser request produced all three expected distribution/FCF equations; numerical prose was withheld. This is observed request evidence, not an accuracy benchmark.

The local ignored evidence files are `artifacts/feedback/live-ask.json` and `artifacts/feedback/live-ask-final.json`; the browser result is pictured above. Existing server-side credentials were loaded into the test processes without printing or committing them. No bulk memo regeneration, new live SEC extraction, public deployment verification, or institutional-accuracy claim is made in this milestone. New-memo conflict rejection was tested with an explicitly synthetic provider response, not a new paid memo-generation run.

## Remaining limitations and handoff

- The language checker is bounded phrase matching. Unsupported wording, negation and forward-looking judgments remain unreviewed; citations do not prove entailment. Further language coverage needs independent examples.
- Existing erroneous drafts remain in the stored JSON and raw-data downloads. The app's review layer identifies and withholds recognized conflicts; a full corpus repair or regeneration has not been performed.
- Model operand selection can be incomplete or inappropriate. Canonical labels and equations expose exactly what was computed; arithmetic verification does not verify the answer's completeness.
- Peer comparisons use the existing sector aggregate; constituent-level SEC citation lineage for that median is not supplied by the current dataset. Issuer input citations do not prove benchmark lineage.
- Money arithmetic uses the document's reporting currency and its existing normalization. No FX conversion, debt-scope reconciliation or proxy-quality overhaul is included.
- The review endpoint reads loaded/static documents and does not trigger paid generation or SEC fetching. Review freshness is checked against the issuer dataset build timestamp. A missing/unavailable review is labelled not checked.
- The pre-existing partial dataset synchronization remains uncommitted in this checkout. The branch contains only correctness code, tests and documentation; the weekly workflow and precomputation files are untouched. The original local repository is not pushed to or modified. This checkout now tracks the GitHub branch through a separate `github` remote; its inherited local `origin` is preserved.
- Existing Next.js dependency security warning remains open. Upgrade requires a separate scoped change because this task freezes dependency/UI work.

## CV and interview language

Suggested CV bullet: “Built source-bound arithmetic verification and bilingual comparison checks for an SEC-based credit research app, with explicit formulas, missing-data handling and regression tests for AI-generated financial claims.”

Suggested interview explanation: “I found that a citation could resolve while the conclusion was still reversed. I moved coverage and comparison direction into deterministic code, and made Q&A calculations identify their metric, period, unit and sources. The UI shows what was computed and what remains unreviewed. The checker covers specified phrases; it does not prove every sentence correct.”

Do not claim that all memos are corrected, every answer is verified, the app is institutional-grade, the risk bands are agency ratings, or that this work achieved a measured accuracy percentage. Describe the 90 checks as offline engineering regressions, not 87 independent financial audits.
