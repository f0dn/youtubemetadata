"""Storage locations for cached / downloaded / generated YouTube Music metadata."""

import os
from pathlib import Path

# XDG cache home (~/.cache on Linux, ~/Library/Caches on macOS, %LOCALAPPDATA% on Windows),
# with a `youtubemetadata` subdirectory holding all of our artifacts.
CACHE_ROOT = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "youtubemetadata"

RAW_DIR = CACHE_ROOT / "raw"
METADATA_DIR = CACHE_ROOT / "metadata"
ALBUM_DIR = METADATA_DIR / "albums"
SONG_DIR = METADATA_DIR / "songs"
