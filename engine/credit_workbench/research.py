"""Versioned identities and JSON-only serialization for persisted public research."""
from dataclasses import asdict
from datetime import date
import hashlib
import json

from .cache_keys import analysis_key
from .memo import PROMPT_VERSION
from .models import Fact, Period, Snapshot, Source
from .normalize import EXTRACTOR_VERSION, NormalizedResearch
from .scoring import METHODOLOGY_VERSION


def financial_identity(submissions: dict, ticker: str) -> str:
    recent = submissions.get('filings', {}).get('recent', {})
    relevant = [(form, recent['accessionNumber'][i], recent['reportDate'][i], recent['filingDate'][i])
                for i, form in enumerate(recent.get('form', []))
                if form in {'10-K','10-K/A','10-Q','10-Q/A','20-F','20-F/A','40-F','40-F/A'}
                and recent['filingDate'][i] <= date.today().isoformat()][:30]
    content = json.dumps([str(submissions['cik']), ticker, relevant, EXTRACTOR_VERSION], sort_keys=True)
    return 'financial:' + hashlib.sha256(content.encode()).hexdigest()


def snapshot_data(snapshot: Snapshot) -> dict:
    return {'cik': snapshot.cik, 'ticker': snapshot.ticker, 'currency': snapshot.currency,
            'flow_period': asdict(snapshot.flow_period), 'as_of': snapshot.as_of,
            'facts': {key: asdict(fact) for key, fact in snapshot.facts.items()}}


def encode_research(research: NormalizedResearch) -> dict:
    data = {'name': research.name, 'cik': research.cik, 'ticker': research.ticker,
            'currency': research.currency, 'warnings': research.warnings,
            'fiscal_year_end': research.fiscal_year_end,
            'annual': [snapshot_data(s) for s in research.annual],
            'quarter': snapshot_data(research.quarter) if research.quarter else None,
            'ttm': snapshot_data(research.ttm) if research.ttm else None}
    return json.loads(json.dumps(data, default=str))


def _snapshot(data: dict) -> Snapshot:
    def period(item):
        return Period(date.fromisoformat(item['start']) if item['start'] else None,
                      date.fromisoformat(item['end']), item['basis'])
    def source(item):
        return Source(**{**item, 'filed_on': date.fromisoformat(item['filed_on'])})
    facts = {key: Fact(**{**item, 'period': period(item['period']),
                         'sources': tuple(source(s) for s in item['sources']),
                         'lineage': tuple(source(s) for s in item.get('lineage', []))})
             for key, item in data['facts'].items()}
    return Snapshot(data['cik'], data['ticker'], data['currency'],
                    period(data['flow_period']), date.fromisoformat(data['as_of']), facts)


def decode_research(data: dict) -> NormalizedResearch:
    return NormalizedResearch(**{**data, 'warnings': tuple(data['warnings']),
                                 'annual': tuple(_snapshot(s) for s in data['annual']),
                                 'quarter': _snapshot(data['quarter']) if data['quarter'] else None,
                                 'ttm': _snapshot(data['ttm']) if data['ttm'] else None})


def memo_identity(snapshot: Snapshot, passages, model: str) -> str:
    normalized = {field: {'value': fact.value, 'status': fact.status,
                          'period': [str(fact.period.start), str(fact.period.end)],
                          'note': fact.note, 'source_ids': [s.evidence_id for s in fact.sources]}
                  for field, fact in snapshot.facts.items()}
    accessions = sorted({s.accession for f in snapshot.facts.values() for s in f.sources}
                        | {p.accession for p in passages})
    return analysis_key(cik=snapshot.cik, accessions=accessions,
                        normalized_data=normalized,
                        disclosure_hash=hashlib.sha256(''.join(p.text for p in passages).encode()).hexdigest(),
                        extractor_version=EXTRACTOR_VERSION, methodology_version=METHODOLOGY_VERSION,
                        prompt_version=PROMPT_VERSION, model=model)
