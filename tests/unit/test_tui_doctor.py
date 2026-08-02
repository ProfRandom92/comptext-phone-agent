from comptext_phone_agent.tui.doctor import diagnose_tui

def test_tui_doctor_classifies_viewports(tmp_path):
    assert diagnose_tui(columns=40,lines=20,database=tmp_path/'x').layout=='compact'
    assert diagnose_tui(columns=72,lines=32,database=tmp_path/'x').layout=='wide'
    db=tmp_path/'state.sqlite3'; db.touch()
    result=diagnose_tui(columns=120,lines=40,database=db)
    assert result.layout=='desktop' and result.database_exists
