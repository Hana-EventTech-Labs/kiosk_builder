from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QPushButton, QSpinBox, QWidget)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from utils.file_handler import FileHandler
from .base_tab import BaseTab

class CaptureTab(BaseTab):
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

        # 우측 미리보기 영역 추가
        preview_group = QGroupBox("미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_layout = QVBoxLayout(preview_group)
        
        self.image_preview_label = QLabel()
        self.image_preview_label.setFixedSize(300, 300)
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        preview_layout.addWidget(self.image_preview_label, 0, Qt.AlignHCenter)
        main_layout.addWidget(preview_group, 1)

        # 초기 미리보기 업데이트
        self._update_card_preview()

    def _update_card_preview(self):
        """촬영 사진 인쇄 크기 설정 미리보기 업데이트"""
        if not self.image_preview_label:
            return

        # 카드 크기 (세로 기준)
        card_width, card_height = 636, 1012
        card_pixmap = QPixmap(card_width, card_height)
        card_pixmap.fill(Qt.white)

        painter = QPainter(card_pixmap)
        
        # "촬영 사진 인쇄크기 설정" 값 가져오기
        try:
            width = self.photo_fields["width"].value()
            height = self.photo_fields["height"].value()
            x = self.photo_fields["x"].value()
            y = self.photo_fields["y"].value()
        except (AttributeError, KeyError):
            # 위젯이 아직 완전히 생성되지 않았을 수 있음
            painter.end()
            return
            
        # 사각형 그리기
        pen = QPen(QColor("red"), 10, Qt.SolidLine) # 10px 빨간 테두리
        painter.setPen(pen)
        painter.setBrush(Qt.white) # 흰색으로 채우기
        painter.drawRect(x, y, width, height)
        
        painter.end()

        # 라벨에 최종 이미지 설정
        self.image_preview_label.setPixmap(card_pixmap.scaled(
            self.image_preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
    
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
        
        # 카메라 카운트 설정 저장
        config["camera_count"]["number"] = self.camera_count_fields["number"].value()
        config["camera_count"]["font_size"] = self.camera_count_fields["font_size"].value()
        config["camera_count"]["font_color"] = self.camera_count_fields["font_color"].color