"""Small behavior checks; no new test framework required."""
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1] / "plugin"
sys.path.insert(0, str(PLUGIN))
from learning_store import LearningError, Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "learning.db"
        self.store = Store(self.path)

    def test_ad_hoc_has_no_records_and_cannot_record_hint(self):
        self.assertEqual(self.store.state()["contexts"], [])
        self.assertEqual(self.store.state()["attempts"], [])
        with self.assertRaises(LearningError):
            self.store.hint("unapproved-context")
        self.assertEqual(self.store.state()["contexts"], [])

    def test_hint_and_answer_persist_across_service_instances(self):
        context = self.store.start("Retry lesson", origin="workspace_action")
        self.store.hint(context["id"])
        other = Store(self.path)
        result = other.submit(context["id"], context["run_id"], "A retry can apply the write twice.")
        self.assertEqual(result["attempt"]["assistance"], "targeted_hint")
        self.assertEqual(result["attempt"]["status"], "awaiting_assessment")
        self.assertEqual(Store(self.path).state()["attempts"][0]["answer"], "A retry can apply the write twice.")
        self.assertEqual(self.store.state()["store_id"], other.state()["store_id"])

    def test_retry_is_idempotent_but_intentional_repeat_is_new(self):
        context = self.store.start("Retries", origin="slash_command")
        first = self.store.submit(context["id"], context["run_id"], "same answer")
        retry = self.store.submit(context["id"], context["run_id"], "same answer")
        self.assertTrue(retry["duplicate"])
        self.assertEqual(first["attempt"]["id"], retry["attempt"]["id"])
        with self.assertRaises(LearningError):
            self.store.submit(context["id"], context["run_id"], "changed payload")
        new = self.store.new_run(context["id"])
        self.store.submit(context["id"], new["run_id"], "same answer")
        self.assertEqual(len(self.store.state()["attempts"]), 2)

    def test_leave_revokes_late_writes_without_deleting_saved_answer(self):
        context = self.store.start("Explicit opt-in", origin="workspace_action")
        self.store.submit(context["id"], context["run_id"], "original")
        self.store.leave(context["id"])
        for operation in [lambda: self.store.hint(context["id"]),
                          lambda: self.store.submit(context["id"], context["run_id"], "original"),
                          lambda: self.store.new_run(context["id"])]:
            with self.assertRaises(LearningError):
                operation()
        self.assertEqual(len(Store(self.path).state()["attempts"]), 1)
        self.assertEqual(self.store.state()["contexts"][0]["active"], 0)


if __name__ == "__main__":
    unittest.main()
