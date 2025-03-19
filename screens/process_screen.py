from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QFont, Qt, QFontDatabase

from printer_utils.printer_thread import PrinterThread
from config import config
import os

class ProcessScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.printer_thread = None
        self.loadCustomFont()
        self.setupUI()
    
    def loadCustomFont(self):
        """커스텀 폰트 로드"""
        font_name = config["process"]["font"]
        font_path = os.path.join("resources", "font", font_name)
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            else:
                self.font_family = "맑은 고딕"  # 폰트 로드 실패 시 기본 폰트
        else:
            self.font_family = "맑은 고딕"  # 폰트 파일이 없을 때 기본 폰트
    
    def setupUI(self):
        self.setupBackground()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.process_label = self.createProcessLabel()
        self.process_label.setGeometry(config["process"]["x"], config["process"]["y"],
                                       self.process_label.sizeHint().width(), self.process_label.sizeHint().height())
    
    def setupBackground(self):
        # 먼저 인덱스 기반 파일(0.jpg, 0.png)을 찾고, 없으면 기존 파일명 사용
        background_files = ["background/4.png", "background/4.jpg", "background/process_bg.jpg"]
        
        pixmap = None
        for filename in background_files:
            file_path = f"resources/{filename}"
            if os.path.exists(file_path):
                pixmap = QPixmap(file_path)
                break
        
        if pixmap is None or pixmap.isNull():
            # 모든 파일이 없는 경우 빈 배경 사용
            pixmap = QPixmap()
        
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setScaledContents(True)
        background_label.resize(*self.screen_size)

    def createProcessLabel(self):
        process_label = QLabel(self)  # 부모 위젯을 self로 지정
        process_label.setText(config["process"]["phrase"])
        
        # 커스텀 폰트 적용
        custom_font = QFont(self.font_family)
        custom_font.setPointSize(config["process"]["font_size"])
        process_label.setFont(custom_font)
        
        # 스타일시트 수정 (폰트 패밀리 제거)
        process_label_style = f""" color: {config["process"]["font_color"]};"""
        process_label.setStyleSheet(process_label_style)
        process_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return process_label
        
    def showEvent(self, event):
        # PrinterThread가 이미 실행 중인지 확인
        if self.printer_thread is None or not self.printer_thread.isRunning():
            self.printer_thread = PrinterThread()  # 새로운 스레드 생성
            self.printer_thread.start()  # 스레드 시작
        next_index = self.main_window.getNextScreenIndex()
        QTimer.singleShot(config["process"]["process_time"], lambda: self.stack.setCurrentIndex(next_index))
        
    # def mousePressEvent(self, event):
    #     self.stack.setCurrentIndex(4)
