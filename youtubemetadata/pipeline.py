"""YouTube Music metadata → Navidrome library.

Phases:
    resolve   — collect all albums of a playlist and save every song that is also in it
    lyrics    — fetch lyrics for the resolved tracks (optional)
    download  — download the audio of the resolved tracks via yt-dlp
    library   — write the resolved tracks into a Navidrome-compatible library

Usage:
    python -m youtubemetadata.pipeline <playlist_url> <library_path>
"""

import argparse

from youtubemetadata.phases import download, library, lyrics, resolve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtubemetadata",
        description="Include proper song metadata in YouTube Music.",
    )
    parser.add_argument("playlist_url", help="YouTube playlist URL")
    parser.add_argument("library_path", help="path to the Navidrome library directory to write to")
    return parser


def run(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    resolution = resolve.phase_resolve(args.playlist_url)
    lyrics.phase_lyrics(resolution)
    download.phase_download(resolution)
    lib = library.phase_library(resolution, args.library_path)
    print(f"\nNavidrome library written → {lib}")


if __name__ == "__main__":
    run()
