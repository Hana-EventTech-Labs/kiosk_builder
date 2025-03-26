import requests
import json
import tkinter as tk
from tkinter import messagebox, Label, Button, Frame, StringVar, Toplevel
from PIL import Image, ImageTk
import qrcode
import io
import webbrowser
import threading
import time
import uuid
import os

# 서버 URL
SERVER_URL = "https://port-0-kiosk-builder-m47pn82w3295ead8.sel4.cloudtype.app"

class QRCodeTester:
    def __init__(self, root):
        self.root = root
        self.root.title("QR 코드 테스트 프로그램")
        self.root.geometry("600x700")
        self.root.configure(bg="#f0f0f0")
        
        # 변수 초기화
        self.event_id = None
        self.event_name = None
        self.qr_url = None
        self.status_text = StringVar()
        self.status_text.set("테스트를 시작하려면 '이벤트 생성' 버튼을 클릭하세요")
        
        # UI 구성
        self.setup_ui()
        
    def setup_ui(self):
        # 제목 프레임
        title_frame = Frame(self.root, bg="#f0f0f0", pady=15)
        title_frame.pack(fill="x")
        
        title_label = Label(
            title_frame, 
            text="QR 코드 이미지 서버 테스트", 
            font=("Arial", 16, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack()
        
        # 버튼 프레임
        button_frame = Frame(self.root, bg="#f0f0f0", pady=10)
        button_frame.pack(fill="x")
        
        create_event_btn = Button(
            button_frame, 
            text="이벤트 생성",
            command=self.create_event,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10),
            width=15,
            height=2
        )
        create_event_btn.pack(side="left", padx=10, pady=5)
        
        test_qr_btn = Button(
            button_frame, 
            text="QR 코드 테스트",
            command=self.show_qr_code,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10),
            width=15,
            height=2,
            state="disabled"
        )
        self.test_qr_btn = test_qr_btn
        test_qr_btn.pack(side="left", padx=10, pady=5)
        
        open_mobile_btn = Button(
            button_frame, 
            text="모바일 페이지 열기",
            command=self.open_mobile_page,
            bg="#FF9800",
            fg="white",
            font=("Arial", 10),
            width=15,
            height=2,
            state="disabled"
        )
        self.open_mobile_btn = open_mobile_btn
        open_mobile_btn.pack(side="left", padx=10, pady=5)
        
        # 이벤트 정보 프레임
        info_frame = Frame(self.root, bg="white", padx=20, pady=20, relief="solid", borderwidth=1)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        self.event_id_label = Label(
            info_frame,
            text="이벤트 ID: 아직 생성되지 않음",
            font=("Arial", 10),
            bg="white",
            anchor="w"
        )
        self.event_id_label.pack(fill="x", pady=2)
        
        self.event_name_label = Label(
            info_frame,
            text="이벤트 이름: 아직 생성되지 않음",
            font=("Arial", 10),
            bg="white",
            anchor="w"
        )
        self.event_name_label.pack(fill="x", pady=2)
        
        self.qr_url_label = Label(
            info_frame,
            text="QR URL: 아직 생성되지 않음",
            font=("Arial", 10),
            bg="white",
            anchor="w",
            wraplength=550
        )
        self.qr_url_label.pack(fill="x", pady=2)
        
        # QR 코드 프레임
        qr_frame = Frame(self.root, bg="white", padx=20, pady=20, relief="solid", borderwidth=1)
        qr_frame.pack(fill="x", padx=20, pady=10)
        
        qr_title = Label(
            qr_frame,
            text="QR 코드",
            font=("Arial", 12, "bold"),
            bg="white"
        )
        qr_title.pack(pady=5)
        
        self.qr_image_label = Label(
            qr_frame,
            text="아직 QR 코드가 생성되지 않았습니다",
            bg="white",
            padx=10,
            pady=30
        )
        self.qr_image_label.pack(pady=10)
        
        # 결과 프레임
        result_frame = Frame(self.root, bg="white", padx=20, pady=20, relief="solid", borderwidth=1)
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        result_title = Label(
            result_frame,
            text="업로드된 이미지",
            font=("Arial", 12, "bold"),
            bg="white"
        )
        result_title.pack(pady=5)
        
        self.result_label = Label(
            result_frame,
            text="아직 업로드된 이미지가 없습니다",
            bg="white",
            padx=10,
            pady=30
        )
        self.result_label.pack(pady=10)
        
        # 상태바
        status_bar = Frame(self.root, bg="#e0e0e0", height=25)
        status_bar.pack(fill="x", side="bottom")
        
        status_label = Label(
            status_bar,
            textvariable=self.status_text,
            bg="#e0e0e0",
            anchor="w",
            padx=10
        )
        status_label.pack(fill="x")
    
    def create_event(self):
        """서버에 이벤트를 등록하고 QR 코드를 생성합니다"""
        try:
            self.status_text.set("이벤트 생성 중...")
            self.root.update()
            
            # 이벤트 이름 생성
            event_name = f"테스트 이벤트 {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 서버에 이벤트 등록
            response = requests.post(
                f"{SERVER_URL}/api/events/register",
                params={"event_name": event_name}
            )
            
            if response.status_code == 200:
                event_data = response.json()
                self.event_id = event_data["event_id"]
                self.event_name = event_data["event_name"]
                self.qr_url = event_data["qr_url"]
                
                # UI 업데이트
                self.event_id_label.config(text=f"이벤트 ID: {self.event_id}")
                self.event_name_label.config(text=f"이벤트 이름: {self.event_name}")
                self.qr_url_label.config(text=f"QR URL: {self.qr_url}")
                
                # QR 코드 생성
                self.generate_qr_code()
                
                # 버튼 활성화
                self.test_qr_btn.config(state="normal")
                self.open_mobile_btn.config(state="normal")
                
                self.status_text.set(f"이벤트가 성공적으로 생성되었습니다. ID: {self.event_id}")
            else:
                messagebox.showerror("오류", f"이벤트 생성 실패: {response.text}")
                self.status_text.set("이벤트 생성에 실패했습니다")
        
        except Exception as e:
            messagebox.showerror("오류", f"이벤트 생성 중 오류 발생: {str(e)}")
            self.status_text.set(f"오류: {str(e)}")
    
    def generate_qr_code(self):
        """QR 코드를 생성하고 UI에 표시합니다"""
        try:
            # QR 코드 생성
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.qr_url)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # PIL 이미지를 Tkinter 이미지로 변환
            img_io = io.BytesIO()
            qr_img.save(img_io, 'PNG')
            img_io.seek(0)
            
            img = Image.open(img_io)
            self.tk_qr_img = ImageTk.PhotoImage(img)
            
            # QR 코드 이미지 표시
            self.qr_image_label.config(image=self.tk_qr_img, text="")
            
            self.status_text.set("QR 코드가 생성되었습니다")
        
        except Exception as e:
            messagebox.showerror("오류", f"QR 코드 생성 중 오류 발생: {str(e)}")
            self.status_text.set(f"QR 코드 생성 오류: {str(e)}")
    
    def show_qr_code(self):
        """QR 코드를 큰 창에 표시합니다"""
        if not self.qr_url:
            messagebox.showwarning("경고", "먼저 이벤트를 생성해야 합니다")
            return
        
        # 새 창 생성
        qr_window = Toplevel(self.root)
        qr_window.title("QR 코드 스캔")
        qr_window.geometry("400x500")
        qr_window.configure(bg="white")
        
        # QR 코드 표시
        qr_img_label = Label(qr_window, image=self.tk_qr_img, bg="white")
        qr_img_label.pack(pady=20)
        
        # URL 표시
        url_label = Label(
            qr_window,
            text=self.qr_url,
            wraplength=380,
            font=("Arial", 10),
            bg="white"
        )
        url_label.pack(pady=10)
        
        # 안내 메시지
        instruction_label = Label(
            qr_window,
            text="스마트폰으로 QR 코드를 스캔하거나\n아래 버튼을 눌러 모바일 페이지를 열어보세요",
            font=("Arial", 11),
            bg="white"
        )
        instruction_label.pack(pady=20)
        
        # 링크 버튼
        open_url_btn = Button(
            qr_window,
            text="모바일 페이지 열기",
            command=self.open_mobile_page,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10),
            width=15,
            height=2
        )
        open_url_btn.pack(pady=10)
    
    def open_mobile_page(self):
        """모바일 페이지를 기본 브라우저에서 엽니다"""
        if not self.qr_url:
            messagebox.showwarning("경고", "먼저 이벤트를 생성해야 합니다")
            return
        
        self.status_text.set("모바일 페이지를 엽니다...")
        webbrowser.open(self.qr_url)
        self.status_text.set(f"브라우저에서 URL 열림: {self.qr_url}")

# 메인 함수
def main():
    root = tk.Tk()
    app = QRCodeTester(root)
    root.mainloop()

if __name__ == "__main__":
    main()