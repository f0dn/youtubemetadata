"""Disk cache for raw YouTube Music metadata responses.

Only what comes back from ``ytmusicapi`` is cached (album and song responses).
Everything derived from those responses (resolutions, lyrics, downloads, …) is
kept in memory only and never persisted here.
"""

import json
from pathlib import Path

from youtubemetadata.paths import ALBUM_DIR, SONG_DIR


def load_raw(path: Path) -> dict | None:
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_raw(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_album(album_id: str) -> dict | None:
    """Load a cached raw album response (``yt.get_album``), if any."""
    return load_raw(ALBUM_DIR / f"{album_id}.json")


def save_album(album_id: str, album: dict) -> None:
    save_raw(ALBUM_DIR / f"{album_id}.json", album)


def load_song(song_id: str) -> dict | None:
    """Load a cached raw song response (``yt.get_song`` / ``yt.get_song_credits``), if any."""
    return load_raw(SONG_DIR / f"{song_id}.json")


def save_song(song_id: str, song: dict) -> None:
    save_raw(SONG_DIR / f"{song_id}.json", song)
