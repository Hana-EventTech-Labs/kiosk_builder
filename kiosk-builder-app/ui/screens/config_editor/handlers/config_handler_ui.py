from PySide6.QtWidgets import QMessageBox
from ui.styles.colors import COLORS
import copy
import os

class ConfigHandlerUI:
    def __init__(self, main_window):
        self.main_window = main_window

    def save_config(self):
        """설정 저장"""
        self.main_window.tab_manager.update_config_from_tabs(self.main_window.config)
        
        missing_fonts = self._check_missing_fonts()
        if missing_fonts:
            error_msg = "다음 폰트 파일을 찾을 수 없습니다:\n\n" + "\n".join(missing_fonts)
            self._show_message_box("폰트 파일 누락", error_msg, QMessageBox.Warning)
            return
        
        if self.main_window.config_manager.save_config():
            self._show_message_box("저장 완료", "설정이 저장되었습니다.", QMessageBox.Information)
            self.main_window.statusBar().showMessage("설정이 성공적으로 저장되었습니다.")
            self.update_save_button_state()
        else:
            self._show_message_box("저장 실패", "설정 저장 중 오류가 발생했습니다.", QMessageBox.Warning)

    def reload_config(self):
        """설정 다시 로드"""
        self.main_window.config = self.main_window.config_manager.reload_config()
        self.main_window.tab_manager.update_ui_from_config(self.main_window.config)
        self._show_message_box("설정 로드", "설정이 다시 로드되었습니다.", QMessageBox.Information)

    def update_save_button_state(self):
        """저장 버튼 상태 업데이트"""
        enabled = os.path.exists(self.main_window.config_manager.config_path)
        self.main_window.button_manager.update_save_button_state(enabled)

    def _check_missing_fonts(self):
        """폰트 파일 존재 여부 확인"""
        missing_fonts = []
        
        # 텍스트 항목 폰트 확인
        keyboard_tab = self.main_window.tab_manager.tabs['keyboard']
        for i, fields in enumerate(keyboard_tab.text_item_fields):
            font_file = fields["font"].text()
            if font_file and font_file.strip():
                font_path = os.path.join("resources/font", font_file)
                if not os.path.exists(font_path):
                    missing_fonts.append(f"텍스트 {i+1}: {font_file}")
        
        # 화면별 폰트 확인
        for section, tab_key in [("splash", "splash"), ("process", "processing"), ("complete", "complete")]:
            tab = self.main_window.tab_manager.tabs[tab_key]
            fields = getattr(tab, f"{section}_fields")
            font_file = fields["font"].text()
            if font_file and font_file.strip():
                font_path = os.path.join("resources/font", font_file)
                if not os.path.exists(font_path):
                    missing_fonts.append(f"{section} 화면: {font_file}")
        
        return missing_fonts

    def _show_message_box(self, title, message, icon=QMessageBox.Information):
        """스타일이 적용된 메시지 박스 표시"""
        msg_box = QMessageBox(self.main_window)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setMinimumWidth(400)
        
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['background']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {COLORS['text_dark']};
                font-size: 12px;
                padding: 10px;
                qproperty-alignment: AlignLeft;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_light']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_darker']};
            }}
        """)
        
        return msg_box.exec_()