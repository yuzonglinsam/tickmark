"""Deterministic comparisons and bounded, bilingual prose checks (not semantic proof).

Unknown language is explicitly unreviewed. Never infer zero for a missing operand,
compare different debt definitions, or call a qualitative judgement verified.
"""
from __future__ import annotations

from datetime import date
import math
import re

VERSION = "consistency-v1.2"
# key -> peer key, preferred direction. Adjusted net leverage matches peer nlev.
DIRECTIONS = {
    "gross_leverage": ("lev", "lower"), "net_leverage_adj": ("nlev", "lower"),
    "current_ratio": ("cr", "higher"), "interest_coverage": ("icov", "higher"),
    "ebitda_coverage": ("ecov", "higher"), "cfo_to_debt": ("cfod", "higher"),
    "fcf_to_debt": ("fcfd", "higher"), "operating_margin": ("om", "higher"),
}


def finite(v):
    return isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v)


def row(doc, key, pid=None):
    pid = pid or doc["primary"]
    for group in ("metrics", "facts", "extended"):
        r = doc.get(group, {}).get(pid, {}).get(key) or {}
        if finite(r.get("value")):
            return {"value": r["value"], "sources": r.get("evidence", r.get("sources", []))}
    return {"value": None, "sources": []}


def deterministic_facts(doc):
    pid = doc["primary"]
    out = {}

    def compare(key, left, right, formula, preferred="higher", sources=()):
        known = finite(left) and finite(right)
        relation = ("equal" if math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-12)
                    else "above" if left > right else "below") if known else "unknown"
        out[key] = {"id": key, "period": pid, "left": left, "right": right,
                    "relation": relation, "preferred": preferred, "formula": formula,
                    "sources": sorted(set(sources)),
                    "ratio": left / right if known and right > 0 else None}

    def coverage(key, left_key, right_keys):
        a = row(doc, left_key)
        bs = [row(doc, k) for k in right_keys]
        b = sum(r["value"] for r in bs) if all(finite(r["value"]) for r in bs) else None
        compare(key, a["value"], b, f"{left_key} vs {' + '.join(right_keys)}",
                sources=a["sources"] + [s for r in bs for s in r["sources"]])
        out[key]["covered"] = a["value"] >= b if finite(a["value"]) and finite(b) and b >= 0 else None

    coverage("ocf_capex_dividends", "operating_cash_flow", ["capex", "dividends"])
    coverage("ocf_dividends", "operating_cash_flow", ["dividends"])
    coverage("ocf_buybacks", "operating_cash_flow", ["buybacks"])
    coverage("ocf_distributions", "operating_cash_flow", ["dividends", "buybacks"])
    coverage("fcf_distributions", "fcf", ["dividends", "buybacks"])
    coverage("fcf_buybacks", "fcf", ["buybacks"])
    coverage("fcf_dividends", "fcf", ["dividends"])
    periods = sorted((p for p in doc["periods"] if p["basis"] == "annual"), key=lambda p: p["end"], reverse=True)
    current = next((p for p in periods if p["id"] == pid), None)
    previous = next((p for p in periods if current and p["end"] < current["end"]), None)
    comparable = bool(previous and current and 330 <= (date.fromisoformat(current["end"]) - date.fromisoformat(previous["end"])).days <= 400
                      and current.get("start") and previous.get("start")
                      and abs((date.fromisoformat(current["end"]) - date.fromisoformat(current["start"])).days
                              - (date.fromisoformat(previous["end"]) - date.fromisoformat(previous["start"])).days) <= 14)
    for key, (peer, preferred) in DIRECTIONS.items():
        a = row(doc, key)
        b = row(doc, key, previous["id"]) if comparable else {"value": None, "sources": []}
        compare(key + ".yoy", a["value"], b["value"], f"{key}: {pid} vs {previous['id'] if comparable else 'unavailable comparable prior year'}", preferred, a["sources"] + b["sources"])
        compare(key + ".peer", a["value"], (doc.get("peers") or {}).get("median", {}).get(peer),
                f"{key} vs sector median {peer} (same definition)", preferred, a["sources"])
    for key in ("current_ratio", "interest_coverage", "ebitda_coverage"):
        a = row(doc, key)
        compare(key + ".one", a["value"], 1, f"{key} vs one", "higher", a["sources"])
    for side, key in (("leverage", "net_leverage_adj"), ("cashflow", "cfo_to_net_debt")):
        rp = doc.get("risk_profile", {})
        h = (rp.get("headroom") or {}).get(side) or {}
        compare(key + ".threshold", (rp.get(side) or {}).get("value"), h.get("next_threshold"),
                f"{key} vs next risk-band boundary (net-debt basis)", "lower" if side == "leverage" else "higher",
                (row(doc, "net_leverage_adj")["sources"] if side == "leverage" else
                 row(doc, "cfo_to_debt")["sources"] + row(doc, "net_debt_adj")["sources"]))
    return out


METRICS = {
    "net_leverage_adj": r"net leverage|net.debt.to.ebitda|淨槓桿|净杠杆",
    "gross_leverage": r"gross leverage|(?<!net )\bleverage\b|總槓桿|总杠杆",
    "current_ratio": r"current ratio|流動比率|流动比率",
    "interest_coverage": r"interest coverage|利息覆蓋率|利息覆盖率",
    "ebitda_coverage": r"ebitda coverage",
    "cfo_to_debt": r"(?:cash flow|cfo|ocf).to.debt|現金流對債務比率|现金流对债务比率",
    "fcf_to_debt": r"(?:free cash flow|fcf).to.debt",
    "operating_margin": r"operating margin|營業利潤率|营业利润率",
}
ABOVE = r"above|higher than|exceeds?|greater than|高[於于]|超過|超过"
BELOW = r"below|lower than|less than|lags?|weaker than|低[於于]|弱[於于]|落後|落后"
IMPROVE = r"improv(?:e[ds]?|ing)|strengthen(?:ed|s)?|改善"
WORSEN = r"deteriorat(?:e[ds]?|ing)|worsen(?:ed|s)?|weaken(?:ed|s)?|惡化|恶化"
COVER = r"covers?|covering|covered|sufficient|enough|覆蓋|覆盖|足以|足夠|足够"
NEGATIVE = r"\bnot\b|neither|no longer|cannot|can't|does not|do not|not fully|insufficient|inadequate|fails? to|unable to|不足|未能|無法|无法|不能|不敷|不(?:足以|足夠|足够)"
OCF = r"operating cash flow|\b(?:ocf|cfo)\b|營運現金流|經營現金流|经营现金流"
FCF = r"free cash flow|\bfcf\b|自由現金流|自由现金流"
DIV = r"dividends?|股息|分紅|分红"
DIST = r"shareholder (?:distributions?|returns?)|股東分派|股东分配|buybacks?|repurchases?|回購|回购"
CAPEX = r"capex|capital expenditur(?:e|es)|資本開支|资本开支"


def check_sections(sections, facts):
    """Extract explicit comparisons per clause. All other prose remains unreviewed."""
    checks = []
    for section, claims in sections.items():
        for index, claim in enumerate(claims):
            text = claim["text"] if isinstance(claim, dict) else claim.text
            for clause in re.split(r"[.;。；，]|,\s+and\s+|,?\s+but\s+|,?\s+however,?\s*|但|然而", text, flags=re.I):
                clause = clause.strip()
                if re.search(r"\b(?:could|may|would|if|forecast|expected)\b|可能|預期|预计|若", clause, re.I):
                    checks.append({"section": section, "index": index, "text": clause, "fact_id": None,
                                   "status": "unreviewed", "reason": "Conditional or forward-looking statement"})
                    continue
                if not clause:
                    continue
                found = []
                def add(fid, expected, test=None):
                    fact = facts.get(fid, {})
                    actual = fact.get("relation", "unknown")
                    if expected in ("covered", "not covered") and fact.get("covered") is None:
                        actual = "unknown"
                    status = "unreviewed" if actual == "unknown" or expected is None else (
                        "consistent" if (test(fact) if test else actual == expected) else "conflict")
                    found.append({"section": section, "index": index, "text": clause,
                                  "fact_id": fid, "expected": expected, "actual": actual, "status": status,
                                  "formula": fact.get("formula", ""), "sources": fact.get("sources", []),
                                  "left": fact.get("left"), "right": fact.get("right")})

                # Cash coverage, including reversed 'distributions exceed FCF'.
                has_ocf, has_fcf = bool(re.search(OCF, clause, re.I)), bool(re.search(FCF, clause, re.I))
                has_div, has_dist = bool(re.search(DIV, clause, re.I)), bool(re.search(DIST, clause, re.I))
                if (has_ocf or has_fcf) and (has_div or has_dist):
                    # Ambiguous funding bases and unsupported compound uses remain unreviewed.
                    fid = None
                    if not (has_ocf and has_fcf):
                        base = "ocf" if has_ocf else "fcf"
                        if re.search(CAPEX, clause, re.I):
                            if has_ocf and has_div and not has_dist:
                                fid = "ocf_capex_dividends"
                        elif has_dist:
                            distribution_total = bool(re.search(r"shareholder (?:distributions?|returns?)|股東分派|股东分配", clause, re.I))
                            fid = base + ("_distributions" if has_div or distribution_total else "_buybacks")
                        elif has_div:
                            fid = base + "_dividends"
                    neg = bool(re.search(NEGATIVE, clause, re.I))
                    if fid is None:
                        pass
                    elif re.search(COVER, clause, re.I):
                        # Covers is directional: distributions 'covered by FCF' is supported;
                        # distributions 'cover FCF' is not an understood coverage statement.
                        funding = re.search(OCF if has_ocf else FCF, clause, re.I)
                        use = re.search(DIV + "|" + DIST, clause, re.I)
                        if funding.start() < use.start() or re.search(r"covered by|由.*(?:覆蓋|覆盖)", clause, re.I):
                            add(fid, "not covered" if neg else "covered", lambda f: f.get("covered") is (not neg))
                    elif re.search(ABOVE + "|" + BELOW, clause, re.I):
                        funding = re.search(OCF if has_ocf else FCF, clause, re.I)
                        use = re.search(DIV + "|" + DIST, clause, re.I)
                        above = bool(re.search(ABOVE, clause, re.I))
                        expected = "above" if above == (funding.start() < use.start()) else "below"
                        add(fid, None if neg else expected)
                    elif has_fcf and re.search(r"most|大部分", clause, re.I):
                        add(fid, "uses most but not more than FCF", lambda f: f.get("ratio") is not None and 1 <= f["ratio"] < 2)

                candidates = [(m.start(), m.end(), key) for key, pattern in METRICS.items()
                              for m in re.finditer(pattern, clause, re.I)]
                # Prefer the longest metric name so FCF/debt cannot bind to CFO/debt,
                # and net leverage cannot also bind to generic gross leverage.
                matches = []
                for candidate in sorted(candidates, key=lambda m: m[1] - m[0], reverse=True):
                    start, end, _ = candidate
                    if not any(start < b and end > a for a, b, _ in matches):
                        matches.append(candidate)
                matches.sort()
                for j, (start, end, key) in enumerate(matches):
                    segment = clause[start:matches[j + 1][0] if j + 1 < len(matches) else len(clause)]
                    direction = "above" if re.search(ABOVE, segment, re.I) else "below" if re.search(BELOW, segment, re.I) else None
                    suffix = ".peer" if re.search(r"median|中位數|中位数", segment, re.I) else ".threshold" if re.search(r"threshold|boundary|門檻|门槛", segment, re.I) else ".one" if re.search(r"\bone\b|unity|一", segment, re.I) else None
                    if direction and suffix:
                        add(key + suffix, None if re.search(NEGATIVE, segment, re.I) else direction)
                    elif re.search(IMPROVE + "|" + WORSEN + r"|increas(?:ed|es)|decreas(?:ed|es)|rose|fell|上升|下降", segment, re.I):
                        if re.search(r"could|may|would|if|可能|若|預期|预计", segment, re.I):
                            continue
                        if re.search(IMPROVE + "|" + WORSEN, segment, re.I):
                            improved = bool(re.search(IMPROVE, segment, re.I))
                            higher = DIRECTIONS[key][1] == "higher"
                            direction = "above" if improved == higher else "below"
                        else:
                            direction = "above" if re.search(r"increas|rose|上升", segment, re.I) else "below"
                        add(key + ".yoy", None if re.search(NEGATIVE, segment, re.I) else direction)
                if not found:
                    found.append({"section": section, "index": index, "text": clause,
                                  "fact_id": None, "status": "unreviewed",
                                  "reason": "Outside supported comparison grammar; analyst review required"})
                checks.extend(found)
    conflicts = sum(c["status"] == "conflict" for c in checks)
    return {"version": VERSION, "status": "conflict" if conflicts else "partial",
            "checked": sum(c["status"] != "unreviewed" for c in checks), "conflicts": conflicts,
            "unreviewed": sum(c["status"] == "unreviewed" for c in checks), "checks": checks,
            "scope": "Rule-based financial comparisons only; citations and other prose need separate review."}


def audit_memo(doc, memo=None):
    facts = deterministic_facts(doc)
    memo = memo if memo is not None else doc.get("memo") or {}
    return {lang: check_sections(memo[lang], facts) for lang in ("en", "zh") if memo.get(lang)}


def memo_review(doc, memo=None):
    """Citations and numerical consistency are distinct checks, never semantic proof."""
    memo = memo if memo is not None else doc.get('memo') or {}
    audit = audit_memo(doc, memo)
    citations = {}
    for lang in ('en', 'zh'):
        if not memo.get(lang):
            continue
        refs = [e for claims in memo[lang].values() for c in claims for e in c.get('evidence', [])]
        def resolves(e):
            if 'passage' in e:
                return any(p['id'] == e['passage'] for p in doc.get('passages', []))
            return any(s.get('accession') == e.get('accession') and s.get('concept') == e.get('concept')
                       for s in doc.get('sources', {}).values())
        citations[lang] = {'total': len(refs), 'resolved': sum(resolves(e) for e in refs)}
    return {'issuer_generated_at': doc.get('generated_at'), 'consistency': audit, 'citations': citations, 'facts': deterministic_facts(doc),
            'coverage': coverage_note(doc)}


def coverage_note(doc):
    periods = doc.get('periods', [])
    primary = next((p for p in periods if p['id'] == doc.get('primary')), {})
    quarters = [p for p in periods if p.get('basis') == 'quarter']
    return {'dataset_built': doc.get('generated_at'), 'evidence_cutoff': doc.get('as_of'),
            'financial_start': primary.get('start'), 'financial_end': primary.get('end'),
            'basis': primary.get('basis'), 'available_quarters': [p['id'] for p in quarters],
            'note': 'Dataset build and evidence cut-off are not the financial coverage period. '
                    + ('Only the listed quarters are available; absent quarters are unavailable, not zero. '
                       if quarters else 'No standalone quarters are available; annual figures do not imply quarterly coverage. ')
                    + 'The simplified risk band uses net leverage and CFO/net debt, not a full agency methodology or credit rating.'}
