from types import SimpleNamespace
import httpx
import pytest
from comptext_phone_agent.agent.ollama_client import OllamaChatError, OllamaCloudClient, extract_tool_calls

def test_extract_native_tool_call():
    msg=SimpleNamespace(tool_calls=[SimpleNamespace(function=SimpleNamespace(name='find_duplicates',arguments={'verify':True}))])
    calls=extract_tool_calls(msg)
    assert calls[0].name=='find_duplicates' and calls[0].arguments['verify'] is True

def test_ollama_native_tools_payload():
    def handler(request):
        payload=httpx.Response(200,content=request.content).json()
        assert payload['tools'][0]['function']['name']=='find_duplicates'
        return httpx.Response(200,json={'message':{'content':'','tool_calls':[{'function':{'name':'find_duplicates','arguments':{'verify':True}}}]}})
    client=httpx.Client(transport=httpx.MockTransport(handler))
    response=OllamaCloudClient(api_key='x',host='https://example.test',client=client).chat([{'role':'user','content':'duplicates'}],[{'type':'function','function':{'name':'find_duplicates','parameters':{'type':'object'}}}],stream=False)
    assert extract_tool_calls(response.message)[0].name=='find_duplicates'


@pytest.mark.parametrize(
    ("status_code", "category"),
    [
        (401, "authentication"),
        (403, "authorization"),
        (404, "not_found"),
        (429, "rate_limited"),
    ],
)
def test_ollama_classifies_http_failures_without_switching_model(
    status_code,
    category,
):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status_code, request=request)

    client = OllamaCloudClient(
        model="configured-model",
        api_key="secret",
        host="https://example.test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(OllamaChatError) as raised:
        client.chat([], [], stream=False)

    assert raised.value.category == category
    assert raised.value.status_code == status_code
    assert client.model == "configured-model"
    assert len(requests) == 1


@pytest.mark.parametrize(
    ("error_type", "category"),
    [
        (httpx.ReadTimeout, "timeout"),
        (httpx.ConnectError, "network"),
    ],
)
def test_ollama_classifies_transport_failures(error_type, category):
    def handler(request):
        raise error_type("provider unavailable", request=request)

    client = OllamaCloudClient(
        model="configured-model",
        api_key="secret",
        host="https://example.test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(OllamaChatError) as raised:
        client.chat([], [], stream=False)

    assert raised.value.category == category
