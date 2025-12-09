"""
확대/축소 기능이 포함된 미리보기 래퍼 위젯

LivePreviewWidget 또는 TextPreviewWidget을 감싸서 확대/축소 컨트롤을 제공합니다.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QScrollArea, QFrame, QSpinBox, QToolButton)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QWheelEvent


# 기본 미리보기 크기 상수
DEFAULT_PREVIEW_SIZE = QSize(400, 400)


class ZoomablePreviewWidget(QWidget):
    """
    확대/축소 기능이 포함된 미리보기 래퍼 위젯

    Features:
    - 줌 슬라이더로 50% ~ 200% 확대/축소
    - 마우스 휠로 확대/축소
    - +/- 버튼으로 단계별 확대/축소
    - 100% 리셋 버튼
    """

    zoom_changed = Signal(int)  # 줌 레벨 변경 시그널 (퍼센트)

    def __init__(self, preview_widget: QWidget, parent=None,
                 min_zoom: int = 50, max_zoom: int = 200, default_zoom: int = 100):
        """
        Args:
            preview_widget: LivePreviewWidget 또는 TextPreviewWidget 인스턴스
            parent: 부모 위젯
            min_zoom: 최소 줌 레벨 (%)
            max_zoom: 최대 줌 레벨 (%)
            default_zoom: 기본 줌 레벨 (%)
        """
        super().__init__(parent)

        self._preview_widget = preview_widget
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom
        self._current_zoom = default_zoom
        self._base_size = preview_widget.size()

        self._init_ui()
        self._apply_zoom()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 스크롤 영역 (확대 시 스크롤 가능)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(False)
        self._scroll_area.setAlignment(Qt.AlignCenter)
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        self._scroll_area.setWidget(self._preview_widget)

        # 스크롤 영역 최소 크기 설정
        self._scroll_area.setMinimumSize(self._base_size.width() + 20, self._base_size.height() + 20)

        layout.addWidget(self._scroll_area, 1)

        # 줌 컨트롤 바 (SpinBox 기반 컴팩트 디자인)
        zoom_bar = QFrame()
        zoom_bar.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        zoom_bar.setFixedHeight(32)
        zoom_layout = QHBoxLayout(zoom_bar)
        zoom_layout.setContentsMargins(6, 2, 6, 2)
        zoom_layout.setSpacing(4)

        # 중앙 정렬
        zoom_layout.addStretch()

        # 축소 버튼
        self._zoom_out_btn = QToolButton()
        self._zoom_out_btn.setText("−")
        self._zoom_out_btn.setFixedSize(24, 24)
        self._zoom_out_btn.setToolTip("축소 (Ctrl+휠)")
        self._zoom_out_btn.setStyleSheet("""
            QToolButton {
                background: #e0e0e0;
                border: none;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover { background: #d0d0d0; }
            QToolButton:pressed { background: #c0c0c0; }
            QToolButton:disabled { color: #aaa; }
        """)
        self._zoom_out_btn.clicked.connect(self._zoom_out)
        zoom_layout.addWidget(self._zoom_out_btn)

        # SpinBox로 퍼센트 표시 및 입력
        self._zoom_spinbox = QSpinBox()
        self._zoom_spinbox.setRange(self._min_zoom, self._max_zoom)
        self._zoom_spinbox.setValue(self._current_zoom)
        self._zoom_spinbox.setSuffix("%")
        self._zoom_spinbox.setFixedWidth(65)
        self._zoom_spinbox.setAlignment(Qt.AlignCenter)
        self._zoom_spinbox.setButtonSymbols(QSpinBox.NoButtons)
        self._zoom_spinbox.setToolTip("직접 입력 가능 (50~200%)")
        self._zoom_spinbox.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px;
                font-size: 11px;
                font-weight: bold;
            }
            QSpinBox:focus {
                border-color: #2196F3;
            }
        """)
        self._zoom_spinbox.valueChanged.connect(self._on_spinbox_changed)
        zoom_layout.addWidget(self._zoom_spinbox)

        # 확대 버튼
        self._zoom_in_btn = QToolButton()
        self._zoom_in_btn.setText("+")
        self._zoom_in_btn.setFixedSize(24, 24)
        self._zoom_in_btn.setToolTip("확대 (Ctrl+휠)")
        self._zoom_in_btn.setStyleSheet(self._zoom_out_btn.styleSheet())
        self._zoom_in_btn.clicked.connect(self._zoom_in)
        zoom_layout.addWidget(self._zoom_in_btn)

        # 중앙 정렬
        zoom_layout.addStretch()

        layout.addWidget(zoom_bar)

    def _apply_zoom(self):
        """현재 줌 레벨 적용"""
        scale = self._current_zoom / 100.0
        new_width = int(self._base_size.width() * scale)
        new_height = int(self._base_size.height() * scale)

        self._preview_widget.setFixedSize(new_width, new_height)

        # SpinBox 값 동기화 (시그널 블록하여 무한 루프 방지)
        self._zoom_spinbox.blockSignals(True)
        self._zoom_spinbox.setValue(self._current_zoom)
        self._zoom_spinbox.blockSignals(False)

        # 버튼 상태 업데이트
        self._zoom_out_btn.setEnabled(self._current_zoom > self._min_zoom)
        self._zoom_in_btn.setEnabled(self._current_zoom < self._max_zoom)

        self.zoom_changed.emit(self._current_zoom)

    def _on_spinbox_changed(self, value: int):
        """SpinBox 값 변경"""
        self._current_zoom = value
        self._apply_zoom()

    def _zoom_in(self):
        """확대 (10% 단위)"""
        new_zoom = min(self._current_zoom + 10, self._max_zoom)
        self._zoom_spinbox.setValue(new_zoom)

    def _zoom_out(self):
        """축소 (10% 단위)"""
        new_zoom = max(self._current_zoom - 10, self._min_zoom)
        self._zoom_spinbox.setValue(new_zoom)

    def set_zoom(self, zoom_percent: int):
        """줌 레벨 설정"""
        zoom_percent = max(self._min_zoom, min(self._max_zoom, zoom_percent))
        self._zoom_spinbox.setValue(zoom_percent)

    def get_zoom(self) -> int:
        """현재 줌 레벨 반환"""
        return self._current_zoom

    def get_preview_widget(self) -> QWidget:
        """내부 미리보기 위젯 반환"""
        return self._preview_widget

    def wheelEvent(self, event: QWheelEvent):
        """마우스 휠 이벤트 (Ctrl+휠로 줌)"""
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            elif delta < 0:
                self._zoom_out()
            event.accept()
        else:
            # Ctrl 없이 휠 사용 시 스크롤
            super().wheelEvent(event)


def create_zoomable_preview(preview_widget_class, preview_size: QSize = None,
                            parent=None, **preview_kwargs):
    """
    확대/축소 기능이 포함된 미리보기 위젯 생성 헬퍼 함수

    Args:
        preview_widget_class: LivePreviewWidget 또는 TextPreviewWidget 클래스
        preview_size: 미리보기 기본 크기 (기본: 400x400)
        parent: 부모 위젯
        **preview_kwargs: 미리보기 위젯에 전달할 추가 인자

    Returns:
        tuple: (ZoomablePreviewWidget, 내부 preview_widget)
    """
    size = preview_size or DEFAULT_PREVIEW_SIZE
    preview_widget = preview_widget_class(preview_size=size, **preview_kwargs)
    zoomable = ZoomablePreviewWidget(preview_widget, parent=parent)
    return zoomable, preview_widget
