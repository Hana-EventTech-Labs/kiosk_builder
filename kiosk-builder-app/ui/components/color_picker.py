from PySide6.QtWidgets import QPushButton, QColorDialog
from PySide6.QtGui import QColor

class ColorPickerButton(QPushButton):
    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self.color = color
        self.setMinimumSize(40, 25)
        self.update_color(color)
        self.clicked.connect(self.pick_color)

    def update_color(self, color):
        self.color = color
        self.setStyleSheet(f"background-color: {color}; min-width: 40px; min-height: 25px;")

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid():
            self.update_color(color.name())