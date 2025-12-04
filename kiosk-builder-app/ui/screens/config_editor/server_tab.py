# server_tab.py
# 서버 등록 탭 - 행사 등록 및 활성화 코드 생성

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QGroupBox, QTextEdit, QDateTimeEdit,
    QMessageBox, QProgressBar, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QDateTime, QThread, Signal
from PySide6.QtGui import QFont
from ui.styles.colors import COLORS
from utils.file_handler import get_resources_base_path
import os


class UploadWorker(QThread):
    """백그라운드 업로드 워커"""
    progress = Signal(int, str)  # (퍼센트, 메시지)
    finished = Signal(bool, dict)  # (성공여부, 결과)

    def __init__(self, event_name, kiosk_count, expired_at, config, resources_dir):
        super().__init__()
        self.event_name = event_name
        self.kiosk_count = kiosk_count
        self.expired_at = expired_at
        self.config = config
        self.resources_dir = resources_dir

    def run(self):
        try:
            from api_client import register_event_with_resources

            self.progress.emit(10, "서버에 이벤트 등록 중...")

            success, result = register_event_with_resources(
                event_name=self.event_name,
                kiosk_count=self.kiosk_count,
                expired_at=self.expired_at,
                config=self.config,
                resources_dir=self.resources_dir,
                progress_callback=self._on_progress
            )

            self.finished.emit(success, result)

        except Exception as e:
            self.finished.emit(False, {"error": str(e)})

    def _on_progress(self, percent, message):
        self.progress.emit(percent, message)


class ServerTab(QWidget):
    """서버 등록 탭"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.main_window = parent
        self.upload_worker = None
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        # 스크롤 영역 설정
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 설명
        desc = QLabel("행사 정보를 입력하고 서버에 등록하면 활성화 코드가 생성됩니다.\n현장 키오스크에서 활성화 코드를 입력하면 설정과 리소스가 자동으로 다운로드됩니다.")
        desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; padding: 10px; background: {COLORS['background_light']}; border-radius: 8px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 행사 정보 그룹
        event_group = QGroupBox("행사 정보")
        event_group.setStyleSheet(self._group_style())
        event_layout = QVBoxLayout(event_group)
        event_layout.setSpacing(15)

        # 행사명
        name_layout = QHBoxLayout()
        name_label = QLabel("행사명:")
        name_label.setFixedWidth(100)
        name_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        self.event_name_input = QLineEdit()
        self.event_name_input.setPlaceholderText("예: 삼성 신제품 런칭 이벤트")
        self.event_name_input.setStyleSheet(self._input_style())
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.event_name_input)
        event_layout.addLayout(name_layout)

        # 키오스크 대수
        count_layout = QHBoxLayout()
        count_label = QLabel("키오스크 대수:")
        count_label.setFixedWidth(100)
        count_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        self.kiosk_count_input = QSpinBox()
        self.kiosk_count_input.setRange(1, 100)
        self.kiosk_count_input.setValue(1)
        self.kiosk_count_input.setStyleSheet(self._input_style())
        self.kiosk_count_input.setFixedWidth(100)
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.kiosk_count_input)
        count_layout.addStretch()
        event_layout.addLayout(count_layout)

        # 만료일
        expire_layout = QHBoxLayout()
        expire_label = QLabel("만료일:")
        expire_label.setFixedWidth(100)
        expire_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        self.expire_input = QDateTimeEdit()
        self.expire_input.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.expire_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.expire_input.setCalendarPopup(True)
        self.expire_input.setStyleSheet(self._input_style())
        expire_layout.addWidget(expire_label)
        expire_layout.addWidget(self.expire_input)
        expire_layout.addStretch()
        event_layout.addLayout(expire_layout)

        layout.addWidget(event_group)

        # 등록 버튼
        self.register_btn = QPushButton("🚀 서버에 등록하고 활성화 코드 생성")
        self.register_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.register_btn.clicked.connect(self.on_register_clicked)
        layout.addWidget(self.register_btn)

        # 진행 상태
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # 결과 그룹
        result_group = QGroupBox("활성화 코드")
        result_group.setStyleSheet(self._group_style())
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("등록이 완료되면 여기에 활성화 코드가 표시됩니다.")
        self.result_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 15px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                color: {COLORS['text_dark']};
            }}
        """)
        self.result_text.setMinimumHeight(200)
        result_layout.addWidget(self.result_text)

        # 복사 버튼
        copy_btn = QPushButton("📋 클립보드에 복사")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background_light']};
                color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border']};
            }}
        """)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        result_layout.addWidget(copy_btn)

        layout.addWidget(result_group)

        layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _group_style(self):
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }}
        """

    def _input_style(self):
        return f"""
            QLineEdit, QSpinBox, QDateTimeEdit {{
                background-color: {COLORS['background_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                color: {COLORS['text_dark']};
            }}
            QLineEdit:focus, QSpinBox:focus, QDateTimeEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """

    def on_register_clicked(self):
        """등록 버튼 클릭"""
        event_name = self.event_name_input.text().strip()
        if not event_name:
            QMessageBox.warning(self, "입력 오류", "행사명을 입력해주세요.")
            return

        kiosk_count = self.kiosk_count_input.value()
        expired_at = self.expire_input.dateTime().toString("yyyy-MM-ddTHH:mm:ss")

        # resources 폴더 경로 (EXE/개발 모드 모두 지원)
        base_dir = get_resources_base_path()
        resources_dir = os.path.join(base_dir, 'resources')

        # 모든 탭에서 현재 설정값을 config에 반영 (배포용 생성과 동일한 방식)
        if self.main_window and hasattr(self.main_window, 'tab_manager'):
            self.main_window.tab_manager.update_config_from_tabs(self.main_window.config)
            self.config = self.main_window.config
            print("서버 등록: 탭에서 config 업데이트 완료")

        # config.json 파일도 저장 (동일 경로에)
        self._save_config_to_file(base_dir)

        # UI 비활성화
        self.register_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText("등록 준비 중...")

        # 백그라운드 워커 시작
        self.upload_worker = UploadWorker(
            event_name=event_name,
            kiosk_count=kiosk_count,
            expired_at=expired_at,
            config=self.config,
            resources_dir=resources_dir
        )
        self.upload_worker.progress.connect(self.on_progress)
        self.upload_worker.finished.connect(self.on_finished)
        self.upload_worker.start()

    def _save_config_to_file(self, base_dir):
        """현재 config를 파일로 저장"""
        import json

        # config.json 저장 경로 (EXE와 동일한 디렉토리)
        config_path = os.path.join(base_dir, 'config.json')

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            print(f"config.json 저장 완료: {config_path}")
        except Exception as e:
            print(f"config.json 저장 실패: {e}")

    def on_progress(self, percent, message):
        """진행 상태 업데이트"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)

    def on_finished(self, success, result):
        """업로드 완료"""
        self.register_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        if success:
            # 결과 표시
            codes_text = f"✅ 등록 완료!\n\n"
            codes_text += f"행사명: {result.get('event_name', '')}\n"
            codes_text += f"이벤트 번호: {result.get('event_number', '')}\n\n"
            codes_text += "=" * 50 + "\n"
            codes_text += "활성화 코드 목록\n"
            codes_text += "=" * 50 + "\n\n"

            for code_info in result.get('activation_codes', []):
                codes_text += f"키오스크 {code_info['kiosk_id']}: {code_info['code']}\n"

            codes_text += "\n" + "=" * 50
            codes_text += "\n현장 키오스크에서 위 코드를 입력하세요."

            self.result_text.setText(codes_text)

            QMessageBox.information(
                self, "등록 완료",
                f"행사 '{result.get('event_name')}'이(가) 등록되었습니다.\n"
                f"키오스크 {len(result.get('activation_codes', []))}대 라이선스 발급 완료!"
            )
        else:
            error_msg = result.get('error', '알 수 없는 오류')
            self.result_text.setText(f"❌ 등록 실패\n\n오류: {error_msg}")
            QMessageBox.critical(self, "등록 실패", f"서버 등록에 실패했습니다.\n\n{error_msg}")

    def copy_to_clipboard(self):
        """클립보드에 복사"""
        from PySide6.QtWidgets import QApplication
        text = self.result_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "복사 완료", "활성화 코드가 클립보드에 복사되었습니다.")

    def update_config(self, config):
        """config 업데이트 (다른 탭과 호환용)"""
        self.config = config

    def update_ui(self, config):
        """UI 업데이트 (다른 탭과 호환용)"""
        self.config = config
