from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QWidget, QTabWidget,
                              QDialog, QDialogButtonBox, QRadioButton, QButtonGroup, QGridLayout)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QRect, QSize
from ui.components.inputs import NumberLineEdit
from ui.components.live_preview import LivePreviewWidget
from ui.components.zoomable_preview import ZoomablePreviewWidget, DEFAULT_PREVIEW_SIZE
from ui.components.language_preview_tabs import LanguagePreviewTabs
from ui.components.position_size_input import PositionSizeInput
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# QR 화면 screen_key = "3"
QR_SCREEN_KEY = "3"

class QRTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.tab_manager = None
        self.qr_preview = None
        self.card_preview = None
        self.sub_tabs = None
        # 언어별 배경화면 필드
        self.lang_bg_fields = {"ko": {}, "en": {}}
        # 언어별 미리보기 탭 위젯
        self.lang_preview_tabs = None
        # 언어별 미리보기 선택 (라디오 버튼용)
        self._current_lang_preview = None
        self.init_ui()

    def init_ui(self):
        scroll_content_layout = self.create_tab_with_scroll()

        # ═══════════════════════════════════════════════════════════════
        # 서브 탭 위젯 (각 탭 내부에 좌측 설정 + 우측 미리보기)
        # ═══════════════════════════════════════════════════════════════
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #ffffff;
                border: 1px solid #ccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #f8f8f8;
            }
        """)

        # 탭 1: 화면 설정 (배경 + 화면 미리보기)
        self._create_screen_settings_tab()

        # 탭 2: 인쇄 설정 (QR 코드 위치, 이미지 인쇄 위치 + 카드 미리보기)
        self._create_print_settings_tab()

        scroll_content_layout.addWidget(self.sub_tabs)
        scroll_content_layout.addStretch()

        # 라디오 버튼 초기 상태 설정
        self._update_preview_radio_visibility()

        # 초기 미리보기 업데이트
        self._update_qr_preview()
        self._update_card_preview()

    # ═══════════════════════════════════════════════════════════════
    # 탭 1: 화면 설정 (좌측 설정 + 우측 화면 미리보기)
    # ═══════════════════════════════════════════════════════════════
    def _create_screen_settings_tab(self):
        """화면 설정 탭 생성 (배경화면 + QR코드 화면 위치 + 화면 미리보기)"""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(20)

        # ───────────────────────────────────────────────────────────
        # 좌측: 설정 영역
        # ───────────────────────────────────────────────────────────
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        # 배경화면 설정
        self._init_background_settings(settings_layout)

        # QR 코드 화면 위치 설정
        qr_group = QGroupBox("📊 QR 코드 화면 위치")
        self.apply_left_aligned_group_style(qr_group)
        qr_inner = QHBoxLayout(qr_group)
        qr_inner.setContentsMargins(12, 16, 12, 12)
        qr_inner.setSpacing(16)

        # 위치/크기 입력
        self.qr_position_input = PositionSizeInput()
        self.qr_position_input.set_values(
            x=self.config["qr"]["x"],
            y=self.config["qr"]["y"],
            width=self.config["qr"]["preview_width"],
            height=self.config["qr"]["preview_height"]
        )
        self.qr_position_input.value_changed.connect(self._update_qr_preview)
        qr_inner.addWidget(self.qr_position_input)

        # 빠른 정렬 버튼 (2x2 그리드)
        qr_btn_widget = QWidget()
        qr_btn_widget.setStyleSheet("background-color: transparent;")
        qr_btn_grid = QGridLayout(qr_btn_widget)
        qr_btn_grid.setContentsMargins(0, 0, 0, 0)
        qr_btn_grid.setSpacing(4)

        qr_btns = [
            ("전체", self._fill_qr_frame, "화면 전체에 맞춤"),
            ("가운데", self._center_qr_frame, "화면 중앙에 배치"),
            ("넓이맞춤", self._fit_qr_width, "화면 넓이에 맞춤"),
            ("높이맞춤", self._fit_qr_height, "화면 높이에 맞춤"),
        ]
        qr_btn_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 8px 12px;
                min-width: 60px;
            }
            QPushButton:hover { background-color: #1e88e5; }
            QPushButton:pressed { background-color: #1565c0; }
        """
        for i, (text, callback, tooltip) in enumerate(qr_btns):
            btn = QPushButton(text)
            btn.setStyleSheet(qr_btn_style)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            qr_btn_grid.addWidget(btn, i // 2, i % 2)
        qr_inner.addStretch(1)
        qr_inner.addWidget(qr_btn_widget)
        qr_inner.addStretch(1)

        settings_layout.addWidget(qr_group)
        settings_layout.addStretch()

        tab_layout.addWidget(settings_widget, 1)

        # ───────────────────────────────────────────────────────────
        # 우측: 화면 미리보기 (언어별 탭)
        # ───────────────────────────────────────────────────────────
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self._init_language_preview_tabs(preview_layout)
        preview_layout.addStretch()

        tab_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab_widget, "화면 설정")

    # ═══════════════════════════════════════════════════════════════
    # 탭 2: 인쇄 설정 (좌측 설정 + 우측 카드 미리보기)
    # ═══════════════════════════════════════════════════════════════
    def _create_print_settings_tab(self):
        """인쇄 설정 탭 생성 (QR 이미지 인쇄 위치 + 카드 미리보기)"""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(20)

        # ───────────────────────────────────────────────────────────
        # 좌측: 설정 영역
        # ───────────────────────────────────────────────────────────
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        # QR 이미지 인쇄 위치 설정
        qr_uploaded_group = QGroupBox("🖨️ QR 이미지 인쇄 위치")
        self.apply_left_aligned_group_style(qr_uploaded_group)
        qr_uploaded_layout = QVBoxLayout(qr_uploaded_group)

        self.qr_uploaded_input = PositionSizeInput()
        self.qr_uploaded_input.set_values(
            x=self.config["qr_uploaded_image"]["x"],
            y=self.config["qr_uploaded_image"]["y"],
            width=self.config["qr_uploaded_image"]["width"],
            height=self.config["qr_uploaded_image"]["height"]
        )
        self.qr_uploaded_input.value_changed.connect(self._update_card_preview)
        qr_uploaded_layout.addWidget(self.qr_uploaded_input)

        # 빠른 정렬 버튼 (1행 4열)
        qr_print_btn_layout = QHBoxLayout()
        qr_print_btn_layout.setContentsMargins(0, 4, 0, 0)
        qr_print_btn_layout.setSpacing(4)
        qr_print_btn_layout.addStretch(1)

        for label, callback in [("전체", self._fill_image_frame),
                                 ("가운데", self._center_image_frame),
                                 ("넓이맞춤", self._fit_image_width),
                                 ("높이맞춤", self._fit_image_height)]:
            btn = QPushButton(label)
            btn.setFixedSize(80, 26)
            btn.clicked.connect(callback)
            qr_print_btn_layout.addWidget(btn)

        qr_print_btn_layout.addStretch(1)
        qr_uploaded_layout.addLayout(qr_print_btn_layout)

        settings_layout.addWidget(qr_uploaded_group)
        settings_layout.addStretch()

        tab_layout.addWidget(settings_widget, 1)

        # ───────────────────────────────────────────────────────────
        # 우측: 카드 인쇄 미리보기
        # ───────────────────────────────────────────────────────────
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self._init_card_preview(preview_layout)
        preview_layout.addStretch()

        tab_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab_widget, "인쇄 설정")

    # ═══════════════════════════════════════════════════════════════
    # 배경 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_background_settings(self, parent_layout):
        """배경 설정 그룹"""
        # 그룹박스 헤더 (타이틀 + ? 버튼)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 5)
        header_layout.setSpacing(8)

        title_label = QLabel("배경 설정")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)

        help_btn = self.create_help_button("배경화면 설정 안내")
        help_btn.clicked.connect(self._show_bg_help_dialog)
        header_layout.addWidget(help_btn)
        header_layout.addStretch()

        parent_layout.addWidget(header_widget)

        # 배경 설정 내용 그룹
        bg_group = QGroupBox()
        self.apply_left_aligned_group_style(bg_group)
        bg_form = QFormLayout(bg_group)
        bg_form.setSpacing(8)

        # 라벨 너비 고정
        LABEL_WIDTH = 80

        # 기본 배경화면 행
        basic_label = QLabel("기본:")
        basic_label.setFixedWidth(LABEL_WIDTH)
        bg_row = QHBoxLayout()
        saved_bg = FileHandler.get_background_display_name(QR_SCREEN_KEY)
        self.qr_bg_edit = QLineEdit(saved_bg)
        self.qr_bg_edit.setReadOnly(True)
        self.qr_bg_edit.setPlaceholderText("배경화면 없음")
        self.qr_bg_edit.textChanged.connect(self._update_qr_preview)
        bg_row.addWidget(self.qr_bg_edit, 1)

        browse_button = QPushButton("찾기...")
        browse_button.setFixedWidth(60)
        browse_button.clicked.connect(self._browse_and_update_background)
        bg_row.addWidget(browse_button)

        reset_button = QPushButton("초기화")
        reset_button.setFixedWidth(60)
        reset_button.setToolTip("배경화면을 삭제합니다")
        reset_button.clicked.connect(self._reset_background)
        bg_row.addWidget(reset_button)
        bg_form.addRow(basic_label, bg_row)

        # 한국어 배경화면
        ko_label = QLabel("🇰🇷 한국어:")
        ko_label.setFixedWidth(LABEL_WIDTH)
        ko_bg_layout = QHBoxLayout()
        saved_ko_bg = FileHandler.get_background_display_name(QR_SCREEN_KEY, lang="ko")
        self.ko_bg_edit = QLineEdit(saved_ko_bg)
        self.ko_bg_edit.setReadOnly(True)
        self.ko_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        ko_bg_layout.addWidget(self.ko_bg_edit, 1)
        self.lang_bg_fields["ko"]["background"] = self.ko_bg_edit
        ko_browse_btn = QPushButton("찾기...")
        ko_browse_btn.setFixedWidth(60)
        ko_browse_btn.clicked.connect(lambda: self._browse_lang_bg("ko"))
        ko_bg_layout.addWidget(ko_browse_btn)
        ko_reset_btn = QPushButton("초기화")
        ko_reset_btn.setFixedWidth(60)
        ko_reset_btn.clicked.connect(lambda: self._reset_lang_bg("ko"))
        ko_bg_layout.addWidget(ko_reset_btn)
        bg_form.addRow(ko_label, ko_bg_layout)

        # 영어 배경화면
        en_label = QLabel("🇺🇸 English:")
        en_label.setFixedWidth(LABEL_WIDTH)
        en_bg_layout = QHBoxLayout()
        saved_en_bg = FileHandler.get_background_display_name(QR_SCREEN_KEY, lang="en")
        self.en_bg_edit = QLineEdit(saved_en_bg)
        self.en_bg_edit.setReadOnly(True)
        self.en_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        en_bg_layout.addWidget(self.en_bg_edit, 1)
        self.lang_bg_fields["en"]["background"] = self.en_bg_edit
        en_browse_btn = QPushButton("찾기...")
        en_browse_btn.setFixedWidth(60)
        en_browse_btn.clicked.connect(lambda: self._browse_lang_bg("en"))
        en_bg_layout.addWidget(en_browse_btn)
        en_reset_btn = QPushButton("초기화")
        en_reset_btn.setFixedWidth(60)
        en_reset_btn.clicked.connect(lambda: self._reset_lang_bg("en"))
        en_bg_layout.addWidget(en_reset_btn)
        bg_form.addRow(en_label, en_bg_layout)

        # 구분선
        from PySide6.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("margin: 8px 0;")
        bg_form.addRow(separator)

        # 미리보기 언어 선택 라디오 버튼
        preview_label = QLabel("미리보기:")
        preview_label.setFixedWidth(LABEL_WIDTH)
        preview_radio_layout = QHBoxLayout()
        preview_radio_layout.setSpacing(15)

        self.preview_lang_group = QButtonGroup(self)
        self.radio_default = QRadioButton("기본")
        self.radio_ko = QRadioButton("한국어")
        self.radio_en = QRadioButton("English")
        self.radio_default.setChecked(True)

        self.preview_lang_group.addButton(self.radio_default, 0)
        self.preview_lang_group.addButton(self.radio_ko, 1)
        self.preview_lang_group.addButton(self.radio_en, 2)

        self.preview_lang_group.buttonClicked.connect(self._on_preview_lang_changed)

        preview_radio_layout.addWidget(self.radio_default)
        preview_radio_layout.addWidget(self.radio_ko)
        preview_radio_layout.addWidget(self.radio_en)
        preview_radio_layout.addStretch()
        bg_form.addRow(preview_label, preview_radio_layout)

        parent_layout.addWidget(bg_group)

    # ═══════════════════════════════════════════════════════════════
    # 미리보기 영역
    # ═══════════════════════════════════════════════════════════════
    def _init_language_preview_tabs(self, parent_layout):
        """화면 미리보기 초기화 (단일 미리보기)"""
        group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(group)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("QR 코드 영역을 드래그하여 위치/크기 조절 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        layout.addWidget(desc)

        # 단일 미리보기 위젯 + 확대/축소
        self.qr_preview = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.qr_preview.position_changed.connect(self._on_qr_position_changed)
        self.qr_preview.size_changed.connect(self._on_qr_size_changed)
        self._zoomable_qr_preview = ZoomablePreviewWidget(self.qr_preview)
        layout.addWidget(self._zoomable_qr_preview, 0, Qt.AlignCenter)

        parent_layout.addWidget(group)

    def _init_card_preview(self, parent_layout):
        """QR 이미지 인쇄 미리보기 영역 초기화"""
        preview_group = QGroupBox("QR 이미지 인쇄 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("이미지 영역을 드래그하여 위치 조절 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_layout.addWidget(desc)

        self.card_preview = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.card_preview.position_changed.connect(self._on_image_position_changed)
        self.card_preview.size_changed.connect(self._on_image_size_changed)
        self._zoomable_card_preview = ZoomablePreviewWidget(self.card_preview)
        preview_layout.addWidget(self._zoomable_card_preview, 0, Qt.AlignCenter)

        parent_layout.addWidget(preview_group)

    def _browse_and_update_background(self):
        """배경화면 파일 선택 및 업데이트"""
        FileHandler.browse_background_file(self, self.qr_bg_edit, QR_SCREEN_KEY)
        saved_bg = FileHandler.get_background_display_name(QR_SCREEN_KEY)
        self.qr_bg_edit.setText(saved_bg)
        self._update_qr_preview()

    def _reset_background(self):
        """배경화면 초기화 (삭제)"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "배경화면 초기화",
            "이 화면의 배경화면을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(QR_SCREEN_KEY)
            self.qr_bg_edit.setText("")
            self._update_qr_preview()

    # ==================== 배경화면 도움말 및 언어별 배경화면 ====================
    def _show_bg_help_dialog(self):
        """배경화면 도움말 다이얼로그 표시"""
        dialog = QDialog(self)
        dialog.setWindowTitle("배경화면 설정 안내")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)

        info_text = QLabel(
            "<b>📌 배경화면 설정 안내</b><br><br>"
            "• <b>배경화면</b>: 기본 배경화면입니다. 언어별 배경화면이 없을 경우 사용됩니다.<br><br>"
            "• <b>🇰🇷 한국어</b>: 사용자가 한국어를 선택했을 때 표시되는 배경화면입니다.<br><br>"
            "• <b>🇺🇸 English</b>: 사용자가 영어를 선택했을 때 표시되는 배경화면입니다.<br><br>"
            "<i>※ 언어별 배경화면이 설정되지 않으면 기본 배경화면이 사용됩니다.</i>"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 10px;")
        layout.addWidget(info_text)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec()

    def _browse_lang_bg(self, lang_code: str):
        """언어별 배경화면 파일 선택"""
        bg_edit = self.lang_bg_fields[lang_code].get("background")
        if bg_edit:
            FileHandler.browse_background_file(self, bg_edit, QR_SCREEN_KEY, lang=lang_code)
            saved_bg = FileHandler.get_background_display_name(QR_SCREEN_KEY, lang=lang_code)
            bg_edit.setText(saved_bg)
            self._update_qr_preview()

    def _reset_lang_bg(self, lang_code: str):
        """언어별 배경화면 초기화"""
        from PySide6.QtWidgets import QMessageBox
        lang_name = "한국어" if lang_code == "ko" else "영어"
        reply = QMessageBox.question(
            self, f"{lang_name} 배경화면 초기화",
            f"{lang_name} QR 화면의 배경화면을 삭제하시겠습니까?\n삭제 시 기본 배경화면이 사용됩니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(QR_SCREEN_KEY, lang=lang_code)
            bg_edit = self.lang_bg_fields[lang_code].get("background")
            if bg_edit:
                bg_edit.setText("")
            self._update_qr_preview()

    def _fill_qr_frame(self):
        """QR 코드를 모니터 크기에 맞게 채웁니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.qr_position_input.set_values(x=0, y=0, width=monitor_width, height=monitor_height)
        self._update_qr_preview()

    def _center_qr_frame(self):
        """QR 코드를 모니터의 중앙에 정렬합니다."""
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        qr_width = self.qr_position_input.get_width()
        qr_height = self.qr_position_input.get_height()

        center_x = (monitor_width - qr_width) // 2
        center_y = (monitor_height - qr_height) // 2

        self.qr_position_input.set_x(center_x)
        self.qr_position_input.set_y(center_y)
        self._update_qr_preview()

    def _fit_qr_width(self):
        """QR 코드 넓이를 모니터 넓이에 맞춥니다 (높이 유지)."""
        try:
            monitor_width = self.config["screen_size"]["width"]
        except KeyError:
            monitor_width = 1080

        self.qr_position_input.set_x(0)
        self.qr_position_input.set_width(monitor_width)
        self._update_qr_preview()

    def _fit_qr_height(self):
        """QR 코드 높이를 모니터 높이에 맞춥니다 (넓이 유지)."""
        try:
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_height = 1920

        self.qr_position_input.set_y(0)
        self.qr_position_input.set_height(monitor_height)
        self._update_qr_preview()

    def _fill_image_frame(self):
        """업로드된 이미지를 카드 크기에 맞게 채웁니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        self.qr_uploaded_input.set_values(x=0, y=0, width=card_width, height=card_height)
        self._update_card_preview()

    def _center_image_frame(self):
        """업로드된 이미지를 카드의 중앙에 정렬합니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        image_width = self.qr_uploaded_input.get_width()
        image_height = self.qr_uploaded_input.get_height()

        center_x = (card_width - image_width) // 2
        center_y = (card_height - image_height) // 2

        self.qr_uploaded_input.set_x(center_x)
        self.qr_uploaded_input.set_y(center_y)
        self._update_card_preview()

    def _fit_image_width(self):
        """이미지 넓이만 카드 넓이에 맞춥니다 (높이 유지)."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012

        self.qr_uploaded_input.set_x(0)
        self.qr_uploaded_input.set_width(card_width)
        self._update_card_preview()

    def _fit_image_height(self):
        """이미지 높이만 카드 높이에 맞춥니다 (넓이 유지)."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_height = 1012 if is_portrait else 636

        self.qr_uploaded_input.set_y(0)
        self.qr_uploaded_input.set_height(card_height)
        self._update_card_preview()

    def _on_qr_position_changed(self, element_id, x, y):
        """드래그로 QR 코드 위치 변경 시 호출"""
        if element_id == "qr_area":
            self.qr_position_input.block_all_signals(True)
            self.qr_position_input.set_x(x)
            self.qr_position_input.set_y(y)
            self.qr_position_input.block_all_signals(False)
            self.request_real_time_update()

    def _on_image_position_changed(self, element_id, x, y):
        """드래그로 이미지 위치 변경 시 호출"""
        if element_id == "image_area":
            self.qr_uploaded_input.block_all_signals(True)
            self.qr_uploaded_input.set_x(x)
            self.qr_uploaded_input.set_y(y)
            self.qr_uploaded_input.block_all_signals(False)
            self.request_real_time_update()

    def _on_qr_size_changed(self, element_id, x, y, width, height):
        """드래그로 QR 코드 크기 변경 시 호출"""
        if element_id == "qr_area":
            self.qr_position_input.block_all_signals(True)
            self.qr_position_input.set_values(x=x, y=y, width=width, height=height)
            self.qr_position_input.block_all_signals(False)
            self.request_real_time_update()

    def _on_image_size_changed(self, element_id, x, y, width, height):
        """드래그로 이미지 크기 변경 시 호출"""
        if element_id == "image_area":
            self.qr_uploaded_input.block_all_signals(True)
            self.qr_uploaded_input.set_values(x=x, y=y, width=width, height=height)
            self.qr_uploaded_input.block_all_signals(False)
            self.request_real_time_update()

    def _update_qr_preview(self):
        """QR 코드 화면 미리보기 업데이트"""
        if not self.qr_preview:
            return

        self.qr_preview.clear_elements()

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.qr_preview.set_original_size(monitor_width, monitor_height)

        # 배경 이미지 (언어 활성화 상태에 따라 처리)
        lang_enabled = self.config.get("language", {}).get("enabled", False)
        if lang_enabled:
            lang = getattr(self, '_current_lang_preview', "ko")
            if lang is None:
                lang = "ko"
            bg_path = FileHandler.resolve_background_path(QR_SCREEN_KEY, lang=lang)
        else:
            bg_path = FileHandler.resolve_background_path(QR_SCREEN_KEY, lang=None)

        self.qr_preview.set_background(bg_path, QColor("#ffffff"))
        self.qr_preview.set_card_border(True, QColor("#333333"), 2)

        # QR 코드 영역 정보
        try:
            x = self.qr_position_input.get_x()
            y = self.qr_position_input.get_y()
            width = self.qr_position_input.get_width()
            height = self.qr_position_input.get_height()
            qr_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            qr_rect = QRect(0, 0, 400, 400)

        self.qr_preview.add_element(
            "qr_area",
            qr_rect,
            color=QColor("cyan"),
            label="QR 코드",
            draggable=True,
            resizable=True
        )

        self.request_real_time_update()

    # ==================== 언어별 미리보기 라디오 버튼 ====================
    def _on_preview_lang_changed(self, button):
        """미리보기 언어 변경 시 호출"""
        if button == self.radio_default:
            self._current_lang_preview = None
        elif button == self.radio_ko:
            self._current_lang_preview = "ko"
        else:
            self._current_lang_preview = "en"
        self._update_qr_preview()

    def _update_preview_radio_visibility(self):
        """언어 버튼 활성화 상태에 따라 라디오 버튼 활성화/비활성화 (전체 표시 유지)"""
        lang_enabled = self.config.get("language", {}).get("enabled", False)

        # 모든 라디오 버튼 항상 표시
        self.radio_default.show()
        self.radio_ko.show()
        self.radio_en.show()

        if lang_enabled:
            # 언어 활성화: 기본 비활성화, 한국어/영어 활성화
            self.radio_default.setEnabled(False)
            self.radio_ko.setEnabled(True)
            self.radio_en.setEnabled(True)
            # 기본이 선택되어 있으면 한국어로 변경
            if self.radio_default.isChecked():
                self.radio_ko.setChecked(True)
            # 현재 선택된 라디오박스에 맞게 _current_lang_preview 동기화
            if self.radio_ko.isChecked():
                self._current_lang_preview = "ko"
            elif self.radio_en.isChecked():
                self._current_lang_preview = "en"
        else:
            # 언어 비활성화: 기본 활성화, 한국어/영어 비활성화
            self.radio_default.setEnabled(True)
            self.radio_ko.setEnabled(False)
            self.radio_en.setEnabled(False)
            # 한국어/영어가 선택되어 있으면 기본으로 변경
            if not self.radio_default.isChecked():
                self.radio_default.setChecked(True)
            self._current_lang_preview = None

    def _update_card_preview(self):
        """카드 인쇄 미리보기 업데이트"""
        if not self.card_preview:
            return

        # 카드 크기
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        self.card_preview.set_original_size(card_width, card_height)
        self.card_preview.set_background_color(QColor("white"))

        # 카드 테두리 표시 (인쇄 영역 경계)
        self.card_preview.set_card_border(True, QColor("#333333"), 3)

        # 이미지 영역 추가
        try:
            x = self.qr_uploaded_input.get_x()
            y = self.qr_uploaded_input.get_y()
            width = self.qr_uploaded_input.get_width()
            height = self.qr_uploaded_input.get_height()
            image_rect = QRect(x, y, width, height)
        except (AttributeError, KeyError):
            image_rect = QRect(0, 0, 300, 300)

        self.card_preview.add_element(
            "image_area",
            image_rect,
            color=QColor("red"),
            label="QR 이미지",
            draggable=True
        )

        self.request_real_time_update()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        self.qr_bg_edit.setText(config["qr"].get("background", ""))

        # QR 코드 위치/크기 업데이트
        self.qr_position_input.set_values(
            x=config["qr"]["x"],
            y=config["qr"]["y"],
            width=config["qr"]["preview_width"],
            height=config["qr"]["preview_height"]
        )

        # 이미지 인쇄 위치/크기 업데이트
        self.qr_uploaded_input.set_values(
            x=config["qr_uploaded_image"]["x"],
            y=config["qr_uploaded_image"]["y"],
            width=config["qr_uploaded_image"]["width"],
            height=config["qr_uploaded_image"]["height"]
        )

        # 언어 활성화 상태에 따라 라디오 버튼 업데이트
        self._update_preview_radio_visibility()

        self._update_qr_preview()
        self._update_card_preview()

    def update_config(self, config):
        """UI 값을 config에 반영"""
        config["qr"]["background"] = self.qr_bg_edit.text()

        # QR 코드 위치/크기 저장
        config["qr"]["x"] = self.qr_position_input.get_x()
        config["qr"]["y"] = self.qr_position_input.get_y()
        config["qr"]["preview_width"] = self.qr_position_input.get_width()
        config["qr"]["preview_height"] = self.qr_position_input.get_height()

        # 이미지 인쇄 위치/크기 저장
        config["qr_uploaded_image"]["x"] = self.qr_uploaded_input.get_x()
        config["qr_uploaded_image"]["y"] = self.qr_uploaded_input.get_y()
        config["qr_uploaded_image"]["width"] = self.qr_uploaded_input.get_width()
        config["qr_uploaded_image"]["height"] = self.qr_uploaded_input.get_height()
