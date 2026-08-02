from comptext_phone_agent.tui.models import ToolCardView
from comptext_phone_agent.tui.widgets import ToolCard, CommandPalettePanel

def test_tool_card_can_be_updated_in_place():
    widget=ToolCard(ToolCardView('generic','scan','running','läuft',progress=10,call_id='a'))
    widget.update_card(ToolCardView('storage','scan','completed','12 Dateien',progress=100,call_id='a'))
    assert widget.card.state=='completed' and widget.card.call_id=='a'

def test_command_palette_lists_safe_actions():
    text=CommandPalettePanel().render().plain
    assert 'Speicher analysieren' in text and 'Aufräumplan' in text
