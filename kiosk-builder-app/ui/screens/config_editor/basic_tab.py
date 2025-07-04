#BaseTab을 상속받은 구체적인 탭 클래스
import os
import shutil
from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QRadioButton, QCheckBox, QGridLayout, QFileDialog, QFrame, QMessageBox)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect, Signal
from ui.components.inputs import NumberLineEdit, ModernLineEdit  # ModernLineEdit 추가
from utils.file_handler import FileHandler
from .base_tab import BaseTab
from ui.components.preview_label import DraggablePreviewLabel
from utils.printer_thread import PrinterThread

class BasicTab(BaseTab):
    config_changed = Signal()

    def __init__(self, config):
        super().__init__(config)
        self.screen_order_checkboxes = []
        self.crop_preview_label = None
        self.card_portrait_radio = None
        self.card_landscape_radio = None
        self.print_count_edit = None
        self.print_button = None
        self.printer_thread = None
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
        
        # 실제 인쇄 영역 컨테이너
        crop_section_container = QWidget()
        crop_section_layout = QHBoxLayout(crop_section_container)
        
        # 실제 인쇄 영역
        crop_group = QGroupBox("실제 인쇄 영역(예시: 945, 1080, 487, 0)")
        self.apply_left_aligned_group_style(crop_group)
        crop_layout = QFormLayout(crop_group)
        
        self.crop_fields = {}
        
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["crop_area"][key])
            line_edit.textChanged.connect(self._update_crop_preview)
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            crop_layout.addRow(f"{label_text}:", line_edit)
            self.crop_fields[key] = line_edit
        
        crop_section_layout.addWidget(crop_group, 1)

        # 미리보기 그룹
        crop_preview_group = QGroupBox("미리보기")
        self.apply_left_aligned_group_style(crop_preview_group)
        crop_preview_layout = QVBoxLayout(crop_preview_group)
        
        self.crop_preview_label = DraggablePreviewLabel()
        self.crop_preview_label.position_changed.connect(self._on_crop_position_changed)
        self.crop_preview_label.setFixedSize(300, 300)
        self.crop_preview_label.setAlignment(Qt.AlignCenter)
        self.crop_preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        crop_preview_layout.addWidget(self.crop_preview_label, 0, Qt.AlignHCenter)
        
        # 버튼 레이아웃
        crop_button_layout = QHBoxLayout()
        fill_button_crop = QPushButton("채우기")
        fill_button_crop.clicked.connect(self._fill_crop_area)
        center_button_crop = QPushButton("가운데 정렬")
        center_button_crop.clicked.connect(self._center_crop_area)
        crop_button_layout.addWidget(fill_button_crop)
        crop_button_layout.addWidget(center_button_crop)
        crop_preview_layout.addLayout(crop_button_layout)
        
        crop_section_layout.addWidget(crop_preview_group, 1)

        content_layout.addWidget(crop_section_container)
        
        # 프린터 설정 추가
        self.init_printer_settings(content_layout)
        
        # 카드 설정 추가
        self.init_card_settings(content_layout)
        
        # 이미지 설정 추가
        self.init_image_settings(content_layout)
        
        # 스트레치 추가
        content_layout.addStretch()
        
        self._update_crop_preview()
        
    def init_card_settings(self, parent_layout):
        """카드 방향 설정 초기화"""
        card_group = QGroupBox("카드 설정")
        self.apply_left_aligned_group_style(card_group)
        card_layout = QFormLayout(card_group)
        
        orientation_layout = QHBoxLayout()
        self.card_portrait_radio = QRadioButton("세로")
        self.card_landscape_radio = QRadioButton("가로")
        
        # config에서 'card' 설정을 안전하게 가져오기
        card_config = self.config.get("card", {})
        if card_config.get("orientation", "portrait") == "portrait":
            self.card_portrait_radio.setChecked(True)
        else:
            self.card_landscape_radio.setChecked(True)

        # 카드 미리보기와 고정 이미지 미리보기 모두 업데이트하도록 연결
        self.card_portrait_radio.toggled.connect(self._on_orientation_changed)
        
        orientation_layout.addWidget(self.card_portrait_radio)
        self.card_landscape_radio.toggled.connect(self._on_orientation_changed)
        orientation_layout.addWidget(self.card_landscape_radio)
        
        card_layout.addRow("인쇄 방향:", orientation_layout)
        parent_layout.addWidget(card_group)
        
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
        
        # 이미지 개수 설정 (드롭다운)
        image_count_layout = QHBoxLayout()
        self.image_count_combo = QComboBox()
        self.image_count_combo.addItems(["0", "1"])
        
        # config에서 현재 값 가져오기 (없거나 유효하지 않으면 0)
        current_count = self.config["images"].get("count", 0)
        if current_count not in [0, 1]:
            current_count = 0
        self.image_count_combo.setCurrentIndex(current_count)
        
        self.image_count_combo.currentIndexChanged.connect(self.update_image_items)
        
        image_count_layout.addWidget(self.image_count_combo)
        image_count_layout.addStretch()
        
        images_layout.addLayout(image_count_layout)
        
        # 이미지 항목 컨테이너
        self.image_items_container = QWidget()
        self.image_items_layout = QVBoxLayout(self.image_items_container)
        self.image_items_layout.setContentsMargins(0, 0, 0, 0)
        
        # 이미지 항목 필드 초기화
        self.image_item_fields = []
        self.update_image_items(current_count) # 초기값으로 업데이트
        
        images_layout.addWidget(self.image_items_container)
        parent_layout.addWidget(images_group)
        
    def update_image_items(self, count):
        """이미지 항목 UI 업데이트"""
        # 기존 위젯 제거
        for i in reversed(range(self.image_items_layout.count())):
            item = self.image_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # 필드 및 미리보기 초기화
        self.image_item_fields = []
        self.image_preview_label = None

        if count == 1:
            item_data = self.config["images"]["items"][0] if self.config["images"]["items"] else {
                "filename": "", "x": 0, "y": 0, "width": 300, "height": 300, "orientation": "portrait"
            }
            main_container, item_fields = self.create_image_settings_ui(item_data)
            self.image_items_layout.addWidget(main_container)
            self.image_item_fields.append(item_fields)
            self.update_card_preview()

    def create_image_settings_ui(self, item_data):
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)

        item_group = QGroupBox("이미지 1")
        item_layout = QFormLayout(item_group)
        item_fields = {}

        filename_layout = QHBoxLayout()
        filename_edit = QLineEdit(item_data.get("filename", ""))
        filename_layout.addWidget(filename_edit, 1)
        item_fields["filename"] = filename_edit
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda: self.on_browse_image(filename_edit))
        filename_layout.addWidget(browse_button)
        item_layout.addRow("파일명:", filename_layout)

        for key, label in [("width", "너비"), ("height", "높이"), ("x", "X 위치"), ("y", "Y 위치")]:
            line_edit = NumberLineEdit()
            line_edit.setValue(item_data.get(key, 0))
            line_edit.textChanged.connect(self.update_card_preview)
            item_layout.addRow(f"{label}:", line_edit)
            item_fields[key] = line_edit
        
        # 구분선 추가
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        item_layout.addRow(separator)

        # 인쇄 매수 설정 및 버튼
        print_controls_layout = QHBoxLayout()
        print_controls_layout.setContentsMargins(0,0,0,0)
        
        self.print_count_edit = NumberLineEdit()
        self.print_count_edit.setFixedWidth(50) # 너비 조절
        self.print_count_edit.setValue(1)
        
        self.print_button = QPushButton("인쇄")
        self.print_button.clicked.connect(self._on_print_button_clicked)

        print_controls_layout.addWidget(QLabel("인쇄매수:"))
        print_controls_layout.addWidget(self.print_count_edit)
        print_controls_layout.addStretch(1)
        print_controls_layout.addWidget(self.print_button)
        
        item_layout.addRow(print_controls_layout)

        main_layout.addWidget(item_group, 1)

        preview_group = QGroupBox("미리보기")
        preview_layout = QVBoxLayout(preview_group)
        self.image_preview_label = DraggablePreviewLabel()
        self.image_preview_label.position_changed.connect(self._on_image_position_changed)
        self.image_preview_label.setFixedSize(300, 300)
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        preview_layout.addWidget(self.image_preview_label, 0, Qt.AlignHCenter)
        main_layout.addWidget(preview_group, 1)

        return main_container, item_fields

    def on_browse_image(self, filename_edit):
        source_path, _ = QFileDialog.getOpenFileName(self, "이미지 파일 선택", "", "Image Files (*.png *.jpg *.jpeg *.gif)")
        if source_path:
            destination_dir = "resources"
            os.makedirs(destination_dir, exist_ok=True)
            filename = os.path.basename(source_path)
            destination_path = os.path.join(destination_dir, filename)
            try:
                shutil.copy(source_path, destination_path)
                filename_edit.setText(filename)
                self.update_card_preview()
            except Exception as e:
                print(f"이미지 복사 오류: {e}")

    def update_card_preview(self):
        if not self.image_item_fields or not self.image_preview_label:
            return

        fields = self.image_item_fields[0]
        filename = fields["filename"].text()
        x = fields["x"].value()
        y = fields["y"].value()
        width = fields["width"].value()
        height = fields["height"].value()

        # 전역 카드 방향 설정 사용
        if not self.card_portrait_radio: # UI가 아직 생성되지 않은 경우
            is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        else:
            is_portrait = self.card_portrait_radio.isChecked()

        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        card_pixmap = QPixmap(card_width, card_height)
        card_pixmap.fill(Qt.white)

        overlay_pixmap = QPixmap()
        image_path = os.path.join("resources", filename) if filename else ""
        if filename and os.path.exists(image_path):
            overlay_pixmap = QPixmap(image_path)
            
        image_rect = QRect(x, y, width, height)
        
        self.image_preview_label.update_preview(card_pixmap, image_rect, overlay_pixmap)
    
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
        """카메라 해상도 변경 시 호출되는 메소드"""
        selected_resolution = self.camera_resolution_combo.itemData(index)
        if selected_resolution:
            self.config["camera_size"]["width"] = selected_resolution[0]
            self.config["camera_size"]["height"] = selected_resolution[1]
        self._update_crop_preview()

    def _fill_crop_area(self):
        """실제 인쇄 영역을 카메라 해상도에 맞게 채웁니다."""
        cam_resolution = self.camera_resolution_combo.currentData()
        if not cam_resolution:
            return
        cam_width, cam_height = cam_resolution
        
        self.crop_fields['width'].setValue(cam_width)
        self.crop_fields['height'].setValue(cam_height)
        self.crop_fields['x'].setValue(0)
        self.crop_fields['y'].setValue(0)

    def _center_crop_area(self):
        """실제 인쇄 영역을 카메라 해상도의 중앙에 정렬합니다."""
        cam_resolution = self.camera_resolution_combo.currentData()
        if not cam_resolution:
            return
        cam_width, cam_height = cam_resolution

        crop_width = self.crop_fields['width'].value()
        crop_height = self.crop_fields['height'].value()
        
        center_x = (cam_width - crop_width) / 2
        center_y = (cam_height - crop_height) / 2
        
        self.crop_fields['x'].setValue(int(center_x))
        self.crop_fields['y'].setValue(int(center_y))

    def _update_crop_preview(self):
        """실제 인쇄 영역 미리보기 업데이트"""
        if not self.crop_preview_label:
            return

        cam_resolution = self.camera_resolution_combo.currentData()
        if not cam_resolution:
            cam_width = self.config["camera_size"]["width"]
            cam_height = self.config["camera_size"]["height"]
        else:
            cam_width, cam_height = cam_resolution

        if cam_width == 0 or cam_height == 0:
            return

        bg_pixmap = QPixmap(cam_width, cam_height)
        bg_pixmap.fill(Qt.white)
        
        try:
            width = self.crop_fields["width"].value()
            height = self.crop_fields["height"].value()
            x = self.crop_fields["x"].value()
            y = self.crop_fields["y"].value()
            crop_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            crop_rect = QRect()
        
        pen = QPen(QColor("red"), 2)
        self.crop_preview_label.set_pen(pen)
        self.crop_preview_label.update_preview(bg_pixmap, crop_rect)

    def _on_crop_position_changed(self, x, y):
        """드래그로 위치 변경 시 호출되는 슬롯"""
        self.crop_fields['x'].blockSignals(True)
        self.crop_fields['y'].blockSignals(True)
        
        self.crop_fields['x'].setValue(x)
        self.crop_fields['y'].setValue(y)
        
        self.crop_fields['x'].blockSignals(False)
        self.crop_fields['y'].blockSignals(False)

    def _on_image_position_changed(self, x, y):
        """드래그로 고정 이미지 위치 변경 시 호출되는 슬롯"""
        if not self.image_item_fields:
            return
            
        fields = self.image_item_fields[0]
        fields['x'].blockSignals(True)
        fields['y'].blockSignals(True)
        
        fields['x'].setValue(x)
        fields['y'].setValue(y)
        
        fields['x'].blockSignals(False)
        fields['y'].blockSignals(False)

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
        
        # 실제 인쇄 영역 업데이트
        for key, widget in self.crop_fields.items():
            widget.setValue(config["crop_area"][key])
        
        # 카드 방향 업데이트
        if self.card_portrait_radio:
            orientation = config.get("card", {}).get("orientation", "portrait")
            if orientation == "portrait":
                self.card_portrait_radio.setChecked(True)
            else:
                self.card_landscape_radio.setChecked(True)
        
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
        new_count = config["images"].get("count", 0)
        if new_count not in [0, 1]:
            new_count = 0

        if self.image_count_combo.currentIndex() != new_count:
            self.image_count_combo.setCurrentIndex(new_count)
        else:
            # 이미지 항목 업데이트
            self.update_image_items(new_count)
            
            # 각 항목의 데이터도 업데이트
            for i, fields in enumerate(self.image_item_fields):
                if i < len(config["images"]["items"]):
                    item = config["images"]["items"][i]
                    fields["filename"].setText(item["filename"])
                    fields["x"].setValue(item["x"])
                    fields["y"].setValue(item["y"])
                    fields["width"].setValue(item["width"])
                    fields["height"].setValue(item["height"])
            
        self.update_card_preview()
        self._update_crop_preview()
        
    def update_config(self, config):
        """UI 값을 config에 반영"""
        config["app_name"] = self.app_name_edit.text()
        config["screen_size"]["width"] = self.screen_width_edit.value()
        config["screen_size"]["height"] = self.screen_height_edit.value()
        
        # 카드 방향 저장
        if "card" not in config:
            config["card"] = {}
        if self.card_portrait_radio:
            config["card"]["orientation"] = "portrait" if self.card_portrait_radio.isChecked() else "landscape"
        else: # UI 로드 전의 경우를 대비
            config["card"]["orientation"] = config.get("card", {}).get("orientation", "portrait")

        # 실제 인쇄 영역 설정 저장
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
        config["images"]["count"] = self.image_count_combo.currentIndex()
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

    def _on_print_button_clicked(self):
        """인쇄 버튼 클릭 시 호출되는 슬롯"""
        if not self.image_item_fields:
            self._show_error_message("인쇄할 이미지가 설정되지 않았습니다.")
            return

        # UI에서 현재 설정 값 가져오기
        try:
            print_data = {
                "filename": self.image_item_fields[0]["filename"].text(),
                "x": self.image_item_fields[0]["x"].value(),
                "y": self.image_item_fields[0]["y"].value(),
                "width": self.image_item_fields[0]["width"].value(),
                "height": self.image_item_fields[0]["height"].value(),
            }
            print_count = self.print_count_edit.value()
            panel_id = self.panel_combo.currentData()

        except (IndexError, KeyError) as e:
            self._show_error_message(f"인쇄 정보를 가져오는 중 오류가 발생했습니다: {e}")
            return
            
        if not print_data["filename"]:
            self._show_error_message("인쇄할 이미지 파일이 선택되지 않았습니다.")
            return

        # 인쇄 스레드 시작
        self.print_button.setEnabled(False)
        self.window().statusBar().showMessage("인쇄를 시작합니다...")

        self.printer_thread = PrinterThread(print_data, print_count, panel_id)
        self.printer_thread.finished.connect(self._on_print_finished)
        self.printer_thread.error.connect(self._on_print_error)
        self.printer_thread.start()

    def _on_print_finished(self):
        """인쇄 성공 시 호출되는 슬롯"""
        self.window().statusBar().showMessage("인쇄가 완료되었습니다.", 5000)
        self.print_button.setEnabled(True)

    def _on_print_error(self, message):
        """인쇄 오류 시 호출되는 슬롯"""
        self._show_error_message(message)
        self.window().statusBar().showMessage(f"인쇄 오류: {message}", 5000)
        self.print_button.setEnabled(True)

    def _show_error_message(self, message):
        """오류 메시지 박스를 표시하는 헬퍼 함수"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("오류")
        msg_box.setInformativeText(message)
        msg_box.setWindowTitle("오류")
        msg_box.exec()

    def _on_orientation_changed(self):
        """카드 방향 변경 시 호출되는 슬롯"""
        # 1. 즉시 config 객체 업데이트
        if "card" not in self.config:
            self.config["card"] = {}
        self.config["card"]["orientation"] = "portrait" if self.card_portrait_radio.isChecked() else "landscape"
        
        # 2. BasicTab의 미리보기 업데이트
        self.update_card_preview()
        
        # 3. 다른 탭에 변경사항 전파
        self.config_changed.emit()