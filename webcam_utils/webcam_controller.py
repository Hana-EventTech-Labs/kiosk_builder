import cv2
import logging
from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap, QMouseEvent
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
import time
import os
from config import config

def initialize_camera(camera_index=0, width=1920, height=1080, fps=60):
    """카메라 초기화 및 최적화"""
    camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera = cv2.VideoCapture(camera_index)
    
    if camera.isOpened():
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config["camera_size"]["width"])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config["camera_size"]["height"])

        # 실제 설정된 해상도 확인
        actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # print(f"설정된 해상도: {actual_width}x{actual_height}")

        camera.set(cv2.CAP_PROP_FPS, fps)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # 기본값 유지, 필요 시 변경 가능
        camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # 자동 노출을 부드럽게 조정
        for _ in range(5):  # 프레임 버퍼 줄이기
            camera.read()
        logging.info("카메라 초기화 완료")
        return camera
    logging.error("카메라 초기화 실패")
    return None

def get_frame(camera):
    """최신 프레임을 반환"""
    if camera and camera.isOpened():
        ret, frame = camera.read()
        if ret:
            return cv2.flip(frame, 1)  # 좌우 반전
    return None

def release_camera(camera):
    """카메라 자원 해제"""
    if camera and camera.isOpened():
        camera.release()
        logging.info("카메라 해제 완료")

def capture_and_save_photo(camera, save_path="resources/captured_image.jpg", x=0, y=0, width=None, height=None):
    """현재 카메라 인스턴스를 사용하여 사진 촬영 후 저장, 특정 영역만 캡처 가능"""
    frame = get_frame(camera)
    if frame is not None:
        h, w = frame.shape[:2]
        # print(h, w)
        # print("x", x, "y", y)
        # print("height", height, "width", width)
        frame = frame[int(y):int(y+height), int(x):int(x+width)]
        # print(frame.shape)
        # timestamp = time.strftime("%Y%m%d_%H%M%S")
        # 파일 이름과 경로 분리
        dir_path = os.path.dirname(save_path)
        file_name = os.path.basename(save_path)
        # file_name = file_name.replace(".jpg", f"_{timestamp}.jpg")
        file_path = os.path.join(dir_path, file_name)
        
        # 디렉토리가 없으면 생성
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        cv2.imwrite(file_path, frame)
        # logging.info(f"📸 사진 저장 완료: {file_path}")
        return file_path
    logging.error("사진 촬영 실패")
    return None

class CountdownThread(QThread):
    countdown_signal = Signal(int)
    finished_signal = Signal()

    def __init__(self, countdown_time):
        super().__init__()
        self.countdown_time = countdown_time
        self.is_running = True

    def run(self):
        for i in range(self.countdown_time, 0, -1):
            if not self.is_running:
                break
            self.countdown_signal.emit(i)
            time.sleep(1)
        if self.is_running:
            self.finished_signal.emit()
            
    def stop(self):
        """스레드 실행 중지"""
        self.is_running = False

class WebcamViewer(QWidget):
    """PyQt를 이용한 실시간 웹캠 프리뷰"""
    # 사진 촬영 완료 시그널 추가
    photo_captured_signal = Signal(str)
    
    def __init__(self, camera_index=0, preview_width=640, preview_height=480, capture_width=None, capture_height=None, x=0, y=0, countdown=0):
        super().__init__()
        self.setWindowTitle("Webcam Viewer")
        self.setGeometry(x, y, preview_width, preview_height)  # 윈도우 위치 및 크기 설정
        
        # 프리뷰 크기와 캡처 크기를 별도로 저장
        self.preview_width = preview_width
        self.preview_height = preview_height
        self.capture_width = capture_width if capture_width is not None else preview_width
        self.capture_height = capture_height if capture_height is not None else preview_height
        
        # 캡처 영역 좌표
        self.capture_x = x
        self.capture_y = y
        
        # 카메라 초기화 - 프리뷰 크기로 설정
        self.camera = initialize_camera(camera_index, preview_width, preview_height)
        
        # 프리뷰 레이블 - 프리뷰 크기로 설정 및 정확한 위치에 배치
        self.preview_label = QLabel(self)
        self.preview_label.setFixedSize(preview_width, preview_height)
        self.preview_label.move(0, 0)  # 정확히 0,0 위치에 배치

        self.countdown_label = QLabel(self)
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet(
            f"font-size: {config['camera_count']['font_size']}px;"
            f"color: {config['camera_count']['font_color']};"
        )  # 글자 크기 조정
        self.countdown_label.setGeometry(0, 0, preview_width, preview_height)  # 중앙 상단 배치
        self.countdown_label.hide()
        
        self.countdown_time = countdown
        self.countdown_thread = None  # 카운트다운 스레드 초기화
        
        # 레이아웃 제거하고 직접 위치 지정
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)  # 60fps
    
    def set_capture_area(self, x, y, width, height):
        self.capture_x = (config["camera_size"]["width"] - width) / 2
        self.capture_y = (config["camera_size"]["height"] - height) / 2
    
    def update_frame(self):
        frame = get_frame(self.camera)
        if frame is not None:
            # 프레임을 프리뷰 크기로 리사이즈
            resized_frame = cv2.resize(frame, (self.preview_width, self.preview_height))
            rgb_image = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            qimage = QImage(rgb_image.data, w, h, w * ch, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            self.preview_label.setPixmap(pixmap)
    
    def mousePressEvent(self, event: QMouseEvent):
        """마우스로 클릭 시 사진 촬영 (카운트다운 적용)"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 이미 카운트다운 중인지 확인
            if hasattr(self, 'countdown_thread') and self.countdown_thread is not None and self.countdown_thread.isRunning():
                return  # 이미 카운트다운 중이면 무시
                
            if self.countdown_time > 0:
                self.countdown_label.show()
                self.countdown_thread = CountdownThread(self.countdown_time)
                self.countdown_thread.countdown_signal.connect(self.update_countdown)
                self.countdown_thread.finished_signal.connect(self.capture_photo)
                self.countdown_thread.start()
            else:
                self.capture_photo()
    
    def update_countdown(self, count):
        """카운트다운 업데이트"""
        self.countdown_label.setText(str(count))
        self.countdown_label.show()  # 카운트다운 라벨이 보이도록 확실히 함

    def capture_photo(self):
        """사진 촬영 후 카운트다운 숨기기"""
        self.countdown_label.hide()
        self.countdown_label.setText("")  # 텍스트 초기화
        self.set_capture_area(self.capture_x, self.capture_y, self.capture_width, self.capture_height)
        # 설정된 캡처 영역으로 사진 촬영
        file_path = capture_and_save_photo(
            self.camera, 
            "resources/captured_image.jpg", 
            x=self.capture_x, 
            y=self.capture_y, 
            width=self.capture_width, 
            height=self.capture_height
        )
        if file_path:
            # print(self.capture_x, self.capture_y, self.capture_width, self.capture_height)
            # print(f"📸 사진 저장 완료: {file_path}")
            # 사진 촬영 완료 시그널 발생
            self.photo_captured_signal.emit(file_path)
            
    def reset_countdown(self):
        """카운트다운 상태 초기화"""
        if hasattr(self, 'countdown_thread') and self.countdown_thread and self.countdown_thread.isRunning():
            self.countdown_thread.stop()  # 실행 중인 스레드 종료
            self.countdown_thread.wait()  # 스레드가 완전히 종료될 때까지 대기
        self.countdown_label.hide()
        self.countdown_label.setText("")  # 텍스트 초기화
        self.countdown_thread = None
    
    def closeEvent(self, event):
        """창 닫을 때 카메라 해제"""
        self.timer.stop()
        release_camera(self.camera)
        event.accept()
