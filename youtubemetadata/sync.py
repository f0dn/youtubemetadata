"""YouTube Music metadata sync.

Phases:
    resolve   — collect all albums of a playlist and save every song that is also in it
    lyrics    — fetch lyrics for the resolved tracks (optional)
    download  — download the audio of the resolved tracks via yt-dlp

Usage:
    python -m youtubemetadata.sync resolve <playlist_url>
    python -m youtubemetadata.sync lyrics <playlist_url>
    python -m youtubemetadata.sync download <playlist_url>
    python -m youtubemetadata.sync sync <playlist_url>
"""

import sys

from youtubemetadata.phases import download, lyrics, resolve


def run() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "resolve":
        if len(sys.argv) < 3:
            print("Usage: python -m youtubemetadata.sync resolve <playlist_url>")
            sys.exit(1)
        resolve.phase_resolve(sys.argv[2])

    elif cmd == "lyrics":
        if len(sys.argv) < 3:
            print("Usage: python -m youtubemetadata.sync lyrics <playlist_url>")
            sys.exit(1)
        lyrics.phase_lyrics(resolve.phase_resolve(sys.argv[2]))

    elif cmd == "download":
        if len(sys.argv) < 3:
            print("Usage: python -m youtubemetadata.sync download <playlist_url>")
            sys.exit(1)
        download.phase_download(resolve.phase_resolve(sys.argv[2]))

    elif cmd == "sync":
        if len(sys.argv) < 3:
            print("Usage: python -m youtubemetadata.sync sync <playlist_url>")
            sys.exit(1)
        resolution = resolve.phase_resolve(sys.argv[2])
        lyrics.phase_lyrics(resolution)
        download.phase_download(resolution)

    else:
        print(f"Unknown command: {cmd}\n")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    run()
