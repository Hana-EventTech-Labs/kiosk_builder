from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap

from config import screen_order

class ProcessScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.setupUI()
    
    def setupUI(self):
        self.setupBackground()
        layout = QVBoxLayout()

        self.printing_label = QLabel("발급중입니다...")

        layout.addWidget(self.printing_label)
        self.setLayout(layout)
    
    def setupBackground(self):
        pixmap = QPixmap("resources/process_bg.jpg")  # 이미지 로드
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setScaledContents(True)  # QLabel 크기에 맞게 이미지 조정
        background_label.resize(*self.screen_size)  # 전체 화면 크기로 설정
    
    def showEvent(self, event):
        next_index = self.main_window.getNextScreenIndex()
        QTimer.singleShot(3000, lambda: self.stack.setCurrentIndex(next_index))
        
    # def mousePressEvent(self, event):
    #     self.stack.setCurrentIndex(4)
