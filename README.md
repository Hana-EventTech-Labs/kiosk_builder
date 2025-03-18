# 키오스크 앱 (Kiosk App)

## 개요
이 프로젝트는 사진 촬영, 텍스트 입력, 인쇄 기능을 갖춘 키오스크 애플리케이션입니다.

## 기능
- 웹캠을 통한 사진 촬영
- 한글/영문 텍스트 입력 (가상 키보드)
- 카드 인쇄 기능 (SmartComm 인쇄 드라이버 사용)

## 설치 방법

### 필수 요구사항
- Python 3.8 이상
- PySide6
- opencv-python
- cffi
- pillow

### 설치 명령어
```bash
pip install -r requirements.txt
```

## 실행 방법
```bash
python main.py
```

## 화면 구성
애플리케이션은 다음 화면들로 구성되어 있습니다:

1. **스플래시 화면** (index 0)
   - 시작 화면, 클릭하면 다음 화면으로 이동

2. **사진 촬영 화면** (index 1)
   - 웹캠을 통한 사진 촬영
   - 클릭하면 카운트다운 후 사진 촬영

3. **텍스트 입력 화면** (index 2)
   - 한글/영문 가상 키보드로 텍스트 입력
   - 키보드의 '다음' 버튼으로 다음 화면 이동

4. **처리 화면** (index 3)
   - 사진과 텍스트 데이터 처리 및 인쇄 준비
   - 자동으로 다음 화면으로 이동

5. **완료 화면** (index 4)
   - 작업 완료 표시
   - 자동으로 스플래시 화면으로 돌아감

## 설정 파일 (config.json)

### 주요 설정 항목

```json
{
    "screen_order": [0, 2, 1, 3, 4],  // 화면 전환 순서
    "image": {
        "x": 0,            // 프린터에 인쇄될 이미지의 X좌표
        "y": 0,            // 프린터에 인쇄될 이미지의 Y좌표
        "width": 300,      // 프린터에 인쇄될 이미지의 너비
        "height": 300      // 프린터에 인쇄될 이미지의 높이
    },
    "text": {
        "x": 0,            // 프린터에 인쇄될 텍스트의 X좌표
        "y": 0,            // 프린터에 인쇄될 텍스트의 Y좌표
        "width": 300,      // 프린터에 인쇄될 텍스트 영역의 너비
        "height": 300      // 프린터에 인쇄될 텍스트 영역의 높이
    },
    "text_input": {
        "width": 800,      // 텍스트 입력 필드의 너비
        "height": 80,      // 텍스트 입력 필드의 높이
        "margin_top": 200, // 텍스트 입력 필드의 위쪽 여백
        "font_size": 36    // 텍스트 입력 필드의 글꼴 크기
    },
    "keyboard": {
        "x": 320,          // 가상 키보드의 X좌표
        "y": 400,          // 가상 키보드의 Y좌표
        "width": 1280,     // 가상 키보드의 너비
        "height": 400,     // 가상 키보드의 높이
        "max_hangul": 100  // 최대 한글 입력 글자 수
    }
}
```

## 화면 순서 변경
`config.json`의 `screen_order` 배열을 수정하여 화면 전환 순서를 변경할 수 있습니다.

## 배경 이미지 추가
각 화면에 배경 이미지를 추가하려면:
1. `resources` 폴더에 이미지 파일 추가
2. 각 화면에 맞는 번호를 사용하여 파일 이름 지정:
   - 스플래시 화면: `0.png` 또는 `0.jpg`
   - 사진 촬영 화면: `1.png` 또는 `1.jpg`
   - 텍스트 입력 화면: `2.png` 또는 `2.jpg`
   - 처리 화면: `3.png` 또는 `3.jpg`
   - 완료 화면: `4.png` 또는 `4.jpg`

## 폴더 구조
```
kiosk_app/
├── components/              # 컴포넌트 폴더
│   ├── __init__.py
│   ├── hangul_composer.py   # 한글 조합 처리
│   └── virtual_keyboard.py  # 가상 키보드
├── printer_utils/           # 프린터 유틸리티
│   ├── __init__.py
│   ├── cffi_defs.py
│   ├── device_functions.py
│   ├── image_utils.py
│   └── printer_thread.py
├── resources/               # 리소스 폴더
│   ├── config.json          # 설정 파일
│   ├── LAB디지털.ttf         # 폰트 파일
│   └── SmartComm2.dll       # 프린터 드라이버
├── screens/                 # 화면 폴더
│   ├── camera_screen.py
│   ├── complete_screen.py
│   ├── process_screen.py
│   ├── splash_screen.py
│   └── text_input_screen.py
├── webcam_utils/            # 웹캠 유틸리티
│   ├── __init__.py
│   └── webcam_controller.py
├── main.py                  # 메인 프로그램
├── config.py                # 설정 로더
└── requirements.txt         # 의존성 패키지
```

## 키보드 사용 방법
- **한/영**: 한글과 영문 전환
- **Shift**: 대문자 또는 쌍자음 전환
- **Space**: 띄어쓰기
- **←**: 백스페이스 (글자 삭제)
- **다음**: 입력 완료 및 다음 화면으로 이동

## 주의 사항
- 프린터 기능을 사용하려면 SmartComm2.dll이 resources 폴더에 있어야 합니다.
- 폰트 파일(LAB디지털.ttf)이 resources 폴더에 필요합니다.
