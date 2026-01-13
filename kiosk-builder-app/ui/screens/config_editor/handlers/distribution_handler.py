from PySide6.QtWidgets import QMessageBox, QDialog, QFileDialog
import os
import sys
import json
import shutil
import subprocess
import requests
from utils.file_handler import get_resources_base_path

# GitHub 저장소 정보
GITHUB_REPO = "Hana-EventTech-Labs/kiosk_builder"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# 파일 이름 설정 (새 파일명이 없으면 기존 파일명으로 fallback)
KIOSK_EXE_NAME = "HanaKiosk.exe"  # 최종 저장될 파일명
BUILDER_EXE_NAME = "SuperKioskBuilder.exe"  # 최종 저장될 파일명


class DistributionHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        self.target_dir = None
        self.app_name = None
        self.online_mode = None
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
                self._set_fallback_release()
                return False

        except requests.exceptions.Timeout:
            print("GitHub API 요청 타임아웃")
            self._set_fallback_release()
            return False

        except Exception as e:
            print(f"최신 릴리즈 정보 가져오기 실패: {e}")
            self._set_fallback_release()
            return False

    def _set_fallback_release(self):
        """기본 릴리즈 정보로 폴백"""
        self.latest_release_tag = "v1.0.2"
        self.latest_release_url = f"https://github.com/{GITHUB_REPO}/releases/download/v1.0.2"

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

            # 6. GitHub에서 파일 다운로드 + 서버 업로드 (온라인 모드)
            from .distribution_progress_dialog import DistributionProgressDialog

            # 온라인 모드 시 basic_tab에서 키오스크 대수와 만료일 가져오기
            kiosk_count = 0
            expired_at = None
            if self.online_mode:
                kiosk_count = self._get_kiosk_count()
                expired_at = self._get_expired_at()

            dialog = DistributionProgressDialog(
                parent=self.main_window,
                github_base_url=self.latest_release_url,
                target_dir=os.path.join(self.target_dir, "bin"),
                online_mode=self.online_mode,
                config=self.main_window.config if self.online_mode else None,
                event_name=self.app_name if self.online_mode else None,
                kiosk_count=kiosk_count,
                expired_at=expired_at,
                resources_dir=os.path.join(get_resources_base_path(), 'resources') if self.online_mode else None
            )

            if dialog.exec() == QDialog.Accepted:
                results = dialog.get_results()
                downloaded_files = results.get('downloaded_files', [])
                failed_downloads = results.get('failed_downloads', [])
                server_result = results.get('server_result', None)
            else:
                # 사용자가 취소한 경우
                downloaded_files = []
                failed_downloads = [KIOSK_EXE_NAME, BUILDER_EXE_NAME]
                server_result = None

            # 7. 리소스 복사
            copied_folders, copied_resource_files = self._copy_resources()

            # 8. 언어별 배경 폴더 확인 및 생성
            self._ensure_language_folders()

            # 9. 결과 표시
            self._show_results(
                created_dirs, downloaded_files, failed_downloads,
                copied_folders, copied_resource_files, auth_copied, server_result
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
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

        # 배포 모드 선택 (온라인/오프라인)
        self.online_mode = self._ask_distribution_mode()
        if self.online_mode is None:
            return False  # 사용자가 취소

        # GitHub 최신 릴리즈 정보 가져오기
        self._get_latest_release_info()

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

    def _ask_distribution_mode(self):
        """배포 모드 선택 (온라인/오프라인)"""
        msg_box = QMessageBox(self.main_window)
        msg_box.setWindowTitle("배포 모드 선택")
        msg_box.setText("배포 모드를 선택해주세요.")
        msg_box.setInformativeText(
            "🌐 온라인 모드:\n"
            "  • 서버에 자동 등록 및 활성화 코드 생성\n"
            "  • 현장에서 활성화 코드 입력으로 자동 설정\n"
            "  • 라이선스 관리 가능\n\n"
            "💾 오프라인 모드:\n"
            "  • 활성화 코드 없이 바로 실행\n"
            "  • 현재 설정이 포함됨\n"
            "  • 독립 실행 (서버 연결 불필요)"
        )

        online_btn = msg_box.addButton("🌐 온라인 모드", QMessageBox.AcceptRole)
        offline_btn = msg_box.addButton("💾 오프라인 모드", QMessageBox.AcceptRole)
        cancel_btn = msg_box.addButton("취소", QMessageBox.RejectRole)

        msg_box.exec()

        clicked = msg_box.clickedButton()
        if clicked == online_btn:
            return True  # 온라인 모드
        elif clicked == offline_btn:
            return False  # 오프라인 모드
        else:
            return None  # 취소

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

        if not os.path.exists(ko_folder):
            os.makedirs(ko_folder, exist_ok=True)
            print(f"background_ko 폴더 생성됨")

        if not os.path.exists(en_folder):
            os.makedirs(en_folder, exist_ok=True)
            print(f"background_en 폴더 생성됨")

        self._create_language_folder_readme()

    def _copy_config_files(self):
        """설정 파일 복사 (온라인/오프라인 모드에 따라 다르게 처리)"""
        target_config_path = os.path.join(self.target_dir, "bin", "config.json")

        if self.online_mode:
            # 온라인 모드: 최소 설정만 포함 (활성화 후 서버에서 다운로드)
            # screen_order는 사용자가 선택한 값 사용
            minimal_config = {
                "app_name": self.main_window.config.get("app_name", "Kiosk"),
                "screen_size": self.main_window.config.get("screen_size", {"width": 1080, "height": 1920}),
                "online_mode": True,
                "require_activation": True,
                "screen_order": self.main_window.config.get("screen_order", [0, 1, 2, 3, 4, 5, 6])
            }
            with open(target_config_path, 'w', encoding='utf-8') as f:
                json.dump(minimal_config, f, ensure_ascii=False, indent=4)
            print("온라인 모드: 최소 설정 파일 생성됨")
        else:
            # 오프라인 모드: 전체 설정 포함
            offline_config = self.main_window.config.copy()
            offline_config["online_mode"] = False
            offline_config["require_activation"] = False
            with open(target_config_path, 'w', encoding='utf-8') as f:
                json.dump(offline_config, f, ensure_ascii=False, indent=4)
            print("오프라인 모드: 전체 설정 파일 복사됨")

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
        base_path = get_resources_base_path()
        resources_path = os.path.join(base_path, "resources")
        font_path = os.path.join(resources_path, "font")
        background_path = os.path.join(resources_path, "background")
        frames_path = os.path.join(resources_path, "frames")

        created_dirs = []

        if not os.path.exists(font_path):
            os.makedirs(font_path, exist_ok=True)
            created_dirs.append("resources/font")

        if not os.path.exists(background_path):
            os.makedirs(background_path, exist_ok=True)
            created_dirs.append("resources/background")

        if not os.path.exists(frames_path):
            os.makedirs(frames_path, exist_ok=True)
            created_dirs.append("resources/frames")

        return created_dirs

    def _copy_resources(self):
        """리소스 폴더 복사"""
        base_path = get_resources_base_path()
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
                    print(f"DLL 파일 {len(dll_files)}개 복사됨")

                if font_files:
                    print(f"폰트 파일 {len(font_files)}개 복사됨")

        return copied_folders, copied_resource_files

    def _copy_resources_recursive(self, source_dir, target_dir):
        """리소스 폴더 재귀 복사"""
        if not os.path.exists(source_dir):
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
                except Exception as e:
                    print(f"파일 복사 실패: {item} - {e}")

        return copied_files

    def _show_results(self, created_dirs, downloaded_files, failed_downloads,
                      copied_folders, copied_resource_files, auth_copied, server_result):
        """결과 표시"""
        app_folder_name = os.path.basename(self.target_dir)
        result_message = f"배포 폴더 '{app_folder_name}'이(가) 생성되었습니다.\n\n"

        # 배포 모드 표시
        if self.online_mode:
            result_message += "🌐 배포 모드: 온라인 (활성화 코드 필요)\n"
            if server_result and server_result.get('success'):
                result_message += f"   ✅ 서버 등록 완료!\n"
                result_message += f"   📋 이벤트 번호: {server_result.get('event_number', 'N/A')}\n"
                codes = server_result.get('activation_codes', [])
                if codes:
                    result_message += f"   🔑 활성화 코드: {codes[0].get('code', 'N/A')}\n"
            else:
                result_message += "   ⚠️ 서버 등록 실패 또는 취소됨\n"
            result_message += "\n"
        else:
            result_message += "💾 배포 모드: 오프라인 (독립 실행)\n"
            result_message += "   • 활성화 없이 바로 실행\n"
            result_message += "   • 현재 설정이 포함됨\n\n"

        # 릴리즈 버전 표시
        if self.latest_release_tag:
            result_message += f"📦 다운로드 버전: {self.latest_release_tag}\n\n"

        if created_dirs:
            result_message += "생성된 폴더:\n- " + "\n- ".join(created_dirs) + "\n\n"

        success_items = []
        failure_items = []

        if downloaded_files:
            success_items.extend(downloaded_files)

        if copied_folders:
            success_items.extend(copied_folders)

        if auth_copied:
            success_items.append("auth_settings.dat (로그인 정보)")

        if success_items:
            result_message += "✅ 성공적으로 복사된 항목:\n"
            result_message += "- " + "\n- ".join(success_items) + "\n\n"

            # 리소스 파일 통계
            dll_files = [f for f in copied_resource_files if f.endswith(".dll")]
            font_files = [f for f in copied_resource_files if f.endswith((".ttf", ".otf"))]
            image_files = [f for f in copied_resource_files if f.endswith((".png", ".jpg", ".jpeg", ".gif", ".mp4"))]

            if dll_files:
                result_message += f"📦 DLL 파일 {len(dll_files)}개\n"
            if font_files:
                result_message += f"🔤 폰트 파일 {len(font_files)}개\n"
            if image_files:
                result_message += f"🖼️ 이미지/동영상 {len(image_files)}개\n"

        if failed_downloads:
            failure_items.extend([f"{f} (다운로드 실패)" for f in failed_downloads])

        if failure_items:
            result_message += "\n⚠️ 실패한 항목:\n"
            result_message += "- " + "\n- ".join(failure_items) + "\n"

        # 폴더 경로
        result_message += f"\n📁 배포 폴더 위치:\n{self.target_dir}"

        # 온라인 모드 시 basic_tab에 활성화 코드 결과 표시
        if self.online_mode:
            try:
                basic_tab = self.main_window.tab_manager.tabs['basic']
                if server_result and server_result.get('success'):
                    codes_text = f"✅ 등록 완료! (이벤트: {server_result.get('event_number', '')})\n"
                    codes_text += f"행사명: {server_result.get('event_name', self.app_name)}\n"
                    codes_text += "-" * 30 + "\n"
                    for code_info in server_result.get('activation_codes', []):
                        codes_text += f"키오스크 {code_info['kiosk_id']}: {code_info['code']}\n"
                    basic_tab.set_activation_result(codes_text)
                elif server_result:
                    error_msg = server_result.get('error', '알 수 없는 오류')
                    basic_tab.set_activation_result(f"❌ 서버 등록 실패\n{error_msg}")
                else:
                    basic_tab.set_activation_result("⚠️ 서버 등록이 취소되었거나 결과를 받지 못했습니다.")
            except Exception as e:
                import logging
                logging.error(f"활성화 코드 결과 표시 실패: {e}")

        # 결과 표시
        if downloaded_files or copied_folders:
            QMessageBox.information(self.main_window, "배포용 파일 생성 완료", result_message)
        else:
            QMessageBox.warning(
                self.main_window,
                "배포용 파일 생성 실패",
                result_message + "\n\n필요한 파일을 다운로드하지 못했습니다."
            )

    def _get_kiosk_count(self):
        """basic_tab에서 키오스크 대수 가져오기"""
        try:
            return self.main_window.tab_manager.tabs['basic'].kiosk_count_spin.value()
        except Exception:
            return 1  # 기본값

    def _get_expired_at(self):
        """basic_tab에서 만료일 가져오기"""
        try:
            dt = self.main_window.tab_manager.tabs['basic'].expire_date_edit.dateTime()
            return dt.toString("yyyy-MM-ddTHH:mm:ss")
        except Exception:
            from datetime import datetime, timedelta
            return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
