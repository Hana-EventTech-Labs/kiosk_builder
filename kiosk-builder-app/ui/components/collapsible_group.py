"""접이식 그룹박스 컴포넌트"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, Signal
from PySide6.QtGui import QFont
from ui.styles.colors import COLORS


class CollapsibleGroupBox(QWidget):
    """접이식 그룹박스 - 헤더 클릭으로 내용 펼침/접기"""

    collapsed_changed = Signal(bool)  # 접힘 상태 변경 시그널

    def __init__(self, title: str, parent=None, collapsed: bool = False):
        super().__init__(parent)
        self._collapsed = collapsed
        self._title = title
        self._animation_duration = 200

        self._init_ui()

        # 초기 상태 설정
        if collapsed:
            self._content_widget.setMaximumHeight(0)
            self._toggle_btn.setText("▶")

    def _init_ui(self):
        """UI 초기화"""
        self.setObjectName("collapsibleGroupBox")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 카드 컨테이너
        self._card = QFrame()
        self._card.setObjectName("cardFrame")
        self._card.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 헤더 영역
        self._header = QFrame()
        self._header.setObjectName("headerFrame")
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.setStyleSheet(f"""
            QFrame#headerFrame {{
                background-color: {COLORS['background_light']};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {COLORS['border']};
                padding: 8px 12px;
            }}
            QFrame#headerFrame:hover {{
                background-color: #F0F0F0;
            }}
        """)

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(8)

        # 토글 버튼 (화살표)
        self._toggle_btn = QPushButton("▼" if not self._collapsed else "▶")
        self._toggle_btn.setObjectName("toggleButton")
        self._toggle_btn.setFixedSize(24, 24)
        self._toggle_btn.setStyleSheet(f"""
            QPushButton#toggleButton {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_dark']};
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        self._toggle_btn.clicked.connect(self.toggle)
        header_layout.addWidget(self._toggle_btn)

        # 타이틀 레이블
        self._title_label = QPushButton(self._title)
        self._title_label.setObjectName("titleLabel")
        self._title_label.setStyleSheet(f"""
            QPushButton#titleLabel {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_dark']};
                font-size: 14px;
                font-weight: bold;
                text-align: left;
                padding: 0;
            }}
        """)
        self._title_label.setCursor(Qt.PointingHandCursor)
        self._title_label.clicked.connect(self.toggle)
        header_layout.addWidget(self._title_label, 1)

        card_layout.addWidget(self._header)

        # 컨텐츠 영역
        self._content_widget = QWidget()
        self._content_widget.setObjectName("contentWidget")
        self._content_widget.setStyleSheet(f"""
            QWidget#contentWidget {{
                background-color: {COLORS['background']};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
        """)

        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(16, 12, 16, 16)
        self._content_layout.setSpacing(10)

        card_layout.addWidget(self._content_widget)

        main_layout.addWidget(self._card)

        # 애니메이션 설정
        self._animation = QPropertyAnimation(self._content_widget, b"maximumHeight")
        self._animation.setDuration(self._animation_duration)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)

    def toggle(self):
        """접기/펼치기 토글"""
        self._collapsed = not self._collapsed
        self._toggle_btn.setText("▶" if self._collapsed else "▼")

        # 컨텐츠 높이 계산 - maximumHeight 제한 해제 후 계산
        self._content_widget.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
        content_height = self._content_layout.sizeHint().height() + 28

        # 최소 높이 보장
        if content_height < 50:
            content_height = 200  # fallback 높이

        if self._collapsed:
            # 접기
            self._animation.setStartValue(content_height)
            self._animation.setEndValue(0)
        else:
            # 펼치기 - 시작 값을 0으로 다시 설정
            self._content_widget.setMaximumHeight(0)
            self._animation.setStartValue(0)
            self._animation.setEndValue(content_height)

        self._animation.start()
        self.collapsed_changed.emit(self._collapsed)

    def setCollapsed(self, collapsed: bool):
        """접힘 상태 설정"""
        if self._collapsed != collapsed:
            self.toggle()

    def isCollapsed(self) -> bool:
        """접힘 상태 반환"""
        return self._collapsed

    def setTitle(self, title: str):
        """타이틀 설정"""
        self._title = title
        self._title_label.setText(title)

    def title(self) -> str:
        """타이틀 반환"""
        return self._title

    def addWidget(self, widget: QWidget):
        """컨텐츠 영역에 위젯 추가"""
        self._content_layout.addWidget(widget)

    def addLayout(self, layout):
        """컨텐츠 영역에 레이아웃 추가"""
        self._content_layout.addLayout(layout)

    def contentLayout(self):
        """컨텐츠 레이아웃 반환"""
        return self._content_layout

    def setContentMargins(self, left, top, right, bottom):
        """컨텐츠 마진 설정"""
        self._content_layout.setContentsMargins(left, top, right, bottom)


class CardGroupBox(QFrame):
    """카드 스타일 그룹박스 - 접이식 없이 카드 스타일만 적용"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        self.setObjectName("cardGroupBox")
        self.setStyleSheet(f"""
            QFrame#cardGroupBox {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 헤더 영역
        self._header = QFrame()
        self._header.setObjectName("cardHeader")
        self._header.setStyleSheet(f"""
            QFrame#cardHeader {{
                background-color: {COLORS['background_light']};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # 타이틀 레이블
        self._title_label = QPushButton(self._title)
        self._title_label.setObjectName("cardTitle")
        self._title_label.setStyleSheet(f"""
            QPushButton#cardTitle {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_dark']};
                font-size: 14px;
                font-weight: bold;
                text-align: left;
                padding: 0;
            }}
        """)
        self._title_label.setEnabled(False)
        header_layout.addWidget(self._title_label, 1)

        main_layout.addWidget(self._header)

        # 컨텐츠 영역
        self._content_widget = QWidget()
        self._content_widget.setObjectName("cardContent")
        self._content_widget.setStyleSheet(f"""
            QWidget#cardContent {{
                background-color: {COLORS['background']};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
        """)

        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(16, 12, 16, 16)
        self._content_layout.setSpacing(10)

        main_layout.addWidget(self._content_widget)

    def setTitle(self, title: str):
        """타이틀 설정"""
        self._title = title
        self._title_label.setText(title)

    def title(self) -> str:
        """타이틀 반환"""
        return self._title

    def addWidget(self, widget: QWidget):
        """컨텐츠 영역에 위젯 추가"""
        self._content_layout.addWidget(widget)

    def addLayout(self, layout):
        """컨텐츠 영역에 레이아웃 추가"""
        self._content_layout.addLayout(layout)

    def contentLayout(self):
        """컨텐츠 레이아웃 반환"""
        return self._content_layout

    def setContentMargins(self, left, top, right, bottom):
        """컨텐츠 마진 설정"""
        self._content_layout.setContentsMargins(left, top, right, bottom)
