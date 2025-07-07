from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QPushButton, QSpinBox, QWidget, QGridLayout)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from utils.file_handler import FileHandler
from .base_tab import BaseTab
from ui.components.preview_label import DraggablePreviewLabel

class KeyboardTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.keyboard_preview_label = None
        self.text_input_preview_labels = []  # 사용자 입력 설정 미리보기 라벨들
        self.text_input_preview_container = None
        self.fixed_text_preview_labels = []  # 고정 텍스트 미리보기 라벨들
        self.fixed_text_preview_container = None
        self.init_ui()
        
    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        scroll_content_layout = self.create_tab_with_scroll()

        # 메인 레이아웃을 QGridLayout으로 변경
        main_layout = QGridLayout()
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        scroll_content_layout.addLayout(main_layout)

        # -- 좌측 상단 위젯 (배경, 키보드 위치) --
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(10)

        # 배경화면 설정
        bg_group = QGroupBox("배경화면 설정")
        self.apply_left_aligned_group_style(bg_group)
        bg_layout = QHBoxLayout(bg_group)
        self.keyboard_bg_edit = QLineEdit(self.config["text_input"].get("background", ""))
        bg_layout.addWidget(self.keyboard_bg_edit, 1)
        browse_button_bg = QPushButton("찾기...")
        browse_button_bg.clicked.connect(lambda checked: FileHandler.browse_background_file(self, self.keyboard_bg_edit, "2"))
        bg_layout.addWidget(browse_button_bg)
        
        # 키보드 위치 및 크기
        position_group = QGroupBox("키보드 위치 및 크기")
        self.apply_left_aligned_group_style(position_group)
        position_layout = QFormLayout(position_group)
        self.keyboard_position_fields = {}
        for key in ["width", "height", "x", "y"]:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["keyboard"][key])
            line_edit.textChanged.connect(self._update_keyboard_preview)
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            position_layout.addRow(f"{label_text}:", line_edit)
            self.keyboard_position_fields[key] = line_edit

        # 위젯들을 아래로 밀기 위해 stretch 추가
        left_layout.addStretch(1)
        left_layout.addWidget(bg_group)
        left_layout.addWidget(position_group)

        # -- 우측 상단 위젯 (미리보기들) --
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 키보드 미리보기
        keyboard_preview_group = QGroupBox("키보드 미리보기")
        self.apply_left_aligned_group_style(keyboard_preview_group)
        keyboard_preview_layout = QVBoxLayout(keyboard_preview_group)
        self.keyboard_preview_label = DraggablePreviewLabel()
        self.keyboard_preview_label.position_changed.connect(self._on_keyboard_position_changed)
        self.keyboard_preview_label.setFixedSize(300, 300)
        self.keyboard_preview_label.setAlignment(Qt.AlignCenter)
        self.keyboard_preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        keyboard_preview_layout.addWidget(self.keyboard_preview_label, 0, Qt.AlignHCenter)
        keyboard_button_layout = QHBoxLayout()
        fill_button_keyboard = QPushButton("채우기")
        fill_button_keyboard.clicked.connect(self._fill_keyboard_frame)
        center_button_keyboard = QPushButton("가운데 정렬")
        center_button_keyboard.clicked.connect(self._center_keyboard_frame)
        keyboard_button_layout.addWidget(fill_button_keyboard)
        keyboard_button_layout.addWidget(center_button_keyboard)
        keyboard_preview_layout.addLayout(keyboard_button_layout)

        # 사용자 입력 설정 미리보기 컨테이너
        self.text_input_preview_container = QWidget()
        self.text_input_preview_layout = QVBoxLayout(self.text_input_preview_container)
        self.text_input_preview_layout.setContentsMargins(0, 0, 0, 0)
        self.text_input_preview_layout.setSpacing(10)

        # 고정 텍스트 미리보기 컨테이너
        self.fixed_text_preview_container = QWidget()
        self.fixed_text_preview_layout = QVBoxLayout(self.fixed_text_preview_container)
        self.fixed_text_preview_layout.setContentsMargins(0, 0, 0, 0)
        self.fixed_text_preview_layout.setSpacing(10)

        right_layout.addWidget(keyboard_preview_group)
        right_layout.addWidget(self.text_input_preview_container)
        right_layout.addWidget(self.fixed_text_preview_container)
        right_layout.addStretch()

        # -- 하단 위젯 (나머지 설정들) --
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 10, 0, 0)
        bottom_layout.setSpacing(10)
        bottom_widget.setLayout(bottom_layout)
        
        # 사용자 입력 필드 설정
        text_input_group = QGroupBox("사용자 입력 필드 설정")
        self.apply_left_aligned_group_style(text_input_group)
        text_input_layout = QVBoxLayout(text_input_group)
        basic_settings_layout = QFormLayout()
        self.text_input_fields = {}
        settings_map = {"margin_top": "상단 여백", "margin_left": "왼쪽 여백", "margin_right": "오른쪽 여백", "spacing": "간격"}
        for key in settings_map:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["text_input"][key])
            basic_settings_layout.addRow(f"{settings_map[key]}:", line_edit)
            self.text_input_fields[key] = line_edit
        text_input_layout.addLayout(basic_settings_layout)
        text_input_count_layout = QHBoxLayout()
        self.text_input_count_spinbox = QSpinBox()
        self.text_input_count_spinbox.setRange(1, 10)
        count_value = max(1, self.config["text_input"]["count"])
        self.text_input_count_spinbox.setValue(count_value)
        self.text_input_count_spinbox.valueChanged.connect(self.update_text_input_items)
        text_input_count_layout.addWidget(QLabel("사용자 입력 필드 개수:"))
        text_input_count_layout.addWidget(self.text_input_count_spinbox)
        text_input_count_layout.addStretch()
        text_input_layout.addLayout(text_input_count_layout)
        self.text_input_items_container = QWidget()
        self.text_input_items_layout = QVBoxLayout(self.text_input_items_container)
        self.text_input_items_layout.setContentsMargins(0, 0, 0, 0)
        self.text_input_item_fields = []
        self.update_text_input_items(count_value)
        text_input_layout.addWidget(self.text_input_items_container)
        bottom_layout.addWidget(text_input_group)

        # 고정 텍스트 설정
        texts_group = QGroupBox("고정 텍스트 설정")
        self.apply_left_aligned_group_style(texts_group)
        texts_layout = QVBoxLayout(texts_group)
        text_count_layout = QHBoxLayout()
        self.text_count_spinbox = QSpinBox()
        self.text_count_spinbox.setRange(0, 10)
        self.text_count_spinbox.setValue(self.config["texts"]["count"])
        self.text_count_spinbox.valueChanged.connect(self.update_text_items)
        text_count_layout.addWidget(self.text_count_spinbox)
        text_count_layout.addStretch()
        texts_layout.addLayout(text_count_layout)
        self.text_items_container = QWidget()
        self.text_items_layout = QVBoxLayout(self.text_items_container)
        self.text_items_layout.setContentsMargins(0, 0, 0, 0)
        self.text_item_fields = []
        self.update_text_items(self.config["texts"]["count"])
        texts_layout.addWidget(self.text_items_container)
        bottom_layout.addWidget(texts_group)

        # 키보드 스타일
        style_group = QGroupBox("키보드 스타일")
        self.apply_left_aligned_group_style(style_group)
        style_layout = QFormLayout(style_group)
        self.keyboard_style_fields = {}
        color_keys = ["bg_color", "border_color", "button_bg_color", "button_text_color", "button_pressed_color", "hangul_btn_color", "shift_btn_color", "backspace_btn_color", "next_btn_color"]
        color_labels = {"bg_color": "배경 색상", "border_color": "테두리 색상", "button_bg_color": "버튼 배경 색상", "button_text_color": "버튼 텍스트 색상", "button_pressed_color": "버튼 누름 색상", "hangul_btn_color": "한글 버튼 색상", "shift_btn_color": "시프트 버튼 색상", "backspace_btn_color": "지우기 버튼 색상", "next_btn_color": "다음 버튼 색상"}
        for key in color_keys:
            color_button = ColorPickerButton(self.config["keyboard"][key])
            style_layout.addRow(f"{color_labels[key]}:", color_button)
            self.keyboard_style_fields[key] = color_button
        number_keys = ["border_width", "border_radius", "padding", "font_size", "button_radius", "special_btn_width", "max_hangul", "max_lowercase", "max_uppercase"]
        number_labels = {"border_width": "테두리 두께", "border_radius": "테두리 둥글기", "padding": "내부 여백", "font_size": "폰트 크기", "button_radius": "버튼 둥글기", "special_btn_width": "특수 버튼 너비", "max_hangul": "최대 한글 자수", "max_lowercase": "최대 소문자 자수", "max_uppercase": "최대 대문자 자수"}
        for key in number_keys:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["keyboard"][key])
            style_layout.addRow(f"{number_labels[key]}:", line_edit)
            self.keyboard_style_fields[key] = line_edit
        bottom_layout.addWidget(style_group)

        # -- 그리드에 위젯 배치 --
        main_layout.addWidget(left_widget, 0, 0)
        main_layout.addWidget(right_widget, 0, 1, 2, 1)  # 0행부터 2행까지 우측 전체 영역 사용
        main_layout.addWidget(bottom_widget, 1, 0, 1, 1)  # 1, 1로 변경하여 왼쪽 반만 사용
        
        main_layout.setRowStretch(1, 1) # 하단 영역이 남는 공간을 차지하도록

        # 초기 미리보기 업데이트
        self._update_keyboard_preview()
        self._update_text_input_previews()

    def _on_keyboard_position_changed(self, x, y):
        """드래그로 키보드 위치 변경 시 호출되는 슬롯"""
        self.keyboard_position_fields['x'].blockSignals(True)
        self.keyboard_position_fields['y'].blockSignals(True)
        
        self.keyboard_position_fields['x'].setValue(x)
        self.keyboard_position_fields['y'].setValue(y)
        
        self.keyboard_position_fields['x'].blockSignals(False)
        self.keyboard_position_fields['y'].blockSignals(False)

    def _on_text_input_position_changed(self, index, x, y):
        """드래그로 텍스트 입력 위치 변경 시 호출되는 슬롯"""
        if index < len(self.text_input_item_fields):
            fields = self.text_input_item_fields[index]
            fields['x'].blockSignals(True)
            fields['y'].blockSignals(True)
            
            fields['x'].setValue(x)
            fields['y'].setValue(y)
            
            fields['x'].blockSignals(False)
            fields['y'].blockSignals(False)

    def _on_fixed_text_position_changed(self, index, x, y):
        """고정 텍스트 위치 변경 시 호출"""
        if index < len(self.text_item_fields):
            fields = self.text_item_fields[index]
            fields['x'].blockSignals(True)
            fields['y'].blockSignals(True)
            
            fields['x'].setValue(x)
            fields['y'].setValue(y)
            
            fields['x'].blockSignals(False)
            fields['y'].blockSignals(False)

    def _fill_keyboard_frame(self):
        """키보드를 모니터 크기에 맞게 채웁니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.keyboard_position_fields['width'].setValue(monitor_width)
        self.keyboard_position_fields['height'].setValue(monitor_height)
        self.keyboard_position_fields['x'].setValue(0)
        self.keyboard_position_fields['y'].setValue(0)

    def _center_keyboard_frame(self):
        """키보드를 모니터의 중앙에 정렬합니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        keyboard_width = self.keyboard_position_fields['width'].value()
        keyboard_height = self.keyboard_position_fields['height'].value()

        center_x = (monitor_width - keyboard_width) / 2
        center_y = (monitor_height - keyboard_height) / 2

        self.keyboard_position_fields['x'].setValue(int(center_x))
        self.keyboard_position_fields['y'].setValue(int(center_y))

    def _fill_text_input_frame(self, index):
        """텍스트 입력을 카드 크기에 맞게 채웁니다."""
        if index >= len(self.text_input_item_fields):
            return
            
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        fields = self.text_input_item_fields[index]
        fields['width'].setValue(card_width)
        fields['height'].setValue(card_height)
        fields['x'].setValue(0)
        fields['y'].setValue(0)

    def _center_text_input_frame(self, index):
        """텍스트 입력을 카드의 중앙에 정렬합니다."""
        if index >= len(self.text_input_item_fields):
            return
            
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        fields = self.text_input_item_fields[index]
        input_width = fields['width'].value()
        input_height = fields['height'].value()

        center_x = (card_width - input_width) / 2
        center_y = (card_height - input_height) / 2

        fields['x'].setValue(int(center_x))
        fields['y'].setValue(int(center_y))

    def _fill_fixed_text_frame(self, index):
        """고정 텍스트를 카드 크기에 맞게 채웁니다."""
        if index >= len(self.text_item_fields):
            return
            
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        fields = self.text_item_fields[index]
        fields['width'].setValue(card_width)
        fields['height'].setValue(card_height)
        fields['x'].setValue(0)
        fields['y'].setValue(0)

    def _center_fixed_text_frame(self, index):
        """고정 텍스트를 카드의 중앙에 정렬합니다."""
        if index >= len(self.text_item_fields):
            return
            
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        fields = self.text_item_fields[index]
        text_width = fields['width'].value()
        text_height = fields['height'].value()

        center_x = (card_width - text_width) / 2
        center_y = (card_height - text_height) / 2

        fields['x'].setValue(int(center_x))
        fields['y'].setValue(int(center_y))

    def _update_keyboard_preview(self):
        """키보드 설정 미리보기 업데이트"""
        if not self.keyboard_preview_label:
            return

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920 # 기본값
            
        monitor_pixmap = QPixmap(monitor_width, monitor_height)
        monitor_pixmap.fill(Qt.black)
        
        # "키보드 위치 및 크기" 값 가져오기
        try:
            width = self.keyboard_position_fields["width"].value()
            height = self.keyboard_position_fields["height"].value()
            x = self.keyboard_position_fields["x"].value()
            y = self.keyboard_position_fields["y"].value()
            keyboard_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            keyboard_rect = QRect()
            
        # 사각형 그리기
        pen = QPen(QColor("magenta"), 2, Qt.SolidLine)
        
        self.keyboard_preview_label.set_pen(pen)
        self.keyboard_preview_label.update_preview(monitor_pixmap, keyboard_rect)

    def _update_text_input_previews(self):
        """사용자 입력 설정 미리보기들 업데이트"""
        # 기존 미리보기 제거
        for i in reversed(range(self.text_input_preview_layout.count())):
            item = self.text_input_preview_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.text_input_preview_labels = []
        
        # 각 입력 필드에 대해 미리보기 생성
        for i, fields in enumerate(self.text_input_item_fields):
            self._create_text_input_preview(i, fields)

    def _create_text_input_preview(self, index, fields):
        """개별 텍스트 입력 미리보기 생성"""
        # 미리보기 그룹 생성
        preview_group = QGroupBox(f"텍스트 입력 {index+1} 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_layout = QVBoxLayout(preview_group)
        
        # 미리보기 라벨 생성
        preview_label = DraggablePreviewLabel()
        preview_label.position_changed.connect(lambda x, y, idx=index: self._on_text_input_position_changed(idx, x, y))
        preview_label.setFixedSize(300, 300)
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        preview_layout.addWidget(preview_label, 0, Qt.AlignHCenter)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        fill_button = QPushButton("채우기")
        fill_button.clicked.connect(lambda checked, idx=index: self._fill_text_input_frame(idx))
        center_button = QPushButton("가운데 정렬")
        center_button.clicked.connect(lambda checked, idx=index: self._center_text_input_frame(idx))
        button_layout.addWidget(fill_button)
        button_layout.addWidget(center_button)
        preview_layout.addLayout(button_layout)
        
        # 컨테이너에 추가
        self.text_input_preview_layout.addWidget(preview_group)
        self.text_input_preview_labels.append(preview_label)
        
        # 초기 미리보기 업데이트
        self._update_single_text_input_preview(index, fields)

    def _update_single_text_input_preview(self, index, fields):
        """개별 텍스트 입력 미리보기 업데이트"""
        if index >= len(self.text_input_preview_labels):
            return
            
        preview_label = self.text_input_preview_labels[index]
        
        # 카드 크기 (전역 설정 기준)
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636
        
        card_pixmap = QPixmap(card_width, card_height)
        card_pixmap.fill(Qt.white)
        
        try:
            width = fields["width"].value()
            height = fields["height"].value()
            x = fields["x"].value()
            y = fields["y"].value()
            input_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            input_rect = QRect()
            
        # 사각형 그리기
        colors = [QColor("red"), QColor("blue"), QColor("green"), QColor("orange"), QColor("purple")]
        color = colors[index % len(colors)]
        pen = QPen(color, 2, Qt.SolidLine)
        
        preview_label.set_pen(pen)
        preview_label.update_preview(card_pixmap, input_rect)

    def _update_fixed_text_previews(self):
        """고정 텍스트 미리보기들 업데이트"""
        # 기존 미리보기 제거
        for i in reversed(range(self.fixed_text_preview_layout.count())):
            item = self.fixed_text_preview_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.fixed_text_preview_labels = []
        
        # 각 고정 텍스트에 대해 미리보기 생성
        for i, fields in enumerate(self.text_item_fields):
            self._create_fixed_text_preview(i, fields)

    def _create_fixed_text_preview(self, index, fields):
        """개별 고정 텍스트 미리보기 생성"""
        # 미리보기 그룹 생성
        preview_group = QGroupBox(f"고정 텍스트 {index+1} 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_layout = QVBoxLayout(preview_group)
        
        # 미리보기 라벨 생성
        preview_label = DraggablePreviewLabel()
        preview_label.position_changed.connect(lambda x, y, idx=index: self._on_fixed_text_position_changed(idx, x, y))
        preview_label.setFixedSize(300, 300)
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        preview_layout.addWidget(preview_label, 0, Qt.AlignHCenter)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        fill_button = QPushButton("채우기")
        fill_button.clicked.connect(lambda checked, idx=index: self._fill_fixed_text_frame(idx))
        center_button = QPushButton("가운데 정렬")
        center_button.clicked.connect(lambda checked, idx=index: self._center_fixed_text_frame(idx))
        button_layout.addWidget(fill_button)
        button_layout.addWidget(center_button)
        preview_layout.addLayout(button_layout)
        
        # 컨테이너에 추가
        self.fixed_text_preview_layout.addWidget(preview_group)
        self.fixed_text_preview_labels.append(preview_label)
        
        # 초기 미리보기 업데이트
        self._update_single_fixed_text_preview(index, fields)

    def _update_single_fixed_text_preview(self, index, fields):
        """개별 고정 텍스트 미리보기 업데이트"""
        if index >= len(self.fixed_text_preview_labels):
            return
            
        preview_label = self.fixed_text_preview_labels[index]
        
        # 카드 크기 (전역 설정 기준)
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636
        
        card_pixmap = QPixmap(card_width, card_height)
        card_pixmap.fill(Qt.white)
        
        try:
            width = fields["width"].value()
            height = fields["height"].value()
            x = fields["x"].value()
            y = fields["y"].value()
            text_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            text_rect = QRect()
            
        # 사각형 그리기
        colors = [QColor("cyan"), QColor("magenta"), QColor("yellow"), QColor("brown"), QColor("gray")]
        color = colors[index % len(colors)]
        pen = QPen(color, 2, Qt.SolidLine)
        
        preview_label.set_pen(pen)
        preview_label.update_preview(card_pixmap, text_rect)

    def update_text_input_items(self, count):
        """텍스트 입력 항목 UI 업데이트"""
        # 기존 위젯 제거
        for i in reversed(range(self.text_input_items_layout.count())):
            item = self.text_input_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # 텍스트 입력 항목 필드 초기화
        self.text_input_item_fields = []
        
        # 새 항목 추가
        for i in range(count):
            # 기본값 설정
            item_data = {
                "label": "",
                "placeholder": "",
                "width": 800,
                "height": 80,
                "x": 100,
                "y": 100 + i * 100,
                "font_size": 36
            }
            
            # 기존 데이터가 있으면 사용
            if i < len(self.config["text_input"]["items"]):
                item_data = self.config["text_input"]["items"][i]
            
            # 항목 그룹 생성
            item_group = QGroupBox(f"텍스트 입력 {i+1}")
            item_layout = QFormLayout(item_group)
            
            # 항목 필드 생성
            item_fields = {}
            
            # 레이블
            label_edit = QLineEdit(item_data.get("label", ""))
            item_layout.addRow("항목 이름:", label_edit)
            item_fields["label"] = label_edit
            
            # 플레이스홀더
            placeholder_edit = QLineEdit(item_data.get("placeholder", ""))
            item_layout.addRow("입력 예시:", placeholder_edit)
            item_fields["placeholder"] = placeholder_edit
            
            # 위치 및 크기
            for key in ["width", "height", "x", "y"]:
                # QSpinBox 대신 NumberLineEdit 사용
                line_edit = NumberLineEdit()
                line_edit.setValue(item_data.get(key, 0))
                line_edit.textChanged.connect(lambda text, idx=i: self._update_single_text_input_preview(idx, self.text_input_item_fields[idx]) if idx < len(self.text_input_item_fields) else None)
                label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
                item_layout.addRow(f"{label_text}:", line_edit)
                item_fields[key] = line_edit
            
            # 폰트 크기
            font_size_spin = NumberLineEdit()
            font_size_spin.setValue(item_data.get("font_size", 36))
            item_layout.addRow("폰트 크기:", font_size_spin)
            item_fields["font_size"] = font_size_spin
            
            # 출력용 폰트 설정 - 폰트 선택 레이아웃
            output_font_layout = QHBoxLayout()
            output_font_edit = QLineEdit(item_data.get("output_font", ""))
            output_font_layout.addWidget(output_font_edit, 1)
            item_fields["output_font"] = output_font_edit
            
            # 폰트 파일 선택 버튼 추가
            browse_button = QPushButton("찾기...")
            browse_button.clicked.connect(lambda checked, edit=output_font_edit: FileHandler.browse_font_file(self, edit))
            output_font_layout.addWidget(browse_button)
            
            item_layout.addRow("출력용 폰트:", output_font_layout)
            
            # 출력용 폰트 크기
            output_font_size_spin = NumberLineEdit()
            output_font_size_spin.setValue(item_data.get("output_font_size", 16))
            item_layout.addRow("출력용 폰트 크기:", output_font_size_spin)
            item_fields["output_font_size"] = output_font_size_spin
            
            # 출력용 폰트 색상
            output_font_color_button = ColorPickerButton(item_data.get("output_font_color", "#000000"))
            item_layout.addRow("출력용 폰트 색상:", output_font_color_button)
            item_fields["output_font_color"] = output_font_color_button
            
            self.text_input_items_layout.addWidget(item_group)
            self.text_input_item_fields.append(item_fields)
        
        # UI 업데이트
        self.text_input_items_container.updateGeometry()
        
        # 미리보기 업데이트
        self._update_text_input_previews()
    
    def update_text_items(self, count):
        """텍스트 항목 UI 업데이트"""
        # 기존 위젯 제거
        for i in reversed(range(self.text_items_layout.count())):
            item = self.text_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # 텍스트 항목 필드 초기화
        self.text_item_fields = []
        
        # 새 항목 추가
        for i in range(count):
            # 기본값 설정
            item_data = {
                "content": "텍스트",
                "x": 0,
                "y": 0,
                "width": 300,
                "height": 100,
                "font": "LAB디지털.ttf",
                "font_size": 16,
                "font_color": "#000000"
            }
            
            # 기존 데이터가 있으면 사용
            if i < len(self.config["texts"]["items"]):
                item_data = self.config["texts"]["items"][i]
            
            # 항목 그룹 생성
            item_group = QGroupBox(f"텍스트 {i+1}")
            item_layout = QFormLayout(item_group)
            
            # 항목 필드 생성
            item_fields = {}
            
            # 내용
            content_edit = QLineEdit(item_data["content"])
            item_layout.addRow("문구:", content_edit)
            item_fields["content"] = content_edit
            
            # 위치 및 크기
            for key in ["width", "height", "x", "y"]:
                # QSpinBox 대신 NumberLineEdit 사용
                line_edit = NumberLineEdit()
                line_edit.setValue(item_data[key])
                line_edit.textChanged.connect(lambda text, idx=i: self._update_single_fixed_text_preview(idx, self.text_item_fields[idx]) if idx < len(self.text_item_fields) else None)
                label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
                item_layout.addRow(f"{label_text}:", line_edit)
                item_fields[key] = line_edit
            
            # 폰트 선택 레이아웃
            font_layout = QHBoxLayout()
            font_edit = QLineEdit(item_data["font"])
            font_layout.addWidget(font_edit, 1)  # 1은 stretch factor로, 남은 공간을 차지하도록 함
            item_fields["font"] = font_edit
            
            # 폰트 파일 선택 버튼
            browse_button = QPushButton("찾기...")
            browse_button.clicked.connect(lambda checked, edit=font_edit: FileHandler.browse_font_file(self, edit))
            font_layout.addWidget(browse_button)
            
            item_layout.addRow("폰트:", font_layout)
            
            # 폰트 크기
            font_size_spin = NumberLineEdit()
            font_size_spin.setValue(item_data["font_size"])
            item_layout.addRow("폰트 크기:", font_size_spin)
            item_fields["font_size"] = font_size_spin
            
            # 폰트 색상
            font_color_button = ColorPickerButton(item_data["font_color"])
            item_layout.addRow("폰트 색상:", font_color_button)
            item_fields["font_color"] = font_color_button
            
            self.text_items_layout.addWidget(item_group)
            self.text_item_fields.append(item_fields)
        
        # UI 업데이트
        self.text_items_container.updateGeometry()
        
        # 미리보기 업데이트
        self._update_fixed_text_previews()

        # 미리보기 업데이트
        self._update_keyboard_preview()
        self._update_text_input_previews()
        self._update_fixed_text_previews()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        
        # 배경화면 업데이트
        self.keyboard_bg_edit.setText(config["text_input"].get("background", ""))
        
        # 키보드 위치 및 크기 업데이트
        for key, widget in self.keyboard_position_fields.items():
            widget.setValue(config["keyboard"][key])
        
        # 텍스트 입력 설정 업데이트
        for key, widget in self.text_input_fields.items():
            if key != "count":  # count는 spinbox에서 별도로 처리
                widget.setValue(config["text_input"][key])
        
        # 텍스트 입력 개수 업데이트 - 최소값 1 보장
        count_value = max(1, config["text_input"]["count"])
        if self.text_input_count_spinbox.value() != count_value:
            self.text_input_count_spinbox.setValue(count_value)
        else:
            self.update_text_input_items(count_value)  # 여기도 count_value 사용
        
        # 텍스트 개수 업데이트
        if self.text_count_spinbox.value() != config["texts"]["count"]:
            self.text_count_spinbox.setValue(config["texts"]["count"])
        else:
            self.update_text_items(config["texts"]["count"])
        
        # 키보드 스타일 업데이트
        for key, widget in self.keyboard_style_fields.items():
            if isinstance(widget, ColorPickerButton):
                widget.update_color(config["keyboard"][key])
            else:
                widget.setValue(config["keyboard"][key])

        # 미리보기 업데이트
        self._update_keyboard_preview()
        self._update_text_input_previews()
    
    def update_config(self, config):
        """UI 값을 config에 반영"""
        # 배경화면 저장
        config["text_input"]["background"] = self.keyboard_bg_edit.text()
        
        # 키보드 위치 및 크기 저장
        for key, widget in self.keyboard_position_fields.items():
            config["keyboard"][key] = widget.value()
        
        # 키보드 스타일 저장
        for key, widget in self.keyboard_style_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["keyboard"][key] = widget.color
            else:
                config["keyboard"][key] = widget.value()
        
        # 텍스트 입력 설정 저장
        for key, widget in self.text_input_fields.items():
            config["text_input"][key] = widget.value()
        
        # 텍스트 입력 개수 설정 저장
        config["text_input"]["count"] = self.text_input_count_spinbox.value()
        config["text_input"]["items"] = []
        
        for i, fields in enumerate(self.text_input_item_fields):
            item = {
                "label": fields["label"].text(),
                "placeholder": fields["placeholder"].text(),
                "x": fields["x"].value(),
                "y": fields["y"].value(),
                "width": fields["width"].value(),
                "height": fields["height"].value(),
                "font_size": fields["font_size"].value(),
                "output_font": fields["output_font"].text(),
                "output_font_size": fields["output_font_size"].value(),
                "output_font_color": fields["output_font_color"].color
            }
            config["text_input"]["items"].append(item)
        
        # 텍스트 설정 저장
        config["texts"]["count"] = self.text_count_spinbox.value()
        config["texts"]["items"] = []
        
        for i, fields in enumerate(self.text_item_fields):
            item = {
                "content": fields["content"].text(),
                "x": fields["x"].value(),
                "y": fields["y"].value(),
                "width": fields["width"].value(),
                "height": fields["height"].value(),
                "font": fields["font"].text(),
                "font_size": fields["font_size"].value(),
                "font_color": fields["font_color"].color
            }
            config["texts"]["items"].append(item)