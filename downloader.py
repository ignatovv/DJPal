"""Download tracks via deemix using Spotify track URLs."""

import shutil
import subprocess
import time
from pathlib import Path


class DeemixNotFoundError(Exception):
    pass


class DownloadError(Exception):
    pass


def _check_deemix() -> str:
    """Return path to deemix binary or raise."""
    binary = shutil.which("deemix")
    if not binary:
        raise DeemixNotFoundError(
            "deemix not found. Install it with: pip install deemix\n"
            "Then ensure it's on your PATH."
        )
    return binary


def download_track(spotify_url: str, output_dir: Path, arl: str) -> list[Path]:
    """
    Download a single track via deemix. Returns list of .flac (or .mp3) files created.
    Raises DownloadError on failure.
    """
    binary = _check_deemix()
    output_dir.mkdir(parents=True, exist_ok=True)

    before = set(output_dir.rglob("*"))

    result = subprocess.run(
        [binary, "--arl", arl, "--path", str(output_dir), spotify_url],
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        raise DownloadError(
            f"deemix exited with code {result.returncode}:\n{result.stderr.strip()}"
        )

    after = set(output_dir.rglob("*"))
    new_files = [
        p for p in (after - before)
        if p.is_file() and p.suffix.lower() in (".flac", ".mp3")
    ]
    return new_files
