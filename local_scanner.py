"""Scan local music folder and build a normalized index of .flac files."""

import re
from pathlib import Path

from rapidfuzz import fuzz, process
from unidecode import unidecode


# Words stripped from filenames *only for matching* (not from stored names)
_FILLER_PATTERN = re.compile(
    r"\b(original mix|extended mix|extended version|radio edit|club mix|"
    r"radio mix|album version|remaster(?:ed)?|remastered version)\b",
    re.IGNORECASE,
)

_LEADING_NUMBER_PATTERN = re.compile(r"^\d+[\s.\-_]+")
_MULTI_SPACE = re.compile(r"\s+")
_NON_ALPHANUM = re.compile(r"[^\w\s]")


def normalize(text: str) -> str:
    """Normalize a string for fuzzy comparison."""
    text = unidecode(text)
    text = text.lower()
    text = _FILLER_PATTERN.sub(" ", text)
    text = _LEADING_NUMBER_PATTERN.sub("", text)
    text = _NON_ALPHANUM.sub(" ", text)
    text = _MULTI_SPACE.sub(" ", text)
    return text.strip()


def find_playlist_folder(music_folder: Path, playlist_name: str) -> Path:
    """Return the local folder for a playlist, creating it if needed."""
    # Exact match first
    exact = music_folder / playlist_name
    if exact.exists():
        return exact

    # Fuzzy match against existing folders (handles minor naming differences)
    existing = [d for d in music_folder.iterdir() if d.is_dir()]
    if existing:
        names = [d.name for d in existing]
        match = process.extractOne(
            playlist_name, names, scorer=fuzz.token_set_ratio, score_cutoff=80
        )
        if match:
            matched_name, score, _ = match
            return music_folder / matched_name

    # Create folder
    exact.mkdir(parents=True, exist_ok=True)
    return exact


def build_local_index(folder: Path) -> dict[str, Path]:
    """
    Scan folder for .flac files. Returns {normalized_name: path}.
    Normalized name = full filename (without extension) after normalization.
    """
    index = {}
    for f in folder.rglob("*.flac"):
        key = normalize(f.stem)
        index[key] = f
    return index
