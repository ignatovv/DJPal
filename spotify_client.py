"""Fetch Spotify playlists and their tracks using the Spotify API."""

from dataclasses import dataclass, field
from typing import Iterator

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials


@dataclass
class SpotifyTrack:
    name: str
    artists: list[str]
    spotify_url: str
    duration_ms: int

    @property
    def display(self) -> str:
        return f"{', '.join(self.artists)} — {self.name}"


@dataclass
class SpotifyPlaylist:
    name: str
    playlist_id: str
    tracks: list[SpotifyTrack] = field(default_factory=list)


def _make_client(client_id: str, client_secret: str) -> spotipy.Spotify:
    """Client credentials flow — no user login needed for reading public playlists.
    For private playlists, falls back to OAuth."""
    auth = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth)


def _make_oauth_client(client_id: str, client_secret: str) -> spotipy.Spotify:
    auth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:8080",
        scope="playlist-read-private playlist-read-collaborative",
        cache_path=str(__import__("pathlib").Path.home() / ".cache" / "flac-sync" / ".spotify_token"),
    )
    return spotipy.Spotify(auth_manager=auth)


def fetch_hash_playlists(client_id: str, client_secret: str) -> list[SpotifyPlaylist]:
    """Return all playlists whose name starts with '#'."""
    sp = _make_oauth_client(client_id, client_secret)

    playlists = []
    result = sp.current_user_playlists(limit=50)
    while result:
        for item in result["items"]:
            if item and item["name"].startswith("#"):
                playlists.append(SpotifyPlaylist(name=item["name"], playlist_id=item["id"]))
        result = sp.next(result) if result["next"] else None

    for playlist in playlists:
        playlist.tracks = list(_fetch_tracks(sp, playlist.playlist_id))

    return playlists


def _fetch_tracks(sp: spotipy.Spotify, playlist_id: str) -> Iterator[SpotifyTrack]:
    result = sp.playlist_tracks(playlist_id, fields="items,next,total")
    while result:
        for item in result["items"]:
            track = item.get("track")
            if not track or track.get("is_local"):
                continue
            external = track.get("external_urls", {})
            url = external.get("spotify", "")
            if not url:
                continue
            artists = [a["name"] for a in track.get("artists", [])]
            yield SpotifyTrack(
                name=track["name"],
                artists=artists,
                spotify_url=url,
                duration_ms=track.get("duration_ms", 0),
            )
        result = sp.next(result) if result.get("next") else None
