"""CLI tests for the pipeline."""

from youtubemetadata.pipeline import build_parser


def test_parser_accepts_resolve_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["resolve", "https://www.youtube.com/playlist?list=PLabc"])
    assert args.command == "resolve"
    assert args.playlist_url == "https://www.youtube.com/playlist?list=PLabc"


def test_parser_accepts_full_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["full", "https://music.youtube.com/playlist?list=PLGuOJ7hPNiJA"])
    assert args.command == "full"
    assert args.playlist_url == "https://music.youtube.com/playlist?list=PLGuOJ7hPNiJA"


def test_parser_rejects_unknown_subcommand() -> None:
    import pytest

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["bogus", "https://www.youtube.com/playlist?list=PLabc"])
