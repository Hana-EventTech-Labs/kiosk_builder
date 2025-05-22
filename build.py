import os
import subprocess
import re
import shutil

def modify_printer_thread(mode):
    """printer_thread.py 파일에서 미리보기/인쇄 모드 전환"""
    file_path = "printer_utils/printer_thread.py"
    
    if not os.path.exists(file_path):
        print(f"오류: {file_path} 파일을 찾을 수 없습니다.")
        return False
    
    # 파일 백업
    backup_path = f"{file_path}.bak"
    shutil.copy2(file_path, backup_path)
    
    # 파일을 라인 단위로 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if mode == "preview":
        # 미리보기 활성화, 인쇄 비활성화
        modified_lines = []
        
        for line in lines:
            if "result = print_image(device_handle)" in line and not line.strip().startswith('#'):
                modified_lines.append('# ' + line)
            elif "if result != 0:" in line and not line.strip().startswith('#') and "print_image" in '\n'.join(modified_lines[-5:]):
                modified_lines.append('# ' + line)
            elif "self.error.emit(\"이미지 인쇄 실패\")" in line and not line.strip().startswith('#'):
                modified_lines.append('# ' + line)
            elif "return" in line and "이미지 인쇄 실패" in '\n'.join(modified_lines[-5:]):
                if not line.strip().startswith('#'):
                    modified_lines.append('# ' + line)
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        print("미리보기 모드로 설정했습니다.")
    elif mode == "print":
        # 인쇄 활성화, 미리보기 비활성화
        modified_lines = []
        
        # 미리보기 관련 코드 주석 처리 (256~263 줄)
        in_preview_section = False
        
        for line in lines:
            if "result, bm_info = get_preview_bitmap(device_handle, PAGE_FRONT)" in line:
                in_preview_section = True
                modified_lines.append('# ' + line.lstrip('#').lstrip())
            elif in_preview_section and any(keyword in line for keyword in ["if result == 0:", "image = bitmapinfo_to_image", "# self.preview_ready", "image.show()", "else:", "미리보기 비트맵 가져오기 실패"]):
                modified_lines.append('# ' + line.lstrip('#').lstrip())
            elif in_preview_section and "return" in line and "미리보기 비트맵 가져오기 실패" in '\n'.join(modified_lines[-5:]):
                modified_lines.append('# ' + line.lstrip('#').lstrip())
                in_preview_section = False
            elif "result = print_image(device_handle)" in line:
                # 인쇄 관련 코드 주석 해제
                modified_lines.append(line.replace('# ', '', 1) if line.strip().startswith('#') else line)
            elif "if result != 0:" in line and "print_image" in '\n'.join(modified_lines[-5:]):
                # 인쇄 관련 코드 주석 해제
                modified_lines.append(line.replace('# ', '', 1) if line.strip().startswith('#') else line)
            elif "self.error.emit(\"이미지 인쇄 실패\")" in line:
                # 인쇄 관련 코드 주석 해제
                modified_lines.append(line.replace('# ', '', 1) if line.strip().startswith('#') else line)
            elif "return" in line and "이미지 인쇄 실패" in '\n'.join(modified_lines[-5:]):
                # 인쇄 관련 코드 주석 해제
                modified_lines.append(line.replace('# ', '', 1) if line.strip().startswith('#') else line)
            else:
                modified_lines.append(line)
        
        print("인쇄 모드로 설정했습니다.")
    
    # 수정된 라인들을 파일에 쓰기
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    
    return True

def run_pyinstaller(name):
    """PyInstaller 실행"""
    command = [
        "pyinstaller", "--clean", "--onefile", "--windowed",
        "--add-data", "resources;resources",
        "--add-data", "screens;screens",
        "--add-data", "components;components",
        "--add-data", "printer_utils;printer_utils",
        "--add-data", "webcam_utils;webcam_utils",
        "--add-data", "config.json;.",
        "--name", name,
        "main.py"
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"{name} 빌드 실패:")
        print(result.stderr)
        return False
    
    print(f"{name} 빌드 성공!")
    return True

def build_all():
    """미리보기와 인쇄 모드 모두 빌드"""
    # 원본 파일 백업
    file_path = "printer_utils/printer_thread.py"
    backup_path = f"{file_path}.original"
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_path)
    
    # 미리보기 모드 빌드
    print("=== 미리보기 모드 빌드 시작 ===")
    if modify_printer_thread("preview"):
        success_preview = run_pyinstaller("kiosk_preview")
    else:
        success_preview = False
    
    # 인쇄 모드 빌드
    print("\n=== 인쇄 모드 빌드 시작 ===")
    if modify_printer_thread("print"):
        success_print = run_pyinstaller("kiosk_print")
    else:
        success_print = False
    
    # 원본 파일 복원
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        os.remove(backup_path)
    
    # 결과 출력
    print("\n=== 빌드 결과 ===")
    print(f"미리보기 모드: {'성공' if success_preview else '실패'}")
    print(f"인쇄 모드: {'성공' if success_print else '실패'}")

if __name__ == "__main__":
    build_all()