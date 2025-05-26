# version.py
"""
프로젝트 전체 버전 관리
이 파일에서만 버전을 수정하면 모든 프로그램에 반영됩니다.
"""

__version__ = "0.9.3"
BUILD_DATE = "2025-05-26"
BUILD_NUMBER = "146"

def get_version():
    """현재 버전 반환"""
    return __version__

def get_full_version():
    """상세 버전 정보 반환"""
    return f"{__version__} (Build {BUILD_NUMBER}, {BUILD_DATE})"

def get_build_info():
    """빌드 정보 반환"""
    return {
        "version": __version__,
        "build_date": BUILD_DATE,
        "build_number": BUILD_NUMBER
    }

# 버전 정보 파싱
VERSION_PARTS = __version__.split('.')
VERSION_INFO = {
    "major": int(VERSION_PARTS[0]) if len(VERSION_PARTS) > 0 else 1,
    "minor": int(VERSION_PARTS[1]) if len(VERSION_PARTS) > 1 else 0,
    "patch": int(VERSION_PARTS[2]) if len(VERSION_PARTS) > 2 else 0,
    "stage": "release"
}
