from pathlib import Path
import pytest, yaml
from pydantic import ValidationError
from comptext_phone_agent.config import AppConfig, load_config

def test_default_configuration_loads():
    config = load_config(Path("/nonexistent/config.yaml"))
    assert config.mode.value == "analysis"
    assert config.dashboard.host == "127.0.0.1"


def test_invalid_dashboard_host_rejected():
    with pytest.raises(ValidationError):
        AppConfig.model_validate({"dashboard": {"host": "0.0.0.0"}})

def test_unknown_key_rejected():
    with pytest.raises(ValidationError):
        AppConfig.model_validate({"unexpected": True})

def test_user_configuration_merges(configured_env):
    config = load_config(configured_env)
    assert config.termux_api.mock is True
