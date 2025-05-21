from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                              QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
import os
from api_client import login
from ..components.inputs import ModernLineEdit
from ..components.buttons import ModernButton
from ..styles.colors import COLORS

class LoginScreen(QWidget):
    def __init__(self, on_login_success=None):
        super().__init__()
        self.on_login_success = on_login_success
        
        # 창 설정
        self.setWindowTitle("슈퍼 키오스크 로그인")
        self.resize(400, 500)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # 로고/헤더
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel()
        # 로고 이미지가 있다면 다음 줄의 주석을 해제하고 경로 설정
        # logo_pixmap = QPixmap("path/to/your/logo.png")
        # logo_label.setPixmap(logo_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # 로고 대신 스타일된 텍스트 라벨 사용
        logo_label.setText("SUPER KIOSK")
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
        
        # 초기 포커스 설정
        self.id_input.setFocus()
        
        # 화면 중앙에 위치
        self.center_on_screen()
    
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
        """애니메이션 피드백과 함께 로그인 시도 처리"""
        # 로딩 상태로 버튼 업데이트
        self.login_button.set_loading(True)
        
        # 로그인 정보 가져오기
        login_id = self.id_input.text()
        password = self.pw_input.text()
        
        # 로그인 처리 (원래 코드와 같이 try-except 사용)
        try:
            success, message, user_id = login(login_id, password)
            if success:
                # 로그인 성공 시 사용자 ID를 전역 변수에 저장
                import builtins
                builtins.CURRENT_USER_ID = user_id  # 전역 변수에 사용자 ID 저장
                
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