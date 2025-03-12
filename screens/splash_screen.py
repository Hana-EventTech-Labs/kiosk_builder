from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QPropertyAnimation, QSequentialAnimationGroup

from config import screen_order

class SplashScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.setupUI()
        self.startAnimation()

    def setupUI(self):
        self.setupBackground()

        layout = QVBoxLayout()

        layout.addStretch(5)

        self.splash_label = self.createSplashLabel()
        layout.addWidget(self.splash_label)

        layout.addStretch(1)

        self.setLayout(layout)
    
    def setupBackground(self):
        pixmap = QPixmap("resources/splash_bg.jpg")  # 이미지 로드
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setScaledContents(True)  # QLabel 크기에 맞게 이미지 조정
        background_label.resize(*self.screen_size)  # 전체 화면 크기로 설정

    def createSplashLabel(self):
        splash_label = QLabel("스플래시 화면입니다. 클릭하면 넘어갑니다.")
        splash_label.setStyleSheet("color: white; font-size: 32px;")
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

    def mousePressEvent(self, event):
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
            