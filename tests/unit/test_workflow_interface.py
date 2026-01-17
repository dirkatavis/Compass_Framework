import unittest

from compass_core import StandardWorkflowManager
from compass_core.workflow import WorkflowManager, Workflow, FlowContext, WorkflowStep


class DummyStep(WorkflowStep):
    def name(self) -> str:
        return "dummy"
    def execute(self, context: FlowContext):
        return {"status": "ok"}


class DummyWorkflow(Workflow):
    def id(self) -> str:
        return "dummy_workflow"
    def plan(self, context: FlowContext):
        return [DummyStep()]
    def run(self, context: FlowContext):
        return {"status": "ok"}


class TestWorkflowInterface(unittest.TestCase):
    def test_manager_protocol_compliance(self):
        mgr = StandardWorkflowManager()
        self.assertIsInstance(mgr, WorkflowManager)

    def test_manager_runs_workflow(self):
        mgr = StandardWorkflowManager()
        wf = DummyWorkflow()
        ctx = FlowContext(mva="MVA123", params={})
        res = mgr.run(wf, ctx)
        self.assertEqual(res.get("status"), "ok")


if __name__ == '__main__':
    unittest.main()