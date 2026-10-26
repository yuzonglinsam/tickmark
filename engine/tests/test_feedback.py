"""Offline regressions; modified copies are synthetic and never production output."""
import copy
import json
from pathlib import Path
import unittest
from credit_workbench.answer_checks import calculate, render_answer
from credit_workbench.consistency import deterministic_facts, check_sections, memo_review
ROOT = Path(__file__).resolve().parents[2]

def issuer(t='KO'):
    return json.loads((ROOT / ('engine/tests/fixtures/ko-feedback.json' if t == 'KO' else f'public/data/issuers/{t}.json')).read_text())

class FeedbackTests(unittest.TestCase):
    def setUp(self): self.d = issuer(); self.p = self.d['primary']
    def calc(self, op, keys, **kw):
        return calculate(dict(operation=op, refs=[f'{self.p}/{k}' for k in keys], **kw), self.d)
    def check(self, text):
        return check_sections({'test': [{'text': text}]}, deterministic_facts(self.d))
    def test_sum_and_conversion(self):
        r=self.calc('sum', ['dividends','buybacks'], scale='bn')
        self.assertEqual(r['value'], 9.525e9); self.assertIn('÷ 1,000,000,000',r['formula'])
        self.assertTrue(r['sources']); self.assertEqual(self.calc('value',['debt'],scale='億')['value'],45.492e9)
    def test_difference_ratio_percent(self):
        self.assertEqual(self.calc('difference',['operating_cash_flow','dividends'])['value'],-1.371e9)
        self.assertAlmostEqual(self.calc('ratio',['operating_cash_flow','debt'])['value'],7.408/45.492)
        self.assertIn('%',self.calc('percent',['operating_cash_flow','debt'])['text'])
    def test_free_prose_never_verified_by_coincidence(self):
        for text in ('FY2025 debt was CNY 45.492bn.', 'Debt was USD -45.492bn.',
                     'FY2025 revenue was USD 45.492bn.', 'Debt was 0.', 'Coverage is 1x.'):
            result = render_answer({'answer':text}, self.d)
            self.assertIn('withheld', result['answer'])
            self.assertFalse(result['numbers'])
    def test_model_labels_and_values_are_ignored(self):
        r=render_answer({'answer':'Revenue is high.','calculations':[{'operation':'value','refs':[f'{self.p}/debt'],
            'label':'revenue','value':-1,'scale':'bn'}]},self.d)
        self.assertIn('FY2025/debt',r['answer']); self.assertIn('45.492 USD bn',r['answer'])
    def test_missing_zero_signed_nonfinite(self):
        r=self.d['extended'][self.p]['dividends']
        for v in (None, True, float('nan'), float('inf')):
            r['value']=v
            with self.assertRaises(ValueError): self.calc('sum',['dividends','buybacks'])
        r['value']=0
        self.assertEqual(self.calc('sum',['dividends','buybacks'])['value'],746e6)
        with self.assertRaises(ValueError): self.calc('ratio',['buybacks','dividends'])
        r['value']=-3; self.assertEqual(self.calc('value',['dividends'])['value'],-3)
    def test_wrong_currency_period_units_sources(self):
        for spec in [dict(operation='value',refs=['FY2025/debt'],currency='CNY'),
                     dict(operation='value',refs=['FY2099/debt']),
                     dict(operation='sum',refs=['FY2025/debt','FY2025/current_ratio']),
                     dict(operation='ratio',refs=['FY2024/current_ratio','FY2025/current_ratio']),
                     dict(operation='value',refs=['FY2025/current_ratio'],scale='bn'),
                     dict(operation='sum',refs=['FY2025/debt','FY2025/debt'])]:
            with self.subTest(spec=spec),self.assertRaises(ValueError): calculate(spec,self.d)
        self.d['sources']={}
        with self.assertRaises(ValueError): self.calc('value',['debt'])
    def test_explicit_cross_period_difference(self):
        r=calculate(dict(operation='difference',refs=['FY2025/debt','FY2024/debt']),self.d)
        self.assertIn('FY2024/debt',r['formula'])
    def test_malformed_payload(self):
        for p in ({},[],{'answer':'Hello','calculations':'bad'}):
            with self.assertRaises(ValueError): render_answer(p,self.d)
    def test_ko_original_bilingual_direction(self):
        self.d['peers']['median']['nlev']=2.302
        for t in ('Net leverage sits below the sector median.','淨槓桿低於行業中位數。'):
            self.assertEqual(self.check(t)['conflicts'],1)
        self.assertEqual(self.check('Net leverage is above the sector median.')['conflicts'],0)
    def test_cash_coverage_and_missing(self):
        self.assertEqual(self.check('Operating cash flow covers capex and dividends.')['conflicts'],1)
        self.assertEqual(self.check('Operating cash flow cannot cover capex and dividends.')['conflicts'],0)
        self.assertEqual(self.check('Dividends exceed free cash flow.')['conflicts'],0)
        self.assertEqual(self.check('Free cash flow covers buybacks.')['conflicts'],0)
        self.d['extended'][self.p]['dividends']['value']=None
        self.assertEqual(self.check('Free cash flow covers dividends.')['checked'],0)
    def test_improvement_polarity(self):
        for pid,lev,cr in [('FY2025',2.,1.2),('FY2024',3.,1.)]:
            self.d['metrics'][pid]['net_leverage_adj']['value']=lev
            self.d['metrics'][pid]['current_ratio']['value']=cr
        self.assertEqual(self.check('Net leverage improved. Current ratio improved.')['conflicts'],0)
        self.assertEqual(self.check('Net leverage worsened. Current ratio deteriorated.')['conflicts'],2)
    def test_conditional_negation_qualitative(self):
        for t in ('Net leverage may fall below the sector median.','Net leverage is not below the sector median.',
                  'The business has a durable franchise.'):
            self.assertEqual(self.check(t)['checked'],0)
    def test_missing_nonadjacent_year(self):
        self.d['periods']=[p for p in self.d['periods'] if p['id']!='FY2024']
        self.assertEqual(self.check('Net leverage improved.')['checked'],0)
    def test_real_issuer_types(self):
        for t in ('KO','BA','BABA','AAPL'):
            with self.subTest(t=t):
                r=memo_review(issuer(t)); self.assertIn('financial_end',r['coverage'])
                self.assertIn('not a full agency',r['coverage']['note'])
                if t=='KO':
                    self.assertEqual(r['facts']['net_leverage_adj.peer']['relation'],'above')
                    for lang in ('en','zh'):
                        self.assertTrue(any(c['fact_id']=='net_leverage_adj.peer' and c['status']=='conflict'
                                            for c in r['consistency'][lang]['checks']))

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location('feedback_api', ROOT / 'api/index.py')
        cls.api = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.api)
    def test_cached_review_is_separate_from_citations(self):
        from unittest.mock import patch
        with patch.object(self.api,'covered_doc',return_value=issuer()):
            r=self.api.app.test_client().get('/api/py/review?ticker=KO')
        self.assertEqual(r.status_code,200)
        body=r.get_json(); self.assertIn('citations',body); self.assertGreater(body['consistency']['en']['conflicts'],0)
    def test_bound_ask_and_conflicting_prose(self):
        from unittest.mock import patch
        payload={'answer':'Net leverage sits below the sector median.','evidence':['P999'],
                 'calculations':[{'operation':'sum','refs':['FY2025/dividends','FY2025/buybacks'],'scale':'bn'}]}
        with patch.object(self.api,'deepseek',return_value=payload),patch.object(self.api,'allowed',return_value=True):
            r=self.api.app.test_client().post('/api/py/ask',json={'ticker':'KO','question':'Distributions?'})
        self.assertEqual(r.status_code,200); body=r.get_json()
        self.assertIn('withheld',body['answer']); self.assertIn('9.525 USD bn',body['answer'])
        self.assertTrue(body['calculations'][0]['verified'])
        self.assertNotIn({'passage':'P999'},body['evidence'])
    def test_malformed_ai_answer_fails_closed(self):
        from unittest.mock import patch
        with patch.object(self.api,'deepseek',return_value=[]),patch.object(self.api,'allowed',return_value=True):
            r=self.api.app.test_client().post('/api/py/ask',json={'ticker':'KO','question':'Debt?'})
        self.assertEqual(r.status_code,502)

class CompoundTests(unittest.TestCase):
    def test_distribution_shortfall_and_percentage(self):
        result=render_answer({'answer':'The calculations below show the funding gap.','calculations':[
            {'operation':'sum','refs':['FY2025/dividends','FY2025/buybacks'],'scale':'bn'},
            {'operation':'difference','refs':['FY2025/fcf','calc:0'],'scale':'bn'},
            {'operation':'percent','refs':['calc:0','FY2025/fcf']}]},issuer())
        self.assertEqual(result['calculations'][1]['value'],-4.229e9)
        self.assertAlmostEqual(result['calculations'][2]['value'],9.525/5.296)
        self.assertIn('dividends',result['calculations'][1]['formula'])
    def test_forward_refs_fail_closed(self):
        result=render_answer({'answer':'Calculation.','calculations':[
            {'operation':'value','refs':['calc:0']}]},issuer())
        self.assertFalse(result['calculations'][0]['verified'])
    def test_unbound_chinese_quantity_is_withheld(self):
        r=render_answer({'answer':'債務約為二百二十點八億元。'},issuer())
        self.assertIn('withheld',r['answer'])

class GenerationTests(unittest.TestCase):
    def test_generation_rejects_known_direction_conflict_before_caching(self):
        from unittest.mock import patch, Mock
        from credit_workbench.memo import generate, MemoError, SECTIONS
        from credit_workbench.disclosures import Passage
        from test_core import snapshot
        # Synthetic provider payload; no real network request or production memo.
        payload={s:[{'text':'Net leverage sits below the sector median.','evidence_ids':[], 'metric_ids':[]}] for s in SECTIONS}
        response=Mock(); response.json.return_value={'choices':[{'message':{'content':json.dumps(payload)}}]}
        facts=deterministic_facts(issuer())
        passage=Mock(spec=Passage); passage.evidence_id='synthetic'; passage.heading='Risk factors'; passage.text='Synthetic test'; passage.url='https://example.test';
        with patch('credit_workbench.memo.requests.post',return_value=response) as post, patch('credit_workbench.memo.validate_memo'):
            with self.assertRaises(MemoError):
                generate(snapshot(),(passage,),api_key='synthetic-test-only',context={'deterministic_comparisons':facts})
            self.assertEqual(post.call_count,2)

class BindingRegressionTests(unittest.TestCase):
    def test_ocf_buybacks_uses_buybacks_not_dividends(self):
        d=issuer(); f=deterministic_facts(d)
        result=check_sections({'test':[{'text':'Operating cash flow covers buybacks.'}]},f)
        self.assertEqual(result['checks'][0]['fact_id'],'ocf_buybacks')
        self.assertEqual(result['conflicts'],0)
    def test_free_cash_flow_ratio_name_does_not_bind_to_cfo(self):
        d=issuer(); d['peers']['median']['fcfd']=1.; d['peers']['median']['cfod']=0.
        r=check_sections({'test':[{'text':'Free cash flow to debt is below the sector median.'}]},deterministic_facts(d))
        self.assertEqual(r['checks'][0]['fact_id'],'fcf_to_debt.peer')
        self.assertEqual(r['conflicts'],0)
    def test_chinese_free_cash_flow_ratio_name_does_not_bind_to_cfo(self):
        d=issuer(); d['peers']['median']['fcfd']=1.; d['peers']['median']['cfod']=0.
        for text in ('自由現金流對債務比率低於行業中位數。',
                     '自由现金流对债务比率低于行业中位数。'):
            with self.subTest(text=text):
                r=check_sections({'test':[{'text':text}]},deterministic_facts(d))
                self.assertEqual(r['checks'][0]['fact_id'],'fcf_to_debt.peer')
                self.assertEqual(r['conflicts'],0)
    def test_mixed_direction_targets_remain_unreviewed(self):
        for text in ('Interest coverage is above one though below the sector median.',
                     'The current ratio is below the sector median because liabilities exceed current assets.'):
            with self.subTest(text=text):
                r=check_sections({'test':[{'text':text}]},deterministic_facts(issuer()))
                self.assertEqual(r['checked'],0)
                self.assertEqual(r['conflicts'],0)
                self.assertGreater(r['unreviewed'],0)
    def test_ambiguous_funding_bases_are_unreviewed(self):
        r=check_sections({'test':[{'text':'Operating cash flow and free cash flow cover dividends.'}]},deterministic_facts(issuer()))
        self.assertEqual(r['checked'],0)
