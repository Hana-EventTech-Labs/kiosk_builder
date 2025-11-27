from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QWidget, QTabWidget,
                              QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import TextPreviewWidget
from utils.file_handler import FileHandler
from .base_tab import BaseTab

# 발급완료 화면 screen_key = "6" (complete)
COMPLETE_SCREEN_KEY = "6"

class CompleteTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.screen_preview = None
        # 언어별 배경화면 필드
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

        # 발급완료 화면 설정
        complete_group = QGroupBox("발급완료 화면 설정")
        self.apply_left_aligned_group_style(complete_group)
        complete_layout = QFormLayout(complete_group)

        # 필드 저장을 위한 딕셔너리
        self.complete_fields = {}

        # 배경화면 선택 레이아웃 (레이블 + ? 버튼)
        bg_label_layout = QHBoxLayout()
        bg_label = QLabel("배경화면:")
        bg_label_layout.addWidget(bg_label)

        # ? 도움말 버튼
        help_btn = QPushButton("?")
        help_btn.setFixedSize(20, 20)
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
        bg_label_layout.addWidget(help_btn)
        bg_label_layout.addStretch()

        complete_layout.addRow(bg_label_layout)

        # 기본 배경화면
        background_layout = QHBoxLayout()
        saved_bg = FileHandler.get_background_display_name(COMPLETE_SCREEN_KEY)
        background_edit = QLineEdit(saved_bg)
        background_edit.setReadOnly(True)
        background_edit.setPlaceholderText("배경화면 없음")
        background_edit.textChanged.connect(self._update_screen_preview)
        background_layout.addWidget(background_edit, 1)
        self.complete_fields["background"] = background_edit

        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(self._browse_and_update_background)
        background_layout.addWidget(browse_button)

        reset_button = QPushButton("초기화")
        reset_button.setFixedWidth(60)
        reset_button.setToolTip("배경화면을 삭제합니다")
        reset_button.clicked.connect(self._reset_background)
        background_layout.addWidget(reset_button)

        complete_layout.addRow("기본:", background_layout)

        # 한국어 배경화면
        ko_bg_layout = QHBoxLayout()
        saved_ko_bg = FileHandler.get_background_display_name(COMPLETE_SCREEN_KEY, lang="ko")
        self.ko_bg_edit = QLineEdit(saved_ko_bg)
        self.ko_bg_edit.setReadOnly(True)
        self.ko_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        ko_bg_layout.addWidget(self.ko_bg_edit, 1)
        self.lang_bg_fields["ko"]["background"] = self.ko_bg_edit
        ko_browse_btn = QPushButton("찾기...")
        ko_browse_btn.clicked.connect(lambda: self._browse_lang_bg("ko"))
        ko_bg_layout.addWidget(ko_browse_btn)
        ko_reset_btn = QPushButton("초기화")
        ko_reset_btn.setFixedWidth(60)
        ko_reset_btn.clicked.connect(lambda: self._reset_lang_bg("ko"))
        ko_bg_layout.addWidget(ko_reset_btn)
        complete_layout.addRow("🇰🇷 한국어:", ko_bg_layout)

        # 영어 배경화면
        en_bg_layout = QHBoxLayout()
        saved_en_bg = FileHandler.get_background_display_name(COMPLETE_SCREEN_KEY, lang="en")
        self.en_bg_edit = QLineEdit(saved_en_bg)
        self.en_bg_edit.setReadOnly(True)
        self.en_bg_edit.setPlaceholderText("미설정 (기본 사용)")
        en_bg_layout.addWidget(self.en_bg_edit, 1)
        self.lang_bg_fields["en"]["background"] = self.en_bg_edit
        en_browse_btn = QPushButton("찾기...")
        en_browse_btn.clicked.connect(lambda: self._browse_lang_bg("en"))
        en_bg_layout.addWidget(en_browse_btn)
        en_reset_btn = QPushButton("초기화")
        en_reset_btn.setFixedWidth(60)
        en_reset_btn.clicked.connect(lambda: self._reset_lang_bg("en"))
        en_bg_layout.addWidget(en_reset_btn)
        complete_layout.addRow("🇺🇸 English:", en_bg_layout)

        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["complete"]["font"])
        font_layout.addWidget(font_edit, 1)
        self.complete_fields["font"] = font_edit

        # 폰트 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked: FileHandler.browse_font_file(self, font_edit))
        font_layout.addWidget(browse_button)

        complete_layout.addRow("폰트:", font_layout)

        phrase_edit = QLineEdit(self.config["complete"]["phrase"])
        phrase_edit.textChanged.connect(self._update_screen_preview)
        complete_layout.addRow("문구:", phrase_edit)
        self.complete_fields["phrase"] = phrase_edit

        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config["complete"]["font_size"])
        font_size_edit.textChanged.connect(self._update_screen_preview)
        complete_layout.addRow("폰트 크기:", font_size_edit)
        self.complete_fields["font_size"] = font_size_edit

        font_color_button = ColorPickerButton(self.config["complete"]["font_color"])
        font_color_button.color_changed.connect(self._update_screen_preview)
        complete_layout.addRow("폰트 색상:", font_color_button)
        self.complete_fields["font_color"] = font_color_button

        x_edit = NumberLineEdit()
        x_edit.setValue(self.config["complete"]["x"])
        x_edit.textChanged.connect(self._update_screen_preview)
        complete_layout.addRow("X 위치:", x_edit)
        self.complete_fields["x"] = x_edit

        y_edit = NumberLineEdit()
        y_edit.setValue(self.config["complete"]["y"])
        y_edit.textChanged.connect(self._update_screen_preview)
        complete_layout.addRow("Y 위치:", y_edit)
        self.complete_fields["y"] = y_edit

        # 시간 필드
        time_edit = NumberLineEdit()
        time_edit.setValue(self.config["complete"]["complete_time"])
        complete_layout.addRow("시간 (ms):", time_edit)
        self.complete_fields["complete_time"] = time_edit

        content_layout.addWidget(complete_group)

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

        self.screen_preview = TextPreviewWidget()
        self.screen_preview.position_changed.connect(self._on_text_position_changed)
        screen_preview_layout.addWidget(self.screen_preview, 0, Qt.AlignHCenter)

        preview_layout.addWidget(screen_preview_group)
        preview_layout.addStretch()

        main_layout.addWidget(preview_widget, 1)

        # 초기 미리보기 업데이트
        self._update_screen_preview()

    def _browse_and_update_background(self):
        """배경화면 파일 선택 및 업데이트"""
        FileHandler.browse_background_file(self, self.complete_fields["background"], COMPLETE_SCREEN_KEY)
        saved_bg = FileHandler.get_background_display_name(COMPLETE_SCREEN_KEY)
        self.complete_fields["background"].setText(saved_bg)
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
            FileHandler.delete_background(COMPLETE_SCREEN_KEY)
            self.complete_fields["background"].setText("")
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
            FileHandler.browse_background_file(self, bg_edit, COMPLETE_SCREEN_KEY, lang=lang_code)
            saved_bg = FileHandler.get_background_display_name(COMPLETE_SCREEN_KEY, lang=lang_code)
            bg_edit.setText(saved_bg)
            self._update_screen_preview()

    def _reset_lang_bg(self, lang_code: str):
        """언어별 배경화면 초기화"""
        from PySide6.QtWidgets import QMessageBox
        lang_name = "한국어" if lang_code == "ko" else "영어"
        reply = QMessageBox.question(
            self, f"{lang_name} 배경화면 초기화",
            f"{lang_name} 발급완료 화면의 배경화면을 삭제하시겠습니까?\n삭제 시 기본 배경화면이 사용됩니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            FileHandler.delete_background(COMPLETE_SCREEN_KEY, lang=lang_code)
            bg_edit = self.lang_bg_fields[lang_code].get("background")
            if bg_edit:
                bg_edit.setText("")
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
        bg_path = FileHandler.resolve_background_path(COMPLETE_SCREEN_KEY)
        self.screen_preview.set_background(bg_path, QColor("#1a1a1a"))

        # 텍스트 설정
        try:
            text = self.complete_fields["phrase"].text()
            font_path = self.complete_fields["font"].text()
            font_size = self.complete_fields["font_size"].value()
            font_color = self.complete_fields["font_color"].color
            x = self.complete_fields["x"].value()
            y = self.complete_fields["y"].value()

            self.screen_preview.add_text(
                "complete_text",
                text,
                x, y,
                font_path=font_path,
                font_size=font_size,
                color=QColor(font_color),
                draggable=True
            )
        except (AttributeError, KeyError):
            pass

        self.request_real_time_update()

    def _on_text_position_changed(self, element_id, x, y):
        """드래그로 텍스트 위치 변경 시 호출"""
        if element_id == "complete_text":
            self.complete_fields['x'].blockSignals(True)
            self.complete_fields['y'].blockSignals(True)

            self.complete_fields['x'].setValue(x)
            self.complete_fields['y'].setValue(y)

            self.complete_fields['x'].blockSignals(False)
            self.complete_fields['y'].blockSignals(False)

            self.request_real_time_update()

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config
        for key, widget in self.complete_fields.items():
            if isinstance(widget, ColorPickerButton):
                widget.update_color(config["complete"][key])
            else:
                if isinstance(widget, NumberLineEdit):
                    widget.setValue(config["complete"][key])
                else:
                    widget.setText(config["complete"][key])

        # 미리보기 업데이트
        self._update_screen_preview()

    def update_config(self, config):
        """UI 값을 config에 반영"""
        for key, widget in self.complete_fields.items():
            if isinstance(widget, ColorPickerButton):
                config["complete"][key] = widget.color
            else:
                if isinstance(widget, NumberLineEdit):
                    config["complete"][key] = widget.value()
                else:
                    config["complete"][key] = widget.text()
