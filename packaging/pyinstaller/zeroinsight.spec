# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path.cwd()

datas = [
    (str(ROOT / "zero_insight" / "render" / "templates"), "zero_insight/render/templates"),
    (str(ROOT / "zero_insight" / "content" / "prompts"), "zero_insight/content/prompts"),
    (str(ROOT / ".env.example"), "."),
]

block_cipher = None

a = Analysis(
    [str(ROOT / "zero_insight" / "desktop" / "app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PIL.Image",
        "docx",
        "fitz",
        "playwright.async_api",
        "zero_insight.brand",
        "zero_insight.ai_providers",
        "zero_insight.ai_providers.text",
        "zero_insight.ai_providers.image",
        "zero_insight.ai_providers.vision",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[".env", "screenshots", "stories", "posts"],
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
    name="ZeroInsight",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
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
    upx=True,
    upx_exclude=[],
    name="ZeroInsight",
)
