from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QPushButton, QWidget)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRect
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from utils.file_handler import FileHandler
from .base_tab import BaseTab
from ui.components.preview_label import DraggablePreviewLabel

class ProcessingTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.final_card_preview_label = None
        self.init_ui()
        
    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()

        # 메인 레이아웃 (좌: 설정, 우: 미리보기)
        main_layout = QHBoxLayout()
        content_layout.addLayout(main_layout)

        # 설정 영역
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # 발급중 화면 설정
        process_group = QGroupBox("발급중 화면 설정")
        self.apply_left_aligned_group_style(process_group)
        process_layout = QFormLayout(process_group)
        
        # 필드 저장을 위한 딕셔너리
        self.process_fields = {}
        
        # 배경화면 선택 레이아웃 추가
        background_layout = QHBoxLayout()
        # 원본 파일명 표시
        background_edit = QLineEdit(self.config["process"].get("background", ""))
        background_layout.addWidget(background_edit, 1)
        self.process_fields["background"] = background_edit
        
        # 배경화면 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_background_file(self, background_edit, "process"))
        background_layout.addWidget(browse_button)
        
        process_layout.addRow("배경화면:", background_layout)
        
        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["process"]["font"])
        font_layout.addWidget(font_edit, 1)
        self.process_fields["font"] = font_edit
        
        # 폰트 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_font_file(self, font_edit))
        font_layout.addWidget(browse_button)
        
        process_layout.addRow("폰트:", font_layout)
        
        phrase_edit = QLineEdit(self.config["process"]["phrase"])
        process_layout.addRow("문구:", phrase_edit)
        self.process_fields["phrase"] = phrase_edit
        
        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config["process"]["font_size"])
        process_layout.addRow("폰트 크기:", font_size_edit)
        self.process_fields["font_size"] = font_size_edit
        
        font_color_button = ColorPickerButton(self.config["process"]["font_color"])
        process_layout.addRow("폰트 색상:", font_color_button)
        self.process_fields["font_color"] = font_color_button
        
        x_edit = NumberLineEdit()
        x_edit.setValue(self.config["process"]["x"])
        process_layout.addRow("X 위치:", x_edit)
        self.process_fields["x"] = x_edit
        
        y_edit = NumberLineEdit()
        y_edit.setValue(self.config["process"]["y"])
        process_layout.addRow("Y 위치:", y_edit)
        self.process_fields["y"] = y_edit
        
        # 시간 필드
        time_edit = NumberLineEdit()
        time_edit.setValue(self.config["process"]["process_time"])
        process_layout.addRow("시간 (ms):", time_edit)
        self.process_fields["process_time"] = time_edit
        
        settings_layout.addWidget(process_group)
        
        # 스트레치 추가
        settings_layout.addStretch()

        # 좌측 설정 영역을 메인 레이아웃에 추가
        main_layout.addWidget(settings_widget, 1)

        # 우측 미리보기 영역
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # 최종 카드 미리보기
        final_preview_group = QGroupBox("최종 카드 미리보기")
        self.apply_left_aligned_group_style(final_preview_group)
        final_preview_layout = QVBoxLayout(final_preview_group)
        
        self.final_card_preview_label = QLabel()
        self.final_card_preview_label.setFixedSize(400, 400)
        self.final_card_preview_label.setAlignment(Qt.AlignCenter)
        self.final_card_preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        final_preview_layout.addWidget(self.final_card_preview_label, 0, Qt.AlignHCenter)
        
        # 미리보기 업데이트 버튼
        update_preview_button = QPushButton("미리보기 업데이트")
        update_preview_button.clicked.connect(self._update_final_card_preview)
        final_preview_layout.addWidget(update_preview_button, 0, Qt.AlignHCenter)
        
        preview_layout.addWidget(final_preview_group)
        preview_layout.addStretch()
        
        main_layout.addWidget(preview_widget, 1)

        # 초기 미리보기 업데이트
        self._update_final_card_preview()

    def _update_final_card_preview(self):
        """최종 카드 미리보기 업데이트"""
        if not self.final_card_preview_label:
            return

        # 카드 크기 (전역 설정 기준)
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636
        
        # 카드 배경 생성
        card_pixmap = QPixmap(card_width, card_height)
        card_pixmap.fill(Qt.white)
        
        painter = QPainter(card_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 체크된 화면 순서 확인
        screen_order = self.config.get("screen_order", [])
        
        # 1. 촬영 화면이 체크되어 있으면 촬영 사진 영역 그리기
        if 1 in screen_order:  # 촬영 화면
            self._draw_photo_area(painter, card_width, card_height)
        
        # 2. 키보드 화면이 체크되어 있으면 텍스트 입력 및 고정 텍스트 그리기
        if 2 in screen_order:  # 키보드 화면
            self._draw_text_areas(painter, card_width, card_height)
        
        # 3. QR코드 화면이 체크되어 있으면 QR 업로드 이미지 영역 그리기
        if 3 in screen_order:  # QR코드 화면
            self._draw_qr_image_area(painter, card_width, card_height)
        
        # 4. 기본 이미지들 그리기 (basic_tab에서 설정한 이미지들)
        self._draw_basic_images(painter, card_width, card_height)
        
        painter.end()
        
        # 미리보기 라벨에 표시
        scaled_pixmap = card_pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.final_card_preview_label.setPixmap(scaled_pixmap)

    def _draw_photo_area(self, painter, card_width, card_height):
        """촬영 사진 영역 그리기"""
        try:
            photo_config = self.config.get("photo", {})
            x = photo_config.get("x", 0)
            y = photo_config.get("y", 0)
            width = photo_config.get("width", 300)
            height = photo_config.get("height", 300)
            
            # 촬영 사진 영역 (빨간색 테두리)
            pen = QPen(QColor("red"), 3, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(x, y, width, height)
            
            # 라벨 추가
            painter.setPen(QPen(QColor("red"), 1))
            painter.drawText(x + 5, y + 20, "촬영 사진")
        except Exception as e:
            pass

    def _draw_text_areas(self, painter, card_width, card_height):
        """텍스트 입력 및 고정 텍스트 영역 그리기"""
        try:
            # 텍스트 입력 필드들
            text_input_items = self.config.get("text_input", {}).get("items", [])
            colors = [QColor("blue"), QColor("green"), QColor("orange"), QColor("purple")]
            
            for i, item in enumerate(text_input_items):
                x = item.get("x", 0)
                y = item.get("y", 0)
                width = item.get("width", 200)
                height = item.get("height", 50)
                
                # 텍스트 입력 영역 그리기
                color = colors[i % len(colors)]
                pen = QPen(color, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(x, y, width, height)
                
                # 라벨 추가
                painter.setPen(QPen(color, 1))
                label = item.get("label", f"입력{i+1}")
                painter.drawText(x + 5, y + 15, label)
            
            # 고정 텍스트들
            text_items = self.config.get("texts", {}).get("items", [])
            fixed_colors = [QColor("cyan"), QColor("magenta"), QColor("yellow"), QColor("brown")]
            
            for i, item in enumerate(text_items):
                x = item.get("x", 0)
                y = item.get("y", 0)
                width = item.get("width", 200)
                height = item.get("height", 50)
                
                # 고정 텍스트 영역 그리기
                color = fixed_colors[i % len(fixed_colors)]
                pen = QPen(color, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(x, y, width, height)
                
                # 텍스트 내용 표시
                painter.setPen(QPen(color, 1))
                content = item.get("content", f"텍스트{i+1}")
                painter.drawText(x + 5, y + 15, content)
                
        except Exception as e:
            pass

    def _draw_qr_image_area(self, painter, card_width, card_height):
        """QR 업로드 이미지 영역 그리기"""
        try:
            qr_image_config = self.config.get("qr_uploaded_image", {})
            x = qr_image_config.get("x", 0)
            y = qr_image_config.get("y", 0)
            width = qr_image_config.get("width", 200)
            height = qr_image_config.get("height", 200)
            
            # QR 업로드 이미지 영역 (보라색 테두리)
            pen = QPen(QColor("purple"), 3, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(x, y, width, height)
            
            # 라벨 추가
            painter.setPen(QPen(QColor("purple"), 1))
            painter.drawText(x + 5, y + 20, "QR 이미지")
        except Exception as e:
            pass

    def _draw_basic_images(self, painter, card_width, card_height):
        """기본 이미지들 그리기"""
        try:
            images = self.config.get("images", {}).get("items", [])
            
            for i, image in enumerate(images):
                x = image.get("x", 0)
                y = image.get("y", 0)
                width = image.get("width", 100)
                height = image.get("height", 100)
                
                # 기본 이미지 영역 (회색 테두리)
                pen = QPen(QColor("gray"), 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(x, y, width, height)
                
                # 라벨 추가
                painter.setPen(QPen(QColor("gray"), 1))
                filename = image.get("filename", f"이미지{i+1}")
                # 파일명에서 확장자 제거
                if "." in filename:
                    filename = filename.split(".")[0]
                painter.drawText(x + 5, y + 15, filename)
                
        except Exception as e:
            pass
    
    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        for key, widget in self.process_fields.items():
            if isinstance(widget, ColorPickerButton):
                widget.update_color(config["process"][key])
            else:
                if isinstance(widget, NumberLineEdit):
                    widget.setValue(config["process"][key])
                else:
                    widget.setText(config["process"][key])
        
        # 미리보기 업데이트
        self._update_final_card_preview()
    
    def update_config(self, config):
        """UI 값을 config에 반영"""
        for key, widget in self.process_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["process"][key] = widget.color
            else:
                if isinstance(widget, NumberLineEdit):
                    config["process"][key] = widget.value()
                else:
                    config["process"][key] = widget.text()