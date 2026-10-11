"""Synthetic offline contracts only; these fixtures are never production research."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import pandas as pd

from credit_workbench.models import Period
from credit_workbench.normalize import _find, _debt, _difference, normalize, eligibility
from credit_workbench.memo import validate_memo, MemoError, SECTIONS
from credit_workbench.memo_cache import MemoStore
from credit_workbench.research import encode_research, decode_research, memo_identity
from credit_workbench.sec import SECClient, SECError
from credit_workbench.xbrl_fallback import standard_rows
from test_core import snapshot

ASOF = date(2026, 10, 11)
ANNUAL = Period(date(2025, 1, 1), date(2025, 12, 31), 'annual')
INSTANT = Period(None, ANNUAL.end, 'instant')


def fixture(rows):
    data = {'cik': 1, 'facts': {}, '_filing_scope_checked': ['synthetic-2026']}
    for tag, value, start, end, filed, accession in rows:
        ns, tag = tag.split(':', 1) if ':' in tag else ('us-gaap', tag)
        row = {'val': value, 'end': end, 'filed': filed, 'form': '10-K', 'accn': accession}
        if start: row['start'] = start
        data['facts'].setdefault(ns, {}).setdefault(tag, {'units': {'USD': []}})['units']['USD'].append(row)
    return data


def rows_for(tags):
    return [(tag, value, None, '2025-12-31', '2026-02-01', 'synthetic-2026') for tag, value in tags.items()]


class NormalizationTests(unittest.TestCase):
    def test_restated_exact_context_retains_lineage_and_asof(self):
        rows = [('Revenues', 100, '2025-01-01', '2025-12-31', '2026-02-01', 'synthetic-2026'),
                ('Revenues', 110, '2025-01-01', '2025-12-31', '2026-06-01', 'synthetic-restatement'),
                ('Revenues', 999, '2025-01-01', '2025-12-31', '2027-02-01', 'future'),
                ('Revenues', 888, '2025-04-01', '2025-12-31', '2026-08-01', 'wrong-duration')]
        found = _find(fixture(rows), '1', ('Revenues',), 'USD', ANNUAL, ASOF, {'10-K'})
        self.assertEqual(found.value, 110)
        self.assertEqual(found.lineage[0].accession, 'synthetic-2026')
        earlier = _find(fixture(rows), '1', ('Revenues',), 'USD', ANNUAL, date(2026, 3, 1), {'10-K'})
        self.assertEqual(earlier.value, 100)

    def test_debt_does_not_add_total_and_components_or_double_finance_lease(self):
        data = fixture(rows_for({'LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities':100,
                                'LongTermDebtCurrent':20, 'LongTermDebtNoncurrent':80,
                                'ShortTermBorrowings':15,'CommercialPaper':10,'OtherShortTermBorrowings':5,
                                'FinanceLeaseLiability':8}))
        self.assertEqual(_debt(data, '1', 'USD', INSTANT, ASOF, {'10-K'}).value, 115)

    def test_debt_requires_filing_scope_check(self):
        data = fixture(rows_for({'LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities':100}))
        data['_filing_scope_checked'] = []
        self.assertIsNone(_debt(data, '1', 'USD', INSTANT, ASOF, {'10-K'}).value)

    def test_missing_lease_is_not_inferred_zero(self):
        data = fixture(rows_for({'LongTermDebt':100,'CommercialPaper':0}))
        self.assertIsNone(_debt(data, '1', 'USD', INSTANT, ASOF, {'10-K'}).value)

    def test_reviewed_disposal_borrowings_added_once(self):
        data = fixture(rows_for({'LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities':100,'ShortTermBorrowings':0,
          'ko:DisposalGroupIncludingDiscontinuedOperationCurrentMaturitiesOfLongTermDebt':3,
          'ko:DisposalGroupIncludingDiscontinuedOperationLongTermDebt':7}))
        self.assertEqual(_debt(data, '1', 'USD', INSTANT, ASOF, {'10-K'}).value, 110)

    def test_unknown_custom_debt_suppresses_total(self):
        data = fixture(rows_for({'LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities':100}))
        data['_unknown_debt'] = [{'end':'2025-12-31','concept':'synthetic:UnknownBorrowings'}]
        self.assertIsNone(_debt(data, '1', 'USD', INSTANT, ASOF, {'10-K'}).value)

    def test_quarter_difference_requires_matching_concepts(self):
        from dataclasses import replace
        a = snapshot().facts['operating_cash_flow']
        b = replace(a, value=50, sources=(replace(a.sources[0], concept='other'),))
        self.assertIsNone(_difference(a,b,ANNUAL,'operating_cash_flow','Test').value)

    def test_financial_reit_and_missing_sic_are_excluded(self):
        for sic in (6021,6798,None):
            self.assertFalse(eligibility({'sic':sic,'name':'SYNTHETIC'})[0])
        self.assertTrue(eligibility({'sic':3674})[0])

    def test_xbrl_segment_and_conflicting_duplicate_are_excluded(self):
        common = {'concept':'us-gaap:Revenues','currency':'USD','numeric_value':100.,
                  'period_type':'duration','period_start':'2025-01-01','period_end':'2025-12-31',
                  'context_ref':'synthetic','fact_id':'synthetic-id','is_dimensioned':False}
        filing={'accessionNumber':'synthetic','primaryDocument':'synthetic.htm','filingDate':'2026-02-01','form':'10-K'}
        conflict=pd.DataFrame([common,{**common,'numeric_value':101.},{**common,'is_dimensioned':True}])
        self.assertEqual(standard_rows(conflict,filing,'1'),[])
        valid=standard_rows(pd.DataFrame([common,{**common,'is_dimensioned':True}]),filing,'1')
        self.assertEqual(len(valid),1)
        self.assertIn('#synthetic-id',valid[0]['_url'])


class PersistenceTests(unittest.TestCase):
    def test_concurrent_claim_is_unique_and_survives_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'cache.sqlite'); store=MemoStore(local_path=path)
            with ThreadPoolExecutor(max_workers=8) as executor:
                claims=list(executor.map(lambda _:store.claim('fixture'),range(8)))
            self.assertEqual(sum(claims),1)
            memo=self.synthetic_memo();store.finish('fixture',memo)
            self.assertEqual(MemoStore(local_path=path).get('fixture'),memo)
            self.assertFalse(store.claim('fixture'))

    @staticmethod
    def synthetic_memo():
        text=('Synthetic offline narrative solely for validation. The fixture supports arithmetic checks, '
              'but no statement here describes a real company or a live financial result. '
              'Missing information remains explicitly unresolved, and every inference requires review. '
              'This content must never be used in the production dashboard or delivered as actual research. ')
        payload={k:[{'text':text,'evidence_ids':['fixture'],'metric_ids':[]}] for k in SECTIONS}
        return validate_memo(payload,{'fixture'},set(),model='synthetic')

    def test_rate_limit_shared_and_analysis_json_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'cache.sqlite');store=MemoStore(local_path=path)
            self.assertTrue(store.allow_call(1));self.assertFalse(MemoStore(local_path=path).allow_call(1))
            from credit_workbench.normalize import NormalizedResearch
            research=NormalizedResearch('SYNTHETIC','1','TEST','USD',(snapshot(),),None,None,('fixture',),'1231')
            store.save_analysis('fixture',encode_research(research))
            restored=decode_research(MemoStore(local_path=path).get_analysis('fixture'))
            self.assertEqual(dict(restored.annual[0].facts),dict(research.annual[0].facts))
            self.assertEqual(restored.warnings,('fixture',))

    def test_model_change_invalidates_identity(self):
        self.assertNotEqual(memo_identity(snapshot(),(),'synthetic-a'),memo_identity(snapshot(),(),'synthetic-b'))

    def test_invalid_reference_and_unverified_numeric_text_rejected(self):
        memo=self.synthetic_memo()
        from dataclasses import asdict
        payload={k:[asdict(c) for c in v] for k,v in memo.sections.items()}
        for rows in payload.values():
            for row in rows: row['evidence_ids']=list(row['evidence_ids']);row['metric_ids']=[]
        payload['credit_strengths'][0]['text']+=' Revenue grew 25%.'
        with self.assertRaises(MemoError):validate_memo(payload,{'fixture'},set(),model='synthetic')
        payload['credit_strengths'][0]['text']='Unknown reference claim with no valid supporting evidence.'
        payload['credit_strengths'][0]['evidence_ids']=['unknown']
        with self.assertRaises(MemoError):validate_memo(payload,{'fixture'},set(),model='synthetic')


class FailureTests(unittest.TestCase):
    def test_sec_403_retains_stale_valid_data_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            client=SECClient('Synthetic contact test@fixture.invalid',tmp)
            url='https://data.sec.gov/submissions/CIK0000000001.json'
            import hashlib
            path=Path(tmp)/(hashlib.sha256(url.encode()).hexdigest()+'.json')
            path.write_text('{"synthetic":true}')
            with patch('credit_workbench.sec.urlopen',side_effect=HTTPError(url,403,'blocked',{},None)):
                self.assertEqual(client._get(url,0),{'synthetic':True})
            self.assertTrue(client.statuses[url]['stale'])

    def test_sec_error_without_cache_never_substitutes_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            client=SECClient('Synthetic contact test@fixture.invalid',tmp)
            url='https://data.sec.gov/submissions/CIK0000000001.json'
            with patch('credit_workbench.sec.urlopen',side_effect=TimeoutError):
                with self.assertRaises(SECError):client._get(url,0)


class FiscalAssemblyTests(unittest.TestCase):
    @staticmethod
    def fiscal_fixture():
        data={'cik':1,'facts':{'us-gaap':{}},'_filing_scope_checked':['fy','q2']}
        def add(tag,value,start,end,form,accn,filed):
            row={'val':value,'end':end,'form':form,'accn':accn,'filed':filed}
            if start:row['start']=start
            data['facts']['us-gaap'].setdefault(tag,{'units':{'USD':[]}})['units']['USD'].append(row)
        for tag in ('Revenues','OperatingIncomeLoss','NetCashProvidedByUsedInOperatingActivities'):
            add(tag,100,'2025-01-01','2025-12-31','10-K','fy','2026-02-01')
            add(tag,60,'2026-01-01','2026-06-30','10-Q','q2','2026-08-01')
            add(tag,50,'2025-01-01','2025-06-30','10-Q','q2','2026-08-01')
            add(tag,25,'2026-01-01','2026-03-31','10-Q','q1','2026-05-01')
        add('Revenues',35,'2026-04-01','2026-06-30','10-Q','q2','2026-08-01')
        add('OperatingIncomeLoss',35,'2026-04-01','2026-06-30','10-Q','q2','2026-08-01')
        add('CashAndCashEquivalentsAtCarryingValue',12,None,'2026-06-30','10-Q','q2','2026-08-01')
        s={'cik':1,'name':'SYNTHETIC','sic':3571,'fiscalYearEnd':'1231','filings':{'recent':{
           'form':['10-Q','10-Q','10-K','10-Q'],
           'reportDate':['2026-06-30','2026-03-31','2025-12-31','2025-06-30'],
           'filingDate':['2026-08-01','2026-05-01','2026-02-01','2025-08-01']}}}
        return s,data,add

    def test_quarter_cfo_is_ytd_difference_and_ttm_is_not_times_four(self):
        s,d,_=self.fiscal_fixture();n=normalize(s,d,'TEST',ASOF)
        self.assertEqual(n.quarter.facts['operating_cash_flow'].value,35)
        self.assertEqual(n.ttm.facts['operating_cash_flow'].value,110)
        self.assertEqual(n.ttm.facts['cash'].period.end,date(2026,6,30))
        self.assertEqual(n.ttm.facts['cash'].value,12)
        self.assertEqual(len(n.ttm.facts['operating_cash_flow'].sources),3)

    def test_ifrs_exact_currency_is_retained(self):
        s,d,add=self.fiscal_fixture();s['filings']['recent']={'form':['20-F'],'reportDate':['2025-12-31'],'filingDate':['2026-04-01']}
        row={'val':123,'start':'2025-01-01','end':'2025-12-31','form':'20-F','accn':'ifrs','filed':'2026-04-01'}
        d['facts']={'ifrs-full':{'Revenue':{'units':{'TWD':[row]}}}}
        n=normalize(s,d,'TEST',ASOF)
        self.assertEqual(n.currency,'TWD');self.assertEqual(n.annual[0].facts['revenue'].value,123)
        self.assertIsNone(n.annual[0].facts['interest_expense'].value)

    def test_latest_annual_can_supply_q4_from_full_year_minus_nine_months(self):
        s,d,add=self.fiscal_fixture();s['filings']['recent']={'form':['10-K','10-Q'],'reportDate':['2025-12-31','2025-09-30'],'filingDate':['2026-02-01','2025-11-01']}
        for tag in ('Revenues','OperatingIncomeLoss','NetCashProvidedByUsedInOperatingActivities'):
            add(tag,70,'2025-01-01','2025-09-30','10-Q','q3','2025-11-01')
        n=normalize(s,d,'TEST',ASOF)
        self.assertEqual(n.quarter.flow_period.start,date(2025,10,1))
        self.assertEqual(n.quarter.facts['operating_cash_flow'].value,30)


if __name__ == '__main__':
    unittest.main()
