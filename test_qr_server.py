import requests
import json
import time
import threading
import tkinter as tk
from tkinter import messagebox, Label, Button, Frame, StringVar
from PIL import Image, ImageTk
import qrcode
import io
import uuid
import base64
import os
from datetime import datetime

# 참고: websocket-client 패키지가 필요합니다
# pip install websocket-client
try:
    import websocket
except ImportError:
    print("websocket-client 패키지를 설치해야 합니다!")
    print("명령어 실행: pip install websocket-client")

# 서버 URL
SERVER_URL = "https://port-0-kiosk-builder-m47pn82w3295ead8.sel4.cloudtype.app"

class QRImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("QR 코드 이미지 뷰어")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # 변수 초기화
        self.event_id = None
        self.qr_url = None
        self.client_connected = False
        self.ws = None
        self.status_text = StringVar()
        self.status_text.set("시작하려면 이벤트 생성 버튼을 클릭하세요")
        
        # UI 구성
        self.setup_ui()
        
    def setup_ui(self):
        # 상단 프레임 (제목 및 버튼)
        top_frame = Frame(self.root, bg="#f0f0f0", pady=10)
        top_frame.pack(fill="x")
        
        title_label = Label(
            top_frame, 
            text="QR 코드 이미지 뷰어", 
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=10)
        
        # 버튼 프레임
        button_frame = Frame(top_frame, bg="#f0f0f0")
        button_frame.pack(pady=10)
        
        create_event_btn = Button(
            button_frame, 
            text="이벤트 생성 및 QR 코드 표시",
            command=self.create_event,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=5
        )
        create_event_btn.pack(side="left", padx=5)
        
        # 중앙 프레임 (QR 코드 및 이미지)
        self.center_frame = Frame(self.root, bg="#f0f0f0")
        self.center_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # QR 코드 프레임
        self.qr_frame = Frame(self.center_frame, bg="white", padx=20, pady=20, borderwidth=1, relief="solid")
        self.qr_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        self.qr_label = Label(self.qr_frame, text="QR 코드가 여기에 표시됩니다", bg="white")
        self.qr_label.pack(pady=20)
        
        # 이미지 프레임
        self.image_frame = Frame(self.center_frame, bg="white", padx=20, pady=20, borderwidth=1, relief="solid")
        self.image_frame.pack(side="right", fill="both", expand=True, padx=10)
        
        self.image_label = Label(self.image_frame, text="업로드된 이미지가 여기에 표시됩니다", bg="white")
        self.image_label.pack(pady=20)
        
        # 하단 프레임 (상태 바)
        bottom_frame = Frame(self.root, bg="#e0e0e0", height=30)
        bottom_frame.pack(fill="x", side="bottom")
        
        status_label = Label(
            bottom_frame, 
            textvariable=self.status_text,
            bg="#e0e0e0",
            anchor="w",
            padx=10
        )
        status_label.pack(fill="x")
    
    def create_event(self):
        """이벤트를 생성하고 QR 코드를 표시합니다"""
        try:
            self.status_text.set("이벤트 생성 중...")
            self.root.update()
            
            # 이벤트 생성 API 호출
            response = requests.post(
                f"{SERVER_URL}/api/events/register",
                params={"event_name": f"테스트 이벤트 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
            )
            
            if response.status_code == 200:
                event_data = response.json()
                self.event_id = event_data["event_id"]
                self.qr_url = event_data["qr_url"]
                
                # QR 코드 생성 및 표시
                self.display_qr_code(self.qr_url)
                
                # 웹소켓 연결 시작
                self.connect_websocket()
                
                self.status_text.set(f"이벤트 생성 완료! 이벤트 ID: {self.event_id}")
            else:
                self.status_text.set(f"이벤트 생성 실패! 상태 코드: {response.status_code}")
                messagebox.showerror("오류", f"이벤트 생성에 실패했습니다: {response.text}")
        
        except Exception as e:
            self.status_text.set(f"오류 발생: {str(e)}")
            messagebox.showerror("오류", f"이벤트 생성 중 오류가 발생했습니다: {str(e)}")
    
    def display_qr_code(self, url):
        """QR 코드를 생성하고 UI에 표시합니다"""
        try:
            # QR 코드 생성
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # PIL 이미지를 Tkinter 이미지로 변환
            self.tk_qr_img = ImageTk.PhotoImage(qr_img)
            
            # 기존 내용 제거 후 QR 코드 표시
            for widget in self.qr_frame.winfo_children():
                widget.destroy()
            
            qr_image_label = Label(self.qr_frame, image=self.tk_qr_img, bg="white")
            qr_image_label.pack(pady=10)
            
            url_label = Label(
                self.qr_frame, 
                text=f"URL: {url}",
                wraplength=300,
                bg="white",
                fg="blue"
            )
            url_label.pack(pady=5)
            
            instruction_label = Label(
                self.qr_frame,
                text="모바일에서 QR 코드를 스캔하여 이미지를 업로드하세요",
                wraplength=300,
                bg="white"
            )
            instruction_label.pack(pady=10)
            
        except Exception as e:
            self.status_text.set(f"QR 코드 생성 오류: {str(e)}")
            messagebox.showerror("오류", f"QR 코드 생성 중 오류가 발생했습니다: {str(e)}")
    
    def connect_websocket(self):
        """키오스크 웹소켓 연결을 설정합니다"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                print(f"웹소켓 메시지 수신: {data}")
                
                if data["type"] == "client_connected":
                    client_id = data["client_id"]
                    self.client_connected = True
                    self.status_text.set(f"클라이언트가 연결되었습니다: {client_id}")
                
                elif data["type"] == "image_uploaded":
                    client_id = data["client_id"]
                    image_url = data["image_url"]
                    self.status_text.set(f"이미지가 업로드되었습니다: {client_id}")
                    
                    # 이미지 다운로드 및 표시
                    self.display_uploaded_image(image_url)
                
                elif data["type"] == "client_disconnected":
                    client_id = data["client_id"]
                    self.client_connected = False
                    self.status_text.set(f"클라이언트 연결이 끊겼습니다: {client_id}")
            
            except Exception as e:
                print(f"메시지 처리 오류: {str(e)}")
        
        def on_error(ws, error):
            print(f"웹소켓 오류: {error}")
            self.status_text.set(f"웹소켓 오류: {str(error)}")
        
        def on_close(ws, close_status_code, close_msg):
            print(f"웹소켓 연결 종료: {close_status_code} {close_msg}")
            self.status_text.set("웹소켓 연결이 종료되었습니다")
        
        def on_open(ws):
            print("웹소켓 연결 성공")
            self.status_text.set("웹소켓 연결이 설정되었습니다. QR 코드를 스캔해주세요.")
        
        def run_websocket():
            # 웹소켓 URL 생성
            ws_url = f"{SERVER_URL.replace('https://', 'wss://')}/ws/kiosk/{self.event_id}"
            print(f"웹소켓 연결 시도: {ws_url}")
            
            # 웹소켓 클라이언트 설정
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            # 연결 유지
            self.ws.run_forever()
        
        # 별도 스레드에서 웹소켓 실행
        thread = threading.Thread(target=run_websocket, daemon=True)
        thread.start()
    
    def display_uploaded_image(self, image_url):
        """업로드된 이미지를 다운로드하고 UI에 표시합니다"""
        try:
            # 상대 URL을 절대 URL로 변환
            if image_url.startswith('/'):
                image_url = f"{SERVER_URL}{image_url}"
            
            # 이미지 다운로드
            response = requests.get(image_url)
            
            if response.status_code == 200:
                # 이미지 데이터를 PIL 이미지로 변환
                img_data = io.BytesIO(response.content)
                img = Image.open(img_data)
                
                # 이미지 크기 조정 (필요시)
                max_size = (400, 300)
                img.thumbnail(max_size)
                
                # PIL 이미지를 Tkinter 이미지로 변환
                self.tk_uploaded_img = ImageTk.PhotoImage(img)
                
                # 기존 내용 제거 후 이미지 표시
                for widget in self.image_frame.winfo_children():
                    widget.destroy()
                
                uploaded_image_label = Label(self.image_frame, image=self.tk_uploaded_img, bg="white")
                uploaded_image_label.pack(pady=10)
                
                # 이미지 정보 표시
                info_label = Label(
                    self.image_frame, 
                    text=f"업로드된 이미지: {image_url.split('/')[-1]}",
                    wraplength=300,
                    bg="white"
                )
                info_label.pack(pady=5)
                
                self.status_text.set("이미지가 성공적으로 표시되었습니다")
            else:
                self.status_text.set(f"이미지 다운로드 실패! 상태 코드: {response.status_code}")
        
        except Exception as e:
            self.status_text.set(f"이미지 표시 오류: {str(e)}")
            messagebox.showerror("오류", f"이미지 표시 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    # tkinter 초기화
    root = tk.Tk()
    app = QRImageViewer(root)
    
    # 프로그램 실행
    root.mainloop()