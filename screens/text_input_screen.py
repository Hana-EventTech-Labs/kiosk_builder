from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont
from components.hangul_composer import HangulComposer
from components.virtual_keyboard import VirtualKeyboard
from config import config
import os

class CustomLineEdit(QLineEdit):
    def __init__(self, parent=None, index=0, on_focus=None):
        super().__init__(parent)
        self.index = index
        self.on_focus = on_focus
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.on_focus:
            self.on_focus(self)

class TextInputScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.active_input = None  # 현재 활성화된 입력 필드
        self.text_inputs = []  # 모든 텍스트 입력 필드 관리
        self.keyboard = None
        self.setupUI()
    
    def setupUI(self):
        self.setupBackground()
        self.addCloseButton()

        # 커서 변경 이벤트를 연결할 입력 필드 리스트 초기화
        self.text_inputs = []
        
        # 입력 필드 개수
        input_count = config["text_input"]["count"]
        
        # 여러 개의 텍스트 입력 필드 생성
        for i in range(input_count):
            # config.json에서 설정 가져오기
            item_config = config["text_input"]["items"][i] if i < len(config["text_input"]["items"]) else {}
            
            # 레이블 추가 (있는 경우)
            if "label" in item_config:
                label = QLabel(item_config["label"], self)
                # 레이블 위치 설정 (입력 필드 왼쪽)
                label_x = item_config.get("x", 0) + config["text_input"].get("margin_left", 0) - 150
                label_y = item_config.get("y", 0) + config["text_input"].get("margin_top", 0) + i * config["text_input"].get("spacing", 30)
                label.setGeometry(label_x, label_y, 140, 40)
                label.setStyleSheet("color: black; font-size: 18px;")
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # 텍스트 입력 필드 생성 (CustomLineEdit 사용)
            text_input = CustomLineEdit(self, i, self.input_focus_received)
            
            # 위치 및 크기 설정
            width = item_config.get("width", config["text_input"]["common"]["width"])
            height = item_config.get("height", config["text_input"]["common"]["height"])
            x = item_config.get("x", 0) + config["text_input"].get("margin_left", 0)
            y = item_config.get("y", 0) + config["text_input"].get("margin_top", 0) + i * config["text_input"].get("spacing", 30)
            
            text_input.setGeometry(x, y, width, height)
            text_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_input.setFont(QFont('맑은 고딕', config["text_input"]["common"]["font_size"]))
            
            # 플레이스홀더 설정 (있는 경우)
            if "placeholder" in item_config:
                text_input.setPlaceholderText(item_config["placeholder"])
            
            text_input.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 2px solid #00FFC2;
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
            
            # 입력 필드 리스트에 추가
            self.text_inputs.append(text_input)
        
        # 가상 키보드 초기화 (첫 번째 입력 필드 연결)
        if self.text_inputs:
            self.active_input = self.text_inputs[0]
            self.active_input.setFocus()
            
            self.keyboard = VirtualKeyboard(self.active_input)
            self.keyboard.setGeometry(
                config["keyboard"]["x"],
                config["keyboard"]["y"],
                config["keyboard"]["width"],
                config["keyboard"]["height"]
            )
            self.keyboard.setParent(self)
    
    def input_focus_received(self, input_field):
        """입력 필드가 포커스를 받았을 때 호출됨"""
        # print(f"포커스 변경: 인덱스 {input_field.index}로 변경")
        self.active_input = input_field
        
        # 키보드의 대상 입력 필드 변경
        if self.keyboard:
            self.keyboard.input_widget = input_field
            self.keyboard.hangul_composer.reset()  # 한글 작성기 초기화
            self.keyboard.bumper = True  # 새 입력 필드로 전환 시 bumper 플래그 설정
    
    def confirm_pressed(self, event):
        # 모든 입력 필드의 텍스트 저장
        input_texts = {}
        for i, input_field in enumerate(self.text_inputs):
            input_texts[f"text_{i+1}"] = input_field.text()
        
        # JSON 형식으로 저장
        import json
        with open("resources/input_texts.json", "w", encoding="utf-8") as f:
            json.dump(input_texts, f, ensure_ascii=False)
        
        # 이전 방식과의 호환성을 위해 첫 번째 입력 필드만 텍스트 파일로 저장
        if self.text_inputs:
            with open("resources/input_text.txt", "w", encoding="utf-8") as f:
                f.write(self.text_inputs[0].text())
        
        # 다음 화면으로 이동
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
    
    def setupBackground(self):
        # First try index-based files (2.jpg, 2.png), then fallback to generic name
        background_files = ["background/2.png", "background/2.jpg", "background/text_input_bg.jpg"]
        
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
    
    def showEvent(self, event):
        # When screen becomes visible, make sure keyboard is shown
        if self.keyboard:
            self.keyboard.show()
        if self.active_input:
            self.active_input.setFocus()
            
        # Clear any previous text
        for input_field in self.text_inputs:
            input_field.clear()
    
    def hideEvent(self, event):
        # When screen is hidden, hide the keyboard
        if self.keyboard:
            self.keyboard.hide()