from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QFont, Qt, QFontDatabase, QMovie
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from config import config
import os

class CompleteScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.background_widget = None  # 배경 위젯 추적을 위한 변수
        self.media_player = None  # 미디어 플레이어 추적을 위한 변수
        self.loadCustomFont()
        self.setupUI()

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

    def setupUI(self):
        self.setupBackground()
        self.addCloseButton()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.complete_label = self.createCompleteLabel()
        self.complete_label.setGeometry(config["complete"]["x"], config["complete"]["y"],
                                       self.complete_label.sizeHint().width(), self.complete_label.sizeHint().height())

    def setupBackground(self):
        # 지원하는 배경 파일들 (우선순위 순)
        background_files = [
            "background/6.mp4", "background/6.gif", "background/6.png", "background/6.jpg",
            "background/complete_bg.mp4", "background/complete_bg.gif", "background/complete_bg.png", "background/complete_bg.jpg"
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
    
    def createCompleteLabel(self):
        complete_label = QLabel(self)  # 부모 위젯을 self로 지정
        complete_label.setText(config["complete"]["phrase"])
        
        # 커스텀 폰트 적용
        custom_font = QFont(self.font_family)
        custom_font.setPointSize(config["complete"]["font_size"])
        complete_label.setFont(custom_font)
        
        # 스타일시트 수정 (폰트 패밀리 제거)
        complete_label_style = f""" color: {config["complete"]["font_color"]};"""
        complete_label.setStyleSheet(complete_label_style)
        complete_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return complete_label
        
    def getNextScreenIndex(self):
        self.current_index = 0
        return config["screen_order"][self.current_index]
    
    def showEvent(self, event):
        """화면이 표시될 때 2초 후 스플래시 화면으로 이동"""
        next_index = self.main_window.getNextScreenIndex()
        # print(f"완료 화면에서 다음 인덱스: {next_index}, 타이머: {config['complete']['complete_time']}ms")
        QTimer.singleShot(config["complete"]["complete_time"], 
                        lambda: self.stack.setCurrentIndex(next_index))

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