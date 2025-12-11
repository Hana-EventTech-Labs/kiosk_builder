# -*- mode: python ; coding: utf-8 -*-
"""
온라인 모드용 PyInstaller 스펙 파일
- resources 폴더 미포함 (서버에서 다운로드)
- 최소한의 파일만 번들링
- EXE 크기 최소화
"""

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 온라인 모드: resources 폴더 제외 (런타임에 다운로드)
        # ('resources', 'resources'),  # 제외!

        # 프린터 DLL은 필수 포함
        ('resources/SmartComm2.dll', 'resources'),

        # 코드 모듈만 포함
        ('screens', 'screens'),
        ('components', 'components'),
        ('printer_utils', 'printer_utils'),
        ('webcam_utils', 'webcam_utils'),

        # 기본 설정 파일 (온라인 모드 활성화)
        ('config.json', '.'),
    ],
    hiddenimports=[
        'requests',  # HTTP 다운로드용
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
    name='HanaKiosk',  # 온라인 버전 이름
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
    icon='resources/icon.ico' if __import__('os').path.exists('resources/icon.ico') else None,
)
