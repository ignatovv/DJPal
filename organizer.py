"""Move downloaded files into the correct playlist folder."""

import shutil
from pathlib import Path


def move_to_playlist_folder(downloaded_files: list[Path], playlist_folder: Path) -> list[Path]:
    """
    Move downloaded files into playlist_folder.
    Returns list of final destination paths.
    Skips silently if destination already exists (duplicate safety).
    """
    moved = []
    for src in downloaded_files:
        dest = playlist_folder / src.name
        if dest.exists():
            # Don't overwrite existing files
            continue
        shutil.move(str(src), str(dest))
        moved.append(dest)
    return moved
