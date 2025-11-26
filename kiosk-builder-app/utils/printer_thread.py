from PySide6.QtCore import QThread, Signal
from .device_functions import get_device_list, get_device_id, open_device, draw_image, print_image, close_device
from .cffi_defs import ffi, SMART_OPENDEVICE_BYID, PAGE_FRONT, PANELID_COLOR
import os

class PrinterThread(QThread):
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, print_data, print_count=1, panel_id=PANELID_COLOR):
        super().__init__()
        self.print_data = print_data
        self.print_count = print_count
        self.panel_id = panel_id
    
    def run(self):
        device_handle = None  # finally에서 접근할 수 있도록 먼저 초기화
        try:
            # 장치 목록 조회
            result, printer_list = get_device_list()
            if result != 0:
                self.error.emit(f"프린터 목록 가져오기 실패 (코드: {result})")
                return

            # 프린터가 없는 경우
            if printer_list.n == 0:
                self.error.emit("연결된 프린터가 없습니다.")
                return

            # 장치 선택
            device_index = 0
            device_id = get_device_id(printer_list, device_index)

            # 장치 열기
            result, device_handle = open_device(device_id, SMART_OPENDEVICE_BYID)
            if result != 0:
                self.error.emit(f"장치 열기 실패 (코드: {result})")
                device_handle = None  # 실패 시 None으로 설정
                return

            # 이미지 그리기
            image_path = os.path.join("resources", self.print_data['filename'])
            if not os.path.exists(image_path):
                self.error.emit(f"이미지 파일을 찾을 수 없습니다: {image_path}")
                return

            result = draw_image(
                device_handle, PAGE_FRONT, self.panel_id,
                x=self.print_data['x'], y=self.print_data['y'],
                cx=self.print_data['width'], cy=self.print_data['height'],
                image_filename=image_path
            )

            if result != 0:
                self.error.emit(f"이미지 그리기 실패 (코드: {result})")
                return

            # 지정된 매수만큼 인쇄
            for i in range(self.print_count):
                result = print_image(device_handle)
                if result != 0:
                    self.error.emit(f"이미지 인쇄 실패 (코드: {result}, {i+1}/{self.print_count}매)")
                    return

            self.finished.emit()

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.error.emit(f"알 수 없는 오류 발생: {str(e)}\n{error_detail}")

        finally:
            if device_handle is not None:
                try:
                    close_device(device_handle)
                except Exception:
                    pass  # 장치 닫기 실패는 무시
                
            
                
            
        
