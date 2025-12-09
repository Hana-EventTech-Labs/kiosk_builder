# kiosk-builder-app/ui/screens/config_editor/main_window.py 수정

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon
import copy
import os
import sys

# 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from utils.config_manager import ConfigManager
from utils.auth_manager import AuthManager
# from utils.auto_updater import AutoUpdater  # 이 줄 삭제
from ui.styles.colors import COLORS

from .components.menu_manager import MenuManager
from .components.tab_manager import TabManager
from .components.button_manager import ButtonManager
from .components.style_manager import StyleManager
from .components.card_preview_dialog import FloatingCardPreviewDialog
from .handlers.config_handler_ui import ConfigHandlerUI
from .handlers.distribution_handler import DistributionHandler

# 버전 정보 (version.py 대신 직접 정의)
APP_VERSION = "1.0.0"

def get_version():
    return APP_VERSION

def get_full_version():
    return f"{APP_VERSION}"
    
class ConfigEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_version = get_version()

        # 창 위치/크기 설정 저장용
        self.settings = QSettings("HanaEventTech", "SKProgram")

        # 핵심 매니저들 초기화
        self.config_manager = ConfigManager.get_instance()
        self.auth_manager = AuthManager()
        self.config = self.config_manager.get_config()

        # 플로팅 카드 미리보기 다이얼로그
        self.card_preview_dialog = None

        # GitHub 설정 (필요하면 나중에 제거)
        # self.github_release_base_url = "https://github.com/Hana-EventTech-Labs/kiosk_builder/releases/download/v1.0.0"

        # UI 매니저들 초기화
        self.style_manager = StyleManager()
        self.menu_manager = MenuManager(self)
        self.tab_manager = TabManager(self)
        self.button_manager = ButtonManager(self)

        # 핸들러들 초기화
        self.config_handler_ui = ConfigHandlerUI(self)
        self.distribution_handler = DistributionHandler(self)

        # UI 초기화
        self.init_ui()
        # self.init_auto_updater()  # 이 줄 삭제
        self.config_handler_ui.update_save_button_state()

        # 저장된 창 위치/크기 복원
        self._restore_window_geometry()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(f"S.K Program - 설정 편집기 v{self.current_version}")
        self.setMinimumSize(1300, 950)
        
        # 스타일 적용
        self.style_manager.apply_styles(self)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 헤더 추가
        self.add_header(main_layout)
        
        # 탭 위젯 추가
        self.tab_manager.create_tabs()
        main_layout.addWidget(self.tab_manager.tab_widget)
        
        # 버튼 추가
        self.button_manager.create_buttons(main_layout)
        
        # TabManager의 config_changed 시그널 연결
        self.tab_manager.config_changed.connect(self.on_config_changed_globally)

        # 메뉴바 생성
        self.menu_manager.create_menu_bar()
        
        # 상태 바 설정
        self.style_manager.setup_status_bar(self)

    def add_header(self, layout):
        """헤더 추가"""
        from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton

        header_layout = QHBoxLayout()

        app_title = QLabel("프로그램 화면 설정")
        app_title.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        header_layout.addWidget(app_title)

        self.user_info_label = QLabel()
        header_layout.addWidget(self.user_info_label)
        header_layout.addStretch()

        # 최종 카드 미리보기 버튼
        self.card_preview_btn = QPushButton("🖼️ 최종 카드 미리보기")
        self.card_preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_darker']};
            }}
            QPushButton:checked {{
                background-color: #e74c3c;
            }}
        """)
        self.card_preview_btn.setCheckable(True)
        self.card_preview_btn.clicked.connect(self._toggle_card_preview_dialog)
        header_layout.addWidget(self.card_preview_btn)

        layout.addLayout(header_layout)
        
        # 설명 추가
        description = QLabel("키오스크 애플리케이션 설정을 편집하세요. 각 탭에서 특정 화면과 관련된 설정을 변경할 수 있습니다.")
        description.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; margin-bottom: 0px;")
        layout.addWidget(description)

    def on_config_changed_globally(self):
        """전역 설정 변경 시 호출되는 슬롯"""
        self.statusBar().showMessage("카드 방향 설정이 모든 탭에 실시간으로 반영되었습니다.", 3000)
        # 저장 버튼 상태 업데이트도 필요
        self.config_handler_ui.update_save_button_state()
        # 카드 미리보기 다이얼로그 업데이트
        self._update_card_preview_dialog()

    def _toggle_card_preview_dialog(self, checked):
        """최종 카드 미리보기 다이얼로그 토글"""
        if checked:
            self._show_card_preview_dialog()
        else:
            self._hide_card_preview_dialog()

    def _show_card_preview_dialog(self):
        """최종 카드 미리보기 다이얼로그 표시"""
        if self.card_preview_dialog is None:
            self.card_preview_dialog = FloatingCardPreviewDialog(self.config, self)
            self.card_preview_dialog.closed.connect(self._on_card_preview_dialog_closed)

            # 메인 창 우측에 위치시키기
            main_geo = self.geometry()
            dialog_x = main_geo.right() + 10
            dialog_y = main_geo.top() + 50
            self.card_preview_dialog.move(dialog_x, dialog_y)

        self.card_preview_dialog.update_config(self.config)
        self.card_preview_dialog.show()
        self.card_preview_dialog.raise_()

    def _hide_card_preview_dialog(self):
        """최종 카드 미리보기 다이얼로그 숨기기"""
        if self.card_preview_dialog:
            self.card_preview_dialog.hide()

    def _on_card_preview_dialog_closed(self):
        """다이얼로그가 닫힐 때 버튼 상태 업데이트"""
        self.card_preview_btn.setChecked(False)

    def _update_card_preview_dialog(self):
        """카드 미리보기 다이얼로그 업데이트"""
        if self.card_preview_dialog and self.card_preview_dialog.isVisible():
            self.card_preview_dialog.update_config(self.config)

    def update_card_preview(self):
        """외부에서 카드 미리보기 업데이트 호출용 (탭에서 호출)"""
        self._update_card_preview_dialog()

    def _restore_window_geometry(self):
        """저장된 창 위치/크기 복원"""
        # 저장된 geometry가 있으면 복원
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # 저장된 값이 없으면 기본 크기로 화면 중앙에 배치
            self.resize(1400, 1000)
            self._center_on_screen()

        # 최대화 상태 복원
        is_maximized = self.settings.value("window/maximized", False, type=bool)
        if is_maximized:
            self.showMaximized()

    def _center_on_screen(self):
        """창을 화면 중앙에 배치"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    def _save_window_geometry(self):
        """창 위치/크기 저장"""
        # 최대화 상태 저장
        self.settings.setValue("window/maximized", self.isMaximized())

        # 최대화 상태가 아닐 때만 geometry 저장 (최대화 해제 시 원래 크기로 복원되도록)
        if not self.isMaximized():
            self.settings.setValue("window/geometry", self.saveGeometry())

    def closeEvent(self, event):
        """창 닫힐 때 위치/크기 저장"""
        self._save_window_geometry()
        event.accept()
