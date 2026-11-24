"""Phase 4 — write the resolved tracks into a Navidrome-compatible library."""

import re
import shutil
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile
from mutagen.mp4 import MP4 as MP4Tag

from youtubemetadata.models import PlaylistResolution, TrackEntry
from youtubemetadata.paths import RAW_DIR


def _sanitize(name: str | None) -> str:
    """Make a name safe for use as a folder / file name."""
    cleaned = re.sub(r'[\\/:*?"<>|]+', " ", name or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "Unknown"


def _artist_list(entry: TrackEntry) -> list[str]:
    """Individual artists of a track (credits-expanded), fallback to the main artist."""
    artists = entry.artists or ([entry.artist] if entry.artist else [])
    cleaned = [a.strip() for a in artists if (a or "").strip()]
    return cleaned or ["Unknown"]


def _display_artist(artists: list[str]) -> str:
    """Display name of an artist / album artist list.

    Multiple artists are joined with ``" feat. "`` (e.g. ``"Alice feat. Bob"``); a
    single artist is used as-is.
    """
    if len(artists) <= 1:
        return artists[0] if artists else "Unknown"
    return " feat. ".join(artists)


def _album_artist_list(entry: TrackEntry, fallback: list[str]) -> list[str]:
    artists = [a for a in (entry.albumArtist or []) if (a or "").strip()]
    return artists or fallback


def _tag_values(entry: TrackEntry) -> dict[str, Any]:
    """Map a resolved track onto simple Navidrome tag names (see mappings.yaml)."""
    artist_list = _artist_list(entry)
    album_artist_list = _album_artist_list(entry, artist_list)
    values: dict[str, Any] = {
        "title": entry.title or "Unknown",
        "artists": artist_list,
        "albumartists": album_artist_list,
        "album": entry.album or "Unknown",
    }
    if entry.trackNumber is not None:
        values["track"] = entry.trackNumber
        values["tracktotal"] = entry.trackTotal or entry.trackNumber
    if entry.year is not None:
        values["releasedate"] = entry.year
    if entry.writtenBy:
        # Navidrome treats WRITER as an alias of COMPOSER
        values["composer"] = "; ".join(entry.writtenBy)
    if entry.producedBy:
        values["producer"] = "; ".join(entry.producedBy)
    if entry.albumVersion:
        values["albumversion"] = entry.albumVersion
    if entry.isExplicit:
        values["explicitstatus"] = 1
    if entry.lyrics:
        values["lyrics"] = entry.lyrics
    if entry.albumDescription:
        values["comment"] = entry.albumDescription
    return values


def _write_tags(path: Path, values: dict[str, Any]) -> bool:
    """Write Navidrome-compatible tags into an audio file (MP4 / m4a)."""
    try:
        tag = MutagenFile(path)
    except Exception:
        return False
    if not isinstance(tag, MP4Tag):
        # only MP4 (m4a) files can be tagged for now
        return False
    try:
        if tag.tags is None:
            tag.add_tags()
        mp4 = tag.tags

        def set_str(name: str, value: Any) -> None:
            if value is None:
                return
            mp4[name] = str(value).encode("utf-8")

        def set_multi(name: str, items: list[str]) -> None:
            clean = [str(i).strip() for i in items or [] if str(i).strip()]
            if clean:
                mp4[name] = [i.encode("utf-8") for i in clean]

        set_str("title", values.get("title"))
        set_multi("artists", values.get("artists") or [])
        set_multi("albumartists", values.get("albumartists") or [])
        set_str("album", values.get("album"))
        set_str("composer", values.get("composer"))
        set_str("producer", values.get("producer"))
        set_str("albumversion", values.get("albumversion"))
        set_str("lyrics", values.get("lyrics"))
        set_str("releasedate", values.get("releasedate"))
        if values.get("track") is not None and values.get("tracktotal") is not None:
            mp4["track"] = str(values["track"]).encode("utf-8")
            mp4["tracktotal"] = str(values["tracktotal"]).encode("utf-8")
        set_str("explicitstatus", values.get("explicitstatus"))
        set_str("explicitstatus", values.get("explicitstatus"))
        set_str("comment", values.get("comment"))
        tag.save()
    except Exception:
        return False
    return True


def phase_library(resolution: PlaylistResolution, library_path: str | Path) -> Path:
    """Write the resolved tracks into a Navidrome-compatible library.

    Creates an ``artist / album / song`` directory structure under ``library_path`` and
    copies + tags the downloaded audio tracks accordingly (Navidrome tag mapping).
    """
    lib = Path(library_path).expanduser()

    written = 0
    skipped = 0
    for entry in resolution.tracks:
        if not entry.isAvailable:
            skipped += 1
            continue
        if entry.isMusicVideo and not entry.musicVideoOf:
            # music video → audio track could not be resolved, nothing to save
            skipped += 1
            continue
        src_file = RAW_DIR / entry.videoId / "audio.m4a"
        if not src_file.is_file():
            skipped += 1
            continue

        dest = (
            lib
            / _sanitize(_display_artist(_artist_list(entry)))
            / _sanitize(entry.album)
            / f"{entry.trackNumber or entry.index:02d} - {_sanitize(entry.title)}.m4a"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest)
        _write_tags(dest, _tag_values(entry))
        written += 1

    print(f"Navidrome library written → {lib}  ({written} track(s), {skipped} skipped)")
    return lib
