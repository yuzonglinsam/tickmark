"""Reconcile standard consolidated facts from the actual filing instance.

Custom labels are diagnostics only. No label matching fills canonical numbers.
The shared EdgarTools transport is capped at two requests per second, reserving
another two for SECClient. Only one filing parse runs at a time per process.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
import math
import os
from pathlib import Path
import threading
from uuid import uuid4

from .normalize import ANNUAL_FORMS, QUARTER_FORMS

_PARSE_LOCK = threading.Lock()
FALLBACK_VERSION = 'filing-xbrl-v0.2'
# Reviewed against the FY2025 disposal-group table and debt note. These are
# supplemental borrowing balances, not the continuing-operations debt total.
REVIEWED_EXTENSIONS = {
    'ko:DisposalGroupIncludingDiscontinuedOperationCurrentMaturitiesOfLongTermDebt',
    'ko:DisposalGroupIncludingDiscontinuedOperationLongTermDebt',
}


def latest_filings(submissions: dict, as_of: date) -> list[dict]:
    recent = submissions.get('filings', {}).get('recent', {})
    selected = []
    for family in ({'10-K', '20-F', '40-F'}, {'10-Q'}):
        for i, form in enumerate(recent.get('form', [])):
            if form in family and recent['filingDate'][i] <= as_of.isoformat():
                selected.append({k: recent[k][i] for k in
                                 ('form', 'accessionNumber', 'filingDate', 'primaryDocument', 'reportDate')})
                break
    return selected


def standard_rows(frame, filing: dict, cik: str) -> list[dict]:
    """Exclude segment contexts, non-money units and conflicting duplicates."""
    groups: dict[tuple, list[dict]] = {}
    url = (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
           f"{filing['accessionNumber'].replace('-', '')}/{filing['primaryDocument']}")
    for _, item in frame.iterrows():
        concept = str(item.get('concept', ''))
        currency = item.get('currency')
        value = item.get('numeric_value')
        if (':' not in concept or (concept.split(':')[0] not in {'us-gaap', 'ifrs-full'} and concept not in REVIEWED_EXTENSIONS)
                or item.get('is_dimensioned', True) != False
                or not isinstance(currency, str) or len(currency) != 3
                or not isinstance(value, (int, float)) or not math.isfinite(value)):
            continue
        start = item.get('period_start') if item.get('period_type') == 'duration' else None
        end = item.get('period_end') if start else item.get('period_instant')
        if not isinstance(end, str):
            continue
        try:
            date.fromisoformat(end)
            if start:
                date.fromisoformat(start)
        except (ValueError, TypeError):
            continue
        context = str(item.get('context_ref', ''))
        fact_id = item.get('fact_id')
        row = {'concept': concept, 'currency': currency, 'val': float(value),
               'end': end, 'filed': filing['filingDate'], 'form': filing['form'],
               'accn': filing['accessionNumber'], '_context_ref': context,
               '_url': url + (f'#{fact_id}' if isinstance(fact_id, str) and fact_id else '')}
        if start:
            row['start'] = start
        groups.setdefault((concept, currency, start, end), []).append(row)
    # Conflicting duplicate values are not resolved by choosing a convenient row.
    return [items[0] for items in groups.values() if len({r['val'] for r in items}) == 1]


def reconcile(submissions: dict, companyfacts: dict, identity: str,
              cache_dir: str = '.cache/filing-xbrl', as_of: date | None = None) -> tuple[dict, tuple[str, ...]]:
    as_of = as_of or date.today()
    merged = deepcopy(companyfacts)
    root = Path(cache_dir)
    root.mkdir(parents=True, exist_ok=True)
    diagnostics = []
    for filing in latest_filings(submissions, as_of):
        path = root / f"{filing['accessionNumber']}-{FALLBACK_VERSION}.json"
        with _PARSE_LOCK:
            rows = None
            try:
                saved = json.loads(path.read_text())
                if saved.get('version') == FALLBACK_VERSION:
                    rows = saved['rows']
            except (OSError, ValueError, KeyError, TypeError):
                pass
            if rows is None:
                os.environ['EDGAR_RATE_LIMIT_PER_SEC'] = '2'
                from edgar import Filing, set_identity
                set_identity(identity)
                obj = Filing(cik=int(submissions['cik']), company=submissions['name'],
                             form=filing['form'], filing_date=filing['filingDate'],
                             accession_no=filing['accessionNumber'])
                instance = obj.xbrl()
                if instance is None:
                    diagnostics.append(f"{filing['form']} {filing['reportDate']}: no XBRL instance available.")
                    continue
                frame = instance.facts.to_dataframe()
                rows = standard_rows(frame, filing, str(submissions['cik']))
                unknown = []
                for _, item in frame.iterrows():
                    concept = str(item.get('concept', ''))
                    label = str(item.get('label', '')).lower()
                    value = item.get('numeric_value')
                    if (concept.split(':')[0] not in {'us-gaap', 'ifrs-full'} and concept not in REVIEWED_EXTENSIONS
                            and item.get('is_dimensioned', True) == False
                            and isinstance(value, (int, float)) and math.isfinite(value) and value > 0
                            and isinstance(item.get('period_instant'), str)
                            and any(word in label for word in ('debt', 'borrowings', 'finance lease'))
                            and not any(word in label for word in ('securities', 'fair value', 'hedge', 'discount', 'issuance cost', 'maturit'))):
                        unknown.append({'end': item['period_instant'], 'concept': concept})
                temp = path.with_suffix(f'.{uuid4().hex}.tmp')
                try:
                    saved = {'version': FALLBACK_VERSION, 'rows': rows, 'unknown_debt': unknown}
                    temp.write_text(json.dumps(saved))
                    os.replace(temp, path)
                finally:
                    temp.unlink(missing_ok=True)
        merged.setdefault('_filing_scope_checked', []).append(filing['accessionNumber'])
        merged.setdefault('_unknown_debt', []).extend(saved.get('unknown_debt', []))
        added = 0
        for item in rows:
            row = dict(item)
            namespace, tag = row.pop('concept').split(':', 1)
            currency = row.pop('currency')
            destination = merged.setdefault('facts', {}).setdefault(namespace, {}).setdefault(tag, {}).setdefault('units', {}).setdefault(currency, [])
            same = [r for r in destination if r.get('accn') == row['accn'] and
                    r.get('start') == row.get('start') and r.get('end') == row['end']]
            if same:
                continue  # Companyfacts remains authoritative; do not overwrite a conflict.
            destination.append(row)
            added += 1
        diagnostics.append(f"Reconciled {filing['form']} {filing['reportDate']}: {added} additional consolidated standard facts; custom and dimensioned concepts remain unverified.")
    return merged, tuple(diagnostics)
