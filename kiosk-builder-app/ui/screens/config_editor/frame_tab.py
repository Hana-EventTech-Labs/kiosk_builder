from PySide6.QtWidgets import (QGroupBox, QFormLayout, QHBoxLayout, QLineEdit, QPushButton)
from .base_tab import BaseTab
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from utils.file_handler import FileHandler

class FrameTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.init_ui()

    def init_ui(self):
        content_layout = self.create_tab_with_scroll()

        # 배경화면 설정 그룹
        bg_group = QGroupBox("배경화면 설정")
        self.apply_left_aligned_group_style(bg_group)
        bg_layout = QHBoxLayout(bg_group)
        
        # 배경화면 파일 선택
        self.frame_bg_edit = QLineEdit(self.config.get("photo_frame", {}).get("background", ""))
        bg_layout.addWidget(self.frame_bg_edit, 1)
        
        # 배경화면 파일 선택 버튼
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_background_file(self, self.frame_bg_edit, "4"))
        bg_layout.addWidget(browse_button)
        
        content_layout.addWidget(bg_group)

        # 프레임 설정 그룹
        frame_group = QGroupBox("프레임 설정")
        self.apply_left_aligned_group_style(frame_group)
        frame_layout = QFormLayout(frame_group)
        
        self.frame_fields = {}
        
        # 'photo_frame' 설정이 없으면 기본값으로 초기화
        if "photo_frame" not in self.config:
            self.config["photo_frame"] = {
                "font_size": 32,
                "font_color": "green",
                "width": 800,
                "height": 600,
                "font": "",
                "background": ""
            }
        
        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["photo_frame"].get("font", ""))
        font_layout.addWidget(font_edit, 1)
        self.frame_fields["font"] = font_edit
        
        # 폰트 파일 선택 버튼 추가
        font_browse_button = QPushButton("찾기...")
        font_browse_button.clicked.connect(lambda checked: FileHandler.browse_font_file(self, font_edit))
        font_layout.addWidget(font_browse_button)
        
        frame_layout.addRow("폰트:", font_layout)
        
        # 숫자 필드들
        for key, label in [("font_size", "글자 크기"), ("width", "너비"), ("height", "높이")]:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["photo_frame"].get(key, 32 if key == "font_size" else 800 if key == "width" else 600))
            frame_layout.addRow(f"{label}:", line_edit)
            self.frame_fields[key] = line_edit
        
        # 색상 필드
        font_color_button = ColorPickerButton(self.config["photo_frame"].get("font_color", "green"))
        frame_layout.addRow("글자 색상:", font_color_button)
        self.frame_fields["font_color"] = font_color_button
            
        content_layout.addWidget(frame_group)
        content_layout.addStretch()

    def update_config(self, config):
        """UI 값을 config에 반영"""
        if "photo_frame" not in config:
            config["photo_frame"] = {}
        
        # 배경화면 저장
        config["photo_frame"]["background"] = self.frame_bg_edit.text()
        
        # 다른 필드들 저장
        for key, widget in self.frame_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["photo_frame"][key] = widget.color
            elif isinstance(widget, NumberLineEdit):
                config["photo_frame"][key] = widget.value()
            else:  # QLineEdit (font)
                config["photo_frame"][key] = widget.text()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        
        # 배경화면 업데이트
        self.frame_bg_edit.setText(config.get("photo_frame", {}).get("background", ""))
        
        if "photo_frame" in config:
            for key, widget in self.frame_fields.items():
                if isinstance(widget, ColorPickerButton):
                    widget.update_color(config["photo_frame"].get(key, "green"))
                elif isinstance(widget, NumberLineEdit):
                    widget.setValue(config["photo_frame"].get(key, 32 if key == "font_size" else 800 if key == "width" else 600))
                else:  # QLineEdit (font)
                    widget.setText(config["photo_frame"].get(key, "")) 