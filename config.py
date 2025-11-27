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


# ═══════════════════════════════════════════════════════════
# 언어 관리 클래스
# ═══════════════════════════════════════════════════════════

class LanguageManager:
    """다국어 지원을 위한 언어 관리 클래스"""

    _instance = None
    _current_language = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        # 기본 언어 설정
        lang_config = config.get("language", {})
        self._current_language = lang_config.get("default", "ko")

    @property
    def current_language(self) -> str:
        """현재 선택된 언어 반환"""
        return self._current_language

    @current_language.setter
    def current_language(self, lang: str):
        """언어 설정"""
        if lang in ["ko", "en"]:
            self._current_language = lang
            print(f"언어가 '{lang}'로 설정되었습니다.")

    def is_enabled(self) -> bool:
        """언어 선택 기능 활성화 여부"""
        return config.get("language", {}).get("enabled", False)

    def get_background_folder(self) -> str:
        """현재 언어에 맞는 배경 폴더명 반환"""
        if not self.is_enabled():
            return "background"
        return f"background_{self._current_language}"

    def get_background_path(self, screen_index: int) -> str:
        """
        현재 언어에 맞는 배경화면 경로 반환

        Args:
            screen_index: 화면 인덱스 (0: splash, 1: camera, 등)

        Returns:
            배경화면 파일 경로 (없으면 빈 문자열)
        """
        extensions = ['.mp4', '.gif', '.png', '.jpg']

        # 언어별 폴더 먼저 확인
        if self.is_enabled():
            lang_folder = f"resources/background_{self._current_language}"
            for ext in extensions:
                path = os.path.join(lang_folder, f"{screen_index}{ext}")
                if os.path.exists(path):
                    return path

        # 기본 폴더 확인
        default_folder = "resources/background"
        for ext in extensions:
            path = os.path.join(default_folder, f"{screen_index}{ext}")
            if os.path.exists(path):
                return path

        return ""

    def get_phrase(self, phrase_key: str) -> str:
        """
        현재 언어에 맞는 문구 반환

        Args:
            phrase_key: 문구 키 (예: "splash_phrase", "process_phrase", "complete_phrase")

        Returns:
            문구 문자열
        """
        i18n = config.get("i18n", {})
        lang_phrases = i18n.get(self._current_language, {})

        # i18n에서 먼저 찾기
        phrase = lang_phrases.get(phrase_key, "")

        # i18n에 없으면 기존 config에서 가져오기
        if not phrase:
            # phrase_key가 "splash_phrase" 형태면 "splash"."phrase"로 변환
            parts = phrase_key.rsplit("_", 1)
            if len(parts) == 2:
                section, key = parts
                phrase = config.get(section, {}).get(key, "")

        return phrase


# 전역 언어 관리자 인스턴스
language_manager = LanguageManager()