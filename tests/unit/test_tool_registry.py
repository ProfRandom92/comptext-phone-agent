import pytest
from comptext_phone_agent.cli import get_context
from comptext_phone_agent.agent.tool_registry import ToolRegistry

def test_registry_only_allows_registered_tools(configured_env,phone):
    registry=ToolRegistry(get_context(),phone)
    names={x['function']['name'] for x in registry.schemas()}
    assert {'scan_storage','find_duplicates','cleanup_plan'} <= names
    with pytest.raises(ValueError): registry.execute('shell',{'command':'rm -rf /'})

def test_cleanup_tool_creates_plan_only(configured_env,phone):
    result=ToolRegistry(get_context(),phone).execute('cleanup_plan',{'old_days':365})
    assert result['changed'] is False and result['approval_required'] is True

def test_cloud_results_redact_absolute_paths_and_wifi(configured_env,phone):
    registry=ToolRegistry(get_context(),phone)
    scan=registry.execute('scan_storage',{'top':2})
    assert all('absolute_path' not in x for x in scan['largest'])
    wifi=registry.execute('device_wifi',{})
    assert 'ip' not in wifi and 'bssid' not in wifi and 'mac_address' not in wifi
