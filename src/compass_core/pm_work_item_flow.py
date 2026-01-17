"""
PM Work Item Flow (baseline)

High-level orchestration for handling PM work items using protocol-first design.
This baseline implementation is mock-friendly and does not depend on Selenium.
Real adapters can use `Navigator` and page objects to perform UI actions.
"""
from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass

from .workflow import Workflow, WorkflowStep, FlowContext

# Prefer shared PmActions protocol; provide fallback when unavailable
try:
    from .pm_actions import PmActions
except Exception:
    from typing import Protocol, runtime_checkable, Optional

    @runtime_checkable
    class PmActions(Protocol):
        def get_lighthouse_status(self, mva: str) -> Optional[str]: ...
        def has_open_workitem(self, mva: str) -> bool: ...
        def complete_open_workitem(self, mva: str) -> Dict[str, Any]: ...
        def start_new_workitem(self, mva: str) -> Dict[str, Any]: ...
        def has_pm_complaint(self, mva: str) -> bool: ...
        def associate_pm_complaint(self, mva: str) -> Dict[str, Any]: ...
        def navigate_back_home(self) -> None: ...


@dataclass
class _Step(WorkflowStep):
    _name: str
    _fn: Any

    def name(self) -> str:
        return self._name

    def execute(self, context: FlowContext) -> Dict[str, Any]:
        return self._fn(context)


class PmWorkItemFlow(Workflow):
    """Baseline PM work item flow.

    Expected `context.params` keys (for baseline, mock-driven):
      - lighthouse_status: str | None
      - has_open_workitem: bool
      - has_pm_complaint: bool
    """

    def id(self) -> str:
        return "pm_workitem"

    def plan(self, context: FlowContext) -> List[WorkflowStep]:
        return [
            _Step("evaluate_lighthouse", _evaluate_lighthouse),
            _Step("handle_existing_workitem", _handle_existing_workitem),
            _Step("associate_or_skip", _associate_or_skip),
        ]

    def run(self, context: FlowContext) -> Dict[str, Any]:
        # Simple inline orchestration to allow direct use without manager
        results: List[Dict[str, Any]] = []
        for step in self.plan(context):
            res = step.execute(context)
            results.append({"step": step.name(), **res})
            if res.get("status") == "skipped":
                return {"status": "skipped", "reason": res.get("reason"), "trace": results}
            if res.get("status") != "ok":
                return {"status": "failed", "reason": res.get("reason", step.name()), "trace": results}
        return {"status": "ok", "trace": results}


def _evaluate_lighthouse(context: FlowContext) -> Dict[str, Any]:
    status = (context.params or {}).get("lighthouse_status")
    actions: PmActions | None = getattr(context, "actions", None)
    if status is None and actions is not None:
        status = actions.get_lighthouse_status(context.mva)
        (context.params or {}).update({"lighthouse_status": status})
    if status and "rentable" in str(status).lower():
        if context.logger:
            context.logger.info(f"[LIGHTHOUSE] {context.mva} - rentable, skipping")
        return {"status": "skipped", "reason": "lighthouse_rentable"}
    return {"status": "ok"}


def _handle_existing_workitem(context: FlowContext) -> Dict[str, Any]:
    has_open = bool((context.params or {}).get("has_open_workitem"))
    actions: PmActions | None = getattr(context, "actions", None)
    if not has_open and actions is not None:
        has_open = actions.has_open_workitem(context.mva)
        (context.params or {}).update({"has_open_workitem": has_open})
    if has_open:
        # In a real implementation, open and complete the existing PM work item.
        if context.logger:
            context.logger.info(f"[WORKITEM] {context.mva} - completing existing PM work item")
        if actions is not None:
            res = actions.complete_open_workitem(context.mva)
            if res.get("status") != "ok":
                return {"status": "failed", "reason": res.get("reason", "complete_open_pm")}
        # Mark completion to allow short-circuit in subsequent step
        (context.params or {}).update({"completed_open_pm": True})
        return {"status": "ok", "reason": "completed_open_pm"}
    return {"status": "ok"}


def _associate_or_skip(context: FlowContext) -> Dict[str, Any]:
    has_pm = bool((context.params or {}).get("has_pm_complaint"))
    status = (context.params or {}).get("lighthouse_status")
    actions: PmActions | None = getattr(context, "actions", None)
    if bool((context.params or {}).get("completed_open_pm")):
        # Existing work item was completed, conclude flow
        return {"status": "ok", "reason": "completed_open_pm"}
    # Determine complaint presence before starting a new work item
    if not has_pm and actions is not None:
        has_pm = actions.has_pm_complaint(context.mva)
        (context.params or {}).update({"has_pm_complaint": has_pm})
    if has_pm:
        # Only start a new work item when a PM complaint exists
        if actions is not None:
            start_res = actions.start_new_workitem(context.mva)
            if start_res.get("status") != "ok":
                return {"status": "failed", "reason": start_res.get("reason", "start_new_workitem")}
        # In a real implementation, associate complaint and finalize.
        if context.logger:
            context.logger.info(f"[COMPLAINT] {context.mva} - associated PM complaint")
        if actions is not None:
            res = actions.associate_pm_complaint(context.mva)
            if res.get("status") != "ok":
                # Distinguish skipped-no-complaint from failure
                if res.get("status") == "skipped_no_complaint":
                    return {"status": "skipped", "reason": "no_pm_complaint"}
                return {"status": "failed", "reason": res.get("reason", "associate_pm")}
        return {"status": "ok", "reason": "associated"}

    # No PM complaint available; special CDK case when Lighthouse shows PM
    if status and "pm" in str(status).lower():
        if context.logger:
            context.logger.info(f"[WORKITEM] {context.mva} - PM must be closed in CDK")
        if actions is not None:
            actions.navigate_back_home()
        return {"status": "skipped", "reason": "cdk_pm"}

    # Otherwise, skip without CDK note
    if context.logger:
        context.logger.info(f"[WORKITEM] {context.mva} - navigating back after skip")
    if actions is not None:
        actions.navigate_back_home()
    return {"status": "skipped", "reason": "no_pm_complaint"}
