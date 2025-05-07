from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QPushButton)
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from utils.file_handler import FileHandler
from .base_tab import BaseTab

class SplashTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.init_ui()
        
    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()
        
        # 스플래시 화면 설정
        splash_group = QGroupBox("스플래쉬 화면 설정")
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
        splash_layout.addRow("문구:", phrase_edit)
        self.splash_fields["phrase"] = phrase_edit
        
        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config["splash"]["font_size"])
        splash_layout.addRow("폰트 크기:", font_size_edit)
        self.splash_fields["font_size"] = font_size_edit
        
        font_color_button = ColorPickerButton(self.config["splash"]["font_color"])
        splash_layout.addRow("폰트 색상:", font_color_button)
        self.splash_fields["font_color"] = font_color_button
        
        x_edit = NumberLineEdit()
        x_edit.setValue(self.config["splash"]["x"])
        splash_layout.addRow("X 위치:", x_edit)
        self.splash_fields["x"] = x_edit
        
        y_edit = NumberLineEdit()
        y_edit.setValue(self.config["splash"]["y"])
        splash_layout.addRow("Y 위치:", y_edit)
        self.splash_fields["y"] = y_edit
        
        content_layout.addWidget(splash_group)
        
        # 스트레치 추가
        content_layout.addStretch()
        
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