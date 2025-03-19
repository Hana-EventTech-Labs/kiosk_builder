from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap

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
        self.setupUI()
    
    def setupUI(self):
        self.setupBackground()
        layout = QVBoxLayout()
        self.setLayout(layout)
    
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
        
    def showEvent(self, event):
        # PrinterThread가 이미 실행 중인지 확인
        if self.printer_thread is None or not self.printer_thread.isRunning():
            self.printer_thread = PrinterThread()  # 새로운 스레드 생성
            self.printer_thread.start()  # 스레드 시작
        next_index = self.main_window.getNextScreenIndex()
        QTimer.singleShot(config["process_time"], lambda: self.stack.setCurrentIndex(next_index))
        
    # def mousePressEvent(self, event):
    #     self.stack.setCurrentIndex(4)
