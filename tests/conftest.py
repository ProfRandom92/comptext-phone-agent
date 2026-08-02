from __future__ import annotations
from pathlib import Path
import yaml, pytest
from comptext_phone_agent.mocks.filesystem import create_mock_phone

@pytest.fixture
def phone(tmp_path: Path) -> Path:
    return create_mock_phone(tmp_path / "mock-phone")

@pytest.fixture
def configured_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phone: Path) -> Path:
    source = Path(__file__).resolve().parents[1] / "config/default.yaml"
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    data["data_dir"] = str(tmp_path / "data")
    data["storage_roots"] = [str(phone)]
    data["trash_dir"] = str(phone / ".CompTextTrash")
    data["termux_api"]["mock"] = True
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    monkeypatch.setenv("COMPTEXT_PHONE_CONFIG", str(config))
    monkeypatch.setenv("COMPTEXT_PHONE_HOME", str(tmp_path / "data"))
    return config
