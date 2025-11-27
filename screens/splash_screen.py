from PySide6.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect, QPushButton
from PySide6.QtGui import QPixmap, QFont, QFontDatabase, QMovie
from PySide6.QtCore import Qt, QPropertyAnimation, QSequentialAnimationGroup
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
from config import config, language_manager

class SplashScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.background_widget = None  # 배경 위젯 추적을 위한 변수
        self.media_player = None  # 미디어 플레이어 추적을 위한 변수
        self.lang_buttons = {}  # 언어 선택 버튼
        self.loadCustomFont()
        self.setupUI()
        self.startAnimation()

    def loadCustomFont(self):
        """커스텀 폰트 로드"""
        font_name = config["splash"]["font"]
        font_path = os.path.join("resources", "font", font_name)
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            else:
                self.font_family = "맑은 고딕"  # 폰트 로드 실패 시 기본 폰트
        else:
            self.font_family = "맑은 고딕"  # 폰트 파일이 없을 때 기본 폰트

    def setupUI(self):
        self.setupBackground()
        self.addCloseButton()
        self.splash_label = self.createSplashLabel()
        self.splash_label.setGeometry(config["splash"]["x"], config["splash"]["y"], self.splash_label.sizeHint().width(), self.splash_label.sizeHint().height())

        # 언어 선택 버튼 추가 (활성화된 경우)
        if language_manager.is_enabled():
            self.setupLanguageButtons()
    
    def setupBackground(self):
        background_file = None

        # 언어 선택 모드가 활성화된 경우 언어별 배경 먼저 확인
        if language_manager.is_enabled():
            lang_path = language_manager.get_background_path(0)  # splash screen = index 0
            if lang_path:
                background_file = lang_path

        # 언어별 배경이 없으면 기본 배경 파일들 확인
        if background_file is None:
            background_files = [
                "background/0.mp4", "background/0.gif", "background/0.png", "background/0.jpg",
                "background/splash_bg.mp4", "background/splash_bg.gif", "background/splash_bg.png", "background/splash_bg.jpg"
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
    
    def setupGifBackground(self, gif_path):
        """GIF 애니메이션 배경 설정"""
        self.background_widget = QLabel(self)
        self.background_widget.resize(*self.screen_size)
        
        movie = QMovie(gif_path)
        movie.setScaledSize(self.background_widget.size())
        self.background_widget.setMovie(movie)
        self.background_widget.setScaledContents(True)
        movie.start()
    
    def setupImageBackground(self, image_path):
        """일반 이미지 배경 설정"""
        self.background_widget = QLabel(self)
        pixmap = QPixmap(image_path)
        self.background_widget.setPixmap(pixmap)
        self.background_widget.setScaledContents(True)
        self.background_widget.resize(*self.screen_size)
    
    def onVideoStatusChanged(self, status):
        """비디오 상태 변경 시 호출 (루프 재생을 위해)"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()

    def createSplashLabel(self):
        splash_label = QLabel(self)  # 부모 위젯을 self로 지정

        # 언어 선택 모드가 활성화된 경우 언어별 문구 사용
        if language_manager.is_enabled():
            phrase = language_manager.get_phrase("splash_phrase")
        else:
            phrase = config["splash"]["phrase"]

        splash_label.setText(phrase if phrase else config["splash"]["phrase"])
        
        # 커스텀 폰트 적용
        custom_font = QFont(self.font_family)
        custom_font.setPointSize(config["splash"]["font_size"])
        splash_label.setFont(custom_font)
        
        # 스타일시트 수정 (폰트 패밀리 제거)
        splash_label_style = f""" color: {config["splash"]["font_color"]};"""
        splash_label.setStyleSheet(splash_label_style)
        splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.opacity_effect = QGraphicsOpacityEffect(splash_label)
        splash_label.setGraphicsEffect(self.opacity_effect)

        return splash_label
    
    def startAnimation(self):
        # 🔹 애니메이션 설정 (opacity: 0.3 → 1.0)
        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(1000)  # 1초 동안 변화
        fade_in.setStartValue(0.3)
        fade_in.setEndValue(1.0)

        # 🔹 두 번째 애니메이션 (1.0 → 0.3)
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(1000)  # 1초 동안 변화
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.3)

        # 🔹 애니메이션 그룹 (순차 실행)
        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(fade_in)
        self.animation_group.addAnimation(fade_out)
        self.animation_group.setLoopCount(-1)  # 무한 반복
        self.animation_group.start()

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

    def setupLanguageButtons(self):
        """언어 선택 버튼 생성"""
        lang_config = config.get("language", {})

        for lang_code in ["ko", "en"]:
            btn_config = lang_config.get(f"{lang_code}_button", {})

            # 기본값
            defaults = {
                "text": "한글" if lang_code == "ko" else "English",
                "x": 340,
                "y": 800 if lang_code == "ko" else 960,
                "width": 400,
                "height": 120,
                "font_size": 48,
                "font_color": "#ffffff",
                "bg_color": "#2563eb" if lang_code == "ko" else "#059669",
                "border_color": "#1d4ed8" if lang_code == "ko" else "#047857",
                "border_width": 3,
                "border_radius": 15
            }

            # 버튼 생성
            btn = QPushButton(btn_config.get("text", defaults["text"]), self)

            # 위치 및 크기 설정
            x = btn_config.get("x", defaults["x"])
            y = btn_config.get("y", defaults["y"])
            width = btn_config.get("width", defaults["width"])
            height = btn_config.get("height", defaults["height"])
            btn.setGeometry(x, y, width, height)

            # 스타일 설정
            font_size = btn_config.get("font_size", defaults["font_size"])
            font_color = btn_config.get("font_color", defaults["font_color"])
            bg_color = btn_config.get("bg_color", defaults["bg_color"])
            border_color = btn_config.get("border_color", defaults["border_color"])
            border_width = btn_config.get("border_width", defaults["border_width"])
            border_radius = btn_config.get("border_radius", defaults["border_radius"])

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {font_color};
                    font-size: {font_size}px;
                    font-weight: bold;
                    border: {border_width}px solid {border_color};
                    border-radius: {border_radius}px;
                }}
                QPushButton:hover {{
                    background-color: {border_color};
                }}
                QPushButton:pressed {{
                    background-color: {font_color};
                    color: {bg_color};
                }}
            """)

            # 클릭 이벤트 연결
            btn.clicked.connect(lambda checked, lc=lang_code: self.onLanguageSelected(lc))

            # 버튼 저장
            self.lang_buttons[lang_code] = btn

    def onLanguageSelected(self, lang_code: str):
        """언어 선택 시 호출"""
        print(f"언어 선택: {lang_code}")

        # 언어 설정
        language_manager.current_language = lang_code

        # 다음 화면으로 이동
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)

    def mousePressEvent(self, event):
        # 언어 선택 모드가 활성화되어 있으면 화면 터치로 넘어가지 않음
        if language_manager.is_enabled():
            return

        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)

    def cleanup(self):
        """스플래시 화면 리소스 정리"""
        try:
            print("SplashScreen 리소스 정리 중...")
            
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
            
            # 타이머 정리
            if hasattr(self, 'timer') and self.timer:
                self.timer.stop()
                self.timer.deleteLater()
                self.timer = None
            
            print("SplashScreen 리소스 정리 완료")
            
        except Exception as e:
            print(f"SplashScreen cleanup 오류: {e}")
            