from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QGridLayout, QMessageBox)
from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QPixmap, QFont, QFontDatabase, QMovie
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PIL import Image, ImageQt

from config import config
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
        self.captured_photo_path = "resources/captured_image.jpg"  # 촬영된 사진 경로
        self.selected_frame = None
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
        
        # 메인 레이아웃
        main_layout = QHBoxLayout(self)
        
        # 왼쪽: 프레임 선택 영역
        self.setupFrameSelection(main_layout)
        
        # 오른쪽: 미리보기 영역
        self.setupPreview(main_layout)
        
        # 하단 버튼들
        self.setupButtons()
        self.addCloseButton()
        
    def setupBackground(self):
        # 지원하는 배경 파일들 (우선순위 순)
        background_files = [
            "background/5.mp4", "background/5.gif", "background/5.png", "background/5.jpg",
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
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
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
        """프레임 이미지들을 그리드로 로드"""
        frame_files = glob.glob("resources/frames/*.png")
        
        row, col = 0, 0
        for frame_path in frame_files:
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
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 10px; color: #333;")
        preview_layout.addWidget(title_label)
        
        # 미리보기 이미지 라벨 - 더 크게 증가
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(800, 600)  # 600x450에서 800x600으로 더 크게 증가
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
        
        # 여백 추가하여 버튼과 충돌 방지
        preview_layout.addStretch()
        
        # 초기 사진만 표시 (showEvent로 이동하여 파일 로드 시점 문제를 해결)
        # self.showCapturedPhoto()
        
        main_layout.addWidget(preview_widget)

    def showEvent(self, event):
        """위젯이 화면에 표시될 때 호출되어, 파일 생성 지연 문제를 해결합니다."""
        super().showEvent(event)
        self.showCapturedPhoto()
        event.accept()
    
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
            self.preview_label.setText("캡처된 이미지를 찾을 수 없습니다.")
            return

        try:
            # 사용 가능한 첫 번째 프레임의 크기를 가져옴
            frame_files = glob.glob("resources/frames/*.png")
            if not frame_files:
                # 프레임이 없으면 원본 사진을 그대로 표시
                pixmap = QPixmap(self.captured_photo_path)
                scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled_pixmap)
                return

            # 첫 번째 프레임의 크기를 기준으로 사진 리사이즈
            with Image.open(frame_files[0]) as frame_img:
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
    
    def setupButtons(self):
        """하단 버튼들 설정"""
        # 확인 버튼
        self.confirm_button = QPushButton("선택 완료", self)  # 부모 위젯 명시적 설정
        self.confirm_button.setFixedSize(150, 50)
        self.confirm_button.move(self.screen_size[0] - 200, self.screen_size[1] - 100)
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
        self.confirm_button.raise_()  # 버튼을 맨 앞으로 가져오기
        self.confirm_button.show()    # 명시적으로 보이기
        
        # 다시 촬영 버튼
        self.retake_button = QPushButton("다시 촬영", self)  # 부모 위젯 명시적 설정
        self.retake_button.setFixedSize(150, 50)
        self.retake_button.move(50, self.screen_size[1] - 100)
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
        self.retake_button.raise_()  # 버튼을 맨 앞으로 가져오기
        self.retake_button.show()    # 명시적으로 보이기
    
    def onConfirm(self):
        """확인 버튼 클릭 시"""
        if self.selected_frame:
            # 최종 합성 이미지 저장
            final_image = self.compositeImages(self.captured_photo_path, self.selected_frame)
            final_path = "resources/final_photo.jpg"
            final_image.save(final_path, "JPEG", quality=95)
            
            # 다음 화면으로 이동
            next_index = self.main_window.getNextScreenIndex()
            self.stack.setCurrentIndex(next_index)
        else:
            # 프레임 선택 안내
            QMessageBox.warning(self, "알림", "프레임을 선택해주세요!")
    
    def onRetake(self):
        """다시 촬영 버튼 클릭 시"""
        # 카메라 화면으로 돌아가기
        camera_index = 1  # config에서 카메라 화면 인덱스 가져오기
        self.stack.setCurrentIndex(camera_index)