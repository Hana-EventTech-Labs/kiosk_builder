from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QMovie
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from webcam_utils.webcam_controller import WebcamViewer
from config import config, language_manager
import os

class CameraScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.background_widget = None  # 배경 위젯 추적을 위한 변수
        self.media_player = None  # 미디어 플레이어 추적을 위한 변수
        self._background_initialized = False  # 배경 지연 초기화 플래그
        self._last_language = None  # 마지막으로 로드된 언어 추적
        self.setupUI()

    def showEvent(self, event):
        """화면이 표시될 때 배경 초기화 (언어 변경 시 갱신)"""
        current_lang = language_manager.current_language

        # 배경이 초기화되지 않았거나 언어가 변경된 경우 배경 갱신
        if not self._background_initialized or self._last_language != current_lang:
            # 기존 배경 리소스 정리
            self._cleanupBackground()
            # 새 배경 설정
            self.setupBackground()
            self._background_initialized = True
            self._last_language = current_lang
        super().showEvent(event)

    def _cleanupBackground(self):
        """기존 배경 리소스 정리"""
        # 미디어 플레이어 정리
        if self.media_player:
            self.media_player.stop()
            self.media_player.deleteLater()
            self.media_player = None

        # 오디오 출력 정리
        if hasattr(self, 'audio_output') and self.audio_output:
            self.audio_output.deleteLater()
            self.audio_output = None

        # 배경 위젯 정리
        if self.background_widget:
            self.background_widget.deleteLater()
            self.background_widget = None

    def setupUI(self):
        # 배경은 showEvent에서 초기화 (언어 선택 후)
        # preview_width는 widget의 너비이고 camera_width는 카메라 화질의 너비입니다
        # 프리뷰 크기가 카메라 전체 크기가 아니니 참고 바랍니다 (카메라 크기는 config.json에 있습니다)
        self.preview_width = config["frame"]["width"]
        self.preview_height = config["frame"]["height"]
        self.camera_width = config["camera_size"]["width"]
        self.camera_height = config["camera_size"]["height"]
        if 1 in config["screen_order"]:
            self.webcam = WebcamViewer(
                preview_width=self.preview_width, 
                preview_height=self.preview_height, 
                camera_width=self.camera_width, 
                camera_height=self.camera_height, 
                x=config["frame"]["x"], 
                y=config["frame"]["y"], 
                countdown=config["camera_count"]["number"]
            )
            self.webcam.setParent(self)
            self.webcam.setGeometry(config["frame"]["x"], config["frame"]["y"], self.preview_width, self.preview_height)
            self.webcam.photo_captured_signal.connect(self.onPhotoCaptured)
        self.addCloseButton()


    
    def setupBackground(self):
        background_file = None

        # 디버그: 현재 언어 상태 출력
        print(f"[CameraScreen] setupBackground 호출 - 현재 언어: {language_manager.current_language}")
        print(f"[CameraScreen] 언어 기능 활성화: {language_manager.is_enabled()}")

        # 언어 선택 모드가 활성화된 경우 언어별 배경 먼저 확인
        if language_manager.is_enabled():
            lang_path = language_manager.get_background_path(1)  # camera screen = index 1
            print(f"[CameraScreen] 언어별 배경 경로: {lang_path}")
            if lang_path:
                background_file = lang_path

        # 언어별 배경이 없으면 기본 배경 파일들 확인
        if background_file is None:
            background_files = [
                "background/1.mp4", "background/1.gif", "background/1.png", "background/1.jpg",
                "background/photo_bg.mp4", "background/photo_bg.gif", "background/photo_bg.png", "background/photo_bg.jpg"
            ]

            for filename in background_files:
                file_path = f"resources/{filename}"
                if os.path.exists(file_path):
                    background_file = file_path
                    break

        print(f"[CameraScreen] 최종 배경 파일: {background_file}")

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
        
    def onPhotoCaptured(self):
        """사진이 촬영되었을 때 호출되는 함수"""
        # 현재 카메라 화면(인덱스 1)이 screen_order에서 몇 번째 위치인지 찾기
        current_screen = 1  # 카메라 화면 인덱스
        try:
            current_position = config["screen_order"].index(current_screen)
            self.main_window.current_index = current_position
        except ValueError:
            # screen_order에 카메라 화면이 없으면 0으로 설정
            self.main_window.current_index = 0
        
        # 다음 화면으로 이동
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)

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

    def cleanup(self):
        """카메라 화면 리소스 정리"""
        try:
            print("CameraScreen 리소스 정리 중...")
            
            # 웹캠 정리
            if hasattr(self, 'webcam') and self.webcam:
                if hasattr(self.webcam, 'timer') and self.webcam.timer:
                    self.webcam.timer.stop()
                if hasattr(self.webcam, 'camera') and self.webcam.camera:
                    self.webcam.camera.release()
                    self.webcam.camera = None
                self.webcam.deleteLater()
                self.webcam = None
            
            # 미디어 플레이어 정리
            if hasattr(self, 'media_player') and self.media_player:
                self.media_player.stop()
                self.media_player.deleteLater()
                self.media_player = None
            
            # 배경 위젯 정리
            if hasattr(self, 'background_widget') and self.background_widget:
                self.background_widget.deleteLater()
                self.background_widget = None
            
            print("CameraScreen 리소스 정리 완료")
            
        except Exception as e:
            print(f"CameraScreen cleanup 오류: {e}")
