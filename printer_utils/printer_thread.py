from PySide6.QtCore import QThread, Signal
from .device_functions import get_device_list, get_device_id, open_device, draw_image, get_preview_bitmap, print_image, close_device, load_font, draw_text2
from .image_utils import bitmapinfo_to_image
from .cffi_defs import ffi, SMART_OPENDEVICE_BYID, PAGE_FRONT, PANELID_COLOR
from config import config
import os

class PrinterThread(QThread):
    finished = Signal()
    error = Signal(str)
    # preview_ready = Signal(object)  # 미리보기 이미지 전달용
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            # 장치 목록 조회
            result, printer_list = get_device_list()
            if result != 0:
                self.error.emit("프린터 목록 가져오기 실패")
                return
                
            # 장치 선택
            device_index = 0
            device_id = get_device_id(printer_list, device_index)
            
            # 장치 열기
            result, device_handle = open_device(device_id, SMART_OPENDEVICE_BYID)
            if result != 0:
                self.error.emit("장치 열기 실패")
                return
                
            try:
                # 이미지 그리기
                result = draw_image(device_handle, PAGE_FRONT, PANELID_COLOR, 
                                    x=config["image"]["x"], y=config["image"]["y"],
                                    cx=config["image"]["width"], cy=config["image"]["height"], 
                                    image_filename="resources/captured_image.jpg")
                if result != 0:
                    self.error.emit("이미지 그리기 실패")
                    return
                    
                # 폰트 로드
                font_name = load_font(f"resources/font/{config['text']['font']}")
                if font_name is None:
                    self.error.emit("폰트 로드 실패")
                    return
                    
                # 사용자 입력 텍스트 가져오기
                input_text = "TEST용 텍스트입니다"  # 기본값
                if os.path.exists("resources/input_text.txt"):
                    try:
                        with open("resources/input_text.txt", "r", encoding="utf-8") as f:
                            input_text = f.read().strip()
                    except Exception as e:
                        self.error.emit(f"텍스트 파일 읽기 실패: {str(e)}")
                        
                # 텍스트 그리기
                result = draw_text2(device_handle,
                                    PAGE_FRONT, PANELID_COLOR,
                                    x = config["text"]["x"], y = config["text"]["y"], 
                                    width = config["text"]["width"], height = config["text"]["height"], 
                                    font_name = font_name, 
                                    font_height = config["text"]["font_size"], font_width = 0, font_style = 0x01, font_color = int(config["text"]["font_color"].lstrip('#'), 16), 
                                    text = input_text, 
                                    rotate = 0, align = 0x01 | 0x10, option = 4)
                if result != 0:
                    self.error.emit("텍스트 그리기 실패")
                    return
                
                # 미리보기 비트맵 가져오기
                result, bm_info = get_preview_bitmap(device_handle, PAGE_FRONT)
                if result == 0:
                    image = bitmapinfo_to_image(bm_info)
                    # self.preview_ready.emit(image)
                    image.show()
                else:
                    self.error.emit("미리보기 비트맵 가져오기 실패")
                    return
                
                # # 이미지 인쇄
                # result = print_image(device_handle)
                # if result != 0:
                #     self.error.emit("이미지 인쇄 실패")
                #     return
                    
                # self.finished.emit()
            finally:
                # 장치 닫기 (항상 실행)
                close_device(device_handle)
        except Exception as e:
            self.error.emit(f"인쇄 중 오류 발생: {str(e)}")