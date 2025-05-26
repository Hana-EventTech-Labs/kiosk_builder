# scripts/build_all.py - NSIS 설치 프로그램 방식
import subprocess
import sys
import os
import shutil
from pathlib import Path

def run_command_list(command_list, description):
    print(f"[BUILD] {description}...")
    try:
        result = subprocess.run(command_list, check=True, 
                                capture_output=True, text=True)
        print(f"[SUCCESS] {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def clean_build_dirs():
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"[CLEAN] Cleaned {dir_name}")

def build_super_kiosk_builder():
    builder_path = os.path.join("kiosk-builder-app", "run_gui.py")

    command = [
        'pyinstaller', '--clean', '--onedir', '--windowed',
        '--noupx',
        '--exclude-module=matplotlib',
        '--hidden-import=tkinter',
        '--add-data', 'resources;resources',
        '--add-data', 'kiosk-builder-app/config.json;.',
        '--add-data', 'version.py;.',
        '--name=super-kiosk-builder'
    ]

    if os.path.exists("Hana.ico"):
        command.extend(['--icon', 'Hana.ico'])

    command.append(builder_path)
    return run_command_list(command, "Building super-kiosk-builder (onedir)")

def build_super_kiosk():
    command = [
        'pyinstaller', '--clean', '--onedir', '--windowed',
        '--noupx',
        '--debug=all',
        '--add-data', 'resources;resources',
        '--add-data', 'screens;screens',
        '--add-data', 'components;components',
        '--add-data', 'printer_utils;printer_utils',
        '--add-data', 'webcam_utils;webcam_utils',
        '--add-data', 'config.json;.',
        '--add-data', 'version.py;.',
        '--name=super-kiosk'
    ]

    if os.path.exists("Kiosk.ico"):
        command.extend(['--icon', 'Kiosk.ico'])

    command.append("kiosk_main.py")
    return run_command_list(command, "Building super-kiosk (onedir)")

def create_nsis_script():
    """NSIS 설치 스크립트 생성"""
    print("[NSIS] Creating installer script...")
    
    # version.py에서 버전 읽기
    try:
        with open('version.py', 'r', encoding='utf-8') as f:
            content = f.read()
            # __version__ = "x.x.x" 찾기
            import re
            version_match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
            if version_match:
                version = version_match.group(1)
            else:
                version = "1.0.0"
    except:
        version = "1.0.0"
    
    nsis_script = f'''# Super Kiosk Builder Installer
!define PRODUCT_NAME "Super Kiosk Builder"
!define PRODUCT_VERSION "{version}"
!define PRODUCT_PUBLISHER "HanaLabs"
!define PRODUCT_WEB_SITE "https://github.com/Hana-EventTech-Labs/kiosk_builder"
!define PRODUCT_DIR_REGKEY "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\super-kiosk-builder.exe"
!define PRODUCT_UNINST_KEY "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor lzma

# Modern UI
!include "MUI2.nsh"

# General
Name "${{PRODUCT_NAME}} ${{PRODUCT_VERSION}}"
OutFile "dist\\SuperKioskSetup.exe"
InstallDir "$PROGRAMFILES\\Super Kiosk Builder"
InstallDirRegKey HKLM "${{PRODUCT_DIR_REGKEY}}" ""
ShowInstDetails show
ShowUnInstDetails show

# Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-install.ico"
!define MUI_UNICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-uninstall.ico"

# Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\\super-kiosk-builder.exe"
!insertmacro MUI_PAGE_FINISH

# Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

# Language files
!insertmacro MUI_LANGUAGE "Korean"
!insertmacro MUI_LANGUAGE "English"

# Reserve files
!insertmacro MUI_RESERVEFILE_LANGDLL

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  # 프로그램 파일들 설치
  File /r "dist\\super-kiosk-builder\\*.*"
  
  # 바이너리 파일 등록
  WriteRegStr HKLM "${{PRODUCT_DIR_REGKEY}}" "" "$INSTDIR\\super-kiosk-builder.exe"
  
  # 시작 메뉴 바로가기
  CreateDirectory "$SMPROGRAMS\\Super Kiosk Builder"
  CreateShortCut "$SMPROGRAMS\\Super Kiosk Builder\\Super Kiosk Builder.lnk" "$INSTDIR\\super-kiosk-builder.exe"
  CreateShortCut "$SMPROGRAMS\\Super Kiosk Builder\\Uninstall.lnk" "$INSTDIR\\uninst.exe"
  
  # 바탕화면 바로가기
  CreateShortCut "$DESKTOP\\Super Kiosk Builder.lnk" "$INSTDIR\\super-kiosk-builder.exe"
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\\${{PRODUCT_NAME}}.url" "InternetShortcut" "URL" "${{PRODUCT_WEB_SITE}}"
  CreateShortCut "$SMPROGRAMS\\Super Kiosk Builder\\Website.lnk" "$INSTDIR\\${{PRODUCT_NAME}}.url"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\\uninst.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayName" "${{PRODUCT_NAME}}"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "UninstallString" "$INSTDIR\\uninst.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayIcon" "$INSTDIR\\super-kiosk-builder.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayVersion" "${{PRODUCT_VERSION}}"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "URLInfoAbout" "${{PRODUCT_WEB_SITE}}"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "Publisher" "${{PRODUCT_PUBLISHER}}"
SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name)가 컴퓨터에서 성공적으로 제거되었습니다."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "$(^Name)을(를) 완전히 제거하시겠습니까?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  Delete "$INSTDIR\\${{PRODUCT_NAME}}.url"
  Delete "$INSTDIR\\uninst.exe"
  
  # 모든 파일 삭제
  RMDir /r "$INSTDIR"
  
  # 바로가기 삭제
  Delete "$SMPROGRAMS\\Super Kiosk Builder\\*.*"
  RMDir "$SMPROGRAMS\\Super Kiosk Builder"
  Delete "$DESKTOP\\Super Kiosk Builder.lnk"
  
  # 레지스트리 삭제
  DeleteRegKey HKLM "${{PRODUCT_UNINST_KEY}}"
  DeleteRegKey HKLM "${{PRODUCT_DIR_REGKEY}}"
  
  SetAutoClose true
SectionEnd
'''
    
    with open('installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script)
    
    print("[NSIS] Installer script created: installer.nsi")
    return True

def create_license_file():
    """라이선스 파일 생성 (NSIS 요구사항)"""
    license_content = """MIT License

Copyright (c) 2025 Super Kiosk Builder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    with open('LICENSE.txt', 'w', encoding='utf-8') as f:
        f.write(license_content)
    
    print("[NSIS] License file created")

def build_installer():
    """NSIS로 설치 프로그램 빌드"""
    print("[NSIS] Building installer...")
    
    # NSIS 경로 확인
    nsis_paths = [
        "C:\\Program Files (x86)\\NSIS\\makensis.exe",
        "C:\\Program Files\\NSIS\\makensis.exe",
        "makensis.exe"  # PATH에 있는 경우
    ]
    
    nsis_exe = None
    for path in nsis_paths:
        if shutil.which(path):
            nsis_exe = path
            break
    
    if not nsis_exe:
        print("[ERROR] NSIS not found. Installing NSIS...")
        # GitHub Actions에서 NSIS 설치
        install_cmd = [
            'powershell', '-Command',
            'choco install nsis -y'
        ]
        if not run_command_list(install_cmd, "Installing NSIS"):
            print("[ERROR] Failed to install NSIS")
            return False
        nsis_exe = "makensis.exe"
    
    # NSIS 컴파일
    compile_cmd = [nsis_exe, 'installer.nsi']
    return run_command_list(compile_cmd, "Compiling NSIS installer")

def verify_builds():
    installer_path = Path("dist/SuperKioskSetup.exe")
    
    if installer_path.exists():
        print("[SUCCESS] NSIS installer created!")
        print(f"[INSTALLER] SuperKioskSetup.exe: {installer_path.stat().st_size:,} bytes")
        return True
    else:
        print("[ERROR] Installer creation failed")
        return False

def main():
    print("[START] Building NSIS installer package")
    print("Professional installer solution for DLL issues")

    required_files = [
        os.path.join("kiosk-builder-app", "run_gui.py"),
        "kiosk_main.py",
        "version.py"
    ]
    for file in required_files:
        if not os.path.exists(file):
            print(f"[ERROR] {file} not found")
            sys.exit(1)

    shutil.copy2("version.py", os.path.join("kiosk-builder-app", "version.py"))
    print("[COPY] version.py copied to kiosk-builder-app")

    clean_build_dirs()

    if not build_super_kiosk_builder():
        print("[ERROR] Builder build failed")
        sys.exit(1)

    if not build_super_kiosk():
        print("[ERROR] Kiosk build failed")
        sys.exit(1)
    
    create_license_file()
    
    if not create_nsis_script():
        print("[ERROR] NSIS script creation failed")
        sys.exit(1)
    
    if not build_installer():
        print("[ERROR] Installer build failed")
        sys.exit(1)

    if not verify_builds():
        sys.exit(1)

    print("[SUCCESS] Professional installer created!")
    print("")
    print("User experience:")
    print("  1. Download SuperKioskSetup.exe")
    print("  2. Run installer")
    print("  3. Click Start menu shortcut")
    print("  4. No DLL issues!")

if __name__ == "__main__":
    main()