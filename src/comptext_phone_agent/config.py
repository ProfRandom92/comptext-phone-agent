from __future__ import annotations
from pathlib import Path
from typing import Any
import copy, os, re, yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .models import OperatingMode

class CompatModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ScanConfig(CompatModel):
    follow_symlinks: bool = False
    hash_chunk_size: int = 1048576
    old_days: int = 365
    large_file_bytes: int = 524288000
    partial_hash_bytes: int = 1048576

class ApprovalConfig(CompatModel):
    ttl_seconds: int = 900
    require_user_phrase_for_risk3: bool = True

class BackupConfig(CompatModel):
    rclone_binary: str = "rclone"
    timeout_seconds: int = 900
    retries: int = 2
    conflict_strategy: str = "skip"

class TermuxApiConfig(CompatModel):
    timeout_seconds: int = 8
    mock: bool = False

class DashboardConfig(CompatModel):
    host: str = "127.0.0.1"
    port: int = 8765
    session_ttl_seconds: int = 3600

    @field_validator("host")
    @classmethod
    def local_only(cls, value: str) -> str:
        if value not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("dashboard host must be loopback")
        return value

class ExclusionConfig(CompatModel):
    protect_comptext: bool = True
    exact_paths: list[str] = Field(default_factory=list)
    globs: list[str] = Field(default_factory=list)
    regex: list[str] = Field(default_factory=list)
    extensions: list[str] = Field(default_factory=list)
    never_delete: list[str] = Field(default_factory=list)
    never_upload: list[str] = Field(default_factory=list)
    analyze_only: list[str] = Field(default_factory=list)

class AgentConfig(CompatModel):
    provider: str = ""
    model: str = ""
    base_url: str = ""
    timeout_seconds: int = 30


class OrchestratorConfig(CompatModel):
    enabled: bool = True
    router_mode: str = "keyword"
    router_base_url: str = "http://127.0.0.1:8080"
    router_model: str = "MobileActions-270M"
    planner_model: str = "Gemma-4-E2B-it"
    router_token_env: str = "COMPTEXT_BROKER_TOKEN"
    minimum_confidence: float = 0.80
    timeout_seconds: int = 20

    @field_validator("router_mode")
    @classmethod
    def valid_router_mode(cls, value: str) -> str:
        if value not in {"keyword", "broker", "auto"}:
            raise ValueError("router_mode must be keyword, broker, or auto")
        return value

    @field_validator("router_base_url")
    @classmethod
    def loopback_only(cls, value: str) -> str:
        from .orchestrator.router import validate_loopback_router_url

        try:
            return validate_loopback_router_url(value)
        except ValueError as error:
            raise ValueError("router_base_url must be strict loopback HTTP") from error

    @field_validator("router_token_env")
    @classmethod
    def valid_token_environment_name(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}",value):
            raise ValueError("router_token_env must be an environment variable name")
        return value

    @field_validator("minimum_confidence")
    @classmethod
    def confidence_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("minimum_confidence must be between 0 and 1")
        return value

class AppConfig(CompatModel):
    mode: OperatingMode = OperatingMode.ANALYSIS
    data_dir: str = "~/.comptext-phone-agent"
    storage_roots: list[str] = Field(default_factory=lambda: ["~/storage/shared"])
    trash_dir: str = "~/storage/shared/.CompTextTrash"
    scan: ScanConfig = Field(default_factory=ScanConfig)
    approvals: ApprovalConfig = Field(default_factory=ApprovalConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    termux_api: TermuxApiConfig = Field(default_factory=TermuxApiConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    exclusions: ExclusionConfig = Field(default_factory=ExclusionConfig)
    def expanded_data_dir(self) -> Path:
        return Path(os.path.expandvars(os.path.expanduser(self.data_dir))).resolve()
    def expanded_trash_dir(self) -> Path:
        return Path(os.path.expandvars(os.path.expanduser(self.trash_dir))).resolve()

def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        result[key] = _deep_merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else copy.deepcopy(value)
    return result

def default_config_path() -> Path:
    env = os.environ.get("COMPTEXT_PHONE_CONFIG")
    return Path(env).expanduser() if env else Path.home() / ".config/comptext-phone-agent/config.yaml"

def bundled_default_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config/default.yaml"

def load_config(path: Path | None = None) -> AppConfig:
    default = bundled_default_path()
    base = yaml.safe_load(default.read_text(encoding="utf-8")) if default.exists() else {}
    user = path or default_config_path()
    if user.exists():
        base = _deep_merge(base, yaml.safe_load(user.read_text(encoding="utf-8")) or {})
    return AppConfig.model_validate(base)

def write_default_config(path: Path | None = None, overwrite: bool = False) -> Path:
    target = path or default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        return target
    target.write_text(bundled_default_path().read_text(encoding="utf-8"), encoding="utf-8")
    return target
