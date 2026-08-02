from __future__ import annotations
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status
from .chat_store import ChatStore
from .ollama_client import OllamaCloudClient, OllamaChatError
from .provider_config import EffectiveProviderConfig, ProviderConfigError, resolve_provider_config
from .tool_registry import ToolRegistry
from ..runtime.compaction import ContextCompactor
from ..runtime.loop import AgentRuntime
from ..runtime.artifacts import ArtifactStore
from ..runtime.ollama_model import OllamaRuntimeModel
from ..runtime.policy import RuntimePolicy
from ..runtime.store import RuntimeStore
from ..version import application_version


def _to_messages(items: list[dict]) -> list[dict]:
    return [{"role": x["role"], "content": x["content"]} for x in items if x["role"] in {"user", "assistant"}]


def build_banner(
    *,
    version: str,
    provider: str,
    model: str,
    session_id: str,
    root: Path,
    mode: str,
) -> str:
    provider_label = "Ollama Cloud" if provider == "ollama-cloud" else provider
    return (
        f"[bold]CompText Phone Agent {version}[/bold]\n"
        f"{provider_label} · {model}\n"
        f"Session: {session_id[:8]}\n"
        f"Root: {root}\n"
        f"Mode: {mode}"
    )


def run_terminal_chat(
    context,
    root: Path,
    new_session: bool = False,
    client=None,
    safe_mode: bool = False,
    provider_config: EffectiveProviderConfig | None = None,
) -> None:
    console = Console()
    effective = provider_config or resolve_provider_config(context.config.agent)
    if effective.provider != "ollama-cloud":
        raise ProviderConfigError(
            "the tool-enabled chat runtime currently requires provider=ollama-cloud; "
            "the local keyword orchestrator remains available without cloud chat"
        )
    model = effective.model
    provider = effective.provider
    store = ChatStore(context.database)
    session = None if new_session else store.latest(provider, model)
    if session is None:
        session = store.create(provider, model)
    registry = ToolRegistry(context, root)
    policy = RuntimePolicy(registry, root, safe_mode=safe_mode)
    artifact_store = ArtifactStore(context.database, root)
    runtime = AgentRuntime(
        store=RuntimeStore(context.database),
        model=OllamaRuntimeModel(
            client or OllamaCloudClient(
                model=model,
                host=effective.base_url,
                timeout=effective.timeout_seconds,
            )
        ),
        registry=registry,
        policy=policy,
        result_projector=artifact_store.project_for_model,
    )
    compactor = ContextCompactor()
    prompt = PromptSession(completer=WordCompleter(["/help", "/clear", "/new", "/exit"], ignore_case=True))
    mode = "SAFE READ-ONLY" if safe_mode else "ANALYSIS + PLAN"
    console.print(Panel(
        build_banner(
            version=application_version(),
            provider=provider,
            model=model,
            session_id=session.id,
            root=root,
            mode=mode,
        ),
        title="Secure Agent Runtime",
    ))
    while True:
        try:
            text = prompt.prompt("Du › ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        if not text:
            continue
        if text in {"/exit", "/quit"}:
            break
        if text == "/help":
            console.print("/clear Verlauf löschen · /new neue Sitzung · /exit beenden")
            continue
        if text == "/clear":
            store.clear(session.id)
            console.print("Verlauf gelöscht.")
            continue
        if text == "/new":
            session = store.create(provider, model)
            console.print(f"Neue Sitzung: {session.id[:8]}")
            continue
        history = _to_messages(store.messages(session.id, limit=60))
        compacted = compactor.build_context(history, store.summary(session.id))
        if compacted.compacted:
            store.set_summary(session.id, compacted.summary)
        store.add(session.id, "user", text)
        try:
            with Status("Agent arbeitet …", console=console, spinner="dots"):
                result = runtime.run(text, session.id, history=compacted.messages)
            answer = result.answer or (
                f"Ein lokaler Plan ist bereit. Freigabe-ID: `{result.approval_id}`"
                if result.state == "waiting_approval" else
                f"Der Lauf wurde beendet: `{result.stop_reason}`"
            )
            store.add(session.id, "assistant", answer)
            console.print(Markdown(answer))
            if result.state == "waiting_approval":
                console.print(Panel(
                    f"Run: {result.run_id[:8]}\nFreigabe: {result.approval_id}\nEs wurde nichts angewendet.",
                    title="Freigabe erforderlich",
                    border_style="yellow",
                ))
        except (OllamaChatError, ValueError, KeyError) as exc:
            console.print(f"[red]Fehler:[/red] {exc}")
