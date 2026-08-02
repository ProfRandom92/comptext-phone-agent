from comptext_phone_agent.tui.projection import compact_layout,tool_card_from_event

def test_mobile_breakpoint_and_tool_cards():
    assert compact_layout(59) and not compact_layout(60)
    running=tool_card_from_event('tool.started.v1',{'name':'scan'})
    done=tool_card_from_event('tool.completed.v1',{'name':'scan','result':{'total_files':12,'changed':False}})
    assert running.state=='running' and done.summary=='12 Ergebnisse' and not done.changed
