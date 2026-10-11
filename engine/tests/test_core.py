"""Synthetic test inputs only. These values must never appear as issuer research."""
from dataclasses import replace
from datetime import date
import unittest

from credit_workbench.cache_keys import analysis_key
from credit_workbench.metrics import calculate, revenue_growth
from credit_workbench.models import Fact, Period, Snapshot, Source, STOCK_KEYS
from credit_workbench.scoring import score
from credit_workbench.sec import search_index
from credit_workbench.stress import stress

PERIOD = Period(date(2025, 1, 1), date(2025, 12, 31), "annual")
SOURCE = Source("fixture:annual", "fixture://synthetic-only", "fixture-accession", "TEST",
                date(2026, 2, 1), "fixture:synthetic")
BASE = {"revenue": 1000, "operating_income": 150, "depreciation_amortization": 50,
        "operating_cash_flow": 170, "capex": 60, "interest_expense": 20,
        "debt": 400, "cash": 100, "current_assets": 300, "current_liabilities": 150}


def snapshot(period=PERIOD, **overrides):
    values = {**BASE, **overrides}
    facts = {
        key: Fact(value, Period(None, period.end, "instant") if key in STOCK_KEYS else period,
                  "USD", (SOURCE,) if value is not None else (),
                  "reported" if value is not None else "missing",
                  "Synthetic arithmetic fixture" if value is not None else "Not disclosed in fixture")
        for key, value in values.items()
    }
    return Snapshot("1", "TEST", "USD", period, date(2026, 10, 11), facts)


class FinancialArithmeticTests(unittest.TestCase):
    def test_hand_calculated_metrics(self):
        result = calculate(snapshot())
        expected = {"ebitda_proxy": 200, "fcf": 110, "net_debt": 300,
                    "gross_leverage": 2, "net_leverage": 1.5, "interest_coverage": 7.5,
                    "current_ratio": 2, "fcf_to_debt": .275, "operating_margin": .15}
        for key, value in expected.items():
            with self.subTest(metric=key):
                self.assertAlmostEqual(result[key].value, value)
                self.assertEqual(result[key].evidence_ids, ("fixture:annual",))

    def test_missing_da_does_not_turn_ebit_into_ebitda(self):
        result = calculate(snapshot(depreciation_amortization=None))
        self.assertIsNone(result["ebitda_proxy"].value)
        self.assertIsNone(result["gross_leverage"].value)
        self.assertEqual(result["fcf"].value, 110)

    def test_missing_cash_is_not_zero(self):
        self.assertIsNone(calculate(snapshot(cash=None))["net_debt"].value)

    def test_net_cash_is_preserved(self):
        result = calculate(snapshot(cash=500))
        self.assertEqual(result["net_debt"].value, -100)
        self.assertEqual(result["net_leverage"].value, -.5)

    def test_nonpositive_ebitda_has_no_negative_leverage(self):
        for ebit in (-50, -100):
            self.assertEqual(calculate(snapshot(operating_income=ebit))["gross_leverage"].status,
                             "not_meaningful")

    def test_zero_interest_is_not_infinite_coverage(self):
        self.assertIsNone(calculate(snapshot(interest_expense=0))["interest_coverage"].value)

    def test_zero_liabilities_not_infinite_liquidity(self):
        self.assertIsNone(calculate(snapshot(current_liabilities=0))["current_ratio"].value)

    def test_negative_coverage_preserved(self):
        self.assertEqual(calculate(snapshot(operating_income=-100))["interest_coverage"].value, -5)

    def test_quarter_not_annualized(self):
        quarter = Period(date(2025, 10, 1), date(2025, 12, 31), "quarter")
        result = calculate(snapshot(quarter))
        self.assertIsNone(result["gross_leverage"].value)
        self.assertIsNone(result["fcf_to_debt"].value)
        self.assertEqual(result["interest_coverage"].value, 7.5)

    def test_growth_comparable_annual(self):
        prior = snapshot(Period(date(2024, 1, 1), date(2024, 12, 31), "annual"), revenue=800)
        self.assertAlmostEqual(revenue_growth(snapshot(), prior).value, .25)

    def test_growth_rejects_sequential_quarters_as_yoy(self):
        first = snapshot(Period(date(2025, 1, 1), date(2025, 3, 31), "quarter"))
        second = snapshot(Period(date(2025, 4, 1), date(2025, 6, 30), "quarter"))
        self.assertIsNone(revenue_growth(second, first).value)


class ContractTests(unittest.TestCase):
    def test_currency_mismatch_rejected(self):
        base = snapshot()
        with self.assertRaises(ValueError):
            replace(base, facts={**base.facts, "cash": replace(base.facts["cash"], unit="EUR")})

    def test_stale_balance_sheet_rejected(self):
        base = snapshot()
        with self.assertRaises(ValueError):
            replace(base, facts={**base.facts, "debt": replace(base.facts["debt"],
                    period=Period(None, date(2024, 12, 31), "instant"))})

    def test_future_filing_rejected(self):
        with self.assertRaises(ValueError):
            replace(snapshot(), as_of=date(2026, 1, 1))

    def test_source_required(self):
        with self.assertRaises(ValueError):
            Fact(1, PERIOD, "USD")

    def test_missing_explanation_required(self):
        with self.assertRaises(ValueError):
            Fact(None, PERIOD, "USD", status="missing")

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            snapshot(cash=float("nan"))

    def test_signed_capex_rejected_until_validated_normalization(self):
        with self.assertRaises(ValueError):
            snapshot(capex=-60)

    def test_cannot_mutate_snapshot(self):
        with self.assertRaises(TypeError):
            snapshot().facts["cash"] = None


class ScoringAndStressTests(unittest.TestCase):
    def test_score_matches_independent_hand_calculation(self):
        # Leverage 22.5 + coverage 23.2142857 + FCF 13.75 + liquidity 15 + margin 7.5
        self.assertEqual(score(snapshot()).value, 82.0)

    def test_missing_factor_suppresses_point_score(self):
        result = score(snapshot(depreciation_amortization=None))
        self.assertIsNone(result.value)
        self.assertEqual(result.coverage, 70)
        self.assertAlmostEqual(result.upper_bound - result.lower_bound, 30)

    def test_losses_do_not_hide_leverage_risk(self):
        result = score(snapshot(operating_income=-100))
        leverage = next(f for f in result.factors if f.name == "leverage")
        self.assertEqual(leverage.points, 0)

    def test_debt_with_zero_interest_suppresses_score(self):
        self.assertIsNone(score(snapshot(interest_expense=0)).value)

    def test_confirmed_debt_free_case(self):
        result = score(snapshot(debt=0, interest_expense=0))
        self.assertEqual(result.coverage, 100)
        self.assertIsNotNone(result.value)

    def test_downside_reduces_score(self):
        base = snapshot()
        adverse = stress(base, ebit_change=-.3, interest_change=.2, cash_flow_change=-.3)
        self.assertLess(score(adverse).value, score(base).value)
        self.assertEqual(adverse.facts["operating_income"].value, 105)
        self.assertEqual(adverse.facts["interest_expense"].value, 24)
        self.assertEqual(adverse.facts["operating_cash_flow"].value, 119)
        self.assertEqual(base.facts["operating_income"].value, 150)

    def test_deterioration_worsens_negative_ebit_and_cashflow(self):
        adverse = stress(snapshot(operating_income=-100, operating_cash_flow=-100),
                         ebit_change=-.2, cash_flow_change=-.2)
        self.assertEqual(adverse.facts["operating_income"].value, -120)
        self.assertEqual(adverse.facts["operating_cash_flow"].value, -120)

    def test_stress_changes_flows_but_not_cash_or_debt(self):
        base = snapshot()
        changed = stress(base, cash_flow_change=-.5)
        self.assertEqual(changed.facts["cash"], base.facts["cash"])
        self.assertEqual(changed.facts["debt"], base.facts["debt"])

    def test_stress_retains_missing_inputs(self):
        self.assertIsNone(stress(snapshot(interest_expense=None), interest_change=.5)
                          .facts["interest_expense"].value)

    def test_stress_cannot_compound_previous_scenario(self):
        with self.assertRaises(ValueError):
            stress(stress(snapshot(), ebit_change=-.2), ebit_change=-.2)

    def test_zero_scenario_identical(self):
        self.assertEqual(stress(snapshot()), snapshot())

    def test_bad_stress_input_rejected(self):
        for bad in (float("nan"), -1.01, 2.01):
            with self.assertRaises(ValueError):
                stress(snapshot(), ebit_change=bad)


class CacheAndSearchTests(unittest.TestCase):
    def key(self, **changes):
        args = dict(cik="1", accessions=["filing-a", "filing-b"], normalized_data={"revenue": 100},
                    disclosure_hash="sha256:disclosure", extractor_version="v1", methodology_version="v1",
                    prompt_version="v1", model="configured-model")
        return analysis_key(**{**args, **changes})

    def test_order_does_not_change_cache_identity(self):
        self.assertEqual(self.key(), self.key(accessions=["filing-b", "filing-a"]))

    def test_new_filing_and_methodology_invalidate_memo(self):
        for changes in ({"accessions": ["filing-c"]}, {"prompt_version": "v2"},
                        {"methodology_version": "v2"}, {"model": "new-model"},
                        {"normalized_data": {"revenue": 101}}, {"disclosure_hash": "new-text"}):
            with self.subTest(changes=changes):
                self.assertNotEqual(self.key(), self.key(**changes))

    def test_dynamic_search_is_not_a_ticker_allowlist(self):
        rows = {"0": {"ticker": "ZZNEW", "title": "Fresh Industrial Company", "cik_str": 123},
                "1": {"ticker": "FRESH", "title": "Fresh Research Corporation", "cik_str": 456}}
        self.assertEqual(search_index(rows, "ZZNEW")[0]["cik"], "0000000123")
        self.assertEqual(search_index(rows, "Industrial")[0]["ticker"], "ZZNEW")
        self.assertEqual(len(search_index(rows, "fresh")), 2)

    def test_ticker_class_separator(self):
        rows = {"0": {"ticker": "TEST-B", "title": "Fixture Corp", "cik_str": 1}}
        self.assertEqual(search_index(rows, "test.b")[0]["ticker"], "TEST-B")


if __name__ == "__main__":
    unittest.main()
