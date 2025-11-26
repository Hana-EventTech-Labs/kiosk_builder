from PySide6.QtWidgets import (QGroupBox, QFormLayout, QHBoxLayout, QVBoxLayout,
                              QLineEdit, QPushButton, QListWidget, QListWidgetItem, QWidget)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor
from .base_tab import BaseTab
from ui.components.inputs import NumberLineEdit
from ui.components.color_picker import ColorPickerButton
from ui.components.live_preview import LivePreviewWidget
from utils.file_handler import FileHandler

# 프레임 선택 화면 screen_key = "4"
FRAME_SCREEN_KEY = "4"

class FrameTab(BaseTab):
    def __init__(self, config):
        super().__init__(config)
        self.screen_preview = None
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

        # 배경화면 설정 그룹
        bg_group = QGroupBox("배경화면 설정")
        self.apply_left_aligned_group_style(bg_group)
        bg_layout = QHBoxLayout(bg_group)
        
        # 배경화면 파일 선택
        self.frame_bg_edit = QLineEdit(self.config.get("photo_frame", {}).get("background", ""))
        bg_layout.addWidget(self.frame_bg_edit, 1)
        
        # 배경화면 파일 선택 버튼
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(self._on_browse_background)
        bg_layout.addWidget(browse_button)

        # 배경화면 변경 시 미리보기 업데이트
        self.frame_bg_edit.textChanged.connect(self._update_screen_preview)

        content_layout.addWidget(bg_group)

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
        
        content_layout.addWidget(frame_add_group)

        # 프레임 설정 그룹
        frame_group = QGroupBox("프레임 설정")
        self.apply_left_aligned_group_style(frame_group)
        frame_layout = QFormLayout(frame_group)
        
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
        
        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config["photo_frame"].get("font", ""))
        font_layout.addWidget(font_edit, 1)
        self.frame_fields["font"] = font_edit
        
        # 폰트 파일 선택 버튼 추가
        font_browse_button = QPushButton("찾기...")
        font_browse_button.clicked.connect(lambda checked: FileHandler.browse_font_file(self, font_edit))
        font_layout.addWidget(font_browse_button)
        
        frame_layout.addRow("폰트:", font_layout)
        
        # 숫자 필드들
        for key, label in [("font_size", "글자 크기"), ("width", "너비"), ("height", "높이")]:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["photo_frame"].get(key, 32 if key == "font_size" else 800 if key == "width" else 600))
            # 너비/높이 변경 시 미리보기 업데이트
            if key in ["width", "height"]:
                line_edit.textChanged.connect(self._update_screen_preview)
            frame_layout.addRow(f"{label}:", line_edit)
            self.frame_fields[key] = line_edit
        
        # 색상 필드
        font_color_button = ColorPickerButton(self.config["photo_frame"].get("font_color", "green"))
        frame_layout.addRow("글자 색상:", font_color_button)
        self.frame_fields["font_color"] = font_color_button
            
        content_layout.addWidget(frame_group)
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

        self.screen_preview = LivePreviewWidget()
        self.screen_preview.position_changed.connect(self._on_frame_position_changed)
        self.screen_preview.size_changed.connect(self._on_frame_size_changed)
        screen_preview_layout.addWidget(self.screen_preview, 0, Qt.AlignHCenter)

        preview_layout.addWidget(screen_preview_group)
        preview_layout.addStretch()

        main_layout.addWidget(preview_widget, 1)

        # 기존 프레임 목록 로드
        self.load_frame_list()

        # 초기 미리보기 업데이트
        self._update_screen_preview()

    def _on_browse_background(self):
        """배경화면 파일 선택"""
        FileHandler.browse_background_file(self, self.frame_bg_edit, "4")
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
        bg_path = FileHandler.resolve_background_path(FRAME_SCREEN_KEY)
        self.screen_preview.set_background(bg_path, QColor("#1a1a1a"))

        # 프레임 영역 표시 (설정된 크기)
        try:
            frame_width = self.frame_fields["width"].value()
            frame_height = self.frame_fields["height"].value()
        except (AttributeError, KeyError):
            frame_width, frame_height = 800, 600

        # 프레임 중앙 위치 계산
        frame_x = (monitor_width - frame_width) // 2
        frame_y = (monitor_height - frame_height) // 2
        frame_rect = QRect(frame_x, frame_y, frame_width, frame_height)

        # 선택된 프레임 이미지가 있으면 표시
        selected_item = self.frame_list.currentItem()
        frame_image_name = selected_item.text() if selected_item else None
        # 프레임 파일 경로 resolve
        frame_image_path = FileHandler.resolve_frame_path(frame_image_name) if frame_image_name else None

        self.screen_preview.add_element(
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
            for key in ['width', 'height']:
                self.frame_fields[key].blockSignals(True)

            self.frame_fields['width'].setValue(width)
            self.frame_fields['height'].setValue(height)

            for key in ['width', 'height']:
                self.frame_fields[key].blockSignals(False)

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
        
        if "photo_frame" in config:
            for key, widget in self.frame_fields.items():
                if isinstance(widget, ColorPickerButton):
                    widget.update_color(config["photo_frame"].get(key, "green"))
                elif isinstance(widget, NumberLineEdit):
                    widget.setValue(config["photo_frame"].get(key, 32 if key == "font_size" else 800 if key == "width" else 600))
                else:  # QLineEdit (font)
                    widget.setText(config["photo_frame"].get(key, ""))

        # 미리보기 업데이트
        self._update_screen_preview() 