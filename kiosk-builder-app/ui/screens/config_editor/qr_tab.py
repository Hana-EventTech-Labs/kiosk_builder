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
        self.tab_manager = None  # TabManager 참조 추가
        self.image_preview_label = None
        self.qr_preview_label = None  # QR 코드 미리보기 라벨 추가
        self.init_ui()
        
    def set_tab_manager(self, tab_manager):
        """TabManager 참조를 설정합니다."""
        self.tab_manager = tab_manager
        
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
        preview_width_edit.textChanged.connect(self._update_qr_preview)
        qr_layout.addRow("너비:", preview_width_edit)
        self.qr_fields["preview_width"] = preview_width_edit
        
        preview_height_edit = NumberLineEdit()
        preview_height_edit.setValue(self.config["qr"]["preview_height"])
        preview_height_edit.textChanged.connect(self._update_qr_preview)
        qr_layout.addRow("높이:", preview_height_edit)
        self.qr_fields["preview_height"] = preview_height_edit
        
        x_edit = NumberLineEdit()
        x_edit.setValue(self.config["qr"]["x"])
        x_edit.textChanged.connect(self._update_qr_preview)
        qr_layout.addRow("X 위치:", x_edit)
        self.qr_fields["x"] = x_edit
        
        y_edit = NumberLineEdit()
        y_edit.setValue(self.config["qr"]["y"])
        y_edit.textChanged.connect(self._update_qr_preview)
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

        # 우측 미리보기 영역
        previews_widget = QWidget()
        previews_layout = QVBoxLayout(previews_widget)
        previews_layout.setContentsMargins(0, 0, 0, 0)
        
        # QR 코드 미리보기
        qr_preview_group = QGroupBox("QR 코드 미리보기")
        self.apply_left_aligned_group_style(qr_preview_group)
        qr_preview_layout = QVBoxLayout(qr_preview_group)
        
        self.qr_preview_label = DraggablePreviewLabel()
        self.qr_preview_label.position_changed.connect(self._on_qr_position_changed)
        self.qr_preview_label.setFixedSize(300, 300)
        self.qr_preview_label.setAlignment(Qt.AlignCenter)
        self.qr_preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        qr_preview_layout.addWidget(self.qr_preview_label, 0, Qt.AlignHCenter)

        # 버튼 레이아웃
        qr_button_layout = QHBoxLayout()
        fill_button_qr = QPushButton("채우기")
        fill_button_qr.clicked.connect(self._fill_qr_frame)
        center_button_qr = QPushButton("가운데 정렬")
        center_button_qr.clicked.connect(self._center_qr_frame)
        qr_button_layout.addWidget(fill_button_qr)
        qr_button_layout.addWidget(center_button_qr)
        qr_preview_layout.addLayout(qr_button_layout)

        previews_layout.addWidget(qr_preview_group)

        # 카드 인쇄 미리보기
        preview_group = QGroupBox("카드 인쇄 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_layout = QVBoxLayout(preview_group)
        
        self.image_preview_label = DraggablePreviewLabel()
        self.image_preview_label.position_changed.connect(self._on_image_position_changed)
        self.image_preview_label.setFixedSize(300, 300)
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        preview_layout.addWidget(self.image_preview_label, 0, Qt.AlignHCenter)
        
        # 버튼 레이아웃
        image_button_layout = QHBoxLayout()
        fill_button_image = QPushButton("채우기")
        fill_button_image.clicked.connect(self._fill_image_frame)
        center_button_image = QPushButton("가운데 정렬")
        center_button_image.clicked.connect(self._center_image_frame)
        image_button_layout.addWidget(fill_button_image)
        image_button_layout.addWidget(center_button_image)
        preview_layout.addLayout(image_button_layout)
        
        previews_layout.addWidget(preview_group)
        main_layout.addWidget(previews_widget, 1)

        # 초기 미리보기 업데이트
        self._update_card_preview()
        self._update_qr_preview()

    def _fill_qr_frame(self):
        """QR 코드를 모니터 크기에 맞게 채웁니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.qr_fields['preview_width'].setValue(monitor_width)
        self.qr_fields['preview_height'].setValue(monitor_height)
        self.qr_fields['x'].setValue(0)
        self.qr_fields['y'].setValue(0)

    def _center_qr_frame(self):
        """QR 코드를 모니터의 중앙에 정렬합니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        qr_width = self.qr_fields['preview_width'].value()
        qr_height = self.qr_fields['preview_height'].value()

        center_x = (monitor_width - qr_width) / 2
        center_y = (monitor_height - qr_height) / 2

        self.qr_fields['x'].setValue(int(center_x))
        self.qr_fields['y'].setValue(int(center_y))

    def _fill_image_frame(self):
        """업로드된 이미지를 카드 크기에 맞게 채웁니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636
        
        self.qr_uploaded_fields['width'].setValue(card_width)
        self.qr_uploaded_fields['height'].setValue(card_height)
        self.qr_uploaded_fields['x'].setValue(0)
        self.qr_uploaded_fields['y'].setValue(0)

    def _center_image_frame(self):
        """업로드된 이미지를 카드의 중앙에 정렬합니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        image_width = self.qr_uploaded_fields['width'].value()
        image_height = self.qr_uploaded_fields['height'].value()

        center_x = (card_width - image_width) / 2
        center_y = (card_height - image_height) / 2

        self.qr_uploaded_fields['x'].setValue(int(center_x))
        self.qr_uploaded_fields['y'].setValue(int(center_y))

    def _on_qr_position_changed(self, x, y):
        """드래그로 QR 코드 위치 변경 시 호출되는 슬롯"""
        self.qr_fields['x'].blockSignals(True)
        self.qr_fields['y'].blockSignals(True)
        
        self.qr_fields['x'].setValue(x)
        self.qr_fields['y'].setValue(y)
        
        self.qr_fields['x'].blockSignals(False)
        self.qr_fields['y'].blockSignals(False)
        
        # 실시간 업데이트 신호 방출
        if self.tab_manager:
            self.tab_manager.real_time_update_requested.emit()

    def _on_image_position_changed(self, x, y):
        """드래그로 이미지 위치 변경 시 호출되는 슬롯"""
        self.qr_uploaded_fields['x'].blockSignals(True)
        self.qr_uploaded_fields['y'].blockSignals(True)
        
        self.qr_uploaded_fields['x'].setValue(x)
        self.qr_uploaded_fields['y'].setValue(y)
        
        self.qr_uploaded_fields['x'].blockSignals(False)
        self.qr_uploaded_fields['y'].blockSignals(False)
        
        # 실시간 업데이트 신호 방출
        if self.tab_manager:
            self.tab_manager.real_time_update_requested.emit()

    def _update_qr_preview(self):
        """QR 코드 설정 미리보기 업데이트"""
        if not self.qr_preview_label:
            return

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920 # 기본값
            
        monitor_pixmap = QPixmap(monitor_width, monitor_height)
        monitor_pixmap.fill(Qt.black)
        
        # "QR 코드 설정" 값 가져오기
        try:
            width = self.qr_fields["preview_width"].value()
            height = self.qr_fields["preview_height"].value()
            x = self.qr_fields["x"].value()
            y = self.qr_fields["y"].value()
            qr_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            qr_rect = QRect()
            
        # 사각형 그리기
        pen = QPen(QColor("cyan"), 2, Qt.SolidLine)
        
        self.qr_preview_label.set_pen(pen)
        self.qr_preview_label.update_preview(monitor_pixmap, qr_rect)

    def _update_card_preview(self):
        """이미지 인쇄 설정 미리보기 업데이트"""
        if not self.image_preview_label:
            return

        # 전역 카드 방향 설정 사용
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636
        
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
        self._update_qr_preview()
    
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