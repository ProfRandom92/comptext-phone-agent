import importlib
import importlib.util
import tomllib
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


def test_dashboard_extra_is_intentionally_empty_until_pydantic_v2_migration():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dashboard = data["project"]["optional-dependencies"]["dashboard"]
    assert dashboard == []


def test_license_contains_complete_mit_permission_notice():
    text = Path("LICENSE").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    assert "subject to the following conditions:" in normalized
    assert "this permission notice shall be included in all copies or substantial portions of the Software." in normalized
    assert "IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE" in normalized


def test_active_docs_do_not_claim_repository_is_private_or_future_public():
    active_docs = [Path("README.md"), Path("AGENTS.md"), Path("docs/release/release-contract.md")]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in active_docs).casefold()
    assert "repository remains private" not in combined
    assert "visibility: private" not in combined
    assert "private github push" not in combined
    assert "after the repository becomes public" not in combined
    assert "feature-phone-agent-061-hardening" not in combined
