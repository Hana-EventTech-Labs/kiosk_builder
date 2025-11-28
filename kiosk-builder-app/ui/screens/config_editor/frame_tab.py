from PySide6.QtWidgets import (QGroupBox, QFormLayout, QHBoxLayout, QVBoxLayout,
                              QLineEdit, QPushButton, QListWidget, QListWidgetItem, QWidget, QLabel, QTabWidget,
                              QDialog, QDialogButtonBox, QFrame)
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QColor
from .base_tab import BaseTab
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import LivePreviewWidget
from ui.components.position_size_input import PositionSizeInput
from utils.file_handler import FileHandler

# 프레임 선택 화면 screen_key = "4"
FRAME_SCREEN_KEY = "4"

class FrameTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.sub_tabs = None
        # 각 탭의 미리보기 위젯
        self.screen_preview_screen = None
        self.screen_preview_frame = None
        # 언어별 배경화면 필드
        self.lang_bg_fields = {"ko": {}, "en": {}}
        self.init_ui()

    def init_ui(self):
        scroll_content_layout = self.create_tab_with_scroll()

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

        # 탭 2: 프레임 설정
        self._create_frame_settings_tab()

        scroll_content_layout.addWidget(self.sub_tabs)
        scroll_content_layout.addStretch()

        # 기존 프레임 목록 로드
        self.load_frame_list()

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

        desc = QLabel("프레임 영역을 드래그하여 위치 조절")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_layout.addWidget(desc)

        self.screen_preview_screen = LivePreviewWidget(preview_size=QSize(350, 350))
        self.screen_preview_screen.position_changed.connect(self._on_frame_position_changed)
        self.screen_preview_screen.size_changed.connect(self._on_frame_size_changed)
        preview_layout.addWidget(self.screen_preview_screen, 0, Qt.AlignCenter)

        hint = QLabel("모서리를 드래그하여 크기 조절")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        preview_layout.addWidget(hint)

        right_layout.addWidget(preview_group)

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "화면 설정")

    # ═══════════════════════════════════════════════════════════════
    # 탭 2: 프레임 설정
    # ═══════════════════════════════════════════════════════════════
    def _create_frame_settings_tab(self):
        """프레임 설정 탭 생성 - 좌측(설정) + 우측(미리보기)"""
        tab_widget = QWidget()
        tab_main_layout = QHBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(10, 10, 10, 10)
        tab_main_layout.setSpacing(20)

        # 좌측: 설정 영역
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 프레임 추가 그룹
        frame_add_group = QGroupBox("프레임 추가")
        self.apply_left_aligned_group_style(frame_add_group)
        frame_add_layout = QVBoxLayout(frame_add_group)

        # 프레임 파일 추가 레이아웃
        add_frame_layout = QHBoxLayout()
        self.frame_file_edit = QLineEdit()
        self.frame_file_edit.setPlaceholderText("프레임 파일을 선택하세요...")
        add_frame_layout.addWidget(self.frame_file_edit, 1)

        # 프레임 파일 선택 버튼
        frame_browse_button = QPushButton("찾기...")
        frame_browse_button.clicked.connect(self.browse_frame_file)
        add_frame_layout.addWidget(frame_browse_button)

        # 프레임 추가 버튼
        add_frame_button = QPushButton("프레임 추가")
        add_frame_button.clicked.connect(self.add_frame_to_list)
        add_frame_layout.addWidget(add_frame_button)

        frame_add_layout.addLayout(add_frame_layout)

        # 프레임 목록
        self.frame_list = QListWidget()
        self.frame_list.setMaximumHeight(150)
        self.frame_list.currentItemChanged.connect(self._on_frame_selection_changed)
        frame_add_layout.addWidget(self.frame_list)

        # 프레임 삭제 버튼
        remove_frame_button = QPushButton("선택한 프레임 삭제")
        remove_frame_button.clicked.connect(self.remove_frame_from_list)
        frame_add_layout.addWidget(remove_frame_button)

        left_layout.addWidget(frame_add_group)

        # 프레임 설정 그룹
        frame_group = QGroupBox("📐 프레임 설정")
        self.apply_left_aligned_group_style(frame_group)
        frame_layout = QVBoxLayout(frame_group)
        frame_layout.setSpacing(10)

        self.frame_fields = {}

        # 'photo_frame' 설정이 없으면 기본값으로 초기화
        if "photo_frame" not in self.config:
            self.config["photo_frame"] = {
                "font_size": 32,
                "font_color": "green",
                "width": 800,
                "height": 600,
                "font": "",
                "background": "",
                "frame_files": []
            }

        # 프레임 크기 (위치 없이 크기만 표시)
        size_label = QLabel("프레임 크기:")
        size_label.setStyleSheet("font-weight: bold; color: #555;")
        frame_layout.addWidget(size_label)

        self.frame_size_input = PositionSizeInput(show_position=False, show_size=True)
        self.frame_size_input.set_values(
            width=self.config["photo_frame"].get("width", 800),
            height=self.config["photo_frame"].get("height", 600)
        )
        self.frame_size_input.value_changed.connect(self._update_screen_preview)
        frame_layout.addWidget(self.frame_size_input)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        frame_layout.addWidget(separator)

        # 폰트 설정 (FormLayout으로)
        font_form = QFormLayout()
        font_form.setSpacing(8)

        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["photo_frame"].get("font", ""))
        font_layout.addWidget(font_edit, 1)
        self.frame_fields["font"] = font_edit

        # 폰트 파일 선택 버튼 추가
        font_browse_button = QPushButton("찾기...")
        font_browse_button.clicked.connect(lambda checked: FileHandler.browse_font_file(self, font_edit))
        font_layout.addWidget(font_browse_button)
        font_form.addRow("폰트:", font_layout)

        # 글자 크기
        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config["photo_frame"].get("font_size", 32))
        font_form.addRow("글자 크기:", font_size_edit)
        self.frame_fields["font_size"] = font_size_edit

        # 색상 필드
        font_color_button = ColorPickerButton(self.config["photo_frame"].get("font_color", "green"))
        font_form.addRow("글자 색상:", font_color_button)
        self.frame_fields["font_color"] = font_color_button

        frame_layout.addLayout(font_form)
        left_layout.addWidget(frame_group)
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

        desc = QLabel("프레임 영역을 드래그하여 위치 조절")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_layout.addWidget(desc)

        self.screen_preview_frame = LivePreviewWidget(preview_size=QSize(350, 350))
        self.screen_preview_frame.position_changed.connect(self._on_frame_position_changed)
        self.screen_preview_frame.size_changed.connect(self._on_frame_size_changed)
        preview_layout.addWidget(self.screen_preview_frame, 0, Qt.AlignCenter)

        hint = QLabel("모서리를 드래그하여 크기 조절")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #7f8c8d; font-size: 10px; font-style: italic;")
        preview_layout.addWidget(hint)

        right_layout.addWidget(preview_group)

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "프레임 설정")

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
        saved_bg = FileHandler.get_background_display_name(FRAME_SCREEN_KEY)
        self.frame_bg_edit = QLineEdit(saved_bg)
        self.frame_bg_edit.setReadOnly(True)
        self.frame_bg_edit.setPlaceholderText("배경화면 없음")
        self.frame_bg_edit.textChanged.connect(self._update_screen_preview)
        bg_row.addWidget(self.frame_bg_edit, 1)

        browse_button = QPushButton("찾기...")
        browse_button.setFixedWidth(60)
        browse_button.clicked.connect(self._on_browse_background)
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
        saved_ko_bg = FileHandler.get_background_display_name(FRAME_SCREEN_KEY, lang="ko")
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
        saved_en_bg = FileHandler.get_background_display_name(FRAME_SCREEN_KEY, lang="en")
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

        parent_layout.addWidget(bg_group)

    def _on_browse_background(self):
        """배경화면 파일 선택"""
        FileHandler.browse_background_file(self, self.frame_bg_edit, FRAME_SCREEN_KEY)
        saved_bg = FileHandler.get_background_display_name(FRAME_SCREEN_KEY)
        self.frame_bg_edit.setText(saved_bg)
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
            FileHandler.delete_background(FRAME_SCREEN_KEY)
            self.frame_bg_edit.setText("")
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
            FileHandler.browse_background_file(self, bg_edit, FRAME_SCREEN_KEY, lang=lang_code)
            saved_bg = FileHandler.get_background_display_name(FRAME_SCREEN_KEY, lang=lang_code)
            bg_edit.setText(saved_bg)
            self._update_screen_preview()

    def _reset_lang_bg(self, lang_code: str):
        """언어별 배경화면 초기화"""
        from PySide6.QtWidgets import QMessageBox
        lang_name = "한국어" if lang_code == "ko" else "영어"
        reply = QMessageBox.question(
            self, f"{lang_name} 배경화면 초기화",
            f"{lang_name} 프레임 선택 화면의 배경화면을 삭제하시겠습니까?\n삭제 시 기본 배경화면이 사용됩니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(FRAME_SCREEN_KEY, lang=lang_code)
            bg_edit = self.lang_bg_fields[lang_code].get("background")
            if bg_edit:
                bg_edit.setText("")
            self._update_screen_preview()

    def _update_screen_preview(self):
        """화면 미리보기 업데이트 - 모든 탭의 미리보기 동기화"""
        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        # 배경 이미지 경로
        bg_path = FileHandler.resolve_background_path(FRAME_SCREEN_KEY)

        # 프레임 영역 크기
        try:
            frame_width = self.frame_size_input.get_width()
            frame_height = self.frame_size_input.get_height()
        except (AttributeError, KeyError):
            frame_width, frame_height = 800, 600

        # 프레임 중앙 위치 계산
        frame_x = (monitor_width - frame_width) // 2
        frame_y = (monitor_height - frame_height) // 2
        frame_rect = QRect(frame_x, frame_y, frame_width, frame_height)

        # 선택된 프레임 이미지
        selected_item = self.frame_list.currentItem() if hasattr(self, 'frame_list') else None
        frame_image_name = selected_item.text() if selected_item else None
        frame_image_path = FileHandler.resolve_frame_path(frame_image_name) if frame_image_name else None

        # 2개의 미리보기 위젯 업데이트
        for preview in [self.screen_preview_screen, self.screen_preview_frame]:
            if not preview:
                continue

            preview.set_original_size(monitor_width, monitor_height)
            preview.set_background(bg_path, QColor("#ffffff"))
            preview.set_card_border(True, QColor("#333333"), 2)

            preview.add_element(
                "frame_area",
                frame_rect,
                color=QColor("cyan"),
                image_path=frame_image_path,
                label="프레임",
                draggable=True
            )

        self.request_real_time_update()

    def _on_frame_position_changed(self, element_id, x, y):
        """드래그로 프레임 위치 변경 시 호출"""
        # 프레임 위치는 중앙 정렬 기준이므로 별도 처리 필요 없음
        self.request_real_time_update()

    def _on_frame_size_changed(self, element_id, x, y, width, height):
        """드래그로 프레임 크기 변경 시 호출"""
        if element_id == "frame_area":
            self.frame_size_input.block_all_signals(True)
            self.frame_size_input.set_width(width)
            self.frame_size_input.set_height(height)
            self.frame_size_input.block_all_signals(False)
            self.request_real_time_update()

    def _on_frame_selection_changed(self, current, previous):
        """프레임 목록 선택 변경 시 미리보기 업데이트"""
        self._update_screen_preview()

    def browse_frame_file(self):
        """프레임 파일 선택"""
        FileHandler.browse_frame_file(self, self.frame_file_edit)

    def add_frame_to_list(self):
        """프레임을 목록에 추가"""
        frame_file = self.frame_file_edit.text().strip()
        if not frame_file:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "경고", "프레임 파일을 선택해주세요.")
            return

        # 중복 확인
        for i in range(self.frame_list.count()):
            if self.frame_list.item(i).text() == frame_file:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "경고", "이미 추가된 프레임입니다.")
                return

        # 목록에 추가
        self.frame_list.addItem(frame_file)
        self.frame_file_edit.clear()

        # config 업데이트
        self.update_frame_config()

    def remove_frame_from_list(self):
        """선택한 프레임을 목록에서 삭제"""
        current_item = self.frame_list.currentItem()
        if current_item:
            row = self.frame_list.row(current_item)
            self.frame_list.takeItem(row)

            # config 업데이트
            self.update_frame_config()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "경고", "삭제할 프레임을 선택해주세요.")

    def update_frame_config(self):
        """프레임 목록을 config에 반영"""
        frame_files = []
        for i in range(self.frame_list.count()):
            frame_files.append(self.frame_list.item(i).text())

        if "photo_frame" not in self.config:
            self.config["photo_frame"] = {}

        self.config["photo_frame"]["frame_files"] = frame_files

    def load_frame_list(self):
        """config에서 프레임 목록 로드"""
        frame_files = self.config.get("photo_frame", {}).get("frame_files", [])
        self.frame_list.clear()

        for frame_file in frame_files:
            self.frame_list.addItem(frame_file)

    def update_config(self, config):
        """UI 값을 config에 반영"""
        if "photo_frame" not in config:
            config["photo_frame"] = {}

        # 배경화면 저장
        config["photo_frame"]["background"] = self.frame_bg_edit.text()

        # 프레임 목록 저장
        frame_files = []
        for i in range(self.frame_list.count()):
            frame_files.append(self.frame_list.item(i).text())
        config["photo_frame"]["frame_files"] = frame_files

        # 프레임 크기 저장
        config["photo_frame"]["width"] = self.frame_size_input.get_width()
        config["photo_frame"]["height"] = self.frame_size_input.get_height()

        # 다른 필드들 저장
        for key, widget in self.frame_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["photo_frame"][key] = widget.color
            elif isinstance(widget, NumberLineEdit):
                config["photo_frame"][key] = widget.value()
            else:  # QLineEdit (font)
                config["photo_frame"][key] = widget.text()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config

        # 배경화면 업데이트
        self.frame_bg_edit.setText(config.get("photo_frame", {}).get("background", ""))

        # 프레임 목록 업데이트
        self.load_frame_list()

        # 프레임 크기 업데이트
        self.frame_size_input.set_values(
            width=config.get("photo_frame", {}).get("width", 800),
            height=config.get("photo_frame", {}).get("height", 600)
        )

        if "photo_frame" in config:
            for key, widget in self.frame_fields.items():
                if isinstance(widget, ColorPickerButton):
                    widget.update_color(config["photo_frame"].get(key, "green"))
                elif isinstance(widget, NumberLineEdit):
                    widget.setValue(config["photo_frame"].get(key, 32))
                else:  # QLineEdit (font)
                    widget.setText(config["photo_frame"].get(key, ""))

        # 미리보기 업데이트
        self._update_screen_preview()
