import json
import tempfile
import unittest
from pathlib import Path

from pipeline import memo_repair

FIXTURE = Path(__file__).parent / "fixtures" / "ko-feedback.json"


class MemoRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        (self.data / "issuers").mkdir()
        (self.data / "ai").mkdir()
        doc = json.loads(FIXTURE.read_text())
        (self.data / "issuers" / "KO.json").write_text(json.dumps(doc))
        (self.data / "ai" / "KO.json").write_text(json.dumps(
            {"fingerprint": "x", "passages": doc["passages"], "memo": doc["memo"]}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_conflicted_memo_is_found_in_both_languages(self):
        self.assertEqual(memo_repair.conflicted_tickers(self.data), ["KO"])
        found = memo_repair.conflicts("KO", self.data)
        self.assertGreater(found["en"], 0)
        self.assertGreater(found["zh"], 0)

    def test_merge_replaces_only_memo_and_passages(self):
        issuer = self.data / "issuers" / "KO.json"
        before = json.loads(issuer.read_text())
        new_memo = {**before["memo"], "status": "regenerated"}
        (self.data / "ai" / "KO.json").write_text(json.dumps(
            {"fingerprint": "y", "passages": [], "memo": new_memo}))
        self.assertEqual(memo_repair.merge(["KO", "NOPE"], self.data), ["KO"])
        after = json.loads(issuer.read_text())
        self.assertEqual(after["memo"]["status"], "regenerated")
        self.assertEqual(after["passages"], [])
        for key in before:
            if key not in ("memo", "passages"):
                self.assertEqual(after[key], before[key], key)
        self.assertNotIn("fingerprint", after)


if __name__ == "__main__":
    unittest.main()
