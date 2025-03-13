from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from webcam_utils.webcam_controller import WebcamViewer

class CameraScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.setupUI()
    
    def setupUI(self):
        self.setupBackground()
        # preview_width는 widget의 너비이고 capture_width는 카메라 전체 영역에서 캡쳐 영역의 너비입니다
        # 프리뷰 크기가 카메라 전체 크기가 아니니 참고 바랍니다 (카메라 크기는 config.json에 있습니다)
        self.preview_width = 1280
        self.preview_height = 720
        self.capture_width = 1280
        self.capture_height = 720
        self.webcam = WebcamViewer(
            preview_width=self.preview_width, 
            preview_height=self.preview_height, 
            capture_width=self.capture_width, 
            capture_height=self.capture_height, 
            x=(1920 - self.preview_width) / 2, 
            y=(1080 - self.preview_height) / 2, 
            countdown=3
        )
        self.webcam.setParent(self)

        self.webcam.photo_captured_signal.connect(self.onPhotoCaptured)

        layout = QVBoxLayout()
        self.setLayout(layout)
    
    def setupBackground(self):
        pixmap = QPixmap("resources/photo_bg.jpg")  # 이미지 로드
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setScaledContents(True)  # QLabel 크기에 맞게 이미지 조정
        background_label.resize(*self.screen_size)  # 전체 화면 크기로 설정
    
    def onPhotoCaptured(self):
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
