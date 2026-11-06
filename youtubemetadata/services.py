"""YouTube Music service: typed access to ytmusicapi with caching of raw metadata."""

import time

from ytmusicapi import YTMusic
from ytmusicapi.models.content.enums import VideoType

from youtubemetadata.cache import load_album, load_song, save_album, save_song
from youtubemetadata.models import Album, Playlist, SongCredits, SongPlayback, Track

MUSIC_VIDEO_TYPE_OMV = VideoType.OMV.value
MUSIC_VIDEO_TYPE_UGC = VideoType.UGC.value
MUSIC_VIDEO_TYPE_ATV = VideoType.ATV.value
MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC = VideoType.OFFICIAL_SOURCE_MUSIC.value

AUDIO_VIDEO_TYPES = frozenset(
    {MUSIC_VIDEO_TYPE_ATV, MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC}
)

SPEED = 0.5  # seconds between API calls (be nice to YouTube)


def is_music_video(track: Track) -> bool:
    """True when the track points at a music video (e.g. ``MUSIC_VIDEO_TYPE_OMV``)
    instead of an actual audio track (``MUSIC_VIDEO_TYPE_ATV``)."""
    if track.videoType is None:
        return False
    # actual audio tracks (MUSIC_VIDEO_TYPE_ATV / MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC)
    # are saved directly; anything else (e.g. MUSIC_VIDEO_TYPE_OMV) is a music video
    return track.videoType not in AUDIO_VIDEO_TYPES


class YouTubeMusicService:
    """Typed wrapper around ``ytmusicapi`` with a disk cache for raw metadata responses."""

    def __init__(self) -> None:
        self.yt = YTMusic()

    # ─── playlists (not cached — derived per run) ────────────────────

    def get_playlist(self, playlist_id: str) -> Playlist:
        time.sleep(SPEED)
        return Playlist.model_validate(self.yt.get_playlist(playlist_id, limit=None))

    def get_watch_playlist(self, video_id: str) -> dict:
        time.sleep(SPEED)
        return self.yt.get_watch_playlist(videoId=video_id)

    def get_lyrics(self, browse_id: str) -> dict | None:
        time.sleep(SPEED)
        return self.yt.get_lyrics(browse_id)

    # ─── albums (cached raw responses) ───────────────────────────────

    def get_album(self, album_id: str) -> Album:
        raw = load_album(album_id)
        if raw is None:
            time.sleep(SPEED)
            raw = self.yt.get_album(album_id)
            save_album(album_id, raw)
        return Album.model_validate(raw)

    # ─── songs (cached raw responses) ─────────────────────────────────

    def get_song_credits(self, browse_id: str) -> SongCredits:
        raw = load_song(browse_id)
        if raw is None:
            time.sleep(SPEED)
            raw = self.yt.get_song_credits(browse_id)
            save_song(browse_id, raw)
        return SongCredits.model_validate(raw)

    def get_song_by_video_id(self, video_id: str) -> SongPlayback:
        raw = load_song(video_id)
        if raw is None:
            time.sleep(SPEED)
            raw = self.yt.get_song(video_id)
            save_song(video_id, raw)
        return SongPlayback.model_validate(raw)

    def get_song(self, song_id: str) -> SongCredits | SongPlayback:
        """Get a song's credits or playback metadata. ``song_id`` is either a credits
        browse id (``MPTC...``) or a YouTube ``videoId``."""
        if song_id.startswith("MPTC"):
            return self.get_song_credits(song_id)
        return self.get_song_by_video_id(song_id)

    # ─── music videos → audio tracks ─────────────────────────────────

    def get_music_video_audio(self, video_id: str) -> Track | None:
        """Music videos (``MUSIC_VIDEO_TYPE_OMV``) are videos, not audio tracks.
        Whenever we hit one, follow the watch page's related tracks to find the
        actual audio track (``MUSIC_VIDEO_TYPE_ATV``) that belongs to the same song."""
        try:
            watch = self.get_watch_playlist(video_id)
        except Exception:
            return None

        related_id = watch.get("related") if isinstance(watch, dict) else None
        if not related_id:
            return None

        try:
            time.sleep(SPEED)
            sections = self.yt.get_song_related(related_id) or []
        except Exception:
            return None

        candidates: list[Track] = []

        def collect(items) -> None:
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                if item.get("videoId"):
                    candidates.append(Track.model_validate(item))
                collect(item.get("contents"))

        collect(sections)

        audio_track = next(
            (c for c in candidates if c.videoType == MUSIC_VIDEO_TYPE_ATV), None
        )
        chosen = audio_track or (candidates[0] if candidates else None)
        if chosen is None:
            return None
        if audio_track is None:
            # related tracks are not always parsed with a video type; fall back to the
            # first related track and treat it as the audio track of the music video
            chosen = chosen.model_copy(update={"videoType": MUSIC_VIDEO_TYPE_ATV})
        return chosen
