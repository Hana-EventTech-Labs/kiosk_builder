from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QFont, Qt, QFontDatabase

from config import config
import os

class CompleteScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.loadCustomFont()
        self.setupUI()

    def loadCustomFont(self):
        """커스텀 폰트 로드"""
        font_name = config["complete"]["font"]
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
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.complete_label = self.createCompleteLabel()
        self.complete_label.setGeometry(config["complete"]["x"], config["complete"]["y"],
                                       self.complete_label.sizeHint().width(), self.complete_label.sizeHint().height())

    def setupBackground(self):
        # 먼저 인덱스 기반 파일(0.jpg, 0.png)을 찾고, 없으면 기존 파일명 사용
        background_files = ["background/5.png", "background/5.jpg", "background/complete_bg.jpg"]
        
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
    
    def createCompleteLabel(self):
        complete_label = QLabel(self)  # 부모 위젯을 self로 지정
        complete_label.setText(config["complete"]["phrase"])
        
        # 커스텀 폰트 적용
        custom_font = QFont(self.font_family)
        custom_font.setPointSize(config["complete"]["font_size"])
        complete_label.setFont(custom_font)
        
        # 스타일시트 수정 (폰트 패밀리 제거)
        complete_label_style = f""" color: {config["complete"]["font_color"]};"""
        complete_label.setStyleSheet(complete_label_style)
        complete_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return complete_label
        
    def getNextScreenIndex(self):
        self.current_index = 0
        return config["screen_order"][self.current_index]
    
    def showEvent(self, event):
        """화면이 표시될 때 2초 후 스플래시 화면으로 이동"""
        next_index = self.main_window.getNextScreenIndex()
        # print(f"완료 화면에서 다음 인덱스: {next_index}, 타이머: {config['complete']['complete_time']}ms")
        QTimer.singleShot(config["complete"]["complete_time"], 
                        lambda: self.stack.setCurrentIndex(next_index))

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