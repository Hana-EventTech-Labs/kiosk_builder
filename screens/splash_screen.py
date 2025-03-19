from PySide6.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect, QPushButton
from PySide6.QtGui import QPixmap, QFont, QFontDatabase
from PySide6.QtCore import Qt, QPropertyAnimation, QSequentialAnimationGroup
import os
from config import config

class SplashScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.loadCustomFont()
        self.setupUI()
        self.startAnimation()

    def loadCustomFont(self):
        """커스텀 폰트 로드"""
        font_name = config["splash"]["font"]
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
        self.addCloseButton()
        self.splash_label = self.createSplashLabel()
        self.splash_label.setGeometry(config["splash"]["x"], config["splash"]["y"], self.splash_label.sizeHint().width(), self.splash_label.sizeHint().height())
    
    def setupBackground(self):
        # 먼저 인덱스 기반 파일(0.jpg, 0.png)을 찾고, 없으면 기존 파일명 사용
        background_files = ["background/0.png", "background/0.jpg", "background/splash_bg.jpg"]
        
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

    def createSplashLabel(self):
        splash_label = QLabel(self)  # 부모 위젯을 self로 지정
        splash_label.setText(config["splash"]["phrase"])
        
        # 커스텀 폰트 적용
        custom_font = QFont(self.font_family)
        custom_font.setPointSize(config["splash"]["font_size"])
        splash_label.setFont(custom_font)
        
        # 스타일시트 수정 (폰트 패밀리 제거)
        splash_label_style = f""" color: {config["splash"]["font_color"]};"""
        splash_label.setStyleSheet(splash_label_style)
        splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.opacity_effect = QGraphicsOpacityEffect(splash_label)
        splash_label.setGraphicsEffect(self.opacity_effect)

        return splash_label
    
    def startAnimation(self):
        # 🔹 애니메이션 설정 (opacity: 0.3 → 1.0)
        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(1000)  # 1초 동안 변화
        fade_in.setStartValue(0.3)
        fade_in.setEndValue(1.0)

        # 🔹 두 번째 애니메이션 (1.0 → 0.3)
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(1000)  # 1초 동안 변화
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.3)

        # 🔹 애니메이션 그룹 (순차 실행)
        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(fade_in)
        self.animation_group.addAnimation(fade_out)
        self.animation_group.setLoopCount(-1)  # 무한 반복
        self.animation_group.start()

    def addCloseButton(self):
        """오른쪽 상단에 닫기 버튼 추가"""
        self.close_button = QPushButton("X", self)
        self.close_button.setFixedSize(100, 100)
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
            