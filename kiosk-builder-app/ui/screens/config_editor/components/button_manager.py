from PySide6.QtWidgets import QHBoxLayout, QPushButton
from ui.styles.colors import COLORS

class ButtonManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.buttons = {}

    def create_buttons(self, parent_layout):
        """버튼들 생성"""
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 15, 0, 0)
        
        btn_style = self._get_button_style()
        
        # 배포용 생성 버튼
        self.buttons['build'] = QPushButton("배포용 생성")
        self.buttons['build'].setStyleSheet(btn_style)
        self.buttons['build'].clicked.connect(self.main_window.distribution_handler.create_distribution)
        button_layout.addWidget(self.buttons['build'])
        
        button_layout.addSpacing(10)
        
        # 저장 버튼
        self.buttons['save'] = QPushButton("저장")
        self.buttons['save'].setStyleSheet(btn_style)
        self.buttons['save'].clicked.connect(self.main_window.config_handler_ui.save_config)
        button_layout.addWidget(self.buttons['save'])
        
        button_layout.addSpacing(10)
        
        # 다시 로드 버튼
        self.buttons['reload'] = QPushButton("다시 로드")
        self.buttons['reload'].setStyleSheet(btn_style)
        self.buttons['reload'].clicked.connect(self.main_window.config_handler_ui.reload_config)
        button_layout.addWidget(self.buttons['reload'])
        
        parent_layout.addLayout(button_layout)

    def _get_button_style(self):
        """버튼 스타일 반환"""
        return f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 16px;
                min-width: 120px;
                height: 45px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_darker']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['disabled']};
                color: {COLORS['disabled_text']};
            }}
        """

    def update_save_button_state(self, enabled):
        """저장 버튼 상태 업데이트"""
        if 'save' in self.buttons:
            self.buttons['save'].setEnabled(enabled)