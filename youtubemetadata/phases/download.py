"""Phase 3 — download audio via yt-dlp for the resolved tracks."""

import yt_dlp

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

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio",
            "merge_output_format": "m4a",
            "writethumbnail": True,
            "outtmpl": str(track_dir / "audio.m4a"),
            "noplaylist": True,
            "postprocessors": [
                {
                    "key": "EmbedThumbnail",
                    "already_have_thumbnail": False,
                }
            ],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"  [{i}/{n}] ✓ {tr.title}")
        except Exception as e:
            print(f"  [{i}/{n}] ✗ {tr.title}  {e}")

    return resolution
