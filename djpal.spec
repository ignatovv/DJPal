# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for DJPal.
# Produces dist/DJPal/ with two executables:
#   djpal          — the main sync app
#   deemix_runner  — bundled deemix CLI (called by downloader.py)
#
# Build: python build.py   OR   pyinstaller --clean djpal.spec

block_cipher = None

# ── Main app ──────────────────────────────────────────────────────────────────
main_a = Analysis(
    ["sync.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "spotipy",
        "spotipy.oauth2",
        "rapidfuzz",
        "unidecode",
        "rich",
        "click",
        "yaml",
        "requests",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── deemix runner ─────────────────────────────────────────────────────────────
deemix_a = Analysis(
    ["_deemix_runner.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "deemix",
        "deezer",
        "mutagen",
        "requests",
        "click",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Merge: shared libs are deduplicated into a single location
MERGE(
    (main_a, "djpal", "djpal"),
    (deemix_a, "deemix_runner", "deemix_runner"),
)

# ── PYZ archives ──────────────────────────────────────────────────────────────
main_pyz = PYZ(main_a.pure, main_a.zipped_data, cipher=block_cipher)
deemix_pyz = PYZ(deemix_a.pure, deemix_a.zipped_data, cipher=block_cipher)

# ── Executables ───────────────────────────────────────────────────────────────
main_exe = EXE(
    main_pyz,
    main_a.scripts,
    [],
    exclude_binaries=True,
    name="djpal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

deemix_exe = EXE(
    deemix_pyz,
    deemix_a.scripts,
    [],
    exclude_binaries=True,
    name="deemix_runner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ── Collect into dist/DJPal/ ──────────────────────────────────────────────────
coll = COLLECT(
    main_exe,
    main_a.binaries,
    main_a.zipfiles,
    main_a.datas,
    deemix_exe,
    deemix_a.binaries,
    deemix_a.zipfiles,
    deemix_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DJPal",
)
