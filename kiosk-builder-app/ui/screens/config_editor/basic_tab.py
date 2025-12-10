#BaseTab을 상속받은 구체적인 탭 클래스
import os
import sys
import shutil
from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QRadioButton, QCheckBox, QGridLayout, QFileDialog, QFrame, QMessageBox, QSplitter, QTabWidget, QScrollArea, QDateTimeEdit, QProgressBar, QTextEdit)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect, Signal, QDateTime, QThread
from ui.components.inputs import NumberLineEdit, ModernLineEdit
from ui.components.collapsible_group import CollapsibleGroupBox
from ui.components.position_size_input import PositionSizeInput
from utils.file_handler import FileHandler, get_resources_base_path
from .base_tab import BaseTab
from ui.components.preview_label import DraggablePreviewLabel
from utils.printer_thread import PrinterThread
from api_client import register_event_with_resources


class UploadWorker(QThread):
    """서버 등록 및 리소스 업로드를 백그라운드에서 처리하는 워커"""
    progress = Signal(int, str)  # percent, message
    finished = Signal(bool, dict)  # success, result

    def __init__(self, event_name, kiosk_count, expired_at, config, resources_dir):
        super().__init__()
        self.event_name = event_name
        self.kiosk_count = kiosk_count
        self.expired_at = expired_at
        self.config = config
        self.resources_dir = resources_dir

    def run(self):
        success, result = register_event_with_resources(
            event_name=self.event_name,
            kiosk_count=self.kiosk_count,
            expired_at=self.expired_at,
            config=self.config,
            resources_dir=self.resources_dir,
            progress_callback=self._on_progress
        )
        self.finished.emit(success, result)

    def _on_progress(self, percent, message):
        self.progress.emit(percent, message)


class BasicTab(BaseTab):
    config_changed = Signal()
    screen_order_changed = Signal()  # 화면 순서만 변경될 때 (탭 활성화 상태만 업데이트)

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
        self.upload_worker = None
        self.init_ui()

    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()

        # ═══════════════════════════════════════════════════════════
        # 서브 탭 위젯 생성
        # ═══════════════════════════════════════════════════════════
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #ffffff;
                color: #666;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: #f8f8f8;
            }
        """)

        # 4개의 서브 탭 생성
        self._create_app_settings_tab()       # 앱 기본 설정
        self._create_display_settings_tab()   # 디스플레이
        self._create_print_settings_tab()     # 인쇄 설정
        self._create_fixed_image_tab()        # 고정 이미지

        content_layout.addWidget(self.sub_tabs)

        # 초기 미리보기 업데이트
        self.update_card_preview()

    # ═══════════════════════════════════════════════════════════════
    # 1. 앱 기본 설정 탭
    # ═══════════════════════════════════════════════════════════════
    def _create_app_settings_tab(self):
        """앱 기본 설정 탭 생성"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 앱 이름 그룹 (행사명으로 사용)
        name_group = QGroupBox("행사 정보")
        self.apply_left_aligned_group_style(name_group)
        name_layout = QVBoxLayout(name_group)
        name_layout.setSpacing(10)

        name_form = QFormLayout()
        self.app_name_edit = ModernLineEdit(placeholder="행사명을 입력하세요 (예: 삼성 신제품 런칭)")
        self.app_name_edit.setFixedHeight(35)
        self.app_name_edit.setText(self.config["app_name"])
        name_form.addRow("행사명:", self.app_name_edit)
        name_layout.addLayout(name_form)

        main_layout.addWidget(name_group)

        # 서버 등록 그룹
        server_group = QGroupBox("서버 등록")
        self.apply_left_aligned_group_style(server_group)
        server_layout = QVBoxLayout(server_group)
        server_layout.setSpacing(10)

        # 키오스크 대수 & 만료일
        reg_form = QHBoxLayout()

        reg_form.addWidget(QLabel("키오스크 대수:"))
        self.kiosk_count_spin = QSpinBox()
        self.kiosk_count_spin.setRange(1, 100)
        self.kiosk_count_spin.setValue(1)
        self.kiosk_count_spin.setFixedWidth(70)
        reg_form.addWidget(self.kiosk_count_spin)

        reg_form.addSpacing(20)

        reg_form.addWidget(QLabel("만료일:"))
        self.expire_date_edit = QDateTimeEdit()
        self.expire_date_edit.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.expire_date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.expire_date_edit.setCalendarPopup(True)
        self.expire_date_edit.setFixedWidth(160)
        reg_form.addWidget(self.expire_date_edit)

        reg_form.addStretch()
        server_layout.addLayout(reg_form)

        # 등록 버튼 & 진행바
        btn_row = QHBoxLayout()
        self.register_btn = QPushButton("🚀 서버 등록 && 활성화 코드 생성")
        self.register_btn.setFixedHeight(36)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.register_btn.clicked.connect(self._on_register_clicked)
        btn_row.addWidget(self.register_btn)

        self.register_progress = QProgressBar()
        self.register_progress.setFixedHeight(20)
        self.register_progress.setVisible(False)
        self.register_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        btn_row.addWidget(self.register_progress)
        btn_row.addStretch()
        server_layout.addLayout(btn_row)

        # 활성화 코드 결과 (접혀있는 텍스트 영역)
        self.activation_result = QTextEdit()
        self.activation_result.setReadOnly(True)
        self.activation_result.setPlaceholderText("등록 후 활성화 코드가 여기에 표시됩니다.")
        self.activation_result.setFixedHeight(100)
        self.activation_result.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        server_layout.addWidget(self.activation_result)

        # 복사 버튼
        copy_row = QHBoxLayout()
        copy_btn = QPushButton("📋 복사")
        copy_btn.setFixedWidth(80)
        copy_btn.clicked.connect(self._copy_activation_codes)
        copy_row.addWidget(copy_btn)
        copy_row.addStretch()
        server_layout.addLayout(copy_row)

        main_layout.addWidget(server_group)

        # 화면 순서 그룹
        screen_group = QGroupBox("화면 순서")
        self.apply_left_aligned_group_style(screen_group)
        screen_layout = QVBoxLayout(screen_group)
        screen_layout.setSpacing(10)

        screen_label = QLabel("활성화할 화면을 선택하세요:")
        screen_label.setStyleSheet("color: #555; font-size: 12px;")
        screen_layout.addWidget(screen_label)

        screen_order_layout = QGridLayout()
        screen_order_layout.setSpacing(10)

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

        screen_layout.addLayout(screen_order_layout)
        main_layout.addWidget(screen_group)

        main_layout.addStretch()
        self.sub_tabs.addTab(tab, "📱 앱 기본 설정")

    # ═══════════════════════════════════════════════════════════════
    # 2. 디스플레이 탭
    # ═══════════════════════════════════════════════════════════════
    def _create_display_settings_tab(self):
        """디스플레이 설정 탭 생성"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 모니터 크기 그룹
        monitor_group = QGroupBox("모니터 크기")
        self.apply_left_aligned_group_style(monitor_group)
        monitor_layout = QVBoxLayout(monitor_group)
        monitor_layout.setSpacing(10)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("가로:"))

        self.screen_width_edit = NumberLineEdit()
        self.screen_width_edit.setValue(self.config["screen_size"]["width"])
        self.screen_width_edit.setFixedWidth(100)
        self.screen_width_edit.editingFinished.connect(self._on_monitor_size_changed)
        size_layout.addWidget(self.screen_width_edit)

        size_layout.addWidget(QLabel("×"))

        size_layout.addWidget(QLabel("세로:"))
        self.screen_height_edit = NumberLineEdit()
        self.screen_height_edit.setValue(self.config["screen_size"]["height"])
        self.screen_height_edit.setFixedWidth(100)
        self.screen_height_edit.editingFinished.connect(self._on_monitor_size_changed)
        size_layout.addWidget(self.screen_height_edit)

        size_layout.addWidget(QLabel("px"))
        size_layout.addStretch()
        monitor_layout.addLayout(size_layout)

        # 설명 라벨
        info_label = QLabel("실제 키오스크 디스플레이의 해상도를 입력하세요.\n카메라 관련 설정은 '촬영화면' 탭에서 설정할 수 있습니다.")
        info_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic; padding: 10px;")
        monitor_layout.addWidget(info_label)

        main_layout.addWidget(monitor_group)

        main_layout.addStretch()
        self.sub_tabs.addTab(tab, "🖥️ 디스플레이")

    # ═══════════════════════════════════════════════════════════════
    # 3. 인쇄 설정 탭
    # ═══════════════════════════════════════════════════════════════
    def _create_print_settings_tab(self):
        """인쇄 설정 탭 생성"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 프린터 모드 그룹
        mode_group = QGroupBox("프린터 모드")
        self.apply_left_aligned_group_style(mode_group)
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(10)

        mode_row = QHBoxLayout()
        self.preview_mode_radio = QRadioButton("미리보기 모드")
        self.print_mode_radio = QRadioButton("인쇄 모드")

        current_print_mode = self.config.get("printer", {}).get("print_mode", True)
        if current_print_mode:
            self.print_mode_radio.setChecked(True)
        else:
            self.preview_mode_radio.setChecked(True)

        mode_row.addWidget(self.preview_mode_radio)
        mode_row.addWidget(self.print_mode_radio)
        mode_row.addStretch()
        mode_layout.addLayout(mode_row)

        mode_info = QLabel("미리보기 모드: 실제 인쇄 없이 결과물 미리보기\n인쇄 모드: 프린터로 실제 인쇄 실행")
        mode_info.setStyleSheet("color: #888; font-size: 10px; padding-left: 5px;")
        mode_layout.addWidget(mode_info)

        main_layout.addWidget(mode_group)

        # 패널 설정 그룹
        panel_group = QGroupBox("패널 설정")
        self.apply_left_aligned_group_style(panel_group)
        panel_layout = QVBoxLayout(panel_group)
        panel_layout.setSpacing(10)

        panel_row = QHBoxLayout()
        panel_row.addWidget(QLabel("패널 타입:"))

        self.panel_combo = QComboBox()
        self.panel_combo.addItem("YMC (컬러)", 1)
        self.panel_combo.addItem("Resin (블랙/실버)", 2)
        self.panel_combo.addItem("Overlay (보호막)", 4)
        self.panel_combo.addItem("UV (형광)", 8)
        self.panel_combo.setMinimumWidth(200)

        current_panel_id = self.config.get("printer", {}).get("panel_id", 1)
        for i in range(self.panel_combo.count()):
            if self.panel_combo.itemData(i) == current_panel_id:
                self.panel_combo.setCurrentIndex(i)
                break

        panel_row.addWidget(self.panel_combo)
        panel_row.addStretch()
        panel_layout.addLayout(panel_row)

        main_layout.addWidget(panel_group)

        # 카드 방향 그룹
        orientation_group = QGroupBox("카드 방향")
        self.apply_left_aligned_group_style(orientation_group)
        orientation_layout = QVBoxLayout(orientation_group)
        orientation_layout.setSpacing(10)

        orientation_row = QHBoxLayout()
        self.card_portrait_radio = QRadioButton("세로 (Portrait)")
        self.card_landscape_radio = QRadioButton("가로 (Landscape)")

        card_config = self.config.get("card", {})
        if card_config.get("orientation", "portrait") == "portrait":
            self.card_portrait_radio.setChecked(True)
        else:
            self.card_landscape_radio.setChecked(True)

        self.card_portrait_radio.toggled.connect(self._on_orientation_changed)
        self.card_landscape_radio.toggled.connect(self._on_orientation_changed)

        orientation_row.addWidget(self.card_portrait_radio)
        orientation_row.addWidget(self.card_landscape_radio)
        orientation_row.addStretch()
        orientation_layout.addLayout(orientation_row)

        orientation_info = QLabel("인쇄할 카드의 방향을 선택하세요.\n세로: 636 x 1012 px / 가로: 1012 x 636 px")
        orientation_info.setStyleSheet("color: #888; font-size: 10px; padding-left: 5px;")
        orientation_layout.addWidget(orientation_info)

        main_layout.addWidget(orientation_group)

        main_layout.addStretch()
        self.sub_tabs.addTab(tab, "🖨️ 인쇄 설정")

    # ═══════════════════════════════════════════════════════════════
    # 4. 고정 이미지 탭
    # ═══════════════════════════════════════════════════════════════
    def _create_fixed_image_tab(self):
        """고정 이미지 설정 탭 생성 (미리보기 포함)"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ───────────────────────────────────────────────────────────
        # 좌측: 설정 영역 (스크롤 가능)
        # ───────────────────────────────────────────────────────────
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")

        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: white;")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(12)
        settings_layout.setContentsMargins(0, 0, 10, 0)

        # 이미지 사용 여부 그룹
        use_group = QGroupBox("이미지 사용")
        self.apply_left_aligned_group_style(use_group)
        use_layout = QVBoxLayout(use_group)
        use_layout.setSpacing(10)

        use_row = QHBoxLayout()
        use_row.addWidget(QLabel("고정 이미지:"))

        self.image_count_combo = QComboBox()
        self.image_count_combo.addItems(["사용 안함", "1개 사용"])
        current_count = self.config["images"].get("count", 0)
        if current_count not in [0, 1]:
            current_count = 0
        self.image_count_combo.setCurrentIndex(current_count)
        self.image_count_combo.currentIndexChanged.connect(self.update_image_items)
        use_row.addWidget(self.image_count_combo)
        use_row.addStretch()
        use_layout.addLayout(use_row)

        use_info = QLabel("모든 인쇄물에 공통으로 적용될 고정 이미지를 설정합니다.\n(예: 로고, 워터마크 등)")
        use_info.setStyleSheet("color: #888; font-size: 10px;")
        use_layout.addWidget(use_info)

        settings_layout.addWidget(use_group)

        # 이미지 항목 컨테이너
        self.image_items_container = QWidget()
        self.image_items_layout = QVBoxLayout(self.image_items_container)
        self.image_items_layout.setContentsMargins(0, 0, 0, 0)
        self.image_items_layout.setSpacing(12)

        self.image_item_fields = []
        self.update_image_items(current_count)

        settings_layout.addWidget(self.image_items_container)
        settings_layout.addStretch()

        settings_scroll.setWidget(settings_widget)
        main_layout.addWidget(settings_scroll, 3)

        # ───────────────────────────────────────────────────────────
        # 우측: 미리보기 영역
        # ───────────────────────────────────────────────────────────
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setSpacing(10)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("인쇄물 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_group_layout = QVBoxLayout(preview_group)
        preview_group_layout.setSpacing(10)

        # 미리보기 라벨
        self.image_preview_label = DraggablePreviewLabel()
        self.image_preview_label.position_changed.connect(self._on_image_position_changed)
        self.image_preview_label.setFixedSize(280, 280)
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setStyleSheet("""
            border: 1px solid #ccc;
            background-color: #ffffff;
            border-radius: 6px;
        """)
        preview_group_layout.addWidget(self.image_preview_label, 0, Qt.AlignCenter)


        preview_layout.addWidget(preview_group)
        preview_layout.addStretch()

        main_layout.addWidget(preview_widget, 2)

        self.sub_tabs.addTab(tab, "🖼️ 고정 이미지")

    # ═══════════════════════════════════════════════════════════════
    # 이미지 설정 UI
    # ═══════════════════════════════════════════════════════════════
    def update_image_items(self, count):
        """이미지 항목 UI 업데이트"""
        self.config["images"]["count"] = count

        # 기존 위젯 제거
        for i in reversed(range(self.image_items_layout.count())):
            item = self.image_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.image_item_fields = []

        if count == 1:
            item_data = self.config["images"]["items"][0] if self.config["images"]["items"] else {
                "filename": "", "x": 0, "y": 0, "width": 300, "height": 300
            }

            # 이미지 설정 그룹
            settings_group = QGroupBox("이미지 설정")
            self.apply_left_aligned_group_style(settings_group)
            settings_group_layout = QVBoxLayout(settings_group)
            settings_group_layout.setSpacing(10)

            item_widget, item_fields = self._create_image_item_ui(item_data)
            settings_group_layout.addWidget(item_widget)

            self.image_items_layout.addWidget(settings_group)
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

        # 위치 & 크기 + 버튼 (가로 배치)
        pos_btn_layout = QHBoxLayout()
        pos_btn_layout.setSpacing(10)

        position_size = PositionSizeInput()
        position_size.set_values(
            x=item_data.get("x", 0),
            y=item_data.get("y", 0),
            width=item_data.get("width", 300),
            height=item_data.get("height", 300)
        )
        position_size.value_changed.connect(self.update_card_preview)
        pos_btn_layout.addWidget(position_size)
        item_fields["position_size"] = position_size

        # 배치 버튼 4개 (세로로 2x2 그리드)
        btn_grid = QGridLayout()
        btn_grid.setSpacing(4)

        image_btns = [
            ("채우기", self._fill_image_frame),
            ("가운데", self._center_image_frame),
            ("넓이맞춤", self._fit_image_width),
            ("높이맞춤", self._fit_image_height),
        ]

        for idx, (label, handler) in enumerate(image_btns):
            btn = QPushButton(label)
            btn.setFixedSize(60, 28)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                }
            """)
            btn.clicked.connect(handler)
            row = idx // 2
            col = idx % 2
            btn_grid.addWidget(btn, row, col)

        pos_btn_layout.addLayout(btn_grid)
        pos_btn_layout.addStretch()
        layout.addLayout(pos_btn_layout)

        # 인쇄 버튼
        print_group = QGroupBox("테스트 인쇄")
        self.apply_left_aligned_group_style(print_group)
        print_group_layout = QVBoxLayout(print_group)

        print_layout = QHBoxLayout()
        print_layout.addWidget(QLabel("매수:"))
        self.print_count_edit = NumberLineEdit()
        self.print_count_edit.setFixedWidth(60)
        self.print_count_edit.setValue(1)
        print_layout.addWidget(self.print_count_edit)

        self.print_button = QPushButton("🖨️ 인쇄")
        self.print_button.setFixedHeight(32)
        self.print_button.clicked.connect(self._on_print_button_clicked)
        print_layout.addWidget(self.print_button)
        print_layout.addStretch()
        print_group_layout.addLayout(print_layout)

        layout.addWidget(print_group)

        return widget, item_fields

    def on_browse_image(self, filename_edit):
        source_path, _ = QFileDialog.getOpenFileName(self, "이미지 파일 선택", "", "Image Files (*.png *.jpg *.jpeg *.gif)")
        if source_path:
            base_path = get_resources_base_path()
            destination_dir = os.path.join(base_path, "resources")
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
        base_path = get_resources_base_path()
        image_path = os.path.join(base_path, "resources", filename) if filename else ""
        if filename and os.path.exists(image_path):
            overlay_pixmap = QPixmap(image_path)

        image_rect = QRect(x, y, width, height)
        self.image_preview_label.set_card_border(True)  # 카드 테두리 표시
        self.image_preview_label.update_preview(card_pixmap, image_rect, overlay_pixmap)
        self.request_real_time_update()

    # ═══════════════════════════════════════════════════════════════
    # 서버 등록 기능
    # ═══════════════════════════════════════════════════════════════
    def _on_register_clicked(self):
        """서버 등록 버튼 클릭"""
        event_name = self.app_name_edit.text().strip()
        if not event_name:
            QMessageBox.warning(self, "입력 오류", "행사명을 입력해주세요.")
            return

        kiosk_count = self.kiosk_count_spin.value()
        expired_at = self.expire_date_edit.dateTime().toString("yyyy-MM-ddTHH:mm:ss")

        # resources 폴더 경로 (EXE/개발 모드 모두 지원)
        base_path = get_resources_base_path()
        resources_dir = os.path.join(base_path, "resources")

        # UI 비활성화
        self.register_btn.setEnabled(False)
        self.register_progress.setVisible(True)
        self.register_progress.setValue(0)

        # 백그라운드 워커 시작
        self.upload_worker = UploadWorker(
            event_name=event_name,
            kiosk_count=kiosk_count,
            expired_at=expired_at,
            config=self.config,
            resources_dir=resources_dir
        )
        self.upload_worker.progress.connect(self._on_upload_progress)
        self.upload_worker.finished.connect(self._on_upload_finished)
        self.upload_worker.start()

    def _on_upload_progress(self, percent, message):
        """업로드 진행 상태"""
        self.register_progress.setValue(percent)
        self.window().statusBar().showMessage(message)

    def _on_upload_finished(self, success, result):
        """업로드 완료"""
        self.register_btn.setEnabled(True)
        self.register_progress.setVisible(False)

        if success:
            codes_text = f"✅ 등록 완료! (이벤트: {result.get('event_number', '')})\n"
            for code_info in result.get('activation_codes', []):
                codes_text += f"키오스크 {code_info['kiosk_id']}: {code_info['code']}\n"
            self.activation_result.setText(codes_text)
            self.window().statusBar().showMessage("서버 등록 완료!", 5000)
            QMessageBox.information(self, "등록 완료",
                f"행사 '{result.get('event_name')}'이(가) 등록되었습니다.\n"
                f"키오스크 {len(result.get('activation_codes', []))}대 라이선스 발급!")
        else:
            error_msg = result.get('error', '알 수 없는 오류')
            self.activation_result.setText(f"❌ 등록 실패: {error_msg}")
            self.window().statusBar().showMessage(f"등록 실패: {error_msg}", 5000)
            QMessageBox.critical(self, "등록 실패", f"서버 등록에 실패했습니다.\n{error_msg}")

    def _copy_activation_codes(self):
        """활성화 코드 복사"""
        from PySide6.QtWidgets import QApplication
        text = self.activation_result.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.window().statusBar().showMessage("클립보드에 복사되었습니다.", 3000)

    # ═══════════════════════════════════════════════════════════════
    # 이벤트 핸들러
    # ═══════════════════════════════════════════════════════════════
    def on_screen_order_changed(self):
        self.config["screen_order"] = sorted([
            cb.property("screen_index")
            for cb in self.screen_order_checkboxes
            if cb.isChecked()
        ])
        # 화면 순서 변경 시에는 탭 활성화 상태만 업데이트 (행사명 등 초기화 방지)
        self.screen_order_changed.emit()

    def _fill_image_frame(self):
        if not self.image_item_fields:
            return

        is_portrait = self.card_portrait_radio.isChecked() if self.card_portrait_radio else True
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        fields = self.image_item_fields[0]
        position_size = fields["position_size"]
        position_size.set_values(x=0, y=0, width=card_width, height=card_height)
        self.request_real_time_update()

    def _center_image_frame(self):
        if not self.image_item_fields:
            return

        is_portrait = self.card_portrait_radio.isChecked() if self.card_portrait_radio else True
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

    def _fit_image_width(self):
        """이미지 넓이만 카드 넓이에 맞춤 (높이 유지)"""
        if not self.image_item_fields:
            return

        is_portrait = self.card_portrait_radio.isChecked() if self.card_portrait_radio else True
        card_width = 636 if is_portrait else 1012

        fields = self.image_item_fields[0]
        position_size = fields["position_size"]
        position_size.set_x(0)
        position_size.set_width(card_width)
        self.request_real_time_update()

    def _fit_image_height(self):
        """이미지 높이만 카드 높이에 맞춤 (넓이 유지)"""
        if not self.image_item_fields:
            return

        is_portrait = self.card_portrait_radio.isChecked() if self.card_portrait_radio else True
        card_height = 1012 if is_portrait else 636

        fields = self.image_item_fields[0]
        position_size = fields["position_size"]
        position_size.set_y(0)
        position_size.set_height(card_height)
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
        new_width = self.screen_width_edit.value()
        new_height = self.screen_height_edit.value()

        self.config["screen_size"]["width"] = new_width
        self.config["screen_size"]["height"] = new_height

        # 모든 화면 좌표 기반 설정 조정
        self._adjust_screen_coordinates(new_width, new_height)

        self.config_changed.emit()

    def _adjust_screen_coordinates(self, max_width: int, max_height: int):
        """모니터 크기에 맞게 모든 화면 좌표 설정 조정"""

        def clamp_rect(cfg: dict, x_key="x", y_key="y", w_key="width", h_key="height"):
            """x, y, width, height 값을 모니터 범위 내로 조정"""
            if x_key in cfg:
                cfg[x_key] = max(0, min(cfg[x_key], max_width - 10))
            if y_key in cfg:
                cfg[y_key] = max(0, min(cfg[y_key], max_height - 10))
            if w_key in cfg:
                x_val = cfg.get(x_key, 0)
                cfg[w_key] = min(cfg[w_key], max_width - x_val)
            if h_key in cfg:
                y_val = cfg.get(y_key, 0)
                cfg[h_key] = min(cfg[h_key], max_height - y_val)

        def clamp_position(cfg: dict, x_key="x", y_key="y"):
            """x, y 위치만 조정 (크기 없는 경우)"""
            if x_key in cfg:
                cfg[x_key] = max(0, min(cfg[x_key], max_width - 10))
            if y_key in cfg:
                cfg[y_key] = max(0, min(cfg[y_key], max_height - 10))

        # 1. 키보드 설정
        if "keyboard" in self.config:
            clamp_rect(self.config["keyboard"])

        # 2. 텍스트 입력창 (화면 표시용)
        if "text_input" in self.config and "items" in self.config["text_input"]:
            for item in self.config["text_input"]["items"]:
                clamp_rect(item, "screen_x", "screen_y", "screen_width", "screen_height")

        # 3. 프레임 설정
        if "frame" in self.config:
            clamp_rect(self.config["frame"])

        # 4. splash/process/complete 위치
        for screen_key in ["splash", "process", "complete"]:
            if screen_key in self.config:
                clamp_position(self.config[screen_key])

        # 5. 언어 선택 버튼
        if "language" in self.config:
            for btn_key in ["ko_button", "en_button"]:
                if btn_key in self.config["language"]:
                    clamp_rect(self.config["language"][btn_key])

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

        current_print_mode = config.get("printer", {}).get("print_mode", True)
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
            config["printer"] = {"print_mode": True, "panel_id": 1}

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
