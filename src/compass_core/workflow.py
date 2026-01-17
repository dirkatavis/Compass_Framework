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
