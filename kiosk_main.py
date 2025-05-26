# kiosk_main.py
"""
키오스크 실행 전용 프로그램
실제 키오스크 화면을 표시하고 사용자 인터랙션을 처리합니다.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from version import get_version, get_full_version

# 기존 main.py의 모든 import들
from main import KioskApp, SingleApplication

def main():
    """키오스크 메인 함수"""
    # 애플리케이션 ID 지정
    app_id = "kiosk_app_unique_id"
    
    # 중복 실행 방지 앱 생성
    app = SingleApplication(app_id, sys.argv)
    
    # 아이콘 설정
    icon_path = "Kiosk.ico"
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 애플리케이션 정보 설정
    app.setApplicationName("Super Kiosk")
    app.setApplicationVersion(get_version())
    
    # 키오스크 창 생성
    window = KioskApp()
    
    # 윈도우 제목에 버전 정보 추가
    window.setWindowTitle(f"Super Kiosk v{get_version()}")
    
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())