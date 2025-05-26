
from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import Qt
from ui.styles.colors import COLORS

from ..basic_tab import BasicTab
from ..splash_tab import SplashTab
from ..capture_tab import CaptureTab
from ..keyboard_tab import KeyboardTab
from ..qr_tab import QRTab
from ..processing_tab import ProcessingTab
from ..complete_tab import CompleteTab

class TabManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tab_widget = None
        self.tabs = {}

    def create_tabs(self):
        """탭 위젯 생성"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setElideMode(Qt.ElideNone)
        self.tab_widget.setMovable(False)
        self.tab_widget.setUsesScrollButtons(True)
        
        # 탭들 생성
        self._create_individual_tabs()
        self.update_tab_enabled_states()

    def _create_individual_tabs(self):
        """개별 탭들 생성"""
        config = self.main_window.config
        
        self.tabs['basic'] = BasicTab(config)
        self.tab_widget.addTab(self.tabs['basic'], "기본 설정")
        
        self.tabs['splash'] = SplashTab(config)
        self.tab_widget.addTab(self.tabs['splash'], "스플래쉬 화면(0)")
        
        self.tabs['capture'] = CaptureTab(config)
        self.tab_widget.addTab(self.tabs['capture'], "촬영 화면(1)")
        
        self.tabs['keyboard'] = KeyboardTab(config)
        self.tab_widget.addTab(self.tabs['keyboard'], "키보드 화면(2)")
        
        self.tabs['qr'] = QRTab(config)
        self.tab_widget.addTab(self.tabs['qr'], "QR코드 화면(3)")
        
        self.tabs['processing'] = ProcessingTab(config)
        self.tab_widget.addTab(self.tabs['processing'], "발급중 화면(4)")
        
        self.tabs['complete'] = CompleteTab(config)
        self.tab_widget.addTab(self.tabs['complete'], "발급완료 화면(5)")

    def update_tab_enabled_states(self):
        """화면 순서에 따라 탭 활성화/비활성화"""
        try:
            basic_tab = self.tabs['basic']
            screen_order_text = basic_tab.screen_order_edit.text()
            
            if not screen_order_text.strip():
                screen_order = self.main_window.config["screen_order"]
            else:
                try:
                    screen_order = [int(x.strip()) for x in screen_order_text.split(",")]
                except ValueError:
                    for i in range(1, 7):
                        self.tab_widget.setTabEnabled(i, True)
                    return
            
            # 탭 인덱스 매핑
            tab_indices = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
            
            # 모든 화면 탭 비활성화
            for i in range(1, 7):
                self.tab_widget.setTabEnabled(i, False)
            
            # screen_order에 있는 탭만 활성화
            for screen_type in screen_order:
                if 0 <= screen_type <= 5:
                    tab_index = tab_indices.get(screen_type)
                    if tab_index is not None:
                        self.tab_widget.setTabEnabled(tab_index, True)
            
            # 스타일 업데이트
            self.tab_widget.setStyleSheet(self.tab_widget.styleSheet())
            
            # 상태 바 업데이트
            self.main_window.statusBar().showMessage(
                f"화면 순서가 업데이트되었습니다: {', '.join(map(str, screen_order))}"
            )
            
        except Exception as e:
            print(f"탭 활성화 상태 업데이트 중 오류 발생: {e}")
            for i in range(1, 7):
                self.tab_widget.setTabEnabled(i, True)

    def update_ui_from_config(self, config):
        """설정에 따라 모든 탭 UI 업데이트"""
        for tab in self.tabs.values():
            if hasattr(tab, 'update_ui'):
                tab.update_ui(config)
        self.update_tab_enabled_states()

    def update_config_from_tabs(self, config):
        """모든 탭에서 설정값 수집"""
        for tab in self.tabs.values():
            if hasattr(tab, 'update_config'):
                tab.update_config(config)
