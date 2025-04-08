#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from config_editor import ConfigEditor
import os

# 애플리케이션 중복 실행 방지 클래스
class SingleApplication(QApplication):
    def __init__(self, app_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_id = app_id
        self.server = None
        
        # 이미 실행 중인지 확인
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        is_running = socket.waitForConnected(500)
        
        if is_running:
            # 이미 실행 중인 경우
            QMessageBox.warning(None, "이미 실행 중", "슈퍼 키오스크 프로그램이 이미 실행 중입니다.")
            sys.exit(0)
        else:
            # 새로운 인스턴스인 경우, 서버 생성
            self.server = QLocalServer()
            self.server.listen(self.app_id)

if getattr(sys, 'frozen', False):
    # 실행파일로 실행한 경우,해당 파일을 보관한 디렉토리의 full path를 취득
    program_directory = os.path.dirname(os.path.abspath(sys.executable))
    # _internal을 쓸 경우
    # program_directory = os.path.join(program_directory, "_internal")
else:
    # 파이썬 파일로 실행한 경우,해당 파일을 보관한 디렉토리의 full path를 취득
    program_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(program_directory)

if __name__ == "__main__":
    # 애플리케이션 ID 지정
    app_id = "kiosk_builder_app_unique_id"
    
    app = SingleApplication(app_id, sys.argv)
    window = ConfigEditor()
    window.show()
    sys.exit(app.exec()) 