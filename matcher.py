"""Fuzzy match Spotify tracks against local .flac file index."""

from pathlib import Path

from rapidfuzz import fuzz, process

from local_scanner import normalize
from spotify_client import SpotifyTrack


def _track_search_string(track: SpotifyTrack) -> str:
    """Build a normalized search string from Spotify track metadata."""
    parts = track.artists + [track.name]
    return normalize(" ".join(parts))


def find_missing_tracks(
    tracks: list[SpotifyTrack],
    local_index: dict[str, Path],
    threshold: int = 85,
) -> tuple[list[SpotifyTrack], dict[SpotifyTrack, Path]]:
    """
    Returns:
        missing: tracks not found locally
        matched: {track: local_path} for tracks that are present
    """
    if not local_index:
        return tracks, {}

    local_keys = list(local_index.keys())
    missing = []
    matched = {}

    for track in tracks:
        query = _track_search_string(track)
        result = process.extractOne(
            query,
            local_keys,
            scorer=fuzz.token_set_ratio,
            score_cutoff=threshold,
        )
        if result:
            best_key, score, _ = result
            matched[track] = local_index[best_key]
        else:
            missing.append(track)

    return missing, matched


def find_unmatched_local(
    local_index: dict[str, Path],
    matched: dict[SpotifyTrack, Path],
) -> list[Path]:
    """Return local files that didn't match any Spotify track in this playlist."""
    matched_paths = set(matched.values())
    return [p for p in local_index.values() if p not in matched_paths]
