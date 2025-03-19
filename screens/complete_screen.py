from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap

from config import config
import os

class CompleteScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.setupUI()

    def setupUI(self):
        self.setupBackground()
        layout = QVBoxLayout()

        self.setLayout(layout)

    def setupBackground(self):
        # 먼저 인덱스 기반 파일(0.jpg, 0.png)을 찾고, 없으면 기존 파일명 사용
        background_files = ["background/5.png", "background/5.jpg", "background/complete_bg.jpg"]
        
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
        
    def getNextScreenIndex(self):
        self.current_index = 0
        return config["screen_order"][self.current_index]
    
    def showEvent(self, event):
        """화면이 표시될 때 2초 후 스플래시 화면으로 이동"""
        next_index = self.main_window.getNextScreenIndex()
        print(f"완료 화면에서 다음 인덱스: {next_index}, 타이머: {config['complete_time']}ms")
        QTimer.singleShot(config["complete_time"], 
                        lambda: self.stack.setCurrentIndex(next_index))