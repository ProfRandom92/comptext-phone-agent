from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json, os, secrets, sys, time
import typer

from . import __version__
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .approvals.engine import ApprovalEngine
from .approvals.policy import PolicyError
from .audit.database import Database
from .audit.logger import AuditLogger
from .backup.planner import BackupPlanner
from .backup.rclone import RcloneClient
from .config import AppConfig, default_config_path, load_config, write_default_config
from .doctor import run_doctor
from .models import ActionPlan, OperatingMode, PlanAction, RiskClass
from .reports.html import render_html
from .reports.json_report import render_json
from .reports.markdown import render_markdown
from .storage.analyzer import StorageAnalyzer
from .storage.cleanup import CleanupPlanner
from .storage.duplicates import DuplicateDetector
from .storage.exclusions import ExclusionEngine
from .storage.scanner import StorageScanner
from .storage.trash import TrashManager
from .storage.hash_cache import HashCache
from .agent.executor import PlanExecutor
from .agent.provider_config import ProviderConfigError, resolve_provider_config
from .termux_api.client import TermuxApiClient, TermuxApiError
from .termux_api.mock import MockTermuxApiClient
from .tui.doctor import diagnose_tui

app = typer.Typer(help="Secure Android storage, file and device assistant for Termux.", no_args_is_help=True)
config_app = typer.Typer(help="Inspect and validate configuration.")
cleanup_app = typer.Typer(help="Create, approve and apply cleanup plans.")
trash_app = typer.Typer(help="Manage the reversible CompText trash.")
backup_app = typer.Typer(help="Plan and run approved rclone backups.")
device_app = typer.Typer(help="Use defensive Termux:API wrappers.")
audit_app = typer.Typer(help="Inspect audit events.")
orchestrator_app = typer.Typer(help="Route local commands through the trusted two-model orchestrator.")
app.add_typer(config_app, name="config")
app.add_typer(cleanup_app, name="cleanup")
app.add_typer(trash_app, name="trash")
app.add_typer(backup_app, name="backup")
app.add_typer(device_app, name="device")
app.add_typer(audit_app, name="audit")
app.add_typer(orchestrator_app, name="orchestrator")

console = Console(stderr=False)
error_console = Console(stderr=True)

@dataclass(slots=True)
class Context:
    config: AppConfig
    data_dir: Path
    database: Database
    audit: AuditLogger
    exclusions: ExclusionEngine
    scanner: StorageScanner
    approvals: ApprovalEngine
    trash: TrashManager
    hash_cache: HashCache
    def device_client(self):
        return MockTermuxApiClient() if self.config.termux_api.mock else TermuxApiClient(self.config.termux_api.timeout_seconds)

def get_context() -> Context:
    config = load_config()
    env_home = os.environ.get("COMPTEXT_PHONE_HOME")
    data_dir = Path(env_home).expanduser().resolve() if env_home else config.expanded_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    database = Database(data_dir / "state.sqlite3")
    audit = AuditLogger(database)
    exclusions = ExclusionEngine(config.exclusions)
    hash_cache = HashCache(database.path)
    scanner = StorageScanner(exclusions, config.scan.follow_symlinks, hash_cache)
    approvals = ApprovalEngine(database, data_dir)
    trash = TrashManager(config.expanded_trash_dir(), database, exclusions)
    return Context(config, data_dir, database, audit, exclusions, scanner, approvals, trash, hash_cache)

def resolve_root(ctx: Context, path: Optional[Path]) -> Path:
    value = path or Path(ctx.config.storage_roots[0]).expanduser()
    return value.resolve()

def print_json(value) -> None:
    console.print_json(json.dumps(value, ensure_ascii=False, default=str))

def file_table(items, title: str = "Files") -> Table:
    table = Table(title=title)
    table.add_column("Size", justify="right")
    table.add_column("Type")
    table.add_column("Path", overflow="fold")
    table.add_column("Protected")
    for item in items:
        table.add_row(str(item.size), item.category, item.relative_path, "yes" if item.exclusion_reason else "no")
    return table

@app.command()
def doctor(path: Optional[Path] = typer.Option(None, "--path"), json_output: bool = typer.Option(False, "--json")) -> None:
    result = run_doctor(path)
    if json_output:
        print_json(result)
        return
    table = Table(title="CompText Phone Agent Doctor")
    table.add_column("Check")
    table.add_column("OK")
    table.add_column("Value", overflow="fold")
    for key, value in result.items():
        if key == "overall_ok":
            continue
        table.add_row(key, "yes" if value["ok"] else "no", str(value["value"]))
    console.print(table)
    raise typer.Exit(0 if result["overall_ok"] else 2)


@app.command("tui-doctor")
def tui_doctor(json_output: bool = typer.Option(False, "--json")) -> None:
    ctx=get_context()
    result=diagnose_tui(database=ctx.database.path).to_dict()
    if json_output:
        print_json(result)
        return
    table=Table(title="CompText TUI Doctor")
    table.add_column("Check")
    table.add_column("Value",overflow="fold")
    for key,value in result.items():
        table.add_row(key,str(value))
    console.print(table)

@app.command("provider-doctor")
def provider_doctor(json_output: bool = typer.Option(False, "--json")) -> None:
    """Show effective provider settings without rendering credentials."""
    try:
        data=resolve_provider_config(load_config().agent).diagnostics()
    except ProviderConfigError as error:
        error_console.print(f"Provider configuration invalid: {error}")
        raise typer.Exit(2)
    if json_output:
        print_json(data)
        return
    table=Table(title="CompText Provider Doctor")
    table.add_column("Setting")
    table.add_column("Value",overflow="fold")
    for key,value in data.items():
        table.add_row(key,json.dumps(value,ensure_ascii=False) if isinstance(value,dict) else str(value))
    console.print(table)

@app.command()
def status(json_output: bool = typer.Option(False, "--json")) -> None:
    ctx = get_context()
    result = {
        "version": __version__, "mode": ctx.config.mode.value, "data_dir": str(ctx.data_dir),
        "database": str(ctx.database.path), "trash_dir": str(ctx.trash.trash_dir),
        "config": str(default_config_path()), "audit_events": len(ctx.audit.list(10000)),
    }
    print_json(result) if json_output else console.print(result)

@config_app.command("show")
def config_show(json_output: bool = typer.Option(False, "--json")) -> None:
    cfg = load_config()
    data = cfg.model_dump(mode="json")
    print_json(data) if json_output else console.print_json(json.dumps(data, ensure_ascii=False))

@config_app.command("validate")
def config_validate() -> None:
    cfg = load_config()
    console.print(f"[green]Configuration valid[/green]: mode={cfg.mode.value}, dashboard={cfg.dashboard.host}:{cfg.dashboard.port}")

@app.command()
def scan(
    path: Optional[Path] = typer.Option(None, "--path"),
    top: int = typer.Option(30, "--top", min=1, max=1000),
    verify_hashes: bool = typer.Option(False, "--hash"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    root = resolve_root(ctx, path)
    started = time.perf_counter()
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True, disable=json_output) as progress:
        progress.add_task("Scanning storage...", total=None)
        result = ctx.scanner.scan(root, with_hash=verify_hashes)
    duration = int((time.perf_counter() - started) * 1000)
    ctx.audit.log(action="storage.scan", tool="scanner", parameters={"hash": verify_hashes}, paths=[str(root)], duration_ms=duration, file_count=result.total_files, byte_count=result.total_size)
    if json_output:
        print_json({"root": result.root, "total_files": result.total_files, "total_size": result.total_size, "errors": result.errors, "top": [x.to_dict() for x in StorageAnalyzer(result).largest_files(top)]})
    else:
        console.print(file_table(StorageAnalyzer(result).largest_files(top), f"Largest {top} files"))
        console.print(f"Files: {result.total_files} | Size: {result.total_size} bytes | Errors: {len(result.errors)}")

def _analyze(kind: str, path: Optional[Path], top: int, json_output: bool) -> None:
    ctx = get_context()
    result = ctx.scanner.scan(resolve_root(ctx, path))
    analyzer = StorageAnalyzer(result)
    if kind == "large":
        values = analyzer.largest_files(top)
        output = [x.to_dict() for x in values]
    elif kind == "old":
        values = analyzer.old_files(ctx.config.scan.old_days, top)
        output = [x.to_dict() for x in values]
    elif kind == "types":
        output = analyzer.by_type()
        values = None
    else:
        raise typer.BadParameter("kind must be large, old or types")
    ctx.audit.log(action=f"storage.analyze.{kind}", tool="analyzer", paths=[result.root], file_count=result.total_files, byte_count=result.total_size)
    if json_output:
        print_json(output)
    elif values is not None:
        console.print(file_table(values, f"Analysis: {kind}"))
    else:
        table = Table(title="File types")
        table.add_column("Type")
        table.add_column("Count", justify="right")
        table.add_column("Bytes", justify="right")
        for name, data in output.items():
            table.add_row(name, str(data["count"]), str(data["size"]))
        console.print(table)

@app.command("analyze")
def analyze_command(
    kind: str = typer.Argument("large"),
    path: Optional[Path] = typer.Option(None, "--path"),
    top: int = typer.Option(30, "--top"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    _analyze(kind, path, top, json_output)

@app.command()
def duplicates(
    path: Optional[Path] = typer.Option(None, "--path"),
    verify: bool = typer.Option(False, "--verify"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    root = resolve_root(ctx, path)
    result = ctx.scanner.scan(root)
    groups = DuplicateDetector(ctx.hash_cache).find(result, verify=verify)
    ctx.audit.log(action="duplicates.scan", tool="duplicates", parameters={"verify": verify}, paths=[str(root)], file_count=sum(len(x.files) for x in groups))
    if json_output:
        print_json([x.to_dict() for x in groups])
        return
    table = Table(title="Duplicate report")
    table.add_column("Kind")
    table.add_column("Size", justify="right")
    table.add_column("Files", overflow="fold")
    table.add_column("Protected")
    for group in groups:
        table.add_row(group.kind, str(group.size), "\n".join(group.files), "\n".join(group.protected) or "no")
    console.print(table)

@cleanup_app.command("plan")
def cleanup_plan(
    path: Optional[Path] = typer.Option(None, "--path"),
    old_days: int = typer.Option(365, "--old-days"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    root = resolve_root(ctx, path)
    result = ctx.scanner.scan(root)
    plan = CleanupPlanner(ctx.exclusions).plan(result, session_id=secrets.token_hex(8), old_days=old_days)
    ctx.approvals.save_plan(plan)
    ctx.audit.log(action="cleanup.plan", tool="planner", paths=[str(root)], plan_id=plan.id, file_count=len(plan.actions), byte_count=plan.total_size)
    print_json(plan.to_dict()) if json_output else console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))

@cleanup_app.command("approve")
def cleanup_approve(
    plan_id: str,
    phrase: str = typer.Option("APPROVE", "--phrase", help="Risk 1/2: APPROVE; risk 3: DELETE PERMANENTLY"),
    ttl: Optional[int] = typer.Option(None, "--ttl"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    plan = ctx.approvals.load_plan(plan_id)
    token, claims = ctx.approvals.approve(plan, phrase, ttl or ctx.config.approvals.ttl_seconds)
    token_dir = ctx.data_dir / "tokens"
    token_dir.mkdir(parents=True, exist_ok=True)
    token_file = token_dir / f"{plan_id}.token"
    token_file.write_text(token, encoding="utf-8")
    os.chmod(token_file, 0o600)
    result = {"approval_id": claims.approval_id, "plan_id": plan_id, "expires_at": claims.expires_at, "token_file": str(token_file)}
    print_json(result) if json_output else console.print(result)

@cleanup_app.command("apply")
def cleanup_apply(
    plan_id: str,
    token: Optional[str] = typer.Option(None, "--token"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    plan = ctx.approvals.load_plan(plan_id)
    if dry_run:
        result = {"dry_run": True, "plan": plan.to_dict(), "changed": False}
        print_json(result) if json_output else console.print(result)
        return
    approval_token = token
    if not approval_token:
        token_file = ctx.data_dir / "tokens" / f"{plan_id}.token"
        if token_file.exists():
            approval_token = token_file.read_text(encoding="utf-8").strip()
    if not approval_token:
        error_console.print("[red]Approval required. Run cleanup approve first.[/red]")
        raise typer.Exit(3)
    root_candidates = [Path(x).expanduser().resolve() for x in ctx.config.storage_roots]
    sources = [Path(action.source).resolve() for action in plan.actions]
    if sources:
        common = Path(os.path.commonpath([str(source) for source in sources])).resolve()
        allowed_root = common.parent if common.is_file() else common
    else:
        allowed_root = root_candidates[0]
    configured_root = next((root for root in root_candidates if all(source == root or root in source.parents for source in sources)), None)
    if configured_root is not None:
        allowed_root = configured_root
    try:
        ids = PlanExecutor(ctx.approvals, ctx.trash, ctx.audit).apply(plan, approval_token, allowed_root)
    except (PolicyError, PermissionError, FileNotFoundError) as error:
        error_console.print(f"[red]{error}[/red]")
        raise typer.Exit(3)
    result = {"changed": True, "trash_item_ids": ids}
    print_json(result) if json_output else console.print(result)

@trash_app.command("list")
def trash_list(json_output: bool = typer.Option(False, "--json")) -> None:
    items = get_context().trash.list()
    print_json(items) if json_output else console.print(items)

@trash_app.command("restore")
def trash_restore(
    item_id: str,
    phrase: str = typer.Option("", "--phrase"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    item = next((x for x in ctx.trash.list() if x["id"] == item_id), None)
    if not item:
        raise typer.BadParameter("active trash item not found")
    action = PlanAction("restore", item["trash_path"], item["original_path"], item["size"], "restore from CompText trash", RiskClass.REVERSIBLE)
    plan = ActionPlan.create(secrets.token_hex(8), OperatingMode.ORGANIZE, [action], "Restore one item from the CompText trash.")
    ctx.approvals.save_plan(plan)
    if phrase != "APPROVE":
        result = {"changed": False, "plan": plan.to_dict(), "required_phrase": "APPROVE"}
        print_json(result) if json_output else console.print(result)
        raise typer.Exit(3)
    token, claims = ctx.approvals.approve(plan, phrase)
    ctx.approvals.verify(token, plan, consume=True)
    path = ctx.trash.restore(item_id, claims.approval_id)
    result = {"restored": str(path), "item_id": item_id, "approval_id": claims.approval_id}
    print_json(result) if json_output else console.print(result)

@trash_app.command("purge")
def trash_purge(
    plan_id: Optional[str] = typer.Option(None, "--plan-id"),
    token: Optional[str] = typer.Option(None, "--token"),
    phrase: str = typer.Option("", "--phrase"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    items = ctx.trash.list()
    if plan_id:
        plan = ctx.approvals.load_plan(plan_id)
    else:
        actions = [PlanAction("purge", x["trash_path"], None, x["size"], "permanent trash purge", RiskClass.IRREVERSIBLE) for x in items]
        plan = ActionPlan.create(secrets.token_hex(8), OperatingMode.CONTROLLED, actions, "Permanently purge active CompText trash items.")
        ctx.approvals.save_plan(plan)
    if not token:
        if phrase == "DELETE PERMANENTLY":
            token, _ = ctx.approvals.approve(plan, phrase)
        else:
            result = {"changed": False, "plan": plan.to_dict(), "plan_id": plan.id, "required_phrase": "DELETE PERMANENTLY"}
            print_json(result) if json_output else console.print(result)
            raise typer.Exit(3)
    claims = ctx.approvals.verify(token, plan, consume=True)
    by_path = {x["trash_path"]: x["id"] for x in items}
    item_ids = []
    for action in plan.actions:
        if action.action != "purge" or action.source not in by_path:
            raise typer.BadParameter("trash contents changed after purge plan creation")
        item_ids.append(by_path[action.source])
    count = ctx.trash.purge(item_ids, claims.approval_id)
    result = {"purged": count, "approval_id": claims.approval_id}
    print_json(result) if json_output else console.print(result)

@backup_app.command("plan")
def backup_plan(
    path: list[Path] = typer.Option(..., "--path"),
    destination: str = typer.Option(..., "--destination"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    plan = BackupPlanner(ctx.exclusions).plan([x.expanduser().resolve() for x in path], destination, session_id=secrets.token_hex(8))
    ctx.approvals.save_plan(plan)
    ctx.audit.log(action="backup.plan", tool="backup", paths=[x.source for x in plan.actions], plan_id=plan.id, file_count=len(plan.actions), byte_count=plan.total_size)
    print_json(plan.to_dict()) if json_output else console.print_json(json.dumps(plan.to_dict(), ensure_ascii=False))

@backup_app.command("approve")
def backup_approve(
    plan_id: str,
    phrase: str = typer.Option("APPROVE", "--phrase"),
    ttl: Optional[int] = typer.Option(None, "--ttl"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    plan = ctx.approvals.load_plan(plan_id)
    token, claims = ctx.approvals.approve(plan, phrase, ttl or ctx.config.approvals.ttl_seconds)
    token_dir = ctx.data_dir / "tokens"
    token_dir.mkdir(parents=True, exist_ok=True)
    token_file = token_dir / f"{plan_id}.token"
    token_file.write_text(token, encoding="utf-8")
    os.chmod(token_file, 0o600)
    result = {"approval_id": claims.approval_id, "plan_id": plan_id, "expires_at": claims.expires_at, "token_file": str(token_file)}
    print_json(result) if json_output else console.print(result)

@backup_app.command("apply")
def backup_apply(
    plan_id: str,
    token: Optional[str] = typer.Option(None, "--token"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx = get_context()
    plan = ctx.approvals.load_plan(plan_id)
    if not dry_run:
        if not token:
            token_file = ctx.data_dir / "tokens" / f"{plan_id}.token"
            if token_file.exists():
                token = token_file.read_text(encoding="utf-8").strip()
        if not token:
            raise typer.BadParameter("approved token is required for external upload")
        ctx.approvals.verify(token, plan, consume=True)
    result = RcloneClient(ctx.config.backup.rclone_binary, ctx.config.backup.timeout_seconds, ctx.exclusions, ctx.config.backup.retries, ctx.config.backup.conflict_strategy).apply(plan, dry_run=dry_run)
    ctx.audit.log(action="backup.dry_run" if dry_run else "backup.apply", tool="rclone", paths=[x.source for x in plan.actions], plan_id=plan.id, result="ok", file_count=len(plan.actions), byte_count=plan.total_size)
    payload = {"dry_run": result.dry_run, "command_preview": result.command_preview, "returncode": result.returncode, "copied": result.copied, "skipped": result.skipped, "verified": result.verified}
    print_json(payload) if json_output else console.print(payload)

def _device_client(ctx: Context, mock: bool):
    return MockTermuxApiClient() if mock or ctx.config.termux_api.mock else TermuxApiClient(ctx.config.termux_api.timeout_seconds)

@device_app.command("battery")
def device_battery(mock: bool = typer.Option(False, "--mock"), json_output: bool = typer.Option(False, "--json")) -> None:
    ctx = get_context()
    try:
        result = _device_client(ctx, mock).battery()
    except TermuxApiError as error:
        error_console.print(f"[red]{error}[/red]")
        raise typer.Exit(4)
    ctx.audit.log(action="device.battery", tool="termux-api", parameters={"mock": mock})
    print_json(result) if json_output else console.print(result)

@device_app.command("wifi")
def device_wifi(mock: bool = typer.Option(False, "--mock"), json_output: bool = typer.Option(False, "--json")) -> None:
    ctx = get_context()
    try:
        result = _device_client(ctx, mock).wifi()
    except TermuxApiError as error:
        error_console.print(f"[red]{error}[/red]")
        raise typer.Exit(4)
    ctx.audit.log(action="device.wifi", tool="termux-api", parameters={"mock": mock})
    print_json(result) if json_output else console.print(result)

@device_app.command("volume")
def device_volume(mock: bool = typer.Option(False, "--mock"), json_output: bool = typer.Option(False, "--json")) -> None:
    ctx = get_context()
    try: result = _device_client(ctx, mock).volume()
    except TermuxApiError as error:
        error_console.print(f"[red]{error}[/red]"); raise typer.Exit(4)
    ctx.audit.log(action="device.volume", tool="termux-api", parameters={"mock": mock})
    print_json(result) if json_output else console.print(result)

@device_app.command("clipboard-get")
def device_clipboard_get(mock: bool = typer.Option(False, "--mock"), json_output: bool = typer.Option(False, "--json")) -> None:
    ctx = get_context()
    try: value = _device_client(ctx, mock).clipboard_get()
    except TermuxApiError as error:
        error_console.print(f"[red]{error}[/red]"); raise typer.Exit(4)
    ctx.audit.log(action="device.clipboard_get", tool="termux-api", parameters={"mock": mock, "content_length": len(value)})
    print_json({"clipboard": value}) if json_output else console.print(value)

@device_app.command("clipboard-set")
def device_clipboard_set(value: str = typer.Argument(...), mock: bool = typer.Option(False, "--mock")) -> None:
    ctx = get_context()
    try: _device_client(ctx, mock).clipboard_set(value)
    except TermuxApiError as error:
        error_console.print(f"[red]{error}[/red]"); raise typer.Exit(4)
    ctx.audit.log(action="device.clipboard_set", tool="termux-api", parameters={"mock": mock, "content_length": len(value)})
    console.print("[green]Clipboard updated.[/green]")

@device_app.command("tts")
def device_tts(value: str = typer.Argument(...), mock: bool = typer.Option(False, "--mock")) -> None:
    ctx = get_context()
    try: _device_client(ctx, mock).tts(value)
    except TermuxApiError as error:
        error_console.print(f"[red]{error}[/red]"); raise typer.Exit(4)
    ctx.audit.log(action="device.tts", tool="termux-api", parameters={"mock": mock, "content_length": len(value)})
    console.print("[green]TTS requested.[/green]")

@device_app.command("vibrate")
def device_vibrate(duration_ms: int = typer.Option(250, "--duration-ms", min=1, max=10000), mock: bool = typer.Option(False, "--mock")) -> None:
    ctx = get_context()
    try: _device_client(ctx, mock).vibrate(duration_ms)
    except TermuxApiError as error:
        error_console.print(f"[red]{error}[/red]"); raise typer.Exit(4)
    ctx.audit.log(action="device.vibrate", tool="termux-api", parameters={"mock": mock, "duration_ms": duration_ms})
    console.print("[green]Vibration requested.[/green]")

@device_app.command("notify")
def device_notify(
    title: str = typer.Option("CompText Phone Agent", "--title"),
    content: str = typer.Option("Task completed", "--content"),
    mock: bool = typer.Option(False, "--mock"),
) -> None:
    ctx = get_context()
    try:
        _device_client(ctx, mock).notify(title, content)
    except TermuxApiError as error:
        error_console.print(f"[red]{error}[/red]")
        raise typer.Exit(4)
    ctx.audit.log(action="device.notify", tool="termux-api", parameters={"title": title, "content_length": len(content), "mock": mock})
    console.print("[green]Notification sent.[/green]")

@app.command()
def report(
    path: Optional[Path] = typer.Option(None, "--path"),
    format: str = typer.Option("markdown", "--format"),
    output: Optional[Path] = typer.Option(None, "--output"),
    verify_duplicates: bool = typer.Option(True, "--verify-duplicates/--no-verify-duplicates"),
) -> None:
    ctx = get_context()
    root = resolve_root(ctx, path)
    result = ctx.scanner.scan(root)
    duplicates = DuplicateDetector(ctx.hash_cache).find(result, verify=verify_duplicates)
    renderers = {"markdown": (render_markdown, ".md"), "json": (render_json, ".json"), "html": (render_html, ".html")}
    if format not in renderers:
        raise typer.BadParameter("format must be markdown, json or html")
    renderer, suffix = renderers[format]
    text = renderer(result, duplicates)
    target = output or ctx.data_dir / "reports" / f"report-{int(time.time())}{suffix}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    ctx.audit.log(action=f"report.{format}", tool="report", paths=[str(root), str(target)], file_count=result.total_files, byte_count=result.total_size)
    console.print(str(target))

@audit_app.callback(invoke_without_command=True)
def audit_list(ctx: typer.Context, limit: int = typer.Option(100, "--limit"), json_output: bool = typer.Option(False, "--json")) -> None:
    if ctx.invoked_subcommand is not None:
        return
    values = get_context().audit.list(limit)
    print_json(values) if json_output else console.print(values)

@audit_app.command("show")
def audit_show(event_id: int, json_output: bool = typer.Option(False, "--json")) -> None:
    value = get_context().audit.get(event_id)
    if not value:
        raise typer.Exit(1)
    print_json(value) if json_output else console.print(value)


def _build_orchestrator(ctx: Context, root: Path):
    from .agent.tool_registry import ToolRegistry
    from .orchestrator.catalog import ActionCatalog
    from .orchestrator.router import KeywordRouter, LoopbackRouterClient
    from .orchestrator.service import OrchestratorService
    from .runtime.policy import RuntimePolicy
    registry=ToolRegistry(ctx,root)
    catalog=ActionCatalog.from_registry(registry)
    cfg=ctx.config.orchestrator
    router=(LoopbackRouterClient(cfg.router_base_url,cfg.timeout_seconds,cfg.router_model)
            if cfg.router_mode == "broker" else KeywordRouter())
    service=OrchestratorService(router=router,registry=registry,catalog=catalog,
        policy=RuntimePolicy(registry,root),min_confidence=cfg.minimum_confidence)
    return service,catalog

@orchestrator_app.command("route")
def orchestrator_route(
    text: str = typer.Argument(...),
    path: Optional[Path] = typer.Option(None, "--path"),
    execute: bool = typer.Option(False, "--execute"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    ctx=get_context(); root=resolve_root(ctx,path); service,_=_build_orchestrator(ctx,root)
    out=service.handle(text,execute=execute)
    payload={
        "status":out.status,
        "decision":{
            "kind":out.decision.kind.value,"action":out.decision.action,
            "arguments":out.decision.arguments,"confidence":out.decision.confidence,
            "reason":out.decision.reason,"source":out.decision.source,
        },
        "result":out.result,"approval_required":out.approval_required,"error":out.error,
    }
    ctx.audit.log(action="orchestrator.route",tool="local-orchestrator",
        parameters={"execute":execute,"status":out.status,"action":out.decision.action})
    print_json(payload) if json_output else console.print(payload)
    if out.status == "rejected": raise typer.Exit(3)

@orchestrator_app.command("doctor")
def orchestrator_doctor(json_output: bool = typer.Option(False, "--json")) -> None:
    from .orchestrator.doctor import diagnose_orchestrator
    ctx=get_context(); _,catalog=_build_orchestrator(ctx,resolve_root(ctx,None))
    data=diagnose_orchestrator(ctx.config.orchestrator,catalog)
    print_json(data) if json_output else console.print(data)


@app.command()
def chat(
    path: Optional[Path] = typer.Option(None, "--path"),
    new_session: bool = typer.Option(False, "--new"),
    safe_mode: bool = typer.Option(False, "--safe-mode"),
    simple: bool = typer.Option(True, "--simple/--tui", help="Use simple prompt_toolkit chat or launch the TUI."),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
) -> None:
    ctx = get_context(); root = resolve_root(ctx, path)
    try:
        effective=resolve_provider_config(ctx.config.agent,cli_provider=provider,cli_model=model,cli_base_url=base_url)
    except ProviderConfigError as error:
        error_console.print(f"Provider configuration invalid: {error}"); raise typer.Exit(2)
    if not simple:
        try:
            from .tui.app import run_tui
        except (ImportError, RuntimeError) as error:
            error_console.print(f"[yellow]{error} Falling back to simple chat.[/yellow]")
        else:
            run_tui(ctx, root, new_session=new_session, safe_mode=safe_mode,provider_config=effective); return
    from .agent.terminal_chat import run_terminal_chat
    run_terminal_chat(ctx, root, new_session=new_session, safe_mode=safe_mode,provider_config=effective)

@app.command()
def tui(
    path: Optional[Path] = typer.Option(None, "--path"),
    new_session: bool = typer.Option(False, "--new"),
    safe_mode: bool = typer.Option(False, "--safe-mode"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
) -> None:
    try:
        from .tui.app import run_tui
    except (ImportError, RuntimeError) as error:
        error_console.print(str(error)); raise typer.Exit(5)
    ctx=get_context()
    try:
        effective=resolve_provider_config(ctx.config.agent,cli_provider=provider,cli_model=model,cli_base_url=base_url)
    except ProviderConfigError as error:
        error_console.print(f"Provider configuration invalid: {error}"); raise typer.Exit(2)
    run_tui(ctx,resolve_root(ctx,path),new_session=new_session,safe_mode=safe_mode,provider_config=effective)

@app.command()
def serve() -> None:
    ctx = get_context()
    try:
        import uvicorn
        from .api.app import create_app
    except ImportError:
        error_console.print("Install dashboard dependencies: pip install -e '.[dashboard]'")
        raise typer.Exit(5)
    dashboard = create_app(ctx)
    console.print(f"Local dashboard: http://{ctx.config.dashboard.host}:{ctx.config.dashboard.port}")
    console.print(f"Session token: {dashboard.state.session_token}")
    uvicorn.run(dashboard, host=ctx.config.dashboard.host, port=ctx.config.dashboard.port)

@app.command()
def demo(path: Path = typer.Option(Path("./mock-phone"), "--path")) -> None:
    from .mocks.filesystem import create_mock_phone
    root = path.resolve()
    if not root.exists():
        create_mock_phone(root)
    ctx = get_context()
    result = ctx.scanner.scan(root)
    duplicates = DuplicateDetector(ctx.hash_cache).find(result, verify=True)
    plan = CleanupPlanner(ctx.exclusions).plan(result, session_id="demo", old_days=365)
    console.print({
        "mock_root": str(root), "files": result.total_files, "bytes": result.total_size,
        "duplicate_groups": len(duplicates), "cleanup_candidates": len(plan.actions),
        "protected_comptext": any("comptext" in x.absolute_path.lower() and x.exclusion_reason for x in result.files),
        "changed": False,
    })

if __name__ == "__main__":
    app()
