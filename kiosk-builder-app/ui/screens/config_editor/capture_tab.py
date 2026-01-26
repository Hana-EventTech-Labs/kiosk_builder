from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
                              QLabel, QLineEdit, QPushButton, QSpinBox, QWidget, QComboBox, QFrame,
                              QDialog, QDialogButtonBox, QTabWidget, QScrollArea)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect, QSize
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import LivePreviewWidget
from ui.components.zoomable_preview import ZoomablePreviewWidget, DEFAULT_PREVIEW_SIZE
from ui.components.language_preview_tabs import LanguagePreviewTabs
from ui.components.collapsible_group import CollapsibleGroupBox
from ui.components.position_size_input import PositionSizeInput
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# 카메라/촬영 화면 screen_key = "1"
CAPTURE_SCREEN_KEY = "1"


class CaptureTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.screen_preview = None
        self.screen_preview_camera_area = None  # 카메라 영역 탭용
        self.screen_preview_count = None  # 카메라 카운트 탭용
        self.card_preview = None
        self.sub_tabs = None
        # 언어별 배경화면 필드
        self.lang_bg_fields = {"ko": {}, "en": {}}
        # 미리보기 언어 선택 (라디오 버튼)
        self._current_lang_preview = None
        self.init_ui()

    def init_ui(self):
        scroll_content_layout = self.create_tab_with_scroll()

        # ═══════════════════════════════════════════════════════════════
        # 서브 탭 위젯 생성
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
                padding: 8px 20px;
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
        scroll_content_layout.addWidget(self.sub_tabs)

        # 탭 1: 화면 설정 (배경 설정)
        self._create_screen_settings_tab()

        # 탭 2: 카메라 영역 (카메라 영역 + 선택 영역)
        self._create_camera_area_tab()

        # 탭 3: 카메라 카운트
        self._create_camera_count_tab()

        # 탭 4: 인쇄 설정
        self._create_print_settings_tab()

        scroll_content_layout.addStretch()

        # 라디오박스 활성화 상태 먼저 설정 (미리보기 전에 호출해야 함)
        self._update_preview_radio_visibility()
        self._update_screen_preview()
        self._update_card_preview()

    # ═══════════════════════════════════════════════════════════════
    # 탭 1: 화면 설정 (배경 설정만)
    # ═══════════════════════════════════════════════════════════════
    def _create_screen_settings_tab(self):
        """화면 설정 탭 생성 - 배경 설정만 포함"""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(20)

        # 좌측: 설정 영역 (스크롤)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")

        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: white;")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 10, 0)
        settings_layout.setSpacing(12)

        # 배경 설정만
        self._init_camera_settings(settings_layout)

        settings_layout.addStretch()
        settings_scroll.setWidget(settings_widget)
        tab_layout.addWidget(settings_scroll, 1)

        # 우측: 화면 미리보기 (언어별 탭 - 좌측 배치)
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self._init_language_preview_tabs(preview_layout)
        preview_layout.addStretch()

        tab_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab_widget, "화면 설정")

    # ═══════════════════════════════════════════════════════════════
    # 탭 2: 카메라 영역 (카메라 영역 + 선택 영역)
    # ═══════════════════════════════════════════════════════════════
    def _create_camera_area_tab(self):
        """카메라 영역 탭 생성 - 카메라 영역 + 선택 영역 포함"""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(20)

        # 좌측: 설정 영역 (스크롤)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")

        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: white;")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 10, 0)
        settings_layout.setSpacing(12)

        # 카메라 영역 및 선택 영역
        self._init_frame_settings(settings_layout)

        settings_layout.addStretch()
        settings_scroll.setWidget(settings_widget)
        tab_layout.addWidget(settings_scroll, 1)

        # 우측: 화면 미리보기 (2번째 인스턴스)
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self._init_screen_preview_for_camera_area(preview_layout)
        preview_layout.addStretch()

        tab_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab_widget, "카메라 영역")

    # ═══════════════════════════════════════════════════════════════
    # 탭 2: 인쇄 설정
    # ═══════════════════════════════════════════════════════════════
    def _create_print_settings_tab(self):
        """인쇄 설정 탭 생성"""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(20)

        # 좌측: 설정 영역
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        # 베이스 카드 설정
        self._init_base_card_settings(settings_layout)

        # 사진 위치 설정
        self._init_photo_settings(settings_layout)

        settings_layout.addStretch()
        tab_layout.addWidget(settings_widget, 1)

        # 우측: 카드 미리보기
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self._init_card_preview(preview_layout)
        preview_layout.addStretch()

        tab_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab_widget, "인쇄 설정")

    # ═══════════════════════════════════════════════════════════════
    # 1. 배경 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_camera_settings(self, parent_layout):
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
        camera_group = QGroupBox()
        self.apply_left_aligned_group_style(camera_group)
        bg_form = QFormLayout(camera_group)
        bg_form.setSpacing(8)

        # 라벨 너비 고정
        LABEL_WIDTH = 80

        # 배경화면 (기본)
        basic_label = QLabel("기본:")
        basic_label.setFixedWidth(LABEL_WIDTH)
        bg_layout = QHBoxLayout()
        saved_bg = FileHandler.get_background_display_name(CAPTURE_SCREEN_KEY)
        self.capture_bg_edit = QLineEdit(saved_bg)
        self.capture_bg_edit.setReadOnly(True)
        self.capture_bg_edit.setPlaceholderText("배경화면 없음")
        self.capture_bg_edit.textChanged.connect(self._update_screen_preview)
        bg_layout.addWidget(self.capture_bg_edit, 1)
        browse_btn = QPushButton("찾기...")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(lambda: self._browse_and_update_background())
        bg_layout.addWidget(browse_btn)
        reset_btn = QPushButton("초기화")
        reset_btn.setFixedWidth(60)
        reset_btn.setToolTip("배경화면을 삭제합니다")
        reset_btn.clicked.connect(self._reset_capture_background)
        bg_layout.addWidget(reset_btn)
        bg_form.addRow(basic_label, bg_layout)

        # 한국어 배경화면
        ko_label = QLabel("🇰🇷 한국어:")
        ko_label.setFixedWidth(LABEL_WIDTH)
        ko_bg_layout = QHBoxLayout()
        saved_ko_bg = FileHandler.get_background_display_name(CAPTURE_SCREEN_KEY, lang="ko")
        self.ko_bg_edit = QLineEdit(saved_ko_bg)
        self.ko_bg_edit.setReadOnly(True)
        self.ko_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        self.ko_bg_edit.textChanged.connect(self._update_screen_preview)
        ko_bg_layout.addWidget(self.ko_bg_edit, 1)
        self.lang_bg_fields["ko"]["background"] = self.ko_bg_edit
        ko_browse_btn = QPushButton("찾기...")
        ko_browse_btn.setFixedWidth(60)
        ko_browse_btn.clicked.connect(lambda: self._browse_lang_background("ko"))
        ko_bg_layout.addWidget(ko_browse_btn)
        ko_reset_btn = QPushButton("초기화")
        ko_reset_btn.setFixedWidth(60)
        ko_reset_btn.clicked.connect(lambda: self._reset_lang_background("ko"))
        ko_bg_layout.addWidget(ko_reset_btn)
        bg_form.addRow(ko_label, ko_bg_layout)

        # 영어 배경화면
        en_label = QLabel("🇺🇸 English:")
        en_label.setFixedWidth(LABEL_WIDTH)
        en_bg_layout = QHBoxLayout()
        saved_en_bg = FileHandler.get_background_display_name(CAPTURE_SCREEN_KEY, lang="en")
        self.en_bg_edit = QLineEdit(saved_en_bg)
        self.en_bg_edit.setReadOnly(True)
        self.en_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        self.en_bg_edit.textChanged.connect(self._update_screen_preview)
        en_bg_layout.addWidget(self.en_bg_edit, 1)
        self.lang_bg_fields["en"]["background"] = self.en_bg_edit
        en_browse_btn = QPushButton("찾기...")
        en_browse_btn.setFixedWidth(60)
        en_browse_btn.clicked.connect(lambda: self._browse_lang_background("en"))
        en_bg_layout.addWidget(en_browse_btn)
        en_reset_btn = QPushButton("초기화")
        en_reset_btn.setFixedWidth(60)
        en_reset_btn.clicked.connect(lambda: self._reset_lang_background("en"))
        en_bg_layout.addWidget(en_reset_btn)
        bg_form.addRow(en_label, en_bg_layout)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("margin: 8px 0;")
        bg_form.addRow(separator)

        # 미리보기 언어 선택 라디오 버튼
        from PySide6.QtWidgets import QRadioButton, QButtonGroup
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

        parent_layout.addWidget(camera_group)

        # 언어 활성화 상태에 따라 라디오 버튼 초기 표시 설정
        self._update_preview_radio_visibility()

    def _on_preview_lang_changed(self, button):
        """미리보기 언어 변경 시 호출"""
        if button == self.radio_default:
            self._current_lang_preview = None
        elif button == self.radio_ko:
            self._current_lang_preview = "ko"
        else:
            self._current_lang_preview = "en"
        self._update_screen_preview()

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

    def _show_bg_help_dialog(self):
        """배경화면 도움말 다이얼로그"""
        dialog = QDialog(self)
        dialog.setWindowTitle("언어별 배경화면 안내")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        info = QLabel(
            "<b>언어별 배경화면 설정</b><br><br>"
            "키오스크에서 <b>언어 선택 기능</b>을 사용할 경우,<br>"
            "사용자가 선택한 언어에 따라 다른 배경화면을 표시할 수 있습니다.<br><br>"
            "<b>• 배경화면</b>: 기본 배경화면 (언어 미지정 시 사용)<br>"
            "<b>• 🇰🇷 한국어</b>: 한국어 선택 시 표시되는 배경<br>"
            "<b>• 🇺🇸 English</b>: 영어 선택 시 표시되는 배경<br><br>"
            "<i>언어별 배경화면 미설정 시 기본 배경화면이 사용됩니다.</i>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 12px; line-height: 1.5;")
        layout.addWidget(info)

        # 폴더 안내
        folder_info = QLabel(
            "📁 <b>저장 위치:</b><br>"
            "  • 기본: resources/background/<br>"
            "  • 한국어: resources/background_ko/<br>"
            "  • 영어: resources/background_en/"
        )
        folder_info.setStyleSheet("background-color: #ffffff; border: 1px solid #e9ecef; padding: 10px; border-radius: 4px; font-size: 11px;")
        layout.addWidget(folder_info)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec()

    def _browse_lang_background(self, lang_code: str):
        """언어별 배경화면 파일 선택"""
        bg_edit = self.lang_bg_fields[lang_code].get("background")
        if bg_edit:
            FileHandler.browse_background_file(self, bg_edit, CAPTURE_SCREEN_KEY, lang=lang_code)
            saved_bg = FileHandler.get_background_display_name(CAPTURE_SCREEN_KEY, lang=lang_code)
            bg_edit.setText(saved_bg)
            self._update_screen_preview()

    def _reset_lang_background(self, lang_code: str):
        """언어별 배경화면 초기화"""
        from PySide6.QtWidgets import QMessageBox
        lang_name = "한국어" if lang_code == "ko" else "영어"
        reply = QMessageBox.question(
            self, f"{lang_name} 배경화면 초기화",
            f"{lang_name} 카메라 화면의 배경화면을 삭제하시겠습니까?\n삭제 시 기본 배경화면이 사용됩니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(CAPTURE_SCREEN_KEY, lang=lang_code)
            bg_edit = self.lang_bg_fields[lang_code].get("background")
            if bg_edit:
                bg_edit.setText("")
            self._update_screen_preview()

    def _on_crop_changed(self):
        """크롭 영역 변경 시 호출"""
        self._validate_crop_area()
        self._update_screen_preview()
        self._update_crop_ratio_info()
        self._update_card_preview()

    def _validate_crop_area(self):
        """선택 영역이 카메라 해상도를 초과하지 않도록 검증"""
        cam_res = self.camera_resolution_combo.currentData()
        if not cam_res:
            return

        cam_w, cam_h = cam_res
        crop_x, crop_y, crop_w, crop_h = self.crop_input.get_values()
        changed = False

        if crop_w > cam_w:
            crop_w = cam_w
            changed = True
        if crop_h > cam_h:
            crop_h = cam_h
            changed = True

        if crop_x + crop_w > cam_w:
            crop_x = max(0, cam_w - crop_w)
            changed = True
        if crop_y + crop_h > cam_h:
            crop_y = max(0, cam_h - crop_h)
            changed = True

        if crop_x < 0:
            crop_x = 0
            changed = True
        if crop_y < 0:
            crop_y = 0
            changed = True

        if changed:
            self.crop_input.block_all_signals(True)
            self.crop_input.set_values(crop_x, crop_y, crop_w, crop_h)
            self.crop_input.block_all_signals(False)

    def _on_photo_settings_changed(self):
        """인쇄물 사진 설정 변경 시 호출"""
        self._update_card_preview()
        self._update_crop_ratio_info()
        self.request_real_time_update()

    def _update_crop_ratio_info(self):
        """크롭 영역 비율 정보 업데이트"""
        if not hasattr(self, 'crop_ratio_label'):
            return

        crop_w = self.crop_input.get_width()
        crop_h = self.crop_input.get_height()

        if crop_w > 0 and crop_h > 0:
            from math import gcd
            g = gcd(crop_w, crop_h)
            ratio_w = crop_w // g
            ratio_h = crop_h // g

            photo_w = self.photo_input.get_width() if hasattr(self, 'photo_input') else 0
            photo_h = self.photo_input.get_height() if hasattr(self, 'photo_input') else 0

            ratio_text = f"선택 비율: {ratio_w}:{ratio_h} ({crop_w}×{crop_h})"

            if photo_w > 0 and photo_h > 0:
                photo_g = gcd(photo_w, photo_h)
                photo_ratio_w = photo_w // photo_g
                photo_ratio_h = photo_h // photo_g

                if (ratio_w, ratio_h) == (photo_ratio_w, photo_ratio_h):
                    ratio_text += "  ✅ 인쇄 영역과 비율 일치"
                    self.crop_ratio_label.setStyleSheet("color: #27ae60; font-size: 11px; font-weight: bold;")
                else:
                    ratio_text += f"  ⚠️ 인쇄 영역({photo_ratio_w}:{photo_ratio_h})과 비율 다름"
                    self.crop_ratio_label.setStyleSheet("color: #e67e22; font-size: 11px;")
            else:
                self.crop_ratio_label.setStyleSheet("color: #666; font-size: 11px;")

            self.crop_ratio_label.setText(ratio_text)
        else:
            self.crop_ratio_label.setText("")

    # ═══════════════════════════════════════════════════════════════
    # 2. 카메라 영역 + 선택 영역
    # ═══════════════════════════════════════════════════════════════
    def _init_frame_settings(self, parent_layout):
        """카메라 영역과 선택 영역을 콤팩트하게 세로 배치"""
        # 카메라 해상도 선택 (상단에 배치)
        res_layout = QHBoxLayout()
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_label = QLabel("카메라 해상도:")
        res_label.setStyleSheet("font-weight: bold;")
        res_layout.addWidget(res_label)
        self.camera_resolution_combo = QComboBox()
        self.camera_resolution_combo.setFixedWidth(150)
        resolutions = [
            (1920, 1080, "1920×1080 (FHD)"),
            (2592, 1944, "2592×1944 (NUTZ)"),
            (1280, 720, "1280×720 (HD)"),
            (640, 480, "640×480 (VGA)"),
            (3840, 2160, "3840×2160 (4K)"),
        ]
        current_res = (self.config["camera_size"]["width"], self.config["camera_size"]["height"])
        current_idx = 0
        for i, (w, h, label) in enumerate(resolutions):
            self.camera_resolution_combo.addItem(label, (w, h))
            if (w, h) == current_res:
                current_idx = i
        res_found = any((w, h) == current_res for w, h, _ in resolutions)
        if not res_found:
            self.camera_resolution_combo.addItem(f"{current_res[0]}×{current_res[1]}", current_res)
            current_idx = self.camera_resolution_combo.count() - 1
        self.camera_resolution_combo.setCurrentIndex(current_idx)
        self.camera_resolution_combo.currentIndexChanged.connect(self._on_camera_resolution_changed)
        res_layout.addWidget(self.camera_resolution_combo)

        help_btn = self.create_help_button("인쇄 흐름 안내")
        help_btn.clicked.connect(self._show_flow_help_dialog)
        res_layout.addWidget(help_btn)
        res_layout.addStretch()
        parent_layout.addLayout(res_layout)

        # ───────────────────────────────────────────────────────────
        # 카메라 영역 (화면 표시 위치)
        # ───────────────────────────────────────────────────────────
        frame_group = QGroupBox("📹 카메라 영역 (화면 표시 위치)")
        frame_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #27ae60;
                border: 2px solid #27ae60;
                border-radius: 8px;
                margin-top: 12px;
                padding: 8px;
                background-color: #f8fff8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                background-color: white;
                border-radius: 4px;
            }
        """)
        frame_inner = QHBoxLayout(frame_group)
        frame_inner.setContentsMargins(12, 16, 12, 12)
        frame_inner.setSpacing(16)

        # 위치/크기 입력
        self.frame_input = PositionSizeInput()
        self.frame_input.set_values(
            self.config["frame"]["x"], self.config["frame"]["y"],
            self.config["frame"]["width"], self.config["frame"]["height"]
        )
        self.frame_input.value_changed.connect(self._update_screen_preview)
        frame_inner.addWidget(self.frame_input)

        # 빠른 정렬 버튼 (2x2 그리드)
        from PySide6.QtWidgets import QGridLayout
        frame_btn_widget = QWidget()
        frame_btn_widget.setStyleSheet("background-color: transparent;")
        frame_btn_grid = QGridLayout(frame_btn_widget)
        frame_btn_grid.setContentsMargins(0, 0, 0, 0)
        frame_btn_grid.setSpacing(4)

        frame_btns = [
            ("전체", self._fill_camera_frame, "화면 전체에 맞춤"),
            ("가운데", self._center_camera_frame, "화면 중앙에 배치"),
            ("넓이맞춤", self._fit_frame_width, "화면 넓이에 맞춤"),
            ("높이맞춤", self._fit_frame_height, "화면 높이에 맞춤"),
        ]
        frame_btn_style = """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 8px 12px;
                min-width: 60px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:pressed { background-color: #1e8449; }
        """
        for i, (text, callback, tooltip) in enumerate(frame_btns):
            btn = QPushButton(text)
            btn.setStyleSheet(frame_btn_style)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            frame_btn_grid.addWidget(btn, i // 2, i % 2)
        frame_inner.addStretch(1)
        frame_inner.addWidget(frame_btn_widget)
        frame_inner.addStretch(1)

        parent_layout.addWidget(frame_group)

        # ───────────────────────────────────────────────────────────
        # 선택 영역 (인쇄할 부분)
        # ───────────────────────────────────────────────────────────
        crop_group = QGroupBox("✂️ 선택 영역 (인쇄할 부분)")
        crop_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #e67e22;
                border: 2px solid #e67e22;
                border-radius: 8px;
                margin-top: 12px;
                padding: 8px;
                background-color: #fffaf5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                background-color: white;
                border-radius: 4px;
            }
        """)
        crop_inner = QHBoxLayout(crop_group)
        crop_inner.setContentsMargins(12, 16, 12, 12)
        crop_inner.setSpacing(16)

        # 위치/크기 입력
        self.crop_input = PositionSizeInput()
        self.crop_input.set_values(
            self.config["crop_area"]["x"], self.config["crop_area"]["y"],
            self.config["crop_area"]["width"], self.config["crop_area"]["height"]
        )
        self.crop_input.value_changed.connect(self._on_crop_changed)
        crop_inner.addWidget(self.crop_input)

        # 빠른 정렬 버튼 (2x2 그리드)
        crop_btn_widget = QWidget()
        crop_btn_widget.setStyleSheet("background-color: transparent;")
        crop_btn_grid = QGridLayout(crop_btn_widget)
        crop_btn_grid.setContentsMargins(0, 0, 0, 0)
        crop_btn_grid.setSpacing(4)

        crop_btns = [
            ("전체", self._fill_crop_area, "카메라 전체 영역 선택"),
            ("가운데", self._center_crop_area, "선택 영역을 중앙으로"),
            ("넓이맞춤", self._fit_crop_width, "카메라 넓이에 맞춤"),
            ("높이맞춤", self._fit_crop_height, "카메라 높이에 맞춤"),
        ]
        crop_btn_style = """
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 8px 12px;
                min-width: 60px;
            }
            QPushButton:hover { background-color: #f39c12; }
            QPushButton:pressed { background-color: #d35400; }
        """
        for i, (text, callback, tooltip) in enumerate(crop_btns):
            btn = QPushButton(text)
            btn.setStyleSheet(crop_btn_style)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            crop_btn_grid.addWidget(btn, i // 2, i % 2)
        crop_inner.addStretch(1)
        crop_inner.addWidget(crop_btn_widget)
        crop_inner.addStretch(1)

        parent_layout.addWidget(crop_group)

        # 비율 정보 (하단에 작게 표시)
        self.crop_ratio_label = QLabel()
        self.crop_ratio_label.setAlignment(Qt.AlignLeft)
        self.crop_ratio_label.setStyleSheet("color: #666; font-size: 10px; padding-left: 4px;")
        parent_layout.addWidget(self.crop_ratio_label)
        self._update_crop_ratio_info()

    # ═══════════════════════════════════════════════════════════════
    # 3. 베이스 카드 이미지 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_base_card_settings(self, parent_layout):
        """베이스 카드 이미지 선택"""
        card_group = QGroupBox("베이스 카드 이미지")
        self.apply_left_aligned_group_style(card_group)
        card_layout = QVBoxLayout(card_group)
        card_layout.setSpacing(8)

        desc = QLabel("인쇄될 카드의 배경 이미지를 선택합니다 (636×1012)")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
        card_layout.addWidget(desc)

        file_layout = QHBoxLayout()
        self.base_card_edit = QLineEdit(self.config.get("card", {}).get("background", ""))
        self.base_card_edit.setPlaceholderText("이미지를 선택하세요...")
        self.base_card_edit.textChanged.connect(self._on_base_card_changed)
        file_layout.addWidget(self.base_card_edit, 1)

        browse_btn = QPushButton("찾기...")
        browse_btn.clicked.connect(self._browse_base_card_image)
        file_layout.addWidget(browse_btn)
        card_layout.addLayout(file_layout)

        parent_layout.addWidget(card_group)

    def _browse_base_card_image(self):
        """베이스 카드 이미지 파일 선택"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "베이스 카드 이미지 선택", "",
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp);;모든 파일 (*.*)"
        )
        if file_path:
            self.base_card_edit.setText(file_path)

    def _on_base_card_changed(self):
        """베이스 카드 이미지 변경 시 호출"""
        self._update_card_preview()
        self.request_real_time_update()

    # ═══════════════════════════════════════════════════════════════
    # 4. 인쇄물 사진 위치
    # ═══════════════════════════════════════════════════════════════
    def _init_photo_settings(self, parent_layout):
        photo_group = QGroupBox("인쇄물에 들어갈 사진 위치")
        self.apply_left_aligned_group_style(photo_group)
        photo_layout = QVBoxLayout(photo_group)
        photo_layout.setSpacing(8)

        desc = QLabel("촬영된 사진이 카드에 인쇄될 위치와 크기를 설정합니다")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
        photo_layout.addWidget(desc)

        self.photo_input = PositionSizeInput()
        self.photo_input.set_values(
            self.config["photo"]["x"],
            self.config["photo"]["y"],
            self.config["photo"]["width"],
            self.config["photo"]["height"]
        )
        self.photo_input.value_changed.connect(self._on_photo_settings_changed)
        photo_layout.addWidget(self.photo_input, 0, Qt.AlignCenter)

        # 빠른 정렬 버튼 (1행 4열)
        photo_btn_layout = QHBoxLayout()
        photo_btn_layout.setContentsMargins(0, 4, 0, 0)
        photo_btn_layout.setSpacing(4)
        photo_btn_layout.addStretch(1)

        for label, callback in [("전체", self._fill_photo_frame),
                                 ("가운데", self._center_photo_frame),
                                 ("넓이맞춤", self._fit_photo_width),
                                 ("높이맞춤", self._fit_photo_height)]:
            btn = QPushButton(label)
            btn.setFixedSize(80, 26)
            btn.clicked.connect(callback)
            photo_btn_layout.addWidget(btn)

        photo_btn_layout.addStretch(1)
        photo_layout.addLayout(photo_btn_layout)

        parent_layout.addWidget(photo_group)

    # ═══════════════════════════════════════════════════════════════
    # 탭 3: 카메라 카운트
    # ═══════════════════════════════════════════════════════════════
    def _create_camera_count_tab(self):
        """카메라 카운트 설정 탭 생성"""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(20)

        # 좌측: 설정 영역
        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: white;")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 10, 0)
        settings_layout.setSpacing(12)

        # 카메라 카운트 그룹
        count_group = QGroupBox("카메라 카운트 설정")
        self.apply_left_aligned_group_style(count_group)
        count_layout = QFormLayout(count_group)
        count_layout.setSpacing(12)

        # 설명
        desc = QLabel("촬영 전 화면에 표시되는 카운트다운 숫자를 설정합니다.")
        desc.setStyleSheet("color: #666; font-size: 11px; padding: 4px 0 8px 0;")
        desc.setWordWrap(True)
        count_layout.addRow("", desc)

        self.camera_count_fields = {}

        number_spin = QSpinBox()
        number_spin.setRange(0, 10)
        number_spin.setValue(self.config["camera_count"]["number"])
        number_spin.setFixedWidth(80)
        count_layout.addRow("카운트 시작 숫자:", number_spin)
        self.camera_count_fields["number"] = number_spin

        font_size_spin = NumberLineEdit()
        font_size_spin.setValue(self.config["camera_count"]["font_size"])
        font_size_spin.setFixedWidth(80)
        count_layout.addRow("폰트 크기:", font_size_spin)
        self.camera_count_fields["font_size"] = font_size_spin

        font_color_btn = ColorPickerButton(self.config["camera_count"]["font_color"])
        count_layout.addRow("폰트 색상:", font_color_btn)
        self.camera_count_fields["font_color"] = font_color_btn

        settings_layout.addWidget(count_group)
        settings_layout.addStretch()
        tab_layout.addWidget(settings_widget, 1)

        # 우측: 화면 미리보기 (3번째 인스턴스)
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self._init_screen_preview_for_count(preview_layout)
        preview_layout.addStretch()

        tab_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab_widget, "카메라 카운트")

    # ═══════════════════════════════════════════════════════════════
    # 미리보기 영역
    # ═══════════════════════════════════════════════════════════════
    def _init_language_preview_tabs(self, parent_layout):
        """화면 미리보기 초기화 (확대된 크기)"""
        group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(group)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("녹색 = 카메라 영역  |  주황색 = 인쇄될 선택 영역 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        layout.addWidget(desc)

        # 확대된 미리보기 위젯 + 줌 기능
        self.screen_preview = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.screen_preview.position_changed.connect(self._on_frame_position_changed)
        self.screen_preview.size_changed.connect(self._on_frame_size_changed)
        self._zoomable_screen_preview = ZoomablePreviewWidget(self.screen_preview)
        layout.addWidget(self._zoomable_screen_preview, 0, Qt.AlignCenter)

        hint = QLabel("녹색 영역을 드래그하여 위치/크기 조절")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        layout.addWidget(hint)

        parent_layout.addWidget(group)

    def _init_screen_preview(self, parent_layout):
        group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(group)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("녹색 = 카메라 영역  |  주황색 = 인쇄될 선택 영역 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        layout.addWidget(desc)

        self.screen_preview = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.screen_preview.position_changed.connect(self._on_frame_position_changed)
        self.screen_preview.size_changed.connect(self._on_frame_size_changed)
        self._zoomable_screen_preview2 = ZoomablePreviewWidget(self.screen_preview)
        layout.addWidget(self._zoomable_screen_preview2, 0, Qt.AlignCenter)

        hint = QLabel("녹색 영역을 드래그하여 위치/크기 조절")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        layout.addWidget(hint)

        parent_layout.addWidget(group)

    def _init_card_preview(self, parent_layout):
        group = QGroupBox("카드 인쇄 미리보기 (58x90mm)")
        self.apply_left_aligned_group_style(group)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("빨간색 영역 = 촬영된 사진이 인쇄될 위치 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold; padding: 4px;")
        layout.addWidget(desc)

        self.card_preview = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.card_preview.position_changed.connect(self._on_photo_position_changed)
        self.card_preview.size_changed.connect(self._on_photo_size_changed)
        self._zoomable_card_preview = ZoomablePreviewWidget(self.card_preview)
        layout.addWidget(self._zoomable_card_preview, 0, Qt.AlignCenter)

        # 안내 문구
        card_info = QLabel("※ 검정 테두리가 실제 인쇄되는 카드 영역입니다.")
        card_info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(card_info, 0, Qt.AlignCenter)

        hint = QLabel("빨간색 영역을 드래그하여 위치/크기 조절")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        layout.addWidget(hint)

        parent_layout.addWidget(group)

    def _init_screen_preview_for_camera_area(self, parent_layout):
        """카메라 영역 탭용 화면 미리보기"""
        group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(group)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("녹색 = 카메라 영역  |  주황색 = 인쇄될 선택 영역 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        layout.addWidget(desc)

        self.screen_preview_camera_area = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.screen_preview_camera_area.position_changed.connect(self._on_frame_position_changed)
        self.screen_preview_camera_area.size_changed.connect(self._on_frame_size_changed)
        self._zoomable_camera_area_preview = ZoomablePreviewWidget(self.screen_preview_camera_area)
        layout.addWidget(self._zoomable_camera_area_preview, 0, Qt.AlignCenter)

        hint = QLabel("녹색 영역을 드래그하여 위치/크기 조절")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        layout.addWidget(hint)

        parent_layout.addWidget(group)

    def _init_screen_preview_for_count(self, parent_layout):
        """카메라 카운트 탭용 화면 미리보기"""
        group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(group)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("녹색 = 카메라 영역  |  주황색 = 인쇄될 선택 영역 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        layout.addWidget(desc)

        self.screen_preview_count = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        # 카운트 탭은 조절 기능 불필요하므로 드래그 비활성화
        self._zoomable_count_preview = ZoomablePreviewWidget(self.screen_preview_count)
        layout.addWidget(self._zoomable_count_preview, 0, Qt.AlignCenter)

        hint = QLabel("화면에 표시되는 미리보기입니다")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        layout.addWidget(hint)

        parent_layout.addWidget(group)

    # ═══════════════════════════════════════════════════════════════
    # 도움말 다이얼로그
    # ═══════════════════════════════════════════════════════════════
    def _show_flow_help_dialog(self):
        """인쇄 흐름 안내 다이얼로그 표시"""
        dialog = QDialog(self)
        dialog.setWindowTitle("인쇄 흐름 안내")
        dialog.setMinimumWidth(450)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)

        flow_diagram = QLabel(
            "┌──────────────┐      ┌──────────────┐      ┌──────────────┐\n"
            "│  카메라      │  →   │  선택 영역   │  →   │  인쇄 카드   │\n"
            "│  (화면표시)   │      │  (크롭 부분)  │      │   (결과물)   │\n"
            "└──────────────┘      └──────────────┘      └──────────────┘"
        )
        flow_diagram.setAlignment(Qt.AlignCenter)
        flow_diagram.setStyleSheet("""
            font-family: 'Consolas', 'D2Coding', monospace;
            font-size: 12px;
            color: #34495e;
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            padding: 16px;
            border-radius: 8px;
        """)
        layout.addWidget(flow_diagram)

        desc = QLabel(
            "<b>카메라 영역</b>: 화면에서 카메라가 보이는 위치입니다.<br><br>"
            "<b>선택 영역</b>: 카메라 원본에서 인쇄할 부분을 선택합니다.<br>"
            "　  녹색 영역 안에서 주황색 선택 영역만 잘라서 인쇄됩니다.<br><br>"
            "미리보기에서 녹색 영역을 드래그하면 주황색 영역도 함께 이동합니다."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #555; font-size: 12px; line-height: 1.5;")
        layout.addWidget(desc)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec()

    # ═══════════════════════════════════════════════════════════════
    # 배경화면 관련 메서드
    # ═══════════════════════════════════════════════════════════════
    def _browse_and_update_background(self):
        """배경화면 파일 선택 후 표시 업데이트"""
        FileHandler.browse_background_file(self, self.capture_bg_edit, CAPTURE_SCREEN_KEY)
        saved_bg = FileHandler.get_background_display_name(CAPTURE_SCREEN_KEY)
        self.capture_bg_edit.setText(saved_bg)
        self._update_screen_preview()

    def _reset_capture_background(self):
        """배경화면 초기화 (삭제)"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "배경화면 초기화",
            "이 화면의 배경화면을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(CAPTURE_SCREEN_KEY)
            self.capture_bg_edit.setText("")
            self._update_screen_preview()

    # ═══════════════════════════════════════════════════════════════
    # 이벤트 핸들러
    # ═══════════════════════════════════════════════════════════════
    def _on_camera_resolution_changed(self, index):
        res = self.camera_resolution_combo.itemData(index)
        if res:
            self.config["camera_size"]["width"] = res[0]
            self.config["camera_size"]["height"] = res[1]
        self._validate_crop_area()
        self._update_screen_preview()
        self._update_crop_ratio_info()

    def _fill_crop_area(self):
        res = self.camera_resolution_combo.currentData()
        if res:
            self.crop_input.set_values(0, 0, res[0], res[1])
        self._update_screen_preview()
        self._update_crop_ratio_info()

    def _center_crop_area(self):
        res = self.camera_resolution_combo.currentData()
        if res:
            x, y, w, h = self.crop_input.get_values()
            self.crop_input.set_x((res[0] - w) // 2)
            self.crop_input.set_y((res[1] - h) // 2)
        self._update_screen_preview()
        self._update_crop_ratio_info()

    def _fill_camera_frame(self):
        try:
            mw = self.config["screen_size"]["width"]
            mh = self.config["screen_size"]["height"]
        except KeyError:
            mw, mh = 1080, 1920
        self.frame_input.set_values(0, 0, mw, mh)
        self._update_screen_preview()

    def _center_camera_frame(self):
        try:
            mw = self.config["screen_size"]["width"]
            mh = self.config["screen_size"]["height"]
        except KeyError:
            mw, mh = 1080, 1920
        x, y, w, h = self.frame_input.get_values()
        self.frame_input.set_x((mw - w) // 2)
        self.frame_input.set_y((mh - h) // 2)
        self._update_screen_preview()

    def _fit_frame_width(self):
        """카메라 영역 넓이만 화면 넓이에 맞춤 (높이 유지)"""
        try:
            mw = self.config["screen_size"]["width"]
        except KeyError:
            mw = 1080
        self.frame_input.set_x(0)
        self.frame_input.set_width(mw)
        self._update_screen_preview()

    def _fit_frame_height(self):
        """카메라 영역 높이만 화면 높이에 맞춤 (넓이 유지)"""
        try:
            mh = self.config["screen_size"]["height"]
        except KeyError:
            mh = 1920
        self.frame_input.set_y(0)
        self.frame_input.set_height(mh)
        self._update_screen_preview()

    def _fit_crop_width(self):
        """선택 영역 넓이만 카메라 넓이에 맞춤 (높이 유지)"""
        res = self.camera_resolution_combo.currentData()
        if res:
            self.crop_input.set_x(0)
            self.crop_input.set_width(res[0])
            self._on_crop_changed()

    def _fit_crop_height(self):
        """선택 영역 높이만 카메라 높이에 맞춤 (넓이 유지)"""
        res = self.camera_resolution_combo.currentData()
        if res:
            self.crop_input.set_y(0)
            self.crop_input.set_height(res[1])
            self._on_crop_changed()

    def _fill_photo_frame(self):
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        cw, ch = (636, 1012) if is_portrait else (1012, 636)
        self.photo_input.set_values(0, 0, cw, ch)
        self._update_card_preview()
        self.request_real_time_update()

    def _center_photo_frame(self):
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        cw, ch = (636, 1012) if is_portrait else (1012, 636)
        x, y, w, h = self.photo_input.get_values()
        self.photo_input.set_x((cw - w) // 2)
        self.photo_input.set_y((ch - h) // 2)
        self._update_card_preview()
        self.request_real_time_update()

    def _fit_photo_width(self):
        """사진 넓이를 카드 넓이에 맞춤"""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        cw, ch = (636, 1012) if is_portrait else (1012, 636)
        self.photo_input.set_x(0)
        self.photo_input.set_width(cw)
        self._update_card_preview()
        self.request_real_time_update()

    def _fit_photo_height(self):
        """사진 높이를 카드 높이에 맞춤"""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        cw, ch = (636, 1012) if is_portrait else (1012, 636)
        self.photo_input.set_y(0)
        self.photo_input.set_height(ch)
        self._update_card_preview()
        self.request_real_time_update()

    def _on_frame_position_changed(self, element_id, x, y):
        if element_id == "camera_frame":
            self.frame_input.block_all_signals(True)
            self.frame_input.set_x(x)
            self.frame_input.set_y(y)
            self.frame_input.block_all_signals(False)
            self._update_screen_preview()
            self.request_real_time_update()
        elif element_id == "crop_area":
            frame_x, frame_y, frame_w, frame_h = self.frame_input.get_values()
            cam_res = self.camera_resolution_combo.currentData()
            if cam_res and frame_w > 0 and frame_h > 0:
                scale_x = cam_res[0] / frame_w
                scale_y = cam_res[1] / frame_h
                crop_x = int((x - frame_x) * scale_x)
                crop_y = int((y - frame_y) * scale_y)

                crop_w = self.crop_input.get_width()
                crop_h = self.crop_input.get_height()
                crop_x = max(0, min(crop_x, cam_res[0] - crop_w))
                crop_y = max(0, min(crop_y, cam_res[1] - crop_h))

                self.crop_input.block_all_signals(True)
                self.crop_input.set_x(crop_x)
                self.crop_input.set_y(crop_y)
                self.crop_input.block_all_signals(False)

                self._update_screen_preview()
                self._update_crop_ratio_info()
                self.request_real_time_update()

    def _on_frame_size_changed(self, element_id, x, y, w, h):
        if element_id == "camera_frame":
            self.frame_input.block_all_signals(True)
            self.frame_input.set_values(x, y, w, h)
            self.frame_input.block_all_signals(False)
            self._update_screen_preview()
            self.request_real_time_update()
        elif element_id == "crop_area":
            frame_x, frame_y, frame_w, frame_h = self.frame_input.get_values()
            cam_res = self.camera_resolution_combo.currentData()
            if cam_res and frame_w > 0 and frame_h > 0:
                scale_x = cam_res[0] / frame_w
                scale_y = cam_res[1] / frame_h
                crop_x = int((x - frame_x) * scale_x)
                crop_y = int((y - frame_y) * scale_y)
                crop_w = int(w * scale_x)
                crop_h = int(h * scale_y)

                crop_x = max(0, min(crop_x, cam_res[0] - crop_w))
                crop_y = max(0, min(crop_y, cam_res[1] - crop_h))
                crop_w = max(1, min(crop_w, cam_res[0]))
                crop_h = max(1, min(crop_h, cam_res[1]))

                self.crop_input.block_all_signals(True)
                self.crop_input.set_values(crop_x, crop_y, crop_w, crop_h)
                self.crop_input.block_all_signals(False)

                self._validate_crop_area()
                self._update_screen_preview()
                self._update_crop_ratio_info()
                self.request_real_time_update()

    def _on_photo_position_changed(self, element_id, x, y):
        if element_id == "photo_area":
            self.photo_input.block_all_signals(True)
            self.photo_input.set_x(x)
            self.photo_input.set_y(y)
            self.photo_input.block_all_signals(False)
            self.request_real_time_update()

    def _on_photo_size_changed(self, element_id, x, y, w, h):
        if element_id == "photo_area":
            self.photo_input.block_all_signals(True)
            self.photo_input.set_values(x, y, w, h)
            self.photo_input.block_all_signals(False)
            self.request_real_time_update()

    # ═══════════════════════════════════════════════════════════════
    # 미리보기 업데이트
    # ═══════════════════════════════════════════════════════════════
    def _update_screen_preview(self):
        """모든 화면 미리보기를 업데이트합니다."""
        try:
            mw = self.config["screen_size"]["width"]
            mh = self.config["screen_size"]["height"]
        except KeyError:
            mw, mh = 1080, 1920

        # 프레임 값 가져오기
        x, y, w, h = 0, 0, mw, mh
        if hasattr(self, 'frame_input'):
            x, y, w, h = self.frame_input.get_values()

        # 선택 영역 계산
        display_crop_rect = None
        if hasattr(self, 'crop_input') and hasattr(self, 'camera_resolution_combo'):
            crop_x, crop_y, crop_w, crop_h = self.crop_input.get_values()
            cam_res = self.camera_resolution_combo.currentData()
            if cam_res and cam_res[0] > 0 and cam_res[1] > 0 and w > 0 and h > 0:
                scale_x = w / cam_res[0]
                scale_y = h / cam_res[1]
                display_crop_x = x + int(crop_x * scale_x)
                display_crop_y = y + int(crop_y * scale_y)
                display_crop_w = int(crop_w * scale_x)
                display_crop_h = int(crop_h * scale_y)
                display_crop_rect = QRect(display_crop_x, display_crop_y, display_crop_w, display_crop_h)

        # 화면 설정 탭의 미리보기 (언어 활성화 상태에 따라 처리)
        lang_enabled = self.config.get("language", {}).get("enabled", False)

        if lang_enabled:
            # 언어 활성화: 선택된 언어(ko/en)의 배경만 사용, 없으면 빈 배경
            lang = getattr(self, '_current_lang_preview', "ko")  # 기본값 한국어
            if lang is None:
                lang = "ko"  # 언어 활성화 시 기본 선택은 한국어
            lang_bg_path = FileHandler.resolve_background_path(CAPTURE_SCREEN_KEY, lang=lang)
            # 언어 활성화 시에는 기본 배경으로 fallback 하지 않음
        else:
            # 언어 비활성화: 기본 배경만 사용
            lang_bg_path = FileHandler.resolve_background_path(CAPTURE_SCREEN_KEY, lang=None)

        # 기존 미리보기들도 업데이트 (카메라 영역 탭, 카운트 탭) - 언어 설정에 맞게 배경 적용
        previews = [self.screen_preview_camera_area, self.screen_preview_count]
        for preview in previews:
            if preview:
                preview.set_original_size(mw, mh)
                preview.set_background(lang_bg_path, QColor("#ffffff"))
                preview.set_card_border(True, QColor("#333333"), 2)

                preview.add_element(
                    "camera_frame", QRect(x, y, w, h),
                    color=QColor("lime"), label="카메라", draggable=True
                )

                if display_crop_rect:
                    preview.add_element(
                        "crop_area", display_crop_rect,
                        color=QColor("#FF6B00"), label="선택영역", draggable=True
                    )

        # 화면 설정 탭의 미리보기 (언어 버튼으로 선택된 배경 적용)
        if self.screen_preview:
            # 언어 활성화 시 해당 언어 배경이 없으면 빈 화면 (fallback 없음)
            # 언어 비활성화 시에만 기본 배경 사용
            use_bg = lang_bg_path  # 배경이 없으면 None, 빈 화면으로 표시됨
            self.screen_preview.set_original_size(mw, mh)
            self.screen_preview.set_background(use_bg, QColor("#ffffff"))
            self.screen_preview.set_card_border(True, QColor("#333333"), 2)

            self.screen_preview.add_element(
                "camera_frame", QRect(x, y, w, h),
                color=QColor("lime"), label="카메라", draggable=True
            )

            if display_crop_rect:
                self.screen_preview.add_element(
                    "crop_area", display_crop_rect,
                    color=QColor("#FF6B00"), label="선택영역", draggable=True
                )

        self.request_real_time_update()

    def _update_card_preview(self):
        if not self.card_preview:
            return

        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        cw, ch = (636, 1012) if is_portrait else (1012, 636)

        self.card_preview.set_original_size(cw, ch)

        base_card_path = ""
        if hasattr(self, 'base_card_edit'):
            base_card_path = self.base_card_edit.text()

        if base_card_path:
            self.card_preview.set_background(base_card_path, QColor("white"))
        else:
            self.card_preview.set_background_color(QColor("white"))

        # 카드 테두리 표시 (인쇄 영역 경계)
        self.card_preview.set_card_border(True, QColor("#333333"), 3)

        x, y, w, h = self.photo_input.get_values()
        self.card_preview.add_element(
            "photo_area", QRect(x, y, w, h),
            color=QColor("red"), label="사진", draggable=True
        )
        self.request_real_time_update()

    # ═══════════════════════════════════════════════════════════════
    # Config 동기화
    # ═══════════════════════════════════════════════════════════════
    def update_ui(self, config):
        self.config = config
        self.capture_bg_edit.setText(config["photo"].get("background", ""))

        res = (config["camera_size"]["width"], config["camera_size"]["height"])
        found = False
        for i in range(self.camera_resolution_combo.count()):
            if self.camera_resolution_combo.itemData(i) == res:
                self.camera_resolution_combo.setCurrentIndex(i)
                found = True
                break
        if not found:
            self.camera_resolution_combo.addItem(f"{res[0]} × {res[1]}", res)
            self.camera_resolution_combo.setCurrentIndex(self.camera_resolution_combo.count() - 1)

        self.crop_input.set_values(
            config["crop_area"]["x"], config["crop_area"]["y"],
            config["crop_area"]["width"], config["crop_area"]["height"]
        )

        self.frame_input.set_values(
            config["frame"]["x"], config["frame"]["y"],
            config["frame"]["width"], config["frame"]["height"]
        )

        self.photo_input.set_values(
            config["photo"]["x"], config["photo"]["y"],
            config["photo"]["width"], config["photo"]["height"]
        )

        self.camera_count_fields["number"].setValue(config["camera_count"]["number"])
        self.camera_count_fields["font_size"].setValue(config["camera_count"]["font_size"])
        self.camera_count_fields["font_color"].update_color(config["camera_count"]["font_color"])

        if hasattr(self, 'base_card_edit'):
            self.base_card_edit.setText(config.get("card", {}).get("background", ""))

        # 언어 활성화 상태에 따라 라디오 버튼 표시 업데이트
        self._update_preview_radio_visibility()
        self._update_screen_preview()
        self._update_card_preview()

    def update_config(self, config):
        config["photo"]["background"] = self.capture_bg_edit.text()

        res = self.camera_resolution_combo.currentData()
        if res:
            config["camera_size"]["width"] = res[0]
            config["camera_size"]["height"] = res[1]

        x, y, w, h = self.crop_input.get_values()
        config["crop_area"]["x"] = x
        config["crop_area"]["y"] = y
        config["crop_area"]["width"] = w
        config["crop_area"]["height"] = h

        x, y, w, h = self.frame_input.get_values()
        config["frame"]["x"] = x
        config["frame"]["y"] = y
        config["frame"]["width"] = w
        config["frame"]["height"] = h

        x, y, w, h = self.photo_input.get_values()
        config["photo"]["filename"] = "captured_image.jpg"
        config["photo"]["x"] = x
        config["photo"]["y"] = y
        config["photo"]["width"] = w
        config["photo"]["height"] = h

        if "framed_photo" not in config:
            config["framed_photo"] = {}
        config["framed_photo"]["x"] = x
        config["framed_photo"]["y"] = y
        config["framed_photo"]["width"] = w
        config["framed_photo"]["height"] = h
        if "filename" not in config["framed_photo"]:
            config["framed_photo"]["filename"] = "framed_photo.jpg"

        config["camera_count"]["number"] = self.camera_count_fields["number"].value()
        config["camera_count"]["font_size"] = self.camera_count_fields["font_size"].value()
        config["camera_count"]["font_color"] = self.camera_count_fields["font_color"].color

        if "card" not in config:
            config["card"] = {}
        if hasattr(self, 'base_card_edit'):
            config["card"]["background"] = self.base_card_edit.text()
