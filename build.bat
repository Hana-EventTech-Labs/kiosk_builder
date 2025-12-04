@echo off
chcp 65001 > nul
title HanaKiosk 빌드 도구

echo.
echo ============================================================
echo   HanaKiosk ^& SuperKioskBuilder 빌드 도구
echo ============================================================
echo.
echo   1. 전체 빌드 (HanaKiosk + SuperKioskBuilder)
echo   2. HanaKiosk만 빌드
echo   3. SuperKioskBuilder만 빌드
echo   4. 전체 빌드 + GitHub 배포
echo   5. 종료
echo.

set /p choice="선택하세요 (1-5): "

if "%choice%"=="1" (
    echo.
    echo [전체 빌드 시작]
    python "%~dp0build_and_deploy.py" --all
    goto end
)

if "%choice%"=="2" (
    echo.
    echo [HanaKiosk 빌드 시작]
    python "%~dp0build_and_deploy.py" --kiosk
    goto end
)

if "%choice%"=="3" (
    echo.
    echo [SuperKioskBuilder 빌드 시작]
    python "%~dp0build_and_deploy.py" --builder
    goto end
)

if "%choice%"=="4" (
    echo.
    set /p version="버전 태그를 입력하세요 (예: v1.0.3, 비워두면 자동생성): "
    if "%version%"=="" (
        python "%~dp0build_and_deploy.py" --all --deploy
    ) else (
        python "%~dp0build_and_deploy.py" --all --deploy --version %version%
    )
    goto end
)

if "%choice%"=="5" (
    echo.
    echo 종료합니다.
    goto end
)

echo.
echo 잘못된 선택입니다.

:end
echo.
pause
