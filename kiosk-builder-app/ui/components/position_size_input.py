"""위치/크기 입력 컴포넌트 - 직관적인 UI"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                                QLabel, QFrame)
from PySide6.QtCore import Signal
from ui.components.inputs import NumberLineEdit


class PositionSizeInput(QWidget):
    """위치와 크기를 입력받는 직관적인 컴포넌트

    레이아웃:
    ┌─────────────────────────────────┐
    │ 📍 위치          │ 📐 크기      │
    │ 가로 →  [___]    │ 너비 ↔ [___] │
    │ 세로 ↓  [___]    │ 높이 ↕ [___] │
    └─────────────────────────────────┘
    """

    value_changed = Signal()  # 값 변경 시 발생

    def __init__(self, parent=None, show_position=True, show_size=True):
        super().__init__(parent)
        self.show_position = show_position
        self.show_size = show_size
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # 위치 섹션
        if self.show_position:
            position_widget = self._create_position_section()
            main_layout.addWidget(position_widget)

        # 크기 섹션
        if self.show_size:
            size_widget = self._create_size_section()
            main_layout.addWidget(size_widget)

        main_layout.addStretch()

    def _create_position_section(self):
        """위치 입력 섹션 생성"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # 헤더
        header = QLabel("📍 위치")
        header.setStyleSheet("font-weight: bold; color: #495057; border: none; background: transparent;")
        layout.addWidget(header)

        # 입력 필드들
        grid = QGridLayout()
        grid.setSpacing(8)

        # 가로 (X)
        x_label = QLabel("가로 →")
        x_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        x_label.setFixedWidth(50)
        self.x_input = NumberLineEdit()
        self.x_input.setFixedWidth(70)
        self.x_input.setToolTip("왼쪽에서부터의 거리 (픽셀)")
        self.x_input.textChanged.connect(self._on_value_changed)
        grid.addWidget(x_label, 0, 0)
        grid.addWidget(self.x_input, 0, 1)

        # 세로 (Y)
        y_label = QLabel("세로 ↓")
        y_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        y_label.setFixedWidth(50)
        self.y_input = NumberLineEdit()
        self.y_input.setFixedWidth(70)
        self.y_input.setToolTip("위에서부터의 거리 (픽셀)")
        self.y_input.textChanged.connect(self._on_value_changed)
        grid.addWidget(y_label, 1, 0)
        grid.addWidget(self.y_input, 1, 1)

        layout.addLayout(grid)
        return widget

    def _create_size_section(self):
        """크기 입력 섹션 생성"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # 헤더
        header = QLabel("📐 크기")
        header.setStyleSheet("font-weight: bold; color: #495057; border: none; background: transparent;")
        layout.addWidget(header)

        # 입력 필드들
        grid = QGridLayout()
        grid.setSpacing(8)

        # 너비 (Width)
        w_label = QLabel("너비 ↔")
        w_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        w_label.setFixedWidth(50)
        self.width_input = NumberLineEdit()
        self.width_input.setFixedWidth(70)
        self.width_input.setToolTip("가로 크기 (픽셀)")
        self.width_input.textChanged.connect(self._on_value_changed)
        grid.addWidget(w_label, 0, 0)
        grid.addWidget(self.width_input, 0, 1)

        # 높이 (Height)
        h_label = QLabel("높이 ↕")
        h_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        h_label.setFixedWidth(50)
        self.height_input = NumberLineEdit()
        self.height_input.setFixedWidth(70)
        self.height_input.setToolTip("세로 크기 (픽셀)")
        self.height_input.textChanged.connect(self._on_value_changed)
        grid.addWidget(h_label, 1, 0)
        grid.addWidget(self.height_input, 1, 1)

        layout.addLayout(grid)
        return widget

    def _on_value_changed(self):
        """값 변경 시 시그널 발생"""
        self.value_changed.emit()

    # ═══════════════════════════════════════════════════════════════
    # 값 접근 메서드
    # ═══════════════════════════════════════════════════════════════
    def set_values(self, x=0, y=0, width=0, height=0):
        """모든 값 설정"""
        if self.show_position:
            self.x_input.blockSignals(True)
            self.y_input.blockSignals(True)
            self.x_input.setValue(x)
            self.y_input.setValue(y)
            self.x_input.blockSignals(False)
            self.y_input.blockSignals(False)

        if self.show_size:
            self.width_input.blockSignals(True)
            self.height_input.blockSignals(True)
            self.width_input.setValue(width)
            self.height_input.setValue(height)
            self.width_input.blockSignals(False)
            self.height_input.blockSignals(False)

    def get_values(self):
        """모든 값 반환 (x, y, width, height)"""
        x = self.x_input.value() if self.show_position else 0
        y = self.y_input.value() if self.show_position else 0
        width = self.width_input.value() if self.show_size else 0
        height = self.height_input.value() if self.show_size else 0
        return x, y, width, height

    def get_x(self):
        return self.x_input.value() if self.show_position else 0

    def get_y(self):
        return self.y_input.value() if self.show_position else 0

    def get_width(self):
        return self.width_input.value() if self.show_size else 0

    def get_height(self):
        return self.height_input.value() if self.show_size else 0

    def set_x(self, value):
        if self.show_position:
            self.x_input.blockSignals(True)
            self.x_input.setValue(value)
            self.x_input.blockSignals(False)

    def set_y(self, value):
        if self.show_position:
            self.y_input.blockSignals(True)
            self.y_input.setValue(value)
            self.y_input.blockSignals(False)

    def set_width(self, value):
        if self.show_size:
            self.width_input.blockSignals(True)
            self.width_input.setValue(value)
            self.width_input.blockSignals(False)

    def set_height(self, value):
        if self.show_size:
            self.height_input.blockSignals(True)
            self.height_input.setValue(value)
            self.height_input.blockSignals(False)

    def block_all_signals(self, block: bool):
        """모든 입력 필드의 시그널 차단/해제"""
        if self.show_position:
            self.x_input.blockSignals(block)
            self.y_input.blockSignals(block)
        if self.show_size:
            self.width_input.blockSignals(block)
            self.height_input.blockSignals(block)


class CompactPositionSizeInput(QWidget):
    """컴팩트한 한 줄 위치/크기 입력 컴포넌트

    레이아웃:
    가로 → [___]  세로 ↓ [___]  │  너비 ↔ [___]  높이 ↕ [___]
    """

    value_changed = Signal()

    def __init__(self, parent=None, show_position=True, show_size=True):
        super().__init__(parent)
        self.show_position = show_position
        self.show_size = show_size
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        if self.show_position:
            # 가로 (X)
            x_label = QLabel("가로→")
            x_label.setStyleSheet("color: #6c757d;")
            self.x_input = NumberLineEdit()
            self.x_input.setFixedWidth(60)
            self.x_input.setToolTip("왼쪽에서부터의 거리")
            self.x_input.textChanged.connect(self._on_value_changed)
            main_layout.addWidget(x_label)
            main_layout.addWidget(self.x_input)

            # 세로 (Y)
            y_label = QLabel("세로↓")
            y_label.setStyleSheet("color: #6c757d;")
            self.y_input = NumberLineEdit()
            self.y_input.setFixedWidth(60)
            self.y_input.setToolTip("위에서부터의 거리")
            self.y_input.textChanged.connect(self._on_value_changed)
            main_layout.addWidget(y_label)
            main_layout.addWidget(self.y_input)

        if self.show_position and self.show_size:
            # 구분선
            separator = QFrame()
            separator.setFrameShape(QFrame.VLine)
            separator.setStyleSheet("color: #dee2e6;")
            main_layout.addWidget(separator)

        if self.show_size:
            # 너비 (Width)
            w_label = QLabel("너비↔")
            w_label.setStyleSheet("color: #6c757d;")
            self.width_input = NumberLineEdit()
            self.width_input.setFixedWidth(60)
            self.width_input.setToolTip("가로 크기")
            self.width_input.textChanged.connect(self._on_value_changed)
            main_layout.addWidget(w_label)
            main_layout.addWidget(self.width_input)

            # 높이 (Height)
            h_label = QLabel("높이↕")
            h_label.setStyleSheet("color: #6c757d;")
            self.height_input = NumberLineEdit()
            self.height_input.setFixedWidth(60)
            self.height_input.setToolTip("세로 크기")
            self.height_input.textChanged.connect(self._on_value_changed)
            main_layout.addWidget(h_label)
            main_layout.addWidget(self.height_input)

        main_layout.addStretch()

    def _on_value_changed(self):
        self.value_changed.emit()

    # 값 접근 메서드 (PositionSizeInput과 동일)
    def set_values(self, x=0, y=0, width=0, height=0):
        if self.show_position:
            self.x_input.blockSignals(True)
            self.y_input.blockSignals(True)
            self.x_input.setValue(x)
            self.y_input.setValue(y)
            self.x_input.blockSignals(False)
            self.y_input.blockSignals(False)

        if self.show_size:
            self.width_input.blockSignals(True)
            self.height_input.blockSignals(True)
            self.width_input.setValue(width)
            self.height_input.setValue(height)
            self.width_input.blockSignals(False)
            self.height_input.blockSignals(False)

    def get_values(self):
        x = self.x_input.value() if self.show_position else 0
        y = self.y_input.value() if self.show_position else 0
        width = self.width_input.value() if self.show_size else 0
        height = self.height_input.value() if self.show_size else 0
        return x, y, width, height

    def get_x(self):
        return self.x_input.value() if self.show_position else 0

    def get_y(self):
        return self.y_input.value() if self.show_position else 0

    def get_width(self):
        return self.width_input.value() if self.show_size else 0

    def get_height(self):
        return self.height_input.value() if self.show_size else 0

    def set_x(self, value):
        if self.show_position:
            self.x_input.blockSignals(True)
            self.x_input.setValue(value)
            self.x_input.blockSignals(False)

    def set_y(self, value):
        if self.show_position:
            self.y_input.blockSignals(True)
            self.y_input.setValue(value)
            self.y_input.blockSignals(False)

    def set_width(self, value):
        if self.show_size:
            self.width_input.blockSignals(True)
            self.width_input.setValue(value)
            self.width_input.blockSignals(False)

    def set_height(self, value):
        if self.show_size:
            self.height_input.blockSignals(True)
            self.height_input.setValue(value)
            self.height_input.blockSignals(False)

    def block_all_signals(self, block: bool):
        if self.show_position:
            self.x_input.blockSignals(block)
            self.y_input.blockSignals(block)
        if self.show_size:
            self.width_input.blockSignals(block)
            self.height_input.blockSignals(block)
