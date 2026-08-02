from types import SimpleNamespace
import httpx
from comptext_phone_agent.agent.ollama_client import OllamaCloudClient, extract_tool_calls

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
