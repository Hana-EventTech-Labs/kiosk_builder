from PySide6.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QWidget, QTabWidget,
                              QDialog, QDialogButtonBox)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QRect
from ui.components.inputs import NumberLineEdit
from ui.components.live_preview import LivePreviewWidget
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
        # 언어별 배경화면 필드
        self.lang_bg_fields = {"ko": {}, "en": {}}
        self.init_ui()

    def init_ui(self):
        scroll_content_layout = self.create_tab_with_scroll()

        # 메인 레이아웃 (좌: 설정, 우: 미리보기)
        main_layout = QHBoxLayout()
        scroll_content_layout.addLayout(main_layout)

        # 설정 영역
        settings_widget = QWidget()
        content_layout = QVBoxLayout(settings_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 배경화면 설정
        bg_group = QGroupBox("배경화면 설정")
        self.apply_left_aligned_group_style(bg_group)
        bg_group_layout = QVBoxLayout(bg_group)

        # 기본 배경화면 행 (레이블 + ? 버튼 + 입력필드)
        bg_row = QHBoxLayout()
        bg_label = QLabel("배경화면:")
        bg_row.addWidget(bg_label)

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
        bg_row.addWidget(help_btn)
        bg_row.addSpacing(10)

        saved_bg = FileHandler.get_background_display_name(QR_SCREEN_KEY)
        self.qr_bg_edit = QLineEdit(saved_bg)
        self.qr_bg_edit.setReadOnly(True)
        self.qr_bg_edit.setPlaceholderText("배경화면 없음")
        self.qr_bg_edit.textChanged.connect(self._update_qr_preview)
        bg_row.addWidget(self.qr_bg_edit, 1)

        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(self._browse_and_update_background)
        bg_row.addWidget(browse_button)

        reset_button = QPushButton("초기화")
        reset_button.setFixedWidth(60)
        reset_button.setToolTip("배경화면을 삭제합니다")
        reset_button.clicked.connect(self._reset_background)
        bg_row.addWidget(reset_button)

        bg_group_layout.addLayout(bg_row)

        # 한국어 배경화면
        ko_bg_layout = QHBoxLayout()
        ko_bg_layout.addWidget(QLabel("🇰🇷 한국어:"))
        saved_ko_bg = FileHandler.get_background_display_name(QR_SCREEN_KEY, lang="ko")
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
        bg_group_layout.addLayout(ko_bg_layout)

        # 영어 배경화면
        en_bg_layout = QHBoxLayout()
        en_bg_layout.addWidget(QLabel("🇺🇸 English:"))
        saved_en_bg = FileHandler.get_background_display_name(QR_SCREEN_KEY, lang="en")
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
        bg_group_layout.addLayout(en_bg_layout)

        content_layout.addWidget(bg_group)

        # QR 코드 설정 그룹
        qr_group = QGroupBox("📊 QR 코드 화면 위치")
        self.apply_left_aligned_group_style(qr_group)
        qr_layout = QVBoxLayout(qr_group)

        # 위치/크기 직관적 입력
        self.qr_position_input = PositionSizeInput()
        self.qr_position_input.set_values(
            x=self.config["qr"]["x"],
            y=self.config["qr"]["y"],
            width=self.config["qr"]["preview_width"],
            height=self.config["qr"]["preview_height"]
        )
        self.qr_position_input.value_changed.connect(self._update_qr_preview)
        qr_layout.addWidget(self.qr_position_input)

        content_layout.addWidget(qr_group)

        # 업로드 이미지 설정 그룹박스
        qr_uploaded_group = QGroupBox("🖨️ 이미지 인쇄 위치")
        self.apply_left_aligned_group_style(qr_uploaded_group)
        qr_uploaded_layout = QVBoxLayout(qr_uploaded_group)

        # 위치/크기 직관적 입력
        self.qr_uploaded_input = PositionSizeInput()
        self.qr_uploaded_input.set_values(
            x=self.config["qr_uploaded_image"]["x"],
            y=self.config["qr_uploaded_image"]["y"],
            width=self.config["qr_uploaded_image"]["width"],
            height=self.config["qr_uploaded_image"]["height"]
        )
        self.qr_uploaded_input.value_changed.connect(self._update_card_preview)
        qr_uploaded_layout.addWidget(self.qr_uploaded_input)

        content_layout.addWidget(qr_uploaded_group)
        content_layout.addStretch()

        main_layout.addWidget(settings_widget, 1)

        # 우측 미리보기 영역
        previews_widget = QWidget()
        previews_layout = QVBoxLayout(previews_widget)
        previews_layout.setContentsMargins(0, 0, 0, 0)

        # QR 코드 화면 미리보기
        qr_preview_group = QGroupBox("화면 미리보기")
        self.apply_left_aligned_group_style(qr_preview_group)
        qr_preview_layout = QVBoxLayout(qr_preview_group)

        self.qr_preview = LivePreviewWidget()
        self.qr_preview.position_changed.connect(self._on_qr_position_changed)
        self.qr_preview.size_changed.connect(self._on_qr_size_changed)
        qr_preview_layout.addWidget(self.qr_preview, 0, Qt.AlignHCenter)

        qr_button_layout = QHBoxLayout()
        fill_button_qr = QPushButton("채우기")
        fill_button_qr.clicked.connect(self._fill_qr_frame)
        center_button_qr = QPushButton("가운데 정렬")
        center_button_qr.clicked.connect(self._center_qr_frame)
        qr_button_layout.addWidget(fill_button_qr)
        qr_button_layout.addWidget(center_button_qr)
        qr_preview_layout.addLayout(qr_button_layout)

        previews_layout.addWidget(qr_preview_group)

        # 카드 인쇄 미리보기
        card_preview_group = QGroupBox("카드 인쇄 미리보기")
        self.apply_left_aligned_group_style(card_preview_group)
        card_preview_layout = QVBoxLayout(card_preview_group)

        self.card_preview = LivePreviewWidget()
        self.card_preview.position_changed.connect(self._on_image_position_changed)
        self.card_preview.size_changed.connect(self._on_image_size_changed)
        card_preview_layout.addWidget(self.card_preview, 0, Qt.AlignHCenter)

        image_button_layout = QHBoxLayout()
        fill_button_image = QPushButton("채우기")
        fill_button_image.clicked.connect(self._fill_image_frame)
        center_button_image = QPushButton("가운데 정렬")
        center_button_image.clicked.connect(self._center_image_frame)
        image_button_layout.addWidget(fill_button_image)
        image_button_layout.addWidget(center_button_image)
        card_preview_layout.addLayout(image_button_layout)

        previews_layout.addWidget(card_preview_group)
        main_layout.addWidget(previews_widget, 1)

        # 초기 미리보기 업데이트
        self._update_qr_preview()
        self._update_card_preview()

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
        self.request_real_time_update()

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
        self.request_real_time_update()

    def _fill_image_frame(self):
        """업로드된 이미지를 카드 크기에 맞게 채웁니다."""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        card_width = 636 if is_portrait else 1012
        card_height = 1012 if is_portrait else 636

        self.qr_uploaded_input.set_values(x=0, y=0, width=card_width, height=card_height)
        self.request_real_time_update()

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
        self.request_real_time_update()

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

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.qr_preview.set_original_size(monitor_width, monitor_height)

        # 배경 이미지 설정 - screen_key를 사용하여 실제 파일 경로 찾기
        bg_path = FileHandler.resolve_background_path(QR_SCREEN_KEY)
        self.qr_preview.set_background(bg_path, QColor("#1a1a1a"))

        # QR 코드 영역 추가
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
            draggable=True
        )

        self.request_real_time_update()

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
            label="이미지",
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
