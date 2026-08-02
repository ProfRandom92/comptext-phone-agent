from __future__ import annotations
from dataclasses import asdict, dataclass
import os
from pathlib import Path
import shutil
from .models import layout_mode

@dataclass(frozen=True, slots=True)
class TuiDoctorResult:
    columns: int
    lines: int
    layout: str
    term: str
    color_term: str
    textual_available: bool
    termux: bool
    termux_api_available: bool
    ollama_host_configured: bool
    database_exists: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

def diagnose_tui(*, columns: int | None = None, lines: int | None = None, database: Path | None = None) -> TuiDoctorResult:
    size=shutil.get_terminal_size((55,28))
    cols=max(1, columns or size.columns)
    rows=max(1, lines or size.lines)
    try:
        import textual  # noqa: F401
        textual_available=True
    except ImportError:
        textual_available=False
    prefix=os.environ.get('PREFIX','')
    termux='com.termux' in prefix or 'TERMUX_VERSION' in os.environ
    return TuiDoctorResult(
        columns=cols,
        lines=rows,
        layout=layout_mode(cols).value,
        term=os.environ.get('TERM','unknown'),
        color_term=os.environ.get('COLORTERM','unknown'),
        textual_available=textual_available,
        termux=termux,
        termux_api_available=shutil.which('termux-battery-status') is not None,
        ollama_host_configured=bool(os.environ.get('OLLAMA_HOST')),
        database_exists=bool(database and database.exists()),
    )
