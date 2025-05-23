#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtGui import QIcon
from ui.screens.login_screen import LoginScreen

# 애플리케이션 중복 실행 방지 클래스
class SingleApplication(QApplication):
    def __init__(self, app_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_id = app_id
        self.server = None

        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        is_running = socket.waitForConnected(500)

        if is_running:
            QMessageBox.warning(None, "이미 실행 중", "슈퍼 키오스크 프로그램이 이미 실행 중입니다.")
            sys.exit(0)
        else:
            self.server = QLocalServer()
            self.server.listen(self.app_id)

# 작업 디렉토리 설정
if getattr(sys, 'frozen', False):
    program_directory = os.path.dirname(os.path.abspath(sys.executable))
else:
    program_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(program_directory)

def show_settings_window():
    try:
        print("설정 창을 열려고 시도 중...")
        
        from ui.screens.config_editor.main_window import ConfigEditor
        settings_window = ConfigEditor()
        
        # 설정 창에도 아이콘 적용
        icon_path = "Hana.ico"
        if os.path.exists(icon_path):
            settings_window.setWindowIcon(QIcon(icon_path))
        
        settings_window.show()
        
        # 윈도우 객체가 가비지 컬렉션되지 않도록 전역 변수로 저장
        global main_window
        main_window = settings_window
        
        print("설정 창이 열렸습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
        # 오류 메시지 표시
        from PySide6.QtWidgets import QMessageBox
        error_box = QMessageBox()
        error_box.setWindowTitle("오류")
        error_box.setText(f"설정 창을 여는 중 오류가 발생했습니다: {e}")
        error_box.setDetailedText(traceback.format_exc())
        error_box.setIcon(QMessageBox.Critical)
        error_box.exec_()
        
if __name__ == "__main__":
    app_id = "kiosk_builder_app_unique_id"
    app = SingleApplication(app_id, sys.argv)
    
    # 애플리케이션 전체에 아이콘 설정
    icon_path = "Hana.png"
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 애플리케이션 이름 설정 (작업 표시줄에 표시됨)
    app.setApplicationName("슈퍼 키오스크")

    login_window = LoginScreen(on_login_success=show_settings_window)
    
    # 로그인 창에도 아이콘 적용
    if os.path.exists(icon_path):
        login_window.setWindowIcon(QIcon(icon_path))
    
    login_window.show()

    sys.exit(app.exec())