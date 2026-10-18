import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ── defaults ──────────────────────────────────────────────────────────
DEFAULT_RAW = Path("raw")
DEFAULT_LIBRARY = Path("library")

AUDIO_EXTS = {".m4a", ".mp3", ".opus", ".flac", ".ogg", ".wav", ".aac"}
IMAGE_EXTS = {".webp", ".jpg", ".jpeg", ".png"}

MIME_BY_EXT = {
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


# ═════════════════════════════════════════════════════════════════════
#  helpers
# ═════════════════════════════════════════════════════════════════════


def _split_artists(raw: str) -> list[str]:
    """'A ft. B & C' → ['A', 'B', 'C']"""
    parts = re.split(
        r"\s+(?:ft\.?|feat\.?|featuring|&|and)\s+", raw, flags=re.IGNORECASE
    )
    return [p.strip() for p in parts if p.strip()]


def _sanitize(name: str) -> str:
    """Replace characters that are illegal in file/folder names."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()


def _first(video_dir: Path, exts: set[str]) -> Path | None:
    """Return the first file in *video_dir* whose suffix is in *exts*."""
    for f in sorted(video_dir.iterdir()):
        if f.suffix.lower() in exts:
            return f
    return None


def _find_info(video_dir: Path) -> Path | None:
    for f in video_dir.iterdir():
        if f.name.endswith(".info.json"):
            return f
    return None


def download(url: str, raw: Path, transcode: str | None = None) -> None:
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / ".download_archive"

    cmd: list[str] = [
        "yt-dlp",
        "-f",
        "bestaudio/best",
        "--write-info-json",
        "--write-thumbnail",
        "--yes-playlist",
        "--download-archive",
        str(archive),
        "-o",
        str(raw / "%(id)s" / "%(id)s.%(ext)s"),
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "--sleep-requests",
        "3",
        "--sleep-interval",
        "2",
        "--max-sleep-interval",
        "15",
        url,
    ]

    if transcode:
        cmd[2:2] = ["-x", "--audio-format", transcode, "--audio-quality", "0"]

    print(f"Downloading into {raw.resolve()}/")
    subprocess.run(cmd, check=True)
    print("Download complete")


def organise_track(video_dir: Path, library: Path) -> Path | None:
    info_file = _find_info(video_dir)
    if info_file is None:
        print(f"  ⚠ {video_dir.name}: no .info.json, skipping")
        return None

    with open(info_file) as fh:
        info = json.load(fh)

    video_id = video_dir.name

    title = info.get("title", "Unknown")

    artist = info.get("artist") or info.get("channel") or ""
    artists = info.get("artists")
    primary = artists[0] if artists else artist

    album = info.get("album") or "Singles"

    try:
        track_num = int(info.get("track_number") or info.get("track") or 0)
    except TypeError, ValueError:
        track_num = 0

    # ── locate the audio file ───────────────────────────────────────
    audio = _first(video_dir, AUDIO_EXTS)
    if audio is None:
        print(f"  ⚠ {video_dir.name}: no audio file, skipping")
        return None

    # ── build target path ───────────────────────────────────────────
    prefix = f"{track_num:02d} - " if track_num else ""
    dest_name = _sanitize(f"{prefix}{title}{audio.suffix}")
    dest_dir = library / _sanitize(primary) / _sanitize(album)
    dest_path = dest_dir / dest_name

    # skip if already in the library (idempotent re-runs)
    if dest_path.exists():
        print(f"  ↷ exists  {dest_path.relative_to(library)}")
        return None

    # ── copy + tag ──────────────────────────────────────────────────
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audio, dest_path)

    try:
        _embed_tags(
            dest_path,
            video_dir,
            info,
            title,
            artists,
            primary,
            album,
            track_num,
            video_id,
        )
    except ImportError:
        print("  ⚠ mutagen not installed — file copied, tags skipped")
    except Exception as exc:
        print(f"  ⚠ tagging failed ({exc}) — file still copied")

    print(f"  ✓ {dest_path.relative_to(library)}")
    return dest_path


def _embed_tags(
    path: Path,
    video_dir: Path,
    info: dict,
    title: str,
    artists: list[str],
    album_artist: str,
    album: str,
    track_num: int,
    video_id: str,
) -> None:
    """Write metadata + embedded cover via mutagen EasyMode.

    Works for MP3 (ID3), M4A (MP4), FLAC/Opus (Vorbis) transparently.
    """
    from mutagen import File as MFile  # raises ImportError if not installed

    audio = MFile(path, easy=True)
    if audio is None:
        return

    # core tags
    audio["title"] = title
    audio["artist"] = artists  # mutagen joins list with ';'
    audio["album"] = album
    audio["albumartist"] = [album_artist]

    if track_num:
        audio["tracknumber"] = [f"{track_num:02d}"]

    # year from upload_date (YYYYMMDD → YYYY)
    year = (info.get("upload_date") or "")[:4]
    if year.isdigit():
        audio["date"] = [year]

    # genre from YouTube categories (best-effort)
    cats = info.get("categories") or []
    if cats:
        audio["genre"] = [cats[0]]

    # traceability: keep the YouTube ID + a short description
    comments = [f"yt:{video_id}"]
    desc = (info.get("description") or "").strip()
    if desc:
        comments.append(desc[:200])
    audio["comment"] = comments

    # ── cover art ───────────────────────────────────────────────────
    thumb = _first(video_dir, IMAGE_EXTS)
    if thumb is not None:
        mime = MIME_BY_EXT.get(thumb.suffix.lower(), "image/jpeg")
        audio.add_picture(thumb.read_bytes(), mime, "Front Cover", 3)

    # ── extension point: lyrics go here ────────────────────────────
    # audio["lyrics"]       = "plain text lyrics"
    # audio["synced_lyrics"] = "[00:12.00]line one\n[00:15.00]line two"

    audio.save()


def organise(raw: Path, library: Path) -> None:
    """Walk every raw/<id>/ directory and copy into the library."""
    if not raw.is_dir():
        print(f"✗ raw directory not found at {raw.resolve()}")
        print("  Run:  python yt_sync.py download <url>")
        sys.exit(1)

    video_dirs = sorted(d for d in raw.iterdir() if d.is_dir())
    if not video_dirs:
        print("raw/ is empty — nothing to organise.")
        return

    library.mkdir(parents=True, exist_ok=True)

    added = skipped = 0
    for vd in video_dirs:
        if organise_track(vd, library):
            added += 1
        else:
            skipped += 1

    print(f"\n✓ {added} added, {skipped} skipped → {library.resolve()}/")


# ═════════════════════════════════════════════════════════════════════
#  CLI
# ═════════════════════════════════════════════════════════════════════


def run() -> None:
    parser = argparse.ArgumentParser(
        prog="yt_sync",
        description="Download YouTube Music audio and organise it for Navidrome.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── download ────────────────────────────────────────────────────
    p_dl = sub.add_parser("download", help="Step 1: fetch audio + metadata into raw/")
    p_dl.add_argument("url", help="YouTube Music video or playlist URL")
    p_dl.add_argument(
        "--raw",
        type=Path,
        default=DEFAULT_RAW,
        help=f"cache directory (default: {DEFAULT_RAW})",
    )
    p_dl.add_argument(
        "--transcode",
        choices=["mp3", "flac", "opus", "aac"],
        default=None,
        help="transcode with ffmpeg (default: keep native format)",
    )

    # ── organise ────────────────────────────────────────────────────
    p_org = sub.add_parser("organise", help="Step 2: tag + copy raw/ into library/")
    p_org.add_argument(
        "--raw",
        type=Path,
        default=DEFAULT_RAW,
        help=f"cache directory (default: {DEFAULT_RAW})",
    )
    p_org.add_argument(
        "--library",
        type=Path,
        default=DEFAULT_LIBRARY,
        help=f"Navidrome music root (default: {DEFAULT_LIBRARY})",
    )

    args = parser.parse_args()

    if args.cmd == "download":
        download(args.url, args.raw, args.transcode)
    elif args.cmd == "organise":
        organise(args.raw, args.library)
