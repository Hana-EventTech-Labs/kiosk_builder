"""
플로팅 최종 카드 미리보기 다이얼로그

모든 탭에서 설정한 인쇄 요소들을 통합하여 실제 인쇄될 형태로 미리보기합니다.
- 사진 영역 (촬영 화면) - 플레이스홀더 이미지
- QR 이미지 (QR 화면) - 실제 이미지 또는 플레이스홀더
- 사용자 입력 텍스트 (키보드 화면) - 실제 폰트/색상/크기 렌더링
- 고정 텍스트 (키보드 화면) - 실제 폰트/색상/크기 렌더링
- 기본 이미지들 (기본 설정) - 실제 이미지 렌더링
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QWidget, QSizeGrip, QFrame
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QFontMetrics, QFontDatabase, QBrush
from ui.styles.colors import COLORS


class FloatingCardPreviewDialog(QDialog):
    """
    플로팅 최종 카드 미리보기 다이얼로그

    Features:
    - 항상 위에 표시 옵션
    - 실시간 업데이트
    - 리사이즈 가능
    - 드래그로 이동 가능
    """

    # 다이얼로그가 닫힐 때 시그널
    closed = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._drag_pos = None

        self.setWindowTitle("최종 카드 미리보기")
        self.setMinimumSize(350, 450)
        self.resize(400, 550)

        # 프레임리스 윈도우 + 항상 위 옵션
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.CustomizeWindowHint |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint
        )

        self._init_ui()
        self._apply_styles()
        self.update_preview()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 헤더 (드래그 영역 + 컨트롤)
        self._create_header(layout)

        # 미리보기 영역
        self._create_preview_area(layout)

        # 푸터 (옵션 + 리사이즈 그립)
        self._create_footer(layout)

    def _create_header(self, parent_layout):
        """헤더 영역 생성 (타이틀 + 닫기 버튼)"""
        header = QWidget()
        header.setObjectName("dialogHeader")
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        header_layout.setSpacing(8)

        # 아이콘 + 타이틀
        title_label = QLabel("🖼️ 최종 카드 미리보기")
        title_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: white;
        """)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 닫기 버튼
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)

        parent_layout.addWidget(header)

        # 헤더 드래그 이벤트 설정
        header.mousePressEvent = self._header_mouse_press
        header.mouseMoveEvent = self._header_mouse_move
        header.mouseReleaseEvent = self._header_mouse_release

    def _create_preview_area(self, parent_layout):
        """미리보기 영역 생성"""
        preview_container = QWidget()
        preview_container.setObjectName("previewContainer")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(12, 12, 12, 8)
        preview_layout.setAlignment(Qt.AlignCenter)

        # 미리보기 라벨
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(300, 350)
        self.preview_label.setStyleSheet("""
            background-color: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 4px;
        """)
        preview_layout.addWidget(self.preview_label, 1)

        parent_layout.addWidget(preview_container, 1)

    def _create_footer(self, parent_layout):
        """푸터 영역 생성 (옵션 + 정보)"""
        footer = QWidget()
        footer.setObjectName("dialogFooter")
        footer.setFixedHeight(36)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 0, 4, 4)
        footer_layout.setSpacing(8)

        # 항상 위에 표시 체크박스
        self.always_on_top_check = QCheckBox("항상 위에 표시")
        self.always_on_top_check.setChecked(True)
        self.always_on_top_check.setStyleSheet("""
            QCheckBox {
                color: #666;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """)
        self.always_on_top_check.toggled.connect(self._toggle_always_on_top)
        footer_layout.addWidget(self.always_on_top_check)

        footer_layout.addStretch()

        # 카드 크기 정보
        self.size_info_label = QLabel("636 × 1012 px")
        self.size_info_label.setStyleSheet("color: #999; font-size: 10px;")
        footer_layout.addWidget(self.size_info_label)

        # 리사이즈 그립
        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)
        footer_layout.addWidget(size_grip)

        parent_layout.addWidget(footer)

    def _apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: white;
                border: 1px solid {COLORS['primary']};
                border-radius: 8px;
            }}
            #dialogHeader {{
                background-color: {COLORS['primary']};
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
            }}
            #previewContainer {{
                background-color: white;
            }}
            #dialogFooter {{
                background-color: #f8f9fa;
                border-top: 1px solid #e9ecef;
                border-bottom-left-radius: 7px;
                border-bottom-right-radius: 7px;
            }}
        """)

    def _header_mouse_press(self, event):
        """헤더 마우스 프레스 - 드래그 시작"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _header_mouse_move(self, event):
        """헤더 마우스 이동 - 드래그 중"""
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _header_mouse_release(self, event):
        """헤더 마우스 릴리즈 - 드래그 종료"""
        self._drag_pos = None

    def _toggle_always_on_top(self, checked):
        """항상 위에 표시 토글"""
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()  # 플래그 변경 후 다시 표시

    def update_config(self, config):
        """설정 업데이트 및 미리보기 갱신"""
        self.config = config
        self.update_preview()

    def update_preview(self):
        """미리보기 업데이트"""
        if not self.preview_label:
            return

        # 카드 크기
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        # 크기 정보 업데이트
        self.size_info_label.setText(f"{card_width} × {card_height} px")

        # 카드 배경 생성
        card_pixmap = QPixmap(card_width, card_height)

        # 베이스 카드 이미지가 있으면 로드
        base_card_path = self.config.get("card", {}).get("background", "")
        if base_card_path:
            import os
            if os.path.exists(base_card_path):
                base_pixmap = QPixmap(base_card_path)
                if not base_pixmap.isNull():
                    card_pixmap = base_pixmap.scaled(
                        card_width, card_height,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                else:
                    card_pixmap.fill(Qt.white)
            else:
                card_pixmap.fill(Qt.white)
        else:
            card_pixmap.fill(Qt.white)

        painter = QPainter(card_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 화면 순서 확인
        screen_order = self.config.get("screen_order", [])

        # 1. 촬영 사진 영역
        if 1 in screen_order:
            self._draw_photo_area(painter)

        # 2. 텍스트 영역 (키보드 화면)
        if 2 in screen_order:
            self._draw_text_areas(painter)

        # 3. QR 이미지 영역
        if 3 in screen_order:
            self._draw_qr_area(painter)

        # 4. 기본 이미지들
        self._draw_basic_images(painter)

        # 5. 카드 테두리
        border_pen = QPen(QColor("#333333"), 3, Qt.SolidLine)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(1, 1, card_width - 3, card_height - 3)

        painter.end()

        # 미리보기 라벨 크기에 맞게 스케일
        label_size = self.preview_label.size()
        scaled_pixmap = card_pixmap.scaled(
            label_size.width() - 4,
            label_size.height() - 4,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def _draw_photo_area(self, painter):
        """촬영 사진 영역 그리기 - 실제 인쇄처럼 플레이스홀더 표시"""
        photo_config = self.config.get("photo", {})
        x = photo_config.get("x", 0)
        y = photo_config.get("y", 0)
        width = photo_config.get("width", 300)
        height = photo_config.get("height", 300)

        # 사진 영역 배경 (연한 회색 - 실제 사진이 들어갈 자리)
        painter.fillRect(x, y, width, height, QColor(240, 240, 240))

        # 사진 아이콘/플레이스홀더 그리기
        icon_size = min(width, height) // 3
        icon_x = x + (width - icon_size) // 2
        icon_y = y + (height - icon_size) // 2

        # 카메라 아이콘 형태 그리기
        painter.setPen(QPen(QColor(180, 180, 180), 3))
        painter.setBrush(QBrush(QColor(200, 200, 200)))

        # 카메라 본체
        cam_rect = QRect(icon_x, icon_y + icon_size // 6, icon_size, icon_size * 2 // 3)
        painter.drawRoundedRect(cam_rect, 8, 8)

        # 렌즈
        lens_size = icon_size // 3
        lens_x = icon_x + (icon_size - lens_size) // 2
        lens_y = icon_y + icon_size // 6 + (icon_size * 2 // 3 - lens_size) // 2
        painter.setBrush(QBrush(QColor(160, 160, 160)))
        painter.drawEllipse(lens_x, lens_y, lens_size, lens_size)

        # "사진 영역" 텍스트
        painter.setPen(QColor(150, 150, 150))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        text_rect = QRect(x, y + height - 30, width, 25)
        painter.drawText(text_rect, Qt.AlignCenter, "촬영 사진 영역")

        # 얇은 테두리 (인쇄 경계 표시)
        painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(x, y, width, height)

    def _draw_text_areas(self, painter):
        """텍스트 영역 그리기 - 실제 폰트/색상/크기로 렌더링"""
        # 사용자 입력 텍스트 - 플레이스홀더로 표시
        text_input_items = self.config.get("text_input", {}).get("items", [])

        for i, item in enumerate(text_input_items):
            x = item.get("x", 0)
            y = item.get("y", 0)
            font_size = item.get("font_size", 24)
            font_color = item.get("font_color", "#333333")
            font_path = item.get("font", "")
            placeholder = item.get("placeholder", f"사용자 입력 {i+1}")

            # 폰트 설정
            font = self._get_font(font_path, font_size)
            painter.setFont(font)
            painter.setPen(QColor(font_color))

            # 플레이스홀더 텍스트 그리기 (연한 색으로)
            placeholder_color = QColor(font_color)
            placeholder_color.setAlpha(150)
            painter.setPen(placeholder_color)
            painter.drawText(x, y + font_size, f"[{placeholder}]")

        # 고정 텍스트 - 실제 내용 표시
        text_items = self.config.get("texts", {}).get("items", [])

        for i, item in enumerate(text_items):
            x = item.get("x", 0)
            y = item.get("y", 0)
            font_size = item.get("font_size", 24)
            font_color = item.get("font_color", "#333333")
            font_path = item.get("font", "")
            content = item.get("content", f"텍스트 {i+1}")

            # 폰트 설정
            font = self._get_font(font_path, font_size)
            painter.setFont(font)
            painter.setPen(QColor(font_color))

            # 실제 텍스트 그리기
            painter.drawText(x, y + font_size, content)

    def _draw_qr_area(self, painter):
        """QR 이미지 영역 그리기 - 실제 이미지 또는 플레이스홀더"""
        qr_config = self.config.get("qr_uploaded_image", {})
        x = qr_config.get("x", 0)
        y = qr_config.get("y", 0)
        width = qr_config.get("width", 200)
        height = qr_config.get("height", 200)
        image_path = qr_config.get("path", "")

        # 실제 이미지가 있으면 로드
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # 중앙 정렬
                offset_x = x + (width - scaled_pixmap.width()) // 2
                offset_y = y + (height - scaled_pixmap.height()) // 2
                painter.drawPixmap(offset_x, offset_y, scaled_pixmap)
                return

        # 이미지가 없으면 QR 플레이스홀더 그리기
        painter.fillRect(x, y, width, height, QColor(245, 245, 245))

        # QR 코드 패턴 플레이스홀더
        qr_margin = 10
        qr_x = x + qr_margin
        qr_y = y + qr_margin
        qr_size = min(width, height) - qr_margin * 2
        cell_size = qr_size // 7

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(60, 60, 60)))

        # QR 코드 모서리 패턴 (위치 탐지 패턴)
        for corner_x, corner_y in [(0, 0), (4, 0), (0, 4)]:
            cx = qr_x + corner_x * cell_size
            cy = qr_y + corner_y * cell_size
            # 외곽
            painter.drawRect(cx, cy, cell_size * 3, cell_size * 3)
            # 내부 흰색
            painter.setBrush(QBrush(QColor(245, 245, 245)))
            painter.drawRect(cx + cell_size // 2, cy + cell_size // 2, cell_size * 2, cell_size * 2)
            # 중심
            painter.setBrush(QBrush(QColor(60, 60, 60)))
            painter.drawRect(cx + cell_size, cy + cell_size, cell_size, cell_size)

        # "QR 이미지" 텍스트
        painter.setPen(QColor(150, 150, 150))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        text_rect = QRect(x, y + height - 25, width, 20)
        painter.drawText(text_rect, Qt.AlignCenter, "QR/이미지 영역")

    def _draw_basic_images(self, painter):
        """기본 이미지들 그리기 - 실제 이미지 렌더링"""
        image_count = self.config.get("images", {}).get("count", 0)
        if image_count == 0:
            return

        images = self.config.get("images", {}).get("items", [])

        for i, image in enumerate(images):
            x = image.get("x", 0)
            y = image.get("y", 0)
            width = image.get("width", 100)
            height = image.get("height", 100)
            image_path = image.get("path", "")

            # 실제 이미지가 있으면 로드
            if image_path and os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    # 중앙 정렬
                    offset_x = x + (width - scaled_pixmap.width()) // 2
                    offset_y = y + (height - scaled_pixmap.height()) // 2
                    painter.drawPixmap(offset_x, offset_y, scaled_pixmap)
                    continue

            # 이미지가 없으면 플레이스홀더 그리기
            painter.fillRect(x, y, width, height, QColor(248, 248, 248))

            # 이미지 아이콘 그리기
            icon_size = min(width, height) // 3
            icon_x = x + (width - icon_size) // 2
            icon_y = y + (height - icon_size) // 2 - 10

            painter.setPen(QPen(QColor(200, 200, 200), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(icon_x, icon_y, icon_size, icon_size)

            # 산 모양 (이미지 아이콘)
            painter.setPen(QPen(QColor(180, 180, 180), 2))
            mountain_y = icon_y + icon_size * 2 // 3
            painter.drawLine(icon_x, mountain_y + icon_size // 4,
                           icon_x + icon_size // 2, mountain_y - icon_size // 4)
            painter.drawLine(icon_x + icon_size // 2, mountain_y - icon_size // 4,
                           icon_x + icon_size, mountain_y + icon_size // 4)

            # 파일명 표시
            filename = image.get("filename", f"이미지{i+1}")
            if "." in filename:
                filename = filename.split(".")[0]
            if len(filename) > 10:
                filename = filename[:10] + "..."

            painter.setPen(QColor(150, 150, 150))
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)
            text_rect = QRect(x, y + height - 20, width, 18)
            painter.drawText(text_rect, Qt.AlignCenter, filename)

    def _get_font(self, font_path: str, font_size: int) -> QFont:
        """폰트 로드 - 경로가 있으면 로드, 없으면 기본 폰트"""
        font = QFont()
        font.setPointSize(font_size)

        if font_path and os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font.setFamily(font_families[0])

        return font

    def resizeEvent(self, event):
        """리사이즈 시 미리보기 업데이트"""
        super().resizeEvent(event)
        # 약간의 딜레이 후 업데이트 (성능 최적화)
        QTimer.singleShot(50, self.update_preview)

    def closeEvent(self, event):
        """닫힐 때 시그널 발생"""
        self.closed.emit()
        super().closeEvent(event)
