#!/usr/bin/env python3
"""
spotify-flac-sync — sync Spotify playlists to local FLAC files.

Usage:
    python sync.py              # Run sync
    python sync.py --setup      # Re-run setup wizard
    python sync.py --dry-run    # Show what would be downloaded, don't download
    python sync.py --threshold 90       # Override fuzzy match threshold
    python sync.py --suggest-cleanup    # List orphan local files and offer to delete
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import print as rprint

from config import load_config, is_configured, CONFIG_PATH
from wizard import run_wizard
from spotify_client import fetch_hash_playlists, SpotifyPlaylist, SpotifyTrack
from local_scanner import build_local_index, find_playlist_folder
from matcher import find_missing_tracks, find_unmatched_local
from downloader import download_track, DeemixNotFoundError, DownloadError
from organizer import move_to_playlist_folder

console = Console()


@click.command()
@click.option("--setup", is_flag=True, help="Re-run setup wizard")
@click.option("--dry-run", is_flag=True, help="Show missing tracks without downloading")
@click.option("--threshold", default=None, type=int, help="Fuzzy match threshold (0-100, default 85)")
@click.option("--playlist", default=None, help="Sync only this playlist (partial name match)")
@click.option("--suggest-cleanup", is_flag=True, help="List local files with no Spotify match and offer to delete them")
def main(setup: bool, dry_run: bool, threshold: int | None, playlist: str | None, suggest_cleanup: bool) -> None:
    cfg = load_config()

    if setup or not is_configured(cfg):
        cfg = run_wizard()

    music_folder = Path(cfg["music_folder"])
    match_threshold = threshold or cfg.get("matching", {}).get("threshold", 85)
    arl = cfg["deezer"]["arl"]
    temp_dir = Path(cfg.get("download", {}).get("temp_dir", Path.home() / ".cache" / "flac-sync" / "downloads"))
    temp_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        f"[bold cyan]spotify-flac-sync[/bold cyan]\n"
        f"Music folder: [dim]{music_folder}[/dim]\n"
        f"Match threshold: [dim]{match_threshold}%[/dim]"
        + (" · [yellow]DRY RUN[/yellow]" if dry_run else ""),
        border_style="cyan",
    ))

    # --- Fetch Spotify playlists ---
    console.print("\n[bold]Fetching Spotify playlists...[/bold]")
    with console.status("Connecting to Spotify..."):
        try:
            playlists = fetch_hash_playlists(
                cfg["spotify"]["client_id"],
                cfg["spotify"]["client_secret"],
            )
        except Exception as e:
            console.print(f"[red]Spotify error: {e}[/red]")
            sys.exit(1)

    if not playlists:
        console.print("[yellow]No playlists starting with '#' found in your Spotify account.[/yellow]")
        sys.exit(0)

    # Filter by --playlist flag
    if playlist:
        playlists = [p for p in playlists if playlist.lower() in p.name.lower()]
        if not playlists:
            console.print(f"[red]No playlist matching '{playlist}' found.[/red]")
            sys.exit(1)

    console.print(f"Found [bold]{len(playlists)}[/bold] playlist(s) to sync.\n")

    # --- Scan + match ---
    summary_rows = []
    all_missing: list[tuple[SpotifyTrack, Path]] = []  # (track, playlist_folder)
    all_orphans: list[Path] = []  # local files with no Spotify match

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning playlists...", total=len(playlists))
        for pl in playlists:
            progress.update(task, description=f"Scanning {pl.name}...")
            folder = find_playlist_folder(music_folder, pl.name)
            local_index = build_local_index(folder)
            missing, matched = find_missing_tracks(pl.tracks, local_index, threshold=match_threshold)
            orphans = find_unmatched_local(local_index, matched) if suggest_cleanup else []

            summary_rows.append((pl.name, len(pl.tracks), len(matched), len(missing), len(orphans), folder))
            for track in missing:
                all_missing.append((track, folder))
            all_orphans.extend(orphans)

            progress.advance(task)

    # --- Print summary table ---
    table = Table(title="Sync Status", show_header=True, header_style="bold cyan")
    table.add_column("Playlist", style="bold")
    table.add_column("Total", justify="right")
    table.add_column("Present", justify="right", style="green")
    table.add_column("Missing", justify="right", style="red")
    if suggest_cleanup:
        table.add_column("Orphans", justify="right", style="yellow")
    table.add_column("Folder", style="dim", overflow="fold")

    for row in summary_rows:
        name, total, present, missing_count, orphan_count, folder = row
        cells = [name, str(total), str(present), str(missing_count)]
        if suggest_cleanup:
            cells.append(str(orphan_count) if orphan_count else "[dim]0[/dim]")
        cells.append(str(folder))
        table.add_row(*cells)

    console.print(table)

    total_missing = len(all_missing)
    if total_missing == 0 and not all_orphans:
        console.print("\n[green bold]Everything is in sync![/green bold]")
        return

    if total_missing > 0:
        console.print(f"\n[bold yellow]{total_missing} track(s) missing across all playlists.[/bold yellow]")

    # --- Orphan cleanup suggestion ---
    if suggest_cleanup and all_orphans:
        console.print(f"\n[bold yellow]{len(all_orphans)} local file(s) have no matching Spotify track:[/bold yellow]")
        for p in all_orphans:
            console.print(f"  [yellow]•[/yellow] [dim]{p.parent.name}/[/dim]{p.name}")

        if not dry_run:
            try:
                answer = input(f"\nDelete these {len(all_orphans)} file(s)? [y/N] ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                answer = ""
            if answer == "y":
                deleted = 0
                for p in all_orphans:
                    try:
                        p.unlink()
                        deleted += 1
                    except OSError as e:
                        console.print(f"  [red]Could not delete {p.name}:[/red] {e}")
                console.print(f"[green]Deleted {deleted} file(s).[/green]")
            else:
                console.print("[dim]Cleanup skipped.[/dim]")

    if total_missing == 0:
        return

    if dry_run:
        console.print("\n[dim]Dry run — listing missing tracks:[/dim]")
        for track, folder in all_missing:
            console.print(f"  [yellow]•[/yellow] {track.display} [dim]→ {folder.name}[/dim]")
        return

    # --- Confirm download ---
    try:
        answer = input(f"\nDownload {total_missing} missing track(s)? [y/N] ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Cancelled.[/yellow]")
        return

    if answer != "y":
        console.print("[yellow]Skipped.[/yellow]")
        return

    # --- Download ---
    success = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading...", total=total_missing)
        for i, (track, playlist_folder) in enumerate(all_missing, 1):
            progress.update(task, description=f"{track.display[:60]}...")
            try:
                downloaded = download_track(track.spotify_url, temp_dir, arl)
                if downloaded:
                    moved = move_to_playlist_folder(downloaded, playlist_folder)
                    success += len(moved)
                else:
                    console.print(f"\n  [yellow]No file returned for:[/yellow] {track.display}")
                    failed += 1
            except DeemixNotFoundError as e:
                console.print(f"\n[red]deemix not installed:[/red] {e}")
                sys.exit(1)
            except DownloadError as e:
                console.print(f"\n  [red]Failed:[/red] {track.display}\n  {e}")
                failed += 1
            progress.advance(task)

    console.print(f"\n[bold]Done.[/bold] Downloaded: [green]{success}[/green] · Failed: [red]{failed}[/red]")


if __name__ == "__main__":
    main()
