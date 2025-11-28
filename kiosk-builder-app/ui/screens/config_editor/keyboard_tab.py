from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QSpinBox, QWidget,
                              QTabWidget, QScrollArea, QFrame, QSizePolicy, QDialog,
                              QDialogButtonBox, QGridLayout)
from PySide6.QtGui import QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QRect, QSize, QRectF
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import LivePreviewWidget, TextPreviewWidget
from ui.components.position_size_input import PositionSizeInput
from ui.components.collapsible_group import CollapsibleGroupBox
from ui.components.keyboard_preview import KeyboardStylePreview
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# 키보드 화면 screen_key = "2"
KEYBOARD_SCREEN_KEY = "2"


class KeyboardTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.tab_manager = None

        # 미리보기 위젯
        self.screen_preview = None  # 화면 미리보기 (화면 설정 탭)
        self.card_preview = None    # 카드 미리보기 (인쇄 설정 탭)
        self.keyboard_style_preview = None  # 키보드 스타일 미리보기

        # 설정 필드들
        self.keyboard_position_input = None
        self.text_input_item_fields = []  # 입력창 화면 표시 설정
        self.print_input_item_fields = []  # 사용자 입력 텍스트 인쇄 설정
        self.text_item_fields = []  # 고정 텍스트 설정
        self.keyboard_style_fields = {}

        # 언어별 배경화면 필드
        self.lang_bg_fields = {"ko": {}, "en": {}}

        self.init_ui()

    def init_ui(self):
        scroll_content_layout = self.create_tab_with_scroll()

        # 서브 탭 위젯 생성
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

        # 3개의 서브 탭 생성
        self._create_screen_settings_tab()  # 화면 설정
        self._create_print_settings_tab()   # 인쇄 설정
        self._create_style_settings_tab()   # 키보드 스타일

        scroll_content_layout.addWidget(self.sub_tabs)

        # 초기 미리보기 업데이트
        self._update_screen_preview()
        self._update_card_preview()

    # ==================== 화면 설정 탭 ====================
    def _create_screen_settings_tab(self):
        """화면 설정 탭 생성 (배경화면, 키보드, 입력창 화면 표시)"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 좌측: 설정 영역 (스크롤 가능)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        settings_scroll.setMinimumWidth(380)

        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: white;")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(8)
        settings_layout.setContentsMargins(0, 0, 5, 0)

        # 1. 배경 설정 헤더 (타이틀 + ? 버튼)
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

        settings_layout.addWidget(header_widget)

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
        saved_bg = FileHandler.get_background_display_name(KEYBOARD_SCREEN_KEY)
        self.keyboard_bg_edit = QLineEdit(saved_bg)
        self.keyboard_bg_edit.setReadOnly(True)
        self.keyboard_bg_edit.setPlaceholderText("배경화면 없음")
        self.keyboard_bg_edit.textChanged.connect(self._update_screen_preview)
        bg_row.addWidget(self.keyboard_bg_edit, 1)

        browse_btn = QPushButton("찾기...")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_and_update_background)
        bg_row.addWidget(browse_btn)

        reset_btn = QPushButton("초기화")
        reset_btn.setFixedWidth(60)
        reset_btn.setToolTip("배경화면을 삭제합니다")
        reset_btn.clicked.connect(self._reset_background)
        bg_row.addWidget(reset_btn)
        bg_form.addRow(basic_label, bg_row)

        # 한국어 배경화면
        ko_label = QLabel("🇰🇷 한국어:")
        ko_label.setFixedWidth(LABEL_WIDTH)
        ko_bg_layout = QHBoxLayout()
        saved_ko_bg = FileHandler.get_background_display_name(KEYBOARD_SCREEN_KEY, lang="ko")
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
        saved_en_bg = FileHandler.get_background_display_name(KEYBOARD_SCREEN_KEY, lang="en")
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

        settings_layout.addWidget(bg_group)

        # 2. 키보드 위치 설정
        keyboard_group = QGroupBox("키보드 위치")
        self.apply_left_aligned_group_style(keyboard_group)
        keyboard_layout = QVBoxLayout(keyboard_group)
        keyboard_layout.setSpacing(4)
        keyboard_layout.setContentsMargins(8, 12, 8, 8)

        self.keyboard_position_input = PositionSizeInput()
        self.keyboard_position_input.set_values(
            x=self.config["keyboard"]["x"],
            y=self.config["keyboard"]["y"],
            width=self.config["keyboard"]["width"],
            height=self.config["keyboard"]["height"]
        )
        self.keyboard_position_input.value_changed.connect(self._update_screen_preview)
        keyboard_layout.addWidget(self.keyboard_position_input)

        # 버튼들 (더 작게)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        fill_btn = QPushButton("채우기")
        fill_btn.setFixedWidth(55)
        fill_btn.clicked.connect(self._fill_keyboard_frame)
        center_btn = QPushButton("가운데")
        center_btn.setFixedWidth(55)
        center_btn.clicked.connect(self._center_keyboard_frame)
        btn_layout.addWidget(fill_btn)
        btn_layout.addWidget(center_btn)
        btn_layout.addStretch()
        keyboard_layout.addLayout(btn_layout)

        settings_layout.addWidget(keyboard_group)

        # 3. 입력창 설정 (화면 표시만)
        input_group = QGroupBox("입력창")
        self.apply_left_aligned_group_style(input_group)
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(5)
        input_layout.setContentsMargins(8, 12, 8, 8)

        # 입력창 개수 + 안내 (한 줄로)
        count_layout = QHBoxLayout()
        count_layout.setSpacing(5)
        count_layout.addWidget(QLabel("개수:"))
        self.text_input_count_spinbox = QSpinBox()
        self.text_input_count_spinbox.setRange(1, 10)
        self.text_input_count_spinbox.setFixedWidth(50)
        count_value = max(1, self.config["text_input"]["count"])
        self.text_input_count_spinbox.setValue(count_value)
        self.text_input_count_spinbox.valueChanged.connect(self._on_input_count_changed)
        count_layout.addWidget(self.text_input_count_spinbox)

        # 안내 문구 (같은 줄에 표시)
        info_label = QLabel("※ 인쇄 위치는 [인쇄 설정]에서 설정")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        count_layout.addWidget(info_label)
        count_layout.addStretch()
        input_layout.addLayout(count_layout)

        # 입력창 항목들 컨테이너
        self.input_items_container = QWidget()
        self.input_items_layout = QVBoxLayout(self.input_items_container)
        self.input_items_layout.setContentsMargins(0, 0, 0, 0)
        self.input_items_layout.setSpacing(6)
        input_layout.addWidget(self.input_items_container)

        settings_layout.addWidget(input_group)
        settings_layout.addStretch()

        settings_scroll.setWidget(settings_widget)
        main_layout.addWidget(settings_scroll, 1)

        # 우측: 화면 미리보기
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_group_layout = QVBoxLayout(preview_group)
        preview_group_layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("키보드/입력창을 드래그하여 위치 조절")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_group_layout.addWidget(desc)

        self.screen_preview = LivePreviewWidget(preview_size=QSize(350, 350))
        self.screen_preview.position_changed.connect(self._on_screen_element_position_changed)
        self.screen_preview.size_changed.connect(self._on_screen_element_size_changed)
        preview_group_layout.addWidget(self.screen_preview, 0, Qt.AlignCenter)

        hint = QLabel("모서리를 드래그하여 크기 조절")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        preview_group_layout.addWidget(hint)

        preview_layout.addWidget(preview_group)
        preview_layout.addStretch()

        main_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab, "화면 설정")

        # 입력창 항목들 초기화
        self._rebuild_screen_input_items(count_value)

    # ==================== 인쇄 설정 탭 ====================
    def _create_print_settings_tab(self):
        """인쇄 설정 탭 생성 (사용자 입력 텍스트 인쇄 + 고정 텍스트)"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(15)

        # 좌측: 설정 영역 (스크롤 가능)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")

        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: white;")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(15)

        # 1. 사용자 입력 텍스트 인쇄 설정
        user_input_group = QGroupBox("사용자 입력 텍스트 (입력창에서 입력받은 내용)")
        self.apply_left_aligned_group_style(user_input_group)
        user_input_layout = QVBoxLayout(user_input_group)

        # 안내 문구
        info_label = QLabel("※ 입력창 개수는 [화면 설정] 탭에서 설정합니다. 여기서는 카드에 인쇄될 위치를 설정합니다.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        info_label.setWordWrap(True)
        user_input_layout.addWidget(info_label)

        # 사용자 입력 텍스트 항목들 컨테이너
        self.print_input_container = QWidget()
        self.print_input_layout = QVBoxLayout(self.print_input_container)
        self.print_input_layout.setContentsMargins(0, 0, 0, 0)
        self.print_input_layout.setSpacing(10)
        user_input_layout.addWidget(self.print_input_container)

        settings_layout.addWidget(user_input_group)

        # 2. 고정 텍스트 설정
        fixed_text_group = QGroupBox("고정 텍스트 (항상 인쇄되는 텍스트)")
        self.apply_left_aligned_group_style(fixed_text_group)
        fixed_text_layout = QVBoxLayout(fixed_text_group)

        # 고정 텍스트 개수
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("고정 텍스트 개수:"))
        self.text_count_spinbox = QSpinBox()
        self.text_count_spinbox.setRange(0, 10)
        self.text_count_spinbox.setValue(self.config["texts"]["count"])
        self.text_count_spinbox.valueChanged.connect(self._on_fixed_text_count_changed)
        count_layout.addWidget(self.text_count_spinbox)
        count_layout.addStretch()
        fixed_text_layout.addLayout(count_layout)

        # 고정 텍스트 항목들 컨테이너
        self.fixed_text_container = QWidget()
        self.fixed_text_layout = QVBoxLayout(self.fixed_text_container)
        self.fixed_text_layout.setContentsMargins(0, 0, 0, 0)
        self.fixed_text_layout.setSpacing(10)
        fixed_text_layout.addWidget(self.fixed_text_container)

        settings_layout.addWidget(fixed_text_group)
        settings_layout.addStretch()

        settings_scroll.setWidget(settings_widget)
        main_layout.addWidget(settings_scroll, 1)

        # 우측: 카드 인쇄 미리보기
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("카드 인쇄 미리보기 (58x90mm)")
        self.apply_left_aligned_group_style(preview_group)
        preview_group_layout = QVBoxLayout(preview_group)
        preview_group_layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("텍스트를 드래그하여 위치 조절")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_group_layout.addWidget(desc)

        # TextPreviewWidget 사용하여 실제 텍스트 렌더링
        self.card_preview = TextPreviewWidget()
        self.card_preview.position_changed.connect(self._on_card_element_position_changed)
        self.card_preview.size_changed.connect(self._on_card_element_size_changed)
        self.card_preview.text_size_changed.connect(self._on_text_size_changed)
        preview_group_layout.addWidget(self.card_preview, 0, Qt.AlignCenter)

        hint = QLabel("모서리를 드래그하여 크기 조절")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        preview_group_layout.addWidget(hint)

        preview_layout.addWidget(preview_group)
        preview_layout.addStretch()

        main_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab, "인쇄 설정")

        # 인쇄 설정 항목들 초기화
        count_value = max(1, self.config["text_input"]["count"])
        self._rebuild_print_input_items(count_value)
        self._rebuild_fixed_text_items(self.config["texts"]["count"])

    # ==================== 키보드 스타일 탭 ====================
    def _create_style_settings_tab(self):
        """키보드 스타일 탭 생성 (콤팩트 레이아웃 + 미리보기)"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(15)

        # ========== 좌측: 설정 영역 (스크롤 가능) ==========
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        settings_scroll.setMinimumWidth(380)

        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: white;")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(8)
        settings_layout.setContentsMargins(5, 5, 5, 5)

        # 1. 키보드 컨테이너 스타일 (접이식)
        container_group = CollapsibleGroupBox("키보드 컨테이너", collapsed=False)
        container_grid = QGridLayout()
        container_grid.setSpacing(8)

        # 배경색, 테두리색
        container_grid.addWidget(QLabel("배경색:"), 0, 0)
        bg_color = ColorPickerButton(self.config["keyboard"].get("bg_color", "#1B2838"))
        bg_color.color_changed.connect(self._on_style_changed)
        container_grid.addWidget(bg_color, 0, 1)
        self.keyboard_style_fields["bg_color"] = bg_color

        container_grid.addWidget(QLabel("테두리색:"), 0, 2)
        border_color = ColorPickerButton(self.config["keyboard"].get("border_color", "#00FFC2"))
        border_color.color_changed.connect(self._on_style_changed)
        container_grid.addWidget(border_color, 0, 3)
        self.keyboard_style_fields["border_color"] = border_color

        # 두께, 둥글기
        container_grid.addWidget(QLabel("두께:"), 1, 0)
        border_width = NumberLineEdit()
        border_width.setValue(self.config["keyboard"].get("border_width", 2))
        border_width.setFixedWidth(60)
        border_width.textChanged.connect(self._on_style_changed)
        container_grid.addWidget(border_width, 1, 1)
        self.keyboard_style_fields["border_width"] = border_width

        container_grid.addWidget(QLabel("둥글기:"), 1, 2)
        border_radius = NumberLineEdit()
        border_radius.setValue(self.config["keyboard"].get("border_radius", 15))
        border_radius.setFixedWidth(60)
        border_radius.textChanged.connect(self._on_style_changed)
        container_grid.addWidget(border_radius, 1, 3)
        self.keyboard_style_fields["border_radius"] = border_radius

        # 여백, 글자크기
        container_grid.addWidget(QLabel("여백:"), 2, 0)
        padding = NumberLineEdit()
        padding.setValue(self.config["keyboard"].get("padding", 10))
        padding.setFixedWidth(60)
        padding.textChanged.connect(self._on_style_changed)
        container_grid.addWidget(padding, 2, 1)
        self.keyboard_style_fields["padding"] = padding

        container_grid.addWidget(QLabel("글자크기:"), 2, 2)
        font_size = NumberLineEdit()
        font_size.setValue(self.config["keyboard"].get("font_size", 28))
        font_size.setFixedWidth(60)
        font_size.textChanged.connect(self._on_style_changed)
        container_grid.addWidget(font_size, 2, 3)
        self.keyboard_style_fields["font_size"] = font_size

        container_group.addLayout(container_grid)
        settings_layout.addWidget(container_group)

        # 2. 일반 버튼 스타일 (접이식)
        button_group = CollapsibleGroupBox("일반 버튼", collapsed=False)
        button_grid = QGridLayout()
        button_grid.setSpacing(8)

        # 버튼 배경, 글자색
        button_grid.addWidget(QLabel("배경:"), 0, 0)
        btn_bg = ColorPickerButton(self.config["keyboard"].get("button_bg_color", "#2D3748"))
        btn_bg.color_changed.connect(self._on_style_changed)
        button_grid.addWidget(btn_bg, 0, 1)
        self.keyboard_style_fields["button_bg_color"] = btn_bg

        button_grid.addWidget(QLabel("글자:"), 0, 2)
        btn_text = ColorPickerButton(self.config["keyboard"].get("button_text_color", "white"))
        btn_text.color_changed.connect(self._on_style_changed)
        button_grid.addWidget(btn_text, 0, 3)
        self.keyboard_style_fields["button_text_color"] = btn_text

        # 누름색, 둥글기
        button_grid.addWidget(QLabel("누름:"), 1, 0)
        btn_pressed = ColorPickerButton(self.config["keyboard"].get("button_pressed_color", "#4A5568"))
        btn_pressed.color_changed.connect(self._on_style_changed)
        button_grid.addWidget(btn_pressed, 1, 1)
        self.keyboard_style_fields["button_pressed_color"] = btn_pressed

        button_grid.addWidget(QLabel("둥글기:"), 1, 2)
        btn_radius = NumberLineEdit()
        btn_radius.setValue(self.config["keyboard"].get("button_radius", 10))
        btn_radius.setFixedWidth(60)
        btn_radius.textChanged.connect(self._on_style_changed)
        button_grid.addWidget(btn_radius, 1, 3)
        self.keyboard_style_fields["button_radius"] = btn_radius

        button_group.addLayout(button_grid)
        settings_layout.addWidget(button_group)

        # 3. 특수 버튼 스타일 (접이식)
        special_group = CollapsibleGroupBox("특수 버튼", collapsed=False)
        special_grid = QGridLayout()
        special_grid.setSpacing(8)

        # 한/영, Shift
        special_grid.addWidget(QLabel("한/영:"), 0, 0)
        hangul_btn = ColorPickerButton(self.config["keyboard"].get("hangul_btn_color", "#4299E1"))
        hangul_btn.color_changed.connect(self._on_style_changed)
        special_grid.addWidget(hangul_btn, 0, 1)
        self.keyboard_style_fields["hangul_btn_color"] = hangul_btn

        special_grid.addWidget(QLabel("Shift:"), 0, 2)
        shift_btn = ColorPickerButton(self.config["keyboard"].get("shift_btn_color", "#3182CE"))
        shift_btn.color_changed.connect(self._on_style_changed)
        special_grid.addWidget(shift_btn, 0, 3)
        self.keyboard_style_fields["shift_btn_color"] = shift_btn

        # 지우기, 다음
        special_grid.addWidget(QLabel("지우기:"), 1, 0)
        backspace_btn = ColorPickerButton(self.config["keyboard"].get("backspace_btn_color", "#6ae517"))
        backspace_btn.color_changed.connect(self._on_style_changed)
        special_grid.addWidget(backspace_btn, 1, 1)
        self.keyboard_style_fields["backspace_btn_color"] = backspace_btn

        special_grid.addWidget(QLabel("다음:"), 1, 2)
        next_btn = ColorPickerButton(self.config["keyboard"].get("next_btn_color", "#48BB78"))
        next_btn.color_changed.connect(self._on_style_changed)
        special_grid.addWidget(next_btn, 1, 3)
        self.keyboard_style_fields["next_btn_color"] = next_btn

        # 특수버튼 너비
        special_grid.addWidget(QLabel("너비:"), 2, 0)
        special_width = NumberLineEdit()
        special_width.setValue(self.config["keyboard"].get("special_btn_width", 100))
        special_width.setFixedWidth(60)
        special_width.textChanged.connect(self._on_style_changed)
        special_grid.addWidget(special_width, 2, 1)
        self.keyboard_style_fields["special_btn_width"] = special_width

        special_group.addLayout(special_grid)
        settings_layout.addWidget(special_group)

        # 4. 입력 제한 (접이식, 기본 접힘)
        limit_group = CollapsibleGroupBox("입력 글자 수 제한", collapsed=True)
        limit_grid = QGridLayout()
        limit_grid.setSpacing(8)

        limit_grid.addWidget(QLabel("한글:"), 0, 0)
        max_hangul = NumberLineEdit()
        max_hangul.setValue(self.config["keyboard"].get("max_hangul", 100))
        max_hangul.setFixedWidth(60)
        limit_grid.addWidget(max_hangul, 0, 1)
        self.keyboard_style_fields["max_hangul"] = max_hangul

        limit_grid.addWidget(QLabel("소문자:"), 0, 2)
        max_lower = NumberLineEdit()
        max_lower.setValue(self.config["keyboard"].get("max_lowercase", 100))
        max_lower.setFixedWidth(60)
        limit_grid.addWidget(max_lower, 0, 3)
        self.keyboard_style_fields["max_lowercase"] = max_lower

        limit_grid.addWidget(QLabel("대문자:"), 1, 0)
        max_upper = NumberLineEdit()
        max_upper.setValue(self.config["keyboard"].get("max_uppercase", 100))
        max_upper.setFixedWidth(60)
        limit_grid.addWidget(max_upper, 1, 1)
        self.keyboard_style_fields["max_uppercase"] = max_upper

        limit_group.addLayout(limit_grid)
        settings_layout.addWidget(limit_group)

        settings_layout.addStretch()
        settings_scroll.setWidget(settings_widget)
        main_layout.addWidget(settings_scroll, 1)

        # ========== 우측: 미리보기 영역 ==========
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("키보드 스타일 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_group_layout = QVBoxLayout(preview_group)

        # 키보드 스타일 미리보기 위젯
        self.keyboard_style_preview = KeyboardStylePreview()
        self.keyboard_style_preview.setMinimumSize(300, 200)
        preview_group_layout.addWidget(self.keyboard_style_preview, 0, Qt.AlignHCenter)

        # 안내 문구
        info_label = QLabel("※ 위 미리보기는 실제 키보드의 축소 버전입니다.\n   색상과 스타일이 실시간으로 반영됩니다.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        info_label.setAlignment(Qt.AlignCenter)
        preview_group_layout.addWidget(info_label)

        preview_layout.addWidget(preview_group)
        preview_layout.addStretch()

        main_layout.addWidget(preview_widget, 1)

        self.sub_tabs.addTab(tab, "키보드 스타일")

        # 초기 미리보기 업데이트
        self._update_keyboard_style_preview()

    def _on_style_changed(self):
        """스타일 필드 변경 시 미리보기 업데이트"""
        self._update_keyboard_style_preview()
        self._update_screen_preview()  # 화면 미리보기에도 반영

    def _update_keyboard_style_preview(self):
        """키보드 스타일 미리보기 업데이트"""
        if not self.keyboard_style_preview:
            return

        style_config = {}
        for key, widget in self.keyboard_style_fields.items():
            if isinstance(widget, ColorPickerButton):
                style_config[key] = widget.color
            elif isinstance(widget, NumberLineEdit):
                style_config[key] = widget.value()

        self.keyboard_style_preview.update_style(style_config)

    def _get_current_keyboard_style(self) -> dict:
        """현재 키보드 스타일 설정값 반환"""
        style = {
            "bg_color": self.config["keyboard"].get("bg_color", "#1B2838"),
            "border_color": self.config["keyboard"].get("border_color", "#00FFC2"),
            "border_width": self.config["keyboard"].get("border_width", 2),
            "border_radius": self.config["keyboard"].get("border_radius", 15),
            "padding": self.config["keyboard"].get("padding", 10),
            "font_size": self.config["keyboard"].get("font_size", 28),
            "button_bg_color": self.config["keyboard"].get("button_bg_color", "#2D3748"),
            "button_text_color": self.config["keyboard"].get("button_text_color", "white"),
            "button_pressed_color": self.config["keyboard"].get("button_pressed_color", "#4A5568"),
            "button_radius": self.config["keyboard"].get("button_radius", 10),
            "hangul_btn_color": self.config["keyboard"].get("hangul_btn_color", "#4299E1"),
            "shift_btn_color": self.config["keyboard"].get("shift_btn_color", "#3182CE"),
            "backspace_btn_color": self.config["keyboard"].get("backspace_btn_color", "#6ae517"),
            "next_btn_color": self.config["keyboard"].get("next_btn_color", "#48BB78"),
        }

        # 스타일 필드가 있으면 현재 UI 값으로 덮어쓰기
        for key, widget in self.keyboard_style_fields.items():
            if isinstance(widget, ColorPickerButton):
                style[key] = widget.color
            elif isinstance(widget, NumberLineEdit):
                style[key] = widget.value()

        return style

    def _render_keyboard_preview(self, painter, rect: QRect, style: dict):
        """화면 미리보기에 키보드 스타일 렌더링"""
        if not style:
            style = self._get_current_keyboard_style()

        # 키보드 배경
        border_width = max(1, style.get("border_width", 2) // 3)
        border_radius = min(style.get("border_radius", 15) // 2, rect.width() // 10, rect.height() // 10)

        painter.setPen(QPen(QColor(style.get("border_color", "#00FFC2")), border_width))
        painter.setBrush(QBrush(QColor(style.get("bg_color", "#1B2838"))))
        painter.drawRoundedRect(rect, border_radius, border_radius)

        # 키보드 내부 영역
        inner_padding = style.get("padding", 10) // 3 + border_width
        inner_rect = rect.adjusted(inner_padding, inner_padding, -inner_padding, -inner_padding)

        if inner_rect.width() <= 0 or inner_rect.height() <= 0:
            return

        # 간소화된 키 레이아웃
        keys = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["ㅂ", "ㅈ", "ㄷ", "ㄱ", "ㅅ", "ㅛ", "ㅕ", "ㅑ", "ㅐ", "ㅔ"],
            ["ㅁ", "ㄴ", "ㅇ", "ㄹ", "ㅎ", "ㅗ", "ㅓ", "ㅏ", "ㅣ"],
            ["ㅋ", "ㅌ", "ㅊ", "ㅍ", "ㅠ", "ㅜ", "ㅡ"],
        ]
        special_keys = ["한", "Sh", "Space", "←", "다음"]
        special_colors = [
            style.get("hangul_btn_color", "#4299E1"),
            style.get("shift_btn_color", "#3182CE"),
            style.get("button_bg_color", "#2D3748"),
            style.get("backspace_btn_color", "#6ae517"),
            style.get("next_btn_color", "#48BB78"),
        ]

        key_spacing = 2
        button_radius = min(style.get("button_radius", 10) // 2, 5)
        total_rows = len(keys) + 1
        row_height = (inner_rect.height() - key_spacing * (total_rows - 1)) / total_rows

        # 폰트 설정 (미리보기용 작은 폰트)
        font_size = max(6, min(int(row_height / 2.5), 10))
        font = QFont("맑은 고딕", font_size)
        painter.setFont(font)

        current_y = inner_rect.top()

        # 일반 키 그리기
        for row in keys:
            key_count = len(row)
            key_width = (inner_rect.width() - key_spacing * (key_count - 1)) / key_count
            current_x = inner_rect.left()

            for key in row:
                key_rect = QRectF(current_x, current_y, key_width - 1, row_height - 1)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(style.get("button_bg_color", "#2D3748"))))
                painter.drawRoundedRect(key_rect, button_radius, button_radius)

                painter.setPen(QColor(style.get("button_text_color", "white")))
                painter.drawText(key_rect, Qt.AlignCenter, key)
                current_x += key_width + key_spacing

            current_y += row_height + key_spacing

        # 특수 키 그리기
        widths = [2, 2, 4, 2, 2]
        total_units = sum(widths)
        unit_width = (inner_rect.width() - key_spacing * (len(special_keys) - 1)) / total_units
        current_x = inner_rect.left()

        for key, color, width_units in zip(special_keys, special_colors, widths):
            key_width = unit_width * width_units
            key_rect = QRectF(current_x, current_y, key_width - 1, row_height - 1)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawRoundedRect(key_rect, button_radius, button_radius)

            painter.setPen(QColor(style.get("button_text_color", "white")))
            painter.drawText(key_rect, Qt.AlignCenter, key)
            current_x += key_width + key_spacing

    def _render_input_field_preview(self, painter, rect: QRect, data: dict):
        """화면 미리보기에 입력창 스타일 렌더링 (라벨 + 힌트 포함)"""
        if not data:
            data = {"label": "", "placeholder": "", "font_size": 36, "index": 0}

        label_text = data.get("label", "")
        placeholder_text = data.get("placeholder", "")
        font_size = data.get("font_size", 36)
        index = data.get("index", 0)

        # 미리보기에서의 폰트 크기 (원본 대비 축소, 최소/최대 제한)
        # 미리보기가 축소되어 있으므로 폰트도 비례 축소
        preview_font_size = max(6, min(int(font_size / 4), 16))

        # 라벨 영역 (입력창 왼쪽)
        if label_text:
            label_width = min(80, rect.width() // 4)  # 라벨 최대 너비
            label_rect = QRectF(
                rect.x() - label_width - 5,
                rect.y(),
                label_width,
                rect.height()
            )
            # 라벨 텍스트 그리기
            font = QFont("맑은 고딕", max(6, preview_font_size - 2))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#333333"))
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, label_text)

        # 입력창 배경 (흰색 + 초록 테두리)
        border_radius = min(8, rect.height() // 6)
        painter.setPen(QPen(QColor("#00FFC2"), 2))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRoundedRect(QRectF(rect), border_radius, border_radius)

        # 힌트 텍스트 (회색으로 입력창 내부에 표시) - 설정된 폰트 크기 반영
        font = QFont("맑은 고딕", preview_font_size)
        painter.setFont(font)

        if placeholder_text:
            painter.setPen(QColor("#999999"))  # 회색 힌트 텍스트
            text_rect = QRectF(rect.x() + 5, rect.y(), rect.width() - 10, rect.height())
            painter.drawText(text_rect, Qt.AlignCenter, placeholder_text)
        else:
            # 힌트가 없으면 기본 텍스트 표시
            painter.setPen(QColor("#cccccc"))
            text_rect = QRectF(rect.x() + 5, rect.y(), rect.width() - 10, rect.height())
            painter.drawText(text_rect, Qt.AlignCenter, f"입력창 {index + 1}")

    # ==================== 입력창 화면 표시 관리 ====================
    def _on_input_count_changed(self, count):
        """입력창 개수 변경"""
        self._rebuild_screen_input_items(count)
        self._rebuild_print_input_items(count)
        self._update_screen_preview()
        self._update_card_preview()

    def _rebuild_screen_input_items(self, count):
        """입력창 화면 표시 항목들 재생성"""
        # 기존 위젯 제거
        for i in reversed(range(self.input_items_layout.count())):
            item = self.input_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.text_input_item_fields = []

        for i in range(count):
            # 기존 데이터 로드
            item_data = {
                "label": "", "placeholder": "",
                "screen_x": 40, "screen_y": 200 + i * 100,
                "screen_width": 1000, "screen_height": 70,
                "font_size": 36
            }
            if i < len(self.config["text_input"]["items"]):
                item_data.update(self.config["text_input"]["items"][i])

            # 항목 그룹 생성 (더 콤팩트하게)
            item_group = QGroupBox(f"입력창 {i+1}")
            item_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #2196F3;
                    border-radius: 4px;
                    margin-top: 8px;
                    padding-top: 8px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 3px;
                    color: #2196F3;
                    font-size: 12px;
                }
            """)
            item_layout = QVBoxLayout(item_group)
            item_layout.setSpacing(4)
            item_layout.setContentsMargins(6, 10, 6, 6)

            fields = {}

            # 첫째 줄: 라벨 + 힌트 + 글자크기 (더 콤팩트하게)
            first_row = QHBoxLayout()
            first_row.setSpacing(8)

            # 라벨 (입력창 왼쪽에 표시) - 인라인
            label_label = QLabel("라벨:")
            label_label.setStyleSheet("color: #2196F3; font-size: 11px;")
            first_row.addWidget(label_label)
            label_edit = QLineEdit(item_data.get("label", ""))
            label_edit.setPlaceholderText("이름")
            label_edit.setFixedWidth(80)
            label_edit.textChanged.connect(self._update_all_previews)
            first_row.addWidget(label_edit)
            fields["label"] = label_edit

            # 힌트 (입력창 안에 회색으로 표시) - 인라인
            hint_label = QLabel("힌트:")
            hint_label.setStyleSheet("color: #2196F3; font-size: 11px;")
            first_row.addWidget(hint_label)
            placeholder_edit = QLineEdit(item_data.get("placeholder", ""))
            placeholder_edit.setPlaceholderText("홍길동")
            placeholder_edit.setFixedWidth(100)
            placeholder_edit.textChanged.connect(self._update_screen_preview)
            first_row.addWidget(placeholder_edit)
            fields["placeholder"] = placeholder_edit

            # 글자 크기 - 인라인
            font_label = QLabel("글자:")
            font_label.setStyleSheet("color: #2196F3; font-size: 11px;")
            first_row.addWidget(font_label)
            font_size_edit = NumberLineEdit()
            font_size_edit.setValue(item_data.get("font_size", 36))
            font_size_edit.setFixedWidth(45)
            font_size_edit.textChanged.connect(self._update_screen_preview)
            first_row.addWidget(font_size_edit)
            fields["font_size"] = font_size_edit

            first_row.addStretch()
            item_layout.addLayout(first_row)

            # 둘째 줄: 화면 위치/크기 (카드 형식 유지)
            screen_pos = PositionSizeInput()
            screen_pos.set_values(
                x=item_data.get("screen_x", 40),
                y=item_data.get("screen_y", 200),
                width=item_data.get("screen_width", 1000),
                height=item_data.get("screen_height", 70)
            )
            screen_pos.value_changed.connect(self._update_screen_preview)
            item_layout.addWidget(screen_pos)
            fields["screen_pos"] = screen_pos

            self.input_items_layout.addWidget(item_group)
            self.text_input_item_fields.append(fields)

    # ==================== 사용자 입력 텍스트 인쇄 관리 ====================
    def _rebuild_print_input_items(self, count):
        """사용자 입력 텍스트 인쇄 항목들 재생성"""
        if not hasattr(self, 'print_input_layout') or self.print_input_layout is None:
            return

        # 기존 위젯 제거
        for i in reversed(range(self.print_input_layout.count())):
            item = self.print_input_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.print_input_item_fields = []

        for i in range(count):
            # 기존 데이터 로드
            item_data = {
                "x": 168, "y": 100 + i * 100,
                "width": 300, "height": 80,
                "output_font": "", "output_font_size": 16, "output_font_color": "#000000"
            }
            if i < len(self.config["text_input"]["items"]):
                item_data.update(self.config["text_input"]["items"][i])

            # 항목 이름 가져오기 (화면 설정의 label)
            label_text = f"사용자 입력 텍스트 {i+1}"
            if i < len(self.text_input_item_fields) and "label" in self.text_input_item_fields[i]:
                label_val = self.text_input_item_fields[i]["label"].text()
                if label_val:
                    label_text = f"사용자 입력: {label_val}"

            # 항목 그룹 생성
            item_group = QGroupBox(label_text)
            item_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #FF9800;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #FF9800;
                }
            """)
            item_layout = QFormLayout(item_group)
            item_layout.setSpacing(6)

            fields = {}

            # 인쇄 위치
            print_pos = PositionSizeInput()
            print_pos.set_values(
                x=item_data.get("x", 168),
                y=item_data.get("y", 100),
                width=item_data.get("width", 300),
                height=item_data.get("height", 80)
            )
            print_pos.value_changed.connect(self._update_card_preview)
            item_layout.addRow("인쇄 위치:", print_pos)
            fields["print_pos"] = print_pos

            # 폰트
            font_layout = QHBoxLayout()
            output_font_edit = QLineEdit(item_data.get("output_font", ""))
            output_font_edit.setPlaceholderText("기본 폰트")
            font_layout.addWidget(output_font_edit, 1)
            browse_btn = QPushButton("찾기")
            browse_btn.setFixedWidth(50)
            browse_btn.clicked.connect(lambda checked, edit=output_font_edit: FileHandler.browse_font_file(self, edit))
            font_layout.addWidget(browse_btn)
            item_layout.addRow("폰트:", font_layout)
            fields["output_font"] = output_font_edit

            # 폰트 크기 + 색상
            size_color_layout = QHBoxLayout()
            output_font_size = NumberLineEdit()
            output_font_size.setValue(item_data.get("output_font_size", 16))
            output_font_size.setFixedWidth(60)
            size_color_layout.addWidget(QLabel("크기:"))
            size_color_layout.addWidget(output_font_size)
            size_color_layout.addSpacing(20)
            size_color_layout.addWidget(QLabel("색상:"))
            output_font_color = ColorPickerButton(item_data.get("output_font_color", "#000000"))
            size_color_layout.addWidget(output_font_color)
            size_color_layout.addStretch()
            item_layout.addRow("", size_color_layout)
            fields["output_font_size"] = output_font_size
            fields["output_font_color"] = output_font_color

            self.print_input_layout.addWidget(item_group)
            self.print_input_item_fields.append(fields)

    # ==================== 고정 텍스트 항목 관리 ====================
    def _on_fixed_text_count_changed(self, count):
        """고정 텍스트 개수 변경"""
        self._rebuild_fixed_text_items(count)
        self._update_card_preview()

    def _rebuild_fixed_text_items(self, count):
        """고정 텍스트 항목들 재생성"""
        # 기존 위젯 제거
        for i in reversed(range(self.fixed_text_layout.count())):
            item = self.fixed_text_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.text_item_fields = []

        for i in range(count):
            # 기존 데이터 로드
            item_data = {
                "content": "텍스트",
                "x": 0, "y": 0, "width": 300, "height": 100,
                "font": "", "font_size": 16, "font_color": "#000000"
            }
            if i < len(self.config["texts"]["items"]):
                item_data.update(self.config["texts"]["items"][i])

            # 항목 그룹
            item_group = QGroupBox(f"고정 텍스트 {i+1}")
            item_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #4CAF50;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #4CAF50;
                }
            """)
            item_layout = QFormLayout(item_group)
            item_layout.setSpacing(8)

            fields = {}

            # 문구
            content_edit = QLineEdit(item_data.get("content", ""))
            content_edit.textChanged.connect(self._update_card_preview)
            item_layout.addRow("문구:", content_edit)
            fields["content"] = content_edit

            # 위치
            pos_input = PositionSizeInput()
            pos_input.set_values(
                x=item_data.get("x", 0),
                y=item_data.get("y", 0),
                width=item_data.get("width", 300),
                height=item_data.get("height", 100)
            )
            pos_input.value_changed.connect(self._update_card_preview)
            item_layout.addRow("인쇄 위치:", pos_input)
            fields["pos"] = pos_input

            # 폰트
            font_layout = QHBoxLayout()
            font_edit = QLineEdit(item_data.get("font", ""))
            font_layout.addWidget(font_edit, 1)
            browse_btn = QPushButton("찾기...")
            browse_btn.clicked.connect(lambda checked, edit=font_edit: FileHandler.browse_font_file(self, edit))
            font_layout.addWidget(browse_btn)
            item_layout.addRow("폰트:", font_layout)
            fields["font"] = font_edit

            # 폰트 크기
            font_size = NumberLineEdit()
            font_size.setValue(item_data.get("font_size", 16))
            item_layout.addRow("글자 크기:", font_size)
            fields["font_size"] = font_size

            # 폰트 색상
            font_color = ColorPickerButton(item_data.get("font_color", "#000000"))
            item_layout.addRow("글자 색상:", font_color)
            fields["font_color"] = font_color

            self.fixed_text_layout.addWidget(item_group)
            self.text_item_fields.append(fields)

    # ==================== 미리보기 업데이트 ====================
    def _update_all_previews(self):
        """모든 미리보기 업데이트"""
        self._update_screen_preview()
        self._update_card_preview()

    def _update_screen_preview(self):
        """화면 미리보기 업데이트 (키보드 + 입력창)"""
        if not self.screen_preview:
            return

        self.screen_preview.clear_elements()

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.screen_preview.set_original_size(monitor_width, monitor_height)

        # 배경 이미지
        bg_path = FileHandler.resolve_background_path(KEYBOARD_SCREEN_KEY)
        self.screen_preview.set_background(bg_path, QColor("#ffffff"))
        self.screen_preview.set_card_border(True, QColor("#333333"), 2)

        # 키보드 영역 - 스타일 적용된 미리보기
        if self.keyboard_position_input:
            kb_rect = QRect(
                self.keyboard_position_input.get_x(),
                self.keyboard_position_input.get_y(),
                self.keyboard_position_input.get_width(),
                self.keyboard_position_input.get_height()
            )
            # 현재 키보드 스타일 데이터 수집
            keyboard_style = self._get_current_keyboard_style()
            self.screen_preview.add_element(
                "keyboard", kb_rect,
                color=QColor("red"),
                label="키보드",
                draggable=True,
                custom_renderer=self._render_keyboard_preview,
                renderer_data=keyboard_style
            )

        # 입력창들 - 실제 입력창 스타일로 렌더링
        for i, fields in enumerate(self.text_input_item_fields):
            if "screen_pos" in fields:
                pos = fields["screen_pos"]
                rect = QRect(pos.get_x(), pos.get_y(), pos.get_width(), pos.get_height())

                # 입력창 데이터 수집
                input_data = {
                    "label": fields.get("label").text() if fields.get("label") else "",
                    "placeholder": fields.get("placeholder").text() if fields.get("placeholder") else "",
                    "font_size": fields.get("font_size").value() if fields.get("font_size") else 36,
                    "index": i
                }

                self.screen_preview.add_element(
                    f"input_{i}", rect,
                    color=QColor("#00FFC2"),  # 기본 테두리 색상 (폴백용)
                    label=None,  # 커스텀 렌더러가 라벨 처리
                    draggable=True,
                    custom_renderer=self._render_input_field_preview,
                    renderer_data=input_data
                )

        self.request_real_time_update()

    def _update_card_preview(self):
        """카드 미리보기 업데이트 (사용자 입력 텍스트 + 고정 텍스트)"""
        if not self.card_preview:
            return

        self.card_preview.clear_elements()
        self.card_preview.clear_texts()

        # 카드 크기
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        self.card_preview.set_original_size(card_width, card_height)
        self.card_preview.set_background_color(QColor("white"))

        # 카드 테두리 표시 (인쇄 영역 경계)
        self.card_preview.set_card_border(True, QColor("#333333"), 3)

        # 사용자 입력 텍스트 인쇄 위치 (실제 텍스트로 렌더링)
        input_colors = [QColor("#E53935"), QColor("#1E88E5"), QColor("#7B1FA2"),
                        QColor("#FB8C00"), QColor("#5D4037")]
        for i, fields in enumerate(self.print_input_item_fields):
            if "print_pos" in fields:
                pos = fields["print_pos"]
                x, y = pos.get_x(), pos.get_y()

                # 표시할 텍스트 (placeholder 또는 label 사용)
                display_text = f"(입력{i+1})"
                if i < len(self.text_input_item_fields):
                    screen_fields = self.text_input_item_fields[i]
                    if "placeholder" in screen_fields and screen_fields["placeholder"].text():
                        display_text = screen_fields["placeholder"].text()
                    elif "label" in screen_fields and screen_fields["label"].text():
                        display_text = f"({screen_fields['label'].text()})"

                # 폰트 크기
                font_size = fields.get("output_font_size")
                font_size_val = font_size.value() if font_size else 16

                # 폰트 색상
                font_color = fields.get("output_font_color")
                color_val = QColor(font_color.color) if font_color else input_colors[i % len(input_colors)]

                # 폰트 경로
                font_path = fields.get("output_font")
                font_path_val = font_path.text() if font_path else ""

                self.card_preview.add_text(
                    f"print_input_{i}",
                    display_text,
                    x, y,
                    font_path=font_path_val,
                    font_size=font_size_val,
                    color=color_val,
                    draggable=True,
                    resizable=True
                )

        # 고정 텍스트 (실제 텍스트로 렌더링)
        fixed_colors = [QColor("#43A047"), QColor("#00897B"), QColor("#00ACC1"),
                        QColor("#D81B60"), QColor("#757575")]
        for i, fields in enumerate(self.text_item_fields):
            if "pos" in fields:
                pos = fields["pos"]
                x, y = pos.get_x(), pos.get_y()

                # 표시할 텍스트
                content = fields.get("content")
                display_text = content.text() if content and content.text() else f"텍스트{i+1}"

                # 폰트 크기
                font_size = fields.get("font_size")
                font_size_val = font_size.value() if font_size else 16

                # 폰트 색상
                font_color = fields.get("font_color")
                color_val = QColor(font_color.color) if font_color else fixed_colors[i % len(fixed_colors)]

                # 폰트 경로
                font_path = fields.get("font")
                font_path_val = font_path.text() if font_path else ""

                self.card_preview.add_text(
                    f"fixed_text_{i}",
                    display_text,
                    x, y,
                    font_path=font_path_val,
                    font_size=font_size_val,
                    color=color_val,
                    draggable=True,
                    resizable=True
                )

        self.request_real_time_update()

    # ==================== 드래그 이벤트 처리 ====================
    def _on_screen_element_position_changed(self, element_id, x, y):
        """화면 미리보기에서 요소 드래그"""
        if element_id == "keyboard" and self.keyboard_position_input:
            self.keyboard_position_input.block_all_signals(True)
            self.keyboard_position_input.set_x(x)
            self.keyboard_position_input.set_y(y)
            self.keyboard_position_input.block_all_signals(False)
        elif element_id.startswith("input_"):
            idx = int(element_id.split("_")[1])
            if idx < len(self.text_input_item_fields) and "screen_pos" in self.text_input_item_fields[idx]:
                pos = self.text_input_item_fields[idx]["screen_pos"]
                pos.block_all_signals(True)
                pos.set_x(x)
                pos.set_y(y)
                pos.block_all_signals(False)
        self.request_real_time_update()

    def _on_screen_element_size_changed(self, element_id, x, y, width, height):
        """화면 미리보기에서 요소 크기 변경"""
        if element_id == "keyboard" and self.keyboard_position_input:
            self.keyboard_position_input.block_all_signals(True)
            self.keyboard_position_input.set_values(x=x, y=y, width=width, height=height)
            self.keyboard_position_input.block_all_signals(False)
        elif element_id.startswith("input_"):
            idx = int(element_id.split("_")[1])
            if idx < len(self.text_input_item_fields) and "screen_pos" in self.text_input_item_fields[idx]:
                pos = self.text_input_item_fields[idx]["screen_pos"]
                pos.block_all_signals(True)
                pos.set_values(x=x, y=y, width=width, height=height)
                pos.block_all_signals(False)
        self.request_real_time_update()

    def _on_card_element_position_changed(self, element_id, x, y):
        """카드 미리보기에서 요소 드래그"""
        if element_id.startswith("print_input_"):
            idx = int(element_id.split("_")[2])
            if idx < len(self.print_input_item_fields) and "print_pos" in self.print_input_item_fields[idx]:
                pos = self.print_input_item_fields[idx]["print_pos"]
                pos.block_all_signals(True)
                pos.set_x(x)
                pos.set_y(y)
                pos.block_all_signals(False)
        elif element_id.startswith("fixed_text_"):
            idx = int(element_id.split("_")[2])
            if idx < len(self.text_item_fields) and "pos" in self.text_item_fields[idx]:
                pos = self.text_item_fields[idx]["pos"]
                pos.block_all_signals(True)
                pos.set_x(x)
                pos.set_y(y)
                pos.block_all_signals(False)
        self.request_real_time_update()

    def _on_card_element_size_changed(self, element_id, x, y, width, height):
        """카드 미리보기에서 요소 크기 변경"""
        if element_id.startswith("print_input_"):
            idx = int(element_id.split("_")[2])
            if idx < len(self.print_input_item_fields) and "print_pos" in self.print_input_item_fields[idx]:
                pos = self.print_input_item_fields[idx]["print_pos"]
                pos.block_all_signals(True)
                pos.set_values(x=x, y=y, width=width, height=height)
                pos.block_all_signals(False)
        elif element_id.startswith("fixed_text_"):
            idx = int(element_id.split("_")[2])
            if idx < len(self.text_item_fields) and "pos" in self.text_item_fields[idx]:
                pos = self.text_item_fields[idx]["pos"]
                pos.block_all_signals(True)
                pos.set_values(x=x, y=y, width=width, height=height)
                pos.block_all_signals(False)
        self.request_real_time_update()

    def _on_text_size_changed(self, element_id, new_font_size):
        """텍스트 크기 변경 (드래그 리사이즈)"""
        if element_id.startswith("print_input_"):
            idx = int(element_id.split("_")[2])
            if idx < len(self.print_input_item_fields) and "output_font_size" in self.print_input_item_fields[idx]:
                font_size_widget = self.print_input_item_fields[idx]["output_font_size"]
                font_size_widget.blockSignals(True)
                font_size_widget.setValue(new_font_size)
                font_size_widget.blockSignals(False)
        elif element_id.startswith("fixed_text_"):
            idx = int(element_id.split("_")[2])
            if idx < len(self.text_item_fields) and "font_size" in self.text_item_fields[idx]:
                font_size_widget = self.text_item_fields[idx]["font_size"]
                font_size_widget.blockSignals(True)
                font_size_widget.setValue(new_font_size)
                font_size_widget.blockSignals(False)
        self.request_real_time_update()

    # ==================== 채우기/가운데 정렬 ====================
    def _fill_keyboard_frame(self):
        """키보드를 화면 크기로 채우기"""
        try:
            w = self.config["screen_size"]["width"]
            h = self.config["screen_size"]["height"]
        except KeyError:
            w, h = 1080, 1920
        self.keyboard_position_input.set_values(x=0, y=0, width=w, height=h)
        self._update_screen_preview()

    def _center_keyboard_frame(self):
        """키보드를 화면 중앙에 정렬"""
        try:
            mw = self.config["screen_size"]["width"]
            mh = self.config["screen_size"]["height"]
        except KeyError:
            mw, mh = 1080, 1920
        kw = self.keyboard_position_input.get_width()
        kh = self.keyboard_position_input.get_height()
        self.keyboard_position_input.set_x((mw - kw) // 2)
        self.keyboard_position_input.set_y((mh - kh) // 2)
        self._update_screen_preview()

    # ==================== 배경화면 관리 ====================
    def _browse_and_update_background(self):
        """배경화면 파일 선택"""
        FileHandler.browse_background_file(self, self.keyboard_bg_edit, KEYBOARD_SCREEN_KEY)
        saved_bg = FileHandler.get_background_display_name(KEYBOARD_SCREEN_KEY)
        self.keyboard_bg_edit.setText(saved_bg)
        self._update_screen_preview()

    def _reset_background(self):
        """배경화면 초기화"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "배경화면 초기화",
            "배경화면을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(KEYBOARD_SCREEN_KEY)
            self.keyboard_bg_edit.setText("")
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
            FileHandler.browse_background_file(self, bg_edit, KEYBOARD_SCREEN_KEY, lang=lang_code)
            saved_bg = FileHandler.get_background_display_name(KEYBOARD_SCREEN_KEY, lang=lang_code)
            bg_edit.setText(saved_bg)
            self._update_screen_preview()

    def _reset_lang_bg(self, lang_code: str):
        """언어별 배경화면 초기화"""
        from PySide6.QtWidgets import QMessageBox
        lang_name = "한국어" if lang_code == "ko" else "영어"
        reply = QMessageBox.question(
            self, f"{lang_name} 배경화면 초기화",
            f"{lang_name} 텍스트 입력 화면의 배경화면을 삭제하시겠습니까?\n삭제 시 기본 배경화면이 사용됩니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(KEYBOARD_SCREEN_KEY, lang=lang_code)
            bg_edit = self.lang_bg_fields[lang_code].get("background")
            if bg_edit:
                bg_edit.setText("")
            self._update_screen_preview()

    # ==================== 설정 저장/로드 ====================
    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config

        # 배경화면
        saved_bg = FileHandler.get_background_display_name(KEYBOARD_SCREEN_KEY)
        self.keyboard_bg_edit.setText(saved_bg)

        # 키보드 위치
        if self.keyboard_position_input:
            self.keyboard_position_input.set_values(
                x=config["keyboard"]["x"],
                y=config["keyboard"]["y"],
                width=config["keyboard"]["width"],
                height=config["keyboard"]["height"]
            )

        # 입력창 개수
        count_value = max(1, config["text_input"]["count"])
        if self.text_input_count_spinbox.value() != count_value:
            self.text_input_count_spinbox.setValue(count_value)
        else:
            self._rebuild_screen_input_items(count_value)
            self._rebuild_print_input_items(count_value)

        # 고정 텍스트 개수
        text_count = config["texts"]["count"]
        if self.text_count_spinbox.value() != text_count:
            self.text_count_spinbox.setValue(text_count)
        else:
            self._rebuild_fixed_text_items(text_count)

        # 키보드 스타일
        for key, widget in self.keyboard_style_fields.items():
            if isinstance(widget, ColorPickerButton):
                widget.update_color(config["keyboard"].get(key, "#ffffff"))
            elif isinstance(widget, NumberLineEdit):
                widget.setValue(config["keyboard"].get(key, 0))

        # 미리보기 업데이트
        self._update_screen_preview()
        self._update_card_preview()

    def update_config(self, config):
        """UI 값을 config에 반영"""
        # 배경화면
        config["text_input"]["background"] = self.keyboard_bg_edit.text()

        # 키보드 위치
        if self.keyboard_position_input:
            config["keyboard"]["x"] = self.keyboard_position_input.get_x()
            config["keyboard"]["y"] = self.keyboard_position_input.get_y()
            config["keyboard"]["width"] = self.keyboard_position_input.get_width()
            config["keyboard"]["height"] = self.keyboard_position_input.get_height()

        # 키보드 스타일
        for key, widget in self.keyboard_style_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["keyboard"][key] = widget.color
            elif isinstance(widget, NumberLineEdit):
                config["keyboard"][key] = widget.value()

        # 입력창 설정 (화면 + 인쇄 통합)
        config["text_input"]["count"] = self.text_input_count_spinbox.value()
        config["text_input"]["items"] = []

        for i in range(len(self.text_input_item_fields)):
            screen_fields = self.text_input_item_fields[i] if i < len(self.text_input_item_fields) else {}
            print_fields = self.print_input_item_fields[i] if i < len(self.print_input_item_fields) else {}

            item = {
                "label": screen_fields["label"].text() if "label" in screen_fields else "",
                "placeholder": screen_fields["placeholder"].text() if "placeholder" in screen_fields else "",
                "font_size": screen_fields["font_size"].value() if "font_size" in screen_fields else 36,
            }

            # 화면 위치
            if "screen_pos" in screen_fields:
                pos = screen_fields["screen_pos"]
                item["screen_x"] = pos.get_x()
                item["screen_y"] = pos.get_y()
                item["screen_width"] = pos.get_width()
                item["screen_height"] = pos.get_height()

            # 인쇄 위치
            if "print_pos" in print_fields:
                pos = print_fields["print_pos"]
                item["x"] = pos.get_x()
                item["y"] = pos.get_y()
                item["width"] = pos.get_width()
                item["height"] = pos.get_height()

            # 출력 폰트
            if "output_font" in print_fields:
                item["output_font"] = print_fields["output_font"].text()
            if "output_font_size" in print_fields:
                item["output_font_size"] = print_fields["output_font_size"].value()
            if "output_font_color" in print_fields:
                item["output_font_color"] = print_fields["output_font_color"].color

            config["text_input"]["items"].append(item)

        # 고정 텍스트 설정
        config["texts"]["count"] = self.text_count_spinbox.value()
        config["texts"]["items"] = []

        for fields in self.text_item_fields:
            item = {
                "content": fields["content"].text() if "content" in fields else "",
                "font": fields["font"].text() if "font" in fields else "",
                "font_size": fields["font_size"].value() if "font_size" in fields else 16,
                "font_color": fields["font_color"].color if "font_color" in fields else "#000000",
            }

            if "pos" in fields:
                pos = fields["pos"]
                item["x"] = pos.get_x()
                item["y"] = pos.get_y()
                item["width"] = pos.get_width()
                item["height"] = pos.get_height()

            config["texts"]["items"].append(item)
