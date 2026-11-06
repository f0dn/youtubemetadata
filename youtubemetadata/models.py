"""Typed models for YouTube Music metadata (pydantic)."""

from typing import Any

from pydantic import BaseModel, Field


class Artist(BaseModel):
    name: str | None = None
    id: str | None = None


class AlbumRef(BaseModel):
    name: str | None = None
    id: str | None = None


class CommunityVoteStatus(BaseModel):
    netVoteValue: int | None = None
    status: str | None = None


class Track(BaseModel):
    """A track as encountered in playlists, albums or related tracks."""

    videoId: str | None = None
    title: str | None = None
    artists: list[Artist] = Field(default_factory=list)
    # album tracks use the album *title* (str), playlist tracks use {"name", "id"}
    album: AlbumRef | str | None = None
    isAvailable: bool = True
    isExplicit: bool = False
    duration: str | None = None
    duration_seconds: int | None = None
    trackNumber: int | None = None
    creditsBrowseId: str | None = None
    videoType: str | None = None
    views: str | None = None
    inLibrary: bool | None = None
    pinnedToListenAgain: bool | None = None
    feedbackTokens: dict[str, Any] | None = None
    listenAgainFeedbackTokens: dict[str, Any] | None = None
    communityVoteStatus: CommunityVoteStatus | None = None
    thumbnails: list[dict[str, Any]] | None = None
    year: int | str | None = None


class Album(BaseModel):
    """Full album metadata as returned by ``ytmusicapi.get_album``."""

    title: str | None = None
    type: str | None = None
    description: str | None = None
    artists: list[Artist] = Field(default_factory=list)
    year: int | str | None = None
    trackCount: int | None = None
    duration: str | None = None
    duration_seconds: int | None = None
    audioPlaylistId: str | None = None
    tracks: list[Track] = Field(default_factory=list)
    thumbnails: list[dict[str, Any]] | None = None
    other_versions: list[Any] = Field(default_factory=list)


class CreditSection(BaseModel):
    localized_title: str | None = None
    data: list[str] = Field(default_factory=list)


class SongCredits(BaseModel):
    """Credits of a song, as returned by ``ytmusicapi.get_song_credits``."""

    performed_by: CreditSection | None = None
    written_by: CreditSection | None = None
    produced_by: CreditSection | None = None
    music_metadata_provided_by: CreditSection | None = None
    other_sections: list[CreditSection] = Field(default_factory=list)


class VideoDetails(BaseModel):
    videoId: str | None = None
    title: str | None = None
    lengthSeconds: str | None = None
    channelId: str | None = None
    author: str | None = None
    isOwnerViewing: bool = False
    isCrawlable: bool = False
    isPrivate: bool = False
    isUnpluggedCorpus: bool = False
    musicVideoType: str | None = None
    isLiveContent: bool = False
    viewCount: str | None = None


class SongPlayback(BaseModel):
    """Player response of a song / music video, as returned by ``ytmusicapi.get_song``."""

    videoDetails: VideoDetails | None = None
    playabilityStatus: dict[str, Any] | None = None
    streamingData: dict[str, Any] | None = None
    microformat: dict[str, Any] | None = None
    playbackTracking: dict[str, Any] | None = None


class Playlist(BaseModel):
    """Playlist as returned by ``ytmusicapi.get_playlist``."""

    owned: bool = False
    id: str | None = None
    privacy: str | None = None
    description: str | None = None
    views: int | None = None
    duration: str | None = None
    duration_seconds: int | None = None
    trackCount: int | None = None
    title: str | None = None
    thumbnails: list[dict[str, Any]] | None = None
    year: int | str | None = None
    tracks: list[Track] = Field(default_factory=list)
    suggestions: list[Track] = Field(default_factory=list)
    related: list[Any] = Field(default_factory=list)


class TrackEntry(BaseModel):
    """A resolved playlist track: derived metadata used for saving / downloading."""

    index: int
    videoId: str = ""
    title: str = "Unknown"
    artist: str = "Unknown"
    artists: list[str] = Field(default_factory=list)
    album: str = "Unknown"
    albumArtist: str = "Unknown"
    trackNumber: int | None = None
    trackTotal: int | None = None
    year: int | str | None = None
    duration: str | None = None
    durationSeconds: int | None = None
    isExplicit: bool = False
    isAvailable: bool = True
    videoType: str | None = None
    isMusicVideo: bool = False
    musicVideoOf: str | None = None
    creditsBrowseId: str | None = None
    lyrics: str | None = None
    lyricsSource: str | None = None


class PlaylistResolution(BaseModel):
    """Everything gathered for one playlist."""

    playlistId: str
    playlistTitle: str = "Unknown"
    totalTracks: int = 0
    uniqueAlbums: int = 0
    tracks: list[TrackEntry] = Field(default_factory=list)
