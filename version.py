# version.py
"""
프로젝트 전체 버전 관리
이 파일에서만 버전을 수정하면 모든 프로그램에 반영됩니다.
"""

__version__ = "1.0.6"
BUILD_DATE = "2025-05-26"
BUILD_NUMBER = "001"

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

# 버전업 시 이 값만 수정하면 됩니다
VERSION_INFO = {
    "major": 1,
    "minor": 0, 
    "patch": 0,
    "stage": "release"  # release, beta, alpha
}