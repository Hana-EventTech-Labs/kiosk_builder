# -*- mode: python ; coding: utf-8 -*-
"""
슈퍼 키오스크 빌더 GUI PyInstaller 스펙 파일
- resources 폴더 미포함 (업로드 대상 파일은 EXE와 같은 경로에 별도 배치)
"""

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui', 'ui'),
        ('utils', 'utils'),
        ('Hana.ico', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'requests',
    ],
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
    name='SuperKioskBuilder',
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
    icon='Hana.ico',
)
