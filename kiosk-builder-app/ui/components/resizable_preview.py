"""
크기 조절 및 위치 이동이 가능한 미리보기 컨테이너 위젯

모든 미리보기 위젯을 감싸서 부드러운 드래그로 크기/위치 조절 기능을 제공합니다.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QSizeGrip
from PySide6.QtCore import Signal, Qt, QPoint, QSize, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPen, QCursor


class ResizeHandle(QWidget):
    """리사이즈 핸들 위젯 - 8방향 지원"""

    # 핸들 위치 상수
    TOP_LEFT = 0
    TOP = 1
    TOP_RIGHT = 2
    LEFT = 3
    RIGHT = 4
    BOTTOM_LEFT = 5
    BOTTOM = 6
    BOTTOM_RIGHT = 7

    # 위치별 커서 매핑
    CURSORS = {
        TOP_LEFT: Qt.SizeFDiagCursor,
        TOP: Qt.SizeVerCursor,
        TOP_RIGHT: Qt.SizeBDiagCursor,
        LEFT: Qt.SizeHorCursor,
        RIGHT: Qt.SizeHorCursor,
        BOTTOM_LEFT: Qt.SizeBDiagCursor,
        BOTTOM: Qt.SizeVerCursor,
        BOTTOM_RIGHT: Qt.SizeFDiagCursor,
    }

    def __init__(self, position: int, parent=None):
        super().__init__(parent)
        self.position = position
        self._handle_size = 8
        self.setFixedSize(self._handle_size, self._handle_size)
        self.setCursor(self.CURSORS.get(position, Qt.ArrowCursor))
        self.setStyleSheet("""
            background-color: #3498db;
            border: 1px solid #2980b9;
            border-radius: 2px;
        """)
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.setStyleSheet("""
            background-color: #2ecc71;
            border: 1px solid #27ae60;
            border-radius: 2px;
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.setStyleSheet("""
            background-color: #3498db;
            border: 1px solid #2980b9;
            border-radius: 2px;
        """)
        super().leaveEvent(event)


class ResizablePreviewContainer(QFrame):
    """
    크기 조절 및 위치 이동이 가능한 미리보기 컨테이너

    Features:
    - 8방향 리사이즈 핸들
    - 부드러운 드래그 이동
    - 최소/최대 크기 제한
    - 비율 유지 옵션
    - 애니메이션 효과
    """

    # 시그널
    size_changed = Signal(int, int)  # (width, height)
    position_changed = Signal(int, int)  # (x, y)

    def __init__(self, parent=None, min_size: QSize = None, max_size: QSize = None):
        """
        Args:
            parent: 부모 위젯
            min_size: 최소 크기 (기본: 150x150)
            max_size: 최대 크기 (기본: 800x800)
        """
        super().__init__(parent)

        # 크기 제한
        self._min_size = min_size or QSize(150, 150)
        self._max_size = max_size or QSize(800, 800)

        # 비율 유지 옵션
        self._keep_aspect_ratio = True
        self._aspect_ratio = 1.0

        # 드래그 상태
        self._dragging = False
        self._resizing = False
        self._resize_handle = None
        self._drag_start_pos = QPoint()
        self._drag_start_geometry = QRect()

        # 내부 위젯
        self._content_widget = None

        # 리사이즈 핸들
        self._handles = {}

        # 스타일
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setStyleSheet("""
            ResizablePreviewContainer {
                background-color: #2a2a2a;
                border: 2px solid #444;
                border-radius: 4px;
            }
            ResizablePreviewContainer:hover {
                border: 2px solid #3498db;
            }
        """)

        # 레이아웃
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(0)

        # 마우스 추적
        self.setMouseTracking(True)

        # 리사이즈 핸들 생성
        self._create_resize_handles()

        # 초기 크기
        self.setMinimumSize(self._min_size)
        self.setMaximumSize(self._max_size)

    def _create_resize_handles(self):
        """8방향 리사이즈 핸들 생성"""
        positions = [
            ResizeHandle.TOP_LEFT,
            ResizeHandle.TOP,
            ResizeHandle.TOP_RIGHT,
            ResizeHandle.LEFT,
            ResizeHandle.RIGHT,
            ResizeHandle.BOTTOM_LEFT,
            ResizeHandle.BOTTOM,
            ResizeHandle.BOTTOM_RIGHT,
        ]

        for pos in positions:
            handle = ResizeHandle(pos, self)
            handle.hide()  # 기본적으로 숨김
            self._handles[pos] = handle

    def _update_handle_positions(self):
        """핸들 위치 업데이트"""
        if not self._handles:
            return

        w = self.width()
        h = self.height()
        hs = 8  # 핸들 크기
        offset = -hs // 2

        # 각 핸들 위치 설정
        self._handles[ResizeHandle.TOP_LEFT].move(offset, offset)
        self._handles[ResizeHandle.TOP].move(w // 2 + offset, offset)
        self._handles[ResizeHandle.TOP_RIGHT].move(w - hs + offset + hs, offset)
        self._handles[ResizeHandle.LEFT].move(offset, h // 2 + offset)
        self._handles[ResizeHandle.RIGHT].move(w - hs + offset + hs, h // 2 + offset)
        self._handles[ResizeHandle.BOTTOM_LEFT].move(offset, h - hs + offset + hs)
        self._handles[ResizeHandle.BOTTOM].move(w // 2 + offset, h - hs + offset + hs)
        self._handles[ResizeHandle.BOTTOM_RIGHT].move(w - hs + offset + hs, h - hs + offset + hs)

    def _show_handles(self):
        """핸들 표시"""
        for handle in self._handles.values():
            handle.show()
            handle.raise_()

    def _hide_handles(self):
        """핸들 숨김"""
        for handle in self._handles.values():
            handle.hide()

    def set_content_widget(self, widget: QWidget):
        """내부 콘텐츠 위젯 설정"""
        # 기존 위젯 제거
        if self._content_widget:
            self._layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)

        self._content_widget = widget
        self._layout.addWidget(widget)

        # 위젯 크기에 맞게 컨테이너 조정
        if widget.minimumSize().isValid():
            content_min = widget.minimumSize()
            self._min_size = QSize(
                content_min.width() + 8,
                content_min.height() + 8
            )
            self.setMinimumSize(self._min_size)

    def set_aspect_ratio(self, width: int, height: int):
        """비율 설정"""
        if height > 0:
            self._aspect_ratio = width / height

    def set_keep_aspect_ratio(self, keep: bool):
        """비율 유지 여부 설정"""
        self._keep_aspect_ratio = keep

    def enterEvent(self, event):
        """마우스 진입 - 핸들 표시"""
        self._show_handles()
        self._update_handle_positions()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """마우스 이탈 - 핸들 숨김"""
        if not self._resizing:
            self._hide_handles()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """마우스 클릭"""
        if event.button() == Qt.LeftButton:
            # 핸들 클릭 확인
            for pos, handle in self._handles.items():
                if handle.geometry().contains(event.pos()):
                    self._resizing = True
                    self._resize_handle = pos
                    self._drag_start_pos = event.globalPos()
                    self._drag_start_geometry = self.geometry()
                    return

            # 드래그 시작 (핸들이 아닌 영역 클릭)
            self._dragging = True
            self._drag_start_pos = event.globalPos()
            self._drag_start_geometry = self.geometry()
            self.setCursor(Qt.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """마우스 이동"""
        if self._resizing and self._resize_handle is not None:
            self._do_resize(event.globalPos())
        elif self._dragging:
            self._do_move(event.globalPos())
        else:
            # 커서 변경
            self._update_cursor(event.pos())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """마우스 릴리즈"""
        if event.button() == Qt.LeftButton:
            if self._dragging:
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
            if self._resizing:
                self._resizing = False
                self._resize_handle = None
                # 마우스가 여전히 위젯 위에 있으면 핸들 유지
                if not self.rect().contains(event.pos()):
                    self._hide_handles()

        super().mouseReleaseEvent(event)

    def _update_cursor(self, pos: QPoint):
        """위치에 따른 커서 업데이트"""
        for handle_pos, handle in self._handles.items():
            if handle.geometry().contains(pos):
                self.setCursor(ResizeHandle.CURSORS.get(handle_pos, Qt.ArrowCursor))
                return
        self.setCursor(Qt.OpenHandCursor)

    def _do_move(self, global_pos: QPoint):
        """드래그 이동 처리"""
        delta = global_pos - self._drag_start_pos
        new_pos = self._drag_start_geometry.topLeft() + delta
        self.move(new_pos)
        self.position_changed.emit(new_pos.x(), new_pos.y())

    def _do_resize(self, global_pos: QPoint):
        """리사이즈 처리"""
        delta = global_pos - self._drag_start_pos
        new_geometry = QRect(self._drag_start_geometry)

        handle = self._resize_handle

        # 방향별 리사이즈 처리
        if handle in [ResizeHandle.TOP_LEFT, ResizeHandle.TOP, ResizeHandle.TOP_RIGHT]:
            new_top = self._drag_start_geometry.top() + delta.y()
            new_height = self._drag_start_geometry.bottom() - new_top + 1
            if new_height >= self._min_size.height() and new_height <= self._max_size.height():
                new_geometry.setTop(new_top)

        if handle in [ResizeHandle.BOTTOM_LEFT, ResizeHandle.BOTTOM, ResizeHandle.BOTTOM_RIGHT]:
            new_height = self._drag_start_geometry.height() + delta.y()
            if new_height >= self._min_size.height() and new_height <= self._max_size.height():
                new_geometry.setHeight(new_height)

        if handle in [ResizeHandle.TOP_LEFT, ResizeHandle.LEFT, ResizeHandle.BOTTOM_LEFT]:
            new_left = self._drag_start_geometry.left() + delta.x()
            new_width = self._drag_start_geometry.right() - new_left + 1
            if new_width >= self._min_size.width() and new_width <= self._max_size.width():
                new_geometry.setLeft(new_left)

        if handle in [ResizeHandle.TOP_RIGHT, ResizeHandle.RIGHT, ResizeHandle.BOTTOM_RIGHT]:
            new_width = self._drag_start_geometry.width() + delta.x()
            if new_width >= self._min_size.width() and new_width <= self._max_size.width():
                new_geometry.setWidth(new_width)

        # 비율 유지 (모서리 핸들에서만)
        if self._keep_aspect_ratio and handle in [
            ResizeHandle.TOP_LEFT, ResizeHandle.TOP_RIGHT,
            ResizeHandle.BOTTOM_LEFT, ResizeHandle.BOTTOM_RIGHT
        ]:
            current_ratio = new_geometry.width() / new_geometry.height() if new_geometry.height() > 0 else 1
            if current_ratio > self._aspect_ratio:
                # 너비가 더 큼 - 높이 기준으로 조정
                new_geometry.setWidth(int(new_geometry.height() * self._aspect_ratio))
            else:
                # 높이가 더 큼 - 너비 기준으로 조정
                new_geometry.setHeight(int(new_geometry.width() / self._aspect_ratio))

        # 적용
        self.setGeometry(new_geometry)
        self._update_handle_positions()

        # 내부 위젯 크기 조정
        if self._content_widget:
            content_size = QSize(
                new_geometry.width() - 8,
                new_geometry.height() - 8
            )
            self._content_widget.setFixedSize(content_size)

        self.size_changed.emit(new_geometry.width(), new_geometry.height())

    def resizeEvent(self, event):
        """크기 변경 이벤트"""
        super().resizeEvent(event)
        self._update_handle_positions()

        # 내부 위젯 크기 동기화
        if self._content_widget:
            content_size = QSize(
                self.width() - 8,
                self.height() - 8
            )
            # FixedSize 제거하고 동적 크기 허용
            self._content_widget.setMinimumSize(content_size)
            self._content_widget.setMaximumSize(content_size)


class ResizableLivePreviewWidget(QWidget):
    """
    LivePreviewWidget을 감싸는 크기 조절 가능한 래퍼

    LivePreviewWidget의 모든 기능을 유지하면서
    드래그로 크기/위치 조절 기능을 추가합니다.
    """

    # 시그널 전달 (컨테이너)
    size_changed = Signal(int, int)
    position_changed = Signal(int, int)
    # 시그널 전달 (내부 요소)
    element_position_changed = Signal(str, int, int)
    element_size_changed = Signal(str, int, int, int, int)

    def __init__(self, parent=None, preview_size: QSize = None,
                 min_size: QSize = None, max_size: QSize = None):
        super().__init__(parent)

        from ui.components.live_preview import LivePreviewWidget

        # 레이아웃
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 컨테이너 생성
        self._container = ResizablePreviewContainer(
            self,
            min_size=min_size or QSize(200, 200),
            max_size=max_size or QSize(600, 600)
        )

        # LivePreviewWidget 생성
        self._preview = LivePreviewWidget(
            parent=None,
            preview_size=preview_size or QSize(300, 300)
        )

        # 컨테이너에 미리보기 위젯 설정
        self._container.set_content_widget(self._preview)

        # 초기 크기 설정
        initial_size = preview_size or QSize(300, 300)
        self._container.setFixedSize(
            initial_size.width() + 8,
            initial_size.height() + 8
        )

        layout.addWidget(self._container)

        # 시그널 연결 (컨테이너)
        self._container.size_changed.connect(self.size_changed.emit)
        self._container.position_changed.connect(self.position_changed.emit)
        # 시그널 연결 (내부 요소)
        self._preview.position_changed.connect(self.element_position_changed.emit)
        self._preview.size_changed.connect(self.element_size_changed.emit)

    @property
    def preview(self):
        """내부 LivePreviewWidget 접근"""
        return self._preview

    # LivePreviewWidget 메서드 위임
    def set_original_size(self, width: int, height: int):
        self._preview.set_original_size(width, height)
        # 비율 설정
        self._container.set_aspect_ratio(width, height)

    def set_background(self, image_path: str, fallback_color: QColor = None):
        self._preview.set_background(image_path, fallback_color)

    def set_background_color(self, color: QColor):
        self._preview.set_background_color(color)

    def add_element(self, element_id: str, rect, color=None, image_path=None,
                    draggable=True, label=None, border_width=2):
        self._preview.add_element(element_id, rect, color, image_path,
                                   draggable, label, border_width)

    def update_element(self, element_id: str, rect=None, image_path=None,
                       color=None, label=None):
        self._preview.update_element(element_id, rect, image_path, color, label)

    def remove_element(self, element_id: str):
        self._preview.remove_element(element_id)

    def clear_elements(self):
        self._preview.clear_elements()

    def get_element_rect(self, element_id: str):
        return self._preview.get_element_rect(element_id)


class ResizableTextPreviewWidget(QWidget):
    """
    TextPreviewWidget을 감싸는 크기 조절 가능한 래퍼

    TextPreviewWidget의 모든 기능을 유지하면서
    드래그로 크기/위치 조절 기능을 추가합니다.
    """

    # 시그널 전달
    size_changed = Signal(int, int)
    position_changed = Signal(int, int)
    element_position_changed = Signal(str, int, int)

    def __init__(self, parent=None, preview_size: QSize = None,
                 min_size: QSize = None, max_size: QSize = None):
        super().__init__(parent)

        from ui.components.live_preview import TextPreviewWidget

        # 레이아웃
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 컨테이너 생성
        self._container = ResizablePreviewContainer(
            self,
            min_size=min_size or QSize(200, 200),
            max_size=max_size or QSize(600, 600)
        )

        # TextPreviewWidget 생성
        self._preview = TextPreviewWidget(
            parent=None,
            preview_size=preview_size or QSize(300, 300)
        )

        # 컨테이너에 미리보기 위젯 설정
        self._container.set_content_widget(self._preview)

        # 초기 크기 설정
        initial_size = preview_size or QSize(300, 300)
        self._container.setFixedSize(
            initial_size.width() + 8,
            initial_size.height() + 8
        )

        layout.addWidget(self._container)

        # 시그널 연결
        self._container.size_changed.connect(self.size_changed.emit)
        self._container.position_changed.connect(self.position_changed.emit)
        self._preview.position_changed.connect(self.element_position_changed.emit)

    @property
    def preview(self):
        """내부 TextPreviewWidget 접근"""
        return self._preview

    # LivePreviewWidget 메서드 위임
    def set_original_size(self, width: int, height: int):
        self._preview.set_original_size(width, height)
        self._container.set_aspect_ratio(width, height)

    def set_background(self, image_path: str, fallback_color: QColor = None):
        self._preview.set_background(image_path, fallback_color)

    def set_background_color(self, color: QColor):
        self._preview.set_background_color(color)

    def add_element(self, element_id: str, rect, color=None, image_path=None,
                    draggable=True, label=None, border_width=2):
        self._preview.add_element(element_id, rect, color, image_path,
                                   draggable, label, border_width)

    def update_element(self, element_id: str, rect=None, image_path=None,
                       color=None, label=None):
        self._preview.update_element(element_id, rect, image_path, color, label)

    def remove_element(self, element_id: str):
        self._preview.remove_element(element_id)

    def clear_elements(self):
        self._preview.clear_elements()

    def get_element_rect(self, element_id: str):
        return self._preview.get_element_rect(element_id)

    # TextPreviewWidget 전용 메서드
    def add_text(self, element_id: str, text: str, x: int, y: int,
                 font_path: str = None, font_size: int = 24,
                 color: QColor = None, draggable: bool = True):
        self._preview.add_text(element_id, text, x, y, font_path, font_size, color, draggable)

    def update_text(self, element_id: str, text: str = None,
                    x: int = None, y: int = None,
                    font_size: int = None, color: QColor = None):
        self._preview.update_text(element_id, text, x, y, font_size, color)

    def remove_text(self, element_id: str):
        self._preview.remove_text(element_id)

    def clear_texts(self):
        self._preview.clear_texts()
