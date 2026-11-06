"""Phase 2 — fetch lyrics for the resolved tracks."""

from youtubemetadata.models import PlaylistResolution
from youtubemetadata.services import YouTubeMusicService


def phase_lyrics(
    resolution: PlaylistResolution, service: YouTubeMusicService | None = None
) -> PlaylistResolution:
    svc = service or YouTubeMusicService()
    n = len(resolution.tracks)

    print(f"\n{'=' * 60}")
    print(f"PHASE 2 — Fetch lyrics  ({n} tracks)")
    print(f"{'=' * 60}")

    for i, tr in enumerate(resolution.tracks, 1):
        vid = tr.videoId
        try:
            watch = svc.get_watch_playlist(vid)
            # lyrics browseId is nested in the watch response
            lyr_bid = None
            lyrics_section = watch.get("lyrics", {})
            if isinstance(lyrics_section, dict):
                lyr_bid = lyrics_section.get("browseId")
            if not lyr_bid:
                # fallback: search in the full response
                for key in ("lyrics", "lyricsRenderer"):
                    val = watch.get(key)
                    if isinstance(val, dict) and val.get("browseId"):
                        lyr_bid = val["browseId"]
                        break

            if lyr_bid:
                res = svc.get_lyrics(lyr_bid)
                if res and res.get("lyrics"):
                    raw = res["lyrics"]
                    if isinstance(raw, str):
                        tr.lyrics = raw
                    else:
                        tr.lyrics = "\n".join(ln.text for ln in raw)
                    tr.lyricsSource = res.get("source") or ""
                    print(f"  [{i}/{n}] ✓ {tr.title}")
                else:
                    tr.lyrics = None
                    print(f"  [{i}/{n}] — {tr.title}  (none)")
            else:
                tr.lyrics = None
                print(f"  [{i}/{n}] — {tr.title}  (no lyrics id)")
        except Exception as e:
            tr.lyrics = None
            print(f"  [{i}/{n}] ✗ {tr.title}  {e}")

    got = sum(1 for t in resolution.tracks if t.lyrics)
    print(f"\nLyrics: {got}/{n}")
    return resolution
