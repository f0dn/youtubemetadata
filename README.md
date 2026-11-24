# YouTube Metadata Enhancer

Include proper song metadata in YouTube Music.

## Usage

Resolve a playlist, fetch lyrics and download tagged audio into a
[Navidrome](https://navidrome.org) music library:

```bash
python -m youtubemetadata.pipeline <playlist_url> <library_path>
```

For example:

```bash
python -m youtubemetadata.pipeline "https://music.youtube.com/playlist?list=PLGuOJ7hPNiJA" /path/to/navidrome/library
```

The CLI runs the full flow:

1. **resolve** — collect all albums of the playlist and pick the songs that are also in it
2. **lyrics** — fetch lyrics for the resolved tracks (optional)
3. **download** — download the audio of the resolved tracks via `yt-dlp`
4. **library** — write the tracks into a Navidrome-compatible library at the given path
   (artist / album / song directory structure + audio file tags)

The Navidrome library directory is cleared before the new library is written.
