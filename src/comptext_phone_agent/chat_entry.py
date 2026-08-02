from __future__ import annotations
from pathlib import Path
from .cli import get_context, resolve_root
from .agent.terminal_chat import run_terminal_chat

def main() -> None:
    context=get_context()
    run_terminal_chat(context,resolve_root(context,None))

if __name__ == "__main__": main()
