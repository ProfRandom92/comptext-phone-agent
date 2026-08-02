"""Optional Textual user interface.

The package stays importable without the optional ``tui`` extra.  Textual is
loaded only when ``PhoneAgentApp`` or ``run_tui`` is requested.
"""
from __future__ import annotations

from typing import Any

__all__ = ["PhoneAgentApp", "run_tui"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .app import PhoneAgentApp, run_tui
        return {"PhoneAgentApp": PhoneAgentApp, "run_tui": run_tui}[name]
    raise AttributeError(name)
