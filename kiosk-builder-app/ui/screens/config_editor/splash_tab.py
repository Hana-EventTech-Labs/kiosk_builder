from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import TextPreviewWidget
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# 스플래시 화면 screen_key = "splash" (0)
SPLASH_SCREEN_KEY = "splash"

class SplashTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.screen_preview = None
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

        # 스플래시 화면 설정
        splash_group = QGroupBox("스플래쉬 화면 설정")
        self.apply_left_aligned_group_style(splash_group)
        splash_layout = QFormLayout(splash_group)
        
        # 필드 저장을 위한 딕셔너리
        self.splash_fields = {}
        
        # 배경화면 선택 레이아웃 추가
        background_layout = QHBoxLayout()
        # 원본 파일명 표시
        background_edit = QLineEdit(self.config["splash"].get("background", ""))
        background_layout.addWidget(background_edit, 1)
        self.splash_fields["background"] = background_edit
        
        # 배경화면 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_background_file(self, background_edit, "splash"))
        background_layout.addWidget(browse_button)

        # 배경화면 변경 시 미리보기 업데이트
        background_edit.textChanged.connect(self._update_screen_preview)

        splash_layout.addRow("배경화면:", background_layout)
        
        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["splash"]["font"])
        font_layout.addWidget(font_edit, 1)  # 1은 stretch factor로, 남은 공간을 차지하도록 함
        self.splash_fields["font"] = font_edit
        
        # 폰트 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_font_file(self, font_edit))
        font_layout.addWidget(browse_button)
        
        splash_layout.addRow("폰트:", font_layout)
        
        phrase_edit = QLineEdit(self.config["splash"]["phrase"])
        phrase_edit.textChanged.connect(self._update_screen_preview)
        splash_layout.addRow("문구:", phrase_edit)
        self.splash_fields["phrase"] = phrase_edit

        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config["splash"]["font_size"])
        font_size_edit.textChanged.connect(self._update_screen_preview)
        splash_layout.addRow("폰트 크기:", font_size_edit)
        self.splash_fields["font_size"] = font_size_edit

        font_color_button = ColorPickerButton(self.config["splash"]["font_color"])
        font_color_button.color_changed.connect(self._update_screen_preview)
        splash_layout.addRow("폰트 색상:", font_color_button)
        self.splash_fields["font_color"] = font_color_button

        x_edit = NumberLineEdit()
        x_edit.setValue(self.config["splash"]["x"])
        x_edit.textChanged.connect(self._update_screen_preview)
        splash_layout.addRow("X 위치:", x_edit)
        self.splash_fields["x"] = x_edit

        y_edit = NumberLineEdit()
        y_edit.setValue(self.config["splash"]["y"])
        y_edit.textChanged.connect(self._update_screen_preview)
        splash_layout.addRow("Y 위치:", y_edit)
        self.splash_fields["y"] = y_edit

        content_layout.addWidget(splash_group)

        # 스트레치 추가
        content_layout.addStretch()

        # 좌측 설정 영역을 메인 레이아웃에 추가
        main_layout.addWidget(settings_widget, 1)

        # 우측 미리보기 영역
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # 화면 미리보기
        screen_preview_group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(screen_preview_group)
        screen_preview_layout = QVBoxLayout(screen_preview_group)

        self.screen_preview = TextPreviewWidget()
        self.screen_preview.position_changed.connect(self._on_text_position_changed)
        screen_preview_layout.addWidget(self.screen_preview, 0, Qt.AlignHCenter)

        preview_layout.addWidget(screen_preview_group)
        preview_layout.addStretch()

        main_layout.addWidget(preview_widget, 1)

        # 초기 미리보기 업데이트
        self._update_screen_preview()

    def _update_screen_preview(self):
        """화면 미리보기 업데이트"""
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
        bg_path = FileHandler.resolve_background_path(SPLASH_SCREEN_KEY)
        self.screen_preview.set_background(bg_path, QColor("#1a1a1a"))

        # 텍스트 설정
        try:
            text = self.splash_fields["phrase"].text()
            font_path = self.splash_fields["font"].text()
            font_size = self.splash_fields["font_size"].value()
            font_color = self.splash_fields["font_color"].color
            x = self.splash_fields["x"].value()
            y = self.splash_fields["y"].value()

            self.screen_preview.add_text(
                "splash_text",
                text,
                x, y,
                font_path=font_path,
                font_size=font_size,
                color=QColor(font_color),
                draggable=True
            )
        except (AttributeError, KeyError):
            pass

        self.request_real_time_update()

    def _on_text_position_changed(self, element_id, x, y):
        """드래그로 텍스트 위치 변경 시 호출"""
        if element_id == "splash_text":
            self.splash_fields['x'].blockSignals(True)
            self.splash_fields['y'].blockSignals(True)

            self.splash_fields['x'].setValue(x)
            self.splash_fields['y'].setValue(y)

            self.splash_fields['x'].blockSignals(False)
            self.splash_fields['y'].blockSignals(False)

            self.request_real_time_update()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        for key, widget in self.splash_fields.items():
            if isinstance(widget, ColorPickerButton):
                widget.update_color(config["splash"][key])
            else:
                if isinstance(widget, NumberLineEdit):
                    widget.setValue(config["splash"][key])
                else:
                    widget.setText(config["splash"][key])

        # 미리보기 업데이트
        self._update_screen_preview()
    
    def update_config(self, config):
        """UI 값을 config에 반영"""
        for key, widget in self.splash_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["splash"][key] = widget.color
            else:
                if isinstance(widget, NumberLineEdit):
                    config["splash"][key] = widget.value()
                else:
                    config["splash"][key] = widget.text()