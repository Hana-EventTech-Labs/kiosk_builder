from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox)
from ui.components.inputs import NumberLineEdit
from utils.file_handler import FileHandler
from .base_tab import BaseTab

class BasicTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.init_ui()
        
    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        content_layout.addLayout(form_layout)
        
        # 앱 이름
        self.app_name_edit = QLineEdit(self.config["app_name"])
        form_layout.addRow("앱 이름:", self.app_name_edit)
        
        # 화면 순서
        screen_order_group = QGroupBox("화면 순서")
        screen_order_layout = QVBoxLayout(screen_order_group)
        
        screen_order_label = QLabel("화면 순서 (쉼표로 구분):")
        screen_order_layout.addWidget(screen_order_label)
        
        self.screen_order_edit = QLineEdit(",".join(map(str, self.config["screen_order"])))
        self.screen_order_edit.textChanged.connect(self.on_screen_order_changed)
        screen_order_layout.addWidget(self.screen_order_edit)
        
        screen_order_info = QLabel("0: 스플래쉬, 1: 촬영, 2: 키보드, 3: QR코드, 4: 발급중, 5: 발급완료")
        screen_order_info.setStyleSheet("color: gray;")
        screen_order_layout.addWidget(screen_order_info)
        
        content_layout.addWidget(screen_order_group)
        
        # 모니터 크기
        screen_group = QGroupBox("모니터 크기")
        screen_layout = QFormLayout(screen_group)
        
        self.screen_width_edit = NumberLineEdit()
        self.screen_width_edit.setValue(self.config["screen_size"]["width"])
        screen_layout.addRow("너비:", self.screen_width_edit)
        
        self.screen_height_edit = NumberLineEdit()
        self.screen_height_edit.setValue(self.config["screen_size"]["height"])
        screen_layout.addRow("높이:", self.screen_height_edit)
        
        content_layout.addWidget(screen_group)
        
        # 카메라 해상도
        camera_group = QGroupBox("카메라 해상도")
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
        
        # 이미지 설정 추가
        self.init_image_settings(content_layout)
        
        # 스트레치 추가
        content_layout.addStretch()
        
    def init_image_settings(self, parent_layout):
        """이미지 설정 초기화"""
        # 이미지 설정 그룹
        images_group = QGroupBox("이미지 설정")
        images_layout = QVBoxLayout(images_group)
        
        # 이미지 개수 설정
        image_count_layout = QHBoxLayout()
        image_count_label = QLabel("이미지 개수:")
        self.image_count_spinbox = QSpinBox()
        self.image_count_spinbox.setRange(0, 10)
        self.image_count_spinbox.setValue(self.config["images"]["count"])
        self.image_count_spinbox.valueChanged.connect(self.update_image_items)
        image_count_layout.addWidget(image_count_label)
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
        # 메인 윈도우에서 처리할 것이므로 여기서는 구현하지 않음
        pass
    
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
            screen_order_text = ",".join(map(str, config["screen_order"]))
            if self.screen_order_edit.text() != screen_order_text:
                self.screen_order_edit.setText(screen_order_text)
            
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
        try:
            screen_order = [int(x.strip()) for x in self.screen_order_edit.text().split(",")]
            config["screen_order"] = screen_order
        except ValueError:
            pass  # 화면 순서에 숫자가 아닌 값이 있으면 무시
        
        # 카메라 해상도 업데이트
        selected_resolution = self.camera_resolution_combo.currentData()
        if selected_resolution:
            config["camera_size"]["width"] = selected_resolution[0]
            config["camera_size"]["height"] = selected_resolution[1]
        
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