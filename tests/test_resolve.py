"""Phase 1 — resolve a playlist into album-backed song metadata."""

from youtubemetadata.models import Album, CreditSection, Playlist, SongCredits, Track
from youtubemetadata.phases import resolve as resolve_phase


class FakeService:
    def get_playlist(self, playlist_id: str):
        return Playlist.model_validate(
            {
                "title": "Test Playlist",
                "trackCount": 2,
                "duration_seconds": 600,
                "tracks": [
                    {
                        "videoId": "esom",
                        "title": "Empire State of Mind",
                        "artists": [{"name": "Jay-Z", "id": "UCjayz"}],
                        "album": {"name": "Album One", "id": "MPREb_123"},
                        "duration": "4:00",
                        "duration_seconds": 240,
                        "isAvailable": True,
                        "isExplicit": False,
                        "videoType": "MUSIC_VIDEO_TYPE_ATV",
                        "creditsBrowseId": "MPTCesom",
                    },
                    {
                        "videoId": "omv3",
                        "title": "Song Three",
                        "artists": [{"name": "Artist", "id": "UCabc"}],
                        "album": {"name": "Album One", "id": "MPREb_123"},
                        "duration": "3:00",
                        "duration_seconds": 180,
                        "isAvailable": True,
                        "isExplicit": False,
                        "videoType": "MUSIC_VIDEO_TYPE_OMV",
                        "creditsBrowseId": "MPTCsong3",
                    },
                ],
            }
        )

    def get_album(self, album_id: str):
        if album_id == "MPREb_123":
            return Album.model_validate(
                {
                    "title": "Album One",
                    "type": "Album",
                    "year": "2009",
                    "trackCount": 2,
                    "duration": "8:00",
                    "duration_seconds": 480,
                    "audioPlaylistId": "OLAK5uy_abc",
                    "artists": [{"name": "Jay-Z", "id": "UCjayz"}],
                    "tracks": [
                        {
                            "videoId": "esom",
                            "title": "Empire State of Mind",
                            "artists": [{"name": "Jay-Z", "id": "UCjayz"}],
                            "album": "Album One",
                            "duration": "4:00",
                            "duration_seconds": 240,
                            "trackNumber": 1,
                            "isAvailable": True,
                            "isExplicit": False,
                            "videoType": "MUSIC_VIDEO_TYPE_ATV",
                            "creditsBrowseId": "MPTCesom",
                        },
                        {
                            "videoId": "omv3",
                            "title": "Song Three",
                            "artists": [{"name": "Artist", "id": "UCabc"}],
                            "album": "Album One",
                            "duration": "3:00",
                            "duration_seconds": 180,
                            "trackNumber": 3,
                            "isAvailable": True,
                            "isExplicit": False,
                            "videoType": "MUSIC_VIDEO_TYPE_OMV",
                            "creditsBrowseId": "MPTCsong3",
                        },
                    ],
                }
            )
        return None

    def get_music_video_audio(
        self, video_id: str, omv_title: str | None = None, omv_artist: str | None = None
    ):
        if video_id == "omv3":
            return Track.model_validate(
                {
                    "videoId": "atv3",
                    "title": "Song Three",
                    "artists": [{"name": "Artist", "id": "UCabc"}],
                    "isAvailable": True,
                    "isExplicit": False,
                    "videoType": "MUSIC_VIDEO_TYPE_ATV",
                    "trackNumber": 3,
                    "creditsBrowseId": "MPTCsong3",
                }
            )
        return None

    def get_song(self, song_id: str):
        return SongCredits(
            performed_by=CreditSection(
                localized_title="Performed by", data=["Jay-Z", "Alicia Keys"]
            ),
            written_by=CreditSection(localized_title="Written by", data=["Jay-Z", "Alicia Keys"]),
            produced_by=CreditSection(localized_title="Produced by", data=["Various"]),
        )


class TwoAlbumService:
    """Playlist with 2 songs from 2 different albums; each album holds a second song."""

    def get_playlist(self, playlist_id: str):
        return Playlist.model_validate(
            {
                "title": "Two Album Playlist",
                "trackCount": 2,
                "duration_seconds": 600,
                "tracks": [
                    {
                        "videoId": "s1",
                        "title": "First Song",
                        "artists": [{"name": "Artist A", "id": "UCaa"}],
                        "album": {"name": "Album A", "id": "MPREb_aaa"},
                        "duration": "3:00",
                        "duration_seconds": 180,
                        "isAvailable": True,
                        "isExplicit": False,
                        "videoType": "MUSIC_VIDEO_TYPE_ATV",
                        "creditsBrowseId": "MPTCs1",
                    },
                    {
                        "videoId": "s2",
                        "title": "Second Song",
                        "artists": [{"name": "Artist B", "id": "UCbb"}],
                        "album": {"name": "Album B", "id": "MPREb_bbb"},
                        "duration": "3:00",
                        "duration_seconds": 180,
                        "isAvailable": True,
                        "isExplicit": False,
                        "videoType": "MUSIC_VIDEO_TYPE_ATV",
                        "creditsBrowseId": "MPTCs2",
                    },
                ],
            }
        )

    def get_album(self, album_id: str):
        if album_id == "MPREb_aaa":
            return Album.model_validate(
                {
                    "title": "Album A",
                    "type": "Album",
                    "year": "2020",
                    "trackCount": 2,
                    "duration": "6:00",
                    "duration_seconds": 360,
                    "audioPlaylistId": "OLAK5uy_aaa",
                    "artists": [{"name": "Artist A", "id": "UCaa"}],
                    "tracks": [
                        {
                            "videoId": "s1",
                            "title": "First Song",
                            "artists": [{"name": "Artist A", "id": "UCaa"}],
                            "album": "Album A",
                            "duration": "3:00",
                            "duration_seconds": 180,
                            "trackNumber": 1,
                            "isAvailable": True,
                            "isExplicit": False,
                            "videoType": "MUSIC_VIDEO_TYPE_ATV",
                            "creditsBrowseId": "MPTCs1",
                        },
                        {
                            "videoId": "s1b",
                            "title": "First Song (Acoustic)",
                            "artists": [{"name": "Artist A", "id": "UCaa"}],
                            "album": "Album A",
                            "duration": "2:30",
                            "duration_seconds": 150,
                            "trackNumber": 2,
                            "isAvailable": True,
                            "isExplicit": False,
                            "videoType": "MUSIC_VIDEO_TYPE_ATV",
                            "creditsBrowseId": "MPTCs1b",
                        },
                    ],
                }
            )
        if album_id == "MPREb_bbb":
            return Album.model_validate(
                {
                    "title": "Album B",
                    "type": "Album",
                    "year": "2021",
                    "trackCount": 2,
                    "duration": "6:00",
                    "duration_seconds": 360,
                    "audioPlaylistId": "OLAK5uy_bbb",
                    "artists": [{"name": "Artist B", "id": "UCbb"}],
                    "tracks": [
                        {
                            "videoId": "s2",
                            "title": "Second Song",
                            "artists": [{"name": "Artist B", "id": "UCbb"}],
                            "album": "Album B",
                            "duration": "3:00",
                            "duration_seconds": 180,
                            "trackNumber": 1,
                            "isAvailable": True,
                            "isExplicit": False,
                            "videoType": "MUSIC_VIDEO_TYPE_ATV",
                            "creditsBrowseId": "MPTCs2",
                        },
                        {
                            "videoId": "s2b",
                            "title": "Second Song (Live)",
                            "artists": [{"name": "Artist B", "id": "UCbb"}],
                            "album": "Album B",
                            "duration": "3:30",
                            "duration_seconds": 210,
                            "trackNumber": 2,
                            "isAvailable": True,
                            "isExplicit": False,
                            "videoType": "MUSIC_VIDEO_TYPE_ATV",
                            "creditsBrowseId": "MPTCs2b",
                        },
                    ],
                }
            )
        return None

    def get_music_video_audio(
        self, video_id: str, omv_title: str | None = None, omv_artist: str | None = None
    ):
        return None

    def get_song(self, song_id: str):
        return SongCredits(
            performed_by=CreditSection(localized_title="Performed by", data=["Artist A"]),
            written_by=CreditSection(localized_title="Written by", data=["Artist A"]),
            produced_by=CreditSection(localized_title="Produced by", data=["Various"]),
        )


def test_resolve_swaps_music_video_for_audio_track() -> None:
    resolution = resolve_phase.phase_resolve(
        "https://www.youtube.com/playlist?list=PLabc", service=FakeService()
    )
    entry = resolution.tracks[0]
    assert entry.videoId == "esom"
    assert entry.isMusicVideo is False
    assert entry.musicVideoOf is None

    mv_entry = resolution.tracks[1]
    assert mv_entry.isMusicVideo is True
    assert mv_entry.musicVideoOf == "omv3"
    assert mv_entry.videoId == "atv3"


def test_resolve_uses_song_credits_for_multiple_artists() -> None:
    resolution = resolve_phase.phase_resolve(
        "https://www.youtube.com/playlist?list=PLabc", service=FakeService()
    )
    entry = resolution.tracks[0]
    assert entry.artist == "Jay-Z"
    assert entry.artists == ["Jay-Z", "Alicia Keys"]
    assert entry.albumArtist == ["Jay-Z"]
    assert entry.albumDescription is None
    assert entry.trackNumber == 1
    assert entry.trackTotal == 2
    assert entry.writtenBy == ["Jay-Z", "Alicia Keys"]
    assert entry.producedBy == ["Various"]


def test_album_version_detection() -> None:
    assert resolve_phase._split_album_version("Song (Deluxe Version)") == ("Deluxe", "Song")
    assert resolve_phase._split_album_version("Song (Remastered)") == ("Remastered", "Song")
    assert resolve_phase._split_album_version("Song") == (None, "Song")
    assert resolve_phase._split_album_version(None) == (None, "")


def test_resolve_expands_playlist_to_all_album_songs() -> None:
    """A playlist with 2 songs from 2 albums resolves to all songs of both albums."""
    resolution = resolve_phase.phase_resolve(
        "https://www.youtube.com/playlist?list=PLabc", service=TwoAlbumService()
    )
    saved = {t.videoId: t for t in resolution.tracks}
    # every song of both albums made it into the resolution — nothing was skipped
    assert set(saved) == {"s1", "s1b", "s2", "s2b"}
    assert len(resolution.tracks) == 4

    first_song = saved["s1"]
    assert first_song.trackNumber == 1
    assert first_song.trackTotal == 2
    assert first_song.album == "Album A"

    acoustic = saved["s1b"]
    assert acoustic.trackNumber == 2
    assert acoustic.album == "Album A"

    second_song = saved["s2"]
    assert second_song.trackNumber == 1
    assert second_song.trackTotal == 2
    assert second_song.album == "Album B"

    live = saved["s2b"]
    assert live.trackNumber == 2
    assert live.album == "Album B"


def test_resolve_keeps_playlist_tracks_without_album_as_is() -> None:
    """Tracks that cannot be tied to an album (singles) are still resolved."""

    class SingleService:
        def get_playlist(self, playlist_id: str):
            return Playlist.model_validate(
                {
                    "title": "Singles",
                    "trackCount": 1,
                    "tracks": [
                        {
                            "videoId": "single1",
                            "title": "Lonely Song",
                            "artists": [{"name": "Artist C", "id": "UCC"}],
                            "duration": "3:00",
                            "duration_seconds": 180,
                            "isAvailable": True,
                            "isExplicit": False,
                            "videoType": "MUSIC_VIDEO_TYPE_ATV",
                            "creditsBrowseId": "MPTCsingle1",
                        },
                    ],
                }
            )

        def get_album(self, album_id: str):
            return None

        def get_music_video_audio(self, video_id: str, omv_title=None, omv_artist=None):
            return None

        def get_song(self, song_id: str):
            return None

    resolution = resolve_phase.phase_resolve(
        "https://www.youtube.com/playlist?list=PLabc", service=SingleService()
    )
    assert len(resolution.tracks) == 1
    entry = resolution.tracks[0]
    assert entry.videoId == "single1"
    assert entry.isAvailable is True
