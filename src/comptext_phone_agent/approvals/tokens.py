from __future__ import annotations
import base64, hashlib, hmac, json
from .policy import PolicyError

def _encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
def _decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * ((4 - len(text) % 4) % 4))
def encode(payload: dict, secret: bytes) -> str:
    body = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    signature = _encode(hmac.new(secret, body.encode(), hashlib.sha256).digest())
    return body + "." + signature
def decode(token: str, secret: bytes) -> dict:
    try:
        body, signature = token.split(".", 1)
    except ValueError as error:
        raise PolicyError("malformed approval token") from error
    expected = _encode(hmac.new(secret, body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise PolicyError("invalid approval signature")
    try:
        return json.loads(_decode(body))
    except Exception as error:
        raise PolicyError("invalid approval payload") from error
def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
