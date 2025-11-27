from PySide6.QtWidgets import QMessageBox, QDialog
import os
import sys
import json
import shutil
import subprocess
import requests
from ..download_progress_dialog import DownloadProgressDialog

# GitHub 저장소 정보
GITHUB_REPO = "Hana-EventTech-Labs/kiosk_builder"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class DistributionHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        self.target_dir = None
        self.app_name = None
        self.latest_release_tag = None
        self.latest_release_url = None

    def _get_latest_release_info(self):
        """GitHub API를 통해 최신 릴리즈 정보 가져오기"""
        try:
            print("GitHub API에서 최신 릴리즈 정보를 가져오는 중...")
            response = requests.get(GITHUB_API_URL, timeout=10)

            if response.status_code == 200:
                release_data = response.json()
                tag_name = release_data.get("tag_name", "v1.0.0")
                self.latest_release_tag = tag_name
                self.latest_release_url = f"https://github.com/{GITHUB_REPO}/releases/download/{tag_name}"
                print(f"최신 릴리즈 버전: {tag_name}")
                return True
            else:
                print(f"GitHub API 응답 오류: {response.status_code}")
                # 기본값으로 fallback
                self.latest_release_tag = "v1.0.0"
                self.latest_release_url = f"https://github.com/{GITHUB_REPO}/releases/download/v1.0.0"
                return False

        except requests.exceptions.Timeout:
            print("GitHub API 요청 타임아웃")
            self.latest_release_tag = "v1.0.0"
            self.latest_release_url = f"https://github.com/{GITHUB_REPO}/releases/download/v1.0.0"
            return False

        except Exception as e:
            print(f"최신 릴리즈 정보 가져오기 실패: {e}")
            self.latest_release_tag = "v1.0.0"
            self.latest_release_url = f"https://github.com/{GITHUB_REPO}/releases/download/v1.0.0"
            return False

    def create_distribution(self):
        """배포용 파일 생성 및 복사"""
        try:
            # 1. 기본 검증 및 준비
            if not self._validate_and_prepare():
                return

            # 2. 폴더 구조 생성
            self._create_directory_structure()

            # 3. 설정 파일 복사
            self._copy_config_files()

            # 4. 인증 파일 처리
            auth_copied = self._handle_auth_files()

            # 5. 리소스 폴더 처리
            created_dirs = self._ensure_resource_directories()

            # 6. 실행 파일 복사
            builder_copied = self._copy_builder_executable()

            # 7. GitHub에서 파일 다운로드
            downloaded_files, failed_downloads = self._download_github_files()

            # 8. 리소스 복사
            copied_folders, copied_resource_files = self._copy_resources()

            # 9. 언어별 배경 폴더 확인 및 생성 (리소스 복사 후 재확인)
            self._ensure_language_folders()

            # 10. 결과 표시
            self._show_results(
                created_dirs, builder_copied, downloaded_files, 
                failed_downloads, copied_folders, copied_resource_files, auth_copied
            )

        except Exception as e:
            QMessageBox.warning(
                self.main_window, 
                "오류", 
                f"배포용 파일 처리 중 오류가 발생했습니다: {str(e)}"
            )

    def _validate_and_prepare(self):
        """기본 검증 및 준비"""
        # 앱 이름 검증
        self.app_name = self.main_window.tab_manager.tabs['basic'].app_name_edit.text()
        if not self.app_name:
            QMessageBox.warning(
                self.main_window,
                "경고",
                "앱 이름을 입력해주세요."
            )
            return False

        # 설정 업데이트
        self.main_window.tab_manager.update_config_from_tabs(self.main_window.config)
        
        # 대상 디렉토리 설정
        app_folder_name = self.app_name.replace(" ", "_").replace(".", "_")
        
        if getattr(sys, 'frozen', False):
            parent_dir = os.path.dirname(sys.executable)
        else:
            parent_dir = os.getcwd()
        
        self.target_dir = os.path.join(parent_dir, app_folder_name)
        
        # 기존 폴더 확인
        return self._check_existing_folder()

    def _check_existing_folder(self):
        """기존 폴더 존재 확인"""
        if os.path.exists(self.target_dir):
            app_folder_name = os.path.basename(self.target_dir)
            reply = QMessageBox.question(
                self.main_window,
                "폴더 이미 존재",
                f"'{app_folder_name}' 폴더가 이미 존재합니다. 내용을 덮어쓰시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return False
            
            # 기존 폴더 내용 삭제
            for item in os.listdir(self.target_dir):
                item_path = os.path.join(self.target_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        
        return True

    def _create_directory_structure(self):
        """디렉토리 구조 생성"""
        os.makedirs(self.target_dir, exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "bin"), exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "bin", "resources", "background"), exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "bin", "resources", "background_ko"), exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "bin", "resources", "background_en"), exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "bin", "resources", "font"), exist_ok=True)
        os.makedirs(os.path.join(self.target_dir, "bin", "resources", "frames"), exist_ok=True)

        # 언어별 폴더에 README 파일 생성
        self._create_language_folder_readme()

    def _create_language_folder_readme(self):
        """언어별 배경 폴더에 README 파일 생성"""
        # 한국어 폴더 README
        ko_readme = """===============================================
한국어 배경화면 폴더
===============================================

이 폴더에 한국어 화면용 배경 이미지를 넣어주세요.

[파일명 규칙]
화면번호.확장자

[화면 번호]
0 = 시작 화면 (Splash)
1 = 카메라 화면
2 = 텍스트 입력 화면
3 = QR 코드 화면
4 = 프레임 선택 화면
5 = 처리 중 화면
6 = 완료 화면

[지원 확장자]
.mp4 (동영상), .gif (애니메이션), .png (이미지), .jpg (이미지)

[예시]
0.png -> 한국어 시작화면 배경
1.jpg -> 한국어 카메라화면 배경

[참고]
파일이 없는 화면은 기본 배경(background 폴더)이 사용됩니다.
"""

        # 영어 폴더 README
        en_readme = """===============================================
English Background Folder
===============================================

Place English screen backgrounds in this folder.

[File Naming]
screen_number.extension

[Screen Numbers]
0 = Splash Screen
1 = Camera Screen
2 = Text Input Screen
3 = QR Code Screen
4 = Frame Selection Screen
5 = Processing Screen
6 = Complete Screen

[Supported Extensions]
.mp4 (video), .gif (animation), .png (image), .jpg (image)

[Examples]
0.png -> English splash background
1.jpg -> English camera background

[Notes]
Screens without files will use default backgrounds (from background folder).
"""

        try:
            ko_path = os.path.join(self.target_dir, "bin", "resources", "background_ko", "README.txt")
            with open(ko_path, 'w', encoding='utf-8') as f:
                f.write(ko_readme)

            en_path = os.path.join(self.target_dir, "bin", "resources", "background_en", "README.txt")
            with open(en_path, 'w', encoding='utf-8') as f:
                f.write(en_readme)
        except Exception as e:
            print(f"README 파일 생성 실패: {e}")

    def _ensure_language_folders(self):
        """언어별 배경 폴더가 존재하는지 확인하고 없으면 생성"""
        resources_target = os.path.join(self.target_dir, "bin", "resources")

        ko_folder = os.path.join(resources_target, "background_ko")
        en_folder = os.path.join(resources_target, "background_en")

        # 폴더가 없으면 생성
        if not os.path.exists(ko_folder):
            os.makedirs(ko_folder, exist_ok=True)
            print(f"background_ko 폴더 생성됨")

        if not os.path.exists(en_folder):
            os.makedirs(en_folder, exist_ok=True)
            print(f"background_en 폴더 생성됨")

        # README 파일이 없으면 생성
        self._create_language_folder_readme()

    def _copy_config_files(self):
        """설정 파일 복사"""
        target_config_path = os.path.join(self.target_dir, "bin", "config.json")
        with open(target_config_path, 'w', encoding='utf-8') as f:
            json.dump(self.main_window.config, f, ensure_ascii=False, indent=4)
        
        # 저장 버튼 상태 업데이트
        self.main_window.config_handler_ui.update_save_button_state()

    def _handle_auth_files(self):
        """인증 파일 처리"""
        if getattr(sys, 'frozen', False):
            parent_dir = os.path.dirname(sys.executable)
        else:
            parent_dir = os.getcwd()
            
        auth_file_path = os.path.join(parent_dir, "auth_settings.dat")
        
        if not os.path.exists(auth_file_path):
            return False

        auth_settings = self.main_window.auth_manager.load_auth_settings()
        
        if not (auth_settings.get("auto_login", False) or auth_settings.get("remember_id", False)):
            return False

        reply = QMessageBox.question(
            self.main_window,
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
        
        if reply == QMessageBox.Yes:
            try:
                target_auth_path = os.path.join(self.target_dir, "bin", "auth_settings.dat")
                shutil.copy2(auth_file_path, target_auth_path)
                print("로그인 정보 파일이 복사되었습니다.")
                return True
            except Exception as e:
                print(f"로그인 정보 파일 복사 실패: {e}")
        
        return False

    def _ensure_resource_directories(self):
        """리소스 디렉토리 확인 및 생성"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.getcwd()
            
        resources_path = os.path.join(base_path, "resources")
        font_path = os.path.join(resources_path, "font")
        background_path = os.path.join(resources_path, "background")
        frames_path = os.path.join(resources_path, "frames")
        
        created_dirs = []
        
        if not os.path.exists(font_path):
            os.makedirs(font_path, exist_ok=True)
            created_dirs.append("resources/font")
            print(f"resources/font 폴더를 생성했습니다: {font_path}")
        
        if not os.path.exists(background_path):
            os.makedirs(background_path, exist_ok=True)
            created_dirs.append("resources/background")
            print(f"resources/background 폴더를 생성했습니다: {background_path}")
        
        if not os.path.exists(frames_path):
            os.makedirs(frames_path, exist_ok=True)
            created_dirs.append("resources/frames")
            print(f"resources/frames 폴더를 생성했습니다: {frames_path}")
        
        return created_dirs

    def _copy_builder_executable(self):
        """빌더 실행 파일 복사"""
        if getattr(sys, 'frozen', False):
            parent_dir = os.path.dirname(sys.executable)
        else:
            parent_dir = os.getcwd()
            
        builder_exe = os.path.join(parent_dir, "super-kiosk-builder.exe")
        
        if not os.path.exists(builder_exe):
            # 다른 경로에서 찾기
            possible_paths = [
                os.path.join(parent_dir, "dist", "super-kiosk-builder.exe"),
                os.path.join(parent_dir, "build", "super-kiosk-builder.exe"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    builder_exe = path
                    break
            else:
                return False

        try:
            target_builder_path = os.path.join(self.target_dir, "bin", "super-kiosk-builder.exe")
            
            # robocopy 시도
            try:
                result = subprocess.run([
                    'robocopy', 
                    os.path.dirname(builder_exe), 
                    os.path.join(self.target_dir, "bin"), 
                    os.path.basename(builder_exe),
                    '/R:3', '/W:1'
                ], capture_output=True, text=True)
                
                if os.path.exists(target_builder_path):
                    print("super-kiosk-builder.exe 복사 완료 (robocopy 사용)")
                    return True
            except:
                pass
            
            # 일반 복사 시도
            import time
            time.sleep(0.1)
            shutil.copy2(builder_exe, target_builder_path)
            print("super-kiosk-builder.exe 복사 완료 (일반 복사)")
            return True
            
        except Exception as e:
            print(f"super-kiosk-builder.exe 복사 실패: {e}")
            return False

    def _download_github_files(self):
        """GitHub에서 파일 다운로드 또는 로컬에서 복사"""
        downloaded_files = []
        failed_downloads = []

        # GitHub에서 다운로드할 파일 목록
        files_to_download = [
            {"name": "super-kiosk.exe"},
            {"name": "super-kiosk-builder.exe"}
        ]

        # GitHub API를 통해 최신 릴리즈 정보 가져오기
        self._get_latest_release_info()

        # GitHub 릴리즈 URL 설정 (최신 버전 자동 감지)
        github_base_url = self.latest_release_url
        print(f"다운로드 URL: {github_base_url}")
        
        # 다운로드 대화상자 표시
        try:
            from ..download_progress_dialog import DownloadProgressDialog
            
            dialog = DownloadProgressDialog(
                parent=self.main_window,
                github_base_url=github_base_url,
                files_to_download=files_to_download,
                target_dir=os.path.join(self.target_dir, "bin")
            )
            
            if dialog.exec() == QDialog.Accepted:
                results = dialog.get_results()
                
                # 결과 처리
                for filename, result in results.items():
                    if result['success']:
                        if filename == "super-kiosk.exe":
                            # 앱 이름으로 파일명 변경
                            safe_app_name = self.app_name.replace(" ", "_").replace(".", "_").replace("/", "_").replace("\\", "_")
                            new_filename = f"{safe_app_name}.exe"
                            
                            original_path = os.path.join(self.target_dir, "bin", filename)
                            new_path = os.path.join(self.target_dir, "bin", new_filename)
                            
                            # 파일명 변경
                            if os.path.exists(original_path):
                                try:
                                    shutil.move(original_path, new_path)
                                    downloaded_files.append(f"{new_filename} (GitHub에서 다운로드 완료, 크기: {result['size']:,} bytes)")
                                except Exception as e:
                                    downloaded_files.append(f"{filename} (GitHub에서 다운로드 완료, 이름 변경 실패: {e})")
                            else:
                                downloaded_files.append(f"{filename} (GitHub에서 다운로드 완료)")
                        
                        elif filename == "super-kiosk-builder.exe":
                            # 빌더는 파일명 그대로 유지
                            downloaded_files.append(f"{filename} (GitHub에서 다운로드 완료, 크기: {result['size']:,} bytes)")
                        
                    else:
                        failed_downloads.append(filename)
                
                # GitHub 다운로드가 성공한 경우 로컬 검색 건너뛰기
                if len(downloaded_files) == len(files_to_download):
                    print("GitHub에서 모든 파일을 성공적으로 다운로드했습니다.")
                    return downloaded_files, []
            else:
                # 사용자가 다운로드를 취소한 경우
                failed_downloads = ["super-kiosk.exe", "super-kiosk-builder.exe"]
        
        except Exception as e:
            print(f"GitHub 다운로드 중 오류 발생: {e}")
            failed_downloads = ["super-kiosk.exe", "super-kiosk-builder.exe"]

        # GitHub 다운로드 실패 시 로컬에서 찾기
        if failed_downloads:
            print("GitHub 다운로드 실패 또는 취소, 로컬에서 파일을 찾습니다...")
            
            if getattr(sys, 'frozen', False):
                parent_dir = os.path.dirname(sys.executable)
            else:
                parent_dir = os.getcwd()
            
            remaining_failures = []
            
            # super-kiosk.exe 로컬에서 찾기
            if "super-kiosk.exe" in str(failed_downloads):
                kiosk_possible_paths = [
                    os.path.join(parent_dir, "super-kiosk.exe"),
                    os.path.join(parent_dir, "..", "super-kiosk.exe"),
                    os.path.join(parent_dir, "dist", "super-kiosk.exe"),
                    os.path.join(parent_dir, "..", "dist", "super-kiosk.exe"),
                ]
                
                kiosk_exe_found = False
                for source_path in kiosk_possible_paths:
                    if os.path.exists(source_path):
                        try:
                            safe_app_name = self.app_name.replace(" ", "_").replace(".", "_").replace("/", "_").replace("\\", "_")
                            new_filename = f"{safe_app_name}.exe"
                            target_path = os.path.join(self.target_dir, "bin", new_filename)
                            
                            shutil.copy2(source_path, target_path)
                            file_size = os.path.getsize(target_path)
                            
                            downloaded_files.append(f"{new_filename} (로컬에서 복사됨, 크기: {file_size:,} bytes)")
                            kiosk_exe_found = True
                            break
                            
                        except Exception as e:
                            print(f"super-kiosk.exe 복사 실패: {e}")
                            continue
                
                if not kiosk_exe_found:
                    remaining_failures.append("super-kiosk.exe")
                    print("super-kiosk.exe를 찾을 수 없습니다.")
            
            # super-kiosk-builder.exe 로컬에서 찾기
            if "super-kiosk-builder.exe" in str(failed_downloads):
                builder_possible_paths = [
                    os.path.join(parent_dir, "super-kiosk-builder.exe"),
                    os.path.join(parent_dir, "..", "super-kiosk-builder.exe"),
                    os.path.join(parent_dir, "dist", "super-kiosk-builder.exe"),
                    os.path.join(parent_dir, "..", "dist", "super-kiosk-builder.exe"),
                ]
                
                builder_exe_found = False
                for source_path in builder_possible_paths:
                    if os.path.exists(source_path):
                        try:
                            target_path = os.path.join(self.target_dir, "bin", "super-kiosk-builder.exe")
                            
                            shutil.copy2(source_path, target_path)
                            file_size = os.path.getsize(target_path)
                            
                            downloaded_files.append(f"super-kiosk-builder.exe (로컬에서 복사됨, 크기: {file_size:,} bytes)")
                            builder_exe_found = True
                            break
                            
                        except Exception as e:
                            print(f"super-kiosk-builder.exe 복사 실패: {e}")
                            continue
                
                if not builder_exe_found:
                    remaining_failures.append("super-kiosk-builder.exe")
                    print("super-kiosk-builder.exe를 찾을 수 없습니다.")
            
            failed_downloads = remaining_failures

        return downloaded_files, failed_downloads


    def _copy_builder_executable(self):
        """빌더 실행 파일 복사 (GitHub 다운로드가 실패한 경우만)"""
        # GitHub 다운로드에서 처리하므로 이 메서드는 더 이상 사용하지 않음
        # 호환성을 위해 항상 True 반환
        return True


    def _copy_resources(self):
        """리소스 폴더 복사"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.getcwd()
            
        resources_source = os.path.join(base_path, "resources")
        resources_target = os.path.join(self.target_dir, "bin", "resources")
        
        copied_folders = []
        copied_resource_files = []

        if os.path.exists(resources_source):
            if os.path.exists(resources_target):
                shutil.rmtree(resources_target)
            
            copied_files_list = self._copy_resources_recursive(resources_source, resources_target)
            if copied_files_list:
                copied_folders.append("resources")
                copied_resource_files = copied_files_list
                
                dll_files = [f for f in copied_files_list if f.endswith(".dll")]
                font_files = [f for f in copied_files_list if f.endswith((".ttf", ".otf"))]
                
                if dll_files:
                    print(f"DLL 파일 {len(dll_files)}개 복사됨: {', '.join(dll_files)}")
                
                if font_files:
                    print(f"폰트 파일 {len(font_files)}개 복사됨: {', '.join(font_files)}")

        return copied_folders, copied_resource_files

    def _copy_resources_recursive(self, source_dir, target_dir):
        """리소스 폴더 재귀 복사"""
        if not os.path.exists(source_dir):
            print(f"소스 폴더를 찾을 수 없음: {source_dir}")
            return []
        
        copied_files = []
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        for item in os.listdir(source_dir):
            source_item = os.path.join(source_dir, item)
            target_item = os.path.join(target_dir, item)
            
            if os.path.isdir(source_item):
                sub_copied = self._copy_resources_recursive(source_item, target_item)
                copied_files.extend(sub_copied)
            else:
                try:
                    shutil.copy2(source_item, target_item)
                    copied_files.append(os.path.relpath(target_item, target_dir))
                    print(f"파일 복사됨: {os.path.relpath(target_item, target_dir)}")
                except Exception as e:
                    print(f"파일 복사 실패: {item} - {e}")

        return copied_files

    def _show_results(self, created_dirs, builder_copied, downloaded_files,
                      failed_downloads, copied_folders, copied_resource_files, auth_copied):
        """결과 표시"""
        app_folder_name = os.path.basename(self.target_dir)
        result_message = f"배포 폴더 '{app_folder_name}'이(가) 생성되었습니다.\n\n"

        # 다운로드한 버전 표시
        if self.latest_release_tag:
            result_message += f"📦 다운로드 버전: {self.latest_release_tag}\n\n"
        
        if created_dirs:
            result_message += "다음 폴더를 자동으로 생성했습니다:\n- " + "\n- ".join(created_dirs) + "\n\n"
        
        success_items = []
        
        if builder_copied:
            success_items.append("super-kiosk-builder.exe (설정 프로그램)")
        
        if downloaded_files:
            success_items.extend(downloaded_files)
        
        if copied_folders:
            success_items.extend(copied_folders)
        
        if auth_copied:
            success_items.append("auth_settings.dat (로그인 정보)")
        
        if success_items:
            result_message += "다음 항목이 성공적으로 복사되었습니다:\n\n"
            result_message += "- " + "\n- ".join(success_items) + "\n\n"
            
            dll_files = [f for f in copied_resource_files if f.endswith(".dll")]
            font_files = [f for f in copied_resource_files if f.endswith((".ttf", ".otf"))]
            
            if dll_files:
                result_message += f"DLL 파일 {len(dll_files)}개가 복사되었습니다.\n"
            
            if font_files:
                result_message += f"폰트 파일 {len(font_files)}개가 복사되었습니다.\n\n"
            
            if auth_copied:
                result_message += "📋 로그인 정보가 포함되어 자동 로그인이 가능합니다.\n"
            else:
                result_message += "🔐 로그인 정보가 포함되지 않아 보안상 안전합니다.\n"
        
        failure_items = []
        
        if not builder_copied:
            failure_items.append("super-kiosk-builder.exe (설정 프로그램)")
        
        if failed_downloads:
            failure_items.extend([f"{f} (다운로드 실패)" for f in failed_downloads])
        
        if failure_items:
            result_message += "다음 항목을 찾을 수 없어 복사하지 못했습니다:\n\n"
            result_message += "- " + "\n- ".join(failure_items) + "\n\n"
        
        if success_items:
            QMessageBox.information(self.main_window, "배포용 파일 생성 완료", result_message)
            self._log_distribution_creation()
        else:
            QMessageBox.warning(
                self.main_window, 
                "배포용 파일 생성 실패", 
                result_message + "필요한 파일을 찾을 수 없습니다."
            )

    def _log_distribution_creation(self):
        """배포 생성 로그 기록"""
        try:
            import builtins
            user_id = getattr(builtins, 'CURRENT_USER_ID', 0)
            
            if user_id > 0:
                from api_client import log_distribution_creation
                success, message = log_distribution_creation(user_id, self.app_name)
                
                if not success:
                    print(f"로그 기록 실패: {message}")
            else:
                print("사용자 ID가 없어 로그를 기록할 수 없습니다.")
        except Exception as e:
            print(f"로그 기록 중 오류 발생: {e}")