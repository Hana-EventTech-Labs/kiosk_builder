import requests
import os
import sys
import subprocess
import tempfile
import shutil
from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import QThread, Signal, QTimer


class UpdateChecker(QThread):
    """업데이트 확인을 위한 워커 스레드"""
    update_available = Signal(dict)
    no_update = Signal()
    error_occurred = Signal(str)

    def __init__(self, current_version, github_repo):
        super().__init__()
        self.current_version = current_version
        self.github_repo = github_repo

    def run(self):
        try:
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'SuperKioskBuilder-AutoUpdater'
            }

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')

            if self.is_newer_version(latest_version, self.current_version):
                self.update_available.emit({
                    'version': latest_version,
                    'tag_name': release_data['tag_name'],
                    'name': release_data.get('name', f'Version {latest_version}'),
                    'body': release_data.get('body', '업데이트 내용을 확인할 수 없습니다.'),
                    'download_url': self.get_download_url(release_data),
                    'published_at': release_data.get('published_at', '')
                })
            else:
                self.no_update.emit()

        except Exception as e:
            self.error_occurred.emit(f"업데이트 확인 중 오류 발생: {str(e)}")

    def is_newer_version(self, latest, current):
        """버전 비교 (semantic versioning)"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        try:
            return version_tuple(latest) > version_tuple(current)
        except:
            return False

    def get_download_url(self, release_data):
        """실행 파일 다운로드 URL 찾기"""
        for asset in release_data.get('assets', []):
            if asset['name'].endswith('.exe') and 'builder' in asset['name'].lower():
                return asset['browser_download_url']
        return None


class UpdateDownloader(QThread):
    """업데이트 다운로드를 위한 워커 스레드"""
    progress = Signal(int, int)  # current, total
    finished = Signal(str, bool)  # file_path, success

    def __init__(self, download_url, filename):
        super().__init__()
        self.download_url = download_url
        self.filename = filename
        self.temp_dir = tempfile.mkdtemp()

    def run(self):
        """업데이트 파일 다운로드"""
        try:
            file_path = os.path.join(self.temp_dir, self.filename)

            response = requests.get(self.download_url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        self.progress.emit(downloaded_size, total_size)

            self.finished.emit(file_path, True)

        except Exception as e:
            self.finished.emit(f"다운로드 실패: {str(e)}", False)


class AutoUpdater:
    """자동 업데이트 관리 클래스"""

    def __init__(self, parent_window, current_version="1.0.0", github_repo="Hana-EventTech-Labs/kiosk_builder"):
        self.parent = parent_window
        self.current_version = current_version
        self.github_repo = github_repo
        self.check_timer = QTimer()

    def start_periodic_check(self, interval_hours=24):
        """주기적 업데이트 확인 시작"""
        self.check_timer.timeout.connect(self.check_for_updates)
        self.check_timer.start(interval_hours * 60 * 60 * 1000)
        QTimer.singleShot(5000, self.check_for_updates)

    def check_for_updates(self, show_no_update_message=False):
        """업데이트 확인"""
        self.show_no_update = show_no_update_message

        self.update_checker = UpdateChecker(self.current_version, self.github_repo)
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.no_update.connect(self.on_no_update)
        self.update_checker.error_occurred.connect(self.on_error)
        self.update_checker.start()

    def on_update_available(self, update_info):
        """업데이트가 있을 때 호출"""
        reply = QMessageBox.question(
            self.parent,
            "업데이트 알림",
            f"""🚀 새로운 버전이 있습니다!

현재 버전: {self.current_version}
최신 버전: {update_info['version']}

📋 업데이트 내용:
{update_info['body'][:300]}{'...' if len(update_info['body']) > 300 else ''}

지금 업데이트하시겠습니까?""",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.download_and_install_update(update_info)

    def on_no_update(self):
        """업데이트가 없을 때 호출"""
        if self.show_no_update:
            QMessageBox.information(
                self.parent,
                "업데이트 확인",
                "✅ 현재 최신 버전을 사용 중입니다."
            )

    def on_error(self, error_message):
        """오류 발생 시 호출"""
        if self.show_no_update:
            QMessageBox.warning(
                self.parent,
                "업데이트 확인 실패",
                f"❌ 업데이트 확인에 실패했습니다:\n\n{error_message}"
            )

    def download_and_install_update(self, update_info):
        """업데이트 다운로드 및 설치"""
        if not update_info['download_url']:
            QMessageBox.warning(
                self.parent,
                "업데이트 오류",
                "다운로드 가능한 업데이트 파일을 찾을 수 없습니다."
            )
            return

        self.progress_dialog = QProgressDialog(
            "업데이트를 다운로드하고 있습니다...",
            "취소",
            0, 100,
            self.parent
        )
        self.progress_dialog.setWindowTitle("업데이트 다운로드")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()

        filename = f"super-kiosk-builder-{update_info['version']}.exe"
        self.downloader = UpdateDownloader(update_info['download_url'], filename)
        self.downloader.progress.connect(self.on_download_progress)
        self.downloader.finished.connect(self.on_download_finished)
        self.progress_dialog.canceled.connect(self.downloader.terminate)
        self.downloader.start()

    def on_download_progress(self, current, total):
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_dialog.setValue(percentage)

            current_mb = current / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.progress_dialog.setLabelText(
                f"업데이트를 다운로드하고 있습니다...\n"
                f"📥 {current_mb:.1f}MB / {total_mb:.1f}MB ({percentage}%)"
            )

    def on_download_finished(self, result, success):
        self.progress_dialog.close()

        if success:
            downloaded_file = result

            reply = QMessageBox.question(
                self.parent,
                "업데이트 설치",
                "✅ 다운로드가 완료되었습니다!\n\n"
                "🔄 지금 업데이트를 설치하시겠습니까?\n\n"
                "⚠️ 설치하면 프로그램이 종료되고 새 버전으로 자동 재시작됩니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.install_update(downloaded_file)
        else:
            QMessageBox.critical(
                self.parent,
                "다운로드 실패",
                f"❌ 업데이트 다운로드에 실패했습니다:\n\n{result}"
            )

    def install_update(self, update_file_path):
        """업데이트 설치 (프로세스 종료 로직 강화)"""
        try:
            current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
            current_exe_path = os.path.abspath(current_exe)
            backup_path = current_exe_path + ".backup"

            if os.path.exists(backup_path):
                os.remove(backup_path)

            update_script = self.create_update_script(current_exe_path, update_file_path, backup_path)

            QMessageBox.information(
                self.parent,
                "업데이트 설치 시작",
                "🚀 업데이트 설치를 시작합니다!\n\n"
                "💡 프로그램이 자동으로 종료되고 새 버전으로 재시작됩니다.\n"
                "⚠️ 잠시 후 프로그램이 자동으로 재시작됩니다."
            )

            subprocess.Popen([update_script], shell=True)
            sys.exit(0)

        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "업데이트 설치 실패",
                f"❌ 업데이트 설치 중 오류가 발생했습니다:\n\n{str(e)}"
            )

    def create_update_script(self, current_exe, update_file, backup_path):
        """업데이트 배치 스크립트 생성"""
        script_content = f'''@echo off
chcp 65001 > nul
echo.
echo 🔄 슈퍼 키오스크 빌더 업데이트 설치 중...
echo.

taskkill /f /im super-kiosk-builder.exe 2>nul
taskkill /f /im super-kiosk.exe 2>nul
timeout /t 5 /nobreak > nul

for /d %%i in ("%TEMP%\\_MEI*") do (
    if exist "%%i" (
        echo 삭제 중: %%i
        rmdir /s /q "%%i" 2>nul
    )
)

timeout /t 3 /nobreak > nul

if exist "{current_exe}" (
    move "{current_exe}" "{backup_path}"
    if errorlevel 1 (
        del "{current_exe}" /f /q 2>nul
    )
)

copy "{update_file}" "{current_exe}"
if errorlevel 1 (
    if exist "{backup_path}" (
        move "{backup_path}" "{current_exe}"
    )
    pause
    exit /b 1
)

if exist "{current_exe}" (
    timeout /t 3 /nobreak > nul
    start "" "{current_exe}"
    del "{update_file}" 2>nul
    del "{backup_path}" 2>nul
    timeout /t 2 /nobreak > nul
) else (
    if exist "{backup_path}" (
        move "{backup_path}" "{current_exe}"
        start "" "{current_exe}"
    )
    pause
)

del "%~f0" 2>nul
'''

        script_path = os.path.join(tempfile.gettempdir(), "super_kiosk_updater.bat")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        return script_path
