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

def get_python_dll_option():
    dll_path = "C:\\Python312\\python312.dll"
    if os.path.exists(dll_path):
        print(f"[INFO] Python DLL found: {dll_path}")
        return ["--add-binary", f"{dll_path};."]
    else:
        print(f"[WARNING] DLL not found: {dll_path}")
        return []

def build_super_kiosk_builder():
    builder_path = os.path.join("kiosk-builder-app", "run_gui.py")

    command = [
        'pyinstaller', '--clean', '--onefile', '--windowed',
        '--noupx',
        '--exclude-module=matplotlib',
        '--hidden-import=tkinter',
        '--add-data', 'resources;resources',
        '--add-data', 'kiosk-builder-app/config.json;.',
        '--add-data', 'version.py;.',
        '--name=super-kiosk-builder'
    ]

    if os.path.exists("Hana.ico"):
        command.insert(-2, '--icon=Hana.ico')

    command += get_python_dll_option()
    command.append(builder_path)

    return run_command_list(command, "Building super-kiosk-builder.exe")

def build_super_kiosk():
    command = [
        'pyinstaller', '--clean', '--onefile', '--windowed',
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
        command.insert(-2, '--icon=Kiosk.ico')

    command += get_python_dll_option()
    command.append("kiosk_main.py")

    return run_command_list(command, "Building super-kiosk.exe")

def verify_builds():
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
    print("[START] Starting dual exe build process...")

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

    if not verify_builds():
        sys.exit(1)

    print("[SUCCESS] All builds completed successfully!")

if __name__ == "__main__":
    main()
