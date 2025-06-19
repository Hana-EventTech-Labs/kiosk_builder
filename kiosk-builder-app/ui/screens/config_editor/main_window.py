# kiosk-builder-app/ui/screens/config_editor/main_window.py 수정

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import copy
import os
import sys

# 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from utils.config_handler import ConfigHandler
from utils.auth_manager import AuthManager
# from utils.auto_updater import AutoUpdater  # 이 줄 삭제
from ui.styles.colors import COLORS

from .components.menu_manager import MenuManager
from .components.tab_manager import TabManager
from .components.button_manager import ButtonManager
from .components.style_manager import StyleManager
from .handlers.config_handler_ui import ConfigHandlerUI
from .handlers.distribution_handler import DistributionHandler

# 프로젝트 루트의 version.py를 import하기 위한 경로 추가
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
sys.path.insert(0, os.path.abspath(project_root))

try:
    from version import get_version, get_full_version
    VERSION_AVAILABLE = True
except ImportError:
    # 현재 디렉토리에서 찾을 수 없으면 상위 디렉토리에서 시도
    try:
        import sys
        import os
        # kiosk-builder-app 기준으로 프로젝트 루트의 version.py 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # main_window.py에서 프로젝트 루트까지 4단계 상위
        project_root = os.path.join(current_dir, '..', '..', '..', '..')
        sys.path.insert(0, os.path.abspath(project_root))
        from version import get_version, get_full_version
        VERSION_AVAILABLE = True
    except ImportError:
        VERSION_AVAILABLE = False
        def get_version():
            return "1.0.0"
        def get_full_version():
            return "1.0.0 (Build 001, 2025-05-26)"
    
class ConfigEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_version = get_version() if VERSION_AVAILABLE else "1.0.0"
        
        # 핵심 매니저들 초기화
        self.config_handler = ConfigHandler()
        self.auth_manager = AuthManager()
        self.config = copy.deepcopy(self.config_handler.config)
        
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

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(f"S.K Program - 설정 편집기 v{self.current_version}")
        self.setMinimumSize(1250, 900)
        
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
        
        # 메뉴바 생성
        self.menu_manager.create_menu_bar()
        
        # 상태 바 설정
        self.style_manager.setup_status_bar(self)

    def add_header(self, layout):
        """헤더 추가"""
        from PySide6.QtWidgets import QHBoxLayout, QLabel
        
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
        
        layout.addLayout(header_layout)
        
        # 설명 추가
        description = QLabel("키오스크 애플리케이션 설정을 편집하세요. 각 탭에서 특정 화면과 관련된 설정을 변경할 수 있습니다.")
        description.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; margin-bottom: 0px;")
        layout.addWidget(description)

