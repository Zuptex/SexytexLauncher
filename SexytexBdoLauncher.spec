# -*- mode: python ; coding: utf-8 -*-
# SexytexBdoLauncher.spec
# Run with: pyinstaller SexytexBdoLauncher.spec

from PyInstaller.building.datastruct import Tree

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PIL', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],                         # onedir: binaries go into COLLECT, not EXE
    exclude_binaries=True,      # required for onedir
    name='SexytexBdoLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,              # no black console window
    disable_windowed_traceback=False,
    uac_admin=True,             # always prompt for admin
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',
)

# COLLECT puts the exe + all Python runtime files into dist/SexytexBdoLauncher/
# The exe lives at dist/SexytexBdoLauncher/SexytexBdoLauncher.exe
# Users place nvidiaProfileInspector\ and profiles\ next to that exe — works from any path.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SexytexBdoLauncher',
)
