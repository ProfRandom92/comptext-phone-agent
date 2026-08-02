from pathlib import Path

from comptext_phone_agent import __version__


def test_runtime_version_matches_release():
    assert __version__ == "0.6.1"


def test_tui_package_import_is_lazy():
    import comptext_phone_agent.tui as tui
    assert "PhoneAgentApp" in tui.__all__


def test_installer_requests_tui_extra():
    text = Path("install-termux.sh").read_text(encoding="utf-8")
    assert ".[test,tui]" in text
