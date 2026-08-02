from __future__ import annotations
class MockTermuxApiClient:
    def battery(self) -> dict:
        return {"health": "GOOD", "percentage": 78, "plugged": "UNPLUGGED", "status": "DISCHARGING", "temperature": 29.1}
    def wifi(self) -> dict:
        return {"ssid": "MockWiFi", "ip": "192.168.1.42", "link_speed_mbps": 433}
    def volume(self) -> list[dict]:
        return [{"stream": "music", "volume": 8, "max_volume": 15}]
    def clipboard_get(self) -> str:
        return "<mock clipboard redacted>"
    def notify(self, title: str, content: str) -> None:
        return None
    def clipboard_set(self, value: str) -> None:
        return None
    def tts(self, value: str) -> None:
        return None
    def vibrate(self, duration_ms: int = 250) -> None:
        return None
