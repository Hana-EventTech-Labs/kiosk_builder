from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QGridLayout, QMessageBox,
                               QFrame, QSizePolicy, QGraphicsOpacityEffect)
from PySide6.QtCore import QTimer, Qt, QSize, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPixmap, QFont, QFontDatabase, QMovie, QPainter, QColor
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PIL import Image, ImageQt

from config import config, language_manager
import os
import glob

class FrameScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.background_widget = None
        self.media_player = None
        self._background_initialized = False  # 배경 지연 초기화 플래그
        self._last_language = None  # 마지막으로 로드된 언어 추적
        self.captured_photo_path = "resources/captured_image.jpg"  # 촬영된 사진 경로
        self.selected_frame = None
        self.frame_files = []  # 프레임 파일 목록
        self.current_frame_index = 0  # 캐러셀용 현재 인덱스
        self.carousel_buttons = []  # 캐러셀 썸네일 버튼들
        self.layout_style = config.get("photo_frame", {}).get("layout_style", "classic")
        self.loadCustomFont()
        self.loadFrameFiles()  # 프레임 파일 미리 로드
        self.setupUI()

    def showEvent(self, event):
        """화면이 표시될 때 배경 초기화 및 사진 표시 (언어 변경 시 갱신)"""
        current_lang = language_manager.current_language

        # 배경이 초기화되지 않았거나 언어가 변경된 경우 배경 갱신
        if not self._background_initialized or self._last_language != current_lang:
            self._cleanupBackground()
            self.setupBackground()
            self._background_initialized = True
            self._last_language = current_lang
        # 촬영된 사진 표시 (파일 생성 지연 문제 해결)
        self.showCapturedPhoto()
        super().showEvent(event)
        event.accept()

    def _cleanupBackground(self):
        """기존 배경 리소스 정리"""
        if self.media_player:
            self.media_player.stop()
            self.media_player.deleteLater()
            self.media_player = None
        if hasattr(self, 'audio_output') and self.audio_output:
            self.audio_output.deleteLater()
            self.audio_output = None
        if self.background_widget:
            self.background_widget.deleteLater()
            self.background_widget = None

    def loadCustomFont(self):
        """커스텀 폰트 로드"""
        font_name = config["complete"]["font"]
        font_path = os.path.join("resources", "font", font_name)
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            else:
                self.font_family = "맑은 고딕"  # 폰트 로드 실패 시 기본 폰트
        else:
            self.font_family = "맑은 고딕"  # 폰트 파일이 없을 때 기본 폰트

    def loadFrameFiles(self):
        """프레임 파일 목록 로드"""
        frame_files_config = config.get("photo_frame", {}).get("frame_files", [])

        if frame_files_config:
            for frame_file in frame_files_config:
                if not frame_file.startswith("resources/"):
                    frame_path = f"resources/frames/{frame_file}"
                else:
                    frame_path = frame_file

                if os.path.exists(frame_path):
                    self.frame_files.append(frame_path)
                else:
                    print(f"프레임 파일을 찾을 수 없습니다: {frame_path}")
        else:
            self.frame_files = glob.glob("resources/frames/*.png")

    def setupUI(self):
        # 배경은 showEvent에서 초기화 (언어 선택 후)

        # 레이아웃 스타일에 따라 UI 설정
        if self.layout_style == "carousel":
            self.setupCarouselLayout()
        elif self.layout_style == "fullscreen":
            self.setupFullscreenLayout()
        elif self.layout_style == "grid_overlay":
            self.setupGridOverlayLayout()
        else:  # classic (기본값)
            self.setupClassicLayout()

        self.addCloseButton()

    def setupClassicLayout(self):
        """클래식 레이아웃 (좌우 분할)"""
        main_layout = QHBoxLayout(self)

        # 왼쪽: 프레임 선택 영역
        self.setupFrameSelection(main_layout)

        # 오른쪽: 미리보기 영역
        self.setupPreview(main_layout)

    def setupCarouselLayout(self):
        """캐러셀 레이아웃 (중앙 미리보기 + 하단 슬라이더)"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)

        # 상단 제목
        title_label = QLabel("프레임을 선택하세요")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: #333;
            font-family: '{config['photo_frame'].get('font') or self.font_family}';
        """)
        main_layout.addWidget(title_label)

        # 중앙 영역 (화살표 + 미리보기)
        center_layout = QHBoxLayout()
        center_layout.setSpacing(20)

        # 왼쪽 화살표 버튼
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(60, 120)
        self.prev_button.clicked.connect(self.showPreviousFrame)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.3);
                color: white;
                font-size: 32px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        center_layout.addWidget(self.prev_button, alignment=Qt.AlignVCenter)

        # 중앙 미리보기 영역
        preview_container = QWidget()
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel()
        preview_width = config["photo_frame"].get("width", 800)
        preview_height = config["photo_frame"].get("height", 600)
        self.preview_label.setFixedSize(preview_width, preview_height)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            border: 4px solid #00FFC2;
            background-color: #f9f9f9;
            border-radius: 15px;
        """)
        self.preview_label.setText("프레임을 선택하면\n미리보기가 나타납니다")
        preview_container_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        center_layout.addWidget(preview_container, stretch=1)

        # 오른쪽 화살표 버튼
        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(60, 120)
        self.next_button.clicked.connect(self.showNextFrame)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.3);
                color: white;
                font-size: 32px;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        center_layout.addWidget(self.next_button, alignment=Qt.AlignVCenter)

        main_layout.addLayout(center_layout, stretch=1)

        # 하단 썸네일 슬라이더
        self.setupCarouselThumbnails(main_layout)

        # 하단 버튼 (다시 촬영, 선택 완료)
        self.setupCarouselButtons(main_layout)

    def setupCarouselThumbnails(self, parent_layout):
        """캐러셀 하단 썸네일 슬라이더"""
        thumbnail_container = QWidget()
        thumbnail_container.setFixedHeight(120)
        thumbnail_container.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
        """)

        thumbnail_layout = QHBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(20, 10, 20, 10)
        thumbnail_layout.setSpacing(15)
        thumbnail_layout.setAlignment(Qt.AlignCenter)

        self.carousel_buttons = []
        for i, frame_path in enumerate(self.frame_files):
            btn = QPushButton()
            btn.setFixedSize(80, 80)
            btn.setCheckable(True)

            pixmap = QPixmap(frame_path)
            btn.setIcon(pixmap.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            btn.setIconSize(QSize(70, 70))

            btn.clicked.connect(lambda checked, idx=i: self.selectCarouselFrame(idx))
            btn.setStyleSheet("""
                QPushButton {
                    border: 3px solid transparent;
                    border-radius: 8px;
                    background-color: white;
                }
                QPushButton:hover {
                    border-color: #00FFC2;
                }
                QPushButton:checked {
                    border-color: #00FFC2;
                    background-color: #e0fff5;
                }
            """)

            thumbnail_layout.addWidget(btn)
            self.carousel_buttons.append(btn)

        parent_layout.addWidget(thumbnail_container)

    def setupCarouselButtons(self, parent_layout):
        """캐러셀 하단 액션 버튼"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(30)
        buttons_layout.setAlignment(Qt.AlignCenter)

        # 다시 촬영 버튼
        self.retake_button = QPushButton("다시 촬영")
        self.retake_button.setFixedSize(180, 60)
        self.retake_button.clicked.connect(self.onRetake)
        self.retake_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        buttons_layout.addWidget(self.retake_button)

        # 선택 완료 버튼
        self.confirm_button = QPushButton("선택 완료")
        self.confirm_button.setFixedSize(180, 60)
        self.confirm_button.clicked.connect(self.onConfirm)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #00FFC2;
                color: black;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #00E6A8;
            }
        """)
        buttons_layout.addWidget(self.confirm_button)

        parent_layout.addLayout(buttons_layout)

    def selectCarouselFrame(self, index):
        """캐러셀에서 프레임 선택"""
        if 0 <= index < len(self.frame_files):
            self.current_frame_index = index
            self.selected_frame = self.frame_files[index]

            # 버튼 상태 업데이트
            for i, btn in enumerate(self.carousel_buttons):
                btn.setChecked(i == index)

            self.updatePreview()

    def showPreviousFrame(self):
        """이전 프레임 표시"""
        if self.frame_files:
            self.current_frame_index = (self.current_frame_index - 1) % len(self.frame_files)
            self.selectFrameByLayout(self.current_frame_index)

    def showNextFrame(self):
        """다음 프레임 표시"""
        if self.frame_files:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frame_files)
            self.selectFrameByLayout(self.current_frame_index)

    def selectFrameByLayout(self, index):
        """레이아웃에 따른 프레임 선택"""
        if 0 <= index < len(self.frame_files):
            self.current_frame_index = index
            self.selected_frame = self.frame_files[index]

            # 레이아웃별 UI 업데이트
            if self.layout_style == "carousel":
                # 캐러셀 버튼 상태 업데이트
                for i, btn in enumerate(self.carousel_buttons):
                    btn.setChecked(i == index)
            elif self.layout_style == "fullscreen":
                # 페이지 인디케이터 업데이트
                self.updatePageIndicators()
            elif self.layout_style == "grid_overlay":
                # 그리드 버튼 상태 업데이트
                if hasattr(self, 'grid_buttons'):
                    for i, btn in enumerate(self.grid_buttons):
                        btn.setChecked(i == index)

            self.updatePreview()

    def setupFullscreenLayout(self):
        """풀스크린 갤러리 레이아웃 (전체 화면 미리보기 + 페이지 인디케이터)"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 상단 제목 바
        title_bar = QWidget()
        title_bar.setFixedHeight(80)
        title_bar.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        title_layout = QHBoxLayout(title_bar)

        title_label = QLabel("프레임을 선택하세요")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 36px;
            font-weight: bold;
            color: white;
            font-family: '{config['photo_frame'].get('font') or self.font_family}';
        """)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_bar)

        # 중앙 미리보기 영역 (화면 거의 전체)
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(20, 20, 20, 20)

        # 왼쪽 화살표
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(80, 150)
        self.prev_button.clicked.connect(self.showPreviousFrame)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.4);
                color: white;
                font-size: 40px;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.6);
            }
        """)
        center_layout.addWidget(self.prev_button, alignment=Qt.AlignVCenter)

        # 중앙 미리보기
        self.preview_label = QLabel()
        # 화면 크기에 따른 동적 크기 설정
        preview_width = min(self.screen_size[0] - 250, 1400)
        preview_height = min(self.screen_size[1] - 300, 900)
        self.preview_label.setFixedSize(preview_width, preview_height)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            background-color: #1a1a1a;
            border: 3px solid #00FFC2;
            border-radius: 20px;
        """)
        self.preview_label.setText("프레임을 선택하면\n미리보기가 나타납니다")
        self.preview_label.setStyleSheet(self.preview_label.styleSheet() + "color: #666; font-size: 24px;")
        center_layout.addWidget(self.preview_label, stretch=1, alignment=Qt.AlignCenter)

        # 오른쪽 화살표
        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(80, 150)
        self.next_button.clicked.connect(self.showNextFrame)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.4);
                color: white;
                font-size: 40px;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.6);
            }
        """)
        center_layout.addWidget(self.next_button, alignment=Qt.AlignVCenter)

        main_layout.addWidget(center_widget, stretch=1)

        # 하단 영역 (페이지 인디케이터 + 버튼)
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(140)
        bottom_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setSpacing(15)

        # 페이지 인디케이터
        self.setupPageIndicators(bottom_layout)

        # 하단 버튼
        self.setupFullscreenButtons(bottom_layout)

        main_layout.addWidget(bottom_widget)

    def setupPageIndicators(self, parent_layout):
        """페이지 인디케이터 (점) 설정"""
        indicator_layout = QHBoxLayout()
        indicator_layout.setAlignment(Qt.AlignCenter)
        indicator_layout.setSpacing(12)

        self.page_indicators = []
        for i in range(len(self.frame_files)):
            indicator = QLabel("●")
            indicator.setFixedSize(20, 20)
            indicator.setAlignment(Qt.AlignCenter)
            indicator.setStyleSheet("color: #666; font-size: 16px;")
            indicator_layout.addWidget(indicator)
            self.page_indicators.append(indicator)

        # 첫 번째 인디케이터 활성화
        if self.page_indicators:
            self.page_indicators[0].setStyleSheet("color: #00FFC2; font-size: 20px;")

        parent_layout.addLayout(indicator_layout)

    def setupFullscreenButtons(self, parent_layout):
        """풀스크린 레이아웃 하단 버튼"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.setSpacing(40)

        # 다시 촬영 버튼
        self.retake_button = QPushButton("다시 촬영")
        self.retake_button.setFixedSize(200, 55)
        self.retake_button.clicked.connect(self.onRetake)
        self.retake_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                font-size: 22px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        buttons_layout.addWidget(self.retake_button)

        # 선택 완료 버튼
        self.confirm_button = QPushButton("선택 완료")
        self.confirm_button.setFixedSize(200, 55)
        self.confirm_button.clicked.connect(self.onConfirm)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #00FFC2;
                color: black;
                font-size: 22px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #00E6A8;
            }
        """)
        buttons_layout.addWidget(self.confirm_button)

        parent_layout.addLayout(buttons_layout)

    def updatePageIndicators(self):
        """페이지 인디케이터 업데이트"""
        if hasattr(self, 'page_indicators'):
            for i, indicator in enumerate(self.page_indicators):
                if i == self.current_frame_index:
                    indicator.setStyleSheet("color: #00FFC2; font-size: 20px;")
                else:
                    indicator.setStyleSheet("color: #666; font-size: 16px;")

    def setupGridOverlayLayout(self):
        """그리드 오버레이 레이아웃 (상단 미리보기 + 하단 투명 그리드)"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 상단 제목
        title_label = QLabel("프레임을 선택하세요")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: #333;
            font-family: '{config['photo_frame'].get('font') or self.font_family}';
        """)
        main_layout.addWidget(title_label)

        # 상단 미리보기 영역
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_label = QLabel()
        preview_width = config["photo_frame"].get("width", 800)
        preview_height = config["photo_frame"].get("height", 600)
        # 화면 크기에 맞게 조정
        max_preview_height = int(self.screen_size[1] * 0.55)
        if preview_height > max_preview_height:
            scale = max_preview_height / preview_height
            preview_height = max_preview_height
            preview_width = int(preview_width * scale)

        self.preview_label.setFixedSize(preview_width, preview_height)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            border: 4px solid #00FFC2;
            background-color: #f9f9f9;
            border-radius: 15px;
        """)
        self.preview_label.setText("프레임을 선택하면\n미리보기가 나타납니다")
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        main_layout.addWidget(preview_container, stretch=1)

        # 하단 그리드 오버레이 영역
        self.setupGridOverlayThumbnails(main_layout)

        # 하단 버튼
        self.setupGridOverlayButtons(main_layout)

    def setupGridOverlayThumbnails(self, parent_layout):
        """그리드 오버레이 썸네일 영역"""
        grid_container = QWidget()
        grid_container.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
        """)

        grid_layout = QHBoxLayout(grid_container)
        grid_layout.setContentsMargins(20, 15, 20, 15)
        grid_layout.setSpacing(15)
        grid_layout.setAlignment(Qt.AlignCenter)

        self.grid_buttons = []
        for i, frame_path in enumerate(self.frame_files):
            btn = QPushButton()
            btn.setFixedSize(100, 100)
            btn.setCheckable(True)

            pixmap = QPixmap(frame_path)
            btn.setIcon(pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            btn.setIconSize(QSize(90, 90))

            btn.clicked.connect(lambda checked, idx=i: self.selectFrameByLayout(idx))
            btn.setStyleSheet("""
                QPushButton {
                    border: 3px solid rgba(255, 255, 255, 0.5);
                    border-radius: 10px;
                    background-color: rgba(255, 255, 255, 0.8);
                }
                QPushButton:hover {
                    border-color: #00FFC2;
                    background-color: white;
                }
                QPushButton:checked {
                    border-color: #00FFC2;
                    border-width: 4px;
                    background-color: #e0fff5;
                }
            """)

            grid_layout.addWidget(btn)
            self.grid_buttons.append(btn)

        parent_layout.addWidget(grid_container)

    def setupGridOverlayButtons(self, parent_layout):
        """그리드 오버레이 하단 버튼"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.setSpacing(30)

        # 다시 촬영 버튼
        self.retake_button = QPushButton("다시 촬영")
        self.retake_button.setFixedSize(180, 55)
        self.retake_button.clicked.connect(self.onRetake)
        self.retake_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        buttons_layout.addWidget(self.retake_button)

        # 선택 완료 버튼
        self.confirm_button = QPushButton("선택 완료")
        self.confirm_button.setFixedSize(180, 55)
        self.confirm_button.clicked.connect(self.onConfirm)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #00FFC2;
                color: black;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #00E6A8;
            }
        """)
        buttons_layout.addWidget(self.confirm_button)

        parent_layout.addLayout(buttons_layout)
        
    def setupBackground(self):
        background_file = None

        # 언어 선택 모드가 활성화된 경우 언어별 배경 먼저 확인
        if language_manager.is_enabled():
            lang_path = language_manager.get_background_path(4)  # frame screen = index 4
            if lang_path:
                background_file = lang_path

        # 언어별 배경이 없으면 기본 배경 파일들 확인
        if background_file is None:
            background_files = [
                "background/4.mp4", "background/4.gif", "background/4.png", "background/4.jpg",
                "background/frame_bg.mp4", "background/frame_bg.gif", "background/frame_bg.png", "background/frame_bg.jpg"
            ]

            for filename in background_files:
                file_path = f"resources/{filename}"
                if os.path.exists(file_path):
                    background_file = file_path
                    break

        if background_file is None:
            # 모든 파일이 없는 경우 빈 배경 사용
            background_label = QLabel(self)
            background_label.resize(*self.screen_size)
            self.background_widget = background_label
            return

        file_extension = background_file.lower().split('.')[-1]

        if file_extension == 'mp4':
            # MP4 비디오 재생
            self.setupVideoBackground(background_file)
        elif file_extension == 'gif':
            # GIF 애니메이션 재생
            self.setupGifBackground(background_file)
        else:
            # 일반 이미지 (PNG, JPG)
            self.setupImageBackground(background_file)
    
    def setupVideoBackground(self, video_path):
        """MP4 비디오 배경 설정"""
        self.background_widget = QVideoWidget(self)
        self.background_widget.resize(*self.screen_size)

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setMuted(True)  # 음소거

        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.background_widget)
        self.media_player.setSource(f"file:///{os.path.abspath(video_path)}")

        # 비디오가 끝나면 다시 재생 (루프)
        self.media_player.mediaStatusChanged.connect(self.onVideoStatusChanged)
        self.media_player.play()

        # 배경을 맨 뒤로 보내고 표시
        self.background_widget.lower()
        self.background_widget.show()

    def setupGifBackground(self, gif_path):
        """GIF 애니메이션 배경 설정"""
        self.background_widget = QLabel(self)
        self.background_widget.resize(*self.screen_size)

        movie = QMovie(gif_path)
        movie.setScaledSize(self.background_widget.size())
        self.background_widget.setMovie(movie)
        self.background_widget.setScaledContents(True)
        movie.start()

        # 배경을 맨 뒤로 보내고 표시
        self.background_widget.lower()
        self.background_widget.show()

    def setupImageBackground(self, image_path):
        """일반 이미지 배경 설정"""
        self.background_widget = QLabel(self)
        pixmap = QPixmap(image_path)
        self.background_widget.setPixmap(pixmap)
        self.background_widget.setScaledContents(True)
        self.background_widget.resize(*self.screen_size)

        # 배경을 맨 뒤로 보내고 표시
        self.background_widget.lower()
        self.background_widget.show()

    def onVideoStatusChanged(self, status):
        """비디오 상태 변경 시 호출 (루프 재생을 위해)"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()

    def addCloseButton(self):
        """오른쪽 상단에 닫기 버튼 추가"""
        self.close_button = QPushButton("X", self)
        self.close_button.setFixedSize(200, 200)
        self.close_button.move(self.screen_size[0] - 50, 10)  # 오른쪽 상단 위치
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 92, 92, 0);  /* 완전히 투명하게 설정 */
                color: rgba(255, 255, 255, 0);  /* 텍스트도 완전히 투명하게 설정 (보이지 않음) */
                font-weight: bold;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(224, 74, 74, 0);  /* 호버 시에도 완전히 투명하게 설정 */
            }
        """)
        self.close_button.clicked.connect(self.main_window.closeApplication)

    def setupFrameSelection(self, main_layout):
        """프레임 선택 영역 설정"""
        frame_widget = QWidget()
        frame_layout = QVBoxLayout(frame_widget)
        
        # 제목
        title_label = QLabel("프레임을 선택하세요")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; margin: 20px; font-family: '{config['photo_frame']['font'] or self.font_family}';")
        frame_layout.addWidget(title_label)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        grid_layout = QGridLayout(scroll_widget)
        
        # 프레임 이미지들 로드
        self.loadFrameImages(grid_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        frame_layout.addWidget(scroll_area)
        
        frame_widget.setMaximumWidth(400)
        main_layout.addWidget(frame_widget)
    
    def loadFrameImages(self, grid_layout):
        """프레임 이미지들을 그리드로 로드 (클래식 레이아웃용)"""
        row, col = 0, 0
        for frame_path in self.frame_files:
            frame_button = self.createFrameButton(frame_path)
            grid_layout.addWidget(frame_button, row, col)
            
            col += 1
            if col >= 2:  # 2열로 배치
                col = 0
                row += 1
    
    def createFrameButton(self, frame_path):
        """프레임 선택 버튼 생성"""
        button = QPushButton()
        button.setFixedSize(150, 150)
        
        # 프레임 미리보기 이미지 로드
        pixmap = QPixmap(frame_path)
        button.setIcon(pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        button.setIconSize(QSize(140, 140))
        
        button.clicked.connect(lambda: self.selectFrame(frame_path))
        button.setStyleSheet("""
            QPushButton {
                border: 3px solid #ddd;
                border-radius: 10px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #00FFC2;
            }
            QPushButton:pressed {
                background-color: #f0f0f0;
            }
        """)
        
        return button
    
    def setupPreview(self, main_layout):
        """미리보기 영역 설정"""
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setSpacing(10)  # 간격 조정
        preview_layout.setContentsMargins(20, 20, 20, 20)  # 여백 추가
        
        # 제목
        title_label = QLabel("미리보기")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"font-size: 32px; font-weight: bold; margin-bottom: 10px; color: #333; font-family: '{config['photo_frame']['font'] or self.font_family}';")
        preview_layout.addWidget(title_label)
        
        # 미리보기 이미지 라벨 - 더 크게 증가
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(config["photo_frame"]["width"], config["photo_frame"]["height"])  # 600x450에서 800x600으로 더 크게 증가
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            border: 3px solid #00FFC2; 
            background-color: #f9f9f9; 
            border-radius: 10px;
            font-size: 18px;
            color: #666;
        """)
        self.preview_label.setText("프레임을 선택하면\n미리보기가 나타납니다")
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
        
        # 하단 버튼 레이아웃
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignCenter)

        # 다시 촬영 버튼
        self.retake_button = QPushButton("다시 촬영")
        self.retake_button.setFixedSize(150, 50)
        self.retake_button.clicked.connect(self.onRetake)
        self.retake_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        buttons_layout.addWidget(self.retake_button)

        # 확인 버튼
        self.confirm_button = QPushButton("선택 완료")
        self.confirm_button.setFixedSize(150, 50)
        self.confirm_button.clicked.connect(self.onConfirm)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #00FFC2;
                color: black;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #00E6A8;
            }
        """)
        buttons_layout.addWidget(self.confirm_button)
        
        preview_layout.addLayout(buttons_layout)

        # 여백 추가하여 버튼과 충돌 방지
        preview_layout.addStretch()
        
        # 초기 사진만 표시 (showEvent로 이동하여 파일 로드 시점 문제를 해결)
        # self.showCapturedPhoto()
        
        main_layout.addWidget(preview_widget)

    def selectFrame(self, frame_path):
        """프레임 선택 시 호출"""
        self.selected_frame = frame_path
        self.updatePreview()
    
    def updatePreview(self):
        """미리보기 업데이트"""
        if not self.selected_frame or not os.path.exists(self.captured_photo_path):
            return
            
        try:
            # PIL로 이미지 합성
            composite_image = self.compositeImages(self.captured_photo_path, self.selected_frame)
            
            # Qt로 변환하여 표시
            qt_image = ImageQt.ImageQt(composite_image)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"미리보기 생성 오류: {e}")
    
    def compositeImages(self, photo_path, frame_path):
        """사진과 프레임을 합성"""
        # 배경 사진 로드
        background = Image.open(photo_path).convert("RGBA")
        # 프레임 로드
        frame = Image.open(frame_path).convert("RGBA")
        
        # 크기 조정 (프레임 크기에 맞춤)
        background = background.resize(frame.size, Image.LANCZOS)
        
        # 알파 합성
        result = Image.alpha_composite(background, frame)
        return result.convert("RGB")
    
    def showCapturedPhoto(self):
        """촬영된 사진을 프레임 크기에 맞춰서 미리 표시"""
        if not os.path.exists(self.captured_photo_path):
            if hasattr(self, 'preview_label') and self.preview_label:
                self.preview_label.setText("캡처된 이미지를 찾을 수 없습니다.")
            return

        try:
            if not self.frame_files:
                # 프레임이 없으면 원본 사진을 그대로 표시
                pixmap = QPixmap(self.captured_photo_path)
                scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled_pixmap)
                return

            # 첫 번째 프레임의 크기를 기준으로 사진 리사이즈
            with Image.open(self.frame_files[0]) as frame_img:
                frame_size = frame_img.size

            with Image.open(self.captured_photo_path) as photo_img:
                # 사진을 프레임 크기에 맞춤
                resized_photo = photo_img.resize(frame_size, Image.LANCZOS)

                # PIL 이미지를 QPixmap으로 변환
                qt_image = ImageQt.ImageQt(resized_photo.convert("RGB"))
                pixmap = QPixmap.fromImage(qt_image)

                # 라벨 크기에 맞춰 최종 표시
                scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled_pixmap)

        except Exception as e:
            print(f"사진 미리보기 오류: {e}")
            # 오류 발생 시 원본 사진 표시
            pixmap = QPixmap(self.captured_photo_path)
            scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
    
    def onRetake(self):
        """다시 촬영 버튼 클릭 시"""
        # 카메라 화면으로 돌아가기 (스택 인덱스 2 = photo_screen)
        # screen_order에서 카메라(1)의 위치로 current_index도 업데이트
        camera_stack_index = 2
        camera_screen_order = 1  # screen_order에서 카메라 화면 값

        # main_window의 current_index를 카메라 화면 위치로 설정
        if camera_screen_order in config["screen_order"]:
            self.main_window.current_index = config["screen_order"].index(camera_screen_order)

        self.stack.setCurrentIndex(camera_stack_index)

    def onConfirm(self):
        """확인 버튼 클릭 시"""
        if self.selected_frame:
            # 프레임 적용된 이미지 저장
            framed_image = self.compositeImages(self.captured_photo_path, self.selected_frame)
            framed_photo_path = "resources/framed_photo.jpg"
            framed_image.save(framed_photo_path, "JPEG", quality=95)
            
            # 다음 화면으로 이동
            next_index = self.main_window.getNextScreenIndex()
            self.stack.setCurrentIndex(next_index)
        else:
            # 프레임 선택 안내
            QMessageBox.warning(self, "알림", "프레임을 선택해주세요!")

    def cleanup(self):
        """프레임 화면 리소스 정리"""
        try:
            print("FrameScreen 리소스 정리 중...")
            
            # 미디어 플레이어 정리
            if hasattr(self, 'media_player') and self.media_player:
                self.media_player.stop()
                self.media_player.deleteLater()
                self.media_player = None
            
            # 오디오 출력 정리
            if hasattr(self, 'audio_output') and self.audio_output:
                self.audio_output.deleteLater()
                self.audio_output = None
            
            # 배경 위젯 정리
            if hasattr(self, 'background_widget') and self.background_widget:
                self.background_widget.deleteLater()
                self.background_widget = None
            
            # 프레임 버튼들 정리
            if hasattr(self, 'frame_buttons') and self.frame_buttons:
                for button in self.frame_buttons:
                    if button:
                        button.deleteLater()
                self.frame_buttons = []
            
            # 선택된 프레임 관련 정리
            if hasattr(self, 'selected_frame_index'):
                self.selected_frame_index = None
            
            print("FrameScreen 리소스 정리 완료")
            
        except Exception as e:
            print(f"FrameScreen cleanup 오류: {e}")