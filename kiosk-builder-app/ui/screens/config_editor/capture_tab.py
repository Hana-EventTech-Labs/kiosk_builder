from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QPushButton, QSpinBox)
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from utils.file_handler import FileHandler
from .base_tab import BaseTab

class CaptureTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.init_ui()
        
    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()
        
        # 배경화면 설정
        bg_group = QGroupBox("배경화면 설정")
        self.apply_left_aligned_group_style(bg_group)
        bg_layout = QHBoxLayout(bg_group)
        
        # 원본 파일명 표시
        self.capture_bg_edit = QLineEdit(self.config["photo"].get("background", ""))
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
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            frame_layout.addRow(f"{label_text}:", line_edit)
            self.frame_fields[key] = line_edit
        
        content_layout.addWidget(frame_group)
        
        # 사진 설정 추가 (photo)
        photo_group = QGroupBox("촬영 사진 설정")
        self.apply_left_aligned_group_style(photo_group)
        photo_layout = QFormLayout(photo_group)
        
        self.photo_fields = {}
        
        # 위치 및 크기
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["photo"][key])
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
        
        # 카메라 카운트 설정 저장
        config["camera_count"]["number"] = self.camera_count_fields["number"].value()
        config["camera_count"]["font_size"] = self.camera_count_fields["font_size"].value()
        config["camera_count"]["font_color"] = self.camera_count_fields["font_color"].color