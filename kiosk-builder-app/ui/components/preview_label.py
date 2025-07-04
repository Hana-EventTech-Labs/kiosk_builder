from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal, Qt, QPoint, QRect
from PySide6.QtGui import QMouseEvent, QPainter, QPixmap

class DraggablePreviewLabel(QLabel):
    """드래그 앤 드롭을 지원하고 자체적으로 미리보기를 그리는 라벨"""
    position_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._dragging = False
        self._offset = QPoint()

        self._background_pixmap = QPixmap()
        self._overlay_rect = QRect()
        self._overlay_pixmap = QPixmap()
        self._pen = None

        self._original_size = None
        self._scale = 1.0
        self._render_offset = QPoint()

    def set_pen(self, pen):
        """사각형을 그릴 때 사용할 펜 설정"""
        self._pen = pen

    def update_preview(self, bg_pixmap, overlay_rect, overlay_pixmap=None):
        """표시할 배경과 사각형/이미지 업데이트"""
        self._background_pixmap = bg_pixmap
        self._original_size = bg_pixmap.size()
        self._overlay_rect = overlay_rect
        self._overlay_pixmap = overlay_pixmap if overlay_pixmap else QPixmap()
        self._calculate_render_parameters()
        self.update()

    def _calculate_render_parameters(self):
        """렌더링에 필요한 스케일과 오프셋 계산"""
        if self._original_size is None or self.width() == 0 or self.height() == 0:
            return

        # 여백을 고려한 렌더링 영역 계산
        padding = 10 
        render_width = self.width() - padding
        render_height = self.height() - padding

        if render_width <= 0 or render_height <= 0:
            return

        # KeepAspectRatio에 맞는 스케일 계산
        scale_x = self._original_size.width() / render_width
        scale_y = self._original_size.height() / render_height
        self._scale = max(scale_x, scale_y)

        # 중앙 정렬을 위한 오프셋 계산
        scaled_width = self._original_size.width() / self._scale
        scaled_height = self._original_size.height() / self._scale
        self._render_offset = QPoint(
            (self.width() - scaled_width) / 2,
            (self.height() - scaled_height) / 2
        )

    def paintEvent(self, event):
        """배경과 오버레이 사각형을 그림"""
        super().paintEvent(event)
        painter = QPainter(self)
        
        if self._background_pixmap.isNull():
            return

        # 배경 그리기
        target_rect = QRect(self._render_offset.x(), self._render_offset.y(),
                            self._original_size.width() / self._scale,
                            self._original_size.height() / self._scale)
        painter.drawPixmap(target_rect, self._background_pixmap)

        # 오버레이 사각형 또는 이미지 그리기
        if not self._overlay_rect.isNull():
            scaled_rect = self._get_scaled_rect_on_label()
            
            if not self._overlay_pixmap.isNull():
                # 이미지가 있으면 이미지를 그림
                painter.drawPixmap(scaled_rect, self._overlay_pixmap)
            elif self._pen:
                # 펜이 설정되어 있으면 사각형을 그림
                painter.setPen(self._pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(scaled_rect)

    def _get_scaled_rect_on_label(self):
        """원본 좌표의 사각형을 라벨에 그려지는 좌표로 변환"""
        if self._overlay_rect.isNull() or self._scale == 0:
            return QRect()
        
        scaled_x = (self._overlay_rect.x() / self._scale) + self._render_offset.x()
        scaled_y = (self._overlay_rect.y() / self._scale) + self._render_offset.y()
        scaled_w = self._overlay_rect.width() / self._scale
        scaled_h = self._overlay_rect.height() / self._scale
        return QRect(int(scaled_x), int(scaled_y), int(scaled_w), int(scaled_h))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and not self._overlay_rect.isNull():
            scaled_rect = self._get_scaled_rect_on_label()
            if scaled_rect.contains(event.pos()):
                self._dragging = True
                self._offset = event.pos() - scaled_rect.topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            new_pos_on_label = event.pos() - self._offset
            
            # 라벨 좌표를 원본 이미지 좌표로 변환
            original_x = (new_pos_on_label.x() - self._render_offset.x()) * self._scale
            original_y = (new_pos_on_label.y() - self._render_offset.y()) * self._scale

            # 현재 사각형의 크기는 유지하면서 위치만 업데이트
            self._overlay_rect.moveTo(int(original_x), int(original_y))
            self.position_changed.emit(int(original_x), int(original_y))
            self.update() # 다시 그리기

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            
    def resizeEvent(self, event):
        """라벨 크기가 변경될 때 스케일 재계산"""
        super().resizeEvent(event)
        self._calculate_render_parameters() 