"""Phase 1 — resolve a playlist into album-backed song metadata."""

from youtubemetadata.models import (
    Album,
    AlbumRef,
    PlaylistResolution,
    Track,
    TrackEntry,
)
from youtubemetadata.services import YouTubeMusicService, is_music_video
from youtubemetadata.utils import extract_playlist_id


def phase_resolve(
    playlist_url: str, service: YouTubeMusicService | None = None
) -> PlaylistResolution:
    """Collect all albums of a playlist and save (cache) every song that is also in it.

    Music videos encountered along the way are swapped for their actual audio track.
    """
    svc = service or YouTubeMusicService()
    pid = extract_playlist_id(playlist_url)
    playlist = svc.get_playlist(pid)

    print(f"resolving playlist: {playlist.title or 'Unknown'} ({pid})")

    tracks: list[Track] = playlist.tracks

    album_ids: set[str] = set()
    for t in tracks:
        if t.album and t.album.id:
            album_ids.add(t.album.id)

    albums: dict[str, Album | None] = {}
    for i, aid in enumerate(sorted(album_ids), 1):
        try:
            album = svc.get_album(aid)
            albums[aid] = album
            artists = ", ".join(a.name or "" for a in album.artists if a.name)
            print(
                f"  [{i}/{len(album_ids)}] ✓ {aid}  {album.title or 'Unknown'} — {artists}"
            )
        except Exception as e:
            albums[aid] = None
            print(f"  [{i}/{len(album_ids)}] ✗ {aid}  {e}")

    # index the fetched albums by videoId so we can save from the album
    # exactly the songs that are also part of the playlist
    album_tracks: dict[str, Track] = {}
    track_albums: dict[str, str] = {}
    for aid, album in sorted(albums.items()):
        if album is None:
            continue
        for at in album.tracks:
            if at.videoId:
                album_tracks[at.videoId] = at
                track_albums[at.videoId] = aid

    entries: list[TrackEntry] = []

    for idx, t in enumerate(tracks, 1):
        vid = t.videoId
        track = album_tracks.get(vid) or t

        audio_vid = vid
        is_music = False
        music_video_of = None
        src = track

        if is_music_video(track):
            related = svc.get_music_video_audio(vid)
            if related is not None and related.videoId:
                src = related
                audio_vid = related.videoId
                is_music = True
                music_video_of = vid
                print(
                    f"  [{idx}/{len(tracks)}] ♪ music video → audio track  {vid}  {t.title}  →  {audio_vid}"
                )

        artists = [a.name or "" for a in src.artists]
        artist_names = [a for a in artists if a]
        artist = artist_names[0] if artist_names else "Unknown"

        raw_album = src.album
        album_nm = (
            raw_album.name
            if isinstance(raw_album, AlbumRef)
            else (raw_album if isinstance(raw_album, str) else None)
        )
        album_art = None
        year = None
        track_tot = None
        track_no = None
        aid = track_albums.get(audio_vid) or track_albums.get(vid or "")
        album = albums.get(aid) if aid else None
        if album is not None:
            album_nm = album.title or album_nm
            album_art = ", ".join(a.name or "" for a in album.artists if a.name) or None
            year = album.year
            track_tot = album.trackCount
            # the audio track (ATV) may not be an album track itself, so fall back to the
            # music video (OMV) track for the shared metadata (e.g. track number)
            for at in album.tracks:
                if at.videoId not in (audio_vid, vid):
                    continue
                if at.trackNumber is not None:
                    track_no = at.trackNumber + 1
                    break

        entries.append(
            TrackEntry(
                index=idx,
                videoId=audio_vid or "",
                title=src.title or t.title or "Unknown",
                artist=artist,
                artists=artist_names,
                album=album_nm or "Unknown",
                albumArtist=album_art or artist,
                trackNumber=track_no,
                trackTotal=track_tot,
                year=year,
                duration=src.duration or t.duration,
                durationSeconds=src.duration_seconds or t.duration_seconds,
                isExplicit=bool(src.isExplicit or t.isExplicit),
                isAvailable=src.isAvailable or t.isAvailable,
                videoType=src.videoType or t.videoType,
                isMusicVideo=is_music,
                musicVideoOf=music_video_of,
                creditsBrowseId=src.creditsBrowseId or t.creditsBrowseId,
            )
        )

        # cache the full song metadata (credits / player details) for the audio track we keep
        sid = src.creditsBrowseId or t.creditsBrowseId or audio_vid
        try:
            svc.get_song(sid)
        except Exception as e:
            print(f"  [{idx}/{len(tracks)}] ✗ song {audio_vid}  {e}")

    resolution = PlaylistResolution(
        playlistId=pid,
        playlistTitle=playlist.title or "Unknown",
        totalTracks=len(tracks),
        uniqueAlbums=len(album_ids),
        tracks=entries,
    )

    # quick summary
    with_no_album = sum(1 for m in resolution.tracks if m.trackNumber is None)
    music_vids = sum(1 for m in resolution.tracks if m.isMusicVideo)
    print(
        f"\nResolved  : {len(resolution.tracks) - with_no_album}/{len(resolution.tracks)} "
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

    return resolution
