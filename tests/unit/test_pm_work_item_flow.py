import unittest
from unittest.mock import Mock

from compass_core.pm_work_item_flow import PmWorkItemFlow
from compass_core.workflow import FlowContext


class TestPmWorkItemFlow(unittest.TestCase):
    def setUp(self):
        self.flow = PmWorkItemFlow()
        self.mva = '12345678'

    def test_evaluate_lighthouse_skips_when_rentable(self):
        ctx = FlowContext(mva=self.mva, params={'lighthouse_status': 'Rentable'})
        res = self.flow.run(ctx)
        self.assertEqual(res['status'], 'skipped')
        self.assertIn('lighthouse_rentable', res.get('reason', '') or res.get('trace', [{}])[0].get('reason', ''))

    def test_handle_existing_calls_complete(self):
        mock_actions = Mock()
        mock_actions.has_open_workitem.return_value = True
        mock_actions.complete_open_workitem.return_value = {'status': 'ok'}

        ctx = FlowContext(mva=self.mva, params={}, actions=mock_actions)
        res = self.flow.run(ctx)

        # Flow should succeed and have marked completion
        self.assertEqual(res['status'], 'ok')
        self.assertTrue((ctx.params or {}).get('completed_open_pm'))
        mock_actions.complete_open_workitem.assert_called_once_with(self.mva)

    def test_associate_calls_associate_pm_complaint(self):
        mock_actions = Mock()
        mock_actions.has_open_workitem.return_value = False
        mock_actions.has_pm_complaint.return_value = True
        mock_actions.associate_pm_complaint.return_value = {'status': 'ok'}

        ctx = FlowContext(mva=self.mva, params={}, actions=mock_actions)
        res = self.flow.run(ctx)

        self.assertEqual(res['status'], 'ok')
        mock_actions.associate_pm_complaint.assert_called_once_with(self.mva)


if __name__ == '__main__':
    unittest.main()
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