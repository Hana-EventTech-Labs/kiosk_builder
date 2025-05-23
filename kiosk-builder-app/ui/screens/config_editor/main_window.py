from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QMessageBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon,QAction
from utils.auth_manager import AuthManager
from PySide6.QtWidgets import QMenuBar, QMenu
import json
import copy
import os
import shutil
import requests
from utils.config_handler import ConfigHandler
from ui.styles.colors import COLORS
from .basic_tab import BasicTab
from .splash_tab import SplashTab
from .capture_tab import CaptureTab
from .keyboard_tab import KeyboardTab
from .qr_tab import QRTab
from .processing_tab import ProcessingTab
from .complete_tab import CompleteTab
from .download_progress_dialog import DownloadProgressDialog

class ConfigEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_handler = ConfigHandler()
        self.auth_manager = AuthManager()  # 추가된 라인
        self.config = copy.deepcopy(self.config_handler.config)
        
        # GitHub Releases 다운로드 URL 설정
        self.github_release_base_url = "https://github.com/Hana-EventTech-Labs/kiosk_builder/releases/download/v1.0.0"
        
        self.init_ui()
        self.create_menu_bar()  # 추가된 라인
        
        # config.json 파일 존재 여부에 따라 저장 버튼 상태 설정
        self.update_save_button_state()

    def init_ui(self):
        self.setWindowTitle("S.K Program - 설정 편집기")
        self.setMinimumSize(1250, 900)
        
        # 탭 위젯 스타일 (기존과 동일하지만 QMenuBar 스타일 추가)
        self.setStyleSheet(f"""
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
        """)
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 헤더 추가
        header_layout = QHBoxLayout()
        
        # 앱 타이틀
        app_title = QLabel("프로그램 화면 설정")
        app_title.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        header_layout.addWidget(app_title)
        
        # 사용자 정보 표시 (추가된 부분)
        self.user_info_label = QLabel()
        self.update_user_info()
        header_layout.addWidget(self.user_info_label)
        
        # 헤더에 여백 추가
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # 설명 레이블 추가
        description = QLabel("키오스크 애플리케이션 설정을 편집하세요. 각 탭에서 특정 화면과 관련된 설정을 변경할 수 있습니다.")
        description.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; margin-bottom: 0px;")

        main_layout.addWidget(description)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setElideMode(Qt.ElideNone)
        self.tab_widget.setMovable(False)
        self.tab_widget.setUsesScrollButtons(True)
        main_layout.addWidget(self.tab_widget)
        
        # 탭 생성
        self.basic_tab = BasicTab(self.config)
        self.tab_widget.addTab(self.basic_tab, "기본 설정")
        
        self.splash_tab = SplashTab(self.config)
        self.tab_widget.addTab(self.splash_tab, "스플래쉬 화면(0)")
        
        self.capture_tab = CaptureTab(self.config)
        self.tab_widget.addTab(self.capture_tab, "촬영 화면(1)")
        
        self.keyboard_tab = KeyboardTab(self.config)
        self.tab_widget.addTab(self.keyboard_tab, "키보드 화면(2)")
        
        self.qr_tab = QRTab(self.config)
        self.tab_widget.addTab(self.qr_tab, "QR코드 화면(3)")
        
        self.processing_tab = ProcessingTab(self.config)
        self.tab_widget.addTab(self.processing_tab, "발급중 화면(4)")
        
        self.complete_tab = CompleteTab(self.config)
        self.tab_widget.addTab(self.complete_tab, "발급완료 화면(5)")
        
        # 화면 순서에 따라 탭 활성화/비활성화 설정
        self.update_tab_enabled_states()
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 15, 0, 0)
        main_layout.addLayout(button_layout)
        
        # 버튼 스타일 정의
        btn_style = f"""
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
        
        # 배포용 생성 버튼
        self.build_button = QPushButton("배포용 생성")
        self.build_button.setStyleSheet(btn_style)
        self.build_button.clicked.connect(self.create_distribution)
        button_layout.addWidget(self.build_button)
        
        # 버튼 사이 간격
        button_layout.addSpacing(10)
        
        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setStyleSheet(btn_style)
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        # 버튼 사이 간격
        button_layout.addSpacing(10)
        
        # 다시 로드 버튼
        self.reload_button = QPushButton("다시 로드")
        self.reload_button.setStyleSheet(btn_style)
        self.reload_button.clicked.connect(self.reload_config)
        button_layout.addWidget(self.reload_button)
        
        # 상태 바 설정
        status_bar = self.statusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['background_light']};
                color: {COLORS['text_muted']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        status_bar.showMessage("슈퍼 키오스크 설정 프로그램이 준비되었습니다.")

    # 새로 추가되는 메서드들
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 계정 메뉴
        account_menu = menubar.addMenu("계정")
        
        # 로그아웃 액션
        logout_action = QAction("로그아웃", self)
        logout_action.setStatusTip("다른 계정으로 로그인")
        logout_action.triggered.connect(self.logout)
        account_menu.addAction(logout_action)
        
        # 구분선
        account_menu.addSeparator()
        
        # 종료 액션
        exit_action = QAction("종료", self)
        exit_action.setStatusTip("프로그램 종료")
        exit_action.triggered.connect(self.close)
        account_menu.addAction(exit_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")
        
        # 정보 액션
        about_action = QAction("프로그램 정보", self)
        about_action.setStatusTip("프로그램 정보 보기")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def update_user_info(self):
        # """사용자 정보 업데이트"""
        # import builtins
        # user_id = getattr(builtins, 'CURRENT_USER_ID', 0)
        
        # if user_id > 0:
        #     # 실제 환경에서는 사용자 정보를 API에서 가져올 수 있음
        #     # self.user_info_label.setText(f"사용자 ID: {user_id}")
        #     self.user_info_label.setStyleSheet(f"""
        #         color: {COLORS['text_muted']};
        #         font-size: 12px;
        #         background-color: {COLORS['background_light']};
        #         padding: 5px 10px;
        #         border-radius: 4px;
        #         border: 1px solid {COLORS['border']};
        #     """)
        # else:
        #     self.user_info_label.setText("사용자 정보 없음")
        #     self.user_info_label.setStyleSheet(f"""
        #         color: {COLORS['danger']};
        #         font-size: 12px;
        #         background-color: {COLORS['background_light']};
        #         padding: 5px 10px;
        #         border-radius: 4px;
        #         border: 1px solid {COLORS['danger']};
        #     """)
        pass
    
    def logout(self):
        """로그아웃 처리"""
        reply = QMessageBox.question(
            self, 
            "로그아웃", 
            "정말 로그아웃하시겠습니까?\n다른 계정으로 로그인할 수 있습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 인증 매니저를 통해 로그아웃 처리
            self.auth_manager.logout()
            
            # 창 닫기
            self.close()
            
            # 로그인 화면으로 돌아가기
            from ui.screens.login_screen import LoginScreen
            
            def show_settings_window():
                from ui.screens.config_editor.main_window import ConfigEditor
                settings_window = ConfigEditor()
                
                # 설정 창에도 아이콘 적용
                icon_path = "Hana.ico"
                if os.path.exists(icon_path):
                    settings_window.setWindowIcon(QIcon(icon_path))
                
                settings_window.show()
                
                # 윈도우 객체가 가비지 컬렉션되지 않도록 전역 변수로 저장
                global main_window
                main_window = settings_window
            
            login_window = LoginScreen(on_login_success=show_settings_window)
            
            # 로그인 창에도 아이콘 적용
            icon_path = "Hana.png"
            if os.path.exists(icon_path):
                login_window.setWindowIcon(QIcon(icon_path))
            
            login_window.show()
            
            # 전역 변수로 참조 유지
            global login_window_ref
            login_window_ref = login_window
    
    def show_about(self):
        """프로그램 정보 표시"""
        QMessageBox.about(
            self,
            "프로그램 정보",
            """
            <h3>슈퍼 키오스크 빌더</h3>
            <p><b>버전:</b> 1.0.0</p>
            <p><b>설명:</b> 키오스크 애플리케이션 설정 도구</p>
            <p><b>개발:</b> HanaLabs</p>
            <p><b>저작권:</b> © 2025 Super Kiosk Builder</p>
            <br>
            <p>이 프로그램은 키오스크 애플리케이션의 화면 설정과<br>
            배포용 파일 생성을 지원합니다.</p>
            """
        )
        
    def download_file_from_github(self, filename, target_path):
        """GitHub Releases에서 파일 다운로드"""
        try:
            download_url = f"{self.github_release_base_url}/{filename}"
            print(f"{filename} 다운로드 시작: {download_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(download_url, headers=headers, timeout=60)
            response.raise_for_status()
            
            # 파일 크기 확인
            if len(response.content) < 10000:  # 10KB 미만이면 실패로 간주
                raise Exception(f"다운로드된 파일이 너무 작습니다 ({len(response.content)} bytes)")
            
            with open(target_path, 'wb') as f:
                f.write(response.content)
            
            print(f"{filename} 다운로드 완료 (크기: {len(response.content):,} bytes)")
            return True
            
        except Exception as e:
            print(f"{filename} 다운로드 실패: {e}")
            return False

    def update_tab_enabled_states(self):
        """현재 screen_order 설정에 따라 탭 활성화/비활성화 상태를 업데이트"""
        try:
            # 화면 순서 가져오기 - 기본 탭에서 화면 순서 텍스트를 가져옴
            screen_order_text = self.basic_tab.screen_order_edit.text()
            
            if not screen_order_text.strip():
                # 텍스트가 비어있으면 기본 config 값 사용
                screen_order = self.config["screen_order"]
            else:
                try:
                    # 텍스트에서 화면 순서 파싱
                    screen_order = [int(x.strip()) for x in screen_order_text.split(",")]
                except ValueError:
                    # 변환할 수 없는 값이 있으면 모든 탭 활성화
                    for i in range(1, 7):
                        self.tab_widget.setTabEnabled(i, True)
                    # 탭 스타일 업데이트
                    self.tab_widget.setStyleSheet(self.tab_widget.styleSheet())
                    return
            
            # 탭 인덱스 매핑
            tab_indices = {
                0: 1,  # 화면 타입 0 (스플래쉬) -> 탭 인덱스 1
                1: 2,  # 화면 타입 1 (촬영) -> 탭 인덱스 2
                2: 3,  # 화면 타입 2 (키보드) -> 탭 인덱스 3
                3: 4,  # 화면 타입 3 (QR코드) -> 탭 인덱스 4
                4: 5,  # 화면 타입 4 (발급중) -> 탭 인덱스 5
                5: 6   # 화면 타입 5 (발급완료) -> 탭 인덱스 6
            }
            
            # 먼저 모든 화면 탭 비활성화
            for i in range(1, 7):  # 1부터 6까지 (기본 설정 탭 제외)
                self.tab_widget.setTabEnabled(i, False)
            
            # screen_order에 있는 탭만 활성화
            for screen_type in screen_order:
                if 0 <= screen_type <= 5:  # 유효한 화면 타입인지 확인
                    tab_index = tab_indices.get(screen_type)
                    if tab_index is not None:
                        self.tab_widget.setTabEnabled(tab_index, True)
            
            # 탭 스타일 업데이트 - CSS가 적용되도록 스타일시트 리프레시
            self.tab_widget.setStyleSheet(self.tab_widget.styleSheet())
            
            # 상태 바 업데이트
            self.statusBar().showMessage(f"화면 순서가 업데이트되었습니다: {', '.join(map(str, screen_order))}")
            
        except Exception as e:
            print(f"탭 활성화 상태 업데이트 중 오류 발생: {e}")
            # 오류가 발생하면 모든 탭 활성화
            for i in range(1, 7):
                self.tab_widget.setTabEnabled(i, True)
            # 탭 스타일 업데이트
            self.tab_widget.setStyleSheet(self.tab_widget.styleSheet())
            
    def save_config(self):
        # 각 탭에서 설정 값 가져오기
        self.update_config_from_tabs()
        
        # 텍스트 항목의 폰트 파일 존재 여부 확인
        missing_fonts = self.check_missing_fonts()
        
        if missing_fonts:
            error_msg = "다음 폰트 파일을 찾을 수 없습니다:\n\n" + "\n".join(missing_fonts)
            self.show_message_box("폰트 파일 누락", error_msg, QMessageBox.Warning)
            return
        
        # 설정 저장
        if self.config_handler.save_config(self.config):
            self.show_message_box("저장 완료", "설정이 저장되었습니다.", QMessageBox.Information)
            # 상태 메시지 업데이트
            self.statusBar().showMessage("설정이 성공적으로 저장되었습니다.")
            # 저장 버튼 상태 업데이트
            self.update_save_button_state()
        else:
            self.show_message_box("저장 실패", "설정 저장 중 오류가 발생했습니다.", QMessageBox.Warning)
            self.statusBar().showMessage("설정 저장 중 오류가 발생했습니다.")
    
    def update_config_from_tabs(self):
        """각 탭에서 설정 값을 가져와 self.config를 업데이트"""
        # 각 탭의 update_config 메서드 호출
        self.basic_tab.update_config(self.config)
        self.splash_tab.update_config(self.config)
        self.capture_tab.update_config(self.config)
        self.keyboard_tab.update_config(self.config)
        self.qr_tab.update_config(self.config)
        self.processing_tab.update_config(self.config)
        self.complete_tab.update_config(self.config)
        
        # 화면 순서에 따른 photo와 qr_uploaded_image 존재 여부 설정
        try:
            screen_order = [int(x.strip()) for x in self.basic_tab.screen_order_edit.text().split(",")]
            
            if "photo" in self.config:
                self.config["photo"]["exists"] = (1 in screen_order)
            
            if "qr_uploaded_image" in self.config:
                self.config["qr_uploaded_image"]["exists"] = (3 in screen_order)
        except ValueError:
            pass
    
    def check_missing_fonts(self):
        """폰트 파일 존재 여부 확인"""
        missing_fonts = []
        
        # 텍스트 항목 폰트 확인
        for i, fields in enumerate(self.keyboard_tab.text_item_fields):
            font_file = fields["font"].text()
            # 폰트가 빈 문자열이면 확인 건너뛰기
            if font_file and font_file.strip():  # 빈 문자열이 아니면 체크
                font_path = os.path.join("resources/font", font_file)
                if not os.path.exists(font_path):
                    missing_fonts.append(f"텍스트 {i+1}: {font_file}")
        
        # 스플래시, 프로세스, 완료 화면의 폰트 확인
        for section, tab in [("splash", self.splash_tab), 
                           ("process", self.processing_tab), 
                           ("complete", self.complete_tab)]:
            fields = getattr(tab, f"{section}_fields")
            font_file = fields["font"].text()
            # 폰트가 빈 문자열이면 확인 건너뛰기
            if font_file and font_file.strip():  # 빈 문자열이 아니면 체크
                font_path = os.path.join("resources/font", font_file)
                if not os.path.exists(font_path):
                    missing_fonts.append(f"{section} 화면: {font_file}")
        
        return missing_fonts
    
    def reload_config(self):
        """설정을 다시 로드하고 UI를 업데이트합니다."""
        self.config = copy.deepcopy(self.config_handler.load_config())
        self.update_ui_from_config()
        self.show_message_box("설정 로드", "설정이 다시 로드되었습니다.", QMessageBox.Information)
        self.statusBar().showMessage("설정이 다시 로드되었습니다.")
    
    def update_ui_from_config(self):
        """현재 설정에 따라 UI 요소들을 업데이트합니다."""
        # 각 탭의 update_ui 메서드 호출
        self.basic_tab.update_ui(self.config)
        self.splash_tab.update_ui(self.config)
        self.capture_tab.update_ui(self.config)
        self.keyboard_tab.update_ui(self.config)
        self.qr_tab.update_ui(self.config)
        self.processing_tab.update_ui(self.config)
        self.complete_tab.update_ui(self.config)
        
        # 탭 활성화 상태 업데이트
        self.update_tab_enabled_states()
    
    def update_save_button_state(self):
        """config.json 파일 존재 여부에 따라 저장 버튼 활성화/비활성화"""
        if os.path.exists(self.config_handler.config_path):
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

    def show_message_box(self, title, message, icon=QMessageBox.Information):
        """스타일이 적용된 메시지 박스 표시"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        
        # 메시지 박스 너비 설정
        msg_box.setMinimumWidth(400)
        
        # 메시지 박스 스타일 설정
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
        
    def create_distribution(self):
        """배포용 파일 생성 및 복사"""
        try:
            import subprocess
            import sys
            
            # 재귀적 복사 함수
            def copy_resources_recursive(source_dir, target_dir):
                """리소스 폴더와 모든 하위 폴더/파일을 재귀적으로 복사"""
                if not os.path.exists(source_dir):
                    print(f"소스 폴더를 찾을 수 없음: {source_dir}")
                    return []
                
                copied_files = []
                
                # 대상 폴더가 없으면 생성
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)
                
                # 소스 폴더의 모든 항목 순회
                for item in os.listdir(source_dir):
                    source_item = os.path.join(source_dir, item)
                    target_item = os.path.join(target_dir, item)
                    
                    if os.path.isdir(source_item):
                        # 디렉토리인 경우 재귀적으로 복사
                        sub_copied = copy_resources_recursive(source_item, target_item)
                        copied_files.extend(sub_copied)
                    else:
                        # 파일인 경우 복사
                        try:
                            shutil.copy2(source_item, target_item)
                            copied_files.append(os.path.relpath(target_item, target_dir))
                            print(f"파일 복사됨: {os.path.relpath(target_item, target_dir)}")
                        except Exception as e:
                            print(f"파일 복사 실패: {item} - {e}")

                return copied_files
            
            # 앱 이름으로 폴더 생성
            app_name = self.basic_tab.app_name_edit.text()
            if not app_name:
                self.show_message_box("경고", "앱 이름을 입력해주세요.", QMessageBox.Warning)
                return

            # 특수문자 및 공백 처리
            app_folder_name = app_name.replace(" ", "_").replace(".", "_")
            
            # 실행 파일 경로 확인 (PyInstaller)
            if getattr(sys, 'frozen', False):
                # PyInstaller로 패키징된 경우
                base_path = sys._MEIPASS
                parent_dir = os.path.dirname(sys.executable)
            else:
                # 일반 Python 스크립트로 실행된 경우
                base_path = os.getcwd()
                parent_dir = os.getcwd()
            
            # 앱 폴더 경로
            target_dir = os.path.join(parent_dir, app_folder_name)
            
            # 설정 업데이트
            self.update_config_from_tabs()
            
            # 로그인 정보 포함 여부 확인
            include_auth = False
            auth_file_path = os.path.join(parent_dir, "auth_settings.dat")
            
            if os.path.exists(auth_file_path):
                # 현재 로그인 설정 확인
                auth_settings = self.auth_manager.load_auth_settings()
                
                if auth_settings.get("auto_login", False) or auth_settings.get("remember_id", False):
                    reply = QMessageBox.question(
                        self, 
                        "로그인 정보 포함", 
                        "현재 저장된 로그인 정보를 배포용 파일에 포함하시겠습니까?\n\n"
                        "포함하면:\n"
                        "✓ 배포된 프로그램에서 자동 로그인/아이디 저장 기능 유지\n"
                        "✗ 다른 사용자가 해당 계정으로 접근 가능\n\n"
                        "포함하지 않으면:\n"
                        "✓ 보안상 안전함\n"
                        "✗ 배포된 프로그램에서 다시 로그인 필요",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    include_auth = (reply == QMessageBox.Yes)
            
            # 폴더가 이미 존재하는지 확인하고 사용자에게 확인
            if os.path.exists(target_dir):
                reply = QMessageBox.question(
                    self, 
                    "폴더 이미 존재", 
                    f"'{app_folder_name}' 폴더가 이미 존재합니다. 내용을 덮어쓰시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                
                # 기존 폴더 내용 삭제
                for item in os.listdir(target_dir):
                    item_path = os.path.join(target_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
            else:
                # 폴더 생성
                os.makedirs(target_dir, exist_ok=True)
            
            # 폴더 구조 생성
            os.makedirs(os.path.join(target_dir, "bin"), exist_ok=True)
            os.makedirs(os.path.join(target_dir, "bin", "resources", "background"), exist_ok=True)
            os.makedirs(os.path.join(target_dir, "bin", "resources", "font"), exist_ok=True)
            
            # 배포 폴더 내에 config.json 파일 생성
            target_config_path = os.path.join(target_dir, "bin", "config.json")
            with open(target_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            # 로그인 정보 파일 복사
            auth_copied = False
            if include_auth and os.path.exists(auth_file_path):
                try:
                    target_auth_path = os.path.join(target_dir, "bin", "auth_settings.dat")
                    shutil.copy2(auth_file_path, target_auth_path)
                    auth_copied = True
                    print("로그인 정보 파일이 복사되었습니다.")
                except Exception as e:
                    print(f"로그인 정보 파일 복사 실패: {e}")
            
            # config.json 생성 후 저장 버튼 상태 업데이트
            self.update_save_button_state()
            
            # resources 폴더 안에 필요한 하위 폴더 확인 및 생성
            resources_path = os.path.join(base_path, "resources")
            font_path = os.path.join(resources_path, "font")
            background_path = os.path.join(resources_path, "background")
            
            # 폴더 생성 여부를 저장할 변수
            created_dirs = []
            
            # font 폴더가 없으면 생성
            if not os.path.exists(font_path):
                os.makedirs(font_path, exist_ok=True)
                created_dirs.append("resources/font")
                print(f"resources/font 폴더를 생성했습니다: {font_path}")
            
            # background 폴더가 없으면 생성
            if not os.path.exists(background_path):
                os.makedirs(background_path, exist_ok=True)
                created_dirs.append("resources/background")
                print(f"resources/background 폴더를 생성했습니다: {background_path}")
            
            # super-kiosk-builder.exe (설정 프로그램) 복사
            builder_exe = os.path.join(parent_dir, "super-kiosk-builder.exe")
            builder_copied = False

            if os.path.exists(builder_exe):
                try:
                    # 실행 중인 파일 복사 시도
                    target_builder_path = os.path.join(target_dir, "bin", "super-kiosk-builder.exe")
                    
                    # 방법 1: robocopy 사용 (Windows 전용)
                    result = subprocess.run([
                        'robocopy', 
                        parent_dir, 
                        os.path.join(target_dir, "bin"), 
                        "super-kiosk-builder.exe",
                        '/R:3',  # 재시도 3번
                        '/W:1'   # 1초 대기
                    ], capture_output=True, text=True)
                    
                    if os.path.exists(target_builder_path):
                        builder_copied = True
                        print("super-kiosk-builder.exe 복사 완료 (robocopy 사용)")
                    else:
                        raise Exception("robocopy 실패")
                        
                except Exception as e:
                    try:
                        # 방법 2: 일반 복사 재시도
                        import time
                        time.sleep(0.1)  # 잠시 대기
                        shutil.copy2(builder_exe, os.path.join(target_dir, "bin", "super-kiosk-builder.exe"))
                        builder_copied = True
                        print("super-kiosk-builder.exe 복사 완료 (일반 복사)")
                    except Exception as e2:
                        print(f"super-kiosk-builder.exe 복사 실패: {e2}")
            else:
                # 다른 경로에서 찾기
                possible_paths = [
                    os.path.join(parent_dir, "dist", "super-kiosk-builder.exe"),
                    os.path.join(parent_dir, "build", "super-kiosk-builder.exe"),
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        try:
                            shutil.copy2(path, os.path.join(target_dir, "bin", "super-kiosk-builder.exe"))
                            builder_copied = True
                            print(f"{path}에서 super-kiosk-builder.exe 복사 완료")
                            break
                        except Exception as e:
                            print(f"{path} 복사 실패: {e}")
            
            # GitHub에서 super-kiosk.exe 다운로드
            github_files = [
                {"name": "super-kiosk.exe", "required": True}
            ]

            downloaded_files = []
            failed_downloads = []

            # 다운로드 진행률 다이얼로그 표시
            download_dialog = DownloadProgressDialog(
                parent=self,
                github_base_url=self.github_release_base_url,
                files_to_download=github_files,
                target_dir=os.path.join(target_dir, "bin")
            )

            # 다이얼로그 실행 (모달)
            download_dialog.exec_()

            # 다운로드 결과 처리 및 파일명 변경
            download_results = download_dialog.get_results()
            kiosk_exe_renamed = False

            for filename, result in download_results.items():
                if result['success'] and filename == "super-kiosk.exe":
                    # 다운로드 성공 시 앱 이름으로 파일명 변경
                    original_path = os.path.join(target_dir, "bin", "super-kiosk.exe")
                    
                    # 앱 이름을 파일명으로 사용 (특수문자 처리)
                    safe_app_name = app_name.replace(" ", "_").replace(".", "_").replace("/", "_").replace("\\", "_")
                    new_filename = f"{safe_app_name}.exe"
                    new_path = os.path.join(target_dir, "bin", new_filename)
                    
                    try:
                        os.rename(original_path, new_path)
                        downloaded_files.append(f"{new_filename} (GitHub에서 다운로드 후 이름 변경, 크기: {result.get('size', 0):,} bytes)")
                        kiosk_exe_renamed = True
                        print(f"super-kiosk.exe를 {new_filename}으로 이름 변경 완료")
                    except Exception as e:
                        print(f"파일명 변경 실패: {e}")
                        downloaded_files.append(f"super-kiosk.exe (GitHub에서 다운로드됨, 크기: {result.get('size', 0):,} bytes)")
                else:
                    failed_downloads.append(filename)
            
            # 폴더들을 대상 폴더로 복사 (재귀적으로)
            copied_folders = []
            missing_folders = []
            copied_resource_files = []

            # resources 폴더 복사
            resources_source = os.path.join(base_path, "resources")
            resources_target = os.path.join(target_dir, "bin", "resources")
            
            if os.path.exists(resources_source):
                # 대상 폴더가 존재하면 삭제 후 복사
                if os.path.exists(resources_target):
                    shutil.rmtree(resources_target)
                
                # 재귀적 복사 함수 사용
                copied_files_list = copy_resources_recursive(resources_source, resources_target)
                if copied_files_list:
                    copied_folders.append("resources")
                    copied_resource_files = copied_files_list
                    
                    # DLL과 폰트 파일 확인
                    dll_files = [f for f in copied_files_list if f.endswith(".dll")]
                    font_files = [f for f in copied_files_list if f.endswith((".ttf", ".otf"))]
                    
                    if dll_files:
                        print(f"DLL 파일 {len(dll_files)}개 복사됨: {', '.join(dll_files)}")
                    
                    if font_files:
                        print(f"폰트 파일 {len(font_files)}개 복사됨: {', '.join(font_files)}")
            else:
                missing_folders.append("resources")
            
            # 결과 메시지 구성
            result_message = f"배포 폴더 '{app_folder_name}'이(가) 생성되었습니다.\n\n"
            
            # 폴더 생성 메시지 추가
            if created_dirs:
                result_message += "다음 폴더를 자동으로 생성했습니다:\n- " + "\n- ".join(created_dirs) + "\n\n"
            
            success_items = []
            
            if builder_copied:
                success_items.append("super-kiosk-builder.exe (설정 프로그램)")
            
            if downloaded_files:
                success_items.extend(downloaded_files)
            
            if copied_folders:
                success_items.extend(copied_folders)
            
            # 로그인 정보 복사 결과 추가
            if auth_copied:
                success_items.append("auth_settings.dat (로그인 정보)")
            
            if success_items:
                result_message += "다음 항목이 성공적으로 복사되었습니다:\n\n"
                result_message += "- " + "\n- ".join(success_items) + "\n\n"
                
                # DLL 및 폰트 파일 정보 추가
                dll_files = [f for f in copied_resource_files if f.endswith(".dll")]
                font_files = [f for f in copied_resource_files if f.endswith((".ttf", ".otf"))]
                
                if dll_files:
                    result_message += f"DLL 파일 {len(dll_files)}개가 복사되었습니다.\n"
                
                if font_files:
                    result_message += f"폰트 파일 {len(font_files)}개가 복사되었습니다.\n\n"
                
                # 로그인 정보 상태 안내
                if auth_copied:
                    result_message += "📋 로그인 정보가 포함되어 자동 로그인이 가능합니다.\n"
                else:
                    result_message += "🔐 로그인 정보가 포함되지 않아 보안상 안전합니다.\n"
            
            failure_items = []
            
            if not builder_copied:
                failure_items.append("super-kiosk-builder.exe (설정 프로그램)")
            
            if failed_downloads:
                failure_items.extend([f"{f} (다운로드 실패)" for f in failed_downloads])
            
            if missing_folders:
                failure_items.extend(missing_folders)
            
            if failure_items:
                result_message += "다음 항목을 찾을 수 없어 복사하지 못했습니다:\n\n"
                result_message += "- " + "\n- ".join(failure_items) + "\n\n"
            
            # 사용자에게 결과 알림
            if success_items:
                QMessageBox.information(
                    self, 
                    "배포용 파일 생성 완료", 
                    result_message
                )
                
                # 배포용 생성 성공 시 로그 기록
                try:
                    # 전역 변수에서 사용자 ID 가져오기
                    import builtins
                    user_id = getattr(builtins, 'CURRENT_USER_ID', 0)
                    
                    if user_id > 0:
                        # api_client의 로그 기록 함수 호출
                        from api_client import log_distribution_creation
                        success, message = log_distribution_creation(user_id, app_name)
                        
                        if not success:
                            print(f"로그 기록 실패: {message}")
                    else:
                        print("사용자 ID가 없어 로그를 기록할 수 없습니다.")
                except Exception as e:
                    print(f"로그 기록 중 오류 발생: {e}")
                    
            else:
                QMessageBox.warning(
                    self, 
                    "배포용 파일 생성 실패", 
                    result_message + "필요한 파일을 찾을 수 없습니다."
                )
                    
        except Exception as e:
            QMessageBox.warning(self, "오류", f"배포용 파일 처리 중 오류가 발생했습니다: {str(e)}")