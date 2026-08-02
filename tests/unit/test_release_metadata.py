import importlib
import importlib.util
from importlib import metadata
from pathlib import Path

from comptext_phone_agent import __version__
from comptext_phone_agent.agent import terminal_chat


def test_runtime_version_matches_release():
    assert __version__ == metadata.version("comptext-phone-agent")


def test_application_version_reads_distribution_metadata(monkeypatch):
    spec = importlib.util.find_spec("comptext_phone_agent.version")
    assert spec is not None, "central version module is missing"
    version_module = importlib.import_module("comptext_phone_agent.version")
    monkeypatch.setattr(version_module.metadata, "version", lambda name: "9.8.7")

    assert version_module.application_version() == "9.8.7"


def test_terminal_banner_uses_application_version():
    assert hasattr(terminal_chat, "build_banner"), "shared banner builder is missing"

    banner = terminal_chat.build_banner(
        version="9.8.7",
        provider="ollama-cloud",
        model="gpt-oss:20b",
        session_id="12345678-more",
        root=Path("/storage/shared"),
        mode="SAFE READ-ONLY",
    )

    assert "CompText Phone Agent 9.8.7" in banner
    assert "Ollama Cloud · gpt-oss:20b" in banner
    assert "Session: 12345678" in banner
    assert "0.3" not in banner


def test_tui_package_import_is_lazy():
    import comptext_phone_agent.tui as tui
    assert "PhoneAgentApp" in tui.__all__


def test_installer_requests_tui_extra():
    text = Path("install-termux.sh").read_text(encoding="utf-8")
    assert ".[test,tui]" in text
