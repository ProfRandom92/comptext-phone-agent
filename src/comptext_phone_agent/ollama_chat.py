from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx


API_URL = "https://ollama.com/api/chat"
MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:20b")
API_KEY = os.environ.get("OLLAMA_API_KEY", "")

STORAGE_ROOT = Path.home() / "storage" / "shared"
HISTORY_FILE = (
    Path.home()
    / ".comptext-phone-agent"
    / "chat"
    / "ollama-history.json"
)

SYSTEM_PROMPT = """
Du bist CompText Phone Agent, ein deutschsprachiger Assistent auf Android.

Du kannst normal mit dem Nutzer sprechen und Ergebnisse lokaler, sicher
vordefinierter Werkzeuge erklären.

Wichtige Regeln:
- Erfinde keine Scan-, Geräte- oder Dateiergebnisse.
- Wenn ein TOOL_RESULT vorliegt, stütze deine Antwort ausschließlich darauf.
- Behaupte keine Dateiänderung, wenn keine lokale Aktion ausgeführt wurde.
- Empfehle keine freien find-, xargs-, rm-, mv- oder Shell-Konstruktionen,
  wenn der CompText Phone Agent bereits ein passendes Werkzeug besitzt.
- Löschen, Verschieben, Überschreiben und Uploads benötigen einen gespeicherten
  Plan und eine lokale Freigabe.
- CompText-, DCIM-, Pictures-, WhatsApp-, Android- und Samsung-Pfade sind
  besonders geschützt.
- Gib Secrets niemals aus.
- Antworte klar und standardmäßig auf Deutsch.
""".strip()


def run_fixed(command: list[str], timeout: int = 300) -> dict[str, Any]:
    """Run only a preconstructed command list. No shell interpretation."""
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Das lokale Werkzeug hat das Zeitlimit überschritten.",
        }
    except OSError as exc:
        return {
            "ok": False,
            "error": f"Das lokale Werkzeug konnte nicht gestartet werden: {exc}",
        }

    if completed.returncode != 0:
        return {
            "ok": False,
            "exit_code": completed.returncode,
            "error": completed.stderr.strip() or completed.stdout.strip(),
        }

    output = completed.stdout.strip()

    try:
        data: Any = json.loads(output)
    except json.JSONDecodeError:
        data = output

    return {
        "ok": True,
        "command": command[1] if len(command) > 1 else command[0],
        "data": data,
    }


def detect_tool(text: str) -> tuple[str, list[str]] | None:
    """
    Map natural language to an allow-listed CompText command.

    No model-generated command is accepted.
    """
    lower = text.casefold()
    executable = "comptext-phone"
    root = str(STORAGE_ROOT)

    if any(word in lower for word in ("doppelte", "duplikate", "duplicate")):
        return (
            "duplicates",
            [
                executable,
                "duplicates",
                "--path",
                root,
                "--verify",
                "--json",
            ],
        )

    if (
        "größte datei" in lower
        or "größten datei" in lower
        or "grosse datei" in lower
        or "große datei" in lower
        or "viel platz" in lower
    ):
        return (
            "largest_files",
            [
                executable,
                "analyze",
                "large",
                "--path",
                root,
                "--top",
                "30",
                "--json",
            ],
        )

    if any(phrase in lower for phrase in ("speicher analys", "speicher scann", "scan meinen speicher")):
        return (
            "storage_scan",
            [
                executable,
                "scan",
                "--path",
                root,
                "--top",
                "30",
                "--json",
            ],
        )

    if any(phrase in lower for phrase in ("alte dateien", "alte datei")):
        return (
            "old_files",
            [
                executable,
                "analyze",
                "old",
                "--path",
                root,
                "--top",
                "30",
                "--json",
            ],
        )

    if any(phrase in lower for phrase in ("dateitypen", "welche dateien", "dateiarten")):
        return (
            "file_types",
            [
                executable,
                "analyze",
                "types",
                "--path",
                root,
                "--json",
            ],
        )

    if any(word in lower for word in ("akku", "batterie", "battery")):
        return (
            "battery",
            [executable, "device", "battery", "--json"],
        )

    if any(word in lower for word in ("wlan", "wifi", "wi-fi")):
        return (
            "wifi",
            [executable, "device", "wifi", "--json"],
        )

    if any(word in lower for word in ("lautstärke", "lautstaerke", "volume")):
        return (
            "volume",
            [executable, "device", "volume", "--json"],
        )

    if any(phrase in lower for phrase in ("systemstatus", "agent status", "dein status")):
        return (
            "status",
            [executable, "status", "--json"],
        )

    if any(
        word in lower
        for word in (
            "lösche",
            "loesche",
            "entferne",
            "verschiebe",
            "räume auf",
            "raeume auf",
            "bereinige",
        )
    ):
        return (
            "cleanup_plan",
            [
                executable,
                "cleanup",
                "plan",
                "--path",
                root,
                "--json",
            ],
        )

    return None


def load_history() -> list[dict[str, str]]:
    if not HISTORY_FILE.exists():
        return []

    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    result: list[dict[str, str]] = []

    for item in data[-30:]:
        if (
            isinstance(item, dict)
            and item.get("role") in {"user", "assistant"}
            and isinstance(item.get("content"), str)
        ):
            result.append(
                {
                    "role": item["role"],
                    "content": item["content"],
                }
            )

    return result


def save_history(messages: list[dict[str, str]]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary = HISTORY_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(messages[-30:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(HISTORY_FILE)
    HISTORY_FILE.chmod(0o600)


def ask_ollama(
    history: list[dict[str, str]],
    user_text: str,
    tool_name: str | None = None,
    tool_result: dict[str, Any] | None = None,
) -> str:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_text},
    ]

    if tool_result is not None:
        messages.append(
            {
                "role": "system",
                "content": (
                    f"TOOL_RESULT\n"
                    f"tool={tool_name}\n"
                    f"{json.dumps(tool_result, ensure_ascii=False)}\n\n"
                    "Erkläre das Ergebnis verständlich. "
                    "Nenne geschützte Dateien ausdrücklich. "
                    "Führe keine weitere Aktion aus."
                ),
            }
        )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }

    with httpx.Client(timeout=180) as client:
        response = client.post(
            API_URL,
            headers=headers,
            json=payload,
        )

    if response.status_code == 401:
        raise RuntimeError("Der Ollama API-Key wurde abgelehnt.")

    if response.status_code == 429:
        raise RuntimeError("Das Ollama-Cloud-Nutzungslimit wurde erreicht.")

    response.raise_for_status()

    data = response.json()
    content = data.get("message", {}).get("content")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama lieferte keine lesbare Antwort.")

    return content.strip()


def print_help() -> None:
    print(
        """
Beispiele:
  Finde doppelte Dateien, aber ändere nichts.
  Zeige mir die 30 größten Dateien.
  Analysiere meinen Speicher.
  Welche alten Dateien habe ich?
  Wie ist mein Akkustand?
  Zeige meinen WLAN-Status.
  Bereite einen Aufräumplan vor.

Direkte Befehle:
  /clear      Gesprächsverlauf löschen
  /help       Hilfe anzeigen
  /exit       Chat beenden

Sicherheitsmodell:
  Lesende Werkzeuge dürfen automatisch laufen.
  Verändernde Anfragen erzeugen ausschließlich einen Plan.
  Keine freie Shell-Ausführung.
""".strip()
    )


def main() -> None:
    if not API_KEY:
        print(
            "OLLAMA_API_KEY ist nicht geladen.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    history = load_history()

    print(f"CompText Phone Agent · Ollama Cloud · {MODEL}")
    print("Sichere lokale Tools sind aktiviert.")
    print("Schreibe /help für Beispiele oder /exit zum Beenden.")

    while True:
        try:
            text = input("\nDu › ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue

        if text in {"/exit", "/quit"}:
            break

        if text == "/help":
            print_help()
            continue

        if text == "/clear":
            history.clear()
            HISTORY_FILE.unlink(missing_ok=True)
            print("Gesprächsverlauf gelöscht.")
            continue

        selected = detect_tool(text)
        tool_name: str | None = None
        tool_result: dict[str, Any] | None = None

        if selected is not None:
            tool_name, command = selected
            print(f"\nLokales Werkzeug › {tool_name}")
            tool_result = run_fixed(command)

        try:
            answer = ask_ollama(
                history=history,
                user_text=text,
                tool_name=tool_name,
                tool_result=tool_result,
            )
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            print(f"\nFehler › {exc}")
            continue

        history.extend(
            [
                {"role": "user", "content": text},
                {"role": "assistant", "content": answer},
            ]
        )
        save_history(history)

        print(f"\nAgent › {answer}")


if __name__ == "__main__":
    main()
