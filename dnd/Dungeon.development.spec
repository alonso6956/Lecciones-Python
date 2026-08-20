# -*- mode: python ; coding: utf-8 -*-

analisis = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("web", "web"), ("config.json", ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["runtime_development.py"],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(analisis.pure)

ejecutable = EXE(
    pyz,
    analisis.scripts,
    analisis.binaries,
    analisis.datas,
    [],
    name="Dungeon-Developer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
