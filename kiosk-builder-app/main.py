#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PySide6.QtWidgets import QApplication
from config_editor import ConfigEditor
import os

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
    app = QApplication(sys.argv)
    window = ConfigEditor()
    window.show()
    sys.exit(app.exec()) 