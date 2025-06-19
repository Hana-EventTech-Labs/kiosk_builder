# kiosk-builder-app/ui/screens/config_editor/components/menu_manager.py 수정

from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QAction, QIcon
import os

class MenuManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.main_window.menuBar()
        
        self._create_account_menu(menubar)
        self._create_help_menu(menubar)

    def _create_account_menu(self, menubar):
        """계정 메뉴 생성"""
        account_menu = menubar.addMenu("계정")
        
        logout_action = QAction("로그아웃", self.main_window)
        logout_action.setStatusTip("다른 계정으로 로그인")
        logout_action.triggered.connect(self._logout)
        account_menu.addAction(logout_action)
        
        account_menu.addSeparator()
        
        exit_action = QAction("종료", self.main_window)
        exit_action.setStatusTip("프로그램 종료")
        exit_action.triggered.connect(self.main_window.close)
        account_menu.addAction(exit_action)

    def _create_help_menu(self, menubar):
        """도움말 메뉴 생성"""
        help_menu = menubar.addMenu("도움말")
        
        # 업데이트 확인 메뉴 제거
        # check_update_action = QAction("업데이트 확인", self.main_window)
        # check_update_action.setStatusTip("수동으로 업데이트 확인")
        # check_update_action.triggered.connect(self._check_for_updates_manually)
        # help_menu.addAction(check_update_action)
        # help_menu.addSeparator()
        
        about_action = QAction("프로그램 정보", self.main_window)
        about_action.setStatusTip("프로그램 정보 보기")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _logout(self):
        """로그아웃 처리"""
        reply = QMessageBox.question(
            self.main_window,
            "로그아웃",
            "정말 로그아웃하시겠습니까?\n다른 계정으로 로그인할 수 있습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.main_window.auth_manager.logout()
            self.main_window.close()
            self._show_login_screen()

    def _show_login_screen(self):
        """로그인 화면 표시"""
        from ui.screens.login_screen import LoginScreen
        
        def show_settings_window():
            from ui.screens.config_editor.main_window import ConfigEditor
            settings_window = ConfigEditor()
            
            icon_path = "Hana.ico"
            if os.path.exists(icon_path):
                settings_window.setWindowIcon(QIcon(icon_path))
            
            settings_window.show()
            global main_window
            main_window = settings_window
        
        login_window = LoginScreen(on_login_success=show_settings_window)
        
        icon_path = "Hana.png"
        if os.path.exists(icon_path):
            login_window.setWindowIcon(QIcon(icon_path))
        
        login_window.show()
        global login_window_ref
        login_window_ref = login_window

    # 업데이트 확인 메서드 제거
    # def _check_for_updates_manually(self):
    #     """수동 업데이트 확인"""
    #     if hasattr(self.main_window, 'auto_updater'):
    #         self.main_window.auto_updater.check_for_updates(show_no_update_message=True)
    #     else:
    #         QMessageBox.warning(
    #             self.main_window,
    #             "업데이트 확인 불가",
    #             "자동 업데이트 시스템이 초기화되지 않았습니다."
    #         )

    def _show_about(self):
        """프로그램 정보 표시"""
        QMessageBox.about(
            self.main_window,
            "프로그램 정보",
            f"""
            <h3>슈퍼 키오스크 빌더</h3>
            <p><b>버전:</b> {self.main_window.current_version}</p>
            <p><b>설명:</b> 키오스크 애플리케이션 설정 도구</p>
            <p><b>개발:</b> HanaLabs</p>
            <p><b>저작권:</b> © 2025 Super Kiosk Builder</p>
            <br>
            <p>이 프로그램은 키오스크 애플리케이션의 화면 설정과<br>
            배포용 파일 생성을 지원합니다.</p>
            """
            # 자동 업데이트 관련 문구 제거
            # <br>
            # <p>🔄 자동 업데이트 기능이 활성화되어 있습니다.</p>
        )