"""
배포용 생성 통합 진행률 다이얼로그
- GitHub에서 실행 파일 다운로드
- 온라인 모드 시 서버에 이벤트 등록 및 리소스 업로드
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QProgressBar, QTextEdit, QGroupBox)
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QFont
import requests
import os
from ui.styles.colors import COLORS

# 파일 이름 설정 (새 파일명 → 기존 파일명 순으로 시도)
KIOSK_EXE_NAMES = ["HanaKiosk.exe", "super-kiosk.exe"]  # 우선순위 순
BUILDER_EXE_NAMES = ["SuperKioskBuilder.exe", "super-kiosk-builder.exe"]  # 우선순위 순


class DistributionWorker(QThread):
    """다운로드 및 서버 업로드 작업을 처리하는 워커 스레드"""
    progress = Signal(str, int, int)  # phase, current, total
    log_message = Signal(str)
    phase_changed = Signal(str)  # 단계 변경 알림
    all_finished = Signal(dict)  # 전체 완료 시 결과 전달

    def __init__(self, github_base_url, target_dir, online_mode=False,
                 config=None, event_name=None, kiosk_count=1, resources_dir=None):
        super().__init__()
        self.github_base_url = github_base_url
        self.target_dir = target_dir
        self.online_mode = online_mode
        self.config = config
        self.event_name = event_name
        self.kiosk_count = kiosk_count
        self.resources_dir = resources_dir

        self.results = {
            'downloaded_files': [],
            'failed_downloads': [],
            'server_result': None
        }

    def run(self):
        """작업 실행"""
        try:
            # Phase 1: GitHub에서 파일 다운로드
            self.phase_changed.emit("download")
            self._download_files()

            # Phase 2: 온라인 모드인 경우 서버에 업로드
            if self.online_mode:
                self.phase_changed.emit("upload")
                self._upload_to_server()

            self.log_message.emit("\n✅ 모든 작업이 완료되었습니다.")

        except Exception as e:
            self.log_message.emit(f"\n❌ 오류 발생: {str(e)}")

        finally:
            self.all_finished.emit(self.results)

    def _download_files(self):
        """GitHub에서 파일 다운로드 (여러 파일명 시도)"""
        files_to_download = [
            {"names": KIOSK_EXE_NAMES, "target_name": "HanaKiosk.exe", "description": "키오스크 실행 파일"},
            {"names": BUILDER_EXE_NAMES, "target_name": "SuperKioskBuilder.exe", "description": "설정 프로그램"}
        ]

        self.log_message.emit("📥 GitHub에서 파일 다운로드 시작...")

        for i, file_info in enumerate(files_to_download):
            possible_names = file_info["names"]
            target_name = file_info["target_name"]
            description = file_info["description"]
            target_path = os.path.join(self.target_dir, target_name)

            self.log_message.emit(f"\n다운로드 중: {target_name} ({description})")

            # 여러 파일명 시도
            success = False
            last_error = ""
            downloaded_from = ""
            size = 0

            for filename in possible_names:
                self.log_message.emit(f"  시도: {filename}")
                success, message, size = self._download_file(filename, target_path)
                if success:
                    downloaded_from = filename
                    break
                else:
                    last_error = message

            if success:
                size_mb = size / (1024 * 1024)
                if downloaded_from != target_name:
                    self.results['downloaded_files'].append(f"{target_name} ({size_mb:.1f} MB, from {downloaded_from})")
                else:
                    self.results['downloaded_files'].append(f"{target_name} ({size_mb:.1f} MB)")
                self.log_message.emit(f"  ✓ 완료: {size_mb:.1f} MB")
            else:
                self.results['failed_downloads'].append(target_name)
                self.log_message.emit(f"  ✗ 실패: {last_error}")

            # 전체 진행률
            self.progress.emit("download", i + 1, len(files_to_download))

    def _download_file(self, filename, target_path):
        """개별 파일 다운로드"""
        try:
            download_url = f"{self.github_base_url}/{filename}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(download_url, headers=headers, timeout=120, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            chunk_size = 8192

            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 다운로드 진행률 (로그에 표시)
                        if total_size > 0:
                            percent = int((downloaded_size / total_size) * 100)
                            if percent % 20 == 0:  # 20% 단위로 로그
                                self.log_message.emit(f"    {percent}% ({downloaded_size // (1024*1024)} MB)")

            if downloaded_size < 10000:  # 10KB 미만이면 실패
                raise Exception(f"파일이 너무 작습니다 ({downloaded_size} bytes)")

            return True, "성공", downloaded_size

        except Exception as e:
            return False, str(e), 0

    def _upload_to_server(self):
        """서버에 이벤트 등록 및 리소스 업로드"""
        self.log_message.emit("\n📤 서버에 이벤트 등록 중...")

        try:
            from api_client import register_event_with_resources
            from datetime import datetime, timedelta

            # 만료일 설정 (30일 후)
            expired_at = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")

            def progress_callback(percent, message):
                self.log_message.emit(f"  {message}")
                self.progress.emit("upload", percent, 100)

            success, result = register_event_with_resources(
                event_name=self.event_name,
                kiosk_count=self.kiosk_count,
                expired_at=expired_at,
                config=self.config,
                resources_dir=self.resources_dir,
                progress_callback=progress_callback
            )

            if success:
                self.results['server_result'] = {
                    'success': True,
                    'event_number': result.get('event_number'),
                    'event_name': result.get('event_name'),
                    'activation_codes': result.get('activation_codes', [])
                }

                codes = result.get('activation_codes', [])
                self.log_message.emit(f"\n✅ 서버 등록 완료!")
                self.log_message.emit(f"   이벤트 번호: {result.get('event_number')}")
                if codes:
                    self.log_message.emit(f"   활성화 코드: {codes[0].get('code')}")
            else:
                self.results['server_result'] = {
                    'success': False,
                    'error': result.get('error', '알 수 없는 오류')
                }
                self.log_message.emit(f"\n❌ 서버 등록 실패: {result.get('error')}")

        except Exception as e:
            self.results['server_result'] = {
                'success': False,
                'error': str(e)
            }
            self.log_message.emit(f"\n❌ 서버 등록 오류: {str(e)}")


class DistributionProgressDialog(QDialog):
    """배포용 생성 통합 진행률 다이얼로그"""

    def __init__(self, parent=None, github_base_url="", target_dir="",
                 online_mode=False, config=None, event_name=None,
                 kiosk_count=1, resources_dir=None):
        super().__init__(parent)
        self.github_base_url = github_base_url
        self.target_dir = target_dir
        self.online_mode = online_mode
        self.config = config
        self.event_name = event_name
        self.kiosk_count = kiosk_count
        self.resources_dir = resources_dir

        self.results = {}
        self.worker = None

        self.init_ui()
        self.start_work()

    def init_ui(self):
        """UI 초기화"""
        title = "배포용 파일 생성 중" if not self.online_mode else "배포용 파일 생성 및 서버 등록 중"
        self.setWindowTitle(title)
        self.setFixedSize(600, 500)
        self.setModal(True)

        # 스타일 적용
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {COLORS['text_dark']};
                font-size: 12px;
            }}
            QProgressBar {{
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                background-color: {COLORS['background_light']};
                text-align: center;
                font-weight: bold;
                color: {COLORS['text_dark']};
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 4px;
            }}
            QTextEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: 13px;
                color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['disabled']};
                color: {COLORS['disabled_text']};
            }}
        """)

        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목
        title_label = QLabel("📦 배포용 파일을 생성하고 있습니다...")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title_label)

        # 단계 표시
        phase_group = QGroupBox("진행 단계")
        phase_layout = QVBoxLayout(phase_group)

        # Phase 1: 다운로드
        download_layout = QHBoxLayout()
        self.download_icon = QLabel("⏳")
        self.download_label = QLabel("GitHub에서 실행 파일 다운로드")
        download_layout.addWidget(self.download_icon)
        download_layout.addWidget(self.download_label)
        download_layout.addStretch()
        phase_layout.addLayout(download_layout)

        self.download_progress = QProgressBar()
        self.download_progress.setMaximum(2)  # 2개 파일
        self.download_progress.setValue(0)
        phase_layout.addWidget(self.download_progress)

        # Phase 2: 서버 업로드 (온라인 모드만)
        if self.online_mode:
            upload_layout = QHBoxLayout()
            self.upload_icon = QLabel("⏳")
            self.upload_label = QLabel("서버에 이벤트 등록 및 리소스 업로드")
            upload_layout.addWidget(self.upload_icon)
            upload_layout.addWidget(self.upload_label)
            upload_layout.addStretch()
            phase_layout.addLayout(upload_layout)

            self.upload_progress = QProgressBar()
            self.upload_progress.setMaximum(100)
            self.upload_progress.setValue(0)
            phase_layout.addWidget(self.upload_progress)

        layout.addWidget(phase_group)

        # 로그 영역
        log_group = QGroupBox("작업 로그")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(180)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.close_button = QPushButton("닫기")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def start_work(self):
        """작업 시작"""
        self.worker = DistributionWorker(
            github_base_url=self.github_base_url,
            target_dir=self.target_dir,
            online_mode=self.online_mode,
            config=self.config,
            event_name=self.event_name,
            kiosk_count=self.kiosk_count,
            resources_dir=self.resources_dir
        )

        self.worker.progress.connect(self.on_progress)
        self.worker.log_message.connect(self.add_log)
        self.worker.phase_changed.connect(self.on_phase_changed)
        self.worker.all_finished.connect(self.on_finished)

        self.worker.start()

    def on_progress(self, phase, current, total):
        """진행률 업데이트"""
        if phase == "download":
            self.download_progress.setValue(current)
        elif phase == "upload" and self.online_mode:
            self.upload_progress.setValue(current)

    def on_phase_changed(self, phase):
        """단계 변경"""
        if phase == "download":
            self.download_icon.setText("🔄")
            self.download_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold;")
        elif phase == "upload" and self.online_mode:
            self.download_icon.setText("✅")
            self.download_label.setStyleSheet(f"color: {COLORS['success']};")
            self.upload_icon.setText("🔄")
            self.upload_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold;")

    def add_log(self, message):
        """로그 메시지 추가"""
        self.log_text.append(message)
        # 스크롤을 최하단으로
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_finished(self, results):
        """작업 완료"""
        self.results = results

        # 아이콘 업데이트
        if results.get('downloaded_files'):
            self.download_icon.setText("✅")
            self.download_label.setStyleSheet(f"color: {COLORS['success']};")
            self.download_progress.setValue(self.download_progress.maximum())
        else:
            self.download_icon.setText("❌")
            self.download_label.setStyleSheet("color: #e74c3c;")

        if self.online_mode:
            server_result = results.get('server_result', {})
            if server_result and server_result.get('success'):
                self.upload_icon.setText("✅")
                self.upload_label.setStyleSheet(f"color: {COLORS['success']};")
                self.upload_progress.setValue(100)
            else:
                self.upload_icon.setText("❌")
                self.upload_label.setStyleSheet("color: #e74c3c;")

        # 닫기 버튼 활성화
        self.close_button.setEnabled(True)

        # 2초 후 자동 닫기
        QTimer.singleShot(2000, self.accept)

    def get_results(self):
        """결과 반환"""
        return self.results
