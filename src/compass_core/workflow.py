"""
Workflow protocol definitions and baseline context for flows.

Provides `Workflow`, `WorkflowStep`, and `FlowContext` used by flow
implementations like `PmWorkItemFlow`. Designed to be runtime-checkable
and mock-friendly.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable, Dict, Any, List, Optional


@dataclass
class FlowContext:
    """Shared context passed across workflow steps.

    Attributes:
        mva: Vehicle identifier or unit string.
        params: Mutable bag for step/state parameters.
        logger: Optional logger providing `.info(...)` etc.
        actions: Optional implementation-specific actions object
            (e.g., `PmActions`) used by steps.
    """
    mva: str
    params: Optional[Dict[str, Any]] = None
    logger: Optional[Any] = None  # type: ignore[valid-type]
    actions: Optional[Any] = None  # type: ignore[valid-type]


@runtime_checkable
class WorkflowStep(Protocol):
    """A single step in a workflow plan."""

    def name(self) -> str: ...

    def execute(self, context: FlowContext) -> Dict[str, Any]: ...


@runtime_checkable
class Workflow(Protocol):
    """Protocol for orchestrating multi-step business flows."""

    def id(self) -> str: ...

    def plan(self, context: FlowContext) -> List[WorkflowStep]: ...

    def run(self, context: FlowContext) -> Dict[str, Any]: ...


@runtime_checkable
class WorkflowManager(Protocol):
    """Protocol for managing workflow execution."""

    def run(self, workflow: Workflow, context: FlowContext) -> Dict[str, Any]: ...


class StandardWorkflowManager:
    """Default implementation that delegates to the workflow's `run`.

    If the workflow raises NotImplementedError for `run`, it will fallback
    to executing each planned step sequentially and aggregate results.
    """

    def run(self, workflow: Workflow, context: FlowContext) -> Dict[str, Any]:
        # Prefer the workflow's own run implementation
        try:
            return workflow.run(context)
        except NotImplementedError:
            # Fallback: execute the plan step-by-step
            results: List[Dict[str, Any]] = []
            status: str = "ok"
            steps = workflow.plan(context)
            for step in steps:
                res = step.execute(context)
                results.append({"step": step.name(), "result": res})
                step_status = res.get("status")
                if step_status and step_status not in ("ok", "success", "passed"):
                    status = step_status
            return {"status": status, "results": results}
