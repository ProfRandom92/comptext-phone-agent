from __future__ import annotations
from ..models import ScanResult
from ..storage.analyzer import StorageAnalyzer
from ..storage.duplicates import DuplicateGroup

def render_markdown(result: ScanResult, duplicates: list[DuplicateGroup] | None = None) -> str:
    analyzer = StorageAnalyzer(result)
    duplicates = duplicates or []
    lines = [
        "# CompText Phone Agent Report", "",
        f"- Scan time: {result.completed_at}",
        f"- Storage root: `{result.root}`",
        f"- Total files: {result.total_files}",
        f"- Total size: {result.total_size} bytes",
        f"- Scan errors: {len(result.errors)}", "",
        "## Largest files", "",
        "| Size | Path | Protected |", "|---:|---|---|",
    ]
    for item in analyzer.largest_files(30):
        lines.append(f"| {item.size} | `{item.relative_path}` | {'yes' if item.exclusion_reason else 'no'} |")
    lines += ["", "## Largest directories", "", "| Size | Directory |", "|---:|---|"]
    for path, size in analyzer.directory_sizes(20):
        lines.append(f"| {size} | `{path}` |")
    lines += ["", "## File types", "", "| Type | Count | Size |", "|---|---:|---:|"]
    for category, data in analyzer.by_type().items():
        lines.append(f"| {category} | {data['count']} | {data['size']} |")
    lines += ["", "## Old files (mtime)", "", "Android access times are often unreliable; this report uses modification time (`mtime`) for age decisions.", ""]
    for item in analyzer.old_files(365, 30):
        lines.append(f"- `{item.relative_path}` — {item.size} bytes")
    lines += ["", "## Possible duplicates", ""]
    for group in duplicates:
        lines.append(f"- {group.kind}: {len(group.files)} files, {group.size} bytes each")
    if not duplicates:
        lines.append("- None verified in this report.")
    lines += ["", "## Exclusions and protected paths", ""]
    protected = [x for x in result.files if x.exclusion_reason]
    for item in protected[:50]:
        lines.append(f"- `{item.relative_path}` — {item.exclusion_reason}")
    lines += ["", "## Recommendations", ""]
    lines += [f"- {text}" for text in analyzer.recommendations()]
    return "\n".join(lines) + "\n"
