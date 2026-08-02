from __future__ import annotations
from datetime import datetime
from rich.text import Text
from textual.containers import Container
from textual.widgets import Static
from .models import StatusView, ToolCardView, TranscriptItem

class NeonHeader(Static):
    def __init__(self, session_id: str, status: StatusView, **kwargs):
        super().__init__(**kwargs); self.session_id=session_id; self.status_view=status
    def render(self) -> Text:
        t=Text()
        t.append('∞ ',style='bold cyan'); t.append('COMPTEXT PHONE AGENT',style='bold #e8ddff')
        t.append(f"  {datetime.now().strftime('%H:%M')}",style='#9fe9ff')
        t.append(f"\nSESSION {self.session_id[:8]}  ",style='#8e81b7')
        t.append(self.status_view.mode,style='bold cyan')
        t.append(' · ',style='#554a72'); t.append('SAFE' if self.status_view.safe_mode else 'SAFE OFF',style='bold green' if self.status_view.safe_mode else '#d29cff')
        t.append(' · ',style='#554a72'); t.append(self.status_view.model,style='#b9adcf')
        return t

class WelcomePanel(Static):
    def render(self) -> Text:
        t=Text('∞ BEREIT\n',style='bold #b88cff')
        t.append('Frag mich zum Beispiel:\n\n',style='#b6afc8')
        for line in ('› Analysiere meinen Speicher','› Finde große Dateien','› Prüfe meinen Akku','› Erstelle einen sicheren Aufräumplan'):
            t.append(line+'\n',style='#68dcff')
        return t

class MessageBlock(Static):
    def __init__(self, item: TranscriptItem, **kwargs):
        super().__init__(**kwargs); self.item=item; self.add_class(item.kind)
    def render(self) -> Text:
        color='#68dcff' if self.item.kind=='user' else '#bb8cff' if self.item.kind=='agent' else '#8e81b7'
        t=Text()
        if self.item.timestamp: t.append(self.item.timestamp+'  ',style='#68627a')
        t.append(self.item.title+'\n',style=f'bold {color}')
        t.append(self.item.body,style='#e8e8f4')
        return t

class ToolCard(Static):
    def __init__(self, card: ToolCardView, compact: bool=False, **kwargs):
        super().__init__(**kwargs); self.card=card; self.compact=compact; self.add_class(card.kind,card.state)
    def update_card(self, card: ToolCardView) -> None:
        self.remove_class(self.card.kind,self.card.state)
        self.card=card
        self.add_class(card.kind,card.state)
        self.refresh(layout=True)
    def render(self) -> Text:
        icon={'storage':'▣','duplicates':'▤','approval':'!','error':'×'}.get(self.card.kind,'◆')
        state={'running':'LÄUFT','completed':'ABGESCHLOSSEN','waiting_approval':'FREIGABE','failed':'FEHLER'}.get(self.card.state,self.card.state.upper())
        accent='#55d9ff' if self.card.kind=='storage' else '#b56cff' if self.card.kind in {'duplicates','approval'} else '#ff6b7d' if self.card.kind=='error' else '#9fe9ff'
        t=Text()
        t.append(f'{icon} {self.card.title}',style=f'bold {accent}')
        t.append(f'   {state}\n',style='bold green' if self.card.state=='completed' else 'bold #ffbf69' if self.card.state=='waiting_approval' else accent)
        if self.card.progress is not None:
            width=16 if self.compact else 28; filled=max(0,min(width,round(width*self.card.progress/100)))
            t.append('█'*filled,style=accent); t.append('░'*(width-filled),style='#25223a'); t.append(f' {self.card.progress}%\n',style='#b6afc8')
        t.append(self.card.summary+'\n',style='#f0edf7')
        if not self.compact:
            for key,value in self.card.details: t.append(f'{key:<16}',style='#8e879c'); t.append(value+'\n',style='#69dcff')
        if self.card.protected: t.append('GESCHÜTZTE ELEMENTE ERKANNT\n',style='bold #ffbf69')
        if self.card.approval_id: t.append(f'Approval: {self.card.approval_id}',style='#ffbf69')
        return t

class StatusPanel(Static):
    def __init__(self, status: StatusView, **kwargs): super().__init__(**kwargs); self.status_view=status
    def render(self) -> Text:
        s=self.status_view; t=Text('● SYSTEM\n',style='bold #55d9ff')
        t.append(f"Akku              {s.battery_percent if s.battery_percent is not None else '—'}%\n",style='#ddd8e7')
        t.append(f"Cloud             {'VERBUNDEN' if s.cloud_connected else 'OFFLINE'}\n\n",style='green' if s.cloud_connected else '#ffbf69')
        t.append('● MODEL\n',style='bold #b56cff'); t.append(f'{s.model}\nModus             {s.mode}\n\n',style='#ddd8e7')
        t.append('● PROTECTIONS\n',style='bold #55d9ff')
        for item in s.protections: t.append(f'{item:<18}',style='#ddd8e7'); t.append('AKTIV\n',style='green')
        t.append('\n∞ COMPTEXT',style='bold #6cdfff')
        return t

class Transcript(Container):
    pass


class CommandPalettePanel(Static):
    def render(self) -> Text:
        t=Text('⌘ COMMAND PALETTE\n',style='bold #69dcff')
        commands=(
            ('1','Neue Sitzung'),
            ('2','Speicher analysieren'),
            ('3','Doppelte Dateien finden'),
            ('4','Sicheren Aufräumplan erstellen'),
            ('5','Systemstatus öffnen'),
        )
        for key,label in commands:
            t.append(f'\n {key}  ',style='bold #b56cff')
            t.append(label,style='#eeeaf6')
        t.append('\n\n ESC  Schließen',style='#8e81b7')
        return t
