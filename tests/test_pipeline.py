"""CLI tests for the pipeline."""

from unittest.mock import MagicMock, patch

from youtubemetadata.pipeline import build_parser, run


def test_parser_accepts_playlist_and_library() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["https://www.youtube.com/playlist?list=PLabc", "/tmp/navidrome-library"]
    )
    assert args.playlist_url == "https://www.youtube.com/playlist?list=PLabc"
    assert args.library_path == "/tmp/navidrome-library"


def test_run_resolves_lyrics_downloads_and_writes_library() -> None:
    resolution = MagicMock()
    with (
        patch(
            "youtubemetadata.pipeline.resolve.phase_resolve", return_value=resolution
        ) as mock_resolve,
        patch("youtubemetadata.pipeline.lyrics.phase_lyrics") as mock_lyrics,
        patch("youtubemetadata.pipeline.download.phase_download") as mock_download,
        patch("youtubemetadata.pipeline.library.phase_library") as mock_library,
    ):
        run(["https://www.youtube.com/playlist?list=PLabc", "/tmp/navidrome-library"])

    mock_resolve.assert_called_once_with("https://www.youtube.com/playlist?list=PLabc")
    mock_lyrics.assert_called_once_with(resolution)
    mock_download.assert_called_once_with(resolution)
    mock_library.assert_called_once_with(resolution, "/tmp/navidrome-library")
