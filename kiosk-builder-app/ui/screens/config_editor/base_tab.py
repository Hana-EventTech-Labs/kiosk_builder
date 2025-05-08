from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PySide6.QtCore import Qt
from ui.styles.colors import COLORS  # 경로 수정됨

class BaseTab(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        
    def create_tab_with_scroll(self):
        """스크롤 영역이 있는 탭 기본 구조 생성"""
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)  # 프레임 제거
        
        # 스크롤 내용 위젯
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        content_widget.setStyleSheet(f"""
            #scrollContent {{
                background-color: {COLORS['background_light']};
                border-radius: 8px;
            }}
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # 단위 안내 레이블 추가
        unit_label = QLabel("모든 크기와 위치의 단위는 px(픽셀)입니다.")
        unit_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-style: italic;")
        content_layout.addWidget(unit_label)
        
        # 스크롤 영역에 컨텐츠 설정
        scroll.setWidget(content_widget)
        
        # 탭에 스크롤 영역 추가
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
        return content_layout
    
    def update_ui(self, config):
        """설정에 따라 UI 업데이트 (하위 클래스에서 구현)"""
        pass
    
    def update_config(self, config):
        """UI 내용을 config에 업데이트 (하위 클래스에서 구현)"""
        pass