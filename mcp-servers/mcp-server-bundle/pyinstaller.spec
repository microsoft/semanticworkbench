# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

is_windows = sys.platform.startswith('win')

executable_packages = [
    'mcp-server-filesystem',
]
if is_windows:
    executable_packages += [
        'mcp-server-office',
    ]

executable_paths = [
    f'../{package}/dist/{package}'
    for package in executable_packages
]

if is_windows:
    executable_paths = [
        path + '.exe'
        for path in executable_paths
    ]

a = Analysis(
    ['mcp_server_bundle/main.py'],
    pathex=[],
    binaries=[
        # Add the external executable as a binary
        # Format: (source_path, destination_directory_in_bundle)
        (exe, 'external_executables')
        for exe in executable_paths
    ],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mcp-server-bundle',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
