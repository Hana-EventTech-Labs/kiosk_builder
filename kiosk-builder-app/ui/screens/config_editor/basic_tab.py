#BaseTab을 상속받은 구체적인 탭 클래스

from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QRadioButton, QCheckBox, QGridLayout)
from PySide6.QtCore import Qt  # Qt 모듈 추가
from ui.components.inputs import NumberLineEdit, ModernLineEdit  # ModernLineEdit 추가
from utils.file_handler import FileHandler
from .base_tab import BaseTab

class BasicTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.screen_order_checkboxes = []
        self.init_ui()
        
    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()
        
        # 앱 이름 그룹박스 추가
        app_name_group = QGroupBox("앱 이름")
        self.apply_left_aligned_group_style(app_name_group)
        app_name_layout = QFormLayout(app_name_group)

        # 정렬 설정
        app_name_layout.setLabelAlignment(Qt.AlignVCenter | Qt.AlignRight)
        app_name_layout.setFormAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # 앱 이름 입력 필드 - ModernLineEdit 사용
        from ui.components.inputs import ModernLineEdit
        self.app_name_edit = ModernLineEdit(placeholder="앱 이름을 입력하세요")

        # 높이 설정으로 정렬 조정
        self.app_name_edit.setFixedHeight(35)  # 다른 입력 필드와 동일한 높이로 조정

        self.app_name_edit.setText(self.config["app_name"])
        app_name_layout.addRow(self.app_name_edit)

        # 그룹박스를 레이아웃에 추가
        content_layout.addWidget(app_name_group)
        
        # 화면 순서
        screen_order_group = QGroupBox("화면 순서 선택")
        self.apply_left_aligned_group_style(screen_order_group)
        screen_order_layout = QGridLayout(screen_order_group)

        self.screen_options = [
            (0, "스플래쉬"), (1, "촬영"), (2, "키보드"), 
            (3, "QR코드"), (4, "프레임"), (5, "발급중"), 
            (6, "발급완료")
        ]

        for i, (index, name) in enumerate(self.screen_options):
            checkbox = QCheckBox(name)
            checkbox.setProperty("screen_index", index)
            checkbox.setChecked(index in self.config["screen_order"])
            checkbox.stateChanged.connect(self.on_screen_order_changed)
            
            row, col = divmod(i, 4)  # 4열로 배치
            screen_order_layout.addWidget(checkbox, row, col)
            self.screen_order_checkboxes.append(checkbox)

        content_layout.addWidget(screen_order_group)

        
        # 모니터 크기
        screen_group = QGroupBox("모니터 크기")
        self.apply_left_aligned_group_style(screen_group)

        screen_layout = QHBoxLayout(screen_group)
        
        screen_layout.addWidget(QLabel("너비:"))
        self.screen_width_edit = NumberLineEdit()
        self.screen_width_edit.setValue(self.config["screen_size"]["width"])
        screen_layout.addWidget(self.screen_width_edit)
        
        screen_layout.addWidget(QLabel("높이:"))
        self.screen_height_edit = NumberLineEdit()
        self.screen_height_edit.setValue(self.config["screen_size"]["height"])
        screen_layout.addWidget(self.screen_height_edit)
        
        screen_layout.addStretch(1)
        
        content_layout.addWidget(screen_group)
        
        # 카메라 해상도
        camera_group = QGroupBox("카메라 해상도")
        self.apply_left_aligned_group_style(camera_group)
        camera_layout = QFormLayout(camera_group)
        
        # 카메라 해상도 콤보박스 생성
        self.camera_resolution_combo = QComboBox()
        self.camera_resolution_combo.addItem("2560 X 1440", (2560, 1440))
        self.camera_resolution_combo.addItem("1920 X 1080", (1920, 1080))
        self.camera_resolution_combo.addItem("1080 X 720", (1080, 720))
        
        # 현재 해상도 선택
        current_width = self.config["camera_size"]["width"]
        current_height = self.config["camera_size"]["height"]
        current_resolution = (current_width, current_height)
        
        # 콤보박스에서 현재 해상도와 일치하는 항목을 찾아 선택
        found = False
        for i in range(self.camera_resolution_combo.count()):
            if self.camera_resolution_combo.itemData(i) == current_resolution:
                self.camera_resolution_combo.setCurrentIndex(i)
                found = True
                break
        
        # 일치하는 항목이 없으면 사용자 정의 항목 추가
        if not found:
            user_resolution = f"{current_width} X {current_height}"
            self.camera_resolution_combo.addItem(user_resolution, current_resolution)
            self.camera_resolution_combo.setCurrentIndex(self.camera_resolution_combo.count() - 1)
        
        # 해상도 변경 시 이벤트 연결
        self.camera_resolution_combo.currentIndexChanged.connect(self.on_camera_resolution_changed)
        
        camera_layout.addRow("해상도:", self.camera_resolution_combo)
        
        content_layout.addWidget(camera_group)
        
        # 실제 인쇄 영역
        crop_group = QGroupBox("실제 인쇄 영역(예시: 945, 1080, 487, 0)")
        self.apply_left_aligned_group_style(crop_group)
        crop_layout = QFormLayout(crop_group)
        
        self.crop_fields = {}
        
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["crop_area"][key])
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            crop_layout.addRow(f"{label_text}:", line_edit)
            self.crop_fields[key] = line_edit
        
        content_layout.addWidget(crop_group)
        
        # 프린터 설정 추가
        self.init_printer_settings(content_layout)
        
        # 이미지 설정 추가
        self.init_image_settings(content_layout)
        
        # 스트레치 추가
        content_layout.addStretch()
        
    def init_printer_settings(self, parent_layout):
        """프린터 설정 초기화"""
        # 프린터 설정 그룹
        printer_group = QGroupBox("프린터 설정")
        self.apply_left_aligned_group_style(printer_group)
        printer_layout = QFormLayout(printer_group)
        
        # 프린터 모드 설정 (라디오 버튼)
        mode_layout = QHBoxLayout()
        
        self.preview_mode_radio = QRadioButton("미리보기 모드")
        self.print_mode_radio = QRadioButton("인쇄 모드")
        
        # 현재 설정값에 따라 라디오 버튼 선택
        current_print_mode = self.config.get("printer", {}).get("print_mode", False)
        if current_print_mode:
            self.print_mode_radio.setChecked(True)
        else:
            self.preview_mode_radio.setChecked(True)
        
        mode_layout.addWidget(self.preview_mode_radio)
        mode_layout.addWidget(self.print_mode_radio)
        mode_layout.addStretch()
        
        printer_layout.addRow("모드 선택:", mode_layout)
        
        # 패널 ID 설정 (콤보박스)
        self.panel_combo = QComboBox()
        self.panel_combo.addItem("YMC (컬러)", 1)
        self.panel_combo.addItem("Resin (블랙/실버)", 2)
        self.panel_combo.addItem("Overlay (보호막)", 4)
        self.panel_combo.addItem("UV (형광)", 8)
        
        # 현재 패널 ID 선택
        current_panel_id = self.config.get("printer", {}).get("panel_id", 1)
        for i in range(self.panel_combo.count()):
            if self.panel_combo.itemData(i) == current_panel_id:
                self.panel_combo.setCurrentIndex(i)
                break
        
        printer_layout.addRow("패널 타입:", self.panel_combo)
        
        parent_layout.addWidget(printer_group)
        
    def init_image_settings(self, parent_layout):
        """이미지 설정 초기화"""
        # 이미지 설정 그룹
        images_group = QGroupBox("고정 이미지 설정")
        self.apply_left_aligned_group_style(images_group)
        images_layout = QVBoxLayout(images_group)
        
        # 이미지 개수 설정
        image_count_layout = QHBoxLayout()
        # image_count_label = QLabel("이미지 개수:")
        self.image_count_spinbox = QSpinBox()
        self.image_count_spinbox.setRange(0, 10)
        self.image_count_spinbox.setValue(self.config["images"]["count"])
        self.image_count_spinbox.valueChanged.connect(self.update_image_items)
        # image_count_layout.addWidget(image_count_label)
        image_count_layout.addWidget(self.image_count_spinbox)
        image_count_layout.addStretch()
        
        images_layout.addLayout(image_count_layout)
        
        # 이미지 항목 컨테이너
        self.image_items_container = QWidget()
        self.image_items_layout = QVBoxLayout(self.image_items_container)
        self.image_items_layout.setContentsMargins(0, 0, 0, 0)
        
        # 이미지 항목 필드 초기화
        self.image_item_fields = []
        self.update_image_items(self.config["images"]["count"])
        
        images_layout.addWidget(self.image_items_container)
        parent_layout.addWidget(images_group)
        
    def update_image_items(self, count):
        """이미지 항목 UI 업데이트"""
        # 이전 이미지 개수 확인
        prev_count = len(self.image_item_fields)
        
        # 기존 이미지 데이터 저장
        prev_image_data = []
        for i, fields in enumerate(self.image_item_fields):
            prev_data = {
                "filename": fields["filename"].text(),
                "x": fields["x"].value(),
                "y": fields["y"].value(),
                "width": fields["width"].value(),
                "height": fields["height"].value()
            }
            prev_image_data.append(prev_data)
        
        # 기존 위젯 제거
        for i in reversed(range(self.image_items_layout.count())):
            item = self.image_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # 이미지 항목 필드 초기화
        self.image_item_fields = []
        
        # 새 항목 추가
        for i in range(count):
            # 기본값 설정
            item_data = {
                "filename": "file_name.jpg",
                "x": 0,
                "y": 0,
                "width": 300,
                "height": 300
            }
            
            # 기존 이미지 데이터 유지
            if i < prev_count:
                item_data = prev_image_data[i]
            # 저장된 config에서 데이터 가져오기
            elif i < len(self.config["images"]["items"]):
                item_data = self.config["images"]["items"][i]
            
            # 항목 그룹 생성
            item_group = QGroupBox(f"이미지 {i+1}")
            item_layout = QFormLayout(item_group)
            
            # 항목 필드 생성
            item_fields = {}
            
            # 파일명 입력란과 파일 선택 버튼을 담을 레이아웃
            filename_layout = QHBoxLayout()
            
            # 파일명 입력란
            filename_edit = QLineEdit(item_data["filename"])
            filename_layout.addWidget(filename_edit, 1)  # 1은 stretch factor로, 남은 공간을 차지하도록 함
            item_fields["filename"] = filename_edit
            
            # 파일 선택 버튼
            browse_button = QPushButton("찾기...")
            browse_button.clicked.connect(lambda checked, edit=filename_edit: FileHandler.browse_image_file(self, edit))
            filename_layout.addWidget(browse_button)
            
            item_layout.addRow("파일명:", filename_layout)
            
            # 위치 및 크기
            for key in ["width", "height", "x", "y"]:
                # QSpinBox 대신 NumberLineEdit 사용
                line_edit = NumberLineEdit()
                line_edit.setValue(item_data.get(key, 0))
                label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
                item_layout.addRow(f"{label_text}:", line_edit)
                item_fields[key] = line_edit
            
            self.image_items_layout.addWidget(item_group)
            self.image_item_fields.append(item_fields)
        
        # UI 업데이트
        self.image_items_container.updateGeometry()
    
    def on_screen_order_changed(self):
        """화면 순서가 변경되었을 때 호출되는 메소드"""
        try:
            # 체크된 체크박스의 screen_index를 가져와서 정렬
            screen_order = sorted([
                cb.property("screen_index") 
                for cb in self.screen_order_checkboxes 
                if cb.isChecked()
            ])
            
            self.config["screen_order"] = screen_order
            
            # 메인 윈도우의 탭 활성화 상태 업데이트
            main_window = self.window()
            if hasattr(main_window, 'update_tab_enabled_states'):
                main_window.update_tab_enabled_states()

        except Exception as e:
            print(f"화면 순서 변경 중 오류 발생: {e}")
    
    def on_camera_resolution_changed(self, index):
        """카메라 해상도 선택이 변경되었을 때 호출되는 메소드"""
        selected_resolution = self.camera_resolution_combo.itemData(index)
        
        if selected_resolution:
            width, height = selected_resolution
            self.config["camera_size"]["width"] = width
            self.config["camera_size"]["height"] = height
    
    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        self.app_name_edit.setText(config["app_name"])
        self.screen_width_edit.setValue(config["screen_size"]["width"])
        self.screen_height_edit.setValue(config["screen_size"]["height"])
        
        # 화면 순서 업데이트
        for checkbox in self.screen_order_checkboxes:
            index = checkbox.property("screen_index")
            # 업데이트 중 시그널 발생 방지
            checkbox.stateChanged.disconnect(self.on_screen_order_changed)
            checkbox.setChecked(index in config["screen_order"])
            checkbox.stateChanged.connect(self.on_screen_order_changed)
        
        # 카메라 해상도 업데이트
        current_width = config["camera_size"]["width"]
        current_height = config["camera_size"]["height"]
        current_resolution = (current_width, current_height)
        
        # 일치하는 항목 찾기
        found = False
        for i in range(self.camera_resolution_combo.count()):
            if self.camera_resolution_combo.itemData(i) == current_resolution:
                self.camera_resolution_combo.setCurrentIndex(i)
                found = True
                break
        
        # 일치하는 항목이 없으면 새 항목 추가
        if not found:
            user_resolution = f"{current_width} X {current_height}"
            # 이미 사용자 정의 항목이 있는지 확인
            for i in range(self.camera_resolution_combo.count()):
                if self.camera_resolution_combo.itemText(i) == user_resolution:
                    self.camera_resolution_combo.setItemData(i, current_resolution)
                    self.camera_resolution_combo.setCurrentIndex(i)
                    found = True
                    break
            
            # 사용자 정의 항목이 없으면 새로 추가
            if not found:
                self.camera_resolution_combo.addItem(user_resolution, current_resolution)
                self.camera_resolution_combo.setCurrentIndex(self.camera_resolution_combo.count() - 1)
        
        # 크롭 영역 업데이트
        for key, widget in self.crop_fields.items():
            widget.setValue(config["crop_area"][key])
        
        # 프린터 설정 업데이트
        current_print_mode = config.get("printer", {}).get("print_mode", False)
        if current_print_mode:
            self.print_mode_radio.setChecked(True)
        else:
            self.preview_mode_radio.setChecked(True)
        
        # 패널 ID 업데이트
        current_panel_id = config.get("printer", {}).get("panel_id", 1)
        for i in range(self.panel_combo.count()):
            if self.panel_combo.itemData(i) == current_panel_id:
                self.panel_combo.setCurrentIndex(i)
                break
        
        # 이미지 개수 업데이트
        if self.image_count_spinbox.value() != config["images"]["count"]:
            self.image_count_spinbox.setValue(config["images"]["count"])
        else:
            # 이미지 항목 업데이트
            self.update_image_items(config["images"]["count"])
            
            # 각 항목의 데이터도 업데이트
            for i, fields in enumerate(self.image_item_fields):
                if i < len(config["images"]["items"]):
                    item = config["images"]["items"][i]
                    fields["filename"].setText(item["filename"])
                    fields["x"].setValue(item["x"])
                    fields["y"].setValue(item["y"])
                    fields["width"].setValue(item["width"])
                    fields["height"].setValue(item["height"])
                    
    def update_config(self, config):
        """UI 값을 config에 반영"""
        config["app_name"] = self.app_name_edit.text()
        config["screen_size"]["width"] = self.screen_width_edit.value()
        config["screen_size"]["height"] = self.screen_height_edit.value()
        
        # 크롭 영역 설정 저장
        for key, widget in self.crop_fields.items():
            config["crop_area"][key] = widget.value()
        
        # 화면 순서 업데이트
        config["screen_order"] = sorted([
            cb.property("screen_index") 
            for cb in self.screen_order_checkboxes 
            if cb.isChecked()
        ])
        
        # 카메라 해상도 업데이트
        selected_resolution = self.camera_resolution_combo.currentData()
        if selected_resolution:
            config["camera_size"]["width"] = selected_resolution[0]
            config["camera_size"]["height"] = selected_resolution[1]
        
        # 프린터 설정이 없으면 기본값으로 초기화
        if "printer" not in config:
            config["printer"] = {"print_mode": False, "panel_id": 1}
        
        # 프린터 모드 업데이트
        config["printer"]["print_mode"] = self.print_mode_radio.isChecked()
        
        # 패널 ID 업데이트
        selected_panel_id = self.panel_combo.currentData()
        if selected_panel_id:
            config["printer"]["panel_id"] = selected_panel_id
        
        # 이미지 설정 저장
        config["images"]["count"] = self.image_count_spinbox.value()
        config["images"]["items"] = []
        
        for i, fields in enumerate(self.image_item_fields):
            item = {
                "filename": fields["filename"].text(),
                "x": fields["x"].value(),
                "y": fields["y"].value(),
                "width": fields["width"].value(),
                "height": fields["height"].value()
            }
            config["images"]["items"].append(item)