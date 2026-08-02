from comptext_phone_agent.tui.models import LayoutMode,layout_mode

def test_responsive_breakpoints():
    assert layout_mode(40) is LayoutMode.COMPACT
    assert layout_mode(70) is LayoutMode.WIDE
    assert layout_mode(100) is LayoutMode.DESKTOP
