from __future__ import annotations
from pathlib import Path
import os, time

def _write(path: Path, data: bytes, old_days: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            path.chmod(0o600)
        except OSError:
            pass
    path.write_bytes(data)
    if old_days:
        stamp = time.time() - old_days * 86400
        os.utime(path, (stamp, stamp))

def create_mock_phone(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name in ["DCIM", "Download", "Documents", "Pictures", "Movies", "Music", "WhatsApp", "Android", "Samsung", "CompText", ".CompTextTrash"]:
        (root / name).mkdir(parents=True, exist_ok=True)
    common_video = (b"MOCK-VIDEO-FRAME" * 4096)
    _write(root / "DCIM/Camera/VID_0001.mp4", common_video, 30)
    _write(root / "Download/copied-video.mp4", common_video, 400)
    _write(root / "Download/old-installer.apk", b"APK" * 8192, 600)
    _write(root / "Download/archive-old.zip", b"ZIPDATA" * 8192, 700)
    _write(root / "Download/recent.zip", b"RECENT" * 1024, 2)
    _write(root / "Download/same-name.zip", b"FIRST", 500)
    _write(root / "Documents/same-name.zip", b"SECOND-DIFFERENT", 500)
    _write(root / "Pictures/photo.jpg", b"JPEG" * 4096, 50)
    _write(root / "WhatsApp/Media/shared.jpg", b"WHATSAPP" * 1024, 250)
    _write(root / "Music/song.mp3", b"MP3" * 4096, 100)
    _write(root / "Documents/notes.txt", b"notes", 20)
    _write(root / "Documents/empty.txt", b"", 1000)
    _write(root / "CompText/critical-project.zip", b"DO-NOT-TOUCH" * 1024, 1000)
    _write(root / "Download/CompText/backup.zip", b"DO-NOT-TOUCH" * 512, 1000)
    sparse = root / "Movies/large-demo-video.mkv"
    sparse.parent.mkdir(parents=True, exist_ok=True)
    with sparse.open("wb") as handle:
        handle.truncate(8 * 1024 * 1024)
    stamp = time.time() - 500 * 86400
    os.utime(sparse, (stamp, stamp))
    outside = root.parent / "outside-secret.txt"
    outside.write_text("outside", encoding="utf-8")
    link = root / "Download/outside-link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pass
    unreadable = root / "Android/data/restricted.bin"
    _write(unreadable, b"restricted", 500)
    try:
        unreadable.chmod(0)
    except OSError:
        pass
    return root
