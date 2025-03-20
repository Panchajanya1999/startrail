# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['star_trail_app.py'],  # Main script name
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PIL', 'PIL._imagingtk', 'PIL._tkinter_finder', 'cv2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='StarTrailGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI applications
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Optional: path to an icon file (for Windows)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StarTrailGenerator',
)

# For macOS, create a .app bundle
app = BUNDLE(
    coll,
    name='StarTrailGenerator.app',
    icon='icon.icns',  # macOS icon file
    bundle_identifier=None,
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
    },
)
