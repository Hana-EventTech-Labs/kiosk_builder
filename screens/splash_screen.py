from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QPropertyAnimation, QSequentialAnimationGroup

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
        self.addCloseButton()

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
            