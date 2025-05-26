# scripts/build_all.py 수정된 버전

import subprocess
import sys
import os
import shutil
from pathlib import Path

def run_command_list(command_list, description):
    """명령어 리스트 실행 및 결과 확인"""
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
    """빌드 디렉토리 정리"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"[CLEAN] Cleaned {dir_name}")

def build_super_kiosk_builder():
    """super-kiosk-builder.exe 빌드 (DLL 문제 해결 옵션 추가)"""
    builder_path = os.path.join("kiosk-builder-app", "run_gui.py")
    
    command = [
        'pyinstaller', '--clean', '--onefile', '--windowed',
        # DLL 로드 문제 해결을 위한 옵션들 추가
        '--noupx',  # UPX 압축 비활성화
        '--exclude-module=matplotlib',
        '--hidden-import=tkinter',  # tkinter 명시적 포함
        '--add-data', 'resources;resources',
        '--add-data', 'kiosk-builder-app/config.json;.',
        '--add-data', 'version.py;.',  # version.py 명시적 추가
        '--name=super-kiosk-builder',
        builder_path
    ]
    
    # 아이콘 파일이 있으면 추가
    if os.path.exists("Hana.ico"):
        command.insert(-2, '--icon=Hana.ico')
    
    return run_command_list(command, "Building super-kiosk-builder.exe")

def build_super_kiosk():
    """super-kiosk.exe 빌드 (DLL 문제 해결 옵션 추가)"""
    command = [
        'pyinstaller', '--clean', '--onefile', '--windowed',
        # DLL 로드 문제 해결을 위한 옵션들 추가
        '--noupx',  # UPX 압축 비활성화
        '--debug=all',  # 디버그 정보 포함
        '--add-data', 'resources;resources',
        '--add-data', 'screens;screens',
        '--add-data', 'components;components', 
        '--add-data', 'printer_utils;printer_utils',
        '--add-data', 'webcam_utils;webcam_utils',
        '--add-data', 'config.json;.',
        '--add-data', 'version.py;.',  # version.py 명시적 추가
        '--name=super-kiosk',
        'kiosk_main.py'
    ]
    
    # 아이콘 파일이 있으면 추가
    if os.path.exists("Kiosk.ico"):
        command.insert(-2, '--icon=Kiosk.ico')
    
    return run_command_list(command, "Building super-kiosk.exe")

def verify_builds():
    """빌드 결과 확인"""
    builder_exe = Path("dist/super-kiosk-builder.exe")
    kiosk_exe = Path("dist/super-kiosk.exe")
    
    if builder_exe.exists() and kiosk_exe.exists():
        print("[SUCCESS] All builds successful!")
        print(f"[FILE] super-kiosk-builder.exe: {builder_exe.stat().st_size:,} bytes")
        print(f"[FILE] super-kiosk.exe: {kiosk_exe.stat().st_size:,} bytes")
        return True
    else:
        print("[ERROR] Build verification failed")
        if not builder_exe.exists():
            print("  - super-kiosk-builder.exe not found")
        if not kiosk_exe.exists():
            print("  - super-kiosk.exe not found")
        return False

def main():
    """메인 빌드 프로세스"""
    print("[START] Starting dual exe build process...")
    
    # 1. 환경 확인
    required_files = [
        os.path.join("kiosk-builder-app", "run_gui.py"), 
        "kiosk_main.py",
        "version.py"
    ]
    for file in required_files:
        if not os.path.exists(file):
            print(f"[ERROR] {file} not found")
            sys.exit(1)
    
    # 2. version.py를 kiosk-builder-app에 복사
    shutil.copy2("version.py", os.path.join("kiosk-builder-app", "version.py"))
    print("[COPY] version.py copied to kiosk-builder-app")
    
    # 3. 빌드 디렉토리 정리
    clean_build_dirs()
    
    # 4. Builder 빌드
    if not build_super_kiosk_builder():
        print("[ERROR] Builder build failed")
        sys.exit(1)
    
    # 5. Kiosk 빌드  
    if not build_super_kiosk():
        print("[ERROR] Kiosk build failed")
        sys.exit(1)
    
    # 6. 빌드 결과 확인
    if not verify_builds():
        sys.exit(1)
    
    print("[SUCCESS] All builds completed successfully!")

if __name__ == "__main__":
    main()