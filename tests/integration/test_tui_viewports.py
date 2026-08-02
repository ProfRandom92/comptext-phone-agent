import asyncio
from comptext_phone_agent.cli import get_context
from comptext_phone_agent.tui.app import PhoneAgentApp

class FakeClient:
    def chat(self,*args,**kwargs): raise AssertionError('not called')

def test_supported_viewports(configured_env,phone):
    async def scenario():
        app=PhoneAgentApp(get_context(),phone,new_session=True,client=FakeClient())
        async with app.run_test(size=(40,20)) as pilot:
            for width,height,expected in ((40,20,'compact'),(55,28,'compact'),(72,32,'wide'),(90,36,'desktop'),(120,40,'desktop')):
                await pilot.resize_terminal(width,height); await pilot.pause()
                assert app.query_one('#root').has_class(expected)
            app.action_toggle_palette()
            assert app.query_one('#command-palette').has_class('visible')
    asyncio.run(scenario())
