from pathlib import Path
import json, httpx, pytest
from comptext_phone_agent.agent.providers import MockProvider, OpenAICompatibleProvider, ProviderError, create_provider
from comptext_phone_agent.agent.provider_planner import ProviderBackedPlanner

def test_mock_provider():
    assert 'scan' in MockProvider().complete([])

def test_openai_compatible_provider_uses_typed_http():
    def handler(request):
        assert request.url.path.endswith('/chat/completions')
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"intent":"scan"}'}}]})
    client=httpx.Client(transport=httpx.MockTransport(handler))
    value=OpenAICompatibleProvider('https://example.test/v1','secret','model',client=client).complete([{'role':'user','content':'scan'}])
    assert json.loads(value)['intent']=='scan'

def test_provider_planner_restricts_intents(tmp_path):
    root=tmp_path/'phone'; root.mkdir()
    planner=ProviderBackedPlanner(MockProvider('{"intent":"cleanup_plan","path":"%s"}' % root))
    result=planner.interpret('delete things',root)
    assert result['plan_only'] is True

def test_provider_planner_rejects_untyped_delete(tmp_path):
    root=tmp_path/'phone'; root.mkdir()
    with pytest.raises(ProviderError):
        ProviderBackedPlanner(MockProvider('{"intent":"delete"}')).interpret('delete',root)

def test_provider_factory_requires_secret(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with pytest.raises(ProviderError): create_provider('openai')
    assert create_provider('local')
