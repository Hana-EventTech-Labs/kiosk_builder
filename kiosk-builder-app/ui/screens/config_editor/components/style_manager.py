from ui.styles.colors import COLORS

class StyleManager:
    def apply_styles(self, main_window):
        """메인 윈도우에 스타일 적용"""
        main_window.setStyleSheet(self._get_main_styles())

    def setup_status_bar(self, main_window):
        """상태 바 설정"""
        status_bar = main_window.statusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['background_light']};
                color: {COLORS['text_muted']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        status_bar.showMessage("슈퍼 키오스크 설정 프로그램이 준비되었습니다.")

    def _get_main_styles(self):
        """메인 스타일 반환"""
        return f"""
            QMainWindow {{
                background-color: {COLORS['background']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QMenuBar {{
                background-color: {COLORS['background_light']};
                color: {COLORS['text_dark']};
                border-bottom: 1px solid {COLORS['border']};
                padding: 2px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 8px 12px;
                margin: 2px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_light']};
            }}
            QMenu {{
                background-color: {COLORS['background']};
                color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_light']};
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {COLORS['background_light']};
                border-radius: 10px;
                padding: 10px;
                margin-top: 0px;
            }}
            QTabWidget {{
                background: transparent;
                border: none;
            }}
            QTabBar {{
                border-top: none;
                border-bottom: none;
            }}
            QTabWidget::tab-bar {{
                alignment: left;
                border-top: none;
                border-bottom: none;
            }}
            QTabBar::tab {{
                background-color: {COLORS['background']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                padding: 10px 20px;
                margin: 0 4px 0 0;
                font-size: 13px;
                font-weight: bold;
                min-width: 120px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_light']};
                font-weight: bold;
                border: 2px solid {COLORS['primary_dark']};
                border-bottom: none;
            }}
            QTabBar::tab:!selected:hover {{
                background-color: {COLORS['background_light']};
                color: {COLORS['text_dark']};
            }}
            QTabBar::tab:disabled {{
                color: {COLORS['disabled_text']};
                background-color: {COLORS['disabled']};
                border-color: {COLORS['disabled']};
                font-style: italic;
                opacity: 0.7;
            }}
            QGroupBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 1.5ex;
                padding-top: 1.5ex;
                background-color: {COLORS['background']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: {COLORS['text_dark']};
                font-weight: bold;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """
