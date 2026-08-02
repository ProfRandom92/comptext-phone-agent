from typer.main import get_command
from typer.testing import CliRunner

from comptext_phone_agent.cli import app

runner = CliRunner()


def _option_names(command_name: str) -> set[str]:
    command = get_command(app).commands[command_name]
    return {
        option
        for parameter in command.params
        for option in (
            *getattr(parameter, "opts", ()),
            *getattr(parameter, "secondary_opts", ()),
        )
    }


def test_chat_help_exposes_safe_and_tui_options():
    result = runner.invoke(app, ["chat", "--help"])
    assert result.exit_code == 0
    assert {"--safe-mode", "--tui", "--provider", "--model", "--base-url"} <= _option_names("chat")


def test_tui_command_exists():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0 and "tui" in result.stdout
    assert "provider-doctor" in result.stdout


def test_tui_help_exposes_provider_options():
    result = runner.invoke(app, ["tui", "--help"])
    assert result.exit_code == 0
    assert {"--provider", "--model", "--base-url"} <= _option_names("tui")
