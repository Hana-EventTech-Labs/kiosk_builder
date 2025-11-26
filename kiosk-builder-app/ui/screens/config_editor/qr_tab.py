from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QWidget)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QRect
from ui.components.inputs import NumberLineEdit
from ui.components.live_preview import LivePreviewWidget
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# QR 화면 screen_key = "3"
QR_SCREEN_KEY = "3"

class QRTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.tab_manager = None
        self.qr_preview = None
        self.card_preview = None
        self.init_ui()

    def init_ui(self):
        scroll_content_layout = self.create_tab_with_scroll()

        # 메인 레이아웃 (좌: 설정, 우: 미리보기)
        main_layout = QHBoxLayout()
        scroll_content_layout.addLayout(main_layout)

        # 설정 영역
        settings_widget = QWidget()
        content_layout = QVBoxLayout(settings_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 배경화면 설정
        bg_group = QGroupBox("배경화면 설정")
        self.apply_left_aligned_group_style(bg_group)
        bg_layout = QHBoxLayout(bg_group)

        self.qr_bg_edit = QLineEdit(self.config["qr"].get("background", ""))
        self.qr_bg_edit.textChanged.connect(self._update_qr_preview)
        bg_layout.addWidget(self.qr_bg_edit, 1)

        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_background_file(self, self.qr_bg_edit, "3"))
        bg_layout.addWidget(browse_button)

        content_layout.addWidget(bg_group)

        # QR 코드 설정 그룹
        qr_group = QGroupBox("QR 코드 설정")
        self.apply_left_aligned_group_style(qr_group)
        qr_layout = QFormLayout(qr_group)

        self.qr_fields = {}

        for key, label in [("preview_width", "너비"), ("preview_height", "높이"), ("x", "X 위치"), ("y", "Y 위치")]:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["qr"][key])
            line_edit.textChanged.connect(self._update_qr_preview)
            qr_layout.addRow(f"{label}:", line_edit)
            self.qr_fields[key] = line_edit

        content_layout.addWidget(qr_group)

        # 업로드 이미지 설정 그룹박스
        qr_uploaded_group = QGroupBox("이미지 인쇄 설정")
        self.apply_left_aligned_group_style(qr_uploaded_group)
        qr_uploaded_layout = QFormLayout(qr_uploaded_group)

        self.qr_uploaded_fields = {}

        for key in ["width", "height", "x", "y"]:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["qr_uploaded_image"][key])
            line_edit.textChanged.connect(self._update_card_preview)
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            qr_uploaded_layout.addRow(f"{label_text}:", line_edit)
            self.qr_uploaded_fields[key] = line_edit

        content_layout.addWidget(qr_uploaded_group)
        content_layout.addStretch()

        main_layout.addWidget(settings_widget, 1)

        # 우측 미리보기 영역
        previews_widget = QWidget()
        previews_layout = QVBoxLayout(previews_widget)
        previews_layout.setContentsMargins(0, 0, 0, 0)

        # QR 코드 화면 미리보기
        qr_preview_group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(qr_preview_group)
        qr_preview_layout = QVBoxLayout(qr_preview_group)

        self.qr_preview = LivePreviewWidget()
        self.qr_preview.position_changed.connect(self._on_qr_position_changed)
        self.qr_preview.size_changed.connect(self._on_qr_size_changed)
        qr_preview_layout.addWidget(self.qr_preview, 0, Qt.AlignHCenter)

        qr_button_layout = QHBoxLayout()
        fill_button_qr = QPushButton("채우기")
        fill_button_qr.clicked.connect(self._fill_qr_frame)
        center_button_qr = QPushButton("가운데 정렬")
        center_button_qr.clicked.connect(self._center_qr_frame)
        qr_button_layout.addWidget(fill_button_qr)
        qr_button_layout.addWidget(center_button_qr)
        qr_preview_layout.addLayout(qr_button_layout)

        previews_layout.addWidget(qr_preview_group)

        # 카드 인쇄 미리보기
        card_preview_group = QGroupBox("카드 인쇄 미리보기")
        self.apply_left_aligned_group_style(card_preview_group)
        card_preview_layout = QVBoxLayout(card_preview_group)

        self.card_preview = LivePreviewWidget()
        self.card_preview.position_changed.connect(self._on_image_position_changed)
        self.card_preview.size_changed.connect(self._on_image_size_changed)
        card_preview_layout.addWidget(self.card_preview, 0, Qt.AlignHCenter)

        image_button_layout = QHBoxLayout()
        fill_button_image = QPushButton("채우기")
        fill_button_image.clicked.connect(self._fill_image_frame)
        center_button_image = QPushButton("가운데 정렬")
        center_button_image.clicked.connect(self._center_image_frame)
        image_button_layout.addWidget(fill_button_image)
        image_button_layout.addWidget(center_button_image)
        card_preview_layout.addLayout(image_button_layout)

        previews_layout.addWidget(card_preview_group)
        main_layout.addWidget(previews_widget, 1)

        # 초기 미리보기 업데이트
        self._update_qr_preview()
        self._update_card_preview()

    def _fill_qr_frame(self):
        """QR 코드를 모니터 크기에 맞게 채웁니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.qr_fields['preview_width'].setValue(monitor_width)
        self.qr_fields['preview_height'].setValue(monitor_height)
        self.qr_fields['x'].setValue(0)
        self.qr_fields['y'].setValue(0)
        self.request_real_time_update()

    def _center_qr_frame(self):
        """QR 코드를 모니터의 중앙에 정렬합니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        qr_width = self.qr_fields['preview_width'].value()
        qr_height = self.qr_fields['preview_height'].value()

        center_x = (monitor_width - qr_width) // 2
        center_y = (monitor_height - qr_height) // 2

        self.qr_fields['x'].setValue(center_x)
        self.qr_fields['y'].setValue(center_y)
        self.request_real_time_update()

    def _fill_image_frame(self):
        """업로드된 이미지를 카드 크기에 맞게 채웁니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        self.qr_uploaded_fields['width'].setValue(card_width)
        self.qr_uploaded_fields['height'].setValue(card_height)
        self.qr_uploaded_fields['x'].setValue(0)
        self.qr_uploaded_fields['y'].setValue(0)
        self.request_real_time_update()

    def _center_image_frame(self):
        """업로드된 이미지를 카드의 중앙에 정렬합니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        image_width = self.qr_uploaded_fields['width'].value()
        image_height = self.qr_uploaded_fields['height'].value()

        center_x = (card_width - image_width) // 2
        center_y = (card_height - image_height) // 2

        self.qr_uploaded_fields['x'].setValue(center_x)
        self.qr_uploaded_fields['y'].setValue(center_y)
        self.request_real_time_update()

    def _on_qr_position_changed(self, element_id, x, y):
        """드래그로 QR 코드 위치 변경 시 호출"""
        if element_id == "qr_area":
            self.qr_fields['x'].blockSignals(True)
            self.qr_fields['y'].blockSignals(True)

            self.qr_fields['x'].setValue(x)
            self.qr_fields['y'].setValue(y)

            self.qr_fields['x'].blockSignals(False)
            self.qr_fields['y'].blockSignals(False)

            self.request_real_time_update()

    def _on_image_position_changed(self, element_id, x, y):
        """드래그로 이미지 위치 변경 시 호출"""
        if element_id == "image_area":
            self.qr_uploaded_fields['x'].blockSignals(True)
            self.qr_uploaded_fields['y'].blockSignals(True)

            self.qr_uploaded_fields['x'].setValue(x)
            self.qr_uploaded_fields['y'].setValue(y)

            self.qr_uploaded_fields['x'].blockSignals(False)
            self.qr_uploaded_fields['y'].blockSignals(False)

            self.request_real_time_update()

    def _on_qr_size_changed(self, element_id, x, y, width, height):
        """드래그로 QR 코드 크기 변경 시 호출"""
        if element_id == "qr_area":
            for key in ['x', 'y', 'preview_width', 'preview_height']:
                self.qr_fields[key].blockSignals(True)

            self.qr_fields['x'].setValue(x)
            self.qr_fields['y'].setValue(y)
            self.qr_fields['preview_width'].setValue(width)
            self.qr_fields['preview_height'].setValue(height)

            for key in ['x', 'y', 'preview_width', 'preview_height']:
                self.qr_fields[key].blockSignals(False)

            self.request_real_time_update()

    def _on_image_size_changed(self, element_id, x, y, width, height):
        """드래그로 이미지 크기 변경 시 호출"""
        if element_id == "image_area":
            for key in ['x', 'y', 'width', 'height']:
                self.qr_uploaded_fields[key].blockSignals(True)

            self.qr_uploaded_fields['x'].setValue(x)
            self.qr_uploaded_fields['y'].setValue(y)
            self.qr_uploaded_fields['width'].setValue(width)
            self.qr_uploaded_fields['height'].setValue(height)

            for key in ['x', 'y', 'width', 'height']:
                self.qr_uploaded_fields[key].blockSignals(False)

            self.request_real_time_update()

    def _update_qr_preview(self):
        """QR 코드 화면 미리보기 업데이트"""
        if not self.qr_preview:
            return

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.qr_preview.set_original_size(monitor_width, monitor_height)

        # 배경 이미지 설정 - screen_key를 사용하여 실제 파일 경로 찾기
        bg_path = FileHandler.resolve_background_path(QR_SCREEN_KEY)
        self.qr_preview.set_background(bg_path, QColor("#1a1a1a"))

        # QR 코드 영역 추가
        try:
            width = self.qr_fields["preview_width"].value()
            height = self.qr_fields["preview_height"].value()
            x = self.qr_fields["x"].value()
            y = self.qr_fields["y"].value()
            qr_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            qr_rect = QRect(0, 0, 400, 400)

        self.qr_preview.add_element(
            "qr_area",
            qr_rect,
            color=QColor("cyan"),
            label="QR 코드",
            draggable=True
        )

        self.request_real_time_update()

    def _update_card_preview(self):
        """카드 인쇄 미리보기 업데이트"""
        if not self.card_preview:
            return

        # 카드 크기
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        self.card_preview.set_original_size(card_width, card_height)
        self.card_preview.set_background_color(QColor("white"))

        # 이미지 영역 추가
        try:
            width = self.qr_uploaded_fields["width"].value()
            height = self.qr_uploaded_fields["height"].value()
            x = self.qr_uploaded_fields["x"].value()
            y = self.qr_uploaded_fields["y"].value()
            image_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            image_rect = QRect(0, 0, 300, 300)

        self.card_preview.add_element(
            "image_area",
            image_rect,
            color=QColor("red"),
            label="이미지",
            draggable=True
        )

        self.request_real_time_update()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        self.qr_bg_edit.setText(config["qr"].get("background", ""))

        for key, widget in self.qr_fields.items():
            widget.setValue(config["qr"][key])

        for key, widget in self.qr_uploaded_fields.items():
            widget.setValue(config["qr_uploaded_image"][key])

        self._update_qr_preview()
        self._update_card_preview()

    def update_config(self, config):
        """UI 값을 config에 반영"""
        config["qr"]["background"] = self.qr_bg_edit.text()

        for key, widget in self.qr_fields.items():
            config["qr"][key] = widget.value()

        for key, widget in self.qr_uploaded_fields.items():
            config["qr_uploaded_image"][key] = widget.value()
