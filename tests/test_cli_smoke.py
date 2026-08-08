from pathlib import Path
import json
from typer.testing import CliRunner
from comptext_phone_agent.cli import app

runner = CliRunner()

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "CompText" in result.stdout

def test_config_validate(configured_env):
    result = runner.invoke(app, ["config", "validate"])
    assert result.exit_code == 0
    assert "valid" in result.stdout.lower()

def test_scan_json(configured_env, phone):
    result = runner.invoke(app, ["scan", "--path", str(phone), "--top", "3", "--json"])
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["total_files"] >= 12
    assert len(data["top"]) == 3

def test_duplicates_json(configured_env, phone):
    result = runner.invoke(app, ["duplicates", "--path", str(phone), "--verify", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert any(x["kind"] == "same_content_different_name" for x in data)

def test_device_mock_json(configured_env):
    result = runner.invoke(app, ["device", "battery", "--mock", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["percentage"] == 78

def test_cleanup_apply_without_approval(configured_env, phone):
    plan_result = runner.invoke(app, ["cleanup", "plan", "--path", str(phone), "--json"])
    assert plan_result.exit_code == 0
    plan_id = json.loads(plan_result.stdout)["id"]
    result = runner.invoke(app, ["cleanup", "apply", plan_id])
    assert result.exit_code == 3
    assert "Approval required" in result.stderr

def test_report_formats(configured_env, phone, tmp_path):
    for fmt, suffix in [("markdown", ".md"), ("json", ".json"), ("html", ".html")]:
        out = tmp_path / f"report{suffix}"
        result = runner.invoke(app, ["report", "--path", str(phone), "--format", fmt, "--output", str(out)])
        assert result.exit_code == 0, result.stdout
        assert out.exists() and out.stat().st_size > 50

def test_demo(configured_env, phone):
    result = runner.invoke(app, ["demo", "--path", str(phone)])
    assert result.exit_code == 0
    assert "duplicate_groups" in result.stdout

def test_cleanup_approve_apply_multidirectory_and_restore(configured_env, phone):
    plan_result=runner.invoke(app,['cleanup','plan','--path',str(phone),'--json'])
    plan=json.loads(plan_result.stdout)
    assert len({str(Path(x['source']).parent) for x in plan['actions']})>1
    approved=runner.invoke(app,['cleanup','approve',plan['id'],'--phrase','APPROVE','--json'])
    assert approved.exit_code==0
    applied=runner.invoke(app,['cleanup','apply',plan['id'],'--json'])
    assert applied.exit_code==0, applied.stderr
    item_id=json.loads(applied.stdout)['trash_item_ids'][0]
    restored=runner.invoke(app,['trash','restore',item_id,'--phrase','APPROVE','--json'])
    assert restored.exit_code==0 and Path(json.loads(restored.stdout)['restored']).exists()

def test_backup_explicit_approval_command(configured_env, phone):
    planned=runner.invoke(app,['backup','plan','--path',str(phone/'Download/recent.zip'),'--destination','nextcloud:Phone','--json'])
    plan_id=json.loads(planned.stdout)['id']
    approved=runner.invoke(app,['backup','approve',plan_id,'--phrase','APPROVE','--json'])
    assert approved.exit_code==0
    assert Path(json.loads(approved.stdout)['token_file']).exists()

def test_device_extended_mock_commands(configured_env):
    for args in [
        ['device','volume','--mock','--json'],
        ['device','clipboard-get','--mock','--json'],
        ['device','clipboard-set','hello','--mock'],
        ['device','tts','hello','--mock'],
        ['device','vibrate','--duration-ms','25','--mock'],
    ]:
        result=runner.invoke(app,args)
        assert result.exit_code==0, result.stderr

def test_restore_requires_explicit_phrase(configured_env,phone):
    planned=runner.invoke(app,['cleanup','plan','--path',str(phone),'--json'])
    plan_id=json.loads(planned.stdout)['id']
    runner.invoke(app,['cleanup','approve',plan_id,'--phrase','APPROVE','--json'])
    applied=runner.invoke(app,['cleanup','apply',plan_id,'--json'])
    item=json.loads(applied.stdout)['trash_item_ids'][0]
    blocked=runner.invoke(app,['trash','restore',item,'--json'])
    assert blocked.exit_code==3 and json.loads(blocked.stdout)['changed'] is False
    restored=runner.invoke(app,['trash','restore',item,'--phrase','APPROVE','--json'])
    assert restored.exit_code==0


def test_orchestrator_doctor_and_preview_are_local(configured_env, phone, monkeypatch):
    monkeypatch.delenv("COMPTEXT_BROKER_TOKEN", raising=False)
    doctor=runner.invoke(app,["orchestrator","doctor","--json"])
    assert doctor.exit_code==0, doctor.stderr
    diagnostics=json.loads(doctor.stdout)
    assert diagnostics["router_mode"]=="keyword"
    assert diagnostics["broker_token_configured"] is False

    preview=runner.invoke(
        app,
        ["orchestrator","route","Zeige meinen Akku","--path",str(phone),"--json"],
    )
    assert preview.exit_code==0, preview.stderr
    payload=json.loads(preview.stdout)
    assert payload["status"]=="preview"
    assert payload["decision"]["action"]=="device_battery"
    assert payload["result"]["action"]=="device_battery"


def test_orchestrator_mock_execution_requires_execute_flag(configured_env, phone):
    executed=runner.invoke(
        app,
        [
            "orchestrator","route","Zeige meinen Akku","--path",str(phone),
            "--execute","--json",
        ],
    )
    assert executed.exit_code==0, executed.stderr
    payload=json.loads(executed.stdout)
    assert payload["status"]=="completed"
    assert payload["result"]["percentage"]==78


def test_serve_fails_closed_until_dashboard_migration(configured_env):
    result = runner.invoke(app, ["serve"])

    assert result.exit_code == 5
    assert "not shipped in 0.6.1" in result.stderr
    assert "Pydantic 2" in result.stderr
