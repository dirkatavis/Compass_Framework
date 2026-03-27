"""
Public API marker decorator for Compass Framework.

Applying ``@compass_public`` to a class or method signals that it is part
of the intentional, versioned public contract of the Compass API.  The
decorator is a strict no-op at runtime – it exists solely as a human- and
machine-readable annotation used by the inventory exporter
(``tools/export_inventory.py``) and by code reviewers as an explicit
opt-in signal.

Usage::

    from compass_core.decorators import compass_public

    @compass_public
    class Navigator(Protocol):

        @compass_public
        def navigate_to(self, url: str) -> Dict[str, Any]: ...
"""
from typing import TypeVar

_T = TypeVar("_T")


def compass_public(obj: _T) -> _T:
    """Mark a class or method as part of the public Compass API contract.

    This decorator is a no-op at runtime.  It is used by the inventory
    exporter to identify *Certified Public* API surfaces and by code
    reviewers as an explicit opt-in signal.

    Can be applied to both classes and callable members (methods, functions).
    """
    return obj  # type: ignore[return-value]
