from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QProgressBar, QTextEdit)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont
import requests
import os
from ui.styles.colors import COLORS

class DownloadWorker(QThread):
    """다운로드 작업을 처리하는 워커 스레드"""
    progress = Signal(str, int, int)  # filename, current, total
    finished = Signal(str, bool, str)  # filename, success, message
    log_message = Signal(str)  # 로그 메시지
    all_finished = Signal(dict)  # 전체 다운로드 완료 시 결과 전달
    
    def __init__(self, github_base_url, files_to_download, target_dir):
        super().__init__()
        self.github_base_url = github_base_url
        self.files_to_download = files_to_download
        self.target_dir = target_dir
        self.results = {}
        
    def run(self):
        """다운로드 실행"""
        self.log_message.emit("다운로드를 시작합니다...")
        
        for file_info in self.files_to_download:
            filename = file_info["name"]
            target_path = os.path.join(self.target_dir, filename)
            
            self.log_message.emit(f"{filename} 다운로드 시작...")
            success, message = self.download_file(filename, target_path)
            
            self.results[filename] = {
                'success': success,
                'message': message,
                'size': os.path.getsize(target_path) if success else 0
            }
            
            self.finished.emit(filename, success, message)
            
        self.log_message.emit("모든 다운로드가 완료되었습니다.")
        self.all_finished.emit(self.results)
    
    def download_file(self, filename, target_path):
        """개별 파일 다운로드"""
        try:
            download_url = f"{self.github_base_url}/{filename}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 스트리밍 다운로드로 진행률 표시
            response = requests.get(download_url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # 파일 크기 확인
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                # Content-Length가 없는 경우 일반 다운로드
                content = response.content
                if len(content) < 10000:  # 10KB 미만이면 실패로 간주
                    raise Exception(f"다운로드된 파일이 너무 작습니다 ({len(content)} bytes)")
                
                with open(target_path, 'wb') as f:
                    f.write(content)
                
                self.progress.emit(filename, len(content), len(content))
                return True, f"다운로드 완료 (크기: {len(content):,} bytes)"
            
            # 진행률을 보여주며 다운로드
            downloaded_size = 0
            chunk_size = 8192
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        self.progress.emit(filename, downloaded_size, total_size)
            
            if downloaded_size < 10000:  # 10KB 미만이면 실패로 간주
                raise Exception(f"다운로드된 파일이 너무 작습니다 ({downloaded_size} bytes)")
            
            return True, f"다운로드 완료 (크기: {downloaded_size:,} bytes)"
            
        except Exception as e:
            return False, f"다운로드 실패: {str(e)}"

class DownloadProgressDialog(QDialog):
    """다운로드 진행률을 보여주는 다이얼로그"""
    
    def __init__(self, parent=None, github_base_url="", files_to_download=[], target_dir=""):
        super().__init__(parent)
        self.github_base_url = github_base_url
        self.files_to_download = files_to_download
        self.target_dir = target_dir
        self.download_results = {}
        
        self.init_ui()
        self.start_download()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("파일 다운로드")
        self.setFixedSize(500, 400)
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
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 4px;
            }}
            QTextEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                background-color: {COLORS['background_light']};
                color: {COLORS['text_dark']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_darker']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['disabled']};
                color: {COLORS['disabled_text']};
            }}
        """)
        
        # 레이아웃 설정
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목
        title_label = QLabel("GitHub에서 필요한 파일을 다운로드하고 있습니다...")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # 현재 파일 레이블
        self.current_file_label = QLabel("준비 중...")
        layout.addWidget(self.current_file_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 전체 진행률 레이블
        self.overall_progress_label = QLabel("0 / 0 파일 완료")
        layout.addWidget(self.overall_progress_label)
        
        # 로그 텍스트 영역
        log_label = QLabel("다운로드 로그:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 닫기 버튼 (처음에는 비활성화)
        self.close_button = QPushButton("닫기")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def start_download(self):
        """다운로드 시작"""
        # 워커 스레드 생성 및 시작
        self.worker = DownloadWorker(
            self.github_base_url, 
            self.files_to_download, 
            self.target_dir
        )
        
        # 시그널 연결
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.file_finished)
        self.worker.log_message.connect(self.add_log_message)
        self.worker.all_finished.connect(self.all_downloads_finished)
        
        # 다운로드 시작
        self.worker.start()
        
        # 전체 진행률 업데이트
        self.update_overall_progress(0)
    
    def update_progress(self, filename, current, total):
        """개별 파일 진행률 업데이트"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            
            # 파일 크기를 읽기 쉽게 표시
            current_mb = current / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            
            self.current_file_label.setText(
                f"다운로드 중: {filename} ({current_mb:.1f}MB / {total_mb:.1f}MB)"
            )
    
    def file_finished(self, filename, success, message):
        """개별 파일 다운로드 완료"""
        completed_count = len([r for r in self.download_results.values() if 'completed' in r])
        self.update_overall_progress(completed_count + 1)
        
        # 결과 저장
        self.download_results[filename] = {
            'success': success,
            'message': message,
            'completed': True
        }
        
        # 로그 추가
        status = "✓" if success else "✗"
        self.add_log_message(f"{status} {filename}: {message}")
        
        if success:
            self.current_file_label.setText(f"완료: {filename}")
        else:
            self.current_file_label.setText(f"실패: {filename}")
    
    def add_log_message(self, message):
        """로그 메시지 추가"""
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()
    
    def update_overall_progress(self, completed_count):
        """전체 진행률 업데이트"""
        total_files = len(self.files_to_download)
        self.overall_progress_label.setText(f"{completed_count} / {total_files} 파일 완료")
    
    def all_downloads_finished(self, results):
        """모든 다운로드 완료"""
        self.download_results = results
        
        # UI 업데이트
        self.progress_bar.setValue(100)
        self.current_file_label.setText("모든 다운로드가 완료되었습니다.")
        self.close_button.setEnabled(True)
        
        # 결과 요약
        success_count = len([r for r in results.values() if r['success']])
        total_count = len(results)
        
        if success_count == total_count:
            self.add_log_message(f"\n✓ 모든 파일({total_count}개)이 성공적으로 다운로드되었습니다!")
        else:
            failed_count = total_count - success_count
            self.add_log_message(f"\n⚠ {success_count}개 성공, {failed_count}개 실패")
        
        # 1초 후 자동으로 다이얼로그 닫기
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self.accept)
    
    def get_results(self):
        """다운로드 결과 반환"""
        return self.download_results