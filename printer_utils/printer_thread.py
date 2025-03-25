from PySide6.QtCore import QThread, Signal
from .device_functions import get_device_list, get_device_id, open_device, draw_image, get_preview_bitmap, print_image, close_device, load_font, draw_text2
from .image_utils import bitmapinfo_to_image
from .cffi_defs import ffi, SMART_OPENDEVICE_BYID, PAGE_FRONT, PANELID_COLOR
from config import config
import os
import json

class PrinterThread(QThread):
    finished = Signal()
    error = Signal(str)
    # preview_ready = Signal(object)  # 미리보기 이미지 전달용
    
    def __init__(self):
        super().__init__()
        self.images = []  # 이미지 정보 저장 리스트
        self.texts = []   # 텍스트 정보 저장 리스트
        
    def add_image(self, image_filename, x, y, width, height):
        """이미지 그리기 작업 추가"""
        self.images.append({
            "filename": image_filename,
            "x": x,
            "y": y,
            "width": width,
            "height": height
        })
        
    def add_text(self, text, x, y, width, height, font_name, font_size, font_color, font_style=0x01, rotate=0, align=0x01|0x10, option=4):
        """텍스트 그리기 작업 추가"""
        self.texts.append({
            "text": text,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "font_name": font_name,
            "font_size": font_size, 
            "font_color": font_color,
            "font_style": font_style,
            "rotate": rotate,
            "align": align,
            "option": option
        })
    
    def load_contents(self):
        """config.json에서 이미지와 텍스트 로드"""
        # 이미지 설정 불러오기
        expected_img_count = config.get("images", {}).get("count", 0)
        img_items = config.get("images", {}).get("items", [])
        
        if len(img_items) != expected_img_count:
            print(f"경고: 설정된 이미지 수({expected_img_count})와 실제 이미지 항목 수({len(img_items)})가 다릅니다")
        
        for img_config in img_items:
            self.add_image(
                image_filename=f"resources/{img_config.get('filename', 'captured_image.jpg')}",
                x=img_config.get("x", 0),
                y=img_config.get("y", 0),
                width=img_config.get("width", 300),
                height=img_config.get("height", 300)
            )
        
        # 텍스트 설정 불러오기
        expected_text_count = config.get("texts", {}).get("count", 0)
        text_items = config.get("texts", {}).get("items", [])
        
        if len(text_items) != expected_text_count:
            print(f"경고: 설정된 텍스트 수({expected_text_count})와 실제 텍스트 항목 수({len(text_items)})가 다릅니다")
        
        # input_texts.json 파일 로드 시도
        input_texts = {}
        if os.path.exists("resources/input_texts.json"):
            try:
                with open("resources/input_texts.json", "r", encoding="utf-8") as f:
                    input_texts = json.loads(f.read())
                # print(f"input_texts.json 파일을 성공적으로 로드했습니다: {input_texts}")
            except Exception as e:
                print(f"input_texts.json 파일 읽기 실패: {str(e)}")
        
        for i, text_config in enumerate(text_items):
            # 텍스트 내용 결정
            content = text_config.get("content", "")
            
            # input_texts.json에서 해당 인덱스의 텍스트 가져오기
            text_key = f"text_{i+1}"
            if text_key in input_texts and input_texts[text_key]:
                content = input_texts[text_key]
                # print(f"텍스트 {i+1}: input_texts.json에서 '{content}' 가져옴")
            
            self.add_text(
                text=content,
                x=text_config.get("x", 0),
                y=text_config.get("y", 0),
                width=text_config.get("width", 300),
                height=text_config.get("height", 300),
                font_name=text_config.get("font", "LAB디지털.ttf"),
                font_size=text_config.get("font_size", 32),
                font_color=text_config.get("font_color", "#000000"),
                font_style=text_config.get("style", 0x01),
                rotate=text_config.get("rotate", 0),
                align=text_config.get("align", 0x01 | 0x10),
                option=text_config.get("option", 4)
            )
    
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
                # 폰트 캐시 딕셔너리 생성 (폰트 중복 로드 방지)
                loaded_fonts = {}
                
                # 이미지 그리기 (여러 개)
                for img_info in self.images:
                    result = draw_image(
                        device_handle, PAGE_FRONT, PANELID_COLOR, 
                        x=img_info["x"], y=img_info["y"],
                        cx=img_info["width"], cy=img_info["height"], 
                        image_filename=img_info["filename"]
                    )
                    if result != 0:
                        self.error.emit(f"이미지 그리기 실패: {img_info['filename']}")
                        return
                
                # 텍스트 그리기 (여러 개)
                for text_info in self.texts:
                    # 폰트 로드 (중복 로드 방지)
                    font_path = f"resources/font/{text_info['font_name']}"
                    if font_path not in loaded_fonts:
                        font_name = load_font(font_path)
                        if font_name is None:
                            self.error.emit(f"폰트 로드 실패: {text_info['font_name']}")
                            return
                        loaded_fonts[font_path] = font_name
                    else:
                        font_name = loaded_fonts[font_path]
                        
                    # 색상 변환 (문자열 -> 16진수 정수)
                    if isinstance(text_info["font_color"], str):
                        font_color = int(text_info["font_color"].lstrip('#'), 16)
                    else:
                        font_color = text_info["font_color"]
                        
                    result = draw_text2(
                        device_handle, PAGE_FRONT, PANELID_COLOR,
                        x=text_info["x"], y=text_info["y"], 
                        width=text_info["width"], height=text_info["height"], 
                        font_name=font_name, 
                        font_height=text_info["font_size"], font_width=0, 
                        font_style=text_info["font_style"], 
                        font_color=font_color,
                        text=text_info["text"], 
                        rotate=text_info["rotate"], 
                        align=text_info["align"], 
                        option=text_info["option"]
                    )
                    if result != 0:
                        self.error.emit(f"텍스트 그리기 실패: {text_info['text']}")
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