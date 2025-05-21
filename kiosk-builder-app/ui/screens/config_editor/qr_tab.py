from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QPushButton)
from ui.components.inputs import NumberLineEdit
from utils.file_handler import FileHandler
from .base_tab import BaseTab

class QRTab(BaseTab):
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
        self.qr_bg_edit = QLineEdit(self.config["qr"].get("background", ""))
        bg_layout.addWidget(self.qr_bg_edit, 1)
        
        # 배경화면 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_background_file(self, self.qr_bg_edit, "3"))
        bg_layout.addWidget(browse_button)
        
        content_layout.addWidget(bg_group)
        
        # QR 코드 설정 그룹
        qr_group = QGroupBox("QR 코드 설정")
        self.apply_left_aligned_group_style(qr_group)
        qr_layout = QFormLayout(qr_group)
        
        self.qr_fields = {}
        
        # 미리보기 영역 위치 및 크기 설정
        preview_width_edit = NumberLineEdit()
        preview_width_edit.setValue(self.config["qr"]["preview_width"])
        qr_layout.addRow("너비:", preview_width_edit)
        self.qr_fields["preview_width"] = preview_width_edit
        
        preview_height_edit = NumberLineEdit()
        preview_height_edit.setValue(self.config["qr"]["preview_height"])
        qr_layout.addRow("높이:", preview_height_edit)
        self.qr_fields["preview_height"] = preview_height_edit
        
        x_edit = NumberLineEdit()
        x_edit.setValue(self.config["qr"]["x"])
        qr_layout.addRow("X 위치:", x_edit)
        self.qr_fields["x"] = x_edit
        
        y_edit = NumberLineEdit()
        y_edit.setValue(self.config["qr"]["y"])
        qr_layout.addRow("Y 위치:", y_edit)
        self.qr_fields["y"] = y_edit
        
        content_layout.addWidget(qr_group)
        
        # 업로드 이미지 설정 그룹박스 추가
        qr_uploaded_group = QGroupBox("이미지 인쇄 설정")
        self.apply_left_aligned_group_style(qr_uploaded_group)
        qr_uploaded_layout = QFormLayout(qr_uploaded_group)
        
        self.qr_uploaded_fields = {}
        
        # 이미지 위치 및 크기 설정
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["qr_uploaded_image"][key])
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            qr_uploaded_layout.addRow(f"{label_text}:", line_edit)
            self.qr_uploaded_fields[key] = line_edit
        
        content_layout.addWidget(qr_uploaded_group)
        
        # 스트레치 추가
        content_layout.addStretch()
    
    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        self.qr_bg_edit.setText(config["qr"].get("background", ""))
        
        # QR 코드 설정 업데이트
        for key, widget in self.qr_fields.items():
            widget.setValue(config["qr"][key])
        
        # QR 업로드 이미지 설정 업데이트
        for key, widget in self.qr_uploaded_fields.items():
            widget.setValue(config["qr_uploaded_image"][key])
    
    def update_config(self, config):
        """UI 값을 config에 반영"""
        # 배경화면 저장
        config["qr"]["background"] = self.qr_bg_edit.text()
        
        # QR 코드 설정 저장
        for key, widget in self.qr_fields.items():
            config["qr"][key] = widget.value()
        
        # QR 업로드 이미지 설정 저장
        for key, widget in self.qr_uploaded_fields.items():
            config["qr_uploaded_image"][key] = widget.value()