from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QMovie
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from webcam_utils.webcam_controller import WebcamViewer
from config import config
import os

class CameraScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.background_widget = None  # 배경 위젯 추적을 위한 변수
        self.media_player = None  # 미디어 플레이어 추적을 위한 변수
        self.setupUI()
    
    def setupUI(self):
        self.setupBackground()
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
        # 지원하는 배경 파일들 (우선순위 순)
        background_files = [
            "background/1.mp4", "background/1.gif", "background/1.png", "background/1.jpg",
            "background/photo_bg.mp4", "background/photo_bg.gif", "background/photo_bg.png", "background/photo_bg.jpg"
        ]
        
        background_file = None
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
        
    def onPhotoCaptured(self):
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
