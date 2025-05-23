from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                              QLineEdit, QMessageBox, QCheckBox, QPushButton)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QGuiApplication, QIcon
import os
from utils.auth_manager import AuthManager
from ..components.inputs import ModernLineEdit
from ..components.buttons import ModernButton
from ..styles.colors import COLORS

class LoginScreen(QWidget):
    def __init__(self, on_login_success=None):
        super().__init__()
        self.on_login_success = on_login_success
        self.auth_manager = AuthManager()
        
        # 창 설정
        self.setWindowTitle("슈퍼 키오스크 로그인")
        self.resize(450, 600)
        
        # 아이콘 설정
        icon_path = "Hana.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        
        self.init_ui()
        self.load_saved_settings()
        
        # 자동 로그인 체크 시도
        QTimer.singleShot(100, self.check_auto_login)
        
        # 화면 중앙에 위치
        self.center_on_screen()
    
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # 로고/헤더
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel("SUPER KIOSK")
        logo_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        logo_label.setFont(font)
        logo_label.setStyleSheet(f"color: {COLORS['primary']}; margin-bottom: 20px;")
        
        header_layout.addWidget(logo_label)
        
        welcome_label = QLabel("환영합니다")
        welcome_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        welcome_label.setFont(font)
        welcome_label.setStyleSheet(f"color: {COLORS['text_dark']}; margin-bottom: 10px;")
        
        login_desc_label = QLabel("계정에 로그인하여 시작하세요")
        login_desc_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        login_desc_label.setFont(font)
        login_desc_label.setStyleSheet(f"color: {COLORS['text_muted']}; margin-bottom: 30px;")
        
        header_layout.addWidget(welcome_label)
        header_layout.addWidget(login_desc_label)
        
        main_layout.addLayout(header_layout)
        
        # 폼 영역
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.NoFrame)
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background']};
                border-radius: 10px;
            }}
        """)
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        
        # 아이디 필드
        username_label = QLabel("아이디")
        username_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 11px;")
        form_layout.addWidget(username_label)
        
        # 아이콘 경로가 존재하는지 확인
        icon_path = "resources/icons/user_icon.png"
        if not os.path.exists(icon_path):
            icon_path = None
            
        self.id_input = ModernLineEdit(placeholder="아이디를 입력하세요", icon_path=icon_path)
        form_layout.addWidget(self.id_input)
        
        # 비밀번호 필드
        password_label = QLabel("비밀번호")
        password_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 11px;")
        form_layout.addWidget(password_label)
        
        # 아이콘 경로가 존재하는지 확인
        icon_path = "resources/icons/lock_icon.png"
        if not os.path.exists(icon_path):
            icon_path = None
            
        self.pw_input = ModernLineEdit(placeholder="비밀번호를 입력하세요", icon_path=icon_path)
        self.pw_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.pw_input)
        
        # 체크박스 영역
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(8)
        
        # 아이디 저장 체크박스
        self.remember_id_checkbox = QCheckBox("아이디 저장")
        self.remember_id_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_dark']};
                font-size: 11px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid {COLORS['border']};
                background-color: {COLORS['background_light']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['primary']};
                border-radius: 3px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
        """)
        checkbox_layout.addWidget(self.remember_id_checkbox)
        
        # 자동 로그인 체크박스
        self.auto_login_checkbox = QCheckBox("자동 로그인")
        self.auto_login_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_dark']};
                font-size: 11px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid {COLORS['border']};
                background-color: {COLORS['background_light']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['primary']};
                border-radius: 3px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
        """)
        checkbox_layout.addWidget(self.auto_login_checkbox)
        
        form_layout.addLayout(checkbox_layout)
        
        # 공간 추가
        form_layout.addSpacing(20)
        
        # 로그인 버튼
        self.login_button = ModernButton("로그인")
        self.login_button.clicked.connect(self.attempt_login)
        form_layout.addWidget(self.login_button)
        
        main_layout.addWidget(form_frame)
        
        # 푸터 추가
        footer_label = QLabel("© 2025 Super Kiosk Builder")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; margin-top: 20px;")
        main_layout.addWidget(footer_label)
        
        self.setLayout(main_layout)
        
        # Enter 키 연결
        self.id_input.returnPressed.connect(self.focus_password)
        self.pw_input.returnPressed.connect(self.attempt_login)
        
        # 체크박스 상태 변경 연결
        self.auto_login_checkbox.stateChanged.connect(self.on_auto_login_changed)
        
        # 초기 포커스 설정
        self.id_input.setFocus()
    
    def on_auto_login_changed(self, state):
        """자동 로그인 체크박스 상태 변경 시"""
        if state == Qt.Checked:
            # 자동 로그인 체크 시 아이디 저장도 자동으로 체크
            self.remember_id_checkbox.setChecked(True)
    
    def load_saved_settings(self):
        """저장된 인증 설정 불러오기"""
        auth_settings = self.auth_manager.load_auth_settings()
        
        if auth_settings["login_id"]:
            self.id_input.setText(auth_settings["login_id"])
        
        self.remember_id_checkbox.setChecked(auth_settings["remember_id"])
        self.auto_login_checkbox.setChecked(auth_settings["auto_login"])
        
        # 자동 로그인이 설정되어 있으면 비밀번호도 설정
        if auth_settings["auto_login"] and auth_settings["password"]:
            self.pw_input.setText(auth_settings["password"])
    
    def check_auto_login(self):
        """자동 로그인 체크"""
        if self.auto_login_checkbox.isChecked():
            success, message, user_id = self.auth_manager.attempt_auto_login()
            if success:
                self.close()
                if self.on_login_success:
                    self.on_login_success()
                return
            else:
                # 자동 로그인 실패 시 체크박스 해제
                self.auto_login_checkbox.setChecked(False)
                if "자동 로그인 설정이 비활성화" not in message:
                    self.show_error_message("자동 로그인 실패", message)
    
    def center_on_screen(self):
        """화면 중앙에 창 위치시키기"""
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def focus_password(self):
        """아이디에서 Enter 키를 누르면 비밀번호 필드로 포커스 이동"""
        self.pw_input.setFocus()
    
    def attempt_login(self):
        """로그인 시도 처리"""
        # 로딩 상태로 버튼 업데이트
        self.login_button.set_loading(True)
        
        # 로그인 정보 가져오기
        login_id = self.id_input.text()
        password = self.pw_input.text()
        
        # 입력 검증
        if not login_id.strip():
            self.show_error_message("입력 오류", "아이디를 입력해주세요.")
            self.login_button.set_loading(False)
            return
            
        if not password.strip():
            self.show_error_message("입력 오류", "비밀번호를 입력해주세요.")
            self.login_button.set_loading(False)
            return
        
        # 로그인 처리
        try:
            success, message, user_id = self.auth_manager.validate_credentials(login_id, password)
            if success:
                # 로그인 성공 시 설정 저장
                self.auth_manager.save_auth_settings(
                    login_id=login_id,
                    password=password,
                    remember_id=self.remember_id_checkbox.isChecked(),
                    auto_login=self.auto_login_checkbox.isChecked()
                )
                
                # 로그인 성공 시 사용자 ID를 전역 변수에 저장
                import builtins
                builtins.CURRENT_USER_ID = user_id
                
                self.close()
                if self.on_login_success:
                    self.on_login_success()
            else:
                self.show_error_message("로그인 실패", message)
                # 버튼 상태 초기화
                self.login_button.set_loading(False)
        except Exception as e:
            self.show_error_message("오류", f"로그인 중 예외 발생: {e}")
            # 버튼 상태 초기화
            self.login_button.set_loading(False)
    
    def show_error_message(self, title, message):
        """스타일이 적용된 오류 메시지 표시"""
        error_box = QMessageBox(self)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.setIcon(QMessageBox.Warning)
        error_box.setStandardButtons(QMessageBox.Ok)
        
        # 오류 메시지 박스에도 아이콘 적용
        icon_path = "Hana.png"
        if os.path.exists(icon_path):
            error_box.setWindowIcon(QIcon(icon_path))
        
        # 메시지 박스에 커스텀 스타일 적용
        error_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['background']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {COLORS['text_dark']};
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_light']};
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
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
        
        error_box.exec_()