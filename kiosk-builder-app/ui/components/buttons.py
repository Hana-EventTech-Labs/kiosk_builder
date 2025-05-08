from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
from ..styles.colors import COLORS

class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(45)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)
        
        # 기본 스타일
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_darker']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['disabled']};
                color: {COLORS['disabled_text']};
            }}
        """)
        
        # 버튼 누름 애니메이션
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(100)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 살짝 눌림 효과 생성
            rect = self.geometry()
            target_rect = rect.adjusted(2, 2, -2, -2)
            
            self._animation.setStartValue(rect)
            self._animation.setEndValue(target_rect)
            self._animation.start()
            
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 원래 크기로 복원
            rect = self.geometry()
            target_rect = rect.adjusted(-2, -2, 2, 2)
            
            self._animation.setStartValue(rect)
            self._animation.setEndValue(target_rect)
            self._animation.start()
            
        super().mouseReleaseEvent(event)
        
    def set_loading(self, is_loading=True):
        """로딩 상태 설정"""
        if is_loading:
            self.setEnabled(False)
            self.setText("로그인 중...")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['disabled']};
                    color: {COLORS['disabled_text']};
                    border: none;
                    border-radius: 8px;
                    padding: 10px;
                }}
            """)
        else:
            self.setEnabled(True)
            self.setText("로그인")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_dark']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['primary_darker']};
                }}
            """)