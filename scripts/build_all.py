# scripts/build_all.py
"""
두 개의 exe 파일을 동시에 빌드하는 스크립트
로컬 개발 및 GitHub Actions에서 사용
"""

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

def run_command(command, description):
    """명령어 실행 및 결과 확인 (기존 호환성용)"""
    print(f"[BUILD] {description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
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
    """super-kiosk-builder.exe 빌드"""
    # Windows에서 안전한 경로 처리
    builder_path = os.path.join("kiosk-builder-app", "run_gui.py")
    
    command = [
        'pyinstaller', '--clean', '--onefile', '--windowed',
        '--add-data', 'resources;resources',
        '--add-data', 'kiosk-builder-app/config.json;.',
        '--name', 'super-kiosk-builder',
        builder_path
    ]
    
    # 아이콘 파일이 있으면 추가
    if os.path.exists("Hana.ico"):
        command.insert(-2, '--icon=Hana.ico')
    
    return run_command_list(command, "Building super-kiosk-builder.exe")

def build_super_kiosk():
    """super-kiosk.exe 빌드"""
    command = [
        'pyinstaller', '--clean', '--onefile', '--windowed',
        '--add-data', 'resources;resources',
        '--add-data', 'screens;screens',
        '--add-data', 'components;components', 
        '--add-data', 'printer_utils;printer_utils',
        '--add-data', 'webcam_utils;webcam_utils',
        '--add-data', 'config.json;.',
        '--name', 'super-kiosk',
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
        "kiosk_main.py"
    ]
    for file in required_files:
        if not os.path.exists(file):
            print(f"[ERROR] {file} not found")
            sys.exit(1)
    
    # 2. 빌드 디렉토리 정리
    clean_build_dirs()
    
    # 3. Builder 빌드
    if not build_super_kiosk_builder():
        print("[ERROR] Builder build failed")
        sys.exit(1)
    
    # 4. Kiosk 빌드  
    if not build_super_kiosk():
        print("[ERROR] Kiosk build failed")
        sys.exit(1)
    
    # 5. 빌드 결과 확인
    if not verify_builds():
        sys.exit(1)
    
    print("[SUCCESS] All builds completed successfully!")

if __name__ == "__main__":
    main()