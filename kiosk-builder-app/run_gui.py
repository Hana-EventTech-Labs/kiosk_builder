### run_gui.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from login_window import LoginWindow

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
    from config_editor import ConfigEditor
    settings_window = ConfigEditor()
    settings_window.show()

if __name__ == "__main__":
    app_id = "kiosk_builder_app_unique_id"
    app = SingleApplication(app_id, sys.argv)

    login_window = LoginWindow(on_login_success=show_settings_window)
    login_window.show()

    sys.exit(app.exec())
