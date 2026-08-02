from typer.testing import CliRunner
from comptext_phone_agent.cli import app
runner=CliRunner()

def test_chat_help_exposes_safe_and_tui_options():
    result=runner.invoke(app,['chat','--help'])
    assert result.exit_code==0
    assert '--safe-mode' in result.stdout and '--tui' in result.stdout
    assert '--provider' in result.stdout
    assert '--model' in result.stdout
    assert '--base-url' in result.stdout

def test_tui_command_exists():
    result=runner.invoke(app,['--help'])
    assert result.exit_code==0 and 'tui' in result.stdout
    assert 'provider-doctor' in result.stdout


def test_tui_help_exposes_provider_options():
    result = runner.invoke(app, ['tui', '--help'])
    assert result.exit_code == 0
    assert '--provider' in result.stdout
    assert '--model' in result.stdout
    assert '--base-url' in result.stdout
