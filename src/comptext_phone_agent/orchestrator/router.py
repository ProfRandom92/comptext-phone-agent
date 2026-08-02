from __future__ import annotations
from urllib.parse import urlparse
import httpx
from .models import RouteDecision, RouteKind
from .parser import parse_router_output

class KeywordRouter:
    def route(self,text:str) -> RouteDecision:
        value=text.lower()
        rules=(
            (('akku','batterie'),'device_battery'),
            (('wlan','wifi','wi-fi'),'device_wifi'),
            (('doppelt','duplikat'),'find_duplicates'),
            (('größte datei','grosse datei','große datei'),'largest_files'),
            (('alte datei','alte Dateien'.lower()),'old_files'),
            (('aufräumplan','aufraeumplan','bereinigungsplan'),'cleanup_plan'),
            (('speicher','storage'),'scan_storage'),
        )
        for words,action in rules:
            if any(word in value for word in words):
                return RouteDecision(RouteKind.DIRECT_ACTION,action,{},0.91,source='keyword')
        return RouteDecision(RouteKind.PLANNER,confidence=0.5,reason='complex_or_unknown',source='keyword')

class LoopbackRouterClient:
    def __init__(self,base_url:str,timeout_seconds:int=20,model:str='MobileActions-270M'):
        parsed=urlparse(base_url)
        if parsed.scheme not in {'http','https'} or parsed.hostname not in {'127.0.0.1','localhost','::1'}:
            raise ValueError('router endpoint must be loopback')
        self.base_url=base_url.rstrip('/'); self.timeout_seconds=timeout_seconds; self.model=model
    def route(self,text:str) -> RouteDecision:
        response=httpx.post(
            f'{self.base_url}/v1/chat/completions',
            json={'model':self.model,'messages':[{'role':'user','content':text}],'temperature':0},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data=response.json()
        content=data['choices'][0]['message']['content']
        return parse_router_output(content)
