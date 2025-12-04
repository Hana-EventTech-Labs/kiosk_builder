"""
활성화 화면
- 활성화 코드 입력
- 서버 검증
- 설정 및 리소스 다운로드
"""
import os
import json
import requests
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QProgressBar,
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QFont, QPixmap, QColor, QLinearGradient, QPainter, QBrush
from PySide6.QtCore import Qt, QThread, Signal

# API 서버 URL
API_BASE_URL = "https://kiosk-manager-production.up.railway.app"


class ActivationWorker(QThread):
    """활성화 검증 및 다운로드 워커"""
    progress = Signal(int, str)  # (percent, message)
    finished = Signal(bool, dict)  # (success, result)

    def __init__(self, code: str):
        super().__init__()
        self.code = code

    def run(self):
        try:
            # 1. 활성화 코드 검증
            print(f"[ActivationWorker] Starting with code: {self.code}")
            self.progress.emit(10, "활성화 코드 검증 중...")

            print(f"[ActivationWorker] Sending request to {API_BASE_URL}/api/activation/validate")
            response = requests.post(
                f"{API_BASE_URL}/api/activation/validate",
                json={"code": self.code},
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=30
            )

            print(f"[ActivationWorker] Response status: {response.status_code}")

            if response.status_code != 200:
                print(f"[ActivationWorker] Server error: {response.status_code}")
                self.finished.emit(False, {"error": f"서버 오류: {response.status_code}"})
                return

            result = response.json()
            print(f"[ActivationWorker] is_valid: {result.get('is_valid')}")

            if not result.get("is_valid"):
                print(f"[ActivationWorker] Validation failed: {result.get('error_message')}")
                self.finished.emit(False, {"error": result.get("error_message", "활성화 실패")})
                return

            self.progress.emit(30, "활성화 성공! 설정 다운로드 중...")

            # 2. config.json 다운로드
            config_info = result.get("config", {})
            resources = result.get("resources", [])

            # config.json URL 찾기
            config_url = None
            for res in resources:
                if res.get("name") == "config.json":
                    config_url = res.get("url")
                    break

            if config_url:
                self.progress.emit(40, "설정 파일 다운로드 중...")
                try:
                    config_response = requests.get(config_url, timeout=10)
                    if config_response.status_code == 200:
                        # config.json 저장 (EXE/개발 모드 모두 지원)
                        import sys
                        if getattr(sys, 'frozen', False):
                            config_base = os.path.dirname(sys.executable)
                        else:
                            config_base = os.path.dirname(os.path.dirname(__file__))
                        config_path = os.path.join(config_base, "config.json")
                        with open(config_path, 'w', encoding='utf-8') as f:
                            f.write(config_response.text)
                        self.progress.emit(50, "설정 파일 저장 완료")
                    else:
                        print(f"[ActivationWorker] config.json download failed: {config_response.status_code}")
                        self.progress.emit(50, "설정 파일 다운로드 생략 (기본 설정 사용)")
                except Exception as config_error:
                    # config.json 다운로드 실패는 치명적이지 않음 - 로컬 config 사용
                    print(f"[ActivationWorker] config.json download error (non-critical): {config_error}")
                    self.progress.emit(50, "설정 파일 다운로드 생략 (기본 설정 사용)")

            # 3. 리소스 다운로드 (배경 이미지, 프레임 등)
            resource_files = [r for r in resources if r.get("name") != "config.json"]
            if resource_files:
                self.progress.emit(55, f"리소스 다운로드 준비 중... ({len(resource_files)}개)")

                # 리소스 저장 기본 경로 (EXE/개발 모드 모두 지원)
                import sys
                if getattr(sys, 'frozen', False):
                    # EXE 모드: EXE가 있는 디렉토리 기준
                    base_dir = os.path.dirname(sys.executable)
                else:
                    # 개발 모드: 스크립트 디렉토리 기준
                    base_dir = os.path.dirname(os.path.dirname(__file__))
                resources_dir = os.path.join(base_dir, "resources")

                # 다운로드 진행
                downloaded = 0
                failed = 0

                for idx, res in enumerate(resource_files):
                    res_name = res.get("name", "")
                    res_url = res.get("url", "")

                    if not res_name or not res_url:
                        continue

                    try:
                        # 진행률 계산 (55% ~ 90% 사이)
                        progress_percent = 55 + int((idx / max(len(resource_files), 1)) * 35)
                        self.progress.emit(progress_percent, f"다운로드 중: {res_name}")

                        # 파일 다운로드
                        response = requests.get(res_url, timeout=30)
                        if response.status_code == 200:
                            # 저장 경로 생성 (폴더 구조 유지)
                            save_path = os.path.join(resources_dir, res_name)
                            save_dir = os.path.dirname(save_path)

                            # 폴더가 없으면 생성
                            if not os.path.exists(save_dir):
                                os.makedirs(save_dir, exist_ok=True)

                            # 파일 저장
                            with open(save_path, 'wb') as f:
                                f.write(response.content)

                            downloaded += 1
                            print(f"[ActivationWorker] Downloaded: {res_name}")
                        else:
                            failed += 1
                            print(f"[ActivationWorker] Download failed ({response.status_code}): {res_name}")

                    except Exception as res_error:
                        failed += 1
                        print(f"[ActivationWorker] Download error: {res_name} - {res_error}")

                self.progress.emit(90, f"리소스 다운로드 완료 ({downloaded}/{len(resource_files)}개)")

                if failed > 0:
                    print(f"[ActivationWorker] {failed}개 리소스 다운로드 실패")
            else:
                self.progress.emit(90, "활성화 완료 준비 중...")

            # 4. 완료
            self.progress.emit(100, "활성화 완료!")

            self.finished.emit(True, {
                "event_number": config_info.get("event_number"),
                "event_name": config_info.get("event_name"),
                "kiosk_id": config_info.get("kiosk_id")
            })

        except requests.exceptions.Timeout as e:
            print(f"[ActivationWorker] Timeout: {e}")
            self.finished.emit(False, {"error": "서버 응답 시간 초과"})
        except requests.exceptions.ConnectionError as e:
            print(f"[ActivationWorker] ConnectionError: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit(False, {"error": "서버 연결 실패. 인터넷 연결을 확인하세요."})
        except Exception as e:
            print(f"[ActivationWorker] Exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit(False, {"error": f"오류 발생: {str(e)}"})


class GradientWidget(QWidget):
    """그라데이션 배경 위젯"""
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 그라데이션 생성 (다크 블루 → 퍼플)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#0f0c29"))
        gradient.setColorAt(0.5, QColor("#302b63"))
        gradient.setColorAt(1.0, QColor("#24243e"))

        painter.fillRect(self.rect(), gradient)


class ActivationScreen(QWidget):
    """활성화 화면"""

    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.worker = None
        self.setupUI()

    def setupUI(self):
        """UI 설정"""
        self.setFixedSize(*self.screen_size)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 그라데이션 배경
        self.bg_widget = GradientWidget(self)
        self.bg_widget.setFixedSize(*self.screen_size)

        # 콘텐츠 레이아웃
        content_layout = QVBoxLayout(self.bg_widget)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(20)

        # 상단 여백
        content_layout.addStretch(2)

        # 아이콘/로고 영역
        icon_label = QLabel("🔐")
        icon_label.setFont(QFont("Segoe UI Emoji", 72))
        icon_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(icon_label)

        content_layout.addSpacing(10)

        # 타이틀
        title = QLabel("키오스크 활성화")
        title.setFont(QFont("맑은 고딕", 42, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        # 설명
        desc = QLabel("활성화 코드를 입력해주세요")
        desc.setFont(QFont("맑은 고딕", 18))
        desc.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        desc.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(desc)

        content_layout.addSpacing(40)

        # 카드 스타일 컨테이너
        card = QFrame()
        card.setFixedSize(750, 320)
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)

        # 카드에 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 40, 50, 40)
        card_layout.setSpacing(25)

        # 입력 필드
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("예: EVENT-35-001-ABCD")
        self.code_input.setFont(QFont("Consolas", 24))
        self.code_input.setFixedHeight(70)
        self.code_input.setAlignment(Qt.AlignCenter)
        self.code_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.95);
                color: #1a1a2e;
                border: none;
                border-radius: 15px;
                padding: 15px 25px;
            }
            QLineEdit:focus {
                background-color: #ffffff;
            }
            QLineEdit::placeholder {
                color: #888888;
            }
        """)
        self.code_input.returnPressed.connect(self.onActivate)
        card_layout.addWidget(self.code_input)

        # 진행 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 4px;
            }
        """)
        card_layout.addWidget(self.progress_bar)

        # 상태 메시지
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("맑은 고딕", 14))
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(25)
        card_layout.addWidget(self.status_label)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        # 활성화 버튼
        self.activate_btn = QPushButton("활성화")
        self.activate_btn.setFont(QFont("맑은 고딕", 20, QFont.Bold))
        self.activate_btn.setFixedSize(200, 60)
        self.activate_btn.setCursor(Qt.PointingHandCursor)
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7b8ff0, stop:1 #8b5fbf);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd6, stop:1 #6a4196);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.3);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.activate_btn.clicked.connect(self.onActivate)
        btn_layout.addWidget(self.activate_btn)

        # 오프라인 모드 버튼
        self.offline_btn = QPushButton("오프라인 모드")
        self.offline_btn.setFont(QFont("맑은 고딕", 16))
        self.offline_btn.setFixedSize(200, 60)
        self.offline_btn.setCursor(Qt.PointingHandCursor)
        self.offline_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.8);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-color: rgba(255, 255, 255, 0.5);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.offline_btn.clicked.connect(self.onOfflineMode)
        btn_layout.addWidget(self.offline_btn)

        card_layout.addLayout(btn_layout)

        content_layout.addWidget(card, alignment=Qt.AlignCenter)

        # 하단 안내 텍스트
        content_layout.addSpacing(30)

        help_text = QLabel("활성화 코드는 관리자에게 문의하세요")
        help_text.setFont(QFont("맑은 고딕", 12))
        help_text.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        help_text.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(help_text)

        content_layout.addStretch(3)

        main_layout.addWidget(self.bg_widget)

        # 종료 버튼 (오른쪽 상단)
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(50, 50)
        self.close_btn.move(self.screen_size[0] - 70, 20)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.7);
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: rgba(255, 92, 92, 0.8);
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.main_window.closeApplication)

    def onActivate(self):
        """활성화 버튼 클릭"""
        code = self.code_input.text().strip()

        if not code:
            self.showError("활성화 코드를 입력해주세요.")
            return

        # UI 비활성화
        self.activate_btn.setEnabled(False)
        self.offline_btn.setEnabled(False)
        self.code_input.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")

        # 워커 시작
        self.worker = ActivationWorker(code)
        self.worker.progress.connect(self.onProgress)
        self.worker.finished.connect(self.onFinished)
        self.worker.start()

    def onProgress(self, percent: int, message: str):
        """진행 상태 업데이트"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def onFinished(self, success: bool, result: dict):
        """활성화 완료"""
        # UI 활성화
        self.activate_btn.setEnabled(True)
        self.offline_btn.setEnabled(True)
        self.code_input.setEnabled(True)

        if success:
            self.status_label.setText(f"✓ 활성화 완료: {result.get('event_name', '')}")
            self.status_label.setStyleSheet("color: #4ade80;")

            # 활성화 상태 저장 (다음 실행 시 활성화 화면 건너뛰기)
            self.saveActivationState(result)

            # 설정 다시 로드
            self.reloadConfig()

            # 2초 후 다음 화면으로 이동
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, self.goToNextScreen)
        else:
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"✗ {result.get('error', '활성화 실패')}")
            self.status_label.setStyleSheet("color: #f87171;")

    def saveActivationState(self, result: dict):
        """활성화 상태 저장 (다음 실행 시 활성화 화면 건너뛰기)"""
        try:
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(__file__))

            activation_file = os.path.join(base_dir, "activation.json")

            activation_data = {
                "activated": True,
                "event_number": result.get("event_number"),
                "event_name": result.get("event_name"),
                "kiosk_id": result.get("kiosk_id"),
                "activated_at": __import__("datetime").datetime.now().isoformat()
            }

            with open(activation_file, 'w', encoding='utf-8') as f:
                json.dump(activation_data, f, ensure_ascii=False, indent=2)

            print(f"활성화 상태 저장 완료: {activation_file}")
        except Exception as e:
            print(f"활성화 상태 저장 실패: {e}")

    def showError(self, message: str):
        """에러 메시지 표시"""
        self.status_label.setText(f"✗ {message}")
        self.status_label.setStyleSheet("color: #f87171;")

    def onOfflineMode(self):
        """오프라인 모드로 진행"""
        # 커스텀 스타일 메시지 박스
        msg = QMessageBox(self)
        msg.setWindowTitle("오프라인 모드")
        msg.setText("기존 설정으로 오프라인 모드로 실행합니다.")
        msg.setInformativeText("계속하시겠습니까?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        reply = msg.exec()

        if reply == QMessageBox.Yes:
            self.goToNextScreen()

    def reloadConfig(self):
        """설정 다시 로드"""
        try:
            # config 모듈 다시 로드
            import importlib
            import config as config_module
            importlib.reload(config_module)

            # main_window의 config 업데이트
            from config import config

            print(f"설정 다시 로드됨: {config.get('app_name', 'Unknown')}")
        except Exception as e:
            print(f"설정 로드 오류: {e}")

    def goToNextScreen(self):
        """다음 화면 (스플래쉬)으로 이동"""
        # 활성화 후 스플래시 화면 재생성 (새 config 반영)
        if hasattr(self.main_window, 'rebuildSplashScreen'):
            self.main_window.rebuildSplashScreen()

        # 인덱스 1은 스플래쉬 화면
        self.stack.setCurrentIndex(1)

    def cleanup(self):
        """리소스 정리"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
