@echo off
REM ========================================
REM 온라인 모드 키오스크 빌드 스크립트
REM - resources 폴더 미포함 (서버 다운로드)
REM - 경량 EXE 생성
REM ========================================

echo =====================================
echo  HanaKiosk 온라인 모드 빌드
echo =====================================
echo.

REM PyInstaller 확인
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller가 설치되어 있지 않습니다.
    echo pip install pyinstaller 를 실행하세요.
    pause
    exit /b 1
)

REM 기존 빌드 삭제
echo [1/4] 기존 빌드 파일 정리 중...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM 빌드 실행
echo [2/4] PyInstaller 빌드 실행 중...
pyinstaller super-kiosk-online.spec --noconfirm

if %errorlevel% neq 0 (
    echo [ERROR] 빌드 실패!
    pause
    exit /b 1
)

REM 빈 resources 폴더 생성 (다운로드 대상 폴더)
echo [3/4] resources 폴더 구조 생성 중...
mkdir "dist\resources" 2>nul
mkdir "dist\resources\background" 2>nul
mkdir "dist\resources\frames" 2>nul
mkdir "dist\resources\font" 2>nul

REM 기본 config.json 복사 (온라인 모드 활성화)
echo [4/4] 기본 설정 파일 복사 중...
copy "config.json" "dist\config.json" >nul

echo.
echo =====================================
echo  빌드 완료!
echo =====================================
echo.
echo 출력 위치: dist\HanaKiosk.exe
echo.
echo * 온라인 모드: 활성화시 서버에서 리소스 다운로드
echo * 배포시 dist 폴더 전체를 복사하세요
echo.

REM 파일 크기 표시
for %%A in (dist\HanaKiosk.exe) do echo EXE 크기: %%~zA bytes

pause
