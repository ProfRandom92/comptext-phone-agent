from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel, Field
from ..paths import normalize_path

class ScanToolInput(BaseModel):
    path: str
    top: int = Field(default=30, ge=1, le=1000)

class CleanupToolInput(BaseModel):
    path: str
    old_days: int = Field(default=365, ge=1, le=10000)

def validate_tool_path(value: str, allowed_roots: list[str]) -> Path:
    return normalize_path(value, allowed_roots=allowed_roots, must_exist=True)
