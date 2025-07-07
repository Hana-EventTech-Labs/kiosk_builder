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
    # 새로운 실시간 업데이트 시그널 추가
    real_time_update_requested = Signal()

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
        # BasicTab에 tab_manager 참조 설정
        if hasattr(self.tabs['basic'], 'set_tab_manager'):
            self.tabs['basic'].set_tab_manager(self)
        self.tab_widget.addTab(self.tabs['basic'], "기본 설정")
        
        self.tabs['splash'] = SplashTab(config)
        self.tab_widget.addTab(self.tabs['splash'], "스플래쉬 화면(0)")
        
        self.tabs['capture'] = CaptureTab(config)
        # CaptureTab에 tab_manager 참조 설정
        if hasattr(self.tabs['capture'], 'set_tab_manager'):
            self.tabs['capture'].set_tab_manager(self)
        self.tab_widget.addTab(self.tabs['capture'], "촬영 화면(1)")
        
        self.tabs['keyboard'] = KeyboardTab(config)
        # KeyboardTab에 tab_manager 참조 설정
        if hasattr(self.tabs['keyboard'], 'set_tab_manager'):
            self.tabs['keyboard'].set_tab_manager(self)
        self.tab_widget.addTab(self.tabs['keyboard'], "키보드 화면(2)")
        
        self.tabs['qr'] = QRTab(config)
        self.tab_widget.addTab(self.tabs['qr'], "QR코드 화면(3)")
        # QRTab에 tab_manager 참조 설정
        if hasattr(self.tabs['qr'], 'set_tab_manager'):
            self.tabs['qr'].set_tab_manager(self)
        
        self.tabs['frame'] = FrameTab(config)
        self.tab_widget.addTab(self.tabs['frame'], "프레임 화면(4)")
        
        self.tabs['processing'] = ProcessingTab(config)
        self.tab_widget.addTab(self.tabs['processing'], "발급중 화면(5)")
        
        self.tabs['complete'] = CompleteTab(config)
        self.tab_widget.addTab(self.tabs['complete'], "발급완료 화면(6)")
        
        # 실시간 업데이트 시그널 연결
        self._connect_real_time_signals()

    def _connect_real_time_signals(self):
        """실시간 업데이트를 위한 시그널 연결"""
        # 각 탭에서 DraggablePreviewLabel의 position_changed 시그널을 연결
        self._connect_draggable_signals()
        
        # 실시간 업데이트 시그널을 processing_tab의 미리보기 업데이트에 연결
        self.real_time_update_requested.connect(self._update_processing_preview)

    def _connect_draggable_signals(self):
        """각 탭의 DraggablePreviewLabel 시그널 연결"""
        try:
            # capture_tab의 드래그 가능한 라벨들
            if hasattr(self.tabs['capture'], 'camera_preview_label'):
                self.tabs['capture'].camera_preview_label.position_changed.connect(self._on_position_changed)
            if hasattr(self.tabs['capture'], 'image_preview_label'):
                self.tabs['capture'].image_preview_label.position_changed.connect(self._on_position_changed)
            
            # keyboard_tab의 드래그 가능한 라벨들
            if hasattr(self.tabs['keyboard'], 'keyboard_preview_label'):
                self.tabs['keyboard'].keyboard_preview_label.position_changed.connect(self._on_position_changed)
            
            # qr_tab의 드래그 가능한 라벨들
            if hasattr(self.tabs['qr'], 'qr_preview_label'):
                self.tabs['qr'].qr_preview_label.position_changed.connect(self._on_position_changed)
            if hasattr(self.tabs['qr'], 'image_preview_label'):
                self.tabs['qr'].image_preview_label.position_changed.connect(self._on_position_changed)
            
            # basic_tab의 드래그 가능한 라벨들
            if hasattr(self.tabs['basic'], 'crop_preview_label'):
                self.tabs['basic'].crop_preview_label.position_changed.connect(self._on_position_changed)
            if hasattr(self.tabs['basic'], 'image_preview_label'):
                self.tabs['basic'].image_preview_label.position_changed.connect(self._on_position_changed)
            
            # keyboard_tab의 동적 생성되는 라벨들은 별도로 처리
            self._connect_keyboard_dynamic_signals()
                
        except Exception as e:
            print(f"드래그 시그널 연결 중 오류 발생: {e}")

    def _connect_keyboard_dynamic_signals(self):
        """keyboard_tab의 동적으로 생성되는 라벨들의 시그널 연결"""
        try:
            keyboard_tab = self.tabs['keyboard']
            
            # 텍스트 입력 미리보기 라벨들
            if hasattr(keyboard_tab, 'text_input_preview_labels'):
                for i, label in enumerate(keyboard_tab.text_input_preview_labels):
                    if hasattr(label, 'position_changed'):
                        label.position_changed.connect(self._on_position_changed)
            
            # 고정 텍스트 미리보기 라벨들
            if hasattr(keyboard_tab, 'text_preview_labels'):
                for i, label in enumerate(keyboard_tab.text_preview_labels):
                    if hasattr(label, 'position_changed'):
                        label.position_changed.connect(self._on_position_changed)
                        
        except Exception as e:
            print(f"키보드 탭 동적 시그널 연결 중 오류 발생: {e}")

    def _on_position_changed(self, x, y):
        """위치 변경 시 호출되는 슬롯"""
        # 현재 탭의 config를 업데이트
        self._update_current_tab_config()
        
        # 실시간 업데이트 요청
        self.real_time_update_requested.emit()

    def _update_current_tab_config(self):
        """현재 탭의 설정을 config에 반영"""
        current_tab_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.widget(current_tab_index)
        
        if hasattr(current_tab, 'update_config'):
            current_tab.update_config(self.main_window.config)

    def _update_processing_preview(self):
        """processing_tab의 미리보기 업데이트"""
        if 'processing' in self.tabs:
            processing_tab = self.tabs['processing']
            if hasattr(processing_tab, '_update_final_card_preview'):
                processing_tab._update_final_card_preview()

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

    def reconnect_dynamic_signals(self):
        """동적으로 생성되는 라벨들의 시그널 재연결 (탭에서 호출)"""
        self._connect_keyboard_dynamic_signals()
