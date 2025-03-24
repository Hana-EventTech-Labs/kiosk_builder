from PySide6.QtWidgets import QWidget, QLabel, QPushButton
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
import qrcode
from PIL import Image
import io
from config import config
import os

class QR_screen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.setupUI()
    
    def setupUI(self):
        self.setupBackground()
        self.addCloseButton()
        self.setupQRCode()
        self.setupPreviewArea()
    
    def setupBackground(self):
        # First try index-based files (2.jpg, 2.png), then fallback to generic name
        background_files = ["background/3.png", "background/3.jpg", "background/qr_bg.jpg"]
        
        pixmap = None
        for filename in background_files:
            file_path = f"resources/{filename}"
            if os.path.exists(file_path):
                pixmap = QPixmap(file_path)
                break
        
        if pixmap is None or pixmap.isNull():
            # Use empty background if no files exist
            pixmap = QPixmap()
        
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setScaledContents(True)
        background_label.resize(*self.screen_size)
    
    def setupQRCode(self):
        # QR 코드 라벨 생성
        self.qr_label = QLabel(self)
        
        # QR 코드 위치와 크기 설정 (원하는 값으로 조정 가능)
        qr_size = 300
        x_pos = (self.screen_size[0] - qr_size) // 2  # 화면 중앙
        y_pos = (self.screen_size[1] - qr_size) // 4  # 화면 중앙
        self.qr_label.setGeometry(x_pos, y_pos, qr_size, qr_size)
        
        # QR 코드 생성 (URL을 원하는 값으로 변경 가능)
        self.generateQRCode(config["qr"]["url"])
    
    def setupPreviewArea(self):
        # 미리보기 영역 설정
        preview_width = config["qr"]["preview_width"]
        preview_height = config["qr"]["preview_height"]
        
        # 미리보기 위치 설정 
        x_pos = config["qr"]["x"]
        y_pos = config["qr"]["y"]
        
        # 미리보기 라벨 생성
        self.preview_label = QLabel(self)
        self.preview_label.setGeometry(x_pos, y_pos, preview_width, preview_height)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        self.preview_label.setText("이미지 미리보기")
    
    def generateQRCode(self, data):
        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # PIL Image를 QPixmap으로 변환
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='PNG')
        qimage = QImage.fromData(byte_arr.getvalue())
        pixmap = QPixmap.fromImage(qimage)

        # QR 이미지를 QLabel에 표시
        self.qr_label.setPixmap(pixmap)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setScaledContents(True)
    
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
    
    def mousePressEvent(self, event):
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
