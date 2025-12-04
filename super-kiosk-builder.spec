# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['kiosk-builder-app\\run_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('kiosk-builder-app/resources', 'resources'), ('kiosk-builder-app/ui', 'ui'), ('kiosk-builder-app/config.json', '.'), ('kiosk-builder-app/api_client.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='super-kiosk-builder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
