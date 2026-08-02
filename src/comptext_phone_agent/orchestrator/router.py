from __future__ import annotations

from dataclasses import replace
import json
import os
import unicodedata
from urllib.parse import urlsplit

import httpx

from .models import RouteDecision, RouteKind
from .parser import MAX_ROUTER_RESPONSE_BYTES, parse_router_output


_STATUS_CATEGORIES = {
    401: 'authentication',
    403: 'authorization',
    404: 'not_found',
    429: 'rate_limited',
    502: 'service_unavailable',
    503: 'service_unavailable',
    504: 'service_unavailable',
}
MAX_ROUTER_INPUT_BYTES = 16 * 1024
_FALLBACK_CATEGORIES = frozenset({'network','timeout','service_unavailable'})


class RouterError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        category: str = 'router_error',
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.status_code = status_code


def validate_loopback_router_url(base_url: str) -> str:
    try:
        parsed=urlsplit(base_url)
        port=parsed.port
    except (TypeError,ValueError) as error:
        raise ValueError('router endpoint must be strict loopback HTTP') from error
    if (
        parsed.scheme != 'http'
        or parsed.hostname not in {'127.0.0.1','localhost','::1'}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {'','/'}
        or port is None
    ):
        raise ValueError('router endpoint must be strict loopback HTTP')
    return base_url.rstrip('/')


class KeywordRouter:
    def route(self,text:str) -> RouteDecision:
        value=' '.join(unicodedata.normalize('NFKC',text).casefold().split())
        rules=(
            (('akku','batterie'),'device_battery'),
            (('wlan','wifi','wi-fi'),'device_wifi'),
            (('doppelt','duplikat'),'find_duplicates'),
            (('größte datei','grosse datei','große datei','groesste datei'),'largest_files'),
            (('alte datei',),'old_files'),
            (('aufräumplan','aufraeumplan','bereinigungsplan'),'cleanup_plan'),
            (('speicher','storage'),'scan_storage'),
        )
        for words,action in rules:
            if any(word in value for word in words):
                return RouteDecision(RouteKind.DIRECT_ACTION,action,{},0.91,source='keyword')
        return RouteDecision(RouteKind.DELEGATE,confidence=0.5,reason='complex_or_unknown',source='keyword')


class LoopbackRouterClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 20,
        model: str = 'MobileActions-270M',
        *,
        token: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url=validate_loopback_router_url(base_url)
        self.timeout_seconds=timeout_seconds
        self.model=model
        self.token=token if token is not None else os.environ.get('COMPTEXT_BROKER_TOKEN','')
        if not self.token:
            raise RouterError('broker token is not configured',category='configuration')
        self._client=client

    def route(self,text:str) -> RouteDecision:
        if not isinstance(text,str) or len(text.encode('utf-8')) > MAX_ROUTER_INPUT_BYTES:
            raise RouterError('router input is too large',category='request_too_large')
        client=self._client or httpx.Client(timeout=self.timeout_seconds,follow_redirects=False)
        close=self._client is None
        response=None
        try:
            request=client.build_request(
                'POST',
                f'{self.base_url}/v1/route',
                headers={
                    'Authorization':f'Bearer {self.token}',
                    'Accept-Encoding':'identity',
                    'Content-Type':'application/json',
                },
                json={'model':self.model,'input':text},
            )
            response=client.send(request,stream=True,follow_redirects=False)
            if 300 <= response.status_code < 400:
                raise RouterError('broker redirects are forbidden',category='redirect',status_code=response.status_code)
            response.raise_for_status()
            content_encoding=response.headers.get('Content-Encoding','identity').strip().casefold()
            if content_encoding not in {'','identity'}:
                raise RouterError('encoded broker responses are forbidden',category='invalid_response')
            content_length=response.headers.get('Content-Length')
            if content_length is not None:
                try:
                    declared_length=int(content_length)
                except ValueError as error:
                    raise RouterError('invalid broker content length',category='invalid_response') from error
                if declared_length < 0:
                    raise RouterError('invalid broker content length',category='invalid_response')
                if declared_length > MAX_ROUTER_RESPONSE_BYTES:
                    raise RouterError('broker response is too large',category='response_too_large')
            body=bytearray()
            chunks=((response.content,) if response.is_stream_consumed
                    else response.iter_raw(chunk_size=8192))
            for chunk in chunks:
                remaining=MAX_ROUTER_RESPONSE_BYTES-len(body)
                if len(chunk) > remaining:
                    body.extend(chunk[:remaining])
                    raise RouterError('broker response is too large',category='response_too_large')
                body.extend(chunk)
            data=json.loads(bytes(body))
            if not isinstance(data,dict):
                raise ValueError('broker response must be an object')
            if 'decision' in data:
                rendered=json.dumps(data['decision'],ensure_ascii=False)
            elif 'choices' in data:
                rendered=data['choices'][0]['message']['content']
            else:
                rendered=json.dumps(data,ensure_ascii=False)
            if not isinstance(rendered,str):
                raise ValueError('broker decision must be text or an object')
            return parse_router_output(rendered)
        except RouterError:
            raise
        except httpx.HTTPStatusError as error:
            status=error.response.status_code
            raise RouterError(
                'broker HTTP request failed',
                category=_STATUS_CATEGORIES.get(status,'http_error'),
                status_code=status,
            ) from error
        except httpx.TimeoutException as error:
            raise RouterError('broker request timed out',category='timeout') from error
        except httpx.RequestError as error:
            raise RouterError('broker network request failed',category='network') from error
        except (json.JSONDecodeError,KeyError,IndexError,TypeError,ValueError) as error:
            raise RouterError('broker returned an invalid response',category='invalid_response') from error
        finally:
            if response is not None:
                response.close()
            if close:
                client.close()


class AutoRouter:
    def __init__(self,primary, fallback: KeywordRouter | None=None) -> None:
        self.primary=primary
        self.fallback=fallback or KeywordRouter()

    def route(self,text:str) -> RouteDecision:
        try:
            if self.primary is None:
                raise RouterError('broker is not configured',category='configuration')
            return self.primary.route(text)
        except RouterError as error:
            if error.category not in _FALLBACK_CATEGORIES:
                raise
            decision=self.fallback.route(text)
            return replace(decision,source='keyword_fallback')
