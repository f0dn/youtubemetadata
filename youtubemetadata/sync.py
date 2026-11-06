"""YouTube Music metadata sync.

Phases:
    resolve   — collect all albums of a playlist and save every song that is also in it
    lyrics    — fetch lyrics for the resolved tracks (optional)
    download  — download the audio of the resolved tracks via yt-dlp

Usage:
    python -m youtubemetadata.sync resolve <playlist_url>
    python -m youtubemetadata.sync lyrics
    python -m youtubemetadata.sync download
    python -m youtubemetadata.sync sync <playlist_url>
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ytmusicapi import YTMusic
from ytmusicapi.models.content.enums import VideoType

RAW_DIR = Path("raw")
METADATA_DIR = Path("metadata")
ALBUM_DIR = METADATA_DIR / "albums"
SONG_DIR = METADATA_DIR / "songs"
MANIFEST = Path("manifest.json")
SPEED = 0.5  # seconds between API calls (be nice to YouTube)

MUSIC_VIDEO_TYPE_OMV = VideoType.OMV.value
MUSIC_VIDEO_TYPE_UGC = VideoType.UGC.value
MUSIC_VIDEO_TYPE_ATV = VideoType.ATV.value
MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC = VideoType.OFFICIAL_SOURCE_MUSIC.value

AUDIO_VIDEO_TYPES = frozenset(
    {MUSIC_VIDEO_TYPE_ATV, MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC}
)

yt = YTMusic()


# ─── helpers ───────────────────────────────────────────────────────


def extract_playlist_id(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "list" in qs:
        return qs["list"][0]
    for p in parsed.path.split("/"):
        if p.startswith(("PL", "OLAK", "RDAM")):
            return p
    raise ValueError(f"Could not extract playlist ID from: {url}")


def save(data: dict):
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nManifest saved → {MANIFEST}")


def load() -> dict:
    return json.loads(MANIFEST.read_text())


def get_album(id: str) -> dict:
    file = ALBUM_DIR / f"{id}.json"
    if file.exists():
        return json.loads(file.read_text())

    album = yt.get_album(id)
    ALBUM_DIR.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(album, indent=2, ensure_ascii=False))
    return album


def get_song(id: str) -> dict:
    """Fetch (and cache) the metadata of a song.

    ``id`` is either a YouTube ``videoId`` or a song credits ``browseId``
    (``MPTC...``) — both are cached on disk.
    """
    file = SONG_DIR / f"{id}.json"
    if file.exists():
        return json.loads(file.read_text())

    if id.startswith("MPTC"):
        song = yt.get_song_credits(id)
        song["creditsBrowseId"] = id
    else:
        song = yt.get_song(id)
        song["videoId"] = id

    SONG_DIR.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(song, indent=2, ensure_ascii=False))
    return song


def video_type_of(track: dict) -> str | None:
    """Normalize a track's ``videoType`` to its raw string value (or None)."""
    video_type = track.get("videoType") if isinstance(track, dict) else None
    if video_type is None:
        return None
    return video_type.value if isinstance(video_type, VideoType) else str(video_type)


def is_music_video(track: dict) -> bool:
    """True when the track points at a music video (e.g. ``MUSIC_VIDEO_TYPE_OMV``)
    instead of an actual audio track (``MUSIC_VIDEO_TYPE_ATV``)."""
    video_type = video_type_of(track)
    if video_type is None:
        return False
    # actual audio tracks (MUSIC_VIDEO_TYPE_ATV / MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC)
    # are saved directly; anything else (e.g. MUSIC_VIDEO_TYPE_OMV) is a music video
    return video_type not in AUDIO_VIDEO_TYPES


def get_music_video_audio(video_id: str) -> dict | None:
    """Music videos (``MUSIC_VIDEO_TYPE_OMV``) are videos, not audio tracks.
    Whenever we hit one, follow the watch page's related tracks to find the
    actual audio track (``MUSIC_VIDEO_TYPE_ATV``) that belongs to the same song."""
    try:
        watch = yt.get_watch_playlist(videoId=video_id)
    except Exception:
        return None

    related_id = watch.get("related") if isinstance(watch, dict) else None
    if not related_id:
        return None

    try:
        sections = yt.get_song_related(related_id) or []
    except Exception:
        return None

    candidates: list[dict] = []

    def collect(items) -> None:
        for item in items or []:
            if not isinstance(item, dict):
                continue
            if item.get("videoId"):
                candidates.append(item)
            collect(item.get("contents"))

    collect(sections)

    audio_track = next(
        (c for c in candidates if video_type_of(c) == MUSIC_VIDEO_TYPE_ATV),
        None,
    )
    chosen = audio_track or (candidates[0] if candidates else None)
    if chosen is not None and audio_track is not None:
        chosen["videoType"] = MUSIC_VIDEO_TYPE_ATV
    elif chosen is not None:
        # related tracks are not always parsed with a video type; fall back to the
        # first related track and treat it as the audio track of the music video
        chosen["videoType"] = chosen.get("videoType") or MUSIC_VIDEO_TYPE_ATV
    return chosen


# ─── Phase 1: resolve playlist → albums → songs ────────────────────


def phase_resolve(playlist_url: str) -> dict:
    pid = extract_playlist_id(playlist_url)
    playlist = yt.get_playlist(pid, limit=None)

    print(f"resolving playlist: {playlist.get('title', 'Unknown')} ({pid})")

    tracks = playlist.get("tracks") or []

    album_ids: set[str] = set()
    for t in tracks:
        ref = t.get("album") or {}
        if isinstance(ref, dict) and ref.get("id"):
            album_ids.add(ref["id"])

    albums: dict[str, dict | None] = {}
    for i, aid in enumerate(sorted(album_ids), 1):
        if i > 1:
            time.sleep(SPEED)
        try:
            albums[aid] = get_album(aid)
            album = albums[aid] or {}
            artists = ", ".join(a["name"] for a in album.get("artists") or [])
            print(
                f"  [{i}/{len(album_ids)}] ✓ {aid}  {album.get('title', 'Unknown')} — {artists}"
            )
        except Exception as e:
            albums[aid] = None
            print(f"  [{i}/{len(album_ids)}] ✗ {aid}  {e}")

    # index the fetched albums by videoId so we can save from the album
    # exactly the songs that are also part of the playlist
    album_tracks: dict[str, dict] = {}
    track_albums: dict[str, str] = {}
    for aid, album in sorted(albums.items()):
        if not album:
            continue
        for at in album.get("tracks") or []:
            avid = at.get("videoId")
            if not avid:
                continue
            album_tracks[avid] = at
            track_albums[avid] = aid

    manifest: list[dict] = []

    for idx, t in enumerate(tracks, 1):
        vid = t.get("videoId")
        track = album_tracks.get(vid) or t

        audio_vid = vid
        is_music = False
        music_video_of = None
        src = track

        if is_music_video(track):
            related = get_music_video_audio(vid)
            if related and related.get("videoId"):
                src = related
                audio_vid = related["videoId"]
                is_music = True
                music_video_of = vid
                print(
                    f"  [{idx}/{len(tracks)}] ♪ music video → audio track  "
                    f"{vid}  {t.get('title')}  →  {audio_vid}"
                )

        artists = [a["name"] for a in src.get("artists") or []]
        ref = src.get("album") or {}
        album_nm = ref.get("name") if isinstance(ref, dict) else ref
        album_art = None
        year = None
        track_tot = None
        track_no = None
        aid = track_albums.get(audio_vid) or track_albums.get(vid or "")
        album = albums.get(aid) if aid else None
        if album:
            album_nm = album.get("title") or album_nm
            album_art = ", ".join(a["name"] for a in album.get("artists") or [])
            year = album.get("year")
            track_tot = album.get("trackCount")
            # the audio track (ATV) may not be an album track itself, so fall back to the
            # music video (OMV) track for the shared metadata (e.g. track number)
            for at in album.get("tracks") or []:
                if at.get("videoId") not in (audio_vid, vid):
                    continue
                n = at.get("trackNumber")
                if n is not None:
                    track_no = n + 1
                    break

        manifest.append(
            {
                "index": idx,
                "videoId": audio_vid,
                "title": src.get("title") or t.get("title") or "Unknown",
                "artist": artists[0] if artists else "Unknown",
                "artists": artists,
                "album": album_nm or "Unknown",
                "albumArtist": album_art or (artists[0] if artists else "Unknown"),
                "trackNumber": track_no,
                "trackTotal": track_tot,
                "year": year,
                "duration": src.get("duration") or t.get("duration"),
                "durationSeconds": src.get("duration_seconds")
                or t.get("duration_seconds"),
                "isExplicit": bool(
                    src.get("isExplicit") or t.get("isExplicit") or False
                ),
                "isAvailable": src.get("isAvailable", t.get("isAvailable", True)),
                "videoType": video_type_of(src) or video_type_of(t),
                "isMusicVideo": is_music,
                "musicVideoOf": music_video_of,
                "creditsBrowseId": src.get("creditsBrowseId")
                or t.get("creditsBrowseId"),
            }
        )

        # cache the full song metadata (credits / player details) for the audio track we keep
        sid = src.get("creditsBrowseId") or t.get("creditsBrowseId") or audio_vid
        try:
            get_song(sid)
        except Exception as e:
            print(f"  [{idx}/{len(tracks)}] ✗ song {audio_vid}  {e}")

    data = {
        "playlistId": pid,
        "playlistTitle": playlist.get("title", "Unknown"),
        "totalTracks": len(tracks),
        "uniqueAlbums": len(album_ids),
        "tracks": manifest,
    }
    save(data)

    # quick summary
    with_no_album = sum(1 for m in manifest if m["trackNumber"] is None)
    music_vids = sum(1 for m in manifest if m.get("isMusicVideo"))
    print(
        f"\nResolved  : {len(manifest) - with_no_album}/{len(manifest)} "
        f"have track numbers"
    )
    if with_no_album:
        print(
            f"  ⚠  {with_no_album} tracks missing album/track# "
            f"(likely singles, uploads, or unavailable)"
        )
    if music_vids:
        print(
            f"  ♪  {music_vids} track(s) were music videos — swapped for audio tracks"
        )

    return data


# ─── Phase 2: fetch lyrics (optional) ─────────────────────────────


def phase_lyrics() -> dict:
    data = load()
    n = len(data["tracks"])

    print(f"\n{'=' * 60}")
    print(f"PHASE 2 — Fetch lyrics  ({n} tracks)")
    print(f"{'=' * 60}")

    for i, tr in enumerate(data["tracks"], 1):
        if i > 1:
            time.sleep(SPEED)
        vid = tr["videoId"]
        try:
            watch = yt.get_watch_playlist(vid)
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
                res = yt.get_lyrics(lyr_bid)
                if res and res.get("lyrics"):
                    raw = res["lyrics"]
                    if isinstance(raw, str):
                        tr["lyrics"] = raw
                    else:
                        tr["lyrics"] = "\n".join(ln.text for ln in raw)
                    tr["lyricsSource"] = res.get("source", "")
                    print(f"  [{i}/{n}] ✓ {tr['title']}")
                else:
                    tr["lyrics"] = None
                    print(f"  [{i}/{n}] — {tr['title']}  (none)")
            else:
                tr["lyrics"] = None
                print(f"  [{i}/{n}] — {tr['title']}  (no lyrics id)")
        except Exception as e:
            tr["lyrics"] = None
            print(f"  [{i}/{n}] ✗ {tr['title']}  {e}")

    save(data)
    got = sum(1 for t in data["tracks"] if t.get("lyrics"))
    print(f"\nLyrics: {got}/{n}")
    return data


# ─── Phase 3: download audio via yt-dlp ───────────────────────────


def phase_download() -> dict:
    data = load()
    n = len(data["tracks"])
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"PHASE 3 — Download audio  ({n} tracks)")
    print(f"{'=' * 60}")

    for i, tr in enumerate(data["tracks"], 1):
        vid = tr["videoId"]
        track_dir = RAW_DIR / vid
        audio_f = track_dir / "audio.m4a"

        if audio_f.exists():
            print(f"  [{i}/{n}] ⏭  {tr['title']}  (cached)")
            continue
        if not tr.get("isAvailable", True):
            print(f"  [{i}/{n}] ⏭  {tr['title']}  (unavailable)")
            continue
        if is_music_video(tr):
            # we only ever save actual audio tracks (ATVs); music videos themselves are skipped
            print(
                f"  [{i}/{n}] ⏭  {tr['title']}  "
                f"(music video → audio track {tr.get('musicVideoOf') or vid} not resolved)"
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
                print(f"  [{i}/{n}] ✓ {tr['title']}")
            else:
                err = (r.stderr or r.stdout or "").strip().splitlines()
                print(f"  [{i}/{n}] ✗ {tr['title']}  {err[-1] if err else 'err'}")
        except subprocess.TimeoutExpired:
            print(f"  [{i}/{n}] ⏱  {tr['title']}  (timeout)")
        except FileNotFoundError:
            print("ERROR: yt-dlp not found.  pip install yt-dlp")
            sys.exit(1)

    save(data)
    return data


# ─── CLI ───────────────────────────────────────────────────────────


def run():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "resolve":
        if len(sys.argv) < 3:
            print("Usage: python -m youtubemetadata.sync resolve <playlist_url>")
            sys.exit(1)
        phase_resolve(sys.argv[2])

    elif cmd == "lyrics":
        phase_lyrics()

    elif cmd == "download":
        phase_download()

    elif cmd == "sync":
        if len(sys.argv) < 3:
            print("Usage: python -m youtubemetadata.sync sync <playlist_url>")
            sys.exit(1)
        phase_resolve(sys.argv[2])
        phase_lyrics()
        phase_download()

    else:
        print(f"Unknown command: {cmd}\n")
        print(__doc__)
        sys.exit(1)
