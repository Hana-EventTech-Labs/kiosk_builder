"""
실시간 미리보기 위젯

실제 배경 이미지를 표시하고 드래그 가능한 오버레이 요소를 지원합니다.
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt, QPoint, QRect, QSize
from PySide6.QtGui import QMouseEvent, QPainter, QPixmap, QColor, QPen, QBrush, QFont
import os


class LivePreviewWidget(QWidget):
    """
    실제 이미지를 배경으로 사용하는 미리보기 위젯

    Features:
    - 배경 이미지 로드 및 표시
    - 다중 오버레이 요소 지원 (사각형, 이미지)
    - 드래그로 위치 조절
    - 드래그로 크기 조절 (4개 모서리 핸들)
    - 실시간 업데이트
    - 스케일 자동 계산
    """

    # 시그널: (element_id, x, y) - 원본 좌표 기준
    position_changed = Signal(str, int, int)
    # 시그널: (element_id, x, y, width, height) - 원본 좌표 기준
    size_changed = Signal(str, int, int, int, int)

    # 리사이즈 핸들 상수
    HANDLE_NONE = 0
    HANDLE_TOP_LEFT = 1
    HANDLE_TOP_RIGHT = 2
    HANDLE_BOTTOM_LEFT = 3
    HANDLE_BOTTOM_RIGHT = 4

    def __init__(self, parent=None, preview_size: QSize = None):
        """
        Args:
            parent: 부모 위젯
            preview_size: 미리보기 크기 (기본: 300x300)
        """
        super().__init__(parent)

        self._preview_size = preview_size or QSize(300, 300)
        self.setFixedSize(self._preview_size)

        # 배경 관련
        self._background_path = ""
        self._background_pixmap = QPixmap()
        self._original_size = QSize(1080, 1920)  # 기본 원본 크기

        # 오버레이 요소들
        # [{id, rect, color, image_path, image_pixmap, draggable, resizable, label}]
        self._overlay_elements = []

        # 드래그 상태
        self._dragging = False
        self._dragging_element_id = None
        self._drag_offset = QPoint()

        # 리사이즈 상태
        self._resizing = False
        self._resize_handle = self.HANDLE_NONE
        self._resize_element_id = None
        self._resize_start_rect = QRect()
        self._resize_start_pos = QPoint()

        # 선택된 요소 (핸들 표시용)
        self._selected_element_id = None

        # 핸들 크기
        self._handle_size = 8

        # 스케일 및 오프셋
        self._scale = 1.0
        self._render_offset = QPoint()

        # 스타일
        self.setStyleSheet("border: 1px solid #ccc; background-color: #2a2a2a;")
        self.setMouseTracking(True)

        # 이미지 캐시
        self._image_cache = {}

    def set_original_size(self, width: int, height: int):
        """원본 크기 설정 (화면 또는 카드 크기)"""
        self._original_size = QSize(width, height)
        self._calculate_render_parameters()
        self.update()

    def set_background(self, image_path: str, fallback_color: QColor = None,
                       use_image_size: bool = False):
        """
        배경 이미지 설정

        Args:
            image_path: 이미지 파일 경로
            fallback_color: 이미지 로드 실패 시 대체 색상
            use_image_size: True면 이미지 크기를 원본 크기로 사용,
                           False면 set_original_size()로 설정한 크기 유지
        """
        self._background_path = image_path

        if image_path and os.path.exists(image_path):
            # 캐시 확인
            if image_path in self._image_cache:
                self._background_pixmap = self._image_cache[image_path]
            else:
                self._background_pixmap = QPixmap(image_path)
                if not self._background_pixmap.isNull():
                    self._image_cache[image_path] = self._background_pixmap

            # use_image_size가 True일 때만 이미지 크기를 원본 크기로 사용
            if use_image_size and not self._background_pixmap.isNull():
                self._original_size = self._background_pixmap.size()
        else:
            # 이미지 없으면 단색 배경
            self._background_pixmap = QPixmap(self._original_size)
            color = fallback_color or QColor("#1a1a1a")
            self._background_pixmap.fill(color)

        self._calculate_render_parameters()
        self.update()

    def set_background_color(self, color: QColor):
        """단색 배경 설정"""
        self._background_pixmap = QPixmap(self._original_size)
        self._background_pixmap.fill(color)
        self._calculate_render_parameters()
        self.update()

    def add_element(self, element_id: str, rect: QRect,
                    color: QColor = None, image_path: str = None,
                    draggable: bool = True, resizable: bool = True,
                    label: str = None, border_width: int = 2):
        """
        오버레이 요소 추가

        Args:
            element_id: 요소 식별자
            rect: 원본 좌표 기준 사각형
            color: 테두리 색상 (이미지가 없을 때)
            image_path: 오버레이 이미지 경로
            draggable: 드래그 가능 여부
            resizable: 크기 조절 가능 여부
            label: 요소 레이블
            border_width: 테두리 두께
        """
        # 기존 요소가 있으면 업데이트
        for element in self._overlay_elements:
            if element['id'] == element_id:
                element['rect'] = rect
                element['color'] = color
                element['draggable'] = draggable
                element['resizable'] = resizable
                element['label'] = label
                element['border_width'] = border_width
                if image_path:
                    element['image_path'] = image_path
                    element['image_pixmap'] = self._load_image(image_path)
                self.update()
                return

        # 새 요소 추가
        image_pixmap = None
        if image_path:
            image_pixmap = self._load_image(image_path)

        self._overlay_elements.append({
            'id': element_id,
            'rect': rect,
            'color': color or QColor("lime"),
            'image_path': image_path,
            'image_pixmap': image_pixmap,
            'draggable': draggable,
            'resizable': resizable,
            'label': label,
            'border_width': border_width
        })
        self.update()

    def update_element(self, element_id: str, rect: QRect = None,
                       image_path: str = None, color: QColor = None,
                       label: str = None):
        """특정 요소 업데이트"""
        for element in self._overlay_elements:
            if element['id'] == element_id:
                if rect is not None:
                    element['rect'] = rect
                if image_path is not None:
                    element['image_path'] = image_path
                    element['image_pixmap'] = self._load_image(image_path)
                if color is not None:
                    element['color'] = color
                if label is not None:
                    element['label'] = label
                self.update()
                return

    def remove_element(self, element_id: str):
        """요소 제거"""
        self._overlay_elements = [
            e for e in self._overlay_elements if e['id'] != element_id
        ]
        self.update()

    def clear_elements(self):
        """모든 요소 제거"""
        self._overlay_elements = []
        self.update()

    def get_element_rect(self, element_id: str) -> QRect:
        """요소의 원본 좌표 사각형 반환"""
        for element in self._overlay_elements:
            if element['id'] == element_id:
                return element['rect']
        return QRect()

    def _load_image(self, image_path: str) -> QPixmap:
        """이미지 로드 (캐시 사용)"""
        if not image_path or not os.path.exists(image_path):
            return QPixmap()

        if image_path in self._image_cache:
            return self._image_cache[image_path]

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self._image_cache[image_path] = pixmap
        return pixmap

    def _calculate_render_parameters(self):
        """렌더링 스케일 및 오프셋 계산"""
        if self._original_size.isEmpty():
            return

        padding = 10
        render_width = self.width() - padding * 2
        render_height = self.height() - padding * 2

        if render_width <= 0 or render_height <= 0:
            return

        # KeepAspectRatio 스케일 계산
        scale_x = self._original_size.width() / render_width
        scale_y = self._original_size.height() / render_height
        self._scale = max(scale_x, scale_y)

        # 중앙 정렬 오프셋
        scaled_width = self._original_size.width() / self._scale
        scaled_height = self._original_size.height() / self._scale
        self._render_offset = QPoint(
            int((self.width() - scaled_width) / 2),
            int((self.height() - scaled_height) / 2)
        )

    def _original_to_preview(self, rect: QRect) -> QRect:
        """원본 좌표 → 미리보기 좌표 변환"""
        if self._scale == 0:
            return QRect()

        x = int(rect.x() / self._scale) + self._render_offset.x()
        y = int(rect.y() / self._scale) + self._render_offset.y()
        w = int(rect.width() / self._scale)
        h = int(rect.height() / self._scale)
        return QRect(x, y, w, h)

    def _preview_to_original(self, point: QPoint) -> QPoint:
        """미리보기 좌표 → 원본 좌표 변환"""
        x = int((point.x() - self._render_offset.x()) * self._scale)
        y = int((point.y() - self._render_offset.y()) * self._scale)
        return QPoint(x, y)

    def _get_handle_rects(self, preview_rect: QRect) -> dict:
        """요소의 4개 모서리 핸들 영역 반환"""
        hs = self._handle_size
        half = hs // 2
        return {
            self.HANDLE_TOP_LEFT: QRect(
                preview_rect.left() - half,
                preview_rect.top() - half,
                hs, hs
            ),
            self.HANDLE_TOP_RIGHT: QRect(
                preview_rect.right() - half,
                preview_rect.top() - half,
                hs, hs
            ),
            self.HANDLE_BOTTOM_LEFT: QRect(
                preview_rect.left() - half,
                preview_rect.bottom() - half,
                hs, hs
            ),
            self.HANDLE_BOTTOM_RIGHT: QRect(
                preview_rect.right() - half,
                preview_rect.bottom() - half,
                hs, hs
            ),
        }

    def _get_handle_at_pos(self, pos: QPoint, element) -> int:
        """주어진 위치에 있는 핸들 반환"""
        if not element.get('resizable', True):
            return self.HANDLE_NONE

        preview_rect = self._original_to_preview(element['rect'])
        handles = self._get_handle_rects(preview_rect)

        for handle_type, handle_rect in handles.items():
            if handle_rect.contains(pos):
                return handle_type

        return self.HANDLE_NONE

    def paintEvent(self, event):
        """렌더링"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 배경 그리기
        if not self._background_pixmap.isNull():
            target_rect = QRect(
                self._render_offset.x(),
                self._render_offset.y(),
                int(self._original_size.width() / self._scale),
                int(self._original_size.height() / self._scale)
            )
            painter.drawPixmap(target_rect, self._background_pixmap)

        # 오버레이 요소들 그리기
        for element in self._overlay_elements:
            preview_rect = self._original_to_preview(element['rect'])

            if element['image_pixmap'] and not element['image_pixmap'].isNull():
                # 이미지 그리기
                painter.drawPixmap(preview_rect, element['image_pixmap'])
            else:
                # 사각형 그리기
                pen = QPen(element['color'], element['border_width'], Qt.SolidLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(preview_rect)

            # 레이블 그리기
            if element.get('label'):
                font = QFont()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)

                # 레이블 배경
                label_rect = QRect(
                    preview_rect.x(),
                    preview_rect.y() - 16,
                    len(element['label']) * 8 + 8,
                    16
                )
                painter.fillRect(label_rect, element['color'])

                # 레이블 텍스트
                painter.setPen(QColor("white"))
                painter.drawText(
                    preview_rect.x() + 4,
                    preview_rect.y() - 4,
                    element['label']
                )

            # 리사이즈 핸들 그리기 (resizable이고 선택된 요소일 때)
            if element.get('resizable', True) and element['id'] == self._selected_element_id:
                handles = self._get_handle_rects(preview_rect)
                painter.setPen(QPen(QColor("#2980b9"), 1))
                painter.setBrush(QBrush(QColor("#3498db")))
                for handle_rect in handles.values():
                    painter.drawRect(handle_rect)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        """마우스 클릭 - 드래그/리사이즈 시작"""
        if event.button() == Qt.LeftButton:
            # 먼저 선택된 요소의 핸들 클릭 확인
            if self._selected_element_id:
                for element in self._overlay_elements:
                    if element['id'] == self._selected_element_id:
                        handle = self._get_handle_at_pos(event.pos(), element)
                        if handle != self.HANDLE_NONE:
                            # 리사이즈 시작
                            self._resizing = True
                            self._resize_handle = handle
                            self._resize_element_id = element['id']
                            self._resize_start_rect = QRect(element['rect'])
                            self._resize_start_pos = event.pos()
                            self._update_cursor_for_handle(handle)
                            return
                        break

            # 클릭된 요소 찾기 (역순으로 검색하여 위에 있는 요소 우선)
            for element in reversed(self._overlay_elements):
                if not element.get('draggable', True) and not element.get('resizable', True):
                    continue

                preview_rect = self._original_to_preview(element['rect'])
                if preview_rect.contains(event.pos()):
                    # 요소 선택
                    self._selected_element_id = element['id']

                    if element.get('draggable', True):
                        self._dragging = True
                        self._dragging_element_id = element['id']
                        self._drag_offset = event.pos() - preview_rect.topLeft()
                        self.setCursor(Qt.ClosedHandCursor)

                    self.update()  # 핸들 표시를 위해 다시 그리기
                    return

            # 빈 영역 클릭 시 선택 해제
            self._selected_element_id = None
            self.update()

    def _update_cursor_for_handle(self, handle: int):
        """핸들 타입에 따른 커서 설정"""
        if handle in [self.HANDLE_TOP_LEFT, self.HANDLE_BOTTOM_RIGHT]:
            self.setCursor(Qt.SizeFDiagCursor)
        elif handle in [self.HANDLE_TOP_RIGHT, self.HANDLE_BOTTOM_LEFT]:
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        """마우스 이동 - 드래그/리사이즈 중"""
        # 리사이즈 중
        if self._resizing and self._resize_element_id:
            self._do_resize(event.pos())
            return

        # 드래그 중
        if self._dragging and self._dragging_element_id:
            new_preview_pos = event.pos() - self._drag_offset
            new_original_pos = self._preview_to_original(new_preview_pos)

            # 요소 위치 업데이트
            for element in self._overlay_elements:
                if element['id'] == self._dragging_element_id:
                    element['rect'].moveTo(new_original_pos)
                    self.position_changed.emit(
                        element['id'],
                        new_original_pos.x(),
                        new_original_pos.y()
                    )
                    break

            self.update()
            return

        # 호버 시 커서 변경
        # 먼저 선택된 요소의 핸들 확인
        if self._selected_element_id:
            for element in self._overlay_elements:
                if element['id'] == self._selected_element_id:
                    handle = self._get_handle_at_pos(event.pos(), element)
                    if handle != self.HANDLE_NONE:
                        self._update_cursor_for_handle(handle)
                        return
                    break

        # 요소 위에 있으면 이동 커서
        for element in reversed(self._overlay_elements):
            if not element.get('draggable', True):
                continue
            preview_rect = self._original_to_preview(element['rect'])
            if preview_rect.contains(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
                return

        self.setCursor(Qt.ArrowCursor)

    def _do_resize(self, pos: QPoint):
        """리사이즈 처리"""
        if not self._resize_element_id:
            return

        # 미리보기 좌표에서의 이동량 계산
        delta = pos - self._resize_start_pos

        # 원본 좌표에서의 이동량으로 변환
        delta_original_x = int(delta.x() * self._scale)
        delta_original_y = int(delta.y() * self._scale)

        # 시작 rect 복사
        start_rect = self._resize_start_rect
        new_rect = QRect(start_rect)

        # 핸들에 따른 크기 조정
        if self._resize_handle == self.HANDLE_TOP_LEFT:
            new_rect.setLeft(start_rect.left() + delta_original_x)
            new_rect.setTop(start_rect.top() + delta_original_y)
        elif self._resize_handle == self.HANDLE_TOP_RIGHT:
            new_rect.setRight(start_rect.right() + delta_original_x)
            new_rect.setTop(start_rect.top() + delta_original_y)
        elif self._resize_handle == self.HANDLE_BOTTOM_LEFT:
            new_rect.setLeft(start_rect.left() + delta_original_x)
            new_rect.setBottom(start_rect.bottom() + delta_original_y)
        elif self._resize_handle == self.HANDLE_BOTTOM_RIGHT:
            new_rect.setRight(start_rect.right() + delta_original_x)
            new_rect.setBottom(start_rect.bottom() + delta_original_y)

        # 최소 크기 보장
        min_size = 20
        if new_rect.width() < min_size:
            if self._resize_handle in [self.HANDLE_TOP_LEFT, self.HANDLE_BOTTOM_LEFT]:
                new_rect.setLeft(new_rect.right() - min_size)
            else:
                new_rect.setRight(new_rect.left() + min_size)
        if new_rect.height() < min_size:
            if self._resize_handle in [self.HANDLE_TOP_LEFT, self.HANDLE_TOP_RIGHT]:
                new_rect.setTop(new_rect.bottom() - min_size)
            else:
                new_rect.setBottom(new_rect.top() + min_size)

        # 요소 업데이트
        for element in self._overlay_elements:
            if element['id'] == self._resize_element_id:
                element['rect'] = new_rect
                self.size_changed.emit(
                    element['id'],
                    new_rect.x(),
                    new_rect.y(),
                    new_rect.width(),
                    new_rect.height()
                )
                break

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """마우스 릴리즈 - 드래그/리사이즈 종료"""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._dragging_element_id = None
            self._resizing = False
            self._resize_handle = self.HANDLE_NONE
            self._resize_element_id = None
            self.setCursor(Qt.ArrowCursor)

    def resizeEvent(self, event):
        """크기 변경 시 스케일 재계산"""
        super().resizeEvent(event)
        self._calculate_render_parameters()


class TextPreviewWidget(LivePreviewWidget):
    """
    텍스트를 실제 폰트로 렌더링하는 미리보기 위젯

    Features:
    - 실제 폰트 파일 로드
    - 텍스트 렌더링
    - 텍스트 위치 드래그
    - 텍스트 크기 조절 (드래그)
    """

    # 텍스트 크기 변경 시그널: (element_id, new_font_size)
    text_size_changed = Signal(str, int)

    def __init__(self, parent=None, preview_size: QSize = None):
        super().__init__(parent, preview_size)

        # 텍스트 요소들
        # [{id, text, x, y, font_path, font_size, color, draggable, resizable}]
        self._text_elements = []

        # 텍스트 선택 및 리사이즈 상태
        self._selected_text_id = None
        self._text_resizing = False
        self._text_resize_handle = self.HANDLE_NONE
        self._text_resize_start_size = 0
        self._text_resize_start_pos = QPoint()

    def add_text(self, element_id: str, text: str, x: int, y: int,
                 font_path: str = None, font_size: int = 24,
                 color: QColor = None, draggable: bool = True,
                 resizable: bool = True):
        """
        텍스트 요소 추가

        Args:
            element_id: 요소 식별자
            text: 표시할 텍스트
            x, y: 원본 좌표
            font_path: 폰트 파일 경로
            font_size: 폰트 크기
            color: 텍스트 색상
            draggable: 드래그 가능 여부
            resizable: 크기 조절 가능 여부
        """
        # 기존 요소 업데이트
        for elem in self._text_elements:
            if elem['id'] == element_id:
                elem['text'] = text
                elem['x'] = x
                elem['y'] = y
                elem['font_path'] = font_path
                elem['font_size'] = font_size
                elem['color'] = color or QColor("black")
                elem['draggable'] = draggable
                elem['resizable'] = resizable
                self.update()
                return

        # 새 요소 추가
        self._text_elements.append({
            'id': element_id,
            'text': text,
            'x': x,
            'y': y,
            'font_path': font_path,
            'font_size': font_size,
            'color': color or QColor("black"),
            'draggable': draggable,
            'resizable': resizable
        })
        self.update()

    def update_text(self, element_id: str, text: str = None,
                    x: int = None, y: int = None,
                    font_size: int = None, color: QColor = None):
        """텍스트 요소 업데이트"""
        for elem in self._text_elements:
            if elem['id'] == element_id:
                if text is not None:
                    elem['text'] = text
                if x is not None:
                    elem['x'] = x
                if y is not None:
                    elem['y'] = y
                if font_size is not None:
                    elem['font_size'] = font_size
                if color is not None:
                    elem['color'] = color
                self.update()
                return

    def remove_text(self, element_id: str):
        """텍스트 요소 제거"""
        self._text_elements = [
            e for e in self._text_elements if e['id'] != element_id
        ]
        self.update()

    def clear_texts(self):
        """모든 텍스트 제거"""
        self._text_elements = []
        self.update()

    def _get_text_rect(self, elem) -> QRect:
        """텍스트 요소의 미리보기 좌표 경계 사각형 반환"""
        preview_x = int(elem['x'] / self._scale) + self._render_offset.x()
        preview_y = int(elem['y'] / self._scale) + self._render_offset.y()
        font_size_preview = int(elem['font_size'] / self._scale)

        # 텍스트 폭 대략 계산 (글자당 0.6 * font_size)
        text_width = int(len(elem['text']) * font_size_preview * 0.6) + 20
        text_height = font_size_preview + 10

        return QRect(
            preview_x - 5,
            preview_y - font_size_preview,
            text_width,
            text_height
        )

    def _get_text_resize_handle(self, pos: QPoint, elem) -> int:
        """텍스트 요소의 리사이즈 핸들 확인 (우하단만 사용)"""
        if not elem.get('resizable', True):
            return self.HANDLE_NONE

        text_rect = self._get_text_rect(elem)
        hs = self._handle_size

        # 우하단 핸들만 사용 (크기 조절용)
        handle_rect = QRect(
            text_rect.right() - hs // 2,
            text_rect.bottom() - hs // 2,
            hs, hs
        )

        if handle_rect.contains(pos):
            return self.HANDLE_BOTTOM_RIGHT

        return self.HANDLE_NONE

    def paintEvent(self, event):
        """렌더링 (배경 + 오버레이 + 텍스트)"""
        # 부모 클래스 렌더링 (배경 + 오버레이)
        super().paintEvent(event)

        # 텍스트 렌더링
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)

        for elem in self._text_elements:
            # 폰트 설정
            font = QFont()
            if elem['font_path'] and os.path.exists(elem['font_path']):
                font.setFamily(elem['font_path'])
            font.setPointSize(int(elem['font_size'] / self._scale))

            painter.setFont(font)
            painter.setPen(QPen(elem['color']))

            # 원본 좌표를 미리보기 좌표로 변환
            preview_x = int(elem['x'] / self._scale) + self._render_offset.x()
            preview_y = int(elem['y'] / self._scale) + self._render_offset.y()

            painter.drawText(preview_x, preview_y, elem['text'])

            # 선택된 텍스트에 경계선 및 리사이즈 핸들 표시
            if elem['id'] == self._selected_text_id and elem.get('resizable', True):
                text_rect = self._get_text_rect(elem)

                # 선택 경계선
                painter.setPen(QPen(QColor("#3498db"), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(text_rect)

                # 리사이즈 핸들 (우하단)
                hs = self._handle_size
                handle_rect = QRect(
                    text_rect.right() - hs // 2,
                    text_rect.bottom() - hs // 2,
                    hs, hs
                )
                painter.setPen(QPen(QColor("#2980b9"), 1))
                painter.setBrush(QBrush(QColor("#3498db")))
                painter.drawRect(handle_rect)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        """마우스 클릭 - 텍스트 드래그/리사이즈 시작"""
        if event.button() == Qt.LeftButton:
            # 1. 선택된 텍스트의 리사이즈 핸들 클릭 확인
            if self._selected_text_id:
                for elem in self._text_elements:
                    if elem['id'] == self._selected_text_id:
                        handle = self._get_text_resize_handle(event.pos(), elem)
                        if handle != self.HANDLE_NONE:
                            # 리사이즈 시작
                            self._text_resizing = True
                            self._text_resize_handle = handle
                            self._text_resize_start_size = elem['font_size']
                            self._text_resize_start_pos = event.pos()
                            self.setCursor(Qt.SizeFDiagCursor)
                            return
                        break

            # 2. 텍스트 요소 클릭 확인
            for elem in reversed(self._text_elements):
                text_rect = self._get_text_rect(elem)

                if text_rect.contains(event.pos()):
                    # 요소 선택
                    self._selected_text_id = elem['id']
                    self.update()

                    if elem.get('draggable', True):
                        preview_x = int(elem['x'] / self._scale) + self._render_offset.x()
                        preview_y = int(elem['y'] / self._scale) + self._render_offset.y()
                        self._dragging = True
                        self._dragging_element_id = elem['id']
                        self._drag_offset = event.pos() - QPoint(preview_x, preview_y)
                        self.setCursor(Qt.ClosedHandCursor)
                    return

            # 빈 영역 클릭 시 선택 해제
            self._selected_text_id = None
            self.update()

        # 부모 클래스 이벤트 처리
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """마우스 이동 - 텍스트 드래그/리사이즈"""
        # 텍스트 리사이즈 중
        if self._text_resizing and self._selected_text_id:
            for elem in self._text_elements:
                if elem['id'] == self._selected_text_id:
                    # 마우스 이동량으로 폰트 크기 계산
                    delta_y = event.pos().y() - self._text_resize_start_pos.y()
                    # 미리보기 좌표 -> 원본 좌표 스케일 적용
                    size_change = int(delta_y * self._scale * 0.5)
                    new_size = max(8, self._text_resize_start_size + size_change)  # 최소 8pt

                    elem['font_size'] = new_size
                    self.text_size_changed.emit(elem['id'], new_size)
                    self.update()
                    return

        # 텍스트 드래그 중
        if self._dragging and self._dragging_element_id:
            # 텍스트 요소인지 확인
            for elem in self._text_elements:
                if elem['id'] == self._dragging_element_id:
                    new_preview_pos = event.pos() - self._drag_offset
                    new_original_x = int((new_preview_pos.x() - self._render_offset.x()) * self._scale)
                    new_original_y = int((new_preview_pos.y() - self._render_offset.y()) * self._scale)

                    elem['x'] = new_original_x
                    elem['y'] = new_original_y

                    self.position_changed.emit(elem['id'], new_original_x, new_original_y)
                    self.update()
                    return

        # 호버 시 커서 변경
        if self._selected_text_id:
            for elem in self._text_elements:
                if elem['id'] == self._selected_text_id:
                    handle = self._get_text_resize_handle(event.pos(), elem)
                    if handle != self.HANDLE_NONE:
                        self.setCursor(Qt.SizeFDiagCursor)
                        return
                    break

        # 텍스트 위에 있으면 이동 커서
        for elem in reversed(self._text_elements):
            if not elem.get('draggable', True):
                continue
            text_rect = self._get_text_rect(elem)
            if text_rect.contains(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
                return

        # 부모 클래스 이벤트 처리
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """마우스 릴리즈 - 드래그/리사이즈 종료"""
        if event.button() == Qt.LeftButton:
            # 텍스트 리사이즈 종료
            if self._text_resizing:
                self._text_resizing = False
                self._text_resize_handle = self.HANDLE_NONE
                self.setCursor(Qt.ArrowCursor)
                return

            # 드래그 종료
            self._dragging = False
            self._dragging_element_id = None
            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)
