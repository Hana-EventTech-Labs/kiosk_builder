from .cffi_defs import ffi
from PIL import Image, ImageDraw, ImageFont

def bitmapinfo_to_image(bitmap_info):
    
    bm_info = ffi.cast("BITMAPINFO *", bitmap_info)

    header = bm_info.bmiHeader
    width = header.biWidth
    height = header.biHeight
    bit_count = header.biBitCount
    size_image = header.biSizeImage

    # 픽셀 데이터 시작 오프셋 결정
    if bit_count > 8:
        offset = header.biSize
    else:
        num_colors = header.biClrUsed if header.biClrUsed != 0 else (1 << bit_count)
        offset = header.biSize + num_colors * ffi.sizeof("RGBQUAD")
    
    bm_ptr = ffi.cast("char *", bm_info)
    pixel_data_ptr = bm_ptr + offset

    if size_image == 0:
        row_bytes = ((width * bit_count + 31) // 32) * 4
        size_image = row_bytes * abs(height)

    pixel_data = ffi.buffer(pixel_data_ptr, size_image)[:]

    if bit_count == 24:
        try:
            img = Image.frombuffer("RGB", (width, abs(height)), pixel_data, "raw", "BGR", 0, 1)
            if header.biHeight > 0:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            return img
        except Exception as e:
            print("이미지 변환 중 오류 발생:", e)
            return None
    else:
        print(f"현재 {bit_count}비트 이미지는 지원하지 않습니다.")
        return None