# 키오스크 설정 편집기

## 소개
이 프로그램은 키오스크 애플리케이션의 설정을 편집하는 GUI 도구입니다. config.json 파일의 다양한 설정값을 시각적으로 수정할 수 있습니다.

## 설치 방법
1. Python 3.7 이상이 필요합니다.
2. 필요한 라이브러리 설치:
   ```bash
   pip install -r requirements.txt
   ```

## 사용 방법
1. 다음 명령으로 프로그램 실행:
   ```bash
   python main.py
   ```
2. 탭을 통해 다양한 설정 섹션에 접근할 수 있습니다:
   - 기본 설정: 앱 이름, 화면 크기, 카메라 크기, 화면 순서
   - 레이아웃 설정: 프레임, 이미지, 텍스트, 텍스트 입력, 확인 버튼
   - 키보드 설정: 키보드 위치, 크기, 스타일
   - 화면 설정: 스플래시, 프로세스, 완료 화면

3. 수정 후 저장 버튼을 클릭하여 config.json 파일에 변경사항을 저장할 수 있습니다.

## 설정 구조
config.json 파일은 다음과 같은 주요 섹션으로 구성됩니다:
- app_name: 앱 이름
- screen_size: 화면 크기
- camera_size: 카메라 크기
- screen_order: 화면 순서
- frame, image, text: 위치 및 크기 설정
- text_input: 텍스트 입력 필드 설정
- keyboard: 가상 키보드 설정
- confirm_button: 확인 버튼 설정
- splash, process, complete: 각 화면별 설정 

### kiosk-builder-app 용 pyinstaller 명령어
```
pyinstaller --clean --onefile --windowed --add-data "resources;resources" --add-data "config.json;." --icon="Hana.ico" --name super-kiosk-builder run_gui.py
```