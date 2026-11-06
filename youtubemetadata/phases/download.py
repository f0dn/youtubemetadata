"""Phase 3 — download audio via yt-dlp for the resolved tracks."""

import subprocess
import sys

from youtubemetadata.models import PlaylistResolution
from youtubemetadata.paths import RAW_DIR
from youtubemetadata.services import is_music_video


def phase_download(resolution: PlaylistResolution) -> PlaylistResolution:
    n = len(resolution.tracks)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"PHASE 3 — Download audio  ({n} tracks)")
    print(f"{'=' * 60}")

    for i, tr in enumerate(resolution.tracks, 1):
        vid = tr.videoId
        track_dir = RAW_DIR / vid
        audio_f = track_dir / "audio.m4a"

        if audio_f.exists():
            print(f"  [{i}/{n}] ⏭  {tr.title}  (cached)")
            continue
        if not tr.isAvailable:
            print(f"  [{i}/{n}] ⏭  {tr.title}  (unavailable)")
            continue
        if is_music_video(tr):
            # we only ever save actual audio tracks (ATVs); music videos themselves are skipped
            print(
                f"  [{i}/{n}] ⏭  {tr.title}  "
                f"(music video → audio track {tr.musicVideoOf or vid} not resolved)"
            )
            continue

        track_dir.mkdir(parents=True, exist_ok=True)
        url = f"https://www.youtube.com/watch?v={vid}"

        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-f",
            "bestaudio[ext=m4a]/bestaudio",
            "--merge-output-format",
            "m4a",
            "--write-info-json",
            "--write-thumbnail",
            "-o",
            str(track_dir / "audio"),
            url,
        ]
        try:
            r = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=180
            )
            if r.returncode == 0:
                print(f"  [{i}/{n}] ✓ {tr.title}")
            else:
                err = (r.stderr or r.stdout or "").strip().splitlines()
                print(f"  [{i}/{n}] ✗ {tr.title}  {err[-1] if err else 'err'}")
        except subprocess.TimeoutExpired:
            print(f"  [{i}/{n}] ⏱  {tr.title}  (timeout)")
        except FileNotFoundError:
            print("ERROR: yt-dlp not found.  pip install yt-dlp")
            sys.exit(1)

    return resolution
