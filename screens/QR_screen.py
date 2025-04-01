from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QMessageBox
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QTimer, Signal
import qrcode
from PIL import Image
import io
import requests
import json
import threading
import websocket
from io import BytesIO
import uuid
import os
from config import config

# 서버 URL
SERVER_URL = "https://port-0-kiosk-builder-m47pn82w3295ead8.sel4.cloudtype.app"

class QR_screen(QWidget):
    # 이미지 업로드 시그널 정의
    image_uploaded_signal = Signal(str)
    
    def __init__(self, stack, screen_size, main_window):
        super().__init__()
        self.stack = stack
        self.screen_size = screen_size
        self.main_window = main_window
        
        # 이벤트 정보 초기화
        self.event_id = None
        self.event_name = None
        self.qr_url = None
        
        # 이미지 업로드 시그널 연결
        self.image_uploaded_signal.connect(self.display_uploaded_image)
        
        self.setupUI()
        
        # 화면 표시시 자동으로 이벤트 생성 및 QR 코드 표시
        QTimer.singleShot(500, self.create_event)
    
    def setupUI(self):
        self.setupBackground()
        self.addCloseButton()
        self.setupQRCode()
        self.setupPreviewArea()
        self.addPrintButton()
        self.addHomeButton()
    
    def setupBackground(self):
        background_files = ["background/3.png", "background/3.jpg", "background/qr_bg.jpg"]
        
        pixmap = None
        for filename in background_files:
            file_path = f"resources/{filename}"
            if os.path.exists(file_path):
                pixmap = QPixmap(file_path)
                break
        
        if pixmap is None or pixmap.isNull():
            pixmap = QPixmap()
        
        background_label = QLabel(self)
        background_label.setPixmap(pixmap)
        background_label.setScaledContents(True)
        background_label.resize(*self.screen_size)
    
    def setupQRCode(self):
        # QR 코드 라벨 생성
        self.qr_label = QLabel(self)
        
        # QR 코드 위치와 크기 설정
        qr_size = 350
        x_pos = (self.screen_size[0] - qr_size) // 4  # 왼쪽에 배치
        y_pos = (self.screen_size[1] - qr_size) // 2  # 화면 중앙
        self.qr_label.setGeometry(x_pos, y_pos, qr_size, qr_size)
        self.qr_label.setStyleSheet("background-color: white; border: 2px solid #ddd;")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setText("QR 코드 생성 중...")
    
    def setupPreviewArea(self):
        # 미리보기 영역 설정
        preview_width = config["qr"]["preview_width"]
        preview_height = config["qr"]["preview_height"]
        
        # 미리보기 위치 설정 - 오른쪽에 배치
        x_pos = config["qr"]["x"]
        y_pos = config["qr"]["y"]
        
        # 미리보기 제목 라벨
        preview_title = QLabel(self)
        preview_title.setGeometry(x_pos, y_pos - 40, preview_width, 30)
        preview_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_title.setStyleSheet("color: #333; font-size: 18px; font-weight: bold;")
        preview_title.setText("업로드된 이미지")
        
        # 미리보기 라벨 생성
        self.preview_label = QLabel(self)
        self.preview_label.setGeometry(x_pos, y_pos, preview_width, preview_height)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f5f5f5; border: 2px solid #ddd;")
        self.preview_label.setText("아직 업로드된 이미지가 없습니다")
    
    def create_event(self):
        try:
            # 키오스크 앱 이름을 이벤트 이름으로 사용
            event_name = f"{config['app_name']}"

            response = requests.post(
                f"{SERVER_URL}/api/events/register",
                params={"event_name": event_name}
            )

            if response.status_code == 200:
                event_data = response.json()
                self.event_id = event_data["event_id"]
                self.event_name = event_data["event_name"]
                self.qr_url = event_data["qr_url"]
                
                # QR 코드 생성
                self.generate_qr_code()
                
                # 웹소켓 연결 시작
                self.start_kiosk_websocket()
            else:
                print(f"이벤트 생성 실패: {response.text}")

        except Exception as e:
            print(f"이벤트 생성 중 오류 발생: {str(e)}")
    
    def generate_qr_code(self):
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.qr_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # PIL Image를 QPixmap으로 변환
            byte_arr = io.BytesIO()
            qr_img.save(byte_arr, format='PNG')
            qimage = QImage.fromData(byte_arr.getvalue())
            pixmap = QPixmap.fromImage(qimage)

            # QR 이미지를 QLabel에 표시
            self.qr_label.setPixmap(pixmap)
            self.qr_label.setScaledContents(True)

        except Exception as e:
            print(f"QR 코드 생성 중 오류 발생: {str(e)}")
    
    def start_kiosk_websocket(self):
        ws_url = f"{SERVER_URL.replace('https', 'wss')}/ws/kiosk/{self.event_id}"

        def on_message(ws, message):
            data = json.loads(message)
            print("[WebSocket] 수신:", data)
            if data.get("type") == "image_uploaded":
                image_url = f"{SERVER_URL}{data['image_url']}"
                # GUI 스레드에서 이미지 표시를 위해 시그널 사용
                self.image_uploaded_signal.emit(image_url)

        def on_open(ws):
            print("웹소켓 연결됨")

        def on_error(ws, error):
            print("웹소켓 오류:", error)

        def on_close(ws, close_status_code, close_msg):
            print("웹소켓 종료")

        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_open=on_open,
            on_error=on_error,
            on_close=on_close
        )
        threading.Thread(target=ws.run_forever, daemon=True).start()
    
    def display_uploaded_image(self, image_url):
        try:
            print(f"[이미지 표시 시도] {image_url}")
            response = requests.get(image_url)
            response.raise_for_status()

            img_data = BytesIO(response.content)
            
            # 간단한 파일명으로 이미지를 resources 폴더에 저장
            file_name = "qr_uploaded_image.jpg"
            save_path = os.path.join("resources", file_name)
            
            # 디렉토리가 존재하는지 확인하고 없으면 생성
            os.makedirs("resources", exist_ok=True)
            
            # 이미지 저장
            with open(save_path, 'wb') as f:
                f.write(img_data.getvalue())
            print(f"[이미지 저장 성공] {save_path}")
            
            # 이미지 표시 관련 코드
            img = QImage.fromData(img_data.getvalue())
            pixmap = QPixmap.fromImage(img)
            
            # 이미지 크기 조정
            pixmap = pixmap.scaled(config["qr"]["preview_width"], config["qr"]["preview_height"], 
                                Qt.AspectRatioMode.KeepAspectRatio, 
                                Qt.TransformationMode.SmoothTransformation)

            # 미리보기 라벨에 이미지 표시
            self.preview_label.setPixmap(pixmap)
            print("[이미지 표시 성공]")

            # 저장된 이미지 경로를 메인 윈도우에 저장해서 다른 화면에서도 접근 가능하게 함
            self.main_window.uploaded_image_path = save_path

            # 다음 화면으로 자동 이동
            # QTimer.singleShot(2000, lambda: self.stack.setCurrentIndex(self.main_window.getNextScreenIndex()))

        except Exception as e:
            print(f"[이미지 표시 및 저장 오류]: {e}")
            
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
    
    # 인쇄 버튼 추가
    def addPrintButton(self):
        self.print_button = QPushButton("인쇄", self)
        self.print_button.setFixedSize(200, 80)
        
        # 화면 하단 중앙에 배치
        x_pos = (self.screen_size[0] - 200) // 2
        y_pos = self.screen_size[1] - 120  # 하단에서 약간 위로
        
        self.print_button.move(x_pos, y_pos)
        self.print_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)
        
        # 버튼 클릭 이벤트 연결
        self.print_button.clicked.connect(self.on_print_button_clicked)
    
    def on_print_button_clicked(self):
        # 미리보기 위젯의 이미지 지우기
        self.preview_label.setPixmap(QPixmap())  # 먼저 이미지 제거
        self.preview_label.setText("아직 업로드된 이미지가 없습니다")  # 그 다음 텍스트 설정
        
        # 다음 화면으로 이동
        next_index = self.main_window.getNextScreenIndex()
        self.stack.setCurrentIndex(next_index)
    
    # "처음으로" 버튼 추가
    def addHomeButton(self):
        self.home_button = QPushButton("처음으로", self)
        self.home_button.setFixedSize(200, 80)
        
        # 화면 하단 왼쪽에 배치
        x_pos = 50
        y_pos = self.screen_size[1] - 120  # 하단에서 약간 위로
        
        self.home_button.move(x_pos, y_pos)
        self.home_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1d6fa5;
            }
        """)
        
        # 버튼 클릭 이벤트 연결
        self.home_button.clicked.connect(self.on_home_button_clicked)
    
    def on_home_button_clicked(self):
        # 미리보기 위젯의 이미지 지우기
        self.preview_label.setPixmap(QPixmap())  # 먼저 이미지 제거
        self.preview_label.setText("아직 업로드된 이미지가 없습니다")  # 그 다음 텍스트 설정
        
        # 현재 인덱스를 초기화 (첫 화면 이전으로 설정)
        self.main_window.current_index = 0
        
        # 첫 화면으로 이동 (인덱스 0)
        self.stack.setCurrentIndex(0)