"""SEC-backed Streamlit credit research workbench."""
from __future__ import annotations

from datetime import datetime, timezone
import os

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from credit_workbench.disclosures import annual_document, extract_passages
from credit_workbench.memo import MemoError, generate
from credit_workbench.memo_cache import MemoStore
from credit_workbench.metrics import calculate, revenue_growth
from credit_workbench.models import Snapshot
from credit_workbench.normalize import EXTRACTOR_VERSION, NormalizedResearch, normalize
from credit_workbench.pdf_export import render_pdf
from credit_workbench.scoring import METHODOLOGY_VERSION, score
from credit_workbench.sec import SECClient, SECError
from credit_workbench.stress import stress
from credit_workbench.xbrl_fallback import reconcile
from credit_workbench.research import encode_research, decode_research, memo_identity, financial_identity

load_dotenv()
st.set_page_config(page_title="Credit Research Workbench", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown("""
<style>
  .stApp {background:#F5F7FA;color:#142C4B}
  .block-container {max-width:1180px;padding-top:2.3rem;padding-bottom:4rem}
  h1,h2,h3 {color:#142C4B;letter-spacing:-.025em}
  h1 {font-weight:720!important;font-size:2.5rem!important}
  [data-testid="stMetric"] {background:#fff;border:1px solid #DCE5ED;border-radius:10px;
    padding:16px 18px;min-height:110px}
  [data-testid="stMetricLabel"] {color:#657587}
  [data-testid="stMetricValue"] {color:#142C4B}
  [data-testid="stTabs"] button[aria-selected="true"] {color:#167C80;border-bottom-color:#167C80}
  div.stButton>button[kind="primary"] {background:#167C80;border-color:#167C80;color:#fff}
  .eyebrow {font-size:.74rem;letter-spacing:.17em;color:#167C80;font-weight:700}
  .subtle {color:#657587;font-size:.93rem}
</style>
""", unsafe_allow_html=True)


def config(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, RuntimeError):
        return default


@st.cache_resource
def sec_client(identity: str) -> SECClient:
    return SECClient(identity)


@st.cache_resource
def memo_store(database_url: str) -> MemoStore:
    return MemoStore(database_url or None)


def money(value: float | None, unit: str = "USD") -> str:
    if value is None:
        return "N/A"
    if unit == "x":
        return f"{value:.2f}x"
    if unit == "ratio":
        return f"{value * 100:.1f}%"
    scale = 1e9 if abs(value) >= 1e9 else 1e6
    return f"{value / scale:,.2f}{'bn' if scale == 1e9 else 'm'}"


def search_issuer(client: SECClient, query: str) -> None:
    try:
        st.session_state.search_results = client.search(query)
    except (SECError, ValueError) as exc:
        st.session_state.search_results = []
        st.error(str(exc))


def load_research(client: SECClient, selected: dict) -> None:
    submissions = client.submissions(selected['cik'])
    cache_key = financial_identity(submissions, selected['ticker'])
    cached = None
    try:
        cached = memo_store(config('CACHE_DATABASE_URL')).get_analysis(cache_key, max_age=3600)
    except Exception:
        pass  # Financial research remains available if persistence is unavailable.
    facts = None
    if cached:
        research = decode_research(cached)
    else:
        facts = client.company_facts(selected['cik'])
        research = normalize(submissions, facts, selected['ticker'], datetime.now(timezone.utc).date())
    st.session_state.update(research=research, submissions=submissions, companyfacts=facts,
                            freshness=dict(client.statuses), reconciled_notes=(), passages=(), passage_key=None)
    for widget in ('stress_ebit', 'stress_interest', 'stress_cfo', 'period_selector'):
        st.session_state.pop(widget, None)


def source_links(snapshot: Snapshot, keys: tuple[str, ...]) -> None:
    sources = {source.evidence_id: source for key in keys
               if key in snapshot.facts for source in snapshot.facts[key].sources}
    if not sources:
        st.caption("No exact SEC source is available for this field.")
    for source in sources.values():
        st.markdown(f"[SEC {source.form} · {source.filed_on} · {source.concept}]({source.url})")


def score_panel(snapshot: Snapshot) -> None:
    result = score(snapshot)
    if result.value is None:
        st.info(f"No point score: {result.coverage}% of factors supported. "
                f"Mathematically possible range: {result.lower_bound:.1f}–{result.upper_bound:.1f}. "
                "This is not a statistical confidence interval.")
    else:
        st.metric("Heuristic credit health", f"{result.value:.1f} / 100", result.band,
                  delta_color="off")
    with st.expander("Scoring methodology and factor coverage"):
        st.caption("Uncalibrated screening heuristic. No agency rating, probability of default or recommendation.")
        st.dataframe([{"Factor": f.name.replace("_", " ").title(), "Weight": f.weight,
                       "Points": "N/A" if f.points is None else f'{f.points:.1f}',
                       "Method": f.explanation} for f in result.factors],
                     width='stretch', hide_index=True)


def overview(research: NormalizedResearch, snapshot: Snapshot) -> None:
    metrics = calculate(snapshot)
    st.markdown("### Financial profile")
    st.caption(f"{snapshot.currency} base units; values displayed in millions or billions. "
               f"{snapshot.flow_period.basis.upper()} {snapshot.flow_period.start}–{snapshot.flow_period.end}. "
               f"Source as of {snapshot.as_of} UTC.")
    keys = ("revenue", "operating_income", "ebitda_proxy", "fcf")
    labels = ("Revenue", "Operating EBIT proxy", "EBITDA proxy", "Free cash flow")
    cols = st.columns(4)
    for col, key, label in zip(cols, keys, labels):
        with col:
            st.metric(label, money(metrics[key].value, metrics[key].unit))
            with st.popover("Learn & source"):
                st.write(metrics[key].formula)
                inputs = {'ebitda_proxy': ('operating_income', 'depreciation_amortization'),
                          'fcf': ('operating_cash_flow', 'capex')}.get(key, (key,))
                substitution = ' + ' if key == 'ebitda_proxy' else ' − '
                st.write('Current issuer: ' + substitution.join(
                    f"{name.replace('_', ' ')} {money(snapshot.facts[name].value, snapshot.currency)}"
                    for name in inputs) + f" = {money(metrics[key].value, metrics[key].unit)} {snapshot.currency}")
                if key == "ebitda_proxy":
                    st.caption("Operating income plus cash-flow D&A; it is not issuer-adjusted EBITDA.")
                if metrics[key].value is None:
                    st.warning(metrics[key].explanation)
                source_links(snapshot, (key,) if key in snapshot.facts else
                             (("operating_income", "depreciation_amortization") if key == "ebitda_proxy"
                              else ("operating_cash_flow", "capex")))
    left, right = st.columns((1.65, 1))
    with left:
        history = list(reversed(research.annual))
        fig = go.Figure()
        for key, title, color in (("revenue", "Revenue", "#167C80"),
                                  ("operating_income", "Operating EBIT", "#142C4B"),
                                  ("operating_cash_flow", "Operating cash flow", "#89A8B7")):
            fig.add_trace(go.Scatter(x=[str(s.flow_period.end) for s in history],
                                     y=[(s.facts[key].value / 1e9) if s.facts[key].value is not None
                                        else None for s in history], name=title,
                                     mode="lines+markers", line={"color": color, "width": 3},
                                     marker={"size": 8}))
        fig.update_layout(height=330, plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                          margin={"l": 12, "r": 12, "t": 25, "b": 35},
                          yaxis_title=f"{snapshot.currency} billions · fiscal years",
                          legend={"orientation": "h", "y": -0.22},
                          hovermode="x unified")
        st.plotly_chart(fig, width='stretch')
        if len(research.annual) > 1:
            growth = revenue_growth(research.annual[0], research.annual[1])
            st.caption(f"Comparable annual revenue growth: {money(growth.value, 'ratio') if growth.value is not None else 'N/A'}")
    with right:
        score_panel(snapshot)
    st.markdown("### Source-aware financial table")
    table = []
    for key, fact in snapshot.facts.items():
        table.append({"Field": key.replace("_", " ").title(),
                      "Value": money(fact.value, fact.unit), "Status": fact.status,
                      "SEC concept": ", ".join(s.concept for s in fact.sources) or "N/A",
                      "Method / missing reason": fact.note})
    st.dataframe(table, width='stretch', hide_index=True)
    with st.expander("Filing links and exact fact evidence"):
        for key, fact in snapshot.facts.items():
            st.markdown(f"**{key.replace('_',' ').title()}** · {fact.period.start or 'instant'} → {fact.period.end}")
            source_links(snapshot, (key,))
            if fact.lineage:
                st.caption('Superseded values retained for restatement lineage:')
                for source in fact.lineage:
                    st.markdown(f"[Earlier SEC observation · {source.filed_on} · {source.concept}]({source.url})")


def stress_tab(snapshot: Snapshot) -> None:
    st.markdown("### Local stress test")
    st.caption("Static sensitivity from the immutable base. Negative shocks subtract a percentage of the absolute base, "
               "so a loss deteriorates. D&A, capex, debt and cash are held fixed. Slider moves make no AI request.")
    if snapshot.flow_period.basis == "quarter":
        st.warning("Quarter-only flows cannot produce an annual debt-health score. Select FY or TTM for the full view.")
    settings = (("operating_income", "EBIT change", "stress_ebit", -100, 100),
                ("interest_expense", "Interest expense change", "stress_interest", -100, 200),
                ("operating_cash_flow", "Operating cash flow change", "stress_cfo", -100, 100))
    values = {}
    for field, label, widget, low, high in settings:
        fact = snapshot.facts[field]
        disabled = fact.value in (None, 0)
        values[field] = st.slider(label, low, high, 0, step=5, key=widget, disabled=disabled,
                                  help="Unavailable or zero base cannot move under a percentage-only shock."
                                       if disabled else None) / 100
        if disabled:
            st.caption(f"{label}: base is {'missing' if fact.value is None else 'zero'}; percentage stress is disabled.")
    def reset_stress():
        for _, _, widget, _, _ in settings:
            st.session_state[widget] = 0
    st.button("Reset stress controls", on_click=reset_stress)
    scenario = stress(snapshot, ebit_change=values["operating_income"],
                      interest_change=values["interest_expense"],
                      cash_flow_change=values["operating_cash_flow"])
    base, changed = calculate(snapshot), calculate(scenario)
    rows = []
    for key in ("operating_income", "interest_expense", "operating_cash_flow", "fcf",
                "ebitda_proxy", "gross_leverage", "interest_coverage"):
        rows.append({"Metric": key.replace("_", " ").title(),
                     "Base": money(base[key].value, base[key].unit),
                     "Scenario": money(changed[key].value, changed[key].unit)})
    st.dataframe(rows, width='stretch', hide_index=True)
    a, b = score(snapshot), score(scenario)
    st.caption(f"Base score: {a.value if a.value is not None else 'N/A'} · "
               f"Scenario score: {b.value if b.value is not None else 'N/A'} · "
               "Base memo, if present, remains a base-case narrative.")


def memo_tab(client: SECClient, research: NormalizedResearch, snapshot: Snapshot) -> None:
    st.markdown("### DeepSeek credit memo")
    st.caption("Generated only on explicit action. Claims cite SEC filing passages or exact financial facts; "
               "numbers remain in the deterministic table. The memo is the base case and does not update with stress sliders.")
    if snapshot.flow_period.basis == "quarter":
        st.info("Select an annual or reconciled TTM period before generating a memo.")
        return
    key_secret = config("DEEPSEEK_API_KEY")
    if not key_secret:
        st.info("The server's DeepSeek secret is not configured; financial research and stress remain available.")
        return
    database_url = config("CACHE_DATABASE_URL")
    try:
        store = memo_store(database_url)
    except Exception:
        st.error("Memo storage is unavailable; no paid generation was attempted.")
        return
    if not store.durable:
        st.warning("Development cache is local SQLite. Hosted persistence needs a server-only PostgreSQL connection.")
    doc = annual_document(st.session_state.submissions)
    if not doc:
        st.warning("No annual SEC filing document is available for cited disclosures.")
        return
    url, accession = doc
    passage_cache_key = f"{research.cik}:{accession}"
    if st.session_state.get("passage_key") != passage_cache_key:
        if st.button("Load SEC disclosures", type="secondary"):
            try:
                with st.spinner("Extracting bounded passages from the SEC annual filing..."):
                    passages = extract_passages(client.filing_html(url), url, accession)
                st.session_state.passages = passages
                st.session_state.passage_key = passage_cache_key
                st.rerun()
            except (SECError, ValueError) as exc:
                st.error(str(exc))
        return
    passages = st.session_state.get("passages", ())
    if not passages:
        st.warning("The annual filing yielded no reliable bounded passages; memo generation is disabled.")
        return
    with st.expander("Disclosure excerpts sent to DeepSeek"):
        for passage in passages:
            st.markdown(f"**{passage.heading}** · [SEC filing]({passage.url}) · `{passage.evidence_id}`")
            st.write(passage.text[:900] + ("…" if len(passage.text) > 900 else ""))
    identity = memo_identity(snapshot, passages, config("DEEPSEEK_MODEL", "deepseek-flash"))
    try:
        store.save_analysis(identity, encode_research(research))
    except Exception:
        st.error("Research persistence is unavailable; no paid generation was attempted.")
        return
    try:
        memo = store.get(identity)
    except Exception:
        st.error('Saved memo is unavailable; financials remain available and no paid generation was attempted.')
        return
    if memo is None and st.button("Generate cited base-case memo", type="primary"):
        last_call = st.session_state.get("last_memo_call", 0.0)
        now = datetime.now(timezone.utc).timestamp()
        if now - last_call < 30:
            st.warning("Please wait briefly before another paid generation request.")
        elif not store.claim(identity):
            with st.spinner("Another session is generating this exact memo..."):
                memo = store.wait(identity)
            if memo is None:
                st.warning("Generation is in progress; retry in a moment.")
        elif not store.allow_call():
            store.release(identity)
            st.warning("The shared hourly generation limit is reached; financials remain available.")
        else:
            st.session_state.last_memo_call = now
            try:
                with st.spinner("Generating and validating cited research..."):
                    memo = generate(snapshot, passages, api_key=key_secret,
                                    model=config("DEEPSEEK_MODEL", "deepseek-flash"),
                                    base_url=config("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
                store.finish(identity, memo)
            except MemoError as exc:
                store.release(identity)
                st.error(str(exc))
    if memo:
        st.success(f"Validated JSON structure · generated {memo.generated_at[:19]} UTC · {memo.model} · "
                   f"prompt {memo.prompt_version}.")
        if memo.reviewed_at:
            st.caption(f"Editorial review: {memo.reviewed_at[:19]} UTC · {memo.review_notes}")
        else:
            st.info('AI draft: citation structure is checked automatically; claim support needs editorial review.')
        source_map = {s.evidence_id: s.url for f in snapshot.facts.values() for s in f.sources}
        source_map.update({p.evidence_id: p.url for p in passages})
        for title, section in (("Credit Strengths", "credit_strengths"),
                               ("Key Risks", "key_risks"),
                               ("Debt Servicing Capacity", "debt_servicing_capacity"),
                               ("Overall Credit View", "overall_credit_view")):
            st.markdown(f"#### {title}")
            for claim in memo.sections[section]:
                st.write(claim.text)
                links = list(dict.fromkeys(source_map[e] for e in claim.evidence_ids))
                st.caption("Sources: " + " · ".join(f"[SEC {i}]({url})" for i, url in enumerate(links, 1)))
        try:
            output = render_pdf(snapshot, memo, passages, research.name)
            st.download_button("Download one-page PDF", output,
                               file_name=f"{research.ticker.lower()}-credit-memo.pdf",
                               mime="application/pdf", type="primary")
        except ValueError as exc:
            st.error(f"PDF export needs a shorter memo: {exc}")


st.markdown('<div class="eyebrow">RESEARCH WORKBENCH / SEC EDGAR</div>', unsafe_allow_html=True)
st.title("Credit clarity, with a source trail.")
st.markdown('<p class="subtle">Public-company fundamentals, transparent sensitivity and cited credit research.</p>',
            unsafe_allow_html=True)
identity = config("SEC_USER_AGENT")
if not identity:
    st.error("SEC server identity is not configured. Set SEC_USER_AGENT in server environment or Streamlit secrets.")
    st.stop()
try:
    client = sec_client(identity)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

with st.form("search", clear_on_submit=False):
    query = st.text_input("Search a US-listed ticker or company", placeholder="e.g. CAT or Caterpillar")
    submitted = st.form_submit_button("Search SEC index", type="primary")
if submitted:
    search_issuer(client, query)
st.caption("Quick starts use the same live SEC search: " + "  ")
quick = st.columns((1, 1, 1, 5))
for col, ticker in zip(quick, ("AAPL", "KO", "BA")):
    with col:
        if st.button(ticker, width='stretch'):
            search_issuer(client, ticker)
results = st.session_state.get("search_results", [])
if results:
    selected = st.selectbox("Matching issuers", results,
                            format_func=lambda r: f"{r['ticker']} · {r['name']} · CIK {r['cik']}")
    if st.button("Load research", type="primary"):
        try:
            with st.spinner("Loading current SEC filings and exact XBRL facts..."):
                load_research(client, selected)
        except (SECError, ValueError) as exc:
            st.error(str(exc))
elif submitted:
    st.info("No matching ticker or company name appeared in the SEC index.")

research = st.session_state.get("research")
if research:
    st.divider()
    st.markdown(f"## {research.name}  ·  {research.ticker}")
    st.caption(f"CIK {research.cik} · fiscal year end {research.fiscal_year_end} · "
               f"latest analyzed FY {research.annual[0].flow_period.end}")
    status = [s for url, s in st.session_state.get('freshness', {}).items()
              if research.cik in url]
    if status:
        st.caption('SEC data last checked: ' + min(s['data_checked_at'] for s in status)[:19] + ' UTC')
        for s in status:
            if s['stale']:
                st.warning(s['reason'] + ' Last refresh attempted: ' + s['last_attempt_at'][:19] + ' UTC')
    refresh, filing_review = st.columns(2)
    if refresh.button('Refresh SEC data'):
        try:
            with st.spinner('Checking latest SEC filings...'):
                submissions = client.submissions(research.cik, refresh=True)
                facts = client.company_facts(research.cik, refresh=True)
                st.session_state.freshness = dict(client.statuses)
                if any(s['stale'] for url,s in client.statuses.items() if research.cik in url):
                    st.warning('SEC refresh is unavailable. The previous reconciled analysis is retained as stale.')
                    st.rerun()
                if st.session_state.get('reconciled_notes') or research.annual[0].facts['debt'].value is not None:
                    facts, _ = reconcile(submissions, facts, client.identity)
                updated = normalize(submissions, facts, research.ticker, datetime.now(timezone.utc).date())
            st.session_state.update(research=updated, submissions=submissions, companyfacts=facts,
                                    freshness=dict(client.statuses), reconciled_notes=(), passage_key=None)
            st.rerun()
        except (SECError, ValueError) as exc:
            st.error('Refresh failed; previous analysis retained. ' + str(exc))
    if filing_review.button('Reconcile filing XBRL', help='Parse latest annual and quarter filings for missing standard consolidated facts.'):
        try:
            with st.spinner('Reconciling the actual SEC filing instances...'):
                facts = st.session_state.get('companyfacts') or client.company_facts(research.cik)
                merged, notes = reconcile(st.session_state.submissions, facts, client.identity)
                updated = normalize(st.session_state.submissions, merged, research.ticker, datetime.now(timezone.utc).date())
            st.session_state.update(research=updated, companyfacts=merged, reconciled_notes=notes)
            try:
                memo_store(config('CACHE_DATABASE_URL')).save_analysis(
                    financial_identity(st.session_state.submissions, research.ticker), encode_research(updated))
            except Exception:
                st.warning('Reconciliation succeeded, but saving the public research cache failed.')
            st.rerun()
        except Exception:
            st.error('Filing XBRL reconciliation failed; previous analysis retained. Try again later.')
    for note in st.session_state.get('reconciled_notes', ()):
        st.caption(note)
    for warning in research.warnings:
        st.warning(warning)
    choices = {f"FY {s.flow_period.end}": s for s in research.annual}
    if research.quarter:
        choices[f"Quarter {research.quarter.flow_period.end}"] = research.quarter
    if research.ttm:
        choices[f"TTM {research.ttm.flow_period.end}"] = research.ttm
    selected_period = st.selectbox("Analysis period", list(choices), key="period_selector")
    snapshot = choices[selected_period]
    tab_overview, tab_stress, tab_memo = st.tabs(("Overview", "Stress Test", "Credit Memo"))
    with tab_overview:
        overview(research, snapshot)
    with tab_stress:
        stress_tab(snapshot)
    with tab_memo:
        memo_tab(client, research, snapshot)
    st.divider()
    st.caption("Educational screening only. Numeric gaps remain N/A; sourced filings and accounting judgments "
               "should be reviewed before any investment or lending decision.")
