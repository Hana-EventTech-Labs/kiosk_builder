# scripts/update_version.py
"""
버전 업데이트 자동화 스크립트
GitHub Actions에서 사용되거나 수동으로 실행 가능
"""

import sys
import os
import re
from datetime import datetime

def update_version_file(new_version, build_number=None):
    """version.py 파일의 버전 정보 업데이트"""
    
    if build_number is None:
        build_number = datetime.now().strftime("%j")  # 일년 중 날짜
    
    build_date = datetime.now().strftime("%Y-%m-%d")
    
    # 새로운 version.py 내용 생성
    version_content = f'''# version.py
"""
프로젝트 전체 버전 관리
이 파일에서만 버전을 수정하면 모든 프로그램에 반영됩니다.
"""

__version__ = "{new_version}"
BUILD_DATE = "{build_date}"
BUILD_NUMBER = "{build_number:0>3}"

def get_version():
    """현재 버전 반환"""
    return __version__

def get_full_version():
    """상세 버전 정보 반환"""
    return f"{{__version__}} (Build {{BUILD_NUMBER}}, {{BUILD_DATE}})"

def get_build_info():
    """빌드 정보 반환"""
    return {{
        "version": __version__,
        "build_date": BUILD_DATE,
        "build_number": BUILD_NUMBER
    }}

# 버전 정보 파싱
VERSION_PARTS = __version__.split('.')
VERSION_INFO = {{
    "major": int(VERSION_PARTS[0]) if len(VERSION_PARTS) > 0 else 1,
    "minor": int(VERSION_PARTS[1]) if len(VERSION_PARTS) > 1 else 0,
    "patch": int(VERSION_PARTS[2]) if len(VERSION_PARTS) > 2 else 0,
    "stage": "release"
}}
'''
    
    # version.py 파일 업데이트
    with open('version.py', 'w', encoding='utf-8') as f:
        f.write(version_content)
    
    print(f"✅ Version updated to {new_version} (Build {build_number:0>3})")
    return True

def main():
    """메인 함수"""
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <version>")
        print("Example: python update_version.py 1.2.0")
        sys.exit(1)
    
    version_input = sys.argv[1]
    
    # v 접두사 제거
    if version_input.startswith('v'):
        version_input = version_input[1:]
    
    # 버전 형식 검증
    if not re.match(r'^\d+\.\d+\.\d+$', version_input):
        print(f"❌ Invalid version format: {version_input}")
        print("Use format: X.Y.Z (e.g., 1.2.0)")
        sys.exit(1)
    
    update_version_file(version_input)

if __name__ == "__main__":
    main()