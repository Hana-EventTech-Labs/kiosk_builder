import os
import sys
import json

def get_config_path():
    """설정 파일 경로 반환"""
    # PyInstaller 임시 폴더에서 실행 중인지 확인
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        executable_dir = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
        executable_dir = base_path
    
    # 가능한 설정 파일 경로 (우선순위 순)
    possible_paths = [
        os.path.join(executable_dir, "config.json"),          # 실행 파일과 같은 위치
        os.path.join(executable_dir, "config", "config.json"), # 실행 파일 경로의 config 폴더
        os.path.join(base_path, "config.json"),               # 임시 폴더
        "config.json"                                          # 현재 작업 폴더
    ]
    
    # 존재하는 첫 번째 경로 반환
    for path in possible_paths:
        if os.path.exists(path):
            print(f"설정 파일을 찾았습니다: {path}")
            return path
    
    # 설정 파일을 찾지 못한 경우 None 반환
    return None

# 설정 로드
config_path = get_config_path()
if not config_path:
    raise FileNotFoundError("설정 파일(config.json)을 찾을 수 없습니다.")

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)