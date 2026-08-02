from __future__ import annotations
from pathlib import Path
from typing import Any
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, VerticalScroll
    from textual.widgets import Input, Static
    from textual import events, work
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Textual ist nicht installiert. Installiere: pip install -e '.[tui]'") from exc
from ..agent.chat_store import ChatStore
from ..agent.ollama_client import OllamaCloudClient
from ..agent.provider_config import EffectiveProviderConfig, ProviderConfigError, resolve_provider_config
from ..agent.tool_registry import ToolRegistry
from ..runtime.loop import AgentRuntime
from ..runtime.artifacts import ArtifactStore
from ..runtime.ollama_model import OllamaRuntimeModel
from ..runtime.policy import RuntimePolicy
from ..runtime.signals import SignalType
from ..runtime.store import RuntimeStore
from .card_factory import card_from_event
from .models import LayoutMode, StatusView, TranscriptItem, layout_mode
from .widgets import CommandPalettePanel, MessageBlock, NeonHeader, StatusPanel, ToolCard, Transcript, WelcomePanel

class PhoneAgentApp(App):
    CSS_PATH = "theme.tcss"
    BINDINGS = [
        ("ctrl+c","cancel_run","Abbrechen"),
        ("ctrl+n","new_session","Neu"),
        ("ctrl+p","toggle_palette","Palette"),
        ("ctrl+s","toggle_status","Status"),
        ("ctrl+q","quit","Ende"),
    ]

    def __init__(self,context,root:Path,new_session:bool=False,safe_mode:bool=False,client:Any=None,provider_config:EffectiveProviderConfig|None=None):
        super().__init__()
        self.context=context; self.root=root; self.safe_mode=safe_mode; self.client=client
        self.active_run_id=None; self.tool_widgets={}
        effective=provider_config or resolve_provider_config(context.config.agent)
        if effective.provider != 'ollama-cloud':
            raise ProviderConfigError('the tool-enabled TUI currently requires provider=ollama-cloud')
        model=effective.model
        self.provider_name=effective.provider
        self.model_name=model; self.chat_store=ChatStore(context.database); self.runtime_store=RuntimeStore(context.database)
        self.session=None if new_session else self.chat_store.latest(self.provider_name,model)
        if self.session is None: self.session=self.chat_store.create(self.provider_name,model)
        registry=ToolRegistry(context,root); artifacts=ArtifactStore(context.database,root)
        self.runtime=AgentRuntime(
            store=self.runtime_store,
            model=OllamaRuntimeModel(client or OllamaCloudClient(model=model,host=effective.base_url,timeout=effective.timeout_seconds)),
            registry=registry,
            policy=RuntimePolicy(registry,root,safe_mode),
            result_projector=artifacts.project_for_model,
        )
        self.status_view=StatusView(model=model,mode='SAFE' if safe_mode else 'ANALYZE',safe_mode=safe_mode)

    def compose(self)->ComposeResult:
        with Container(id='root'):
            yield NeonHeader(self.session.id,self.status_view,id='neon-header')
            with Horizontal(id='body'):
                with VerticalScroll(id='transcript-scroll'):
                    with Transcript(id='transcript-items'):
                        yield WelcomePanel(id='welcome')
                yield StatusPanel(self.status_view,id='sidebar')
            yield StatusPanel(self.status_view,id='drawer')
            yield CommandPalettePanel(id='command-palette')
            yield Input(placeholder='› Schreibe deinem Agenten …',id='composer')
            yield Static('^Q ENDE   ^N NEU   ^P PALETTE   ^S STATUS   ENTER SENDEN',id='hintbar')

    def on_mount(self):
        self.title='CompText Phone Agent'; self.sub_title=f'Session {self.session.id[:8]}'
        self._apply_layout(self.size.width); self.query_one('#composer',Input).focus()

    def on_resize(self,event:events.Resize):
        self._apply_layout(event.size.width)

    def _apply_layout(self,width:int):
        root=self.query_one('#root'); root.remove_class('compact','wide','desktop'); root.add_class(layout_mode(width).value)
        compact=layout_mode(width) is LayoutMode.COMPACT
        for widget in self.tool_widgets.values():
            widget.compact=compact; widget.refresh(layout=True)

    async def on_input_submitted(self,event:Input.Submitted):
        text=event.value.strip(); event.input.value=''
        if not text:return
        welcome=self.query_one('#welcome')
        welcome.display=False
        await self.query_one('#transcript-items',Transcript).mount(MessageBlock(TranscriptItem('user','DU',text)))
        self.chat_store.add(self.session.id,'user',text); self.run_agent(text)

    @work(thread=True,exclusive=True,group='agent')
    def run_agent(self,text:str):
        try:
            history=[{'role':x['role'],'content':x['content']} for x in self.chat_store.messages(self.session.id,40) if x['role'] in {'user','assistant'}][:-1]
            result=self.runtime.run(text,self.session.id,history=history,event_callback=self._event_from_worker)
            self.active_run_id=result.run_id
            answer=result.answer or (f"Freigabe erforderlich: {result.approval_id}" if result.approval_id else f"Beendet: {result.stop_reason}")
            self.chat_store.add(self.session.id,'assistant',answer)
        except Exception as exc:
            self.call_from_thread(self._show_error,str(exc))

    def _event_from_worker(self,event):
        self.active_run_id=event.run_id
        self.call_from_thread(self._apply_runtime_event,event)

    async def _apply_runtime_event(self,event):
        et=event.event_type; payload=event.payload
        transcript=self.query_one('#transcript-items',Transcript)
        if et=='run.started.v1':
            await transcript.mount(MessageBlock(TranscriptItem('system','AGENT','Lauf gestartet',event.timestamp[11:19])))
        elif et.startswith('tool.') or et in {'approval.requested.v1','run.failed.v1'}:
            card=card_from_event(event)
            key=card.call_id or str(payload.get('call_id') or payload.get('approval_id') or event.id)
            existing=self.tool_widgets.get(key)
            if existing is None:
                existing=ToolCard(card,compact=layout_mode(self.size.width) is LayoutMode.COMPACT)
                self.tool_widgets[key]=existing
                await transcript.mount(existing)
            else:
                existing.update_card(card)
        elif et=='run.completed.v1':
            answer=str(payload.get('answer',''))
            if answer:
                await transcript.mount(MessageBlock(TranscriptItem('agent','◈ AGENT',answer,event.timestamp[11:19])))
        elif et=='run.cancelled.v1':
            await transcript.mount(MessageBlock(TranscriptItem('system','ABGEBROCHEN','Der Lauf wurde beendet.',event.timestamp[11:19])))
        self.query_one('#transcript-scroll').scroll_end(animate=False)

    async def _show_error(self,error:str):
        await self.query_one('#transcript-items',Transcript).mount(MessageBlock(TranscriptItem('system','FEHLER',error)))

    def action_new_session(self):
        self.session=self.chat_store.create(self.provider_name,self.model_name); self.active_run_id=None
        self.sub_title=f'Session {self.session.id[:8]}'
        transcript=self.query_one('#transcript-items',Transcript); transcript.remove_children(); transcript.mount(WelcomePanel(id='welcome'))
        self.tool_widgets.clear()
        self.query_one('#neon-header',NeonHeader).session_id=self.session.id; self.query_one('#neon-header').refresh()

    def action_cancel_run(self):
        if self.active_run_id: self.runtime_store.append_signal(self.active_run_id,SignalType.CANCEL,{'source':'tui'})
        for worker in self.workers: worker.cancel()

    def action_toggle_status(self):
        self.query_one('#drawer').toggle_class('visible')

    def action_toggle_palette(self):
        self.query_one('#command-palette').toggle_class('visible')

    async def on_key(self,event:events.Key):
        palette=self.query_one('#command-palette')
        if not palette.has_class('visible'):
            return
        commands={
            '2':'Analysiere meinen Speicher',
            '3':'Finde doppelte Dateien',
            '4':'Erstelle einen sicheren Aufräumplan',
        }
        if event.key=='escape':
            palette.remove_class('visible'); event.stop(); return
        if event.key=='1':
            self.action_new_session(); palette.remove_class('visible'); event.stop(); return
        if event.key=='5':
            palette.remove_class('visible'); self.action_toggle_status(); event.stop(); return
        if event.key in commands:
            composer=self.query_one('#composer',Input); composer.value=commands[event.key]; composer.focus()
            palette.remove_class('visible'); event.stop()

def run_tui(context,root:Path,new_session:bool=False,safe_mode:bool=False,provider_config:EffectiveProviderConfig|None=None):
    PhoneAgentApp(context,root,new_session,safe_mode,provider_config=provider_config).run()
