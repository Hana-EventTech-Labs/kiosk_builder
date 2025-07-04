from PySide6.QtWidgets import QTabWidget
from PySide6.QtCore import Qt, Signal, QObject
from ui.styles.colors import COLORS

from ..basic_tab import BasicTab
from ..splash_tab import SplashTab
from ..capture_tab import CaptureTab
from ..keyboard_tab import KeyboardTab
from ..qr_tab import QRTab
from ..processing_tab import ProcessingTab
from ..complete_tab import CompleteTab
from ..frame_tab import FrameTab

class TabManager(QObject):
    config_changed = Signal()

    def __init__(self, main_window):
        super().__init__(main_window)
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
        self.tabs['basic'].config_changed.connect(self.on_config_changed_from_tab)
        self.tab_widget.addTab(self.tabs['basic'], "기본 설정")
        
        self.tabs['splash'] = SplashTab(config)
        self.tab_widget.addTab(self.tabs['splash'], "스플래쉬 화면(0)")
        
        self.tabs['capture'] = CaptureTab(config)
        self.tab_widget.addTab(self.tabs['capture'], "촬영 화면(1)")
        
        self.tabs['keyboard'] = KeyboardTab(config)
        self.tab_widget.addTab(self.tabs['keyboard'], "키보드 화면(2)")
        
        self.tabs['qr'] = QRTab(config)
        self.tab_widget.addTab(self.tabs['qr'], "QR코드 화면(3)")
        
        self.tabs['frame'] = FrameTab(config)
        self.tab_widget.addTab(self.tabs['frame'], "프레임 화면(4)")
        
        self.tabs['processing'] = ProcessingTab(config)
        self.tab_widget.addTab(self.tabs['processing'], "발급중 화면(5)")
        
        self.tabs['complete'] = CompleteTab(config)
        self.tab_widget.addTab(self.tabs['complete'], "발급완료 화면(6)")

    def on_config_changed_from_tab(self):
        """특정 탭에서 config가 변경되었을 때 호출되는 슬롯"""
        self.update_ui_from_config(self.main_window.config)

    def update_tab_enabled_states(self):
        """화면 순서에 따라 탭 활성화/비활성화"""
        try:
            basic_tab = self.tabs['basic']
            # 체크박스에서 화면 순서 가져오기
            screen_order = sorted([
                cb.property("screen_index")
                for cb in basic_tab.screen_order_checkboxes
                if cb.isChecked()
            ])
            
            # 탭 인덱스 매핑 (기존 유지)
            # 0: 스플래쉬, 1: 촬영, 2: 키보드, 3: QR, 4: 프레임, 5: 발급중, 6: 완료
            tab_mapping = {
                0: self.tabs['splash'],
                1: self.tabs['capture'],
                2: self.tabs['keyboard'],
                3: self.tabs['qr'],
                4: self.tabs['frame'],
                5: self.tabs['processing'],
                6: self.tabs['complete']
            }

            # 모든 화면 탭 비활성화
            for tab in tab_mapping.values():
                self.tab_widget.setTabEnabled(self.tab_widget.indexOf(tab), False)
            
            # screen_order에 있는 탭만 활성화
            for screen_index in screen_order:
                if screen_index in tab_mapping:
                    tab_widget = tab_mapping[screen_index]
                    self.tab_widget.setTabEnabled(self.tab_widget.indexOf(tab_widget), True)

            # 기본 탭은 항상 활성화
            self.tab_widget.setTabEnabled(self.tab_widget.indexOf(self.tabs['basic']), True)
            
            # 스타일 업데이트
            self.tab_widget.setStyleSheet(self.tab_widget.styleSheet())
            
            # 상태 바 업데이트
            self.main_window.statusBar().showMessage(
                f"화면 순서가 업데이트되었습니다: {', '.join(map(str, screen_order))}"
            )
            
        except Exception as e:
            print(f"탭 활성화 상태 업데이트 중 오류 발생: {e}")
            # 오류 발생 시 모든 탭 활성화 (안전 조치)
            for i in range(self.tab_widget.count()):
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
