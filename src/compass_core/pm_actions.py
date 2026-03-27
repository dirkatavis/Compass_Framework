"""
Protocol for PM flow actions

Abstracts concrete UI interactions needed by PM flow.
"""
from __future__ import annotations
from .decorators import compass_public
from typing import Protocol, runtime_checkable, Dict, Any, Optional


@compass_public
@runtime_checkable
class PmActions(Protocol):
    @compass_public
    def get_lighthouse_status(self, mva: str) -> Optional[str]: ...
    @compass_public
    def has_open_workitem(self, mva: str) -> bool: ...
    @compass_public
    def complete_open_workitem(self, mva: str) -> Dict[str, Any]: ...
    @compass_public
    def has_pm_complaint(self, mva: str) -> bool: ...
    @compass_public
    def associate_pm_complaint(self, mva: str) -> Dict[str, Any]: ...
    @compass_public
    def navigate_back_home(self) -> None: ...
    @compass_public
    def find_workitem(self, mva: str, damage_type: str, sub_damage_type: str, correction_action: str) -> Optional[Dict[str, Any]]: ...
    @compass_public
    def create_workitem(self, mva: str, damage_type: str, sub_damage_type: str, correction_action: str) -> Dict[str, Any]: ...
