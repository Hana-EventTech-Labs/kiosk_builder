from pathlib import Path
from cffi import FFI

ffi = FFI()

ffi.cdef("""
#define MAX_SMART_PRINTER 32
         
#define SMART_OPENDEVICE_BYID 0
#define SMART_OPENDEVICE_BYDESC 1
         
#define PAGE_FRONT 0
#define PAGE_BACK 1
         
#define PANELID_COLOR 1
#define PANELID_BLACK 2
#define PANELID_OVERLAY 4
#define PANELID_UV 8

typedef void* HSMART;
         
typedef void* RECT;

typedef unsigned int DWORD;
typedef int LONG;
typedef unsigned short WORD;
typedef unsigned char BYTE;

typedef struct {
    wchar_t name[128];
    wchar_t id[64];
    wchar_t dev[64];
    wchar_t desc[256];
    int pid;
} SMART_PRINTER_ITEM;

typedef struct {
    int n;
    SMART_PRINTER_ITEM item[MAX_SMART_PRINTER];
} SMART_PRINTER_LIST;
         
typedef struct tagBITMAPINFOHEADER {
    DWORD biSize;
    LONG biWidth;
    LONG biHeight;
    WORD biPlanes;
    WORD biBitCount;
    DWORD biCompression;
    DWORD biSizeImage;
    LONG biXPelsPerMeter;
    LONG biYPelsPerMeter;
    DWORD biClrUsed;
    DWORD biClrImportant;
} BITMAPINFOHEADER;

typedef struct tagRGBQUAD {
    BYTE rgbBlue;
    BYTE rgbGreen;
    BYTE rgbRed;
    BYTE rgbReserved;
} RGBQUAD;

typedef struct tagBITMAPINFO {
    BITMAPINFOHEADER bmiHeader;
    RGBQUAD bmiColors[1];
} BITMAPINFO;

typedef struct {
    DWORD side;
    DWORD orientation;
    DWORD ribbon;
    DWORD ribbon_type;
    DWORD width;
    DWORD height;
} SMART_SURFACE_PROPERTIES;
         
int SmartComm_GetDeviceList2(SMART_PRINTER_LIST* pDevList);
int SmartComm_OpenDevice2(HSMART* pHandle, wchar_t* szDevice, int nDevType);
int SmartComm_DrawImage(HSMART hHandle, unsigned char page, unsigned char panel,
                        int x, int y, int cx, int cy, wchar_t* szImgPath, RECT* prcArea);
int SmartComm_GetPreviewBitmap(HSMART hHandle, unsigned char page, BITMAPINFO** const ppbi);
int SmartComm_Print(HSMART hHandle);
int SmartComm_CloseDevice(HSMART hHandle);
int SmartComm_GetStatus(HSMART hHandle, DWORD* pStatus);
int SmartComm_DrawText(
    HSMART hHandle, 
    BYTE page, 
    BYTE panel, 
    int x, 
    int y, 
    WCHAR* szFontName, 
    int nFontSize, 
    BYTE nFontStyle, 
    WCHAR* szText, 
    RECT* prcArea
);


typedef struct {
    int x;
    int y;
    int cx;
    int cy;
    int rotate;
    int align;
    int fontHeight;
    int fontWidth;
    int style;
    unsigned long color;
    int option;
    wchar_t szFaceName[32];
} DRAWTEXT2INFO;

int SmartComm_DrawText2(
    HSMART hHandle, 
    BYTE page, 
    BYTE panel, 
    DRAWTEXT2INFO* pdt2info, 
    wchar_t* szText
);
         
int SmartComm_DrawBarcode(
    HSMART hHandle,
    BYTE page,
    BYTE panel,
    int x,
    int y,
    int cx,
    int cy,
    unsigned long col,
    RECT* prcArea,
    const wchar_t* szName,
    int nSize,
    const wchar_t* szData,
    const wchar_t* szPost
);

""")

# DLL Lazy Loading - 필요할 때만 로드
import sys

_lib = None  # 내부 캐시

def get_dll_path():
    """DLL 경로 반환"""
    if getattr(sys, 'frozen', False):
        # EXE 모드: 먼저 _MEIPASS (EXE 내부 리소스)에서 찾기
        meipass_dll = Path(sys._MEIPASS) / "resources" / "SmartComm2.dll"
        if meipass_dll.exists():
            return meipass_dll
        # _MEIPASS에 없으면 EXE 위치의 resources 폴더에서 찾기 (활성화 후 다운로드된 경우)
        base_dir = Path(sys.executable).parent
        return base_dir / "resources" / "SmartComm2.dll"
    else:
        # 개발 모드: 스크립트 기준 상대 경로
        return Path(__file__).parent / ".." / "resources" / "SmartComm2.dll"

def get_lib():
    """DLL 라이브러리 반환 (lazy loading)"""
    global _lib
    if _lib is not None:
        return _lib

    dll_path = get_dll_path()
    try:
        _lib = ffi.dlopen(str(dll_path.resolve()))
        print(f"[cffi_defs] SmartComm2.dll 로드 성공: {dll_path}")
        return _lib
    except OSError as e:
        print(f"[cffi_defs] WARNING: SmartComm2.dll 로드 실패 ({dll_path}): {e}")
        print("[cffi_defs] 프린터 기능이 비활성화됩니다.")
        return None

# 하위 호환성을 위한 lib 변수 (property처럼 동작하는 클래스)
class LibProxy:
    """lib 접근 시 자동으로 DLL 로드"""
    def __getattr__(self, name):
        # Python 종료 시점에서 모듈이 정리되면 get_lib이 None이 될 수 있음
        if get_lib is None:
            return None
        try:
            real_lib = get_lib()
            if real_lib is None:
                # DLL 로드 실패 - 조용히 None 반환 (종료 시점 에러 방지)
                return None
            return getattr(real_lib, name)
        except Exception:
            # 종료 시점 에러 무시
            return None

lib = LibProxy()

MAX_SMART_PRINTER = 32
SMART_OPENDEVICE_BYID = 0
SMART_OPENDEVICE_BYDESC = 1
PAGE_FRONT = 0
PAGE_BACK = 1
PANELID_COLOR = 1
PANELID_BLACK = 2
PANELID_OVERLAY = 4
PANELID_UV = 8