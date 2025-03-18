from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont
from components.hangul_composer import HangulComposer
from components.virtual_keyboard import VirtualKeyboard
from config import config
import os

class TextInputScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.setupUI()
    
    def setupUI(self):
        self.setupBackground()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Text input area
        input_container = QHBoxLayout()
        input_container.setContentsMargins(
            config["text_input"]["margin_left"],
            config["text_input"]["margin_top"],
            config["text_input"]["margin_right"],
            0
        )
        
        # Text input field
        self.text_input = QLineEdit()
        self.text_input.setFixedSize(
            config["text_input"]["width"],
            config["text_input"]["height"]
        )
        self.text_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_input.setFont(QFont('맑은 고딕', config["text_input"]["font_size"]))
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #00FFC2;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        # Center the input field horizontally
        input_container.addStretch(1)
        input_container.addWidget(self.text_input)
        input_container.addStretch(1)
        
        main_layout.addLayout(input_container)
        main_layout.addStretch(1)
        
        # Initialize the virtual keyboard
        self.keyboard = VirtualKeyboard(self.text_input)
        self.keyboard.setGeometry(
            config["keyboard"]["x"],
            config["keyboard"]["y"],
            config["keyboard"]["width"],
            config["keyboard"]["height"]
        )
        self.keyboard.setParent(self)  # 명시적으로 부모 설정
        self.setLayout(main_layout)
    
    def setupBackground(self):
        # First try index-based files (2.jpg, 2.png), then fallback to generic name
        background_files = ["2.png", "2.jpg", "text_input_bg.jpg"]
        
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
    
    def confirm_pressed(self, event):
        # Save the entered text for printing
        text = self.text_input.text()
        with open("resources/input_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        
        # Move to the next screen
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
    
    def showEvent(self, event):
        # When screen becomes visible, make sure keyboard is shown
        self.keyboard.show()
        self.text_input.setFocus()
        # Clear any previous text
        self.text_input.clear()
    
    def hideEvent(self, event):
        # When screen is hidden, hide the keyboard
        self.keyboard.hide()