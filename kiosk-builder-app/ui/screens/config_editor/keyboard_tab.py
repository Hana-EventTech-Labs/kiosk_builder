from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QPushButton, QSpinBox, QWidget)
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from utils.file_handler import FileHandler
from .base_tab import BaseTab

class KeyboardTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.init_ui()
        
    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()
        
        # 배경화면 설정
        bg_group = QGroupBox("배경화면 설정")
        bg_layout = QHBoxLayout(bg_group)
        
        # 원본 파일명 표시
        self.keyboard_bg_edit = QLineEdit(self.config["text_input"].get("background", ""))
        bg_layout.addWidget(self.keyboard_bg_edit, 1)
        
        # 배경화면 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_background_file(self, self.keyboard_bg_edit, "2"))
        bg_layout.addWidget(browse_button)
        
        content_layout.addWidget(bg_group)
        
        # 키보드 위치 및 크기
        position_group = QGroupBox("키보드 위치 및 크기")
        position_layout = QFormLayout(position_group)
        
        self.keyboard_position_fields = {}
        
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["keyboard"][key])
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            position_layout.addRow(f"{label_text}:", line_edit)
            self.keyboard_position_fields[key] = line_edit
        
        content_layout.addWidget(position_group)
        
        # 텍스트 입력 설정
        text_input_group = QGroupBox("사용자 입력 필드 설정")
        text_input_layout = QVBoxLayout(text_input_group)
        
        # 텍스트 입력 기본 설정
        basic_settings_layout = QFormLayout()
        self.text_input_fields = {}
        
        # 공통 설정 필드 (각 항목별 설정이 아닌 전체 설정)
        settings_map = {
            "margin_top": "상단 여백",
            "margin_left": "왼쪽 여백",
            "margin_right": "오른쪽 여백",
            "spacing": "간격"
        }
        
        for key in ["margin_top", "margin_left", "margin_right", "spacing"]:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["text_input"][key])
            basic_settings_layout.addRow(f"{settings_map[key]}:", line_edit)
            self.text_input_fields[key] = line_edit
            
        text_input_layout.addLayout(basic_settings_layout)
        
        # 텍스트 입력 개수 설정
        text_input_count_layout = QHBoxLayout()
        text_input_count_label = QLabel("사용자 입력 필드 개수:")
        self.text_input_count_spinbox = QSpinBox()
        self.text_input_count_spinbox.setRange(0, 10)
        self.text_input_count_spinbox.setValue(self.config["text_input"]["count"])
        self.text_input_count_spinbox.valueChanged.connect(self.update_text_input_items)
        text_input_count_layout.addWidget(text_input_count_label)
        text_input_count_layout.addWidget(self.text_input_count_spinbox)
        text_input_count_layout.addStretch()
        
        text_input_layout.addLayout(text_input_count_layout)
        
        # 텍스트 입력 항목 컨테이너
        self.text_input_items_container = QWidget()
        self.text_input_items_layout = QVBoxLayout(self.text_input_items_container)
        self.text_input_items_layout.setContentsMargins(0, 0, 0, 0)
        
        # 텍스트 입력 항목 필드 초기화
        self.text_input_item_fields = []
        self.update_text_input_items(self.config["text_input"]["count"])
        
        text_input_layout.addWidget(self.text_input_items_container)
        content_layout.addWidget(text_input_group)
        
        # 텍스트 설정
        texts_group = QGroupBox("고정 텍스트 설정")
        texts_layout = QVBoxLayout(texts_group)
        
        # 텍스트 개수 설정
        text_count_layout = QHBoxLayout()
        text_count_label = QLabel("고정 텍스트 개수:")
        self.text_count_spinbox = QSpinBox()
        self.text_count_spinbox.setRange(0, 10)
        self.text_count_spinbox.setValue(self.config["texts"]["count"])
        self.text_count_spinbox.valueChanged.connect(self.update_text_items)
        text_count_layout.addWidget(text_count_label)
        text_count_layout.addWidget(self.text_count_spinbox)
        text_count_layout.addStretch()
        
        texts_layout.addLayout(text_count_layout)
        
        # 텍스트 항목 컨테이너
        self.text_items_container = QWidget()
        self.text_items_layout = QVBoxLayout(self.text_items_container)
        self.text_items_layout.setContentsMargins(0, 0, 0, 0)
        
        # 텍스트 항목 필드 초기화
        self.text_item_fields = []
        self.update_text_items(self.config["texts"]["count"])
        
        texts_layout.addWidget(self.text_items_container)
        content_layout.addWidget(texts_group)
        
        # 키보드 스타일
        style_group = QGroupBox("키보드 스타일")
        style_layout = QFormLayout(style_group)
        
        self.keyboard_style_fields = {}
        
        # 색상 필드
        color_keys = ["bg_color", "border_color", "button_bg_color", "button_text_color", 
                    "button_pressed_color", "hangul_btn_color", "shift_btn_color", 
                    "backspace_btn_color", "next_btn_color"]
        
        # 색상 필드 이름 매핑
        color_labels = {
            "bg_color": "배경 색상",
            "border_color": "테두리 색상",
            "button_bg_color": "버튼 배경 색상",
            "button_text_color": "버튼 텍스트 색상",
            "button_pressed_color": "버튼 누름 색상",
            "hangul_btn_color": "한글 버튼 색상",
            "shift_btn_color": "시프트 버튼 색상",
            "backspace_btn_color": "지우기 버튼 색상",
            "next_btn_color": "다음 버튼 색상"
        }
                    
        for key in color_keys:
            color_button = ColorPickerButton(self.config["keyboard"][key])
            style_layout.addRow(f"{color_labels[key]}:", color_button)
            self.keyboard_style_fields[key] = color_button
        
        # 숫자 필드
        number_keys = ["border_width", "border_radius", "padding", "font_size", 
                    "button_radius", "special_btn_width", "max_hangul", 
                    "max_lowercase", "max_uppercase"]
        
        # 숫자 필드 이름 매핑
        number_labels = {
            "border_width": "테두리 두께",
            "border_radius": "테두리 둥글기",
            "padding": "내부 여백",
            "font_size": "폰트 크기",
            "button_radius": "버튼 둥글기",
            "special_btn_width": "특수 버튼 너비",
            "max_hangul": "최대 한글 자수",
            "max_lowercase": "최대 소문자 자수",
            "max_uppercase": "최대 대문자 자수"
        }
                    
        for key in number_keys:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["keyboard"][key])
            style_layout.addRow(f"{number_labels[key]}:", line_edit)
            self.keyboard_style_fields[key] = line_edit
        
        content_layout.addWidget(style_group)
        
        # 스트레치 추가
        content_layout.addStretch()
    
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
                "label": f"입력 {i+1}",
                "placeholder": "입력하세요",
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
            
            # 텍스트 입력 개수 업데이트
            if self.text_input_count_spinbox.value() != config["text_input"]["count"]:
                self.text_input_count_spinbox.setValue(config["text_input"]["count"])
            else:
                self.update_text_input_items(config["text_input"]["count"])
            
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