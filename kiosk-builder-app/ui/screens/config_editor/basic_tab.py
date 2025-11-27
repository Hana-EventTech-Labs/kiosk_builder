#BaseTab을 상속받은 구체적인 탭 클래스
import os
import shutil
from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QRadioButton, QCheckBox, QGridLayout, QFileDialog, QFrame, QMessageBox, QSplitter)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect, Signal
from ui.components.inputs import NumberLineEdit, ModernLineEdit
from ui.components.collapsible_group import CollapsibleGroupBox
from ui.components.position_size_input import PositionSizeInput
from utils.file_handler import FileHandler
from .base_tab import BaseTab
from ui.components.preview_label import DraggablePreviewLabel
from utils.printer_thread import PrinterThread

class BasicTab(BaseTab):
    config_changed = Signal()

    def __init__(self, config):
        super().__init__(config)
        self.tab_manager = None
        self.screen_order_checkboxes = []
        self.card_portrait_radio = None
        self.card_landscape_radio = None
        self.print_count_edit = None
        self.print_button = None
        self.printer_thread = None
        self.image_preview_label = None
        self.init_ui()

    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()

        # ═══════════════════════════════════════════════════════════
        # 메인 2열 레이아웃: 좌측(설정) | 우측(미리보기)
        # ═══════════════════════════════════════════════════════════
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        content_layout.addLayout(main_layout)

        # ───────────────────────────────────────────────────────────
        # 좌측: 설정 영역
        # ───────────────────────────────────────────────────────────
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        # 1. 앱 기본 설정 그룹
        self._init_app_settings(settings_layout)

        # 2. 디스플레이 & 카메라 설정 그룹
        self._init_display_camera_settings(settings_layout)

        # 3. 인쇄 설정 그룹
        self._init_print_settings(settings_layout)

        settings_layout.addStretch()
        main_layout.addWidget(settings_widget, 3)  # 비율 3

        # ───────────────────────────────────────────────────────────
        # 우측: 미리보기 + 고정 이미지 설정 영역
        # ───────────────────────────────────────────────────────────
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(12)

        # 고정 이미지 설정 (토글 형식) - 미리보기 포함
        self._init_fixed_image_settings(preview_layout)

        preview_layout.addStretch()
        main_layout.addWidget(preview_widget, 2)  # 비율 2

        # 초기 미리보기 업데이트
        self.update_card_preview()

    # ═══════════════════════════════════════════════════════════════
    # 1. 앱 기본 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_app_settings(self, parent_layout):
        """앱 기본 설정 그룹 초기화"""
        app_group = QGroupBox("📱 앱 기본 설정")
        self.apply_left_aligned_group_style(app_group)
        app_layout = QVBoxLayout(app_group)
        app_layout.setSpacing(10)

        # 앱 이름
        name_layout = QFormLayout()
        self.app_name_edit = ModernLineEdit(placeholder="앱 이름을 입력하세요")
        self.app_name_edit.setFixedHeight(35)
        self.app_name_edit.setText(self.config["app_name"])
        name_layout.addRow("앱 이름:", self.app_name_edit)
        app_layout.addLayout(name_layout)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        app_layout.addWidget(separator)

        # 화면 순서 선택
        screen_label = QLabel("화면 순서:")
        screen_label.setStyleSheet("font-weight: bold; color: #555;")
        app_layout.addWidget(screen_label)

        screen_order_layout = QGridLayout()
        screen_order_layout.setSpacing(8)

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

            row, col = divmod(i, 4)
            screen_order_layout.addWidget(checkbox, row, col)
            self.screen_order_checkboxes.append(checkbox)

        app_layout.addLayout(screen_order_layout)
        parent_layout.addWidget(app_group)

    # ═══════════════════════════════════════════════════════════════
    # 2. 디스플레이 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_display_camera_settings(self, parent_layout):
        """디스플레이 설정 그룹 초기화"""
        display_group = QGroupBox("🖥️ 디스플레이")
        self.apply_left_aligned_group_style(display_group)
        display_layout = QVBoxLayout(display_group)
        display_layout.setSpacing(10)

        # 모니터 크기
        monitor_layout = QHBoxLayout()
        monitor_layout.addWidget(QLabel("모니터 크기:"))

        self.screen_width_edit = NumberLineEdit()
        self.screen_width_edit.setValue(self.config["screen_size"]["width"])
        self.screen_width_edit.setFixedWidth(80)
        self.screen_width_edit.editingFinished.connect(self._on_monitor_size_changed)
        monitor_layout.addWidget(self.screen_width_edit)

        monitor_layout.addWidget(QLabel("×"))

        self.screen_height_edit = NumberLineEdit()
        self.screen_height_edit.setValue(self.config["screen_size"]["height"])
        self.screen_height_edit.setFixedWidth(80)
        self.screen_height_edit.editingFinished.connect(self._on_monitor_size_changed)
        monitor_layout.addWidget(self.screen_height_edit)

        monitor_layout.addWidget(QLabel("px"))
        monitor_layout.addStretch()
        display_layout.addLayout(monitor_layout)

        # 설명 라벨
        info_label = QLabel("💡 카메라 관련 설정은 '촬영화면' 탭에서 설정하세요")
        info_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        display_layout.addWidget(info_label)

        parent_layout.addWidget(display_group)

    # ═══════════════════════════════════════════════════════════════
    # 3. 인쇄 설정 (고정 이미지 설정 분리됨)
    # ═══════════════════════════════════════════════════════════════
    def _init_print_settings(self, parent_layout):
        """인쇄 설정 그룹 초기화 (프린터 기본 설정만)"""
        print_group = QGroupBox("🖨️ 인쇄 설정")
        self.apply_left_aligned_group_style(print_group)
        print_layout = QVBoxLayout(print_group)
        print_layout.setSpacing(10)

        # 프린터 모드
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("모드:"))

        self.preview_mode_radio = QRadioButton("미리보기")
        self.print_mode_radio = QRadioButton("인쇄")

        current_print_mode = self.config.get("printer", {}).get("print_mode", False)
        if current_print_mode:
            self.print_mode_radio.setChecked(True)
        else:
            self.preview_mode_radio.setChecked(True)

        mode_layout.addWidget(self.preview_mode_radio)
        mode_layout.addWidget(self.print_mode_radio)
        mode_layout.addStretch()
        print_layout.addLayout(mode_layout)

        # 패널 타입
        panel_layout = QHBoxLayout()
        panel_layout.addWidget(QLabel("패널:"))

        self.panel_combo = QComboBox()
        self.panel_combo.addItem("YMC (컬러)", 1)
        self.panel_combo.addItem("Resin (블랙/실버)", 2)
        self.panel_combo.addItem("Overlay (보호막)", 4)
        self.panel_combo.addItem("UV (형광)", 8)

        current_panel_id = self.config.get("printer", {}).get("panel_id", 1)
        for i in range(self.panel_combo.count()):
            if self.panel_combo.itemData(i) == current_panel_id:
                self.panel_combo.setCurrentIndex(i)
                break

        panel_layout.addWidget(self.panel_combo)
        panel_layout.addStretch()
        print_layout.addLayout(panel_layout)

        # 카드 방향
        orientation_layout = QHBoxLayout()
        orientation_layout.addWidget(QLabel("카드 방향:"))

        self.card_portrait_radio = QRadioButton("세로")
        self.card_landscape_radio = QRadioButton("가로")

        card_config = self.config.get("card", {})
        if card_config.get("orientation", "portrait") == "portrait":
            self.card_portrait_radio.setChecked(True)
        else:
            self.card_landscape_radio.setChecked(True)

        self.card_portrait_radio.toggled.connect(self._on_orientation_changed)
        self.card_landscape_radio.toggled.connect(self._on_orientation_changed)

        orientation_layout.addWidget(self.card_portrait_radio)
        orientation_layout.addWidget(self.card_landscape_radio)
        orientation_layout.addStretch()
        print_layout.addLayout(orientation_layout)

        parent_layout.addWidget(print_group)

    # ═══════════════════════════════════════════════════════════════
    # 고정 이미지 설정 (토글 형식, 미리보기 포함)
    # ═══════════════════════════════════════════════════════════════
    def _init_fixed_image_settings(self, parent_layout):
        """고정 이미지 설정 (토글 형식, 1개 사용 시에만 미리보기 표시)"""
        # 접이식 그룹박스
        image_collapsible = CollapsibleGroupBox("🖼️ 고정 이미지 설정", collapsed=False)

        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        image_layout.setSpacing(12)
        image_layout.setContentsMargins(0, 0, 0, 0)

        # 이미지 사용 여부
        use_layout = QHBoxLayout()
        use_label = QLabel("이미지 사용:")
        use_label.setStyleSheet("font-weight: bold; color: #555;")
        use_layout.addWidget(use_label)

        self.image_count_combo = QComboBox()
        self.image_count_combo.addItems(["사용 안함", "1개 사용"])
        current_count = self.config["images"].get("count", 0)
        if current_count not in [0, 1]:
            current_count = 0
        self.image_count_combo.setCurrentIndex(current_count)
        self.image_count_combo.currentIndexChanged.connect(self.update_image_items)
        use_layout.addWidget(self.image_count_combo)
        use_layout.addStretch()
        image_layout.addLayout(use_layout)

        # 이미지 항목 컨테이너 (미리보기 + 설정 포함)
        self.image_items_container = QWidget()
        self.image_items_layout = QVBoxLayout(self.image_items_container)
        self.image_items_layout.setContentsMargins(0, 0, 0, 0)
        self.image_items_layout.setSpacing(12)

        self.image_item_fields = []
        self.image_preview_label = None  # 초기화

        self.update_image_items(current_count)

        image_layout.addWidget(self.image_items_container)
        image_collapsible.addWidget(image_widget)
        parent_layout.addWidget(image_collapsible)

    # ═══════════════════════════════════════════════════════════════
    # 이미지 설정 UI
    # ═══════════════════════════════════════════════════════════════
    def update_image_items(self, count):
        """이미지 항목 UI 업데이트 (미리보기 포함)"""
        self.config["images"]["count"] = count

        # 기존 위젯 제거
        for i in reversed(range(self.image_items_layout.count())):
            item = self.image_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.image_item_fields = []
        self.image_preview_label = None

        if count == 1:
            item_data = self.config["images"]["items"][0] if self.config["images"]["items"] else {
                "filename": "", "x": 0, "y": 0, "width": 300, "height": 300
            }

            # ─────────────────────────────────────────
            # 미리보기 영역 (상단)
            # ─────────────────────────────────────────
            preview_container = QWidget()
            preview_container.setObjectName("previewContainer")
            preview_container.setStyleSheet("""
                QWidget#previewContainer {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                }
            """)
            preview_layout = QVBoxLayout(preview_container)
            preview_layout.setContentsMargins(12, 12, 12, 12)
            preview_layout.setSpacing(8)

            # 미리보기 헤더
            preview_header = QLabel("📋 인쇄물 미리보기")
            preview_header.setStyleSheet("font-weight: bold; color: #333; background: transparent; border: none;")
            preview_layout.addWidget(preview_header)

            # 미리보기 라벨
            self.image_preview_label = DraggablePreviewLabel()
            self.image_preview_label.position_changed.connect(self._on_image_position_changed)
            self.image_preview_label.setFixedSize(240, 240)
            self.image_preview_label.setAlignment(Qt.AlignCenter)
            self.image_preview_label.setStyleSheet("""
                border: 1px solid #ccc;
                background-color: white;
                border-radius: 6px;
            """)
            preview_layout.addWidget(self.image_preview_label, 0, Qt.AlignCenter)

            # 버튼
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)
            fill_btn = QPushButton("채우기")
            fill_btn.setFixedHeight(28)
            fill_btn.clicked.connect(self._fill_image_frame)
            center_btn = QPushButton("가운데")
            center_btn.setFixedHeight(28)
            center_btn.clicked.connect(self._center_image_frame)
            btn_layout.addWidget(fill_btn)
            btn_layout.addWidget(center_btn)
            preview_layout.addLayout(btn_layout)

            self.image_items_layout.addWidget(preview_container)

            # ─────────────────────────────────────────
            # 이미지 설정 영역 (하단)
            # ─────────────────────────────────────────
            item_widget, item_fields = self._create_image_item_ui(item_data)
            self.image_items_layout.addWidget(item_widget)
            self.image_item_fields.append(item_fields)

            # 미리보기 업데이트
            self.update_card_preview()

            if hasattr(self, 'tab_manager') and self.tab_manager:
                self.tab_manager.reconnect_dynamic_signals()

        if hasattr(self, 'tab_manager') and self.tab_manager:
            self.request_real_time_update()

    def _create_image_item_ui(self, item_data):
        """이미지 항목 UI 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        item_fields = {}

        # 파일 선택
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("파일:"))
        filename_edit = QLineEdit(item_data.get("filename", ""))
        filename_edit.setPlaceholderText("이미지 파일 선택...")
        file_layout.addWidget(filename_edit, 1)
        item_fields["filename"] = filename_edit

        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(35)
        browse_btn.clicked.connect(lambda: self.on_browse_image(filename_edit))
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # 위치 & 크기 (직관적 컴포넌트 사용)
        position_size = PositionSizeInput()
        position_size.set_values(
            x=item_data.get("x", 0),
            y=item_data.get("y", 0),
            width=item_data.get("width", 300),
            height=item_data.get("height", 300)
        )
        position_size.value_changed.connect(self.update_card_preview)
        layout.addWidget(position_size)
        item_fields["position_size"] = position_size

        # 인쇄 버튼
        print_layout = QHBoxLayout()
        print_layout.addWidget(QLabel("매수:"))
        self.print_count_edit = NumberLineEdit()
        self.print_count_edit.setFixedWidth(50)
        self.print_count_edit.setValue(1)
        print_layout.addWidget(self.print_count_edit)

        self.print_button = QPushButton("🖨️ 인쇄")
        self.print_button.clicked.connect(self._on_print_button_clicked)
        print_layout.addWidget(self.print_button)
        print_layout.addStretch()
        layout.addLayout(print_layout)

        return widget, item_fields

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
                self.request_real_time_update()
            except Exception as e:
                print(f"이미지 복사 오류: {e}")

    # ═══════════════════════════════════════════════════════════════
    # 미리보기 업데이트 함수들
    # ═══════════════════════════════════════════════════════════════
    def update_card_preview(self):
        """인쇄물 카드 미리보기 업데이트"""
        if not self.image_item_fields or not self.image_preview_label:
            return

        fields = self.image_item_fields[0]
        filename = fields["filename"].text()
        position_size = fields["position_size"]
        x = position_size.get_x()
        y = position_size.get_y()
        width = position_size.get_width()
        height = position_size.get_height()

        if not self.card_portrait_radio:
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
        self.image_preview_label.set_card_border(True)  # 카드 테두리 표시
        self.image_preview_label.update_preview(card_pixmap, image_rect, overlay_pixmap)
        self.request_real_time_update()

    # ═══════════════════════════════════════════════════════════════
    # 이벤트 핸들러
    # ═══════════════════════════════════════════════════════════════
    def on_screen_order_changed(self):
        self.config["screen_order"] = sorted([
            cb.property("screen_index")
            for cb in self.screen_order_checkboxes
            if cb.isChecked()
        ])
        self.config_changed.emit()

    def _fill_image_frame(self):
        if not self.image_item_fields:
            return

        is_portrait = self.card_portrait_radio.isChecked()
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        fields = self.image_item_fields[0]
        position_size = fields["position_size"]
        position_size.set_values(x=0, y=0, width=card_width, height=card_height)
        self.request_real_time_update()

    def _center_image_frame(self):
        if not self.image_item_fields:
            return

        is_portrait = self.card_portrait_radio.isChecked()
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        fields = self.image_item_fields[0]
        position_size = fields["position_size"]
        image_width = position_size.get_width()
        image_height = position_size.get_height()

        center_x = (card_width - image_width) / 2
        center_y = (card_height - image_height) / 2

        position_size.set_x(int(center_x))
        position_size.set_y(int(center_y))
        self.request_real_time_update()

    def _on_image_position_changed(self, x, y):
        if not self.image_item_fields:
            return

        fields = self.image_item_fields[0]
        position_size = fields["position_size"]
        position_size.block_all_signals(True)
        position_size.set_x(x)
        position_size.set_y(y)
        position_size.block_all_signals(False)
        self.request_real_time_update()

    def _on_orientation_changed(self, checked):
        if not checked:
            return

        if "card" not in self.config:
            self.config["card"] = {}
        self.config["card"]["orientation"] = "portrait" if self.card_portrait_radio.isChecked() else "landscape"

        self.update_card_preview()
        self.config_changed.emit()

    def _on_monitor_size_changed(self):
        self.config["screen_size"]["width"] = self.screen_width_edit.value()
        self.config["screen_size"]["height"] = self.screen_height_edit.value()
        self.config_changed.emit()

    # ═══════════════════════════════════════════════════════════════
    # 인쇄 기능
    # ═══════════════════════════════════════════════════════════════
    def _on_print_button_clicked(self):
        if not self.image_item_fields:
            self._show_error_message("인쇄할 이미지가 설정되지 않았습니다.")
            return

        try:
            fields = self.image_item_fields[0]
            position_size = fields["position_size"]
            print_data = {
                "filename": fields["filename"].text(),
                "x": position_size.get_x(),
                "y": position_size.get_y(),
                "width": position_size.get_width(),
                "height": position_size.get_height(),
            }
            print_count = self.print_count_edit.value()
            panel_id = self.panel_combo.currentData()

        except (IndexError, KeyError) as e:
            self._show_error_message(f"인쇄 정보를 가져오는 중 오류가 발생했습니다: {e}")
            return

        if not print_data["filename"]:
            self._show_error_message("인쇄할 이미지 파일이 선택되지 않았습니다.")
            return

        self.print_button.setEnabled(False)
        self.window().statusBar().showMessage("인쇄를 시작합니다...")

        self.printer_thread = PrinterThread(print_data, print_count, panel_id)
        self.printer_thread.finished.connect(self._on_print_finished)
        self.printer_thread.error.connect(self._on_print_error)
        self.printer_thread.start()

    def _on_print_finished(self):
        self.window().statusBar().showMessage("인쇄가 완료되었습니다.", 5000)
        self.print_button.setEnabled(True)

    def _on_print_error(self, message):
        self._show_error_message(message)
        self.window().statusBar().showMessage(f"인쇄 오류: {message}", 5000)
        self.print_button.setEnabled(True)

    def _show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("오류")
        msg_box.setInformativeText(message)
        msg_box.setWindowTitle("오류")
        msg_box.exec()

    # ═══════════════════════════════════════════════════════════════
    # Config 동기화
    # ═══════════════════════════════════════════════════════════════
    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        self.app_name_edit.setText(config["app_name"])
        self.screen_width_edit.setValue(config["screen_size"]["width"])
        self.screen_height_edit.setValue(config["screen_size"]["height"])

        for checkbox in self.screen_order_checkboxes:
            index = checkbox.property("screen_index")
            checkbox.stateChanged.disconnect(self.on_screen_order_changed)
            checkbox.setChecked(index in config["screen_order"])
            checkbox.stateChanged.connect(self.on_screen_order_changed)

        if self.card_portrait_radio:
            orientation = config.get("card", {}).get("orientation", "portrait")
            if orientation == "portrait":
                self.card_portrait_radio.setChecked(True)
            else:
                self.card_landscape_radio.setChecked(True)

        current_print_mode = config.get("printer", {}).get("print_mode", False)
        if current_print_mode:
            self.print_mode_radio.setChecked(True)
        else:
            self.preview_mode_radio.setChecked(True)

        current_panel_id = config.get("printer", {}).get("panel_id", 1)
        for i in range(self.panel_combo.count()):
            if self.panel_combo.itemData(i) == current_panel_id:
                self.panel_combo.setCurrentIndex(i)
                break

        new_count = config["images"].get("count", 0)
        if new_count not in [0, 1]:
            new_count = 0

        if self.image_count_combo.currentIndex() != new_count:
            self.image_count_combo.setCurrentIndex(new_count)
        else:
            self.update_image_items(new_count)

            for i, fields in enumerate(self.image_item_fields):
                if i < len(config["images"]["items"]):
                    item = config["images"]["items"][i]
                    fields["filename"].setText(item["filename"])
                    position_size = fields["position_size"]
                    position_size.set_values(
                        x=item["x"],
                        y=item["y"],
                        width=item["width"],
                        height=item["height"]
                    )

        self.update_card_preview()

    def update_config(self, config):
        """UI 값을 config에 반영"""
        config["app_name"] = self.app_name_edit.text()
        config["screen_size"]["width"] = self.screen_width_edit.value()
        config["screen_size"]["height"] = self.screen_height_edit.value()

        if "card" not in config:
            config["card"] = {}
        if self.card_portrait_radio:
            config["card"]["orientation"] = "portrait" if self.card_portrait_radio.isChecked() else "landscape"
        else:
            config["card"]["orientation"] = config.get("card", {}).get("orientation", "portrait")

        config["screen_order"] = sorted([
            cb.property("screen_index")
            for cb in self.screen_order_checkboxes
            if cb.isChecked()
        ])

        if "printer" not in config:
            config["printer"] = {"print_mode": False, "panel_id": 1}

        config["printer"]["print_mode"] = self.print_mode_radio.isChecked()

        selected_panel_id = self.panel_combo.currentData()
        if selected_panel_id:
            config["printer"]["panel_id"] = selected_panel_id

        config["images"]["count"] = self.image_count_combo.currentIndex()
        config["images"]["items"] = []

        for i, fields in enumerate(self.image_item_fields):
            position_size = fields["position_size"]
            item = {
                "filename": fields["filename"].text(),
                "x": position_size.get_x(),
                "y": position_size.get_y(),
                "width": position_size.get_width(),
                "height": position_size.get_height()
            }
            config["images"]["items"].append(item)
