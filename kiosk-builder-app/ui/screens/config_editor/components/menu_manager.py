# kiosk-builder-app/ui/screens/config_editor/components/menu_manager.py 수정

from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QAction, QIcon
import os
import copy

class MenuManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.main_window.menuBar()
        
        self._create_file_menu(menubar)
        self._create_account_menu(menubar)
        self._create_help_menu(menubar)

    def _create_file_menu(self, menubar):
        """파일 메뉴 생성"""
        file_menu = menubar.addMenu("파일")
        
        # JSON 내보내기
        export_action = QAction("설정 내보내기...", self.main_window)
        export_action.setStatusTip("현재 설정을 JSON 파일로 저장")
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_config)
        file_menu.addAction(export_action)
        
        # JSON 가져오기
        import_action = QAction("설정 가져오기...", self.main_window)
        import_action.setStatusTip("JSON 파일에서 설정 불러오기")
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._import_config)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # 설정 초기화
        reset_action = QAction("설정 초기화", self.main_window)
        reset_action.setStatusTip("모든 설정을 기본값으로 초기화")
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self._reset_config)
        file_menu.addAction(reset_action)

    def _export_config(self):
        """설정을 JSON 파일로 내보내기"""
        from utils.file_handler import FileHandler
        
        current_config = self.main_window.config
        success = FileHandler.export_config_to_json(self.main_window, current_config)
        
        if success:
            self.main_window.statusBar().showMessage("설정 내보내기가 완료되었습니다.", 3000)

    def _import_config(self):
        """JSON 파일에서 설정 가져오기"""
        from utils.file_handler import FileHandler
        
        imported_config = FileHandler.import_config_from_json(self.main_window)
        
        if imported_config:
            # 디버그 정보
            print(f"메뉴 매니저: {len(imported_config)} 개 설정 항목 가져오기 시작")
            print(f"기존 config ID: {id(self.main_window.config)}")
            print(f"새로운 config ID: {id(imported_config)}")
            
            # 1. ConfigManager의 설정 업데이트
            self.main_window.config_manager.config = imported_config
            
            # 2. 메인 윈도우의 설정 업데이트
            self.main_window.config = imported_config
            
            # 3. 모든 탭에서 config 재설정 (깊은 복사로 안전하게)
            for tab_name, tab in self.main_window.tab_manager.tabs.items():
                if hasattr(tab, 'config'):
                    tab.config = copy.deepcopy(imported_config)
                    print(f"{tab_name} 탭 config 업데이트 완료")
            
            # 4. 모든 탭의 UI 업데이트
            print("모든 탭 UI 업데이트 시작")
            self.main_window.tab_manager.update_all_tabs(imported_config)
            print("모든 탭 UI 업데이트 완료")
            
            # 5. 탭 활성화 상태 업데이트
            self.main_window.tab_manager.update_tab_enabled_states()
            
            # 6. 상태바 메시지
            self.main_window.statusBar().showMessage("설정 가져오기가 완료되었습니다.", 3000)
            
            # 7. 저장 버튼 상태 업데이트
            self.main_window.config_handler_ui.update_save_button_state()
            
            # 8. 강제로 모든 탭 새로고침
            current_tab_index = self.main_window.tab_manager.tab_widget.currentIndex()
            self.main_window.tab_manager.tab_widget.setCurrentIndex(0)
            self.main_window.tab_manager.tab_widget.setCurrentIndex(current_tab_index)
            
            print("설정 가져오기 완료")

    def _reset_config(self):
        """설정을 기본값으로 초기화"""
        reply = QMessageBox.question(
            self.main_window,
            "설정 초기화",
            "모든 설정을 기본값으로 초기화하시겠습니까?\n\n현재 설정은 모두 삭제됩니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 기본 설정으로 초기화
            default_config = self.main_window.config_manager._get_default_config()
            self.main_window.config = default_config
            self.main_window.config_manager.config = default_config
            
            # 모든 탭의 UI 업데이트
            self.main_window.tab_manager.update_all_tabs(default_config)
            
            # 상태바 메시지
            self.main_window.statusBar().showMessage("설정이 기본값으로 초기화되었습니다.", 3000)
            
            # 저장 버튼 상태 업데이트
            self.main_window.config_handler_ui.update_save_button_state()

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
        
        icon_path = "Hana.ico"
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