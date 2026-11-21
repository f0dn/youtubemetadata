"""Tests for the YouTube Music service helpers."""

from youtubemetadata.models import Track
from youtubemetadata.services import is_music_video


def test_is_music_video_official_source_music_is_audio() -> None:
    track = Track.model_validate(
        {
            "videoId": "v1",
            "title": "Song",
            "videoType": "MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC",
        }
    )
    assert is_music_video(track) is False


def test_is_music_video_atv_is_audio() -> None:
    track = Track.model_validate(
        {"videoId": "v1", "title": "Song", "videoType": "MUSIC_VIDEO_TYPE_ATV"}
    )
    assert is_music_video(track) is False


def test_is_music_video_omv_is_music_video() -> None:
    track = Track.model_validate(
        {"videoId": "v1", "title": "Song", "videoType": "MUSIC_VIDEO_TYPE_OMV"}
    )
    assert is_music_video(track) is True


def test_is_music_video_without_type_is_not_music_video() -> None:
    track = Track.model_validate({"videoId": "v1", "title": "Song"})
    assert is_music_video(track) is False
