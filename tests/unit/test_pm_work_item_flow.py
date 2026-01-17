import unittest

from compass_core import PmWorkItemFlow
from compass_core.workflow import FlowContext


class _DummyLogger:
    def info(self, *args, **kwargs):
        pass
    def debug(self, *args, **kwargs):
        pass
    def warning(self, *args, **kwargs):
        pass
    def error(self, *args, **kwargs):
        pass


class TestPmWorkItemFlow(unittest.TestCase):
    def setUp(self):
        self.flow = PmWorkItemFlow()
        self.logger = _DummyLogger()

    def run_flow(self, params):
        ctx = FlowContext(mva="MVA123", params=params, logger=self.logger)
        return self.flow.run(ctx)

    def test_skips_when_rentable(self):
        res = self.run_flow({"lighthouse_status": "Rentable"})
        self.assertEqual(res.get("status"), "skipped")
        self.assertEqual(res.get("reason"), "lighthouse_rentable")

    def test_completes_existing_workitem(self):
        res = self.run_flow({"lighthouse_status": "PM", "has_open_workitem": True})
        self.assertEqual(res.get("status"), "ok")
        trace = res.get("trace", [])
        self.assertTrue(any(t.get("reason") == "completed_open_pm" for t in trace))

    def test_associates_pm_complaint(self):
        res = self.run_flow({"has_pm_complaint": True})
        self.assertEqual(res.get("status"), "ok")
        trace = res.get("trace", [])
        self.assertTrue(any(t.get("reason") == "associated" for t in trace))

    def test_skips_cdk_pm_case(self):
        res = self.run_flow({"lighthouse_status": "PM"})
        self.assertEqual(res.get("status"), "skipped")
        self.assertEqual(res.get("reason"), "cdk_pm")

    def test_skips_no_complaint(self):
        res = self.run_flow({})
        self.assertEqual(res.get("status"), "skipped")
        self.assertEqual(res.get("reason"), "no_pm_complaint")


if __name__ == '__main__':
    unittest.main()