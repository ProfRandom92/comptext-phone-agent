import subprocess
import pytest
from comptext_phone_agent.termux_api.client import TermuxApiClient, TermuxApiError
from comptext_phone_agent.termux_api.mock import MockTermuxApiClient

def test_missing_command(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    with pytest.raises(TermuxApiError, match="unavailable"):
        TermuxApiClient().battery()

def test_valid_json(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/bin/mock")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, '{"percentage": 50}', ""))
    assert TermuxApiClient().battery()["percentage"] == 50

def test_invalid_json(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/bin/mock")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, 'not-json', ""))
    with pytest.raises(TermuxApiError, match="invalid JSON"):
        TermuxApiClient().battery()

def test_timeout(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/bin/mock")
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(TermuxApiError, match="timeout"):
        TermuxApiClient(timeout_seconds=1).battery()

def test_mock_client():
    assert MockTermuxApiClient().battery()["percentage"] == 78
    assert MockTermuxApiClient().wifi()["ssid"] == "MockWiFi"
