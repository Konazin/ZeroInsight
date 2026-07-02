# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for ZeroInsight backend.
# Build: pyinstaller backend.spec --clean --noconfirm
#
# Run build-app.ps1 to do the full build (frontend + backend + installer).

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── Data files ────────────────────────────────────────────────────────────────

datas = [
    # Built React app (run `npm run build` in frontend/ first)
    ("frontend/dist", "frontend_dist"),
]

# Bundle the .env template if it exists so the user has a starting config
if os.path.exists(".env"):
    datas.append((".env", "."))

# Collect pydantic data files (JSON schemas, etc.)
datas += collect_data_files("pydantic")
datas += collect_data_files("uvicorn")

# ── Hidden imports ────────────────────────────────────────────────────────────

hiddenimports = [
    # uvicorn — critical: PyInstaller misses these protocol modules
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.protocols.websockets.wsproto_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    # anyio / sniffio (uvicorn async backend)
    "anyio",
    "anyio._backends._asyncio",
    "sniffio",
    # pydantic
    "pydantic",
    "pydantic_core",
    # starlette / fastapi extras
    "starlette.middleware.cors",
    "starlette.staticfiles",
    "fastapi.staticfiles",
    # multipart (file uploads)
    "multipart",
    "multipart.multipart",
    # email (stdlib — sometimes missed on Windows)
    "email.mime.multipart",
    "email.mime.nonmultipart",
    "email.mime.text",
    "email.mime.base",
    # PIL / Pillow
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    "PIL._tkinter_finder",
    # httpx / httpcore
    "httpx",
    "httpx._transports.default",
    "httpcore",
    "httpcore._async.interfaces",
    "httpcore._sync.interfaces",
    # h11
    "h11",
    # python-dotenv
    "dotenv",
    # openai SDK
    "openai",
    "openai.resources",
    "openai.resources.images",
    # certifi (SSL certs for HTTPS)
    "certifi",
]

a = Analysis(
    ["start_backend.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclude heavy packages that are never used by the FastAPI server
    excludes=["tkinter", "matplotlib", "scipy", "PyQt5", "PyQt6", "PySide6", "wx", "notebook"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX can cause false-positive AV detections
    console=True,        # Keep console=True so Electron captures stdout/stderr
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="backend",      # Output: dist/backend/
)
