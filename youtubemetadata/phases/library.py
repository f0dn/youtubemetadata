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
        "artist": _display_artist(artist_list),
        "artists": artist_list,
        "albumartist": _display_artist(album_artist_list),
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

        def set_atom(key: str, value: Any) -> None:
            if value is None:
                return
            mp4[key] = str(value)

        def set_freeform(key: str, value: Any) -> None:
            if value is None:
                return
            if isinstance(value, list):
                mp4[key] = [str(v).encode("utf-8") for v in value]
            else:
                mp4[key] = str(value).encode("utf-8")

        set_atom("\N{COPYRIGHT SIGN}nam", values.get("title"))
        set_atom("\N{COPYRIGHT SIGN}ART", values.get("artist"))
        set_freeform("----:com.apple.iTunes:artists", values.get("artists") or [])
        set_atom("aART", values.get("albumartist"))
        set_freeform("----:com.apple.iTunes:albumartists", values.get("albumartists") or [])
        set_atom("\N{COPYRIGHT SIGN}alb", values.get("album"))
        set_atom("\N{COPYRIGHT SIGN}wrt", values.get("composer"))
        set_freeform("----:com.apple.iTunes:producer", values.get("producer"))
        set_freeform("----:com.apple.iTunes:albumversion", values.get("albumversion"))
        set_freeform("----:com.apple.iTunes:lyrics", values.get("lyrics"))
        set_atom("\N{COPYRIGHT SIGN}day", values.get("releasedate"))
        if values.get("track") is not None and values.get("tracktotal") is not None:
            mp4["trkn"] = [(int(values["track"]), int(values["tracktotal"]))]
        if values.get("explicitstatus") is not None:
            mp4["rtng"] = [int(values["explicitstatus"])]
        set_atom("\N{COPYRIGHT SIGN}cmt", values.get("comment"))
        tag.save()
    except Exception as e:
        raise e
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

        album_name = entry.album or "Unknown"
        if entry.albumVersion:
            album_name = f"{album_name} ({entry.albumVersion})"

        dest = (
            lib
            / _sanitize(_display_artist(_artist_list(entry)))
            / _sanitize(album_name)
            / f"{entry.trackNumber or entry.index:02d} - {_sanitize(entry.title)}.m4a"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest)
        _write_tags(dest, _tag_values(entry))
        written += 1

    print(f"Navidrome library written → {lib}  ({written} track(s), {skipped} skipped)")
    return lib
