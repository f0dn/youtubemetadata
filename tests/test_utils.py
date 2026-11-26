"""Tests for YouTubeMetadata URL / playlist-id utilities."""

import pytest

from youtubemetadata.utils import extract_playlist_id


def test_extract_playlist_id_from_query_param() -> None:
    assert extract_playlist_id("https://www.youtube.com/playlist?list=PLabc123") == "PLabc123"


def test_extract_playlist_id_from_path_segment() -> None:
    assert extract_playlist_id("https://www.youtube.com/playlist/PLxyz789") == "PLxyz789"


def test_extract_playlist_id_from_owner_prefix() -> None:
    assert extract_playlist_id("https://music.youtube.com/playlist/OLAK5def") == "OLAK5def"


def test_extract_playlist_id_raises_without_id() -> None:
    with pytest.raises(ValueError):
        extract_playlist_id("https://www.youtube.com/playlist")
