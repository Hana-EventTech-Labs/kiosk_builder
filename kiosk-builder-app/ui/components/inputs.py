from PySide6.QtWidgets import QLineEdit, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
import os
from ..styles.colors import COLORS

class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", icon_path=None, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(45)
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        self.setPlaceholderText(placeholder)
        
        # 스타일
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 5px 10px;
                background-color: {COLORS['background_light']};
                color: {COLORS['text_dark']};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)

        if icon_path and os.path.exists(icon_path):
            self.setTextMargins(40, 0, 0, 0)
            
            # 아이콘 레이아웃
            self.icon_layout = QHBoxLayout(self)
            self.icon_layout.setContentsMargins(10, 0, 0, 0)
            self.icon_layout.setSpacing(0)
            
            # 아이콘 라벨
            self.icon_label = QLabel(self)
            self.icon_label.setFixedSize(24, 24)
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            # 아이콘 레이아웃에 추가
            self.icon_layout.addWidget(self.icon_label)
            self.icon_layout.addStretch()