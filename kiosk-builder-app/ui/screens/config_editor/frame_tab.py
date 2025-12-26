from PySide6.QtWidgets import (QGroupBox, QFormLayout, QHBoxLayout, QVBoxLayout,
                              QLineEdit, QPushButton, QListWidget, QListWidgetItem, QWidget, QLabel, QTabWidget,
                              QDialog, QDialogButtonBox, QFrame, QRadioButton, QButtonGroup, QScrollArea, QGridLayout,
                              QComboBox)
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QColor, QPixmap
from .base_tab import BaseTab
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import LivePreviewWidget
from ui.components.zoomable_preview import ZoomablePreviewWidget, DEFAULT_PREVIEW_SIZE
from ui.components.language_preview_tabs import LanguagePreviewTabs
from ui.components.position_size_input import PositionSizeInput
from utils.file_handler import FileHandler, get_resources_base_path
import os
import glob

# 프레임 선택 화면 screen_key = "4"
FRAME_SCREEN_KEY = "4"

# 레이아웃 스타일 옵션
LAYOUT_STYLES = {
    "classic": "클래식 (좌우 분할)",
    "carousel": "캐러셀 (하단 슬라이더)",
    "fullscreen": "풀스크린 갤러리",
    "grid_overlay": "그리드 오버레이"
}


class FrameTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.sub_tabs = None
        # 각 탭의 미리보기 위젯
        self.screen_preview_widget = None
        self.print_preview_widget = None
        # 테두리 썸네일 그리드
        self.thumbnail_grid = None
        self.thumbnail_widgets = []
        # 언어별 배경화면 필드
        self.lang_bg_fields = {"ko": {}, "en": {}}
        # 언어별 미리보기 선택 (라디오 버튼용)
        self._current_lang_preview = None
        # 프레임 필드 (호환성 유지)
        self.frame_fields = {}
        self.init_ui()

    def init_ui(self):
        scroll_content_layout = self.create_tab_with_scroll()

        # ═══════════════════════════════════════════════════════════════
        # 서브 탭 위젯 (3개 탭: 화면 설정, 테두리 이미지, 인쇄 설정)
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

        # 탭 2: 테두리 이미지
        self._create_frame_image_tab()

        # 탭 3: 인쇄 설정
        self._create_print_settings_tab()

        scroll_content_layout.addWidget(self.sub_tabs)
        scroll_content_layout.addStretch()

        # 기존 프레임 목록 로드
        self.load_frame_list()

        # 라디오 버튼 초기 상태 설정
        self._update_preview_radio_visibility()

        # 초기 미리보기 업데이트
        self._update_screen_preview()
        self._update_thumbnail_grid()

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

        # 레이아웃 스타일 선택
        self._init_layout_style_settings(left_layout)

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

        desc = QLabel("프레임 선택 화면이 키오스크에서 어떻게 보이는지 미리봅니다.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold; padding: 4px;")
        preview_layout.addWidget(desc)

        # 단일 미리보기 위젯 + 확대/축소
        self.screen_preview_widget = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.screen_preview_widget.position_changed.connect(self._on_screen_element_position_changed)
        self._zoomable_screen_preview = ZoomablePreviewWidget(self.screen_preview_widget)
        preview_layout.addWidget(self._zoomable_screen_preview, 0, Qt.AlignCenter)

        right_layout.addWidget(preview_group)
        right_layout.addStretch()

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "화면 설정")

    # ═══════════════════════════════════════════════════════════════
    # 탭 2: 테두리 이미지
    # ═══════════════════════════════════════════════════════════════
    def _create_frame_image_tab(self):
        """테두리 이미지 탭 생성 - 좌측(관리) + 우측(썸네일 그리드)"""
        tab_widget = QWidget()
        tab_main_layout = QHBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(10, 10, 10, 10)
        tab_main_layout.setSpacing(20)

        # 좌측: 테두리 이미지 관리
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 테두리 이미지 관리 그룹
        frame_manage_group = QGroupBox("테두리 이미지 관리")
        frame_manage_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #9C27B0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #fdf8ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #7B1FA2;
                background-color: #fdf8ff;
            }
        """)
        frame_manage_layout = QVBoxLayout(frame_manage_group)

        # 설명 라벨
        frame_desc = QLabel("사용자가 선택할 수 있는 테두리 이미지를 추가하세요.\n사진 위에 합성되는 PNG 이미지 파일입니다.")
        frame_desc.setStyleSheet("""
            color: #7B1FA2;
            font-size: 11px;
            padding: 4px 8px;
            background-color: #F3E5F5;
            border-radius: 4px;
            margin-bottom: 8px;
            font-weight: normal;
        """)
        frame_desc.setWordWrap(True)
        frame_manage_layout.addWidget(frame_desc)

        # 파일 추가 레이아웃
        add_layout = QHBoxLayout()
        self.frame_file_edit = QLineEdit()
        self.frame_file_edit.setPlaceholderText("테두리 이미지 파일을 선택하세요...")
        add_layout.addWidget(self.frame_file_edit, 1)

        browse_btn = QPushButton("찾기...")
        browse_btn.clicked.connect(self.browse_frame_file)
        add_layout.addWidget(browse_btn)

        add_btn = QPushButton("추가")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        add_btn.clicked.connect(self.add_frame_to_list)
        add_layout.addWidget(add_btn)

        frame_manage_layout.addLayout(add_layout)

        # 테두리 목록
        self.frame_list = QListWidget()
        self.frame_list.setMaximumHeight(200)
        self.frame_list.currentItemChanged.connect(self._on_frame_selection_changed)
        self.frame_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #CE93D8;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #E1BEE7;
                color: #4A148C;
            }
        """)
        frame_manage_layout.addWidget(self.frame_list)

        # 삭제 버튼
        remove_btn = QPushButton("선택한 항목 삭제")
        remove_btn.clicked.connect(self.remove_frame_from_list)
        frame_manage_layout.addWidget(remove_btn)

        left_layout.addWidget(frame_manage_group)
        left_layout.addStretch()

        tab_main_layout.addWidget(left_widget, 1)

        # 우측: 등록된 테두리 미리보기 (썸네일 그리드)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("등록된 테두리 미리보기")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #9C27B0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #fdf8ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #7B1FA2;
                background-color: #fdf8ff;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)

        desc = QLabel("등록된 테두리 이미지들입니다. 클릭하면 확대 미리보기를 볼 수 있습니다.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #7B1FA2; font-size: 11px; padding: 4px; font-weight: normal;")
        preview_layout.addWidget(desc)

        # 스크롤 영역 + 그리드
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.thumbnail_container = QWidget()
        self.thumbnail_grid = QGridLayout(self.thumbnail_container)
        self.thumbnail_grid.setSpacing(10)
        self.thumbnail_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll_area.setWidget(self.thumbnail_container)
        preview_layout.addWidget(scroll_area)

        right_layout.addWidget(preview_group)

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "테두리 이미지")

    # ═══════════════════════════════════════════════════════════════
    # 탭 3: 인쇄 설정
    # ═══════════════════════════════════════════════════════════════
    def _create_print_settings_tab(self):
        """인쇄 설정 탭 생성 - 좌측(위치/크기 설정) + 우측(카드 미리보기)"""
        tab_widget = QWidget()
        tab_main_layout = QHBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(10, 10, 10, 10)
        tab_main_layout.setSpacing(20)

        # 좌측: 인쇄 위치/크기 설정
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # 프레임 이미지 인쇄 영역 설정 그룹
        print_group = QGroupBox("프레임 이미지 인쇄 영역")
        print_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #FF9800;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #fffaf5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #E65100;
                background-color: #fffaf5;
            }
        """)
        print_layout = QVBoxLayout(print_group)

        # 설명 라벨
        print_desc = QLabel("프레임이 적용된 이미지가 카드에 인쇄될 위치와 크기입니다.\n우측 미리보기에서 드래그/리사이즈 가능합니다.")
        print_desc.setStyleSheet("""
            color: #E65100;
            font-size: 11px;
            padding: 4px 8px;
            background-color: #FFF3E0;
            border-radius: 4px;
            margin-bottom: 8px;
            font-weight: normal;
        """)
        print_desc.setWordWrap(True)
        print_layout.addWidget(print_desc)

        # framed_photo 설정 초기화
        if "framed_photo" not in self.config:
            self.config["framed_photo"] = {
                "filename": "framed_photo.jpg",
                "x": 143,
                "y": 314,
                "width": 350,
                "height": 400
            }

        # 위치/크기 입력
        self.framed_photo_input = PositionSizeInput(show_position=True, show_size=True)
        self.framed_photo_input.set_values(
            x=self.config["framed_photo"].get("x", 143),
            y=self.config["framed_photo"].get("y", 314),
            width=self.config["framed_photo"].get("width", 350),
            height=self.config["framed_photo"].get("height", 400)
        )
        self.framed_photo_input.value_changed.connect(self._on_framed_photo_input_changed)
        print_layout.addWidget(self.framed_photo_input)

        # 빠른 설정 버튼들
        quick_btns_layout = QHBoxLayout()
        quick_btns_layout.setSpacing(8)

        fill_btn = QPushButton("전체 채우기")
        fill_btn.clicked.connect(self._fill_framed_photo)
        fill_btn.setStyleSheet("padding: 6px 12px;")
        quick_btns_layout.addWidget(fill_btn)

        center_btn = QPushButton("중앙 정렬")
        center_btn.clicked.connect(self._center_framed_photo)
        center_btn.setStyleSheet("padding: 6px 12px;")
        quick_btns_layout.addWidget(center_btn)

        print_layout.addLayout(quick_btns_layout)

        left_layout.addWidget(print_group)
        left_layout.addStretch()

        tab_main_layout.addWidget(left_widget, 1)

        # 우측: 카드 인쇄 미리보기
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_group = QGroupBox("카드 인쇄 미리보기 (58×90mm)")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #FF9800;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #fffaf5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #E65100;
                background-color: #fffaf5;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("프레임 이미지를 드래그하여 인쇄 위치를 조정하세요.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #E65100; font-size: 11px; font-weight: normal; padding: 4px;")
        preview_layout.addWidget(desc)

        # 카드 미리보기 위젯
        self.print_preview_widget = LivePreviewWidget(preview_size=DEFAULT_PREVIEW_SIZE)
        self.print_preview_widget.position_changed.connect(self._on_framed_photo_position_changed)
        self.print_preview_widget.size_changed.connect(self._on_framed_photo_size_changed)
        self._zoomable_print_preview = ZoomablePreviewWidget(self.print_preview_widget)
        preview_layout.addWidget(self._zoomable_print_preview, 0, Qt.AlignCenter)

        right_layout.addWidget(preview_group)

        tab_main_layout.addWidget(right_widget, 1)

        self.sub_tabs.addTab(tab_widget, "인쇄 설정")

    # ═══════════════════════════════════════════════════════════════
    # 레이아웃 스타일 설정
    # ═══════════════════════════════════════════════════════════════
    def _init_layout_style_settings(self, parent_layout):
        """레이아웃 스타일 선택 그룹"""
        layout_group = QGroupBox("화면 레이아웃 스타일")
        layout_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #f8fbff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #2980b9;
                background-color: #f8fbff;
            }
        """)
        layout_form = QVBoxLayout(layout_group)
        layout_form.setSpacing(10)

        # 설명
        desc_label = QLabel("키오스크에서 테두리 선택 화면의 레이아웃 스타일을 선택합니다.")
        desc_label.setStyleSheet("""
            color: #2980b9;
            font-size: 11px;
            padding: 4px 8px;
            background-color: #EBF5FB;
            border-radius: 4px;
            font-weight: normal;
        """)
        desc_label.setWordWrap(True)
        layout_form.addWidget(desc_label)

        # 드롭다운
        style_row = QHBoxLayout()
        style_label = QLabel("스타일:")
        style_label.setStyleSheet("font-weight: bold; color: #555;")
        style_label.setFixedWidth(60)
        style_row.addWidget(style_label)

        self.layout_style_combo = QComboBox()
        self.layout_style_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                padding-right: 30px;
                border: 1px solid #3498db;
                border-radius: 4px;
                background-color: white;
                min-width: 200px;
            }
            QComboBox:hover {
                border-color: #2980b9;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #3498db;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background-color: #f0f8ff;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #3498db;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #2980b9;
            }
        """)

        # 옵션 추가
        for key, display_name in LAYOUT_STYLES.items():
            self.layout_style_combo.addItem(display_name, key)

        # 현재 설정값 로드
        current_style = self.config.get("photo_frame", {}).get("layout_style", "classic")
        index = self.layout_style_combo.findData(current_style)
        if index >= 0:
            self.layout_style_combo.setCurrentIndex(index)

        self.layout_style_combo.currentIndexChanged.connect(self._on_layout_style_changed)
        style_row.addWidget(self.layout_style_combo, 1)
        layout_form.addLayout(style_row)

        # 스타일별 설명
        self.style_description_label = QLabel()
        self.style_description_label.setStyleSheet("""
            color: #666;
            font-size: 11px;
            padding: 8px;
            background-color: #fafafa;
            border: 1px solid #eee;
            border-radius: 4px;
            font-weight: normal;
        """)
        self.style_description_label.setWordWrap(True)
        self._update_style_description()
        layout_form.addWidget(self.style_description_label)

        parent_layout.addWidget(layout_group)

    def _on_layout_style_changed(self):
        """레이아웃 스타일 변경 시"""
        self._update_style_description()
        self._update_screen_preview()

    def _on_screen_element_position_changed(self, element_id, x, y):
        """화면 미리보기에서 요소 드래그 시 - 위치 저장 및 미리보기 갱신"""
        layout_style = self.layout_style_combo.currentData() if hasattr(self, 'layout_style_combo') else "classic"

        # photo_frame 설정 초기화
        if "photo_frame" not in self.config:
            self.config["photo_frame"] = {}
        if "layout_positions" not in self.config["photo_frame"]:
            self.config["photo_frame"]["layout_positions"] = {}
        if layout_style not in self.config["photo_frame"]["layout_positions"]:
            self.config["photo_frame"]["layout_positions"][layout_style] = {}

        pos_config = self.config["photo_frame"]["layout_positions"][layout_style]

        # 요소별 위치 저장
        if element_id == "thumb_grid":
            pos_config["selection_x"] = x
            pos_config["selection_y"] = y
        elif element_id == "preview_area" or element_id == "main_preview":
            pos_config["preview_x"] = x
            pos_config["preview_y"] = y
        elif element_id == "fullscreen_preview":
            pos_config["preview_x"] = x
            pos_config["preview_y"] = y
        elif element_id == "top_preview":
            pos_config["preview_x"] = x
            pos_config["preview_y"] = y
        elif element_id == "thumb_slider":
            pos_config["slider_y"] = y

        # 미리보기 다시 그리기 (썸네일 위치 동기화)
        self._update_screen_preview()
        self.request_real_time_update()

    def _update_style_description(self):
        """선택된 스타일에 대한 설명 업데이트"""
        style_key = self.layout_style_combo.currentData()
        descriptions = {
            "classic": "📐 기본 레이아웃입니다. 좌측에 테두리 썸네일 그리드, 우측에 합성 미리보기가 표시됩니다.",
            "carousel": "🎠 중앙에 큰 미리보기, 하단에 테두리 썸네일 슬라이더가 표시됩니다. 좌우 버튼 또는 스와이프로 선택합니다.",
            "fullscreen": "🖼️ 화면 전체에 합성 미리보기가 표시됩니다. 스와이프로 테두리를 전환하며, 하단에 페이지 인디케이터가 표시됩니다.",
            "grid_overlay": "📱 상단에 큰 미리보기, 하단에 반투명 그리드로 테두리 썸네일이 표시됩니다."
        }
        self.style_description_label.setText(descriptions.get(style_key, ""))

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
        ko_label = QLabel("한국어:")
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
        en_label = QLabel("English:")
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

        # 구분선
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
            "<b>배경화면 설정 안내</b><br><br>"
            "• <b>배경화면</b>: 기본 배경화면입니다. 언어별 배경화면이 없을 경우 사용됩니다.<br><br>"
            "• <b>한국어</b>: 사용자가 한국어를 선택했을 때 표시되는 배경화면입니다.<br><br>"
            "• <b>English</b>: 사용자가 영어를 선택했을 때 표시되는 배경화면입니다.<br><br>"
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

    # ==================== 미리보기 업데이트 ====================
    def _update_screen_preview(self):
        """화면 미리보기 업데이트 - 레이아웃 스타일에 따라 다르게 표시"""
        if not self.screen_preview_widget:
            return

        self.screen_preview_widget.clear_elements()

        # 모니터 크기
        try:
            monitor_width = self.config["screen_size"]["width"]
            monitor_height = self.config["screen_size"]["height"]
        except KeyError:
            monitor_width, monitor_height = 1080, 1920

        self.screen_preview_widget.set_original_size(monitor_width, monitor_height)

        # 배경 이미지 (언어 활성화 상태에 따라 처리)
        lang_enabled = self.config.get("language", {}).get("enabled", False)
        if lang_enabled:
            lang = getattr(self, '_current_lang_preview', "ko")
            if lang is None:
                lang = "ko"
            bg_path = FileHandler.resolve_background_path(FRAME_SCREEN_KEY, lang=lang)
        else:
            bg_path = FileHandler.resolve_background_path(FRAME_SCREEN_KEY, lang=None)

        self.screen_preview_widget.set_background(bg_path, QColor("#ffffff"))
        self.screen_preview_widget.set_card_border(True, QColor("#333333"), 2)

        # 레이아웃 스타일에 따라 미리보기 구성
        layout_style = self.layout_style_combo.currentData() if hasattr(self, 'layout_style_combo') else "classic"
        frame_files = self.config.get("photo_frame", {}).get("frame_files", [])
        preview_width = self.config.get("photo_frame", {}).get("width", 800)
        preview_height = self.config.get("photo_frame", {}).get("height", 600)

        if not frame_files:
            # 테두리가 없을 때 안내 메시지
            self.screen_preview_widget.add_element(
                "no_frames",
                QRect(monitor_width // 4, monitor_height // 2 - 50, monitor_width // 2, 100),
                color=QColor(200, 200, 200, 100),
                label="테두리 이미지를\n추가하세요",
                draggable=False
            )
        elif layout_style == "carousel":
            self._draw_carousel_preview(monitor_width, monitor_height, frame_files, preview_width, preview_height)
        elif layout_style == "fullscreen":
            self._draw_fullscreen_preview(monitor_width, monitor_height, frame_files, preview_width, preview_height)
        elif layout_style == "grid_overlay":
            self._draw_grid_overlay_preview(monitor_width, monitor_height, frame_files, preview_width, preview_height)
        else:  # classic
            self._draw_classic_preview(monitor_width, monitor_height, frame_files, preview_width, preview_height)

        self.request_real_time_update()

    def _draw_classic_preview(self, monitor_width, monitor_height, frame_files, preview_width, preview_height):
        """클래식 레이아웃 미리보기 - 좌측 그리드 + 우측 미리보기"""
        # config에서 저장된 위치 가져오기 (없으면 기본값)
        layout_positions = self.config.get("photo_frame", {}).get("layout_positions", {})
        classic_pos = layout_positions.get("classic", {})

        selection_x = classic_pos.get("selection_x", 50)
        selection_y = classic_pos.get("selection_y", 200)
        preview_x = classic_pos.get("preview_x", 440)
        preview_y = classic_pos.get("preview_y", (monitor_height - preview_height) // 2)

        thumb_size = 150
        thumb_spacing = 20
        cols = 2

        # 썸네일 그리드 영역 (드래그 가능한 컨테이너)
        grid_width = cols * thumb_size + (cols - 1) * thumb_spacing
        grid_height = 3 * thumb_size + 2 * thumb_spacing
        self.screen_preview_widget.add_element(
            "thumb_grid",
            QRect(selection_x, selection_y, grid_width, grid_height),
            color=QColor(100, 150, 255, 40),
            label="썸네일 그리드\n(드래그하여 이동)",
            draggable=True
        )

        # 각 테두리 이미지를 썸네일로 표시 (최대 6개) - 그리드 안에 상대 위치
        for idx, frame_file in enumerate(frame_files[:6]):
            row = idx // cols
            col = idx % cols
            thumb_x = selection_x + col * (thumb_size + thumb_spacing)
            thumb_y = selection_y + row * (thumb_size + thumb_spacing)
            frame_path = FileHandler.resolve_frame_path(frame_file)

            self.screen_preview_widget.add_element(
                f"frame_thumb_{idx}",
                QRect(thumb_x, thumb_y, thumb_size, thumb_size),
                color=QColor(255, 255, 255, 200),
                image_path=frame_path if frame_path and os.path.exists(frame_path) else None,
                label=f"{idx+1}" if not (frame_path and os.path.exists(frame_path)) else "",
                draggable=False
            )

        if len(frame_files) > 6:
            self.screen_preview_widget.add_element(
                "more_frames",
                QRect(selection_x, selection_y + 3 * (thumb_size + thumb_spacing), thumb_size * 2 + thumb_spacing, 40),
                color=QColor(100, 100, 100, 150),
                label=f"+{len(frame_files) - 6}개 더",
                draggable=False
            )

        # 미리보기 영역 (드래그 가능)
        self.screen_preview_widget.add_element(
            "preview_area",
            QRect(preview_x, preview_y, preview_width, preview_height),
            color=QColor(255, 152, 0, 60),
            label=f"합성 미리보기\n(드래그하여 이동)",
            draggable=True
        )

    def _draw_carousel_preview(self, monitor_width, monitor_height, frame_files, preview_width, preview_height):
        """캐러셀 레이아웃 미리보기 - 중앙 큰 미리보기 + 하단 슬라이더"""
        # config에서 저장된 위치 가져오기
        layout_positions = self.config.get("photo_frame", {}).get("layout_positions", {})
        carousel_pos = layout_positions.get("carousel", {})

        center_x = carousel_pos.get("preview_x", (monitor_width - preview_width) // 2)
        center_y = carousel_pos.get("preview_y", monitor_height // 4)

        # 중앙 큰 미리보기 (드래그 가능)
        self.screen_preview_widget.add_element(
            "main_preview",
            QRect(center_x, center_y, preview_width, preview_height),
            color=QColor(255, 152, 0, 60),
            label=f"합성 미리보기\n(드래그하여 이동)",
            draggable=True
        )

        # 좌우 화살표
        arrow_size = 80
        self.screen_preview_widget.add_element(
            "left_arrow",
            QRect(center_x - arrow_size - 30, center_y + preview_height // 2 - arrow_size // 2, arrow_size, arrow_size),
            color=QColor(100, 100, 100, 150),
            label="◀",
            draggable=False
        )
        self.screen_preview_widget.add_element(
            "right_arrow",
            QRect(center_x + preview_width + 30, center_y + preview_height // 2 - arrow_size // 2, arrow_size, arrow_size),
            color=QColor(100, 100, 100, 150),
            label="▶",
            draggable=False
        )

        # 하단 썸네일 슬라이더
        thumb_size = 100
        thumb_spacing = 15
        slider_y = carousel_pos.get("slider_y", center_y + preview_height + 80)
        total_width = len(frame_files[:5]) * (thumb_size + thumb_spacing) - thumb_spacing
        start_x = (monitor_width - total_width) // 2

        # 슬라이더 영역 컨테이너 (드래그 가능)
        self.screen_preview_widget.add_element(
            "thumb_slider",
            QRect(start_x - 10, slider_y - 10, total_width + 20, thumb_size + 20),
            color=QColor(100, 150, 255, 40),
            label="",
            draggable=True
        )

        for idx, frame_file in enumerate(frame_files[:5]):
            thumb_x = start_x + idx * (thumb_size + thumb_spacing)
            frame_path = FileHandler.resolve_frame_path(frame_file)
            border_color = QColor(0, 200, 150) if idx == 0 else QColor(200, 200, 200)
            self.screen_preview_widget.add_element(
                f"thumb_{idx}",
                QRect(thumb_x, slider_y, thumb_size, thumb_size),
                color=border_color,
                image_path=frame_path if frame_path and os.path.exists(frame_path) else None,
                label="" if (frame_path and os.path.exists(frame_path)) else f"{idx+1}",
                draggable=False
            )

        # 버튼 영역
        btn_y = slider_y + thumb_size + 50
        self.screen_preview_widget.add_element(
            "buttons",
            QRect(monitor_width // 4, btn_y, monitor_width // 2, 60),
            color=QColor(100, 100, 100, 80),
            label="[다시 촬영]    [선택 완료]",
            draggable=False
        )

    def _draw_fullscreen_preview(self, monitor_width, monitor_height, frame_files, preview_width, preview_height):
        """풀스크린 레이아웃 미리보기 - 전체 화면 미리보기 + 인디케이터"""
        # config에서 저장된 위치 가져오기
        layout_positions = self.config.get("photo_frame", {}).get("layout_positions", {})
        fullscreen_pos = layout_positions.get("fullscreen", {})

        # 전체 화면 미리보기 (여백 포함)
        margin = 50
        full_width = monitor_width - margin * 2
        full_height = int(full_width * preview_height / preview_width)
        if full_height > monitor_height - 300:
            full_height = monitor_height - 300
            full_width = int(full_height * preview_width / preview_height)

        center_x = fullscreen_pos.get("preview_x", (monitor_width - full_width) // 2)
        center_y = fullscreen_pos.get("preview_y", 100)

        self.screen_preview_widget.add_element(
            "fullscreen_preview",
            QRect(center_x, center_y, full_width, full_height),
            color=QColor(255, 152, 0, 60),
            label=f"합성 미리보기\n(드래그하여 이동)",
            draggable=True
        )

        # 페이지 인디케이터
        indicator_y = center_y + full_height + 40
        dot_size = 20
        dot_spacing = 15
        num_dots = min(len(frame_files), 7)
        total_dots_width = num_dots * dot_size + (num_dots - 1) * dot_spacing
        start_x = (monitor_width - total_dots_width) // 2

        for idx in range(num_dots):
            dot_x = start_x + idx * (dot_size + dot_spacing)
            dot_color = QColor(0, 200, 150) if idx == 0 else QColor(180, 180, 180)
            self.screen_preview_widget.add_element(
                f"dot_{idx}",
                QRect(dot_x, indicator_y, dot_size, dot_size),
                color=dot_color,
                label="",
                draggable=False
            )

        # 버튼 영역
        btn_y = indicator_y + 80
        self.screen_preview_widget.add_element(
            "buttons",
            QRect(monitor_width // 4, btn_y, monitor_width // 2, 60),
            color=QColor(100, 100, 100, 80),
            label="[다시 촬영]    [선택 완료]",
            draggable=False
        )

    def _draw_grid_overlay_preview(self, monitor_width, monitor_height, frame_files, preview_width, preview_height):
        """그리드 오버레이 레이아웃 미리보기 - 상단 미리보기 + 하단 그리드"""
        # config에서 저장된 위치 가져오기
        layout_positions = self.config.get("photo_frame", {}).get("layout_positions", {})
        grid_overlay_pos = layout_positions.get("grid_overlay", {})

        # 상단 미리보기 (큰 영역)
        margin = 30
        top_height = int(monitor_height * 0.55)
        scaled_width = int(top_height * preview_width / preview_height)
        if scaled_width > monitor_width - margin * 2:
            scaled_width = monitor_width - margin * 2
            top_height = int(scaled_width * preview_height / preview_width)

        center_x = grid_overlay_pos.get("preview_x", (monitor_width - scaled_width) // 2)
        preview_y = grid_overlay_pos.get("preview_y", margin)

        self.screen_preview_widget.add_element(
            "top_preview",
            QRect(center_x, preview_y, scaled_width, top_height),
            color=QColor(255, 152, 0, 60),
            label=f"합성 미리보기\n(드래그하여 이동)",
            draggable=True
        )

        # 하단 반투명 그리드 영역
        grid_y = preview_y + top_height + 20
        grid_height = monitor_height - grid_y - 100
        self.screen_preview_widget.add_element(
            "grid_overlay_bg",
            QRect(0, grid_y, monitor_width, grid_height),
            color=QColor(0, 0, 0, 120),
            label="",
            draggable=False
        )

        # 그리드 내 썸네일
        thumb_size = 120
        thumb_spacing = 15
        cols = 5
        total_width = cols * thumb_size + (cols - 1) * thumb_spacing
        start_x = (monitor_width - total_width) // 2
        thumb_y = grid_y + 30

        for idx, frame_file in enumerate(frame_files[:cols]):
            thumb_x = start_x + idx * (thumb_size + thumb_spacing)
            frame_path = FileHandler.resolve_frame_path(frame_file)
            self.screen_preview_widget.add_element(
                f"grid_thumb_{idx}",
                QRect(thumb_x, thumb_y, thumb_size, thumb_size),
                color=QColor(255, 255, 255, 200),
                image_path=frame_path if frame_path and os.path.exists(frame_path) else None,
                label="" if (frame_path and os.path.exists(frame_path)) else f"{idx+1}",
                draggable=False
            )

        # 버튼 영역
        btn_y = thumb_y + thumb_size + 30
        self.screen_preview_widget.add_element(
            "buttons",
            QRect(monitor_width // 4, btn_y, monitor_width // 2, 50),
            color=QColor(100, 100, 100, 80),
            label="[선택 완료]",
            draggable=False
        )

    def _update_print_preview(self):
        """카드 인쇄 미리보기 업데이트"""
        if not self.print_preview_widget:
            return

        self.print_preview_widget.clear_elements()

        # 카드 크기 (portrait/landscape)
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        cw, ch = (636, 1012) if is_portrait else (1012, 636)

        self.print_preview_widget.set_original_size(cw, ch)

        # 카드 배경 이미지
        base_card_path = self.config.get("card", {}).get("background", "")
        if base_card_path:
            self.print_preview_widget.set_background(base_card_path, QColor("white"))
        else:
            self.print_preview_widget.set_background_color(QColor("white"))

        # 카드 테두리 표시
        self.print_preview_widget.set_card_border(True, QColor("#333333"), 3)

        # framed_photo 영역 가져오기
        x = self.config.get("framed_photo", {}).get("x", 143)
        y = self.config.get("framed_photo", {}).get("y", 314)
        w = self.config.get("framed_photo", {}).get("width", 350)
        h = self.config.get("framed_photo", {}).get("height", 400)

        # 선택된 프레임 이미지 확인
        selected_item = self.frame_list.currentItem() if hasattr(self, 'frame_list') else None
        frame_image_path = None
        if selected_item:
            frame_image_name = selected_item.text()
            frame_image_path = FileHandler.resolve_frame_path(frame_image_name)
            if not (frame_image_path and os.path.exists(frame_image_path)):
                frame_image_path = None

        # 프레임 이미지 영역 추가 (드래그/리사이즈 가능)
        self.print_preview_widget.add_element(
            "framed_photo",
            QRect(x, y, w, h),
            color=QColor("#FF9800") if not frame_image_path else QColor("transparent"),
            image_path=frame_image_path,
            label="프레임" if not frame_image_path else "",
            draggable=True
        )

        self.request_real_time_update()

    # ═══════════════════════════════════════════════════════════════
    # 프레임 인쇄 위치/크기 핸들러
    # ═══════════════════════════════════════════════════════════════
    def _on_framed_photo_input_changed(self):
        """좌측 입력 필드 변경 시"""
        x, y, w, h = self.framed_photo_input.get_values()
        if "framed_photo" not in self.config:
            self.config["framed_photo"] = {}
        self.config["framed_photo"]["x"] = x
        self.config["framed_photo"]["y"] = y
        self.config["framed_photo"]["width"] = w
        self.config["framed_photo"]["height"] = h
        self._update_print_preview()

    def _on_framed_photo_position_changed(self, element_id, x, y):
        """미리보기에서 드래그 시"""
        if element_id == "framed_photo":
            if "framed_photo" not in self.config:
                self.config["framed_photo"] = {}
            self.config["framed_photo"]["x"] = x
            self.config["framed_photo"]["y"] = y
            # 좌측 입력 필드 업데이트
            if hasattr(self, 'framed_photo_input'):
                self.framed_photo_input.set_x(x)
                self.framed_photo_input.set_y(y)
            self.request_real_time_update()

    def _on_framed_photo_size_changed(self, element_id, w, h):
        """미리보기에서 리사이즈 시"""
        if element_id == "framed_photo":
            if "framed_photo" not in self.config:
                self.config["framed_photo"] = {}
            self.config["framed_photo"]["width"] = w
            self.config["framed_photo"]["height"] = h
            # 좌측 입력 필드 업데이트
            if hasattr(self, 'framed_photo_input'):
                self.framed_photo_input.set_width(w)
                self.framed_photo_input.set_height(h)
            self.request_real_time_update()

    def _fill_framed_photo(self):
        """전체 채우기"""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        cw, ch = (636, 1012) if is_portrait else (1012, 636)
        self.framed_photo_input.set_values(0, 0, cw, ch)
        self._on_framed_photo_input_changed()

    def _center_framed_photo(self):
        """중앙 정렬"""
        is_portrait = self.config.get("card", {}).get("orientation", "portrait") == "portrait"
        cw, ch = (636, 1012) if is_portrait else (1012, 636)
        x, y, w, h = self.framed_photo_input.get_values()
        self.framed_photo_input.set_x((cw - w) // 2)
        self.framed_photo_input.set_y((ch - h) // 2)
        self._on_framed_photo_input_changed()

    def _update_thumbnail_grid(self):
        """테두리 썸네일 그리드 업데이트"""
        if not self.thumbnail_grid:
            return

        # 기존 썸네일 제거
        for widget in self.thumbnail_widgets:
            widget.deleteLater()
        self.thumbnail_widgets.clear()

        # 테두리 파일 목록 가져오기
        frame_files = self.config.get("photo_frame", {}).get("frame_files", [])

        if not frame_files:
            # 등록된 테두리 없음 메시지
            empty_label = QLabel("등록된 테두리 이미지가 없습니다.\n좌측에서 테두리 이미지를 추가하세요.")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999; font-size: 12px; padding: 20px;")
            self.thumbnail_grid.addWidget(empty_label, 0, 0)
            self.thumbnail_widgets.append(empty_label)
            return

        # 썸네일 생성 (4열)
        cols = 4
        for i, frame_file in enumerate(frame_files):
            row = i // cols
            col = i % cols

            # 썸네일 위젯
            thumb_widget = self._create_thumbnail_widget(frame_file, i)
            self.thumbnail_grid.addWidget(thumb_widget, row, col)
            self.thumbnail_widgets.append(thumb_widget)

    def _create_thumbnail_widget(self, frame_file, index):
        """썸네일 위젯 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # 썸네일 이미지 버튼
        thumb_btn = QPushButton()
        thumb_btn.setFixedSize(100, 100)
        thumb_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #CE93D8;
                border-radius: 8px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #9C27B0;
                background-color: #F3E5F5;
            }
        """)

        # 이미지 로드
        frame_path = FileHandler.resolve_frame_path(frame_file)
        if frame_path and os.path.exists(frame_path):
            pixmap = QPixmap(frame_path)
            scaled = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb_btn.setIcon(scaled)
            thumb_btn.setIconSize(QSize(90, 90))

        thumb_btn.clicked.connect(lambda checked, f=frame_file: self._show_frame_preview_dialog(f))
        layout.addWidget(thumb_btn, 0, Qt.AlignCenter)

        # 파일명 라벨
        name_label = QLabel(frame_file)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 10px; color: #666;")
        name_label.setMaximumWidth(100)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        return widget

    def _show_frame_preview_dialog(self, frame_file):
        """테두리 이미지 확대 미리보기 다이얼로그"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"테두리 미리보기 - {frame_file}")
        dialog.setMinimumSize(500, 500)
        layout = QVBoxLayout(dialog)

        # 이미지 표시
        frame_path = FileHandler.resolve_frame_path(frame_file)
        if frame_path and os.path.exists(frame_path):
            pixmap = QPixmap(frame_path)
            label = QLabel()
            scaled = pixmap.scaled(450, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

            # 이미지 정보
            info_label = QLabel(f"크기: {pixmap.width()} x {pixmap.height()} px")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("color: #666; font-size: 11px;")
            layout.addWidget(info_label)
        else:
            error_label = QLabel("이미지를 불러올 수 없습니다.")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec()

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

        self.radio_default.show()
        self.radio_ko.show()
        self.radio_en.show()

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

    def _on_frame_selection_changed(self, current, previous):
        """테두리 목록 선택 변경 시 인쇄 미리보기 업데이트"""
        self._update_print_preview()

    # ==================== 테두리 파일 관리 ====================
    def browse_frame_file(self):
        """테두리 파일 선택 - 선택 즉시 목록에 추가"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "테두리 이미지 선택",
            "",
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp);;모든 파일 (*.*)"
        )

        if file_path:
            # 파일명만 추출
            frame_file = os.path.basename(file_path)

            # 중복 확인
            for i in range(self.frame_list.count()):
                if self.frame_list.item(i).text() == frame_file:
                    QMessageBox.warning(self, "경고", "이미 추가된 테두리입니다.")
                    return

            # resources/frames 폴더로 복사
            FileHandler.copy_frame_file(file_path)

            # 목록에 즉시 추가
            self.frame_list.addItem(frame_file)
            self.frame_file_edit.setText(frame_file)

            # config 업데이트
            self.update_frame_config()

            # 모든 미리보기 업데이트
            self._update_thumbnail_grid()
            self._update_screen_preview()
            self._update_print_preview()

    def add_frame_to_list(self):
        """테두리를 목록에 추가"""
        frame_file = self.frame_file_edit.text().strip()
        if not frame_file:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "경고", "테두리 이미지 파일을 선택해주세요.")
            return

        # 중복 확인
        for i in range(self.frame_list.count()):
            if self.frame_list.item(i).text() == frame_file:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "경고", "이미 추가된 테두리입니다.")
                return

        # 목록에 추가
        self.frame_list.addItem(frame_file)
        self.frame_file_edit.clear()

        # config 업데이트
        self.update_frame_config()

        # 모든 미리보기 업데이트
        self._update_thumbnail_grid()
        self._update_screen_preview()

    def remove_frame_from_list(self):
        """선택한 테두리를 목록에서 삭제"""
        current_item = self.frame_list.currentItem()
        if current_item:
            row = self.frame_list.row(current_item)
            self.frame_list.takeItem(row)

            # config 업데이트
            self.update_frame_config()

            # 모든 미리보기 업데이트
            self._update_thumbnail_grid()
            self._update_screen_preview()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "경고", "삭제할 테두리를 선택해주세요.")

    def update_frame_config(self):
        """테두리 목록을 config에 반영"""
        frame_files = []
        for i in range(self.frame_list.count()):
            frame_files.append(self.frame_list.item(i).text())

        if "photo_frame" not in self.config:
            self.config["photo_frame"] = {}

        self.config["photo_frame"]["frame_files"] = frame_files

    def load_frame_list(self):
        """config에서 테두리 목록 로드 + 폴더 자동 스캔"""
        frame_files = self.config.get("photo_frame", {}).get("frame_files", [])
        self.frame_list.clear()

        # config에 등록된 파일 추가
        for frame_file in frame_files:
            self.frame_list.addItem(frame_file)

        # frames 폴더 스캔하여 미등록 파일 자동 추가
        self._scan_frames_folder(frame_files)

    def _scan_frames_folder(self, existing_files):
        """frames 폴더를 스캔하여 미등록 파일 자동 추가"""
        # 기존 파일명 목록 (경로 제외한 파일명만)
        existing_names = set()
        for f in existing_files:
            existing_names.add(os.path.basename(f))

        # frames 폴더 스캔
        frames_folder = os.path.join(get_resources_base_path(), "resources", "frames")
        if not os.path.exists(frames_folder):
            return

        # PNG, JPG 파일 스캔
        for ext in ["*.png", "*.jpg", "*.jpeg"]:
            pattern = os.path.join(frames_folder, ext)
            for filepath in glob.glob(pattern):
                filename = os.path.basename(filepath)
                # 이미 등록된 파일이 아니면 추가
                if filename not in existing_names:
                    self.frame_list.addItem(filename)
                    existing_names.add(filename)

        # config 업데이트 (스캔된 파일들도 저장)
        self.update_frame_config()

    # ==================== config 연동 ====================
    def update_config(self, config):
        """UI 값을 config에 반영"""
        if "photo_frame" not in config:
            config["photo_frame"] = {}

        # 레이아웃 스타일 저장
        config["photo_frame"]["layout_style"] = self.layout_style_combo.currentData()

        # 배경화면 저장
        config["photo_frame"]["background"] = self.frame_bg_edit.text()

        # 테두리 목록 저장
        frame_files = []
        for i in range(self.frame_list.count()):
            frame_files.append(self.frame_list.item(i).text())
        config["photo_frame"]["frame_files"] = frame_files

        # framed_photo 인쇄 위치/크기 저장
        if "framed_photo" not in config:
            config["framed_photo"] = {"filename": "framed_photo.jpg"}
        x, y, w, h = self.framed_photo_input.get_values()
        config["framed_photo"]["x"] = x
        config["framed_photo"]["y"] = y
        config["framed_photo"]["width"] = w
        config["framed_photo"]["height"] = h

    def update_ui(self, config):
        """설정에 따라 UI 업데이트"""
        self.config = config

        # 레이아웃 스타일 업데이트
        current_style = config.get("photo_frame", {}).get("layout_style", "classic")
        index = self.layout_style_combo.findData(current_style)
        if index >= 0:
            self.layout_style_combo.setCurrentIndex(index)
        self._update_style_description()

        # 배경화면 업데이트
        self.frame_bg_edit.setText(config.get("photo_frame", {}).get("background", ""))

        # 테두리 목록 업데이트
        self.load_frame_list()

        # framed_photo 인쇄 위치/크기 업데이트
        framed_photo = config.get("framed_photo", {})
        self.framed_photo_input.set_values(
            x=framed_photo.get("x", 143),
            y=framed_photo.get("y", 314),
            width=framed_photo.get("width", 350),
            height=framed_photo.get("height", 400)
        )

        # 언어 활성화 상태에 따라 라디오 버튼 업데이트
        self._update_preview_radio_visibility()

        # 미리보기 업데이트
        self._update_screen_preview()
        self._update_thumbnail_grid()
        self._update_print_preview()
