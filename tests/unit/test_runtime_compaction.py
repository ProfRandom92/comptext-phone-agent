from comptext_phone_agent.runtime.compaction import ContextCompactor

def test_compaction_keeps_tail_and_approval():
    messages=[{'role':'user','content':f'm{i}'} for i in range(30)]
    messages[2]={'role':'tool','content':'approval required plan_id=abc','approval_required':True}
    result=ContextCompactor(max_messages=10,tail_messages=4).build_context(messages)
    assert result.compacted and result.messages[0]['content'].startswith('SESSION_SUMMARY:')
    assert any('plan_id=abc' in m.get('content','') for m in result.messages)
    assert [m['content'] for m in result.messages[-4:]]==['m26','m27','m28','m29']
