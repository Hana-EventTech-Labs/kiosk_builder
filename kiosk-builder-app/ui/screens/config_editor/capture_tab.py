from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QSpinBox, QWidget, QRadioButton)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import LivePreviewWidget
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# 카메라/촬영 화면 screen_key = "1"
CAPTURE_SCREEN_KEY = "1"

class CaptureTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)

        self.screen_preview = None  # 화면 미리보기
        self.card_preview = None    # 카드 미리보기
        self.init_ui()

    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
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

        # 원본 파일명 표시
        self.capture_bg_edit = QLineEdit(self.config["photo"].get("background", ""))
        self.capture_bg_edit.textChanged.connect(self._on_background_changed)
        bg_layout.addWidget(self.capture_bg_edit, 1)

        # 배경화면 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_background_file(self, self.capture_bg_edit, "1"))
        bg_layout.addWidget(browse_button)

        content_layout.addWidget(bg_group)

        # 프레임 설정
        frame_group = QGroupBox("카메라 위치 및 크기")
        self.apply_left_aligned_group_style(frame_group)

        frame_layout = QFormLayout(frame_group)

        self.frame_fields = {}

        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["frame"][key])
            line_edit.textChanged.connect(self._update_screen_preview)
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            frame_layout.addRow(f"{label_text}:", line_edit)
            self.frame_fields[key] = line_edit

        content_layout.addWidget(frame_group)

        # 사진 설정 추가 (photo)
        photo_group = QGroupBox("촬영 사진 인쇄크기 설정")
        self.apply_left_aligned_group_style(photo_group)
        photo_layout = QFormLayout(photo_group)

        self.photo_fields = {}

        # 위치 및 크기
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["photo"][key])
            line_edit.textChanged.connect(self._update_card_preview)
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            photo_layout.addRow(f"{label_text}:", line_edit)
            self.photo_fields[key] = line_edit

        content_layout.addWidget(photo_group)

        # 카메라 카운트 설정
        camera_count_group = QGroupBox("카메라 카운트 설정")
        self.apply_left_aligned_group_style(camera_count_group)
        camera_count_layout = QFormLayout(camera_count_group)

        self.camera_count_fields = {}

        # 숫자 필드
        number_spin = QSpinBox()
        number_spin.setRange(0, 10)
        number_spin.setValue(self.config["camera_count"]["number"])
        camera_count_layout.addRow("카메라 카운트:", number_spin)
        self.camera_count_fields["number"] = number_spin

        # 폰트 크기
        font_size_spin = NumberLineEdit()
        font_size_spin.setValue(self.config["camera_count"]["font_size"])
        camera_count_layout.addRow("폰트 크기:", font_size_spin)
        self.camera_count_fields["font_size"] = font_size_spin

        # 폰트 색상
        font_color_button = ColorPickerButton(self.config["camera_count"]["font_color"])
        camera_count_layout.addRow("폰트 색상:", font_color_button)
        self.camera_count_fields["font_color"] = font_color_button

        content_layout.addWidget(camera_count_group)

        # 스트레치 추가
        content_layout.addStretch()

        # 좌측 설정 영역을 메인 레이아웃에 추가
        main_layout.addWidget(settings_widget, 1)

        # 우측 미리보기 영역
        previews_widget = QWidget()
        previews_layout = QVBoxLayout(previews_widget)
        previews_layout.setContentsMargins(0, 0, 0, 0)

        # 화면 미리보기 (실제 배경 이미지 사용)
        screen_preview_group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(screen_preview_group)
        screen_preview_layout = QVBoxLayout(screen_preview_group)

        self.screen_preview = LivePreviewWidget()
        self.screen_preview.position_changed.connect(self._on_frame_position_changed)
        self.screen_preview.size_changed.connect(self._on_frame_size_changed)
        screen_preview_layout.addWidget(self.screen_preview, 0, Qt.AlignHCenter)

        # 버튼 레이아웃
        screen_button_layout = QHBoxLayout()
        fill_button_screen = QPushButton("채우기")
        fill_button_screen.clicked.connect(self._fill_camera_frame)
        center_button_screen = QPushButton("가운데 정렬")
        center_button_screen.clicked.connect(self._center_camera_frame)
        screen_button_layout.addWidget(fill_button_screen)
        screen_button_layout.addWidget(center_button_screen)
        screen_preview_layout.addLayout(screen_button_layout)

        previews_layout.addWidget(screen_preview_group)

        # 카드 인쇄 미리보기
        card_preview_group = QGroupBox("카드 인쇄 미리보기")
        self.apply_left_aligned_group_style(card_preview_group)
        card_preview_layout = QVBoxLayout(card_preview_group)

        self.card_preview = LivePreviewWidget()
        self.card_preview.position_changed.connect(self._on_photo_position_changed)
        self.card_preview.size_changed.connect(self._on_photo_size_changed)
        card_preview_layout.addWidget(self.card_preview, 0, Qt.AlignHCenter)

        # 버튼 레이아웃
        card_button_layout = QHBoxLayout()
        fill_button_card = QPushButton("채우기")
        fill_button_card.clicked.connect(self._fill_photo_frame)
        center_button_card = QPushButton("가운데 정렬")
        center_button_card.clicked.connect(self._center_photo_frame)
        card_button_layout.addWidget(fill_button_card)
        card_button_layout.addWidget(center_button_card)
        card_preview_layout.addLayout(card_button_layout)

        previews_layout.addWidget(card_preview_group)
        main_layout.addWidget(previews_widget, 1)

        # 초기 미리보기 업데이트
        self._update_screen_preview()
        self._update_card_preview()

    def _on_background_changed(self):
        """배경 이미지 변경 시 미리보기 업데이트"""
        self._update_screen_preview()

    def _fill_camera_frame(self):
        """카메라 프레임을 모니터 크기에 맞게 채웁니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.frame_fields['width'].setValue(monitor_width)
        self.frame_fields['height'].setValue(monitor_height)
        self.frame_fields['x'].setValue(0)
        self.frame_fields['y'].setValue(0)

        self.request_real_time_update()

    def _center_camera_frame(self):
        """카메라 프레임을 모니터의 중앙에 정렬합니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        frame_width = self.frame_fields['width'].value()
        frame_height = self.frame_fields['height'].value()

        center_x = (monitor_width - frame_width) / 2
        center_y = (monitor_height - frame_height) / 2

        self.frame_fields['x'].setValue(int(center_x))
        self.frame_fields['y'].setValue(int(center_y))

        self.request_real_time_update()

    def _fill_photo_frame(self):
        """촬영 사진을 카드 크기에 맞게 채웁니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        self.photo_fields['width'].setValue(card_width)
        self.photo_fields['height'].setValue(card_height)
        self.photo_fields['x'].setValue(0)
        self.photo_fields['y'].setValue(0)

        self.request_real_time_update()

    def _center_photo_frame(self):
        """촬영 사진을 카드의 중앙에 정렬합니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        photo_width = self.photo_fields['width'].value()
        photo_height = self.photo_fields['height'].value()

        center_x = (card_width - photo_width) / 2
        center_y = (card_height - photo_height) / 2

        self.photo_fields['x'].setValue(int(center_x))
        self.photo_fields['y'].setValue(int(center_y))

        self.request_real_time_update()

    def _on_frame_position_changed(self, element_id, x, y):
        """드래그로 프레임 위치 변경 시 호출되는 슬롯"""
        if element_id == "camera_frame":
            self.frame_fields['x'].blockSignals(True)
            self.frame_fields['y'].blockSignals(True)

            self.frame_fields['x'].setValue(x)
            self.frame_fields['y'].setValue(y)

            self.frame_fields['x'].blockSignals(False)
            self.frame_fields['y'].blockSignals(False)

            self.request_real_time_update()

    def _on_photo_position_changed(self, element_id, x, y):
        """드래그로 사진 위치 변경 시 호출되는 슬롯"""
        if element_id == "photo_area":
            self.photo_fields['x'].blockSignals(True)
            self.photo_fields['y'].blockSignals(True)

            self.photo_fields['x'].setValue(x)
            self.photo_fields['y'].setValue(y)

            self.photo_fields['x'].blockSignals(False)
            self.photo_fields['y'].blockSignals(False)

            self.request_real_time_update()

    def _on_frame_size_changed(self, element_id, x, y, width, height):
        """드래그로 카메라 프레임 크기 변경 시 호출되는 슬롯"""
        if element_id == "camera_frame":
            # 모든 필드의 시그널 블록
            for key in ['x', 'y', 'width', 'height']:
                self.frame_fields[key].blockSignals(True)

            self.frame_fields['x'].setValue(x)
            self.frame_fields['y'].setValue(y)
            self.frame_fields['width'].setValue(width)
            self.frame_fields['height'].setValue(height)

            # 시그널 블록 해제
            for key in ['x', 'y', 'width', 'height']:
                self.frame_fields[key].blockSignals(False)

            self.request_real_time_update()

    def _on_photo_size_changed(self, element_id, x, y, width, height):
        """드래그로 사진 크기 변경 시 호출되는 슬롯"""
        if element_id == "photo_area":
            # 모든 필드의 시그널 블록
            for key in ['x', 'y', 'width', 'height']:
                self.photo_fields[key].blockSignals(True)

            self.photo_fields['x'].setValue(x)
            self.photo_fields['y'].setValue(y)
            self.photo_fields['width'].setValue(width)
            self.photo_fields['height'].setValue(height)

            # 시그널 블록 해제
            for key in ['x', 'y', 'width', 'height']:
                self.photo_fields[key].blockSignals(False)

            self.request_real_time_update()

    def _update_screen_preview(self):
        """화면 미리보기 업데이트 (실제 배경 이미지 사용)"""
        if not self.screen_preview:
            return

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        # 원본 크기 설정
        self.screen_preview.set_original_size(monitor_width, monitor_height)

        # 배경 이미지 설정 - screen_key를 사용하여 실제 파일 경로 찾기
        bg_path = FileHandler.resolve_background_path(CAPTURE_SCREEN_KEY)
        self.screen_preview.set_background(bg_path, QColor("#1a1a1a"))

        # 카메라 프레임 영역 추가
        try:
            width = self.frame_fields["width"].value()
            height = self.frame_fields["height"].value()
            x = self.frame_fields["x"].value()
            y = self.frame_fields["y"].value()
            frame_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            frame_rect = QRect(0, 0, 800, 600)

        self.screen_preview.add_element(
            "camera_frame",
            frame_rect,
            color=QColor("lime"),
            label="카메라",
            draggable=True
        )

        self.request_real_time_update()

    def _update_card_preview(self):
        """카드 인쇄 미리보기 업데이트"""
        if not self.card_preview:
            return

        # 카드 크기 (전역 설정 기준)
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        # 원본 크기 설정
        self.card_preview.set_original_size(card_width, card_height)

        # 카드 배경 (흰색)
        self.card_preview.set_background_color(QColor("white"))

        # 사진 영역 추가
        try:
            width = self.photo_fields["width"].value()
            height = self.photo_fields["height"].value()
            x = self.photo_fields["x"].value()
            y = self.photo_fields["y"].value()
            photo_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            photo_rect = QRect(0, 0, 300, 300)

        self.card_preview.add_element(
            "photo_area",
            photo_rect,
            color=QColor("red"),
            label="사진",
            draggable=True
        )

        self.request_real_time_update()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        self.capture_bg_edit.setText(config["photo"].get("background", ""))

        # 프레임 설정 업데이트
        for key, widget in self.frame_fields.items():
            widget.setValue(config["frame"][key])

        # 촬영 사진 설정 업데이트
        for key, widget in self.photo_fields.items():
            widget.setValue(config["photo"][key])

        # 카메라 카운트 설정 업데이트
        self.camera_count_fields["number"].setValue(config["camera_count"]["number"])
        self.camera_count_fields["font_size"].setValue(config["camera_count"]["font_size"])
        self.camera_count_fields["font_color"].update_color(config["camera_count"]["font_color"])

        # 미리보기 업데이트
        self._update_screen_preview()
        self._update_card_preview()

    def update_config(self, config):
        """UI 값을 config에 반영"""
        # 배경화면 저장
        config["photo"]["background"] = self.capture_bg_edit.text()

        # 프레임 설정 저장
        for key, widget in self.frame_fields.items():
            config["frame"][key] = widget.value()

        # 촬영 사진 설정 저장
        config["photo"]["filename"] = "captured_image.jpg"
        for key, widget in self.photo_fields.items():
            config["photo"][key] = widget.value()

        # framed_photo에도 동일한 x, y, width, height 값 저장
        if "framed_photo" not in config:
            config["framed_photo"] = {}

        # photo의 x, y, width, height 값을 framed_photo에 복사
        config["framed_photo"]["x"] = config["photo"]["x"]
        config["framed_photo"]["y"] = config["photo"]["y"]
        config["framed_photo"]["width"] = config["photo"]["width"]
        config["framed_photo"]["height"] = config["photo"]["height"]

        # framed_photo의 filename이 없으면 기본값 설정
        if "filename" not in config["framed_photo"]:
            config["framed_photo"]["filename"] = "framed_photo.jpg"

        # 카메라 카운트 설정 저장
        config["camera_count"]["number"] = self.camera_count_fields["number"].value()
        config["camera_count"]["font_size"] = self.camera_count_fields["font_size"].value()
        config["camera_count"]["font_color"] = self.camera_count_fields["font_color"].color
