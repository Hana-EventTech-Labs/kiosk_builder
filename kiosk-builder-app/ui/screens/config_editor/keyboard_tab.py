from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QSpinBox, QWidget,
                              QTabWidget, QScrollArea, QFrame, QSizePolicy)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QRect, QSize
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import LivePreviewWidget
from ui.components.position_size_input import PositionSizeInput
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

        # 설정 필드들
        self.keyboard_position_input = None
        self.text_input_item_fields = []  # 입력창 화면 표시 설정
        self.print_input_item_fields = []  # 사용자 입력 텍스트 인쇄 설정
        self.text_item_fields = []  # 고정 텍스트 설정
        self.keyboard_style_fields = {}

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
                background: #e0e0e0;
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
                background: #d0d0d0;
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
        main_layout.setSpacing(15)

        # 좌측: 설정 영역 (스크롤 가능)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { border: none; }")
        settings_scroll.setMinimumWidth(400)

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(12)

        # 1. 배경화면 설정
        bg_group = QGroupBox("배경화면")
        self.apply_left_aligned_group_style(bg_group)
        bg_layout = QHBoxLayout(bg_group)

        saved_bg = FileHandler.get_background_display_name(KEYBOARD_SCREEN_KEY)
        self.keyboard_bg_edit = QLineEdit(saved_bg)
        self.keyboard_bg_edit.setReadOnly(True)
        self.keyboard_bg_edit.setPlaceholderText("배경화면 없음")
        self.keyboard_bg_edit.textChanged.connect(self._update_screen_preview)
        bg_layout.addWidget(self.keyboard_bg_edit, 1)

        browse_btn = QPushButton("찾기...")
        browse_btn.clicked.connect(self._browse_and_update_background)
        bg_layout.addWidget(browse_btn)

        reset_btn = QPushButton("초기화")
        reset_btn.setFixedWidth(60)
        reset_btn.clicked.connect(self._reset_background)
        bg_layout.addWidget(reset_btn)

        settings_layout.addWidget(bg_group)

        # 2. 키보드 위치 설정
        keyboard_group = QGroupBox("키보드 위치")
        self.apply_left_aligned_group_style(keyboard_group)
        keyboard_layout = QVBoxLayout(keyboard_group)

        self.keyboard_position_input = PositionSizeInput()
        self.keyboard_position_input.set_values(
            x=self.config["keyboard"]["x"],
            y=self.config["keyboard"]["y"],
            width=self.config["keyboard"]["width"],
            height=self.config["keyboard"]["height"]
        )
        self.keyboard_position_input.value_changed.connect(self._update_screen_preview)
        keyboard_layout.addWidget(self.keyboard_position_input)

        # 버튼들
        btn_layout = QHBoxLayout()
        fill_btn = QPushButton("화면 채우기")
        fill_btn.clicked.connect(self._fill_keyboard_frame)
        center_btn = QPushButton("가운데 정렬")
        center_btn.clicked.connect(self._center_keyboard_frame)
        btn_layout.addWidget(fill_btn)
        btn_layout.addWidget(center_btn)
        btn_layout.addStretch()
        keyboard_layout.addLayout(btn_layout)

        settings_layout.addWidget(keyboard_group)

        # 3. 입력창 설정 (화면 표시만)
        input_group = QGroupBox("입력창 (화면에 표시되는 입력 필드)")
        self.apply_left_aligned_group_style(input_group)
        input_layout = QVBoxLayout(input_group)

        # 입력창 개수
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("입력창 개수:"))
        self.text_input_count_spinbox = QSpinBox()
        self.text_input_count_spinbox.setRange(1, 10)
        count_value = max(1, self.config["text_input"]["count"])
        self.text_input_count_spinbox.setValue(count_value)
        self.text_input_count_spinbox.valueChanged.connect(self._on_input_count_changed)
        count_layout.addWidget(self.text_input_count_spinbox)
        count_layout.addStretch()
        input_layout.addLayout(count_layout)

        # 안내 문구
        info_label = QLabel("※ 입력창에 입력된 텍스트의 인쇄 위치는 [인쇄 설정] 탭에서 설정합니다.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        info_label.setWordWrap(True)
        input_layout.addWidget(info_label)

        # 입력창 항목들 컨테이너
        self.input_items_container = QWidget()
        self.input_items_layout = QVBoxLayout(self.input_items_container)
        self.input_items_layout.setContentsMargins(0, 0, 0, 0)
        self.input_items_layout.setSpacing(10)
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

        self.screen_preview = LivePreviewWidget()
        self.screen_preview.position_changed.connect(self._on_screen_element_position_changed)
        self.screen_preview.size_changed.connect(self._on_screen_element_size_changed)
        preview_group_layout.addWidget(self.screen_preview, 0, Qt.AlignHCenter)

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
        settings_scroll.setStyleSheet("QScrollArea { border: none; }")

        settings_widget = QWidget()
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

        preview_group = QGroupBox("카드 인쇄 미리보기")
        self.apply_left_aligned_group_style(preview_group)
        preview_group_layout = QVBoxLayout(preview_group)

        self.card_preview = LivePreviewWidget()
        self.card_preview.position_changed.connect(self._on_card_element_position_changed)
        self.card_preview.size_changed.connect(self._on_card_element_size_changed)
        preview_group_layout.addWidget(self.card_preview, 0, Qt.AlignHCenter)

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
        """키보드 스타일 탭 생성"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(20)

        # 좌측: 색상 설정
        color_scroll = QScrollArea()
        color_scroll.setWidgetResizable(True)
        color_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        color_scroll.setStyleSheet("QScrollArea { border: none; }")

        color_widget = QWidget()
        color_layout = QVBoxLayout(color_widget)

        color_group = QGroupBox("키보드 색상")
        self.apply_left_aligned_group_style(color_group)
        color_form = QFormLayout(color_group)

        color_keys = [
            ("bg_color", "배경색"),
            ("border_color", "테두리색"),
            ("button_bg_color", "버튼 배경"),
            ("button_text_color", "버튼 글자"),
            ("button_pressed_color", "버튼 누름"),
            ("hangul_btn_color", "한글 버튼"),
            ("shift_btn_color", "Shift 버튼"),
            ("backspace_btn_color", "지우기 버튼"),
            ("next_btn_color", "다음 버튼")
        ]

        for key, label in color_keys:
            color_button = ColorPickerButton(self.config["keyboard"].get(key, "#ffffff"))
            color_form.addRow(f"{label}:", color_button)
            self.keyboard_style_fields[key] = color_button

        color_layout.addWidget(color_group)
        color_layout.addStretch()

        color_scroll.setWidget(color_widget)
        main_layout.addWidget(color_scroll, 1)

        # 우측: 크기 및 기타 설정
        size_scroll = QScrollArea()
        size_scroll.setWidgetResizable(True)
        size_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        size_scroll.setStyleSheet("QScrollArea { border: none; }")

        size_widget = QWidget()
        size_layout = QVBoxLayout(size_widget)

        size_group = QGroupBox("키보드 크기/여백")
        self.apply_left_aligned_group_style(size_group)
        size_form = QFormLayout(size_group)

        number_keys = [
            ("border_width", "테두리 두께"),
            ("border_radius", "테두리 둥글기"),
            ("padding", "내부 여백"),
            ("font_size", "글자 크기"),
            ("button_radius", "버튼 둥글기"),
            ("special_btn_width", "특수버튼 너비")
        ]

        for key, label in number_keys:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["keyboard"].get(key, 0))
            size_form.addRow(f"{label}:", line_edit)
            self.keyboard_style_fields[key] = line_edit

        size_layout.addWidget(size_group)

        # 입력 제한 설정
        limit_group = QGroupBox("입력 글자 수 제한")
        self.apply_left_aligned_group_style(limit_group)
        limit_form = QFormLayout(limit_group)

        limit_keys = [
            ("max_hangul", "최대 한글"),
            ("max_lowercase", "최대 소문자"),
            ("max_uppercase", "최대 대문자")
        ]

        for key, label in limit_keys:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["keyboard"].get(key, 10))
            limit_form.addRow(f"{label}:", line_edit)
            self.keyboard_style_fields[key] = line_edit

        size_layout.addWidget(limit_group)
        size_layout.addStretch()

        size_scroll.setWidget(size_widget)
        main_layout.addWidget(size_scroll, 1)

        self.sub_tabs.addTab(tab, "키보드 스타일")

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

            # 항목 그룹 생성
            item_group = QGroupBox(f"입력창 {i+1}")
            item_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #2196F3;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #2196F3;
                }
            """)
            item_layout = QFormLayout(item_group)
            item_layout.setSpacing(6)

            fields = {}

            # 이름
            label_edit = QLineEdit(item_data.get("label", ""))
            label_edit.setPlaceholderText("예: 이름, 전화번호")
            label_edit.textChanged.connect(lambda: self._update_all_previews())
            item_layout.addRow("항목 이름:", label_edit)
            fields["label"] = label_edit

            # 입력 예시
            placeholder_edit = QLineEdit(item_data.get("placeholder", ""))
            placeholder_edit.setPlaceholderText("예: 홍길동")
            item_layout.addRow("입력 예시:", placeholder_edit)
            fields["placeholder"] = placeholder_edit

            # 화면 위치
            screen_pos = PositionSizeInput()
            screen_pos.set_values(
                x=item_data.get("screen_x", 40),
                y=item_data.get("screen_y", 200),
                width=item_data.get("screen_width", 1000),
                height=item_data.get("screen_height", 70)
            )
            screen_pos.value_changed.connect(self._update_screen_preview)
            item_layout.addRow("화면 위치:", screen_pos)
            fields["screen_pos"] = screen_pos

            # 화면 폰트 크기
            font_size_edit = NumberLineEdit()
            font_size_edit.setValue(item_data.get("font_size", 36))
            font_size_edit.setFixedWidth(80)
            item_layout.addRow("글자 크기:", font_size_edit)
            fields["font_size"] = font_size_edit

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
        self.screen_preview.set_background(bg_path, QColor("#1a1a1a"))

        # 키보드 영역
        if self.keyboard_position_input:
            kb_rect = QRect(
                self.keyboard_position_input.get_x(),
                self.keyboard_position_input.get_y(),
                self.keyboard_position_input.get_width(),
                self.keyboard_position_input.get_height()
            )
            self.screen_preview.add_element(
                "keyboard", kb_rect,
                color=QColor("red"),
                label="키보드",
                draggable=True
            )

        # 입력창들
        colors = [QColor("lime"), QColor("cyan"), QColor("yellow"), QColor("magenta"), QColor("orange")]
        for i, fields in enumerate(self.text_input_item_fields):
            if "screen_pos" in fields:
                pos = fields["screen_pos"]
                rect = QRect(pos.get_x(), pos.get_y(), pos.get_width(), pos.get_height())
                label = fields.get("label")
                label_text = label.text() if label and label.text() else f"입력창{i+1}"
                self.screen_preview.add_element(
                    f"input_{i}", rect,
                    color=colors[i % len(colors)],
                    label=label_text,
                    draggable=True
                )

        self.request_real_time_update()

    def _update_card_preview(self):
        """카드 미리보기 업데이트 (사용자 입력 텍스트 + 고정 텍스트)"""
        if not self.card_preview:
            return

        self.card_preview.clear_elements()

        # 카드 크기
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        self.card_preview.set_original_size(card_width, card_height)
        self.card_preview.set_background_color(QColor("white"))

        # 사용자 입력 텍스트 인쇄 위치
        input_colors = [QColor("red"), QColor("blue"), QColor("purple"), QColor("orange"), QColor("brown")]
        for i, fields in enumerate(self.print_input_item_fields):
            if "print_pos" in fields:
                pos = fields["print_pos"]
                rect = QRect(pos.get_x(), pos.get_y(), pos.get_width(), pos.get_height())
                # 이름 가져오기
                label_text = f"입력텍스트{i+1}"
                if i < len(self.text_input_item_fields) and "label" in self.text_input_item_fields[i]:
                    label_val = self.text_input_item_fields[i]["label"].text()
                    if label_val:
                        label_text = label_val
                self.card_preview.add_element(
                    f"print_input_{i}", rect,
                    color=input_colors[i % len(input_colors)],
                    label=label_text,
                    draggable=True
                )

        # 고정 텍스트 위치
        fixed_colors = [QColor("green"), QColor("teal"), QColor("cyan"), QColor("magenta"), QColor("gray")]
        for i, fields in enumerate(self.text_item_fields):
            if "pos" in fields:
                pos = fields["pos"]
                rect = QRect(pos.get_x(), pos.get_y(), pos.get_width(), pos.get_height())
                content = fields.get("content")
                label_text = content.text() if content and content.text() else f"고정텍스트{i+1}"
                self.card_preview.add_element(
                    f"fixed_text_{i}", rect,
                    color=fixed_colors[i % len(fixed_colors)],
                    label=label_text,
                    draggable=True
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
