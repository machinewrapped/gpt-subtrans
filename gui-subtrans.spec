# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui-subtrans.py'],
    pathex=['./envsubtrans/lib', './envsubtrans/lib/python3.12/site-packages'],
    binaries=[],
    datas=[('theme/*', 'theme/'), ('instructions*', '.'), ('LICENSE', '.'), ('gui-subtrans.ico', '.')],
    hiddenimports=['PySide6.QtGui'],
    hookspath=['PySubtitleHooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='gui-subtrans',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='gui-subtrans',
)
