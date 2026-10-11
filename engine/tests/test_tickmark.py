"""Tests for the Tickmark additions: reported-debt build-up, risk bands, headroom, export.

Synthetic inputs only (values never appear as issuer research).
"""
from datetime import date
import unittest

from credit_workbench.debt import reported_debt
from credit_workbench.models import Period
from credit_workbench.normalize import _find
from credit_workbench.scorecard import (altman_z_double_prime, cashflow_tier, headroom, leverage_tier,
                                        risk_profile)
from credit_workbench.sectors import sector
from test_integration_contracts import ASOF, INSTANT, fixture, rows_for


def scope_for(tags: dict):
    data = fixture(rows_for(tags))
    data.pop("_filing_scope_checked")  # reported-tags mode

    def find(concepts):
        return _find(data, "1", concepts, "USD", INSTANT, ASOF, {"10-K"})
    return reported_debt(find, INSTANT, "USD")


class ReportedDebtTests(unittest.TestCase):
    def test_total_plus_commercial_paper(self):
        fact, scope = scope_for({"LongTermDebt": 100, "CommercialPaper": 15, "OperatingLeaseLiability": 40})
        self.assertEqual(fact.value, 115)
        self.assertEqual(scope.completeness, "full")
        self.assertIn("OperatingLeaseLiability", scope.leases)  # leases reported, never added

    def test_components_are_not_double_counted_with_total(self):
        fact, _ = scope_for({"LongTermDebt": 100, "LongTermDebtCurrent": 20, "LongTermDebtNoncurrent": 80})
        self.assertEqual(fact.value, 100)

    def test_debt_current_already_includes_short_term(self):
        fact, scope = scope_for({"LongTermDebtNoncurrent": 80, "DebtCurrent": 30, "ShortTermBorrowings": 10})
        self.assertEqual(fact.value, 110)
        self.assertEqual(scope.not_tagged, [])

    def test_missing_short_term_is_listed_not_zero_filled(self):
        fact, scope = scope_for({"LongTermDebt": 100})
        self.assertEqual(fact.value, 100)
        self.assertTrue(any("short-term" in x for x in scope.not_tagged))

    def test_noncurrent_only_is_partial(self):
        fact, scope = scope_for({"LongTermDebtNoncurrent": 80})
        self.assertEqual(scope.completeness, "partial")
        self.assertIn("current maturities of long-term debt", scope.not_tagged)

    def test_no_tags_is_missing_with_reason(self):
        fact, scope = scope_for({"Revenues": 5})
        self.assertIsNone(fact.value)
        self.assertIn("may have no funded debt", fact.note)
        self.assertEqual(scope.completeness, "none")


class RiskBandTests(unittest.TestCase):
    def test_band_edges(self):
        self.assertEqual(leverage_tier(149, 100).tier, 0)
        self.assertEqual(leverage_tier(150, 100).tier, 1)
        self.assertEqual(leverage_tier(299, 100).tier, 2)
        self.assertEqual(leverage_tier(500, 100).tier, 5)
        self.assertEqual(cashflow_tier(61, 100).tier, 0)
        self.assertEqual(cashflow_tier(30, 100).tier, 3)  # exactly 30% is not "above" 30%
        self.assertEqual(cashflow_tier(11, 100).tier, 5)

    def test_profile_is_weaker_of_two_and_nets_liquid_assets(self):
        rp = risk_profile(debt=300, ebitda=100, cfo=40, liquid_assets=50)
        # net debt 250 -> 2.5x (Intermediate); CFO/net debt 16% (Aggressive)
        self.assertAlmostEqual(rp["leverage"]["value"], 2.5)
        self.assertEqual(rp["overall"], 4)
        self.assertEqual(rp["label"], "Aggressive")

    def test_net_cash_is_minimal(self):
        rp = risk_profile(debt=100, ebitda=50, cfo=20, liquid_assets=150)
        self.assertEqual(rp["overall"], 0)
        self.assertIn("Net cash", rp["leverage"]["note"])

    def test_negative_ebitda_is_not_meaningful(self):
        rp = risk_profile(debt=100, ebitda=-5, cfo=10, liquid_assets=0)
        self.assertIsNone(rp["overall"])
        self.assertIn("not meaningful", rp["basis"])

    def test_headroom_hand_calculation(self):
        h = headroom(debt=238, ebitda=100, cfo=50)
        # L = 2.38, T = 3.0: EBITDA can fall 1 - 2.38/3 = 20.67%
        self.assertAlmostEqual(h["leverage"]["ebitda_decline_to_downgrade"], 1 - 2.38 / 3)
        self.assertAlmostEqual(h["leverage"]["debt_increase_to_downgrade"], 3 / 2.38 - 1)
        # R = 50/238 = 21.0%, floor 20%: CFO can fall 1 - 0.2/0.21
        self.assertAlmostEqual(h["cashflow"]["cfo_decline_to_downgrade"], 1 - 0.2 / (50 / 238))

    def test_altman_zones(self):
        z = altman_z_double_prime(300, 150, 1000, 400, 120, 500, 500)
        expected = 6.56 * 0.15 + 3.26 * 0.4 + 6.72 * 0.12 + 1.05 * 1.0
        self.assertAlmostEqual(z["value"], expected)
        self.assertEqual(z["zone"], "Safe")
        self.assertIsNone(altman_z_double_prime(None, 1, 1, 1, 1, 1, 1)["value"])


class SectorTests(unittest.TestCase):
    def test_sic_mapping(self):
        self.assertEqual(sector("2080", "KO"), "Consumer Staples")
        self.assertEqual(sector("3674", "XYZ"), "Information Technology")
        self.assertEqual(sector("7370", "GOOGL"), "Communication Services")
        self.assertEqual(sector(None), "Other")


if __name__ == "__main__":
    unittest.main()
