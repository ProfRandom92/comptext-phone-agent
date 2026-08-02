from comptext_phone_agent.audit.database import Database
from comptext_phone_agent.agent.chat_store import ChatStore

def test_chat_session_persists_and_resumes(tmp_path):
    store=ChatStore(Database(tmp_path/'state.db')); s=store.create('ollama-cloud','model')
    store.add(s.id,'user','hello'); store.add(s.id,'assistant','hi')
    assert store.latest('ollama-cloud','model').id==s.id
    assert [x['content'] for x in store.messages(s.id)]==['hello','hi']
    store.clear(s.id); assert store.messages(s.id)==[]
