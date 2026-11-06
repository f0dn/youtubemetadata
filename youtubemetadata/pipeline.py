"""YouTube Music metadata sync.

Phases:
    resolve   — collect all albums of a playlist and save every song that is also in it
    lyrics    — fetch lyrics for the resolved tracks (optional)
    download  — download the audio of the resolved tracks via yt-dlp

Usage:
    python -m youtubemetadata.pipeline resolve <playlist_url>
    python -m youtubemetadata.pipeline lyrics <playlist_url>
    python -m youtubemetadata.pipeline download <playlist_url>
    python -m youtubemetadata.pipeline full <playlist_url>
"""

import argparse
import sys

from youtubemetadata.phases import download, lyrics, resolve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtubemetadata",
        description="Include proper song metadata in YouTube Music.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser(
        "resolve",
        help="collect all albums of a playlist and save every song that is also in it",
    )
    sub.add_argument("playlist_url", help="YouTube playlist URL")

    sub = subparsers.add_parser("lyrics", help="fetch lyrics for the resolved tracks")
    sub.add_argument("playlist_url", help="YouTube playlist URL")

    sub = subparsers.add_parser(
        "download", help="download the audio of the resolved tracks via yt-dlp"
    )
    sub.add_argument("playlist_url", help="YouTube playlist URL")

    sub = subparsers.add_parser(
        "full", help="resolve, fetch lyrics and download audio for a playlist"
    )
    sub.add_argument("playlist_url", help="YouTube playlist URL")

    return parser


def run(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.command

    if cmd == "resolve":
        resolve.phase_resolve(args.playlist_url)
    elif cmd == "lyrics":
        lyrics.phase_lyrics(resolve.phase_resolve(args.playlist_url))
    elif cmd == "download":
        download.phase_download(resolve.phase_resolve(args.playlist_url))
    elif cmd == "full":
        resolution = resolve.phase_resolve(args.playlist_url)
        lyrics.phase_lyrics(resolution)
        download.phase_download(resolution)
    else:  # pragma: no cover - argparse enforces the choices above
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    run()
