from comptext_phone_agent.tui.models import StatusView,ToolCardView,TranscriptItem
from comptext_phone_agent.tui.widgets import NeonHeader,ToolCard,MessageBlock

def test_widget_render_text_is_branded_and_safe():
    header=NeonHeader('abc12345',StatusView(model='gpt-oss:20b'))
    assert 'COMPTEXT PHONE AGENT' in header.render().plain
    card=ToolCard(ToolCardView('storage','scan_storage','completed','12 Dateien',progress=100),compact=True)
    assert 'ABGESCHLOSSEN' in card.render().plain and '100%' in card.render().plain
    msg=MessageBlock(TranscriptItem('user','DU','[bold]kein markup[/bold]'))
    assert '[bold]kein markup[/bold]' in msg.render().plain
