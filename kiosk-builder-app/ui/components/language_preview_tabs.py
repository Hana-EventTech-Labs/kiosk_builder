"""
언어별 미리보기 탭 위젯

기본/한국어/영어 3가지 버전의 미리보기를 탭으로 제공합니다.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QGroupBox
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor

from .live_preview import LivePreviewWidget, TextPreviewWidget
from utils.file_handler import FileHandler


class LanguagePreviewTabs(QWidget):
    """
    언어별 미리보기 탭 위젯

    기본/한국어/영어 3개의 탭으로 각 언어별 배경화면 미리보기를 제공합니다.
    """

    # 시그널 전달
    position_changed = Signal(str, int, int)
    size_changed = Signal(str, int, int, int, int)

    def __init__(self, screen_key: str, preview_size: QSize = None,
                 preview_type: str = "live", parent=None):
        """
        Args:
            screen_key: 화면 식별자 (1, 2, 3, 4, splash, process, complete 등)
            preview_size: 미리보기 크기 (기본: 350x350)
            preview_type: "live" (LivePreviewWidget) 또는 "text" (TextPreviewWidget)
            parent: 부모 위젯
        """
        super().__init__(parent)

        self.screen_key = screen_key
        self._preview_size = preview_size or QSize(350, 350)
        self._preview_type = preview_type

        # 3개의 미리보기 위젯 (기본, 한국어, 영어)
        self.preview_default = None
        self.preview_ko = None
        self.preview_en = None

        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 탭 위젯 (탭을 왼쪽에 세로로 배치)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.West)  # 탭을 왼쪽에 배치
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: #f8f9fa;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #ffffff;
                border: 1px solid #ddd;
                padding: 8px 6px;
                margin-bottom: 2px;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                font-size: 11px;
                min-width: 60px;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
                border-right-color: #4CAF50;
            }
            QTabBar::tab:hover:!selected {
                background: #e8f5e9;
            }
        """)

        # 기본 미리보기 탭
        default_tab = self._create_preview_tab(None, "기본 배경")
        self.tab_widget.addTab(default_tab, "기본")

        # 한국어 미리보기 탭
        ko_tab = self._create_preview_tab("ko", "한국어 배경")
        self.tab_widget.addTab(ko_tab, "한국")

        # 영어 미리보기 탭
        en_tab = self._create_preview_tab("en", "영어 배경")
        self.tab_widget.addTab(en_tab, "영어")

        layout.addWidget(self.tab_widget)

    def _create_preview_tab(self, lang: str, title: str) -> QWidget:
        """
        미리보기 탭 생성

        Args:
            lang: 언어 코드 (None, "ko", "en")
            title: 탭 제목
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        # 미리보기 위젯 생성 (탭이 좌측에 있으므로 높이는 그대로, 너비만 약간 축소)
        inner_size = QSize(self._preview_size.width() - 20, self._preview_size.height())
        if self._preview_type == "text":
            preview = TextPreviewWidget(preview_size=inner_size)
        else:
            preview = LivePreviewWidget(preview_size=inner_size)

        # 시그널 연결
        preview.position_changed.connect(self.position_changed.emit)
        if hasattr(preview, 'size_changed'):
            preview.size_changed.connect(self.size_changed.emit)

        # 언어별 미리보기 저장
        if lang is None:
            self.preview_default = preview
        elif lang == "ko":
            self.preview_ko = preview
        else:
            self.preview_en = preview

        layout.addWidget(preview, 0, Qt.AlignCenter)

        return tab

    def get_all_previews(self):
        """모든 미리보기 위젯 반환"""
        return [self.preview_default, self.preview_ko, self.preview_en]

    def get_current_preview(self):
        """현재 선택된 탭의 미리보기 위젯 반환"""
        index = self.tab_widget.currentIndex()
        if index == 0:
            return self.preview_default
        elif index == 1:
            return self.preview_ko
        else:
            return self.preview_en

    def update_all_previews(self, update_func):
        """
        모든 미리보기 위젯에 업데이트 함수 적용

        Args:
            update_func: (preview, lang) -> None 형태의 함수
        """
        if self.preview_default:
            update_func(self.preview_default, None)
        if self.preview_ko:
            update_func(self.preview_ko, "ko")
        if self.preview_en:
            update_func(self.preview_en, "en")

    def refresh_status_labels(self):
        """배경 파일 상태 레이블 새로고침 (호환성 유지용 - 현재 미사용)"""
        pass

    def update_tab_visibility(self, lang_enabled: bool):
        """
        언어 활성화 상태에 따라 탭 활성화/비활성화 (전체 탭 항상 표시)

        Args:
            lang_enabled: True이면 한국어/영어 탭 활성화, False이면 기본 탭만 활성화
        """
        # 모든 탭 항상 표시
        self.tab_widget.setTabVisible(0, True)
        self.tab_widget.setTabVisible(1, True)
        self.tab_widget.setTabVisible(2, True)

        if lang_enabled:
            # 언어 활성화: 기본 탭 비활성화, 한국어/영어 탭 활성화
            self.tab_widget.setTabEnabled(0, False)  # 기본 탭 비활성화
            self.tab_widget.setTabEnabled(1, True)   # 한국어 탭 활성화
            self.tab_widget.setTabEnabled(2, True)   # 영어 탭 활성화
            # 현재 기본 탭이 선택되어 있으면 한국어 탭으로 전환
            if self.tab_widget.currentIndex() == 0:
                self.tab_widget.setCurrentIndex(1)
        else:
            # 언어 비활성화: 기본 탭만 활성화, 한국어/영어 탭 비활성화
            self.tab_widget.setTabEnabled(0, True)   # 기본 탭 활성화
            self.tab_widget.setTabEnabled(1, False)  # 한국어 탭 비활성화
            self.tab_widget.setTabEnabled(2, False)  # 영어 탭 비활성화
            # 현재 한국어/영어 탭이 선택되어 있으면 기본 탭으로 전환
            if self.tab_widget.currentIndex() != 0:
                self.tab_widget.setCurrentIndex(0)

    def get_current_lang(self):
        """현재 선택된 탭의 언어 코드 반환"""
        index = self.tab_widget.currentIndex()
        if index == 0:
            return None
        elif index == 1:
            return "ko"
        else:
            return "en"
