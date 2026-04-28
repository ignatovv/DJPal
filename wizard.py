"""First-run setup wizard. Collects credentials, validates connections, saves config."""

from pathlib import Path

import requests
import spotipy
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from spotipy.oauth2 import SpotifyOAuth

from config import DEFAULT_CONFIG, save_config

console = Console()


def _ask(prompt: str, default: str = "", password: bool = False) -> str:
    value = Prompt.ask(prompt, default=default or None, password=password)
    return (value or "").strip()


def _validate_music_folder(path_str: str) -> Path | None:
    p = Path(path_str).expanduser()
    if p.exists() and p.is_dir():
        return p
    return None


def _validate_spotify(client_id: str, client_secret: str) -> bool:
    try:
        auth = spotipy.oauth2.SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth)
        sp.search("test", limit=1)
        return True
    except Exception:
        return False


def _validate_deezer_arl(arl: str) -> bool:
    try:
        resp = requests.get(
            "https://www.deezer.com/ajax/gw-light.php",
            params={"method": "deezer.getUserData", "input": "3", "api_version": "1.0", "api_token": "null"},
            cookies={"arl": arl},
            timeout=10,
        )
        data = resp.json()
        return bool(data.get("results", {}).get("USER", {}).get("USER_ID"))
    except Exception:
        return False


def run_wizard() -> dict:
    console.print(
        Panel.fit(
            "[bold cyan]spotify-flac-sync setup[/bold cyan]\n"
            "This wizard will configure the sync tool.\n"
            "Run again anytime with [bold]python sync.py --setup[/bold]",
            border_style="cyan",
        )
    )

    cfg = dict(DEFAULT_CONFIG)
    cfg["spotify"] = dict(DEFAULT_CONFIG["spotify"])
    cfg["deezer"] = dict(DEFAULT_CONFIG["deezer"])
    cfg["matching"] = dict(DEFAULT_CONFIG["matching"])
    cfg["download"] = dict(DEFAULT_CONFIG["download"])

    # --- Music folder ---
    console.print("\n[bold]Step 1/3 — Music folder[/bold]")
    console.print("This is the folder containing your playlist subfolders (e.g. #DOWN_PsyTech/).")
    while True:
        path_str = _ask("Music folder path", default="~/Library/Mobile Documents/com~apple~CloudDocs/Music")
        folder = _validate_music_folder(path_str)
        if folder:
            cfg["music_folder"] = str(folder)
            console.print(f"[green]✓ Found: {folder}[/green]")
            break
        else:
            console.print(f"[red]Folder not found: {path_str}[/red] — try again")

    # --- Spotify credentials ---
    console.print("\n[bold]Step 2/3 — Spotify API credentials[/bold]")
    console.print(
        "1. Go to [link]https://developer.spotify.com/dashboard[/link]\n"
        "2. Create an app (any name)\n"
        "3. Add redirect URI: [bold]http://localhost:8080[/bold]\n"
        "4. Copy Client ID and Client Secret"
    )
    while True:
        client_id = _ask("Spotify Client ID")
        client_secret = _ask("Spotify Client Secret", password=True)
        console.print("  Validating Spotify credentials...")
        if _validate_spotify(client_id, client_secret):
            cfg["spotify"]["client_id"] = client_id
            cfg["spotify"]["client_secret"] = client_secret
            console.print("[green]✓ Spotify connected[/green]")
            break
        else:
            console.print("[red]Could not connect to Spotify. Check your credentials.[/red]")

    # --- Deezer ARL ---
    console.print("\n[bold]Step 3/3 — Deezer ARL token[/bold]")
    console.print(
        "Your Deezer account needs [bold]HiFi[/bold] or [bold]Premium[/bold] for FLAC quality.\n\n"
        "How to get your ARL token:\n"
        "1. Log into [link]https://www.deezer.com[/link] in your browser\n"
        "2. Open DevTools (F12 or Cmd+Option+I)\n"
        "3. Go to Application → Cookies → https://www.deezer.com\n"
        "4. Find the cookie named [bold]arl[/bold] and copy its value"
    )
    while True:
        arl = _ask("Deezer ARL token", password=True)
        console.print("  Validating Deezer ARL...")
        if _validate_deezer_arl(arl):
            cfg["deezer"]["arl"] = arl
            console.print("[green]✓ Deezer connected[/green]")
            break
        else:
            console.print("[red]Invalid ARL token. Make sure you copied the full value.[/red]")

    save_config(cfg)
    console.print(
        Panel.fit(
            "[green bold]Setup complete![/green bold]\n"
            "Run [bold]python sync.py[/bold] to start syncing.",
            border_style="green",
        )
    )
    return cfg
