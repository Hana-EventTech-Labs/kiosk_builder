from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
import json
import copy
import os
import shutil
from utils.config_handler import ConfigHandler
from .basic_tab import BasicTab
from .splash_tab import SplashTab
from .capture_tab import CaptureTab
from .keyboard_tab import KeyboardTab
from .qr_tab import QRTab
from .processing_tab import ProcessingTab
from .complete_tab import CompleteTab

class ConfigEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_handler = ConfigHandler()
        self.config = copy.deepcopy(self.config_handler.config)
        
        self.init_ui()
        
        # config.json 파일 존재 여부에 따라 저장 버튼 상태 설정
        self.update_save_button_state()
        
    def init_ui(self):
        self.setWindowTitle("슈퍼 키오스크 프로그램")
        self.setMinimumSize(800, 600)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 탭 생성
        self.basic_tab = BasicTab(self.config)
        self.tab_widget.addTab(self.basic_tab, "기본 설정")
        
        self.splash_tab = SplashTab(self.config)
        self.tab_widget.addTab(self.splash_tab, "스플래쉬 화면")
        
        self.capture_tab = CaptureTab(self.config)
        self.tab_widget.addTab(self.capture_tab, "촬영 화면")
        
        self.keyboard_tab = KeyboardTab(self.config)
        self.tab_widget.addTab(self.keyboard_tab, "키보드 화면")
        
        self.qr_tab = QRTab(self.config)
        self.tab_widget.addTab(self.qr_tab, "QR코드 화면")
        
        self.processing_tab = ProcessingTab(self.config)
        self.tab_widget.addTab(self.processing_tab, "발급중 화면")
        
        self.complete_tab = CompleteTab(self.config)
        self.tab_widget.addTab(self.complete_tab, "발급완료 화면")
        
        # 화면 순서에 따라 탭 활성화/비활성화 설정
        self.update_tab_enabled_states()
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # 배포용 생성 버튼
        build_button = QPushButton("배포용 생성")
        build_button.clicked.connect(self.create_distribution)
        button_layout.addWidget(build_button)
        
        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
                
        # 다시 로드 버튼
        reload_button = QPushButton("다시 로드")
        reload_button.clicked.connect(self.reload_config)
        button_layout.addWidget(reload_button)
        
    def update_tab_enabled_states(self):
        """현재 screen_order 설정에 따라 탭 활성화/비활성화 상태를 업데이트"""
        try:
            # 화면 순서 가져오기 - 기본 탭에서 화면 순서 텍스트를 가져옴
            screen_order_text = self.basic_tab.screen_order_edit.text()
            screen_order = [int(x.strip()) for x in screen_order_text.split(",")]
            
            # 탭 인덱스 매핑
            tab_indices = {
                0: 1,  # 화면 타입 0 (스플래쉬) -> 탭 인덱스 1
                1: 2,  # 화면 타입 1 (촬영) -> 탭 인덱스 2
                2: 3,  # 화면 타입 2 (키보드) -> 탭 인덱스 3
                3: 4,  # 화면 타입 3 (QR코드) -> 탭 인덱스 4
                4: 5,  # 화면 타입 4 (발급중) -> 탭 인덱스 5
                5: 6   # 화면 타입 5 (발급완료) -> 탭 인덱스 6
            }
            
            # 모든 화면 탭 비활성화
            for i in range(1, 7):  # 1부터 6까지 (기본 설정 탭 제외)
                self.tab_widget.setTabEnabled(i, False)
            
            # screen_order에 있는 탭만 활성화
            for screen_type in screen_order:
                if 0 <= screen_type <= 5:  # 유효한 화면 타입인지 확인
                    tab_index = tab_indices.get(screen_type)
                    if tab_index is not None:
                        self.tab_widget.setTabEnabled(tab_index, True)
                        
            # 탭 활성화 상태에 따라 시각적 표시 업데이트
            for i in range(1, 7):
                tab_text = self.tab_widget.tabText(i)
                if not self.tab_widget.isTabEnabled(i):
                    if not tab_text.startswith("[비활성] "):
                        self.tab_widget.setTabText(i, f"[비활성] {tab_text}")
                else:
                    if tab_text.startswith("[비활성] "):
                        self.tab_widget.setTabText(i, tab_text[6:])
                        
        except ValueError:
            # 숫자로 변환할 수 없는 값이 있으면 모든 탭 활성화
            for i in range(1, 7):
                self.tab_widget.setTabEnabled(i, True)
                tab_text = self.tab_widget.tabText(i)
                if tab_text.startswith("[비활성] "):
                    self.tab_widget.setTabText(i, tab_text[6:])
    
    def save_config(self):
        # 각 탭에서 설정 값 가져오기
        self.update_config_from_tabs()
        
        # 텍스트 항목의 폰트 파일 존재 여부 확인
        missing_fonts = self.check_missing_fonts()
        
        if missing_fonts:
            error_msg = "다음 폰트 파일을 찾을 수 없습니다:\n\n" + "\n".join(missing_fonts)
            QMessageBox.warning(self, "폰트 파일 누락", error_msg)
            return
        
        # 설정 저장
        if self.config_handler.save_config(self.config):
            QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
            # 저장 버튼 상태 업데이트
            self.update_save_button_state()
        else:
            QMessageBox.warning(self, "저장 실패", "설정 저장 중 오류가 발생했습니다.")
    
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
        QMessageBox.information(self, "설정 로드", "설정이 다시 로드되었습니다.")
    
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
    
    def create_distribution(self):
        """배포용 파일 생성 및 복사"""
        try:
            import sys
            
            # 설정 업데이트
            self.update_config_from_tabs()
            
            # 앱 이름으로 폴더 생성
            app_name = self.basic_tab.app_name_edit.text()
            if not app_name:
                app_name = "Kiosk_App"  # 기본 이름
            
            # 특수문자 및 공백 처리
            app_folder_name = app_name.replace(" ", "_").replace(".", "_")
            
            # 현재 실행 파일 경로 확인
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
            os.makedirs(os.path.join(target_dir, "resources", "background"), exist_ok=True)
            os.makedirs(os.path.join(target_dir, "resources", "font"), exist_ok=True)
            os.makedirs(os.path.join(target_dir, "config"), exist_ok=True)
            
            # 설정 파일 저장
            config_path = os.path.join(target_dir, "config", "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            # 실행 파일 복사
            exe_files = ["kiosk_preview.exe", "kiosk_print.exe"]
            for exe_file in exe_files:
                source_path = os.path.join(base_path, exe_file)
                if os.path.exists(source_path):
                    shutil.copy2(source_path, os.path.join(target_dir, "bin", exe_file))
                    print(f"복사 완료: {exe_file}")
                else:
                    print(f"파일을 찾을 수 없음: {source_path}")
            
            # 메인 실행 파일(json-reader.exe)을 bin 폴더에 super-kiosk-program.exe로 복사
            if getattr(sys, 'frozen', False):
                # 패키징된 경우 현재 실행 파일 복사
                shutil.copy2(sys.executable, os.path.join(target_dir, "bin", "super-kiosk-program.exe"))
            
            # 리소스 폴더 복사
            resource_src = os.path.join(base_path, "resources")
            resource_dest = os.path.join(target_dir, "resources")
            
            # 배경 이미지 복사
            bg_src = os.path.join(resource_src, "background")
            bg_dest = os.path.join(resource_dest, "background")
            if os.path.exists(bg_src):
                for file in os.listdir(bg_src):
                    if file.endswith((".jpg", ".jpeg", ".png", ".bmp")):
                        shutil.copy2(os.path.join(bg_src, file), os.path.join(bg_dest, file))
            
            # 폰트 파일 복사
            font_src = os.path.join(resource_src, "font")
            font_dest = os.path.join(resource_dest, "font")
            if os.path.exists(font_src):
                for file in os.listdir(font_src):
                    if file.endswith((".ttf", ".otf")):
                        shutil.copy2(os.path.join(font_src, file), os.path.join(font_dest, file))
            
            # 실행 배치 파일 생성
            batch_path = os.path.join(target_dir, "run_kiosk.bat")
            with open(batch_path, 'w') as f:
                f.write("@echo off\n")
                f.write("cd bin\n")
                f.write("start super-kiosk-program.exe\n")
            
            # 성공 메시지 표시
            QMessageBox.information(
                self, 
                "배포 완료", 
                f"배포 패키지가 '{app_folder_name}' 폴더에 생성되었습니다.\n\n"
                f"폴더 구조:\n"
                f"- bin/ (실행 파일)\n"
                f"- resources/ (리소스 파일)\n"
                f"- config/ (설정 파일)\n\n"
                f"실행 방법: {app_folder_name}/run_kiosk.bat 파일을 실행하세요."
            )
            
        except Exception as e:
            QMessageBox.warning(self, "오류", f"배포용 파일 처리 중 오류가 발생했습니다: {str(e)}")