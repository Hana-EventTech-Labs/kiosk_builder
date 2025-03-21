from PySide6.QtWidgets import QWidget, QLabel
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
        self.setupQRCode()
    
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
        y_pos = (self.screen_size[1] - qr_size) // 2  # 화면 중앙
        self.qr_label.setGeometry(x_pos, y_pos, qr_size, qr_size)
        
        # QR 코드 생성 (URL을 원하는 값으로 변경 가능)
        self.generateQRCode(config["qr"]["url"])
    
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
    
    def mousePressEvent(self, event):
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
