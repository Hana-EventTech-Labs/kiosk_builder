from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QWidget, QGridLayout, QFrame,
                              QCheckBox, QTabWidget)
from PySide6.QtCore import Qt, QSize, QRect, Signal
from PySide6.QtGui import QColor
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import TextPreviewWidget, render_button_element
from ui.components.zoomable_preview import ZoomablePreviewWidget, DEFAULT_PREVIEW_SIZE
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# 스플래시 화면 screen_key = "splash" (0)
SPLASH_SCREEN_KEY = "splash"

class SplashTab(BaseTab):
    # 언어 활성화 상태 변경 시그널 (다른 탭들에 알림용)
    language_enabled_changed = Signal(bool)

    def __init__(self, config):
        super().__init__(config)
        self.sub_tabs = None
        # 각 탭의 미리보기 위젯
        self.screen_preview_main = None  # 화면 설정 탭용
        self.screen_preview_lang = None  # 언어 선택 버튼 탭용
        # 언어 버튼 필드
        self.lang_fields = {"ko": {}, "en": {}}
        # 필드 저장을 위한 딕셔너리
        self.splash_fields = {}
        self.init_ui()

    def init_ui(self):
        # 스크롤 영역을 포함한 기본 레이아웃 생성
        scroll_content_layout = self.create_tab_with_scroll()

        # ═══════════════════════════════════════════════════════════════
        # 서브 탭 위젯 (2개 탭) - 각 탭 내부에 설정+미리보기 포함
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

        # 탭 1: 화면 설정 (배경 + 텍스트 통합)
        self._create_screen_settings_tab()

        # 탭 2: 언어 선택 버튼 설정
        self._create_language_button_tab()

        # 서브 탭 변경 시 미리보기 업데이트
        self.sub_tabs.currentChanged.connect(self._on_sub_tab_changed)

        scroll_content_layout.addWidget(self.sub_tabs)
        scroll_content_layout.addStretch()

        # 초기 미리보기 업데이트
        self._update_screen_preview()

    def _on_sub_tab_changed(self, index):
        """서브 탭 변경 시 해당 탭의 미리보기 업데이트"""
        self._update_screen_preview()

    # ═══════════════════════════════════════════════════════════════
    # 탭 1: 화면 설정 (배경 + 텍스트 통합)
    # ═══════════════════════════════════════════════════════════════
    def _create_screen_settings_tab(self):
        """화면 설정 탭 생성 - 좌측(배경+텍스트 설정) + 우측(미리보기)"""
        tab_widget = QWidget()
        tab_main_layout = QHBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(10, 10, 10, 10)
        tab_main_layout.setSpacing(20)

        # 좌측: 설정 영역
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 배경 설정
        self._init_background_settings(left_layout)
        # 텍스트 설정
        self._init_text_settings(left_layout)
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

        self.screen_preview_main = TextPreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.screen_preview_main.position_changed.connect(self._on_text_position_changed)
        self.screen_preview_main.text_size_changed.connect(self._on_text_size_changed)
        self._zoomable_preview_main = ZoomablePreviewWidget(self.screen_preview_main)
        preview_layout.addWidget(self._zoomable_preview_main, 0, Qt.AlignCenter)

        right_layout.addWidget(preview_group)

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "화면 설정")

    # ═══════════════════════════════════════════════════════════════
    # 탭 2: 언어 선택 버튼 설정
    # ═══════════════════════════════════════════════════════════════
    def _create_language_button_tab(self):
        """언어 선택 버튼 설정 탭 생성 - 좌측(설정) + 우측(미리보기)"""
        tab_widget = QWidget()
        tab_main_layout = QHBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(10, 10, 10, 10)
        tab_main_layout.setSpacing(20)

        # 좌측: 설정 영역
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        self._init_language_button_settings(left_layout)
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

        desc = QLabel("버튼을 드래그하여 위치 조절 | Ctrl+휠로 확대/축소")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_layout.addWidget(desc)

        self.screen_preview_lang = TextPreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.screen_preview_lang.position_changed.connect(self._on_text_position_changed)
        self.screen_preview_lang.text_size_changed.connect(self._on_text_size_changed)
        self._zoomable_preview_lang = ZoomablePreviewWidget(self.screen_preview_lang)
        preview_layout.addWidget(self._zoomable_preview_lang, 0, Qt.AlignCenter)

        right_layout.addWidget(preview_group)

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "언어 선택 버튼")

    # ═══════════════════════════════════════════════════════════════
    # 1. 배경 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_background_settings(self, parent_layout):
        """배경 설정 그룹 (스플래쉬는 언어 선택 전이므로 기본 배경만 설정)"""
        # 배경 설정 내용 그룹
        bg_group = QGroupBox("배경 설정")
        self.apply_left_aligned_group_style(bg_group)
        bg_form = QFormLayout(bg_group)
        bg_form.setSpacing(8)

        # 배경화면
        bg_row = QHBoxLayout()
        saved_bg = FileHandler.get_background_display_name(SPLASH_SCREEN_KEY)
        background_edit = QLineEdit(saved_bg)
        background_edit.setReadOnly(True)
        background_edit.setPlaceholderText("배경화면 없음")
        background_edit.textChanged.connect(self._update_screen_preview)
        bg_row.addWidget(background_edit, 1)
        self.splash_fields["background"] = background_edit

        browse_btn = QPushButton("찾기...")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_and_update_background)
        bg_row.addWidget(browse_btn)

        reset_btn = QPushButton("초기화")
        reset_btn.setFixedWidth(60)
        reset_btn.setToolTip("배경화면을 삭제합니다")
        reset_btn.clicked.connect(self._reset_background)
        bg_row.addWidget(reset_btn)
        bg_form.addRow("배경화면:", bg_row)

        parent_layout.addWidget(bg_group)

    # ═══════════════════════════════════════════════════════════════
    # 2. 텍스트 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_text_settings(self, parent_layout):
        """텍스트 설정 그룹"""
        text_group = QGroupBox("텍스트 설정")
        self.apply_left_aligned_group_style(text_group)
        text_layout = QFormLayout(text_group)
        text_layout.setSpacing(8)

        # 폰트 선택
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["splash"]["font"])
        font_layout.addWidget(font_edit, 1)
        self.splash_fields["font"] = font_edit
        browse_btn = QPushButton("찾기...")
        browse_btn.clicked.connect(lambda: FileHandler.browse_font_file(self, font_edit, self._update_screen_preview))
        font_layout.addWidget(browse_btn)
        text_layout.addRow("폰트:", font_layout)

        # 문구
        phrase_edit = QLineEdit(self.config["splash"]["phrase"])
        phrase_edit.textChanged.connect(self._update_screen_preview)
        text_layout.addRow("문구:", phrase_edit)
        self.splash_fields["phrase"] = phrase_edit

        # 폰트 크기
        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config["splash"]["font_size"])
        font_size_edit.textChanged.connect(self._update_screen_preview)
        text_layout.addRow("폰트 크기:", font_size_edit)
        self.splash_fields["font_size"] = font_size_edit

        # 폰트 색상
        font_color_btn = ColorPickerButton(self.config["splash"]["font_color"])
        font_color_btn.color_changed.connect(self._update_screen_preview)
        text_layout.addRow("폰트 색상:", font_color_btn)
        self.splash_fields["font_color"] = font_color_btn

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        text_layout.addRow(separator)

        # 텍스트 위치 라벨
        position_label = QLabel("📍 텍스트 위치")
        position_label.setStyleSheet("font-weight: bold; color: #555;")
        text_layout.addRow(position_label)

        # 위치 입력 영역
        position_widget = QWidget()
        position_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
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
        text_layout.addRow(position_widget)

        parent_layout.addWidget(text_group)

    # ═══════════════════════════════════════════════════════════════
    # 3. 언어 선택 버튼 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_language_button_settings(self, parent_layout):
        """언어 선택 버튼 설정"""
        # 언어 선택 활성화 체크박스
        self.lang_enabled_checkbox = QCheckBox("언어 선택 기능 사용")
        self.lang_enabled_checkbox.setChecked(self.config.get("language", {}).get("enabled", False))
        self.lang_enabled_checkbox.stateChanged.connect(self._on_lang_enabled_changed)
        parent_layout.addWidget(self.lang_enabled_checkbox)

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
        ko_tab = self._create_lang_button_detail_tab("ko", "한글 버튼")
        self.lang_tab_widget.addTab(ko_tab, "🇰🇷 한글 버튼")

        # 영어 버튼 탭
        en_tab = self._create_lang_button_detail_tab("en", "English 버튼")
        self.lang_tab_widget.addTab(en_tab, "🇺🇸 English 버튼")

        parent_layout.addWidget(self.lang_tab_widget)

        # 언어 버튼 탭 변경 시 미리보기 업데이트
        self.lang_tab_widget.currentChanged.connect(self._update_screen_preview)

        # 활성화 상태에 따라 탭 위젯 표시/숨김
        self.lang_tab_widget.setVisible(self.lang_enabled_checkbox.isChecked())

    # ═══════════════════════════════════════════════════════════════
    # 4. 화면 미리보기 업데이트 (2개 탭)
    # ═══════════════════════════════════════════════════════════════
    def _update_screen_preview(self):
        """화면 미리보기 업데이트 - 모든 탭의 미리보기 동기화"""
        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        # 배경 이미지 경로
        bg_path = FileHandler.resolve_background_path(SPLASH_SCREEN_KEY)

        # 텍스트 설정 가져오기
        try:
            text = self.splash_fields["phrase"].text()
            font_path = self.splash_fields["font"].text()
            font_size = self.splash_fields["font_size"].value()
            font_color = self.splash_fields["font_color"].color
            x = self.splash_fields["x"].value()
            y = self.splash_fields["y"].value()
            has_text = True
        except (AttributeError, KeyError):
            has_text = False

        # 언어 버튼 활성화 여부
        lang_enabled = hasattr(self, 'lang_enabled_checkbox') and self.lang_enabled_checkbox.isChecked()

        # 2개의 미리보기 위젯 업데이트
        for preview in [self.screen_preview_main, self.screen_preview_lang]:
            if not preview:
                continue

            preview.set_original_size(monitor_width, monitor_height)
            preview.set_background(bg_path, QColor("#ffffff"))
            preview.set_card_border(True, QColor("#333333"), 2)

            # 기존 언어 버튼 요소 제거
            preview.remove_element("lang_btn_ko")
            preview.remove_element("lang_btn_en")

            # 텍스트 설정
            if has_text:
                preview.add_text(
                    "splash_text",
                    text,
                    x, y,
                    font_path=font_path,
                    font_size=font_size,
                    color=QColor(font_color),
                    draggable=True
                )

            # 언어 선택 버튼 표시 (활성화된 경우)
            if lang_enabled:
                self._add_lang_buttons_to_preview_widget(preview)

        self.request_real_time_update()

    def _add_lang_buttons_to_preview_widget(self, preview_widget):
        """언어 선택 버튼을 특정 미리보기 위젯에 추가 (실제 버튼 스타일)"""
        # 시그널 연결 (UniqueConnection으로 중복 연결 방지)
        preview_widget.position_changed.connect(
            self._on_lang_button_position_changed, Qt.UniqueConnection)
        preview_widget.size_changed.connect(
            self._on_lang_button_size_changed, Qt.UniqueConnection)

        # 미리보기 스케일 가져오기
        scale = getattr(preview_widget, '_scale', 1.0)

        for lang_code in ["ko", "en"]:
            fields = self.lang_fields.get(lang_code, {})
            if not fields:
                continue

            try:
                x = fields["x"].value()
                y = fields["y"].value()
                width = fields["width"].value()
                height = fields["height"].value()

                # 버튼 영역
                btn_rect = QRect(x, y, width, height)

                # 버튼 스타일 데이터
                btn_text = fields["text"].text()
                bg_color = QColor(fields["bg_color"].color)
                border_color = QColor(fields["border_color"].color)
                font_color = QColor(fields["font_color"].color)
                border_width = fields["border_width"].value()
                border_radius = fields["border_radius"].value()
                font_size = fields["font_size"].value()

                # 미리보기 스케일 적용된 폰트 크기
                scaled_font_size = int(font_size / scale) if scale > 0 else font_size
                scaled_border_radius = int(border_radius / scale) if scale > 0 else border_radius

                renderer_data = {
                    'text': btn_text,
                    'bg_color': bg_color,
                    'border_color': border_color,
                    'border_width': max(1, int(border_width / scale)) if scale > 0 else border_width,
                    'border_radius': scaled_border_radius,
                    'font_color': font_color,
                    'font_size': scaled_font_size
                }

                preview_widget.add_element(
                    f"lang_btn_{lang_code}",
                    btn_rect,
                    color=bg_color,  # 선택 시 핸들 색상용
                    draggable=True,
                    resizable=True,
                    label=None,  # 레이블 제거 (버튼 내부에 텍스트 표시)
                    border_width=0,  # 기본 테두리 비활성화
                    custom_renderer=render_button_element,
                    renderer_data=renderer_data
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

        # 언어 설정 업데이트
        lang_config = config.get("language", {})
        if hasattr(self, 'lang_enabled_checkbox'):
            self.lang_enabled_checkbox.setChecked(lang_config.get("enabled", False))

        # 언어 버튼 필드 업데이트 (config에 저장된 값이 있으면)
        for lang in ["ko", "en"]:
            btn_key = f"{lang}_button"
            btn_config = lang_config.get(btn_key, {})
            fields = self.lang_fields.get(lang, {})

            for key, widget in fields.items():
                if key in btn_config:
                    if isinstance(widget, ColorPickerButton):
                        widget.update_color(btn_config[key])
                    elif isinstance(widget, NumberLineEdit):
                        widget.blockSignals(True)
                        widget.setValue(btn_config[key])
                        widget.blockSignals(False)
                    elif isinstance(widget, QLineEdit):
                        widget.blockSignals(True)
                        widget.setText(btn_config[key])
                        widget.blockSignals(False)

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

    def _create_lang_button_detail_tab(self, lang_code: str, button_label: str) -> QWidget:
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
                background-color: #ffffff;
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
        from PySide6.QtWidgets import QMessageBox
        enabled = state == Qt.CheckState.Checked.value
        self.lang_tab_widget.setVisible(enabled)

        # config에 즉시 반영 (다른 탭들이 참조할 수 있도록)
        if "language" not in self.config:
            self.config["language"] = {}
        self.config["language"]["enabled"] = enabled

        # 활성화될 때 배경화면 파일 검증
        if enabled:
            validation_result = FileHandler.validate_language_backgrounds()
            warning_message = FileHandler.get_missing_backgrounds_message(validation_result)

            if warning_message:
                QMessageBox.warning(
                    self,
                    "언어별 배경화면 확인 필요",
                    f"언어 선택 기능을 활성화했습니다.\n\n{warning_message}\n\n"
                    "각 탭의 '배경 설정'에서 언어별 배경화면을 설정해주세요."
                )

        self._update_screen_preview()
        # 다른 탭들에 언어 활성화 상태 변경 알림
        self.request_real_time_update()
        # 언어 활성화 상태 변경 시그널 emit (다른 탭들이 연결해서 사용)
        self.language_enabled_changed.emit(enabled)

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

