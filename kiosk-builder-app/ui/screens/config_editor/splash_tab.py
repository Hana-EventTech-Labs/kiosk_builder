from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QWidget, QGridLayout, QFrame,
                              QCheckBox, QTabWidget, QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QColor
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import TextPreviewWidget, LivePreviewWidget
from ui.components.collapsible_group import CollapsibleGroupBox
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# 스플래시 화면 screen_key = "splash" (0)
SPLASH_SCREEN_KEY = "splash"

class SplashTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.screen_preview = None
        # 언어 버튼 필드
        self.lang_fields = {"ko": {}, "en": {}}
        # 언어별 배경화면 필드 (인라인)
        self.lang_bg_fields = {"ko": {}, "en": {}}
        self.init_ui()

    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        scroll_content_layout = self.create_tab_with_scroll()

        # 메인 레이아웃 (좌: 설정, 우: 미리보기)
        main_layout = QHBoxLayout()
        scroll_content_layout.addLayout(main_layout)

        # 설정 영역
        settings_widget = QWidget()
        content_layout = QVBoxLayout(settings_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 스플래시 화면 설정
        splash_group = QGroupBox("스플래쉬 화면 설정")
        self.apply_left_aligned_group_style(splash_group)
        splash_layout = QFormLayout(splash_group)
        
        # 필드 저장을 위한 딕셔너리
        self.splash_fields = {}
        
        # 배경화면 선택 레이아웃 추가 (? 도움말 버튼 포함)
        bg_header_layout = QHBoxLayout()
        bg_label = QLabel("배경화면:")
        bg_header_layout.addWidget(bg_label)
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
        bg_header_layout.addWidget(help_btn)
        bg_header_layout.addStretch()
        splash_layout.addRow(bg_header_layout)

        background_layout = QHBoxLayout()
        # 실제 저장된 배경화면 파일명 로드
        saved_bg = FileHandler.get_background_display_name(SPLASH_SCREEN_KEY)
        background_edit = QLineEdit(saved_bg)
        background_edit.setReadOnly(True)
        background_edit.setPlaceholderText("배경화면 없음")
        background_layout.addWidget(background_edit, 1)
        self.splash_fields["background"] = background_edit

        # 배경화면 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(self._browse_and_update_background)
        background_layout.addWidget(browse_button)

        # 초기화 버튼 추가
        reset_button = QPushButton("초기화")
        reset_button.setFixedWidth(60)
        reset_button.setToolTip("배경화면을 삭제합니다")
        reset_button.clicked.connect(self._reset_background)
        background_layout.addWidget(reset_button)

        # 배경화면 변경 시 미리보기 업데이트
        background_edit.textChanged.connect(self._update_screen_preview)

        splash_layout.addRow("", background_layout)

        # 한국어 배경화면 (인라인)
        ko_bg_layout = QHBoxLayout()
        saved_ko_bg = FileHandler.get_background_display_name(SPLASH_SCREEN_KEY, lang="ko")
        ko_bg_edit = QLineEdit(saved_ko_bg)
        ko_bg_edit.setReadOnly(True)
        ko_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        ko_bg_edit.textChanged.connect(self._update_screen_preview)
        ko_bg_layout.addWidget(ko_bg_edit, 1)
        self.lang_bg_fields["ko"]["background"] = ko_bg_edit
        ko_browse_btn = QPushButton("찾기...")
        ko_browse_btn.clicked.connect(lambda: self._browse_lang_bg("ko"))
        ko_bg_layout.addWidget(ko_browse_btn)
        ko_reset_btn = QPushButton("초기화")
        ko_reset_btn.setFixedWidth(60)
        ko_reset_btn.clicked.connect(lambda: self._reset_lang_bg("ko"))
        ko_bg_layout.addWidget(ko_reset_btn)
        splash_layout.addRow("🇰🇷 한국어:", ko_bg_layout)

        # 영어 배경화면 (인라인)
        en_bg_layout = QHBoxLayout()
        saved_en_bg = FileHandler.get_background_display_name(SPLASH_SCREEN_KEY, lang="en")
        en_bg_edit = QLineEdit(saved_en_bg)
        en_bg_edit.setReadOnly(True)
        en_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        en_bg_edit.textChanged.connect(self._update_screen_preview)
        en_bg_layout.addWidget(en_bg_edit, 1)
        self.lang_bg_fields["en"]["background"] = en_bg_edit
        en_browse_btn = QPushButton("찾기...")
        en_browse_btn.clicked.connect(lambda: self._browse_lang_bg("en"))
        en_bg_layout.addWidget(en_browse_btn)
        en_reset_btn = QPushButton("초기화")
        en_reset_btn.setFixedWidth(60)
        en_reset_btn.clicked.connect(lambda: self._reset_lang_bg("en"))
        en_bg_layout.addWidget(en_reset_btn)
        splash_layout.addRow("🇺🇸 English:", en_bg_layout)
        
        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["splash"]["font"])
        font_layout.addWidget(font_edit, 1)  # 1은 stretch factor로, 남은 공간을 차지하도록 함
        self.splash_fields["font"] = font_edit
        
        # 폰트 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_font_file(self, font_edit))
        font_layout.addWidget(browse_button)
        
        splash_layout.addRow("폰트:", font_layout)
        
        phrase_edit = QLineEdit(self.config["splash"]["phrase"])
        phrase_edit.textChanged.connect(self._update_screen_preview)
        splash_layout.addRow("문구:", phrase_edit)
        self.splash_fields["phrase"] = phrase_edit

        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config["splash"]["font_size"])
        font_size_edit.textChanged.connect(self._update_screen_preview)
        splash_layout.addRow("폰트 크기:", font_size_edit)
        self.splash_fields["font_size"] = font_size_edit

        font_color_button = ColorPickerButton(self.config["splash"]["font_color"])
        font_color_button.color_changed.connect(self._update_screen_preview)
        splash_layout.addRow("폰트 색상:", font_color_button)
        self.splash_fields["font_color"] = font_color_button

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        splash_layout.addRow(separator)

        # 텍스트 위치 (직관적 라벨)
        position_label = QLabel("📍 텍스트 위치")
        position_label.setStyleSheet("font-weight: bold; color: #555;")
        splash_layout.addRow(position_label)

        # 위치 입력 영역 (스타일 적용)
        position_widget = QWidget()
        position_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        position_layout = QGridLayout(position_widget)
        position_layout.setContentsMargins(12, 8, 12, 8)
        position_layout.setSpacing(8)

        # 가로 (X)
        x_label = QLabel("가로 →")
        x_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        x_label.setFixedWidth(50)
        x_edit = NumberLineEdit()
        x_edit.setFixedWidth(70)
        x_edit.setValue(self.config["splash"]["x"])
        x_edit.setToolTip("왼쪽에서부터의 거리 (픽셀)")
        x_edit.textChanged.connect(self._update_screen_preview)
        position_layout.addWidget(x_label, 0, 0)
        position_layout.addWidget(x_edit, 0, 1)
        self.splash_fields["x"] = x_edit

        # 세로 (Y)
        y_label = QLabel("세로 ↓")
        y_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        y_label.setFixedWidth(50)
        y_edit = NumberLineEdit()
        y_edit.setFixedWidth(70)
        y_edit.setValue(self.config["splash"]["y"])
        y_edit.setToolTip("위에서부터의 거리 (픽셀)")
        y_edit.textChanged.connect(self._update_screen_preview)
        position_layout.addWidget(y_label, 1, 0)
        position_layout.addWidget(y_edit, 1, 1)
        self.splash_fields["y"] = y_edit

        position_layout.setColumnStretch(2, 1)  # 나머지 공간
        splash_layout.addRow(position_widget)

        content_layout.addWidget(splash_group)

        # ═══════════════════════════════════════════════════════════
        # 언어 선택 설정 그룹
        # ═══════════════════════════════════════════════════════════
        lang_collapsible = CollapsibleGroupBox("🌐 언어 선택 버튼 설정", collapsed=True)
        lang_widget = QWidget()
        lang_main_layout = QVBoxLayout(lang_widget)
        lang_main_layout.setContentsMargins(0, 0, 0, 0)
        lang_main_layout.setSpacing(10)

        # 언어 선택 활성화 체크박스
        self.lang_enabled_checkbox = QCheckBox("언어 선택 기능 사용")
        self.lang_enabled_checkbox.setChecked(self.config.get("language", {}).get("enabled", False))
        self.lang_enabled_checkbox.stateChanged.connect(self._on_lang_enabled_changed)
        lang_main_layout.addWidget(self.lang_enabled_checkbox)

        # 언어 버튼 설정 탭
        self.lang_tab_widget = QTabWidget()
        self.lang_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2563eb;
                color: white;
                border-radius: 4px 4px 0 0;
            }
        """)

        # 한글 버튼 탭
        ko_tab = self._create_lang_button_tab("ko", "한글 버튼")
        self.lang_tab_widget.addTab(ko_tab, "🇰🇷 한글 버튼")

        # 영어 버튼 탭
        en_tab = self._create_lang_button_tab("en", "English 버튼")
        self.lang_tab_widget.addTab(en_tab, "🇺🇸 English 버튼")

        lang_main_layout.addWidget(self.lang_tab_widget)

        # 활성화 상태에 따라 탭 위젯 표시/숨김
        self.lang_tab_widget.setVisible(self.lang_enabled_checkbox.isChecked())

        lang_collapsible.addWidget(lang_widget)
        content_layout.addWidget(lang_collapsible)

        # 스트레치 추가
        content_layout.addStretch()

        # 좌측 설정 영역을 메인 레이아웃에 추가
        main_layout.addWidget(settings_widget, 1)

        # 우측 미리보기 영역
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # 화면 미리보기
        screen_preview_group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(screen_preview_group)
        screen_preview_layout = QVBoxLayout(screen_preview_group)

        # 더 큰 미리보기 위젯 (400x400)
        self.screen_preview = TextPreviewWidget(preview_size=QSize(400, 400))
        self.screen_preview.position_changed.connect(self._on_text_position_changed)
        self.screen_preview.text_size_changed.connect(self._on_text_size_changed)
        screen_preview_layout.addWidget(self.screen_preview, 0, Qt.AlignHCenter)

        preview_layout.addWidget(screen_preview_group)
        preview_layout.addStretch()

        main_layout.addWidget(preview_widget, 1)

        # 초기 미리보기 업데이트
        self._update_screen_preview()

    def _update_screen_preview(self):
        """화면 미리보기 업데이트"""
        if not self.screen_preview:
            return

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        # 원본 크기 설정
        self.screen_preview.set_original_size(monitor_width, monitor_height)

        # 배경 이미지 설정 - screen_key를 사용하여 실제 파일 경로 찾기
        bg_path = FileHandler.resolve_background_path(SPLASH_SCREEN_KEY)
        self.screen_preview.set_background(bg_path, QColor("#1a1a1a"))

        # 기존 언어 버튼 요소 제거
        self.screen_preview.remove_element("lang_btn_ko")
        self.screen_preview.remove_element("lang_btn_en")

        # 텍스트 설정
        try:
            text = self.splash_fields["phrase"].text()
            font_path = self.splash_fields["font"].text()
            font_size = self.splash_fields["font_size"].value()
            font_color = self.splash_fields["font_color"].color
            x = self.splash_fields["x"].value()
            y = self.splash_fields["y"].value()

            self.screen_preview.add_text(
                "splash_text",
                text,
                x, y,
                font_path=font_path,
                font_size=font_size,
                color=QColor(font_color),
                draggable=True
            )
        except (AttributeError, KeyError):
            pass

        # 언어 선택 버튼 표시 (활성화된 경우)
        if hasattr(self, 'lang_enabled_checkbox') and self.lang_enabled_checkbox.isChecked():
            self._add_lang_buttons_to_preview()

        self.request_real_time_update()

    def _add_lang_buttons_to_preview(self):
        """언어 선택 버튼을 미리보기에 추가"""
        # 시그널 연결 (한 번만)
        try:
            self.screen_preview.position_changed.disconnect(self._on_lang_button_position_changed)
            self.screen_preview.size_changed.disconnect(self._on_lang_button_size_changed)
        except (RuntimeError, TypeError):
            pass

        self.screen_preview.position_changed.connect(self._on_lang_button_position_changed)
        self.screen_preview.size_changed.connect(self._on_lang_button_size_changed)

        for lang_code in ["ko", "en"]:
            fields = self.lang_fields.get(lang_code, {})
            if not fields:
                continue

            try:
                x = fields["x"].value()
                y = fields["y"].value()
                width = fields["width"].value()
                height = fields["height"].value()
                bg_color = QColor(fields["bg_color"].color)

                # 버튼 영역을 사각형으로 표시
                btn_rect = QRect(x, y, width, height)

                # 레이블에 버튼 텍스트 표시
                btn_text = fields["text"].text()

                self.screen_preview.add_element(
                    f"lang_btn_{lang_code}",
                    btn_rect,
                    color=bg_color,
                    draggable=True,
                    resizable=True,
                    label=btn_text,
                    border_width=3
                )
            except (AttributeError, KeyError):
                pass

    def _on_text_position_changed(self, element_id, x, y):
        """드래그로 텍스트 위치 변경 시 호출"""
        if element_id == "splash_text":
            self.splash_fields['x'].blockSignals(True)
            self.splash_fields['y'].blockSignals(True)

            self.splash_fields['x'].setValue(x)
            self.splash_fields['y'].setValue(y)

            self.splash_fields['x'].blockSignals(False)
            self.splash_fields['y'].blockSignals(False)

            self.request_real_time_update()

    def _on_text_size_changed(self, element_id, new_size):
        """드래그로 텍스트 크기 변경 시 호출"""
        if element_id == "splash_text":
            self.splash_fields['font_size'].blockSignals(True)
            self.splash_fields['font_size'].setValue(new_size)
            self.splash_fields['font_size'].blockSignals(False)
            self.request_real_time_update()

    def _browse_and_update_background(self):
        """배경화면 파일 선택 후 표시 업데이트"""
        FileHandler.browse_background_file(self, self.splash_fields["background"], SPLASH_SCREEN_KEY)
        # 선택 후 실제 저장된 파일명으로 업데이트
        saved_bg = FileHandler.get_background_display_name(SPLASH_SCREEN_KEY)
        self.splash_fields["background"].setText(saved_bg)
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
            FileHandler.delete_background(SPLASH_SCREEN_KEY)
            self.splash_fields["background"].setText("")
            self._update_screen_preview()

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

    def _browse_lang_bg(self, lang_code: str):
        """언어별 배경화면 파일 선택 (인라인)"""
        bg_edit = self.lang_bg_fields[lang_code].get("background")
        if bg_edit:
            FileHandler.browse_background_file(self, bg_edit, SPLASH_SCREEN_KEY, lang=lang_code)
            saved_bg = FileHandler.get_background_display_name(SPLASH_SCREEN_KEY, lang=lang_code)
            bg_edit.setText(saved_bg)
            self._update_screen_preview()

    def _reset_lang_bg(self, lang_code: str):
        """언어별 배경화면 초기화 (인라인)"""
        from PySide6.QtWidgets import QMessageBox
        lang_name = "한국어" if lang_code == "ko" else "영어"
        reply = QMessageBox.question(
            self, f"{lang_name} 배경화면 초기화",
            f"{lang_name} 시작화면의 배경화면을 삭제하시겠습니까?\n삭제 시 기본 배경화면이 사용됩니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(SPLASH_SCREEN_KEY, lang=lang_code)
            bg_edit = self.lang_bg_fields[lang_code].get("background")
            if bg_edit:
                bg_edit.setText("")
            self._update_screen_preview()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        for key, widget in self.splash_fields.items():
            if isinstance(widget, ColorPickerButton):
                widget.update_color(config["splash"][key])
            else:
                if isinstance(widget, NumberLineEdit):
                    widget.setValue(config["splash"][key])
                else:
                    widget.setText(config["splash"][key])

        # 미리보기 업데이트
        self._update_screen_preview()
    
    def update_config(self, config):
        """UI 값을 config에 반영"""
        for key, widget in self.splash_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["splash"][key] = widget.color
            else:
                if isinstance(widget, NumberLineEdit):
                    config["splash"][key] = widget.value()
                else:
                    config["splash"][key] = widget.text()

        # 언어 설정 반영
        if "language" not in config:
            config["language"] = {}

        config["language"]["enabled"] = self.lang_enabled_checkbox.isChecked()

        # 각 언어 버튼 설정 반영
        for lang in ["ko", "en"]:
            btn_key = f"{lang}_button"
            if btn_key not in config["language"]:
                config["language"][btn_key] = {}

            fields = self.lang_fields[lang]
            for key, widget in fields.items():
                if isinstance(widget, ColorPickerButton):
                    config["language"][btn_key][key] = widget.color
                elif isinstance(widget, NumberLineEdit):
                    config["language"][btn_key][key] = widget.value()
                elif isinstance(widget, QLineEdit):
                    config["language"][btn_key][key] = widget.text()

    # ═══════════════════════════════════════════════════════════
    # 언어 선택 버튼 설정 UI
    # ═══════════════════════════════════════════════════════════

    def _create_lang_button_tab(self, lang_code: str, button_label: str) -> QWidget:
        """언어 버튼 설정 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # config에서 버튼 설정 로드
        lang_config = self.config.get("language", {})
        btn_config = lang_config.get(f"{lang_code}_button", {})

        # 기본값 설정
        defaults = {
            "text": "한글" if lang_code == "ko" else "English",
            "x": 340,
            "y": 800 if lang_code == "ko" else 960,
            "width": 400,
            "height": 120,
            "font_size": 48,
            "font_color": "#ffffff",
            "bg_color": "#2563eb" if lang_code == "ko" else "#059669",
            "border_color": "#1d4ed8" if lang_code == "ko" else "#047857",
            "border_width": 3,
            "border_radius": 15
        }

        # 버튼 텍스트
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("버튼 텍스트:"))
        text_edit = QLineEdit(btn_config.get("text", defaults["text"]))
        text_edit.textChanged.connect(self._update_screen_preview)
        text_layout.addWidget(text_edit, 1)
        layout.addLayout(text_layout)
        self.lang_fields[lang_code]["text"] = text_edit

        # 구분선
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background-color: #ddd;")
        layout.addWidget(sep1)

        # 위치 및 크기 설정
        pos_label = QLabel("📍 위치 및 크기")
        pos_label.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(pos_label)

        pos_widget = QWidget()
        pos_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        pos_grid = QGridLayout(pos_widget)
        pos_grid.setContentsMargins(12, 8, 12, 8)
        pos_grid.setSpacing(8)

        # X 위치
        x_label = QLabel("가로 →")
        x_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        x_edit = NumberLineEdit()
        x_edit.setFixedWidth(70)
        x_edit.setValue(btn_config.get("x", defaults["x"]))
        x_edit.textChanged.connect(self._update_screen_preview)
        pos_grid.addWidget(x_label, 0, 0)
        pos_grid.addWidget(x_edit, 0, 1)
        self.lang_fields[lang_code]["x"] = x_edit

        # Y 위치
        y_label = QLabel("세로 ↓")
        y_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        y_edit = NumberLineEdit()
        y_edit.setFixedWidth(70)
        y_edit.setValue(btn_config.get("y", defaults["y"]))
        y_edit.textChanged.connect(self._update_screen_preview)
        pos_grid.addWidget(y_label, 1, 0)
        pos_grid.addWidget(y_edit, 1, 1)
        self.lang_fields[lang_code]["y"] = y_edit

        # 너비
        w_label = QLabel("너비")
        w_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        w_edit = NumberLineEdit()
        w_edit.setFixedWidth(70)
        w_edit.setValue(btn_config.get("width", defaults["width"]))
        w_edit.textChanged.connect(self._update_screen_preview)
        pos_grid.addWidget(w_label, 0, 2)
        pos_grid.addWidget(w_edit, 0, 3)
        self.lang_fields[lang_code]["width"] = w_edit

        # 높이
        h_label = QLabel("높이")
        h_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        h_edit = NumberLineEdit()
        h_edit.setFixedWidth(70)
        h_edit.setValue(btn_config.get("height", defaults["height"]))
        h_edit.textChanged.connect(self._update_screen_preview)
        pos_grid.addWidget(h_label, 1, 2)
        pos_grid.addWidget(h_edit, 1, 3)
        self.lang_fields[lang_code]["height"] = h_edit

        pos_grid.setColumnStretch(4, 1)
        layout.addWidget(pos_widget)

        # 구분선
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: #ddd;")
        layout.addWidget(sep2)

        # 스타일 설정
        style_label = QLabel("🎨 스타일")
        style_label.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(style_label)

        style_form = QFormLayout()
        style_form.setSpacing(8)

        # 폰트 크기
        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(btn_config.get("font_size", defaults["font_size"]))
        font_size_edit.textChanged.connect(self._update_screen_preview)
        style_form.addRow("폰트 크기:", font_size_edit)
        self.lang_fields[lang_code]["font_size"] = font_size_edit

        # 폰트 색상
        font_color_btn = ColorPickerButton(btn_config.get("font_color", defaults["font_color"]))
        font_color_btn.color_changed.connect(self._update_screen_preview)
        style_form.addRow("폰트 색상:", font_color_btn)
        self.lang_fields[lang_code]["font_color"] = font_color_btn

        # 배경 색상
        bg_color_btn = ColorPickerButton(btn_config.get("bg_color", defaults["bg_color"]))
        bg_color_btn.color_changed.connect(self._update_screen_preview)
        style_form.addRow("배경 색상:", bg_color_btn)
        self.lang_fields[lang_code]["bg_color"] = bg_color_btn

        # 테두리 색상
        border_color_btn = ColorPickerButton(btn_config.get("border_color", defaults["border_color"]))
        border_color_btn.color_changed.connect(self._update_screen_preview)
        style_form.addRow("테두리 색상:", border_color_btn)
        self.lang_fields[lang_code]["border_color"] = border_color_btn

        # 테두리 두께
        border_width_edit = NumberLineEdit()
        border_width_edit.setValue(btn_config.get("border_width", defaults["border_width"]))
        border_width_edit.textChanged.connect(self._update_screen_preview)
        style_form.addRow("테두리 두께:", border_width_edit)
        self.lang_fields[lang_code]["border_width"] = border_width_edit

        # 테두리 둥글기
        border_radius_edit = NumberLineEdit()
        border_radius_edit.setValue(btn_config.get("border_radius", defaults["border_radius"]))
        border_radius_edit.textChanged.connect(self._update_screen_preview)
        style_form.addRow("테두리 둥글기:", border_radius_edit)
        self.lang_fields[lang_code]["border_radius"] = border_radius_edit

        layout.addLayout(style_form)
        layout.addStretch()

        return tab

    def _on_lang_enabled_changed(self, state):
        """언어 선택 활성화 상태 변경"""
        enabled = state == Qt.CheckState.Checked.value
        self.lang_tab_widget.setVisible(enabled)
        self._update_screen_preview()
        self.request_real_time_update()

    def _on_lang_button_position_changed(self, element_id, x, y):
        """드래그로 언어 버튼 위치 변경 시 호출"""
        if element_id.startswith("lang_btn_"):
            lang_code = element_id.replace("lang_btn_", "")
            if lang_code in self.lang_fields:
                fields = self.lang_fields[lang_code]
                fields['x'].blockSignals(True)
                fields['y'].blockSignals(True)
                fields['x'].setValue(x)
                fields['y'].setValue(y)
                fields['x'].blockSignals(False)
                fields['y'].blockSignals(False)
                self.request_real_time_update()

    def _on_lang_button_size_changed(self, element_id, x, y, width, height):
        """드래그로 언어 버튼 크기 변경 시 호출"""
        if element_id.startswith("lang_btn_"):
            lang_code = element_id.replace("lang_btn_", "")
            if lang_code in self.lang_fields:
                fields = self.lang_fields[lang_code]
                for key in ['x', 'y', 'width', 'height']:
                    fields[key].blockSignals(True)
                fields['x'].setValue(x)
                fields['y'].setValue(y)
                fields['width'].setValue(width)
                fields['height'].setValue(height)
                for key in ['x', 'y', 'width', 'height']:
                    fields[key].blockSignals(False)
                self.request_real_time_update()

