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
    assert entry.trackNumber == 1
    assert entry.trackTotal == 2
    assert entry.writtenBy == ["Jay-Z", "Alicia Keys"]
    assert entry.producedBy == ["Various"]
