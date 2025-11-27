from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QSpinBox, QWidget, QComboBox, QFrame,
                              QDialog, QDialogButtonBox, QTabWidget, QScrollArea)
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect, QSize
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import LivePreviewWidget
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
        self.card_preview = None
        self.sub_tabs = None
        # 언어별 배경화면 필드
        self.lang_bg_fields = {"ko": {}, "en": {}}
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
                background: #f0f0f0;
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
                background: #e0e0e0;
            }
        """)
        scroll_content_layout.addWidget(self.sub_tabs)

        # 탭 1: 화면 설정
        self._create_screen_settings_tab()

        # 탭 2: 인쇄 설정
        self._create_print_settings_tab()

        # 탭 3: 카메라 카운트
        self._create_camera_count_tab()

        scroll_content_layout.addStretch()

        self._update_screen_preview()
        self._update_card_preview()

    # ═══════════════════════════════════════════════════════════════
    # 탭 1: 화면 설정
    # ═══════════════════════════════════════════════════════════════
    def _create_screen_settings_tab(self):
        """화면 설정 탭 생성"""
        tab_widget = QWidget()
        tab_layout = QHBoxLayout(tab_widget)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(20)

        # 좌측: 설정 영역 (스크롤)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 10, 0)
        settings_layout.setSpacing(12)

        # 카메라 설정 (언어별 배경화면 포함)
        self._init_camera_settings(settings_layout)

        # 카메라 영역 및 선택 영역
        self._init_frame_settings(settings_layout)

        settings_layout.addStretch()
        settings_scroll.setWidget(settings_widget)
        tab_layout.addWidget(settings_scroll, 1)

        # 우측: 화면 미리보기
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self._init_screen_preview(preview_layout)
        preview_layout.addStretch()

        tab_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab_widget, "화면 설정")

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
    # 1. 카메라 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_camera_settings(self, parent_layout):
        camera_group = QGroupBox("카메라 설정")
        self.apply_left_aligned_group_style(camera_group)
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setSpacing(10)

        # 배경화면 (기본)
        bg_layout = QHBoxLayout()
        bg_label = QLabel("배경화면:")
        bg_layout.addWidget(bg_label)
        # ? 도움말 버튼
        help_btn = QPushButton("?")
        help_btn.setFixedSize(20, 20)
        help_btn.setToolTip("언어별 배경화면 안내")
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        help_btn.clicked.connect(self._show_bg_help_dialog)
        bg_layout.addWidget(help_btn)
        saved_bg = FileHandler.get_background_display_name(CAPTURE_SCREEN_KEY)
        self.capture_bg_edit = QLineEdit(saved_bg)
        self.capture_bg_edit.setReadOnly(True)
        self.capture_bg_edit.setPlaceholderText("배경화면 없음")
        self.capture_bg_edit.textChanged.connect(self._update_screen_preview)
        bg_layout.addWidget(self.capture_bg_edit, 1)
        browse_btn = QPushButton("찾기...")
        browse_btn.clicked.connect(lambda: self._browse_and_update_background())
        bg_layout.addWidget(browse_btn)
        reset_btn = QPushButton("초기화")
        reset_btn.setFixedWidth(60)
        reset_btn.setToolTip("배경화면을 삭제합니다")
        reset_btn.clicked.connect(self._reset_capture_background)
        bg_layout.addWidget(reset_btn)
        camera_layout.addLayout(bg_layout)

        # 한국어 배경화면
        ko_bg_layout = QHBoxLayout()
        ko_bg_layout.addWidget(QLabel("🇰🇷 한국어:"))
        saved_ko_bg = FileHandler.get_background_display_name(CAPTURE_SCREEN_KEY, lang="ko")
        self.ko_bg_edit = QLineEdit(saved_ko_bg)
        self.ko_bg_edit.setReadOnly(True)
        self.ko_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        self.ko_bg_edit.textChanged.connect(self._update_screen_preview)
        ko_bg_layout.addWidget(self.ko_bg_edit, 1)
        self.lang_bg_fields["ko"]["background"] = self.ko_bg_edit
        ko_browse_btn = QPushButton("찾기...")
        ko_browse_btn.clicked.connect(lambda: self._browse_lang_background("ko"))
        ko_bg_layout.addWidget(ko_browse_btn)
        ko_reset_btn = QPushButton("초기화")
        ko_reset_btn.setFixedWidth(60)
        ko_reset_btn.clicked.connect(lambda: self._reset_lang_background("ko"))
        ko_bg_layout.addWidget(ko_reset_btn)
        camera_layout.addLayout(ko_bg_layout)

        # 영어 배경화면
        en_bg_layout = QHBoxLayout()
        en_bg_layout.addWidget(QLabel("🇺🇸 English:"))
        saved_en_bg = FileHandler.get_background_display_name(CAPTURE_SCREEN_KEY, lang="en")
        self.en_bg_edit = QLineEdit(saved_en_bg)
        self.en_bg_edit.setReadOnly(True)
        self.en_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        self.en_bg_edit.textChanged.connect(self._update_screen_preview)
        en_bg_layout.addWidget(self.en_bg_edit, 1)
        self.lang_bg_fields["en"]["background"] = self.en_bg_edit
        en_browse_btn = QPushButton("찾기...")
        en_browse_btn.clicked.connect(lambda: self._browse_lang_background("en"))
        en_bg_layout.addWidget(en_browse_btn)
        en_reset_btn = QPushButton("초기화")
        en_reset_btn.setFixedWidth(60)
        en_reset_btn.clicked.connect(lambda: self._reset_lang_background("en"))
        en_bg_layout.addWidget(en_reset_btn)
        camera_layout.addLayout(en_bg_layout)

        # 구분선
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #ddd;")
        camera_layout.addWidget(sep)

        # 카메라 해상도
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("카메라 해상도:"))
        self.camera_resolution_combo = QComboBox()
        self.camera_resolution_combo.addItem("2560 × 1440", (2560, 1440))
        self.camera_resolution_combo.addItem("1920 × 1080", (1920, 1080))
        self.camera_resolution_combo.addItem("1080 × 720", (1080, 720))

        current_res = (self.config["camera_size"]["width"], self.config["camera_size"]["height"])
        found = False
        for i in range(self.camera_resolution_combo.count()):
            if self.camera_resolution_combo.itemData(i) == current_res:
                self.camera_resolution_combo.setCurrentIndex(i)
                found = True
                break
        if not found:
            self.camera_resolution_combo.addItem(f"{current_res[0]} × {current_res[1]}", current_res)
            self.camera_resolution_combo.setCurrentIndex(self.camera_resolution_combo.count() - 1)

        self.camera_resolution_combo.currentIndexChanged.connect(self._on_camera_resolution_changed)
        res_layout.addWidget(self.camera_resolution_combo)
        res_layout.addStretch()
        camera_layout.addLayout(res_layout)

        parent_layout.addWidget(camera_group)

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
        folder_info.setStyleSheet("background-color: #f0f4f8; padding: 10px; border-radius: 4px; font-size: 11px;")
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
        """카메라 영역과 선택 영역을 하나의 그룹으로 통합"""
        main_group = QGroupBox("카메라 영역 및 선택 영역")
        self.apply_left_aligned_group_style(main_group)
        main_layout = QVBoxLayout(main_group)
        main_layout.setSpacing(12)

        # 헤더 + 도움말 버튼
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        help_btn = QPushButton("?")
        help_btn.setFixedSize(24, 24)
        help_btn.setToolTip("인쇄 흐름 안내 보기")
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        help_btn.clicked.connect(self._show_flow_help_dialog)
        header_layout.addWidget(help_btn)
        main_layout.addLayout(header_layout)

        # 카메라 영역 (화면에 표시될 위치)
        frame_label = QLabel("카메라 영역 (화면에 표시될 위치)")
        frame_label.setAlignment(Qt.AlignCenter)
        frame_label.setStyleSheet("font-weight: bold; color: #27ae60; margin-top: 4px;")
        main_layout.addWidget(frame_label)

        self.frame_input = PositionSizeInput()
        self.frame_input.set_values(
            self.config["frame"]["x"],
            self.config["frame"]["y"],
            self.config["frame"]["width"],
            self.config["frame"]["height"]
        )
        self.frame_input.value_changed.connect(self._update_screen_preview)
        main_layout.addWidget(self.frame_input, 0, Qt.AlignCenter)

        frame_btn_layout = QHBoxLayout()
        frame_btn_layout.addStretch()
        fill_btn = QPushButton("채우기")
        fill_btn.setFixedWidth(80)
        fill_btn.clicked.connect(self._fill_camera_frame)
        center_btn = QPushButton("가운데")
        center_btn.setFixedWidth(80)
        center_btn.clicked.connect(self._center_camera_frame)
        frame_btn_layout.addWidget(fill_btn)
        frame_btn_layout.addWidget(center_btn)
        frame_btn_layout.addStretch()
        main_layout.addLayout(frame_btn_layout)

        # 구분선
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #ddd; margin: 8px 0;")
        main_layout.addWidget(sep)

        # 선택 영역 (인쇄할 부분)
        crop_label = QLabel("선택 영역 (카메라 내에서 인쇄할 부분)")
        crop_label.setAlignment(Qt.AlignCenter)
        crop_label.setStyleSheet("font-weight: bold; color: #FF6B00;")
        main_layout.addWidget(crop_label)

        self.crop_input = PositionSizeInput()
        self.crop_input.set_values(
            self.config["crop_area"]["x"],
            self.config["crop_area"]["y"],
            self.config["crop_area"]["width"],
            self.config["crop_area"]["height"]
        )
        self.crop_input.value_changed.connect(self._on_crop_changed)
        main_layout.addWidget(self.crop_input, 0, Qt.AlignCenter)

        # 비율 정보 표시
        self.crop_ratio_label = QLabel()
        self.crop_ratio_label.setAlignment(Qt.AlignCenter)
        self.crop_ratio_label.setStyleSheet("color: #666; font-size: 11px;")
        main_layout.addWidget(self.crop_ratio_label)

        crop_btn_layout = QHBoxLayout()
        crop_btn_layout.addStretch()
        crop_fill_btn = QPushButton("전체 선택")
        crop_fill_btn.setFixedWidth(90)
        crop_fill_btn.setToolTip("카메라 전체 영역을 선택합니다")
        crop_fill_btn.clicked.connect(self._fill_crop_area)
        crop_center_btn = QPushButton("가운데 정렬")
        crop_center_btn.setFixedWidth(90)
        crop_center_btn.setToolTip("선택 영역을 카메라 중앙으로 이동합니다")
        crop_center_btn.clicked.connect(self._center_crop_area)
        crop_btn_layout.addWidget(crop_fill_btn)
        crop_btn_layout.addWidget(crop_center_btn)
        crop_btn_layout.addStretch()
        main_layout.addLayout(crop_btn_layout)

        self._update_crop_ratio_info()

        parent_layout.addWidget(main_group)

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

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        fill_btn = QPushButton("채우기")
        fill_btn.setFixedWidth(80)
        fill_btn.clicked.connect(self._fill_photo_frame)
        center_btn = QPushButton("가운데")
        center_btn.setFixedWidth(80)
        center_btn.clicked.connect(self._center_photo_frame)
        btn_layout.addWidget(fill_btn)
        btn_layout.addWidget(center_btn)
        btn_layout.addStretch()
        photo_layout.addLayout(btn_layout)

        parent_layout.addWidget(photo_group)

    # ═══════════════════════════════════════════════════════════════
    # 탭 3: 카메라 카운트
    # ═══════════════════════════════════════════════════════════════
    def _create_camera_count_tab(self):
        """카메라 카운트 설정 탭 생성"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(20, 20, 20, 20)
        tab_layout.setSpacing(20)

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

        tab_layout.addWidget(count_group)
        tab_layout.addStretch()

        self.sub_tabs.addTab(tab_widget, "카메라 카운트")

    # ═══════════════════════════════════════════════════════════════
    # 미리보기 영역
    # ═══════════════════════════════════════════════════════════════
    def _init_screen_preview(self, parent_layout):
        group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(group)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("녹색 = 카메라 영역  |  주황색 = 인쇄될 선택 영역")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        layout.addWidget(desc)

        self.screen_preview = LivePreviewWidget(preview_size=QSize(350, 350))
        self.screen_preview.position_changed.connect(self._on_frame_position_changed)
        self.screen_preview.size_changed.connect(self._on_frame_size_changed)
        layout.addWidget(self.screen_preview, 0, Qt.AlignCenter)

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

        desc = QLabel("빨간색 영역 = 촬영된 사진이 인쇄될 위치")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold; padding: 4px;")
        layout.addWidget(desc)

        self.card_preview = LivePreviewWidget(preview_size=QSize(350, 350))
        self.card_preview.position_changed.connect(self._on_photo_position_changed)
        self.card_preview.size_changed.connect(self._on_photo_size_changed)
        layout.addWidget(self.card_preview, 0, Qt.AlignCenter)

        # 안내 문구
        card_info = QLabel("※ 검정 테두리가 실제 인쇄되는 카드 영역입니다.")
        card_info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(card_info, 0, Qt.AlignCenter)

        hint = QLabel("빨간색 영역을 드래그하여 위치/크기 조절")
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
            background-color: #f0f4f8;
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
        self.request_real_time_update()

    def _center_crop_area(self):
        res = self.camera_resolution_combo.currentData()
        if res:
            x, y, w, h = self.crop_input.get_values()
            self.crop_input.set_x((res[0] - w) // 2)
            self.crop_input.set_y((res[1] - h) // 2)
        self.request_real_time_update()

    def _fill_camera_frame(self):
        try:
            mw = self.config["screen_size"]["width"]
            mh = self.config["screen_size"]["height"]
        except KeyError:
            mw, mh = 1080, 1920
        self.frame_input.set_values(0, 0, mw, mh)
        self.request_real_time_update()

    def _center_camera_frame(self):
        try:
            mw = self.config["screen_size"]["width"]
            mh = self.config["screen_size"]["height"]
        except KeyError:
            mw, mh = 1080, 1920
        x, y, w, h = self.frame_input.get_values()
        self.frame_input.set_x((mw - w) // 2)
        self.frame_input.set_y((mh - h) // 2)
        self.request_real_time_update()

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
        if not self.screen_preview:
            return

        try:
            mw = self.config["screen_size"]["width"]
            mh = self.config["screen_size"]["height"]
        except KeyError:
            mw, mh = 1080, 1920

        self.screen_preview.set_original_size(mw, mh)
        bg_path = FileHandler.resolve_background_path(CAPTURE_SCREEN_KEY)
        self.screen_preview.set_background(bg_path, QColor("#1a1a1a"))

        x, y, w, h = self.frame_input.get_values()
        self.screen_preview.add_element(
            "camera_frame", QRect(x, y, w, h),
            color=QColor("lime"), label="카메라", draggable=True
        )

        if hasattr(self, 'crop_input'):
            crop_x, crop_y, crop_w, crop_h = self.crop_input.get_values()
            cam_res = self.camera_resolution_combo.currentData()
            if cam_res and cam_res[0] > 0 and cam_res[1] > 0:
                scale_x = w / cam_res[0]
                scale_y = h / cam_res[1]
                display_crop_x = x + int(crop_x * scale_x)
                display_crop_y = y + int(crop_y * scale_y)
                display_crop_w = int(crop_w * scale_x)
                display_crop_h = int(crop_h * scale_y)

                self.screen_preview.add_element(
                    "crop_area", QRect(display_crop_x, display_crop_y, display_crop_w, display_crop_h),
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
