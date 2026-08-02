from __future__ import annotations
from jinja2 import Template
from ..models import ScanResult
from ..storage.analyzer import StorageAnalyzer
from ..storage.duplicates import DuplicateGroup

TEMPLATE = Template("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompText Phone Agent Report</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:1rem;background:#f5f5f7;color:#18181b}
.card{background:white;border-radius:14px;padding:1rem;margin:1rem 0;box-shadow:0 1px 5px #0002}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:.5rem;border-bottom:1px solid #ddd}
code{overflow-wrap:anywhere}.badge{padding:.15rem .5rem;border-radius:999px;background:#eee}
</style></head><body>
<h1>CompText Phone Agent Report</h1>
<div class="card"><b>Root:</b> <code>{{ result.root }}</code><br><b>Files:</b> {{ result.total_files }}<br><b>Size:</b> {{ result.total_size }} bytes<br><b>Completed:</b> {{ result.completed_at }}</div>
<div class="card"><h2>Largest files</h2><table><tr><th>Size</th><th>Path</th><th>Protected</th></tr>{% for x in largest %}<tr><td>{{x.size}}</td><td><code>{{x.relative_path}}</code></td><td>{{"yes" if x.exclusion_reason else "no"}}</td></tr>{% endfor %}</table></div>
<div class="card"><h2>File types</h2><table><tr><th>Type</th><th>Count</th><th>Size</th></tr>{% for kind,data in types.items() %}<tr><td>{{kind}}</td><td>{{data.count}}</td><td>{{data.size}}</td></tr>{% endfor %}</table></div>
<div class="card"><h2>Duplicates</h2>{% for d in duplicates %}<p><span class="badge">{{d.kind}}</span> {{d.files|length}} files × {{d.size}} bytes</p>{% else %}<p>None verified.</p>{% endfor %}</div>
<div class="card"><h2>Safety note</h2><p>Age is based on modification time (mtime), not Android access time. This report performs no file modifications.</p></div>
</body></html>""")

def render_html(result: ScanResult, duplicates: list[DuplicateGroup] | None = None) -> str:
    analyzer = StorageAnalyzer(result)
    return TEMPLATE.render(result=result, largest=analyzer.largest_files(30), types=analyzer.by_type(), duplicates=duplicates or [])
