from PySide6.QtWidgets import QPushButton, QColorDialog, QHBoxLayout, QLabel, QWidget
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal


class ColorPickerButton(QPushButton):
    """컬러 선택 버튼 - 색상 스와치와 텍스트 표시"""
    color_changed = Signal(str)

    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self.color = color
        self.setMinimumSize(100, 30)
        self.setMaximumHeight(32)
        self.update_color(color)
        self.clicked.connect(self.pick_color)

    def update_color(self, color):
        self.color = color
        # 색상 스와치 + 텍스트 스타일
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: #999;
                background-color: #f8f8f8;
            }}
        """)
        # 색상 코드와 스와치 아이콘 표시
        self.setText(f"■ {color}")
        # 텍스트 색상을 선택된 색상으로 설정
        palette = self.palette()
        palette.setColor(palette.ColorRole.ButtonText, QColor(color))
        self.setPalette(palette)

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid():
            self.update_color(color.name())
            self.color_changed.emit(color.name())