from fastapi.testclient import TestClient
from comptext_phone_agent.api.app import create_app
from comptext_phone_agent.cli import get_context

def client(configured_env):
    app=create_app(get_context())
    return app, TestClient(app)

def test_dashboard_requires_session(configured_env):
    app,c=client(configured_env)
    assert c.get('/api/status').status_code==403
    assert c.get('/api/status',headers={'X-CompText-Token':app.state.session_token}).status_code==200

def test_dashboard_post_requires_csrf(configured_env,phone):
    app,c=client(configured_env); h={'X-CompText-Token':app.state.session_token}
    assert c.post('/api/scan',headers=h,json={'path':str(phone)}).status_code==403
    csrf=c.get('/api/csrf',headers=h).json()['token']
    response=c.post('/api/scan',headers={**h,'X-CompText-CSRF':csrf},json={'path':str(phone)})
    assert response.status_code==200 and response.json()['total_files']>=12

def test_dashboard_rejects_outside_root(configured_env):
    app,c=client(configured_env); h={'X-CompText-Token':app.state.session_token}
    assert c.get('/api/storage?path=/etc',headers=h).status_code==403

def test_dashboard_has_read_views(configured_env):
    app,c=client(configured_env); h={'X-CompText-Token':app.state.session_token}
    for endpoint in ('status','storage','duplicates','plans','approvals','trash','backups','audit','reports'):
        assert c.get('/api/'+endpoint,headers=h).status_code==200

def test_dashboard_has_no_dangerous_get_scan(configured_env):
    app,c=client(configured_env); h={'X-CompText-Token':app.state.session_token}
    assert c.get('/api/scan',headers=h).status_code==405
