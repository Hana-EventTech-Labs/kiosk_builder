from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap

class PhotoScreen(QWidget):
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
        pixmap = QPixmap("resources/photo_bg.jpg")  # 이미지 로드
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setScaledContents(True)  # QLabel 크기에 맞게 이미지 조정
        background_label.resize(*self.screen_size)  # 전체 화면 크기로 설정
    
    def mousePressEvent(self, event):
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
