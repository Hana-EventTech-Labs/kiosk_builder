from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QPushButton, QWidget)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect
from ui.components.inputs import NumberLineEdit
from utils.file_handler import FileHandler
from .base_tab import BaseTab
from ui.components.preview_label import DraggablePreviewLabel

class QRTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.image_preview_label = None
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
            line_edit.textChanged.connect(self._update_card_preview)
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            qr_uploaded_layout.addRow(f"{label_text}:", line_edit)
            self.qr_uploaded_fields[key] = line_edit
        
        content_layout.addWidget(qr_uploaded_group)
        
        # 스트레치 추가
        content_layout.addStretch()

        # 좌측 설정 영역을 메인 레이아웃에 추가
        main_layout.addWidget(settings_widget, 1)

        # 우측 미리보기 영역 추가
        preview_group = QGroupBox("미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_layout = QVBoxLayout(preview_group)
        
        self.image_preview_label = DraggablePreviewLabel()
        self.image_preview_label.position_changed.connect(self._on_image_position_changed)
        self.image_preview_label.setFixedSize(300, 300)
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        preview_layout.addWidget(self.image_preview_label, 0, Qt.AlignHCenter)
        main_layout.addWidget(preview_group, 1)

        # 초기 미리보기 업데이트
        self._update_card_preview()

    def _on_image_position_changed(self, x, y):
        """드래그로 이미지 위치 변경 시 호출되는 슬롯"""
        self.qr_uploaded_fields['x'].blockSignals(True)
        self.qr_uploaded_fields['y'].blockSignals(True)
        
        self.qr_uploaded_fields['x'].setValue(x)
        self.qr_uploaded_fields['y'].setValue(y)
        
        self.qr_uploaded_fields['x'].blockSignals(False)
        self.qr_uploaded_fields['y'].blockSignals(False)

    def _update_card_preview(self):
        """이미지 인쇄 설정 미리보기 업데이트"""
        if not self.image_preview_label:
            return

        card_width, card_height = 636, 1012
        card_pixmap = QPixmap(card_width, card_height)
        card_pixmap.fill(Qt.white)

        try:
            # 업로드된 이미지 위치 그리기 (빨간색)
            width = self.qr_uploaded_fields["width"].value()
            height = self.qr_uploaded_fields["height"].value()
            x = self.qr_uploaded_fields["x"].value()
            y = self.qr_uploaded_fields["y"].value()
            image_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            image_rect = QRect()
            
        pen = QPen(QColor("red"), 2, Qt.SolidLine)

        self.image_preview_label.set_pen(pen)
        self.image_preview_label.update_preview(card_pixmap, image_rect)
    
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

        # 미리보기 업데이트
        self._update_card_preview()
    
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