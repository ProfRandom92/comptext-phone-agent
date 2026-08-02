from comptext_phone_agent.audit.redaction import redact

def test_secret_keys_redacted():
    result = redact({"api_key": "sk-1234567890", "nested": {"password": "hello"}, "ok": "value"})
    assert result["api_key"] == "<redacted>"
    assert result["nested"]["password"] == "<redacted>"
    assert result["ok"] == "value"

def test_bearer_and_keylike_redacted():
    value = redact("Authorization Bearer abcdefghijklmnop and sk-abcdefghijk")
    assert "abcdefghijklmnop" not in value
    assert "sk-abcdefghijk" not in value

def test_clipboard_field_redacted():
    assert redact({"clipboard": "private text"})["clipboard"] == "<redacted>"
