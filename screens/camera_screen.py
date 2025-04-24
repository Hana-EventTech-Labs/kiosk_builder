from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
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
        # preview_width는 widget의 너비이고 camera_width는 카메라 화질의 너비입니다
        # 프리뷰 크기가 카메라 전체 크기가 아니니 참고 바랍니다 (카메라 크기는 config.json에 있습니다)
        self.preview_width = config["frame"]["width"]
        self.preview_height = config["frame"]["height"]
        self.camera_width = config["camera_size"]["width"]
        self.camera_height = config["camera_size"]["height"]
        if 1 in config["screen_order"]:
            self.webcam = WebcamViewer(
                preview_width=self.preview_width, 
                preview_height=self.preview_height, 
                camera_width=self.camera_width, 
                camera_height=self.camera_height, 
                x=config["frame"]["x"], 
                y=config["frame"]["y"], 
                countdown=config["camera_count"]["number"]
            )
            self.webcam.setParent(self)
            self.webcam.setGeometry(config["frame"]["x"], config["frame"]["y"], self.preview_width, self.preview_height)
            self.webcam.photo_captured_signal.connect(self.onPhotoCaptured)
        self.addCloseButton()


    
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

    def addCloseButton(self):
        """오른쪽 상단에 닫기 버튼 추가"""
        self.close_button = QPushButton("X", self)
        self.close_button.setFixedSize(200, 200)
        self.close_button.move(self.screen_size[0] - 50, 10)  # 오른쪽 상단 위치
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 92, 92, 0);  /* 완전히 투명하게 설정 */
                color: rgba(255, 255, 255, 0);  /* 텍스트도 완전히 투명하게 설정 (보이지 않음) */
                font-weight: bold;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(224, 74, 74, 0);  /* 호버 시에도 완전히 투명하게 설정 */
            }
        """)
        self.close_button.clicked.connect(self.main_window.closeApplication)
