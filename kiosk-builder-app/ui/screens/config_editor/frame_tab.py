from PySide6.QtWidgets import QGroupBox, QFormLayout
from .base_tab import BaseTab
from ui.components.inputs import NumberLineEdit

class FrameTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.init_ui()

    def init_ui(self):
        content_layout = self.create_tab_with_scroll()

        # 프레임 설정 그룹
        frame_group = QGroupBox("프레임 설정")
        self.apply_left_aligned_group_style(frame_group)
        frame_layout = QFormLayout(frame_group)
        
        self.frame_fields = {}
        
        # 'photo_frame' 설정이 없으면 기본값으로 초기화
        if "photo_frame" not in self.config:
            self.config["photo_frame"] = {
                "amount": 0,
                "font_size": 32,
                "font_color": "#000000",
                "x": 0,
                "y": 0
            }
        
        # 필드 생성
        for key, label in [("amount", "프레임 개수"), ("font_size", "글자 크기"), 
                             ("font_color", "글자 색상"), ("x", "X 위치"), ("y", "Y 위치")]:
            
            line_edit = NumberLineEdit()
            # 'photo_frame'에서 값 가져오기
            line_edit.setValue(self.config["photo_frame"].get(key, 0))
            
            frame_layout.addRow(f"{label}:", line_edit)
            self.frame_fields[key] = line_edit
            
        content_layout.addWidget(frame_group)
        content_layout.addStretch()

    def update_config(self, config):
        """UI 값을 config에 반영"""
        if "photo_frame" not in config:
            config["photo_frame"] = {}
            
        for key, widget in self.frame_fields.items():
            config["photo_frame"][key] = widget.value()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        if "photo_frame" in config:
            for key, widget in self.frame_fields.items():
                widget.setValue(config["photo_frame"].get(key, 0)) 