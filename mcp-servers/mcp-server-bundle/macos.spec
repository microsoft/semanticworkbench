# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['mcp_server_bundle/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'subprocess',
        'signal',
        'threading',
        'mcp_tunnel',
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

# For macOS, also create a simple app bundle
app = BUNDLE(
    exe,
    name='MCP Server Bundle.app',
    bundle_identifier='com.example.mcpserverbundle',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSPrincipalClass': 'NSApplication',
        'CFBundleDisplayName': 'MCP Server Bundle',
        'CFBundleName': 'MCP Server Bundle',
        'CFBundleExecutable': 'mcp-server-bundle',
        'CFBundleIdentifier': 'com.example.mcpserverbundle',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'APPL',
    }
)
