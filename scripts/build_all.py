# scripts/build_all.py - 사용자 친화적 onedir
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

def create_user_friendly_structure():
    """사용자 친화적 구조로 재구성"""
    print("[RESTRUCTURE] Creating user-friendly structure...")
    
    try:
        # Builder 구조 개선
        if os.path.exists("dist/super-kiosk-builder"):
            builder_clean_dir = "dist/Super-Kiosk-Builder"
            os.makedirs(builder_clean_dir, exist_ok=True)
            
            # 메인 실행 파일만 최상위에
            exe_source = "dist/super-kiosk-builder/super-kiosk-builder.exe"
            exe_dest = f"{builder_clean_dir}/Super-Kiosk-Builder.exe"
            
            if os.path.exists(exe_source):
                shutil.copy2(exe_source, exe_dest)
            
            # 나머지 파일들은 lib 폴더로
            lib_dir = f"{builder_clean_dir}/lib"
            shutil.copytree("dist/super-kiosk-builder", lib_dir, 
                          ignore=shutil.ignore_patterns("super-kiosk-builder.exe"))
            
            # 실행 스크립트 생성
            launcher_script = f'''@echo off
cd /d "%~dp0"
start "" "lib\\super-kiosk-builder.exe" %*
'''
            
            with open(f"{builder_clean_dir}/실행.bat", "w", encoding="utf-8") as f:
                f.write(launcher_script)
            
            with open(f"{builder_clean_dir}/Run.bat", "w", encoding="utf-8") as f:
                f.write(launcher_script)
            
            # README 파일 생성
            readme_content = '''# Super Kiosk Builder

## 실행 방법
1. "실행.bat" 또는 "Run.bat" 파일을 더블클릭
2. 또는 "Super-Kiosk-Builder.exe" 직접 실행

## 폴더 구조
- Super-Kiosk-Builder.exe: 메인 프로그램 (실행 안될 수 있음)
- 실행.bat / Run.bat: 안전한 실행 방법 (권장)
- lib/: 프로그램 구동에 필요한 파일들

## 주의사항
- 이 폴더 전체를 이동하세요
- exe 파일만 복사하면 안됩니다
'''
            
            with open(f"{builder_clean_dir}/README.txt", "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            print("✅ Builder: 사용자 친화적 구조 생성 완료")
        
        # Kiosk도 동일하게 처리
        if os.path.exists("dist/super-kiosk"):
            kiosk_clean_dir = "dist/Super-Kiosk"
            os.makedirs(kiosk_clean_dir, exist_ok=True)
            
            exe_source = "dist/super-kiosk/super-kiosk.exe" 
            exe_dest = f"{kiosk_clean_dir}/Super-Kiosk.exe"
            
            if os.path.exists(exe_source):
                shutil.copy2(exe_source, exe_dest)
            
            lib_dir = f"{kiosk_clean_dir}/lib"
            shutil.copytree("dist/super-kiosk", lib_dir,
                          ignore=shutil.ignore_patterns("super-kiosk.exe"))
            
            launcher_script = f'''@echo off
cd /d "%~dp0"
start "" "lib\\super-kiosk.exe" %*
'''
            
            with open(f"{kiosk_clean_dir}/키오스크실행.bat", "w", encoding="utf-8") as f:
                f.write(launcher_script)
                
            with open(f"{kiosk_clean_dir}/Run-Kiosk.bat", "w", encoding="utf-8") as f:
                f.write(launcher_script)
            
            print("✅ Kiosk: 사용자 친화적 구조 생성 완료")
            
        return True
        
    except Exception as e:
        print(f"❌ 구조 재구성 실패: {e}")
        return False

def create_zip_packages():
    """ZIP 패키지 생성"""
    print("[PACKAGE] Creating ZIP packages...")
    
    try:
        # 정리된 Builder ZIP 생성
        if os.path.exists("dist/Super-Kiosk-Builder"):
            shutil.make_archive("dist/Super-Kiosk-Builder", 'zip', "dist", "Super-Kiosk-Builder")
            print("✅ Created Super-Kiosk-Builder.zip")
        
        # 정리된 Kiosk ZIP 생성
        if os.path.exists("dist/Super-Kiosk"):
            shutil.make_archive("dist/Super-Kiosk", 'zip', "dist", "Super-Kiosk")
            print("✅ Created Super-Kiosk.zip")
            
        return True
    except Exception as e:
        print(f"❌ ZIP 생성 실패: {e}")
        return False

def verify_builds():
    # 정리된 구조 확인
    builder_dir = Path("dist/Super-Kiosk-Builder")
    kiosk_dir = Path("dist/Super-Kiosk")
    
    # ZIP 파일 확인
    builder_zip = Path("dist/Super-Kiosk-Builder.zip")
    kiosk_zip = Path("dist/Super-Kiosk.zip")

    success = True
    
    if builder_dir.exists() and kiosk_dir.exists():
        print("[SUCCESS] 사용자 친화적 구조 생성 완료!")
        
        # 최상위 파일 개수 확인
        builder_top_files = [f for f in builder_dir.iterdir() if f.is_file()]
        kiosk_top_files = [f for f in kiosk_dir.iterdir() if f.is_file()]
        
        print(f"[CLEAN] Builder 최상위 파일: {len(builder_top_files)}개")
        print(f"[CLEAN] Kiosk 최상위 파일: {len(kiosk_top_files)}개")
        
        for f in builder_top_files:
            print(f"  📄 {f.name}")
            
    else:
        print("[ERROR] 구조 생성 실패")
        success = False

    if builder_zip.exists() and kiosk_zip.exists():
        print("[SUCCESS] ZIP packages created!")
        print(f"[ZIP] Super-Kiosk-Builder.zip: {builder_zip.stat().st_size:,} bytes")
        print(f"[ZIP] Super-Kiosk.zip: {kiosk_zip.stat().st_size:,} bytes")
    else:
        print("[ERROR] ZIP package creation failed")
        success = False

    return success

def main():
    print("[START] Building user-friendly onedir packages")
    print("💡 사용자 친화적 구조로 DLL 문제 해결")

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
    
    if not create_user_friendly_structure():
        print("[ERROR] Structure reorganization failed")
        sys.exit(1)
    
    if not create_zip_packages():
        print("[ERROR] ZIP packaging failed")
        sys.exit(1)

    if not verify_builds():
        sys.exit(1)

    print("[SUCCESS] 사용자 친화적 빌드 완료!")
    print("")
    print("📦 사용자가 보는 것:")
    print("  📄 Super-Kiosk-Builder.exe")
    print("  📄 실행.bat (권장)")
    print("  📄 Run.bat")
    print("  📄 README.txt") 
    print("  📁 lib/ (시스템 파일들)")

if __name__ == "__main__":
    main()