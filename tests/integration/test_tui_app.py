import asyncio
from comptext_phone_agent.cli import get_context
from comptext_phone_agent.tui.app import PhoneAgentApp

class FakeClient:
    def chat(self,*args,**kwargs): raise AssertionError('not called')

def test_compact_and_desktop_layouts(configured_env,phone):
    async def scenario():
        app=PhoneAgentApp(get_context(),phone,new_session=True,client=FakeClient())
        async with app.run_test(size=(55,28)) as pilot:
            assert app.query_one('#root').has_class('compact')
            assert not app.query_one('#sidebar').display
            await pilot.resize_terminal(120,40)
            await pilot.pause()
            assert app.query_one('#root').has_class('desktop')
            assert app.query_one('#sidebar').display
    asyncio.run(scenario())
