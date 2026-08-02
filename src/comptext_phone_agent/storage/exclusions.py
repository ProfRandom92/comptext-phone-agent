from __future__ import annotations
from pathlib import Path
import fnmatch, os, re
from ..config import ExclusionConfig

class ExclusionDecision:
    def __init__(self, analyze_only: bool = False, never_delete: bool = False, never_upload: bool = False, reason: str | None = None):
        self.analyze_only = analyze_only
        self.never_delete = never_delete
        self.never_upload = never_upload
        self.reason = reason
    @property
    def protected(self) -> bool:
        return self.analyze_only or self.never_delete

class ExclusionEngine:
    def __init__(self, config: ExclusionConfig):
        self.config = config
        self._regex = [re.compile(pattern) for pattern in config.regex]
    @staticmethod
    def _match(path: str, pattern: str) -> bool:
        normalized = path.replace(os.sep, "/")
        pat = pattern.replace(os.sep, "/")
        return fnmatch.fnmatch(normalized, pat) or fnmatch.fnmatch("/" + normalized.lstrip("/"), pat)
    def evaluate(self, path: str | Path, base_root: str | Path | None = None) -> ExclusionDecision:
        item = Path(path).expanduser().resolve(strict=False)
        text = str(item).replace(os.sep, "/")
        protected_text = text
        if base_root is not None:
            root = Path(base_root).expanduser().resolve(strict=False)
            try:
                protected_text = str(item.relative_to(root)).replace(os.sep, "/")
            except ValueError:
                protected_text = text
        lower = protected_text.lower()
        analyze = delete = upload = False
        reasons: list[str] = []
        if self.config.protect_comptext and "comptext" in lower:
            analyze = delete = upload = True
            reasons.append("protected CompText path")
        if any(item == Path(x).expanduser().resolve(strict=False) for x in self.config.exact_paths):
            analyze = delete = True
            reasons.append("exact protected path")
        if any(self._match(text, p) for p in self.config.globs):
            analyze = delete = True
            reasons.append("global exclusion")
        if any(rx.search(text) for rx in self._regex):
            analyze = delete = True
            reasons.append("regex exclusion")
        if item.suffix.lower() in {x.lower() for x in self.config.extensions}:
            analyze = delete = True
            reasons.append("protected extension")
        if any(self._match(text, p) for p in self.config.never_delete):
            delete = True
            reasons.append("never-delete rule")
        if any(self._match(text, p) for p in self.config.never_upload):
            upload = True
            reasons.append("never-upload rule")
        if any(self._match(text, p) for p in self.config.analyze_only):
            analyze = True
            reasons.append("analyze-only rule")
        return ExclusionDecision(analyze, delete, upload, "; ".join(dict.fromkeys(reasons)) or None)
    def assert_can_modify(self, path: str | Path, base_root: str | Path | None = None) -> None:
        decision = self.evaluate(path, base_root)
        if decision.protected:
            raise PermissionError(decision.reason or "path is protected")
    def assert_can_delete(self, path: str | Path, base_root: str | Path | None = None) -> None:
        decision = self.evaluate(path, base_root)
        if decision.never_delete or decision.analyze_only:
            raise PermissionError(decision.reason or "deletion prohibited")
    def assert_can_upload(self, path: str | Path, base_root: str | Path | None = None) -> None:
        decision = self.evaluate(path, base_root)
        if decision.never_upload:
            raise PermissionError(decision.reason or "upload prohibited")
