# DJPal

One-command sync of your Spotify playlists to local FLAC files.

DJPal scans your Spotify playlists, compares them against your local music folder, downloads any missing tracks as FLAC via Deezer, and drops them in the right folder — automatically. It never deletes files that aren't in Spotify (you might have added them from other sources).

---

## How it works

```
Spotify playlists (source of truth)
        ↓
  Gap detection  ←──── Local .flac files (fuzzy matched)
        ↓
  Download via Deezer (deemix)
        ↓
  Drop into correct playlist folder
```

1. Fetches all your Spotify playlists starting with `#`
2. Scans the corresponding local folders for `.flac` files
3. Fuzzy-matches tracks against filenames (handles typos, remix suffixes, artist order)
4. Downloads missing tracks from Deezer in FLAC quality
5. Moves files into the correct local folder

---

## Requirements

- Python 3.11+
- A [Spotify Developer app](https://developer.spotify.com/dashboard) (free, 2 minutes to set up)
- A Deezer account with **HiFi** or **Premium** subscription (required for FLAC)
- `deemix` installed on your system

---

## Installation

```bash
git clone https://github.com/ignatovv/DJPal.git
cd DJPal
pip install -r requirements.txt
pip install deemix
```

---

## Setup

Run the setup wizard on first launch:

```bash
python sync.py
```

The wizard will ask for:

### 1. Music folder path

The folder containing your playlist subfolders. Example structure:

```
~/Music/
├── #DOWN_PsyTech/
│   ├── Ouhana - Waves.flac
│   └── Arutani - Craft Coven.flac
├── #AMBIENT_Cinematic/
│   └── ...
└── #DOWN.MELO_Dream/
    └── ...
```

Each subfolder name should match (or closely resemble) the Spotify playlist name.

### 2. Spotify API credentials

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Set the redirect URI to `http://localhost:8080`
4. Copy your **Client ID** and **Client Secret**

The wizard will open a browser window for you to authorize access to your playlists (one-time).

### 3. Deezer ARL token

The ARL token identifies your Deezer session and determines download quality.

**How to get it:**
1. Log into [deezer.com](https://www.deezer.com) in your browser
2. Open DevTools: `F12` (Windows/Linux) or `Cmd+Option+I` (Mac)
3. Go to **Application** → **Cookies** → `https://www.deezer.com`
4. Find the cookie named `arl` and copy its value (it's a long string)

> **Note:** ARL tokens expire after ~3 months or when you log out. Re-run `python sync.py --setup` to update it.

Config is saved to `~/.config/flac-sync/config.yaml`.

---

## Usage

### Sync all playlists

```bash
python sync.py
```

Shows a summary table of all `#` playlists, then asks before downloading anything:

```
             Sync Status
┌─────────────────────┬───────┬─────────┬─────────┐
│ Playlist            │ Total │ Present │ Missing │
├─────────────────────┼───────┼─────────┼─────────┤
│ #DOWN_PsyTech       │  86   │   84    │    2    │
│ #AMBIENT_Cinematic  │  24   │   24    │    0    │
│ #DOWN.MELO_Dream    │ 155   │  150    │    5    │
└─────────────────────┴───────┴─────────┴─────────┘

7 track(s) missing across all playlists.

Download 7 missing track(s)? [y/N]
```

### Flags

| Flag | Description |
|------|-------------|
| `--setup` | Re-run the setup wizard |
| `--dry-run` | Show what would be downloaded without doing it |
| `--playlist "PsyTech"` | Sync only playlists whose name contains this string |
| `--threshold 90` | Override the fuzzy match threshold (default: 85) |
| `--suggest-cleanup` | List local files with no Spotify match and offer to delete them |

### Preview missing tracks without downloading

```bash
python sync.py --dry-run
```

### Sync a single playlist

```bash
python sync.py --playlist "PsyTech"
```

### Clean up orphan files

Files that exist locally but don't match any track currently in Spotify:

```bash
python sync.py --suggest-cleanup
```

This adds an **Orphans** column to the summary table and lists the files after scanning. You confirm before anything is deleted. Useful when you've been reorganizing playlists and want to clean up old downloads.

> Files added from sources other than Spotify will appear as orphans too — review the list carefully before confirming.

---

## Fuzzy matching

DJPal uses fuzzy string matching to handle real-world filename inconsistencies:

- **Order-independent:** `"Ouhana - Waves"` matches `"Waves - Ouhana"`
- **Typo-tolerant:** small character differences don't break matching
- **Remix-aware:** remix/edit suffixes are preserved for differentiation but normalized for comparison
- **Unicode-normalized:** `"Söriös"` matches `"Sorios"`, `"Cihangir Aslan"` matches `"Cihangir Aslan"`
- **Number-stripped:** leading track numbers like `01.` are ignored

Default threshold is **85/100**. Raise it (`--threshold 95`) if you're getting false positives, lower it if too many tracks are flagged as missing.

---

## Download quality

DJPal uses [deemix](https://deemix.app/) to download from Deezer:

| Deezer plan | Quality |
|-------------|---------|
| Free | MP3 128kbps |
| Premium | MP3 320kbps |
| HiFi | FLAC (lossless) |

For FLAC downloads you need a **Deezer HiFi** subscription.

### Alternative download engine

If deemix stops working, [streamrip](https://github.com/nathom/streamrip) is a maintained alternative with the same ARL-based auth:

```bash
pip install streamrip
# configure: rip config open → set deezer arl
```

Then swap the `downloader.py` call from `deemix` to `rip url`.

---

## File structure

```
DJPal/
├── sync.py              # Entry point
├── wizard.py            # First-run setup wizard
├── spotify_client.py    # Spotify API: fetch playlists + tracks
├── local_scanner.py     # Scan local folders, build normalized index
├── matcher.py           # Fuzzy match Spotify tracks vs local files
├── downloader.py        # deemix wrapper
├── organizer.py         # Move downloaded files to correct folder
├── config.py            # Load/save ~/.config/flac-sync/config.yaml
└── requirements.txt
```

---

## Troubleshooting

**"No playlists starting with '#' found"**
Make sure your Spotify playlists are named with a `#` prefix. Only playlists owned by you (or followed collaboratively) are returned.

**"deemix not found"**
Install it: `pip install deemix`. If it installs but isn't on PATH, try `python -m deemix` and adjust `downloader.py` accordingly.

**Track downloaded as MP3 instead of FLAC**
Your Deezer account doesn't have a HiFi subscription. Upgrade at deezer.com.

**ARL token expired**
Re-run `python sync.py --setup` and paste a fresh ARL token from your browser.

**Too many false "missing" results**
Lower the threshold: `python sync.py --threshold 75`. Or inspect your filenames — if they contain no artist info, matching will be harder.

**Too many false "present" results (wrong tracks matched)**
Raise the threshold: `python sync.py --threshold 92`.

---

## License

MIT
