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
        # 배포용 파일 처리
        try:
            import subprocess
            import sys
            
            # 재귀적 복사 함수 추가
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
                app_name = "Kiosk_App"  # 기본 이름
            
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
            
            # "저장" 버튼과 동일한 기능 수행하지만, 외부 config.json에는 저장하지 않음
            # 설정 업데이트 (모든 UI 항목의 값들을 self.config에 업데이트)
            self.update_config_from_tabs()
            
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
            os.makedirs(os.path.join(target_dir, "config"), exist_ok=True)

            # 배포 폴더 내에 config.json 파일 생성
            target_config_path = os.path.join(target_dir, "config", "config.json")
            with open(target_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
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
            
            
            # json-reader.exe 파일 찾기 및 복사
            json_reader_exe = os.path.join(parent_dir, "json-reader.exe")
            super_kiosk_program_copied = False

            if os.path.exists(json_reader_exe):
                # json-reader.exe 파일을 대상 폴더로 복사하면서 이름 변경
                shutil.copy2(json_reader_exe, os.path.join(target_dir, "bin", "super-kiosk-program.exe"))
                super_kiosk_program_copied = True
                print(f"json-reader.exe 파일을 super-kiosk-program.exe로 복사했습니다.")
            else:
                # 다른 경로에서 json-reader.exe 찾기
                possible_paths = [
                    os.path.join(parent_dir, "dist", "json-reader.exe"),
                    os.path.join(parent_dir, "build", "json-reader.exe"),
                    os.path.join(os.path.dirname(parent_dir), "json-reader.exe")
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        shutil.copy2(path, os.path.join(target_dir, "bin", "super-kiosk-program.exe"))
                        super_kiosk_program_copied = True
                        print(f"{path} 파일을 super-kiosk-program.exe로 복사했습니다.")
                        break
            
            # 필요한 파일들 목록
            required_files = [
                {"name": "kiosk_preview.exe", "source": os.path.join(base_path, "kiosk_preview.exe")},
                {"name": "kiosk_print.exe", "source": os.path.join(base_path, "kiosk_print.exe")}
            ]
            
            # 폴더 목록
            required_folders = [
                {"name": "resources", "source": os.path.join(base_path, "resources")}
            ]
            
            # 파일들을 대상 폴더로 복사
            copied_files = []
            missing_files = []
            
            for file_info in required_files:
                source_path = file_info["source"]
                target_path = os.path.join(target_dir, "bin", file_info["name"])
                
                if os.path.exists(source_path):
                    shutil.copy2(source_path, target_path)
                    copied_files.append(file_info["name"])
                else:
                    missing_files.append(file_info["name"])
            
            # 폴더들을 대상 폴더로 복사 (재귀적으로)
            copied_folders = []
            missing_folders = []
            copied_resource_files = []

            for folder_info in required_folders:
                source_path = folder_info["source"]
                # 리소스 폴더를 bin 폴더 안에 복사
                target_path = os.path.join(target_dir, "bin", folder_info["name"])
                
                if os.path.exists(source_path):
                    # 대상 폴더가 존재하면 삭제 후 복사
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                    
                    # 재귀적 복사 함수 사용
                    copied_files_list = copy_resources_recursive(source_path, target_path)
                    if copied_files_list:
                        copied_folders.append(folder_info["name"])
                        copied_resource_files = copied_files_list
                        
                        # DLL과 폰트 파일 확인
                        dll_files = [f for f in copied_files_list if f.endswith(".dll")]
                        font_files = [f for f in copied_files_list if f.endswith((".ttf", ".otf"))]
                        
                        if dll_files:
                            print(f"DLL 파일 {len(dll_files)}개 복사됨: {', '.join(dll_files)}")
                        
                        if font_files:
                            print(f"폰트 파일 {len(font_files)}개 복사됨: {', '.join(font_files)}")
                else:
                    missing_folders.append(folder_info["name"])
            
            # 실행 배치 파일 생성
            batch_path = os.path.join(target_dir, "run_kiosk.bat")
            with open(batch_path, 'w') as f:
                f.write("@echo off\n")
                f.write("cd bin\n")
                f.write("start super-kiosk-program.exe\n")
            
            # 결과 메시지 구성
            result_message = f"배포 폴더 '{app_folder_name}'이(가) 생성되었습니다.\n\n"
            
            # 폴더 생성 메시지 추가
            if created_dirs:
                result_message += "다음 폴더를 자동으로 생성했습니다:\n- " + "\n- ".join(created_dirs) + "\n\n"
            
            if copied_files or copied_folders or super_kiosk_program_copied:
                result_message += "다음 항목이 성공적으로 복사되었습니다:\n\n"
                
                if super_kiosk_program_copied:
                    result_message += "실행 파일:\n- super-kiosk-program.exe\n\n"
                
                if copied_files:
                    result_message += "파일:\n- " + "\n- ".join(copied_files) + "\n\n"
                
                if copied_folders:
                    result_message += "폴더:\n- " + "\n- ".join(copied_folders) + "\n\n"
                    
                    # DLL 및 폰트 파일 정보 추가
                    dll_files = [f for f in copied_resource_files if f.endswith(".dll")]
                    font_files = [f for f in copied_resource_files if f.endswith((".ttf", ".otf"))]
                    
                    if dll_files:
                        result_message += f"DLL 파일 {len(dll_files)}개가 복사되었습니다.\n"
                    
                    if font_files:
                        result_message += f"폰트 파일 {len(font_files)}개가 복사되었습니다.\n\n"
            
            if not super_kiosk_program_copied:
                result_message += "super-kiosk-program.exe 파일을 찾을 수 없습니다. 수동으로 복사해야 합니다.\n\n"
            
            if missing_files or missing_folders:
                result_message += "다음 항목을 찾을 수 없어 복사하지 못했습니다:\n\n"
                
                if missing_files:
                    result_message += "파일:\n- " + "\n- ".join(missing_files) + "\n\n"
                
                if missing_folders:
                    result_message += "폴더:\n- " + "\n- ".join(missing_folders) + "\n\n"
            
            # 사용자에게 결과 알림
            if copied_files or copied_folders or super_kiosk_program_copied:
                QMessageBox.information(
                    self, 
                    "배포용 파일 생성 완료", 
                    result_message
                )
            else:
                QMessageBox.warning(
                    self, 
                    "배포용 파일 생성 실패", 
                    result_message + "필요한 파일을 찾을 수 없습니다."
                )
                    
        except Exception as e:
            QMessageBox.warning(self, "오류", f"배포용 파일 처리 중 오류가 발생했습니다: {str(e)}")