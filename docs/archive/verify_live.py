"""Explicit real SEC/DeepSeek acceptance run. Never runs as part of offline tests."""
from __future__ import annotations
import argparse
from dataclasses import asdict
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import time
from uuid import uuid4
from dotenv import load_dotenv
from credit_workbench.disclosures import annual_document, extract_passages
from credit_workbench.memo import generate
from credit_workbench.memo_cache import MemoStore
from credit_workbench.metrics import calculate
from credit_workbench.normalize import normalize
from credit_workbench.pdf_export import render_pdf
from credit_workbench.research import encode_research, memo_identity, financial_identity
from credit_workbench.sec import SECClient
from credit_workbench.xbrl_fallback import reconcile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ticker')
    parser.add_argument('--ai', action='store_true', help='Explicitly permit a paid DeepSeek call on cache miss')
    parser.add_argument('--cold', action='store_true', help='Use a separate empty raw-data cache')
    args = parser.parse_args()
    load_dotenv('.env')
    root = Path('artifacts') / args.ticker.upper()
    root.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    cold_root = root / ('cold-' + uuid4().hex) if args.cold else None
    client = SECClient(os.environ['SEC_USER_AGENT'], cold_root / 'sec' if args.cold else '.cache/sec')
    matches = client.search(args.ticker)
    row = next((r for r in matches if r['ticker'].upper() == args.ticker.upper()), None)
    if row is None:
        raise ValueError('No exact ticker match; resolve issuer ambiguity in the dashboard')
    submissions = client.submissions(row['cik'])
    facts = client.company_facts(row['cik'])
    facts, diagnostics = reconcile(submissions, facts, client.identity,
                                   str(cold_root / 'xbrl') if args.cold else '.cache/filing-xbrl')
    research = normalize(submissions, facts, row['ticker'], datetime.now(timezone.utc).date())
    financial_seconds = time.monotonic() - start
    snapshot = research.annual[0]
    doc = annual_document(submissions)
    passages = extract_passages(client.filing_html(doc[0]), *doc) if doc else ()
    model = os.getenv('DEEPSEEK_MODEL') or 'deepseek-flash'
    key = memo_identity(snapshot, passages, model)
    store = MemoStore(os.getenv('CACHE_DATABASE_URL'))
    store.save_analysis(key, encode_research(research))
    store.save_analysis(financial_identity(submissions, research.ticker), encode_research(research))
    memo = store.get(key)
    hit = memo is not None
    ai_seconds = None
    if not memo and args.ai:
        if not store.claim(key):
            memo = store.wait(key)
        elif not store.allow_call():
            store.release(key)
            raise RuntimeError('Shared generation limit reached')
        else:
            try:
                ai_start = time.monotonic()
                memo = generate(snapshot, passages, api_key=os.getenv('DEEPSEEK_API_KEY', ''), model=model)
                ai_seconds = time.monotonic() - ai_start
                store.finish(key, memo)
            except Exception:
                store.release(key)
                raise
    evidence = {'ticker': research.ticker, 'cik': research.cik, 'checked_at': datetime.now(timezone.utc).isoformat(),
                'financial_seconds': financial_seconds, 'ai_seconds': ai_seconds, 'memo_cache_hit': hit, 'cold_raw_cache':args.cold,
                'identity': key, 'diagnostics': diagnostics, 'research': encode_research(research),
                'metrics': {k: asdict(v) for k,v in calculate(snapshot).items()},
                'passages': [asdict(p) for p in passages], 'memo': asdict(memo) if memo else None}
    (root / 'acceptance.json').write_text(json.dumps(evidence, indent=2))
    if memo:
        (root / f'{research.ticker.lower()}-credit-memo.pdf').write_bytes(render_pdf(snapshot, memo, passages, research.name))
    print(json.dumps({k: evidence[k] for k in ('ticker','checked_at','financial_seconds','ai_seconds','memo_cache_hit','identity')}))
    print('Periods:', ', '.join(str(s.flow_period.end) for s in research.annual),
          'quarter:', research.quarter.flow_period.end if research.quarter else None)
    print('Disclosures:', [p.heading for p in passages], 'PDF:', bool(memo))


if __name__ == '__main__':
    main()
