from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QMovie
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from components.hangul_composer import HangulComposer
from components.virtual_keyboard import VirtualKeyboard
from config import config
import os

class CustomLineEdit(QLineEdit):
    def __init__(self, parent=None, index=0, on_focus=None):
        super().__init__(parent)
        self.index = index
        self.on_focus = on_focus
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.on_focus:
            self.on_focus(self)

class TextInputScreen(QWidget):
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        self.active_input = None  # 현재 활성화된 입력 필드
        self.text_inputs = []  # 모든 텍스트 입력 필드 관리
        self.keyboard = None
        self.background_widget = None  # 배경 위젯 추적을 위한 변수
        self.media_player = None  # 미디어 플레이어 추적을 위한 변수
        self.setupUI()
    
    def setupUI(self):
        self.setupBackground()
        self.addCloseButton()

        # 커서 변경 이벤트를 연결할 입력 필드 리스트 초기화
        self.text_inputs = []
        
        # 입력 필드 개수
        input_count = config["text_input"]["count"]
        
        # 여러 개의 텍스트 입력 필드 생성
        for i in range(input_count):
            # config.json에서 설정 가져오기
            item_config = config["text_input"]["items"][i] if i < len(config["text_input"]["items"]) else {}
            
            # 레이블 추가 (있는 경우)
            if "label" in item_config:
                label = QLabel(item_config["label"], self)
                # 레이블 위치 설정 (입력 필드 왼쪽)
                label_x = item_config.get("screen_x", item_config.get("x", 0)) - 150  # 화면용 좌표 우선 사용
                label_y = item_config.get("screen_y", item_config.get("y", 0))
                label.setGeometry(label_x, label_y, 140, 40)
                label.setStyleSheet("color: black; font-size: 18px;")
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # 텍스트 입력 필드 생성 (CustomLineEdit 사용)
            text_input = CustomLineEdit(self, i, self.input_focus_received)
            
            # 화면용 위치 및 크기 설정 (screen_* 값 우선 사용)
            width = item_config.get("screen_width", item_config.get("width", 300))
            height = item_config.get("screen_height", item_config.get("height", 80))
            x = item_config.get("screen_x", item_config.get("x", 0))
            y = item_config.get("screen_y", item_config.get("y", 0))
            
            text_input.setGeometry(x, y, width, height)
            text_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_input.setFont(QFont('맑은 고딕', item_config.get("font_size", 36)))
            
            # 플레이스홀더 설정 (있는 경우)
            if "placeholder" in item_config:
                text_input.setPlaceholderText(item_config["placeholder"])
            
            text_input.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 2px solid #00FFC2;
                    border-radius: 10px;
                    padding: 5px;
                }
            """)
            
            # 입력 필드 리스트에 추가
            self.text_inputs.append(text_input)
        
        # 가상 키보드 초기화 (첫 번째 입력 필드 연결)
        if self.text_inputs:
            self.active_input = self.text_inputs[0]
            self.active_input.setFocus()
            
            self.keyboard = VirtualKeyboard(self.active_input)
            self.keyboard.setGeometry(
                config["keyboard"]["x"],
                config["keyboard"]["y"],
                config["keyboard"]["width"],
                config["keyboard"]["height"]
            )
            self.keyboard.setParent(self)
    
    def input_focus_received(self, input_field):
        """입력 필드가 포커스를 받았을 때 호출됨"""
        # print(f"포커스 변경: 인덱스 {input_field.index}로 변경")
        self.active_input = input_field
        
        # 키보드의 대상 입력 필드 변경
        if self.keyboard:
            self.keyboard.input_widget = input_field
            self.keyboard.hangul_composer.reset()  # 한글 작성기 초기화
            self.keyboard.bumper = True  # 새 입력 필드로 전환 시 bumper 플래그 설정
    
    def confirm_pressed(self, event):
        # 모든 입력 필드의 텍스트 저장
        input_texts = {}
        for i, input_field in enumerate(self.text_inputs):
            input_texts[f"text_{i+1}"] = input_field.text()
        
        # JSON 형식으로 저장
        import json
        with open("resources/input_texts.json", "w", encoding="utf-8") as f:
            json.dump(input_texts, f, ensure_ascii=False)
        
        # 다음 화면으로 이동
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
    
    def setupBackground(self):
        # 지원하는 배경 파일들 (우선순위 순)
        background_files = [
            "background/2.mp4", "background/2.gif", "background/2.png", "background/2.jpg",
            "background/text_input_bg.mp4", "background/text_input_bg.gif", "background/text_input_bg.png", "background/text_input_bg.jpg"
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
    
    def showEvent(self, event):
        # When screen becomes visible, make sure keyboard is shown
        if self.keyboard:
            self.keyboard.show()
        if self.active_input:
            self.active_input.setFocus()
            
        # Clear any previous text
        for input_field in self.text_inputs:
            input_field.clear()
    
    def hideEvent(self, event):
        # When screen is hidden, hide the keyboard
        if self.keyboard:
            self.keyboard.hide()