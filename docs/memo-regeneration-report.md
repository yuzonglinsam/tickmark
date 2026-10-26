# Stored memo regeneration — 2026-10-26

The original repair task flagged 209 of 485 bilingual memos. After the weekly SEC refresh, the checked main-branch dataset contained 493 memos, of which the original checker flagged 208 (186 English, 130 Traditional Chinese). All 208 flagged issuer memos were regenerated, including seven issuers absent from the current batch universe: CF, CW, HSAI, NDSN, U, WCC and ZBRA.

## Results

- Regenerated English and Traditional Chinese memos for all 208 targets; KO passed as the initial pilot.
- Merged only `memo` and `passages` into each target issuer JSON. Every other issuer field is structurally identical to the baseline at `8ea27c8fc7085a47b6a954eef150da4f6a908039`: financial facts, metrics, peer statistics, financial definitions and SEC source tables did not change.
- All 493 stored memos have zero recognized deterministic conflicts under `consistency-v1.3`. Applying that same checker to the baseline finds 175 conflicted memos, so the comparable before/after result is **175 → 0**.
- All 13,170 evidence references in the regenerated bilingual memos resolve to the issuer's SEC sources or supplied filing passages. Memo and primary financial periods match, both languages have matching section/claim counts, and narrative text contains no digits.
- The regenerated corpus has 2,035 checked comparisons and 10,353 unreviewed clauses. Zero detected conflicts does **not** establish semantic correctness: source resolution is separate from whether the cited source entails a claim; qualitative, conditional and unsupported comparison grammar remains unreviewed. Memos remain drafts.

## Checker and regression repairs

The corpus run exposed two false-positive cases. Traditional Chinese free-cash-flow/debt wording could bind to operating-cash-flow/debt, and a clause with mixed directions could apply its first direction to the wrong target. `consistency-v1.3` adds the exact Traditional/Simplified Chinese FCF/debt names and leaves mixed-direction clauses unreviewed instead of asserting a comparison. Existing unambiguous conflict tests remain in place.

The API regression now loads the frozen erroneous KO fixture explicitly. It no longer depends on a known-bad production memo remaining in the shipped dataset.

Four Traditional Chinese sentences (WMB, TER, PPG and SWKS) were clarified against their English originals and deterministic values. The wording now states dividend/FCF direction and insufficient full coverage directly; the financial meaning and evidence references are unchanged.

## Execution and validation

The GitHub pilot queued without a runner initially. The local machine could reach SEC and DeepSeek, so generation completed locally using the existing guarded generator and server credentials. The duplicate GitHub pilot was cancelled. Individual failures were retried with explicit disclosure-reference and single-comparison context; no citations were added without model-generated supporting claims.

Local validation: **94 Python tests**, TypeScript, ESLint and a Next.js production build producing **506 pages** passed. The final corpus validator also checked memo/cache equality, regeneration timestamps, bilingual structure, digit guards, resolved references, matching financial periods, unchanged non-memo issuer fields and the full stored-corpus audit.

The task's separate Next.js security patch was merged through PR #3 after its checks passed: Next.js and eslint-config-next changed from 16.4.0 to 16.4.2. A separate high-severity transitive `zod` npm advisory remains outside this memo repair; this work does not claim a clean dependency security audit.

The manual GitHub workflow remains available, but this repair does not claim a completed end-to-end Actions regeneration. Its CLI still selects issuers from the current universe, so an explicit historical ticker outside that list requires using the stored issuer metadata, as done for the seven names above. Generation logs must be reviewed for individual failures before accepting its output.
