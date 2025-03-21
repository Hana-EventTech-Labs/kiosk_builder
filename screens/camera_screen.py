from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from webcam_utils.webcam_controller import WebcamViewer
from config import config
import os

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
        self.preview_width = config["frame"]["width"]
        self.preview_height = config["frame"]["height"]
        self.capture_width = config["camera_size"]["width"]
        self.capture_height = config["camera_size"]["height"]
        self.webcam = WebcamViewer(
            preview_width=self.preview_width, 
            preview_height=self.preview_height, 
            capture_width=self.capture_width, 
            capture_height=self.capture_height, 
            x=config["frame"]["x"], 
            y=config["frame"]["y"], 
            countdown=config["camera_count"]["number"]
        )
        self.webcam.setParent(self)
        self.webcam.setGeometry(config["frame"]["x"], config["frame"]["y"], self.preview_width, self.preview_height)
        self.webcam.photo_captured_signal.connect(self.onPhotoCaptured)


    
    def setupBackground(self):
        # 먼저 인덱스 기반 파일(0.jpg, 0.png)을 찾고, 없으면 기존 파일명 사용
        background_files = ["background/1.png", "background/1.jpg", "background/photo_bg.jpg"]
        
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
        
    def onPhotoCaptured(self):
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
