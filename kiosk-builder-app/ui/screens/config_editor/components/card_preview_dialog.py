"""
플로팅 최종 카드 미리보기 다이얼로그

모든 탭에서 설정한 인쇄 요소들을 통합하여 실제 인쇄될 형태로 미리보기합니다.
- 사진 영역 (촬영 화면) - 플레이스홀더 이미지
- QR 이미지 (QR 화면) - 실제 이미지 또는 플레이스홀더
- 사용자 입력 텍스트 (키보드 화면) - 실제 폰트/색상/크기 렌더링
- 고정 텍스트 (키보드 화면) - 실제 폰트/색상/크기 렌더링
- 기본 이미지들 (기본 설정) - 실제 이미지 렌더링

v2.0 개선사항:
- 카드 그림자 효과 및 둥근 모서리
- mm/DPI 정보 표시
- 줌 슬라이더 (25%~200%)
- 레이어별 표시/숨기기 토글
- PNG 이미지 내보내기
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QWidget, QSizeGrip, QFrame, QSlider, QScrollArea,
    QFileDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QFontMetrics, QFontDatabase, QBrush, QPainterPath
from ui.styles.colors import COLORS
from utils.file_handler import get_resources_base_path

# 인쇄 관련 상수
PRINT_DPI = 300  # 표준 인쇄 DPI
MM_PER_INCH = 25.4
CARD_CORNER_RADIUS = 12  # 카드 모서리 둥글기 (px)


class FloatingCardPreviewDialog(QDialog):
    """
    플로팅 최종 카드 미리보기 다이얼로그

    Features:
    - 항상 위에 표시 옵션
    - 실시간 업데이트
    - 리사이즈 가능
    - 드래그로 이동 가능
    - 줌 슬라이더 (25%~200%)
    - 레이어별 표시/숨기기
    - PNG 내보내기
    """

    # 다이얼로그가 닫힐 때 시그널
    closed = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._drag_pos = None

        # 줌 레벨 (100% = 1.0)
        self._zoom_level = 100

        # 레이어 표시 상태
        self._show_photo = True
        self._show_text = True
        self._show_qr = True
        self._show_images = True

        # 현재 카드 픽스맵 (내보내기용)
        self._current_card_pixmap = None

        self.setWindowTitle("최종 카드 미리보기")
        self.setMinimumSize(420, 600)
        self.resize(480, 700)

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

        # 줌 컨트롤
        self._create_zoom_control(layout)

        # 레이어 토글
        self._create_layer_controls(layout)

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

        # 타이틀
        title_label = QLabel("최종 카드 미리보기")
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
        preview_layout.setContentsMargins(16, 16, 16, 8)
        preview_layout.setAlignment(Qt.AlignCenter)

        # 스크롤 영역 (줌 시 스크롤 가능)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #e9ecef;
                border: none;
                border-radius: 8px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #f0f0f0;
                width: 8px;
                height: 8px;
            }
            QScrollBar::handle {
                background: #ccc;
                border-radius: 4px;
            }
        """)

        # 미리보기 라벨 (카드 이미지)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(300, 350)

        # 그림자 효과 추가
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.preview_label.setGraphicsEffect(shadow)

        self.scroll_area.setWidget(self.preview_label)
        preview_layout.addWidget(self.scroll_area, 1)

        parent_layout.addWidget(preview_container, 1)

    def _create_zoom_control(self, parent_layout):
        """줌 컨트롤 생성"""
        zoom_container = QWidget()
        zoom_container.setObjectName("zoomContainer")
        zoom_container.setFixedHeight(36)
        zoom_layout = QHBoxLayout(zoom_container)
        zoom_layout.setContentsMargins(12, 4, 12, 4)
        zoom_layout.setSpacing(8)

        # 줌 라벨
        zoom_icon = QLabel("확대:")
        zoom_icon.setStyleSheet("font-size: 11px; color: #666;")
        zoom_layout.addWidget(zoom_icon)

        # 축소 버튼
        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(24, 24)
        zoom_out_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        zoom_out_btn.clicked.connect(lambda: self._change_zoom(-25))
        zoom_layout.addWidget(zoom_out_btn)

        # 줌 슬라이더
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(25)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #ddd;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: #2196F3;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #1976D2;
            }
        """)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider, 1)

        # 확대 버튼
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(24, 24)
        zoom_in_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        zoom_in_btn.clicked.connect(lambda: self._change_zoom(25))
        zoom_layout.addWidget(zoom_in_btn)

        # 줌 퍼센트 표시
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(45)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        zoom_layout.addWidget(self.zoom_label)

        # 100% 리셋 버튼
        reset_btn = QPushButton("1:1")
        reset_btn.setFixedSize(32, 24)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background: #e9ecef; }
        """)
        reset_btn.clicked.connect(lambda: self.zoom_slider.setValue(100))
        zoom_layout.addWidget(reset_btn)

        parent_layout.addWidget(zoom_container)

    def _create_layer_controls(self, parent_layout):
        """레이어 토글 컨트롤 생성"""
        layer_container = QWidget()
        layer_container.setObjectName("layerContainer")
        layer_container.setFixedHeight(32)
        layer_layout = QHBoxLayout(layer_container)
        layer_layout.setContentsMargins(12, 2, 12, 2)
        layer_layout.setSpacing(12)

        # 레이어 라벨
        layer_label = QLabel("레이어:")
        layer_label.setStyleSheet("color: #666; font-size: 11px;")
        layer_layout.addWidget(layer_label)

        # 체크박스 스타일
        cb_style = """
            QCheckBox {
                color: #555;
                font-size: 11px;
                spacing: 4px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid #ccc;
            }
            QCheckBox::indicator:checked {
                background: #2196F3;
                border-color: #2196F3;
            }
        """

        # 사진 레이어
        self.cb_photo = QCheckBox("사진")
        self.cb_photo.setChecked(True)
        self.cb_photo.setStyleSheet(cb_style)
        self.cb_photo.toggled.connect(lambda c: self._toggle_layer('photo', c))
        layer_layout.addWidget(self.cb_photo)

        # 텍스트 레이어
        self.cb_text = QCheckBox("텍스트")
        self.cb_text.setChecked(True)
        self.cb_text.setStyleSheet(cb_style)
        self.cb_text.toggled.connect(lambda c: self._toggle_layer('text', c))
        layer_layout.addWidget(self.cb_text)

        # QR/이미지 레이어
        self.cb_qr = QCheckBox("QR")
        self.cb_qr.setChecked(True)
        self.cb_qr.setStyleSheet(cb_style)
        self.cb_qr.toggled.connect(lambda c: self._toggle_layer('qr', c))
        layer_layout.addWidget(self.cb_qr)

        # 기본 이미지 레이어
        self.cb_images = QCheckBox("이미지")
        self.cb_images.setChecked(True)
        self.cb_images.setStyleSheet(cb_style)
        self.cb_images.toggled.connect(lambda c: self._toggle_layer('images', c))
        layer_layout.addWidget(self.cb_images)

        layer_layout.addStretch()

        parent_layout.addWidget(layer_container)

    def _create_footer(self, parent_layout):
        """푸터 영역 생성 (옵션 + 정보)"""
        footer = QWidget()
        footer.setObjectName("dialogFooter")
        footer.setFixedHeight(56)  # 높이 증가
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(12, 4, 8, 4)
        footer_layout.setSpacing(4)

        # 상단 행: 옵션들
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # 항상 위에 표시 체크박스
        self.always_on_top_check = QCheckBox("항상 위에")
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
        top_row.addWidget(self.always_on_top_check)

        top_row.addStretch()

        # 이미지 저장 버튼
        self.export_btn = QPushButton("이미지 저장")
        self.export_btn.setFixedHeight(26)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
            QPushButton:pressed {{
                background-color: #219a52;
            }}
        """)
        self.export_btn.clicked.connect(self._export_image)
        top_row.addWidget(self.export_btn)

        footer_layout.addLayout(top_row)

        # 하단 행: 크기 정보
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        # 카드 크기 정보 (mm + px + DPI)
        self.size_info_label = QLabel("63.6 × 101.2 mm | 636 × 1012 px | 254 DPI")
        self.size_info_label.setStyleSheet("color: #888; font-size: 10px;")
        bottom_row.addWidget(self.size_info_label)

        bottom_row.addStretch()

        # 리사이즈 그립
        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)
        bottom_row.addWidget(size_grip)

        footer_layout.addLayout(bottom_row)

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
                background-color: #f0f0f0;
            }}
            #zoomContainer {{
                background-color: #f8f9fa;
                border-top: 1px solid #e9ecef;
            }}
            #layerContainer {{
                background-color: #f8f9fa;
                border-top: 1px solid #e9ecef;
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

    def _toggle_layer(self, layer_name, checked):
        """레이어 표시 토글"""
        if layer_name == 'photo':
            self._show_photo = checked
        elif layer_name == 'text':
            self._show_text = checked
        elif layer_name == 'qr':
            self._show_qr = checked
        elif layer_name == 'images':
            self._show_images = checked
        self.update_preview()

    def _on_zoom_changed(self, value):
        """줌 슬라이더 값 변경"""
        self._zoom_level = value
        self.zoom_label.setText(f"{value}%")
        self.update_preview()

    def _change_zoom(self, delta):
        """줌 레벨 변경 (+/- 버튼용)"""
        new_value = max(25, min(200, self._zoom_level + delta))
        self.zoom_slider.setValue(new_value)

    def _export_image(self):
        """현재 미리보기를 PNG 이미지로 저장"""
        if self._current_card_pixmap is None:
            return

        # 파일 저장 다이얼로그
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "카드 미리보기 이미지 저장",
            "card_preview.png",
            "PNG 이미지 (*.png);;JPEG 이미지 (*.jpg);;모든 파일 (*.*)"
        )

        if file_path:
            # 확장자에 따라 포맷 결정
            if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                self._current_card_pixmap.save(file_path, "JPEG", 95)
            else:
                self._current_card_pixmap.save(file_path, "PNG")

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

        # mm 크기 계산 (254 DPI 기준)
        mm_width = round(card_width / PRINT_DPI * MM_PER_INCH, 1)
        mm_height = round(card_height / PRINT_DPI * MM_PER_INCH, 1)

        # 크기 정보 업데이트 (mm + px + DPI)
        self.size_info_label.setText(f"{mm_width} × {mm_height} mm | {card_width} × {card_height} px | {PRINT_DPI} DPI")

        # 카드 배경 생성 (둥근 모서리를 위해 투명 배경으로 시작)
        card_pixmap = QPixmap(card_width, card_height)
        card_pixmap.fill(Qt.transparent)

        painter = QPainter(card_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 둥근 모서리 클리핑 경로 생성
        card_path = QPainterPath()
        card_path.addRoundedRect(0, 0, card_width, card_height, CARD_CORNER_RADIUS, CARD_CORNER_RADIUS)
        painter.setClipPath(card_path)

        # 베이스 카드 이미지가 있으면 로드
        base_card_path = self.config.get("card", {}).get("background", "")
        if base_card_path and os.path.exists(base_card_path):
            base_pixmap = QPixmap(base_card_path)
            if not base_pixmap.isNull():
                scaled_base = base_pixmap.scaled(
                    card_width, card_height,
                    Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                # 중앙 정렬
                x_offset = (scaled_base.width() - card_width) // 2
                y_offset = (scaled_base.height() - card_height) // 2
                painter.drawPixmap(-x_offset, -y_offset, scaled_base)
            else:
                painter.fillRect(0, 0, card_width, card_height, Qt.white)
        else:
            painter.fillRect(0, 0, card_width, card_height, Qt.white)

        # 화면 순서 확인
        screen_order = self.config.get("screen_order", [])

        # 1. 촬영 사진 영역
        if 1 in screen_order and self._show_photo:
            self._draw_photo_area(painter)

        # 2. 텍스트 영역 (키보드 화면)
        if 2 in screen_order and self._show_text:
            self._draw_text_areas(painter)

        # 3. QR 이미지 영역
        if 3 in screen_order and self._show_qr:
            self._draw_qr_area(painter)

        # 4. 기본 이미지들
        if self._show_images:
            self._draw_basic_images(painter)

        # 5. 카드 테두리 (둥근 모서리)
        painter.setClipping(False)
        border_pen = QPen(QColor("#aaaaaa"), 2, Qt.SolidLine)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, card_width - 2, card_height - 2, CARD_CORNER_RADIUS, CARD_CORNER_RADIUS)

        painter.end()

        # 내보내기용 원본 저장
        self._current_card_pixmap = card_pixmap

        # 줌 레벨 적용
        zoom_factor = self._zoom_level / 100.0
        display_width = int(card_width * zoom_factor * 0.4)  # 기본 40% 크기에서 줌
        display_height = int(card_height * zoom_factor * 0.4)

        scaled_pixmap = card_pixmap.scaled(
            display_width,
            display_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # 라벨 크기 조정 및 픽스맵 설정
        self.preview_label.setFixedSize(scaled_pixmap.size())
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
        base_path = get_resources_base_path()

        for i, image in enumerate(images):
            x = image.get("x", 0)
            y = image.get("y", 0)
            width = image.get("width", 100)
            height = image.get("height", 100)

            # filename으로 이미지 경로 구성
            filename = image.get("filename", "")
            image_path = os.path.join(base_path, "resources", filename) if filename else ""

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
        font.setPointSize(max(1, font_size))

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
