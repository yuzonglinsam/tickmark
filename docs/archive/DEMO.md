# Local acceptance and demonstration

Checked on 2026-10-11. Public deployment is pending. Examples use actual SEC filings and
real DeepSeek responses; the saved reports were editorially reviewed. They are historical
documentation examples, not an app data source or a guarantee about future results.

## Open and inspect

Open <http://127.0.0.1:8501>. If the server is stopped:

```bash
.venv311/bin/python -m streamlit run app.py
```

The ignored server `.env` is already configured on the development machine. Financials
load before AI. A first-time issuer may require **Reconcile filing XBRL**; use it to
inspect missing fields before relying on leverage or the screening score.

## A warm 60-second walkthrough

1. **0–10s:** Click KO, then Load research. Select FY 2025-12-31. If the research cache
   has expired, reconcile filing XBRL before the score demonstration.
2. **10–25s:** Explain operating EBIT plus scoped D&A = EBITDA proxy. Open its Learn &
   source control: USD 13.76bn + 1.05bn = 14.81bn. Show three fiscal years and source links.
3. **25–40s:** Open Stress Test. Set EBIT −5%, interest +5%, CFO −5%. Score changes from
   64.1 to 60.9. Reset returns it to 64.1. This makes no AI request; it is a static sensitivity.
4. **40–60s:** Open Credit Memo, load disclosures and inspect the saved reviewed narrative.
   Download the one-page PDF. Base-case memo stays separate from stress calculations.

This is a warm-cache demonstration, not a promise about cold filing parsing/AI latency.
After a method/source/model change, the memo may need explicit regeneration.

## Additional acceptance cases

- Search **TXN** through the normal text field. Revenue USD 17.68bn and FCF 2.60bn are
  sourced; interest, D&A and complete debt scope stay N/A under current extraction. Missing
  factors suppress the point score. Inspect its real reviewed memo/PDF.
- Search **TSM**. Three IFRS years retain TWD, with no guessed USD conversion or quarter.
  Its reviewed memo notes that the raw AI output required editorial repair.
- Search **Alphabet** to inspect multiple share classes; search **JPM** to see the explicit
  financial-institution exclusion.
- A client-selected issuer remains a final acceptance step. Wider debt/interest extraction
  and complete real debt-free acceptance remain release work.

## Reviewed exports

- [KO report](examples/ko-credit-memo.pdf): complete FY score, reviewed disposal-group debt.
- [TXN report](examples/txn-credit-memo.pdf): explicit financial extraction gaps.
- [TSM report](examples/tsm-credit-memo.pdf): IFRS/TWD and editorially repaired real AI prose.

## Portfolio claims at this checkpoint

Accurate: “Built a Python/Streamlit SEC research application with cited financial
normalization, fiscal-period assembly, deterministic credit screening, local stress
sensitivities, structured DeepSeek memos and one-page PDF exports; verified real issuer
examples and 54 local tests.”

Do not yet claim a public production service, durable hosted cache, universal accounting
coverage, agency-equivalent credit ratings or passing GitHub CI. Record those only after
the deployment checks in [DEPLOYMENT.md](DEPLOYMENT.md).
