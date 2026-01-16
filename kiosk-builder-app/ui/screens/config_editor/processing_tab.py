from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QWidget, QTabWidget,
                              QDialog, QDialogButtonBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import TextPreviewWidget
from ui.components.zoomable_preview import ZoomablePreviewWidget, DEFAULT_PREVIEW_SIZE
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# 발급중 화면 screen_key = "5" (또는 "process")
PROCESSING_SCREEN_KEY = "5"

class ProcessingTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.screen_preview_screen = None  # 화면 설정 탭용
        self.screen_preview_text = None    # 텍스트 설정 탭용
        self.sub_tabs = None
        # 언어별 배경화면 필드
        self.lang_bg_fields = {"ko": {}, "en": {}}
        # 언어별 미리보기 선택
        self._current_lang_preview = None  # None=기본, "ko"=한국어, "en"=영어
        self.init_ui()

    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        content_layout = self.create_tab_with_scroll()

        # ═══════════════════════════════════════════════════════════════
        # 서브 탭 위젯 (각 탭 내부에 설정+미리보기)
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

        # 탭 1: 화면 설정 (배경)
        self._create_screen_settings_tab()

        # 탭 2: 텍스트 설정
        self._create_text_settings_tab()

        content_layout.addWidget(self.sub_tabs)
        content_layout.addStretch()

        # 라디오 버튼 초기 상태 설정
        self._update_preview_radio_visibility()

        # 초기 미리보기 업데이트
        self._update_screen_preview()

    # ═══════════════════════════════════════════════════════════════
    # 탭 1: 화면 설정
    # ═══════════════════════════════════════════════════════════════
    def _create_screen_settings_tab(self):
        """화면 설정 탭 생성 - 좌측(설정) + 우측(미리보기)"""
        tab_widget = QWidget()
        tab_main_layout = QHBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(10, 10, 10, 10)
        tab_main_layout.setSpacing(20)

        # 좌측: 설정 영역
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        self._init_background_settings(left_layout)
        left_layout.addStretch()

        tab_main_layout.addWidget(left_widget, 1)

        # 우측: 미리보기 영역
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("텍스트를 드래그하여 위치 조절 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_layout.addWidget(desc)

        # 단일 미리보기 위젯 + 확대/축소
        self.screen_preview_screen = TextPreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.screen_preview_screen.set_card_border(True, QColor("#333333"), 2)
        self.screen_preview_screen.position_changed.connect(self._on_text_position_changed)
        self._zoomable_screen_preview = ZoomablePreviewWidget(self.screen_preview_screen)
        preview_layout.addWidget(self._zoomable_screen_preview, 0, Qt.AlignCenter)

        right_layout.addWidget(preview_group)
        right_layout.addStretch()

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "화면 설정")

    # ═══════════════════════════════════════════════════════════════
    # 탭 2: 텍스트 설정
    # ═══════════════════════════════════════════════════════════════
    def _create_text_settings_tab(self):
        """텍스트 설정 탭 생성 - 좌측(설정) + 우측(미리보기)"""
        tab_widget = QWidget()
        tab_main_layout = QHBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(10, 10, 10, 10)
        tab_main_layout.setSpacing(20)

        # 좌측: 설정 영역
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 필드 저장을 위한 딕셔너리
        if not hasattr(self, 'process_fields'):
            self.process_fields = {}

        # 텍스트 설정 그룹
        text_group = QGroupBox("텍스트 설정")
        self.apply_left_aligned_group_style(text_group)
        text_layout = QFormLayout(text_group)
        text_layout.setSpacing(8)

        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["process"]["font"])
        font_layout.addWidget(font_edit, 1)
        self.process_fields["font"] = font_edit

        # 폰트 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_font_file(self, font_edit))
        font_layout.addWidget(browse_button)

        text_layout.addRow("폰트:", font_layout)

        phrase_edit = QLineEdit(self.config["process"]["phrase"])
        phrase_edit.textChanged.connect(self._update_screen_preview)
        text_layout.addRow("문구:", phrase_edit)
        self.process_fields["phrase"] = phrase_edit

        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config["process"]["font_size"])
        font_size_edit.textChanged.connect(self._update_screen_preview)
        text_layout.addRow("폰트 크기:", font_size_edit)
        self.process_fields["font_size"] = font_size_edit

        font_color_button = ColorPickerButton(self.config["process"]["font_color"])
        font_color_button.color_changed.connect(self._update_screen_preview)
        text_layout.addRow("폰트 색상:", font_color_button)
        self.process_fields["font_color"] = font_color_button

        x_edit = NumberLineEdit()
        x_edit.setValue(self.config["process"]["x"])
        x_edit.textChanged.connect(self._update_screen_preview)
        text_layout.addRow("X 위치:", x_edit)
        self.process_fields["x"] = x_edit

        y_edit = NumberLineEdit()
        y_edit.setValue(self.config["process"]["y"])
        y_edit.textChanged.connect(self._update_screen_preview)
        text_layout.addRow("Y 위치:", y_edit)
        self.process_fields["y"] = y_edit

        # 시간 필드
        time_edit = NumberLineEdit()
        time_edit.setValue(self.config["process"]["process_time"])
        text_layout.addRow("시간 (ms):", time_edit)
        self.process_fields["process_time"] = time_edit

        left_layout.addWidget(text_group)
        left_layout.addStretch()

        tab_main_layout.addWidget(left_widget, 1)

        # 우측: 미리보기 영역
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("텍스트를 드래그하여 위치 조절 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_layout.addWidget(desc)

        self.screen_preview_text = TextPreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.screen_preview_text.set_card_border(True, QColor("#333333"), 2)  # 검은 테두리 추가
        self.screen_preview_text.position_changed.connect(self._on_text_position_changed)
        self._zoomable_text_preview = ZoomablePreviewWidget(self.screen_preview_text)
        preview_layout.addWidget(self._zoomable_text_preview, 0, Qt.AlignCenter)

        hint = QLabel("발급 중 화면에 표시되는 미리보기입니다")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        preview_layout.addWidget(hint)

        right_layout.addWidget(preview_group)

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "텍스트 설정")

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

        # 필드 저장을 위한 딕셔너리 (텍스트 탭에서 생성되기 전에 초기화)
        if not hasattr(self, 'process_fields'):
            self.process_fields = {}

        # 기본 배경화면
        basic_label = QLabel("기본:")
        basic_label.setFixedWidth(LABEL_WIDTH)
        background_layout = QHBoxLayout()
        saved_bg = FileHandler.get_background_display_name(PROCESSING_SCREEN_KEY)
        background_edit = QLineEdit(saved_bg)
        background_edit.setReadOnly(True)
        background_edit.setPlaceholderText("배경화면 없음")
        background_layout.addWidget(background_edit, 1)
        self.process_fields["background"] = background_edit

        browse_button = QPushButton("찾기...")
        browse_button.setFixedWidth(60)
        browse_button.clicked.connect(self._browse_and_update_background)
        background_layout.addWidget(browse_button)

        reset_button = QPushButton("초기화")
        reset_button.setFixedWidth(60)
        reset_button.setToolTip("배경화면을 삭제합니다")
        reset_button.clicked.connect(self._reset_background)
        background_layout.addWidget(reset_button)
        bg_form.addRow(basic_label, background_layout)

        # 한국어 배경화면
        ko_label = QLabel("🇰🇷 한국어:")
        ko_label.setFixedWidth(LABEL_WIDTH)
        ko_bg_layout = QHBoxLayout()
        saved_ko_bg = FileHandler.get_background_display_name(PROCESSING_SCREEN_KEY, lang="ko")
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
        saved_en_bg = FileHandler.get_background_display_name(PROCESSING_SCREEN_KEY, lang="en")
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

        self.preview_button_group = QButtonGroup(self)
        self.radio_default = QRadioButton("기본")
        self.radio_ko = QRadioButton("한국어")
        self.radio_en = QRadioButton("English")
        self.radio_default.setChecked(True)

        self.preview_button_group.addButton(self.radio_default, 0)
        self.preview_button_group.addButton(self.radio_ko, 1)
        self.preview_button_group.addButton(self.radio_en, 2)

        self.preview_button_group.buttonClicked.connect(self._on_preview_lang_changed)

        preview_radio_layout.addWidget(self.radio_default)
        preview_radio_layout.addWidget(self.radio_ko)
        preview_radio_layout.addWidget(self.radio_en)
        preview_radio_layout.addStretch()
        bg_form.addRow(preview_label, preview_radio_layout)

        parent_layout.addWidget(bg_group)

    # ═══════════════════════════════════════════════════════════════
    # 미리보기 업데이트
    # ═══════════════════════════════════════════════════════════════
    def _update_screen_preview(self):
        """화면 미리보기 업데이트"""
        from PySide6.QtGui import QColor

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        # 텍스트 정보 수집
        phrase = self.process_fields.get("phrase")
        x_field = self.process_fields.get("x")
        y_field = self.process_fields.get("y")
        font_size_field = self.process_fields.get("font_size")
        font_color_field = self.process_fields.get("font_color")
        font_field = self.process_fields.get("font")

        text = phrase.text() if phrase and hasattr(phrase, 'text') else ""
        x = x_field.value() if x_field and hasattr(x_field, 'value') else 0
        y = y_field.value() if y_field and hasattr(y_field, 'value') else 0
        font_size = font_size_field.value() if font_size_field and hasattr(font_size_field, 'value') else 24
        font_color_str = font_color_field.color if font_color_field and hasattr(font_color_field, 'color') else "#000000"
        font_path = font_field.text() if font_field and hasattr(font_field, 'text') else None

        # 화면 설정 탭 미리보기 (라디오 버튼으로 선택된 언어)
        if self.screen_preview_screen:
            lang_enabled = self.config.get("language", {}).get("enabled", False)

            if lang_enabled:
                lang = getattr(self, '_current_lang_preview', "ko")
                if lang is None:
                    lang = "ko"
                bg_path = FileHandler.resolve_background_path(PROCESSING_SCREEN_KEY, lang=lang)
            else:
                bg_path = FileHandler.resolve_background_path(PROCESSING_SCREEN_KEY, lang=None)

            self.screen_preview_screen.set_original_size(monitor_width, monitor_height)
            self.screen_preview_screen.set_background(bg_path, QColor("#ffffff"))
            self.screen_preview_screen.set_card_border(True, QColor("#333333"), 2)
            self.screen_preview_screen.clear_texts()

            if text:
                self.screen_preview_screen.add_text(
                    element_id="process_text",
                    text=text,
                    x=x,
                    y=y,
                    font_path=font_path,
                    font_size=font_size,
                    color=QColor(font_color_str),
                    draggable=True,
                    resizable=False
                )
            self.screen_preview_screen.update()

        # 텍스트 설정 탭의 미리보기 위젯 업데이트
        if self.screen_preview_text:
            bg_path = FileHandler.resolve_background_path(PROCESSING_SCREEN_KEY)
            self.screen_preview_text.set_original_size(monitor_width, monitor_height)
            self.screen_preview_text.set_background(bg_path)
            self.screen_preview_text.clear_texts()

            if text:
                self.screen_preview_text.add_text(
                    element_id="process_text",
                    text=text,
                    x=x,
                    y=y,
                    font_path=font_path,
                    font_size=font_size,
                    color=QColor(font_color_str),
                    draggable=True,
                    resizable=False
                )
            self.screen_preview_text.update()

        # 실시간 업데이트 요청
        self.request_real_time_update()

    def _on_text_position_changed(self, text_id: str, x: int, y: int):
        """텍스트 위치 변경 시 호출"""
        if text_id == "process_text":
            x_field = self.process_fields.get("x")
            y_field = self.process_fields.get("y")

            if x_field and hasattr(x_field, 'setValue'):
                x_field.blockSignals(True)
                x_field.setValue(x)
                x_field.blockSignals(False)

            if y_field and hasattr(y_field, 'setValue'):
                y_field.blockSignals(True)
                y_field.setValue(y)
                y_field.blockSignals(False)

            # 다른 미리보기 위젯도 동기화
            self._update_screen_preview()
            self.request_real_time_update()

    def _browse_and_update_background(self):
        """배경화면 파일 선택 및 업데이트"""
        FileHandler.browse_background_file(self, self.process_fields["background"], PROCESSING_SCREEN_KEY)
        saved_bg = FileHandler.get_background_display_name(PROCESSING_SCREEN_KEY)
        self.process_fields["background"].setText(saved_bg)
        self._update_screen_preview()

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
            FileHandler.delete_background(PROCESSING_SCREEN_KEY)
            self.process_fields["background"].setText("")
            self._update_screen_preview()

    # ==================== 배경화면 도움말 및 언어별 배경화면 ====================
    def _show_bg_help_dialog(self):
        """배경화면 도움말 다이얼로그 표시"""
        dialog = QDialog(self)
        dialog.setWindowTitle("배경화면 설정 안내")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)

        info_text = QLabel(
            "<b>📌 배경화면 설정 안내</b><br><br>"
            "• <b>기본</b>: 기본 배경화면입니다. 언어별 배경화면이 없을 경우 사용됩니다.<br><br>"
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
            FileHandler.browse_background_file(self, bg_edit, PROCESSING_SCREEN_KEY, lang=lang_code)
            saved_bg = FileHandler.get_background_display_name(PROCESSING_SCREEN_KEY, lang=lang_code)
            bg_edit.setText(saved_bg)
            self._update_screen_preview()

    def _reset_lang_bg(self, lang_code: str):
        """언어별 배경화면 초기화"""
        from PySide6.QtWidgets import QMessageBox
        lang_name = "한국어" if lang_code == "ko" else "영어"
        reply = QMessageBox.question(
            self, f"{lang_name} 배경화면 초기화",
            f"{lang_name} 발급중 화면의 배경화면을 삭제하시겠습니까?\n삭제 시 기본 배경화면이 사용됩니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(PROCESSING_SCREEN_KEY, lang=lang_code)
            bg_edit = self.lang_bg_fields[lang_code].get("background")
            if bg_edit:
                bg_edit.setText("")
            self._update_screen_preview()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        for key, widget in self.process_fields.items():
            if isinstance(widget, ColorPickerButton):
                widget.update_color(config["process"][key])
            else:
                if isinstance(widget, NumberLineEdit):
                    widget.setValue(config["process"][key])
                else:
                    widget.setText(config["process"][key])

        # 라디오 버튼 활성화/비활성화 상태 업데이트
        self._update_preview_radio_visibility()

        # 미리보기 업데이트
        self._update_screen_preview()

    # ==================== 언어별 미리보기 라디오 버튼 ====================
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
        """언어 버튼 활성화 상태에 따라 라디오 버튼 활성화/비활성화"""
        lang_enabled = self.config.get("language", {}).get("enabled", False)

        if not hasattr(self, 'radio_default'):
            return

        if lang_enabled:
            self.radio_default.setEnabled(False)
            self.radio_ko.setEnabled(True)
            self.radio_en.setEnabled(True)

            if self.radio_default.isChecked():
                self.radio_ko.setChecked(True)

            if self.radio_ko.isChecked():
                self._current_lang_preview = "ko"
            elif self.radio_en.isChecked():
                self._current_lang_preview = "en"
        else:
            self.radio_default.setEnabled(True)
            self.radio_ko.setEnabled(False)
            self.radio_en.setEnabled(False)

            if not self.radio_default.isChecked():
                self.radio_default.setChecked(True)

            self._current_lang_preview = None

    def update_config(self, config):
        """UI 값을 config에 반영"""
        for key, widget in self.process_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["process"][key] = widget.color
            else:
                if isinstance(widget, NumberLineEdit):
                    config["process"][key] = widget.value()
                else:
                    config["process"][key] = widget.text()
